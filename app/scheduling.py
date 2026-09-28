"""
PRITHVI — Mine-Specific Regulatory Scheduling Engine

The scheduler converts active RegulatoryScheduleRule records into
mine-specific MineInspectionSchedule records.

Important:
- Regulatory rules remain the source of truth for frequency.
- Mine profile fields determine applicability.
- Unknown mine conditions are NOT treated as False.
- Historical schedule rows are retained; obsolete active instances
  are deactivated when the database cleanup helper is available.
- No regulatory claim is made by this module; rule validation belongs
  to the regulatory dataset / authoritative-source workflow.
"""

from __future__ import annotations

import calendar
import json
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from . import database as db
from .models import MineInspectionSchedule


# ============================================================
# STATUS CONSTANTS
# ============================================================

STATUS_UPCOMING = "upcoming"
STATUS_DUE_SOON = "due_soon"
STATUS_DUE = "due"
STATUS_OVERDUE = "overdue"
STATUS_ONGOING = "ongoing"
STATUS_EVENT_TRIGGERED = "event_triggered"
STATUS_NEEDS_CONDITION = "needs_condition"
STATUS_UNSCHEDULED = "unscheduled"


# ============================================================
# TIME HELPERS
# ============================================================

def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _parse_datetime(value: Any) -> Optional[datetime]:
    if value is None:
        return None

    if isinstance(value, datetime):
        return _ensure_utc(value)

    try:
        return _ensure_utc(
            datetime.fromisoformat(
                str(value).replace("Z", "+00:00")
            )
        )
    except (TypeError, ValueError):
        return None


# ============================================================
# VALUE HELPERS
# ============================================================

def _as_value(value: Any) -> Any:
    return getattr(value, "value", value)


def _normalise(value: Any) -> str:
    if value is None:
        return ""

    value = _as_value(value)

    return (
        str(value)
        .strip()
        .lower()
        .replace("-", "_")
        .replace(" ", "_")
    )


def _json_list(value: Any) -> list[str]:
    if value is None:
        return []

    if isinstance(value, str):
        try:
            decoded = json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return [_normalise(value)]

        if isinstance(decoded, list):
            return [_normalise(item) for item in decoded]

        return [_normalise(decoded)]

    if isinstance(value, (list, tuple, set)):
        return [_normalise(item) for item in value]

    return [_normalise(value)]


def _mine_type(mine: Any) -> str:
    return _normalise(getattr(mine, "mine_type", None))


def _gassy_degree(mine: Any) -> str:
    return _normalise(getattr(mine, "gassy_degree", None))


def _optional_bool(mine: Any, field: str) -> Optional[bool]:
    value = getattr(mine, field, None)

    if value is None:
        return None

    if isinstance(value, bool):
        return value

    normalized = _normalise(value)

    if normalized in {"true", "yes", "y", "1"}:
        return True

    if normalized in {"false", "no", "n", "0"}:
        return False

    return None


# ============================================================
# CONDITION EVALUATION
# ============================================================

def _condition_requirement(
    rule: Any,
    mine: Any,
) -> Optional[bool]:
    """
    Evaluate the explicit condition represented by a known schedule rule.

    Return values:
        True  = condition confirmed
        False = condition disproved
        None  = profile does not contain enough information

    We intentionally do not parse arbitrary natural-language regulatory
    text into executable logic. Known prototype rule IDs are mapped to
    existing Mine fields.
    """

    schedule_id = _normalise(
        getattr(rule, "schedule_id", "")
    )

    # --------------------------------------------------------
    # Surface water rule
    # --------------------------------------------------------

    if schedule_id == "sch_cmr_149_9_water":
        return _optional_bool(
            mine,
            "has_water_danger",
        )

    # --------------------------------------------------------
    # Ventilation air quantity
    # --------------------------------------------------------

    if schedule_id == "sch_cmr_156_8_air_quantity":
        return _optional_bool(
            mine,
            "has_ventilating_district",
        )

    # --------------------------------------------------------
    # Ventilation appliances
    # --------------------------------------------------------

    if schedule_id == "sch_cmr_159_12_vent_appliances":
        return _optional_bool(
            mine,
            "has_ventilating_district",
        )

    # --------------------------------------------------------
    # Ventilation air / temperature
    # --------------------------------------------------------

    if schedule_id == "sch_cmr_153_2e_air_temp":
        return _optional_bool(
            mine,
            "has_ventilating_district",
        )

    # --------------------------------------------------------
    # Mechanical ventilator / booster fan
    #
    # The current Mine model does not contain a dedicated
    # has_mechanical_ventilator / has_booster_fan field.
    #
    # Therefore we MUST NOT infer False from its absence.
    # None means "needs confirmation".
    # --------------------------------------------------------

    if schedule_id == "sch_cmr_156_3_ventilator":
        return None

    # --------------------------------------------------------
    # Coal dust zone sampling
    #
    # No dedicated coal-dust-zone field currently exists.
    # Do not infer absence.
    # --------------------------------------------------------

    if schedule_id == "sch_cmr_145_7_dust":
        return None

    return True


def evaluate_schedule_rule(
    rule: Any,
    mine: Any,
) -> str:
    """
    Return one of:
        APPLICABLE
        NOT_APPLICABLE
        NEEDS_CONFIRMATION
    """

    mine_type = _mine_type(mine)
    gassy_degree = _gassy_degree(mine)

    mine_types = set(
        _json_list(
            getattr(rule, "applicable_mine_types", [])
        )
    )

    gassy_degrees = set(
        _json_list(
            getattr(rule, "applicable_gassy_degrees", [])
        )
    )

    if mine_types and "all" not in mine_types:
        if mine_type not in mine_types:
            return "NOT_APPLICABLE"

    if gassy_degrees and "all" not in gassy_degrees:
        if gassy_degree not in gassy_degrees:
            return "NOT_APPLICABLE"

    condition_result = _condition_requirement(
        rule,
        mine,
    )

    if condition_result is False:
        return "NOT_APPLICABLE"

    if condition_result is None:
        return "NEEDS_CONFIRMATION"

    return "APPLICABLE"


def rule_applies_to_mine(
    rule: Any,
    mine: Any,
) -> bool:
    """
    Backwards-compatible boolean applicability helper.

    Only fully confirmed APPLICABLE rules return True.
    Rules requiring additional profile information return False here;
    generate_mine_schedule() handles them separately as
    NEEDS_CONFIRMATION when appropriate.
    """

    return (
        evaluate_schedule_rule(rule, mine)
        == "APPLICABLE"
    )


def get_applicable_schedule_rules(
    mine: Any,
) -> list[Any]:
    """
    Return active rules that are confirmed applicable.

    Use get_schedule_rule_evaluations() when the caller also needs
    NEEDS_CONFIRMATION rules.
    """

    return [
        rule
        for rule in db.list_schedule_rules()
        if getattr(rule, "active", True)
        and evaluate_schedule_rule(rule, mine) == "APPLICABLE"
    ]


def get_schedule_rule_evaluations(
    mine: Any,
) -> list[tuple[Any, str]]:
    """
    Return all active rules together with their applicability state.
    """

    evaluations: list[tuple[Any, str]] = []

    for rule in db.list_schedule_rules():
        if not getattr(rule, "active", True):
            continue

        evaluations.append(
            (
                rule,
                evaluate_schedule_rule(rule, mine),
            )
        )

    return evaluations


# ============================================================
# DATE ARITHMETIC
# ============================================================

def _add_months(
    dt: datetime,
    months: int,
) -> datetime:
    dt = _ensure_utc(dt)

    month_index = dt.month - 1 + months
    year = dt.year + month_index // 12
    month = month_index % 12 + 1

    day = min(
        dt.day,
        calendar.monthrange(year, month)[1],
    )

    return dt.replace(
        year=year,
        month=month,
        day=day,
    )


def _calendar_year_end(
    reference_time: datetime,
) -> datetime:
    reference_time = _ensure_utc(reference_time)

    candidate = datetime(
        reference_time.year,
        12,
        31,
        23,
        59,
        59,
        999999,
        tzinfo=timezone.utc,
    )

    if candidate > reference_time:
        return candidate

    return datetime(
        reference_time.year + 1,
        12,
        31,
        23,
        59,
        59,
        999999,
        tzinfo=timezone.utc,
    )


def _calendar_month_end(
    reference_time: datetime,
) -> datetime:
    reference_time = _ensure_utc(reference_time)

    last_day = calendar.monthrange(
        reference_time.year,
        reference_time.month,
    )[1]

    candidate = datetime(
        reference_time.year,
        reference_time.month,
        last_day,
        23,
        59,
        59,
        999999,
        tzinfo=timezone.utc,
    )

    if candidate > reference_time:
        return candidate

    next_month = _add_months(
        reference_time.replace(
            day=1,
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        ),
        1,
    )

    next_last_day = calendar.monthrange(
        next_month.year,
        next_month.month,
    )[1]

    return next_month.replace(
        day=next_last_day,
        hour=23,
        minute=59,
        second=59,
        microsecond=999999,
    )


# ============================================================
# NEXT-DUE CALCULATION
# ============================================================

def calculate_next_due(
    rule: Any,
    last_completed_at: Optional[datetime] = None,
    reference_time: Optional[datetime] = None,
) -> Optional[datetime]:

    now = _ensure_utc(
        reference_time or _utc_now()
    )

    frequency = _normalise(
        getattr(rule, "frequency_type", None)
    )

    # Continuous obligations have no conventional deadline.
    if frequency == "continuous":
        return now

    # Event-triggered obligations receive their next date from
    # the event rather than a calendar interval.
    if frequency == "event":
        return None

    # Conditional rules require an external condition.
    if frequency == "conditional":
        return None

    if frequency == "calendar":
        trigger = _normalise(
            getattr(rule, "trigger_type", None)
        )

        if trigger in {
            "calendar_year_end",
            "year_end",
            "annual",
        }:
            return _calendar_year_end(now)

        if trigger in {
            "calendar_month_end",
            "month_end",
            "monthly",
        }:
            return _calendar_month_end(now)

        # A calendar rule with a numeric interval can be interpreted
        # from the beginning of the current calendar period.
        interval_value = getattr(
            rule,
            "interval_value",
            None,
        )

        interval_unit = _normalise(
            getattr(rule, "interval_unit", None)
        )

        if interval_value and interval_unit in {
            "year",
            "years",
        }:
            return _add_months(
                now.replace(
                    month=1,
                    day=1,
                    hour=0,
                    minute=0,
                    second=0,
                    microsecond=0,
                ),
                int(interval_value) * 12,
            )

        return None

    if frequency != "interval":
        return None

    interval_value = getattr(
        rule,
        "interval_value",
        None,
    )

    interval_unit = _normalise(
        getattr(rule, "interval_unit", None)
    )

    if interval_value is None or not interval_unit:
        return None

    try:
        interval_value = int(interval_value)
    except (TypeError, ValueError):
        return None

    if interval_value <= 0:
        return None

    base = (
        _parse_datetime(last_completed_at)
        if last_completed_at is not None
        else now
    )

    if base is None:
        base = now

    if interval_unit in {"hour", "hours"}:
        return base + timedelta(hours=interval_value)

    if interval_unit in {"day", "days"}:
        return base + timedelta(days=interval_value)

    if interval_unit in {"week", "weeks"}:
        return base + timedelta(weeks=interval_value)

    if interval_unit in {"month", "months"}:
        return _add_months(base, interval_value)

    if interval_unit in {"year", "years"}:
        return _add_months(
            base,
            interval_value * 12,
        )

    return None


# ============================================================
# STATUS
# ============================================================

def determine_schedule_status(
    next_due_at: Optional[datetime],
    now: Optional[datetime] = None,
    frequency_type: Optional[str] = None,
    applicability_status: Optional[str] = None,
) -> str:

    if applicability_status == "NEEDS_CONFIRMATION":
        return STATUS_NEEDS_CONDITION

    current = _ensure_utc(
        now or _utc_now()
    )

    frequency = _normalise(frequency_type)

    if frequency == "continuous":
        return STATUS_ONGOING

    if frequency == "event":
        return STATUS_EVENT_TRIGGERED

    if frequency == "conditional":
        return STATUS_NEEDS_CONDITION

    if next_due_at is None:
        return STATUS_UNSCHEDULED

    due = _parse_datetime(next_due_at)

    if due is None:
        return STATUS_UNSCHEDULED

    if due < current:
        return STATUS_OVERDUE

    if due == current:
        return STATUS_DUE

    if due <= current + timedelta(days=7):
        return STATUS_DUE_SOON

    return STATUS_UPCOMING


# ============================================================
# SCHEDULE INSTANCE ID
# ============================================================

def make_schedule_instance_id(
    mine_id: str,
    schedule_id: str,
) -> str:
    safe_mine = str(mine_id).strip().replace(" ", "-")
    safe_schedule = str(schedule_id).strip().replace(" ", "-")

    return (
        f"SCHINST-{safe_mine}-{safe_schedule}"
    )


# ============================================================
# EXISTING SCHEDULES
# ============================================================

def _get_existing_schedule_map(
    mine_id: str,
) -> dict[str, dict]:
    rows = db.get_schedules_for_mine(mine_id)

    return {
        str(row.get("schedule_id")): row
        for row in rows
        if row.get("schedule_id") is not None
    }


# ============================================================
# STALE SCHEDULE CLEANUP
# ============================================================

def _deactivate_stale_schedule_instances(
    mine_id: str,
    active_schedule_ids: set[str],
) -> None:
    """
    Deactivate obsolete schedule instances while retaining history.

    The helper was added to database.py during the scheduling work.
    The getattr fallback prevents an import/runtime failure if an older
    database.py is temporarily used.
    """

    cleanup = getattr(
        db,
        "deactivate_inactive_mine_schedules",
        None,
    )

    if cleanup is None:
        return

    cleanup(
        mine_id,
        active_schedule_ids,
    )


# ============================================================
# GENERATE MINE SCHEDULE
# ============================================================

def generate_mine_schedule(
    mine: Any,
    reference_time: Optional[datetime] = None,
) -> list[MineInspectionSchedule]:

    now = _ensure_utc(
        reference_time or _utc_now()
    )

    mine_id = getattr(mine, "mine_id", None)

    if not mine_id:
        raise ValueError(
            "Mine object must contain a valid mine_id."
        )

    evaluations = get_schedule_rule_evaluations(
        mine
    )

    active_rule_ids = {
        str(getattr(rule, "schedule_id", ""))
        for rule, state in evaluations
        if getattr(rule, "active", True)
        and state != "NOT_APPLICABLE"
        and getattr(rule, "schedule_id", None)
    }

    _deactivate_stale_schedule_instances(
        mine_id,
        active_rule_ids,
    )

    existing = _get_existing_schedule_map(
        mine_id
    )

    schedules: list[MineInspectionSchedule] = []

    for rule, applicability_status in evaluations:

        if applicability_status == "NOT_APPLICABLE":
            continue

        schedule_id = str(
            getattr(rule, "schedule_id", "")
        ).strip()

        if not schedule_id:
            continue

        previous = existing.get(
            schedule_id,
            {},
        )

        last_completed_at = _parse_datetime(
            previous.get("last_completed_at")
        )

        frequency = _normalise(
            getattr(rule, "frequency_type", None)
        )

        next_due_at = calculate_next_due(
            rule=rule,
            last_completed_at=last_completed_at,
            reference_time=now,
        )

        status = determine_schedule_status(
            next_due_at=next_due_at,
            now=now,
            frequency_type=frequency,
            applicability_status=applicability_status,
        )

        schedule = MineInspectionSchedule(
            schedule_instance_id=make_schedule_instance_id(
                mine_id,
                schedule_id,
            ),
            mine_id=mine_id,
            schedule_id=schedule_id,
            last_completed_at=last_completed_at,
            next_due_at=next_due_at,
            status=status,
            generated_at=now,
            active=True,
        )

        db.save_mine_inspection_schedule(
            schedule
        )

        schedules.append(schedule)

    return schedules


# ============================================================
# REFRESH
# ============================================================

def refresh_mine_schedule(
    mine_id: str,
    reference_time: Optional[datetime] = None,
) -> list[MineInspectionSchedule]:
    """
    Refresh the complete mine schedule.

    Old/inactive schedule instances remain in the database for history,
    but are deactivated. Current applicable and needs-confirmation rules
    are regenerated.
    """

    mine = db.get_mine(mine_id)

    if mine is None:
        raise ValueError(
            f"Mine '{mine_id}' does not exist."
        )

    return generate_mine_schedule(
        mine=mine,
        reference_time=reference_time,
    )


# ============================================================
# COMPLETE A SCHEDULE
# ============================================================

def mark_schedule_completed(
    mine_id: str,
    schedule_id: str,
    completed_at: Optional[datetime] = None,
) -> MineInspectionSchedule:

    mine = db.get_mine(mine_id)

    if mine is None:
        raise ValueError(
            f"Mine '{mine_id}' does not exist."
        )

    rule = next(
        (
            candidate
            for candidate in db.list_schedule_rules()
            if str(
                getattr(
                    candidate,
                    "schedule_id",
                    "",
                )
            ) == str(schedule_id)
        ),
        None,
    )

    if rule is None:
        raise ValueError(
            f"Schedule rule '{schedule_id}' does not exist."
        )

    applicability = evaluate_schedule_rule(
        rule,
        mine,
    )

    if applicability == "NOT_APPLICABLE":
        raise ValueError(
            f"Schedule rule '{schedule_id}' is not applicable "
            f"to mine '{mine_id}'."
        )

    completed_time = _ensure_utc(
        completed_at or _utc_now()
    )

    next_due_at = calculate_next_due(
        rule=rule,
        last_completed_at=completed_time,
        reference_time=completed_time,
    )

    status = determine_schedule_status(
        next_due_at=next_due_at,
        now=completed_time,
        frequency_type=getattr(
            rule,
            "frequency_type",
            None,
        ),
        applicability_status=applicability,
    )

    schedule = MineInspectionSchedule(
        schedule_instance_id=make_schedule_instance_id(
            mine_id,
            schedule_id,
        ),
        mine_id=mine_id,
        schedule_id=schedule_id,
        last_completed_at=completed_time,
        next_due_at=next_due_at,
        status=status,
        generated_at=completed_time,
        active=True,
    )

    db.save_mine_inspection_schedule(
        schedule
    )

    return schedule


# ============================================================
# READ CURRENT MINE SCHEDULE
# ============================================================

def get_mine_schedule(
    mine_id: str,
) -> list[dict]:
    return db.get_schedules_for_mine(
        mine_id
    )


def get_due_schedules(
    mine_id: str,
    reference_time: Optional[datetime] = None,
) -> list[dict]:

    now = _ensure_utc(
        reference_time or _utc_now()
    )

    schedules = db.get_schedules_for_mine(
        mine_id
    )

    due: list[dict] = []

    for schedule in schedules:
        status = str(
            schedule.get("status", "")
        )

        if status not in {
            STATUS_DUE,
            STATUS_OVERDUE,
        }:
            continue

        next_due = _parse_datetime(
            schedule.get("next_due_at")
        )

        if next_due is not None and next_due <= now:
            due.append(schedule)

    return due


# ============================================================
# TERMINAL DISPLAY
# ============================================================

def print_mine_schedule(
    mine_id: str,
) -> None:

    mine = db.get_mine(mine_id)

    if mine is None:
        print(
            f"Mine '{mine_id}' does not exist."
        )
        return

    refresh_mine_schedule(
        mine_id
    )

    schedules = get_mine_schedule(
        mine_id
    )

    print()
    print("=" * 70)
    print("PRITHVI — MINE INSPECTION SCHEDULE")
    print("=" * 70)

    print(
        f"Mine ID   : {mine.mine_id}"
    )
    print(
        f"Mine Name : {mine.name}"
    )
    print(
        f"Mine Type : {_mine_type(mine)}"
    )
    print(
        f"Gassy     : {_gassy_degree(mine)}"
    )

    print("-" * 70)

    if not schedules:
        print("No schedules generated.")
        print("=" * 70)
        return

    for schedule in schedules:
        schedule_name = schedule.get(
            "schedule_name"
        ) or schedule.get(
            "name"
        ) or schedule.get(
            "schedule_id"
        )

        print(
            f"Schedule : {schedule_name}"
        )
        print(
            f"Rule ID  : {schedule.get('schedule_id')}"
        )
        print(
            f"Frequency: {schedule.get('frequency_type')}"
        )
        print(
            f"Last Done: {schedule.get('last_completed_at')}"
        )
        print(
            f"Next Due : {schedule.get('next_due_at')}"
        )
        print(
            f"Status   : {schedule.get('status')}"
        )
        print("-" * 70)

    print("=" * 70)


# ============================================================
# MODULE CHECK
# ============================================================

if __name__ == "__main__":
    print(
        "PRITHVI scheduling module loaded successfully."
    )
