"""Hygiene-sweep tests for the canonical repository only.

The external Legacy tree is a deliberate boundary and must never be
enumerated by normal validation.
"""

from __future__ import annotations

import builtins
import io
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
    _git(mini_repo, "init", "-q")
    lock = lockdir / "index.lock"
    lock.write_text("", encoding="utf-8")
    old = time.time() - 3600
    os.utime(lock, (old, old))
    assert "HYGIENE-LOCK" in codes(run(mini_repo), "W")


def test_fresh_index_lock_does_not_warn(mini_repo):
    lockdir = mini_repo / ".git"
    _git(mini_repo, "init", "-q")
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


def _add_note(root: Path, note_id: str = "note-demo-topic"):
    p = root / "knowledge" / "notes" / "mathematics" / f"{note_id}.md"
    p.write_text(
        f"---\nid: {note_id}\ntype: note\ntitle: Demo\ncreated: '2026-08-01'\n"
        "role: reference\nstate: evolving\nauthorship: user\n"
        "concepts: [concept-expected-value]\n---\n\n# Demo\n", encoding="utf-8")
    return p


def test_normal_validation_never_touches_external_legacy(mini_repo, monkeypatch):
    """Normal validation cannot even stat or enumerate Legacy.

    The sentinel is deliberately lower-level than the hygiene implementation:
    a future rule that tries a different ``Path`` helper still reaches either
    ``stat`` or ``scandir`` and fails the test before observing boundary data.
    """
    _add_note(mini_repo)

    real_builtin_open = builtins.open
    real_io_open = io.open
    real_os_open = os.open
    real_listdir = os.listdir
    real_lstat = os.lstat
    real_stat = os.stat
    real_scandir = os.scandir

    def refuse_legacy(value):
        if isinstance(value, (str, bytes, os.PathLike)):
            parts = Path(os.fsdecode(value)).parts
            forbidden = {"legacy"}.intersection(parts)
            if forbidden:
                name = sorted(forbidden)[0]
                raise AssertionError(
                    f"normal validation attempted to access {name}"
                )

    def guarded_stat(path, *args, **kwargs):
        refuse_legacy(path)
        return real_stat(path, *args, **kwargs)

    def guarded_lstat(path, *args, **kwargs):
        refuse_legacy(path)
        return real_lstat(path, *args, **kwargs)

    def guarded_scandir(path="."):
        refuse_legacy(path)
        return real_scandir(path)

    def guarded_listdir(path="."):
        refuse_legacy(path)
        return real_listdir(path)

    def guarded_builtin_open(file, *args, **kwargs):
        refuse_legacy(file)
        return real_builtin_open(file, *args, **kwargs)

    def guarded_io_open(file, *args, **kwargs):
        refuse_legacy(file)
        return real_io_open(file, *args, **kwargs)

    def guarded_os_open(path, *args, **kwargs):
        refuse_legacy(path)
        return real_os_open(path, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", guarded_builtin_open)
    monkeypatch.setattr(io, "open", guarded_io_open)
    monkeypatch.setattr(os, "open", guarded_os_open)
    monkeypatch.setattr(os, "listdir", guarded_listdir)
    monkeypatch.setattr(os, "lstat", guarded_lstat)
    monkeypatch.setattr(os, "stat", guarded_stat)
    monkeypatch.setattr(os, "scandir", guarded_scandir)

    run(mini_repo)
