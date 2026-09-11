"""Finding 2: the highest-value dossier is per-session, not per-route.

`los resume` compiles the five-field bookmark into the screen a returning
operator actually needs: stage, requirement, evidence spec against what
was recorded, open items, last result, and the exam sitting. Pure builder
plus content-addressed cache (same hash-key discipline as the semantic
dossiers); the command itself only resolves and renders.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
import yaml
from repo_builders import _add_material_overview, add_curriculum, run_los, write_yaml

from learning_os.genout.resume_dossier import (
    ResumeDossierError,
    build_resume_dossier,
    load_resume_dossier,
    store_resume_dossier,
)

MAP = "curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml"

TARGET = {
    "concept": "concept-expected-value",
    "capability": {"kind": "explain", "operands": ["expectation"]},
    "conditions": ["unfamiliar-example"],
    "evidence_spec": ["explain-reason"],
}


def _inputs(**overrides):
    fields = {
        "unit_id": "unit-demo-l01",
        "module_id": "module-demo",
        "stage_id": "stage-demo",
        "study_map_id": "study-map-demo-l01",
        "via": "resume pointer",
        "requirement": {"id": "req-demo-l01-demo", "concept": "concept-expected-value"},
        "observations": [{"id": "observation-abc", "result": "partial"}],
        "open_items": ["an open edge"],
        "sittings": [{"label": "2. Termin", "start_date": "2026-10-09"}],
        "titles": {"module": "Demo", "unit": "L01", "stage": "Derive"},
    }
    fields.update(overrides)
    return fields


def test_builder_is_deterministic_and_content_addressed():
    first = build_resume_dossier(**_inputs())
    second = build_resume_dossier(**_inputs())
    assert first == second
    assert first.key.startswith("context://unit-demo-l01/resume-dossier@")
    assert len(first.key.rsplit("@", 1)[1]) == 16
    changed = build_resume_dossier(**_inputs(
        observations=[{"id": "observation-abc", "result": "correct"}]))
    assert changed.key != first.key
    assert changed.hashes != first.hashes


def test_builder_refuses_empty_ids():
    with pytest.raises(ResumeDossierError):
        build_resume_dossier(**_inputs(unit_id="  "))


def test_cache_round_trips_and_refuses_poison(tmp_path: Path):
    dossier = build_resume_dossier(**_inputs())
    path = store_resume_dossier(tmp_path, dossier)
    assert load_resume_dossier(path) == dossier
    raw = json.loads(path.read_text(encoding="utf-8"))
    raw["content"]["open-items"].append("forged hindsight")
    path.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(ResumeDossierError, match="hashes"):
        load_resume_dossier(path)


def _runtime_repo(mini_repo: Path) -> Path:
    add_curriculum(mini_repo)
    _add_material_overview(mini_repo)
    data = yaml.safe_load((mini_repo / MAP).read_text(encoding="utf-8"))
    stage = data["stages"][0]
    stage["concepts"] = ["concept-expected-value"]
    stage["runtime_target"] = copy.deepcopy(TARGET)
    write_yaml(mini_repo / MAP, data)
    return mini_repo


def test_resume_renders_the_pointer_stage(mini_repo: Path):
    proc = run_los(_runtime_repo(mini_repo), "resume", "--json")
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["via"] == "resume pointer"
    content = payload["content"]
    assert content["stage"] == {
        "module_id": "module-demo", "unit_id": "unit-demo-l01",
        "study_map_id": "study-map-demo-l01", "stage_id": "stage-demo"}
    assert content["requirement"]["id"] == "req-demo-l01-demo"
    assert content["observations"] == []
    assert content["sittings"][0]["start_date"] == "2026-10-09"
    text = run_los(mini_repo, "resume")
    assert text.returncode == 0, text.stderr
    assert "req-demo-l01-demo" in text.stdout
    assert "los observe req-demo-l01-demo" in text.stdout
    assert "2026-10-09" in text.stdout


def test_resume_shows_recorded_evidence(mini_repo: Path):
    root = _runtime_repo(mini_repo)
    assert run_los(root, "observe", "req-demo-l01-demo",
                   "--activity", "exercise", "--result", "partial").returncode == 0
    payload = json.loads(run_los(root, "resume", "--json").stdout)
    assert len(payload["content"]["observations"]) == 1
    assert payload["content"]["observations"][0]["result"] == "partial"
    text = run_los(root, "resume")
    assert "Last result  partial" in text.stdout


def test_resume_falls_back_to_the_last_result(mini_repo: Path):
    root = _runtime_repo(mini_repo)
    assert run_los(root, "observe", "req-demo-l01-demo",
                   "--activity", "exercise", "--result", "correct").returncode == 0
    (root / "curriculum/resume.yaml").unlink()
    proc = run_los(root, "resume", "--json")
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["via"].startswith("last recorded result")
    assert payload["content"]["stage"]["stage_id"] == "stage-demo"


def test_resume_refuses_without_anything_to_resume(mini_repo: Path):
    proc = run_los(mini_repo, "resume")
    assert proc.returncode == 2
    assert "no resumable stage" in proc.stderr


def test_resume_prefers_a_stage_with_a_requirement(mini_repo: Path, monkeypatch):
    """The fallback opens on work, not on "none authored": among touched
    study maps it prefers the newest stage carrying a requirement."""
    root = _runtime_repo(mini_repo)
    # l01 keeps its stage but loses its requirement: only l02 offers work.
    lapsed = yaml.safe_load((root / MAP).read_text(encoding="utf-8"))
    del lapsed["stages"][0]["runtime_target"]
    write_yaml(root / MAP, lapsed)
    second = root / "curriculum/modules/module-demo/units/unit-demo-l02"
    second.mkdir(parents=True)
    write_yaml(second / "unit.yaml", {
        "id": "unit-demo-l02", "type": "unit", "module_id": "module-demo",
        "kind": "lecture", "title": "Variance", "order": 2,
        "scope": "The lecture as taught.", "status": "active",
        "current_study_map": "study-map-demo-l02",
        "workspace_ids": ["workspace-demo"],
    })
    write_yaml(second / "study-map.yaml", {
        "id": "study-map-demo-l02", "type": "study-map", "unit_id": "unit-demo-l02",
        "status": "active", "current_stage": "stage-demo2",
        "source_plan": {"path": "work/active/workspace-demo/CONTEXT.md",
                        "provenance": "operator"},
        "detours": [], "shelving": {"state": "none"},
        "stages": [{
            "id": "stage-demo2", "title": "Derive variance", "status": "active",
            "objective": "Derive and explain variance.",
            "done_when": ["Explain the derivation."], "scope_triage": "required-now",
            "concepts": ["concept-expected-value"],
            "runtime_target": dict(TARGET),
            "resources": [], "attachments": [], "source_feedback": [],
        }],
    })
    (root / "curriculum/resume.yaml").unlink()
    old_map = ("curriculum/modules/module-demo/units/unit-demo-l01/"
               "study-map.yaml")
    new_map = ("curriculum/modules/module-demo/units/unit-demo-l02/"
               "study-map.yaml")
    import learning_os.githistory as _git
    from learning_os.commands.resume import _resolve_stage
    from learning_os.loader import load_repo

    # The requirement-less map was touched more recently.
    monkeypatch.setattr(_git, "last_commit_timestamps",
                        lambda _root: {old_map: "200", new_map: "100"})
    via, module_id, unit_id, study_map_id, stage_id = _resolve_stage(
        load_repo(root))
    assert via == "recently touched stage"
    assert (unit_id, stage_id) == ("unit-demo-l02", "stage-demo2")
