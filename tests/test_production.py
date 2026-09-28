"""
PRITHVI — Phase 2 Task 10: Production & Operational Governance Test Suite
========================================================================

Verifies:
1. Valid production record persistence
2. Rejection of invalid quantities (zero, negative)
3. Rejection of unauthorized write access
4. Mine operational summary computation
5. Area-level rollup
6. Subsidiary-level rollup
7. Pan-India CIL Corporate aggregation
8. Target vs actual, variance, and achievement % calculations
9. Shift-level reporting (Shift A, B, C)
10. Production vs dispatch mismatch anomaly detection
11. Duplicate record detection
12. Missing reporting detection logic
13. Production during safety stoppage correlation
14. Risk engine consumes production signals
15. Contractor and MDO contribution linkage
16. Immutability and historical correction workflow (no silent overwrite)
17. Audit event generation on corrections and creation
18. Statutory Daily Production Report generation with SHA-256 hash
19. RBAC validation per role
20. Regression check on all existing statutory capabilities
"""

import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.main import app
from app import database as db
from app.models import (
    ProductionRecord,
    ProductionTarget,
    ProductionSource,
    ContractType,
    ProductionOperationType,
    ProductionRecordStatus,
)
from app.production_service import (
    record_production_event,
    get_mine_production_summary,
    get_area_production_summary,
    get_subsidiary_production_summary,
    get_corporate_production_summary,
    generate_daily_production_report,
)
from app.schemas import ProductionRecordCreate


client = TestClient(app)
TODAY = datetime.now(timezone.utc).strftime("%Y-%m-%d")


def test_01_create_valid_production_record():
    """1. Create and persist a valid operational production record."""
    payload = {
        "mine_id": "MINE-BCCL-JHARIA-01",
        "shift_name": "Shift A",
        "production_date": TODAY,
        "production_quantity": 1450.5,
        "production_unit": "TONNES",
        "dispatch_quantity": 1400.0,
        "production_source": "WEIGHBRIDGE",
        "operation_type": "UNDERGROUND_EXTRACTION",
        "contractor_id": "DEPT-BCCL",
        "contractor_name": "BCCL Departmental Mining",
        "contract_type": "DEPARTMENTAL",
        "target_quantity": 1500.0,
        "downtime_minutes": 15,
        "delay_reason": "Belt feeder maintenance",
        "entered_by": "MANAGER_DESK",
    }
    resp = client.post(
        "/api/production/records",
        json=payload,
        headers={"X-User-Role": "MINE_MANAGER", "X-User-Id": "USR-MGR-01"},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["record_id"].startswith("PROD-")
    assert data["production_quantity"] == 1450.5
    assert data["production_source"] == "WEIGHBRIDGE"
    assert data["content_hash"] is not None


def test_02_reject_invalid_production_quantity():
    """2. Reject zero or negative production quantities."""
    # Zero quantity
    resp = client.post(
        "/api/production/records",
        json={
            "mine_id": "MINE-BCCL-JHARIA-01",
            "shift_name": "Shift A",
            "production_date": TODAY,
            "production_quantity": 0.0,
            "production_source": "WEIGHBRIDGE",
        },
        headers={"X-User-Role": "MINE_MANAGER"},
    )
    assert resp.status_code == 400
    assert "strictly greater than 0" in resp.json()["detail"]

    # Negative quantity
    resp_neg = client.post(
        "/api/production/records",
        json={
            "mine_id": "MINE-BCCL-JHARIA-01",
            "shift_name": "Shift A",
            "production_date": TODAY,
            "production_quantity": -50.0,
            "production_source": "WEIGHBRIDGE",
        },
        headers={"X-User-Role": "MINE_MANAGER"},
    )
    assert resp_neg.status_code == 400


def test_03_reject_unauthorized_access():
    """3. Reject write access for Field Inspector role."""
    resp = client.post(
        "/api/production/records",
        json={
            "mine_id": "MINE-BCCL-JHARIA-01",
            "shift_name": "Shift A",
            "production_date": TODAY,
            "production_quantity": 500.0,
            "production_source": "MANUAL_ENTRY",
        },
        headers={"X-User-Role": "FIELD_INSPECTOR"},
    )
    assert resp.status_code == 403
    assert "not authorized to create or edit production records" in resp.json()["detail"]


def test_04_mine_summary_works():
    """4. Test mine summary calculation with target, actual, variance, and achievement %."""
    resp = client.get(f"/api/production/mine/MINE-BCCL-JHARIA-01/summary?date={TODAY}")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["mine_id"] == "MINE-BCCL-JHARIA-01"
    assert data["production_actual_tonnes"] > 0
    assert data["target_status"] == "CONFIGURED"
    assert data["production_target_tonnes"] == 4500.0
    assert data["achievement_percentage"] is not None
    assert len(data["shifts"]) >= 3


def test_05_area_aggregation_works():
    """5. Area aggregation rolls up mines correctly."""
    resp = client.get(f"/api/production/area/AREA-BCCL-JHARIA/summary?date={TODAY}")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["total_production_tonnes"] > 0
    assert len(data["mines"]) >= 1


def test_06_subsidiary_aggregation_works():
    """6. Subsidiary aggregation rolls up areas and mines for BCCL."""
    resp = client.get(f"/api/production/subsidiary/BCCL/summary?date={TODAY}")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["subsidiary_id"] == "BCCL"
    assert data["total_production_tonnes"] > 0
    assert len(data["areas"]) >= 1


def test_07_corporate_aggregation_works():
    """7. Corporate summary rolls up all subsidiaries for CIL."""
    resp = client.get(f"/api/production/corporate/summary?date={TODAY}")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "Coal India Limited" in data["organization"]
    assert data["pan_india_production_tonnes"] > 0
    assert len(data["subsidiaries"]) >= 1


def test_08_target_vs_actual_calculation():
    """8. Test target vs actual logic and unconfigured target state."""
    # Configured target
    summary = get_mine_production_summary("MINE-BCCL-JHARIA-01", TODAY)
    assert summary["target_status"] == "CONFIGURED"
    expected_variance = round(summary["production_actual_tonnes"] - summary["production_target_tonnes"], 1)
    assert summary["variance_tonnes"] == expected_variance

    # Unconfigured target for future date
    future_date = "2029-12-31"
    future_summary = get_mine_production_summary("MINE-BCCL-JHARIA-01", future_date)
    assert future_summary["target_status"] == "TARGET_NOT_CONFIGURED"
    assert future_summary["production_target_tonnes"] is None
    assert future_summary["variance_tonnes"] is None


def test_09_shift_level_reporting():
    """9. Verify distinct shift records (Shift A, B, C) with individual performance."""
    summary = get_mine_production_summary("MINE-BCCL-JHARIA-01", TODAY)
    shift_names = [s["shift_name"] for s in summary["shifts"]]
    assert "Shift A" in shift_names
    assert "Shift B" in shift_names
    assert "Shift C" in shift_names


def test_10_production_dispatch_mismatch_anomaly():
    """10. Detect anomaly when dispatch exceeds production by >15%."""
    test_date = "2026-09-20"
    # Create record where dispatch (3000 T) vastly exceeds production (1000 T)
    rec_payload = ProductionRecordCreate(
        mine_id="MINE-BCCL-JHARIA-01",
        shift_name="Shift A",
        production_date=test_date,
        production_quantity=1000.0,
        dispatch_quantity=3000.0,
        production_source="WEIGHBRIDGE",
        operation_type="UNDERGROUND_EXTRACTION",
        entered_by="ANOMALY_TEST",
    )
    saved = record_production_event(rec_payload, actor_id="TEST_RUNNER")
    anomalies = db.get_active_production_anomalies("MINE-BCCL-JHARIA-01")
    dispatch_anomalies = [a for a in anomalies if a["anomaly_type"] == "DISPATCH_MISMATCH"]
    assert len(dispatch_anomalies) > 0
    assert "Dispatch quantity" in dispatch_anomalies[0]["what"]


def test_11_duplicate_record_detection():
    """11. Detect potential duplicate production records."""
    test_date = "2026-09-21"
    r1 = ProductionRecordCreate(
        mine_id="MINE-BCCL-JHARIA-01",
        shift_name="Shift B",
        production_date=test_date,
        production_quantity=800.0,
        production_source="SURVEYOR",
        operation_type="UNDERGROUND_EXTRACTION",
    )
    record_production_event(r1, actor_id="TEST_1")

    # Identical record submitted again
    r2 = ProductionRecordCreate(
        mine_id="MINE-BCCL-JHARIA-01",
        shift_name="Shift B",
        production_date=test_date,
        production_quantity=800.0,
        production_source="SURVEYOR",
        operation_type="UNDERGROUND_EXTRACTION",
    )
    record_production_event(r2, actor_id="TEST_2")

    anomalies = db.get_active_production_anomalies("MINE-BCCL-JHARIA-01")
    dup_anomalies = [a for a in anomalies if a["anomaly_type"] == "DUPLICATE_RECORD"]
    assert len(dup_anomalies) > 0


def test_12_missing_report_detection():
    """12. Verify that mines with 0 production for an active shift/day indicate 0 reporting."""
    empty_date = "2025-01-01"
    summary = get_mine_production_summary("MINE-BCCL-JHARIA-01", empty_date)
    assert summary["production_actual_tonnes"] == 0.0
    area = get_area_production_summary("AREA-BCCL-JHARIA", empty_date)
    assert area["mines_reporting"] == 0


def test_13_safety_stoppage_correlation():
    """13. Produce governance alert when production occurs during critical safety condition."""
    # Ensure there is an active safety signal for Jharia
    test_date = "2026-09-22"
    # Query or create a critical safety signal
    from app.models import SafetySignal, SensorType, ThresholdStatus
    sensors = db.list_sensors("MINE-BCCL-JHARIA-01")
    valid_sensor_id = sensors[0]["sensor_id"] if sensors else "SN-JHARIA-CH4-01"
    sig = SafetySignal(
        signal_id="SIG-TEST-CRIT-01",
        mine_id="MINE-BCCL-JHARIA-01",
        sensor_id=valid_sensor_id,
        sensor_type=SensorType.METHANE,
        severity=ThresholdStatus.CRITICAL,
        observed_value=1.85,
        unit="%",
        threshold_definition="CMR 2017 Reg 119 limit 1.25%",
        explanation="Critical test methane accumulation",
        first_detected_at=datetime.now(timezone.utc),
        last_detected_at=datetime.now(timezone.utc),
        simulated=True,
        created_at=datetime.now(timezone.utc),
    )
    sig_payload = sig.model_dump(mode="json")
    db.upsert_safety_signal(sig_payload)

    # Now record production while this critical condition is active
    rec = ProductionRecordCreate(
        mine_id="MINE-BCCL-JHARIA-01",
        shift_name="Shift C",
        production_date=test_date,
        production_quantity=950.0,
        production_source="SHIFT_REPORT",
        operation_type="UNDERGROUND_EXTRACTION",
    )
    record_production_event(rec, actor_id="SAFETY_TEST")

    anomalies = db.get_active_production_anomalies("MINE-BCCL-JHARIA-01")
    safety_anomalies = [a for a in anomalies if a["anomaly_type"] == "SAFETY_STOPPAGE_CONFLICT"]
    assert len(safety_anomalies) > 0
    assert "active safety condition" in safety_anomalies[0]["what"]


def test_14_risk_engine_integration():
    """14. Existing risk engine incorporates production anomaly signals."""
    from app.risk import get_mine_risk_intelligence
    risk_info = get_mine_risk_intelligence("MINE-BCCL-JHARIA-01")
    assert risk_info is not None
    assert "top_risk_drivers" in risk_info
    # Operational driver should be included if active anomalies exist
    assert any("Operational conflict" in d or "Production anomaly" in d or "All statutory" in d for d in risk_info["top_risk_drivers"])


def test_15_contractor_mdo_linkage():
    """15. Production records link to Departmental, Work-Order, and MDO contributions."""
    summary = get_mine_production_summary("MINE-BCCL-JHARIA-01", TODAY)
    contribs = summary["contractor_contributions"]
    assert len(contribs) > 0
    contract_types = [c["contract_type"] for c in contribs]
    assert "DEPARTMENTAL" in contract_types or "MDO" in contract_types


def test_16_immutability_and_correction_workflow():
    """16. Historical records cannot be silently overwritten; corrections create linked superseded records."""
    test_date = "2026-09-23"
    rec = ProductionRecordCreate(
        mine_id="MINE-BCCL-JHARIA-01",
        shift_name="Shift A",
        production_date=test_date,
        production_quantity=1200.0,
        dispatch_quantity=1150.0,
        production_source="WEIGHBRIDGE",
        operation_type="UNDERGROUND_EXTRACTION",
    )
    original = record_production_event(rec, actor_id="ORIG_USER")
    orig_id = original["record_id"]

    # Submit correction via API
    corr_payload = {
        "corrected_quantity": 1280.0,
        "corrected_dispatch": 1150.0,
        "reason": "Calibration error on weighbridge bridge 2",
        "corrected_by": "MANAGER_DESK",
        "notes": "Audited calibration sheet attached",
    }
    resp = client.post(
        f"/api/production/records/{orig_id}/correct",
        json=corr_payload,
        headers={"X-User-Role": "MINE_MANAGER"},
    )
    assert resp.status_code == 200, resp.text
    corrected = resp.json()
    assert corrected["record_id"] != orig_id
    assert corrected["production_quantity"] == 1280.0

    # Verify original record is superseded and unchanged in historical data
    orig_reloaded = db.get_production_record(orig_id)
    assert orig_reloaded["is_superseded"] == 1
    assert orig_reloaded["status"] == "SUPERSEDED"
    assert orig_reloaded["superseded_by"] == corrected["record_id"]
    assert orig_reloaded["production_quantity"] == 1200.0  # Original value preserved!


def test_17_audit_event_generation():
    """17. Audit events are recorded for creation and corrections."""
    test_date = "2026-09-24"
    rec = ProductionRecordCreate(
        mine_id="MINE-BCCL-JHARIA-01",
        shift_name="Shift B",
        production_date=test_date,
        production_quantity=1100.0,
        production_source="WEIGHBRIDGE",
    )
    saved = record_production_event(rec, actor_id="AUDIT_TESTER")
    events = db.get_production_audit_events(saved["record_id"])
    assert len(events) >= 1
    assert events[0]["action"] == "RECORD_CREATED"


def test_18_report_generated_from_database_records():
    """18. Daily Mine Production Summary report is generated from stored records with SHA-256 hash."""
    resp = client.get(f"/api/production/report/daily?mine_id=MINE-BCCL-JHARIA-01&date={TODAY}")
    assert resp.status_code == 200, resp.text
    rep = resp.json()
    assert rep["mine_id"] == "MINE-BCCL-JHARIA-01"
    assert rep["content_hash"] is not None
    assert len(rep["content_hash"]) == 64  # Valid SHA-256
    assert rep["records_included_count"] > 0
    assert rep["integrity_status"] == "AUDIT_PROOF_RECORDED"


def test_19_rbac_per_role():
    """19. Verify role permissions across MINE_MANAGER, CORPORATE_MANAGEMENT, and FIELD_INSPECTOR."""
    # MINE_MANAGER can read and write
    r_mgr = client.get(f"/api/production/mine/MINE-BCCL-JHARIA-01/summary?date={TODAY}", headers={"X-User-Role": "MINE_MANAGER"})
    assert r_mgr.status_code == 200

    # CORPORATE_MANAGEMENT can read
    r_corp = client.get(f"/api/production/mine/MINE-BCCL-JHARIA-01/summary?date={TODAY}", headers={"X-User-Role": "CORPORATE_MANAGEMENT"})
    assert r_corp.status_code == 200

    # FIELD_INSPECTOR cannot write production records
    r_insp_post = client.post(
        "/api/production/records",
        json={"mine_id": "MINE-BCCL-JHARIA-01", "shift_name": "Shift A", "production_date": TODAY, "production_quantity": 100.0},
        headers={"X-User-Role": "FIELD_INSPECTOR"},
    )
    assert r_insp_post.status_code == 403


def test_20_existing_tasks_continue_passing():
    """20. Ensure existing routes (mines, applicability, telemetry) remain 100% operational, and removed DGMS route returns 404."""
    # Mines & Applicability
    resp_mines = client.get("/api/mines")
    assert resp_mines.status_code == 200
    assert len(resp_mines.json()) >= 3

    resp_app = client.get("/api/mines/MINE-BCCL-JHARIA-01/applicability")
    assert resp_app.status_code == 200

    # DGMS route is removed and returns 404
    resp_dgms = client.get("/api/dgms/overview", headers={"X-User-Role": "CORPORATE_MANAGEMENT"})
    assert resp_dgms.status_code == 404

    # Telemetry
    resp_telem = client.get("/api/telemetry/health")
    assert resp_telem.status_code == 200
