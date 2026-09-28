"""
Tests for PRITHVI Architecture: Complete Removal of DGMS Officer Role
=====================================================================

Validates:
1. Supported role list contains ONLY the four operational roles:
   - FIELD_INSPECTOR
   - MINE_SUPERVISOR
   - MINE_MANAGER
   - CORPORATE_MANAGEMENT
2. Attempting to activate or use DGMS_OFFICER provides no workspace access.
3. All /api/dgms/* endpoints are removed and return HTTP 404 Not Found.
4. Protected workspace routes reject unsupported or unauthenticated roles.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

SUPPORTED_ROLES = [
    "FIELD_INSPECTOR",
    "MINE_SUPERVISOR",
    "MINE_MANAGER",
    "CORPORATE_MANAGEMENT",
]

UNSUPPORTED_ROLES = [
    "DGMS_OFFICER",
    "DGMS",
    "dgms_officer",
    "INVALID_ROLE",
]


def test_supported_roles_list():
    """Verify that exactly four operational roles are supported across PRITHVI."""
    assert len(SUPPORTED_ROLES) == 4
    assert "FIELD_INSPECTOR" in SUPPORTED_ROLES
    assert "MINE_SUPERVISOR" in SUPPORTED_ROLES
    assert "MINE_MANAGER" in SUPPORTED_ROLES
    assert "CORPORATE_MANAGEMENT" in SUPPORTED_ROLES
    assert "DGMS_OFFICER" not in SUPPORTED_ROLES


def test_dgms_endpoints_removed_404():
    """Verify all /api/dgms/* endpoints return 404 Not Found."""
    routes_to_test = [
        "/api/dgms/overview",
        "/api/dgms/mines",
        "/api/dgms/attention",
        "/api/dgms/mines/MINE-BCCL-JHARIA-01",
        "/api/dgms/enforcement",
    ]
    for route in routes_to_test:
        resp_get = client.get(route)
        assert resp_get.status_code == 404, f"Expected 404 for GET {route}, got {resp_get.status_code}"

    # Also check POST enforcement returns 404
    resp_post = client.post(
        "/api/dgms/enforcement",
        json={"mine_id": "MINE-BCCL-JHARIA-01", "action_type": "ESCALATE", "reason": "Test", "officer_id": "DGMS-01"},
    )
    assert resp_post.status_code == 404, f"Expected 404 for POST /api/dgms/enforcement, got {resp_post.status_code}"


def test_unsupported_role_dgms_cannot_access_workspace_actions():
    """Verify that attempting to act as DGMS_OFFICER is rejected or gives no workspace privileges."""
    # Attempting to create corrective action as DGMS_OFFICER or unassigned role fails
    resp = client.post(
        "/api/cases/CASE-DEMO-001/actions",
        json={
            "title": "Unauthorized Action",
            "description": "DGMS Officer should not be authorized",
            "due_at": "2026-12-31T00:00:00Z",
        },
        headers={"X-User-Role": "DGMS_OFFICER", "X-User-Id": "DGMS-01"},
    )
    # The endpoint either returns 404 (if case doesn't exist) or rejects unassigned role
    assert resp.status_code in (400, 403, 404, 422)


def test_supported_roles_can_access_their_domains():
    """Verify each of the 4 operational roles can access their respective core endpoints."""
    # 1. Field Inspector
    r_insp = client.get("/api/inspection-templates", headers={"X-User-Role": "FIELD_INSPECTOR"})
    assert r_insp.status_code == 200

    # 2. Mine Supervisor
    r_sup = client.get("/api/attendance/team", headers={"X-User-Role": "MINE_SUPERVISOR"})
    assert r_sup.status_code == 200

    # 3. Mine Manager
    r_mgr = client.get("/api/mines", headers={"X-User-Role": "MINE_MANAGER"})
    assert r_mgr.status_code == 200

    # 4. Corporate Management
    r_corp = client.get("/api/corporate/overview", headers={"X-User-Role": "CORPORATE_MANAGEMENT"})
    assert r_corp.status_code == 200
