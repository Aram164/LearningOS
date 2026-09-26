"""Finding 2: the highest-value dossier is per-session, not per-route.

`los resume` compiles the five-field bookmark into the screen a returning
operator actually needs: stage, requirement, evidence spec against what
was recorded, open items, last result, and the exam sitting. The pure
builder keeps content-addressed keys; the command resolves and renders.
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


def _cluster(**overrides):
    row = {
        "cluster_id": "covering-routes-stale:cluster:abc12345",
        "detector": "covering-routes-stale",
        "title": "3 routes cover moved nodes in unit:unit-demo-l01",
        "tier": 2,
        "nearest_sitting": "2026-10-09",
        "member_count": 3,
    }
    row.update(overrides)
    return row


def test_top_cluster_section_is_bounded_to_one_row():
    dossier = build_resume_dossier(**_inputs(top_cluster=_cluster()))
    content = dict(dossier.content)
    assert content["top-cluster"]["cluster_id"] == "covering-routes-stale:cluster:abc12345"
    assert content["top-cluster"]["member_count"] == 3
    assert "member_ids" not in content["top-cluster"]
    assert "days_until" not in content["top-cluster"]


def test_top_cluster_moves_the_digest():
    first = build_resume_dossier(**_inputs(top_cluster=_cluster()))
    changed = build_resume_dossier(**_inputs(top_cluster=_cluster(member_count=4)))
    assert changed.key != first.key
    missing = build_resume_dossier(**_inputs(top_cluster=None))
    assert missing.key != first.key
    assert build_resume_dossier(**_inputs(top_cluster=None)) == missing


def test_builder_refuses_a_non_mapping_top_cluster():
    with pytest.raises(ResumeDossierError):
        build_resume_dossier(**_inputs(top_cluster="cluster-abc"))


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
    assert not list((mini_repo / "generated/dossiers").glob("*-resume-*.json"))


def test_resume_shows_dated_recorded_aim_and_owning_workspace(mini_repo: Path):
    root = _runtime_repo(mini_repo)
    coordination = root / "work/COORDINATION.md"
    coordination.parent.mkdir(parents=True, exist_ok=True)
    coordination.write_text("---\nid: coordination\ntype: coordination\n---\n"
                            "# Coordination\n\n## Priorities\n\n"
                            "Decision 2026-08-14 by Aram. Keep two tracks in parallel.\n",
                            encoding="utf-8")
    workspace = root / "work/active/workspace-demo/CONTEXT.md"
    workspace.parent.mkdir(parents=True, exist_ok=True)
    workspace.write_text("---\nid: workspace-demo\ntype: workspace\n"
                         "title: Demo plan\ncreated: '2026-08-14'\nstatus: active\n"
                         "module_ids: [module-demo]\n---\n# Demo\n\n"
                         "## Objective\n\nStudy.\n\n## Current Scope\n\nDemo.\n\n"
                         "## Open Questions\n\nNone.\n\n## Next Action\n\n"
                         "Try one closed-book problem.\n", encoding="utf-8")
    proc = run_los(root, "resume")
    assert proc.returncode == 0, proc.stderr
    assert "Coordination decision 2026-08-14" in proc.stdout
    assert "work/COORDINATION.md#Priorities" in proc.stdout
    assert "Try one closed-book problem" in proc.stdout
    assert "workspace-demo/CONTEXT.md#Next-Action" in proc.stdout
    assert "compare with current dates and state" in proc.stdout


def test_resume_json_carries_the_top_cluster_section(mini_repo: Path):
    """The screen files nothing, but the top cluster rides along when the
    scan can run — and degrades to an explicit null when it cannot."""
    payload = json.loads(run_los(_runtime_repo(mini_repo), "resume", "--json").stdout)
    assert "top-cluster" in payload["content"]


def test_render_shows_one_top_goal_row_and_files_nothing():
    from learning_os.commands.resume import _render
    from learning_os.genout.resume_dossier import build_resume_dossier as build

    top = _cluster()
    dossier = build(**_inputs(top_cluster=top))
    text = _render(dossier, {"id": "req-x"}, [], [], [], {"module": "M", "unit": "U", "stage": "S"},
                   "via resume pointer", 0, top)
    assert "Top goal" in text
    assert top["title"] in text
    assert "seeing it files nothing" in text
    assert "los goal <id> --reject|--defer|--close" in text
    assert text.count("Top goal") == 1


def test_render_omits_the_section_without_a_cluster():
    from learning_os.commands.resume import _render
    from learning_os.genout.resume_dossier import build_resume_dossier as build

    dossier = build(**_inputs())
    text = _render(dossier, None, [], [], [], {"module": "M", "unit": "U", "stage": "S"},
                   "via resume pointer", 0, None)
    assert "Top goal" not in text


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


def test_recovery_follows_the_newest_touch_even_with_no_requirement(
        mini_repo: Path, monkeypatch):
    """Recovery reports where he was, not where the feature demos best.

    This used to skip past the most recently touched map to find one whose
    stage carried an authored runtime requirement, so the screen would not
    open on "none authored". With one authored requirement in the whole
    repository, that preference and "always return to that one stage" were
    the same rule, and it outranked the subject he had actually chosen
    (audit `synthetic-learner-2026-09-12`, F05). A truthful "none authored"
    for the right stage beats a complete screen for the wrong one.
    """
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
    assert via == "recently touched stage (resume pointer missing or stale)"
    assert (unit_id, stage_id) == ("unit-demo-l01", "stage-demo")
    # And the other way round, so this pins the ordering rather than a
    # constant: make the requirement-bearing map the newer one and it wins.
    monkeypatch.setattr(_git, "last_commit_timestamps",
                        lambda _root: {old_map: "100", new_map: "200"})
    _, _, unit_id, _, stage_id = _resolve_stage(load_repo(root))
    assert (unit_id, stage_id) == ("unit-demo-l02", "stage-demo2")


def test_stage_note_section_moves_the_digest_and_refuses_non_mappings():
    base = build_resume_dossier(**_inputs())
    assert dict(base.content)["stage-note"] is None
    note = {"working_note": "curriculum/modules/module-demo/units/unit-demo-l01/stages/stage-demo/notes.md",
            "lines": 3, "updated": "2026-09-25", "excerpt": "worked example done\n"}
    changed = build_resume_dossier(**_inputs(stage_note=note))
    assert changed.key != base.key
    assert dict(changed.content)["stage-note"] == note
    again = build_resume_dossier(**_inputs(stage_note=dict(note)))
    assert again == changed
    with pytest.raises(ResumeDossierError):
        build_resume_dossier(**_inputs(stage_note=["not-a-mapping"]))


def test_resume_shows_recorded_stage_note_without_a_requirement(mini_repo: Path):
    add_curriculum(mini_repo)
    note_rel = "curriculum/modules/module-demo/units/unit-demo-l01/stages/stage-demo/notes.md"
    empty = run_los(mini_repo, "resume")
    assert empty.returncode == 0, empty.stderr
    assert "Stage note   nothing recorded yet" in empty.stdout
    (mini_repo / note_rel).write_text(
        "Derived E[X] for a Bernoulli.\nWorked example done zephyr-note.\n",
        encoding="utf-8")
    text = run_los(mini_repo, "resume")
    assert text.returncode == 0, text.stderr
    assert "Stage note   2 lines recorded" in text.stdout
    assert "zephyr-note" in text.stdout
    assert "los stage-note unit-demo-l01 stage-demo --text" in text.stdout
    payload = json.loads(run_los(mini_repo, "resume", "--json").stdout)
    section = payload["content"]["stage-note"]
    assert section["lines"] == 2
    assert section["working_note"] == note_rel
    assert "zephyr-note" in section["excerpt"]


def test_stage_progress_section_moves_the_digest_and_refuses_non_mappings():
    base = build_resume_dossier(**_inputs())
    assert dict(base.content)["stage-progress"] is None
    progress = {"updated": "2026-09-26", "summary": "Worked §1 zephyr-progress.",
                "next": "Re-derive closed-book."}
    changed = build_resume_dossier(**_inputs(stage_progress=progress))
    assert changed.key != base.key
    assert dict(changed.content)["stage-progress"] == progress
    again = build_resume_dossier(**_inputs(stage_progress=dict(progress)))
    assert again == changed
    with pytest.raises(ResumeDossierError):
        build_resume_dossier(**_inputs(stage_progress=["not-a-mapping"]))


def test_resume_shows_recorded_stage_progress(mini_repo: Path):
    add_curriculum(mini_repo)
    empty = run_los(mini_repo, "resume")
    assert empty.returncode == 0, empty.stderr
    assert "Progress" not in empty.stdout
    data = yaml.safe_load((mini_repo / MAP).read_text(encoding="utf-8"))
    data["stages"][0]["progress"] = {
        "updated": "2026-09-26", "summary": "Worked §1 zephyr-progress.",
        "next": "Re-derive closed-book."}
    write_yaml(mini_repo / MAP, data)
    text = run_los(mini_repo, "resume")
    assert text.returncode == 0, text.stderr
    assert "zephyr-progress" in text.stdout
    assert "next: Re-derive closed-book." in text.stdout
    payload = json.loads(run_los(mini_repo, "resume", "--json").stdout)
    assert payload["content"]["stage-progress"]["summary"].endswith("zephyr-progress.")
