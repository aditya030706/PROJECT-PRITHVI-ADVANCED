import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

SEVEN_CATEGORIES = [
    "Ventilation & Gas",
    "Shaft & Winding",
    "Electrical",
    "HEMM",
    "Blasting",
    "Roof / Strata",
    "Water / Drainage",
]

def test_compliance_summary_endpoint_success():
    res = client.get("/api/mines/MINE-BCCL-JHARIA-01/compliance-summary")
    assert res.status_code == 200
    data = res.json()

    assert data["mine_id"] == "MINE-BCCL-JHARIA-01"
    assert "Jharia" in data["mine_name"]
    assert data["total_applicable_inspections"] == 13
    assert data["due_today"] >= 0
    assert data["overdue"] >= 0
    assert data["upcoming"] >= 0
    assert data["submitted"] >= 0
    assert data["verified"] >= 0
    assert data["review_required"] >= 0
    assert data["open_findings"] >= 0
    assert data["threshold_violations"] >= 0

    # Verify 7 categories
    categories = [c["category"] for c in data["category_compliance"]]
    assert len(categories) == 7
    for cat in SEVEN_CATEGORIES:
        assert cat in categories, f"Missing category: {cat}"

    # Verify category compliance structure
    for cat_data in data["category_compliance"]:
        assert "total_schedules" in cat_data
        assert "overdue_count" in cat_data
        assert "due_today_count" in cat_data
        assert "upcoming_count" in cat_data
        assert "inspections_count" in cat_data
        assert "submitted_count" in cat_data
        assert "verified_count" in cat_data
        assert "review_required_count" in cat_data
        assert "threshold_violations_count" in cat_data
        assert "open_findings_count" in cat_data
        assert cat_data["compliance_status"] in [
            "COMPLIANT",
            "UPCOMING_DUE",
            "ATTENTION_REQUIRED",
            "CRITICAL_NON_COMPLIANCE",
        ]

    # Verify attention items
    assert isinstance(data["attention_items"], list)
    for item in data["attention_items"]:
        assert item["item_id"]
        assert item["item_type"] in [
            "OVERDUE_INSPECTION",
            "THRESHOLD_VIOLATION",
            "OPEN_FINDING",
            "VERIFICATION_REVIEW",
        ]
        assert item["severity"] in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
        assert item["title"]
        assert item["description"]
        assert item["action"]

def test_compliance_summary_404_for_unknown_mine():
    res = client.get("/api/mines/UNKNOWN-MINE-999/compliance-summary")
    assert res.status_code == 404

def test_threshold_violation_in_verification_signals():
    # 1. Create inspection for PRE-SHIFT-METHANE-CHECK
    create_payload = {
        "mine_id": "MINE-BCCL-JHARIA-01",
        "template_id": "PRE-SHIFT-METHANE-CHECK",
        "obligation_id": "CMR-119",
        "inspector_id": "INSP-TEST-002",
        "inspection_date": "2026-09-08",
    }
    create_res = client.post("/api/inspections", json=create_payload)
    assert create_res.status_code == 201
    inspection_id = create_res.json()["inspection_id"]

    # 2. Add an excessive methane measurement (e.g. 2.5%, limit is 1.25%)
    # And checklist item
    m_excess = {
        "measurement_type": "Methane at Working Face",
        "value": 2.5,
        "unit": "%",
    }
    meas_res = client.post(f"/api/inspections/{inspection_id}/measurements", json=m_excess)
    assert meas_res.status_code == 201

    c1 = {"item_id": "PSM-CHK-01", "passed": True, "observation": "Detector functional"}
    chk_res = client.post(f"/api/inspections/{inspection_id}/checklist", json=c1)
    assert chk_res.status_code == 201

    # 3. Submit inspection — MUST NOT BE BLOCKED
    sub_payload = {
        "inspection_id": inspection_id,
        "measurements": [],
        "checklist_results": [],
        "findings": [],
        "observation": "Elevated gas observed, recorded for statutory compliance signal.",
    }
    sub_res = client.post(f"/api/inspections/{inspection_id}/submit", json=sub_payload)
    assert sub_res.status_code == 200
    submitted = sub_res.json()

    # 4. Verify verification result has threshold signal
    verif = submitted.get("verification")
    assert verif is not None
    signals = verif.get("signals", [])
    threshold_signals = [s for s in signals if s.get("category") == "regulatory_threshold"]
    assert len(threshold_signals) > 0

    # Look for the exceeded threshold signal
    exceeded = next((s for s in threshold_signals if s.get("status") == "threshold_exceeded"), None)
    assert exceeded is not None
    assert exceeded.get("severity") in ("critical", "warning")
    assert "exceeds statutory maximum" in exceeded.get("explanation", "").lower()
