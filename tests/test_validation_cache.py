"""Status validation cache (#103): warm/cold identity, pin misses, live
advisories on hits, --no-validate shape, and the validate.py refresh rules."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

import pytest
from repo_builders import run_los

import learning_os.validation_cache as vc
from learning_os.genout import generate_all, write_outputs
from learning_os.loader import load_repo
from learning_os.rules import validate
from learning_os.rules.advisories import NEGLECT_GIT_HISTORY_PREFIX
from learning_os.rules.common import Issue

CACHE = vc.CACHE_RELATIVE


def _validation(proc):
    assert proc.returncode in (0, 1), proc.stderr
    return json.loads(proc.stdout)["validation"]


# ------------------------------------------------- warm/cold transparency
def test_status_memoizes_and_reuses_cache_byte_identical(mini_repo):
    cold = run_los(mini_repo, "status", "--json")
    assert cold.returncode == 0, cold.stderr
    assert (mini_repo / CACHE).is_file()
    warm = run_los(mini_repo, "status", "--json")
    assert warm.returncode == 0, warm.stderr
    assert warm.stdout == cold.stdout


def test_status_issues_serves_static_from_cache_without_validating(
    mini_repo, monkeypatch,
):
    """The hit path never calls the validator (it would raise here)."""
    live = validate(load_repo(mini_repo), online=False)
    vc.write_static_cache(mini_repo, live)

    def _boom(*args, **kwargs):
        raise AssertionError("cache hit must not re-validate")

    monkeypatch.setattr(vc, "validate", _boom)
    served = vc.status_issues(load_repo(mini_repo))
    # Same multiset (advisories splice at the end; status counts only).
    assert Counter(str(i) for i in served) == Counter(str(i) for i in live)


def test_rename_note_invalidates_cache(mini_repo):
    first = run_los(mini_repo, "status", "--json")
    assert _validation(first)["errors"] == 0
    note = mini_repo / "knowledge/notes/mathematics/note-demo.md"
    note.rename(note.with_name("renamed-demo.md"))
    second = run_los(mini_repo, "status", "--json")
    assert second.returncode == 1, second.stderr
    assert _validation(second)["errors"] == 1
    # The miss re-memoized: the error persists through the next hit too.
    third = run_los(mini_repo, "status", "--json")
    assert third.returncode == 1, third.stderr
    assert _validation(third)["errors"] == 1


# ------------------------------------------------------- live advisories
def test_mtime_only_inbox_aging_is_served_live_on_a_hit(mini_repo):
    """Pins hash bytes, not mtimes: aging is invisible to the pins, so the
    read hits — and the fresh INBOX-STALE on it proves advisories recompute."""
    drop = mini_repo / "work/inbox/drop.md"
    drop.write_text("unrouted capture\n", encoding="utf-8")
    vc.status_issues(load_repo(mini_repo))  # warm
    assert vc.read_cached_static_issues(mini_repo) is not None
    past = time.time() - 16 * 86400
    os.utime(drop, (past, past))
    issues = vc.status_issues(load_repo(mini_repo))
    assert any(i.code == "INBOX-STALE" and "drop.md" in i.message
               for i in issues)
    # Pins still match: that warning came from the live splice, not a miss.
    assert vc.read_cached_static_issues(mini_repo) is not None


def test_writer_filters_live_advisories_and_splice_keeps_hygiene(mini_repo):
    """The writer is the one choke point: live advisories never persist,
    while hygiene's unrelated GIT-HISTORY (no neglect prefix) is static."""
    issues = [
        Issue("E", "FILE-NAME", "note file mismatch", "knowledge/notes/x.md"),
        Issue("W", "WS-COUNT", "too many workspaces", ""),
        Issue("W", "WS-NEGLECT", "workspace untouched", ""),
        Issue("W", "INBOX-STALE", "inbox item old", ""),
        Issue("E", "GIT-HISTORY", f"{NEGLECT_GIT_HISTORY_PREFIX}boom", ""),
        Issue("E", "GIT-HISTORY", "stale lock file", "operations/"),
    ]
    vc.write_static_cache(mini_repo, issues)
    cached = vc.read_cached_static_issues(mini_repo)
    assert cached is not None
    assert [(i.severity, i.code, i.message, i.path) for i in cached] == [
        ("E", "FILE-NAME", "note file mismatch", "knowledge/notes/x.md"),
        ("W", "WS-COUNT", "too many workspaces", ""),
        ("E", "GIT-HISTORY", "stale lock file", "operations/"),
    ]


# ------------------------------------------------------------------ misses
def test_materials_addition_misses(mini_repo):
    vc.write_static_cache(mini_repo, validate(load_repo(mini_repo), online=False))
    assert vc.read_cached_static_issues(mini_repo) is not None
    materials = mini_repo.parent / "materials"
    (materials / "new-deck.pdf").write_bytes(b"%PDF-1.4 fresh bytes\n")
    assert vc.read_cached_static_issues(mini_repo) is None


def test_garbage_cache_misses_discards_and_leaves_no_phantom(mini_repo):
    cache = mini_repo / CACHE
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_bytes(b"\x00\xff not json {{{")
    assert vc.read_cached_static_issues(mini_repo) is None
    assert not cache.exists()
    # End to end: garbage never surfaces as a GEN-JSON error about the
    # cache itself, and the miss rewrites a valid cache.
    cache.write_bytes(b"\x00\xff not json {{{")
    proc = run_los(mini_repo, "status", "--json")
    assert proc.returncode == 0, proc.stderr
    assert _validation(proc)["errors"] == 0
    assert vc.read_cached_static_issues(mini_repo) is not None
    again = run_los(mini_repo, "status", "--json")
    assert again.stdout == proc.stdout


def _republish_views(root: Path) -> None:
    repo = load_repo(root)
    write_outputs(repo, generate_all(repo))


@pytest.mark.parametrize("mutation, code", [
    # A stray file in generated/: the GEN-* checks read generated/, which
    # no content pin covers.
    (lambda root: (root / "generated/stray.txt").write_text("x\n", encoding="utf-8"),
     "GEN-UNKNOWN"),
    # An unparseable receipt: receipts sit beside the pinned revision
    # ledger, not inside it.
    (lambda root: (root / "operations/transactions").mkdir(parents=True, exist_ok=True)
     or (root / "operations/transactions/transaction-x.yaml").write_text(
         "id: [unclosed\n", encoding="utf-8"),
     "TRANSACTION-RECEIPT"),
], ids=["generated-stray", "unparseable-receipt"])
def test_non_canonical_validator_input_misses(mini_repo, mutation, code):
    vc.status_issues(load_repo(mini_repo))  # warm
    assert vc.read_cached_static_issues(mini_repo) is not None
    mutation(mini_repo)
    assert vc.read_cached_static_issues(mini_repo) is None
    issues = vc.status_issues(load_repo(mini_repo))
    assert any(i.code == code for i in issues), issues


def test_make_views_clears_a_cached_stale_views_warning(mini_repo):
    """The reported case: a hand edit makes the published views stale
    (HYGIENE-VIEWS), `make views` republishes them with no canonical
    change, and status must drop the warning instead of serving it."""
    _republish_views(mini_repo)
    baseline = _validation(run_los(mini_repo, "status", "--json"))
    note = mini_repo / "knowledge/notes/mathematics/note-demo.md"
    note.write_text(note.read_text(encoding="utf-8") + "\nA hand edit.\n",
                    encoding="utf-8")
    stale = _validation(run_los(mini_repo, "status", "--json"))
    assert stale["warnings"] == baseline["warnings"] + 1
    _republish_views(mini_repo)
    after = _validation(run_los(mini_repo, "status", "--json"))
    assert after == baseline
    uncached = validate(load_repo(mini_repo), online=False)
    assert after["warnings"] == sum(1 for i in uncached if i.severity == "W")


def test_stale_index_lock_is_served_live_on_a_hit(mini_repo):
    """HYGIENE-LOCK is clock-derived: a lock that ages past the threshold
    with no other change must appear on a cache hit."""
    subprocess.run(["git", "init", "-q", str(mini_repo)], check=True)
    lock = mini_repo / ".git" / "index.lock"
    lock.write_text("", encoding="utf-8")
    vc.status_issues(load_repo(mini_repo))  # warm, lock still fresh
    assert vc.read_cached_static_issues(mini_repo) is not None
    past = time.time() - 3600
    os.utime(lock, (past, past))
    issues = vc.status_issues(load_repo(mini_repo))
    assert any(i.code == "HYGIENE-LOCK" for i in issues), issues
    assert vc.read_cached_static_issues(mini_repo) is not None
    cached = vc.read_cached_static_issues(mini_repo)
    assert not any(i.code == "HYGIENE-LOCK" for i in cached)


def test_pins_are_observed_before_validation(mini_repo, monkeypatch):
    """status holds no lock: a write landing while the validator runs must
    leave a cache that misses, never one vouching for the post-write state
    with the pre-write issues."""
    note = mini_repo / "knowledge/notes/mathematics/note-demo.md"
    real = vc.validate

    def racing(repo, online=False):
        issues = real(repo, online=online)
        note.rename(note.with_name("renamed-demo.md"))  # lands mid-run
        return issues

    monkeypatch.setattr(vc, "validate", racing)
    first = vc.status_issues(load_repo(mini_repo))
    assert not any(i.severity == "E" for i in first)
    monkeypatch.setattr(vc, "validate", real)
    assert vc.read_cached_static_issues(mini_repo) is None
    proc = run_los(mini_repo, "status", "--json")
    assert _validation(proc)["errors"] == 1


# ------------------------------------------------------------- no-validate
def test_no_validate_shape(mini_repo):
    text = run_los(mini_repo, "status", "--no-validate")
    assert text.returncode == 0, text.stderr
    assert "validation: skipped (--no-validate)" in text.stdout
    payload = run_los(mini_repo, "status", "--json", "--no-validate")
    assert payload.returncode == 0, payload.stderr
    assert json.loads(payload.stdout)["validation"] == {"skipped": True}


@pytest.mark.parametrize("flag", [[], ["--json"]])
def test_no_validate_refusal_still_first(mini_repo, flag):
    concepts = mini_repo / "knowledge/concepts.yaml"
    concepts.write_text(
        concepts.read_text(encoding="utf-8") + "\nbroken: [unclosed\n",
        encoding="utf-8")
    proc = run_los(mini_repo, "status", "--no-validate", *flag)
    assert proc.returncode == 2, proc.stderr
    assert "knowledge/concepts.yaml" in proc.stderr
    assert not proc.stdout


# ------------------------------------------------- validate.py refresh rules
def _run_validate(repo_root: Path, mini_repo: Path, *args: str):
    script = repo_root / "tools" / "validate.py"
    return subprocess.run(
        [sys.executable, str(script), "--root", str(mini_repo), *args],
        text=True, capture_output=True, timeout=120)


def test_validate_offline_writes_cache_with_header_and_pins(mini_repo, repo_root):
    cache = mini_repo / CACHE
    assert not cache.exists()
    proc = _run_validate(repo_root, mini_repo)
    assert proc.returncode == 0, proc.stderr
    data = json.loads(cache.read_text(encoding="utf-8"))
    assert isinstance(data["_generated"], dict)  # GEN-HEADER
    assert data["format"] == 3
    assert set(data["pins"]) == {
        "canonical_fingerprint", "code_identity", "runtime_digest",
        "materials_digest", "operations_digest", "validator_inputs",
    }
    assert isinstance(data["issues"], list)
    assert vc.read_cached_static_issues(mini_repo) is not None


def test_validate_online_never_writes_cache(mini_repo, repo_root):
    cache = mini_repo / CACHE
    assert not cache.exists()
    proc = _run_validate(repo_root, mini_repo, "--online")
    assert proc.returncode == 0, proc.stderr
    assert not cache.exists()
