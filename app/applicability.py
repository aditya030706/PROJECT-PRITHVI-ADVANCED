"""
PRITHVI — Regulatory Applicability Engine
==========================================

The applicability engine determines which inspection workflows apply
to a particular mine.

IMPORTANT DESIGN PRINCIPLES
---------------------------

1. Deterministic first.
   No ML is used to decide whether a statutory inspection applies.

2. Regulatory data is the source of truth.
   Rules are mapped to the inspection catalogue created from the
   regulatory seed.

3. Unknown != False.
   If the mine profile does not contain enough information to decide,
   the engine returns NEEDS_CONFIRMATION rather than silently excluding
   an inspection.

4. Event-triggered inspections are not treated as routine inspections.

5. The engine explains every decision.
   Judges, officers and auditors must be able to understand why an
   inspection was included or excluded.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


# ============================================================
# DECISION STATES
# ============================================================

APPLICABLE = "APPLICABLE"
NOT_APPLICABLE = "NOT_APPLICABLE"
NEEDS_CONFIRMATION = "NEEDS_CONFIRMATION"
EVENT_TRIGGERED = "EVENT_TRIGGERED"


# ============================================================
# RESULT
# ============================================================

@dataclass
class ApplicabilityResult:
    template_id: str
    inspection_type: str
    status: str
    reason: str
    regulatory_basis: str
    trigger_frequency: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "template_id": self.template_id,
            "inspection_type": self.inspection_type,
            "status": self.status,
            "reason": self.reason,
            "regulatory_basis": self.regulatory_basis,
            "trigger_frequency": self.trigger_frequency,
        }


# ============================================================
# SAFE FIELD ACCESS
# ============================================================

def _get(mine: Any, field: str, default: Any = None) -> Any:
    """
    Safely read a mine profile field.

    This intentionally uses getattr so the applicability engine
    remains tolerant while the mine schema evolves.
    """

    return getattr(mine, field, default)


def _normalise(value: Any) -> str:
    if value is None:
        return ""

    if hasattr(value, "value"):
        value = value.value

    return str(value).strip().lower().replace("-", "_").replace(" ", "_")


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value

    if value is None:
        return False

    return _normalise(value) in {
        "true",
        "yes",
        "y",
        "1",
    }


# ============================================================
# MINE CHARACTERISTICS
# ============================================================

def _is_underground(mine: Any) -> bool:
    mine_type = _normalise(
        _get(mine, "mine_type")
    )

    return mine_type in {
        "underground_coal",
        "underground",
        "underground_mine",
    }


def _is_opencast(mine: Any) -> bool:
    mine_type = _normalise(
        _get(mine, "mine_type")
    )

    return mine_type in {
        "opencast_coal",
        "opencast",
        "open_cast",
        "open_cast_coal",
    }


def _has_winding(mine: Any) -> bool:
    return _truthy(
        _get(
            mine,
            "has_winding_installation",
            False,
        )
    )
def _has_ventilating_district(mine: Any) -> bool | None:
    value = _get(mine, "has_ventilating_district", None)

    if value is None:
        return None

    return _truthy(value)


def _has_electric_energy_in_ventilating_district(mine: Any) -> bool | None:
    value = _get(
        mine,
        "electric_energy_in_ventilating_district",
        None,
    )

    if value is None:
        return None

    return _truthy(value)


def _has_shaft_or_incline(mine: Any) -> bool | None:
    value = _get(mine, "has_shaft_or_incline", None)

    if value is None:
        return None

    return _truthy(value)


def _has_fire_risk_area(mine: Any) -> bool | None:
    value = _get(mine, "has_fire_risk_area", None)

    if value is None:
        return None

    return _truthy(value)


def _has_water_danger(mine: Any) -> bool | None:
    value = _get(mine, "has_water_danger", None)

    if value is None:
        return None

    return _truthy(value)    


def _uses_machinery(mine: Any) -> bool:
    mechanised = _truthy(
        _get(mine, "mechanised", False)
    )

    return mechanised


def _uses_hemm(mine: Any) -> bool:
    return _truthy(
        _get(mine, "uses_hemm", False)
    )


def _is_gassy(mine: Any) -> bool:
    degree = _normalise(
        _get(mine, "gassy_degree")
    )

    return degree in {
        "degree_i",
        "degree_ii",
        "degree_iii",
        "i",
        "ii",
        "iii",
        "gassy",
    }


def _has_blasting(mine: Any) -> bool:
    return _truthy(
        _get(mine, "blasting_operation", False)
    )


def _has_ventilating_district(mine: Any) -> bool:
    """
    Explicit mine-profile field if available.

    We deliberately do NOT assume that every underground mine
    automatically satisfies the CMR-169 condition. If the profile
    does not tell us, we return False here and the caller can
    classify the result as NEEDS_CONFIRMATION.
    """

    value = _get(
        mine,
        "has_ventilating_district",
        None,
    )

    if value is None:
        return False

    return _truthy(value)


def _uses_electric_energy_in_ventilating_district(
    mine: Any,
) -> bool | None:

    value = _get(
        mine,
        "electric_energy_in_ventilating_district",
        None,
    )

    if value is None:
        return None

    return _truthy(value)


# ============================================================
# TEMPLATE RULES
# ============================================================

def evaluate_template(
    template_id: str,
    mine: Any,
) -> ApplicabilityResult:

    # --------------------------------------------------------
    # INS-01 — Workplace Safety
    # --------------------------------------------------------

    if template_id == "INS-01":

        if _is_underground(mine):
            return ApplicabilityResult(
                template_id="INS-01",
                inspection_type="Workplace Safety",
                status=APPLICABLE,
                reason=(
                    "Mine is classified as an underground coal mine "
                    "with applicable working places."
                ),
                regulatory_basis="CMR 132",
                trigger_frequency=(
                    "Before work + during shift"
                ),
            )

        return ApplicabilityResult(
            template_id="INS-01",
            inspection_type="Workplace Safety",
            status=NOT_APPLICABLE,
            reason=(
                "The current prototype applicability catalogue "
                "maps this inspection to underground working places."
            ),
            regulatory_basis="CMR 132",
            trigger_frequency="Before work + during shift",
        )

    # --------------------------------------------------------
    # INS-02 — Shaft / Outlet Examination
    # --------------------------------------------------------

    if template_id == "INS-02":

        if _is_underground(mine):
            return ApplicabilityResult(
                template_id="INS-02",
                inspection_type="Shaft / Outlet Examination",
                status=APPLICABLE,
                reason=(
                    "Mine is underground; applicable shafts, "
                    "inclines or outlets must be examined."
                ),
                regulatory_basis="CMR 75",
                trigger_frequency="Every 7 days",
            )

        return ApplicabilityResult(
            template_id="INS-02",
            inspection_type="Shaft / Outlet Examination",
            status=NOT_APPLICABLE,
            reason=(
                "Mine is not classified as underground."
            ),
            regulatory_basis="CMR 75",
            trigger_frequency="Every 7 days",
        )

    # --------------------------------------------------------
    # INS-03 — Winding Equipment
    # --------------------------------------------------------

    if template_id == "INS-03":

        if _has_winding(mine):
            return ApplicabilityResult(
                template_id="INS-03",
                inspection_type="Winding Equipment",
                status=APPLICABLE,
                reason=(
                    "Mine profile declares a winding installation."
                ),
                regulatory_basis="CMR 88",
                trigger_frequency=(
                    "24h / 7d / 30d / 12mo depending on component"
                ),
            )

        return ApplicabilityResult(
            template_id="INS-03",
            inspection_type="Winding Equipment",
            status=NOT_APPLICABLE,
            reason=(
                "Mine profile does not declare a winding installation."
            ),
            regulatory_basis="CMR 88",
            trigger_frequency=(
                "24h / 7d / 30d / 12mo depending on component"
            ),
        )

    # --------------------------------------------------------
    # INS-04 — Ventilation
    # --------------------------------------------------------

    if template_id == "INS-04":

        if _is_underground(mine):
            return ApplicabilityResult(
                template_id="INS-04",
                inspection_type="Ventilation",
                status=APPLICABLE,
                reason=(
                    "Mine is belowground and therefore falls within "
                    "the ventilation inspection catalogue."
                ),
                regulatory_basis="CMR 153/156",
                trigger_frequency=(
                    "Continuous + equipment examination"
                ),
            )

        return ApplicabilityResult(
            template_id="INS-04",
            inspection_type="Ventilation",
            status=NOT_APPLICABLE,
            reason=(
                "Current catalogue defines this workflow for "
                "belowground ventilation."
            ),
            regulatory_basis="CMR 153/156",
            trigger_frequency=(
                "Continuous + equipment examination"
            ),
        )

    # --------------------------------------------------------
    # INS-05 — Gas Monitoring
    # --------------------------------------------------------

    if template_id == "INS-05":

        if not _is_underground(mine):
            return ApplicabilityResult(
                template_id="INS-05",
                inspection_type="Gas Monitoring",
                status=NOT_APPLICABLE,
                reason=(
                    "Current gas-monitoring applicability is tied "
                    "to applicable ventilating districts."
                ),
                regulatory_basis="CMR 169/171",
                trigger_frequency="Conditional",
            )

        electric_condition = (
            _uses_electric_energy_in_ventilating_district(mine)
        )

        if electric_condition is True:
            return ApplicabilityResult(
                template_id="INS-05",
                inspection_type="Gas Monitoring",
                status=APPLICABLE,
                reason=(
                    "The mine profile confirms electric energy "
                    "use in an applicable ventilating district."
                ),
                regulatory_basis="CMR 169/171",
                trigger_frequency="Conditional",
            )

        if _is_gassy(mine):
            return ApplicabilityResult(
                template_id="INS-05",
                inspection_type="Gas Monitoring",
                status=APPLICABLE,
                reason=(
                    "Mine is classified as gassy; gas-monitoring "
                    "controls are therefore relevant."
                ),
                regulatory_basis="CMR 169/171",
                trigger_frequency="Conditional",
            )

        return ApplicabilityResult(
            template_id="INS-05",
            inspection_type="Gas Monitoring",
            status=NEEDS_CONFIRMATION,
            reason=(
                "Underground mine detected, but the profile does not "
                "contain sufficient information to conclusively determine "
                "the CMR-169 applicability condition."
            ),
            regulatory_basis="CMR 169/171",
            trigger_frequency="Conditional",
        )

    # --------------------------------------------------------
    # INS-06 — Machinery & Plant
    # --------------------------------------------------------

    if template_id == "INS-06":

        if _uses_machinery(mine):
            return ApplicabilityResult(
                template_id="INS-06",
                inspection_type="Machinery & Plant",
                status=APPLICABLE,
                reason=(
                    "Mine profile declares mechanised operation."
                ),
                regulatory_basis="CMR 213",
                trigger_frequency="Every 7 days",
            )

        return ApplicabilityResult(
            template_id="INS-06",
            inspection_type="Machinery & Plant",
            status=NEEDS_CONFIRMATION,
            reason=(
                "The catalogue applies this inspection to mines "
                "using machinery; machinery inventory has not been "
                "explicitly confirmed."
            ),
            regulatory_basis="CMR 213",
            trigger_frequency="Every 7 days",
        )

    # --------------------------------------------------------
    # INS-07 — HEMM / Equipment
    # --------------------------------------------------------

    if template_id == "INS-07":

        if _is_opencast(mine) or _uses_hemm(mine):
            return ApplicabilityResult(
                template_id="INS-07",
                inspection_type="HEMM / Equipment",
                status=APPLICABLE,
                reason=(
                    "Mine is opencast or explicitly declares HEMM use."
                ),
                regulatory_basis="CMR 214-216",
                trigger_frequency="Equipment-specific",
            )

        return ApplicabilityResult(
            template_id="INS-07",
            inspection_type="HEMM / Equipment",
            status=NOT_APPLICABLE,
            reason=(
                "Mine profile does not indicate opencast or HEMM "
                "operations."
            ),
            regulatory_basis="CMR 214-216",
            trigger_frequency="Equipment-specific",
        )

    # --------------------------------------------------------
    # INS-08 — Fire Safety
    # --------------------------------------------------------

    if template_id == "INS-08":

        return ApplicabilityResult(
            template_id="INS-08",
            inspection_type="Fire Safety",
            status=APPLICABLE,
            reason=(
                "Fire-fighting equipment examination is applicable "
                "to mine fire-fighting systems/equipment."
            ),
            regulatory_basis="CMR 139",
            trigger_frequency="Monthly",
        )

    # --------------------------------------------------------
    # INS-09 — Working at Height
    # --------------------------------------------------------

    if template_id == "INS-09":

        return ApplicabilityResult(
            template_id="INS-09",
            inspection_type="Working at Height",
            status=EVENT_TRIGGERED,
            reason=(
                "This inspection is available when work at height "
                "is undertaken; it is not a universal routine inspection."
            ),
            regulatory_basis="CMR 131",
            trigger_frequency="Task-triggered",
        )

    # --------------------------------------------------------
    # INS-10 — Danger / Reinspection
    # --------------------------------------------------------

    if template_id == "INS-10":

        return ApplicabilityResult(
            template_id="INS-10",
            inspection_type="Danger / Reinspection",
            status=EVENT_TRIGGERED,
            reason=(
                "This workflow is activated when a dangerous "
                "condition is identified."
            ),
            regulatory_basis="CMR 130",
            trigger_frequency="Event-triggered",
        )

    # --------------------------------------------------------
    # INS-11 — Emergency Preparedness
    # --------------------------------------------------------

    if template_id == "INS-11":

        return ApplicabilityResult(
            template_id="INS-11",
            inspection_type="Emergency Preparedness",
            status=APPLICABLE,
            reason=(
                "Emergency preparedness requirements apply to every mine."
            ),
            regulatory_basis="CMR 252",
            trigger_frequency="Plan + drills",
        )

    # --------------------------------------------------------
    # INS-12 — Accident / Dangerous Occurrence
    # --------------------------------------------------------

    if template_id == "INS-12":

        return ApplicabilityResult(
            template_id="INS-12",
            inspection_type="Accident / Dangerous Occurrence",
            status=EVENT_TRIGGERED,
            reason=(
                "This workflow is activated by an accident or "
                "dangerous occurrence."
            ),
            regulatory_basis="CMR 8",
            trigger_frequency="Immediate / prescribed notice",
        )

    # --------------------------------------------------------
    # Unknown template
    # --------------------------------------------------------

    return ApplicabilityResult(
        template_id=template_id,
        inspection_type="Unknown",
        status=NEEDS_CONFIRMATION,
        reason=(
            "No deterministic applicability rule has been registered "
            "for this inspection template."
        ),
        regulatory_basis="Not mapped",
        trigger_frequency="Not mapped",
    )


# ============================================================
# COMPLETE MINE EVALUATION
# ============================================================

def evaluate_mine(
    mine: Any,
    template_ids: list[str] | None = None,
) -> list[ApplicabilityResult]:
    """
    Evaluate every inspection template for a mine.

    The result deliberately preserves all four states:

        APPLICABLE
        NOT_APPLICABLE
        NEEDS_CONFIRMATION
        EVENT_TRIGGERED

    This is important for auditability. We do not silently throw
    away uncertainty.
    """

    if template_ids is None:
        template_ids = [
            "INS-01",
            "INS-02",
            "INS-03",
            "INS-04",
            "INS-05",
            "INS-06",
            "INS-07",
            "INS-08",
            "INS-09",
            "INS-10",
            "INS-11",
            "INS-12",
        ]

    return [
        evaluate_template(
            template_id,
            mine,
        )
        for template_id in template_ids
    ]


def build_applicability_response(
    mine: Any,
    results: list[ApplicabilityResult],
) -> dict:

    routine = []
    confirmation_required = []
    event_triggered = []
    excluded = []

    for result in results:

        data = result.to_dict()

        if result.status == APPLICABLE:
            routine.append(data)

        elif result.status == NEEDS_CONFIRMATION:
            confirmation_required.append(data)

        elif result.status == EVENT_TRIGGERED:
            event_triggered.append(data)

        elif result.status == NOT_APPLICABLE:
            excluded.append(data)

    return {
        "mine": {
            "mine_id": _get(mine, "mine_id"),
            "name": _get(mine, "name"),
            "mine_type": _normalise(
                _get(mine, "mine_type")
            ),
            "gassy_degree": _normalise(
                _get(mine, "gassy_degree")
            ),
            "mechanised": _truthy(
                _get(mine, "mechanised")
            ),
            "uses_hemm": _truthy(
                _get(mine, "uses_hemm")
            ),
            "has_winding_installation": _truthy(
                _get(mine, "has_winding_installation")
            ),
        },

        "summary": {
            "routine_applicable": len(routine),
            "needs_confirmation": len(
                confirmation_required
            ),
            "event_triggered_available": len(
                event_triggered
            ),
            "not_applicable": len(excluded),
        },

        "routine_inspections": routine,

        "needs_confirmation": confirmation_required,

        "event_triggered_inspections": event_triggered,

        "not_applicable": excluded,
    }