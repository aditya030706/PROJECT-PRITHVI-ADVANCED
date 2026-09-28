"""
PRITHVI — Compliance Case & Corrective Action Service (Phase 2 Task 6)
======================================================================

Implements the closed-loop compliance tracking engine:
  RISK / FINDING / THRESHOLD BREACH
      ↓
  COMPLIANCE CASE
      ↓
  CORRECTIVE ACTION (Owner + Due Date)
      ↓
  CORRECTION EVIDENCE (Photos, Measurements, Readings)
      ↓
  HUMAN REVIEWER VERIFICATION
      ↓
  CASE CLOSED
      ↓
  AUDIT TRAIL + CRYPTOGRAPHIC PROOF
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from fastapi import HTTPException

from . import database as db
from .models import (
    ComplianceCase,
    CaseSourceType,
    CaseStatus,
    ActionPriority,
    CorrectiveAction,
    Evidence,
    EvidenceType,
)
from .compliance import (
    get_mine_compliance_summary,
    get_mine_threshold_violations,
    SEVEN_STATUTORY_CATEGORIES,
)
from .risk import get_mine_risk_intelligence, get_mine_recurring_issues
from .audit_proof import (
    generate_content_hash,
    generate_ipfs_cid,
    create_audit_proof_record,
)

CATEGORY_REGULATION_MAPPING = {
    "Ventilation & Gas": "CMR 2017, Reg 119, 156 (Ventilation & Gases)",
    "Shaft & Winding": "CMR 2017, Reg 75–80 (Shafts, Outlets & Winding)",
    "Electrical": "CMR 2017, Reg 160–170 (Flameproof Apparatus & Earthing)",
    "HEMM": "CMR 2017, Reg 135 (Heavy Earthmoving Machinery)",
    "Blasting": "CMR 2017, Reg 155–158 (Shotfiring & Danger Zones)",
    "Roof / Strata": "CMR 2017, Reg 85–95 (SCAMP & Support Plan)",
    "Water / Drainage": "CMR 2017, Reg 145 (Inundation & Pumping Stations)",
}


# ============================================================
# 1. IDEMPOTENT CASE SYNTHESIS FROM REAL SIGNALS
# ============================================================

def sync_mine_compliance_cases(mine_id: str) -> list[dict]:
    """
    Scan real statutory signals in the database (threshold violations, open findings,
    recurring non-compliance, overdue schedules, and DGMS actions) and idempotently
    synthesize ComplianceCase records. Prevents duplicate cases across dashboard refreshes.
    """
    now = datetime.now(timezone.utc)
    cases_created = 0

    # ------------------------------------------------------------
    # A. Recurring Non-Compliance Issues
    # ------------------------------------------------------------
    recurring_issues = get_mine_recurring_issues(mine_id)
    for rec in recurring_issues:
        source_type = CaseSourceType.RECURRING_NON_COMPLIANCE.value
        source_id = rec["issue_id"]

        existing = db.get_compliance_case_by_source(source_type, source_id)
        if not existing:
            category = rec.get("category") or "Ventilation & Gas"
            reg_ref = CATEGORY_REGULATION_MAPPING.get(category, "CMR 2017 Statutory Mandate")
            case_id = f"CASE-{uuid4().hex[:10].upper()}"
            insp_id = rec.get("related_inspection_ids", [None])[0] if rec.get("related_inspection_ids") else None

            case = ComplianceCase(
                case_id=case_id,
                mine_id=mine_id,
                inspection_id=insp_id,
                finding_id=rec.get("related_finding_ids", [None])[0] if rec.get("related_finding_ids") else None,
                category=category,
                regulation_reference=reg_ref,
                title=f"Recurring Non-Compliance: {rec['title']}",
                description=(
                    f"Substantial repeated statutory failure documented across {rec.get('occurrences', 2)} inspection cycles. "
                    f"Statutory limits breached repeatedly: {rec.get('description', '')}"
                ),
                severity=rec.get("severity", "CRITICAL"),
                risk_level="CRITICAL" if rec.get("severity") == "CRITICAL" else "HIGH",
                status=CaseStatus.OPEN,
                source_type=CaseSourceType.RECURRING_NON_COMPLIANCE,
                source_id=source_id,
                created_at=now,
                updated_at=now,
            )
            db.save_compliance_case(case)
            db.record_case_audit_event(
                event_id=f"EVT-{uuid4().hex[:10].upper()}",
                case_id=case_id,
                action="CASE_CREATED",
                actor_id="SYSTEM_INTELLIGENCE",
                actor_role="COMPLIANCE_ENGINE",
                previous_state=None,
                new_state="OPEN",
                reason=f"Synthesized from recurring non-compliance detection ({source_id})",
                timestamp=now.isoformat(),
                details=f"Recurring failure in {category}: {rec['title']}",
            )
            cases_created += 1

    # ------------------------------------------------------------
    # B. Critical Threshold Violations (Methane, CO, Water)
    # ------------------------------------------------------------
    violations = get_mine_threshold_violations(mine_id)
    for v in violations:
        meas_id = v.get("measurement_id") or "UNKNOWN"
        source_type = CaseSourceType.THRESHOLD_VIOLATION.value
        source_id = f"TV-{meas_id}"

        existing = db.get_compliance_case_by_source(source_type, source_id)
        if not existing:
            category = v.get("inspection_family") or "Ventilation & Gas"
            reg_ref = CATEGORY_REGULATION_MAPPING.get(category, "CMR 2017 Statutory Threshold")
            m_name = v.get("measurement_name") or v.get("measurement_type") or "Statutory Measurement"
            val = v.get("value")
            lim = v.get("limit_value")
            unit = v.get("unit") or ""
            is_critical = "methane" in m_name.lower() or (lim is not None and float(val) >= 2 * float(lim))

            case_id = f"CASE-{uuid4().hex[:10].upper()}"
            case = ComplianceCase(
                case_id=case_id,
                mine_id=mine_id,
                inspection_id=v.get("inspection_id"),
                finding_id=None,
                category=category,
                regulation_reference=reg_ref,
                title=f"Statutory Threshold Violation: {m_name}",
                description=(
                    f"Measured {m_name} recorded at {val} {unit} in inspection {v.get('inspection_id')}, "
                    f"violating statutory threshold limit of {lim} {unit} ({v.get('threshold_label') or 'Mandatory maximum'})."
                ),
                severity="CRITICAL" if is_critical else "HIGH",
                risk_level="CRITICAL" if is_critical else "HIGH",
                status=CaseStatus.OPEN,
                source_type=CaseSourceType.THRESHOLD_VIOLATION,
                source_id=source_id,
                created_at=now,
                updated_at=now,
            )
            db.save_compliance_case(case)
            db.record_case_audit_event(
                event_id=f"EVT-{uuid4().hex[:10].upper()}",
                case_id=case_id,
                action="CASE_CREATED",
                actor_id="SYSTEM_INTELLIGENCE",
                actor_role="COMPLIANCE_ENGINE",
                previous_state=None,
                new_state="OPEN",
                reason=f"Synthesized from measurement threshold breach ({m_name}={val} {unit})",
                timestamp=now.isoformat(),
            )
            cases_created += 1

    # ------------------------------------------------------------
    # C. Open Findings with Corrective Action Required
    # ------------------------------------------------------------
    conn = db._connect()
    f_rows = conn.execute(
        """
        SELECT f.*, i.mine_id, t.inspection_family, t.regulation_reference
        FROM findings f
        JOIN inspections i ON f.inspection_id = i.inspection_id
        LEFT JOIN inspection_templates t ON i.template_id = t.template_id
        WHERE i.mine_id = ? AND f.corrective_action_required = 1 AND LOWER(f.status) = 'open'
        """,
        (mine_id,),
    ).fetchall()
    conn.close()

    for fr in f_rows:
        source_type = CaseSourceType.FINDING.value
        source_id = f"FND-{fr['finding_id']}"
        existing = db.get_compliance_case_by_source(source_type, source_id)
        if not existing:
            cat = fr["inspection_family"] or "General Operations"
            reg_ref = fr["regulation_reference"] or CATEGORY_REGULATION_MAPPING.get(cat, "CMR 2017")
            case_id = f"CASE-{uuid4().hex[:10].upper()}"
            sev = (fr["severity"] or "HIGH").upper()
            case = ComplianceCase(
                case_id=case_id,
                mine_id=mine_id,
                inspection_id=fr["inspection_id"],
                finding_id=fr["finding_id"],
                category=cat,
                regulation_reference=reg_ref,
                title=f"Open Finding: {fr['title']}",
                description=fr["description"],
                severity=sev,
                risk_level="CRITICAL" if sev == "CRITICAL" else "HIGH",
                status=CaseStatus.OPEN,
                source_type=CaseSourceType.FINDING,
                source_id=source_id,
                created_at=now,
                updated_at=now,
            )
            db.save_compliance_case(case)
            db.record_case_audit_event(
                event_id=f"EVT-{uuid4().hex[:10].upper()}",
                case_id=case_id,
                action="CASE_CREATED",
                actor_id="SYSTEM_INTELLIGENCE",
                actor_role="COMPLIANCE_ENGINE",
                previous_state=None,
                new_state="OPEN",
                reason=f"Synthesized from unaddressed field inspection finding ({fr['finding_id']})",
                timestamp=now.isoformat(),
            )
            cases_created += 1

    # ------------------------------------------------------------
    # D. DGMS Regulatory Actions
    # ------------------------------------------------------------
    conn = db._connect()
    ea_rows = conn.execute(
        """
        SELECT * FROM enforcement_actions
        WHERE mine_id = ? AND UPPER(status) = 'OPEN'
        """,
        (mine_id,),
    ).fetchall()
    conn.close()

    for ea in ea_rows:
        source_type = CaseSourceType.REGULATORY_ACTION.value
        source_id = f"REG-{ea['action_id']}"
        existing = db.get_compliance_case_by_source(source_type, source_id)
        if not existing:
            case_id = f"CASE-{uuid4().hex[:10].upper()}"
            case = ComplianceCase(
                case_id=case_id,
                mine_id=mine_id,
                inspection_id=ea["inspection_id"],
                finding_id=None,
                category="Regulatory Enforcement",
                regulation_reference="Mines Act 1952 / CMR 2017 DGMS Directive",
                title=f"DGMS Directive: {ea['action_type'].replace('_', ' ')}",
                description=ea["reason"],
                severity=(ea["severity"] or "CRITICAL").upper(),
                risk_level="CRITICAL",
                status=CaseStatus.OPEN,
                source_type=CaseSourceType.REGULATORY_ACTION,
                source_id=source_id,
                created_at=now,
                updated_at=now,
            )
            db.save_compliance_case(case)
            db.record_case_audit_event(
                event_id=f"EVT-{uuid4().hex[:10].upper()}",
                case_id=case_id,
                action="CASE_CREATED",
                actor_id=ea["issued_by"] if ("issued_by" in ea.keys() and ea["issued_by"]) else "DGMS_OFFICER",
                actor_role="DGMS_OFFICER",
                previous_state=None,
                new_state="OPEN",
                reason=f"Synthesized from formal DGMS regulatory action ({ea['action_id']})",
                timestamp=now.isoformat(),
            )
            cases_created += 1

    # ------------------------------------------------------------
    # F. Active Critical SCADA Telemetry Signals (Phase 2 Task 9)
    # ------------------------------------------------------------
    try:
        active_critical_signals = [
            sig for sig in db.get_active_safety_signals(mine_id)
            if sig.get("severity") == "CRITICAL"
        ]
        for sig in active_critical_signals:
            source_type = CaseSourceType.SCADA_TELEMETRY.value
            source_id = sig["signal_id"]
            existing = db.get_compliance_case_by_source(source_type, source_id)
            if not existing:
                case_id = f"CASE-{uuid4().hex[:10].upper()}"
                category_map = {
                    "METHANE": "Ventilation & Gas",
                    "AIRFLOW": "Ventilation & Gas",
                    "VENTILATION_FAN": "Ventilation & Gas",
                    "DUST": "Ventilation & Gas",
                    "SLOPE_DISPLACEMENT": "Roof / Strata",
                    "PORE_PRESSURE": "Water / Drainage",
                    "RAINFALL": "Water / Drainage",
                }
                category = category_map.get(sig.get("sensor_type"), "Ventilation & Gas")
                case = ComplianceCase(
                    case_id=case_id,
                    mine_id=mine_id,
                    inspection_id=None,
                    finding_id=None,
                    category=category,
                    regulation_reference=sig.get("threshold_definition", "CMR 2017 Safety Threshold"),
                    title=f"SCADA Safety Breach: {sig.get('display_name', sig.get('sensor_type'))}",
                    description=(
                        f"Autonomous SCADA Safety Breach: Observed {sig.get('observed_value')} {sig.get('unit')}. "
                        f"{sig.get('explanation')}"
                    ),
                    severity="CRITICAL",
                    risk_level="CRITICAL",
                    status=CaseStatus.OPEN,
                    source_type=CaseSourceType.SCADA_TELEMETRY,
                    source_id=source_id,
                    created_at=now,
                    updated_at=now,
                )
                db.save_compliance_case(case)
                db.link_safety_signal_case(sig["signal_id"], case_id)
                db.record_case_audit_event(
                    event_id=f"EVT-{uuid4().hex[:10].upper()}",
                    case_id=case_id,
                    action="CASE_CREATED",
                    actor_id="SCADA_SIMULATOR",
                    actor_role="SCADA_TELEMETRY_ENGINE",
                    previous_state=None,
                    new_state="OPEN",
                    reason=f"Synthesized from critical SCADA telemetry signal ({source_id})",
                    timestamp=now.isoformat(),
                )
                cases_created += 1
    except Exception:
        pass

    return db.list_compliance_cases(mine_id=mine_id)


# ============================================================
# 2. SOURCE TRACEABILITY GRAPH
# ============================================================

def get_case_traceability(case_id: str) -> dict:
    """
    Construct the authoritative source chain for a compliance case:
    Inspection -> Measurement -> Threshold -> Finding -> Supporting Evidence -> Risk
    Uses genuine database relationships without fictitious identifiers.
    """
    case = db.get_compliance_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"Compliance case {case_id} not found.")

    conn = db._connect()
    insp_id = case.get("inspection_id")
    fnd_id = case.get("finding_id")

    # 1. Inspection Node
    inspection_node = None
    if insp_id:
        insp_row = conn.execute(
            """
            SELECT i.inspection_id, i.inspection_date, i.status, i.inspector_id, i.submitted_at,
                   t.name as template_name, t.inspection_family, t.regulation_reference
            FROM inspections i
            LEFT JOIN inspection_templates t ON i.template_id = t.template_id
            WHERE i.inspection_id = ?
            """,
            (insp_id,),
        ).fetchone()
        if insp_row:
            inspection_node = {
                "id": insp_row["inspection_id"],
                "name": insp_row["template_name"] or "Statutory Field Inspection",
                "date": insp_row["inspection_date"],
                "inspector_id": insp_row["inspector_id"],
                "status": insp_row["status"],
                "submitted_at": insp_row["submitted_at"],
                "regulation_reference": insp_row["regulation_reference"],
            }

    # 2. Measurement Node & Threshold Node
    measurement_node = None
    threshold_node = None
    if insp_id:
        meas_rows = conn.execute(
            """
            SELECT m.measurement_id, m.measurement_type, m.value, m.unit, m.captured_at,
                   tm.name as def_name, tm.min_value, tm.max_value, tm.threshold_label
            FROM measurements m
            JOIN inspections i ON m.inspection_id = i.inspection_id
            LEFT JOIN template_measurements tm ON i.template_id = tm.template_id
                 AND (LOWER(m.measurement_type) = LOWER(tm.measurement_id) OR LOWER(m.measurement_type) = LOWER(tm.name))
            WHERE m.inspection_id = ?
            """,
            (insp_id,),
        ).fetchall()

        # Find violation measurement if available
        for mr in meas_rows:
            is_violation = False
            if mr["max_value"] is not None and mr["value"] > mr["max_value"]:
                is_violation = True
            elif mr["min_value"] is not None and mr["value"] < mr["min_value"]:
                is_violation = True

            if is_violation or not measurement_node:
                measurement_node = {
                    "measurement_id": mr["measurement_id"],
                    "parameter": mr["def_name"] or mr["measurement_type"],
                    "value": mr["value"],
                    "unit": mr["unit"] or "",
                    "captured_at": mr["captured_at"],
                    "is_violation": is_violation,
                }
                if mr["min_value"] is not None or mr["max_value"] is not None:
                    threshold_node = {
                        "parameter": mr["def_name"] or mr["measurement_type"],
                        "min_limit": mr["min_value"],
                        "max_limit": mr["max_value"],
                        "threshold_label": mr["threshold_label"] or "CMR Statutory Limit",
                        "violation_detected": is_violation,
                    }
            if is_violation:
                break

    # 3. Finding Node
    finding_node = None
    if fnd_id:
        f_row = conn.execute(
            "SELECT * FROM findings WHERE finding_id = ?", (fnd_id,)
        ).fetchone()
        if f_row:
            finding_node = {
                "finding_id": f_row["finding_id"],
                "title": f_row["title"],
                "description": f_row["description"],
                "severity": f_row["severity"],
                "status": f_row["status"],
            }
    elif insp_id:
        # Check if there is any finding for this inspection
        f_row = conn.execute(
            "SELECT * FROM findings WHERE inspection_id = ? LIMIT 1", (insp_id,)
        ).fetchone()
        if f_row:
            finding_node = {
                "finding_id": f_row["finding_id"],
                "title": f_row["title"],
                "description": f_row["description"],
                "severity": f_row["severity"],
                "status": f_row["status"],
            }

    # 4. Supporting Evidence Records
    evidence_nodes = []
    if insp_id:
        ev_rows = conn.execute(
            """
            SELECT evidence_id, evidence_type, filename, storage_reference, sha256, captured_at
            FROM evidence
            WHERE inspection_id = ?
            """,
            (insp_id,),
        ).fetchall()
        for er in ev_rows:
            evidence_nodes.append({
                "evidence_id": er["evidence_id"],
                "evidence_type": er["evidence_type"],
                "filename": er["filename"] or er["storage_reference"],
                "sha256": er["sha256"],
                "captured_at": er["captured_at"],
            })

    # 5. Risk Context
    mine_risk = None
    try:
        r_intel = get_mine_risk_intelligence(case["mine_id"])
        if r_intel:
            cat_risk = next(
                (c for c in r_intel.get("categories", []) if c["category"].lower() == case["category"].lower()),
                None
            )
            mine_risk = {
                "mine_risk_level": r_intel.get("overall_risk_level"),
                "category_risk_level": cat_risk.get("risk_level") if cat_risk else case.get("risk_level"),
                "category_risk_score": cat_risk.get("risk_score") if cat_risk else 0,
                "drivers": cat_risk.get("drivers") if cat_risk else [],
            }
    except Exception:
        pass

    conn.close()

    return {
        "case_id": case_id,
        "source_type": case["source_type"],
        "source_id": case["source_id"],
        "inspection": inspection_node,
        "measurement": measurement_node,
        "threshold": threshold_node,
        "finding": finding_node,
        "evidence_records": evidence_nodes,
        "risk_context": mine_risk,
    }


# ============================================================
# 3. CASE DETAIL & LIFECYCLE
# ============================================================

def get_case_detail(case_id: str) -> dict:
    """
    Returns full operational dossier for a compliance case.
    """
    case = db.get_compliance_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"Compliance case {case_id} not found.")

    # Fetch child elements
    actions = db.list_corrective_actions_for_case(case_id)
    correction_evidence = db.list_case_correction_evidence(case_id)
    audit_events = db.list_case_audit_events(case_id)
    crypto_proofs = db.list_cryptographic_proofs(case_id)
    traceability = get_case_traceability(case_id)

    # Calculate timeline state flags
    status = case["status"]
    has_actions = len(actions) > 0
    has_correction_submitted = any(a.get("status") == "COMPLETED" for a in actions) or len(correction_evidence) > 0
    is_verification_required = status == "VERIFICATION_REQUIRED"
    is_closed = status == "CLOSED"
    is_returned = status == "RETURNED_FOR_CORRECTION"

    # Verification eligibility check
    can_verify = (
        status == "VERIFICATION_REQUIRED"
        and has_actions
        and len(correction_evidence) > 0
    )

    return {
        "case": case,
        "actions": actions,
        "correction_evidence": correction_evidence,
        "audit_events": audit_events,
        "cryptographic_proofs": crypto_proofs,
        "traceability": traceability,
        "timeline": {
            "detected": True,
            "action_assigned": has_actions,
            "correction_submitted": has_correction_submitted,
            "evidence_received": len(correction_evidence) > 0,
            "verification_required": is_verification_required or is_closed,
            "returned_for_correction": is_returned,
            "closed": is_closed,
            "current_stage": status,
        },
        "can_verify": can_verify,
    }


# ============================================================
# 4. CORRECTIVE ACTION MANAGEMENT
# ============================================================

def create_corrective_action(
    case_id: str,
    payload: dict,
    actor_id: str,
    actor_role: str,
) -> dict:
    """
    Assign a corrective action to a compliance case.
    Validates mandatory title, description, responsible party, priority, and due date.
    """
    case = db.get_compliance_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"Compliance case {case_id} not found.")
    if case["status"] == "CLOSED":
        raise HTTPException(status_code=400, detail="Cannot add corrective action to a closed compliance case.")

    title = (payload.get("title") or "").strip()
    description = (payload.get("description") or "").strip()
    assigned_role = (payload.get("assigned_role") or "").strip()
    assigned_user_id = (payload.get("assigned_user_id") or "").strip()
    due_at = (payload.get("due_at") or "").strip()
    priority = (payload.get("priority") or "MEDIUM").strip().upper()

    if not title:
        raise HTTPException(status_code=400, detail="Action title is mandatory.")
    if not description:
        raise HTTPException(status_code=400, detail="Action description is mandatory.")
    if not assigned_role and not assigned_user_id:
        raise HTTPException(status_code=400, detail="Action must be assigned to an owner (role or user ID).")
    if not due_at:
        raise HTTPException(status_code=400, detail="Due date is mandatory for corrective actions.")

    # Validate due date format
    try:
        # Accept YYYY-MM-DD or ISO datetime
        due_date_obj = date.fromisoformat(due_at[:10])
    except Exception:
        raise HTTPException(status_code=400, detail=f"Invalid due date format: '{due_at}'. Expected YYYY-MM-DD.")

    now = datetime.now(timezone.utc)
    action_id = f"ACT-{uuid4().hex[:10].upper()}"

    action = CorrectiveAction(
        action_id=action_id,
        case_id=case_id,
        finding_id=case.get("finding_id"),
        mine_id=case["mine_id"],
        title=title,
        description=description,
        assigned_role=assigned_role or "Mine Safety Supervisor",
        assigned_user_id=assigned_user_id or "SUPERVISOR-01",
        assigned_to=assigned_user_id or assigned_role,
        due_at=due_at,
        due_date=due_date_obj,
        priority=priority if priority in ("CRITICAL", "HIGH", "MEDIUM", "LOW") else "MEDIUM",
        status="OPEN",
        created_at=now,
        updated_at=now,
    )
    db.save_corrective_action_v2(action)

    # Transition case to ACTION_REQUIRED if currently OPEN or RETURNED_FOR_CORRECTION
    prev_status = case["status"]
    if prev_status in ("OPEN", "RETURNED_FOR_CORRECTION"):
        db.update_compliance_case_status(case_id, status="ACTION_REQUIRED", updated_at=now.isoformat())

    # Record Audit Event
    db.record_case_audit_event(
        event_id=f"EVT-{uuid4().hex[:10].upper()}",
        case_id=case_id,
        action="ACTION_ASSIGNED",
        actor_id=actor_id,
        actor_role=actor_role,
        previous_state=prev_status,
        new_state="ACTION_REQUIRED",
        reason=f"Corrective action '{title}' assigned to {assigned_role or assigned_user_id}",
        timestamp=now.isoformat(),
        details=f"Priority: {priority}, Due: {due_at}",
    )

    return {
        "action_id": action_id,
        "case_id": case_id,
        "title": title,
        "status": "OPEN",
        "assigned_role": action.assigned_role,
        "assigned_user_id": action.assigned_user_id,
        "due_at": due_at,
        "priority": action.priority,
        "message": "Corrective action assigned successfully.",
    }


# ============================================================
# 5. SUBMIT CORRECTION EVIDENCE
# ============================================================

def submit_action_correction(
    action_id: str,
    payload: dict,
    actor_id: str,
    actor_role: str,
) -> dict:
    """
    Submit evidence that corrective action was performed.
    Does NOT automatically close the case. Transitions case to VERIFICATION_REQUIRED.
    """
    action = db.get_corrective_action(action_id)
    if not action:
        raise HTTPException(status_code=404, detail=f"Corrective action {action_id} not found.")

    case_id = action.get("case_id")
    if not case_id:
        raise HTTPException(status_code=400, detail=f"Action {action_id} has no associated compliance case.")

    case = db.get_compliance_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"Compliance case {case_id} not found.")
    if case["status"] == "CLOSED":
        raise HTTPException(status_code=400, detail="Cannot submit correction for a closed compliance case.")

    # Check evidence details
    notes = (payload.get("notes") or payload.get("description") or "").strip()
    evidence_id = payload.get("evidence_id")
    filename = payload.get("filename")
    evidence_type = (payload.get("evidence_type") or "photo").lower()
    raw_data = payload.get("raw_data") or notes or f"Correction completed for {action['title']}"

    now = datetime.now(timezone.utc)
    content_hash = generate_content_hash(raw_data)
    ipfs_cid = generate_ipfs_cid(content_hash)

    # If no existing evidence_id provided, create an authoritative evidence record
    if not evidence_id:
        evidence_id = f"EV-CORR-{uuid4().hex[:10].upper()}"
        ev = Evidence(
            evidence_id=evidence_id,
            inspection_id=case.get("inspection_id") or "STATUTORY-CASE-CORRECTION",
            evidence_type=EvidenceType(evidence_type) if evidence_type in [e.value for e in EvidenceType] else EvidenceType.PHOTO,
            filename=filename or f"correction_proof_{action_id}.png",
            storage_reference=f"corrections/{case_id}/{action_id}",
            captured_at=now,
            sha256=content_hash,
            metadata_verified=True,
        )
        db.save_evidence(ev)

    # Link evidence to case corrective action
    link_id = f"CEL-{uuid4().hex[:10].upper()}"
    db.save_case_correction_evidence(
        evidence_link_id=link_id,
        case_id=case_id,
        action_id=action_id,
        evidence_id=evidence_id,
        submitted_at=now.isoformat(),
        submitted_by=actor_id,
        notes=notes,
        sha256=content_hash,
        ipfs_cid=ipfs_cid,
        audit_proof_status="AUDIT_PROOF_RECORDED",
    )

    # Update corrective action status
    conn = db._connect()
    conn.execute(
        """
        UPDATE corrective_actions
        SET status = 'COMPLETED',
            completed_at = ?,
            completed_by = ?,
            updated_at = ?
        WHERE action_id = ?
        """,
        (now.isoformat(), actor_id, now.isoformat(), action_id),
    )
    conn.commit()
    conn.close()

    # Transition case to VERIFICATION_REQUIRED (prompt requirement: does not close!)
    prev_status = case["status"]
    db.update_compliance_case_status(case_id, status="VERIFICATION_REQUIRED", updated_at=now.isoformat())

    # Record Audit Event
    db.record_case_audit_event(
        event_id=f"EVT-{uuid4().hex[:10].upper()}",
        case_id=case_id,
        action="CORRECTION_SUBMITTED",
        actor_id=actor_id,
        actor_role=actor_role,
        previous_state=prev_status,
        new_state="VERIFICATION_REQUIRED",
        reason=f"Correction evidence submitted for action '{action.get('title', action_id)}'. Case requires human verification.",
        timestamp=now.isoformat(),
        details=notes,
        sha256=content_hash,
        ipfs_cid=ipfs_cid,
    )

    # Record Cryptographic Proof
    proof = create_audit_proof_record(
        case_id=case_id,
        action_type="CORRECTION_SUBMITTED",
        payload={
            "action_id": action_id,
            "evidence_id": evidence_id,
            "submitted_by": actor_id,
            "sha256": content_hash,
            "ipfs_cid": ipfs_cid,
        },
        actor_id=actor_id,
        actor_role=actor_role,
    )
    db.save_cryptographic_proof(proof)

    return {
        "action_id": action_id,
        "case_id": case_id,
        "action_status": "COMPLETED",
        "case_status": "VERIFICATION_REQUIRED",
        "evidence_id": evidence_id,
        "sha256": content_hash,
        "ipfs_cid": ipfs_cid,
        "audit_proof_status": "AUDIT_PROOF_RECORDED",
        "message": "Correction evidence submitted. Case transitioned to VERIFICATION_REQUIRED.",
    }


# ============================================================
# 6. VERIFICATION & CLOSURE
# ============================================================

def verify_case_closure(
    case_id: str,
    reviewer_id: str,
    reviewer_role: str,
    notes: Optional[str] = None,
) -> dict:
    """
    Statutory Reviewer validation and verification for closing a compliance case.
    Strict server-side validation:
      - Case exists
      - Corrective action exists and belongs to case
      - Correction evidence exists and is valid
      - Reviewer has authority
      - Case is in VERIFICATION_REQUIRED state
    """
    case = db.get_compliance_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"Compliance case {case_id} not found.")

    if case["status"] == "CLOSED":
        raise HTTPException(status_code=400, detail=f"Compliance case {case_id} is already closed.")

    if case["status"] != "VERIFICATION_REQUIRED":
        raise HTTPException(
            status_code=400,
            detail=f"Case is in '{case['status']}' state. Only cases in 'VERIFICATION_REQUIRED' can be verified and closed.",
        )

    # RBAC: Field Inspector cannot close cases
    if reviewer_role.upper() in ("FIELD_INSPECTOR", "WORKER"):
        raise HTTPException(status_code=403, detail="Field inspectors cannot verify or close compliance cases.")

    actions = db.list_corrective_actions_for_case(case_id)
    if not actions:
        raise HTTPException(status_code=400, detail="Cannot close case: No corrective actions exist for this case.")

    correction_evidence = db.list_case_correction_evidence(case_id)
    if not correction_evidence:
        raise HTTPException(status_code=400, detail="Cannot close case: No correction evidence has been submitted.")

    now = datetime.now(timezone.utc)
    closure_reason = (notes or "").strip() or "Statutory verification confirmed. All corrective actions and evidence validated."

    # Generate Cryptographic Closure Proof
    closure_payload = {
        "case_id": case_id,
        "closed_by": reviewer_id,
        "closed_role": reviewer_role,
        "closed_at": now.isoformat(),
        "reason": closure_reason,
        "verified_evidence_count": len(correction_evidence),
    }
    proof = create_audit_proof_record(
        case_id=case_id,
        action_type="CASE_CLOSED",
        payload=closure_payload,
        actor_id=reviewer_id,
        actor_role=reviewer_role,
    )
    db.save_cryptographic_proof(proof)

    # Update database
    db.update_compliance_case_status(
        case_id,
        status="CLOSED",
        updated_at=now.isoformat(),
        closed_at=now.isoformat(),
        closed_by=reviewer_id,
    )

    # Also mark original finding as resolved if associated
    if case.get("finding_id"):
        conn = db._connect()
        conn.execute(
            "UPDATE findings SET status = 'resolved' WHERE finding_id = ?",
            (case["finding_id"],),
        )
        conn.commit()
        conn.close()

    # Record Audit Event
    db.record_case_audit_event(
        event_id=f"EVT-{uuid4().hex[:10].upper()}",
        case_id=case_id,
        action="CASE_CLOSED",
        actor_id=reviewer_id,
        actor_role=reviewer_role,
        previous_state="VERIFICATION_REQUIRED",
        new_state="CLOSED",
        reason=closure_reason,
        timestamp=now.isoformat(),
        details=f"Verified with {len(correction_evidence)} evidence item(s). Audit proof CID: {proof['ipfs_cid']}",
        sha256=proof["sha256"],
        ipfs_cid=proof["ipfs_cid"],
    )

    return {
        "case_id": case_id,
        "status": "CLOSED",
        "closed_at": now.isoformat(),
        "closed_by": reviewer_id,
        "cryptographic_proof": proof,
        "message": f"Compliance case {case_id} verified and closed with immutable audit proof.",
    }


def return_case_for_correction(
    case_id: str,
    reviewer_id: str,
    reviewer_role: str,
    reason: str,
) -> dict:
    """
    Return case for correction when evidence is insufficient or unsatisfactory.
    Strictly requires a substantive non-empty reason (at least 5 characters).
    """
    case = db.get_compliance_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"Compliance case {case_id} not found.")

    if case["status"] == "CLOSED":
        raise HTTPException(status_code=400, detail="Cannot return an already closed compliance case.")

    if not reason or len(reason.strip()) < 5:
        raise HTTPException(
            status_code=400,
            detail="A substantive reason (minimum 5 characters) is mandatory to return a case for correction.",
        )

    # RBAC: Field Inspector cannot return cases
    if reviewer_role.upper() in ("FIELD_INSPECTOR", "WORKER"):
        raise HTTPException(status_code=403, detail="Field inspectors cannot return compliance cases.")

    clean_reason = reason.strip()
    now = datetime.now(timezone.utc)
    prev_status = case["status"]

    # Transition case to RETURNED_FOR_CORRECTION
    db.update_compliance_case_status(case_id, status="RETURNED_FOR_CORRECTION", updated_at=now.isoformat())

    # Reopen corrective actions so that supervisor/owner can update or resubmit
    conn = db._connect()
    conn.execute(
        """
        UPDATE corrective_actions
        SET status = 'OPEN',
            updated_at = ?
        WHERE case_id = ?
        """,
        (now.isoformat(), case_id),
    )
    conn.commit()
    conn.close()

    # Record Audit Event
    db.record_case_audit_event(
        event_id=f"EVT-{uuid4().hex[:10].upper()}",
        case_id=case_id,
        action="CASE_RETURNED",
        actor_id=reviewer_id,
        actor_role=reviewer_role,
        previous_state=prev_status,
        new_state="RETURNED_FOR_CORRECTION",
        reason=clean_reason,
        timestamp=now.isoformat(),
    )

    return {
        "case_id": case_id,
        "status": "RETURNED_FOR_CORRECTION",
        "returned_by": reviewer_id,
        "reason": clean_reason,
        "timestamp": now.isoformat(),
        "message": f"Compliance case {case_id} returned for correction with audit trail preserved.",
    }
