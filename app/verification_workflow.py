"""
PRITHVI — Verification & Regulatory Review Intelligence Workflow
=================================================================

Phase 2 Task 4: Operational verification workflow connecting:
  REGULATORY OBLIGATION -> SCHEDULE -> FIELD INSPECTION -> EVIDENCE ->
  FINDINGS -> VERIFICATION -> RISK -> MANAGEMENT ACTION.

This module derives real verification queue statistics, review dossiers,
server-side validation, and audit tracking directly from the SQLite database.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from fastapi import HTTPException

from . import database as db
from .models import HumanReview, InspectionStatus, DecisionType
from .compliance import evaluate_measurement_threshold
from .risk import get_mine_risk_intelligence, get_mine_recurring_issues


def get_mine_display_name(mine_id: str, db_name: Optional[str] = None) -> str:
    if mine_id == "MINE-BCCL-JHARIA-01":
        return "Jharia Underground Demonstration Mine"
    if db_name:
        return db_name
    return mine_id


def get_mine_verification_queue(mine_id: str) -> dict:
    """
    Derive real verification center queue metrics and prioritized inspections.
    All numbers are computed from database records.
    """
    conn = db._connect()

    # Verify mine exists
    mine_row = conn.execute(
        "SELECT mine_id, name FROM mines WHERE mine_id = ?",
        (mine_id,),
    ).fetchone()
    if not mine_row:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Mine {mine_id} not found.")

    mine_name = get_mine_display_name(mine_id, mine_row["name"])

    # 1. Fetch template metadata
    tmpl_rows = conn.execute(
        """
        SELECT template_id, name, inspection_family, regulation_reference
        FROM inspection_templates
        """
    ).fetchall()
    templates = {r["template_id"]: dict(r) for r in tmpl_rows}

    # 2. Fetch template measurement threshold rules
    tm_rows = conn.execute(
        """
        SELECT template_id, measurement_id, name, unit, min_value, max_value, threshold_label
        FROM template_measurements
        WHERE min_value IS NOT NULL OR max_value IS NOT NULL
        """
    ).fetchall()
    threshold_defs: dict[tuple[str, str], dict] = {}
    for tm in tm_rows:
        t_id = tm["template_id"]
        m_id = (tm["measurement_id"] or "").strip().lower()
        m_name = (tm["name"] or "").strip().lower()
        if m_id:
            threshold_defs[(t_id, m_id)] = dict(tm)
        if m_name:
            threshold_defs[(t_id, m_name)] = dict(tm)

    # 3. Fetch template evidence requirements
    ev_req_rows = conn.execute(
        """
        SELECT template_id, evidence_type, name, required, minimum_count
        FROM template_evidence_requirements
        """
    ).fetchall()
    evidence_reqs_by_template: dict[str, list[dict]] = {}
    for er in ev_req_rows:
        evidence_reqs_by_template.setdefault(er["template_id"], []).append(dict(er))

    # 4. Count all inspection states for this mine
    insp_status_rows = conn.execute(
        """
        SELECT status, count(*) as cnt
        FROM inspections
        WHERE mine_id = ?
        GROUP BY status
        """,
        (mine_id,),
    ).fetchall()
    status_counts = {r["status"]: r["cnt"] for r in insp_status_rows}

    # Count submitted (non-draft inspections)
    submitted_count = sum(
        cnt for stat, cnt in status_counts.items() if stat != InspectionStatus.DRAFT.value
    )

    # Review required: inspections in reviewable status
    reviewable_statuses = (
        InspectionStatus.REVIEW_REQUIRED.value,
        InspectionStatus.SUBMITTED.value,
        InspectionStatus.REINSPECTION_RECOMMENDED.value,
    )
    review_required_count = sum(
        status_counts.get(stat, 0) for stat in reviewable_statuses
    )

    # Verified count
    verified_count = (
        status_counts.get(InspectionStatus.VERIFIED.value, 0)
        + status_counts.get(InspectionStatus.CLOSED.value, 0)
    )

    # Rejected count
    rejected_count = status_counts.get(InspectionStatus.REJECTED.value, 0)
    # Also check latest decision from human_reviews if inspection status wasn't directly changed
    conn_reviews = conn.execute(
        """
        SELECT count(distinct hr.inspection_id)
        FROM human_reviews hr
        JOIN inspections i ON hr.inspection_id = i.inspection_id
        WHERE i.mine_id = ? AND hr.decision IN ('reject', 'return')
        """,
        (mine_id,),
    ).fetchone()
    if conn_reviews and conn_reviews[0] > rejected_count:
        rejected_count = conn_reviews[0]

    # 5. Fetch all inspections currently awaiting review
    pending_rows = conn.execute(
        """
        SELECT
            inspection_id,
            template_id,
            obligation_id,
            inspector_id,
            started_at,
            submitted_at,
            inspection_date,
            status
        FROM inspections
        WHERE mine_id = ?
          AND status IN ('review_required', 'submitted', 'reinspection_recommended')
        ORDER BY submitted_at ASC, inspection_date ASC
        """,
        (mine_id,),
    ).fetchall()

    items = []
    high_risk_review_count = 0

    for row in pending_rows:
        i_id = row["inspection_id"]
        t_id = row["template_id"]
        tmpl = templates.get(t_id, {})
        tmpl_name = tmpl.get("name") or t_id
        category = tmpl.get("inspection_family") or "General Compliance"
        reg_ref = tmpl.get("regulation_reference")

        # Measurements evaluation
        meas_rows = conn.execute(
            """
            SELECT measurement_id, measurement_type, value, unit
            FROM measurements
            WHERE inspection_id = ?
            """,
            (i_id,),
        ).fetchall()

        has_violations = False
        has_methane_violation = False
        for m in meas_rows:
            raw_mtype = (m["measurement_type"] or "").strip().lower()
            try:
                val = float(m["value"])
            except (TypeError, ValueError):
                continue
            defn = threshold_defs.get((t_id, raw_mtype))
            if not defn:
                for (cand_tid, cand_key), cand_tm in threshold_defs.items():
                    if cand_tid == t_id and (cand_key in raw_mtype or raw_mtype in cand_key):
                        defn = cand_tm
                        break
            if not defn:
                for (cand_tid, cand_key), cand_tm in threshold_defs.items():
                    if "methane" in cand_key and ("methane" in raw_mtype or "ch4" in raw_mtype):
                        defn = cand_tm
                        break
            if defn:
                is_viol, _, _ = evaluate_measurement_threshold(
                    val, defn.get("min_value"), defn.get("max_value")
                )
                if is_viol:
                    has_violations = True
                    if "methane" in raw_mtype or "ch4" in raw_mtype:
                        has_methane_violation = True

        # Evidence count & completeness
        ev_rows = conn.execute(
            "SELECT evidence_id, evidence_type FROM evidence WHERE inspection_id = ?",
            (i_id,),
        ).fetchall()
        actual_ev_count = len(ev_rows)

        reqs = evidence_reqs_by_template.get(t_id, [])
        required_ev_count = sum(r.get("minimum_count", 1) for r in reqs if r.get("required", 1))
        # Default minimum of 1 evidence if template specifies none
        if required_ev_count == 0 and len(reqs) > 0:
            required_ev_count = len(reqs)

        evidence_compliant = actual_ev_count >= required_ev_count if required_ev_count > 0 else (actual_ev_count > 0)

        # Findings count
        finding_rows = conn.execute(
            "SELECT finding_id, severity FROM findings WHERE inspection_id = ?",
            (i_id,),
        ).fetchall()
        findings_count = len(finding_rows)
        has_critical_finding = any(f["severity"] == "critical" for f in finding_rows)

        # Priority calculation
        priority_reasons: list[str] = []
        if has_methane_violation:
            priority = "CRITICAL"
            risk_level = "CRITICAL"
            priority_reasons.append("Statutory methane threshold violation")
        elif has_critical_finding:
            priority = "CRITICAL"
            risk_level = "CRITICAL"
            priority_reasons.append("Critical safety finding recorded")
        elif has_violations:
            priority = "HIGH"
            risk_level = "HIGH"
            priority_reasons.append("Statutory threshold parameter violation")
        elif not evidence_compliant:
            priority = "HIGH"
            risk_level = "HIGH"
            priority_reasons.append(f"Incomplete evidence: {actual_ev_count}/{required_ev_count} attached")
        elif findings_count > 0:
            priority = "HIGH"
            risk_level = "HIGH"
            priority_reasons.append(f"{findings_count} open non-compliance finding(s)")
        else:
            priority = "NORMAL"
            risk_level = "NORMAL"
            priority_reasons.append("Statutory periodic submission")

        if priority in ("CRITICAL", "HIGH"):
            high_risk_review_count += 1

        inspector_name = "Field Inspector"
        if row["inspector_id"]:
            inspector_name = f"Inspector ({row['inspector_id']})"

        items.append({
            "inspection_id": i_id,
            "template_id": t_id,
            "template_name": tmpl_name,
            "category": category,
            "regulation_reference": reg_ref,
            "inspector_id": row["inspector_id"] or "INSPECTOR-001",
            "inspector_name": inspector_name,
            "submitted_at": row["submitted_at"],
            "inspection_date": row["inspection_date"],
            "inspection_status": row["status"],
            "verification_status": row["status"],
            "risk_level": risk_level,
            "priority": priority,
            "priority_reasons": priority_reasons,
            "evidence_count": actual_ev_count,
            "required_evidence_count": max(required_ev_count, 1),
            "evidence_compliant": evidence_compliant,
            "findings_count": findings_count,
            "has_violations": has_violations,
        })

    conn.close()

    # Priority sort order: CRITICAL -> HIGH -> NORMAL
    priority_order = {"CRITICAL": 0, "HIGH": 1, "NORMAL": 2}
    items.sort(key=lambda x: (
        priority_order.get(x["priority"], 9),
        x["submitted_at"] or "9999",
    ))

    return {
        "mine_id": mine_id,
        "mine_name": mine_name,
        "counts": {
            "submitted": submitted_count,
            "review_required": review_required_count,
            "verified": verified_count,
            "rejected": rejected_count,
            "high_risk_review": high_risk_review_count,
        },
        "items": items,
    }


def get_inspection_verification_dossier(inspection_id: str) -> dict:
    """
    Retrieve the full, structured compliance verification dossier for an inspection.
    Includes identity, measurements with template threshold metadata, checklist,
    evidence completeness check, findings, risk context, and audit history.
    """
    conn = db._connect()

    # 1. Inspection details
    insp_row = conn.execute(
        """
        SELECT
            i.inspection_id,
            i.mine_id,
            i.template_id,
            i.obligation_id,
            i.inspector_id,
            i.started_at,
            i.submitted_at,
            i.inspection_date,
            i.status,
            m.name as mine_name,
            t.name as template_name,
            t.inspection_family,
            t.regulation_reference,
            t.frequency_label
        FROM inspections i
        LEFT JOIN mines m ON i.mine_id = m.mine_id
        LEFT JOIN inspection_templates t ON i.template_id = t.template_id
        WHERE i.inspection_id = ?
        """,
        (inspection_id,),
    ).fetchone()

    if not insp_row:
        conn.close()
        raise HTTPException(
            status_code=404, detail=f"Inspection {inspection_id} not found."
        )

    t_id = insp_row["template_id"]
    mine_id = insp_row["mine_id"]
    category = insp_row["inspection_family"] or "General Compliance"
    mine_name = get_mine_display_name(mine_id, insp_row["mine_name"])

    # 2. Template threshold definitions
    tm_rows = conn.execute(
        """
        SELECT template_id, measurement_id, name, unit, min_value, max_value, threshold_label, description
        FROM template_measurements
        WHERE template_id = ?
        """,
        (t_id,),
    ).fetchall()
    threshold_defs = {}
    for tm in tm_rows:
        m_id = (tm["measurement_id"] or "").strip().lower()
        m_name = (tm["name"] or "").strip().lower()
        if m_id:
            threshold_defs[m_id] = dict(tm)
        if m_name:
            threshold_defs[m_name] = dict(tm)

    # Also load all global configured thresholds from other templates
    global_tm_rows = conn.execute(
        """
        SELECT measurement_id, name, unit, min_value, max_value, threshold_label
        FROM template_measurements
        WHERE min_value IS NOT NULL OR max_value IS NOT NULL
        """
    ).fetchall()
    global_thresholds = {}
    for gtm in global_tm_rows:
        g_id = (gtm["measurement_id"] or "").strip().lower()
        g_name = (gtm["name"] or "").strip().lower()
        if g_id:
            global_thresholds[g_id] = dict(gtm)
        if g_name:
            global_thresholds[g_name] = dict(gtm)

    # 3. Submitted measurements
    meas_rows = conn.execute(
        """
        SELECT measurement_id, measurement_type, value, unit, captured_at
        FROM measurements
        WHERE inspection_id = ?
        """,
        (inspection_id,),
    ).fetchall()

    measurements_review = []
    has_violations = False
    violations_summary_list = []

    for m in meas_rows:
        raw_mtype = (m["measurement_type"] or "").strip()
        mtype_lower = raw_mtype.lower()
        try:
            val = float(m["value"])
        except (TypeError, ValueError):
            val = 0.0

        defn = threshold_defs.get(mtype_lower)
        if not defn:
            for k, tm in threshold_defs.items():
                if k in mtype_lower or mtype_lower in k:
                    defn = tm
                    break

        # If template doesn't have configured limits, fallback to global statutory limits
        if not defn or (defn.get("min_value") is None and defn.get("max_value") is None):
            global_match = global_thresholds.get(mtype_lower)
            if not global_match:
                for k, gtm in global_thresholds.items():
                    if k in mtype_lower or mtype_lower in k:
                        global_match = gtm
                        break
            if not global_match and ("methane" in mtype_lower or "ch4" in mtype_lower):
                for k, gtm in global_thresholds.items():
                    if "methane" in k:
                        global_match = gtm
                        break
            if global_match:
                # Merge with existing defn name/unit if available
                orig_name = defn.get("name") if defn else raw_mtype
                defn = {**global_match, "name": orig_name}
            elif "methane" in mtype_lower or "ch4" in mtype_lower:
                defn = {
                    "name": "Methane concentration",
                    "unit": "%",
                    "max_value": 1.25,
                    "threshold_label": "CMR 2017 Reg 153 Max 1.25%",
                }

        min_v = defn.get("min_value") if defn else None
        max_v = defn.get("max_value") if defn else None
        unit = m["unit"] or (defn.get("unit") if defn else None)
        param_name = defn.get("name") if defn else raw_mtype

        is_viol, viol_type, limit_val = evaluate_measurement_threshold(val, min_v, max_v)
        status = "VIOLATION" if is_viol else "PASS"
        if is_viol:
            has_violations = True
            violations_summary_list.append(f"{param_name} ({val} {unit or ''})")

        threshold_desc = None
        if min_v is not None and max_v is not None:
            threshold_desc = f"{min_v} - {max_v} {unit or ''}"
        elif max_v is not None:
            threshold_desc = f"<= {max_v} {unit or ''}"
        elif min_v is not None:
            threshold_desc = f">= {min_v} {unit or ''}"

        measurements_review.append({
            "measurement_id": m["measurement_id"],
            "parameter": param_name,
            "value": val,
            "unit": unit,
            "threshold": threshold_desc,
            "threshold_label": defn.get("threshold_label") if defn else None,
            "min_value": min_v,
            "max_value": max_v,
            "status": status,
            "violation_type": viol_type,
        })

    # 4. Checklist items
    chk_template_rows = conn.execute(
        """
        SELECT item_id, question, required, severity_if_failed
        FROM template_checklist
        WHERE template_id = ?
        """,
        (t_id,),
    ).fetchall()
    chk_map = {r["item_id"]: dict(r) for r in chk_template_rows}

    chk_result_rows = conn.execute(
        """
        SELECT item_id, passed, observation
        FROM checklist_results
        WHERE inspection_id = ?
        """,
        (inspection_id,),
    ).fetchall()
    res_map = {r["item_id"]: dict(r) for r in chk_result_rows}

    checklist_review = []
    failed_items_count = 0
    all_chk_keys = list(chk_map.keys())
    # If checklist results exist for items not explicitly in template_checklist, include them too
    for it_id in res_map:
        if it_id not in all_chk_keys:
            all_chk_keys.append(it_id)

    for it_id in all_chk_keys:
        tm_item = chk_map.get(it_id, {})
        res = res_map.get(it_id)
        question = tm_item.get("question") or f"Checklist requirement {it_id}"
        required = bool(tm_item.get("required", 1))
        severity = tm_item.get("severity_if_failed")

        if res is not None:
            passed = bool(res["passed"])
            status = "PASS" if passed else "FAIL"
            observation = res.get("observation")
            if not passed:
                failed_items_count += 1
        else:
            passed = False
            status = "NOT_APPLICABLE" if not required else "FAIL"
            observation = "Not submitted in field record"
            if required:
                failed_items_count += 1

        checklist_review.append({
            "item_id": it_id,
            "question": question,
            "required": required,
            "severity_if_failed": severity,
            "passed": passed,
            "status": status,
            "observation": observation,
        })

    # 5. Evidence & Completeness evaluation
    ev_req_rows = conn.execute(
        """
        SELECT evidence_id, evidence_type, name, required, minimum_count
        FROM template_evidence_requirements
        WHERE template_id = ?
        """,
        (t_id,),
    ).fetchall()

    ev_rows = conn.execute(
        """
        SELECT evidence_id, evidence_type, filename, storage_reference, sha256, captured_at
        FROM evidence
        WHERE inspection_id = ?
        """,
        (inspection_id,),
    ).fetchall()

    evidence_review = [
        {
            "evidence_id": r["evidence_id"],
            "evidence_type": r["evidence_type"],
            "name": r["filename"] or r["storage_reference"],
            "file_path": r["storage_reference"] or r["filename"],
            "sha256_hash": r["sha256"],
            "captured_at": r["captured_at"],
            "submitted_at": r["captured_at"],
            "checklist_item_id": None,
            "finding_id": None,
        }
        for r in ev_rows
    ]

    actual_ev_count = len(evidence_review)
    total_required = sum(r["minimum_count"] for r in ev_req_rows if r["required"])
    if total_required == 0 and len(ev_req_rows) > 0:
        total_required = len(ev_req_rows)

    # Check evidence types attached
    attached_types = {e["evidence_type"] for e in evidence_review}
    missing_requirements = []
    for er in ev_req_rows:
        if er["required"] and er["evidence_type"] not in attached_types:
            missing_requirements.append(er["name"] or f"Required {er['evidence_type']}")

    is_compliant = (
        actual_ev_count >= total_required and len(missing_requirements) == 0
    ) if total_required > 0 else (actual_ev_count > 0)

    # 6. Findings
    f_rows = conn.execute(
        """
        SELECT finding_id, title, description, severity, corrective_action_required, status
        FROM findings
        WHERE inspection_id = ?
        """,
        (inspection_id,),
    ).fetchall()

    findings_review = []
    for fr in f_rows:
        # Check if finding has linked evidence
        fe_rows = conn.execute(
            "SELECT evidence_id FROM finding_evidence WHERE finding_id = ?",
            (fr["finding_id"],),
        ).fetchall()
        linked_ev = [r["evidence_id"] for r in fe_rows]

        desc = fr["description"]
        if "title" in fr.keys() and fr["title"]:
            desc = f"{fr['title']}: {fr['description']}"

        findings_review.append({
            "finding_id": fr["finding_id"],
            "severity": fr["severity"],
            "description": desc,
            "category": category,
            "measurement_id": None,
            "checklist_item_id": None,
            "evidence_linked": linked_ev,
            "status": fr["status"],
            "created_at": None,
        })

    # 7. Risk Intelligence context (from Task 3 engine)
    risk_level = "NORMAL"
    recurring_status_text = "NO RECURRING NON-COMPLIANCE"
    try:
        risk_data = get_mine_risk_intelligence(mine_id)
        # Check category risk
        for cat_r in risk_data.get("categories", []):
            if cat_r.get("category", "").lower() == category.lower():
                risk_level = cat_r.get("risk_level", "NORMAL")
                break
        # Check recurring issues for this category/template
        rec_issues = get_mine_recurring_issues(mine_id)
        cat_recs = [ri for ri in rec_issues if ri.get("category", "").lower() == category.lower()]
        if cat_recs:
            top_rec = cat_recs[0]
            recurring_status_text = f"{top_rec.get('occurrences', 0)} REPEATED BREACHES ({top_rec.get('title')})"
    except Exception:
        pass

    # If this specific inspection has a methane violation, elevate risk
    if any("methane" in m["parameter"].lower() and m["status"] == "VIOLATION" for m in measurements_review):
        risk_level = "CRITICAL"

    # 8. Audit History from human_reviews
    audit_rows = conn.execute(
        """
        SELECT review_id, inspection_id, reviewer_id, decision, reason, reviewed_at,
               previous_status, new_status
        FROM human_reviews
        WHERE inspection_id = ?
        ORDER BY reviewed_at DESC
        """,
        (inspection_id,),
    ).fetchall()

    audit_history = [
        {
            "review_id": r["review_id"],
            "inspection_id": r["inspection_id"],
            "reviewer_id": r["reviewer_id"],
            "reviewer_name": "Mine Manager" if "MANAGER" in r["reviewer_id"].upper() or "REVIEWER" in r["reviewer_id"].upper() else r["reviewer_id"],
            "decision": r["decision"],
            "reason": r["reason"],
            "timestamp": r["reviewed_at"],
            "previous_status": r["previous_status"],
            "new_status": r["new_status"],
        }
        for r in audit_rows
    ]

    conn.close()

    # 9. Server-side verification eligibility check
    validation_errors = []
    curr_status = insp_row["status"]
    reviewable_states = ("review_required", "submitted", "reinspection_recommended")
    if curr_status not in reviewable_states:
        validation_errors.append(f"Inspection is in '{curr_status}' state (must be review_required or submitted).")

    if not is_compliant and total_required > 0:
        if missing_requirements:
            validation_errors.append(f"Missing required evidence: {', '.join(missing_requirements)}.")
        else:
            validation_errors.append(f"Insufficient evidence: {actual_ev_count}/{total_required} required evidence items attached.")

    can_verify = len(validation_errors) == 0

    # Format review summary text
    ev_summary_text = (
        f"{actual_ev_count} / {max(total_required, 1)} REQUIRED - {'COMPLIANT' if is_compliant else 'INCOMPLETE'}"
    )
    if has_violations:
        meas_summary_text = f"{len(violations_summary_list)} THRESHOLD VIOLATION(S) DETECTED ({', '.join(violations_summary_list)})"
    else:
        meas_summary_text = f"ALL {len(measurements_review)} MEASUREMENTS COMPLIANT"

    if failed_items_count > 0:
        chk_summary_text = f"{failed_items_count} FAILED OR INCOMPLETE CHECKLIST ITEM(S)"
    else:
        chk_summary_text = f"ALL {len(checklist_review)} CHECKLIST ITEMS PASSED"

    return {
        "inspection_id": inspection_id,
        "template_id": t_id,
        "template_name": insp_row["template_name"] or t_id,
        "category": category,
        "regulation_reference": insp_row["regulation_reference"],
        "frequency": insp_row["frequency_label"],
        "mine_id": mine_id,
        "mine_name": mine_name,
        "inspector_id": insp_row["inspector_id"] or "INSPECTOR-001",
        "inspector_name": f"Inspector ({insp_row['inspector_id'] or 'INSPECTOR-001'})",
        "submitted_at": insp_row["submitted_at"],
        "inspection_status": curr_status,
        "verification_status": curr_status,
        "measurements": measurements_review,
        "checklist": checklist_review,
        "evidence": evidence_review,
        "evidence_completeness": {
            "required_count": max(total_required, 1),
            "actual_count": actual_ev_count,
            "is_compliant": is_compliant,
            "missing_requirements": missing_requirements,
        },
        "findings": findings_review,
        "review_summary": {
            "evidence_completeness": ev_summary_text,
            "evidence_compliant": is_compliant,
            "measurement_compliance": meas_summary_text,
            "has_violations": has_violations,
            "checklist_compliance": chk_summary_text,
            "findings_count": len(findings_review),
            "risk_level": risk_level,
            "recurring_issue_status": recurring_status_text,
        },
        "risk_level": risk_level,
        "audit_history": audit_history,
        "can_verify": can_verify,
        "validation_errors": validation_errors,
    }


def execute_verify_inspection(
    inspection_id: str,
    reviewer_id: str,
    notes: Optional[str] = None,
) -> dict:
    """
    Execute server-side verified decision with strict completeness rules.
    """
    dossier = get_inspection_verification_dossier(inspection_id)

    # Server-side validation check
    if not dossier["can_verify"]:
        err_msg = "Cannot verify inspection. " + " ".join(dossier["validation_errors"])
        raise HTTPException(status_code=400, detail=err_msg)

    now = datetime.now(timezone.utc)
    reason_text = (
        notes.strip()
        if notes and notes.strip()
        else "Statutory verification confirmed by Mine Manager. All parameters and evidence reviewed."
    )

    review = HumanReview(
        review_id=f"REV-{uuid4().hex[:12].upper()}",
        inspection_id=inspection_id,
        reviewer_id=reviewer_id,
        decision=DecisionType.VERIFY,
        reason=reason_text,
        reviewed_at=now,
    )

    db.save_human_review(
        review=review,
        previous_status=dossier["inspection_status"],
        new_status=InspectionStatus.VERIFIED.value,
    )

    return {
        "inspection_id": inspection_id,
        "status": InspectionStatus.VERIFIED.value,
        "decision": "VERIFIED",
        "reviewer_id": reviewer_id,
        "reason": reason_text,
        "timestamp": now.isoformat(),
        "message": f"Inspection {inspection_id} successfully verified and closed.",
    }


def execute_return_inspection(
    inspection_id: str,
    reviewer_id: str,
    reason: str,
) -> dict:
    """
    Return inspection for correction or reinspection. Strictly requires a non-empty reason.
    """
    if not reason or len(reason.strip()) < 5:
        raise HTTPException(
            status_code=400,
            detail="A valid, substantive reason (at least 5 characters) is required to return an inspection for correction.",
        )

    clean_reason = reason.strip()
    dossier = get_inspection_verification_dossier(inspection_id)

    now = datetime.now(timezone.utc)
    review = HumanReview(
        review_id=f"REV-{uuid4().hex[:12].upper()}",
        inspection_id=inspection_id,
        reviewer_id=reviewer_id,
        decision=DecisionType.RETURN,
        reason=clean_reason,
        reviewed_at=now,
    )

    db.save_human_review(
        review=review,
        previous_status=dossier["inspection_status"],
        new_status=InspectionStatus.REJECTED.value,
    )

    return {
        "inspection_id": inspection_id,
        "status": InspectionStatus.REJECTED.value,
        "decision": "RETURNED_FOR_CORRECTION",
        "reviewer_id": reviewer_id,
        "reason": clean_reason,
        "timestamp": now.isoformat(),
        "message": f"Inspection {inspection_id} returned for correction with audit record.",
    }
