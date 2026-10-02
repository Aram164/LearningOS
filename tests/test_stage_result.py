"""Untargeted learner results: record without credit, show as context, never retro-credit.

`learner.stage-result.append` (``stage-result``) is the intake for the 448
stages that carry no ``runtime_target``: activity, enumerated result,
assistance, optional conditions and a note, in an append-only workspace
ledger with a ``--supersedes`` correction path. `resume` and
`plan-edit-context --stage-id` show the rows labelled "no credit"; when a
target is later authored the rows stay visible as context only.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
import yaml
from gateway_helpers import approved_v2_call
from repo_builders import add_curriculum, run_los, write_yaml

from learning_os.learning_runtime import (
    RuntimeInputError,
    collect_requirements,
    read_observations,
    read_stage_results,
    stage_results_for,
)
from learning_os.loader import load_repo, parse_frontmatter

MAP = "curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml"
UNIT = "unit-demo-l01"
STAGE = "stage-demo"
WORKSPACE = "workspace-demo"

TARGET = {
    "concept": "concept-expected-value",
    "capability": {"kind": "explain", "operands": ["expectation"]},
    "conditions": ["unfamiliar-example"],
    "evidence_spec": ["explain-reason"],
}


def _stage_result(mini_repo: Path, key: str, **overrides):
    payload = {
        "workspace": WORKSPACE,
        "unit": UNIT,
        "stage": STAGE,
        "activity": "exercise",
        "result": "partial",
    }
    payload.update(overrides)
    return approved_v2_call(
        mini_repo,
        capability="learner.stage-result.append",
        payload=payload,
        artifact_ids=[WORKSPACE],
        idempotency_key=key,
    )


def test_stage_result_appends_with_receipt_and_no_credit(mini_repo: Path):
    add_curriculum(mini_repo)
    proc = _stage_result(mini_repo, "stage-result-001",
                         assistance="a hint", note="solved L05 counting, partially")
    assert proc.returncode == 0, proc.stderr
    response = json.loads(proc.stdout)
    assert response["ok"] is True
    assert response["result"]["credit"] == "none"
    assert response["result"]["stage_result_id"].startswith("stage-result-")
    assert (mini_repo / response["receipt_path"]).is_file()
    ledger = mini_repo / "work/active/workspace-demo/stage-results.jsonl"
    rows = [json.loads(line) for line in ledger.read_text(encoding="utf-8").splitlines()
            if line.strip()]
    assert len(rows) == 1
    assert rows[0]["unit"] == UNIT and rows[0]["stage"] == STAGE
    assert rows[0]["activity"] == "exercise" and rows[0]["result"] == "partial"
    assert rows[0]["assistance"] == "a hint"
    assert rows[0]["note"] == "solved L05 counting, partially"
    # No observation was recorded anywhere: the evidence ledgers are untouched.
    assert not (mini_repo / "work/active/workspace-demo/observations.jsonl").exists()


def test_stage_result_appears_in_resume_labelled_no_credit(mini_repo: Path):
    add_curriculum(mini_repo)
    proc = _stage_result(mini_repo, "stage-result-002", activity="drills")
    assert proc.returncode == 0, proc.stderr
    text = run_los(mini_repo, "resume")
    assert text.returncode == 0, text.stderr
    assert "no credit" in text.stdout
    assert "1 untargeted result" in text.stdout
    assert "drills" in text.stdout
    payload = json.loads(run_los(mini_repo, "resume", "--json").stdout)
    section = payload["content"]["stage-results"]
    assert section["total"] == 1
    assert section["credit"] == "none"
    assert section["results"][0]["activity"] == "drills"


def test_stage_result_supersedes_correction(mini_repo: Path):
    add_curriculum(mini_repo)
    first = _stage_result(mini_repo, "stage-result-003")
    assert first.returncode == 0, first.stderr
    first_id = json.loads(first.stdout)["result"]["stage_result_id"]
    second = _stage_result(mini_repo, "stage-result-004",
                           result="correct", supersedes=first_id)
    assert second.returncode == 0, second.stderr
    repo = load_repo(mini_repo)
    live = stage_results_for(read_stage_results(repo), UNIT, STAGE)
    assert len(live) == 1
    assert live[0]["result"] == "correct"
    assert live[0]["supersedes"] == first_id
    payload = json.loads(run_los(mini_repo, "resume", "--json").stdout)
    assert payload["content"]["stage-results"]["total"] == 1


def test_stage_result_refuses_unknown_unit_stage_and_scope(mini_repo: Path):
    add_curriculum(mini_repo)
    proc = _stage_result(mini_repo, "stage-result-005", unit="unit-nope")
    assert proc.returncode == 2
    assert "unknown unit" in json.loads(proc.stdout)["error"]["message"]
    proc = _stage_result(mini_repo, "stage-result-006", stage="stage-nope")
    assert proc.returncode == 2
    assert "unknown stage stage-nope in unit unit-demo-l01" in json.loads(proc.stdout)["error"]["message"]
    # A workspace that declares neither the module nor the unit cannot own it.
    other = mini_repo / "work/active/workspace-other"
    other.mkdir(parents=True)
    other_context = other / "CONTEXT.md"
    text = (mini_repo / "work/active/workspace-demo/CONTEXT.md").read_text(encoding="utf-8")
    meta, body = parse_frontmatter(text, other_context)
    meta["id"] = "workspace-other"
    meta["title"] = "Other workspace"
    meta["module_ids"] = []
    meta["unit_ids"] = []
    other_context.write_text("---\n" + yaml.safe_dump(meta, sort_keys=False).rstrip()
                             + "\n---\n\n" + body.lstrip(), encoding="utf-8")
    payload = {"workspace": "workspace-other", "unit": UNIT, "stage": STAGE,
               "activity": "exercise", "result": "partial"}
    proc = approved_v2_call(mini_repo, capability="learner.stage-result.append",
                            payload=payload, artifact_ids=["workspace-other"],
                            idempotency_key="stage-result-007")
    assert proc.returncode == 2
    assert "outside the workspace's declared module/unit scope" in json.loads(proc.stdout)["error"]["message"]


def test_plan_edit_context_stage_shows_untargeted_results(mini_repo: Path):
    add_curriculum(mini_repo)
    proc = _stage_result(mini_repo, "stage-result-008",
                         result="incorrect", note="miscounted the cases")
    assert proc.returncode == 0, proc.stderr
    proc = run_los(mini_repo, "plan-edit-context", UNIT, "--stage-id", STAGE)
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["contract"] == "plan-edit-context-stage"
    section = payload["stage_results"]
    assert section["total"] == 1
    assert section["credit"] == "none"
    assert section["results"][0]["result"] == "incorrect"
    assert section["results"][0]["note"] == "miscounted the cases"


def test_stage_results_stay_context_only_after_a_target_is_authored(mini_repo: Path):
    """Authoring a target later never retro-credits earlier untargeted rows."""
    add_curriculum(mini_repo)
    proc = _stage_result(mini_repo, "stage-result-009")
    assert proc.returncode == 0, proc.stderr
    data = yaml.safe_load((mini_repo / MAP).read_text(encoding="utf-8"))
    stage = data["stages"][0]
    stage["concepts"] = ["concept-expected-value"]
    stage["runtime_target"] = copy.deepcopy(TARGET)
    write_yaml(mini_repo / MAP, data)
    repo = load_repo(mini_repo)
    requirements = collect_requirements(repo)
    assert [req["id"] for req in requirements] == ["req-demo-l01-demo"]
    # The untargeted row grants the new requirement no observation.
    assert read_observations(repo, requirements) == []
    assert len(stage_results_for(read_stage_results(repo), UNIT, STAGE)) == 1
    text = run_los(mini_repo, "resume")
    assert text.returncode == 0, text.stderr
    assert "concept-expected-value" in text.stdout
    assert "Evidence     none recorded yet" in text.stdout
    assert "no credit" in text.stdout


def test_observe_refuses_an_untargeted_stage_with_both_paths(mini_repo: Path):
    add_curriculum(mini_repo)
    proc = run_los(mini_repo, "observe", STAGE,
                   "--activity", "exercise", "--result", "partial")
    assert proc.returncode == 2
    assert "unknown requirement" not in proc.stderr
    assert f"stage {STAGE} (unit {UNIT}) has no requirement target" in proc.stderr
    assert "stage-result" in proc.stderr
    assert f"--unit {UNIT} --stage {STAGE}" in proc.stderr
    assert f"unit-plan-revise {UNIT}" in proc.stderr
    assert "runtime_target" in proc.stderr


def test_observe_refuses_a_mistyped_id_with_suggestions(mini_repo: Path):
    add_curriculum(mini_repo)
    proc = run_los(mini_repo, "observe", "stage-demoo",
                   "--activity", "exercise", "--result", "partial")
    assert proc.returncode == 2
    assert "unknown requirement: stage-demoo" in proc.stderr
    assert "did you mean" in proc.stderr
    assert STAGE in proc.stderr


def test_observe_names_the_requirement_for_a_targeted_stage(mini_repo: Path):
    add_curriculum(mini_repo)
    data = yaml.safe_load((mini_repo / MAP).read_text(encoding="utf-8"))
    stage = data["stages"][0]
    stage["concepts"] = ["concept-expected-value"]
    stage["runtime_target"] = copy.deepcopy(TARGET)
    write_yaml(mini_repo / MAP, data)
    proc = run_los(mini_repo, "observe", STAGE,
                   "--activity", "exercise", "--result", "partial")
    assert proc.returncode == 2
    assert "already has a requirement target" in proc.stderr
    assert "req-demo-l01-demo" in proc.stderr


def test_damaged_stage_result_ledger_is_refused(mini_repo: Path):
    add_curriculum(mini_repo)
    proc = _stage_result(mini_repo, "stage-result-010")
    assert proc.returncode == 0, proc.stderr
    ledger = mini_repo / "work/active/workspace-demo/stage-results.jsonl"
    with ledger.open("a", encoding="utf-8") as handle:
        handle.write("not json\n")
    with pytest.raises(RuntimeInputError, match="cannot read runtime stage results"):
        read_stage_results(load_repo(mini_repo))
