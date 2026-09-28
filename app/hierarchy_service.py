"""
PRITHVI Governance Master Hierarchy & Scope Engine (Phase 2 Task 11)

Canonical Governance Backbone:
MINISTRY OF COAL
        ↓
COAL INDIA LIMITED
        ↓
CIL ORGANIZATIONAL ENTITY / SUBSIDIARY
        ↓
AREA
        ↓
MINE / PROJECT
        ↓
OPERATIONAL UNITS (Underground vs Opencast)

Relational Governance Associations:
Mine ── Contract ── Contractor ── Workers
Mine ── Shift/Activity, Inspection, Compliance, Attendance, Telemetry, Production, Cases
"""

from __future__ import annotations

from typing import Optional, Any
from fastapi import HTTPException, status

from .models import (
    OrganizationUnit,
    OrganizationUnitType,
    OperationalUnit,
    OperationalUnitType,
    MineType,
    ContractorMaster,
    ContractMaster,
    WorkerMaster,
)
from .database import (
    get_organization_unit,
    list_organization_units,
    get_operational_unit,
    list_operational_units,
    get_contractor,
    get_contract,
    get_worker,
    get_mine,
    list_mines,
)


# Allowed parent-child organizational hierarchy transitions
ALLOWED_PARENT_CHILD: dict[OrganizationUnitType, list[OrganizationUnitType]] = {
    OrganizationUnitType.MINISTRY: [OrganizationUnitType.CIL],
    OrganizationUnitType.CIL: [OrganizationUnitType.SUBSIDIARY],
    OrganizationUnitType.SUBSIDIARY: [OrganizationUnitType.AREA],
    OrganizationUnitType.AREA: [OrganizationUnitType.MINE],
    OrganizationUnitType.MINE: [],  # Mine has no organizational children (operational units are handled separately)
}

# Operational unit type classifications by mine type
UNDERGROUND_OPERATIONAL_TYPES = {
    OperationalUnitType.SHAFT_INCLINE,
    OperationalUnitType.VENTILATION_DISTRICT,
    OperationalUnitType.PANEL,
    OperationalUnitType.SECTION,
    OperationalUnitType.WORKING_FACE,
}

OPENCAST_OPERATIONAL_TYPES = {
    OperationalUnitType.PIT,
    OperationalUnitType.BENCH,
    OperationalUnitType.HAUL_ROAD,
    OperationalUnitType.DUMP_STOCK,
    OperationalUnitType.HEMM_PARK,
}


def validate_parent_child(parent_type: OrganizationUnitType | str, child_type: OrganizationUnitType | str) -> bool:
    """
    Validate allowed parent-child organizational unit type transitions.
    Allowed:
      MINISTRY -> CIL
      CIL -> SUBSIDIARY
      SUBSIDIARY -> AREA
      AREA -> MINE
    Raises ValueError if invalid.
    """
    p_type = OrganizationUnitType(parent_type) if isinstance(parent_type, str) else parent_type
    c_type = OrganizationUnitType(child_type) if isinstance(child_type, str) else child_type

    allowed = ALLOWED_PARENT_CHILD.get(p_type, [])
    if c_type not in allowed:
        raise ValueError(
            f"Invalid parent-child relationship: {p_type.value} cannot be parent of {c_type.value}. "
            f"Allowed child types for {p_type.value}: {[a.value for a in allowed]}"
        )
    return True


def detect_circular_hierarchy(unit_id: str, proposed_parent_id: Optional[str]) -> bool:
    """
    Detect cycles in the organizational unit parent-child graph.
    Walks up from proposed_parent_id. If unit_id is found in the ancestor chain, raises ValueError.
    """
    if not proposed_parent_id:
        return False

    if unit_id == proposed_parent_id:
        raise ValueError(f"Circular hierarchy detected: Unit '{unit_id}' cannot be its own parent.")

    current_id = proposed_parent_id
    visited = {unit_id}

    while current_id:
        if current_id in visited:
            raise ValueError(f"Circular hierarchy detected: Ancestor '{current_id}' links back to '{unit_id}'.")
        visited.add(current_id)

        parent_unit = get_organization_unit(current_id)
        if not parent_unit:
            break
        current_id = parent_unit.get("parent_id")

    return False


def validate_operational_unit_compatibility(
    mine_id: str, unit_type: OperationalUnitType | str
) -> bool:
    """
    Enforce mine-type compatibility for operational units.
    Underground mines reject PIT, BENCH, HAUL_ROAD, DUMP_STOCK, HEMM_PARK.
    Opencast mines reject SHAFT_INCLINE, VENTILATION_DISTRICT, PANEL, SECTION, WORKING_FACE.
    """
    op_type = OperationalUnitType(unit_type) if isinstance(unit_type, str) else unit_type

    mine = get_mine(mine_id)
    if not mine:
        # Check if mine_id is an organization unit of type MINE
        org_unit = get_organization_unit(mine_id)
        if org_unit and org_unit.get("unit_type") == OrganizationUnitType.MINE.value:
            # Find matching mine by organization_unit_id
            all_mines = list_mines()
            for m in all_mines:
                if getattr(m, "organization_unit_id", None) == mine_id:
                    mine = m
                    break
        if not mine:
            raise ValueError(f"Mine '{mine_id}' not found for operational unit validation.")

    is_underground = mine.mine_type in (MineType.UNDERGROUND_COAL, "underground_coal", "UNDERGROUND")
    is_opencast = mine.mine_type in (MineType.OPENCAST_COAL, "opencast_coal", "OPENCAST")

    if is_underground and op_type in OPENCAST_OPERATIONAL_TYPES:
        raise ValueError(
            f"Operational unit type '{op_type.value}' is incompatible with UNDERGROUND mine '{mine.name}'. "
            f"Allowed types for underground mines: {[t.value for t in UNDERGROUND_OPERATIONAL_TYPES]}"
        )

    if is_opencast and op_type in UNDERGROUND_OPERATIONAL_TYPES:
        raise ValueError(
            f"Operational unit type '{op_type.value}' is incompatible with OPENCAST mine '{mine.name}'. "
            f"Allowed types for opencast mines: {[t.value for t in OPENCAST_OPERATIONAL_TYPES]}"
        )

    return True


def get_hierarchy_path(unit_id: str) -> list[dict]:
    """
    Return path ordered upward: [Mine, Area, Subsidiary/Entity, CIL, Ministry].
    """
    path: list[dict] = []
    current_id: Optional[str] = unit_id

    # If unit_id is a mine_id from the mines table rather than an organization_unit id:
    mine_record = get_mine(unit_id)
    if mine_record and getattr(mine_record, "organization_unit_id", None):
        current_id = mine_record.organization_unit_id
    elif mine_record and not get_organization_unit(unit_id):
        # Look for organization unit matching this mine
        all_units = list_organization_units(unit_type="MINE")
        for u in all_units:
            if u["code"] == mine_record.mine_id or u["name"] == mine_record.name:
                current_id = u["id"]
                break

    visited = set()
    while current_id:
        if current_id in visited:
            break
        visited.add(current_id)

        unit = get_organization_unit(current_id)
        if not unit:
            break

        path.append({
            "id": unit["id"],
            "unit_type": unit["unit_type"],
            "code": unit["code"],
            "name": unit["name"],
            "legal_name": unit.get("legal_name"),
            "status": unit.get("status"),
            "state": unit.get("state"),
            "district": unit.get("district"),
            "headquarters": unit.get("headquarters"),
        })

        current_id = unit.get("parent_id")

    return path


def get_hierarchy_tree(root_id: Optional[str] = None, depth: int = 5) -> list[dict]:
    """
    Build nested organizational hierarchy tree starting from root_id (or top-level nodes).
    Attaches mine profile for MINE nodes.
    """
    all_units = list_organization_units()
    all_mines = list_mines()
    mines_by_org_id = {
        getattr(m, "organization_unit_id", None): m
        for m in all_mines
        if getattr(m, "organization_unit_id", None)
    }
    # Also index by mine_id or code
    mines_by_code = {m.mine_id: m for m in all_mines}

    # Group children by parent_id
    children_by_parent: dict[Optional[str], list[dict]] = {}
    unit_map: dict[str, dict] = {}

    for u in all_units:
        unit_map[u["id"]] = u
        parent = u.get("parent_id")
        if parent not in children_by_parent:
            children_by_parent[parent] = []
        children_by_parent[parent].append(u)

    def _build_node(node_dict: dict, current_depth: int) -> dict:
        nid = node_dict["id"]
        node_res = {
            "id": nid,
            "parent_id": node_dict.get("parent_id"),
            "unit_type": node_dict["unit_type"],
            "code": node_dict["code"],
            "name": node_dict["name"],
            "legal_name": node_dict.get("legal_name"),
            "status": node_dict.get("status"),
            "state": node_dict.get("state"),
            "district": node_dict.get("district"),
            "headquarters": node_dict.get("headquarters"),
            "mine_profile": None,
            "children": [],
        }

        if node_dict["unit_type"] == OrganizationUnitType.MINE.value:
            mine_rec = mines_by_org_id.get(nid) or mines_by_code.get(node_dict["code"])
            if mine_rec:
                node_res["mine_profile"] = {
                    "mine_id": mine_rec.mine_id,
                    "mine_type": mine_rec.mine_type.value if hasattr(mine_rec.mine_type, "value") else str(mine_rec.mine_type),
                    "gassy_degree": mine_rec.gassy_degree.value if hasattr(mine_rec.gassy_degree, "value") else str(mine_rec.gassy_degree),
                    "mechanised": mine_rec.mechanised,
                    "uses_hemm": mine_rec.uses_hemm,
                    "has_winding_installation": mine_rec.has_winding_installation,
                    "blasting_operation": mine_rec.blasting_operation,
                }

        if current_depth < depth:
            for child in children_by_parent.get(nid, []):
                node_res["children"].append(_build_node(child, current_depth + 1))

        return node_res

    if root_id:
        root_unit = unit_map.get(root_id)
        if not root_unit:
            return []
        return [_build_node(root_unit, 1)]

    # If no root specified, select all units without parent_id (or MINISTRY)
    root_units = children_by_parent.get(None, [])
    if not root_units:
        # Fallback to MINISTRY units
        root_units = [u for u in all_units if u["unit_type"] == OrganizationUnitType.MINISTRY.value]

    return [_build_node(u, 1) for u in root_units]


def assert_hierarchy_access(
    user_role: str,
    user_scope_type: Optional[str],
    user_scope_id: Optional[str],
    target_unit_id: str,
) -> bool:
    """
    Assert that a user's role + governance scope authorizes access to target_unit_id.
    Raises HTTPException(403) on violation.

    Hierarchy inheritance:
      - CIL / MINISTRY or global roles (ADMIN, SUPERADMIN, DIRECTOR) can access all descendants.
      - SUBSIDIARY can access descendant Areas, Mines, and Units within that subsidiary.
      - AREA can access descendant Mines and Units within that Area.
      - MINE can access only that Mine and its operational units.
    """
    normalized_role = (user_role or "").upper()

    # Global administrative access
    if normalized_role in ("ADMIN", "SUPERADMIN", "DIRECTOR"):
        return True

    # If no scope specified or scope is global/CIL/MINISTRY
    if not user_scope_type or user_scope_type.upper() in ("ALL", "GLOBAL", "MINISTRY", "CIL"):
        return True

    if not user_scope_id:
        return True

    scope_type = user_scope_type.upper()
    scope_id = user_scope_id

    # If target matches scope_id directly
    if target_unit_id == scope_id:
        return True

    # Check if target is an operational unit
    op_unit = get_operational_unit(target_unit_id)
    target_org_id = target_unit_id
    if op_unit:
        # Target is an operational unit -> resolve to its mine
        target_org_id = op_unit["mine_id"]

    # Check if target is a mine_id from mines table
    mine = get_mine(target_org_id)
    if mine and getattr(mine, "organization_unit_id", None):
        target_org_id = mine.organization_unit_id

    # If scope is MINE, target must match mine_id or mine org unit id
    if scope_type == "MINE":
        if target_unit_id == scope_id or target_org_id == scope_id:
            return True
        if mine and (mine.mine_id == scope_id or getattr(mine, "organization_unit_id", None) == scope_id):
            return True
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied: Mine manager scope '{scope_id}' cannot access '{target_unit_id}'.",
        )

    # Climb upward from target_org_id to see if scope_id is an ancestor
    path = get_hierarchy_path(target_org_id)
    ancestor_ids = {node["id"] for node in path}
    ancestor_codes = {node["code"] for node in path}

    # Also match if scope_id is in ancestor_ids or ancestor_codes
    if scope_id in ancestor_ids or scope_id in ancestor_codes:
        return True

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=f"Access denied: Target unit '{target_unit_id}' is outside authorized scope {scope_type}:{scope_id}.",
    )


def resolve_mine_hierarchy(mine_id: str) -> dict:
    """
    Resolve complete organizational lineage for a mine:
    Mine -> Area -> Subsidiary -> CIL -> Ministry
    """
    mine = get_mine(mine_id)
    org_unit_id = getattr(mine, "organization_unit_id", None) if mine else None

    if not org_unit_id:
        # Try matching by code or id directly
        org_u = get_organization_unit(mine_id)
        if org_u:
            org_unit_id = org_u["id"]
        else:
            # Look up among all organization units of type MINE
            for u in list_organization_units(unit_type="MINE"):
                if u["code"] == mine_id or (mine and u["name"] == mine.name):
                    org_unit_id = u["id"]
                    break

    path = get_hierarchy_path(org_unit_id) if org_unit_id else []

    nodes_by_type: dict[str, dict] = {}
    for node in path:
        nodes_by_type[node["unit_type"]] = node

    mine_info = nodes_by_type.get(OrganizationUnitType.MINE.value, {
        "id": mine_id,
        "name": mine.name if mine else mine_id,
        "code": mine_id,
        "unit_type": "MINE",
    })
    if mine:
        mine_info["mine_type"] = mine.mine_type.value if hasattr(mine.mine_type, "value") else str(mine.mine_type)
        mine_info["gassy_degree"] = mine.gassy_degree.value if hasattr(mine.gassy_degree, "value") else str(mine.gassy_degree)

    return {
        "mine": mine_info,
        "area": nodes_by_type.get(OrganizationUnitType.AREA.value, {}),
        "subsidiary": nodes_by_type.get(OrganizationUnitType.SUBSIDIARY.value, {}),
        "holding_company": nodes_by_type.get(OrganizationUnitType.CIL.value, {}),
        "ministry": nodes_by_type.get(OrganizationUnitType.MINISTRY.value, {}),
    }


def resolve_worker_hierarchy(worker_id: str) -> dict:
    """
    Resolve complete lineage for a worker:
    Worker -> Contract -> Contractor -> Mine -> Area -> Subsidiary -> CIL -> Ministry
    """
    worker = get_worker(worker_id)
    if not worker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Worker '{worker_id}' not found.",
        )

    contract_info = None
    contractor_info = None

    if worker.get("contract_id"):
        contract = get_contract(worker["contract_id"])
        if contract:
            contract_info = contract
            if contract.get("contractor_id"):
                contractor = get_contractor(contract["contractor_id"])
                if contractor:
                    contractor_info = contractor

    if not contractor_info and worker.get("contractor_id"):
        contractor_info = get_contractor(worker["contractor_id"])

    mine_lineage = resolve_mine_hierarchy(worker["mine_id"])

    return {
        "worker_id": worker["id"],
        "worker_code": worker["worker_code"],
        "worker_name": worker["name"],
        "worker_type": worker["worker_type"],
        "contract": contract_info,
        "contractor": contractor_info,
        "mine": mine_lineage.get("mine", {}),
        "area": mine_lineage.get("area", {}),
        "subsidiary": mine_lineage.get("subsidiary", {}),
        "holding_company": mine_lineage.get("holding_company", {}),
        "ministry": mine_lineage.get("ministry", {}),
    }


def resolve_operational_unit_hierarchy(operational_unit_id: str) -> dict:
    """
    Resolve operational unit lineage:
    Operational Unit -> (Parent Operational Unit)* -> Mine -> Area -> Subsidiary -> CIL -> Ministry
    """
    op_unit = get_operational_unit(operational_unit_id)
    if not op_unit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Operational unit '{operational_unit_id}' not found.",
        )

    parent_op = None
    if op_unit.get("parent_operational_unit_id"):
        parent_op = get_operational_unit(op_unit["parent_operational_unit_id"])

    mine_lineage = resolve_mine_hierarchy(op_unit["mine_id"])

    return {
        "operational_unit": op_unit,
        "parent_operational_unit": parent_op,
        "mine": mine_lineage.get("mine", {}),
        "area": mine_lineage.get("area", {}),
        "subsidiary": mine_lineage.get("subsidiary", {}),
        "holding_company": mine_lineage.get("holding_company", {}),
        "ministry": mine_lineage.get("ministry", {}),
    }


def resolve_contract_hierarchy(contract_id: str) -> dict:
    """
    Resolve contract lineage:
    Contract -> Contractor, Mine -> Area -> Subsidiary -> CIL -> Ministry
    """
    contract = get_contract(contract_id)
    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contract '{contract_id}' not found.",
        )

    contractor = get_contractor(contract["contractor_id"]) if contract.get("contractor_id") else None
    mine_lineage = resolve_mine_hierarchy(contract["mine_id"])

    return {
        "contract": contract,
        "contractor": contractor,
        "mine": mine_lineage.get("mine", {}),
        "area": mine_lineage.get("area", {}),
        "subsidiary": mine_lineage.get("subsidiary", {}),
        "holding_company": mine_lineage.get("holding_company", {}),
        "ministry": mine_lineage.get("ministry", {}),
    }
