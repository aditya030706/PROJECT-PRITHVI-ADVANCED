"""
PRITHVI Landing Page Integration & Governance Hierarchy Test Suite.

Verifies:
1. Landing page/hierarchy integration (canonical tree retrieval)
2. Search endpoint functionality
3. Search result schema compliance
4. Hierarchy consistency & unbroken upward lineage
5. Mine lineage resolution
6. Underground operational structure validation
7. Opencast operational structure validation
8. Search for existing hierarchy records (BCCL, Jharia, etc.)
9. Invalid search handling (empty, whitespace, non-existent)
10. Authorization & scope consistency
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app import database as db
from app.models import OrganizationUnitType, OperationalUnitType

client = TestClient(app)


def test_01_landing_hierarchy_tree_integration():
    """Verify canonical tree endpoint serves data for landing page hierarchy component."""
    resp = client.get("/api/hierarchy/tree?depth=6")
    assert resp.status_code == 200
    tree = resp.json()
    assert isinstance(tree, list)
    assert len(tree) > 0

    top_node = tree[0]
    assert top_node["unit_type"] == OrganizationUnitType.MINISTRY.value
    assert "Ministry" in top_node["name"]

    # Verify CIL is direct child
    cil_children = [c for c in top_node["children"] if c["unit_type"] == OrganizationUnitType.CIL.value]
    assert len(cil_children) > 0
    cil = cil_children[0]
    assert "Coal India" in cil["name"]

    # Verify subsidiaries exist under CIL
    subsidiaries = [c for c in cil["children"] if c["unit_type"] == OrganizationUnitType.SUBSIDIARY.value]
    assert len(subsidiaries) > 0


def test_02_search_endpoint_basic():
    """Verify search endpoint responds with HTTP 200 and matches entities."""
    resp = client.get("/api/hierarchy/search?q=BCCL")
    assert resp.status_code == 200
    results = resp.json()
    assert isinstance(results, list)
    assert len(results) > 0
    # At least one result should have BCCL in code or name
    assert any("BCCL" in r["code"] or "BCCL" in r["name"] or "Bharat Coking Coal" in r["name"] for r in results)


def test_03_search_result_schema():
    """Verify search results conform to canonical schema required by landing search bar."""
    resp = client.get("/api/hierarchy/search?q=Jharia")
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) > 0

    required_keys = {"id", "name", "code", "type", "unit_type", "status", "hierarchy_path", "link"}
    for item in results:
        assert required_keys.issubset(item.keys()), f"Missing keys in {item}"
        assert isinstance(item["hierarchy_path"], list)
        assert len(item["hierarchy_path"]) > 0
        assert item["link"].startswith("/")


def test_04_hierarchy_consistency():
    """Verify every search result's hierarchy path starts with Ministry and CIL."""
    resp = client.get("/api/hierarchy/search?q=Jharia")
    assert resp.status_code == 200
    results = resp.json()
    for item in results:
        path = item["hierarchy_path"]
        assert path[0] == "Ministry of Coal"
        if len(path) > 1:
            assert path[1] == "Coal India Limited"


def test_05_mine_lineage_resolution():
    """Verify searching a mine returns full unbroken upward lineage and correct mine_type."""
    resp = client.get("/api/hierarchy/search?q=Jharia Underground")
    assert resp.status_code == 200
    results = resp.json()
    mine_results = [r for r in results if r["unit_type"] == "MINE"]
    assert len(mine_results) > 0

    target_mine = mine_results[0]
    assert target_mine["mine_type"] == "UNDERGROUND"
    path = target_mine["hierarchy_path"]
    assert "Ministry of Coal" in path
    assert "Coal India Limited" in path
    assert "Bharat Coking Coal Limited" in path
    assert "Jharia Area" in path
    assert target_mine["name"] in path


def test_06_underground_operational_structure():
    """Verify underground operational units can be searched and show correct underground mine lineage."""
    resp = client.get("/api/hierarchy/search?q=Face")
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) > 0

    face_results = [r for r in results if r["unit_type"] == "WORKING_FACE"]
    assert len(face_results) > 0
    face = face_results[0]
    assert face["type"] == "OPERATIONAL_UNIT"
    assert "Working Face" in face["name"]
    # Path should include parent mine
    assert any("Mine" in p for p in face["hierarchy_path"])


def test_07_opencast_operational_structure():
    """Verify operational unit compatibility validation enforces UG vs OC rules."""
    from app.hierarchy_service import validate_operational_unit_compatibility

    # Opencast units (PIT, BENCH, HAUL_ROAD, DUMP_STOCK, HEMM_PARK) should fail on UG mine
    with pytest.raises(ValueError) as exc:
        validate_operational_unit_compatibility("MINE-BCCL-JHARIA-01", "PIT")
    assert "incompatible" in str(exc.value)

    with pytest.raises(ValueError) as exc:
        validate_operational_unit_compatibility("MINE-BCCL-JHARIA-01", "BENCH")
    assert "incompatible" in str(exc.value)

    # Underground units (SHAFT_INCLINE, VENTILATION_DISTRICT, PANEL, SECTION, WORKING_FACE) should fail on OC mine
    with pytest.raises(ValueError) as exc:
        validate_operational_unit_compatibility("MINE-MCL-TALCHER-01", "VENTILATION_DISTRICT")
    assert "incompatible" in str(exc.value)


def test_08_search_existing_hierarchy_records():
    """Verify searching for canonical seed records BCCL, Jharia, Talcher succeeds."""
    for query in ["BCCL", "Jharia", "Coal"]:
        resp = client.get(f"/api/hierarchy/search?q={query}")
        assert resp.status_code == 200
        assert len(resp.json()) > 0, f"Expected results for query '{query}'"


def test_09_invalid_search_handling():
    """Verify empty, whitespace, and non-existent queries are handled gracefully."""
    # Empty query
    resp1 = client.get("/api/hierarchy/search?q=")
    assert resp1.status_code == 200
    assert resp1.json() == []

    # Whitespace query
    resp2 = client.get("/api/hierarchy/search?q=     ")
    assert resp2.status_code == 200
    assert resp2.json() == []

    # Non-existent query
    resp3 = client.get("/api/hierarchy/search?q=NONEXISTENT_XYZ_RANDOM_12345")
    assert resp3.status_code == 200
    assert resp3.json() == []


def test_10_authorization_and_scope_consistency():
    """Verify scope check enforces 403 on cross-scope mine queries without proper role."""
    # Corporate Management can access regional/global mines
    resp_corp = client.get(
        "/api/hierarchy/mines/MINE-DEMO-JHARIA-UG-01",
        headers={"X-User-Role": "CORPORATE_MANAGEMENT", "X-User-Scope-Type": "GLOBAL"},
    )
    assert resp_corp.status_code == 200

    # Mine Manager with mismatched mine scope receives 403
    resp_forbidden = client.get(
        "/api/hierarchy/mines/MINE-DEMO-JHARIA-UG-01",
        headers={
            "X-User-Role": "MINE_MANAGER",
            "X-User-Scope-Type": "MINE",
            "X-User-Scope-Id": "MINE-OTHER-DIFFERENT-02",
        },
    )
    assert resp_forbidden.status_code == 403


def test_11_public_guest_access_without_headers():
    """Verify public endpoints require NO headers and succeed for guest visitors."""
    # Hierarchy tree is public
    resp_tree = client.get("/api/hierarchy/tree?depth=3")
    assert resp_tree.status_code == 200
    assert len(resp_tree.json()) > 0

    # Public search requires no auth headers
    resp_search = client.get("/api/hierarchy/search?q=Coal")
    assert resp_search.status_code == 200
    assert len(resp_search.json()) > 0

    # Environmental overview without headers
    resp_env = client.get("/api/environment/overview")
    assert resp_env.status_code == 200


def test_12_role_gate_unauthorized_scope_enforcement():
    """Verify role scope gate blocks unauthorized cross-mine modifications."""
    # Attempting to access another mine with MINE_MANAGER scope returns 403
    resp = client.get(
        "/api/hierarchy/mines/MINE-MCL-TALCHER-01",
        headers={
            "X-User-Role": "MINE_MANAGER",
            "X-User-Scope-Type": "MINE",
            "X-User-Scope-Id": "MINE-BCCL-JHARIA-01",  # Different mine scope
        },
    )
    assert resp.status_code == 403


def test_13_field_inspector_vs_manager_role_isolation():
    """Verify FIELD_INSPECTOR has observation access but cannot mutate mine configurations."""
    # Field inspector attempting to modify mine structure is rejected
    resp = client.put(
        "/api/hierarchy/mines/MINE-MCL-TALCHER-01",
        json={"name": "Inspector Name Change"},
        headers={
            "X-User-Role": "FIELD_INSPECTOR",
            "X-User-Scope-Type": "MINE",
            "X-User-Scope-Id": "MINE-MCL-TALCHER-01",
        },
    )
    assert resp.status_code in (403, 405)


def test_14_corporate_broad_read_visibility():
    """Verify CORPORATE_MANAGEMENT has broad subsidiary and national oversight visibility."""
    resp = client.get(
        "/api/hierarchy/mines/MINE-MCL-TALCHER-01",
        headers={
            "X-User-Role": "CORPORATE_MANAGEMENT",
            "X-User-Scope-Type": "GLOBAL",
        },
    )
    assert resp.status_code == 200
    assert "TALCHER" in resp.json()["mine"]["id"]

