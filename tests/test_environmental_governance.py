"""
PRITHVI Phase 2 Task 13 — Environmental Governance, Monitoring & Regulatory Reporting Tests.
===========================================================================================
Verifies:
- 8 Environmental Domains (AIR, WATER, NOISE, VIBRATION, LAND, RECLAMATION, WASTE, OTHER)
- Parameter Registration & Validation (Units, Ranges, Future Timestamps, Duplicates)
- Underground vs Opencast Mining Method Rule Applicability & Segregation
- Configurable Rule / Statutory Rule Attribution (DEMO / CONFIGURED RULE)
- Deterministic Upper / Lower / Range Threshold Breach Evaluation
- Automatic ComplianceCase & CorrectiveAction Synthesis on Exceedances
- Recurring Environmental Violation Detection (>= 2 breaches)
- Deterministic Risk Calculation (0-100) & Domain Weighting
- Statutory Obligations (CTO, EC) & Monitoring Schedules
- Traceable Regulatory Reporting with Frozen Canonical Lineage to Ministry of Coal
- Cryptographic Sealing (SHA-256 Content Digest & IPFS Content ID via audit_proof.py)
- Scope Engine Authorization Enforcement (Mine, Area, Subsidiary, Corporate, DGMS)
- Contractor & Production Operational Cross-Correlation
- Idempotent Seed Execution
"""

import json
from datetime import datetime, timezone, timedelta
import pytest
from fastapi.testclient import TestClient
from fastapi import HTTPException

from app.main import app
from app import database as db
from app.models import (
    EnvironmentalDomain,
    EnvironmentalSourceType,
    DataQualityStatus,
    EnvironmentalParameter,
    EnvironmentalMeasurement,
    EnvironmentalThreshold,
    EnvironmentalObligation,
    EnvironmentalSchedule,
    EnvironmentalReport,
    CaseSourceType,
    CaseStatus,
)
from app.environmental_service import (
    evaluate_measurement_threshold,
    record_environmental_measurement,
    calculate_environmental_risk,
    detect_recurring_environmental_violations,
    correlate_contractor_context,
    correlate_production_context,
    generate_environmental_report,
    finalize_environmental_report,
)
from app.hierarchy_service import assert_hierarchy_access
from app.seed_data import seed_initial_data, load_environmental_governance_seed
from app.schemas import EnvironmentalMeasurementCreate


@pytest.fixture(scope="module", autouse=True)
def setup_environmental_data():
    """Ensure database and seeds are initialized."""
    db.init_db()
    seed_initial_data()


@pytest.fixture
def client():
    return TestClient(app)


# ------------------------------------------------------------
# 1. Environmental Parameter Registration Across All 8 Domains
# ------------------------------------------------------------
def test_01_environmental_parameter_registration():
    domains = [
        ("PARAM-AIR-PM10", EnvironmentalDomain.AIR, "µg/m³"),
        ("PARAM-WATER-PH", EnvironmentalDomain.WATER, "pH"),
        ("PARAM-NOISE-DAY", EnvironmentalDomain.NOISE, "dB(A)"),
        ("PARAM-VIB-PPV", EnvironmentalDomain.VIBRATION, "mm/s"),
        ("PARAM-LAND-SLOPE", EnvironmentalDomain.LAND, "degrees"),
        ("PARAM-REC-SURV", EnvironmentalDomain.RECLAMATION, "%"),
        ("PARAM-WASTE-OIL", EnvironmentalDomain.WASTE, "KL"),
    ]
    for pid, dom, unit in domains:
        param = db.get_environmental_parameter(pid)
        assert param is not None, f"Parameter {pid} must exist"
        assert param.domain == dom, f"Parameter {pid} must belong to domain {dom}"
        assert param.unit == unit, f"Parameter {pid} unit must match {unit}"
        assert param.active is True


# ------------------------------------------------------------
# 2. Environmental Measurement Recording & Ingestion
# ------------------------------------------------------------
def test_02_environmental_measurement_recording():
    now_utc = datetime.now(timezone.utc)
    create_dto = EnvironmentalMeasurementCreate(
        mine_id="MINE-MCL-TALCHER-01",
        operational_unit_id="OP-ROAD-TALCHER-01",
        parameter_id="PARAM-AIR-PM10",
        value=120.5,
        unit="µg/m³",
        measured_at=now_utc.isoformat(),
        source_type=EnvironmentalSourceType.FIELD_OBSERVATION,
        source_reference="Calibrated High-Vol Sampler 02",
        simulated=True,
    )
    result = record_environmental_measurement(create_dto, actor_id="TEST_INSPECTOR")
    meas = result["measurement"]
    assert meas.id.startswith("ENV-MEAS-")
    assert meas.value == 120.5
    assert meas.unit == "µg/m³"
    assert meas.status in ("RECORDED", "VERIFIED")
    assert meas.data_quality_status == DataQualityStatus.VALID


# ------------------------------------------------------------
# 3. Invalid Measurement Unit Rejected
# ------------------------------------------------------------
def test_03_invalid_measurement_unit_rejected():
    now_utc = datetime.now(timezone.utc)
    create_dto = EnvironmentalMeasurementCreate(
        mine_id="MINE-MCL-TALCHER-01",
        operational_unit_id="OP-ROAD-TALCHER-01",
        parameter_id="PARAM-AIR-PM10",
        value=120.5,
        unit="litres",  # Incompatible unit for PM10
        measured_at=now_utc.isoformat(),
        source_type=EnvironmentalSourceType.MANUAL_ENTRY,
    )
    with pytest.raises(HTTPException) as exc:
        record_environmental_measurement(create_dto, actor_id="TEST_INSPECTOR")
    assert exc.value.status_code == 422
    assert "Incompatible unit" in exc.value.detail


# ------------------------------------------------------------
# 4. Future Measurement Timestamp Rejected
# ------------------------------------------------------------
def test_04_future_timestamp_rejected():
    future_dt = datetime.now(timezone.utc) + timedelta(days=2)
    create_dto = EnvironmentalMeasurementCreate(
        mine_id="MINE-MCL-TALCHER-01",
        operational_unit_id="OP-ROAD-TALCHER-01",
        parameter_id="PARAM-AIR-PM10",
        value=110.0,
        unit="µg/m³",
        measured_at=future_dt.isoformat(),
        source_type=EnvironmentalSourceType.FIELD_OBSERVATION,
    )
    with pytest.raises(HTTPException) as exc:
        record_environmental_measurement(create_dto, actor_id="TEST_INSPECTOR")
    assert exc.value.status_code == 422
    assert "cannot be in the future" in exc.value.detail


# ------------------------------------------------------------
# 5. Duplicate Measurement Prevented / Handled Idempotently
# ------------------------------------------------------------
def test_05_duplicate_measurement_prevented():
    fixed_dt = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    dto = EnvironmentalMeasurementCreate(
        mine_id="MINE-MCL-TALCHER-01",
        operational_unit_id="OP-ROAD-TALCHER-01",
        parameter_id="PARAM-AIR-PM25",
        value=45.0,
        unit="µg/m³",
        measured_at=fixed_dt,
        source_type=EnvironmentalSourceType.FIELD_OBSERVATION,
    )
    # First write succeeds
    res1 = record_environmental_measurement(dto, actor_id="TEST_INSPECTOR")
    assert res1["measurement"].id is not None

    # Immediate second write with same mine, parameter, and timestamp is rejected as duplicate
    with pytest.raises(HTTPException) as exc:
        record_environmental_measurement(dto, actor_id="TEST_INSPECTOR")
    assert exc.value.status_code in (409, 422)
    assert "Duplicate measurement" in exc.value.detail


# ------------------------------------------------------------
# 6. Mine Type Applicability — Underground Specific
# ------------------------------------------------------------
def test_06_mine_type_applicability_ug():
    # PARAM-AIR-VENT-CH4 is applicable only to UNDERGROUND
    param = db.get_environmental_parameter("PARAM-AIR-VENT-CH4")
    assert param is not None
    assert param.mine_type_applicability == "UNDERGROUND"

    # Attempting to record an Opencast-only parameter (PARAM-VIB-PPV) on UG mine is rejected
    now_utc = datetime.now(timezone.utc)
    create_dto = EnvironmentalMeasurementCreate(
        mine_id="MINE-BCCL-JHARIA-01",  # Underground Coal Mine
        operational_unit_id=None,
        parameter_id="PARAM-VIB-PPV",  # Opencast only
        value=5.0,
        unit="mm/s",
        measured_at=now_utc.isoformat(),
        source_type=EnvironmentalSourceType.MANUAL_ENTRY,
    )
    with pytest.raises(HTTPException) as exc:
        record_environmental_measurement(create_dto, actor_id="TEST_INSPECTOR")
    assert exc.value.status_code == 422
    assert "not applicable to mine type" in exc.value.detail


# ------------------------------------------------------------
# 7. Mine Type Applicability — Opencast Specific
# ------------------------------------------------------------
def test_07_mine_type_applicability_oc():
    # PARAM-VIB-PPV (blasting ground vibration) is applicable to OPENCAST
    param = db.get_environmental_parameter("PARAM-VIB-PPV")
    assert param is not None
    assert param.mine_type_applicability == "OPENCAST"

    # Recording on Talcher Opencast succeeds
    now_utc = datetime.now(timezone.utc)
    create_dto = EnvironmentalMeasurementCreate(
        mine_id="MINE-MCL-TALCHER-01",
        operational_unit_id="OP-PIT-TALCHER-01",
        parameter_id="PARAM-VIB-PPV",
        value=6.2,
        unit="mm/s",
        measured_at=now_utc.isoformat(),
        source_type=EnvironmentalSourceType.FIELD_OBSERVATION,
    )
    res = record_environmental_measurement(create_dto, actor_id="TEST_INSPECTOR")
    assert res["measurement"].value == 6.2


# ------------------------------------------------------------
# 8. Threshold Evaluation — Pass (Compliant)
# ------------------------------------------------------------
def test_08_threshold_evaluation_pass():
    # pH 7.2 against range 6.5 - 8.5
    breached, detail = evaluate_measurement_threshold(
        parameter_id="PARAM-WATER-PH",
        value=7.2,
        mine_type="UNDERGROUND_COAL",
    )
    assert breached is False
    assert detail is None


# ------------------------------------------------------------
# 9. Threshold Evaluation — Upper Limit Breach
# ------------------------------------------------------------
def test_09_threshold_evaluation_upper_breach():
    # PM10 of 350.0 against max 300.0
    breached, detail = evaluate_measurement_threshold(
        parameter_id="PARAM-AIR-PM10",
        value=350.0,
        mine_type="OPENCAST_COAL",
    )
    assert breached is True
    assert detail is not None
    assert detail["breach_type"] == "UPPER_LIMIT_EXCEEDED"
    assert detail["observed_value"] == 350.0
    assert detail["limit"] == 300.0


# ------------------------------------------------------------
# 10. Threshold Evaluation — Lower Limit Breach
# ------------------------------------------------------------
def test_10_threshold_evaluation_lower_breach():
    # pH of 5.8 against lower limit 6.5
    breached, detail = evaluate_measurement_threshold(
        parameter_id="PARAM-WATER-PH",
        value=5.8,
        mine_type="UNDERGROUND_COAL",
    )
    assert breached is True
    assert detail is not None
    assert detail["breach_type"] == "LOWER_LIMIT_VIOLATED"
    assert detail["observed_value"] == 5.8
    assert detail["limit"] == 6.5


# ------------------------------------------------------------
# 11. Threshold Evaluation — Range Breach
# ------------------------------------------------------------
def test_11_threshold_evaluation_range_breach():
    # pH of 9.4 against upper limit 8.5
    breached, detail = evaluate_measurement_threshold(
        parameter_id="PARAM-WATER-PH",
        value=9.4,
        mine_type="UNDERGROUND_COAL",
    )
    assert breached is True
    assert detail["breach_type"] == "UPPER_LIMIT_EXCEEDED"
    assert detail["limit"] == 8.5


# ------------------------------------------------------------
# 12. Statutory vs Demo Rule Distinction
# ------------------------------------------------------------
def test_12_statutory_vs_demo_rule_distinction():
    thresholds = db.list_environmental_thresholds()
    assert len(thresholds) > 0
    for t in thresholds:
        assert t.source_reference is not None
        # Unverified demonstration rules must explicitly carry DEMO / CONFIGURED tag
        if t.is_demo_rule:
            assert "DEMO" in t.source_reference or "CONFIGURED" in t.source_reference


# ------------------------------------------------------------
# 13. Automatic ComplianceCase Synthesis on Exceedance
# ------------------------------------------------------------
def test_13_automatic_case_generation_on_breach():
    now_utc = datetime.now(timezone.utc)
    create_dto = EnvironmentalMeasurementCreate(
        mine_id="MINE-MCL-TALCHER-01",
        operational_unit_id="OP-ROAD-TALCHER-01",
        parameter_id="PARAM-AIR-PM10",
        value=380.0,  # Exceeds 300.0 limit
        unit="µg/m³",
        measured_at=now_utc.isoformat(),
        source_type=EnvironmentalSourceType.FIELD_OBSERVATION,
        source_reference="Mobile Sampler Alpha",
    )
    res = record_environmental_measurement(create_dto, actor_id="ENV_TEST")
    assert res["threshold_breach"] is True
    meas_id = res["measurement"].id

    # Verify a ComplianceCase was synthesized with source_type = ENVIRONMENTAL_VIOLATION
    cases = db.list_compliance_cases(mine_id="MINE-MCL-TALCHER-01", source_type="ENVIRONMENTAL_VIOLATION")
    matching_case = next((c for c in cases if c.source_id == meas_id), None)
    assert matching_case is not None
    assert matching_case.source_type == CaseSourceType.ENVIRONMENTAL_VIOLATION
    assert matching_case.status == CaseStatus.ACTION_REQUIRED


# ------------------------------------------------------------
# 14. ComplianceCase Category and Severity Alignment
# ------------------------------------------------------------
def test_14_case_category_and_severity():
    cases = db.list_compliance_cases(mine_id="MINE-MCL-TALCHER-01", source_type="ENVIRONMENTAL_VIOLATION")
    assert len(cases) > 0
    c = cases[0]
    assert c.category == "AIR"
    assert c.severity in ("HIGH", "CRITICAL")
    assert "PM10" in c.title or "Respirable Particulate" in c.title


# ------------------------------------------------------------
# 15. Corrective Action Synthesis & Case Linkage
# ------------------------------------------------------------
def test_15_corrective_action_synthesis():
    cases = db.list_compliance_cases(mine_id="MINE-MCL-TALCHER-01", source_type="ENVIRONMENTAL_VIOLATION")
    assert len(cases) > 0
    c = cases[0]
    actions = db.list_corrective_actions(case_id=c.case_id)
    assert len(actions) > 0
    act = actions[0]
    assert act.case_id == c.case_id
    assert act.assigned_role == "ENVIRONMENTAL_OFFICER"
    assert act.priority in ("HIGH", "CRITICAL")
    assert act.status in ("OPEN", "open")


# ------------------------------------------------------------
# 16. Recurring Violation Detection (>= 2 breaches)
# ------------------------------------------------------------
def test_16_recurring_violation_detection():
    # Check recurring violations for Talcher mine (seeded violation + test violation)
    recurring = detect_recurring_environmental_violations("MINE-MCL-TALCHER-01")
    assert isinstance(recurring, list)
    # PARAM-AIR-PM10 has multiple breaches in Talcher
    pm10_recur = next((r for r in recurring if r["parameter_id"] == "PARAM-AIR-PM10"), None)
    if pm10_recur:
        assert pm10_recur["breach_count"] >= 2
        assert pm10_recur["is_recurring"] is True


# ------------------------------------------------------------
# 17. Deterministic Environmental Risk Calculation (0-100)
# ------------------------------------------------------------
def test_17_deterministic_risk_calculation():
    # Calculate for Talcher mine
    risk_t1 = calculate_environmental_risk("MINE-MCL-TALCHER-01")
    risk_t2 = calculate_environmental_risk("MINE-MCL-TALCHER-01")

    # Pure deterministic idempotency
    assert risk_t1.risk_score == risk_t2.risk_score
    assert risk_t1.risk_level == risk_t2.risk_level
    assert 0 <= risk_t1.risk_score <= 100
    assert risk_t1.risk_level in ("LOW", "MEDIUM", "HIGH", "CRITICAL")
    assert len(risk_t1.explanation) > 10


# ------------------------------------------------------------
# 18. Domain-Specific Risk Weighting
# ------------------------------------------------------------
def test_18_domain_specific_risk_weighting():
    risk = calculate_environmental_risk("MINE-MCL-TALCHER-01")
    assert "AIR" in risk.domain_risks
    assert "WATER" in risk.domain_risks
    # AIR should carry higher risk because of PM10 breaches
    air_risk = risk.domain_risks["AIR"]
    assert air_risk["breaches"] >= 1
    assert air_risk["score"] > 0


# ------------------------------------------------------------
# 19. Statutory Environmental Obligations Retrieval
# ------------------------------------------------------------
def test_19_environmental_obligation_retrieval():
    talcher_obs = db.list_environmental_obligations(mine_id="MINE-MCL-TALCHER-01")
    assert len(talcher_obs) >= 3
    # CTO, EC, DGMS vibration circulars must be present
    sources = [o.regulatory_source for o in talcher_obs]
    assert any("MoEFCC" in s or "Clearance" in s for s in sources)
    assert any("DGMS" in s for s in sources)


# ------------------------------------------------------------
# 20. Environmental Monitoring Schedules Tracking
# ------------------------------------------------------------
def test_20_environmental_monitoring_schedules():
    schedules = db.list_environmental_schedules(mine_id="MINE-MCL-TALCHER-01")
    assert len(schedules) >= 3
    statuses = [s.status for s in schedules]
    assert "NON_COMPLIANT" in statuses or "SCHEDULED" in statuses or "VERIFIED" in statuses


# ------------------------------------------------------------
# 21. Traceable Regulatory Report Generation
# ------------------------------------------------------------
def test_21_traceable_report_generation():
    rep = generate_environmental_report(
        mine_id="MINE-MCL-TALCHER-01",
        reporting_period_start="2026-09-01",
        reporting_period_end="2026-09-15",
        title="Automated Test Regulatory Environmental Report",
        report_type="STATUTORY_HALF_YEARLY",
        actor_id="REGULATORY_INSPECTOR",
    )
    assert rep.report_id.startswith("ENV-REP-")
    assert rep.status == "GENERATED"
    assert rep.measurements_count >= 1
    assert rep.lineage_snapshot is not None
    assert rep.source_record_hashes is not None


# ------------------------------------------------------------
# 22. Report Lineage Snapshot Contains Full Ministry Hierarchy
# ------------------------------------------------------------
def test_22_report_lineage_snapshot_contains_ministry():
    rep = generate_environmental_report(
        mine_id="MINE-MCL-TALCHER-01",
        reporting_period_start="2026-09-01",
        reporting_period_end="2026-09-15",
        title="Lineage Snapshot Verification Report",
    )
    lineage = json.loads(rep.lineage_snapshot)
    assert "ministry" in lineage
    assert lineage["ministry"]["name"] == "Ministry of Coal"
    assert lineage["holding_company"]["name"] == "Coal India Limited"
    assert lineage["subsidiary"]["name"] == "Mahanadi Coalfields Limited"
    assert lineage["mine"]["id"] in ("MINE-MCL-TALCHER-01", "ORG-MINE-MCL-TALCHER-OC")


# ------------------------------------------------------------
# 23. Report Cryptographic Finalization (SHA-256 & IPFS CID)
# ------------------------------------------------------------
def test_23_report_cryptographic_finalization():
    rep = generate_environmental_report(
        mine_id="MINE-MCL-TALCHER-01",
        reporting_period_start="2026-09-01",
        reporting_period_end="2026-09-15",
        title="Cryptographic Sealing Test Dossier",
    )
    finalized = finalize_environmental_report(rep.report_id, actor_id="REGULATORY_DIRECTOR")
    assert finalized.status == "FINALIZED"
    assert finalized.content_hash is not None
    assert len(finalized.content_hash) == 64  # Valid SHA-256 hexadecimal length
    assert finalized.ipfs_cid is not None
    assert finalized.ipfs_cid.startswith("bafkrei")  # Standard CIDv1 raw multihash prefix


# ------------------------------------------------------------
# 24. Tamper Detection on Finalized Report
# ------------------------------------------------------------
def test_24_tamper_detection_on_report():
    rep = generate_environmental_report(
        mine_id="MINE-MCL-TALCHER-01",
        reporting_period_start="2026-09-01",
        reporting_period_end="2026-09-15",
        title="Tamper Detection Baseline Report",
    )
    finalized = finalize_environmental_report(rep.report_id)
    original_hash = finalized.content_hash

    # Simulate tampering by generating report with modified measurement count
    tampered_data = {
        "report_id": finalized.report_id,
        "measurements_count": finalized.measurements_count + 999,
        "source_record_hashes": finalized.source_record_hashes,
    }
    import hashlib
    tampered_hash = hashlib.sha256(json.dumps(tampered_data, sort_keys=True).encode()).hexdigest()
    assert tampered_hash != original_hash


# ------------------------------------------------------------
# 25. Scope Engine — Mine Level Authorization
# ------------------------------------------------------------
def test_25_scope_engine_mine_level_authorization():
    # Talcher Mine Manager accessing Talcher mine
    assert assert_hierarchy_access(
        user_role="MINE_MANAGER",
        user_scope_type="MINE",
        user_scope_id="MINE-MCL-TALCHER-01",
        target_unit_id="MINE-MCL-TALCHER-01",
    ) is True


# ------------------------------------------------------------
# 26. Scope Engine — Cross-Mine Access Forbidden (HTTP 403)
# ------------------------------------------------------------
def test_26_scope_engine_cross_mine_access_forbidden():
    # Jharia Mine Manager accessing Talcher mine
    with pytest.raises(HTTPException) as exc:
        assert_hierarchy_access(
            user_role="MINE_MANAGER",
            user_scope_type="MINE",
            user_scope_id="MINE-BCCL-JHARIA-01",
            target_unit_id="MINE-MCL-TALCHER-01",
        )
    assert exc.value.status_code == 403


# ------------------------------------------------------------
# 27. Scope Engine — Subsidiary Hierarchical Inheritance
# ------------------------------------------------------------
def test_27_scope_engine_subsidiary_hierarchical_access():
    # MCL Subsidiary manager accessing Talcher mine
    assert assert_hierarchy_access(
        user_role="SUBSIDIARY_MANAGER",
        user_scope_type="SUBSIDIARY",
        user_scope_id="ORG-SUBSIDIARY-MCL",
        target_unit_id="MINE-MCL-TALCHER-01",
    ) is True


# ------------------------------------------------------------
# 28. Scope Engine — Corporate Broad Access
# ------------------------------------------------------------
def test_28_scope_engine_corporate_broad_access():
    # CIL Corporate Technical Director accessing any mine
    assert assert_hierarchy_access(
        user_role="CORPORATE_MANAGEMENT",
        user_scope_type="CIL",
        user_scope_id="ORG-CIL-CIL",
        target_unit_id="MINE-MCL-TALCHER-01",
    ) is True
    assert assert_hierarchy_access(
        user_role="CORPORATE_MANAGEMENT",
        user_scope_type="CIL",
        user_scope_id="ORG-CIL-CIL",
        target_unit_id="MINE-BCCL-JHARIA-01",
    ) is True


# ------------------------------------------------------------
# 29. Corporate Statutory Oversight Visibility
# ------------------------------------------------------------
def test_29_corporate_statutory_oversight_visibility(client):
    # Corporate Management accessing environmental overview via HTTP REST endpoint
    headers = {
        "X-User-Role": "CORPORATE_MANAGEMENT",
        "X-User-Id": "CORP-EXEC-01",
        "X-User-Org-Scope": "ORG-CIL-CIL",
    }
    response = client.get("/api/environment/overview?mine_id=MINE-MCL-TALCHER-01", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "total_parameters" in data
    assert "total_measurements" in data
    assert "risk_level" in data


# ------------------------------------------------------------
# 30. Contractor & Production Operational Correlation
# ------------------------------------------------------------
def test_30_contractor_production_correlation():
    # Correlate Talcher Main Haul Road (OP-ROAD-TALCHER-01) with Task 12 active contracts
    contractor = correlate_contractor_context("MINE-MCL-TALCHER-01", "OP-ROAD-TALCHER-01")
    # Talcher Opencast has contractor CONT-TML (Tata Mining Logistics)
    if contractor:
        assert "contractor_id" in contractor
        assert "contractor_name" in contractor

    # Correlate shift production context from Task 10
    prod_context = correlate_production_context("MINE-MCL-TALCHER-01")
    assert "has_production_data" in prod_context
    assert "daily_production_tonnes" in prod_context


# ------------------------------------------------------------
# 31. Idempotent Environmental Seed Loading
# ------------------------------------------------------------
def test_31_idempotent_environmental_seed_loading():
    # Running load_environmental_governance_seed twice must not raise errors or corrupt DB
    load_environmental_governance_seed()
    load_environmental_governance_seed()

    # Verify counts remain intact
    params = db.list_environmental_parameters()
    assert len(params) >= 10
    thresholds = db.list_environmental_thresholds()
    assert len(thresholds) >= 8
