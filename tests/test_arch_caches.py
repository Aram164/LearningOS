"""A10 cache correctness, validation + receipt + dossier families (4.3).

SPEC §14 + D-12: the validation static issues live in one named derived
node, each receipt verdict in its own per-artifact node, and each unit's
semantic dossier in its own per-artifact node. Every case here runs cold,
mutates exactly one input, runs warm, and asserts the warm result equals a
fresh ``LOS_NO_CACHE=1`` run.

Scope: ``cache.validation-static``, ``cache.receipt:<rel>``,
``cache.dossier:<unit>``, and default-path ``cache.text:<sha256>``. A10
is NOT claimed here for summaries, custom text-cache dirs,
derived-state self-consistency, manifest, or search postings.

The input inventories below are independent: validation + receipt were
written from ``scratch/validation-receipt-input-inventory.md`` (read from
``validation_cache.cache_pins`` and ``receipt_cache._current_pins`` before
editing), dossiers from
``scratch/material-dossier-input-inventory.md`` (read from
``semantics/dossiers.py`` before editing), and material text from the
pre-existing cache-format facts (digest-keyed entries, the EXTRACTOR
constant, the index page count) read from ``tools/material_text.py``
before editing. They are hardcoded here, never generated from NodeSpec
declarations or the code under test; the spec-coverage tests verify the
code against them, not the reverse.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path

import pytest
from test_compute_once import _commit_capture
from test_material_text_cache import (
    _manifest_yaml,
    _tiny_pdf,
    _tree,
    needs_pdftotext,
)
from test_material_text_cache import (
    _material_text as _load_material_text,
)

import learning_os.rules.receipt_cache as rc
import learning_os.semantics.dossiers as dz
import learning_os.validation_cache as vc
from learning_os import digests
from learning_os.derived.store import read_state
from learning_os.loader import load_repo
from learning_os.rules import validate

REPO_ROOT = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# Independent input inventory (hardcoded; see module docstring).
# ---------------------------------------------------------------------------

#: The six validation pins from `validation_cache.cache_pins`.
VALIDATION_INPUTS = (
    "canonical_fingerprint",
    "code_identity",
    "runtime_digest",
    "materials_digest",
    "operations_digest",
    "validator_inputs",
)

#: The four global receipt pins from `receipt_cache._current_pins`.
RECEIPT_GLOBAL_INPUTS = (
    "code_identity",
    "runtime_digest",
    "validator_runtime_digest",
    "receipt_schema",
)

#: The six dossier dependency hashes from `dossiers.DEPENDENCIES`.
DOSSIER_INPUTS = (
    "knowledge-map",
    "source-map",
    "routes",
    "evidence",
    "semantic-contract",
    "operator-contract",
)

#: The three per-digest text freshness facts: the live source-bytes
#: digest, the effective extractor identity, and the live page count.
#: Producer and runtime identity ride in the key via the engine session.
TEXT_INPUTS = (
    "source",
    "extractor",
    "pages",
)


def _stage_validation_producers(root: Path) -> None:
    for rel in dict.fromkeys(vc.VALIDATION_PRODUCER_FILES):
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((REPO_ROOT / rel).read_bytes())


def _stage_receipt_producers(root: Path) -> None:
    for rel in dict.fromkeys(rc.RECEIPT_PRODUCER_FILES):
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((REPO_ROOT / rel).read_bytes())


def _stage_all_producers(root: Path) -> None:
    _stage_validation_producers(root)
    _stage_receipt_producers(root)


def _frozen(issues) -> list:
    return [(i.severity, i.code, i.message, i.path) for i in issues]


def _warm_validation(root: Path) -> list:
    return _frozen(vc.status_issues(load_repo(root)))


def _fresh_validation(root: Path, monkeypatch: pytest.MonkeyPatch) -> list:
    monkeypatch.setenv("LOS_NO_CACHE", "1")
    try:
        return _frozen(vc.status_issues(load_repo(root)))
    finally:
        monkeypatch.delenv("LOS_NO_CACHE", raising=False)


def _warm_receipt(root: Path) -> list:
    digests.clear()
    return _frozen(validate(load_repo(root), online=False))


def _fresh_receipt(root: Path, monkeypatch: pytest.MonkeyPatch) -> list:
    monkeypatch.setenv("LOS_NO_CACHE", "1")
    try:
        digests.clear()
        return _frozen(validate(load_repo(root), online=False))
    finally:
        monkeypatch.delenv("LOS_NO_CACHE", raising=False)


def _corrupt_status(path: Path) -> None:
    content = path.read_bytes()
    assert b"status: committed" in content
    path.write_bytes(content.replace(b"status: committed", b"status: corrupted"))


def _receipt_nodes(root: Path) -> dict:
    return {node_id: state for node_id, state in read_state(root).items()
            if node_id.startswith("cache.receipt:")}


def _no_receipt_errors(frozen_list: list) -> bool:
    return not [entry for entry in frozen_list
                if entry[0] == "E" and "transaction-receipt" in entry[2]]


# ---------------------------------------------------------------------------
# Spec coverage against the independent inventory (verification, not input).
# ---------------------------------------------------------------------------

def test_node_specs_cover_the_independent_inventory():
    assert vc.VALIDATION_NODE_ID == "cache.validation-static"
    assert vc.VALIDATION_NODE_VERSION == 1
    assert "tools/learning_os/validation_cache.py" in vc.VALIDATION_PRODUCER_FILES
    spec = vc._validation_spec()
    assert spec.id == "cache.validation-static" and spec.version == 1
    assert len(spec.direct_inputs) == len(VALIDATION_INPUTS) == 6
    assert rc.RECEIPT_NODE_VERSION == 1
    assert "tools/learning_os/rules/receipt_cache.py" in rc.RECEIPT_PRODUCER_FILES
    rel = "operations/transactions/transaction-x.yaml"
    rspec = rc._receipt_spec(rel)
    assert rspec.id == f"cache.receipt:{rel}" and rspec.version == 1
    # Four globals plus this receipt's own content hash, nothing else.
    assert len(rspec.direct_inputs) == len(RECEIPT_GLOBAL_INPUTS) + 1 == 5


def test_live_pin_functions_match_the_independent_inventory(mini_repo: Path):
    from learning_os.rules.core import Validator

    assert set(vc.cache_pins(mini_repo)) == set(VALIDATION_INPUTS)
    pins = rc._current_pins(Validator(load_repo(mini_repo)))
    assert set(pins) == set(RECEIPT_GLOBAL_INPUTS)


def test_generated_findings_have_one_shared_implementation(tmp_path: Path):
    """One read, not two: the validator and the cache pin import it.

    `domain.generated_reads.generated_file_findings` is the single
    implementation (both callers import it with no new A1 exception, so
    neither keeps a copy); this battery pins its codes, messages, and
    raise behavior on every shape.
    """
    import learning_os.domain.generated_reads as shared
    import learning_os.rules.generated as validator_module

    assert validator_module.generated_reads is shared
    assert vc.generated_reads is shared
    assert not hasattr(validator_module, "generated_file_findings")
    assert not hasattr(vc, "generated_file_findings")
    assert not hasattr(vc, "_generated_file_findings")
    findings = shared.generated_file_findings
    (tmp_path / "valid.json").write_text(
        json.dumps({"_generated": {"warning": "GENERATED x", "generator": "t"}}),
        encoding="utf-8")
    (tmp_path / "noheader.json").write_text(json.dumps({"x": 1}), encoding="utf-8")
    (tmp_path / "bad.json").write_text("{ not json", encoding="utf-8")
    (tmp_path / "list.json").write_text("[1, 2]", encoding="utf-8")
    (tmp_path / "valid.md").write_text("<!-- GENERATED file -->\n\nBody.\n",
                                       encoding="utf-8")
    (tmp_path / "bare.md").write_text("No marker here.\n", encoding="utf-8")
    (tmp_path / "dir.json").mkdir()
    (tmp_path / "dir.md").mkdir()
    (tmp_path / "broken.json").symlink_to(tmp_path / "nowhere.json")
    (tmp_path / "link.json").symlink_to(tmp_path / "valid.json")
    (tmp_path / "note.txt").write_text("not a checked suffix\n", encoding="utf-8")
    assert findings(tmp_path / "valid.json") == []
    assert findings(tmp_path / "list.json") == []
    assert findings(tmp_path / "link.json") == []
    assert findings(tmp_path / "note.txt") == []
    assert findings(tmp_path / "valid.md") == []
    assert findings(tmp_path / "noheader.json")[0][0] == "GEN-HEADER"
    assert findings(tmp_path / "bad.json")[0][0] == "GEN-JSON"
    assert findings(tmp_path / "bare.md")[0][0] == "GEN-HEADER"
    assert findings(tmp_path / "dir.json")[0][0] == "GEN-JSON"
    assert findings(tmp_path / "dir.md")[0][0] == "GEN-HEADER"
    assert findings(tmp_path / "broken.json")[0][0] == "GEN-JSON"
    non_utf8 = tmp_path / "nonutf8.json"
    non_utf8.write_bytes(b"\xff\xfe not utf-8")
    with pytest.raises(ValueError):
        findings(non_utf8)
    unreadable = tmp_path / "unreadable.json"
    unreadable.write_text(json.dumps({"x": 1}), encoding="utf-8")
    unreadable.chmod(0o000)
    try:
        with pytest.raises(OSError):
            findings(unreadable)
    finally:
        unreadable.chmod(0o644)


def test_obsolete_sidecars_stay_unwritten(mini_repo: Path):
    _stage_all_producers(mini_repo)
    _commit_capture(mini_repo, "a10-obs-a", "request-a10-obs-a")
    vc.status_issues(load_repo(mini_repo))
    validate(load_repo(mini_repo), online=False)
    assert not (mini_repo / vc.CACHE_RELATIVE).exists()
    assert not (mini_repo / rc.SIDECAR_RELATIVE).exists()


# ---------------------------------------------------------------------------
# Validation warm transitions: one input at a time.
# ---------------------------------------------------------------------------

def test_validation_canonical_mutation_matches_fresh(mini_repo: Path, monkeypatch):
    _stage_validation_producers(mini_repo)
    vc.status_issues(load_repo(mini_repo))
    assert vc.read_cached_static_issues(mini_repo) is not None
    note = mini_repo / "knowledge/notes/mathematics/note-demo.md"
    note.write_text(note.read_text(encoding="utf-8") + "\nA10 canonical touch.\n",
                    encoding="utf-8")
    assert vc.read_cached_static_issues(mini_repo) is None
    assert _warm_validation(mini_repo) == _fresh_validation(mini_repo, monkeypatch)


def test_validation_code_identity_mutation_matches_fresh(mini_repo: Path, monkeypatch):
    _stage_validation_producers(mini_repo)
    vc.status_issues(load_repo(mini_repo))
    assert vc.read_cached_static_issues(mini_repo) is not None
    real = vc.digest_code_identity
    monkeypatch.setattr(vc, "digest_code_identity", lambda root: "f" * 64)
    assert real(mini_repo) != "f" * 64
    assert vc.read_cached_static_issues(mini_repo) is None
    assert _warm_validation(mini_repo) == _fresh_validation(mini_repo, monkeypatch)


def test_validation_runtime_mutation_matches_fresh(mini_repo: Path, monkeypatch):
    _stage_validation_producers(mini_repo)
    vc.status_issues(load_repo(mini_repo))
    assert vc.read_cached_static_issues(mini_repo) is not None
    monkeypatch.setattr(vc, "runtime_digest", lambda: "e" * 64)
    assert vc.read_cached_static_issues(mini_repo) is None
    assert _warm_validation(mini_repo) == _fresh_validation(mini_repo, monkeypatch)


def test_validation_materials_mutation_matches_fresh(mini_repo: Path, monkeypatch):
    _stage_validation_producers(mini_repo)
    vc.status_issues(load_repo(mini_repo))
    assert vc.read_cached_static_issues(mini_repo) is not None
    materials = mini_repo.parent / "materials"
    (materials / "a10-new-deck.pdf").write_bytes(b"%PDF-1.4 a10 bytes\n")
    assert vc.read_cached_static_issues(mini_repo) is None
    assert _warm_validation(mini_repo) == _fresh_validation(mini_repo, monkeypatch)


def test_validation_operations_mutation_matches_fresh(mini_repo: Path, monkeypatch):
    _stage_validation_producers(mini_repo)
    vc.status_issues(load_repo(mini_repo))
    assert vc.read_cached_static_issues(mini_repo) is not None
    monkeypatch.setattr(vc, "operations_digest", lambda root: "d" * 64)
    assert vc.read_cached_static_issues(mini_repo) is None
    assert _warm_validation(mini_repo) == _fresh_validation(mini_repo, monkeypatch)


def test_validation_validator_inputs_mutation_matches_fresh(mini_repo: Path, monkeypatch):
    _stage_validation_producers(mini_repo)
    vc.status_issues(load_repo(mini_repo))
    assert vc.read_cached_static_issues(mini_repo) is not None
    (mini_repo / "generated/stray.txt").write_text("a10\n", encoding="utf-8")
    assert vc.read_cached_static_issues(mini_repo) is None
    warm = _warm_validation(mini_repo)
    assert any(code == "GEN-UNKNOWN" for _, code, _, _ in warm)
    assert warm == _fresh_validation(mini_repo, monkeypatch)


# ---------------------------------------------------------------------------
# Validation robustness: corruption, unreadable state, races, online, drift.
# ---------------------------------------------------------------------------

def test_validation_corrupt_blob_matches_fresh(mini_repo: Path, monkeypatch):
    _stage_validation_producers(mini_repo)
    vc.status_issues(load_repo(mini_repo))
    state = read_state(mini_repo)[vc.VALIDATION_NODE_ID]
    blob = mini_repo / "generated" / "derived-state" / state.blob
    blob.write_bytes(blob.read_bytes()[: len(blob.read_bytes()) // 2])
    assert vc.read_cached_static_issues(mini_repo) is None
    assert _warm_validation(mini_repo) == _fresh_validation(mini_repo, monkeypatch)


def test_validation_unreadable_blob_matches_fresh(mini_repo: Path, monkeypatch):
    _stage_validation_producers(mini_repo)
    vc.status_issues(load_repo(mini_repo))
    assert vc.read_cached_static_issues(mini_repo) is not None
    state = read_state(mini_repo)[vc.VALIDATION_NODE_ID]
    blob = mini_repo / "generated" / "derived-state" / state.blob
    blob.chmod(0o000)
    try:
        assert _warm_validation(mini_repo) == _fresh_validation(mini_repo, monkeypatch)
    finally:
        blob.chmod(0o644)


def test_validation_in_run_write_matches_fresh(mini_repo: Path, monkeypatch):
    _stage_validation_producers(mini_repo)
    note = mini_repo / "knowledge/notes/mathematics/note-demo.md"
    real = vc.validate

    def racing(repo, online=False):
        issues = real(repo, online=online)
        note.rename(note.with_name("a10-raced-demo.md"))
        return issues

    monkeypatch.setattr(vc, "validate", racing)
    first = vc.status_issues(load_repo(mini_repo))
    assert not any(sev == "E" for sev, _, _, _ in _frozen(first))
    monkeypatch.setattr(vc, "validate", real)
    assert vc.read_cached_static_issues(mini_repo) is None
    assert _warm_validation(mini_repo) == _fresh_validation(mini_repo, monkeypatch)


def test_validation_online_run_does_not_poison(mini_repo: Path, monkeypatch):
    _stage_validation_producers(mini_repo)
    vc.status_issues(load_repo(mini_repo))
    assert vc.read_cached_static_issues(mini_repo) is not None
    online = validate(load_repo(mini_repo), online=True)
    assert isinstance(online, list)
    # The online run touched no validation node: the offline read still hits.
    assert vc.read_cached_static_issues(mini_repo) is not None
    assert _warm_validation(mini_repo) == _fresh_validation(mini_repo, monkeypatch)


def test_validation_advisory_drift_matches_fresh(mini_repo: Path, monkeypatch):
    _stage_validation_producers(mini_repo)
    drop = mini_repo / "work/inbox/drop.md"
    drop.write_text("unrouted capture\n", encoding="utf-8")
    vc.status_issues(load_repo(mini_repo))
    assert vc.read_cached_static_issues(mini_repo) is not None
    past = time.time() - 16 * 86400
    os.utime(drop, (past, past))
    warm = _warm_validation(mini_repo)
    assert any(code == "INBOX-STALE" for _, code, _, _ in warm)
    assert vc.read_cached_static_issues(mini_repo) is not None
    assert warm == _fresh_validation(mini_repo, monkeypatch)


# ---------------------------------------------------------------------------
# Validation derived-state inputs: the GEN files under our own cache root.
# ---------------------------------------------------------------------------

def test_validation_derived_state_extra_malformed_matches_fresh(mini_repo: Path, monkeypatch):
    """The retained Task 72 proof: extra.json valid -> malformed must miss."""
    _stage_validation_producers(mini_repo)
    extra = mini_repo / "generated" / "derived-state" / "extra.json"
    extra.parent.mkdir(parents=True, exist_ok=True)
    extra.write_text(json.dumps({"_generated": {"warning": "GENERATED x", "generator": "t"},
                                 "x": 1}), encoding="utf-8")
    vc.status_issues(load_repo(mini_repo))
    assert vc.read_cached_static_issues(mini_repo) is not None
    extra.write_text("{ not json", encoding="utf-8")
    assert vc.read_cached_static_issues(mini_repo) is None
    warm = _warm_validation(mini_repo)
    assert any(code == "GEN-JSON" and "extra.json" in path
               for _, code, _, path in warm)
    assert warm == _fresh_validation(mini_repo, monkeypatch)


def test_validation_derived_state_marker_change_matches_fresh(mini_repo: Path, monkeypatch):
    _stage_validation_producers(mini_repo)
    extra = mini_repo / "generated" / "derived-state" / "extra.md"
    extra.parent.mkdir(parents=True, exist_ok=True)
    extra.write_text("<!-- GENERATED file -->\n\nBody.\n", encoding="utf-8")
    vc.status_issues(load_repo(mini_repo))
    assert vc.read_cached_static_issues(mini_repo) is not None
    extra.write_text("No marker here.\n", encoding="utf-8")
    assert vc.read_cached_static_issues(mini_repo) is None
    warm = _warm_validation(mini_repo)
    assert any(code == "GEN-HEADER" and "extra.md" in path
               for _, code, _, path in warm)
    assert warm == _fresh_validation(mini_repo, monkeypatch)


def test_validation_derived_state_corruption_heals_and_matches_fresh(mini_repo: Path, monkeypatch):
    _stage_validation_producers(mini_repo)
    vc.status_issues(load_repo(mini_repo))
    assert vc.read_cached_static_issues(mini_repo) is not None
    state_path = mini_repo / "generated" / "derived-state" / "state-v1.json"
    good_bytes = state_path.read_bytes()
    state_path.write_bytes(good_bytes[: len(good_bytes) // 2])
    assert vc.read_cached_static_issues(mini_repo) is None
    # Fresh first: it reports the corruption without healing (the bypass
    # persists nothing), so the warm run below still sees truncated bytes.
    fresh = _fresh_validation(mini_repo, monkeypatch)
    assert any(code == "GEN-JSON" and "state-v1.json" in path
               for _, code, _, path in fresh)
    warm = _warm_validation(mini_repo)
    assert warm == fresh
    # Warm healed the index by rebuilding it: it parses again.
    assert json.loads(state_path.read_text(encoding="utf-8"))["schema_version"] == 1
    # The heal moved the pins back to clean, so the error cached under the
    # malformed pin misses; the next warm rebuilds clean and both agree.
    assert vc.read_cached_static_issues(mini_repo) is None
    warm_clean = _warm_validation(mini_repo)
    assert not [entry for entry in warm_clean
                if entry[1] == "GEN-JSON" and "state-v1.json" in entry[3]]
    assert warm_clean == _fresh_validation(mini_repo, monkeypatch)
    assert vc.read_cached_static_issues(mini_repo) is not None


def test_validation_derived_state_deletion_repairs_after_cached_error(
        mini_repo: Path, monkeypatch):
    _stage_validation_producers(mini_repo)
    extra = mini_repo / "generated" / "derived-state" / "extra.json"
    extra.parent.mkdir(parents=True, exist_ok=True)
    extra.write_text("{ not json", encoding="utf-8")
    warm_error = _warm_validation(mini_repo)
    assert any(code == "GEN-JSON" and "extra.json" in path
               for _, code, _, path in warm_error)
    assert warm_error == _fresh_validation(mini_repo, monkeypatch)
    state_path = mini_repo / "generated" / "derived-state" / "state-v1.json"
    state_path.unlink()
    assert vc.read_cached_static_issues(mini_repo) is None
    warm_rebuilt = _warm_validation(mini_repo)
    assert any(code == "GEN-JSON" and "extra.json" in path
               for _, code, _, path in warm_rebuilt)
    assert warm_rebuilt == _fresh_validation(mini_repo, monkeypatch)
    assert state_path.is_file()
    extra.unlink()
    assert vc.read_cached_static_issues(mini_repo) is None
    warm_clean = _warm_validation(mini_repo)
    assert not [entry for entry in warm_clean if "extra.json" in entry[3]]
    assert warm_clean == _fresh_validation(mini_repo, monkeypatch)


def test_validation_derived_state_extra_dir_matches_fresh(mini_repo: Path, monkeypatch):
    """An empty extra.json directory is a real GEN-JSON input: the pin
    must miss and warm must equal fresh (the confirmed Task 76 omission:
    the old walk descended into directories without pinning their
    finding, so warm served stale pre-directory issues)."""
    _stage_validation_producers(mini_repo)
    vc.status_issues(load_repo(mini_repo))
    assert vc.read_cached_static_issues(mini_repo) is not None
    extra = mini_repo / "generated" / "derived-state" / "extra.json"
    extra.mkdir(parents=True)
    assert vc.read_cached_static_issues(mini_repo) is None
    warm = _warm_validation(mini_repo)
    assert any(code == "GEN-JSON" and "extra.json" in path
               for _, code, _, path in warm)
    assert warm == _fresh_validation(mini_repo, monkeypatch)
    # A malformed file nested inside pins too: the directory finding
    # comes first, then the descent covers the children.
    (extra / "inner.json").write_text("{ not json", encoding="utf-8")
    assert vc.read_cached_static_issues(mini_repo) is None
    warm_nested = _warm_validation(mini_repo)
    assert any(code == "GEN-JSON" and "inner.json" in path
               for _, code, _, path in warm_nested)
    assert warm_nested == _fresh_validation(mini_repo, monkeypatch)
    # Removing the directory heals the pin back to clean.
    (extra / "inner.json").unlink()
    extra.rmdir()
    assert vc.read_cached_static_issues(mini_repo) is None
    warm_clean = _warm_validation(mini_repo)
    assert not [entry for entry in warm_clean if "extra.json" in entry[3]]
    assert warm_clean == _fresh_validation(mini_repo, monkeypatch)
    assert vc.read_cached_static_issues(mini_repo) is not None


def test_validation_derived_state_file_to_dir_shape_matches_fresh(
        mini_repo: Path, monkeypatch):
    """A clean extra.json file replaced by a directory: the same name
    with a new shape must miss exactly when the findings change, in
    both directions."""
    _stage_validation_producers(mini_repo)
    extra = mini_repo / "generated" / "derived-state" / "extra.json"
    extra.parent.mkdir(parents=True, exist_ok=True)
    clean = json.dumps({"_generated": {"warning": "GENERATED x", "generator": "t"},
                        "x": 1})
    extra.write_text(clean, encoding="utf-8")
    vc.status_issues(load_repo(mini_repo))
    assert vc.read_cached_static_issues(mini_repo) is not None
    extra.unlink()
    extra.mkdir()
    assert vc.read_cached_static_issues(mini_repo) is None
    warm = _warm_validation(mini_repo)
    assert any(code == "GEN-JSON" and "extra.json" in path
               for _, code, _, path in warm)
    assert warm == _fresh_validation(mini_repo, monkeypatch)
    extra.rmdir()
    extra.write_text(clean, encoding="utf-8")
    assert vc.read_cached_static_issues(mini_repo) is None
    warm_clean = _warm_validation(mini_repo)
    assert not [entry for entry in warm_clean if "extra.json" in entry[3]]
    assert warm_clean == _fresh_validation(mini_repo, monkeypatch)
    assert vc.read_cached_static_issues(mini_repo) is not None


def test_validation_derived_state_broken_link_matches_fresh(mini_repo: Path, monkeypatch):
    """A broken extra.json symlink is a GEN-JSON input like any shape:
    directory, file, and broken-link changes must each invalidate
    exactly when the fresh findings change."""
    _stage_validation_producers(mini_repo)
    vc.status_issues(load_repo(mini_repo))
    assert vc.read_cached_static_issues(mini_repo) is not None
    extra = mini_repo / "generated" / "derived-state" / "extra.json"
    extra.symlink_to(mini_repo / "generated" / "derived-state" / "nowhere.json")
    assert vc.read_cached_static_issues(mini_repo) is None
    warm = _warm_validation(mini_repo)
    assert any(code == "GEN-JSON" and "extra.json" in path
               for _, code, _, path in warm)
    assert warm == _fresh_validation(mini_repo, monkeypatch)
    extra.unlink()
    assert vc.read_cached_static_issues(mini_repo) is None
    assert _warm_validation(mini_repo) == _fresh_validation(mini_repo, monkeypatch)
    assert vc.read_cached_static_issues(mini_repo) is not None


def test_validation_unreadable_state_matches_fresh_by_raising(mini_repo: Path, monkeypatch):
    """Pre-existing: unreadable state-v1.json raises in validation itself
    (`check_generated` has no OSError handling). Warm and fresh must raise
    the same way; this proves matching behavior, not cache recovery."""
    _stage_validation_producers(mini_repo)
    vc.status_issues(load_repo(mini_repo))
    assert vc.read_cached_static_issues(mini_repo) is not None
    state_path = mini_repo / "generated" / "derived-state" / "state-v1.json"
    state_path.chmod(0o000)
    try:
        with pytest.raises(OSError):
            _warm_validation(mini_repo)
        with pytest.raises(OSError):
            _fresh_validation(mini_repo, monkeypatch)
    finally:
        state_path.chmod(0o644)


# ---------------------------------------------------------------------------
# Receipt warm transitions: globals, registry, content, independence.
# ---------------------------------------------------------------------------

def test_receipt_code_identity_matches_fresh(mini_repo: Path, monkeypatch):
    _stage_receipt_producers(mini_repo)
    _commit_capture(mini_repo, "a10-rc-code", "request-a10-rc-code")
    cold = _warm_receipt(mini_repo)
    assert _receipt_nodes(mini_repo)
    monkeypatch.setattr(rc, "digest_code_identity", lambda root: "c" * 64)
    assert _warm_receipt(mini_repo) == _fresh_receipt(mini_repo, monkeypatch)
    assert _warm_receipt(mini_repo) == cold


def test_receipt_runtime_matches_fresh(mini_repo: Path, monkeypatch):
    _stage_receipt_producers(mini_repo)
    _commit_capture(mini_repo, "a10-rc-rt", "request-a10-rc-rt")
    cold = _warm_receipt(mini_repo)
    monkeypatch.setattr(rc, "runtime_digest", lambda: "b" * 64)
    assert _warm_receipt(mini_repo) == _fresh_receipt(mini_repo, monkeypatch)
    assert _warm_receipt(mini_repo) == cold


def test_receipt_validator_runtime_matches_fresh(mini_repo: Path, monkeypatch):
    _stage_receipt_producers(mini_repo)
    _commit_capture(mini_repo, "a10-rc-vrt", "request-a10-rc-vrt")
    cold = _warm_receipt(mini_repo)
    monkeypatch.setattr(rc, "validator_runtime_digest", lambda: "a" * 64)
    assert _warm_receipt(mini_repo) == _fresh_receipt(mini_repo, monkeypatch)
    assert _warm_receipt(mini_repo) == cold


def test_receipt_schema_mutation_matches_fresh(mini_repo: Path, monkeypatch):
    _stage_receipt_producers(mini_repo)
    _commit_capture(mini_repo, "a10-rc-schema", "request-a10-rc-schema")
    _warm_receipt(mini_repo)
    schema = mini_repo / "system/schema/transaction-receipt.schema.json"
    content = schema.read_text(encoding="utf-8")
    assert '"const": "committed"' in content
    schema.write_text(content.replace('"const": "committed"', '"const": "corrupted"'),
                      encoding="utf-8")
    warm = _warm_receipt(mini_repo)
    assert any(code == "SCHEMA" for _, code, _, _ in warm)
    assert warm == _fresh_receipt(mini_repo, monkeypatch)


def test_receipt_registry_mutation_matches_fresh(mini_repo: Path, monkeypatch):
    _stage_receipt_producers(mini_repo)
    _commit_capture(mini_repo, "a10-rc-reg", "request-a10-rc-reg")
    schema_dir = mini_repo / "system/schema"
    receipt_path = schema_dir / "transaction-receipt.schema.json"
    receipt_schema = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt_schema["allOf"] = [{"$ref": "https://learningos.local/schema/receipt-extra.schema.json"}]
    receipt_path.write_text(json.dumps(receipt_schema), encoding="utf-8")
    extra = schema_dir / "receipt-extra.schema.json"
    extra.write_text(json.dumps({"$schema": "https://json-schema.org/draft/2020-12/schema",
                                 "type": "object"}), encoding="utf-8")
    assert _no_receipt_errors(_warm_receipt(mini_repo))
    extra.write_text(json.dumps({"$schema": "https://json-schema.org/draft/2020-12/schema",
                                 "not": {"required": ["id"]}}), encoding="utf-8")
    warm = _warm_receipt(mini_repo)
    assert any(code == "SCHEMA" for _, code, _, _ in warm)
    assert warm == _fresh_receipt(mini_repo, monkeypatch)


def test_receipt_content_mutation_matches_fresh(mini_repo: Path, monkeypatch):
    _stage_receipt_producers(mini_repo)
    result = _commit_capture(mini_repo, "a10-rc-content", "request-a10-rc-content")
    _warm_receipt(mini_repo)
    _corrupt_status(mini_repo / result.receipt_path)
    warm = _warm_receipt(mini_repo)
    assert any("transaction-receipt" in message for _, _, message, _ in warm)
    assert warm == _fresh_receipt(mini_repo, monkeypatch)


def test_receipt_same_stat_bytes_match_fresh(mini_repo: Path, monkeypatch):
    _stage_receipt_producers(mini_repo)
    result = _commit_capture(mini_repo, "a10-rc-stat", "request-a10-rc-stat")
    assert _no_receipt_errors(_warm_receipt(mini_repo))
    path = mini_repo / result.receipt_path
    old = path.stat()
    _corrupt_status(path)
    os.utime(path, ns=(old.st_atime_ns, old.st_mtime_ns))
    assert (path.stat().st_size, path.stat().st_mtime_ns) == (old.st_size, old.st_mtime_ns)
    warm = _warm_receipt(mini_repo)
    assert any("transaction-receipt" in message for _, _, message, _ in warm)
    assert warm == _fresh_receipt(mini_repo, monkeypatch)


def test_receipt_corrupt_blob_matches_fresh(mini_repo: Path, monkeypatch):
    _stage_receipt_producers(mini_repo)
    _commit_capture(mini_repo, "a10-rc-blob", "request-a10-rc-blob")
    cold = _warm_receipt(mini_repo)
    node_id, state = next(iter(_receipt_nodes(mini_repo).items()))
    blob = mini_repo / "generated" / "derived-state" / state.blob
    assert node_id.startswith("cache.receipt:")
    blob.write_bytes(b"\x00\xff not json {{{")
    assert _warm_receipt(mini_repo) == cold
    assert _warm_receipt(mini_repo) == _fresh_receipt(mini_repo, monkeypatch)


def test_receipt_unreadable_blob_matches_fresh(mini_repo: Path, monkeypatch):
    _stage_receipt_producers(mini_repo)
    _commit_capture(mini_repo, "a10-rc-unread", "request-a10-rc-unread")
    cold = _warm_receipt(mini_repo)
    _node_id, state = next(iter(_receipt_nodes(mini_repo).items()))
    blob = mini_repo / "generated" / "derived-state" / state.blob
    blob.chmod(0o000)
    try:
        assert _warm_receipt(mini_repo) == cold
        assert _warm_receipt(mini_repo) == _fresh_receipt(mini_repo, monkeypatch)
    finally:
        blob.chmod(0o644)


def test_two_unrelated_receipts_invalidate_independently(mini_repo: Path, monkeypatch):
    _stage_receipt_producers(mini_repo)
    _commit_capture(mini_repo, "a10-rc-two-a", "request-a10-rc-two-a")
    result_b = _commit_capture(mini_repo, "a10-rc-two-b", "request-a10-rc-two-b")
    assert _no_receipt_errors(_warm_receipt(mini_repo))
    assert len(_receipt_nodes(mini_repo)) == 2
    _corrupt_status(mini_repo / result_b.receipt_path)
    original = rc._validate_fresh
    calls: list = []

    def counted(validator, path: Path, rel: str):
        calls.append(rel)
        return original(validator, path, rel)

    monkeypatch.setattr(rc, "_validate_fresh", counted)
    warm = _warm_receipt(mini_repo)
    assert len(calls) == 1 and calls[0].endswith(".yaml")
    assert any("transaction-receipt" in message for _, _, message, _ in warm)
    assert warm == _fresh_receipt(mini_repo, monkeypatch)


# ---------------------------------------------------------------------------
# Dossier warm transitions: one dependency at a time, plus robustness.
# ---------------------------------------------------------------------------

def _stage_dossier_producers(root: Path) -> None:
    for rel in dict.fromkeys(dz.DOSSIER_PRODUCER_FILES):
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((REPO_ROOT / rel).read_bytes())


_DOSSIER_VERSIONS = {"semantic-contract": "2", "operator-contract": "operator-v1"}
_DOSSIER_MENU = {"routes": ["route-a", "route-b"]}
_DOSSIER_NODES = {"nodes": ["knowledge-a"]}
_DOSSIER_ROUTES = [
    {"id": "route-a", "locator": "ch 1"},
    {"id": "route-b", "locator": "ch 2"},
]
_DOSSIER_EVIDENCE = {"material://demo/deck.pdf": "sha256:abc"}


def _dossier_kwargs(unit_id: str = "unit-aml-l01", **overrides):
    kwargs = {
        "unit_id": unit_id,
        "knowledge_map": dict(_DOSSIER_NODES),
        "source_map": dict(_DOSSIER_MENU),
        "routes": [dict(route) for route in _DOSSIER_ROUTES],
        "evidence": dict(_DOSSIER_EVIDENCE),
        "contract_versions": dict(_DOSSIER_VERSIONS),
    }
    kwargs.update(overrides)
    return kwargs


def _fresh_dossier(monkeypatch: pytest.MonkeyPatch, **kwargs):
    """A fresh dossier build under the bypass flag (builds ignore the store)."""
    monkeypatch.setenv("LOS_NO_CACHE", "1")
    try:
        return dz.build_dossier(**kwargs)
    finally:
        monkeypatch.delenv("LOS_NO_CACHE", raising=False)


def test_dossier_spec_covers_the_independent_inventory():
    assert dz.DOSSIER_NODE_VERSION == 1
    assert "tools/learning_os/semantics/dossiers.py" in dz.DOSSIER_PRODUCER_FILES
    assert tuple(dz.DEPENDENCIES) == DOSSIER_INPUTS
    spec = dz._dossier_spec("unit-x")
    assert spec.id == "cache.dossier:unit-x" and spec.version == 1
    assert len(spec.direct_inputs) == len(DOSSIER_INPUTS) == 6


@pytest.mark.parametrize("dependency", DOSSIER_INPUTS)
def test_dossier_dependency_mutation_matches_fresh(
        tmp_path: Path, monkeypatch, dependency: str):
    _stage_dossier_producers(tmp_path)
    base = _dossier_kwargs()
    first = dz.build_dossier(**base)
    first_path = dz.store_dossier(tmp_path, first)
    assert dz.load_dossier(first_path) == first
    mutated = _dossier_kwargs()
    if dependency == "knowledge-map":
        mutated["knowledge_map"] = {"nodes": ["knowledge-b"]}
    elif dependency == "source-map":
        mutated["source_map"] = {"routes": ["route-c"]}
    elif dependency == "routes":
        mutated["routes"] = [dict(_DOSSIER_ROUTES[0], locator="ch 9"),
                             _DOSSIER_ROUTES[1]]
    elif dependency == "evidence":
        mutated["evidence"] = {"material://demo/deck.pdf": "sha256:def"}
    elif dependency == "semantic-contract":
        mutated["contract_versions"] = {**_DOSSIER_VERSIONS,
                                        "semantic-contract": "3"}
    else:
        mutated["contract_versions"] = {**_DOSSIER_VERSIONS,
                                        "operator-contract": "operator-v2"}
    second = dz.build_dossier(**mutated)
    assert second.key != first.key
    changed = {name for name, digest in second.hashes
               if dict(first.hashes)[name] != digest}
    assert changed == {dependency}
    second_path = dz.store_dossier(tmp_path, second)
    with pytest.raises(dz.DossierError):
        dz.load_dossier(first_path)
    warm = dz.load_dossier(second_path)
    assert warm == _fresh_dossier(monkeypatch, **mutated)


def test_dossier_corrupt_blob_matches_fresh(tmp_path: Path, monkeypatch):
    _stage_dossier_producers(tmp_path)
    kwargs = _dossier_kwargs()
    dossier = dz.build_dossier(**kwargs)
    path = dz.store_dossier(tmp_path, dossier)
    assert dz.load_dossier(path) == dossier
    node_id = f"cache.dossier:{dossier.unit_id}"
    state = read_state(tmp_path)[node_id]
    blob = tmp_path / "generated" / "derived-state" / state.blob
    blob.write_bytes(b"\x00\xff not json {{{")
    with pytest.raises(dz.DossierError):
        dz.load_dossier(path)
    healed = dz.store_dossier(tmp_path, dz.build_dossier(**kwargs))
    assert dz.load_dossier(healed) == _fresh_dossier(monkeypatch, **kwargs)


def test_two_unrelated_dossiers_invalidate_independently(tmp_path: Path, monkeypatch):
    _stage_dossier_producers(tmp_path)
    kwargs_a = _dossier_kwargs("unit-a")
    kwargs_b = _dossier_kwargs("unit-b")
    dossier_a = dz.build_dossier(**kwargs_a)
    dossier_b = dz.build_dossier(**kwargs_b)
    path_a = dz.store_dossier(tmp_path, dossier_a)
    path_b = dz.store_dossier(tmp_path, dossier_b)
    assert dz.load_dossier(path_a) == dossier_a
    assert dz.load_dossier(path_b) == dossier_b
    moved_b = _dossier_kwargs("unit-b", evidence={"material://demo/deck.pdf": "sha256:zzz"})
    dossier_b2 = dz.build_dossier(**moved_b)
    path_b2 = dz.store_dossier(tmp_path, dossier_b2)
    assert dz.load_dossier(path_a) == dossier_a
    assert dz.load_dossier(path_a) == _fresh_dossier(monkeypatch, **kwargs_a)
    assert dz.load_dossier(path_b2) == _fresh_dossier(monkeypatch, **moved_b)
    with pytest.raises(dz.DossierError):
        dz.load_dossier(path_b)


def test_dossier_poison_matches_fresh_by_raising(tmp_path: Path, monkeypatch):
    """Tampered views refuse under warm and fresh alike (the poisoning check
    runs before the derived lookup, so the bypass cannot skip it)."""
    _stage_dossier_producers(tmp_path)
    kwargs = _dossier_kwargs()
    dossier = dz.build_dossier(**kwargs)
    path = dz.store_dossier(tmp_path, dossier)
    raw = json.loads(path.read_text(encoding="utf-8"))
    raw["content"]["routes"][0]["locator"] = "ch 9"
    path.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(dz.DossierError, match="poison"):
        dz.load_dossier(path)
    monkeypatch.setenv("LOS_NO_CACHE", "1")
    try:
        with pytest.raises(dz.DossierError, match="poison"):
            dz.load_dossier(path)
    finally:
        monkeypatch.delenv("LOS_NO_CACHE", raising=False)


# ---------------------------------------------------------------------------
# Material-text default-path warm transitions: source, extractor, pages,
# producer, runtime, corruption, isolation. Custom dirs stay file-only.
# ---------------------------------------------------------------------------

def _stage_text_producers(root: Path, mt) -> None:
    for rel in dict.fromkeys(mt.TEXT_PRODUCER_FILES):
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((REPO_ROOT / rel).read_bytes())


def _text_world(tmp_path: Path, mt, monkeypatch, spec: dict):
    """A fake repo + materials + manifest wired as the tool's default.

    Returns (fake_root, materials_base, manifest). The module's own
    REPO/CACHE_DIR anchors point at the fake root, so the true default
    path (no --cache-dir flag) exercises derived nodes without
    touching the real repository.
    """
    work = tmp_path / "textworld"
    work.mkdir()
    fake = work / "repo"
    fake.mkdir()
    _stage_text_producers(fake, mt)
    monkeypatch.setattr(mt, "REPO", fake)
    monkeypatch.setattr(mt, "CACHE_DIR", fake / "generated" / "text-cache")
    base = work / "materials"
    _tree(base, spec)
    manifest = work / "manifest.yaml"
    manifest.write_text(_manifest_yaml(spec), encoding="utf-8")
    return fake, base, manifest


def _run_text_default(mt, base: Path, manifest: Path, capsys, *flags):
    """Run the tool on its true default cache (no --cache-dir flag)."""
    code = mt.main(["--manifest", str(manifest), "--materials-root", str(base),
                    *flags])
    out, _ = capsys.readouterr()
    return code, json.loads(out)


def _fresh_text_default(mt, base: Path, manifest: Path, capsys, monkeypatch, *flags):
    """A fresh default-cache run under the bypass flag (always extracts)."""
    monkeypatch.setenv("LOS_NO_CACHE", "1")
    try:
        return _run_text_default(mt, base, manifest, capsys, *flags)
    finally:
        monkeypatch.delenv("LOS_NO_CACHE", raising=False)


def _text_views(cache: Path, digest: str):
    page = (cache / digest / "pp-0001.txt").read_bytes()
    index = json.loads((cache / digest / "index.json").read_text(encoding="utf-8"))
    return page, index


def _index_semantics(index: dict) -> dict:
    """An index record minus its built stamp (one-day clock, not cache)."""
    assert "built" in index
    return {key: value for key, value in index.items() if key != "built"}


def _text_nodes(root: Path) -> dict:
    return {node_id: state for node_id, state in read_state(root).items()
            if node_id.startswith("cache.text:")}


def _digest_of(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def test_text_spec_covers_the_independent_inventory():
    mt = _load_material_text()
    assert mt.TEXT_NODE_VERSION == 1
    assert "tools/material_text.py" in mt.TEXT_PRODUCER_FILES
    assert tuple(mt.TEXT_INPUT_KINDS) == TEXT_INPUTS
    digest = "ab" * 32
    spec = mt._text_spec(digest)
    assert spec.id == f"cache.text:{digest}" and spec.version == 1
    assert len(spec.direct_inputs) == len(TEXT_INPUTS) == 3
    assert set(spec.direct_inputs) == {
        f"cache.text.{kind}:{digest}" for kind in TEXT_INPUTS}
    inputs = mt._text_inputs(digest, 2)
    assert set(inputs) == set(spec.direct_inputs)
    assert inputs[f"cache.text.source:{digest}"] == digest
    assert inputs[f"cache.text.extractor:{digest}"] == mt.EXTRACTOR
    assert inputs[f"cache.text.pages:{digest}"] == "2"
    # The default anchor is the module's own verified root, never inferred.
    assert mt.CACHE_DIR == mt.REPO / "generated" / "text-cache"
    assert mt.REPO == Path(mt.__file__).resolve().parents[1]


@needs_pdftotext
def test_text_source_mutation_matches_fresh(tmp_path: Path, capsys, monkeypatch):
    mt = _load_material_text()
    first = _tiny_pdf("First edition text")
    spec = {"deck-a.pdf": first, "deck-b.pdf": _tiny_pdf("Steady text")}
    fake, base, manifest = _text_world(tmp_path, mt, monkeypatch, spec)
    code, cold = _run_text_default(mt, base, manifest, capsys, "--build")
    assert code == 0 and cold["extracted"] == 2
    assert len(_text_nodes(fake)) == 2
    (base / "deck-a.pdf").write_bytes(_tiny_pdf("Second edition text"))
    code, warm = _run_text_default(mt, base, manifest, capsys, "--refresh")
    assert code == 0
    assert (warm["cached"], warm["extracted"], warm["pruned"]) == (1, 1, 1)
    assert warm["stale"] == ["deck-a.pdf"]
    new_digest = _digest_of((base / "deck-a.pdf").read_bytes())
    assert f"cache.text:{new_digest}" in _text_nodes(fake)
    warm_views = {}
    for rel in ("deck-a.pdf", "deck-b.pdf"):
        warm_views[rel] = _text_views(
            mt.CACHE_DIR, _digest_of((base / rel).read_bytes()))
    code, _ = _fresh_text_default(mt, base, manifest, capsys, monkeypatch, "--refresh")
    assert code == 0
    for rel in ("deck-a.pdf", "deck-b.pdf"):
        page, index = _text_views(mt.CACHE_DIR, _digest_of((base / rel).read_bytes()))
        old_page, old_index = warm_views[rel]
        assert page == old_page
        assert _index_semantics(index) == _index_semantics(old_index)


@needs_pdftotext
def test_text_extractor_mutation_matches_fresh(tmp_path: Path, capsys, monkeypatch):
    mt = _load_material_text()
    spec = {"deck-a.pdf": _tiny_pdf("Extractor text")}
    fake, base, manifest = _text_world(tmp_path, mt, monkeypatch, spec)
    code, _ = _run_text_default(mt, base, manifest, capsys, "--build")
    assert code == 0
    digest = _digest_of(spec["deck-a.pdf"])
    assert mt._default_text_lookup(digest, 1) is not None
    monkeypatch.setattr(mt, "EXTRACTOR", "other-extractor")
    assert mt._default_text_lookup(digest, 1) is None
    code, warm = _run_text_default(mt, base, manifest, capsys, "--refresh")
    assert code == 0 and (warm["cached"], warm["extracted"]) == (0, 1)
    page, index = _text_views(mt.CACHE_DIR, digest)
    assert index["extractor"] == "other-extractor"
    code, _ = _fresh_text_default(mt, base, manifest, capsys, monkeypatch, "--refresh")
    assert code == 0
    fresh_page, fresh_index = _text_views(mt.CACHE_DIR, digest)
    assert (page, _index_semantics(index)) == (fresh_page, _index_semantics(fresh_index))
    # Re-hit under the new identity: files and node agree again.
    code, warm2 = _run_text_default(mt, base, manifest, capsys, "--refresh")
    assert code == 0 and (warm2["cached"], warm2["extracted"]) == (1, 0)


@needs_pdftotext
def test_text_pages_mutation_matches_fresh(tmp_path: Path, capsys, monkeypatch):
    mt = _load_material_text()
    spec = {"deck-a.pdf": _tiny_pdf("Paging text")}
    fake, base, manifest = _text_world(tmp_path, mt, monkeypatch, spec)
    code, _ = _run_text_default(mt, base, manifest, capsys, "--build")
    assert code == 0
    digest = _digest_of(spec["deck-a.pdf"])
    assert mt._default_text_lookup(digest, 1) is not None
    monkeypatch.setattr(mt, "_page_count", lambda path: 2)
    assert mt._default_text_lookup(digest, 2) is None
    code, warm = _run_text_default(mt, base, manifest, capsys, "--refresh")
    assert code == 0
    code, fresh = _fresh_text_default(mt, base, manifest, capsys, monkeypatch, "--refresh")
    assert code == 0
    # pdftotext refuses the out-of-range page on both sides alike.
    assert warm == fresh
    assert warm["skipped"] == [{"material": "deck-a.pdf", "reason": "extract-failed"}]


@needs_pdftotext
def test_text_producer_mutation_matches_fresh(tmp_path: Path, capsys, monkeypatch):
    mt = _load_material_text()
    spec = {"deck-a.pdf": _tiny_pdf("Producer text A"),
            "deck-b.pdf": _tiny_pdf("Producer text B")}
    fake, base, manifest = _text_world(tmp_path, mt, monkeypatch, spec)
    code, _ = _run_text_default(mt, base, manifest, capsys, "--build")
    assert code == 0
    staged = fake / "tools" / "material_text.py"
    staged.write_text(staged.read_text(encoding="utf-8") + "\n# a10 producer touch\n",
                      encoding="utf-8")
    digest_a = _digest_of(spec["deck-a.pdf"])
    assert mt._default_text_lookup(digest_a, 1) is None
    code, warm = _run_text_default(mt, base, manifest, capsys, "--refresh")
    assert code == 0 and (warm["cached"], warm["extracted"]) == (0, 2)
    warm_views = {}
    for rel in ("deck-a.pdf", "deck-b.pdf"):
        warm_views[rel] = _text_views(
            mt.CACHE_DIR, _digest_of((base / rel).read_bytes()))
    code, _ = _fresh_text_default(mt, base, manifest, capsys, monkeypatch, "--refresh")
    assert code == 0
    for rel in ("deck-a.pdf", "deck-b.pdf"):
        page, index = _text_views(mt.CACHE_DIR, _digest_of((base / rel).read_bytes()))
        old_page, old_index = warm_views[rel]
        assert page == old_page
        assert _index_semantics(index) == _index_semantics(old_index)
    code, warm2 = _run_text_default(mt, base, manifest, capsys, "--refresh")
    assert code == 0 and (warm2["cached"], warm2["extracted"]) == (2, 0)


@needs_pdftotext
def test_text_runtime_mutation_matches_fresh(tmp_path: Path, capsys, monkeypatch):
    import learning_os.derived.engine as engine_module

    mt = _load_material_text()
    spec = {"deck-a.pdf": _tiny_pdf("Runtime text")}
    fake, base, manifest = _text_world(tmp_path, mt, monkeypatch, spec)
    code, _ = _run_text_default(mt, base, manifest, capsys, "--build")
    assert code == 0
    monkeypatch.setattr(engine_module, "runtime_digest", lambda: "e" * 64)
    digest = _digest_of(spec["deck-a.pdf"])
    assert mt._default_text_lookup(digest, 1) is None
    code, warm = _run_text_default(mt, base, manifest, capsys, "--refresh")
    assert code == 0 and (warm["cached"], warm["extracted"]) == (0, 1)
    page, index = _text_views(mt.CACHE_DIR, digest)
    code, _ = _fresh_text_default(mt, base, manifest, capsys, monkeypatch, "--refresh")
    assert code == 0
    fresh_page, fresh_index = _text_views(mt.CACHE_DIR, digest)
    assert (page, _index_semantics(index)) == (fresh_page, _index_semantics(fresh_index))
    code, warm2 = _run_text_default(mt, base, manifest, capsys, "--refresh")
    assert code == 0 and (warm2["cached"], warm2["extracted"]) == (1, 0)


@needs_pdftotext
def test_text_corrupt_page_reprojects_and_matches_fresh(tmp_path: Path, capsys, monkeypatch):
    mt = _load_material_text()
    spec = {"deck-a.pdf": _tiny_pdf("Original page text")}
    fake, base, manifest = _text_world(tmp_path, mt, monkeypatch, spec)
    code, _ = _run_text_default(mt, base, manifest, capsys, "--build")
    assert code == 0
    digest = _digest_of(spec["deck-a.pdf"])
    page_path = mt.CACHE_DIR / digest / "pp-0001.txt"
    good = page_path.read_bytes()
    page_path.write_text("Altered content\n", encoding="utf-8")
    calls = []
    real_page_text = mt._page_text

    def counted(path, page):
        calls.append((str(path), page))
        return real_page_text(path, page)

    monkeypatch.setattr(mt, "_page_text", counted)
    code, warm = _run_text_default(mt, base, manifest, capsys, "--refresh")
    assert code == 0 and (warm["cached"], warm["extracted"]) == (1, 0)
    assert calls == []
    assert page_path.read_bytes() == good
    warm_page, warm_index = _text_views(mt.CACHE_DIR, digest)
    code, _ = _fresh_text_default(mt, base, manifest, capsys, monkeypatch, "--refresh")
    assert code == 0
    fresh_page, fresh_index = _text_views(mt.CACHE_DIR, digest)
    assert (warm_page, _index_semantics(warm_index)) == (fresh_page, _index_semantics(fresh_index))


@needs_pdftotext
def test_text_corrupt_blob_matches_fresh(tmp_path: Path, capsys, monkeypatch):
    mt = _load_material_text()
    spec = {"deck-a.pdf": _tiny_pdf("Blob text")}
    fake, base, manifest = _text_world(tmp_path, mt, monkeypatch, spec)
    code, _ = _run_text_default(mt, base, manifest, capsys, "--build")
    assert code == 0
    digest = _digest_of(spec["deck-a.pdf"])
    node_id = f"cache.text:{digest}"
    state = read_state(fake)[node_id]
    blob = fake / "generated" / "derived-state" / state.blob
    blob.write_bytes(b"\x00\xff not json {{{")
    assert mt._default_text_lookup(digest, 1) is None
    # Valid files but no node: rebuild from source, never adopt.
    code, warm = _run_text_default(mt, base, manifest, capsys, "--refresh")
    assert code == 0 and (warm["cached"], warm["extracted"]) == (0, 1)
    assert mt._default_text_lookup(digest, 1) is not None
    warm_page, warm_index = _text_views(mt.CACHE_DIR, digest)
    code, _ = _fresh_text_default(mt, base, manifest, capsys, monkeypatch, "--refresh")
    assert code == 0
    fresh_page, fresh_index = _text_views(mt.CACHE_DIR, digest)
    assert (warm_page, _index_semantics(warm_index)) == (fresh_page, _index_semantics(fresh_index))


@needs_pdftotext
def test_two_unrelated_texts_invalidate_independently(tmp_path: Path, capsys, monkeypatch):
    mt = _load_material_text()
    spec = {"deck-a.pdf": _tiny_pdf("Text A one"),
            "deck-b.pdf": _tiny_pdf("Text B one")}
    fake, base, manifest = _text_world(tmp_path, mt, monkeypatch, spec)
    code, _ = _run_text_default(mt, base, manifest, capsys, "--build")
    assert code == 0
    (base / "deck-b.pdf").write_bytes(_tiny_pdf("Text B two"))
    calls = []
    real_page_text = mt._page_text

    def counted(path, page):
        calls.append(Path(path).name)
        return real_page_text(path, page)

    monkeypatch.setattr(mt, "_page_text", counted)
    code, warm = _run_text_default(mt, base, manifest, capsys, "--refresh")
    assert code == 0 and (warm["cached"], warm["extracted"]) == (1, 1)
    assert calls == ["deck-b.pdf"]


@needs_pdftotext
def test_text_custom_cache_stays_file_only(tmp_path: Path, capsys, monkeypatch):
    mt = _load_material_text()
    data = _tiny_pdf("Custom path text")
    spec = {"deck-a.pdf": data}
    fake, base, manifest = _text_world(tmp_path, mt, monkeypatch, spec)
    custom = tmp_path / "textworld" / "custom"
    digest = _digest_of(data)

    def run_custom(*flags):
        code = mt.main(["--manifest", str(manifest), "--materials-root", str(base),
                        "--cache-dir", str(custom), *flags])
        out, _ = capsys.readouterr()
        return code, json.loads(out)

    code, summary = run_custom("--build")
    assert code == 0 and summary["extracted"] == 1
    assert _text_nodes(fake) == {}
    assert not (fake / "generated" / "derived-state").exists()
    assert mt.cache_index(custom, digest)["sha256"] == digest
    # Corruption on a custom path re-extracts (legacy: no node to project).
    (custom / digest / "pp-0001.txt").write_text("Altered\n", encoding="utf-8")
    calls = []
    real_page_text = mt._page_text
    monkeypatch.setattr(
        mt, "_page_text",
        lambda path, page: (calls.append(page), real_page_text(path, page))[1])
    code, summary = run_custom("--refresh")
    assert code == 0 and (summary["cached"], summary["extracted"]) == (0, 1)
    assert calls == [1]
    assert _text_nodes(fake) == {}
    assert not (fake / "generated" / "derived-state").exists()


@needs_pdftotext
@needs_pdftotext
def test_text_warm_run_uses_one_shared_session(tmp_path: Path, capsys, monkeypatch):
    """Warm lookups batch into one session: N materials, one identity."""
    import learning_os.derived.engine as engine_module

    mt = _load_material_text()
    spec = {"deck-a.pdf": _tiny_pdf("Session text A"),
            "deck-b.pdf": _tiny_pdf("Session text B")}
    fake, base, manifest = _text_world(tmp_path, mt, monkeypatch, spec)
    code, _ = _run_text_default(mt, base, manifest, capsys, "--build")
    assert code == 0
    calls = []
    real_identity = engine_module.digest_code_identity

    def counted(root):
        calls.append(root)
        return real_identity(root)

    monkeypatch.setattr(engine_module, "digest_code_identity", counted)
    code, warm = _run_text_default(mt, base, manifest, capsys, "--refresh")
    assert code == 0 and (warm["cached"], warm["extracted"]) == (2, 0)
    assert len(calls) == 1


@needs_pdftotext
def test_text_shared_digest_counts_match_single_pass(tmp_path: Path, capsys, monkeypatch):
    """Two materials, identical bytes: the second serves from the first's
    publish within the run, exactly as one lookup per material does."""
    mt = _load_material_text()
    data = _tiny_pdf("Shared bytes text")
    spec = {"deck-a.pdf": data, "deck-b.pdf": data}
    fake, base, manifest = _text_world(tmp_path, mt, monkeypatch, spec)
    code, cold = _run_text_default(mt, base, manifest, capsys, "--build")
    assert code == 0 and (cold["cached"], cold["extracted"]) == (1, 1)
    digest = _digest_of(data)
    assert len(_text_nodes(fake)) == 1
    index = json.loads((mt.CACHE_DIR / digest / "index.json").read_text(encoding="utf-8"))
    assert index["material"] == "deck-a.pdf"
    code, warm = _run_text_default(mt, base, manifest, capsys, "--refresh")
    assert code == 0 and (warm["cached"], warm["extracted"]) == (2, 0)


@needs_pdftotext
def test_text_coherent_tamper_reextracts(tmp_path: Path, capsys, monkeypatch):
    """Files rewritten coherently (fresh hashes, same extractor) still
    rebuild: the node value, not the view, is the authority."""
    mt = _load_material_text()
    spec = {"deck-a.pdf": _tiny_pdf("True page text")}
    fake, base, manifest = _text_world(tmp_path, mt, monkeypatch, spec)
    code, _ = _run_text_default(mt, base, manifest, capsys, "--build")
    assert code == 0
    digest = _digest_of(spec["deck-a.pdf"])
    page_path = mt.CACHE_DIR / digest / "pp-0001.txt"
    page_path.write_text("Coherent lies\n", encoding="utf-8")
    index_path = mt.CACHE_DIR / digest / "index.json"
    index = json.loads(index_path.read_text(encoding="utf-8"))
    index["pages_sha256"] = [hashlib.sha256(b"Coherent lies\n").hexdigest()]
    index_path.write_text(json.dumps(index), encoding="utf-8")
    assert mt._index_valid(mt.CACHE_DIR, digest, 1)
    code, warm = _run_text_default(mt, base, manifest, capsys, "--refresh")
    assert code == 0 and (warm["cached"], warm["extracted"]) == (0, 1)
    assert "True page text" in page_path.read_text(encoding="utf-8")


@needs_pdftotext
def test_text_skipped_order_matches_manifest_order(tmp_path: Path, capsys, monkeypatch):
    """Refusals print in manifest order although phases split them."""
    mt = _load_material_text()
    data = _tiny_pdf("Order text")
    spec = {"deck-a.pdf": data, "../outside.pdf": None, "gone.pdf": None}
    fake, base, manifest = _text_world(tmp_path, mt, monkeypatch, spec)
    real_count = mt._page_count
    monkeypatch.setattr(
        mt, "_page_count",
        lambda path: 99 if Path(path).name == "deck-a.pdf" else real_count(path))
    code, summary = _run_text_default(mt, base, manifest, capsys, "--refresh")
    assert code == 0
    assert [entry["material"] for entry in summary["skipped"]] == [
        "../outside.pdf", "deck-a.pdf", "gone.pdf"]
    assert [entry["reason"] for entry in summary["skipped"]] == [
        "boundary", "extract-failed", "missing"]


@needs_pdftotext
def test_text_explicit_default_dir_uses_derived_nodes(tmp_path: Path, capsys, monkeypatch):
    """Passing --cache-dir equal to the default selects the same path:
    behavior keys on the selected location, never on flag presence."""
    mt = _load_material_text()
    spec = {"deck-a.pdf": _tiny_pdf("Explicit default text")}
    fake, base, manifest = _text_world(tmp_path, mt, monkeypatch, spec)
    code = mt.main(["--manifest", str(manifest), "--materials-root", str(base),
                    "--cache-dir", str(mt.CACHE_DIR), "--build"])
    out, _ = capsys.readouterr()
    assert code == 0 and json.loads(out)["extracted"] == 1
    digest = _digest_of(spec["deck-a.pdf"])
    assert mt._default_text_lookup(digest, 1) is not None
    code, warm = _run_text_default(mt, base, manifest, capsys, "--refresh")
    assert code == 0 and (warm["cached"], warm["extracted"]) == (1, 0)


@needs_pdftotext
def test_text_default_writes_stay_in_default_cache_and_repo(
        tmp_path: Path, capsys, monkeypatch):
    mt = _load_material_text()
    spec = {"deck-a.pdf": _tiny_pdf("Scoped text")}
    fake, base, manifest = _text_world(tmp_path, mt, monkeypatch, spec)
    before = {path for path in base.rglob("*")}
    code, _ = _run_text_default(mt, base, manifest, capsys, "--build")
    assert code == 0
    assert {path for path in base.rglob("*")} == before
    digest = _digest_of(spec["deck-a.pdf"])
    assert (mt.CACHE_DIR / digest / "index.json").is_file()
    assert _text_nodes(fake) != {}
    # The real repository is untouched: no text node beside this root.
    from learning_os.derived.store import read_state as real_read_state

    assert [name for name in real_read_state(REPO_ROOT)
            if name.startswith("cache.text:")] == []
