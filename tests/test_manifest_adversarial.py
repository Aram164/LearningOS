"""Adversarial manifest proof: the cache trust boundary (F1–F6, G1–G3).

The mutation matrix proves locality under normal edits; these tests
attack the boundary the matrix assumes away — malformed canonical
state, a repo loaded from torn bytes, code and runtime drift, stale git
observations, executing-tree drift, format-provider drift, and
internally consistent but wrong cache entries. Each test names the
finding it closes.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from repo_builders import curriculum_mini, stage_manifest_producers

import learning_os.derived.identity as identity_module
import learning_os.genout.manifest_derived as shadow_module
from learning_os import githistory
from learning_os.contracts.manifest_contract import declared_version
from learning_os.derived.identity import canonical_snapshot_digest, digest_bytes
from learning_os.derived.store import (
    canonical_bytes,
    derived_dir,
    read_state,
)
from learning_os.errors import TransactionFailure
from learning_os.genout.concepts import build_backlinks
from learning_os.genout.manifest import build_manifest
from learning_os.genout.manifest_derived import (
    VALIDATION_PROOF_ID,
    build_manifest_shadow,
    compare_shadow_manifest,
    contract_closure_digest,
    serialize_manifest,
)
from learning_os.loader import load_repo

REPO_ROOT = Path(__file__).resolve().parent.parent
GENERATE = REPO_ROOT / "tools" / "generate.py"
STAMP = "2026-09-20T00:00:00+02:00"

NOTE = "knowledge/notes/mathematics/note-demo.md"
BAD_YAML = "---\n: : : not valid yaml [[[\n"
BAD_FRONTMATTER = "---\nid: [unclosed\ntitle: Demo\n---\n\nBody.\n"

#: domain -> (file, corrupting bytes). Every corruption must load with
#: parse failures recorded (never raise): that is the shape F1 guards.
MALFORMED = {
    "note": (NOTE, BAD_FRONTMATTER),
    "source": ("sources/sources.yaml", BAD_YAML),
    "module": ("curriculum/modules/module-demo/module.yaml", BAD_YAML),
    "unit": ("curriculum/modules/module-demo/units/unit-demo-l01/unit.yaml", BAD_YAML),
    "study-map": (
        "curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml",
        BAD_YAML,
    ),
    "workspace": ("work/active/workspace-demo/CONTEXT.md", BAD_FRONTMATTER),
    "concepts": ("knowledge/concepts.yaml", BAD_YAML),
}


def _warmed(tmp_path: Path) -> Path:
    mini = curriculum_mini(tmp_path)
    repo = load_repo(mini)
    stage_manifest_producers(mini, repo)
    assert compare_shadow_manifest(repo, STAMP).equivalent
    return mini


def _derived_snapshot(mini: Path):
    blobs = derived_dir(mini) / "blobs"
    return (
        read_state(mini),
        sorted(p.name for p in blobs.iterdir()) if blobs.is_dir() else [],
    )


# F1. Malformed canonical state refuses identically, caching nothing.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("domain", sorted(MALFORMED))
def test_malformed_domain_refuses_before_any_caching(tmp_path: Path, domain: str):
    mini = _warmed(tmp_path)
    rel, bad = MALFORMED[domain]
    (mini / rel).write_text(bad, encoding="utf-8")
    assert load_repo(mini).parse_failures, domain
    before = _derived_snapshot(mini)
    assert VALIDATION_PROOF_ID in before[0], "warmed state must hold a proof"

    repo = load_repo(mini)
    with pytest.raises(TransactionFailure) as legacy_exc:
        build_manifest(repo, STAMP, None)
    with pytest.raises(TransactionFailure) as shadow_exc:
        build_manifest_shadow(repo, STAMP)
    assert str(shadow_exc.value) == str(legacy_exc.value)
    # The refusal landed before any derived evaluation or cache
    # mutation: no proof, no payload, no blob may have moved.
    assert _derived_snapshot(mini) == before


# F2. The snapshot transaction: races retry, torn bytes never commit.
# ---------------------------------------------------------------------------


def _retitle(mini: Path, title: str) -> None:
    note = mini / NOTE
    text = note.read_text(encoding="utf-8")
    assert "title: Demo note" in text or "title: " in text
    lines = text.splitlines(keepends=True)
    for index, line in enumerate(lines[:20]):
        if line.startswith("title: "):
            lines[index] = f"title: {title}\n"
            break
    note.write_text("".join(lines), encoding="utf-8")


def test_load_window_race_retries_and_builds_fresh(tmp_path: Path, monkeypatch):
    """An edit landing between load and hashing reloads (F2, class 2)."""
    mini = _warmed(tmp_path)
    real_load = shadow_module.load_repo
    calls: list[str] = []

    def racing_load(root: Path):
        repo = real_load(root)
        calls.append("load")
        if len(calls) == 1:
            _retitle(mini, "Raced title")
        return repo

    monkeypatch.setattr(shadow_module, "load_repo", racing_load)
    shadow = build_manifest_shadow(load_repo(mini), STAMP)
    assert len(calls) == 2  # S0 != S1 forced exactly one reload
    assert "Raced title" in serialize_manifest(shadow)
    # The committed state is fresh-consistent: a stable rerun hits all
    # nodes and still matches the legacy bytes exactly.
    trace: list = []
    assert compare_shadow_manifest(load_repo(mini), STAMP, trace=trace).equivalent
    assert all(event.status == "hit" for event in trace)


def test_eval_window_race_discards_the_staging(tmp_path: Path, monkeypatch):
    """An edit landing during evaluation commits nothing stale (F2, class 3)."""
    mini = _warmed(tmp_path)
    real_evaluate_many = shadow_module.evaluate_many
    real_commit = shadow_module.commit_staging
    commits: list[int] = []
    mutated = False

    def racing_evaluate_many(*args, **kwargs):
        nonlocal mutated
        results = real_evaluate_many(*args, **kwargs)
        if not mutated:
            mutated = True
            _retitle(mini, "Mid-eval title")
        return results

    def counting_commit(root: Path, staging) -> None:
        commits.append(len(staging.pending))
        return real_commit(root, staging)

    monkeypatch.setattr(shadow_module, "evaluate_many", racing_evaluate_many)
    monkeypatch.setattr(shadow_module, "commit_staging", counting_commit)
    shadow = build_manifest_shadow(load_repo(mini), STAMP)
    assert len(commits) == 1  # the torn attempt never committed
    assert "Mid-eval title" in serialize_manifest(shadow)
    trace: list = []
    assert compare_shadow_manifest(load_repo(mini), STAMP, trace=trace).equivalent
    assert all(event.status == "hit" for event in trace)


def test_persistently_moving_tree_refuses_without_caching(tmp_path: Path, monkeypatch):
    mini = _warmed(tmp_path)
    before = _derived_snapshot(mini)
    real_load = shadow_module.load_repo
    calls: list[str] = []

    def moving_load(root: Path):
        repo = real_load(root)
        calls.append("load")
        note = mini / NOTE
        note.write_text(
            note.read_text(encoding="utf-8") + f"\nRace {len(calls)}.\n",
            encoding="utf-8",
        )
        return repo

    monkeypatch.setattr(shadow_module, "load_repo", moving_load)
    with pytest.raises(TransactionFailure, match="changed during"):
        build_manifest_shadow(load_repo(mini), STAMP)
    assert len(calls) == shadow_module.SNAPSHOT_ATTEMPTS
    assert _derived_snapshot(mini) == before


def test_stale_passed_repo_cannot_enter_the_pipeline(tmp_path: Path):
    """The shadow loads inside its own window; the argument is not trusted."""
    mini = _warmed(tmp_path)
    stale = load_repo(mini)
    _retitle(mini, "Fresh title")
    shadow = build_manifest_shadow(stale, STAMP)
    fresh_repo = load_repo(mini)
    legacy = build_manifest(fresh_repo, STAMP, build_backlinks(fresh_repo, STAMP))
    assert serialize_manifest(shadow) == serialize_manifest(legacy)


# F3. Producer identity is the whole Core tree, in any process.
# ---------------------------------------------------------------------------


def _run_generate(mini: Path, *args: str):
    return subprocess.run(
        [sys.executable, str(GENERATE), "--root", str(mini), *args],
        capture_output=True, text=True, timeout=300,
    )


def test_new_process_code_change_hits_nothing(tmp_path: Path):
    """Warm here, edit staged common.py, rerun in a subprocess (F3, class 4).

    common.py is undeclared by the learning-path and study-map nodes;
    under whole-tree identity the edit still invalidates everything,
    and the digest is stable across processes (no hit, no fork).
    """
    mini = _warmed(tmp_path)
    staged = mini / "tools/learning_os/genout/common.py"
    staged.write_text(staged.read_text(encoding="utf-8") + "\n# probe\n",
                      encoding="utf-8")
    result = _run_generate(mini, "--shadow-manifest", "--json")
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["equivalent"] is True
    assert report["nodes"]
    # Nothing hits: the code edit invalidated every key. The proof's
    # output differs only because the subprocess stamps its own
    # generated_at, which is part of the proven bytes.
    assert all(node["status"] == "rebuilt" for node in report["nodes"].values())
    for node_id, node in report["nodes"].items():
        assert node["output_changed"] == (node_id == VALIDATION_PROOF_ID), node_id


def test_loader_orchestration_change_invalidates(tmp_path: Path):
    """loading/__init__.py is undeclared anywhere yet still covered (class 5)."""
    mini = _warmed(tmp_path)
    staged = mini / "tools/learning_os/loading/__init__.py"
    staged.write_text(staged.read_text(encoding="utf-8") + "\n# probe\n",
                      encoding="utf-8")
    trace: list = []
    assert compare_shadow_manifest(load_repo(mini), STAMP, trace=trace).equivalent
    assert trace
    assert all(event.status == "rebuilt" for event in trace)
    assert all(event.reason == "node-key-changed-output-same" for event in trace)


# F4. Runtime drift invalidates validation proofs.
# ---------------------------------------------------------------------------


def test_runtime_change_reruns_validation(tmp_path: Path, monkeypatch):
    mini = _warmed(tmp_path)

    def fake_components():
        return (
            ("python", "9.9.9-fake"),
            ("PyYAML", "0"),
            ("jsonschema", "0"),
            ("referencing", "0"),
            ("learningos-core", "0"),
        )

    monkeypatch.setattr(
        identity_module, "_runtime_components", fake_components)
    calls = 0
    real_enforce = shadow_module.enforce

    def counting(payload, root):
        nonlocal calls
        calls += 1
        return real_enforce(payload, root)

    monkeypatch.setattr(shadow_module, "enforce", counting)
    trace: list = []
    assert compare_shadow_manifest(load_repo(mini), STAMP, trace=trace).equivalent
    assert trace
    assert all(event.status == "rebuilt" for event in trace)
    assert calls == 1


# F5. A wrong proof is rejected even when the key hits.
# ---------------------------------------------------------------------------


def test_consistent_but_wrong_proof_is_rejected(tmp_path: Path, monkeypatch):
    mini = _warmed(tmp_path)
    state_path = derived_dir(mini) / "state-v1.json"
    doc = json.loads(state_path.read_text(encoding="utf-8"))
    forged = {
        "valid": True,
        "contract_version": declared_version(mini),
        "manifest_sha256": "0" * 64,  # structurally valid, semantically wrong
        "contract_closure_sha256": contract_closure_digest(mini),
    }
    blob_bytes = canonical_bytes(forged)
    blob_digest = hashlib.sha256(blob_bytes).hexdigest()
    (derived_dir(mini) / "blobs" / blob_digest).write_bytes(blob_bytes)
    # Keep the entry's node key so the engine reports a hit; only the
    # certified bytes are wrong.
    doc["nodes"][VALIDATION_PROOF_ID]["output_sha256"] = blob_digest
    doc["nodes"][VALIDATION_PROOF_ID]["blob"] = f"blobs/{blob_digest}"
    state_path.write_text(json.dumps(doc, sort_keys=True), encoding="utf-8")

    calls = 0
    real_enforce = shadow_module.enforce

    def counting(payload, root):
        nonlocal calls
        calls += 1
        return real_enforce(payload, root)

    monkeypatch.setattr(shadow_module, "enforce", counting)
    trace: list = []
    shadow = build_manifest_shadow(load_repo(mini), STAMP, trace=trace)
    assert calls == 1  # the wrong proof did not skip the validator
    assert compare_shadow_manifest(load_repo(mini), STAMP).equivalent
    healed = json.loads(
        (derived_dir(mini) / read_state(mini)[VALIDATION_PROOF_ID].blob
         ).read_text(encoding="utf-8"))
    assert healed["manifest_sha256"] == digest_bytes(canonical_bytes(shadow))


# G1a. Git/history observations are snapshot-bound.
# ---------------------------------------------------------------------------

#: Fixed commit dates: the H0/H1 day boundary is what makes a stale git
#: table observationally different from a fresh one.
GIT_H0_WHEN = "2020-01-02T03:04:05+00:00"
GIT_H1_WHEN = "2020-06-03T04:05:06+00:00"
GIT_H0_DAY = "2020-01-02"
GIT_H1_DAY = "2020-06-03"

#: Stage working note: the mini's git-visible surface (notes_updated).
WORKING_NOTE = (
    "curriculum/modules/module-demo/units/unit-demo-l01/"
    "stages/stage-demo/notes.md"
)


@pytest.fixture(autouse=True)
def _isolated_git_caches(monkeypatch):
    for name in ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR"):
        monkeypatch.delenv(name, raising=False)
    githistory.last_commit_dates.cache_clear()
    githistory.last_commit_timestamps.cache_clear()
    yield
    githistory.last_commit_dates.cache_clear()
    githistory.last_commit_timestamps.cache_clear()


def _git(mini: Path, *args: str, when: str = GIT_H0_WHEN) -> str:
    env = {**os.environ, "GIT_AUTHOR_DATE": when, "GIT_COMMITTER_DATE": when}
    return subprocess.run(
        ["git", "-c", "user.name=Test User", "-c", "user.email=test@example.com",
         "-c", "commit.gpgsign=false", *args],
        cwd=mini, check=True, capture_output=True, text=True, env=env,
    ).stdout.strip()


def _git_mini(tmp_path: Path, *, warm: bool) -> Path:
    """A staged mini committed at H0, optionally warmed by one compare."""
    if shutil.which("git") is None:
        pytest.skip("git executable unavailable")
    mini = curriculum_mini(tmp_path)
    repo = load_repo(mini)
    stage_manifest_producers(mini, repo)
    _git(mini, "init")
    _git(mini, "add", "-A")
    _git(mini, "commit", "-m", "initial")
    assert _git(mini, "rev-parse", "HEAD")
    if warm:
        assert compare_shadow_manifest(load_repo(mini), STAMP).equivalent
    return mini


def _commit_working_note(mini: Path, text: str, when: str) -> None:
    note = mini / WORKING_NOTE
    note.write_text(note.read_text(encoding="utf-8") + text + "\n",
                    encoding="utf-8")
    _git(mini, "add", WORKING_NOTE, when=when)
    _git(mini, "commit", "-m", "working note", when=when)


def _all_notes_updated(manifest: dict) -> list:
    found: list = []

    def walk(node) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                if key == "notes_updated":
                    found.append(value)
                else:
                    walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(manifest)
    return found


def _fresh_legacy(mini: Path) -> dict:
    """Legacy bytes under genuinely fresh git reads (the oracle)."""
    githistory.last_commit_dates.cache_clear()
    githistory.last_commit_timestamps.cache_clear()
    repo = load_repo(mini)
    return build_manifest(repo, STAMP, build_backlinks(repo, STAMP))


def test_poisoned_cache_does_not_hide_a_new_commit(tmp_path: Path):
    """A pinned H0 table plus an external commit: the first build is fresh."""
    mini = _git_mini(tmp_path, warm=False)
    githistory.last_commit_dates(str(mini))  # poison the cache with H0
    _commit_working_note(mini, "second thoughts", GIT_H1_WHEN)
    shadow = build_manifest_shadow(load_repo(mini), STAMP)
    fresh = _fresh_legacy(mini)
    assert GIT_H1_DAY in _all_notes_updated(fresh)  # the oracle moved
    assert serialize_manifest(shadow) == serialize_manifest(fresh)


@pytest.mark.parametrize("failure_point", ["head", "table"])
def test_unreadable_history_refuses_without_mutating_derived_state(
    tmp_path: Path, monkeypatch, failure_point: str,
):
    """Readable publication HEAD cannot admit unreadable history plus an old LRU."""
    mini = _git_mini(tmp_path, warm=True)
    old_table = dict(githistory.last_commit_dates(str(mini)))
    _commit_working_note(mini, "second thoughts", GIT_H1_WHEN)
    head = _git(mini, "rev-parse", "HEAD")
    assert shadow_module._git_state(mini)[0] == head
    assert githistory.last_commit_dates(str(mini)) == old_table
    cache = derived_dir(mini)
    before = {p.relative_to(cache): p.read_bytes()
              for p in cache.rglob("*") if p.is_file()}
    real_read = githistory.read_history
    failures = []

    def broken_history(root, *args):
        if failure_point == "head" or "--name-only" in args:
            failures.append(args)
            raise githistory.GitHistoryError("history unavailable")
        return real_read(root, *args)

    monkeypatch.setattr(githistory, "read_history", broken_history)
    trace = []
    with pytest.raises(TransactionFailure):
        build_manifest_shadow(load_repo(mini), STAMP, trace=trace)
    assert len(failures) == shadow_module.SNAPSHOT_ATTEMPTS
    assert trace == []
    assert {p.relative_to(cache): p.read_bytes()
            for p in cache.rglob("*") if p.is_file()} == before


def test_external_commit_between_builds_is_observed_same_process(tmp_path: Path):
    """compare@H0 warms everything; a commit; the rebuild observes H1."""
    mini = _git_mini(tmp_path, warm=True)
    _commit_working_note(mini, "second thoughts", GIT_H1_WHEN)
    shadow = build_manifest_shadow(load_repo(mini), STAMP)  # no clearing
    fresh = _fresh_legacy(mini)
    assert GIT_H1_DAY in _all_notes_updated(fresh)  # the oracle moved
    assert serialize_manifest(shadow) == serialize_manifest(fresh)
    # The committed state is fresh-consistent: a stable rerun hits all
    # nodes and still matches the legacy bytes exactly.
    trace: list = []
    assert compare_shadow_manifest(load_repo(mini), STAMP, trace=trace).equivalent
    assert all(event.status == "hit" for event in trace)


def test_commit_during_evaluation_discards_and_rebuilds_fresh(
    tmp_path: Path, monkeypatch,
):
    """A real commit landing mid-evaluation retries; the result is fresh."""
    mini = _git_mini(tmp_path, warm=True)
    real_evaluate_many = shadow_module.evaluate_many
    mutated = False

    def racing_evaluate_many(*args, **kwargs):
        nonlocal mutated
        results = real_evaluate_many(*args, **kwargs)
        if not mutated:
            mutated = True
            _commit_working_note(mini, "mid-eval thoughts", GIT_H1_WHEN)
        return results

    monkeypatch.setattr(shadow_module, "evaluate_many", racing_evaluate_many)
    shadow = build_manifest_shadow(load_repo(mini), STAMP)
    assert mutated  # the commit landed inside the first attempt
    fresh = _fresh_legacy(mini)
    assert GIT_H1_DAY in _all_notes_updated(fresh)  # the oracle moved
    assert serialize_manifest(shadow) == serialize_manifest(fresh)


def test_empty_commit_moves_the_snapshot_and_the_revision(tmp_path: Path):
    """HEAD-only move is detected: the snapshot moves, revision binds H1."""
    mini = _git_mini(tmp_path, warm=True)
    before = canonical_snapshot_digest(mini)
    _git(mini, "commit", "--allow-empty", "-m", "empty", when=GIT_H1_WHEN)
    assert canonical_snapshot_digest(mini) != before  # HEAD is folded
    shadow = build_manifest_shadow(load_repo(mini), STAMP)
    assert shadow["_generated"]["source_revision"] == _git(mini, "rev-parse", "HEAD")
    assert compare_shadow_manifest(load_repo(mini), STAMP).equivalent


# G2. Code identity covers the executing tree as well as the target.
# ---------------------------------------------------------------------------


def test_executing_code_change_invalidates_everything(tmp_path: Path, monkeypatch):
    """A different executing tree misses every key (target half untouched)."""
    mini = _warmed(tmp_path)
    monkeypatch.setattr(
        identity_module, "digest_executing_code_tree", lambda: "f" * 64)
    trace: list = []
    assert compare_shadow_manifest(load_repo(mini), STAMP, trace=trace).equivalent
    assert trace
    assert all(event.status == "rebuilt" for event in trace)


# G3. Format-provider drift reruns validation, nothing else.
# ---------------------------------------------------------------------------


def test_validator_provider_flip_reruns_only_validation(tmp_path: Path, monkeypatch):
    mini = _warmed(tmp_path)
    real = identity_module._validator_runtime_components()

    def fake_validator_components():
        return (("format-checkers", "date-time,uri"),) + real[1:]

    monkeypatch.setattr(
        identity_module, "_validator_runtime_components", fake_validator_components)
    calls = 0
    real_enforce = shadow_module.enforce

    def counting(payload, root):
        nonlocal calls
        calls += 1
        return real_enforce(payload, root)

    monkeypatch.setattr(shadow_module, "enforce", counting)
    trace: list = []
    assert compare_shadow_manifest(load_repo(mini), STAMP, trace=trace).equivalent
    assert trace
    status = {event.node: event.status for event in trace}
    assert status[VALIDATION_PROOF_ID] == "rebuilt"
    assert all(
        node_status == "hit"
        for node, node_status in status.items()
        if node != VALIDATION_PROOF_ID
    )
    assert calls == 1


# Staging. Discarded attempts mutate nothing persistent.
# ---------------------------------------------------------------------------


def _forge_proof(mini: Path) -> None:
    """Plant a key-matching but semantically wrong proof (F5 shape)."""
    state_path = derived_dir(mini) / "state-v1.json"
    doc = json.loads(state_path.read_text(encoding="utf-8"))
    forged = {
        "valid": True,
        "contract_version": declared_version(mini),
        "manifest_sha256": "0" * 64,  # structurally valid, semantically wrong
        "contract_closure_sha256": contract_closure_digest(mini),
    }
    blob_bytes = canonical_bytes(forged)
    blob_digest = hashlib.sha256(blob_bytes).hexdigest()
    (derived_dir(mini) / "blobs" / blob_digest).write_bytes(blob_bytes)
    doc["nodes"][VALIDATION_PROOF_ID]["output_sha256"] = blob_digest
    doc["nodes"][VALIDATION_PROOF_ID]["blob"] = f"blobs/{blob_digest}"
    state_path.write_text(json.dumps(doc, sort_keys=True), encoding="utf-8")


def test_discarded_attempt_with_bad_proof_mutates_nothing(
    tmp_path: Path, monkeypatch,
):
    """Bad-proof hit plus a tree that moves every evaluation: every attempt
    reaches the proof rebuild and then discards, and persistent state is
    byte-identical afterwards.

    The move lands where admission sees it but no node key does — a
    non-Python file under tools/, covered by the whole-tree snapshot and
    by nothing else (code identity hashes *.py, the fingerprint covers
    canonical roots, inputs enumerate canonical files). The payload stays
    byte-identical to the warmed one, so the proof evaluation is a true
    key hit on the forged value — the exact case the old code answered
    with a persistent invalidate() before the attempt committed.
    """
    mini = _warmed(tmp_path)
    _forge_proof(mini)
    before = _derived_snapshot(mini)
    real_evaluate_many = shadow_module.evaluate_many
    calls: list[str] = []

    def moving_evaluate_many(*args, **kwargs):
        results = real_evaluate_many(*args, **kwargs)
        calls.append("evaluate")
        (mini / "tools" / "scratch.txt").write_text(
            f"Race {len(calls)}.\n", encoding="utf-8")
        return results

    monkeypatch.setattr(shadow_module, "evaluate_many", moving_evaluate_many)
    with pytest.raises(TransactionFailure, match="changed during"):
        build_manifest_shadow(load_repo(mini), STAMP)
    assert len(calls) == shadow_module.SNAPSHOT_ATTEMPTS
    assert _derived_snapshot(mini) == before
