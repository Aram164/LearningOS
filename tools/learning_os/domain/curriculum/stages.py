"""The stage state machine: one status action applied in place.

Pure rules over loaded records. Callers refuse invalid actions first; these
functions assume a valid action and receive the clock as a callable, so the
clock is read exactly where the rule needs a date.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Callable, Mapping
from dataclasses import dataclass

from learning_os.domain.curriculum.lifecycle import is_settled

STAGE_ACTIONS = ("active", "paused", "complete", "skipped", "revisit")


@dataclass(frozen=True, slots=True)
class StudyMapStatusRule:
    """Classification flags for one authored `study-map.status` value."""

    study_open: bool


@dataclass(frozen=True, slots=True)
class StageStatusRule:
    """Classification flags for one authored `stage.status` value."""

    open: bool


STUDY_MAP_STATUS_TABLE: dict[str, StudyMapStatusRule] = {
    "not-started": StudyMapStatusRule(study_open=False),
    "ready": StudyMapStatusRule(study_open=True),
    "active": StudyMapStatusRule(study_open=True),
    "paused": StudyMapStatusRule(study_open=True),
    "ready-to-shelve": StudyMapStatusRule(study_open=False),
    "complete": StudyMapStatusRule(study_open=False),
}

STAGE_STATUS_TABLE: dict[str, StageStatusRule] = {
    "pending": StageStatusRule(open=True),
    "active": StageStatusRule(open=True),
    "paused": StageStatusRule(open=True),
    "complete": StageStatusRule(open=False),
    "skipped": StageStatusRule(open=False),
}

STUDY_MAP_STATUSES: frozenset[str] = frozenset(STUDY_MAP_STATUS_TABLE)

#: Study-map statuses eligible as open study choices. Active maps are work in
#: progress, paused ones are shelved tracks worth resuming, ready ones are
#: prepared ground; anything else (not-started and beyond) is not a next step.
_STUDY_OPEN_STATUSES: frozenset[str] = frozenset(
    status for status, rule in STUDY_MAP_STATUS_TABLE.items() if rule.study_open
)

STAGE_STATUSES: frozenset[str] = frozenset(STAGE_STATUS_TABLE)

_STUDY_OPEN_STAGES: frozenset[str] = frozenset(
    status for status, rule in STAGE_STATUS_TABLE.items() if rule.open
)

#: Stage statuses that close a stage to fresh suggestions. Skipped joins
#: complete so this predicate agrees with the UI's isOpenStage: a skipped stage
#: is a decision already made, never a next step.
_STUDY_CLOSED_STAGES: frozenset[str] = frozenset(
    status for status, rule in STAGE_STATUS_TABLE.items() if not rule.open
)


def stage_is_open(stage: Mapping[str, object]) -> bool:
    """Whether a stage is still open to fresh study (pending, active, or paused)."""
    return stage.get("status") in _STUDY_OPEN_STAGES


def entry_resource(
    stage: Mapping[str, object],
    *,
    allow_untriaged: bool = True,
) -> dict[str, object] | None:
    """The primary entry resource of ``stage``.

    Selects the first ``required-now`` resource. When ``allow_untriaged`` is
    True (the manifest projection default for pre-v1 stages whose resources
    carry no ``scope_triage`` field), falls back to the first untriaged
    resource; the CLI ``resume`` open payload passes ``allow_untriaged=False``
    so it only opens an explicitly triaged ``required-now`` locator.
    """
    resources = stage.get("resources")
    if not isinstance(resources, list):
        return None
    for row in resources:
        if isinstance(row, dict) and row.get("scope_triage") == "required-now":
            return row
    if allow_untriaged:
        for row in resources:
            if isinstance(row, dict) and not row.get("scope_triage"):
                return row
    return None


def study_candidate_stage(repo, study_map):
    """(stage_id, stage) when this map is an eligible study choice, else None.

    The one implementation of study-candidate eligibility. A map is eligible
    when its status is active, paused, or ready; its module resolves and is not
    settled; its unit resolves, belongs to that same module, and does not point
    its ``current_study_map`` at a different map; and its current stage
    resolves and is open (pending, active, or paused). Module kind never enters
    the rule, and enrollment stays display metadata: only settled status closes
    the pool, so skill, foundation and project modules — which have no
    registrar — remain eligible. Status is eligibility only: it is never a rank
    or a recommendation, and the resume pointer overrides every fresh
    suggestion.
    """
    data = study_map.data or {}
    if data.get("status") not in _STUDY_OPEN_STATUSES:
        return None
    stage_id = data.get("current_stage")
    stage = next((row for row in data.get("stages", [])
                  if isinstance(row, dict) and row.get("id") == stage_id), None)
    module = repo.modules.get(study_map.module_id)
    unit = repo.units.get(study_map.unit_id)
    if not isinstance(stage_id, str) or stage is None \
            or module is None or unit is None:
        return None
    unit_module_id = getattr(unit, "module_id", None)
    if unit_module_id != study_map.module_id:
        return None
    unit_data = getattr(unit, "data", None)
    if isinstance(unit_data, Mapping):
        authored_unit_module = unit_data.get("module_id")
        if isinstance(authored_unit_module, str) and authored_unit_module != study_map.module_id:
            return None
        unit_map_id = unit_data.get("current_study_map")
    else:
        unit_map_id = None
    authored_map_unit = data.get("unit_id")
    if isinstance(authored_map_unit, str) and authored_map_unit != study_map.unit_id:
        return None
    authored_map_module = data.get("module_id")
    if isinstance(authored_map_module, str) and authored_map_module != study_map.module_id:
        return None
    map_id = getattr(study_map, "id", None) or data.get("id")
    if isinstance(unit_map_id, str) and isinstance(map_id, str) and unit_map_id != map_id:
        return None
    if is_settled(module):
        return None
    if not stage_is_open(stage):
        return None
    return stage_id, stage


def is_study_candidate(repo, study_map) -> bool:
    """Whether this map is an eligible study choice, never a priority."""
    return study_candidate_stage(repo, study_map) is not None


def activate_stage(data: dict, unit_data: dict, stage: dict) -> None:
    """Activate ``stage`` inside ``data``, clearing any prior active/paused stage."""
    for other in data.get("stages", []) or []:
        if other.get("status") in {"active", "paused"}:
            other["status"] = "pending"
    stage["status"] = "active"
    stage.pop("completed", None)
    data["current_stage"] = stage["id"]
    data["status"] = "active"
    unit_data["status"] = "active"


def pause_stage(data: dict, unit_data: dict, stage: dict) -> None:
    """Pause ``stage`` inside ``data`` and point the map cursor at it."""
    stage["status"] = "paused"
    data["current_stage"] = stage["id"]
    data["status"] = "paused"
    unit_data["status"] = "paused"


def apply_stage_action(data: dict, unit_data: dict, stage: dict, action: str,
                       today: Callable[[], dt.date]) -> None:
    """Move ``stage`` (one of ``data["stages"]``) by ``action``; update map and unit status."""
    if action in {"active", "revisit"}:
        activate_stage(data, unit_data, stage)
    elif action == "paused":
        pause_stage(data, unit_data, stage)
    else:
        stages = data.get("stages", []) or []
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
