"""
PRITHVI Phase 2 Task 9 — Telemetry & SCADA Safety Intelligence Test Suite.
Verifies SCADA telemetry ingestion, statutory threshold evaluation, signal deduplication,
incident case synthesis, risk engine elevation, recovery lifecycle, and health endpoints.
"""

import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.main import app
from app import database as db
from app.models import (
    SensorType,
    ThresholdStatus,
    SignalStatus,
)
from app.safety_engine import (
    evaluate_sensor_reading,
    validate_reading_bounds,
)
from app.telemetry_service import (
    ingest_telemetry_reading,
    ingest_telemetry_batch,
    get_latest_mine_telemetry,
)
from app.risk import get_mine_risk_intelligence
from scada_simulator.scenarios import SCENARIOS, build_scenario_payload
from scada_simulator.config import SENSOR_CATALOG

client = TestClient(app)

JHARIA_MINE_ID = "MINE-BCCL-JHARIA-01"


# ============================================================
# 1. SENSOR SEED REGISTRATION & CATALOG
# ============================================================

def test_sensor_seed_registered():
    """Verify all 7 sensor types are registered for Jharia with correct units."""
    sensors = db.list_sensors(mine_id=JHARIA_MINE_ID)
    assert len(sensors) >= 7
    sensor_types = {s["sensor_type"] for s in sensors}
    expected = {
        "METHANE",
        "AIRFLOW",
        "VENTILATION_FAN",
        "DUST",
        "SLOPE_DISPLACEMENT",
        "PORE_PRESSURE",
        "RAINFALL",
    }
    assert expected.issubset(sensor_types)
    for s in sensors:
        assert s["simulated"] == 1 or s["simulated"] is True
        assert s["status"] == "ACTIVE"


# ============================================================
# 2. INGESTION OF VALID READINGS
# ============================================================

def test_telemetry_ingestion_valid_reading():
    """Verify single valid normal reading ingestion via service."""
    res = ingest_telemetry_reading({
        "sensor_code": "CH4-JHARIA-01",
        "mine_id": JHARIA_MINE_ID,
        "sensor_type": "METHANE",
        "value": 0.35,
        "unit": "%",
        "quality": "GOOD",
    })
    assert res["reading_id"].startswith("TLM-")
    assert res["threshold_status"] == "NORMAL"
    assert res["value"] == 0.35
    assert res["simulated"] is True


def test_telemetry_ingestion_batch():
    """Verify batch ingestion of multiple sensors."""
    batch = [
        {"sensor_code": "CH4-JHARIA-01", "mine_id": JHARIA_MINE_ID, "sensor_type": "METHANE", "value": 0.40, "unit": "%"},
        {"sensor_code": "AIR-JHARIA-01", "mine_id": JHARIA_MINE_ID, "sensor_type": "AIRFLOW", "value": 25.0, "unit": "m³/s"},
    ]
    res = ingest_telemetry_batch(batch)
    assert res["success"] is True
    assert res["ingested_count"] == 2
    assert res["evaluated_signals_count"] == 2


# ============================================================
# 3. SERVER-SIDE VALIDATION CHECKS
# ============================================================

def test_telemetry_validation_unknown_sensor():
    """Verify rejection of unregistered sensor code."""
    with pytest.raises(ValueError, match="not registered"):
        ingest_telemetry_reading({
            "sensor_code": "SN-UNKNOWN-99",
            "mine_id": JHARIA_MINE_ID,
            "sensor_type": "METHANE",
            "value": 0.5,
            "unit": "%",
        })


def test_telemetry_validation_mine_mismatch():
    """Verify rejection when sensor belongs to a different mine."""
    with pytest.raises(ValueError, match="belongs to mine"):
        ingest_telemetry_reading({
            "sensor_code": "CH4-JHARIA-01",
            "mine_id": "MINE-ECL-RANIGANJ-01",
            "sensor_type": "METHANE",
            "value": 0.5,
            "unit": "%",
        })


def test_telemetry_validation_type_mismatch():
    """Verify rejection when sensor_type does not match registered sensor."""
    with pytest.raises(ValueError, match="registered as"):
        ingest_telemetry_reading({
            "sensor_code": "CH4-JHARIA-01",
            "mine_id": JHARIA_MINE_ID,
            "sensor_type": "AIRFLOW",
            "value": 20.0,
            "unit": "m³/s",
        })


def test_telemetry_validation_impossible_bounds():
    """Verify rejection of physically impossible sensor values."""
    with pytest.raises(ValueError, match="physical sensor bounds"):
        ingest_telemetry_reading({
            "sensor_code": "CH4-JHARIA-01",
            "mine_id": JHARIA_MINE_ID,
            "sensor_type": "METHANE",
            "value": -5.0,
            "unit": "%",
        })


def test_telemetry_validation_unit_mismatch():
    """Verify rejection when reading unit does not match sensor unit."""
    with pytest.raises(ValueError, match="Unit mismatch"):
        ingest_telemetry_reading({
            "sensor_code": "CH4-JHARIA-01",
            "mine_id": JHARIA_MINE_ID,
            "sensor_type": "METHANE",
            "value": 0.5,
            "unit": "PPM",
        })


# ============================================================
# 4. STATUTORY THRESHOLD EVALUATION (CMR 2017)
# ============================================================

def test_methane_warning_threshold():
    """CMR 2017 Reg 119: Methane between 0.8% and 1.25% triggers WARNING."""
    eval_res = evaluate_sensor_reading("METHANE", 0.95)
    assert eval_res.status == ThresholdStatus.WARNING
    assert "0.8%" in eval_res.threshold_definition
    assert eval_res.is_statutory is True


def test_methane_critical_statutory_threshold():
    """CMR 2017 Reg 156: Methane >= 1.25% triggers CRITICAL + Compliance Case."""
    res = ingest_telemetry_reading({
        "sensor_code": "CH4-JHARIA-01",
        "mine_id": JHARIA_MINE_ID,
        "sensor_type": "METHANE",
        "value": 1.72,
        "unit": "%",
    })
    assert res["threshold_status"] == "CRITICAL"
    
    # Active signal should be in DB
    signal = db.get_active_signal_for_sensor(res["sensor_id"])
    assert signal is not None
    assert signal["severity"] == "CRITICAL"
    assert signal["status"] == "ACTIVE"
    assert signal["linked_case_id"] is not None

    # Linked compliance case should exist with source_type SCADA_TELEMETRY
    case = db.get_compliance_case(signal["linked_case_id"])
    assert case is not None
    assert case["source_type"] == "SCADA_TELEMETRY"
    assert case["severity"] == "CRITICAL"
    assert case["status"] == "OPEN"


def test_airflow_critical_statutory_threshold():
    """CMR 2017 Reg 119: Airflow < 8.0 m³/s triggers CRITICAL."""
    eval_res = evaluate_sensor_reading("AIRFLOW", 6.5)
    assert eval_res.status == ThresholdStatus.CRITICAL
    assert eval_res.is_statutory is True
    assert "statutory dilution failure" in eval_res.explanation.lower()


def test_ventilation_fan_critical():
    """Ventilation fan < 500 RPM triggers CRITICAL signal."""
    eval_res = evaluate_sensor_reading("VENTILATION_FAN", 450.0)
    assert eval_res.status == ThresholdStatus.CRITICAL
    assert "500 RPM" in eval_res.threshold_definition


def test_dust_concentration_critical():
    """CMR 2017 Reg 124: Respirable dust >= 3.0 mg/m³ triggers CRITICAL."""
    eval_res = evaluate_sensor_reading("DUST", 3.4)
    assert eval_res.status == ThresholdStatus.CRITICAL
    assert "CMR 2017" in (eval_res.regulation_reference or "")


def test_slope_displacement_critical():
    """Slope displacement >= 50 mm triggers CRITICAL highwall alert."""
    eval_res = evaluate_sensor_reading("SLOPE_DISPLACEMENT", 58.0)
    assert eval_res.status == ThresholdStatus.CRITICAL
    assert "50.0 mm" in eval_res.threshold_definition


# ============================================================
# 5. DEDUPLICATION & RECOVERY LIFECYCLE
# ============================================================

def test_signal_deduplication():
    """Subsequent critical readings update consecutive count without duplicate cases."""
    # First pulse
    res1 = ingest_telemetry_reading({
        "sensor_code": "CH4-JHARIA-01",
        "mine_id": JHARIA_MINE_ID,
        "sensor_type": "METHANE",
        "value": 1.65,
        "unit": "%",
    })
    sig1 = db.get_active_signal_for_sensor(res1["sensor_id"])
    assert sig1 is not None
    case1_id = sig1.get("linked_case_id")
    count1 = sig1.get("consecutive_readings", 1)

    # Second pulse while condition persists
    res2 = ingest_telemetry_reading({
        "sensor_code": "CH4-JHARIA-01",
        "mine_id": JHARIA_MINE_ID,
        "sensor_type": "METHANE",
        "value": 1.70,
        "unit": "%",
    })
    sig2 = db.get_active_signal_for_sensor(res2["sensor_id"])
    assert sig2["signal_id"] == sig1["signal_id"]
    assert sig2["consecutive_readings"] > count1
    assert sig2.get("linked_case_id") == case1_id


def test_sensor_recovery_lifecycle():
    """Normal reading marks signal as RECOVERED, but leaves case OPEN for human review."""
    # Trigger critical
    ingest_telemetry_reading({
        "sensor_code": "CH4-JHARIA-01",
        "mine_id": JHARIA_MINE_ID,
        "sensor_type": "METHANE",
        "value": 1.80,
        "unit": "%",
    })
    sensor = db.get_sensor_by_code("CH4-JHARIA-01")
    sig = db.get_active_signal_for_sensor(sensor["sensor_id"])
    assert sig is not None
    linked_case_id = sig["linked_case_id"]

    # Now recover sensor to safe normal level
    ingest_telemetry_reading({
        "sensor_code": "CH4-JHARIA-01",
        "mine_id": JHARIA_MINE_ID,
        "sensor_type": "METHANE",
        "value": 0.30,
        "unit": "%",
    })

    # Active signal should now be cleared
    active_now = db.get_active_signal_for_sensor(sensor["sensor_id"])
    assert active_now is None

    # Case must REMAIN OPEN for human review under CMR statutory rules
    case = db.get_compliance_case(linked_case_id)
    assert case is not None
    assert case["status"] == "OPEN"


# ============================================================
# 6. RISK ENGINE INTEGRATION
# ============================================================

def test_risk_engine_telemetry_integration():
    """Active critical telemetry elevates Ventilation & Gas domain risk."""
    # Ensure a critical methane signal is active
    ingest_telemetry_reading({
        "sensor_code": "CH4-JHARIA-01",
        "mine_id": JHARIA_MINE_ID,
        "sensor_type": "METHANE",
        "value": 1.85,
        "unit": "%",
    })

    risk = get_mine_risk_intelligence(JHARIA_MINE_ID)
    assert risk is not None
    cat_risk = next((c for c in risk["categories"] if c["category"] == "Ventilation & Gas"), None)
    assert cat_risk is not None
    # Risk level elevated to CRITICAL due to live statutory breach
    assert cat_risk["risk_level"] == "CRITICAL"
    # Explainable drivers include telemetry signal notice
    driver_texts = " ".join(cat_risk["drivers"])
    assert "Live SCADA Telemetry Signal" in driver_texts or "Methane" in driver_texts

    # Cleanup: restore to normal
    ingest_telemetry_reading({
        "sensor_code": "CH4-JHARIA-01",
        "mine_id": JHARIA_MINE_ID,
        "sensor_type": "METHANE",
        "value": 0.35,
        "unit": "%",
    })


# ============================================================
# 7. SCADA SIMULATOR SCENARIOS & API ENDPOINTS
# ============================================================

def test_scada_simulator_scenario_payloads():
    """Verify simulator scenarios build valid structured readings."""
    sensors = SENSOR_CATALOG[JHARIA_MINE_ID]
    for sc_key in SCENARIOS.keys():
        payload = build_scenario_payload(sc_key, JHARIA_MINE_ID, sensors)
        assert len(payload) == len(sensors)
        for item in payload:
            assert item["simulated"] is True
            assert item["quality"] == "GOOD"
            assert "value" in item
            assert "unit" in item


def test_telemetry_health_endpoint():
    """Verify /api/telemetry/health returns operational status."""
    res = client.get("/api/telemetry/health")
    assert res.status_code == 200
    data = res.json()
    assert data["source"] == "SIMULATED"
    assert data["status"] == "OPERATIONAL"
    assert data["total_sensors_configured"] >= 7
    assert data["total_readings_stored"] >= 1


def test_api_telemetry_mine_endpoints():
    """Verify /api/telemetry/mine/{mine_id} and latest endpoints."""
    res_latest = client.get(f"/api/telemetry/mine/{JHARIA_MINE_ID}/latest")
    assert res_latest.status_code == 200
    assert isinstance(res_latest.json(), list)

    res_signals = client.get(f"/api/telemetry/mine/{JHARIA_MINE_ID}/signals")
    assert res_signals.status_code == 200
    assert isinstance(res_signals.json(), list)
