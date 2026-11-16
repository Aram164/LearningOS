"""The stage state machine: one status action applied in place.

Pure rules over loaded records. Callers refuse invalid actions first; these
functions assume a valid action and receive the clock as a callable, so the
clock is read exactly where the rule needs a date.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Callable

STAGE_ACTIONS = ("active", "paused", "complete", "skipped", "revisit")


def apply_stage_action(data: dict, unit_data: dict, stage: dict, action: str,
                       today: Callable[[], dt.date]) -> None:
    """Move ``stage`` (one of ``data["stages"]``) by ``action``; update map and unit status."""
    stages = data.get("stages", []) or []
    if action in {"active", "revisit"}:
        for other in stages:
            if other.get("status") in {"active", "paused"}:
                other["status"] = "pending"
        stage["status"] = "active"
        stage.pop("completed", None)
        data["current_stage"] = stage["id"]
        data["status"] = "active"
        unit_data["status"] = "active"
    elif action == "paused":
        stage["status"] = "paused"
        data["current_stage"] = stage["id"]
        data["status"] = "paused"
        unit_data["status"] = "paused"
    else:
        stage["status"] = action
        if action == "complete":
            stage["completed"] = today().isoformat()
        following = next((row for row in stages[stages.index(stage) + 1:]
                          if row.get("status") == "pending"), None)
        if following:
            following["status"] = "active"
            data["current_stage"] = following["id"]
            data["status"] = "active"
            unit_data["status"] = "active"
        else:
            data["status"] = "ready-to-shelve"
            data.setdefault("shelving", {})["state"] = "draft"
            unit_data["status"] = "ready-to-shelve"


def resolve_resume_target(repo):
    """The recorded resume pointer as one resolved target, or ``None``.

    Returns ``(unit, study_map, stage)`` — the existing ``Unit`` and
    ``StudyMap`` records and the authored stage row inside that map — only
    when every declared link agrees: the module is known, the unit belongs
    to it, the named map is the unit's current map and belongs to that
    unit and module, and the stage is a member of that map. Individually
    valid IDs that disagree on ownership resolve nowhere, so no consumer
    can resume into another module's or unit's stage. A recorded stage
    stays resumable whatever its status: completion or a skip is where
    the learner stopped, not a reason to disown the pointer.
    """
    pointer = repo.resume_pointer if isinstance(repo.resume_pointer, dict) else None
    if not pointer:
        return None
    # A malformed ID (a list, a number, …) is a schema error for the
    # validator to name; it must never reach a dict lookup here, where
    # an unhashable value would crash every reader of the pointer.
    module_id = pointer.get("module_id")
    unit_id = pointer.get("unit_id")
    study_map_id = pointer.get("study_map_id")
    stage_id = pointer.get("stage_id")
    if not all(isinstance(value, str)
               for value in (module_id, unit_id, study_map_id, stage_id)):
        return None
    if module_id not in repo.modules:
        return None
    unit = repo.units.get(unit_id)
    if unit is None or unit.module_id != module_id:
        return None
    if (unit.data or {}).get("current_study_map") != study_map_id:
        return None
    study_map = repo.study_maps.get(study_map_id)
    if study_map is None or study_map.unit_id != unit.id \
            or study_map.module_id != unit.module_id:
        return None
    stage = next((row for row in study_map.data.get("stages", []) or []
                  if isinstance(row, dict)
                  and row.get("id") == stage_id), None)
    if stage is None:
        return None
    return (unit, study_map, stage)


def progress_entry(summary: str, upcoming: str | None,
                   today: Callable[[], dt.date]) -> dict:
    """The progress record for a validated summary and optional next step."""
    entry = {"updated": today().isoformat(), "summary": summary.strip()}
    if upcoming is not None:
        entry["next"] = upcoming.strip()
    return entry
