"""Runtime-annotation review accountability (§19.6, first slice).

A stage carrying runtime semantics (``runtime_target`` or resource
``affordance`` rows) must carry a ``runtime_review`` attestation, and any
later change to the reviewed payload must surface as a warning. The checks
prove attestation plus an unchanged payload — never pedagogical correctness.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
import yaml
from gateway_helpers import approved_v2_cli, approved_v2_envelope, file_sha256, run_v2_capability
from repo_builders import (
    _add_material_overview,
    _structural_fixture,
    add_curriculum,
    run_los,
    write_yaml,
)

from learning_os.derive.learning_runtime import bind_runtime_reviews, runtime_review_fingerprint
from learning_os.derive.validation import validate
from learning_os.store.loader import load_repo

MAP = "curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml"

TARGET = {
    "concept": "concept-expected-value",
    "capability": {"kind": "explain", "operands": ["expectation"]},
    "conditions": ["unfamiliar-example"],
    "evidence_spec": ["explain-reason"],
}


def _review_block(stage: dict) -> dict:
    """The attestation a careful reviewer would attach to this stage."""
    return {
        "reviewed_by": "Aram",
        "reviewed_on": "2026-09-10",
        "fingerprint": runtime_review_fingerprint(stage),
    }


@pytest.fixture
def review_root(mini_repo):
    add_curriculum(mini_repo)
    _add_material_overview(mini_repo)
    path = mini_repo / MAP
    data = yaml.safe_load(path.read_text())
    stage = data["stages"][0]
    stage["concepts"] = ["concept-expected-value"]
    stage["runtime_target"] = copy.deepcopy(TARGET)
    for resource, affordance in zip(stage["resources"], ["intervention", "evidence"], strict=False):
        resource.update({"affordance": affordance})
    write_yaml(path, data)
    return mini_repo


def _stage(root: Path) -> tuple[dict, Path]:
    path = root / MAP
    data = yaml.safe_load(path.read_text())
    return data, path


def _codes(root: Path, code: str) -> list:
    return [i for i in validate(load_repo(root)) if i.code == code]


def test_missing_review_warns(review_root):
    issues = _codes(review_root, "RUNTIME-REVIEW-MISSING")
    assert len(issues) == 1
    assert issues[0].severity == "W"
    assert issues[0].path == MAP
    assert "stage-demo" in issues[0].message


def test_valid_review_is_silent(review_root):
    data, path = _stage(review_root)
    data["stages"][0]["runtime_review"] = _review_block(data["stages"][0])
    write_yaml(path, data)
    assert _codes(review_root, "RUNTIME-REVIEW-MISSING") == []
    assert _codes(review_root, "RUNTIME-REVIEW-STALE") == []


@pytest.mark.parametrize("mutate", [
    pytest.param(lambda s: s["resources"][0].update(affordance="evidence"),
                 id="affordance-flip"),
    pytest.param(lambda s: s["runtime_target"]["evidence_spec"].append("show-steps"),
                 id="evidence-spec-grow"),
    pytest.param(lambda s: s["runtime_target"]["capability"]["operands"].append("variance"),
                 id="capability-operand-grow"),
    pytest.param(lambda s: s.update(id="stage-demo-renamed"),
                 id="stage-id-change"),
])
def test_semantic_change_becomes_stale(review_root, mutate):
    data, path = _stage(review_root)
    data["stages"][0]["runtime_review"] = _review_block(data["stages"][0])
    mutate(data["stages"][0])
    write_yaml(path, data)
    issues = _codes(review_root, "RUNTIME-REVIEW-STALE")
    assert len(issues) == 1
    assert issues[0].severity == "W"
    assert issues[0].path == MAP


@pytest.mark.parametrize("mutate", [
    pytest.param(lambda s: s.update(title="A retitled stage"),
                 id="title-retitle"),
    pytest.param(lambda s: s.update(objective="A reworded objective."),
                 id="objective-reword"),
    pytest.param(lambda s: s.update(estimate_minutes=45),
                 id="estimate-added"),
    pytest.param(lambda s: s["resources"][0].update(locator="Task 1, pp. 2-3"),
                 id="locator-clarified"),
])
def test_unrelated_change_stays_valid(review_root, mutate):
    data, path = _stage(review_root)
    data["stages"][0]["runtime_review"] = _review_block(data["stages"][0])
    mutate(data["stages"][0])
    write_yaml(path, data)
    assert _codes(review_root, "RUNTIME-REVIEW-STALE") == []
    assert _codes(review_root, "RUNTIME-REVIEW-MISSING") == []


def test_fingerprint_is_stable_across_key_order_and_yaml_round_trip(review_root):
    data, _ = _stage(review_root)
    stage = data["stages"][0]
    before = runtime_review_fingerprint(stage)
    reordered = {key: copy.deepcopy(stage[key]) for key in reversed(list(stage))}
    assert runtime_review_fingerprint(reordered) == before
    reloaded = yaml.safe_load(yaml.safe_dump(stage, sort_keys=False))
    assert runtime_review_fingerprint(reloaded) == before


# An imported map may declare a review without computing its fingerprint:
# the import binds it (agent-cost D3), and a fingerprint already written is
# never replaced, so a stale review stays visibly stale.
def test_bind_fills_an_absent_fingerprint_and_the_review_is_current(review_root):
    data, path = _stage(review_root)
    data["stages"][0]["runtime_review"] = {"reviewed_by": "Aram", "reviewed_on": "2026-10-23"}
    before = copy.deepcopy(data)
    bound = bind_runtime_reviews(data)
    assert data == before
    stage = bound["stages"][0]
    assert stage["runtime_review"]["fingerprint"] == runtime_review_fingerprint(stage)
    write_yaml(path, bound)
    assert _codes(review_root, "RUNTIME-REVIEW-MISSING") == []
    assert _codes(review_root, "RUNTIME-REVIEW-STALE") == []


def test_bind_keeps_a_written_fingerprint_even_when_stale(review_root):
    data, _ = _stage(review_root)
    stale = {"reviewed_by": "Aram", "reviewed_on": "2026-10-23",
             "fingerprint": "sha256:" + "0" * 64}
    data["stages"][0]["runtime_review"] = stale
    assert bind_runtime_reviews(data)["stages"][0]["runtime_review"] == stale


def test_unit_map_import_binds_a_declared_review(mini_repo, tmp_path):
    add_curriculum(mini_repo)
    module_path = mini_repo / "curriculum/modules/module-demo/module.yaml"
    module = yaml.safe_load(module_path.read_text(encoding="utf-8"))
    module["unit_order"].append("unit-demo-l02")
    write_yaml(module_path, module)
    write_yaml(module_path.parent / "units/unit-demo-l02/unit.yaml", {
        "id": "unit-demo-l02", "type": "unit", "module_id": "module-demo",
        "kind": "lecture", "title": "Variance", "order": 2, "scope": "Lecture 2.",
        "status": "needs-map", "scope_sources": [], "source_selections": [],
        "artifacts": {}, "workspace_ids": [],
    })
    note_rel = "curriculum/modules/module-demo/units/unit-demo-l02/stages/stage-variance/notes.md"
    incoming = tmp_path / "map.yaml"
    write_yaml(incoming, {
        "id": "study-map-demo-l02", "type": "study-map", "unit_id": "unit-demo-l02",
        "plan_template_version": 1,
        "status": "ready", "current_stage": "stage-variance",
        "source_plan": {"path": "proposal.json", "provenance": "ai-proposed"},
        "detours": [], "shelving": {"state": "none"},
        "stages": [{"id": "stage-variance", "number": 1,
                    "title": "Variance", "status": "pending",
                    "objective": "Derive variance.", "done_when": ["Derive it."],
                    "exam_critical": False, "concepts": [],
                    "scope_triage": "required-now", "resources": [],
                    "runtime_review": {"reviewed_by": "Aram", "reviewed_on": "2026-10-23"},
                    "working_note": note_rel, "attachments": [], "source_feedback": []}],
    })
    proc = approved_v2_cli(
        mini_repo, "unit-map-import", "unit-demo-l02", "--file", str(incoming),
        "--file-sha256", file_sha256(incoming),
        artifact_ids=["unit-demo-l02", "study-map-demo-l02"],
        idempotency_key="runtime-review-bind-import",
    )
    assert proc.returncode == 0, proc.stderr
    stored = load_repo(mini_repo).study_maps["study-map-demo-l02"].data["stages"][0]
    assert stored["runtime_review"]["fingerprint"] == runtime_review_fingerprint(stored)


def _reviewed_structural_stage(root: Path) -> tuple[Path, dict]:
    """A valid current map whose stage carries a review, plus a route to place."""
    path, data = _structural_fixture(root)
    stage = next(row for row in data["stages"] if row["id"] == "stage-demo")
    stage["concepts"] = ["concept-expected-value"]
    stage["runtime_target"] = copy.deepcopy(TARGET)
    stage["runtime_review"] = _review_block(stage)
    write_yaml(path, data)
    return path, stage


def _append_intent(tmp_path: Path, **extra) -> Path:
    draft = tmp_path / "intent.json"
    draft.write_text(json.dumps({"unit_id": "unit-demo-l01", "structural_edit": {
        "reason": "Add one reviewed reading.",
        "resource_append": {"stage_id": "stage-demo", **extra, "resource": {
            "id": "resource-new-appended", "kind": "read", "scope_triage": "helpful-now",
            "material_ref": {"route_id": "route-demo-book",
                             "inherit": ["label", "source_id", "locator", "angle", "angle_detail"]}}}}}))
    return draft


def _check(root: Path, draft: Path):
    return run_los(root, "unit-map-import", "unit-demo-l01", "--file", str(draft), "--replace", "--check")


def test_a_new_row_on_a_reviewed_stage_refuses_and_names_the_renewal(mini_repo, tmp_path):
    _reviewed_structural_stage(mini_repo)
    check = _check(mini_repo, _append_intent(tmp_path))
    assert check.returncode != 0
    assert "RUNTIME-REVIEW-STALE" in check.stderr
    assert "add runtime_review with reviewed_by and reviewed_on" in check.stderr


def test_a_compact_edit_renews_the_review_it_invalidated(mini_repo, tmp_path):
    path, before = _reviewed_structural_stage(mini_repo)
    draft = _append_intent(tmp_path, runtime_review={"reviewed_by": "Aram", "reviewed_on": "2026-10-30"})
    check = _check(mini_repo, draft)
    assert check.returncode == 0, check.stderr
    review = json.loads(check.stdout)
    change = review["diff"]["resource_changes"][0]
    assert [row["id"] for row in change["added"]] == ["resource-new-appended"]
    envelope = approved_v2_envelope(mini_repo, capability="unit.map.import", payload={
        "unit_id": "unit-demo-l01", "file": str(draft), "file_sha256": review["file_sha256"], "replace": True,
    }, artifact_ids=list(review["expected_revisions"]), idempotency_key="renew-review")
    envelope["expected_snapshot"] = review["snapshot_id"]
    envelope["expected_revisions"] = review["expected_revisions"]
    result = run_v2_capability(mini_repo, envelope)
    assert result.returncode == 0, result.stdout + result.stderr
    after = next(row for row in yaml.safe_load(path.read_text())["stages"] if row["id"] == "stage-demo")
    assert after["resources"][:len(before["resources"])] == before["resources"]
    assert after["runtime_review"]["reviewed_on"] == "2026-10-30"
    assert after["runtime_review"]["fingerprint"] == runtime_review_fingerprint(after)
    assert _codes(mini_repo, "RUNTIME-REVIEW-STALE") == []


@pytest.mark.parametrize("review", [
    {"reviewed_by": "Aram"},
    {"reviewed_by": " ", "reviewed_on": "2026-10-30"},
    {"reviewed_by": "Aram", "reviewed_on": "2026-10-30", "fingerprint": "sha256:0"},
    "Aram",
])
def test_a_malformed_renewal_refuses(mini_repo, tmp_path, review):
    _reviewed_structural_stage(mini_repo)
    check = _check(mini_repo, _append_intent(tmp_path, runtime_review=review))
    assert check.returncode != 0
    assert "reviewed_by and reviewed_on" in check.stderr


def test_a_stage_without_a_review_has_nothing_to_renew(mini_repo, tmp_path):
    _structural_fixture(mini_repo)
    check = _check(mini_repo, _append_intent(
        tmp_path, runtime_review={"reviewed_by": "Aram", "reviewed_on": "2026-10-30"}))
    assert check.returncode != 0
    assert "no runtime_review to renew" in check.stderr
