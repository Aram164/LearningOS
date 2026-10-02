"""Hostile filesystem and receipt-cache cases found during independent review."""

import json
import os
from pathlib import Path

import pytest
from test_compute_once import _commit_capture

from learning_os import digests
from learning_os.loader import load_repo
from learning_os.rules import validate


def _receipt_errors(root: Path):
    return [(i.code, i.message, i.path) for i in validate(load_repo(root), online=False)
            if i.severity == "E" and "transaction-receipt" in i.message]


def _corrupt_status(path: Path):
    content = path.read_bytes()
    assert b"status: committed" in content
    path.write_bytes(content.replace(b"status: committed", b"status: corrupted"))


def test_preserved_mtime_receipt_tampering_cannot_reuse_verdict(mini_repo: Path):
    result = _commit_capture(mini_repo, "tamper-stat", "request-tamper-stat")
    assert not _receipt_errors(mini_repo)
    path = mini_repo / result.receipt_path
    old = path.stat()
    _corrupt_status(path)
    os.utime(path, ns=(old.st_atime_ns, old.st_mtime_ns))
    assert (path.stat().st_size, path.stat().st_mtime_ns) == (old.st_size, old.st_mtime_ns)
    # Simulate the fresh process that loads the persisted sidecar.
    digests.clear()
    assert _receipt_errors(mini_repo)


def test_receipt_rewrite_after_parse_cannot_bless_new_bytes(mini_repo: Path, monkeypatch):
    import learning_os.rules.receipt_cache as cache

    result = _commit_capture(mini_repo, "parse-race", "request-parse-race")
    path = mini_repo / result.receipt_path
    original = cache._validate_fresh

    def rewrite_after_parse(validator, target, rel):
        verdict = original(validator, target, rel)
        if target == path:
            _corrupt_status(target)
        return verdict

    monkeypatch.setattr(cache, "_validate_fresh", rewrite_after_parse)
    _receipt_errors(mini_repo)
    monkeypatch.setattr(cache, "_validate_fresh", original)
    digests.clear()
    assert _receipt_errors(mini_repo)


def test_changed_sidecar_verdict_is_discarded(mini_repo: Path):
    import learning_os.rules.receipt_cache as cache

    result = _commit_capture(mini_repo, "cache-corrupt", "request-cache-corrupt")
    _corrupt_status(mini_repo / result.receipt_path)
    assert _receipt_errors(mini_repo)
    sidecar = mini_repo / cache.SIDECAR_RELATIVE
    data = json.loads(sidecar.read_text())
    rel = result.receipt_path.relative_to(mini_repo).as_posix()
    data["entries"][rel]["issues"] = []
    sidecar.write_text(json.dumps(data))
    digests.clear()
    assert _receipt_errors(mini_repo)


def test_receipt_cache_pins_the_schema_actually_loaded(mini_repo: Path):
    from learning_os.rules.core import Validator

    _commit_capture(mini_repo, "schema-race", "request-schema-race")
    old_validator = Validator(load_repo(mini_repo))
    schema = mini_repo / "system/schema/transaction-receipt.schema.json"
    content = schema.read_text()
    assert '"const": "committed"' in content
    schema.write_text(content.replace('"const": "committed"', '"const": "corrupted"'))
    # This run already loaded the old schema. It may only cache its proof
    # against that schema, never the new bytes found on disk afterwards.
    old_validator.check_transaction_receipts()
    new_validator = Validator(load_repo(mini_repo))
    new_validator.check_transaction_receipts()
    assert any(i.code == "SCHEMA" for i in new_validator.issues)


def test_warm_boundary_digest_refuses_retarget_to_external_hardlink(tmp_path: Path):
    from learning_os.derived.identity import digest_file

    root = tmp_path / "root"
    root.mkdir()
    shared = root / "shared.md"
    shared.write_bytes(b"private bytes")
    external = tmp_path / "external.md"
    os.link(shared, external)
    alias = root / "alias.md"
    alias.symlink_to(shared)
    digests.clear()
    admitted = digest_file(root, alias)
    alias.unlink()
    alias.symlink_to(external)
    warm = digest_file(root, alias)
    digests.clear()
    cold = digest_file(root, alias)
    assert warm == cold
    assert warm != admitted


@pytest.mark.parametrize("definition", [True, False, 1.0, 2.0, 9])
def test_unsupported_definition_cannot_settle_contract_drift(mini_repo: Path, definition):
    from learning_os.diagnostics.resolver import contract_only_drift_receipt
    from learning_os.fingerprint import data_roots_fingerprint

    receipt = {"id": "transaction-20260101-000001-001", "snapshot_after": "sha256:old",
               "metadata": {"fingerprint_definition": definition,
                            "data_roots_sha256": "sha256:" + data_roots_fingerprint(mini_repo)}}
    assert contract_only_drift_receipt(mini_repo, [receipt], "sha256:new") is None


@pytest.mark.parametrize("suffix, initial, changed, code", [
    ("json", '{"_generated": {}}', "{broken", "GEN-JSON"),
    ("md", "<!-- GENERATED -->\n", "no warning header\n", "GEN-HEADER"),
])
def test_nested_text_cache_input_edit_misses_status(
        mini_repo: Path, suffix, initial, changed, code):
    import learning_os.validation_cache as cache

    target = mini_repo / f"generated/text-cache/demo/pages/unexpected.{suffix}"
    target.parent.mkdir(parents=True)
    target.write_text(initial)
    cache.status_issues(load_repo(mini_repo))
    assert cache.read_cached_static_issues(mini_repo) is not None
    target.write_text(changed)
    assert cache.read_cached_static_issues(mini_repo) is None
    assert any(i.code == code for i in cache.status_issues(load_repo(mini_repo)))


def test_text_cache_index_symlink_target_edit_misses_status(mini_repo: Path):
    import learning_os.validation_cache as cache

    directory = mini_repo / "generated/text-cache/demo"
    directory.mkdir(parents=True)
    blob = directory / "blob.txt"
    blob.write_text('{"_generated": {}}')
    (directory / "index.json").symlink_to(blob)
    cache.status_issues(load_repo(mini_repo))
    assert cache.read_cached_static_issues(mini_repo) is not None
    blob.write_text("{broken")
    assert cache.read_cached_static_issues(mini_repo) is None
    assert any(i.code == "GEN-JSON" for i in cache.status_issues(load_repo(mini_repo)))


def test_non_utf8_attachment_declaration_is_reported_and_excludes_nothing(mini_repo: Path):
    from learning_os.contracts.local_attachments import check, local_paths
    from learning_os.fingerprint import canonical_fingerprint

    declaration = mini_repo / "system/contracts/local-attachments.yaml"
    declaration.write_bytes(b"\xffnot UTF-8")
    assert local_paths(mini_repo) == set()
    assert check(mini_repo, set())[0].code == "UNREADABLE"
    assert canonical_fingerprint(mini_repo) == canonical_fingerprint(mini_repo, definition=1)
