"""Module-first curriculum contract, migration, and action-specific gateway tests."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from learning_os.genout import _source_fingerprint, generate_all, write_outputs
from learning_os.loader import load_repo, parse_frontmatter
from learning_os.rules import validate

ROOT = Path(__file__).resolve().parent.parent
LOS = ROOT / "tools" / "los.py"
MIGRATE = ROOT / "tools" / "migrations" / "curriculum_v2.py"


def run_los(root: Path, *args: str):
    return subprocess.run([sys.executable, str(LOS), "--root", str(root), *args],
                          capture_output=True, text=True, timeout=120)


def write_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")


def add_curriculum(root: Path) -> None:
    write_yaml(root / "curriculum/programs/program-bachelors.yaml", {
        "id": "program-bachelors", "type": "program", "title": "Bachelor’s",
        "kind": "academic", "status": "active", "default": True,
        "semester_bound": True,
        "semesters": [{"id": "semester-sose-2026", "title": "SoSe 2026",
                       "status": "current", "order": 1}],
    })
    module_dir = root / "curriculum/modules/module-demo"
    write_yaml(module_dir / "module.yaml", {
        "id": "module-demo", "type": "module", "kind": "academic",
        "area_id": "program-bachelors", "institution": "HU Berlin",
        "title": "Demo Module", "semester": "sose-2026", "status": "enrolled",
        "unit_order": ["unit-demo-l01"], "source_map": "source-map.yaml",
        "examination": {
            "type": "klausur",
            "sittings": [
                {"termin": 3, "date": "2000-01-01", "label": "Elapsed unregistered sitting"},
                {"termin": 2, "date": "2026-10-09",
                 "time": "13:00-16:00", "label": "2. Termin"},
            ],
            "registration_windows": [{"opens": "2026-08-31", "closes": "2026-09-10",
                                      "label": "2.-PZ Anmeldung",
                                      "action": "Register via AGNES.", "termins": [2]}],
        },
        "attempts": [
            {"termin": 1, "date": "2026-07-27", "result": "withdrawn"},
            {"termin": 2, "date": "2026-10-09", "result": "registered"},
        ],
    })
    write_yaml(module_dir / "source-map.yaml", {
        "type": "module-source-map", "module_id": "module-demo",
        "sources": [{"source_id": "source-demo-book", "role": "spine",
                     "why": "Scoped demo reading.", "priority": 0,
                     "unit_routes": ["unit-demo-l01"]}],
    })
    unit_dir = module_dir / "units/unit-demo-l01"
    write_yaml(unit_dir / "unit.yaml", {
        "id": "unit-demo-l01", "type": "unit", "module_id": "module-demo",
        "kind": "lecture", "title": "Expected value", "order": 1,
        "scope": "The lecture as taught.", "status": "active",
        "scope_sources": [{"source_id": "source-demo-book", "authority": "slides",
                           "locator": "Lecture 1"}],
        "source_selections": [{"source_id": "source-demo-book", "locator": "§1 Erwartungswert",
                               "purpose": "Current derivation"}],
        "current_study_map": "study-map-demo-l01",
        "artifacts": {"ultimate_reference": "note-demo"},
        "workspace_ids": ["workspace-demo"],
    })
    note_rel = "curriculum/modules/module-demo/units/unit-demo-l01/stages/stage-demo/notes.md"
    (root / note_rel).parent.mkdir(parents=True, exist_ok=True)
    (root / note_rel).write_text("", encoding="utf-8")
    write_yaml(unit_dir / "study-map.yaml", {
        "id": "study-map-demo-l01", "type": "study-map", "unit_id": "unit-demo-l01",
        "status": "active", "current_stage": "stage-demo",
        "source_plan": {"path": "work/active/workspace-demo/CONTEXT.md",
                        "provenance": "operator"},
        "detours": [], "shelving": {"state": "none"},
        "stages": [{
            "id": "stage-demo", "title": "Derive expected value", "status": "active",
            "objective": "Derive and explain expected value.",
            "done_when": ["Explain the derivation."], "scope_triage": "required-now",
            "resources": [{"kind": "read", "label": "Demo Book §1",
                           "source_id": "source-demo-book", "locator": "§1"}],
            "working_note": note_rel, "attachments": [], "source_feedback": [],
        }],
    })
    write_yaml(root / "curriculum/resume.yaml", {
        "type": "resume-pointer", "module_id": "module-demo", "unit_id": "unit-demo-l01",
        "study_map_id": "study-map-demo-l01", "stage_id": "stage-demo",
        "updated": "2026-08-03",
    })
    ws_path = root / "work/active/workspace-demo/CONTEXT.md"
    meta, body = parse_frontmatter(ws_path.read_text(encoding="utf-8"), ws_path)
    meta.update({"program_ids": ["program-bachelors"], "module_ids": ["module-demo"],
                 "unit_ids": ["unit-demo-l01"]})
    ws_path.write_text("---\n" + yaml.safe_dump(meta, sort_keys=False).rstrip() +
                       "\n---\n\n" + body.lstrip(), encoding="utf-8")


def test_manifest_v2_exposes_full_curriculum_and_reverse_indexes(mini_repo):
    add_curriculum(mini_repo)
    repo = load_repo(mini_repo)
    assert not [issue for issue in validate(repo) if issue.severity == "E"]
    manifest = json.loads(generate_all(repo, "T1")["manifest.json"])
    assert manifest["_generated"]["contract_version"] == 2
    assert manifest["programs"][0]["id"] == "program-bachelors"
    assert manifest["modules"][0]["id"] == "module-demo"
    assert manifest["units"][0]["source_selections"][0]["locator"] == "§1 Erwartungswert"
    assert manifest["study_maps"][0]["stages"][0]["notes_text"] == ""
    assert manifest["indexes"]["module_to_units"] == {"module-demo": ["unit-demo-l01"]}
    assert manifest["indexes"]["source_to_units"] == {"source-demo-book": ["unit-demo-l01"]}
    assert manifest["resume_pointer"]["stage_id"] == "stage-demo"
    assert manifest["progress"]["module-demo"]["stages_total"] == 1
    assert manifest["academic_deadlines"] == [
        {"kind": "registration-window", "start_date": "2026-08-31",
         "end_date": "2026-09-10", "label": "2.-PZ Anmeldung",
         "modules": [{"module_id": "module-demo", "title": "Demo Module",
                      "action": "Register via AGNES.", "termins": [2]}]},
        {"kind": "exam", "start_date": "2026-10-09", "end_date": "2026-10-09",
         "module_id": "module-demo", "title": "Demo Module", "termin": 2,
         "label": "2. Termin", "time": "13:00-16:00", "notes": None,
         "registration_state": "registered"},
    ]
    assert "Elapsed unregistered sitting" not in json.dumps(manifest["academic_deadlines"])


def test_non_academic_module_needs_no_institution_or_semester(mini_repo):
    add_curriculum(mini_repo)
    write_yaml(mini_repo / "curriculum/programs/program-skills.yaml", {
        "id": "program-skills", "type": "program", "title": "Skills", "kind": "skills",
        "status": "active", "default": False, "semester_bound": False, "semesters": [],
    })
    module = mini_repo / "curriculum/modules/module-skill-python"
    write_yaml(module / "module.yaml", {
        "id": "module-skill-python", "type": "module", "kind": "skill",
        "area_id": "program-skills", "title": "Python", "status": "active",
        "unit_order": ["unit-python-scope"], "source_map": "source-map.yaml",
    })
    write_yaml(module / "source-map.yaml", {"type": "module-source-map",
                                             "module_id": "module-skill-python", "sources": []})
    write_yaml(module / "units/unit-python-scope/unit.yaml", {
        "id": "unit-python-scope", "type": "unit", "module_id": "module-skill-python",
        "kind": "topic", "title": "Scope", "order": 1, "scope": "Python scope repair.",
        "status": "needs-map", "scope_sources": [], "source_selections": [],
        "artifacts": {}, "workspace_ids": [],
    })
    issues = validate(load_repo(mini_repo))
    assert not [issue for issue in issues if issue.severity == "E"]


def test_stage_feedback_detour_and_progress_are_unit_scoped(mini_repo):
    add_curriculum(mini_repo)
    before = load_repo(mini_repo).sources["source-demo-book"]["evaluations"]
    feedback = run_los(mini_repo, "source-feedback", "unit-demo-l01", "stage-demo",
                       "source-demo-book", "too-advanced", "--note", "Return after the lecture.")
    assert feedback.returncode == 0, feedback.stderr
    repo = load_repo(mini_repo)
    stage = repo.study_maps["study-map-demo-l01"].data["stages"][0]
    assert stage["source_feedback"][0]["feedback"] == "too-advanced"
    assert repo.sources["source-demo-book"]["evaluations"] == before

    detour = run_los(mini_repo, "detour-create", "unit-demo-l01", "stage-demo",
                     "--title", "Review finite sums", "--classification", "required-now")
    assert detour.returncode == 0, detour.stderr
    did = json.loads(detour.stdout)["detour"]["id"]
    assert load_repo(mini_repo).study_maps["study-map-demo-l01"].data["status"] == "paused"
    resolved = run_los(mini_repo, "detour-resolve", "unit-demo-l01", did,
                       "--resolution", "Reviewed the needed identity.")
    assert resolved.returncode == 0, resolved.stderr
    completed = run_los(mini_repo, "stage-progress", "unit-demo-l01", "stage-demo", "complete")
    assert completed.returncode == 0, completed.stderr
    repo = load_repo(mini_repo)
    assert repo.study_maps["study-map-demo-l01"].data["status"] == "ready-to-shelve"
    assert repo.units["unit-demo-l01"].data["status"] == "ready-to-shelve"


def test_stage_note_snapshot_guard_and_german_search(mini_repo):
    add_curriculum(mini_repo)
    write_outputs(load_repo(mini_repo), generate_all(load_repo(mini_repo), "T1"))
    manifest = json.loads((mini_repo / "generated/manifest.json").read_text(encoding="utf-8"))
    snapshot = manifest["_generated"]["snapshot_id"]
    saved = run_los(mini_repo, "stage-note", "unit-demo-l01", "stage-demo", "--replace",
                    "--text", "Meine Herleitung.", "--expected-snapshot", snapshot)
    assert saved.returncode == 0, saved.stderr
    stale = run_los(mini_repo, "stage-note", "unit-demo-l01", "stage-demo", "--replace",
                    "--text", "Would overwrite.", "--expected-snapshot", snapshot)
    assert stale.returncode == 3
    search = run_los(mini_repo, "search", "Erwartungswert")
    assert search.returncode == 0
    assert "concept-expected-value" in search.stdout


def test_unit_map_import_creates_one_current_map(mini_repo, tmp_path):
    add_curriculum(mini_repo)
    module_path = mini_repo / "curriculum/modules/module-demo/module.yaml"
    module = yaml.safe_load(module_path.read_text(encoding="utf-8"))
    module["unit_order"].append("unit-demo-l02")
    write_yaml(module_path, module)
    unit_dir = module_path.parent / "units/unit-demo-l02"
    write_yaml(unit_dir / "unit.yaml", {
        "id": "unit-demo-l02", "type": "unit", "module_id": "module-demo",
        "kind": "lecture", "title": "Variance", "order": 2, "scope": "Lecture 2.",
        "status": "needs-map", "scope_sources": [], "source_selections": [],
        "artifacts": {}, "workspace_ids": [],
    })
    note_rel = "curriculum/modules/module-demo/units/unit-demo-l02/stages/stage-variance/notes.md"
    incoming = tmp_path / "map.yaml"
    write_yaml(incoming, {
        "id": "study-map-demo-l02", "type": "study-map", "unit_id": "unit-demo-l02",
        "status": "ready", "current_stage": "stage-variance",
        "source_plan": {"path": "proposal.json", "provenance": "ai-proposed"},
        "detours": [], "shelving": {"state": "none"},
        "stages": [{"id": "stage-variance", "title": "Variance", "status": "pending",
                    "objective": "Derive variance.", "done_when": ["Derive it."],
                    "scope_triage": "required-now", "resources": [],
                    "working_note": note_rel, "attachments": [], "source_feedback": []}],
    })
    proc = run_los(mini_repo, "unit-map-import", "unit-demo-l02", "--file", str(incoming))
    assert proc.returncode == 0, proc.stderr
    repo = load_repo(mini_repo)
    assert repo.units["unit-demo-l02"].data["current_study_map"] == "study-map-demo-l02"
    assert (mini_repo / note_rel).is_file()


def test_module_plan_import_adds_units_sources_and_workspace_join(mini_repo, tmp_path):
    add_curriculum(mini_repo)
    note_rel = "curriculum/modules/module-demo/units/unit-demo-l02/stages/stage-variance/notes.md"
    audit_rel = "work/active/workspace-demo/outputs/demo-coverage-audit.md"
    audit = mini_repo / audit_rel
    audit.parent.mkdir(parents=True, exist_ok=True)
    audit.write_text(
        "# Complete demo coverage audit\n\n## Local inventory\n\nDone.\n\n"
        "## Linked inventory\n\nDone.\n\n## Completeness sign-off\n\nDone.\n",
        encoding="utf-8",
    )
    package = tmp_path / "module-plan.yaml"
    shared_empty = []
    package_data = {
        "module_id": "module-demo",
        "plan_contract": {
            "version": 1,
            "coverage_audit": audit_rel,
            "checks": {
                "local_inventory_complete": True,
                "linked_inventory_complete": True,
                "materials_opened_and_content_checked": True,
                "current_and_prior_scope_reconciled": True,
                "duplicates_and_numbering_checked": True,
                "exclusions_and_unresolved_gaps_recorded": True,
            },
        },
        "module_patch": {"title": "Standardized Demo Module",
                         "unit_order": ["unit-demo-l02", "unit-demo-l01"]},
        "source_patches": [{"id": "source-demo-book", "title": "Demo Book, verified"}],
        "source_map": {
            "type": "module-source-map", "module_id": "module-demo",
            "sources": [{"source_id": "source-demo-book", "role": "course-material",
                         "why": "Scope and drills.", "priority": 0,
                         "unit_routes": ["unit-demo-l01", "unit-demo-l02"]}],
        },
        "units": [{
            "unit": {"id": "unit-demo-l02", "type": "unit", "module_id": "module-demo",
                     "kind": "lecture", "title": "Variance", "order": 1,
                     "scope": "Lecture 2 as taught.", "status": "ready",
                     "scope_sources": [{"source_id": "source-demo-book", "authority": "slides"}],
                     "source_selections": [], "current_study_map": "study-map-demo-l02",
                     "artifacts": {}, "workspace_ids": ["workspace-demo"]},
            "study_map": {"id": "study-map-demo-l02", "type": "study-map",
                          "unit_id": "unit-demo-l02", "status": "ready",
                          "current_stage": "stage-variance",
                          "source_plan": {"path": "work/active/workspace-demo/CONTEXT.md",
                                          "provenance": "operator"},
                          "detours": [], "shelving": {"state": "none"},
                          "stages": [{"id": "stage-variance", "title": "Variance",
                                      "status": "pending", "objective": "Derive variance.",
                                      "done_when": ["Derive it."],
                                      "scope_triage": "required-now", "resources": [],
                                      "working_note": note_rel,
                                      "attachments": shared_empty,
                                      "source_feedback": shared_empty}]},
        }],
        "workspace_updates": [{"id": "workspace-demo",
                               "sources": ["source-demo-book"],
                               "unit_ids": ["unit-demo-l02", "unit-demo-l01"],
                               "sections": {"Next Action": "Start the standardized variance unit."}}],
    }
    write_yaml(package, package_data)
    assert "&id" in package.read_text(encoding="utf-8")

    broken = yaml.safe_load(package.read_text(encoding="utf-8"))
    broken["source_map"]["sources"][0]["unit_routes"] = ["unit-demo-l01"]
    broken_package = tmp_path / "broken-module-plan.yaml"
    write_yaml(broken_package, broken)
    rejected = run_los(mini_repo, "module-plan-import", "module-demo", "--file",
                       str(broken_package), "--check")
    assert rejected.returncode == 1
    assert "source-map unit_routes omit the unit" in rejected.stderr
    assert load_repo(mini_repo).modules["module-demo"]["title"] == "Demo Module"

    checked = run_los(mini_repo, "module-plan-import", "module-demo", "--file",
                      str(package), "--check")
    assert checked.returncode == 0, checked.stderr
    assert json.loads(checked.stdout)["canonical_files_written"] == 0
    assert "unit-demo-l02" not in load_repo(mini_repo).units

    unguarded = run_los(mini_repo, "module-plan-import", "module-demo", "--file",
                        str(package))
    assert unguarded.returncode == 2
    snapshot = f"sha256:{_source_fingerprint(load_repo(mini_repo))}"
    proc = run_los(mini_repo, "module-plan-import", "module-demo", "--file", str(package),
                   "--expected-snapshot", snapshot)
    assert proc.returncode == 0, proc.stderr
    repo = load_repo(mini_repo)
    assert repo.modules["module-demo"]["title"] == "Standardized Demo Module"
    assert repo.sources["source-demo-book"]["title"] == "Demo Book, verified"
    assert repo.modules["module-demo"]["unit_order"][0] == "unit-demo-l02"
    assert repo.workspaces["workspace-demo"].meta["unit_ids"][0] == "unit-demo-l02"
    assert "standardized variance" in repo.workspaces["workspace-demo"].section("Next Action")
    assert (mini_repo / note_rel).is_file()
    rendered_map = (mini_repo / "curriculum/modules/module-demo/units/unit-demo-l02/study-map.yaml").read_text(encoding="utf-8")
    assert "&id" not in rendered_map and "*id" not in rendered_map


def test_note_revise_is_approval_gated_and_preserves_identity_and_role(mini_repo, tmp_path):
    revised = tmp_path / "note-demo.md"
    revised.write_text("""---
id: note-demo
type: note
title: Demo note revised
created: 2026-07-16
role: synthesis
concepts: [concept-expected-value]
sources: [source-demo-book]
---

Revised after explicit review.
""", encoding="utf-8")
    denied = run_los(mini_repo, "note-revise", "note-demo", "--file", str(revised))
    assert denied.returncode == 2
    applied = run_los(mini_repo, "note-revise", "note-demo", "--file", str(revised),
                      "--approve")
    assert applied.returncode == 0, applied.stderr
    note = load_repo(mini_repo).notes["note-demo"]
    assert note.meta["title"] == "Demo note revised"
    assert note.meta["role"] == "synthesis"
    assert "explicit review" in note.body


def test_shelving_applies_only_selected_items_after_explicit_approval(mini_repo, tmp_path):
    add_curriculum(mini_repo)
    items = tmp_path / "items.json"
    items.write_text(json.dumps({"items": [
        {"id": "proposal-keep", "kind": "garden", "title": "Keep",
         "destination": "knowledge/garden/kept-idea.md", "rationale": "Worth gestating.",
         "content": "# Kept idea\n\nOriginal wording."},
        {"id": "proposal-skip", "kind": "garden", "title": "Skip",
         "destination": "knowledge/garden/skipped-idea.md", "rationale": "Optional.",
         "content": "# Skipped idea"},
    ]}), encoding="utf-8")
    prepared = run_los(mini_repo, "shelving-prepare", "unit-demo-l01",
                       "--items-file", str(items))
    assert prepared.returncode == 0, prepared.stderr
    denied = run_los(mini_repo, "shelving-apply", "unit-demo-l01",
                     "--selected", "proposal-keep")
    assert denied.returncode == 2
    applied = run_los(mini_repo, "shelving-apply", "unit-demo-l01", "--approve",
                      "--selected", "proposal-keep")
    assert applied.returncode == 0, applied.stderr
    assert (mini_repo / "knowledge/garden/kept-idea.md").is_file()
    assert not (mini_repo / "knowledge/garden/skipped-idea.md").exists()


def test_quarantine_boundary_never_projects_quarantined_content(mini_repo):
    add_curriculum(mini_repo)
    write_yaml(mini_repo / "curriculum/programs/program-masters-planning.yaml", {
        "id": "program-masters-planning", "type": "program", "title": "Master’s Planning",
        "kind": "quarantine", "status": "quarantined", "default": False,
        "semester_bound": False, "boundary_action": "Open Master’s Planning", "semesters": [],
    })
    write_yaml(mini_repo / "curriculum/quarantine/index.yaml", {
        "type": "quarantine-index", "id": "quarantine-masters-planning",
        "workspace_ids": ["workspace-degree-planning"],
        "boundary_program_id": "program-masters-planning",
    })
    secret = mini_repo / "curriculum/quarantine/masters-planning/prospective.md"
    secret.parent.mkdir(parents=True, exist_ok=True)
    secret.write_text("QUARANTINED-PROSPECTIVE-SECRET", encoding="utf-8")
    manifest = generate_all(load_repo(mini_repo), "T1")["manifest.json"]
    assert "program-masters-planning" in manifest
    assert "QUARANTINED-PROSPECTIVE-SECRET" not in manifest
    assert "workspace-degree-planning" not in manifest


def test_session_end_reports_canvas_as_unrelated_and_never_session_owned(mini_repo):
    add_curriculum(mini_repo)
    subprocess.run(["git", "init", "-q"], cwd=mini_repo, check=True)
    subprocess.run(["git", "config", "user.email", "tests@example.invalid"], cwd=mini_repo, check=True)
    subprocess.run(["git", "config", "user.name", "Tests"], cwd=mini_repo, check=True)
    subprocess.run(["git", "add", "."], cwd=mini_repo, check=True)
    subprocess.run(["git", "commit", "-qm", "fixture"], cwd=mini_repo, check=True)
    saved = run_los(mini_repo, "stage-note", "unit-demo-l01", "stage-demo",
                    "--replace", "--text", "Session-owned note.")
    assert saved.returncode == 0, saved.stderr
    (mini_repo / "Untitled.canvas").write_text("{}", encoding="utf-8")
    ended = run_los(mini_repo, "session-end")
    assert ended.returncode == 0, ended.stderr
    payload = json.loads(ended.stdout)
    assert any("stage-demo/notes.md" in path for path in payload["touched"])
    assert "Untitled.canvas" not in payload["touched"]
    assert any("Untitled.canvas" in line for line in payload["unrelated_changes"])
    # session-end gates on validation, and validate.py resolves its repository
    # from its own location unless given --root. Without that flag it validated
    # the repository the TOOLS live in, so an unrelated warning over there could
    # block closing a session here. The freshly written report proves the
    # validator ran against THIS root.
    report = mini_repo / "generated" / "reports" / "validation-report.md"
    assert report.is_file(), "session-end validated a different repository root"


# ------------------------------------------- write-path robustness (red-team)
NOTE_REL = "curriculum/modules/module-demo/units/unit-demo-l01/stages/stage-demo/notes.md"


def test_empty_note_text_is_refused_instead_of_truncating(mini_repo):
    add_curriculum(mini_repo)
    saved = run_los(mini_repo, "stage-note", "unit-demo-l01", "stage-demo",
                    "--replace", "--text", "Real content worth keeping.")
    assert saved.returncode == 0, saved.stderr
    note = mini_repo / NOTE_REL
    before = note.read_text(encoding="utf-8")
    for empty in ("", "   \n\t "):
        wiped = run_los(mini_repo, "stage-note", "unit-demo-l01", "stage-demo",
                        "--replace", "--text", empty)
        assert wiped.returncode == 2
        assert "empty note" in wiped.stderr
    assert note.read_text(encoding="utf-8") == before


def test_empty_snapshot_token_is_refused_not_read_as_unguarded(mini_repo):
    add_curriculum(mini_repo)
    probe = run_los(mini_repo, "stage-note", "unit-demo-l01", "stage-demo",
                    "--text", "probe", "--expected-snapshot", "")
    assert probe.returncode == 3
    assert "expected-snapshot" in probe.stderr
    # omitting the flag entirely still writes unguarded, as documented
    unguarded = run_los(mini_repo, "stage-note", "unit-demo-l01", "stage-demo",
                        "--text", "probe")
    assert unguarded.returncode == 0, unguarded.stderr


def test_two_captures_with_one_title_in_one_second_keep_both(mini_repo):
    add_curriculum(mini_repo)
    first = run_los(mini_repo, "capture", "--json", "--title", "race", "--text", "FIRST")
    second = run_los(mini_repo, "capture", "--json", "--title", "race", "--text", "SECOND")
    assert first.returncode == 0, first.stderr
    assert second.returncode == 0, second.stderr
    one, two = json.loads(first.stdout), json.loads(second.stdout)
    assert one["ok"] and two["ok"]
    assert one["captured"] != two["captured"]
    bodies = [(mini_repo / payload["captured"]).read_text(encoding="utf-8")
              for payload in (one, two)]
    assert any("FIRST" in body for body in bodies)
    assert any("SECOND" in body for body in bodies)


def test_unwritable_note_target_refuses_cleanly_without_debris(mini_repo):
    add_curriculum(mini_repo)
    note = mini_repo / NOTE_REL
    note.unlink()
    note.mkdir()  # the target is now a directory: an ordinary filesystem mishap
    proc = run_los(mini_repo, "stage-note", "unit-demo-l01", "stage-demo", "--text", "probe")
    assert proc.returncode == 2
    assert "cannot write" in proc.stderr
    assert "Traceback" not in proc.stderr
    assert not list(note.parent.glob(".*.tmp")), "a temp file was left behind"


def test_a_failed_write_rolls_the_whole_transaction_back(mini_repo):
    """stage-progress writes the study map AND the unit.

    When the second write failed the first stayed applied, and `validate` saw
    nothing wrong — a silent cross-file split-brain.
    """
    add_curriculum(mini_repo)
    unit_dir = mini_repo / "curriculum/modules/module-demo/units/unit-demo-l01"
    study_map, unit = unit_dir / "study-map.yaml", unit_dir / "unit.yaml"
    before_map = study_map.read_text(encoding="utf-8")
    before_unit = unit.read_text(encoding="utf-8")
    (unit_dir / ".unit.yaml.tmp").mkdir()  # block the atomic temp name
    proc = run_los(mini_repo, "stage-progress", "unit-demo-l01", "stage-demo", "complete")
    assert proc.returncode == 2
    assert "Traceback" not in proc.stderr
    assert study_map.read_text(encoding="utf-8") == before_map
    assert unit.read_text(encoding="utf-8") == before_unit
    (unit_dir / ".unit.yaml.tmp").rmdir()
    retry = run_los(mini_repo, "stage-progress", "unit-demo-l01", "stage-demo", "complete")
    assert retry.returncode == 0, retry.stderr


def test_stage_ids_must_be_unique_across_study_maps(mini_repo):
    """`stages` is projected as a flat by-id index, so a stage id reused in
    another unit resolves to whichever map was generated last. Five stages in
    the curriculum-v2 import collided this way and only in-map uniqueness was
    checked."""
    import shutil

    add_curriculum(mini_repo)
    units = mini_repo / "curriculum/modules/module-demo/units"
    shutil.copytree(units / "unit-demo-l01", units / "unit-demo-l02")
    for name in ("unit.yaml", "study-map.yaml"):
        target = units / "unit-demo-l02" / name
        text = target.read_text(encoding="utf-8")
        # everything is re-identified except the stage id, which stays colliding
        text = text.replace("unit-demo-l01", "unit-demo-l02")
        text = text.replace("study-map-demo-l01", "study-map-demo-l02")
        target.write_text(text, encoding="utf-8")
    module_path = mini_repo / "curriculum/modules/module-demo/module.yaml"
    module = yaml.safe_load(module_path.read_text(encoding="utf-8"))
    module["unit_order"].append("unit-demo-l02")
    write_yaml(module_path, module)
    codes = {issue.code for issue in validate(load_repo(mini_repo), online=False)}
    assert "MAP-STAGE-GLOBAL-DUP" in codes


def test_an_impossible_calendar_date_fails_validation(mini_repo):
    """`format: date` is declared in the schemas but was never enforced, so a
    transposed exam date validated clean."""
    registry = mini_repo / "records" / "modules.yaml"
    data = yaml.safe_load(registry.read_text(encoding="utf-8"))
    data["modules"][0]["attempts"][0]["date"] = "2026-13-45"
    write_yaml(registry, data)
    proc = run_los(mini_repo, "validate")
    assert proc.returncode != 0
    assert "2026-13-45" in proc.stdout
    assert "date" in proc.stdout


def test_session_end_reports_warnings_without_blocking(mini_repo):
    """Errors gate a session; by-design offline-material warnings must not."""
    add_curriculum(mini_repo)
    for command in (["git", "init", "-q"],
                    ["git", "config", "user.email", "tests@example.invalid"],
                    ["git", "config", "user.name", "Tests"],
                    ["git", "add", "."],
                    ["git", "commit", "-qm", "fixture"]):
        subprocess.run(command, cwd=mini_repo, check=True)
    registry = mini_repo / "sources" / "sources.yaml"
    data = yaml.safe_load(registry.read_text(encoding="utf-8"))
    data["sources"][0]["material"] = "material://source-demo-book-offline"
    write_yaml(registry, data)
    saved = run_los(mini_repo, "stage-note", "unit-demo-l01", "stage-demo",
                    "--replace", "--text", "Session-owned note.")
    assert saved.returncode == 0, saved.stderr
    check = run_los(mini_repo, "validate")
    assert check.returncode == 0, check.stderr
    assert "0 warning(s)" not in check.stdout, "fixture did not produce a warning"
    ended = run_los(mini_repo, "session-end")
    assert ended.returncode == 0, ended.stderr
    payload = json.loads(ended.stdout)
    assert "warning(s)" in payload["validation"]



def test_unit_note_is_session_scoped_and_projected(mini_repo, tmp_path):
    add_curriculum(mini_repo)
    write_outputs(load_repo(mini_repo), generate_all(load_repo(mini_repo), "T0"))
    manifest = json.loads((mini_repo / "generated/manifest.json").read_text(encoding="utf-8"))
    snapshot = manifest["_generated"]["snapshot_id"]
    attachment = tmp_path / "handwritten.png"
    attachment.write_bytes(b"fixture-image")

    saved = run_los(
        mini_repo, "unit-note", "unit-demo-l01",
        "--title", "Expected value session",
        "--text", "I connected linearity to the indicator-variable argument.",
        "--stage-id", "stage-demo",
        "--attachment", str(attachment),
        "--expected-snapshot", snapshot,
    )
    assert saved.returncode == 0, saved.stderr
    payload = json.loads(saved.stdout)
    assert payload["stage_ids"] == ["stage-demo"]
    assert len(payload["attachments"]) == 1

    unit = yaml.safe_load(
        (mini_repo / "curriculum/modules/module-demo/units/unit-demo-l01/unit.yaml")
        .read_text(encoding="utf-8")
    )
    assert unit["working_note"].endswith("/notes.md")
    note = mini_repo / unit["working_note"]
    text = note.read_text(encoding="utf-8")
    assert "learningos:unit-note" in text
    assert "Expected value session" in text
    assert "indicator-variable" in text

    projected = json.loads((mini_repo / "generated/manifest.json").read_text(encoding="utf-8"))
    unit_row = next(row for row in projected["units"] if row["id"] == "unit-demo-l01")
    assert unit_row["notes_text"] == text
    assert unit_row["note_sections"][0]["title"] == "Expected value session"
    assert unit_row["note_sections"][0]["stage_ids"] == ["stage-demo"]
    assert unit_row["note_sections"][0]["attachments"][0]["path"].endswith("handwritten.png")
    assert "indicator-variable" in unit_row["note_sections"][0]["summary"]
    # The legacy selected stage is not required by the command envelope.
    assert "stage_id" not in payload


def test_unit_note_rejects_foreign_stage_and_preserves_state(mini_repo):
    add_curriculum(mini_repo)
    unit_path = mini_repo / "curriculum/modules/module-demo/units/unit-demo-l01/unit.yaml"
    before = unit_path.read_text(encoding="utf-8")
    refused = run_los(
        mini_repo, "unit-note", "unit-demo-l01", "--text", "Do not write this",
        "--stage-id", "stage-foreign",
    )
    assert refused.returncode == 2
    assert "does not belong" in refused.stderr
    assert unit_path.read_text(encoding="utf-8") == before
    assert not (unit_path.parent / "notes.md").exists()


def test_unit_note_snapshot_guard_keeps_note_unchanged(mini_repo):
    add_curriculum(mini_repo)
    refused = run_los(
        mini_repo, "unit-note", "unit-demo-l01", "--text", "stale",
        "--expected-snapshot", "sha256:stale",
    )
    assert refused.returncode == 3
    assert not (mini_repo / "curriculum/modules/module-demo/units/unit-demo-l01/notes.md").exists()

def test_live_migration_is_idempotent_in_dry_run(repo_root):
    proc = subprocess.run([sys.executable, str(MIGRATE), "--root", str(repo_root), "--report"],
                          capture_output=True, text=True, timeout=120)
    assert proc.returncode == 0, proc.stderr
    assert "dry-run: 0 action(s)" in proc.stdout


# AMLS PAPER INVENTORY
#
# The reading list this inventory describes lives outside the authored tree,
# under ../materials/ (CLAUDE.md §11), so a CI checkout of this repository
# alone cannot see it. Splitting the old single test keeps every wiring
# assertion running everywhere:
#
#   * the wiring test reads the checked-in fixture — hermetic, runs in CI;
#   * the drift test proves the fixture still matches the external list —
#     local only, skipped where materials/ is not present.
#
# Regenerate the fixture with tools/refresh_amls_fixture.py.

AMLS_INVENTORY = Path(__file__).resolve().parent / "fixtures" / "amls-paper-inventory.yaml"
AMLS_READING_LIST = (
    ROOT.parent
    / "materials/ML/AMLS/course/amls-ss26-lectures/AMLS-Source-Papers-Reading-List.md"
)


def _amls_inventory() -> dict:
    return yaml.safe_load(AMLS_INVENTORY.read_text(encoding="utf-8"))


def test_amls_complete_paper_inventory_is_wired_per_lecture(repo_root):
    inventory = _amls_inventory()
    assert inventory["totals"]["curated"] == 60
    assert inventory["totals"]["bibliography"] == 283

    repo = load_repo(repo_root)
    source = repo.sources["source-amls-ss26-lectures"]
    assert source["material"] == "material://source-amls-ss26-lectures"
    assert source["identifiers"]["paper-reading-list"].endswith(
        "/AMLS-Source-Papers-Reading-List.md")

    for lecture, expected in inventory["lectures"].items():
        study_map = repo.study_maps[f"study-map-amls-l{lecture}"].data
        stage = next(row for row in study_map["stages"]
                     if row["id"] == f"stage-amls-l{lecture}-integrate")
        selected = [row for row in stage["resources"]
                    if row.get("locator") ==
                    f"AMLS paper reading list, Part 1, Lecture {lecture}"]
        assert [row["label"].removeprefix("Primary paper — ")
                for row in selected] == expected["curated"]
        assert all(row.get("url") and row.get("vault_path") for row in selected)
        complete = [row for row in stage["resources"]
                    if row.get("locator") ==
                    f"AMLS paper reading list, Part 2, Lecture {lecture}; reference-only"]
        assert len(complete) == 1
        assert complete[0]["kind"] == "reference"
        assert f"({expected['bibliography']} entries)" in complete[0]["label"]
        assert any("Every curated paper is marked" in item for item in stage["done_when"])


def test_amls_reading_list_still_matches_checked_in_inventory():
    if not AMLS_READING_LIST.exists():
        pytest.skip(f"materials/ not checked out: {AMLS_READING_LIST}")
    sys.path.insert(0, str(ROOT / "tools"))
    from refresh_amls_fixture import parse_reading_list

    assert parse_reading_list(AMLS_READING_LIST) == _amls_inventory()["lectures"], (
        "the external AMLS reading list has drifted from "
        "tests/fixtures/amls-paper-inventory.yaml — rerun "
        "tools/refresh_amls_fixture.py, then re-wire the affected study maps"
    )


def test_live_migration_preserves_rollback_evidence(repo_root):
    original = repo_root / "records/modules.yaml"
    backup = repo_root / "migration/curriculum-v2/originals/records-modules.yaml"
    mapping = yaml.safe_load(
        (repo_root / "migration/curriculum-v2/old-to-new.yaml").read_text(encoding="utf-8"))
    report = (repo_root / "migration/curriculum-v2/report.md").read_text(encoding="utf-8")
    assert backup.read_bytes() == original.read_bytes()
    pairs = {(row["old"], row["new"]) for row in mapping["mappings"]}
    assert ("work/active/workspace-degree-planning",
            "curriculum/quarantine/masters-planning/workspaces/workspace-degree-planning") in pairs
    assert ("sources/collections/degree-module-anchors.yaml",
            "curriculum/quarantine/masters-planning/sources/degree-module-anchors.yaml") in pairs
    assert "codex/learning-path-app-v1" in report
    assert "revert" in report.casefold()


# MATERIAL RESOURCE PROJECTION REGRESSION MATRIX
#
# These tests define the core-owned interface contract for exact local stage
# resources. They intentionally precede the generator implementation.
#
# They use only mini_repo/tmp_path data and never inspect the real materials
# tree, real generated manifest, canary, or user vault.


def _material_projection_fixture(
        mini_repo,
        *,
        source_material,
        resources,
        existing_files=()):
    """Project one synthetic study-map resource set through the real core."""
    from learning_os.genout import build_manifest
    from learning_os.loader import load_repo

    add_curriculum(mini_repo)

    registry = mini_repo / "sources" / "sources.yaml"
    registry_data = yaml.safe_load(registry.read_text(encoding="utf-8"))
    source = next(
        row for row in registry_data["sources"]
        if row["id"] == "source-demo-book"
    )
    source["material"] = source_material
    write_yaml(registry, registry_data)

    repo = load_repo(mini_repo)
    study_map = next(iter(repo.study_maps.values()))
    map_data = study_map.data

    assert map_data["stages"], "synthetic curriculum has no stage"
    stage = map_data["stages"][0]
    stage_id = stage["id"]
    stage["resources"] = resources
    write_yaml(study_map.path, map_data)

    for relative in existing_files:
        target = repo.materials_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            f"fixture material: {relative}\n",
            encoding="utf-8",
        )

    repo = load_repo(mini_repo)
    manifest = build_manifest(
        repo,
        "2026-08-06T20:00:00+00:00",
    )

    nested_map = next(
        row for row in manifest["study_maps"]
        if row["id"] == study_map.id
    )
    nested_stage = next(
        row for row in nested_map["stages"]
        if row["id"] == stage_id
    )
    flat_stage = next(
        row for row in manifest["stages"]
        if row["id"] == stage_id
    )

    return repo, nested_stage["resources"], flat_stage["resources"]


def _expected_material_path(repo, material_uri):
    target = (
        repo.materials_root
        / material_uri.removeprefix("material://")
    )
    return str(
        target.resolve().relative_to(
            repo.learningos_root.resolve()
        )
    )


def _assert_projected_resource(
        repo,
        nested,
        flat,
        index,
        *,
        material_uri,
        exists):
    projected = nested[index]

    assert projected["material_uri"] == material_uri
    assert projected["material_path"] == _expected_material_path(
        repo,
        material_uri,
    )
    assert projected["material_exists"] is exists

    assert flat[index]["material_uri"] == projected["material_uri"]
    assert flat[index]["material_path"] == projected["material_path"]
    assert flat[index]["material_exists"] is projected["material_exists"]

    return projected


def test_material_resource_projection_preserves_authored_uri(mini_repo):
    material_uri = (
        "material://source-demo-book/"
        "lecture-slides/01_Introduction.pdf"
    )

    repo, nested, flat = _material_projection_fixture(
        mini_repo,
        source_material=(
            "material://source-demo-book/lecture-slides"
        ),
        resources=[{
            "source_id": "source-demo-book",
            "label": "Lecture 01",
            "locator": "lecture-slides/01_Introduction.pdf",
            "vault_path": material_uri,
        }],
        existing_files=[
            "source-demo-book/lecture-slides/01_Introduction.pdf",
        ],
    )

    projected = _assert_projected_resource(
        repo,
        nested,
        flat,
        0,
        material_uri=material_uri,
        exists=True,
    )

    assert projected["vault_path"] == material_uri
    assert "lecture-slides/lecture-slides" not in projected[
        "material_path"
    ]


def test_material_resource_projection_handles_single_file_source(
        mini_repo):
    material_uri = "material://source-demo-book/demo-book.pdf"

    repo, nested, flat = _material_projection_fixture(
        mini_repo,
        source_material=material_uri,
        resources=[{
            "source_id": "source-demo-book",
            "label": "Complete book",
            "locator": "demo-book.pdf",
            "vault_path": material_uri,
        }],
        existing_files=["source-demo-book/demo-book.pdf"],
    )

    projected = _assert_projected_resource(
        repo,
        nested,
        flat,
        0,
        material_uri=material_uri,
        exists=True,
    )

    assert projected["material_path"].endswith(
        "source-demo-book/demo-book.pdf"
    )
    assert "demo-book.pdf/demo-book.pdf" not in projected[
        "material_path"
    ]


def test_material_resource_projection_derives_file_locators(
        mini_repo):
    locators = [
        "Primer_Linear_Algebra.pdf",
        "lecture-slides/02_Regression.pdf",
        "older-lecture-slides/08_Neural_Networks.pdf",
    ]
    resources = [
        {
            "source_id": "source-demo-book",
            "label": locator,
            "locator": locator,
        }
        for locator in locators
    ]

    repo, nested, flat = _material_projection_fixture(
        mini_repo,
        source_material=(
            "material://source-demo-book/lecture-slides"
        ),
        resources=resources,
        existing_files=[
            f"source-demo-book/{locator}"
            for locator in locators
        ],
    )

    for index, locator in enumerate(locators):
        material_uri = (
            f"material://source-demo-book/{locator}"
        )
        projected = _assert_projected_resource(
            repo,
            nested,
            flat,
            index,
            material_uri=material_uri,
            exists=True,
        )
        assert projected["locator"] == locator
        assert "vault_path" not in projected


def test_material_resource_projection_ignores_descriptive_and_unsafe_locators(
        mini_repo):
    resources = [
        {
            "source_id": "source-demo-book",
            "label": "Reading guidance",
            "locator": "Chapter 9, selected sections",
        },
        {
            "source_id": "source-demo-book",
            "label": "Traversal attempt",
            "locator": "../../Job/secret.pdf",
        },
        {
            "source_id": "source-demo-book",
            "label": "Absolute path attempt",
            "locator": "/tmp/secret.pdf",
        },
    ]

    _repo, nested, flat = _material_projection_fixture(
        mini_repo,
        source_material=(
            "material://source-demo-book/lecture-slides"
        ),
        resources=resources,
    )

    for index in range(len(resources)):
        assert nested[index].get("material_uri") is None
        assert nested[index].get("material_path") is None
        assert nested[index].get("material_exists") in {
            None,
            False,
        }

        assert flat[index].get("material_uri") is None
        assert flat[index].get("material_path") is None
        assert flat[index].get("material_exists") in {
            None,
            False,
        }


def test_material_resource_projection_keeps_missing_material_nonfatal(
        mini_repo):
    locator = "lecture-slides/offline.pdf"
    material_uri = f"material://source-demo-book/{locator}"

    repo, nested, flat = _material_projection_fixture(
        mini_repo,
        source_material=(
            "material://source-demo-book/lecture-slides"
        ),
        resources=[{
            "source_id": "source-demo-book",
            "label": "Offline lecture",
            "locator": locator,
        }],
    )

    _assert_projected_resource(
        repo,
        nested,
        flat,
        0,
        material_uri=material_uri,
        exists=False,
    )


def test_material_resource_projection_uses_source_material_authority(
        mini_repo):
    """A source may intentionally delegate material identity to another ID."""
    material_uri = (
        "material://source-shared-slides/"
        "exercise-slides/UE4.pdf"
    )

    repo, nested, flat = _material_projection_fixture(
        mini_repo,
        source_material=(
            "material://source-shared-slides/exercise-slides"
        ),
        resources=[{
            "source_id": "source-demo-book",
            "label": "Shared exercise deck",
            "locator": "exercise-slides/UE4.pdf",
        }],
        existing_files=[
            "source-shared-slides/exercise-slides/UE4.pdf",
        ],
    )

    projected = _assert_projected_resource(
        repo,
        nested,
        flat,
        0,
        material_uri=material_uri,
        exists=True,
    )

    assert projected["source_id"] == "source-demo-book"
    assert projected["material_uri"].startswith(
        "material://source-shared-slides/"
    )


def test_material_resource_projection_refuses_compound_and_unsafe_uris(
        mini_repo):
    resources = [
        {
            "source_id": "source-demo-book",
            "label": "Compound locator",
            "locator": "first.pdf; second.pdf",
        },
        {
            "source_id": "source-demo-book",
            "label": "Unsafe authored URI",
            "vault_path": (
                "material://source-demo-book/"
                "../../../repository/secret.pdf"
            ),
        },
    ]

    _repo, nested, flat = _material_projection_fixture(
        mini_repo,
        source_material="material://source-demo-book",
        resources=resources,
        existing_files=[
            "source-demo-book/first.pdf",
            "source-demo-book/second.pdf",
        ],
    )

    for collection in (nested, flat):
        for resource in collection:
            assert resource.get("material_uri") is None
            assert resource.get("material_path") is None
            assert resource.get("material_exists") in {
                None,
                False,
            }
