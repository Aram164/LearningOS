"""Compute each byte once (#112, S3): the shared digest layer, one walk per
validation, text-cache and local-only pins, the GEN-INPUT pre-filter, the
receipt sidecar, and the fingerprint exclusion of declared local-only
attachments with its resolver transition."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from repo_builders import declare_scan

from learning_os import digests


def _counted_blocks(path: Path, calls: list):
    def read():
        calls.append(path)
        with path.open("rb") as handle:
            while block := handle.read(1024 * 1024):
                yield block

    return read


def test_content_cache_reads_each_file_once_per_stat(tmp_path: Path):
    digests.clear()
    target = tmp_path / "note.md"
    target.write_bytes(b"first bytes")
    calls: list = []
    first = digests.file_content(tmp_path, target, lambda: calls.append(1) or target.read_bytes())
    second = digests.file_content(tmp_path, target, lambda: calls.append(1) or target.read_bytes())
    assert (first, second) == (b"first bytes", b"first bytes")
    assert len(calls) == 1
    # Same size, different bytes: ctime moves on every write, so this
    # misses even where the mtime granularity is coarse.
    target.write_bytes(b"FIRST BYTES")
    third = digests.file_content(tmp_path, target, lambda: calls.append(1) or target.read_bytes())
    assert third == b"FIRST BYTES"
    assert len(calls) == 2


def test_sha256_memo_hashes_each_stream_once_per_stat(tmp_path: Path):
    digests.clear()
    target = tmp_path / "scan.pdf"
    target.write_bytes(b"%PDF bytes" * 1000)
    calls: list = []
    first = digests.file_sha256(tmp_path, target, _counted_blocks(target, calls))
    second = digests.file_sha256(tmp_path, target, _counted_blocks(target, calls))
    assert first == second == hashlib.sha256(b"%PDF bytes" * 1000).hexdigest()
    assert len(calls) == 1
    target.write_bytes(b"%PDF bytes" * 999 + b"%PDF BYTE!")
    third = digests.file_sha256(tmp_path, target, _counted_blocks(target, calls))
    assert third != first
    assert len(calls) == 2


def test_replace_by_rename_misses_via_inode_and_ctime(tmp_path: Path):
    digests.clear()
    target = tmp_path / "note.md"
    target.write_bytes(b"v1")
    assert digests.file_content(tmp_path, target, target.read_bytes) == b"v1"
    staged = tmp_path / "note.md.new"
    staged.write_bytes(b"v1")
    staged.replace(target)
    calls: list = []
    assert digests.file_content(
        tmp_path, target, lambda: calls.append(1) or target.read_bytes()) == b"v1"
    assert len(calls) == 1


def test_paths_outside_the_root_are_never_cached(tmp_path: Path):
    digests.clear()
    elsewhere = tmp_path / "elsewhere.md"
    elsewhere.write_bytes(b"bytes")
    calls: list = []
    root = tmp_path / "root"
    root.mkdir()
    for _ in range(2):
        assert digests.file_content(
            root, elsewhere, lambda: calls.append(1) or elsewhere.read_bytes()) == b"bytes"
    assert len(calls) == 2


def test_root_spellings_share_one_entry(tmp_path: Path):
    """The transaction service resolves the root while the loader keeps
    the spelling it was given: both must hit the same entry."""
    digests.clear()
    target = tmp_path / "note.md"
    target.write_bytes(b"bytes")
    alias = tmp_path / "alias"
    alias.symlink_to(tmp_path, target_is_directory=True)
    calls: list = []
    first = digests.file_content(
        tmp_path, target, lambda: calls.append(1) or target.read_bytes())
    second = digests.file_content(
        alias, alias / "note.md", lambda: calls.append(1) or target.read_bytes())
    assert (first, second) == (b"bytes", b"bytes")
    assert len(calls) == 1


def test_eviction_bounds_memory_and_re_reads(tmp_path: Path, monkeypatch):
    digests.clear()
    monkeypatch.setattr(digests, "_MAX_CACHED_TOTAL_BYTES", 16)
    monkeypatch.setattr(digests, "_MAX_CACHED_FILE_BYTES", 16)
    first = tmp_path / "a.md"
    first.write_bytes(b"a" * 8)
    second = tmp_path / "b.md"
    second.write_bytes(b"b" * 8)
    third = tmp_path / "c.md"
    third.write_bytes(b"c" * 8)
    calls: list = []
    for path in (first, second, third):
        digests.file_content(tmp_path, path, lambda p=path: calls.append(p) or p.read_bytes())
    assert len(calls) == 3
    # The first entry no longer fits beside the other two: re-read.
    digests.file_content(tmp_path, first, lambda: calls.append(first) or first.read_bytes())
    assert calls.count(first) == 2


# ------------------------------------------------- fingerprint exclusion
SCAN_REL = "knowledge/attachments/note-demo/scan.pdf"


def _declare_scan(root: Path, data: bytes = b"%PDF scan\n") -> None:
    declare_scan(root, SCAN_REL, data)


def test_declared_scan_bytes_do_not_move_the_snapshot(mini_repo: Path):
    from learning_os.fingerprint import (
        canonical_data_and_stat_fingerprints,
        canonical_fingerprint,
        canonical_stat_digest,
        data_roots_fingerprint,
    )

    _declare_scan(mini_repo)
    digests.clear()
    before = (
        canonical_fingerprint(mini_repo),
        data_roots_fingerprint(mini_repo),
        canonical_data_and_stat_fingerprints(mini_repo),
        canonical_stat_digest(mini_repo),
    )
    # Rewrite the scan without re-pinning: the pin check still fails on
    # this (see test_local_attachments), but no snapshot moves.
    (mini_repo / SCAN_REL).write_bytes(b"%PDF REPLACED SCAN BYTES\n")
    digests.clear()
    after = (
        canonical_fingerprint(mini_repo),
        data_roots_fingerprint(mini_repo),
        canonical_data_and_stat_fingerprints(mini_repo),
        canonical_stat_digest(mini_repo),
    )
    assert after == before


def test_re_pinning_moves_the_snapshot_through_the_declaration(mini_repo: Path):
    from learning_os.fingerprint import canonical_fingerprint, data_roots_fingerprint

    _declare_scan(mini_repo)
    digests.clear()
    before_full = canonical_fingerprint(mini_repo)
    before_data = data_roots_fingerprint(mini_repo)
    _declare_scan(mini_repo, b"%PDF replacement scan\n")
    digests.clear()
    # The declaration lives under system/contracts: the guard moves, the
    # data-roots digest does not.
    assert canonical_fingerprint(mini_repo) != before_full
    assert data_roots_fingerprint(mini_repo) == before_data


def test_definition_1_reproduces_the_scan_sensitive_digest(mini_repo: Path):
    from learning_os.fingerprint import canonical_fingerprint, data_roots_fingerprint

    _declare_scan(mini_repo)
    digests.clear()
    old_full = canonical_fingerprint(mini_repo, definition=1)
    old_data = data_roots_fingerprint(mini_repo, definition=1)
    assert old_full != canonical_fingerprint(mini_repo)
    assert old_data != data_roots_fingerprint(mini_repo)
    (mini_repo / SCAN_REL).write_bytes(b"%PDF edited\n")
    digests.clear()
    assert canonical_fingerprint(mini_repo, definition=1) != old_full
    assert data_roots_fingerprint(mini_repo, definition=1) != old_data


def test_absent_scans_leave_both_definitions_equal(mini_repo: Path):
    """A machine without the scans computes identical snapshots under
    either definition: the cutover moves nothing where the scans are
    absent (CI, fresh clones)."""
    from learning_os.fingerprint import canonical_fingerprint, data_roots_fingerprint

    _declare_scan(mini_repo)
    (mini_repo / SCAN_REL).unlink()
    digests.clear()
    assert canonical_fingerprint(mini_repo, definition=1) == canonical_fingerprint(mini_repo)
    assert data_roots_fingerprint(mini_repo, definition=1) == data_roots_fingerprint(mini_repo)


@pytest.mark.parametrize("name", [
    "canonical_fingerprint",
    "data_roots_fingerprint",
    "canonical_stat_digest",
    "canonical_data_and_stat_fingerprints",
])
def test_unknown_fingerprint_definition_fails_closed(mini_repo: Path, name: str):
    import learning_os.fingerprint as fingerprint_module

    digests.clear()
    with pytest.raises(ValueError, match="unknown fingerprint definition"):
        getattr(fingerprint_module, name)(mini_repo, definition=9)


def test_second_fingerprint_walk_reads_no_bytes_from_disk(
        mini_repo: Path, monkeypatch: pytest.MonkeyPatch):
    import learning_os.fingerprint as fingerprint_module
    from learning_os.fingerprint import canonical_fingerprint

    _declare_scan(mini_repo)
    digests.clear()
    original = fingerprint_module.read_bytes_inside
    reads: dict[str, int] = {}

    def counted(root: Path, path: Path) -> bytes:
        key = path.relative_to(root).as_posix()
        reads[key] = reads.get(key, 0) + 1
        return original(root, path)

    monkeypatch.setattr(fingerprint_module, "read_bytes_inside", counted)
    first = canonical_fingerprint(mini_repo)
    second = canonical_fingerprint(mini_repo)
    assert first == second
    assert reads, "the walk read nothing at all — this proves nothing"
    assert SCAN_REL not in reads
    assert set(reads.values()) == {1}


# ------------------------------------------------- status-cache pins
def _text_cache_index(root: Path, entry: str = "ab" * 32) -> Path:
    path = root / "generated" / "text-cache" / entry / "index.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "_generated": {"warning": "GENERATED"},
        "sha256": entry,
        "pages": 1,
    }) + "\n", encoding="utf-8")
    return path


def test_corrupted_text_cache_index_misses_and_revalidates(mini_repo: Path):
    """GEN-JSON parses each text-cache index, so a corrupted one must
    miss the status cache (the #103 patch pinned the cache by name
    only and would have served the pre-corruption issues)."""
    import learning_os.validation_cache as vc
    from learning_os.loader import load_repo

    _text_cache_index(mini_repo)
    vc.status_issues(load_repo(mini_repo))  # warm
    assert vc.read_cached_static_issues(mini_repo) is not None
    (mini_repo / "generated" / "text-cache" / ("ab" * 32) / "index.json").write_text(
        "{ not json\n", encoding="utf-8")
    assert vc.read_cached_static_issues(mini_repo) is None
    issues = vc.status_issues(load_repo(mini_repo))
    assert any(i.code == "GEN-JSON" and i.severity == "E" for i in issues)


def test_new_text_cache_entry_misses(mini_repo: Path):
    import learning_os.validation_cache as vc
    from learning_os.loader import load_repo

    vc.status_issues(load_repo(mini_repo))  # warm, no text cache
    assert vc.read_cached_static_issues(mini_repo) is not None
    _text_cache_index(mini_repo)
    assert vc.read_cached_static_issues(mini_repo) is None


def test_rewritten_scan_misses_and_revalidates(mini_repo: Path):
    """Definition 2 took the scans out of the content fingerprint: the
    validator-inputs pin stats them instead, so a rewrite misses rather
    than serving the pre-rewrite issues."""
    import learning_os.validation_cache as vc
    from learning_os.loader import load_repo

    _declare_scan(mini_repo)
    assert vc.status_issues(load_repo(mini_repo)) is not None
    assert vc.read_cached_static_issues(mini_repo) is not None
    # Same size, different bytes: the pin stats (size, mtime, ctime),
    # and the rewrite moves mtime and ctime.
    (mini_repo / SCAN_REL).write_bytes(b"%PDF SCAN\n")
    assert vc.read_cached_static_issues(mini_repo) is None
    issues = vc.status_issues(load_repo(mini_repo))
    assert any(i.code == "ATTACH-LOCAL-CHANGED" and i.severity == "E"
               for i in issues)


def test_absent_then_present_scan_misses(mini_repo: Path):
    import learning_os.validation_cache as vc
    from learning_os.loader import load_repo

    _declare_scan(mini_repo)
    (mini_repo / SCAN_REL).unlink()
    vc.status_issues(load_repo(mini_repo))  # warm, scan absent
    assert vc.read_cached_static_issues(mini_repo) is not None
    (mini_repo / SCAN_REL).write_bytes(b"%PDF scan\n")
    assert vc.read_cached_static_issues(mini_repo) is None


# ------------------------------------------------- GEN-INPUT pre-filter
@pytest.mark.parametrize("text, expected", [
    ("See generated/concept-index.md for the list.", True),
    ("(generated/manifest.json)", True),
    ("\ngenerated/views are disposable", True),
    ("no reference here", False),
    ("https://sklearn.org/modules/generated/foo", False),
    ("xgenerated/y is a longer path", False),
    ("/generated/y has a leading slash", False),
    ("generated without the slash", False),
])
def test_generated_reference_predicate(text: str, expected: bool):
    from learning_os.rules.registries import _references_generated

    assert _references_generated(text) is expected


def test_gen_input_still_flags_a_canonical_reference(mini_repo: Path):
    from learning_os.loader import load_repo
    from learning_os.rules import validate

    note = mini_repo / "knowledge" / "notes" / "mathematics" / "note-demo.md"
    note.write_text(
        note.read_text(encoding="utf-8") + "\nSee generated/concept-index.md.\n",
        encoding="utf-8")
    issues = validate(load_repo(mini_repo), online=False)
    assert any(i.code == "GEN-INPUT" and i.severity == "E" for i in issues)


# ------------------------------------------------- one walk per validation
def test_validate_py_performs_one_canonical_walk(
        mini_repo: Path, monkeypatch: pytest.MonkeyPatch):
    """The validate.py flow (pins, load, seed, validate) walks the
    canonical content once; the unseeded flow walks it twice for
    identical issues."""
    import learning_os.fingerprint as fm
    import learning_os.validation_cache as vc
    from learning_os.fingerprint import seed_source_fingerprint
    from learning_os.genout import generate_all, write_outputs
    from learning_os.loader import load_repo
    from learning_os.rules import validate

    repo_built = load_repo(mini_repo)
    write_outputs(repo_built, generate_all(repo_built))

    original_walk = fm._fingerprint_roots
    original_read = fm.read_bytes_inside
    walks: list = []
    reads: dict[str, int] = {}

    def counted_walk(root: Path, rel_roots, **kwargs):
        walks.append(tuple(rel_roots))
        return original_walk(root, rel_roots, **kwargs)

    def counted_read(root: Path, path: Path) -> bytes:
        key = path.relative_to(root).as_posix()
        reads[key] = reads.get(key, 0) + 1
        return original_read(root, path)

    monkeypatch.setattr(fm, "_fingerprint_roots", counted_walk)
    monkeypatch.setattr(fm, "read_bytes_inside", counted_read)

    def flow(seed: bool):
        digests.clear()
        walks.clear()
        reads.clear()
        pins = vc.observe_pins(mini_repo)
        assert pins is not None
        repo = load_repo(mini_repo)
        if seed:
            seed_source_fingerprint(repo, f"sha256:{pins['canonical_fingerprint']}")
        issues = validate(repo, online=False)
        return (
            list(walks),
            dict(reads),
            [(i.severity, i.code, i.message, i.path) for i in issues],
        )

    unseeded_walks, _unseeded_reads, unseeded_issues = flow(seed=False)
    seeded_walks, seeded_reads, seeded_issues = flow(seed=True)
    assert len(unseeded_walks) == 2
    assert len(seeded_walks) == 1
    assert seeded_issues == unseeded_issues
    assert seeded_reads, "the walk read nothing — this proves nothing"
    assert set(seeded_reads.values()) == {1}


# ------------------------------------------------- receipt sidecar
def _commit_capture(root: Path, key: str, request_id: str):
    """One genuine v2 commit (receipt + ledger row)."""
    from learning_os.contracts.gateway import GatewayRequestContext
    from learning_os.transactions import TransactionService

    target = root / f"work/inbox/{key}.md"
    context = GatewayRequestContext(
        request_id=request_id, idempotency_key=key,
        capability="capture.create", channel="codex",
        intent_sha256="sha256:" + "1" * 64,
        approval_kind="operator-approval",
        approval_subject_sha256="sha256:" + "1" * 64,
    )
    return TransactionService(root).commit(
        capability="capture.create",
        writes={target: "committed\n"},
        artifact_ids=[f"capture:{key}"],
        expected_revisions={f"capture:{key}": 0},
        gateway_request=context,
    )


def _frozen(issues) -> list:
    return [(i.severity, i.code, i.message, i.path) for i in issues]


def test_new_receipts_record_the_fingerprint_definition(mini_repo: Path):
    import yaml

    from learning_os.fingerprint import FINGERPRINT_DEFINITION_VERSION

    result = _commit_capture(mini_repo, "defrec-a", "request-defrec-a")
    receipt = yaml.safe_load(
        (mini_repo / result.receipt_path).read_text(encoding="utf-8"))
    assert receipt["metadata"]["fingerprint_definition"] == FINGERPRINT_DEFINITION_VERSION
    assert receipt["metadata"]["fingerprint_definition"] == 2


def test_receipt_sidecar_warm_run_matches_cold(mini_repo: Path):
    import learning_os.rules.receipt_cache as rc
    from learning_os.loader import load_repo
    from learning_os.rules import validate

    _commit_capture(mini_repo, "warm-a", "request-warm-a")
    _commit_capture(mini_repo, "warm-b", "request-warm-b")
    sidecar = mini_repo / rc.SIDECAR_RELATIVE
    assert not sidecar.exists()
    cold = _frozen(validate(load_repo(mini_repo), online=False))
    assert sidecar.is_file()
    payload = json.loads(sidecar.read_text(encoding="utf-8"))
    assert payload["format"] == 2
    assert isinstance(payload["_generated"], dict)
    assert len(payload["entries"]) == 2
    warm = _frozen(validate(load_repo(mini_repo), online=False))
    assert warm == cold


def test_receipt_sidecar_validates_only_new_receipts_when_warm(
        mini_repo: Path, monkeypatch: pytest.MonkeyPatch):
    import learning_os.rules.receipt_cache as rc
    from learning_os.loader import load_repo
    from learning_os.rules import validate

    _commit_capture(mini_repo, "fresh-a", "request-fresh-a")
    validate(load_repo(mini_repo), online=False)
    original = rc._validate_fresh
    calls: list = []

    def counted(validator, path: Path, rel: str):
        calls.append(rel)
        return original(validator, path, rel)

    monkeypatch.setattr(rc, "_validate_fresh", counted)
    validate(load_repo(mini_repo), online=False)
    assert calls == []
    _commit_capture(mini_repo, "fresh-b", "request-fresh-b")
    validate(load_repo(mini_repo), online=False)
    assert len(calls) == 1 and calls[0].endswith(".yaml")


def test_receipt_sidecar_revalidates_a_changed_receipt(mini_repo: Path):
    import yaml

    import learning_os.rules.receipt_cache as rc
    from learning_os.loader import load_repo
    from learning_os.rules import validate

    result = _commit_capture(mini_repo, "changed-a", "request-changed-a")
    first = _frozen(validate(load_repo(mini_repo), online=False))
    assert not [i for i in first if i[1] == "TRANSACTION-RECEIPT"]
    receipt_path = mini_repo / result.receipt_path
    receipt = yaml.safe_load(receipt_path.read_text(encoding="utf-8"))
    receipt["x-tampered"] = True
    receipt_path.write_text(
        yaml.safe_dump(receipt, sort_keys=False, allow_unicode=True), encoding="utf-8")
    second = _frozen(validate(load_repo(mini_repo), online=False))
    assert any(code == "SCHEMA" and "transaction-receipt" in message
               for _, code, message, _ in second)
    third = _frozen(validate(load_repo(mini_repo), online=False))
    assert third == second
    assert (mini_repo / rc.SIDECAR_RELATIVE).is_file()


def test_receipt_sidecar_duplicate_key_matches_cold_and_warm(mini_repo: Path):
    import yaml

    from learning_os.loader import load_repo
    from learning_os.rules import validate

    _commit_capture(mini_repo, "dup-a", "request-dup-a")
    result_b = _commit_capture(mini_repo, "dup-b", "request-dup-b")
    receipt_path = mini_repo / result_b.receipt_path
    receipt = yaml.safe_load(receipt_path.read_text(encoding="utf-8"))
    receipt["request"]["idempotency_key"] = "dup-a"
    receipt_path.write_text(
        yaml.safe_dump(receipt, sort_keys=False, allow_unicode=True), encoding="utf-8")
    cold = _frozen(validate(load_repo(mini_repo), online=False))
    assert any(code == "TRANSACTION-RECEIPT" and "duplicate idempotency key" in message
               for _, code, message, _ in cold)
    warm = _frozen(validate(load_repo(mini_repo), online=False))
    assert warm == cold


def test_receipt_sidecar_duplicate_id_matches_cold_and_warm(mini_repo: Path):
    import yaml

    from learning_os.loader import load_repo
    from learning_os.rules import validate

    result_a = _commit_capture(mini_repo, "idt-a", "request-idt-a")
    receipt_a = yaml.safe_load(
        (mini_repo / result_a.receipt_path).read_text(encoding="utf-8"))
    result_b = _commit_capture(mini_repo, "idt-b", "request-idt-b")
    receipt_path = mini_repo / result_b.receipt_path
    receipt = yaml.safe_load(receipt_path.read_text(encoding="utf-8"))
    receipt["id"] = receipt_a["id"]
    receipt_path.write_text(
        yaml.safe_dump(receipt, sort_keys=False, allow_unicode=True), encoding="utf-8")
    cold = _frozen(validate(load_repo(mini_repo), online=False))
    assert any(code == "TRANSACTION-RECEIPT" and "duplicate transaction receipt id" in message
               for _, code, message, _ in cold)
    warm = _frozen(validate(load_repo(mini_repo), online=False))
    assert warm == cold


def test_corrupt_receipt_sidecar_falls_back_to_the_full_pass(mini_repo: Path):
    import learning_os.rules.receipt_cache as rc
    from learning_os.loader import load_repo
    from learning_os.rules import validate

    _commit_capture(mini_repo, "corrupt-a", "request-corrupt-a")
    cold = _frozen(validate(load_repo(mini_repo), online=False))
    sidecar = mini_repo / rc.SIDECAR_RELATIVE
    assert sidecar.is_file()
    sidecar.write_bytes(b"\x00\xff not json {{{")
    recovered = _frozen(validate(load_repo(mini_repo), online=False))
    assert recovered == cold
    # No phantom: the corrupt cache never surfaces as a GEN-JSON error
    # about itself, and the run rewrote a valid sidecar.
    assert not [i for i in recovered if i[1] == "GEN-JSON"]
    assert json.loads(sidecar.read_text(encoding="utf-8"))["format"] == 2


def test_receipt_sidecar_hash_settles_mtime_only_changes(
        mini_repo: Path, monkeypatch: pytest.MonkeyPatch):
    import os
    import time

    import learning_os.rules.receipt_cache as rc
    from learning_os.loader import load_repo
    from learning_os.rules import validate

    result = _commit_capture(mini_repo, "mtime-a", "request-mtime-a")
    cold = _frozen(validate(load_repo(mini_repo), online=False))
    original = rc._validate_fresh
    calls: list = []

    def counted(validator, path: Path, rel: str):
        calls.append(rel)
        return original(validator, path, rel)

    monkeypatch.setattr(rc, "_validate_fresh", counted)
    receipt_path = mini_repo / result.receipt_path
    later = time.time() + 30
    os.utime(receipt_path, (later, later))
    warm = _frozen(validate(load_repo(mini_repo), online=False))
    assert calls == []
    assert warm == cold
