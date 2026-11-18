"""The module, unit, and workspace lifecycles: one schema-pinned table each.

`module.status` mixes two state machines. `planned / enrolled / awaiting-grade
/ completed / dropped / archived` answer "what does the university think?";
`active / paused` answer "am I working on this?". `MODULE_STATUS_TABLE` owns the
classification of every module status value, `UNIT_STATUS_TABLE` owns every unit
status value, and `WORKSPACE_STATUS_TABLE` owns every workspace status value.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ModuleStatusRule:
    """Classification flags for one authored `module.status` value."""

    administrative: bool
    owes_planning: bool
    settled: bool
    retired: bool


@dataclass(frozen=True, slots=True)
class UnitStatusRule:
    """Classification flags for one authored `unit.status` value."""

    live: bool


@dataclass(frozen=True, slots=True)
class WorkspaceStatusRule:
    """Classification flags for one authored `workspace.status` value."""

    open_when_unarchived: bool


MODULE_STATUS_TABLE: dict[str, ModuleStatusRule] = {
    "planned": ModuleStatusRule(administrative=True, owes_planning=False, settled=False, retired=False),
    "enrolled": ModuleStatusRule(administrative=True, owes_planning=True, settled=False, retired=False),
    "active": ModuleStatusRule(administrative=False, owes_planning=True, settled=False, retired=False),
    "paused": ModuleStatusRule(administrative=False, owes_planning=False, settled=False, retired=False),
    "awaiting-grade": ModuleStatusRule(administrative=True, owes_planning=False, settled=True, retired=False),
    "completed": ModuleStatusRule(administrative=True, owes_planning=False, settled=True, retired=False),
    "dropped": ModuleStatusRule(administrative=True, owes_planning=False, settled=True, retired=True),
    "archived": ModuleStatusRule(administrative=True, owes_planning=False, settled=True, retired=True),
}

UNIT_STATUS_TABLE: dict[str, UnitStatusRule] = {
    "needs-map": UnitStatusRule(live=True),
    "not-started": UnitStatusRule(live=True),
    "ready": UnitStatusRule(live=True),
    "active": UnitStatusRule(live=True),
    "paused": UnitStatusRule(live=False),
    "ready-to-shelve": UnitStatusRule(live=False),
    "complete": UnitStatusRule(live=False),
}

WORKSPACE_STATUS_TABLE: dict[str, WorkspaceStatusRule] = {
    "active": WorkspaceStatusRule(open_when_unarchived=True),
    "blocked": WorkspaceStatusRule(open_when_unarchived=True),
    "complete": WorkspaceStatusRule(open_when_unarchived=False),
}

#: Ordered tuple preserving schema order for CLI help/error messages.
MODULE_STATUSES: tuple[str, ...] = tuple(MODULE_STATUS_TABLE)

ADMINISTRATIVE_STATUSES: frozenset[str] = frozenset(
    status for status, rule in MODULE_STATUS_TABLE.items() if rule.administrative
)

#: A module whose units are still being studied / owed planning.
STUDIED_MODULE_STATUSES: frozenset[str] = frozenset(
    status for status, rule in MODULE_STATUS_TABLE.items() if rule.owes_planning
)

#: Nothing is expected of the module anymore, whatever the units say.
SETTLED_MODULE_STATUSES: frozenset[str] = frozenset(
    status for status, rule in MODULE_STATUS_TABLE.items() if rule.settled
)
SETTLED_ADMINISTRATIVE: frozenset[str] = SETTLED_MODULE_STATUSES

#: History modules: dropped or archived.
RETIRED_MODULE_STATUSES: frozenset[str] = frozenset(
    status for status, rule in MODULE_STATUS_TABLE.items() if rule.retired
)

#: Module statuses excluded from ordinary open-module listings.
CLOSED_MODULE_STATUSES: frozenset[str] = SETTLED_MODULE_STATUSES

UNIT_STATUSES: frozenset[str] = frozenset(UNIT_STATUS_TABLE)

#: Unit states that mean there is something to pick up. `not-started` counts;
#: `ready-to-shelve` does not — it is a review decision, not a study session.
LIVE_UNIT_STATUSES: frozenset[str] = frozenset(
    status for status, rule in UNIT_STATUS_TABLE.items() if rule.live
)
UNIT_STATUSES_WITHOUT_OBLIGATION: frozenset[str] = frozenset(
    status for status, rule in UNIT_STATUS_TABLE.items() if not rule.live
)

WORKSPACE_STATUSES: frozenset[str] = frozenset(WORKSPACE_STATUS_TABLE)


def administrative_status(module: Mapping[str, object]) -> str | None:
    """The registrar's answer for a module, or None for a non-academic module."""
    if module.get("kind", "academic") != "academic":
        # Skill, foundation and project modules have no registrar.
        return None
    status = str(module.get("status", "") or "")
    if status in ADMINISTRATIVE_STATUSES:
        return status
    # `active`/`paused` on an academic module says nothing administrative,
    # but you cannot be working on one you are not enrolled in.
    return "enrolled"


def is_settled(module: Mapping[str, object]) -> bool:
    """Whether nothing further is expected of this module."""
    return str(module.get("status", "") or "") in SETTLED_MODULE_STATUSES


def is_retired(module: Mapping[str, object]) -> bool:
    """Whether this module is retired history (dropped or archived)."""
    return str(module.get("status", "") or "") in RETIRED_MODULE_STATUSES


def workspace_is_open(archived: object, status: object) -> bool:
    """Whether a workspace is open: unarchived and not complete."""
    if bool(archived):
        return False
    status_key = str(status or "")
    rule = WORKSPACE_STATUS_TABLE.get(status_key)
    if rule is not None:
        return rule.open_when_unarchived
    return status_key != "complete"


def module_lifecycle(
    module: Mapping[str, object],
    unit_statuses: Sequence[str],
) -> dict[str, object]:
    """Administrative state, operational state, and whether work is available.

    Operational state is derived from the units rather than read from
    `module.status`, because the units are where work actually lives — a module
    cannot be operationally active while every unit under it is paused, no
    matter what its own field says.
    """
    administrative = administrative_status(module)
    settled = is_settled(module)
    retired = is_retired(module)

    if not unit_statuses:
        operational = "none"
    elif all(s == "complete" for s in unit_statuses):
        operational = "complete"
    elif any(s in LIVE_UNIT_STATUSES for s in unit_statuses):
        operational = "active"
    else:
        operational = "paused"

    actionable = (
        operational == "active"
        and not settled
        and module.get("status") != "paused"
    )
    return {
        "administrative_status": administrative,
        "operational_state": operational,
        "is_actionable": actionable,
        "is_settled": settled,
        "is_retired": retired,
    }
