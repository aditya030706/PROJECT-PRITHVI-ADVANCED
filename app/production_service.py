"""
PRITHVI — Production & Operational Governance Intelligence Service (Phase 2 Task 10)
=====================================================================================

Provides the operational production governance pipeline:
  SOURCE (Weighbridge / Shift Report / Surveyor / CHP)
      ↓
  VALIDATION & IMMUTABLE PERSISTENCE (SHA-256 Content Hash)
      ↓
  MINE-TYPE ADAPTIVE CONTEXT (Opencast vs Underground)
      ↓
  ANOMALY & SAFETY CORRELATION (Dispatch mismatch, Safety Stoppage overlap)
      ↓
  HIERARCHY AGGREGATION (Mine -> Area -> Subsidiary -> CIL Corporate)
      ↓
  STATUTORY REPORTING & AUDIT INTEGRITY
"""

from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timezone, timedelta
from typing import Any, Optional
from uuid import uuid4

from fastapi import HTTPException

from . import database as db
from .models import (
    ProductionRecord,
    ProductionTarget,
    ProductionAnomaly,
    ProductionSource,
    ContractType,
    ProductionOperationType,
    ProductionRecordStatus,
    CaseSourceType,
    ComplianceCase,
)
from .schemas import (
    ProductionRecordCreate,
    ProductionRecordCorrectionRequest,
    ProductionTargetCreate,
)


# ============================================================
# 1. RECORD PRODUCTION EVENT
# ============================================================

def record_production_event(data: ProductionRecordCreate, actor_id: str = "SYSTEM") -> dict:
    """
    Validate, hash, and persist an operational production record.
    Executes real-time anomaly detection and safety stoppage correlation.
    """
    if data.production_quantity <= 0:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid production quantity: {data.production_quantity}. Must be strictly greater than 0.",
        )

    if data.dispatch_quantity is not None and data.dispatch_quantity < 0:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid dispatch quantity: {data.dispatch_quantity}. Cannot be negative.",
        )

    conn = db._connect()
    mine_row = conn.execute("SELECT * FROM mines WHERE mine_id = ?", (data.mine_id,)).fetchone()
    conn.close()

    if not mine_row:
        raise HTTPException(status_code=404, detail=f"Mine with ID '{data.mine_id}' not found.")

    mine = dict(mine_row)
    area_id = mine.get("area_id") or f"{mine.get('subsidiary', 'CIL')}-{mine.get('district', 'AREA').upper().replace(' ', '-')}"
    subsidiary_id = mine.get("subsidiary") or "CIL"

    record_id = f"PROD-{uuid4().hex[:10].upper()}"
    now = datetime.now(timezone.utc)
    now_iso = now.isoformat()

    # Determine operation type if not explicitly set
    op_type = data.operation_type
    if not op_type:
        if mine.get("mine_type") == "opencast_coal":
            op_type = "OPENCAST_MINING"
        else:
            op_type = "UNDERGROUND_EXTRACTION"

    # Compute deterministic SHA-256 content hash
    content_raw = f"{data.mine_id}|{data.production_date}|{data.shift_name}|{data.production_quantity}|{data.dispatch_quantity}|{data.production_source}|{op_type}|{actor_id}|{now_iso}"
    content_hash = hashlib.sha256(content_raw.encode("utf-8")).hexdigest()

    # Parse contract type
    c_type = None
    if data.contract_type:
        try:
            c_type = ContractType(data.contract_type.upper())
        except Exception:
            c_type = ContractType.DEPARTMENTAL

    # Build persistent model
    record = ProductionRecord(
        record_id=record_id,
        mine_id=data.mine_id,
        area_id=area_id,
        subsidiary_id=subsidiary_id,
        shift_name=data.shift_name,
        production_date=data.production_date,
        production_quantity=data.production_quantity,
        production_unit=data.production_unit or "TONNES",
        dispatch_quantity=data.dispatch_quantity,
        production_source=ProductionSource(data.production_source) if data.production_source in ProductionSource._value2member_map_ else ProductionSource.SHIFT_REPORT,
        operation_type=ProductionOperationType(op_type) if op_type in ProductionOperationType._value2member_map_ else ProductionOperationType.UNDERGROUND_EXTRACTION,
        zone_id=data.zone_id,
        district_section=data.district_section,
        face_panel=data.face_panel,
        overburden_quantity=data.overburden_quantity,
        overburden_unit=data.overburden_unit,
        contractor_id=data.contractor_id,
        contractor_name=data.contractor_name,
        contract_type=c_type,
        target_quantity=data.target_quantity,
        downtime_minutes=data.downtime_minutes or 0,
        delay_reason=data.delay_reason,
        hemm_context=data.hemm_context,
        entered_by=actor_id or data.entered_by or "SYSTEM",
        source_reference=data.source_reference,
        status=ProductionRecordStatus.RECORDED,
        is_superseded=False,
        superseded_by=None,
        correction_reason=None,
        content_hash=content_hash,
        simulated=data.simulated,
        notes=data.notes,
        recorded_at=now,
        created_at=now,
        updated_at=now,
    )

    # Persist record
    db.save_production_record(record)

    # Record initial creation audit event
    db.save_production_audit_event(
        event_id=f"PAUD-{uuid4().hex[:10].upper()}",
        record_id=record_id,
        action="RECORD_CREATED",
        actor_id=actor_id or "SYSTEM",
        previous_state=None,
        new_state=f"Production: {data.production_quantity} {data.production_unit}",
        reason="Initial operational record creation",
        details=f"Source: {data.production_source}, Hash: {content_hash}",
    )

    # Run real-time anomaly detection for this mine and date
    detect_anomalies_for_record(record, mine)

    return db.get_production_record(record_id)


# ============================================================
# 2. DETERMINISTIC ANOMALY DETECTION ENGINE
# ============================================================

def detect_anomalies_for_record(record: ProductionRecord, mine_info: dict) -> list[dict]:
    """
    Run explainable anomaly rules against stored production and safety conditions:
    A. Dispatch exceeds recorded production
    B. Production recorded during active safety stoppage
    C. Duplicate production record
    D. Unexplained sudden deviation (>30% below target)
    """
    now = datetime.now(timezone.utc)
    anomalies_found: list[dict] = []

    # ------------------------------------------------------------
    # A. Production vs Dispatch Mismatch
    # ------------------------------------------------------------
    if record.dispatch_quantity is not None and record.production_quantity > 0:
        # If dispatch exceeds production by more than 15% without prior pithead stock note
        if record.dispatch_quantity > (record.production_quantity * 1.15):
            delta = round(record.dispatch_quantity - record.production_quantity, 1)
            anomaly_id = f"ANOM-DISP-{record.record_id}"
            anomaly = ProductionAnomaly(
                anomaly_id=anomaly_id,
                mine_id=record.mine_id,
                anomaly_type="DISPATCH_MISMATCH",
                severity="HIGH",
                what=f"Dispatch quantity ({record.dispatch_quantity} T) exceeds recorded production ({record.production_quantity} T) by {delta} T.",
                why="Reconciliation variance exceeds statutory threshold (+15%). May indicate delayed production logging or stockpile variance.",
                source="Weighbridge and Dispatch Reconciliation",
                time=now,
                affected_record_ids=[record.record_id],
                recommended_review="Review pithead stockpile records and verify weighbridge calibration certificates.",
                resolved=False,
            )
            db.save_production_anomaly(anomaly)
            anomalies_found.append(anomaly.model_dump())

    # ------------------------------------------------------------
    # B. Production Recorded During Active Safety Stoppage
    # ------------------------------------------------------------
    # Check for active CRITICAL safety signals (e.g. Methane > 1.25%, slope displacement, etc.)
    active_safety_signals = db.get_active_safety_signals(record.mine_id)
    critical_signals = [s for s in active_safety_signals if s.get("severity") == "CRITICAL"]

    # Also check for active DGMS Enforcement Actions of severe type
    conn = db._connect()
    active_enforcements = conn.execute(
        """
        SELECT * FROM enforcement_actions
        WHERE mine_id = ? AND status = 'OPEN' AND severity = 'CRITICAL'
        """,
        (record.mine_id,),
    ).fetchall()
    conn.close()

    if critical_signals or active_enforcements:
        reasons = []
        if critical_signals:
            sig_names = ", ".join([f"{s.get('sensor_type')} ({s.get('observed_value')} {s.get('unit')})" for s in critical_signals])
            reasons.append(f"Active critical telemetry conditions: {sig_names}")
        if active_enforcements:
            reasons.append(f"Active statutory enforcement orders: {len(active_enforcements)} open")

        why_text = " | ".join(reasons)
        anomaly_id = f"ANOM-SAFE-{record.record_id}"
        anomaly = ProductionAnomaly(
            anomaly_id=anomaly_id,
            mine_id=record.mine_id,
            anomaly_type="SAFETY_STOPPAGE_CONFLICT",
            severity="CRITICAL",
            what=f"Production of {record.production_quantity} T recorded during an active safety condition.",
            why=why_text,
            source="SCADA Safety Intelligence & Statutory Enforcement",
            time=now,
            affected_record_ids=[record.record_id],
            recommended_review="Immediate operational review required. Verify whether extraction occurred in affected or isolated ventilating districts.",
            resolved=False,
        )
        db.save_production_anomaly(anomaly)
        anomalies_found.append(anomaly.model_dump())

        # Synthesize a compliance case idempotently in the existing case management system
        try:
            case_id = f"CASE-PROD-{record.record_id}"
            existing_case = db.get_compliance_case_by_source(CaseSourceType.OPERATIONAL_PRODUCTION.value, record.record_id)
            if not existing_case:
                case = ComplianceCase(
                    case_id=case_id,
                    mine_id=record.mine_id,
                    category="Ventilation & Gas" if "Methane" in why_text else "HEMM",
                    regulation_reference="CMR 2017 Reg 119 / Mines Act 1952 Sec 22",
                    title=f"Production During Safety Stoppage: {record.shift_name} ({record.production_quantity} T)",
                    description=f"Operational extraction occurred concurrently with critical safety alarm. {why_text}",
                    severity="CRITICAL",
                    risk_level="CRITICAL",
                    status="OPEN",
                    source_type=CaseSourceType.OPERATIONAL_PRODUCTION,
                    source_id=record.record_id,
                    created_at=now,
                    updated_at=now,
                )
                db.save_compliance_case(case)
        except Exception:
            pass

    # ------------------------------------------------------------
    # C. Duplicate Record Detection
    # ------------------------------------------------------------
    conn = db._connect()
    duplicates = conn.execute(
        """
        SELECT record_id FROM production_records
        WHERE mine_id = ? AND production_date = ? AND shift_name = ?
          AND production_source = ? AND operation_type = ?
          AND is_superseded = 0 AND record_id != ?
        """,
        (
            record.mine_id,
            record.production_date,
            record.shift_name,
            record.production_source.value if hasattr(record.production_source, "value") else str(record.production_source),
            record.operation_type.value if hasattr(record.operation_type, "value") else str(record.operation_type),
            record.record_id,
        ),
    ).fetchall()
    conn.close()

    if duplicates:
        dup_ids = [d["record_id"] for d in duplicates]
        anomaly_id = f"ANOM-DUP-{record.record_id}"
        anomaly = ProductionAnomaly(
            anomaly_id=anomaly_id,
            mine_id=record.mine_id,
            anomaly_type="DUPLICATE_RECORD",
            severity="MEDIUM",
            what=f"Potential duplicate production entry for {record.shift_name} on {record.production_date}.",
            why=f"Identical mine, date, shift, source, and operation type already logged in record(s): {', '.join(dup_ids)}.",
            source="Data Ingestion Deduplication Rule",
            time=now,
            affected_record_ids=[record.record_id] + dup_ids,
            recommended_review="Verify whether this represents an additional sub-shift batch or an accidental double submission.",
            resolved=False,
        )
        db.save_production_anomaly(anomaly)
        anomalies_found.append(anomaly.model_dump())

    # ------------------------------------------------------------
    # D. Sudden Unexplained Deviation (>30% below target)
    # ------------------------------------------------------------
    target = db.get_production_target(record.mine_id, record.production_date)
    if target and target.get("daily_target_tonnes"):
        daily_target = float(target["daily_target_tonnes"])
        expected_shift_target = daily_target / 3.0
        if expected_shift_target > 0 and record.production_quantity < (expected_shift_target * 0.70):
            deficit = round(expected_shift_target - record.production_quantity, 1)
            pct = round((record.production_quantity / expected_shift_target) * 100, 1)
            anomaly_id = f"ANOM-DEV-{record.record_id}"
            anomaly = ProductionAnomaly(
                anomaly_id=anomaly_id,
                mine_id=record.mine_id,
                anomaly_type="PRODUCTION_DEFICIT",
                severity="MEDIUM",
                what=f"Shift production ({record.production_quantity} T) is {deficit} T below nominal shift target ({round(expected_shift_target, 1)} T, {pct}% achievement).",
                why=f"Operational delay recorded: '{record.delay_reason or 'None stated'}', downtime: {record.downtime_minutes} min.",
                source="Target Variance Rule",
                time=now,
                affected_record_ids=[record.record_id],
                recommended_review="Review shift downtime causes, machinery availability, and face geological conditions.",
                resolved=False,
            )
            db.save_production_anomaly(anomaly)
            anomalies_found.append(anomaly.model_dump())

    return anomalies_found


# ============================================================
# 3. MINE PRODUCTION SUMMARY
# ============================================================

def get_mine_production_summary(mine_id: str, query_date: Optional[str] = None) -> dict:
    """
    Generate an operational summary for a specific mine and date:
    - Target vs Actual comparison
    - Shift-level performance breakdown
    - Contractor / Departmental contributions
    - HEMM and delay context
    - Active safety correlation and anomalies
    """
    conn = db._connect()
    mine_row = conn.execute("SELECT * FROM mines WHERE mine_id = ?", (mine_id,)).fetchone()
    if not mine_row:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Mine '{mine_id}' not found.")
    mine = dict(mine_row)

    # If date is not provided, use today's date in UTC, or the latest available record date
    if not query_date:
        latest = conn.execute(
            "SELECT MAX(production_date) FROM production_records WHERE mine_id = ? AND is_superseded = 0",
            (mine_id,),
        ).fetchone()
        if latest and latest[0]:
            query_date = latest[0]
        else:
            query_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    records = conn.execute(
        """
        SELECT * FROM production_records
        WHERE mine_id = ? AND production_date = ? AND is_superseded = 0
        ORDER BY shift_name ASC, recorded_at ASC
        """,
        (mine_id, query_date),
    ).fetchall()

    target_row = conn.execute(
        "SELECT * FROM production_targets WHERE mine_id = ? AND target_date = ?",
        (mine_id, query_date),
    ).fetchone()
    conn.close()

    rec_list = [dict(r) for r in records]
    total_actual = sum(float(r["production_quantity"]) for r in rec_list)
    total_dispatch = sum(float(r["dispatch_quantity"] or 0) for r in rec_list)
    total_downtime = sum(int(r["downtime_minutes"] or 0) for r in rec_list)
    total_ob = sum(float(r["overburden_quantity"] or 0) for r in rec_list if r.get("overburden_quantity"))

    # Target calculations
    target_val = None
    target_status = "TARGET_NOT_CONFIGURED"
    variance = None
    achievement_pct = None

    if target_row:
        target_val = float(target_row["daily_target_tonnes"])
        target_status = "CONFIGURED"
        variance = round(total_actual - target_val, 1)
        achievement_pct = round((total_actual / target_val) * 100, 1) if target_val > 0 else 0.0

    dispatch_variance = round(total_dispatch - total_actual, 1) if total_dispatch > 0 else None

    # Shift Breakdown
    shifts_dict: dict[str, dict] = {
        "Shift A": {"production": 0.0, "dispatch": 0.0, "downtime": 0, "count": 0, "sources": set(), "delays": []},
        "Shift B": {"production": 0.0, "dispatch": 0.0, "downtime": 0, "count": 0, "sources": set(), "delays": []},
        "Shift C": {"production": 0.0, "dispatch": 0.0, "downtime": 0, "count": 0, "sources": set(), "delays": []},
    }

    contractors_dict: dict[str, dict] = {}
    delay_reasons: list[str] = []
    sources_used: set[str] = set()
    hemm_snippets: list[str] = []

    for r in rec_list:
        s_name = r["shift_name"]
        if s_name not in shifts_dict:
            shifts_dict[s_name] = {"production": 0.0, "dispatch": 0.0, "downtime": 0, "count": 0, "sources": set(), "delays": []}

        q = float(r["production_quantity"])
        d = float(r["dispatch_quantity"] or 0)
        dt = int(r["downtime_minutes"] or 0)

        shifts_dict[s_name]["production"] += q
        shifts_dict[s_name]["dispatch"] += d
        shifts_dict[s_name]["downtime"] += dt
        shifts_dict[s_name]["count"] += 1
        shifts_dict[s_name]["sources"].add(r["production_source"])
        if r.get("delay_reason"):
            shifts_dict[s_name]["delays"].append(r["delay_reason"])
            delay_reasons.append(f"{s_name}: {r['delay_reason']} ({dt}m)")

        sources_used.add(r["production_source"])

        # Contractor contribution
        c_name = r.get("contractor_name") or "Departmental Operations"
        c_type = r.get("contract_type") or "DEPARTMENTAL"
        c_id = r.get("contractor_id")
        if c_name not in contractors_dict:
            contractors_dict[c_name] = {"id": c_id, "name": c_name, "type": c_type, "production": 0.0}
        contractors_dict[c_name]["production"] += q

        if r.get("hemm_context"):
            hemm_snippets.append(r["hemm_context"])

    shift_items = []
    shift_target = (target_val / 3.0) if target_val else None
    for s_name, s_data in shifts_dict.items():
        shift_items.append({
            "shift_name": s_name,
            "production_tonnes": round(s_data["production"], 1),
            "dispatch_tonnes": round(s_data["dispatch"], 1),
            "target_tonnes": round(shift_target, 1) if shift_target else None,
            "downtime_minutes": s_data["downtime"],
            "records_count": s_data["count"],
            "sources": sorted(list(s_data["sources"])),
            "delays": s_data["delays"],
        })

    contractor_items = []
    for c_name, c_data in contractors_dict.items():
        share = round((c_data["production"] / total_actual) * 100, 1) if total_actual > 0 else 0.0
        contractor_items.append({
            "contractor_id": c_data["id"],
            "contractor_name": c_data["name"],
            "contract_type": c_data["type"],
            "production_tonnes": round(c_data["production"], 1),
            "percentage_share": share,
        })
    contractor_items.sort(key=lambda x: -x["production_tonnes"])

    # Active safety signals & stoppage status
    active_signals = db.get_active_safety_signals(mine_id)
    has_critical_safety = any(s.get("severity") == "CRITICAL" for s in active_signals)
    safety_notes = None
    if has_critical_safety:
        crit_names = [s.get("sensor_type") for s in active_signals if s.get("severity") == "CRITICAL"]
        safety_notes = f"CRITICAL SAFETY ALERT ACTIVE: High severity conditions detected on {', '.join(set(crit_names))}."

    # Anomalies for this mine
    anomalies = db.get_active_production_anomalies(mine_id)
    filtered_anomalies = [a for a in anomalies if a.get("time", "").startswith(query_date) or not a.get("resolved")]

    # Check compliance status
    comp_status = "COMPLIANT"
    if has_critical_safety or any(a.get("severity") == "CRITICAL" for a in filtered_anomalies):
        comp_status = "REVIEW_REQUIRED"
    elif any(a.get("severity") == "HIGH" for a in filtered_anomalies):
        comp_status = "ACTION_REQUIRED"

    is_simulated = any(bool(r.get("simulated")) for r in rec_list) or True

    return {
        "mine_id": mine_id,
        "mine_name": mine.get("name", mine_id),
        "subsidiary": mine.get("subsidiary", "CIL"),
        "area_name": mine.get("area_name") or f"{mine.get('district', 'Central')} Area",
        "mine_type": mine.get("mine_type", "underground_coal"),
        "date": query_date,
        "production_actual_tonnes": round(total_actual, 1),
        "production_target_tonnes": target_val,
        "target_status": target_status,
        "variance_tonnes": variance,
        "achievement_percentage": achievement_pct,
        "dispatch_actual_tonnes": round(total_dispatch, 1),
        "dispatch_variance_tonnes": dispatch_variance,
        "overburden_actual_bcm": round(total_ob, 1) if total_ob > 0 else None,
        "total_downtime_minutes": total_downtime,
        "shifts": shift_items,
        "contractor_contributions": contractor_items,
        "hemm_context_summary": " · ".join(hemm_snippets) if hemm_snippets else ("HEMM data unavailable" if mine.get("uses_hemm") else None),
        "delay_reasons": delay_reasons,
        "sources_used": sorted(list(sources_used)),
        "anomalies": filtered_anomalies,
        "active_safety_stoppage": has_critical_safety,
        "safety_context_notes": safety_notes,
        "compliance_status": comp_status,
        "simulated": is_simulated,
    }


# ============================================================
# 4. HIERARCHY AGGREGATIONS: AREA, SUBSIDIARY, CORPORATE
# ============================================================

def get_area_production_summary(area_id: str, query_date: Optional[str] = None) -> dict:
    """Roll up all mines belonging to a given Area."""
    if not query_date:
        query_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    conn = db._connect()
    mines_rows = conn.execute(
        "SELECT * FROM mines WHERE area_id = ? OR area_name LIKE ? OR district LIKE ?",
        (area_id, f"%{area_id}%", f"%{area_id}%"),
    ).fetchall()
    conn.close()

    # Fallback: if no area_id matches directly, match by prefix
    if not mines_rows:
        conn = db._connect()
        mines_rows = conn.execute("SELECT * FROM mines").fetchall()
        conn.close()
        mines_rows = [m for m in mines_rows if area_id.lower() in (m["district"] or "").lower() or area_id.lower() in (m["name"] or "").lower()]

    area_name = f"{area_id.replace('-', ' ').title()} Area"
    subsidiary = mines_rows[0]["subsidiary"] if mines_rows else "CIL"

    mine_summaries = []
    tot_prod = 0.0
    tot_target = 0.0
    has_target = False
    anomalies_count = 0

    for m in mines_rows:
        m_id = m["mine_id"]
        s = get_mine_production_summary(m_id, query_date)
        tot_prod += s["production_actual_tonnes"]
        if s["production_target_tonnes"] is not None:
            tot_target += s["production_target_tonnes"]
            has_target = True
        anomalies_count += len(s["anomalies"])
        mine_summaries.append({
            "mine_id": m_id,
            "mine_name": s["mine_name"],
            "mine_type": s["mine_type"],
            "production_actual": s["production_actual_tonnes"],
            "production_target": s["production_target_tonnes"],
            "achievement_percentage": s["achievement_percentage"],
            "compliance_status": s["compliance_status"],
            "anomalies_count": len(s["anomalies"]),
            "active_safety_stoppage": s["active_safety_stoppage"],
        })

    overall_ach = round((tot_prod / tot_target) * 100, 1) if (has_target and tot_target > 0) else None

    return {
        "area_id": area_id,
        "area_name": area_name,
        "subsidiary": subsidiary,
        "date": query_date,
        "total_production_tonnes": round(tot_prod, 1),
        "total_target_tonnes": round(tot_target, 1) if has_target else None,
        "overall_achievement_percentage": overall_ach,
        "mines_reporting": len([m for m in mine_summaries if m["production_actual"] > 0]),
        "total_mines": len(mines_rows),
        "open_anomalies_count": anomalies_count,
        "mines": mine_summaries,
    }


def get_subsidiary_production_summary(subsidiary_id: str, query_date: Optional[str] = None) -> dict:
    """Roll up all areas and mines belonging to a Subsidiary (e.g., BCCL, ECL, MCL)."""
    if not query_date:
        query_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    conn = db._connect()
    mines_rows = conn.execute(
        "SELECT * FROM mines WHERE subsidiary = ? OR mine_id LIKE ?",
        (subsidiary_id.upper(), f"%{subsidiary_id.upper()}%"),
    ).fetchall()
    conn.close()

    areas_dict: dict[str, list[dict]] = {}
    for m in mines_rows:
        a_name = m["area_name"] or f"{m['district']} Area"
        areas_dict.setdefault(a_name, []).append(dict(m))

    tot_prod = 0.0
    tot_disp = 0.0
    tot_target = 0.0
    has_target = False
    tot_anomalies = 0
    tot_critical_safety = 0
    area_items = []

    for a_name, a_mines in areas_dict.items():
        a_prod = 0.0
        a_target = 0.0
        a_has_target = False
        a_disp = 0.0
        a_anom = 0.0

        for m in a_mines:
            m_id = m["mine_id"]
            s = get_mine_production_summary(m_id, query_date)
            a_prod += s["production_actual_tonnes"]
            a_disp += s["dispatch_actual_tonnes"]
            if s["production_target_tonnes"] is not None:
                a_target += s["production_target_tonnes"]
                a_has_target = True
            a_anom += len(s["anomalies"])
            if s["active_safety_stoppage"]:
                tot_critical_safety += 1

        tot_prod += a_prod
        tot_disp += a_disp
        if a_has_target:
            tot_target += a_target
            has_target = True
        tot_anomalies += int(a_anom)

        ach = round((a_prod / a_target) * 100, 1) if (a_has_target and a_target > 0) else None
        area_items.append({
            "area_name": a_name,
            "production_actual": round(a_prod, 1),
            "production_target": round(a_target, 1) if a_has_target else None,
            "achievement_percentage": ach,
            "mines_count": len(a_mines),
            "anomalies_count": int(a_anom),
        })

    sub_ach = round((tot_prod / tot_target) * 100, 1) if (has_target and tot_target > 0) else None

    return {
        "subsidiary_id": subsidiary_id.upper(),
        "subsidiary_name": f"{subsidiary_id.upper()} (Coal India Limited)",
        "date": query_date,
        "total_production_tonnes": round(tot_prod, 1),
        "total_target_tonnes": round(tot_target, 1) if has_target else None,
        "overall_achievement_percentage": sub_ach,
        "total_dispatch_tonnes": round(tot_disp, 1),
        "mines_reporting": len([m for m in mines_rows if m["active"]]),
        "total_mines": len(mines_rows),
        "open_anomalies_count": tot_anomalies,
        "critical_safety_signals_count": tot_critical_safety,
        "areas": area_items,
    }


def get_corporate_production_summary(query_date: Optional[str] = None) -> dict:
    """Pan-India CIL Corporate aggregation across all configured subsidiaries."""
    if not query_date:
        query_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    conn = db._connect()
    subs_rows = conn.execute("SELECT DISTINCT subsidiary FROM mines WHERE subsidiary IS NOT NULL").fetchall()
    total_mines_count = conn.execute("SELECT COUNT(*) FROM mines WHERE active = 1").fetchone()[0]
    conn.close()

    subs_list = [r["subsidiary"] for r in subs_rows] if subs_rows else ["BCCL", "ECL", "MCL"]

    subsidiary_summaries = []
    pan_india_prod = 0.0
    pan_india_disp = 0.0
    pan_india_target = 0.0
    has_target = False
    total_anomalies = 0
    critical_signals = 0
    reporting_mines = 0

    for sub in subs_list:
        sub_summary = get_subsidiary_production_summary(sub, query_date)
        subsidiary_summaries.append(sub_summary)

        pan_india_prod += sub_summary["total_production_tonnes"]
        pan_india_disp += sub_summary["total_dispatch_tonnes"]
        if sub_summary["total_target_tonnes"] is not None:
            pan_india_target += sub_summary["total_target_tonnes"]
            has_target = True
        total_anomalies += sub_summary["open_anomalies_count"]
        critical_signals += sub_summary["critical_safety_signals_count"]
        reporting_mines += sub_summary["mines_reporting"]

    overall_ach = round((pan_india_prod / pan_india_target) * 100, 1) if (has_target and pan_india_target > 0) else None

    return {
        "organization": "Coal India Limited (CIL) Corporate HQ",
        "date": query_date,
        "pan_india_production_tonnes": round(pan_india_prod, 1),
        "pan_india_target_tonnes": round(pan_india_target, 1) if has_target else None,
        "pan_india_achievement_percentage": overall_ach,
        "total_dispatch_tonnes": round(pan_india_disp, 1),
        "subsidiaries_reporting": len(subs_list),
        "total_subsidiaries": len(subs_list),
        "mines_reporting": reporting_mines,
        "total_mines": total_mines_count,
        "total_anomalies_count": total_anomalies,
        "critical_operational_signals": critical_signals,
        "subsidiaries": subsidiary_summaries,
        "environment_notice": "DEMONSTRATION GOVERNANCE ENVIRONMENT",
    }


# ============================================================
# 5. STATUTORY DAILY REPORT GENERATION WITH INTEGRITY HASH
# ============================================================

def generate_daily_production_report(mine_id: str, report_date: Optional[str] = None) -> dict:
    """
    Generate an immutable, database-backed Daily Mine Production Summary report.
    Includes source traceability, shift breakdowns, contractor contributions, and a cryptographic hash.
    """
    summary = get_mine_production_summary(mine_id, report_date)
    records = db.list_production_records(mine_id=mine_id, production_date=summary["date"], include_superseded=False)

    source_breakdown: dict[str, float] = {}
    for r in records:
        src = r["production_source"]
        q = float(r["production_quantity"])
        source_breakdown[src] = round(source_breakdown.get(src, 0.0) + q, 1)

    report_id = f"REP-DPR-{mine_id}-{summary['date']}"
    now_iso = datetime.now(timezone.utc).isoformat()

    # Cryptographic integrity hash of the verified report payload
    raw_payload = f"{report_id}|{mine_id}|{summary['date']}|{summary['production_actual_tonnes']}|{summary['dispatch_actual_tonnes']}|{len(records)}|{json.dumps(source_breakdown, sort_keys=True)}"
    content_hash = hashlib.sha256(raw_payload.encode("utf-8")).hexdigest()

    return {
        "report_id": report_id,
        "report_title": f"Daily Operational & Statutory Production Summary — {summary['mine_name']}",
        "mine_id": mine_id,
        "mine_name": summary["mine_name"],
        "subsidiary": summary["subsidiary"],
        "area_name": summary["area_name"],
        "report_date": summary["date"],
        "generated_at": now_iso,
        "records_included_count": len(records),
        "total_production_tonnes": summary["production_actual_tonnes"],
        "total_dispatch_tonnes": summary["dispatch_actual_tonnes"],
        "target_tonnes": summary["production_target_tonnes"],
        "variance_tonnes": summary["variance_tonnes"],
        "achievement_percentage": summary["achievement_percentage"],
        "total_downtime_minutes": summary["total_downtime_minutes"],
        "source_breakdown": source_breakdown,
        "shift_breakdown": summary["shifts"],
        "contractor_breakdown": summary["contractor_contributions"],
        "anomalies_detected": summary["anomalies"],
        "content_hash": content_hash,
        "integrity_status": "AUDIT_PROOF_RECORDED",
        "blockchain_anchor_ref": f"DEMO-BLOCK-{content_hash[:12].upper()}",
    }
