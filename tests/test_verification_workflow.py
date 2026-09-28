"""
Tests for PRITHVI Phase 2 Task 4: Verification & Regulatory Review Intelligence
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app import database as db
from app.models import InspectionStatus

client = TestClient(app)
MINE_ID = "MINE-BCCL-JHARIA-01"


def test_verification_queue_real_data():
    """Verify that the verification queue returns real counts and prioritized items."""
    response = client.get(f"/api/mines/{MINE_ID}/verification")
    assert response.status_code == 200
    data = response.json()

    assert data["mine_id"] == MINE_ID
    assert "Jharia" in data["mine_name"]
    counts = data["counts"]
    assert "submitted" in counts
    assert "review_required" in counts
    assert "verified" in counts
    assert "rejected" in counts
    assert "high_risk_review" in counts
    assert counts["submitted"] >= counts["review_required"]
    assert counts["review_required"] > 0

    items = data["items"]
    assert len(items) == counts["review_required"]

    # Check structure of each queue item
    first_item = items[0]
    assert "inspection_id" in first_item
    assert "template_name" in first_item
    assert "category" in first_item
    assert "priority" in first_item
    assert first_item["priority"] in ("CRITICAL", "HIGH", "NORMAL")
    assert "evidence_count" in first_item
    assert "required_evidence_count" in first_item
    assert "evidence_compliant" in first_item
    assert "findings_count" in first_item


def test_verification_prioritization_ordering():
    """Verify that CRITICAL priority items precede HIGH and NORMAL items."""
    response = client.get(f"/api/mines/{MINE_ID}/verification")
    assert response.status_code == 200
    items = response.json()["items"]

    priority_rank = {"CRITICAL": 0, "HIGH": 1, "NORMAL": 2}
    ranks = [priority_rank.get(item["priority"], 9) for item in items]
    # Verify that the ranks are non-decreasing
    assert ranks == sorted(ranks), "Queue items must be sorted by priority: CRITICAL -> HIGH -> NORMAL"


def test_inspection_verification_dossier():
    """Verify that inspection verification dossier returns full structured compliance dossier."""
    q_resp = client.get(f"/api/mines/{MINE_ID}/verification")
    items = q_resp.json()["items"]
    assert len(items) > 0
    inspection_id = items[0]["inspection_id"]

    resp = client.get(f"/api/inspections/{inspection_id}/verification")
    assert resp.status_code == 200
    dossier = resp.json()

    assert dossier["inspection_id"] == inspection_id
    assert "template_name" in dossier
    assert "category" in dossier
    assert "measurements" in dossier
    assert "checklist" in dossier
    assert "evidence" in dossier
    assert "evidence_completeness" in dossier
    assert "findings" in dossier
    assert "review_summary" in dossier
    assert "risk_level" in dossier
    assert "audit_history" in dossier
    assert "can_verify" in dossier

    # Check evidence completeness object
    ev_comp = dossier["evidence_completeness"]
    assert "required_count" in ev_comp
    assert "actual_count" in ev_comp
    assert "is_compliant" in ev_comp


def test_server_side_verify_validation_blocks_incomplete():
    """Verify that an inspection with missing evidence or violations cannot be verified silently."""
    q_resp = client.get(f"/api/mines/{MINE_ID}/verification")
    items = q_resp.json()["items"]
    
    # Find an item where evidence is incomplete or can_verify is False
    target_id = None
    for it in items:
        dossier = client.get(f"/api/inspections/{it['inspection_id']}/verification").json()
        if not dossier["can_verify"]:
            target_id = it["inspection_id"]
            break

    if target_id:
        # Attempt to verify incomplete inspection
        resp = client.post(
            f"/api/inspections/{target_id}/verify",
            json={"reviewer_id": "MGR-001", "notes": "Attempting verification"},
        )
        assert resp.status_code == 400
        assert "Cannot verify inspection" in resp.json()["detail"]


def test_return_inspection_requires_substantive_reason():
    """Verify that returning an inspection requires a non-empty reason of at least 5 characters."""
    q_resp = client.get(f"/api/mines/{MINE_ID}/verification")
    items = q_resp.json()["items"]
    assert len(items) > 0
    inspection_id = items[0]["inspection_id"]

    # Empty reason
    resp = client.post(
        f"/api/inspections/{inspection_id}/return",
        json={"reviewer_id": "MGR-001", "reason": ""},
    )
    assert resp.status_code == 400
    assert "reason" in resp.json()["detail"].lower()

    # Short whitespace reason
    resp_short = client.post(
        f"/api/inspections/{inspection_id}/return",
        json={"reviewer_id": "MGR-001", "reason": "   ab  "},
    )
    assert resp_short.status_code == 400


def test_return_inspection_persists_decision_and_audit():
    """Verify that a valid return updates status to rejected and persists in human_reviews."""
    q_resp = client.get(f"/api/mines/{MINE_ID}/verification")
    items = q_resp.json()["items"]
    assert len(items) > 0
    inspection_id = items[-1]["inspection_id"]  # Pick last item

    test_reason = "Evidence photographic proof missing for ventilation airway statutory test."
    resp = client.post(
        f"/api/inspections/{inspection_id}/return",
        json={"reviewer_id": "MGR-001", "reason": test_reason},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["inspection_id"] == inspection_id
    assert data["status"] == "rejected"
    assert data["decision"] == "RETURNED_FOR_CORRECTION"

    # Check inspection dossier reflects rejected status and audit history
    dossier = client.get(f"/api/inspections/{inspection_id}/verification").json()
    assert dossier["inspection_status"] == "rejected"
    assert len(dossier["audit_history"]) > 0

    latest_audit = dossier["audit_history"][0]
    assert latest_audit["reason"] == test_reason
    assert latest_audit["new_status"] == "rejected"
