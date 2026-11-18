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

from learning_os.derive.projection.resume_dossier import (
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


def test_bare_study_suggests_the_single_open_map_without_any_exam(mini_repo: Path):
    """No exam gate anywhere: the fixture's only sitting dates are long
    past, which the old nearest-exam scoping refused with "no upcoming
    exam". Study itself is the offer now, and the pointer never moves."""
    root = _runtime_repo(mini_repo)
    study_map = yaml.safe_load((root / MAP).read_text(encoding="utf-8"))
    study_map["stages"][0]["resources"][0]["scope_triage"] = "required-now"
    write_yaml(root / MAP, study_map)
    pointer = (root / "curriculum/resume.yaml").read_bytes()

    proc = run_los(root, "resume", "--study", "--json")
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["via"] == "single open study map (suggestion)"
    assert payload["study_option"]["open"]["locator"] == "§1"
    assert payload["study_option"]["learner_choice"] is False
    assert (root / "curriculum/resume.yaml").read_bytes() == pointer
    text = run_los(root, "resume", "--study")
    assert text.returncode == 0, text.stderr
    assert "Study suggestion" in text.stdout
    assert "your resume pointer is unchanged" in text.stdout


def _add_unit(root: Path, unit_id: str, order: int, map_status: str,
              stage_status: str = "active") -> None:
    """A second lecture unit with its own study map in module-demo."""
    unit_dir = root / f"curriculum/modules/module-demo/units/{unit_id}"
    unit_dir.mkdir(parents=True)
    write_yaml(unit_dir / "unit.yaml", {
        "id": unit_id, "type": "unit", "module_id": "module-demo",
        "kind": "lecture", "title": f"Lecture {order}", "order": order,
        "scope": "The lecture as taught.", "status": "active",
        "current_study_map": f"study-map-{unit_id[5:]}",
        "workspace_ids": ["workspace-demo"],
    })
    stage_id = f"stage-{unit_id[5:]}"
    note_rel = (f"curriculum/modules/module-demo/units/{unit_id}/"
                f"stages/{stage_id}/notes.md")
    write_yaml(unit_dir / "study-map.yaml", {
        "id": f"study-map-{unit_id[5:]}", "type": "study-map",
        "unit_id": unit_id, "status": map_status, "current_stage": stage_id,
        "source_plan": {"path": "work/active/workspace-demo/CONTEXT.md",
                        "provenance": "operator"},
        "detours": [], "shelving": {"state": "none"},
        "stages": [{
            "id": stage_id, "title": f"Study {unit_id}", "status": stage_status,
            "objective": "Study the lecture.",
            "done_when": ["Explain the lecture."], "scope_triage": "required-now",
            "resources": [{
                "kind": "read", "label": "Demo Book §1",
                "source_id": "source-demo-book", "locator": "§1",
                "scope_triage": "required-now"}],
            "working_note": note_rel, "attachments": [], "source_feedback": [],
        }],
    })
    (root / note_rel).parent.mkdir(parents=True, exist_ok=True)
    (root / note_rel).write_text("", encoding="utf-8")
    module_path = root / "curriculum/modules/module-demo/module.yaml"
    module = yaml.safe_load(module_path.read_text(encoding="utf-8"))
    module["unit_order"].append(unit_id)
    write_yaml(module_path, module)


def test_a_single_paused_map_still_suggests(mini_repo: Path):
    """Paused maps are shelved tracks worth resuming: one open map of any
    status is a suggestion, never a menu and never a refusal."""
    root = _runtime_repo(mini_repo)
    study_map = yaml.safe_load((root / MAP).read_text(encoding="utf-8"))
    study_map["status"] = "paused"
    write_yaml(root / MAP, study_map)
    payload = json.loads(run_los(root, "resume", "--study", "--json").stdout)
    assert payload["via"] == "single open study map (suggestion)"
    assert payload["content"]["stage"]["stage_id"] == "stage-demo"


def test_two_open_maps_become_a_menu_with_rows_and_metadata(mini_repo: Path):
    """The menu is the machine-readable contract: pinned row fields, an
    exact total, a select_with, and a continuation naming commands that
    exist. A plain --study menu carries no recovery context."""
    root = _runtime_repo(mini_repo)
    study_map = yaml.safe_load((root / MAP).read_text(encoding="utf-8"))
    study_map["stages"][0]["resources"][0]["scope_triage"] = "required-now"
    write_yaml(root / MAP, study_map)
    _add_unit(root, "unit-demo-l02", 2, "active")
    proc = run_los(root, "resume", "--study", "--json")
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["contract"] == "resume-study-options"
    assert payload["select_with"] == "resume --study --unit UNIT_ID"
    assert "unit-list --compact" in payload["continuation"]
    assert "bootstrap --compact" in payload["continuation"]
    assert [row["unit_id"] for row in payload["options"]] == [
        "unit-demo-l01", "unit-demo-l02"]
    assert all(row["learner_choice"] is False for row in payload["options"])
    first = payload["options"][0]
    assert first["module_id"] == "module-demo"
    assert first["study_map_id"] == "study-map-demo-l01"
    assert first["current_stage"] == "stage-demo"
    assert first["stage_title"] == "Derive expected value"
    assert first["open"]["locator"] == "§1"
    assert first["map_status"] == "active"
    assert first["module_kind"] == "academic"
    assert first["administrative_status"] == "enrolled"
    assert payload["options"][1]["map_status"] == "active"
    assert payload["total"] == 2
    assert "recovery" not in payload
    pointer = (root / "curriculum/resume.yaml").read_bytes()
    text = run_los(root, "resume", "--study")
    assert text.returncode == 0, text.stderr
    assert "Study options" in text.stdout
    assert "module-demo · unit-demo-l01" in text.stdout
    assert "resume --study --unit UNIT_ID" in text.stdout
    assert (root / "curriculum/resume.yaml").read_bytes() == pointer


def test_menu_ordering_pins_module_then_authored_then_numeric(mini_repo: Path):
    """Status never ranks the menu: authored unit_order positions decide,
    and unlisted units fall back to their numeric order, then the unit id.
    The paused map stays where the authored order put it."""
    root = _runtime_repo(mini_repo)
    _add_unit(root, "unit-demo-l03", 3, "ready")
    _add_unit(root, "unit-demo-l02", 2, "paused")
    _add_unit(root, "unit-demo-l05", 1, "active")
    _add_unit(root, "unit-demo-l04", 4, "active")
    module_path = root / "curriculum/modules/module-demo/module.yaml"
    module = yaml.safe_load(module_path.read_text(encoding="utf-8"))
    module["unit_order"] = ["unit-demo-l01", "unit-demo-l03", "unit-demo-l02"]
    write_yaml(module_path, module)
    payload = json.loads(run_los(root, "resume", "--study", "--json").stdout)
    assert [row["unit_id"] for row in payload["options"]] == [
        "unit-demo-l01", "unit-demo-l03", "unit-demo-l02",
        "unit-demo-l05", "unit-demo-l04"]
    assert [row["map_status"] for row in payload["options"]] == [
        "active", "ready", "paused", "active", "active"]
    assert payload["total"] == 5


def test_menu_total_computes_before_the_one_screen_truncation(mini_repo: Path):
    """The sixth option stays reachable: the total counts every choice,
    the screen carries five rows, and the continuation names the discovery
    commands that list the rest."""
    root = _runtime_repo(mini_repo)
    for number in range(2, 7):
        _add_unit(root, f"unit-demo-l{number:02d}", number, "active")
    payload = json.loads(run_los(root, "resume", "--study", "--json").stdout)
    assert payload["total"] == 6
    assert len(payload["options"]) == 5
    assert payload["options"][0]["unit_id"] == "unit-demo-l01"
    assert "unit-list --compact" in payload["continuation"]
    assert "bootstrap --compact" in payload["continuation"]
    text = run_los(root, "resume", "--study")
    assert text.returncode == 0, text.stderr
    assert "1 more past the one-screen bound" in text.stdout


def test_study_mode_unit_selects_one_option(mini_repo: Path):
    root = _runtime_repo(mini_repo)
    _add_unit(root, "unit-demo-l02", 2, "ready")
    payload = json.loads(run_los(
        root, "resume", "--study", "--unit", "unit-demo-l02", "--json").stdout)
    assert payload["via"] == "requested unit (study suggestion)"
    assert payload["content"]["stage"]["unit_id"] == "unit-demo-l02"
    assert payload["study_option"]["open"]["locator"] == "§1"
    assert payload["study_option"]["learner_choice"] is False


def _add_module_with_unit(root: Path, module_id: str, unit_id: str) -> None:
    """A second module owning one lecture unit with an open study map."""
    module_dir = root / f"curriculum/modules/{module_id}"
    write_yaml(module_dir / "module.yaml", {
        "id": module_id, "type": "module", "kind": "academic",
        "area_id": "program-bachelors", "institution": "HU Berlin",
        "title": "Other Module", "semester": "sose-2026", "status": "enrolled",
        "unit_order": [unit_id], "source_map": "source-map.yaml",
    })
    write_yaml(module_dir / "source-map.yaml", {
        "type": "module-source-map", "module_id": module_id, "sources": []})
    unit_dir = module_dir / "units" / unit_id
    unit_dir.mkdir(parents=True)
    stage_id = f"stage-{unit_id[5:]}"
    map_id = f"study-map-{unit_id[5:]}"
    write_yaml(unit_dir / "unit.yaml", {
        "id": unit_id, "type": "unit", "module_id": module_id,
        "kind": "lecture", "title": "Elsewhere", "order": 1,
        "scope": "The lecture as taught.", "status": "active",
        "current_study_map": map_id, "scope_sources": [], "artifacts": {},
        "workspace_ids": [],
    })
    note_rel = (f"curriculum/modules/{module_id}/units/{unit_id}"
                f"/stages/{stage_id}/notes.md")
    (root / note_rel).parent.mkdir(parents=True, exist_ok=True)
    (root / note_rel).write_text("", encoding="utf-8")
    write_yaml(unit_dir / "study-map.yaml", {
        "id": map_id, "type": "study-map", "unit_id": unit_id,
        "status": "active", "current_stage": stage_id,
        "source_plan": {"path": "work/active/workspace-demo/CONTEXT.md",
                        "provenance": "operator"},
        "detours": [], "shelving": {"state": "none"},
        "stages": [{
            "id": stage_id, "title": "Elsewhere stage", "status": "active",
            "objective": "Study the lecture.",
            "done_when": ["Explain the lecture."], "scope_triage": "required-now",
            "resources": [{
                "kind": "read", "label": "Other Book §1",
                "source_id": "source-demo-book", "locator": "§1",
                "scope_triage": "required-now"}],
            "working_note": note_rel, "attachments": [], "source_feedback": [],
        }],
    })


def test_study_mode_unit_works_across_modules(mini_repo: Path):
    """--unit honors any module's unit: the exam-module confinement is
    gone, and bare --study menus across modules with module_id on rows."""
    root = _runtime_repo(mini_repo)
    _add_module_with_unit(root, "module-other", "unit-other-l01")
    proc = run_los(root, "resume", "--study", "--unit", "unit-other-l01", "--json")
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["via"] == "requested unit (study suggestion)"
    assert payload["content"]["stage"]["unit_id"] == "unit-other-l01"
    assert payload["study_option"]["open"]["locator"] == "§1"
    assert payload["study_option"]["learner_choice"] is False
    pointer = (root / "curriculum/resume.yaml").read_bytes()
    assert (root / "curriculum/resume.yaml").read_bytes() == pointer

    menu = json.loads(run_los(root, "resume", "--study", "--json").stdout)
    assert menu["total"] == 2
    assert [row["module_id"] for row in menu["options"]] == [
        "module-demo", "module-other"]

    missing = run_los(root, "resume", "--study", "--unit", "unit-no-such")
    assert missing.returncode == 2
    assert "unit not found: unit-no-such" in missing.stderr
    assert "unit-list --compact" in missing.stderr
    bare = run_los(root, "resume", "--unit", "unit-demo-l01")
    assert bare.returncode == 2
    assert "resume --unit needs --study" in bare.stderr


def test_a_skipped_stage_is_an_ineligible_map_not_a_choice(mini_repo: Path):
    """The UI's isOpenStage excludes skipped stages; the builder agrees.
    Eligibility filters before anything counts: one eligible row beside
    one ineligible map is one choice, so the suggestion path fires."""
    root = _runtime_repo(mini_repo)
    _add_unit(root, "unit-demo-l02", 2, "active", stage_status="skipped")
    proc = run_los(root, "resume", "--study", "--json")
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["via"] == "single open study map (suggestion)"
    assert payload["content"]["stage"]["unit_id"] == "unit-demo-l01"


def test_study_mode_refusal_names_discovery_commands_when_nothing_is_open(
        mini_repo: Path):
    root = _runtime_repo(mini_repo)
    study_map = yaml.safe_load((root / MAP).read_text(encoding="utf-8"))
    study_map["status"] = "not-started"
    write_yaml(root / MAP, study_map)
    proc = run_los(root, "resume", "--study")
    assert proc.returncode == 2
    assert "no open study map" in proc.stderr
    assert "unit-list --compact" in proc.stderr
    assert "bootstrap --compact" in proc.stderr


def test_study_mode_ignores_recorded_sittings(mini_repo: Path):
    """A withdrawn attempt changes nothing here: exam facts stay canonical
    in the module record and the screen's exam line, never a study filter."""
    root = _runtime_repo(mini_repo)
    module_path = root / "curriculum/modules/module-demo/module.yaml"
    module = yaml.safe_load(module_path.read_text(encoding="utf-8"))
    module["attempts"][1]["result"] = "withdrawn"
    write_yaml(module_path, module)
    proc = run_los(root, "resume", "--study", "--json")
    assert proc.returncode == 0, proc.stderr
    assert json.loads(proc.stdout)["via"] == "single open study map (suggestion)"


def test_resume_renders_the_pointer_stage(
        mini_repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
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
    # The dossier sees the same projection as every other read: the
    # elapsed sitting without an attempt stays visible as unrecorded.
    assert [(row["start_date"], row["registration_state"])
            for row in content["sittings"]] == [
        ("2000-01-01", "unrecorded"), ("2026-10-09", "registered")]
    # Pin the observed clock so the 2026-10-09 sitting is still upcoming.
    observations = tmp_path / "observations.json"
    observations.write_text(
        json.dumps({"now": "2026-10-01T09:00:00+02:00"}) + "\n",
        encoding="utf-8")
    monkeypatch.setenv("LOS_OBSERVATIONS", str(observations))
    text = run_los(mini_repo, "resume")
    assert text.returncode == 0, text.stderr
    assert "req-demo-l01-demo" in text.stdout
    assert "los observe req-demo-l01-demo" in text.stdout
    assert "2026-10-09" in text.stdout
    assert not list((mini_repo / "generated/dossiers").glob("*-resume-*.json"))


def test_the_requirement_line_names_the_id_the_write_path_accepts(mini_repo: Path):
    """The screen labelled a value "Requirement" and the write path wanted
    a different key, so a reader who copied the label's value was refused
    by `los observe`. The label carries the id; the concept has its own line.
    """
    root = _runtime_repo(mini_repo)
    proc = run_los(root, "resume")
    assert proc.returncode == 0, proc.stderr
    lines = [line.strip() for line in proc.stdout.splitlines()]
    requirement = next(line for line in lines if line.startswith("Requirement "))
    assert requirement.split() == ["Requirement", "req-demo-l01-demo"]
    assert any(line.startswith("concept:")
               and "concept-expected-value" in line for line in lines)
    # The value the screen prints is the value the write path accepts.
    observed = run_los(root, "observe", "req-demo-l01-demo",
                       "--activity", "exercise", "--result", "partial")
    assert observed.returncode == 0, observed.stderr


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


def test_render_shows_no_top_goal_section():
    """The passive Top goal decoration is gone from the screen. The
    explicitly requested --json dossier keeps its top-cluster section
    (test_resume_json_carries_the_top_cluster_section pins that side)."""
    from learning_os.app.handlers.resume import _render
    from learning_os.derive.projection.resume_dossier import build_resume_dossier as build

    dossier = build(**_inputs(top_cluster=_cluster()))
    text = _render(dossier, {"id": "req-x"}, [], [], [],
                   {"module": "M", "unit": "U", "stage": "S"},
                   "via resume pointer")
    assert "Top goal" not in text


def test_resume_screen_shows_no_top_goal(mini_repo: Path):
    text = run_los(_runtime_repo(mini_repo), "resume")
    assert text.returncode == 0, text.stderr
    assert "Top goal" not in text.stdout


def test_resume_shows_recorded_evidence(mini_repo: Path):
    root = _runtime_repo(mini_repo)
    assert run_los(root, "observe", "req-demo-l01-demo",
                   "--activity", "exercise", "--result", "partial").returncode == 0
    payload = json.loads(run_los(root, "resume", "--json").stdout)
    assert len(payload["content"]["observations"]) == 1
    assert payload["content"]["observations"][0]["result"] == "partial"
    text = run_los(root, "resume")
    assert "Last result  partial" in text.stdout


def test_recovery_presents_the_menu_when_choices_exist(mini_repo: Path):
    """Choices + history: the menu is the answer, and it rides in the
    payload — the human view is presentation-only. The trail appears as
    clearly labeled context, never as the destination, and nothing here
    writes the pointer."""
    root = _runtime_repo(mini_repo)
    assert run_los(root, "observe", "req-demo-l01-demo",
                   "--activity", "exercise", "--result", "correct").returncode == 0
    (root / "curriculum/resume.yaml").unlink()
    proc = run_los(root, "resume", "--json")
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["contract"] == "resume-study-options"
    assert payload["recovery"]["pointer"] == "missing"
    historical = payload["recovery"]["historical"]
    assert historical["via"] == (
        "last recorded result (resume pointer missing or stale)")
    assert historical["module_id"] == "module-demo"
    assert historical["unit_id"] == "unit-demo-l01"
    assert historical["study_map_id"] == "study-map-demo-l01"
    assert historical["stage_id"] == "stage-demo"
    assert [row["unit_id"] for row in payload["options"]] == ["unit-demo-l01"]
    assert "via" not in payload
    assert not (root / "curriculum/resume.yaml").exists()
    text = run_los(root, "resume")
    assert text.returncode == 0, text.stderr
    assert "recovery asks" in text.stdout
    assert "Where you were (history, not a choice)" in text.stdout
    assert "last recorded result (resume pointer missing or stale)" in text.stdout


def test_recovery_menu_without_any_history(mini_repo: Path, monkeypatch):
    """Missing pointer + no history + a selectable map is a menu, not the
    old refusal. The menu is built independently of the recovery trail:
    monkeypatched-away commit timestamps change nothing but the context
    (precedent: the newest-touch test's timestamp monkeypatch)."""
    import learning_os.store.session.githistory as _git
    from learning_os.app.handlers.resume import _resolve_stage
    from learning_os.store.loader import load_repo

    root = _runtime_repo(mini_repo)
    (root / "curriculum/resume.yaml").unlink()
    monkeypatch.setattr(_git, "last_commit_timestamps", lambda _root: {})
    resolved = _resolve_stage(load_repo(root))
    assert resolved[0] is None
    payload = resolved[1]
    assert payload["contract"] == "resume-study-options"
    assert payload["recovery"]["pointer"] == "missing"
    assert payload["recovery"]["historical"] is None
    assert [row["unit_id"] for row in payload["options"]] == ["unit-demo-l01"]
    proc = run_los(root, "resume", "--json")
    assert proc.returncode == 0, proc.stderr
    assert json.loads(proc.stdout)["recovery"]["historical"] is None


def test_resume_refuses_without_anything_to_resume(mini_repo: Path):
    proc = run_los(mini_repo, "resume")
    assert proc.returncode == 2
    assert "no resumable stage" in proc.stderr
    assert "unit-list --compact" in proc.stderr


def test_recovery_context_names_the_newest_touch_when_a_menu_is_present(
        mini_repo: Path, monkeypatch):
    """History is context, not steering: the newest touched map labels the
    historical row, while the menu itself stays independent of the trail.

    This used to steer the destination: recovery skipped past the menu
    question entirely and opened the most recently touched map as the
    answer, preferencing requirement-bearing stages along the way (audit
    `synthetic-learner-2026-09-12`, F05). Now the same timestamps only
    label the secondary context row.
    """
    root = _runtime_repo(mini_repo)
    # l01 keeps its stage but loses its requirement: only l02 offers one.
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
    import learning_os.store.session.githistory as _git
    from learning_os.app.handlers.resume import _resolve_stage
    from learning_os.store.loader import load_repo

    # The requirement-less map was touched more recently.
    monkeypatch.setattr(_git, "last_commit_timestamps",
                        lambda _root: {old_map: "200", new_map: "100"})
    resolved = _resolve_stage(load_repo(root))
    assert resolved[0] is None
    payload = resolved[1]
    historical = payload["recovery"]["historical"]
    assert historical["via"] == (
        "recently touched stage (resume pointer missing or stale)")
    assert (historical["unit_id"], historical["stage_id"]) == (
        "unit-demo-l01", "stage-demo")
    # The menu itself is independent of the trail: both maps offer rows.
    assert [row["unit_id"] for row in payload["options"]] == [
        "unit-demo-l01", "unit-demo-l02"]
    # And the other way round, so this pins the ordering rather than a
    # constant: make the requirement-bearing map the newer one and the
    # labeled context follows it.
    monkeypatch.setattr(_git, "last_commit_timestamps",
                        lambda _root: {old_map: "100", new_map: "200"})
    resolved = _resolve_stage(load_repo(root))
    historical = resolved[1]["recovery"]["historical"]
    assert (historical["unit_id"], historical["stage_id"]) == (
        "unit-demo-l02", "stage-demo2")


def test_recovery_opens_the_labeled_history_when_nothing_is_selectable(
        mini_repo: Path):
    """No choices + history: the historical destination opens, labeled as
    history — never claimed as an available study choice."""
    root = _runtime_repo(mini_repo)
    assert run_los(root, "observe", "req-demo-l01-demo",
                   "--activity", "exercise", "--result", "correct").returncode == 0
    study_map = yaml.safe_load((root / MAP).read_text(encoding="utf-8"))
    study_map["status"] = "not-started"
    write_yaml(root / MAP, study_map)
    (root / "curriculum/resume.yaml").unlink()
    proc = run_los(root, "resume", "--json")
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["via"] == (
        "last recorded result (resume pointer missing or stale)")
    assert payload["content"]["stage"]["stage_id"] == "stage-demo"
    text = run_los(root, "resume")
    assert text.returncode == 0, text.stderr
    assert ("(via last recorded result (resume pointer missing or stale))"
            in text.stdout)


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
    assert "los stage-note" not in text.stdout
    assert ".venv/bin/python tools/seal_envelope.py --capability stage.note.write" in text.stdout
    assert "los capability stage.note.write --payload-file ENVELOPE.json" in text.stdout
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
