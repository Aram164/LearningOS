"""Hygiene-sweep tests (ADR-004): stale locks, stale views, unfiled files,
shadow copies. All hygiene findings are warnings — they must never produce E."""

from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path

from learning_os.loader import load_repo
from learning_os.rules import validate


def codes(issues, severity=None):
    return [i.code for i in issues if severity is None or i.severity == severity]


def run(root):
    return validate(load_repo(root))


def _git(root: Path, *args: str):
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True,
                   env={**os.environ,
                        "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
                        "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"})


# ------------------------------------------------------------------ baseline
def test_mini_repo_has_no_hygiene_warnings(mini_repo):
    hygiene = [c for c in codes(run(mini_repo)) if c.startswith("HYGIENE-")]
    assert hygiene == []


def test_hygiene_findings_are_never_errors(mini_repo):
    (mini_repo / "stray.md").write_text("x", encoding="utf-8")
    issues = run(mini_repo)
    assert "HYGIENE-UNFILED" not in codes(issues, "E")
    assert "HYGIENE-UNFILED" in codes(issues, "W")


# ---------------------------------------------------------------- stale lock
def test_stale_index_lock_warns(mini_repo):
    lockdir = mini_repo / ".git"
    lockdir.mkdir()
    lock = lockdir / "index.lock"
    lock.write_text("", encoding="utf-8")
    old = time.time() - 3600
    os.utime(lock, (old, old))
    assert "HYGIENE-LOCK" in codes(run(mini_repo), "W")


def test_fresh_index_lock_does_not_warn(mini_repo):
    lockdir = mini_repo / ".git"
    lockdir.mkdir()
    (lockdir / "index.lock").write_text("", encoding="utf-8")
    assert "HYGIENE-LOCK" not in codes(run(mini_repo))


# --------------------------------------------------------------- stale views
def test_views_absent_after_commit_warns(mini_repo):
    # generated/ exists in the fixture; empty it so the manifest is missing.
    _git(mini_repo, "init", "-q")
    _git(mini_repo, "add", "-A")
    _git(mini_repo, "commit", "-qm", "init")
    assert "HYGIENE-VIEWS" in codes(run(mini_repo), "W")


def test_views_older_than_head_warn(mini_repo):
    _git(mini_repo, "init", "-q")
    _git(mini_repo, "add", "-A")
    _git(mini_repo, "commit", "-qm", "init")
    manifest = mini_repo / "generated" / "manifest.json"
    manifest.write_text("{}", encoding="utf-8")
    old = time.time() - 3600
    os.utime(manifest, (old, old))
    assert "HYGIENE-VIEWS" in codes(run(mini_repo), "W")


def test_fresh_views_do_not_warn(mini_repo):
    _git(mini_repo, "init", "-q")
    _git(mini_repo, "add", "-A")
    _git(mini_repo, "commit", "-qm", "init")
    from learning_os.genout import generate_all, write_outputs
    from learning_os.loader import load_repo
    repo = load_repo(mini_repo)
    write_outputs(repo, generate_all(repo, generated_at="T1"))
    assert "HYGIENE-VIEWS" not in codes(run(mini_repo))


# ------------------------------------------------------------- unfiled files
def test_loose_md_locations_warn(mini_repo):
    (mini_repo / "knowledge" / "loose.md").write_text("x", encoding="utf-8")
    (mini_repo / "work" / "plan.md").write_text("x", encoding="utf-8")
    (mini_repo / "records" / "notes.md").write_text("x", encoding="utf-8")
    warns = [i for i in run(mini_repo) if i.code == "HYGIENE-UNFILED"]
    assert len(warns) == 3


def test_workspace_file_beside_context_warns(mini_repo):
    ws = mini_repo / "work" / "active" / "workspace-demo"  # exists in fixture
    (ws / "scratch").mkdir(parents=True, exist_ok=True)
    (ws / "loose-notes.md").write_text("x", encoding="utf-8")
    (ws / "scratch" / "anything.md").write_text("x", encoding="utf-8")  # legal
    warns = [i for i in run(mini_repo) if i.code == "HYGIENE-UNFILED"]
    assert len(warns) == 1
    assert "loose-notes.md" in warns[0].path


def test_inbox_and_garden_are_exempt(mini_repo):
    (mini_repo / "work" / "inbox" / "whatever this is.md").write_text("x", encoding="utf-8")
    garden = mini_repo / "knowledge" / "garden"
    garden.mkdir()
    (garden / "half-formed-idea.md").write_text("x", encoding="utf-8")
    assert "HYGIENE-UNFILED" not in codes(run(mini_repo))


# ------------------------------------------------------------- shadow copies
def _add_note(root: Path, note_id: str = "note-demo-topic"):
    p = root / "knowledge" / "notes" / "mathematics" / f"{note_id}.md"
    p.write_text(
        f"---\nid: {note_id}\ntype: note\ntitle: Demo\ncreated: '2026-08-01'\n"
        "role: reference\nstate: evolving\nauthorship: user\n"
        "concepts: [concept-expected-value]\n---\n\n# Demo\n", encoding="utf-8")
    return p


def test_shadow_edited_after_canon_warns(mini_repo):
    note = _add_note(mini_repo)
    old = time.time() - 7200
    os.utime(note, (old, old))
    shadow_dir = mini_repo.parent.parent / "legacy" / "Plans"
    shadow_dir.mkdir(parents=True)
    (shadow_dir / "Demo_Topic.md").write_text("newer twin", encoding="utf-8")
    assert "HYGIENE-SHADOW" in codes(run(mini_repo), "W")


def test_older_shadow_does_not_warn(mini_repo):
    _add_note(mini_repo)  # canon mtime = now
    shadow_dir = mini_repo.parent.parent / "legacy" / "Plans"
    shadow_dir.mkdir(parents=True)
    shadow = shadow_dir / "Demo_Topic.md"
    shadow.write_text("frozen twin", encoding="utf-8")
    old = time.time() - 7200
    os.utime(shadow, (old, old))
    assert "HYGIENE-SHADOW" not in codes(run(mini_repo))


def test_unrelated_shadow_names_do_not_warn(mini_repo):
    _add_note(mini_repo)
    shadow_dir = mini_repo.parent.parent / "Job" / "workspace-job-deem" / "inputs"
    shadow_dir.mkdir(parents=True)
    (shadow_dir / "Totally-Different.md").write_text("x", encoding="utf-8")
    assert "HYGIENE-SHADOW" not in codes(run(mini_repo))
