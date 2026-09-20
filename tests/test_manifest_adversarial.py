"""Adversarial manifest proof: the cache trust boundary (F1–F6).

The mutation matrix proves locality under normal edits; these tests
attack the boundary the matrix assumes away — malformed canonical
state, a repo loaded from torn bytes, code and runtime drift, and
internally consistent but wrong cache entries. Each test names the
finding it closes.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest
from repo_builders import curriculum_mini, stage_manifest_producers

import learning_os.derived.identity as identity_module
import learning_os.genout.manifest_derived as shadow_module
from learning_os.contracts.manifest_contract import declared_version
from learning_os.derived.identity import digest_bytes
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
