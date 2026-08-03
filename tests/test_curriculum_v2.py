"""Module-first curriculum contract, migration, and action-specific gateway tests."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import yaml

from learning_os.genout import generate_all, write_outputs
from learning_os.loader import load_repo, parse_frontmatter
from learning_os.rules import validate

ROOT = Path(__file__).resolve().parent.parent
LOS = ROOT / "tools" / "los.py"
MIGRATE = ROOT / "tools" / "migrate_curriculum_v2.py"


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


def test_live_migration_is_idempotent_in_dry_run(repo_root):
    proc = subprocess.run([sys.executable, str(MIGRATE), "--root", str(repo_root), "--report"],
                          capture_output=True, text=True, timeout=120)
    assert proc.returncode == 0, proc.stderr
    assert "dry-run: 0 action(s)" in proc.stdout


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
