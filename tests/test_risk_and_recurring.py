import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.compliance import SEVEN_STATUTORY_CATEGORIES
from app.risk import get_mine_risk_intelligence, get_mine_recurring_issues

client = TestClient(app)

JHARIA_MINE_ID = "MINE-BCCL-JHARIA-01"


def test_mine_risk_endpoint_success():
    """Verify GET /api/mines/{mine_id}/risk returns complete deterministic risk profile."""
    res = client.get(f"/api/mines/{JHARIA_MINE_ID}/risk")
    assert res.status_code == 200
    data = res.json()

    assert data["mine_id"] == JHARIA_MINE_ID
    assert "Jharia" in data["mine_name"]
    assert data["overall_risk_level"] in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INSUFFICIENT_DATA"]
    assert 0 <= data["overall_risk_score"] <= 100

    # Jharia has historical critical methane breaches, so overall risk must be CRITICAL
    assert data["overall_risk_level"] == "CRITICAL"
    assert data["overall_risk_score"] >= 50

    # 7 statutory categories must be present
    assert len(data["categories"]) == 7
    cat_names = [c["category"] for c in data["categories"]]
    for cat in SEVEN_STATUTORY_CATEGORIES:
        assert cat in cat_names, f"Missing category: {cat}"

    # Category fields validation
    for cat_data in data["categories"]:
        assert "category" in cat_data
        assert cat_data["risk_level"] in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INSUFFICIENT_DATA"]
        assert 0 <= cat_data["risk_score"] <= 100
        assert cat_data["active_signals"] >= 0
        assert cat_data["recurring_issues"] >= 0
        assert cat_data["open_findings"] >= 0
        assert cat_data["overdue_inspections"] >= 0
        assert isinstance(cat_data["drivers"], list)
        assert len(cat_data["drivers"]) > 0, f"Category {cat_data['category']} has no explainable drivers"

    # Top risk drivers validation
    assert isinstance(data["top_risk_drivers"], list)
    assert len(data["top_risk_drivers"]) > 0
    # Top drivers must mention critical methane breach or recurring failure
    driver_text = " ".join(data["top_risk_drivers"]).lower()
    assert "methane" in driver_text or "ventilation" in driver_text


def test_recurring_compliance_endpoint_success():
    """Verify GET /api/mines/{mine_id}/recurring-compliance isolates repeated non-compliance."""
    res = client.get(f"/api/mines/{JHARIA_MINE_ID}/recurring-compliance")
    assert res.status_code == 200
    issues = res.json()

    assert isinstance(issues, list)
    # Jharia database has repeated methane threshold breaches
    assert len(issues) >= 1

    for issue in issues:
        # Crucial acceptance criterion: only recurring when occurrences >= 2
        assert issue["occurrences"] >= 2, f"Single incident labeled as recurring: {issue}"
        assert issue["category"] in SEVEN_STATUTORY_CATEGORIES
        assert issue["issue_type"] in [
            "RECURRING_THRESHOLD_VIOLATION",
            "RECURRING_FINDING",
            "REPEATED_OVERDUE_INSPECTION",
            "UNRESOLVED_FINDING",
            "CATEGORY_DETERIORATION",
        ]
        assert issue["severity"] in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
        assert issue["status"] in ["OPEN", "RESOLVED"]
        assert len(issue["related_inspection_ids"]) >= 2
        assert len(issue["title"]) > 0
        assert len(issue["description"]) > 0
        assert len(issue["recommended_action"]) > 0

    # Specifically verify the Methane recurring issue
    methane_issues = [i for i in issues if "methane" in i["title"].lower() or "methane" in i["description"].lower()]
    assert len(methane_issues) >= 1
    m_issue = methane_issues[0]
    assert m_issue["severity"] == "CRITICAL"
    assert m_issue["category"] == "Ventilation & Gas"
    assert m_issue["occurrences"] >= 7
    assert "Regulation 119" in m_issue["recommended_action"]


def test_risk_endpoint_404_for_invalid_mine():
    """Verify 404 error returned for unknown mine."""
    res = client.get("/api/mines/UNKNOWN-MINE-9999/risk")
    assert res.status_code == 404
    assert "Mine not found" in res.json()["detail"]


def test_recurring_endpoint_404_for_invalid_mine():
    """Verify 404 error returned for unknown mine."""
    res = client.get("/api/mines/UNKNOWN-MINE-9999/recurring-compliance")
    assert res.status_code == 404
    assert "Mine not found" in res.json()["detail"]


def test_deterministic_risk_calculation():
    """Verify risk model is pure function and yields identical deterministic results."""
    run1 = get_mine_risk_intelligence(JHARIA_MINE_ID)
    run2 = get_mine_risk_intelligence(JHARIA_MINE_ID)

    assert run1 is not None and run2 is not None
    assert run1["overall_risk_level"] == run2["overall_risk_level"]
    assert run1["overall_risk_score"] == run2["overall_risk_score"]
    assert len(run1["categories"]) == len(run2["categories"])
    for c1, c2 in zip(run1["categories"], run2["categories"]):
        assert c1["category"] == c2["category"]
        assert c1["risk_level"] == c2["risk_level"]
        assert c1["risk_score"] == c2["risk_score"]
        assert c1["drivers"] == c2["drivers"]
