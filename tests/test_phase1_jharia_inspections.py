import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.main import app

client = TestClient(app)

EXPECTED_CATEGORIES = {
    "Ventilation & Gas": 3,
    "Shaft & Winding": 2,
    "Electrical": 2,
    "HEMM": 2,
    "Blasting": 2,
    "Roof / Strata": 1,
    "Water / Drainage": 1,
}

EXPECTED_TEMPLATES = [
    "PRE-SHIFT-METHANE-CHECK",
    "WEEKLY-VENTILATION-SURVEY",
    "MONTHLY-VENTILATION-INSPECTION",
    "WEEKLY-SHAFT-EXAMINATION",
    "MONTHLY-WINDING-INSTALLATION",
    "WEEKLY-ELECTRICAL-INSPECTION",
    "MONTHLY-ELECTRICAL-INSTALLATION",
    "DAILY-HEMM-PRESTART",
    "WEEKLY-HEMM-INSPECTION",
    "PRE-BLASTING-INSPECTION",
    "POST-BLASTING-INSPECTION",
    "DAILY-ROOF-INSPECTION",
    "WEEKLY-PUMPING-STATION",
]

def test_jharia_mine_profile():
    res = client.get("/api/mines/MINE-BCCL-JHARIA-01")
    assert res.status_code == 200
    mine = res.json()
    assert mine["mine_id"] == "MINE-BCCL-JHARIA-01"
    assert mine["gassy_degree"].lower() == "degree_ii"
    assert mine["uses_hemm"] is True

def test_13_templates_exist_and_match_categories():
    res = client.get("/api/inspection-templates")
    assert res.status_code == 200
    templates = res.json()
    
    assert len(templates) == 13, f"Expected 13 templates, got {len(templates)}"
    template_ids = [t["template_id"] for t in templates]
    for expected_id in EXPECTED_TEMPLATES:
        assert expected_id in template_ids, f"Missing template: {expected_id}"
    
    # Check category distribution
    counts = {}
    for t in templates:
        cat = t.get("inspection_family")
        counts[cat] = counts.get(cat, 0) + 1
        
        # Verify metadata fields are present and not empty
        assert t.get("responsible_role"), f"Missing responsible_role in {t['template_id']}"
        assert t.get("frequency_label"), f"Missing frequency_label in {t['template_id']}"
        assert t.get("regulation_reference"), f"Missing regulation_reference in {t['template_id']}"
        assert len(t.get("measurements", [])) > 0, f"No measurements in {t['template_id']}"
        assert len(t.get("checklist", [])) > 0, f"No checklist in {t['template_id']}"
        assert len(t.get("evidence_requirements", [])) > 0, f"No evidence requirements in {t['template_id']}"

    assert counts == EXPECTED_CATEGORIES, f"Category count mismatch: {counts} vs {EXPECTED_CATEGORIES}"

def test_mine_templates_endpoint():
    res = client.get("/api/mines/MINE-BCCL-JHARIA-01/templates")
    assert res.status_code == 200
    templates = res.json()
    assert len(templates) == 13

def test_13_schedules_generated_for_jharia():
    res = client.get("/api/mines/MINE-BCCL-JHARIA-01/schedule")
    assert res.status_code == 200
    data = res.json()
    schedules = data.get("schedules", [])
    assert len(schedules) == 13, f"Expected 13 schedules for Jharia, got {len(schedules)}"
    
    for s in schedules:
        assert s.get("template_name") is not None
        assert s.get("inspection_family") in EXPECTED_CATEGORIES
        assert s.get("responsible_role") is not None
        assert s.get("frequency_label") is not None

def test_inspection_lifecycle_and_submission():
    # 1. Fetch schedules to get an instance
    sched_res = client.get("/api/mines/MINE-BCCL-JHARIA-01/schedule")
    assert sched_res.status_code == 200
    schedules = sched_res.json().get("schedules", [])
    
    # Pick PRE-SHIFT-METHANE-CHECK schedule
    methane_sched = next((s for s in schedules if s.get("template_id") == "PRE-SHIFT-METHANE-CHECK"), schedules[0])
    
    # 2. Create inspection
    create_payload = {
        "mine_id": "MINE-BCCL-JHARIA-01",
        "template_id": methane_sched["template_id"],
        "obligation_id": "CMR-119",
        "inspector_id": "INSP-TEST-001",
        "inspection_date": "2026-09-08",
    }
    create_res = client.post("/api/inspections", json=create_payload)
    assert create_res.status_code == 201
    created = create_res.json()
    inspection_id = created["inspection_id"]
    
    # 3. Retrieve created inspection
    get_res = client.get(f"/api/inspections/{inspection_id}")
    assert get_res.status_code == 200
    insp_data = get_res.json()
    assert insp_data["inspection_id"] == inspection_id
    assert insp_data["status"] == "draft"
    
    # 4. Save measurements
    m1 = {"measurement_type": "ch4_general_body", "value": 0.45, "unit": "%"}
    m1_res = client.post(f"/api/inspections/{inspection_id}/measurements", json=m1)
    assert m1_res.status_code == 201

    m2 = {"measurement_type": "air_velocity", "value": 1.5, "unit": "m/s"}
    m2_res = client.post(f"/api/inspections/{inspection_id}/measurements", json=m2)
    assert m2_res.status_code == 201
    
    # 5. Save checklist item
    c1 = {"item_id": "PSM-CHK-01", "passed": True, "observation": "Calibrated this morning"}
    c1_res = client.post(f"/api/inspections/{inspection_id}/checklist", json=c1)
    assert c1_res.status_code == 201
    
    # 6. Save evidence
    ev = {"evidence_type": "photo", "filename": "ch4_reading.jpg", "storage_reference": "/mock/ch4.jpg"}
    ev_res = client.post(f"/api/inspections/{inspection_id}/evidence", json=ev)
    assert ev_res.status_code == 201

    # 7. Submit inspection
    submission_payload = {
        "inspection_id": inspection_id,
        "measurements": [],
        "checklist_results": [],
        "findings": [],
        "observation": "Pre-shift methane check completed successfully.",
    }
    sub_res = client.post(f"/api/inspections/{inspection_id}/submit", json=submission_payload)
    assert sub_res.status_code == 200
    submitted = sub_res.json()
    assert submitted["status"] in ["submitted", "flagged", "completed"]
    assert "verification" in submitted
    
    # 8. Verify it appears in mine inspections
    mine_insps_res = client.get("/api/mines/MINE-BCCL-JHARIA-01/inspections")
    assert mine_insps_res.status_code == 200
    all_mine_insps = mine_insps_res.json().get("inspections", [])
    assert any(i["inspection_id"] == inspection_id for i in all_mine_insps)
