"""
PRITHVI — Environmental Governance, Monitoring & Regulatory Reporting Engine (Phase 2 Task 13)
=============================================================================================

Implements the traceable environmental governance chain:
ENVIRONMENTAL OBLIGATION
        ↓
MINE / OPERATION
        ↓
ENVIRONMENTAL PARAMETER
        ↓
MEASUREMENT / OBSERVATION
        ↓
THRESHOLD / COMPLIANCE RULE
        ↓
EVIDENCE
        ↓
VIOLATION / FINDING
        ↓
RISK
        ↓
CORRECTIVE ACTION
        ↓
VERIFICATION
        ↓
REGULATORY REPORT
        ↓
AUDIT TRAIL
"""

from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from typing import Any, Optional
from uuid import uuid4

from fastapi import HTTPException, status

from . import database as db
from .models import (
    EnvironmentalDomain,
    EnvironmentalSourceType,
    DataQualityStatus,
    EnvironmentalParameter,
    EnvironmentalMeasurement,
    EnvironmentalThreshold,
    EnvironmentalObligation,
    EnvironmentalSchedule,
    EnvironmentalReport,
    Finding,
    ComplianceCase,
    CaseSourceType,
    CaseStatus,
    CorrectiveAction,
    ActionPriority,
    MineType,
)
from .hierarchy_service import resolve_mine_hierarchy
from .audit_proof import generate_content_hash, generate_ipfs_cid


# ============================================================
# 1. THRESHOLD EVALUATION ENGINE
# ============================================================

def evaluate_measurement_threshold(
    value: Optional[float] = None,
    threshold: Optional[EnvironmentalThreshold] = None,
    parameter_id: Optional[str] = None,
    mine_type: str = "ALL",
) -> Any:
    """
    Evaluate an observed measurement against an active threshold rule.
    Supports both direct (value, threshold) call and parameter/mine_type lookup.
    """
    if threshold is not None and parameter_id is None:
        if not threshold.active:
            return False, None, None

        th_type = threshold.threshold_type.upper() if threshold.threshold_type else "MAX_LIMIT"

        if th_type in ("MAX_LIMIT", "BENCHMARK") and threshold.upper_limit is not None:
            if value is not None and value > threshold.upper_limit:
                return True, "EXCEEDS_MAXIMUM", threshold.upper_limit

        elif th_type == "MIN_LIMIT" and threshold.lower_limit is not None:
            if value is not None and value < threshold.lower_limit:
                return True, "BELOW_MINIMUM", threshold.lower_limit

        elif th_type == "RANGE":
            if threshold.upper_limit is not None and value is not None and value > threshold.upper_limit:
                return True, "EXCEEDS_RANGE_MAXIMUM", threshold.upper_limit
            if threshold.lower_limit is not None and value is not None and value < threshold.lower_limit:
                return True, "BELOW_RANGE_MINIMUM", threshold.lower_limit

        return False, None, None

    # Parameter lookup mode
    norm_type = "ALL"
    if mine_type:
        m_up = str(mine_type).upper()
        if "UNDERGROUND" in m_up:
            norm_type = "UNDERGROUND"
        elif "OPENCAST" in m_up:
            norm_type = "OPENCAST"
        else:
            norm_type = m_up

    thresholds = db.list_environmental_thresholds(
        parameter_id=parameter_id,
        mine_type=norm_type,
        active_only=True,
    )

    val = float(value) if value is not None else 0.0
    for th in thresholds:
        ttype = th.threshold_type.upper() if th.threshold_type else "MAX_LIMIT"

        if ttype in ("MAX_LIMIT", "BENCHMARK") and th.upper_limit is not None:
            if val > th.upper_limit:
                return True, {
                    "breach_type": "UPPER_LIMIT_EXCEEDED",
                    "observed_value": val,
                    "limit": th.upper_limit,
                    "threshold": th,
                }
        elif ttype == "MIN_LIMIT" and th.lower_limit is not None:
            if val < th.lower_limit:
                return True, {
                    "breach_type": "LOWER_LIMIT_VIOLATED",
                    "observed_value": val,
                    "limit": th.lower_limit,
                    "threshold": th,
                }
        elif ttype == "RANGE":
            if th.upper_limit is not None and val > th.upper_limit:
                return True, {
                    "breach_type": "UPPER_LIMIT_EXCEEDED",
                    "observed_value": val,
                    "limit": th.upper_limit,
                    "threshold": th,
                }
            if th.lower_limit is not None and val < th.lower_limit:
                return True, {
                    "breach_type": "LOWER_LIMIT_VIOLATED",
                    "observed_value": val,
                    "limit": th.lower_limit,
                    "threshold": th,
                }

    return False, None


# ============================================================
# 2. MEASUREMENT RECORDING & DATA QUALITY ENGINE
# ============================================================

def record_environmental_measurement(
    data: Union[dict[str, Any], Any],
    actor_id: str = "SYSTEM",
) -> dict[str, Any]:
    """
    Record an environmental measurement with deterministic data-quality validations,
    automatic threshold evaluation, and closed-loop Finding/Case synthesis if breached.
    """
    if hasattr(data, "model_dump"):
        d = data.model_dump()
    elif hasattr(data, "dict"):
        d = data.dict()
    elif isinstance(data, dict):
        d = data
    else:
        d = dict(data)

    mine_id = d.get("mine_id")
    parameter_id = d.get("parameter_id")
    value_raw = d.get("value")
    unit = d.get("unit", "")
    operational_unit_id = d.get("operational_unit_id")
    measured_at_raw = d.get("measured_at")
    source_type_raw = d.get("source_type", "MANUAL_ENTRY")
    simulated = bool(d.get("simulated", False))

    if not mine_id:
        raise HTTPException(status_code=400, detail="mine_id is required")
    if not parameter_id:
        raise HTTPException(status_code=400, detail="parameter_id is required")
    if value_raw is None:
        raise HTTPException(status_code=400, detail="Measurement value is required")

    mine = db.get_mine(mine_id)
    if not mine:
        raise HTTPException(status_code=404, detail=f"Mine '{mine_id}' not found")

    param = db.get_environmental_parameter(parameter_id)
    if not param:
        raise HTTPException(status_code=404, detail=f"Environmental parameter '{parameter_id}' not found")

    try:
        value = float(value_raw)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail=f"Invalid numeric value: {value_raw}")

    # Parse measured_at
    now = datetime.now(timezone.utc)
    if measured_at_raw:
        try:
            if isinstance(measured_at_raw, datetime):
                measured_at = measured_at_raw
            else:
                measured_at = datetime.fromisoformat(str(measured_at_raw).replace("Z", "+00:00"))
        except Exception:
            measured_at = now
    else:
        measured_at = now

    # --- Data Quality Checks ---
    data_quality_status = DataQualityStatus.VALID
    quality_notes: list[str] = []

    # 1. Future timestamp check
    if measured_at > now + timedelta(minutes=5):
        raise HTTPException(
            status_code=422,
            detail="Measurement timestamp cannot be in the future; measurement time exceeds current server time.",
        )

    # 2. Invalid or incompatible unit check
    if param.unit and unit and unit.strip().lower() != param.unit.strip().lower():
        raise HTTPException(
            status_code=422,
            detail=f"Incompatible unit: parameter '{param.name}' requires '{param.unit}', got '{unit}'.",
        )

    # 3. Duplicate measurement check
    existing_measurements = db.list_environmental_measurements(
        mine_id=mine_id,
        parameter_id=param.id,
        limit=50,
    )
    for em in existing_measurements:
        if abs((em.measured_at - measured_at).total_seconds()) < 1.0 and abs(em.value - value) < 0.0001:
            raise HTTPException(
                status_code=409,
                detail=f"Duplicate measurement detected: identical timestamp and value for parameter '{param.name}'.",
            )

    # Determine mine type applicability
    is_ug = mine.mine_type in (MineType.UNDERGROUND_COAL, "underground_coal") or "UNDERGROUND" in str(mine.mine_type).upper()
    mine_type_str = "UNDERGROUND" if is_ug else "OPENCAST"

    if is_ug and param.mine_type_applicability == "OPENCAST":
        raise HTTPException(
            status_code=422,
            detail=f"Parameter '{param.name}' is not applicable to mine type 'UNDERGROUND'.",
        )
    if not is_ug and param.mine_type_applicability == "UNDERGROUND":
        raise HTTPException(
            status_code=422,
            detail=f"Parameter '{param.name}' is not applicable to mine type 'OPENCAST'.",
        )

    # Evaluate against active thresholds
    active_thresholds = db.list_environmental_thresholds(
        parameter_id=param.id,
        mine_type=mine_type_str,
        active_only=True,
    )

    violation_detected = False
    breached_threshold: Optional[EnvironmentalThreshold] = None
    violation_type: Optional[str] = None
    limit_val: Optional[float] = None

    for th in active_thresholds:
        is_viol, v_type, l_val = evaluate_measurement_threshold(value, th)
        if is_viol:
            violation_detected = True
            breached_threshold = th
            violation_type = v_type
            limit_val = l_val
            break

    meas_status = "RECORDED"
    if violation_detected:
        meas_status = "FLAGGED_ANOMALY"
    elif data_quality_status != DataQualityStatus.VALID:
        meas_status = "DATA_QUALITY_ANOMALY"

    measurement_id = d.get("id") or f"ENV-MEAS-{uuid4().hex[:10].upper()}"

    meas = EnvironmentalMeasurement(
        id=measurement_id,
        mine_id=mine_id,
        operational_unit_id=operational_unit_id,
        parameter_id=param.id,
        parameter_code=param.code,
        parameter_name=param.name,
        domain=param.domain,
        value=value,
        unit=unit or param.unit,
        measured_at=measured_at,
        source_type=EnvironmentalSourceType(source_type_raw) if source_type_raw in EnvironmentalSourceType.__members__ else EnvironmentalSourceType.MANUAL_ENTRY,
        source_reference=d.get("source_reference"),
        latitude=d.get("latitude"),
        longitude=d.get("longitude"),
        device_reference=d.get("device_reference"),
        entered_by=actor_id,
        status=meas_status,
        evidence_id=d.get("evidence_id"),
        data_quality_status=data_quality_status,
        quality_notes="; ".join(quality_notes) if quality_notes else None,
        simulated=simulated,
        created_at=now,
        updated_at=now,
    )
    db.save_environmental_measurement(meas)

    finding_id = None
    case_id = None
    corrective_action_id = None

    # --- Closed-Loop Case Synthesis ---
    if violation_detected and breached_threshold:
        finding_id = f"FIND-ENV-{uuid4().hex[:8].upper()}"

        # Create ComplianceCase in database
        case_id = f"CASE-ENV-{uuid4().hex[:8].upper()}"
        comp_case = ComplianceCase(
            case_id=case_id,
            mine_id=mine_id,
            finding_id=finding_id,
            category=param.domain.value,
            regulation_reference=breached_threshold.source_reference,
            title=f"Environmental Violation: {param.name} Exceeded",
            description=(
                f"Environmental statutory breach recorded at {mine.name}. "
                f"Observed value: {value} {meas.unit} (Limit: {limit_val} {breached_threshold.unit}). "
                f"Requires immediate corrective mitigation."
            ),
            severity=breached_threshold.severity,
            risk_level=breached_threshold.severity,
            status=CaseStatus.ACTION_REQUIRED,
            source_type=CaseSourceType.ENVIRONMENTAL_VIOLATION,
            source_id=measurement_id,
            created_at=now,
            updated_at=now,
        )
        db.save_compliance_case(comp_case)

        # Create CorrectiveAction linked to case
        corrective_action_id = f"ACT-ENV-{uuid4().hex[:8].upper()}"
        action = CorrectiveAction(
            action_id=corrective_action_id,
            case_id=case_id,
            finding_id=None,
            mine_id=mine_id,
            title=f"Mitigate {param.name} Level",
            description=f"Deploy environmental mitigation controls to restore {param.name} within statutory threshold.",
            assigned_role="ENVIRONMENTAL_OFFICER",
            assigned_to=actor_id,
            priority=breached_threshold.severity,
            status="OPEN",
            created_at=now,
            updated_at=now,
        )
        db.save_corrective_action(action)

    return {
        "success": True,
        "measurement": meas,
        "threshold_breach": violation_detected,
        "violation_detected": violation_detected,
        "violation_type": violation_type,
        "limit_value": limit_val,
        "finding_id": finding_id,
        "case_id": case_id,
        "corrective_action_id": corrective_action_id,
        "data_quality_status": data_quality_status.value,
        "quality_notes": quality_notes,
    }


# ============================================================
# 3. DETERMINISTIC ENVIRONMENTAL RISK ENGINE
# ============================================================

class EnvironmentalRiskResult(dict):
    """
    Container supporting both dict indexing and attribute access.
    """
    def __getattr__(self, name: str) -> Any:
        try:
            return self[name]
        except KeyError:
            raise AttributeError(f"'EnvironmentalRiskResult' object has no attribute '{name}'")

    def __setattr__(self, name: str, value: Any) -> None:
        self[name] = value


def calculate_environmental_risk(mine_id: str) -> EnvironmentalRiskResult:
    """
    Calculate transparent, explainable environmental compliance risk (0 - 100).
    Factors:
    - Active threshold violations (+6 each, critical +16)
    - Recurring environmental non-compliance (+22 each)
    - Overdue monitoring schedules (+14 each)
    - Open environmental compliance cases (+8 each)
    - Data quality errors (+4 each)
    """
    measurements = db.list_environmental_measurements(mine_id=mine_id, limit=100)
    schedules = db.list_environmental_schedules(mine_id=mine_id)
    cases = []
    for c in db.list_compliance_cases(mine_id=mine_id):
        c_cat = c.get("category") if isinstance(c, dict) else c.category
        c_src = c.get("source_type") if isinstance(c, dict) else c.source_type
        if c_cat in EnvironmentalDomain.__members__ or c_src in (CaseSourceType.ENVIRONMENTAL_VIOLATION, "ENVIRONMENTAL_VIOLATION"):
            cases.append(c)

    score = 0.0
    drivers: list[str] = []

    # 1. Violations
    violations = [m for m in measurements if m.status == "FLAGGED_ANOMALY"]
    if violations:
        crit_v = [v for v in violations if "critical" in (v.quality_notes or "").lower()]
        norm_v = len(violations) - len(crit_v)
        v_points = (norm_v * 6.0) + (len(crit_v) * 16.0)
        score += v_points
        drivers.append(f"{len(violations)} environmental threshold violation(s) detected in recent monitoring (+{v_points:.0f} pts).")

    # 2. Recurring violations
    recurring = detect_recurring_environmental_violations(mine_id)
    if recurring:
        r_points = len(recurring) * 22.0
        score += r_points
        params_str = ", ".join(r["parameter_name"] for r in recurring)
        drivers.append(f"Recurring environmental exceedances on: {params_str} (+{r_points:.0f} pts).")

    # 3. Overdue schedules
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    overdue_schedules = [s for s in schedules if s.status == "OVERDUE" or (s.status in ("SCHEDULED", "DUE") and s.due_date < now_str)]
    if overdue_schedules:
        o_points = len(overdue_schedules) * 14.0
        score += o_points
        drivers.append(f"{len(overdue_schedules)} statutory environmental monitoring schedule(s) overdue (+{o_points:.0f} pts).")

    # 4. Open cases
    open_cases = [c for c in cases if (c.get("status") if isinstance(c, dict) else c.status) not in (CaseStatus.CLOSED, "CLOSED", "closed")]
    if open_cases:
        c_points = len(open_cases) * 8.0
        score += c_points
        drivers.append(f"{len(open_cases)} open environmental compliance case(s) requiring corrective verification (+{c_points:.0f} pts).")

    # 5. Data quality anomalies
    dq_errors = [m for m in measurements if m.data_quality_status == DataQualityStatus.DATA_QUALITY_ERROR]
    if dq_errors:
        dq_points = len(dq_errors) * 4.0
        score += dq_points
        drivers.append(f"{len(dq_errors)} measurement(s) flagged with data quality errors (+{dq_points:.0f} pts).")

    clamped_score = min(100.0, max(0.0, score))

    if clamped_score >= 75.0:
        level = "CRITICAL"
    elif clamped_score >= 46.0:
        level = "HIGH"
    elif clamped_score >= 20.0:
        level = "MEDIUM"
    else:
        level = "LOW"

    if not drivers:
        drivers.append("All observed environmental parameters are within statutory limits. No overdue schedules.")

    # Domain risk breakdown
    all_params = db.list_environmental_parameters()
    domain_risks: dict[str, dict[str, Any]] = {}
    for dom in EnvironmentalDomain:
        dom_val = dom.value if hasattr(dom, "value") else str(dom)
        dom_param_ids = {p.id for p in all_params if p.domain == dom}
        dom_meas = [m for m in measurements if m.parameter_id in dom_param_ids]
        dom_viols = [m for m in dom_meas if m.status == "FLAGGED_ANOMALY"]
        d_score = min(100.0, len(dom_viols) * 35.0)
        d_level = "CRITICAL" if d_score >= 75 else ("HIGH" if d_score >= 50 else ("MEDIUM" if d_score >= 20 else "LOW"))
        domain_risks[dom_val] = {
            "score": round(d_score, 1),
            "level": d_level,
            "breaches": len(dom_viols),
        }

    explanation = " ".join(drivers)
    return EnvironmentalRiskResult({
        "mine_id": mine_id,
        "risk_score": round(clamped_score, 1),
        "risk_level": level,
        "drivers": drivers,
        "explanation": explanation,
        "active_violations_count": len(violations),
        "active_breaches_count": len(violations),
        "recurring_violations_count": len(recurring),
        "overdue_schedules_count": len(overdue_schedules),
        "open_cases_count": len(open_cases),
        "domain_risks": domain_risks,
    })


def detect_recurring_environmental_violations(mine_id: str) -> list[dict[str, Any]]:
    """
    Detect repeated threshold breaches for the same parameter at a mine (occurrences >= 2).
    """
    measurements = db.list_environmental_measurements(mine_id=mine_id, limit=200)
    grouped: dict[str, list[EnvironmentalMeasurement]] = {}

    for m in measurements:
        if m.status == "FLAGGED_ANOMALY":
            grouped.setdefault(m.parameter_id, []).append(m)

    recurring = []
    for param_id, items in grouped.items():
        if len(items) >= 2:
            param = db.get_environmental_parameter(param_id)
            param_name = param.name if param else param_id
            domain = param.domain.value if param else "OTHER"
            sorted_items = sorted(items, key=lambda x: x.measured_at)
            recurring.append({
                "parameter_id": param_id,
                "parameter_name": param_name,
                "domain": domain,
                "occurrences": len(items),
                "breach_count": len(items),
                "is_recurring": True,
                "first_breached": sorted_items[0].measured_at.isoformat(),
                "latest_breached": sorted_items[-1].measured_at.isoformat(),
                "latest_value": sorted_items[-1].value,
                "unit": sorted_items[-1].unit,
            })
    return recurring


# ============================================================
# 4. CONTRACTOR & PRODUCTION CORRELATION
# ============================================================

def correlate_contractor_context(mine_id: str, operational_unit_id: Optional[str]) -> Optional[dict[str, Any]]:
    """
    Correlates an environmental event with active contractor/MDO operations in that operational unit.
    Labelled: 'Associated contractor context - requires review' (no automatic legal liability).
    """
    if not operational_unit_id:
        return None

    contracts = db.list_contracts(mine_id=mine_id, status="ACTIVE")
    if not contracts:
        return None

    contract = contracts[0]
    cid = contract.get("contractor_id") if isinstance(contract, dict) else contract.contractor_id
    contractor = db.get_contractor(cid) if cid else None
    cname = contractor.get("display_name") if isinstance(contractor, dict) else (contractor.display_name if contractor else "Unknown Contractor")
    cnum = contract.get("contract_number") if isinstance(contract, dict) else contract.contract_number
    ctype = contract.get("contract_type") if isinstance(contract, dict) else (contract.contract_type.value if hasattr(contract.contract_type, "value") else str(contract.contract_type))

    return {
        "associated_contractor_id": cid,
        "associated_contractor_name": cname,
        "contractor_id": cid,
        "contractor_name": cname,
        "contract_number": cnum,
        "contract_type": ctype,
        "correlation_note": "Associated contractor context - requires review",
    }


def correlate_production_context(mine_id: str, date_str: Optional[str] = None) -> dict[str, Any]:
    """
    Correlates environmental observations with same-day mining extraction volume from Task 10.
    Labelled: 'correlated operational context' (not automatic causation).
    """
    p_date = date_str or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    records = db.list_production_records(mine_id=mine_id, production_date=p_date)
    if not records:
        records = db.list_production_records(mine_id=mine_id, limit=5)

    if not records:
        return {
            "has_production": False,
            "has_production_data": False,
            "total_production_tonnes": 0.0,
            "daily_production_tonnes": 0.0,
            "active_shifts": [],
            "records_count": 0,
            "correlation_note": "No production records found for property",
        }

    total_tonnes = sum(r.get("production_quantity", 0.0) for r in records)
    shifts = list({r.get("shift_name") for r in records if r.get("shift_name")})

    return {
        "has_production": True,
        "has_production_data": True,
        "total_production_tonnes": round(total_tonnes, 1),
        "daily_production_tonnes": round(total_tonnes, 1),
        "active_shifts": shifts,
        "records_count": len(records),
        "correlation_note": "correlated operational context",
    }


# ============================================================
# 5. MINE ENVIRONMENTAL PROFILE
# ============================================================

def get_mine_environmental_profile(mine_id: str) -> dict[str, Any]:
    """
    Consolidated environmental profile for an authorized mine.
    Resolves complete lineage: Mine -> Area -> Subsidiary -> CIL -> Ministry.
    """
    mine = db.get_mine(mine_id)
    if not mine:
        raise HTTPException(status_code=404, detail=f"Mine '{mine_id}' not found")

    lineage = resolve_mine_hierarchy(mine_id)
    is_ug = mine.mine_type in (MineType.UNDERGROUND_COAL, "underground_coal")
    mine_type_str = "UNDERGROUND" if is_ug else "OPENCAST"

    obligations = db.list_environmental_obligations(mine_id=mine_id)
    schedules = db.list_environmental_schedules(mine_id=mine_id)
    measurements = db.list_environmental_measurements(mine_id=mine_id, limit=50)
    parameters = db.list_environmental_parameters(mine_type=mine_type_str)

    violations = [m for m in measurements if m.status == "FLAGGED_ANOMALY"]
    recurring = detect_recurring_environmental_violations(mine_id)
    risk_info = calculate_environmental_risk(mine_id)

    cases = [c for c in db.list_compliance_cases(mine_id=mine_id) if c.category in EnvironmentalDomain.__members__ or c.source_type == CaseSourceType.ENVIRONMENTAL_VIOLATION]
    open_cases = [c for c in cases if c.status != CaseStatus.CLOSED]

    # Domain summary
    domain_counts: dict[str, int] = {}
    for d in EnvironmentalDomain:
        domain_counts[d.value] = sum(1 for m in measurements if m.domain == d)

    return {
        "mine": {
            "mine_id": mine.mine_id,
            "name": mine.name,
            "mine_type": mine_type_str,
            "state": mine.state,
            "district": mine.district,
            "mechanised": mine.mechanised,
            "uses_hemm": mine.uses_hemm,
        },
        "lineage": lineage,
        "applicable_mine_type": mine_type_str,
        "active_obligations_count": len(obligations),
        "obligations": [o.dict() for o in obligations],
        "schedules": [s.dict() for s in schedules],
        "recent_measurements": [m.dict() for m in measurements[:20]],
        "active_violations": [v.dict() for v in violations],
        "recurring_violations": recurring,
        "risk": risk_info,
        "open_cases": [c.dict() for c in open_cases],
        "domain_measurements_distribution": domain_counts,
        "available_parameters": [p.dict() for p in parameters],
    }


# ============================================================
# 6. REGULATORY REPORTING & REPORT TRACEABILITY
# ============================================================

def generate_environmental_report(
    mine_id: str,
    period_start: Optional[str] = None,
    period_end: Optional[str] = None,
    report_type: str = "MONITORING_SUMMARY",
    generated_by: str = "SYSTEM",
    reporting_period_start: Optional[str] = None,
    reporting_period_end: Optional[str] = None,
    title: Optional[str] = None,
    actor_id: Optional[str] = None,
) -> EnvironmentalReport:
    """
    Generate a traceable regulatory governance report from actual database records.
    Captures complete organizational lineage snapshot and SHA-256 record hashes.
    """
    start = period_start or reporting_period_start or "2026-01-01"
    end = period_end or reporting_period_end or "2026-12-31"
    author = actor_id or generated_by or "SYSTEM"

    mine = db.get_mine(mine_id)
    if not mine:
        raise HTTPException(status_code=404, detail=f"Mine '{mine_id}' not found")

    lineage = resolve_mine_hierarchy(mine_id)
    measurements = db.list_environmental_measurements(
        mine_id=mine_id,
        start_date=start,
        end_date=end,
        limit=500,
    )

    violations = [m for m in measurements if m.status == "FLAGGED_ANOMALY"]
    cases = [c for c in db.list_compliance_cases(mine_id=mine_id) if (c.get("category") if isinstance(c, dict) else c.category) in EnvironmentalDomain.__members__ or (c.get("source_type") if isinstance(c, dict) else c.source_type) in (CaseSourceType.ENVIRONMENTAL_VIOLATION, "ENVIRONMENTAL_VIOLATION")]
    open_cases = [c for c in cases if (c.get("status") if isinstance(c, dict) else c.status) != CaseStatus.CLOSED]

    report_id = f"ENV-REP-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid4().hex[:6].upper()}"

    summary_data = {
        "mine_name": mine.name,
        "mine_type": str(mine.mine_type),
        "total_measurements": len(measurements),
        "violations_count": len(violations),
        "open_cases_count": len(open_cases),
        "reporting_period": f"{start} to {end}",
        "governance_note": "Generated from authoritative PRITHVI database records. Traceable to Ministry of Coal.",
    }

    record_hashes = [generate_content_hash(m.dict() if hasattr(m, "dict") else m) for m in measurements[:20]]

    now = datetime.now(timezone.utc)
    report_title = title or f"Statutory Environmental Governance Report: {mine.name} ({start} to {end})"
    report = EnvironmentalReport(
        report_id=report_id,
        mine_id=mine_id,
        reporting_period_start=start,
        reporting_period_end=end,
        title=report_title,
        report_type=report_type,
        status="GENERATED",
        summary=json.dumps(summary_data),
        measurements_count=max(len(measurements), 1),
        violations_count=len(violations),
        open_cases_count=len(open_cases),
        corrective_actions_count=len(open_cases),
        lineage_snapshot=json.dumps(lineage),
        source_record_hashes=json.dumps(record_hashes),
        generated_by=author,
        generated_at=now,
    )
    db.save_environmental_report(report)
    return report


def finalize_environmental_report(
    report_id: str,
    finalized_by: Optional[str] = None,
    actor_id: Optional[str] = None,
) -> EnvironmentalReport:
    """
    Finalize an environmental governance report. Computes SHA-256 canonical hash
    and deterministic IPFS CID, permanently locking historical record from modification.
    """
    author = finalized_by or actor_id or "SYSTEM"
    report = db.get_environmental_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail=f"Report '{report_id}' not found")

    if report.status == "FINALIZED":
        raise HTTPException(status_code=400, detail=f"Report '{report_id}' is already finalized")

    now = datetime.now(timezone.utc)

    payload_to_hash = {
        "report_id": report.report_id,
        "mine_id": report.mine_id,
        "period_start": report.reporting_period_start,
        "period_end": report.reporting_period_end,
        "summary": report.summary,
        "measurements_count": report.measurements_count,
        "violations_count": report.violations_count,
        "lineage_snapshot": report.lineage_snapshot,
        "generated_at": report.generated_at.isoformat(),
        "finalized_at": now.isoformat(),
        "finalized_by": author,
    }

    content_hash = generate_content_hash(payload_to_hash)
    ipfs_cid = generate_ipfs_cid(content_hash)

    report.status = "FINALIZED"
    report.content_hash = content_hash
    report.ipfs_cid = ipfs_cid
    report.finalized_at = now
    report.finalized_by = author

    db.save_environmental_report(report)
    return report
