"""
PRITHVI — Compliance Intelligence Engine (Phase 2)
===================================================

Derives real-time, explainable mine-level statutory compliance state
directly from SQLite database records.

Core Objectives:
- Total applicable inspections (13 for Jharia Underground Demonstration Mine)
- Schedule states: overdue, due today, upcoming
- Execution states: submitted, verified, review required
- Risk indicators: open findings, threshold violations
- Category-level compliance breakdown for all 7 Phase 1 CMR categories:
    1. Ventilation & Gas
    2. Shaft & Winding
    3. Electrical
    4. HEMM
    5. Blasting
    6. Roof / Strata
    7. Water / Drainage
- Actionable attention items prioritized by statutory risk.

NO mock data. NO synthetic dashboard multipliers.
All metrics are mathematically derived from actual database records.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from . import database as db
from .scheduling import refresh_mine_schedule, _parse_datetime

SEVEN_STATUTORY_CATEGORIES = [
    "Ventilation & Gas",
    "Shaft & Winding",
    "Electrical",
    "HEMM",
    "Blasting",
    "Roof / Strata",
    "Water / Drainage",
]

SEVERITY_ORDER = {
    "CRITICAL": 0,
    "HIGH": 1,
    "MEDIUM": 2,
    "LOW": 3,
    "INFO": 4,
}


def evaluate_measurement_threshold(
    value: float,
    min_value: Optional[float],
    max_value: Optional[float],
) -> tuple[bool, Optional[str], Optional[float]]:
    """
    Evaluate actual measurement against template statutory threshold limits.
    Returns: (is_violation, violation_type, limit_value)
    """
    if max_value is not None and value > max_value:
        return True, "EXCEEDS_MAXIMUM", max_value
    if min_value is not None and value < min_value:
        return True, "BELOW_MINIMUM", min_value
    return False, None, None


def get_mine_threshold_violations(mine_id: str) -> list[dict]:
    """
    Scan all submitted measurements for a mine and evaluate them
    against statutory template min_value/max_value thresholds.
    """
    conn = db._connect()

    # Query all measurements belonging to inspections for this mine
    meas_rows = conn.execute(
        """
        SELECT
            m.measurement_id,
            m.inspection_id,
            m.measurement_type,
            m.value,
            m.unit,
            m.captured_at,
            i.template_id,
            i.inspection_date,
            t.name AS template_name,
            t.inspection_family
        FROM measurements m
        JOIN inspections i ON m.inspection_id = i.inspection_id
        JOIN inspection_templates t ON i.template_id = t.template_id
        WHERE i.mine_id = ?
        ORDER BY m.captured_at DESC
        """,
        (mine_id,),
    ).fetchall()

    # Query all template measurement definitions that have thresholds defined
    tm_rows = conn.execute(
        """
        SELECT
            template_id,
            measurement_id,
            name,
            unit,
            min_value,
            max_value,
            threshold_label
        FROM template_measurements
        WHERE min_value IS NOT NULL OR max_value IS NOT NULL
        """
    ).fetchall()

    conn.close()

    # Build threshold definition lookup table
    # Map (template_id, measurement_id_lower) and (template_id, name_lower)
    threshold_defs: dict[tuple[str, str], dict] = {}
    for tm in tm_rows:
        t_id = tm["template_id"]
        m_id = (tm["measurement_id"] or "").strip().lower()
        m_name = (tm["name"] or "").strip().lower()
        if m_id:
            threshold_defs[(t_id, m_id)] = dict(tm)
        if m_name:
            threshold_defs[(t_id, m_name)] = dict(tm)

    violations = []

    for m in meas_rows:
        t_id = m["template_id"]
        raw_mtype = (m["measurement_type"] or "").strip()
        mtype_lower = raw_mtype.lower()
        try:
            val = float(m["value"])
        except (TypeError, ValueError):
            continue

        # 1. Exact lookup
        defn = threshold_defs.get((t_id, mtype_lower))

        # 2. Fuzzy term lookup within same template
        if not defn:
            for (cand_tid, cand_key), cand_tm in threshold_defs.items():
                if cand_tid == t_id and (cand_key in mtype_lower or mtype_lower in cand_key):
                    defn = cand_tm
                    break

        # 3. Global fallback for common gas metrics (e.g. methane / ch4 / temperature)
        if not defn:
            for (cand_tid, cand_key), cand_tm in threshold_defs.items():
                if "methane" in cand_key and ("methane" in mtype_lower or "ch4" in mtype_lower):
                    defn = cand_tm
                    break

        if not defn:
            continue

        is_viol, viol_type, limit_val = evaluate_measurement_threshold(
            val, defn.get("min_value"), defn.get("max_value")
        )

        if is_viol:
            violations.append({
                "inspection_id": m["inspection_id"],
                "measurement_id": m["measurement_id"],
                "measurement_type": raw_mtype,
                "measurement_name": defn.get("name") or raw_mtype,
                "template_id": t_id,
                "template_name": m["template_name"],
                "inspection_family": m["inspection_family"] or "General",
                "value": val,
                "unit": m["unit"] or defn.get("unit"),
                "limit_value": limit_val,
                "threshold_label": defn.get("threshold_label"),
                "violation_type": viol_type,
                "captured_at": str(m["captured_at"]) if m["captured_at"] else None,
                "inspection_date": str(m["inspection_date"]) if m["inspection_date"] else None,
            })

    return violations


def get_mine_compliance_summary(mine_id: str) -> Optional[dict]:
    """
    Compute real-time, comprehensive statutory compliance intelligence for a mine.
    """
    mine = db.get_mine(mine_id)
    if mine is None:
        return None

    # Ensure schedules are refreshed to current time
    try:
        refresh_mine_schedule(mine_id)
    except Exception:
        pass

    now = datetime.now(timezone.utc)
    now_date = now.date()

    # ------------------------------------------------------------
    # 1. SCHEDULE METRICS
    # ------------------------------------------------------------
    schedules = db.get_schedules_for_mine(mine_id)
    active_schedules = [s for s in schedules if bool(s.get("active", True))]
    total_applicable_inspections = len(active_schedules)

    overdue_schedules = []
    due_today_schedules = []
    upcoming_schedules = []

    for s in active_schedules:
        next_due_raw = s.get("next_due_at")
        if not next_due_raw:
            upcoming_schedules.append(s)
            continue

        due_dt = _parse_datetime(next_due_raw)
        if due_dt is None:
            upcoming_schedules.append(s)
            continue

        due_date = due_dt.date()
        if due_dt < now and due_date < now_date:
            overdue_schedules.append(s)
        elif due_date == now_date:
            due_today_schedules.append(s)
        else:
            upcoming_schedules.append(s)

    # ------------------------------------------------------------
    # 2. INSPECTION EXECUTION METRICS
    # ------------------------------------------------------------
    inspections = db.get_inspections_for_mine(mine_id)

    submitted_inspections = [
        i for i in inspections
        if i.get("submitted_at") is not None or i.get("status") != "draft"
    ]
    submitted_count = len(submitted_inspections)

    verified_inspections = [
        i for i in inspections
        if i.get("status") == "verified"
    ]
    verified_count = len(verified_inspections)

    # Check pending verifications needing human review
    conn = db._connect()
    pending_review_rows = conn.execute(
        """
        SELECT v.inspection_id
        FROM verification_results v
        JOIN inspections i ON v.inspection_id = i.inspection_id
        WHERE i.mine_id = ?
          AND v.human_decision_required = 1
          AND NOT EXISTS (
              SELECT 1 FROM human_reviews hr
              WHERE hr.inspection_id = v.inspection_id
          )
          AND v.verification_id = (
              SELECT v2.verification_id
              FROM verification_results v2
              WHERE v2.inspection_id = v.inspection_id
              ORDER BY v2.rowid DESC
              LIMIT 1
          )
        """,
        (mine_id,),
    ).fetchall()
    conn.close()

    pending_review_insp_ids = {r["inspection_id"] for r in pending_review_rows}

    review_required_inspections = [
        i for i in inspections
        if i.get("status") in ("review_required", "reinspection_recommended")
        or i.get("inspection_id") in pending_review_insp_ids
    ]
    review_required_count = len(review_required_inspections)

    # ------------------------------------------------------------
    # 3. OPEN FINDINGS
    # ------------------------------------------------------------
    conn = db._connect()
    findings_rows = conn.execute(
        """
        SELECT
            f.finding_id,
            f.inspection_id,
            f.title,
            f.description,
            f.severity,
            f.status,
            f.corrective_action_required,
            i.template_id,
            i.inspection_date,
            t.name AS template_name,
            t.inspection_family
        FROM findings f
        JOIN inspections i ON f.inspection_id = i.inspection_id
        LEFT JOIN inspection_templates t ON i.template_id = t.template_id
        WHERE i.mine_id = ?
          AND LOWER(COALESCE(f.status, 'open')) NOT IN ('closed', 'resolved', 'completed')
        ORDER BY f.rowid DESC
        """,
        (mine_id,),
    ).fetchall()
    conn.close()

    open_findings = [dict(r) for r in findings_rows]
    open_findings_count = len(open_findings)

    # ------------------------------------------------------------
    # 4. THRESHOLD VIOLATIONS
    # ------------------------------------------------------------
    threshold_violations = get_mine_threshold_violations(mine_id)
    threshold_violations_count = len(threshold_violations)

    # ------------------------------------------------------------
    # 5. CATEGORY-LEVEL COMPLIANCE BREAKDOWN (7 CMR CATEGORIES)
    # ------------------------------------------------------------
    # Map schedules, inspections, findings, and violations to categories
    category_summaries: list[dict] = []

    for cat in SEVEN_STATUTORY_CATEGORIES:
        cat_schedules = [
            s for s in active_schedules
            if (s.get("inspection_family") or "").strip().lower() == cat.lower()
        ]
        cat_overdue = [
            s for s in overdue_schedules
            if (s.get("inspection_family") or "").strip().lower() == cat.lower()
        ]
        cat_due_today = [
            s for s in due_today_schedules
            if (s.get("inspection_family") or "").strip().lower() == cat.lower()
        ]
        cat_upcoming = [
            s for s in upcoming_schedules
            if (s.get("inspection_family") or "").strip().lower() == cat.lower()
        ]
        cat_inspections = [
            i for i in inspections
            if (i.get("inspection_family") or "").strip().lower() == cat.lower()
        ]
        cat_submitted = [
            i for i in submitted_inspections
            if (i.get("inspection_family") or "").strip().lower() == cat.lower()
        ]
        cat_verified = [
            i for i in verified_inspections
            if (i.get("inspection_family") or "").strip().lower() == cat.lower()
        ]
        cat_review_required = [
            i for i in review_required_inspections
            if (i.get("inspection_family") or "").strip().lower() == cat.lower()
        ]
        cat_violations = [
            tv for tv in threshold_violations
            if (tv.get("inspection_family") or "").strip().lower() == cat.lower()
        ]
        cat_findings = [
            f for f in open_findings
            if (f.get("inspection_family") or "").strip().lower() == cat.lower()
        ]

        # Determine compliance status for category
        if cat_overdue or any(
            "methane" in (v.get("measurement_name") or "").lower() for v in cat_violations
        ):
            status = "CRITICAL_NON_COMPLIANCE"
        elif cat_violations or cat_findings or cat_review_required:
            status = "ATTENTION_REQUIRED"
        elif cat_due_today:
            status = "UPCOMING_DUE"
        else:
            status = "COMPLIANT"

        category_summaries.append({
            "category": cat,
            "total_schedules": len(cat_schedules),
            "overdue_count": len(cat_overdue),
            "due_today_count": len(cat_due_today),
            "upcoming_count": len(cat_upcoming),
            "inspections_count": len(cat_inspections),
            "submitted_count": len(cat_submitted),
            "verified_count": len(cat_verified),
            "review_required_count": len(cat_review_required),
            "threshold_violations_count": len(cat_violations),
            "open_findings_count": len(cat_findings),
            "compliance_status": status,
        })

    # ------------------------------------------------------------
    # 6. ACTIONABLE ATTENTION ITEMS
    # ------------------------------------------------------------
    attention_items: list[dict] = []

    # A. Overdue inspections
    for s in overdue_schedules:
        family = s.get("inspection_family") or "Statutory Inspection"
        is_critical = family in ("Ventilation & Gas", "Roof / Strata")
        sched_name = s.get("template_name") or s.get("schedule_name") or s.get("schedule_id")
        due_str = str(s.get("next_due_at"))[:10] if s.get("next_due_at") else "Unscheduled"
        role = s.get("responsible_role") or "Competent Inspection Official"
        reg = s.get("regulation_reference") or s.get("obligation_id") or "Coal Mines Regulations 2017"

        attention_items.append({
            "item_id": f"ATTN-OVD-{s.get('schedule_instance_id')}",
            "item_type": "OVERDUE_INSPECTION",
            "severity": "CRITICAL" if is_critical else "HIGH",
            "category": family,
            "title": f"Statutory Inspection Overdue: {sched_name}",
            "description": (
                f"Statutory {s.get('frequency_label') or 'periodic'} inspection under {reg} "
                f"was due on {due_str}. Operating active faces without valid statutory coverage violates safety mandates."
            ),
            "action": f"Deploy {role} immediately to conduct inspection and submit signed measurements.",
            "reference_id": s.get("schedule_instance_id"),
            "created_at": str(s.get("next_due_at")) if s.get("next_due_at") else None,
        })

    # B. Threshold violations
    for tv in threshold_violations[:10]:  # Highlight top 10 most recent
        is_ch4 = "methane" in (tv["measurement_name"] or "").lower() or "ch4" in (tv["measurement_name"] or "").lower()
        viol_word = "exceeds maximum allowed limit" if tv["violation_type"] == "EXCEEDS_MAXIMUM" else "below minimum statutory requirement"

        attention_items.append({
            "item_id": f"ATTN-THR-{tv['measurement_id']}",
            "item_type": "THRESHOLD_VIOLATION",
            "severity": "CRITICAL" if is_ch4 else "HIGH",
            "category": tv["inspection_family"],
            "title": f"Statutory Threshold Violation: {tv['measurement_name']} ({tv['value']} {tv['unit'] or ''})",
            "description": (
                f"Observed measurement {tv['value']} {tv['unit'] or ''} in inspection {tv['inspection_id']} "
                f"({tv['template_name']}) {viol_word} of {tv['limit_value']} {tv['unit'] or ''} ({tv['threshold_label'] or ''})."
            ),
            "action": (
                "Initiate immediate ventilation dilution and withdrawal protocol under CMR Regulation 119."
                if is_ch4 else
                "Verify sensor calibration and conduct physical engineering check on site."
            ),
            "reference_id": tv["inspection_id"],
            "created_at": tv["captured_at"] or tv["inspection_date"],
        })

    # C. Open Findings
    for f in open_findings[:10]:
        sev = (f.get("severity") or "medium").upper()
        attention_items.append({
            "item_id": f"ATTN-FND-{f['finding_id']}",
            "item_type": "OPEN_FINDING",
            "severity": sev if sev in ("CRITICAL", "HIGH", "MEDIUM", "LOW") else "MEDIUM",
            "category": f.get("inspection_family") or "General Safety",
            "title": f"Open Finding: {f['title']}",
            "description": f"{f['description']} (Logged during {f.get('template_name') or f['inspection_id']}).",
            "action": "Assign designated maintenance supervisor to complete corrective action and verify closure.",
            "reference_id": f["finding_id"],
            "created_at": str(f.get("inspection_date")) if f.get("inspection_date") else None,
        })

    # D. Verification Requiring Review
    for insp in review_required_inspections[:10]:
        family = insp.get("inspection_family") or "Statutory Verification"
        insp_name = insp.get("inspection_name") or insp.get("template_id") or "Inspection"

        attention_items.append({
            "item_id": f"ATTN-REV-{insp['inspection_id']}",
            "item_type": "VERIFICATION_REVIEW",
            "severity": "HIGH",
            "category": family,
            "title": f"Regulatory Audit Adjudication Required: {insp['inspection_id']}",
            "description": (
                f"Automated Document AI / Verification Engine flagged potential conflicts or document anomalies "
                f"for {insp_name}. Statutory compliance determination is blocked pending DGMS human review."
            ),
            "action": "DGMS Regulatory Officer / Mine Manager must review verification dossier and submit audit determination.",
            "reference_id": insp["inspection_id"],
            "created_at": str(insp.get("inspection_date")) if insp.get("inspection_date") else None,
        })

    # Sort attention items by statutory severity priority
    attention_items.sort(
        key=lambda item: SEVERITY_ORDER.get(item.get("severity", "MEDIUM"), 99)
    )

    return {
        "mine_id": mine_id,
        "mine_name": mine.name,
        "subsidiary": mine.subsidiary,
        "mine_type": mine.mine_type.value if hasattr(mine.mine_type, "value") else str(mine.mine_type),
        "gassy_degree": mine.gassy_degree.value if hasattr(mine.gassy_degree, "value") else str(mine.gassy_degree),
        "as_of": now.isoformat(),
        "total_applicable_inspections": total_applicable_inspections,
        "due_today": len(due_today_schedules),
        "overdue": len(overdue_schedules),
        "upcoming": len(upcoming_schedules),
        "submitted": submitted_count,
        "verified": verified_count,
        "review_required": review_required_count,
        "open_findings": open_findings_count,
        "threshold_violations": threshold_violations_count,
        "category_compliance": category_summaries,
        "attention_items": attention_items,
        "threshold_violation_details": threshold_violations[:20],
    }
