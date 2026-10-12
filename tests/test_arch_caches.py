"""A10 cache correctness, validation + receipt families only (4.3).

SPEC §14 + D-12: the validation static issues live in one named derived
node and each receipt verdict in its own per-artifact node. Every case
here runs cold, mutates exactly one input, runs warm, and asserts the
warm result equals a fresh ``LOS_NO_CACHE=1`` run.

Scope: ONLY ``cache.validation-static`` and ``cache.receipt:<rel>``.
A10 is NOT claimed here for material text, summaries, dossiers,
derived-state self-consistency, manifest, or search postings — those
families are unassigned to this task and remain uncovered.

The input inventory below is independent: it was written from the
scratch inventory (``scratch/validation-receipt-input-inventory.md``,
read from ``validation_cache.cache_pins`` and
``receipt_cache._current_pins`` before editing) and is hardcoded here.
It is never generated from NodeSpec declarations or the code under
test; the spec-coverage test verifies the code against it, not the
reverse.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

import pytest
from test_compute_once import _commit_capture

import learning_os.rules.receipt_cache as rc
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
