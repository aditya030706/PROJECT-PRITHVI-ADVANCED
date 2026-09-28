"""
PRITHVI — Phase 2 Task 6: Compliance Case & Corrective Action Management Tests
==============================================================================

Automated test suite verifying the end-to-end closed-loop compliance tracking:
1. Case creation from a real finding.
2. Duplicate source cannot create duplicate cases (idempotent).
3. Case correctly references original inspection and regulation.
4. Corrective action requires owner (role or user ID).
5. Corrective action requires due date.
6. Corrective action persists in database.
7. Evidence can be linked to corrective action.
8. Completion does not automatically close the case.
9. Verification is required before closure.
10. Reviewer can verify valid correction and close case.
11. Reviewer can return insufficient correction.
12. Return requires a substantive reason.
13. Closed case cannot be modified incorrectly.
14. Audit trail records state transitions with timestamps and actors.
15. Unauthorized roles cannot perform restricted actions (RBAC).
16. Existing Phase 1–5 tests remain passing.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app import database as db
from app.main import app
from app.models import (
    Finding,
    ComplianceCase,
    CaseSourceType,
    CaseStatus,
    Inspection,
    InspectionStatus,
)
from app.case_service import (
    sync_mine_compliance_cases,
    create_corrective_action,
    submit_action_correction,
    verify_case_closure,
    return_case_for_correction,
    get_case_detail,
    get_case_traceability,
)

client = TestClient(app)
DEMO_MINE = "MINE-BCCL-JHARIA-01"


@pytest.fixture(autouse=True)
def setup_db():
    """Ensure database schema is ready before every test."""
    db.init_db()


def create_test_finding_and_inspection():
    """Helper to create an authentic inspection and finding in DB."""
    insp_id = f"INSP-TEST-{uuid4().hex[:8].upper()}"
    fnd_id = f"FND-TEST-{uuid4().hex[:8].upper()}"
    now = datetime.now(timezone.utc)

    # Insert test inspection
    conn = db._connect()
    conn.execute(
        """
        INSERT INTO inspections (
            inspection_id, mine_id, template_id, inspector_id, inspection_date, status, submitted_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (insp_id, DEMO_MINE, "INS-VENT-GAS-001", "INSPECTOR-01", date.today().isoformat(), "submitted", now.isoformat()),
    )
    conn.commit()
    conn.close()

    # Insert test finding with corrective_action_required = 1
    finding = Finding(
        finding_id=fnd_id,
        inspection_id=insp_id,
        title="Excessive Methane Accumulation at Tailgate",
        description="CH4 concentration measured at 1.8% at tailgate seal, exceeding 1.25% CMR limit.",
        severity="CRITICAL",
        corrective_action_required=True,
        status="open",
    )
    db.save_finding(finding)

    return insp_id, fnd_id


# ============================================================
# TEST 1 & 3: Case Creation from Real Finding & Inspection Reference
# ============================================================

def test_case_creation_from_real_finding_and_references():
    insp_id, fnd_id = create_test_finding_and_inspection()

    # Sync cases from DB
    cases = sync_mine_compliance_cases(DEMO_MINE)
    assert len(cases) > 0

    # Locate the case created for our finding
    case = next((c for c in cases if c.get("finding_id") == fnd_id), None)
    assert case is not None, f"Expected case for finding {fnd_id}"
    assert case["mine_id"] == DEMO_MINE
    assert case["inspection_id"] == insp_id
    assert case["status"] == "OPEN"
    assert case["severity"] == "CRITICAL"
    assert "Methane" in case["title"]
    assert case["regulation_reference"] is not None

    # Traceability graph check
    traceability = get_case_traceability(case["case_id"])
    assert traceability["inspection"]["id"] == insp_id
    assert traceability["finding"]["finding_id"] == fnd_id


# ============================================================
# TEST 2: Duplicate Source Cannot Create Duplicate Cases (Idempotency)
# ============================================================

def test_idempotent_case_creation():
    insp_id, fnd_id = create_test_finding_and_inspection()

    # Sync once
    cases_1 = sync_mine_compliance_cases(DEMO_MINE)
    count_1 = sum(1 for c in cases_1 if c.get("finding_id") == fnd_id)
    assert count_1 == 1

    # Sync a second time
    cases_2 = sync_mine_compliance_cases(DEMO_MINE)
    count_2 = sum(1 for c in cases_2 if c.get("finding_id") == fnd_id)
    assert count_2 == 1, "Duplicate cases were incorrectly created on second sync."


# ============================================================
# TEST 4 & 5: Corrective Action Requires Owner and Due Date
# ============================================================

def test_corrective_action_validation():
    insp_id, fnd_id = create_test_finding_and_inspection()
    cases = sync_mine_compliance_cases(DEMO_MINE)
    case = next(c for c in cases if c.get("finding_id") == fnd_id)
    case_id = case["case_id"]

    tomorrow = (date.today() + timedelta(days=1)).isoformat()

    # Missing owner (no assigned_role and no assigned_user_id)
    resp_no_owner = client.post(
        f"/api/cases/{case_id}/actions",
        json={
            "title": "Install auxiliary ventilation fan",
            "description": "Deploy flameproof auxiliary fan with 500 m3/min capacity.",
            "due_at": tomorrow,
            "priority": "CRITICAL",
        },
        headers={"X-User-Role": "MINE_MANAGER", "X-User-Id": "MANAGER-01"},
    )
    assert resp_no_owner.status_code == 400
    assert "owner" in resp_no_owner.json()["detail"].lower()

    # Missing due date
    resp_no_due = client.post(
        f"/api/cases/{case_id}/actions",
        json={
            "title": "Install auxiliary ventilation fan",
            "description": "Deploy flameproof auxiliary fan with 500 m3/min capacity.",
            "assigned_role": "Mine Ventilation Officer",
            "due_at": "",
            "priority": "CRITICAL",
        },
        headers={"X-User-Role": "MINE_MANAGER", "X-User-Id": "MANAGER-01"},
    )
    assert resp_no_due.status_code == 400
    assert "due date" in resp_no_due.json()["detail"].lower()

    # Invalid due date format
    resp_bad_due = client.post(
        f"/api/cases/{case_id}/actions",
        json={
            "title": "Install auxiliary ventilation fan",
            "description": "Deploy flameproof auxiliary fan with 500 m3/min capacity.",
            "assigned_role": "Mine Ventilation Officer",
            "due_at": "invalid-date-string",
            "priority": "CRITICAL",
        },
        headers={"X-User-Role": "MINE_MANAGER", "X-User-Id": "MANAGER-01"},
    )
    assert resp_bad_due.status_code == 400
    assert "invalid due date" in resp_bad_due.json()["detail"].lower()


# ============================================================
# TEST 6 & 7: Corrective Action Persists & Evidence Can Be Linked
# ============================================================

def test_corrective_action_persistence_and_evidence_linking():
    insp_id, fnd_id = create_test_finding_and_inspection()
    cases = sync_mine_compliance_cases(DEMO_MINE)
    case = next(c for c in cases if c.get("finding_id") == fnd_id)
    case_id = case["case_id"]
    tomorrow = (date.today() + timedelta(days=1)).isoformat()

    # Create valid action
    resp_create = client.post(
        f"/api/cases/{case_id}/actions",
        json={
            "title": "Increase air velocity at 2nd Dip face",
            "description": "Adjust regulator door #4 to achieve minimum 0.5 m/s velocity.",
            "assigned_role": "Ventilation Officer",
            "assigned_user_id": "VENT-OFFICER-01",
            "due_at": tomorrow,
            "priority": "HIGH",
        },
        headers={"X-User-Role": "MINE_MANAGER", "X-User-Id": "MANAGER-01"},
    )
    assert resp_create.status_code == 200
    action_data = resp_create.json()
    action_id = action_data["action_id"]

    # Action persists in DB
    persisted = db.get_corrective_action(action_id)
    assert persisted is not None
    assert persisted["title"] == "Increase air velocity at 2nd Dip face"
    assert persisted["status"] == "OPEN"

    # Case transitioned to ACTION_REQUIRED
    updated_case = db.get_compliance_case(case_id)
    assert updated_case["status"] == "ACTION_REQUIRED"

    # Submit correction evidence
    resp_submit = client.post(
        f"/api/corrective-actions/{action_id}/submit",
        json={
            "notes": "Regulator adjusted. Anemometer reading confirms 0.65 m/s air velocity.",
            "filename": "anemometer_reading_verified.png",
            "evidence_type": "photo",
            "raw_data": "Velocity=0.65m/s CH4=0.4%",
        },
        headers={"X-User-Role": "MINE_SUPERVISOR", "X-User-Id": "SUPERVISOR-01"},
    )
    assert resp_submit.status_code == 200
    submit_res = resp_submit.json()
    assert submit_res["action_status"] == "COMPLETED"
    assert submit_res["sha256"] is not None
    assert submit_res["ipfs_cid"] is not None
    assert submit_res["audit_proof_status"] == "AUDIT_PROOF_RECORDED"

    # Check evidence linked
    corr_evidence = db.list_case_correction_evidence(case_id)
    assert len(corr_evidence) >= 1
    assert corr_evidence[0]["action_id"] == action_id


# ============================================================
# TEST 8 & 9: Completion Does NOT Automatically Close Case; Verification Required
# ============================================================

def test_completion_does_not_auto_close_and_requires_verification():
    insp_id, fnd_id = create_test_finding_and_inspection()
    cases = sync_mine_compliance_cases(DEMO_MINE)
    case = next(c for c in cases if c.get("finding_id") == fnd_id)
    case_id = case["case_id"]
    tomorrow = (date.today() + timedelta(days=1)).isoformat()

    # Create action
    resp_action = client.post(
        f"/api/cases/{case_id}/actions",
        json={
            "title": "Erect stopping wall",
            "description": "Seal abandoned gallery to prevent gas seepage.",
            "assigned_role": "Mine Overman",
            "due_at": tomorrow,
            "priority": "CRITICAL",
        },
        headers={"X-User-Role": "MINE_MANAGER"},
    )
    action_id = resp_action.json()["action_id"]

    # Submit evidence
    client.post(
        f"/api/corrective-actions/{action_id}/submit",
        json={
            "notes": "Stopping wall erected and plastered with non-combustible material.",
            "filename": "stopping_wall_completed.png",
        },
        headers={"X-User-Role": "MINE_SUPERVISOR"},
    )

    # CRITICAL VERIFICATION: Case must NOT be CLOSED!
    case_after_submit = db.get_compliance_case(case_id)
    assert case_after_submit["status"] == "VERIFICATION_REQUIRED"
    assert case_after_submit["closed_at"] is None

    # Cannot verify if case was NOT in VERIFICATION_REQUIRED
    # Let's test trying to close a newly created OPEN case directly without correction evidence
    case_2_id = f"CASE-DIRECT-{uuid4().hex[:8].upper()}"
    now = datetime.now(timezone.utc)
    c2 = ComplianceCase(
        case_id=case_2_id,
        mine_id=DEMO_MINE,
        category="Electrical",
        title="Direct Close Attempt",
        description="Testing direct closure without workflow.",
        severity="MEDIUM",
        status=CaseStatus.OPEN,
        source_type=CaseSourceType.FINDING,
        created_at=now,
        updated_at=now,
    )
    db.save_compliance_case(c2)

    resp_direct_close = client.post(
        f"/api/cases/{case_2_id}/verify",
        json={"notes": "Trying to bypass verification"},
        headers={"X-User-Role": "MINE_MANAGER"},
    )
    assert resp_direct_close.status_code == 400
    assert "verification_required" in resp_direct_close.json()["detail"].lower()


# ============================================================
# TEST 10: Reviewer Can Verify Valid Correction and Close Case
# ============================================================

def test_reviewer_verifies_and_closes_case():
    insp_id, fnd_id = create_test_finding_and_inspection()
    cases = sync_mine_compliance_cases(DEMO_MINE)
    case = next(c for c in cases if c.get("finding_id") == fnd_id)
    case_id = case["case_id"]
    tomorrow = (date.today() + timedelta(days=1)).isoformat()

    # Action + Submission
    r_act = client.post(
        f"/api/cases/{case_id}/actions",
        json={
            "title": "Purge and vent section",
            "description": "Operate auxiliary fan continuously for 4 hours.",
            "assigned_role": "Mine Overman",
            "due_at": tomorrow,
            "priority": "CRITICAL",
        },
        headers={"X-User-Role": "MINE_MANAGER"},
    )
    action_id = r_act.json()["action_id"]

    client.post(
        f"/api/corrective-actions/{action_id}/submit",
        json={
            "notes": "Section purged. Multi-gas detector reading: CH4 0.1%, O2 20.9%, CO 0 ppm.",
            "filename": "gas_detector_log.pdf",
            "evidence_type": "document",
        },
        headers={"X-User-Role": "MINE_SUPERVISOR"},
    )

    # Statutory Reviewer (Mine Manager) verifies and closes case
    resp_verify = client.post(
        f"/api/cases/{case_id}/verify",
        json={"notes": "Personal inspection conducted by Manager. Atmospheric parameters within CMR safe limits."},
        headers={"X-User-Role": "MINE_MANAGER", "X-User-Id": "MGR-JHARIA-01"},
    )
    assert resp_verify.status_code == 200
    verify_res = resp_verify.json()
    assert verify_res["status"] == "CLOSED"
    assert verify_res["closed_by"] == "MGR-JHARIA-01"
    assert verify_res["cryptographic_proof"] is not None
    assert verify_res["cryptographic_proof"]["status"] == "AUDIT_PROOF_RECORDED"
    assert verify_res["cryptographic_proof"]["sha256"] is not None
    assert verify_res["cryptographic_proof"]["ipfs_cid"] is not None

    # Verify DB persistence
    closed_case = db.get_compliance_case(case_id)
    assert closed_case["status"] == "CLOSED"
    assert closed_case["closed_at"] is not None


# ============================================================
# TEST 11 & 12: Reviewer Returns Correction & Requires Reason
# ============================================================

def test_reviewer_return_for_correction():
    insp_id, fnd_id = create_test_finding_and_inspection()
    cases = sync_mine_compliance_cases(DEMO_MINE)
    case = next(c for c in cases if c.get("finding_id") == fnd_id)
    case_id = case["case_id"]
    tomorrow = (date.today() + timedelta(days=1)).isoformat()

    r_act = client.post(
        f"/api/cases/{case_id}/actions",
        json={
            "title": "Calibrate flame safety lamp",
            "description": "Test and certify lamp in lamp room.",
            "assigned_role": "Lamp Incharge",
            "due_at": tomorrow,
            "priority": "HIGH",
        },
        headers={"X-User-Role": "MINE_MANAGER"},
    )
    action_id = r_act.json()["action_id"]

    client.post(
        f"/api/corrective-actions/{action_id}/submit",
        json={"notes": "Calibration done.", "filename": "lamp_blurry_photo.png"},
        headers={"X-User-Role": "MINE_SUPERVISOR"},
    )

    # Empty or trivial reason is rejected
    resp_empty_reason = client.post(
        f"/api/cases/{case_id}/return",
        json={"reason": "bad"},
        headers={"X-User-Role": "MINE_MANAGER"},
    )
    assert resp_empty_reason.status_code == 400
    assert "reason" in resp_empty_reason.json()["detail"].lower()

    # Substantive return reason accepted
    valid_reason = "Attached photograph is out of focus. Calibration certificate timestamp does not match shift log."
    resp_return = client.post(
        f"/api/cases/{case_id}/return",
        json={"reason": valid_reason},
        headers={"X-User-Role": "MINE_MANAGER", "X-User-Id": "MGR-JHARIA-01"},
    )
    assert resp_return.status_code == 200
    assert resp_return.json()["status"] == "RETURNED_FOR_CORRECTION"
    assert resp_return.json()["reason"] == valid_reason

    # Database state check
    db_case = db.get_compliance_case(case_id)
    assert db_case["status"] == "RETURNED_FOR_CORRECTION"


# ============================================================
# TEST 13: Closed Case Cannot Be Modified Incorrectly
# ============================================================

def test_closed_case_cannot_be_modified():
    insp_id, fnd_id = create_test_finding_and_inspection()
    cases = sync_mine_compliance_cases(DEMO_MINE)
    case = next(c for c in cases if c.get("finding_id") == fnd_id)
    case_id = case["case_id"]
    tomorrow = (date.today() + timedelta(days=1)).isoformat()

    r_act = client.post(
        f"/api/cases/{case_id}/actions",
        json={
            "title": "Repair earthing pit",
            "description": "Earthing resistance measured at 8 ohms; reduce below 2 ohms.",
            "assigned_role": "Mine Electrical Supervisor",
            "due_at": tomorrow,
            "priority": "HIGH",
        },
        headers={"X-User-Role": "MINE_MANAGER"},
    )
    action_id = r_act.json()["action_id"]

    client.post(
        f"/api/corrective-actions/{action_id}/submit",
        json={"notes": "Pit watered and salt added. Resistance = 1.4 ohms."},
        headers={"X-User-Role": "MINE_SUPERVISOR"},
    )

    client.post(
        f"/api/cases/{case_id}/verify",
        json={"notes": "Megger test certificate verified."},
        headers={"X-User-Role": "MINE_MANAGER"},
    )

    # Now case is CLOSED. Attempting to add action to closed case must fail!
    resp_action_on_closed = client.post(
        f"/api/cases/{case_id}/actions",
        json={
            "title": "New action on closed case",
            "description": "This should be disallowed.",
            "assigned_role": "Supervisor",
            "due_at": tomorrow,
        },
        headers={"X-User-Role": "MINE_MANAGER"},
    )
    assert resp_action_on_closed.status_code == 400
    assert "closed" in resp_action_on_closed.json()["detail"].lower()

    # Attempting to return closed case must fail!
    resp_return_on_closed = client.post(
        f"/api/cases/{case_id}/return",
        json={"reason": "Attempting to return an already closed case."},
        headers={"X-User-Role": "MINE_MANAGER"},
    )
    assert resp_return_on_closed.status_code == 400
    assert "closed" in resp_return_on_closed.json()["detail"].lower()


# ============================================================
# TEST 14: Audit Trail Records State Transitions
# ============================================================

def test_audit_trail_records_transitions():
    insp_id, fnd_id = create_test_finding_and_inspection()
    cases = sync_mine_compliance_cases(DEMO_MINE)
    case = next(c for c in cases if c.get("finding_id") == fnd_id)
    case_id = case["case_id"]
    tomorrow = (date.today() + timedelta(days=1)).isoformat()

    # 1. Action assigned
    r_act = client.post(
        f"/api/cases/{case_id}/actions",
        json={
            "title": "Test Audit Trail Action",
            "description": "Traceability test.",
            "assigned_role": "Mine Supervisor",
            "due_at": tomorrow,
            "priority": "MEDIUM",
        },
        headers={"X-User-Role": "MINE_MANAGER", "X-User-Id": "MGR-01"},
    )
    act_id = r_act.json()["action_id"]

    # 2. Correction submitted
    client.post(
        f"/api/corrective-actions/{act_id}/submit",
        json={"notes": "Evidence submitted."},
        headers={"X-User-Role": "MINE_SUPERVISOR", "X-User-Id": "SUP-01"},
    )

    # 3. Verified and closed
    client.post(
        f"/api/cases/{case_id}/verify",
        json={"notes": "Audit closure verified."},
        headers={"X-User-Role": "MINE_MANAGER", "X-User-Id": "MGR-01"},
    )

    # Query audit trail
    resp_audit = client.get(f"/api/cases/{case_id}/audit")
    assert resp_audit.status_code == 200
    audit_data = resp_audit.json()
    events = audit_data["audit_events"]
    actions_logged = [e["action"] for e in events]

    assert "CASE_CREATED" in actions_logged
    assert "ACTION_ASSIGNED" in actions_logged
    assert "CORRECTION_SUBMITTED" in actions_logged
    assert "CASE_CLOSED" in actions_logged

    # Verify cryptographic proof ledger
    proofs = audit_data["cryptographic_proofs"]
    assert len(proofs) >= 2  # Correction proof + Closure proof
    for p in proofs:
        assert p["sha256"] is not None
        assert p["ipfs_cid"].startswith("b")  # Valid CIDv1
        assert p["status"] == "AUDIT_PROOF_RECORDED"


# ============================================================
# TEST 15: Unauthorized Roles Cannot Perform Restricted Actions (RBAC)
# ============================================================

def test_rbac_enforcement():
    insp_id, fnd_id = create_test_finding_and_inspection()
    cases = sync_mine_compliance_cases(DEMO_MINE)
    case = next(c for c in cases if c.get("finding_id") == fnd_id)
    case_id = case["case_id"]
    tomorrow = (date.today() + timedelta(days=1)).isoformat()

    # Field Inspector cannot create/assign corrective actions
    resp_fi_action = client.post(
        f"/api/cases/{case_id}/actions",
        json={
            "title": "Unauthorized Action",
            "description": "Field inspector attempting case management.",
            "assigned_role": "Supervisor",
            "due_at": tomorrow,
        },
        headers={"X-User-Role": "FIELD_INSPECTOR", "X-User-Id": "INSPECTOR-01"},
    )
    assert resp_fi_action.status_code == 403

    # Field Inspector cannot close or verify cases
    resp_fi_verify = client.post(
        f"/api/cases/{case_id}/verify",
        json={"notes": "Field inspector attempting to close case."},
        headers={"X-User-Role": "FIELD_INSPECTOR", "X-User-Id": "INSPECTOR-01"},
    )
    assert resp_fi_verify.status_code == 403

    # Field Inspector cannot return cases
    resp_fi_return = client.post(
        f"/api/cases/{case_id}/return",
        json={"reason": "Field inspector attempting return."},
        headers={"X-User-Role": "FIELD_INSPECTOR", "X-User-Id": "INSPECTOR-01"},
    )
    assert resp_fi_return.status_code == 403
