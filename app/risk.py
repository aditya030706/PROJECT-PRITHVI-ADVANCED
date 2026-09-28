"""
PRITHVI — Risk & Recurring Non-Compliance Intelligence Engine (Phase 2 Task 3)
=============================================================================

Calculates transparent, deterministic, and explainable compliance risk
and detects recurring non-compliance patterns directly from real SQLite database records.

Architecture:
  DATABASE (prithvi.db)
     ↓
  COMPLIANCE SUMMARY (app.compliance)
     ↓
  RISK & RECURRING INTELLIGENCE (app.risk)
     ↓
  API ENDPOINTS (app.main)
     ↓
  COMMAND CENTER UI (frontend)
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from . import database as db
from .compliance import (
    get_mine_compliance_summary,
    get_mine_threshold_violations,
    SEVEN_STATUTORY_CATEGORIES,
)

# ============================================================
# DETERMINISTIC RISK MODEL CONSTANTS & CONFIGURATION
# ============================================================
# Named scoring weights - adjustable and transparent
WEIGHT_THRESHOLD_VIOLATION = 6.0
WEIGHT_CRITICAL_THRESHOLD_VIOLATION = 16.0
WEIGHT_RECURRING_ISSUE = 22.0
WEIGHT_OVERDUE_INSPECTION = 14.0
WEIGHT_OPEN_FINDING = 8.0
WEIGHT_REVIEW_REQUIRED = 4.0

CATEGORY_REGULATION_MAPPING = {
    "Ventilation & Gas": "CMR 2017, Reg 119, 156 (Ventilation & Gases)",
    "Shaft & Winding": "CMR 2017, Reg 75–80 (Shafts, Outlets & Winding)",
    "Electrical": "CMR 2017, Reg 160–170 (Flameproof Apparatus & Earthing)",
    "HEMM": "CMR 2017, Reg 135 (Heavy Earthmoving Machinery)",
    "Blasting": "CMR 2017, Reg 155–158 (Shotfiring & Danger Zones)",
    "Roof / Strata": "CMR 2017, Reg 85–95 (SCAMP & Support Plan)",
    "Water / Drainage": "CMR 2017, Reg 145 (Inundation & Pumping Stations)",
}


def get_mine_recurring_issues(mine_id: str) -> list[dict]:
    """
    Detect recurring compliance problems for a mine from real historical records.
    Only returns an issue when there is actual repeated evidence (occurrences >= 2).
    """
    recurring_issues: list[dict] = []

    # ------------------------------------------------------------
    # 1. RECURRING THRESHOLD VIOLATIONS
    # ------------------------------------------------------------
    # A measurement breaches its statutory threshold repeatedly across inspections.
    violations = get_mine_threshold_violations(mine_id)

    # Group violations by (category, measurement_name)
    grouped_violations: dict[tuple[str, str], list[dict]] = {}
    for v in violations:
        cat = (v.get("inspection_family") or "General").strip()
        m_name = (v.get("measurement_name") or v.get("measurement_type") or "Unknown").strip()
        key = (cat, m_name)
        grouped_violations.setdefault(key, []).append(v)

    for (cat, m_name), items in grouped_violations.items():
        if len(items) < 2:
            # Single incident is not recurring
            continue

        occurrences = len(items)
        # Sort items by date ascending to track trajectory
        sorted_items = sorted(
            items,
            key=lambda x: str(x.get("captured_at") or x.get("inspection_date") or ""),
        )

        first_detected = sorted_items[0].get("captured_at") or sorted_items[0].get("inspection_date")
        last_detected = sorted_items[-1].get("captured_at") or sorted_items[-1].get("inspection_date")

        max_val = max(float(x["value"]) for x in items)
        unit = items[0].get("unit") or ""
        limit_val = items[0].get("limit_value")
        th_label = items[0].get("threshold_label") or ""

        is_methane = "methane" in m_name.lower() or "ch4" in m_name.lower()
        is_critical = is_methane or (limit_val is not None and max_val >= 2 * float(limit_val))

        # Distinct inspection IDs where this repeated breach occurred (most recent first)
        related_inspections = list(dict.fromkeys(
            x["inspection_id"] for x in reversed(sorted_items) if x.get("inspection_id")
        ))

        # Statutory recommended action
        if is_methane:
            action = (
                "Review ventilation circuit and aux fan operation, conduct gas drainage borehole check, "
                "and execute statutory dilution and withdrawal protocol under CMR 2017 Regulation 119."
            )
        elif cat == "Ventilation & Gas":
            action = (
                "Conduct main mechanical ventilator survey, inspect regulator shutters, "
                "and recalibrate airflow sensors under CMR 2017 Regulation 156."
            )
        elif cat == "Roof / Strata":
            action = (
                "Halt extraction in affected face, verify SCAMP tell-tale indicators, "
                "and install additional roof bolt support under CMR 2017 Regulation 85."
            )
        else:
            action = (
                f"Escalate for management review, verify sensor calibration, and investigate recurring "
                f"underlying physical condition pursuant to {CATEGORY_REGULATION_MAPPING.get(cat, 'CMR 2017')}."
            )

        slug = f"{cat.lower().replace('&', 'and').replace('/', 'and').replace(' ', '-')}-{m_name.lower().replace(' ', '-')}"
        recurring_issues.append({
            "issue_id": f"REC-THR-{slug}",
            "category": cat,
            "issue_type": "RECURRING_THRESHOLD_VIOLATION",
            "title": f"Repeated {m_name} statutory threshold violations",
            "occurrences": occurrences,
            "first_detected_at": str(first_detected) if first_detected else None,
            "last_detected_at": str(last_detected) if last_detected else None,
            "severity": "CRITICAL" if is_critical else "HIGH",
            "status": "OPEN",
            "related_inspection_ids": related_inspections,
            "related_finding_ids": [],
            "description": (
                f"Statutory threshold limit of {limit_val} {unit} ({th_label}) breached {occurrences} times "
                f"across sequential field inspections. Observed readings reached up to {max_val} {unit}."
            ),
            "recommended_action": action,
        })

    # ------------------------------------------------------------
    # 2. RECURRING FINDINGS
    # ------------------------------------------------------------
    # The same or substantially similar finding recorded repeatedly across inspections
    conn = db._connect()
    finding_rows = conn.execute(
        """
        SELECT
            f.finding_id,
            f.inspection_id,
            f.title,
            f.description,
            f.severity,
            f.status,
            i.template_id,
            i.inspection_date,
            t.inspection_family
        FROM findings f
        JOIN inspections i ON f.inspection_id = i.inspection_id
        LEFT JOIN inspection_templates t ON i.template_id = t.template_id
        WHERE i.mine_id = ?
        ORDER BY i.inspection_date ASC
        """,
        (mine_id,),
    ).fetchall()
    conn.close()

    grouped_findings: dict[tuple[str, str], list[dict]] = {}
    for r in finding_rows:
        cat = (r["inspection_family"] or "General Safety").strip()
        title_norm = (r["title"] or "").strip().lower()
        key = (cat, title_norm)
        grouped_findings.setdefault(key, []).append(dict(r))

    for (cat, title_norm), f_items in grouped_findings.items():
        if len(f_items) < 2:
            continue

        occurrences = len(f_items)
        first_detected = f_items[0].get("inspection_date")
        last_detected = f_items[-1].get("inspection_date")

        # Open if any is open
        is_open = any(
            (f.get("status") or "open").lower() not in ("closed", "resolved", "completed")
            for f in f_items
        )

        has_critical = any((f.get("severity") or "").upper() == "CRITICAL" for f in f_items)
        has_high = any((f.get("severity") or "").upper() == "HIGH" for f in f_items)

        related_insp = list(dict.fromkeys(
            f["inspection_id"] for f in reversed(f_items) if f.get("inspection_id")
        ))
        related_fnd = [f["finding_id"] for f in f_items if f.get("finding_id")]

        slug = f"{cat.lower().replace('&', 'and').replace('/', 'and').replace(' ', '-')}-{title_norm[:20].replace(' ', '-')}"
        recurring_issues.append({
            "issue_id": f"REC-FND-{slug}",
            "category": cat,
            "issue_type": "RECURRING_FINDING",
            "title": f"Recurring Finding: {f_items[0]['title']}",
            "occurrences": occurrences,
            "first_detected_at": str(first_detected) if first_detected else None,
            "last_detected_at": str(last_detected) if last_detected else None,
            "severity": "CRITICAL" if has_critical else ("HIGH" if has_high else "MEDIUM"),
            "status": "OPEN" if is_open else "RESOLVED",
            "related_inspection_ids": related_insp,
            "related_finding_ids": related_fnd,
            "description": (
                f"Substantially similar finding defect identified across {occurrences} inspection cycles. "
                f"Corrective actions have not prevented recurrence."
            ),
            "recommended_action": (
                "Conduct engineering audit of ventilation circuit, inspect aux fan operation, "
                "and enforce statutory dilution protocol under CMR 2017 Regulation 119."
                if ("methane" in title_norm.lower() or "ch4" in title_norm.lower())
                else "Conduct engineering audit of failure cause and verify corrective action closure before next cycle."
            ),
        })

    # Sort recurring issues by severity and occurrence count
    SEV_SORT = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    recurring_issues.sort(
        key=lambda x: (SEV_SORT.get(x.get("severity", "MEDIUM"), 9), -x.get("occurrences", 0))
    )

    return recurring_issues


def get_mine_risk_intelligence(mine_id: str) -> Optional[dict]:
    """
    Calculate deterministic, explainable compliance risk for a mine and its categories.
    Consumes real database data via compliance summary and recurring non-compliance engine.
    """
    summary = get_mine_compliance_summary(mine_id)
    if summary is None:
        return None

    now = datetime.now(timezone.utc)
    recurring_issues = get_mine_recurring_issues(mine_id)

    # Index recurring issues by category
    rec_by_cat: dict[str, list[dict]] = {}
    for issue in recurring_issues:
        rec_by_cat.setdefault(issue["category"], []).append(issue)

    cat_summaries_input = {c["category"]: c for c in summary.get("category_compliance", [])}

    categories_risk: list[dict] = []
    all_drivers: list[tuple[int, str]] = []  # (priority, driver_text)

    # Query active SCADA telemetry safety signals (Phase 2 Task 9)
    active_telemetry: list[dict] = []
    try:
        active_telemetry = db.get_active_safety_signals(mine_id)
    except Exception:
        pass

    # Query active operational production anomalies (Phase 2 Task 10)
    try:
        active_anomalies = db.get_active_production_anomalies(mine_id)
        for anom in active_anomalies:
            if anom.get("severity") == "CRITICAL":
                all_drivers.append((1, f"Operational conflict: {anom.get('what')}"))
                break
            elif anom.get("severity") == "HIGH":
                all_drivers.append((2, f"Production anomaly: {anom.get('what')}"))
                break
    except Exception:
        pass

    telemetry_cat_map = {
        "METHANE": "Ventilation & Gas",
        "AIRFLOW": "Ventilation & Gas",
        "VENTILATION_FAN": "Ventilation & Gas",
        "DUST": "Ventilation & Gas",
        "SLOPE_DISPLACEMENT": "Roof / Strata",
        "PORE_PRESSURE": "Water / Drainage",
        "RAINFALL": "Water / Drainage",
    }
    telem_by_cat: dict[str, list[dict]] = {}
    for sig in active_telemetry:
        c_name = telemetry_cat_map.get(sig.get("sensor_type", ""), "Ventilation & Gas")
        telem_by_cat.setdefault(c_name, []).append(sig)

    for cat in SEVEN_STATUTORY_CATEGORIES:
        c_data = cat_summaries_input.get(cat, {})
        c_rec = rec_by_cat.get(cat, [])
        c_telem = telem_by_cat.get(cat, [])

        total_scheds = c_data.get("total_schedules", 0)
        submitted = c_data.get("submitted_count", 0)
        overdue = c_data.get("overdue_count", 0)
        tv_count = c_data.get("threshold_violations_count", 0)
        findings = c_data.get("open_findings_count", 0)
        review_req = c_data.get("review_required_count", 0)
        rec_count = len(c_rec)
        telem_count = len(c_telem)
        active_signals = overdue + tv_count + findings + review_req + rec_count + telem_count

        # Check if insufficient data
        if total_scheds == 0 and submitted == 0 and tv_count == 0 and telem_count == 0:
            categories_risk.append({
                "category": cat,
                "risk_level": "INSUFFICIENT_DATA",
                "risk_score": 0,
                "active_signals": 0,
                "recurring_issues": 0,
                "open_findings": 0,
                "overdue_inspections": 0,
                "drivers": ["No historical inspection or schedule data available for this domain."],
            })
            continue

        # Check for critical violations in this category
        has_critical_tv = False
        max_ch4_val = 0.0
        for tv in summary.get("threshold_violation_details", []):
            if (tv.get("inspection_family") or "").strip().lower() == cat.lower():
                m_name = (tv.get("measurement_name") or "").lower()
                val = float(tv.get("value", 0))
                if "methane" in m_name or "ch4" in m_name:
                    has_critical_tv = True
                    if val > max_ch4_val:
                        max_ch4_val = val

        # Check for active critical telemetry
        has_critical_telem = any(sig.get("severity") == "CRITICAL" for sig in c_telem)
        has_warning_telem = any(sig.get("severity") == "WARNING" for sig in c_telem)

        # Calculate deterministic raw score
        raw_score = (
            (tv_count * WEIGHT_THRESHOLD_VIOLATION)
            + ((10.0 if has_critical_tv else 0.0) * WEIGHT_CRITICAL_THRESHOLD_VIOLATION / 10.0)
            + (rec_count * WEIGHT_RECURRING_ISSUE)
            + (overdue * WEIGHT_OVERDUE_INSPECTION)
            + (findings * WEIGHT_OPEN_FINDING)
            + (review_req * WEIGHT_REVIEW_REQUIRED)
            + (30.0 if has_critical_telem else (12.0 if has_warning_telem else 0.0))
        )

        risk_score = min(100, int(round(raw_score)))

        # Determine risk classification
        if risk_score >= 50 or has_critical_tv or has_critical_telem or (overdue > 0 and cat in ("Ventilation & Gas", "Roof / Strata")):
            risk_level = "CRITICAL"
        elif risk_score >= 30 or rec_count > 0 or overdue > 0 or has_warning_telem:
            risk_level = "HIGH"
        elif risk_score >= 12 or tv_count > 0 or findings > 0 or review_req > 0:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        # Construct explainable drivers
        drivers: list[str] = []
        if has_critical_telem:
            crit_sigs = [s for s in c_telem if s.get("severity") == "CRITICAL"]
            for cs in crit_sigs:
                drivers.append(f"Live SCADA Telemetry Alert: {cs.get('display_name')} critical at {cs.get('observed_value')} {cs.get('unit')} (Simulated).")
                all_drivers.append((0, f"Critical live SCADA telemetry: {cs.get('display_name')} at {cs.get('observed_value')} {cs.get('unit')} ({cat})."))
        elif has_warning_telem:
            warn_sigs = [s for s in c_telem if s.get("severity") == "WARNING"]
            for ws in warn_sigs:
                drivers.append(f"Live SCADA Telemetry Warning: {ws.get('display_name')} at {ws.get('observed_value')} {ws.get('unit')} (Simulated).")
                all_drivers.append((1, f"Live SCADA warning: {ws.get('display_name')} in {cat}."))

        if has_critical_tv:
            drivers.append(f"Methane statutory limit (1.25% LEL) breached across inspections (peak: {max_ch4_val}%).")
            all_drivers.append((0, f"Critical Methane threshold breaches in {cat} (readings reached {max_ch4_val}%)."))
        elif tv_count > 0:
            drivers.append(f"{tv_count} statutory threshold violation(s) detected in recent inspections.")
            all_drivers.append((1, f"{tv_count} statutory threshold breaches in {cat}."))

        if rec_count > 0:
            rec_occurrences = sum(r.get("occurrences", 0) for r in c_rec)
            drivers.append(f"{rec_count} recurring non-compliance pattern(s) detected ({rec_occurrences} total occurrences).")
            all_drivers.append((0, f"Recurring compliance failure in {cat} with {rec_occurrences} documented breaches."))

        if overdue > 0:
            drivers.append(f"{overdue} statutory inspection(s) currently overdue past statutory deadline.")
            all_drivers.append((1, f"{overdue} statutory inspection(s) overdue in {cat}."))

        if review_req > 0:
            drivers.append(f"{review_req} inspection(s) require human regulatory review / audit determination.")

        if findings > 0:
            drivers.append(f"{findings} open statutory finding(s) pending maintenance resolution.")

        if not drivers:
            drivers.append("All statutory measurements within limits; inspections conducted on schedule.")

        categories_risk.append({
            "category": cat,
            "risk_level": risk_level,
            "risk_score": risk_score,
            "active_signals": active_signals,
            "recurring_issues": rec_count,
            "open_findings": findings,
            "overdue_inspections": overdue,
            "active_telemetry_signals": telem_count,
            "drivers": drivers,
        })

    # Overall Mine Risk
    # Determine overall risk level from highest category severity
    SEV_WEIGHTS = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1, "INSUFFICIENT_DATA": 0}
    highest_level = "LOW"
    highest_weight = 0
    max_cat_score = 0

    for cr in categories_risk:
        lvl = cr["risk_level"]
        wt = SEV_WEIGHTS.get(lvl, 0)
        if wt > highest_weight:
            highest_weight = wt
            highest_level = lvl
        if cr["risk_score"] > max_cat_score:
            max_cat_score = cr["risk_score"]

    # Deduplicate and sort top risk drivers
    all_drivers.sort(key=lambda x: x[0])
    top_drivers = [d[1] for d in all_drivers[:5]]
    if not top_drivers:
        top_drivers = [
            "All statutory inspections within prescribed limits.",
            "No recurring non-compliance patterns detected.",
            f"{summary.get('total_applicable_inspections', 13)} statutory schedules active and current.",
        ]

    return {
        "mine_id": mine_id,
        "mine_name": summary.get("mine_name"),
        "overall_risk_level": highest_level,
        "overall_risk_score": max_cat_score,
        "as_of": now.isoformat(),
        "categories": categories_risk,
        "recurring_issues": recurring_issues,
        "top_risk_drivers": top_drivers,
    }
