"""Schema-pinned lifecycle tables and predicates in `domain/curriculum/`."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from learning_os.domain.curriculum.lifecycle import (
    ADMINISTRATIVE_STATUSES,
    CLOSED_MODULE_STATUSES,
    LIVE_UNIT_STATUSES,
    MODULE_STATUS_TABLE,
    MODULE_STATUSES,
    RETIRED_MODULE_STATUSES,
    SETTLED_ADMINISTRATIVE,
    SETTLED_MODULE_STATUSES,
    STUDIED_MODULE_STATUSES,
    UNIT_STATUS_TABLE,
    UNIT_STATUSES,
    UNIT_STATUSES_WITHOUT_OBLIGATION,
    WORKSPACE_STATUS_TABLE,
    WORKSPACE_STATUSES,
    administrative_status,
    is_retired,
    is_settled,
    module_lifecycle,
    workspace_is_open,
)
from learning_os.domain.curriculum.stages import (
    _STUDY_CLOSED_STAGES,
    _STUDY_OPEN_STATUSES,
    STAGE_STATUS_TABLE,
    STAGE_STATUSES,
    STUDY_MAP_STATUS_TABLE,
    STUDY_MAP_STATUSES,
    entry_resource,
    stage_is_open,
)

SCHEMA_DIR = Path(__file__).resolve().parent.parent / "system" / "schema"


def _load_schema(name: str) -> dict:
    return json.loads((SCHEMA_DIR / name).read_text(encoding="utf-8"))


def test_module_status_table_matches_schema_enum() -> None:
    schema = _load_schema("module.schema.json")
    enum = schema["properties"]["status"]["enum"]
    assert list(MODULE_STATUS_TABLE) == enum
    assert MODULE_STATUSES == tuple(enum)
    assert ADMINISTRATIVE_STATUSES == {
        "planned", "enrolled", "awaiting-grade", "completed", "dropped", "archived",
    }
    assert STUDIED_MODULE_STATUSES == {"enrolled", "active"}
    assert SETTLED_MODULE_STATUSES == {
        "awaiting-grade", "completed", "dropped", "archived",
    }
    assert SETTLED_ADMINISTRATIVE == SETTLED_MODULE_STATUSES
    assert CLOSED_MODULE_STATUSES == SETTLED_MODULE_STATUSES
    assert RETIRED_MODULE_STATUSES == {"dropped", "archived"}


def test_unit_status_table_matches_schema_enum() -> None:
    schema = _load_schema("unit.schema.json")
    enum = schema["properties"]["status"]["enum"]
    assert set(UNIT_STATUS_TABLE) == set(enum)
    assert UNIT_STATUSES == set(enum)
    assert LIVE_UNIT_STATUSES == {"needs-map", "not-started", "ready", "active"}
    assert UNIT_STATUSES_WITHOUT_OBLIGATION == {"paused", "ready-to-shelve", "complete"}
    assert LIVE_UNIT_STATUSES | UNIT_STATUSES_WITHOUT_OBLIGATION == UNIT_STATUSES
    assert not (LIVE_UNIT_STATUSES & UNIT_STATUSES_WITHOUT_OBLIGATION)


def test_workspace_status_table_matches_schema_enum() -> None:
    schema = _load_schema("workspace.schema.json")
    enum = schema["properties"]["status"]["enum"]
    assert set(WORKSPACE_STATUS_TABLE) == set(enum)
    assert WORKSPACE_STATUSES == set(enum)


def test_study_map_and_stage_tables_match_schema_enums() -> None:
    study_map_schema = _load_schema("study-map.schema.json")
    map_enum = study_map_schema["properties"]["status"]["enum"]
    assert set(STUDY_MAP_STATUS_TABLE) == set(map_enum)
    assert STUDY_MAP_STATUSES == set(map_enum)
    assert _STUDY_OPEN_STATUSES == {"active", "paused", "ready"}

    legacy_stage_enum = study_map_schema["$defs"]["legacyStage"]["properties"]["status"]["enum"]
    plan_schema = _load_schema("learning-plan.schema.json")
    core_stage_enum = plan_schema["$defs"]["stageCore"]["properties"]["status"]["enum"]
    assert set(legacy_stage_enum) == set(core_stage_enum)
    assert set(STAGE_STATUS_TABLE) == set(legacy_stage_enum)
    assert STAGE_STATUSES == set(legacy_stage_enum)
    assert _STUDY_CLOSED_STAGES == {"complete", "skipped"}
    assert "archived" not in STAGE_STATUS_TABLE


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        ("pending", True),
        ("active", True),
        ("paused", True),
        ("complete", False),
        ("skipped", False),
        ("archived", False),
        (None, False),
    ],
)
def test_stage_is_open(status: str | None, expected: bool) -> None:
    stage = {"status": status} if status is not None else {}
    assert stage_is_open(stage) is expected


def test_entry_resource_prefers_required_now_then_untriaged() -> None:
    untriaged = {"label": "Untriaged", "kind": "read"}
    helpful = {"label": "Helpful", "kind": "read", "scope_triage": "helpful-now"}
    req_url = {"label": "Explainer", "kind": "read", "scope_triage": "required-now", "url": "https://example.org"}
    req_loc = {"label": "Book", "kind": "read", "scope_triage": "required-now", "locator": "p. 1"}

    assert entry_resource({"resources": [untriaged, req_url, req_loc]}) is req_url
    assert entry_resource({"resources": [helpful, untriaged]}) is untriaged
    assert entry_resource({"resources": [helpful]}) is None
    assert entry_resource({"resources": []}) is None
    assert entry_resource({}) is None


@pytest.mark.parametrize("kind", ["academic", "skill", "project", "foundation"])
@pytest.mark.parametrize("status", MODULE_STATUSES)
def test_module_predicates_across_all_kinds_and_statuses(kind: str, status: str) -> None:
    module = {"id": "module-test", "kind": kind, "status": status}
    expected_settled = status in {"awaiting-grade", "completed", "dropped", "archived"}
    expected_retired = status in {"dropped", "archived"}

    assert is_settled(module) is expected_settled
    assert is_retired(module) is expected_retired

    if kind != "academic":
        assert administrative_status(module) is None
    elif status in ADMINISTRATIVE_STATUSES:
        assert administrative_status(module) == status
    else:
        assert administrative_status(module) == "enrolled"

    lifecycle = module_lifecycle(module, ["ready"])
    assert lifecycle["administrative_status"] == administrative_status(module)
    assert lifecycle["is_settled"] is expected_settled
    assert lifecycle["is_retired"] is expected_retired
    assert lifecycle["operational_state"] == "active"
    assert lifecycle["is_actionable"] is (not expected_settled and status != "paused")


def test_administrative_status_defaults_missing_kind_to_academic() -> None:
    assert administrative_status({"status": "completed"}) == "completed"
    assert administrative_status({"status": "active"}) == "enrolled"
    assert administrative_status({"kind": "skill", "status": "completed"}) is None
    assert administrative_status({"kind": "project", "status": "planned"}) is None
    assert administrative_status({"kind": "foundation", "status": "dropped"}) is None


@pytest.mark.parametrize(
    ("archived", "status", "expected"),
    [
        (False, "active", True),
        (False, "blocked", True),
        (False, "complete", False),
        (True, "active", False),
        (True, "blocked", False),
        (True, "complete", False),
    ],
)
def test_workspace_is_open_matches_table(
    archived: bool, status: str, expected: bool
) -> None:
    assert workspace_is_open(archived, status) is expected
