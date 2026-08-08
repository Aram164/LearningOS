"""Learning-path workflow, contract versioning, and guarded writes."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import yaml

from learning_os.genout import generate_all, write_outputs
from learning_os.loader import load_repo
from learning_os.rules import validate

LOS = Path(__file__).resolve().parent.parent / "tools" / "los.py"


def run_los(root: Path, *args: str):
    return subprocess.run(
        [sys.executable, str(LOS), "--root", str(root), *args],
        capture_output=True, text=True, timeout=120)


def add_path(root: Path) -> Path:
    ws = root / "work" / "active" / "workspace-demo"
    path_file = ws / "paths" / "path-demo-probability.yaml"
    path_file.parent.mkdir(parents=True)
    path_file.write_text(yaml.safe_dump({
        "id": "path-demo-probability",
        "type": "learning-path",
        "title": "Demo probability",
        "workspace_id": "workspace-demo",
        "area": "university",
        "module_id": "module-demo",
        "status": "active",
        "current_stage": "stage-one",
        "created": "2026-08-03",
        "stages": [
            {"id": "stage-one", "title": "One", "status": "active",
             "objective": "Do one.", "concepts": ["concept-expected-value"],
             "resources": [{"kind": "read", "label": "Demo Book",
                            "source_id": "source-demo-book"}],
             "done_when": ["Explain one."],
             "notes_path": "work/active/workspace-demo/scratch/paths/"
                           "path-demo-probability/stage-one.md"},
            {"id": "stage-two", "title": "Two", "status": "pending",
             "objective": "Do two.", "done_when": ["Explain two."],
             "notes_path": "work/active/workspace-demo/scratch/paths/"
                           "path-demo-probability/stage-two.md"},
        ],
    }, sort_keys=False), encoding="utf-8")
    return path_file


def test_path_loads_validates_and_projects_stage_notes(mini_repo):
    add_path(mini_repo)
    repo = load_repo(mini_repo)
    assert "path-demo-probability" in repo.learning_paths
    assert not [i for i in validate(repo) if i.severity == "E"]

    note = mini_repo / "work/active/workspace-demo/scratch/paths/" \
        "path-demo-probability/stage-one.md"
    note.parent.mkdir(parents=True)
    note.write_text("My uncertain derivation.\n", encoding="utf-8")
    manifest = json.loads(generate_all(load_repo(mini_repo), "T1")["manifest.json"])
    path_rec = next(r for r in manifest["records"] if r["id"] == "path-demo-probability")
    assert path_rec["stages"][0]["notes_text"] == "My uncertain derivation.\n"
    assert manifest["_generated"]["contract_version"] == 3
    assert manifest["_generated"]["snapshot_id"].startswith("sha256:")
    assert "concept_to_notes" in manifest["backlinks"]


def test_path_note_uses_snapshot_guard_and_atomic_projection(mini_repo):
    add_path(mini_repo)
    repo = load_repo(mini_repo)
    write_outputs(repo, generate_all(repo, "T1"))
    manifest = json.loads((mini_repo / "generated/manifest.json").read_text(encoding="utf-8"))
    snapshot = manifest["_generated"]["snapshot_id"]

    proc = run_los(mini_repo, "path-note", "path-demo-probability", "stage-one",
                   "--replace", "--text", "My own reasoning.",
                   "--expected-snapshot", snapshot)
    assert proc.returncode == 0, proc.stderr
    updated = json.loads((mini_repo / "generated/manifest.json").read_text(encoding="utf-8"))
    path_rec = next(r for r in updated["records"] if r["id"] == "path-demo-probability")
    assert path_rec["stages"][0]["notes_text"] == "My own reasoning.\n"
    assert updated["_generated"]["snapshot_id"] != snapshot
    assert not list((mini_repo / "generated").glob(".*.tmp"))

    stale = run_los(mini_repo, "path-note", "path-demo-probability", "stage-one",
                    "--replace", "--text", "Would overwrite newer work.",
                    "--expected-snapshot", snapshot)
    assert stale.returncode == 3
    assert "projection conflict" in stale.stderr


def test_complete_stage_advances_and_last_stage_opens_shelving(mini_repo):
    add_path(mini_repo)
    first = run_los(mini_repo, "path-progress", "path-demo-probability", "stage-one",
                    "complete")
    assert first.returncode == 0, first.stderr
    data = yaml.safe_load((mini_repo / "work/active/workspace-demo/paths/"
                           "path-demo-probability.yaml").read_text(encoding="utf-8"))
    assert data["current_stage"] == "stage-two"
    assert [s["status"] for s in data["stages"]] == ["complete", "active"]

    second = run_los(mini_repo, "path-progress", "path-demo-probability", "stage-two",
                     "complete")
    assert second.returncode == 0, second.stderr
    data = yaml.safe_load((mini_repo / "work/active/workspace-demo/paths/"
                           "path-demo-probability.yaml").read_text(encoding="utf-8"))
    assert data["status"] == "ready-to-shelve"
    assert data["shelving"]["state"] == "draft"


def test_machine_bootstrap_discovers_contract_and_path(mini_repo):
    add_path(mini_repo)
    proc = run_los(mini_repo, "bootstrap")
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["capabilities"]["contract_version"] == 2
    assert payload["capabilities"]["rules"]["shelving_requires_explicit_approval"]
    assert payload["active_study_maps"] == []
    assert payload["resume_pointer"] == {}
