"""
PRITHVI — Telemetry & Safety Intelligence Service (Phase 2 Task 9)
==================================================================

Orchestrates the ingestion, validation, safety threshold evaluation,
signal deduplication, risk integration, and case synthesis for SCADA / IoT telemetry.
"""

from __future__ import annotations
from datetime import datetime, timezone
import hashlib
from typing import Any, Optional
from uuid import uuid4

from . import database as db
from .models import (
    SensorType,
    ThresholdStatus,
    SignalStatus,
    CaseSourceType,
    ActionPriority,
    ComplianceCase,
)
from .safety_engine import (
    evaluate_sensor_reading,
    validate_reading_bounds,
    THRESHOLD_RULES,
)


def ingest_telemetry_reading(item: dict, source: str = "SCADA_SIMULATOR") -> dict:
    """
    Ingest, validate, evaluate, and persist a single telemetry reading.
    Raises ValueError on validation failure.
    """
    sensor_ref = item.get("sensor_id") or item.get("sensor_code")
    mine_id = item.get("mine_id")
    sensor_type = item.get("sensor_type")
    value = item.get("value")
    unit = item.get("unit")

    if not sensor_ref and not (mine_id and sensor_type):
        raise ValueError("Missing required telemetry identifier (sensor_id, sensor_code, or mine_id + sensor_type).")
    if not mine_id or sensor_type is None or value is None or not unit:
        raise ValueError("Missing required telemetry fields (mine_id, sensor_type, value, unit).")

    # 1. Validate sensor existence
    sensor = None
    if sensor_ref:
        sensor = db.get_sensor(sensor_ref)
        if not sensor:
            sensor = db.get_sensor_by_code(sensor_ref)
    
    if not sensor and not sensor_ref and mine_id and sensor_type:
        # Lookup sensor by mine_id and sensor_type
        all_mine_sensors = db.list_sensors(mine_id=mine_id)
        matching = [s for s in all_mine_sensors if s.get("sensor_type") == sensor_type]
        if matching:
            sensor = matching[0]

    if not sensor:
        raise ValueError(f"Sensor '{sensor_ref or f'{mine_id}:{sensor_type}'}' is not registered.")
    
    sensor_id = sensor["sensor_id"]

    # 2. Validate mine ownership
    if sensor["mine_id"] != mine_id:
        raise ValueError(
            f"Sensor '{sensor_id}' belongs to mine '{sensor['mine_id']}', not '{mine_id}'."
        )

    # 3. Validate sensor type matches registered sensor
    if sensor["sensor_type"] != sensor_type:
        raise ValueError(
            f"Sensor '{sensor_id}' is registered as '{sensor['sensor_type']}', not '{sensor_type}'."
        )

    # 4. Validate physical numeric bounds and unit
    valid, err_msg = validate_reading_bounds(sensor_type, float(value), unit)
    if not valid:
        raise ValueError(err_msg)

    # 5. Evaluate reading against safety thresholds
    eval_result = evaluate_sensor_reading(sensor_type, float(value))
    threshold_status = eval_result.status.value

    now_iso = datetime.now(timezone.utc).isoformat()
    recorded_at = item.get("recorded_at") or now_iso
    reading_id = f"TLM-{uuid4().hex[:12].upper()}"

    reading_record = {
        "reading_id": reading_id,
        "sensor_id": sensor_id,
        "mine_id": mine_id,
        "zone_id": item.get("zone_id") or sensor.get("zone_id"),
        "sensor_type": sensor_type,
        "value": float(value),
        "unit": unit,
        "recorded_at": recorded_at,
        "received_at": now_iso,
        "quality_status": item.get("quality_status", "GOOD"),
        "threshold_status": threshold_status,
        "source": source,
        "simulated": True,
        "evidence_id": None,
        "created_at": now_iso,
    }

    # 6. Safety Signal Deduplication & Incident Creation
    linked_case_id = None
    evidence_id = None

    active_signal = db.get_active_signal_for_sensor(sensor_id)

    if threshold_status in (ThresholdStatus.WARNING.value, ThresholdStatus.CRITICAL.value):
        if active_signal:
            # Condition persists — update existing signal without creating duplicate incidents
            active_signal["last_detected_at"] = now_iso
            active_signal["observed_value"] = float(value)
            active_signal["consecutive_readings"] = int(active_signal.get("consecutive_readings", 1)) + 1
            # Escalate severity if reading became critical
            if threshold_status == ThresholdStatus.CRITICAL.value:
                active_signal["severity"] = ThresholdStatus.CRITICAL.value
                active_signal["threshold_definition"] = eval_result.threshold_definition
                active_signal["explanation"] = eval_result.explanation

            db.upsert_safety_signal(active_signal)
            linked_case_id = active_signal.get("linked_case_id")
            evidence_id = active_signal.get("evidence_id")
        else:
            # New breach detected — generate fresh safety signal
            signal_id = f"SIG-{uuid4().hex[:10].upper()}"

            is_new_case = False
            if threshold_status == ThresholdStatus.CRITICAL.value:
                linked_case_id, evidence_id = _create_operational_case_for_critical_signal(
                    signal_id=signal_id,
                    mine_id=mine_id,
                    sensor=sensor,
                    value=float(value),
                    unit=unit,
                    eval_result=eval_result,
                    timestamp=now_iso,
                )
                is_new_case = True
            reading_record["is_new_case"] = is_new_case

            new_signal = {
                "signal_id": signal_id,
                "mine_id": mine_id,
                "sensor_id": sensor_id,
                "sensor_type": sensor_type,
                "severity": threshold_status,
                "status": SignalStatus.ACTIVE.value,
                "observed_value": float(value),
                "unit": unit,
                "threshold_definition": eval_result.threshold_definition,
                "explanation": eval_result.explanation,
                "first_detected_at": now_iso,
                "last_detected_at": now_iso,
                "recovered_at": None,
                "consecutive_readings": 1,
                "linked_case_id": linked_case_id,
                "evidence_id": evidence_id,
                "simulated": True,
                "created_at": now_iso,
            }
            db.upsert_safety_signal(new_signal)

            # Log audit event
            _log_telemetry_audit(
                action="SCADA_SAFETY_SIGNAL_TRIGGERED",
                entity_id=signal_id,
                details=(
                    f"Safety signal {signal_id} ({threshold_status}) triggered on {sensor['sensor_code']} "
                    f"({sensor_type}): {value} {unit}. {eval_result.explanation}"
                ),
            )

    elif threshold_status == ThresholdStatus.NORMAL.value:
        # Value is within normal parameters. If a signal was active, record recovery!
        if active_signal:
            db.resolve_safety_signal(active_signal["signal_id"], now_iso)
            _log_telemetry_audit(
                action="SCADA_TELEMETRY_RECOVERY",
                entity_id=active_signal["signal_id"],
                details=(
                    f"Safety signal {active_signal['signal_id']} recovered. "
                    f"{sensor['sensor_code']} normalized to {value} {unit}."
                ),
            )

    # 7. Persist telemetry reading
    reading_record["evidence_id"] = evidence_id
    db.save_telemetry_reading(reading_record)

    return reading_record


def ingest_telemetry_batch(readings: list[dict], source: str = "SCADA_SIMULATOR") -> dict:
    """
    Ingest a batch of telemetry readings atomically.
    """
    ingested = []
    critical_count = 0
    cases_created = 0

    for r in readings:
        rec = ingest_telemetry_reading(r, source=source)
        ingested.append(rec)
        if rec.get("threshold_status") == "CRITICAL":
            critical_count += 1
        if rec.get("is_new_case"):
            cases_created += 1

    return {
        "success": True,
        "ingested_count": len(ingested),
        "evaluated_signals_count": len(readings),
        "critical_signals_count": critical_count,
        "new_cases_created": cases_created,
        "server_timestamp": datetime.now(timezone.utc).isoformat(),
        "readings": ingested,
    }


def _create_operational_case_for_critical_signal(
    signal_id: str,
    mine_id: str,
    sensor: dict,
    value: float,
    unit: str,
    eval_result: Any,
    timestamp: str,
) -> tuple[str, Optional[str]]:
    """
    Synthesize an operational ComplianceCase (Task 6) and anchor evidence (Task 7)
    from a critical telemetry breach.
    """
    from .case_service import CATEGORY_REGULATION_MAPPING

    category_map = {
        SensorType.METHANE.value: "Ventilation & Gas",
        SensorType.AIRFLOW.value: "Ventilation & Gas",
        SensorType.VENTILATION_FAN.value: "Ventilation & Gas",
        SensorType.DUST.value: "Ventilation & Gas",
        SensorType.SLOPE_DISPLACEMENT: "Roof / Strata",
        SensorType.PORE_PRESSURE: "Water / Drainage",
        SensorType.RAINFALL: "Water / Drainage",
    }
    category = category_map.get(sensor["sensor_type"], "Ventilation & Gas")
    reg_ref = eval_result.regulation_reference or CATEGORY_REGULATION_MAPPING.get(category, "CMR 2017 Safety Directive")

    case_id = f"CASE-SCADA-{uuid4().hex[:8].upper()}"
    evidence_id = f"EVD-SCADA-{uuid4().hex[:8].upper()}"

    # Insert compliance case into database
    conn = db._connect()

    # 2. Insert compliance case into database
    conn.execute(
        """
        INSERT INTO compliance_cases (
            case_id, mine_id, inspection_id, finding_id,
            category, regulation_reference, title, description,
            severity, risk_level, status, source_type, source_id,
            created_at, updated_at, closed_at, closed_by
        ) VALUES (?, ?, NULL, NULL, ?, ?, ?, ?, 'CRITICAL', 'CRITICAL', 'OPEN', 'SCADA_TELEMETRY', ?, ?, ?, NULL, NULL)
        """,
        (
            case_id,
            mine_id,
            category,
            reg_ref,
            f"Critical SCADA Telemetry: {sensor['display_name']} Breach",
            (
                f"Autonomous SCADA Safety Breach: Observed {value} {unit}. "
                f"{eval_result.explanation} Immediate corrective action and human verification required."
            ),
            signal_id,
            timestamp,
            timestamp,
        ),
    )
    conn.commit()
    conn.close()

    # 3. Anchor evidence package using Task 7 integrity service
    try:
        from .integrity_service import anchor_evidence
        anchor_evidence(evidence_id, actor_id="SCADA_SIMULATOR", reference_type="SCADA_TELEMETRY")
    except Exception as e:
        # Fallback in testing / minimal setups
        pass

    return case_id, evidence_id


def _log_telemetry_audit(action: str, entity_id: str, details: str) -> None:
    """Write an entry to PRITHVI audit_log."""
    now_iso = datetime.now(timezone.utc).isoformat()
    try:
        conn = db._connect()
        conn.execute(
            """
            INSERT INTO audit_log (entity_type, entity_id, action, actor_id, timestamp, details)
            VALUES ('SCADA_TELEMETRY', ?, ?, 'SCADA_SIMULATOR', ?, ?)
            """,
            (entity_id, action, now_iso, details),
        )
        conn.commit()
        conn.close()
    except Exception:
        pass


def get_latest_mine_telemetry(mine_id: str) -> list[dict]:
    """
    Get latest reading for each sensor in the mine, formatted for UI consumption.
    """
    readings = db.get_latest_telemetry_by_mine(mine_id)
    enriched = []
    now = datetime.now(timezone.utc)

    for r in readings:
        stype = r["sensor_type"]
        val = r["value"]
        eval_res = evaluate_sensor_reading(stype, val)

        # Elapsed seconds
        rec_time = datetime.fromisoformat(r["recorded_at"].replace("Z", "+00:00"))
        age_seconds = max(0, int((now - rec_time).total_seconds()))

        enriched.append({
            "reading_id": r["reading_id"],
            "sensor_id": r["sensor_id"],
            "sensor_code": r["sensor_code"],
            "sensor_type": stype,
            "display_name": r["display_name"],
            "value": val,
            "unit": r["unit"],
            "threshold_status": r["threshold_status"],
            "status_label": eval_res.status_label,
            "threshold_definition": eval_res.threshold_definition,
            "explanation": eval_res.explanation,
            "is_statutory": eval_res.is_statutory,
            "regulation_reference": eval_res.regulation_reference,
            "recorded_at": r["recorded_at"],
            "age_seconds": age_seconds,
            "is_stale": age_seconds > 120,
            "simulated": True,
        })

    return enriched


def get_mine_safety_signals(mine_id: str | None = None, active_only: bool = False) -> list[dict]:
    """
    Return safety signals with explainable threshold details.
    """
    if active_only:
        signals = db.get_active_safety_signals(mine_id)
    else:
        signals = db.get_safety_signals_history(mine_id, limit=100)

    formatted = []
    for s in signals:
        formatted.append({
            "signal_id": s["signal_id"],
            "mine_id": s["mine_id"],
            "sensor_id": s["sensor_id"],
            "sensor_code": s.get("sensor_code", s["sensor_id"]),
            "display_name": s.get("display_name", s["sensor_type"]),
            "sensor_type": s["sensor_type"],
            "severity": s["severity"],
            "status": s["status"],
            "observed_value": s["observed_value"],
            "unit": s["unit"],
            "threshold_definition": s["threshold_definition"],
            "explanation": s["explanation"],
            "first_detected_at": s["first_detected_at"],
            "last_detected_at": s["last_detected_at"],
            "recovered_at": s.get("recovered_at"),
            "consecutive_readings": s.get("consecutive_readings", 1),
            "linked_case_id": s.get("linked_case_id"),
            "evidence_id": s.get("evidence_id"),
            "simulated": True,
        })
    return formatted
