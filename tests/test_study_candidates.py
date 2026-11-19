"""Study-candidate eligibility has one implementation and one published fact.

``domain/curriculum/stages.py::study_candidate_stage`` owns the rule; the
resume builder consumes it for its rows and the manifest projection publishes
its verdict as ``study_maps[].is_study_candidate``. These tests pin the rule
against the lifecycle table, then require the projection and the resume screen
to agree with it, so a consumer never has to re-derive eligibility.
"""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml
from repo_builders import add_curriculum, run_los, write_yaml

from learning_os.derive.projection.manifest import build_manifest
from learning_os.domain.curriculum.stages import (
    entry_resource,
    is_study_candidate,
    study_candidate_stage,
)
from learning_os.store.loader import load_repo

MAP = "curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml"
UNIT = "curriculum/modules/module-demo/units/unit-demo-l01/unit.yaml"
MODULE = "curriculum/modules/module-demo/module.yaml"


def _manifest(root: Path) -> dict:
    return build_manifest(load_repo(root), generated_at="T1")


def _flags(root: Path) -> dict[str, bool]:
    return {row["id"]: row["is_study_candidate"]
            for row in _manifest(root)["study_maps"]}


def _write_map(root: Path, **fields) -> None:
    data = yaml.safe_load((root / MAP).read_text(encoding="utf-8"))
    data.update(fields)
    write_yaml(root / MAP, data)


def _add_mapless_unit(root: Path, unit_id: str = "unit-demo-l02",
                      order: int = 2) -> None:
    """A lecture unit with no study map beside it."""
    unit_dir = root / f"curriculum/modules/module-demo/units/{unit_id}"
    unit_dir.mkdir(parents=True)
    write_yaml(unit_dir / "unit.yaml", {
        "id": unit_id, "type": "unit", "module_id": "module-demo",
        "kind": "lecture", "title": f"Lecture {order}", "order": order,
        "scope": "The lecture as taught.", "status": "active",
        "artifacts": {}, "workspace_ids": ["workspace-demo"],
    })
    module = yaml.safe_load((root / MODULE).read_text(encoding="utf-8"))
    module["unit_order"].append(unit_id)
    write_yaml(root / MODULE, module)


def _fake_map(*, map_status="active", stage_status="active",
              current_stage="stage-demo", unit_id="unit-demo-l01",
              module_id="module-demo", stages=None) -> SimpleNamespace:
    if stages is None:
        stages = [{"id": "stage-demo", "status": stage_status}]
    return SimpleNamespace(unit_id=unit_id, module_id=module_id, data={
        "status": map_status,
        "current_stage": current_stage,
        "stages": stages,
    })


def _fake_repo(*unit_ids: str, module_status="enrolled",
               module_kind="academic") -> SimpleNamespace:
    return SimpleNamespace(
        units={
            unit_id: SimpleNamespace(
                id=unit_id,
                module_id="module-demo",
                data={"current_study_map": "study-map-demo-l01"},
            )
            for unit_id in unit_ids
        },
        modules={"module-demo": {
            "id": "module-demo", "kind": module_kind, "status": module_status,
        }},
    )


@pytest.mark.parametrize(("map_status", "stage_status", "expected"), [
    ("active", "active", True),
    ("paused", "paused", True),
    ("ready", "pending", True),
    ("not-started", "active", False),
    ("ready-to-shelve", "active", False),
    ("complete", "active", False),
    ("active", "complete", False),
    ("active", "skipped", False),
    ("active", "archived", False),
])
def test_the_predicate_follows_the_published_lifecycle_table(
        map_status: str, stage_status: str, expected: bool) -> None:
    study_map = _fake_map(map_status=map_status, stage_status=stage_status)
    repo = _fake_repo("unit-demo-l01")
    assert is_study_candidate(repo, study_map) is expected
    assert (study_candidate_stage(repo, study_map) is not None) is expected


@pytest.mark.parametrize("stages,current_stage", [
    ([], "stage-demo"),
    ([{"id": "stage-other", "status": "active"}], "stage-demo"),
    ([{"id": "stage-demo", "status": "active"}], ["stage-demo"]),
    ([{"id": "stage-demo", "status": "active"}], None),
])
def test_an_unresolved_current_stage_is_not_a_candidate(
        stages: list[dict], current_stage) -> None:
    repo = _fake_repo("unit-demo-l01")
    study_map = _fake_map(stages=stages, current_stage=current_stage)
    assert is_study_candidate(repo, study_map) is False


def test_an_unresolved_unit_is_not_a_candidate() -> None:
    repo = _fake_repo("unit-demo-l01")
    study_map = _fake_map(unit_id="unit-demo-missing")
    assert is_study_candidate(repo, study_map) is False


def test_the_predicate_ignores_module_kind_but_settled_status_closes_the_pool(
        mini_repo: Path) -> None:
    """Kind is display metadata; a settled administrative status is eligibility.

    Settled means nothing is expected of the module any more. Enrollment stays
    display-only, so this is not the literal ``status == enrolled`` trap that
    would drop every skill, foundation and project module.
    """
    add_curriculum(mini_repo)
    for kind in ("academic", "skill", "foundation", "project"):
        module = yaml.safe_load((mini_repo / MODULE).read_text(encoding="utf-8"))
        module["kind"] = kind
        module["status"] = "enrolled"
        write_yaml(mini_repo / MODULE, module)
        assert _flags(mini_repo) == {"study-map-demo-l01": True}, kind
    module = yaml.safe_load((mini_repo / MODULE).read_text(encoding="utf-8"))
    module["kind"] = "academic"
    for status in ("planned", "enrolled", "active", "paused"):
        module["status"] = status
        write_yaml(mini_repo / MODULE, module)
        assert _flags(mini_repo) == {"study-map-demo-l01": True}, status
    for status in ("awaiting-grade", "completed", "dropped", "archived"):
        module["status"] = status
        write_yaml(mini_repo / MODULE, module)
        assert _flags(mini_repo) == {"study-map-demo-l01": False}, status


def test_a_skill_module_without_a_registrar_stays_eligible(
        mini_repo: Path) -> None:
    """The settled filter reads the administrative axis, not the module kind."""
    add_curriculum(mini_repo)
    module = yaml.safe_load((mini_repo / MODULE).read_text(encoding="utf-8"))
    module["kind"] = "skill"
    module["status"] = "active"
    write_yaml(mini_repo / MODULE, module)
    assert _flags(mini_repo) == {"study-map-demo-l01": True}


@pytest.mark.parametrize("status", [
    "awaiting-grade", "completed", "dropped", "archived",
])
def test_a_settled_module_is_not_published_and_resume_refuses(
        mini_repo: Path, status: str) -> None:
    add_curriculum(mini_repo)
    module = yaml.safe_load((mini_repo / MODULE).read_text(encoding="utf-8"))
    module["status"] = status
    write_yaml(mini_repo / MODULE, module)
    assert _flags(mini_repo) == {"study-map-demo-l01": False}
    refused = run_los(mini_repo, "resume", "--study", "--unit",
                      "unit-demo-l01", "--json")
    assert refused.returncode == 2
    assert "has no open study map" in refused.stderr


def test_projection_and_resume_screen_publish_the_same_verdict(
        mini_repo: Path) -> None:
    add_curriculum(mini_repo)
    assert _flags(mini_repo) == {"study-map-demo-l01": True}
    offered = run_los(mini_repo, "resume", "--study", "--unit",
                      "unit-demo-l01", "--json")
    assert offered.returncode == 0, offered.stderr
    assert json.loads(offered.stdout)["study_option"]["learner_choice"] is False

    _write_map(mini_repo, status="ready-to-shelve")
    assert _flags(mini_repo) == {"study-map-demo-l01": False}
    refused = run_los(mini_repo, "resume", "--study", "--unit",
                      "unit-demo-l01", "--json")
    assert refused.returncode == 2
    assert "has no open study map" in refused.stderr

    _write_map(mini_repo, status="active")
    data = yaml.safe_load((mini_repo / MAP).read_text(encoding="utf-8"))
    data["stages"][0]["status"] = "skipped"
    write_yaml(mini_repo / MAP, data)
    assert _flags(mini_repo) == {"study-map-demo-l01": False}
    refused = run_los(mini_repo, "resume", "--study", "--unit",
                      "unit-demo-l01", "--json")
    assert refused.returncode == 2


def test_a_unit_without_a_map_is_browsable_and_never_a_candidate(
        mini_repo: Path) -> None:
    add_curriculum(mini_repo)
    _add_mapless_unit(mini_repo)
    manifest = _manifest(mini_repo)
    units = {row["id"]: row for row in manifest["units"]}
    assert units["unit-demo-l02"]["needs_study_map"] is True
    assert "unit-demo-l02" not in {
        row["unit_id"] for row in manifest["study_maps"]}
    assert _flags(mini_repo) == {"study-map-demo-l01": True}
    refused = run_los(mini_repo, "resume", "--study", "--unit",
                      "unit-demo-l02", "--json")
    assert refused.returncode == 2
    assert "has no open study map" in refused.stderr


def test_inconsistent_or_unresolved_ownership_is_not_a_candidate(
        mini_repo: Path) -> None:
    """Eligibility rejects unknown modules and map/unit/module ownership mismatches."""
    repo = _fake_repo("unit-demo-l01")
    missing_module_map = _fake_map(module_id="module-missing")
    assert is_study_candidate(repo, missing_module_map) is False

    stale_map = SimpleNamespace(
        id="study-map-other",
        unit_id="unit-demo-l01",
        module_id="module-demo",
        data={
            "id": "study-map-other",
            "status": "active",
            "current_stage": "stage-demo",
            "stages": [{"id": "stage-demo", "status": "active"}],
        },
    )
    assert is_study_candidate(repo, stale_map) is False

    add_curriculum(mini_repo)
    unit = yaml.safe_load((mini_repo / UNIT).read_text(encoding="utf-8"))
    unit["module_id"] = "module-elsewhere"
    write_yaml(mini_repo / UNIT, unit)
    assert _flags(mini_repo) == {"study-map-demo-l01": False}
    refused = run_los(mini_repo, "resume", "--study", "--unit",
                      "unit-demo-l01", "--json")
    assert refused.returncode == 2
    assert "has no open study map" in refused.stderr


def test_entry_resource_distinguishes_untriaged_fallback_from_explicit_triage() -> None:
    stage = {
        "resources": [
            {"id": "res-1", "label": "Untriaged deck", "locator": "p. 1"},
            {"id": "res-2", "label": "Reference book", "scope_triage": "optional"},
        ],
    }
    assert entry_resource(stage) == stage["resources"][0]
    assert entry_resource(stage, allow_untriaged=False) is None

    triaged_stage = {
        "resources": [
            {"id": "res-1", "label": "Untriaged deck", "locator": "p. 1"},
            {"id": "res-2", "label": "Required notes", "locator": "§2", "scope_triage": "required-now"},
        ],
    }
    assert entry_resource(triaged_stage) == triaged_stage["resources"][1]
    assert entry_resource(triaged_stage, allow_untriaged=False) == triaged_stage["resources"][1]
