"""
PRITHVI Phase 2 Task 11 — Governance Master Data, Organizational Hierarchy & Scope Engine Tests.

Verifies:
- Canonical Organizational Hierarchy (Ministry -> CIL -> Subsidiary -> Area -> Mine)
- Mine Type as Property, NOT Hierarchy Node
- Operational Unit Model & Mining Method Compatibility (UG vs OC)
- Relational Governance Associations (Contractors, Contracts, Workers)
- Scope-Aware Governance Authorization Engine & Descendant Inheritance
- Server-side access assertion & Cross-scope HTTP 403 enforcement
- Upward lineage resolution for Mines, Workers, Contracts, Operational Units
- Audit event logging for master data changes
- Zero regression with Tasks 1-10 records
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app import database as db
from app.models import (
    OrganizationUnit,
    OrganizationUnitType,
    OperationalUnit,
    OperationalUnitType,
    ContractorMaster,
    ContractorType,
    ContractMaster,
    WorkerMaster,
    WorkerType,
    Mine,
    MineType,
    GassyDegree,
)
from app.hierarchy_service import (
    validate_parent_child,
    detect_circular_hierarchy,
    validate_operational_unit_compatibility,
    assert_hierarchy_access,
    resolve_mine_hierarchy,
    resolve_worker_hierarchy,
    resolve_contract_hierarchy,
    get_hierarchy_path,
    get_hierarchy_tree,
)
from app.seed_data import seed_initial_data
from fastapi import HTTPException


@pytest.fixture(scope="module", autouse=True)
def setup_hierarchy_data():
    """Ensure database and seeds are loaded."""
    db.init_db()
    seed_initial_data()


@pytest.fixture
def client():
    return TestClient(app)


# ------------------------------------------------------------
# 1. Ministry exists
# ------------------------------------------------------------
def test_01_ministry_exists():
    ministry = db.get_organization_unit("ORG-MINISTRY-MOC")
    assert ministry is not None
    assert ministry["unit_type"] == OrganizationUnitType.MINISTRY.value
    assert ministry["code"] == "MOC"
    assert "Ministry of Coal" in ministry["name"]
    assert ministry["parent_id"] is None


# ------------------------------------------------------------
# 2. CIL exists
# ------------------------------------------------------------
def test_02_cil_exists():
    cil = db.get_organization_unit("ORG-CIL-CIL")
    assert cil is not None
    assert cil["unit_type"] == OrganizationUnitType.CIL.value
    assert cil["parent_id"] == "ORG-MINISTRY-MOC"
    assert cil["code"] == "CIL"


# ------------------------------------------------------------
# 3. CIL entity/subsidiary hierarchy works
# ------------------------------------------------------------
def test_03_subsidiary_hierarchy_works():
    bccl = db.get_organization_unit("ORG-SUBSIDIARY-BCCL")
    assert bccl is not None
    assert bccl["parent_id"] == "ORG-CIL-CIL"
    assert bccl["unit_type"] == OrganizationUnitType.SUBSIDIARY.value

    # CMPDI consultancy non-producing
    cmpdi = db.get_organization_unit("ORG-SUBSIDIARY-CMPDI")
    assert cmpdi is not None
    assert cmpdi["parent_id"] == "ORG-CIL-CIL"
    assert "Consultancy" in (cmpdi.get("metadata") or "")


# ------------------------------------------------------------
# 4. Area belongs to correct entity
# ------------------------------------------------------------
def test_04_area_belongs_to_correct_entity():
    jharia_area = db.get_organization_unit("ORG-AREA-BCCL-JHARIA")
    assert jharia_area is not None
    assert jharia_area["parent_id"] == "ORG-SUBSIDIARY-BCCL"
    assert jharia_area["unit_type"] == OrganizationUnitType.AREA.value

    talcher_area = db.get_organization_unit("ORG-AREA-MCL-TALCHER")
    assert talcher_area is not None
    assert talcher_area["parent_id"] == "ORG-SUBSIDIARY-MCL"


# ------------------------------------------------------------
# 5. Mine belongs to correct Area
# ------------------------------------------------------------
def test_05_mine_belongs_to_correct_area():
    jharia_mine_org = db.get_organization_unit("ORG-MINE-BCCL-JHARIA-UG")
    assert jharia_mine_org is not None
    assert jharia_mine_org["parent_id"] == "ORG-AREA-BCCL-JHARIA"
    assert jharia_mine_org["unit_type"] == OrganizationUnitType.MINE.value

    talcher_mine_org = db.get_organization_unit("ORG-MINE-MCL-TALCHER-OC")
    assert talcher_mine_org is not None
    assert talcher_mine_org["parent_id"] == "ORG-AREA-MCL-TALCHER"


# ------------------------------------------------------------
# 6. Mine type is stored as a property, not hierarchy node
# ------------------------------------------------------------
def test_06_mine_type_is_property_not_node():
    # Verify OrganizationUnitType enum does NOT contain MINE_TYPE
    unit_types = [t.value for t in OrganizationUnitType]
    assert "MINE_TYPE" not in unit_types
    assert "UNDERGROUND" not in unit_types
    assert "OPENCAST" not in unit_types

    # Mine record holds mine_type
    mine = db.get_mine("MINE-BCCL-JHARIA-01")
    assert mine is not None
    assert mine.mine_type == MineType.UNDERGROUND_COAL
    assert mine.organization_unit_id == "ORG-MINE-BCCL-JHARIA-UG"


# ------------------------------------------------------------
# 7. Operational unit belongs to correct Mine
# ------------------------------------------------------------
def test_07_operational_unit_belongs_to_correct_mine():
    shaft = db.get_operational_unit("OP-SHAFT-JHARIA-01")
    assert shaft is not None
    assert shaft["mine_id"] == "MINE-BCCL-JHARIA-01"
    assert shaft["unit_type"] == OperationalUnitType.SHAFT_INCLINE.value


# ------------------------------------------------------------
# 8. UG operational validation works
# ------------------------------------------------------------
def test_08_ug_operational_validation_works():
    # Valid UG operational types
    assert validate_operational_unit_compatibility("MINE-BCCL-JHARIA-01", OperationalUnitType.SHAFT_INCLINE) is True
    assert validate_operational_unit_compatibility("MINE-BCCL-JHARIA-01", OperationalUnitType.VENTILATION_DISTRICT) is True
    assert validate_operational_unit_compatibility("MINE-BCCL-JHARIA-01", OperationalUnitType.PANEL) is True
    assert validate_operational_unit_compatibility("MINE-BCCL-JHARIA-01", OperationalUnitType.SECTION) is True
    assert validate_operational_unit_compatibility("MINE-BCCL-JHARIA-01", OperationalUnitType.WORKING_FACE) is True

    # Invalid OC types on UG mine
    with pytest.raises(ValueError) as exc:
        validate_operational_unit_compatibility("MINE-BCCL-JHARIA-01", OperationalUnitType.PIT)
    assert "incompatible with UNDERGROUND mine" in str(exc.value)

    with pytest.raises(ValueError):
        validate_operational_unit_compatibility("MINE-BCCL-JHARIA-01", OperationalUnitType.BENCH)


# ------------------------------------------------------------
# 9. OC operational validation works
# ------------------------------------------------------------
def test_09_oc_operational_validation_works():
    # Valid OC operational types
    assert validate_operational_unit_compatibility("MINE-MCL-TALCHER-01", OperationalUnitType.PIT) is True
    assert validate_operational_unit_compatibility("MINE-MCL-TALCHER-01", OperationalUnitType.BENCH) is True
    assert validate_operational_unit_compatibility("MINE-MCL-TALCHER-01", OperationalUnitType.HAUL_ROAD) is True
    assert validate_operational_unit_compatibility("MINE-MCL-TALCHER-01", OperationalUnitType.DUMP_STOCK) is True
    assert validate_operational_unit_compatibility("MINE-MCL-TALCHER-01", OperationalUnitType.HEMM_PARK) is True

    # Invalid UG types on OC mine
    with pytest.raises(ValueError) as exc:
        validate_operational_unit_compatibility("MINE-MCL-TALCHER-01", OperationalUnitType.VENTILATION_DISTRICT)
    assert "incompatible with OPENCAST mine" in str(exc.value)

    with pytest.raises(ValueError):
        validate_operational_unit_compatibility("MINE-MCL-TALCHER-01", OperationalUnitType.WORKING_FACE)


# ------------------------------------------------------------
# 10. Contractor association works
# ------------------------------------------------------------
def test_10_contractor_association_works():
    dept = db.get_contractor("CONT-BCCL-DEPT")
    assert dept is not None
    assert dept["contractor_type"] == ContractorType.DEPARTMENTAL.value

    tml = db.get_contractor("CONT-TML")
    assert tml is not None
    assert tml["contractor_type"] == ContractorType.WORK_ORDER.value

    mdo = db.get_contractor("CONT-EMD-MDO")
    assert mdo is not None
    assert mdo["contractor_type"] == ContractorType.MDO.value


# ------------------------------------------------------------
# 11. Contract belongs to correct Mine
# ------------------------------------------------------------
def test_11_contract_belongs_to_correct_mine():
    contract = db.get_contract("CNTR-BCCL-JHARIA-01")
    assert contract is not None
    assert contract["mine_id"] == "MINE-BCCL-JHARIA-01"
    assert contract["contractor_id"] == "CONT-BCCL-DEPT"


# ------------------------------------------------------------
# 12. Contract lineage resolves correctly
# ------------------------------------------------------------
def test_12_contract_lineage_resolves_correctly():
    lineage = resolve_contract_hierarchy("CNTR-BCCL-JHARIA-01")
    assert lineage["contract"]["id"] == "CNTR-BCCL-JHARIA-01"
    assert lineage["contractor"]["id"] == "CONT-BCCL-DEPT"
    assert lineage["mine"]["code"] == "MINE-BCCL-JHARIA-01"
    assert lineage["area"]["code"] == "AREA-JHARIA"
    assert lineage["subsidiary"]["code"] == "BCCL"
    assert lineage["holding_company"]["code"] == "CIL"
    assert lineage["ministry"]["code"] == "MOC"


# ------------------------------------------------------------
# 13. Worker resolves to contract
# ------------------------------------------------------------
def test_13_worker_resolves_to_contract():
    worker = db.get_worker("WRK-TML-002")
    assert worker is not None
    assert worker["contract_id"] == "CNTR-BCCL-JHARIA-02"
    assert worker["contractor_id"] == "CONT-TML"
    assert worker["worker_type"] == WorkerType.CONTRACTOR.value


# ------------------------------------------------------------
# 14. Worker resolves to Mine
# ------------------------------------------------------------
def test_14_worker_resolves_to_mine():
    worker = db.get_worker("WRK-EMP-001")
    assert worker is not None
    assert worker["mine_id"] == "MINE-BCCL-JHARIA-01"
    assert worker["worker_type"] == WorkerType.DEPARTMENTAL.value


# ------------------------------------------------------------
# 15. Worker lineage resolves to Area/Subsidiary
# ------------------------------------------------------------
def test_15_worker_lineage_resolves_to_area_subsidiary():
    lineage = resolve_worker_hierarchy("WRK-TML-002")
    assert lineage["worker_code"] == "TML-WRK-8291"
    assert lineage["contract"]["id"] == "CNTR-BCCL-JHARIA-02"
    assert lineage["contractor"]["id"] == "CONT-TML"
    assert lineage["mine"]["code"] == "MINE-BCCL-JHARIA-01"
    assert lineage["area"]["code"] == "AREA-JHARIA"
    assert lineage["subsidiary"]["code"] == "BCCL"
    assert lineage["holding_company"]["code"] == "CIL"
    assert lineage["ministry"]["code"] == "MOC"


# ------------------------------------------------------------
# 16. Hierarchy tree works
# ------------------------------------------------------------
def test_16_hierarchy_tree_works():
    tree = get_hierarchy_tree(root_id=None, depth=5)
    assert len(tree) > 0
    ministry_node = tree[0]
    assert ministry_node["unit_type"] == OrganizationUnitType.MINISTRY.value
    assert len(ministry_node["children"]) > 0

    cil_node = ministry_node["children"][0]
    assert cil_node["unit_type"] == OrganizationUnitType.CIL.value
    assert len(cil_node["children"]) >= 4  # BCCL, ECL, MCL, SECL, etc.


# ------------------------------------------------------------
# 17. Hierarchy path works
# ------------------------------------------------------------
def test_17_hierarchy_path_works():
    path = get_hierarchy_path("ORG-MINE-BCCL-JHARIA-UG")
    assert len(path) == 5
    # Ordered upward: Mine -> Area -> Subsidiary -> CIL -> Ministry
    assert path[0]["unit_type"] == OrganizationUnitType.MINE.value
    assert path[1]["unit_type"] == OrganizationUnitType.AREA.value
    assert path[2]["unit_type"] == OrganizationUnitType.SUBSIDIARY.value
    assert path[3]["unit_type"] == OrganizationUnitType.CIL.value
    assert path[4]["unit_type"] == OrganizationUnitType.MINISTRY.value


# ------------------------------------------------------------
# 18. Parent-child validation works
# ------------------------------------------------------------
def test_18_parent_child_validation_works():
    # Valid
    assert validate_parent_child(OrganizationUnitType.MINISTRY, OrganizationUnitType.CIL) is True
    assert validate_parent_child(OrganizationUnitType.CIL, OrganizationUnitType.SUBSIDIARY) is True
    assert validate_parent_child(OrganizationUnitType.SUBSIDIARY, OrganizationUnitType.AREA) is True
    assert validate_parent_child(OrganizationUnitType.AREA, OrganizationUnitType.MINE) is True

    # Invalid transitions
    with pytest.raises(ValueError):
        validate_parent_child(OrganizationUnitType.MINE, OrganizationUnitType.SUBSIDIARY)

    with pytest.raises(ValueError):
        validate_parent_child(OrganizationUnitType.AREA, OrganizationUnitType.CIL)

    with pytest.raises(ValueError):
        validate_parent_child(OrganizationUnitType.MINE, OrganizationUnitType.AREA)

    with pytest.raises(ValueError):
        validate_parent_child(OrganizationUnitType.MINISTRY, OrganizationUnitType.MINE)


# ------------------------------------------------------------
# 19. Circular hierarchy rejected
# ------------------------------------------------------------
def test_19_circular_hierarchy_rejected():
    # Self-parenting
    with pytest.raises(ValueError) as exc:
        detect_circular_hierarchy("ORG-SUBSIDIARY-BCCL", "ORG-SUBSIDIARY-BCCL")
    assert "cannot be its own parent" in str(exc.value)

    # Inverted parent: proposing MOC's parent to be Jharia
    with pytest.raises(ValueError) as exc:
        detect_circular_hierarchy("ORG-CIL-CIL", "ORG-AREA-BCCL-JHARIA")
    assert "Circular hierarchy detected" in str(exc.value)


# ------------------------------------------------------------
# 20. Mine manager cannot access another mine
# ------------------------------------------------------------
def test_20_mine_manager_cannot_access_another_mine():
    # Access own mine: allowed
    assert assert_hierarchy_access(
        user_role="MINE_MANAGER",
        user_scope_type="MINE",
        user_scope_id="MINE-BCCL-JHARIA-01",
        target_unit_id="MINE-BCCL-JHARIA-01",
    ) is True

    # Access different mine: 403
    with pytest.raises(HTTPException) as exc:
        assert_hierarchy_access(
            user_role="MINE_MANAGER",
            user_scope_type="MINE",
            user_scope_id="MINE-BCCL-JHARIA-01",
            target_unit_id="MINE-MCL-TALCHER-01",
        )
    assert exc.value.status_code == 403


# ------------------------------------------------------------
# 21. Area scope inherits descendant mines
# ------------------------------------------------------------
def test_21_area_scope_inherits_descendant_mines():
    # Area manager can access mine inside that area
    assert assert_hierarchy_access(
        user_role="AREA_MANAGER",
        user_scope_type="AREA",
        user_scope_id="ORG-AREA-BCCL-JHARIA",
        target_unit_id="ORG-MINE-BCCL-JHARIA-UG",
    ) is True

    # Area manager cannot access mine outside that area
    with pytest.raises(HTTPException) as exc:
        assert_hierarchy_access(
            user_role="AREA_MANAGER",
            user_scope_type="AREA",
            user_scope_id="ORG-AREA-BCCL-JHARIA",
            target_unit_id="ORG-MINE-MCL-TALCHER-OC",
        )
    assert exc.value.status_code == 403


# ------------------------------------------------------------
# 22. Subsidiary scope inherits descendant Areas/Mines
# ------------------------------------------------------------
def test_22_subsidiary_scope_inherits_descendant_areas_and_mines():
    # BCCL manager can access Jharia Area and Jharia Mine
    assert assert_hierarchy_access(
        user_role="SUBSIDIARY_MANAGER",
        user_scope_type="SUBSIDIARY",
        user_scope_id="ORG-SUBSIDIARY-BCCL",
        target_unit_id="ORG-AREA-BCCL-JHARIA",
    ) is True
    assert assert_hierarchy_access(
        user_role="SUBSIDIARY_MANAGER",
        user_scope_type="SUBSIDIARY",
        user_scope_id="ORG-SUBSIDIARY-BCCL",
        target_unit_id="ORG-MINE-BCCL-JHARIA-UG",
    ) is True

    # Cannot access ECL Area or MCL Mine
    with pytest.raises(HTTPException) as exc:
        assert_hierarchy_access(
            user_role="SUBSIDIARY_MANAGER",
            user_scope_type="SUBSIDIARY",
            user_scope_id="ORG-SUBSIDIARY-BCCL",
            target_unit_id="ORG-AREA-ECL-RANIGANJ",
        )
    assert exc.value.status_code == 403


# ------------------------------------------------------------
# 23. Corporate scope resolves descendants correctly
# ------------------------------------------------------------
def test_23_corporate_scope_resolves_descendants_correctly():
    # CIL Corporate can access all units
    assert assert_hierarchy_access(
        user_role="CORPORATE_MANAGEMENT",
        user_scope_type="CIL",
        user_scope_id="ORG-CIL-CIL",
        target_unit_id="ORG-MINE-BCCL-JHARIA-UG",
    ) is True
    assert assert_hierarchy_access(
        user_role="CORPORATE_MANAGEMENT",
        user_scope_type="CIL",
        user_scope_id="ORG-CIL-CIL",
        target_unit_id="ORG-MINE-MCL-TALCHER-OC",
    ) is True


# ------------------------------------------------------------
# 24. Historical relationship resolution works
# ------------------------------------------------------------
def test_24_historical_relationship_resolution_works():
    unit = db.get_organization_unit("ORG-MINE-BCCL-JHARIA-UG")
    assert unit is not None
    assert unit["effective_from"] is not None
    # Verify path is resolved based on parent relationships
    path = get_hierarchy_path(unit["id"])
    assert any(p["id"] == "ORG-AREA-BCCL-JHARIA" for p in path)


# ------------------------------------------------------------
# 25. Existing Tasks 1–10 records resolve to canonical hierarchy
# ------------------------------------------------------------
def test_25_existing_tasks_1_10_records_resolve_to_canonical_hierarchy():
    # Jharia mine from Task 1 resolves to canonical hierarchy
    lineage = resolve_mine_hierarchy("MINE-BCCL-JHARIA-01")
    assert lineage["mine"]["code"] == "MINE-BCCL-JHARIA-01"
    assert lineage["area"]["code"] == "AREA-JHARIA"
    assert lineage["subsidiary"]["code"] == "BCCL"
    assert lineage["holding_company"]["code"] == "CIL"
    assert lineage["ministry"]["code"] == "MOC"

    # Talcher mine from Task 10 resolves to canonical hierarchy
    talcher_lineage = resolve_mine_hierarchy("MINE-MCL-TALCHER-01")
    assert talcher_lineage["mine"]["code"] == "MINE-MCL-TALCHER-01"
    assert talcher_lineage["area"]["code"] == "AREA-TALCHER"
    assert talcher_lineage["subsidiary"]["code"] == "MCL"


# ------------------------------------------------------------
# 26. Unauthorized master-data modification (403)
# ------------------------------------------------------------
def test_26_unauthorized_master_data_modification(client):
    res = client.post(
        "/api/hierarchy/units",
        json={
            "unit_type": "AREA",
            "code": "TEST-AREA",
            "name": "Test Area",
            "parent_id": "ORG-SUBSIDIARY-BCCL",
        },
        headers={"X-User-Role": "FIELD_INSPECTOR"},
    )
    assert res.status_code == 403


# ------------------------------------------------------------
# 27. Cross-mine contract access enforcement
# ------------------------------------------------------------
def test_27_cross_mine_contract_access(client):
    res = client.get(
        "/api/hierarchy/mines/MINE-MCL-TALCHER-01/contracts",
        headers={
            "X-User-Role": "MINE_MANAGER",
            "X-User-Scope-Type": "MINE",
            "X-User-Scope-Id": "MINE-BCCL-JHARIA-01",
        },
    )
    assert res.status_code == 403


# ------------------------------------------------------------
# 28. Cross-mine worker access enforcement
# ------------------------------------------------------------
def test_28_cross_mine_worker_access(client):
    res = client.get(
        "/api/hierarchy/mines/MINE-MCL-TALCHER-01/workforce",
        headers={
            "X-User-Role": "MINE_MANAGER",
            "X-User-Scope-Type": "MINE",
            "X-User-Scope-Id": "MINE-BCCL-JHARIA-01",
        },
    )
    assert res.status_code == 403


# ------------------------------------------------------------
# 29. Invalid operational unit type rejection via API
# ------------------------------------------------------------
def test_29_invalid_operational_unit_type(client):
    res = client.post(
        "/api/hierarchy/operational-units",
        json={
            "mine_id": "MINE-BCCL-JHARIA-01",
            "unit_type": "PIT",  # Incompatible with UG
            "code": "PIT-ILLEGAL",
            "name": "Illegal Pit in UG Mine",
        },
        headers={"X-User-Role": "ADMIN"},
    )
    assert res.status_code == 400
    assert "incompatible with UNDERGROUND mine" in res.json()["detail"]


# ------------------------------------------------------------
# 30. Duplicate seed execution idempotency
# ------------------------------------------------------------
def test_30_duplicate_seed_execution_idempotency():
    units_count_before = len(db.list_organization_units())
    workers_count_before = len(db.list_workers())
    contracts_count_before = len(db.list_contracts())

    # Run seed again
    seed_initial_data()

    units_count_after = len(db.list_organization_units())
    workers_count_after = len(db.list_workers())
    contracts_count_after = len(db.list_contracts())

    assert units_count_before == units_count_after
    assert workers_count_before == workers_count_after
    assert contracts_count_before == contracts_count_after


# ------------------------------------------------------------
# 31. Audit event creation on modification
# ------------------------------------------------------------
def test_31_audit_event_creation(client):
    events_before = len(db.get_organization_audit_events())

    # Create a test operational unit
    res = client.post(
        "/api/hierarchy/operational-units",
        json={
            "mine_id": "MINE-MCL-TALCHER-01",
            "unit_type": "BENCH",
            "code": "BN-TEST-AUDIT",
            "name": "Test Bench for Audit Event",
        },
        headers={"X-User-Role": "ADMIN", "X-User-Id": "AUDIT_ADMIN_USER"},
    )
    assert res.status_code == 200

    events_after = len(db.get_organization_audit_events())
    assert events_after == events_before + 1

    latest_events = db.get_organization_audit_events(limit=1)
    assert latest_events[0]["action"] == "CREATE_OPERATIONAL_UNIT"
    assert latest_events[0]["actor_id"] == "AUDIT_ADMIN_USER"
