"""Compute each byte once (#112, S3): the shared digest layer, one walk per
validation, text-cache and local-only pins, the GEN-INPUT pre-filter, the
receipt sidecar, and the fingerprint exclusion of declared local-only
attachments with its resolver transition."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from learning_os import digests
from learning_os.contracts.local_attachments import LOCAL_ATTACHMENTS_RELATIVE


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
    """A present, pinned local-only attachment owned by the demo note."""
    note = root / "knowledge/notes/mathematics/note-demo.md"
    text = note.read_text(encoding="utf-8")
    if "attachments:" not in text:
        note.write_text(text.replace(
            "sources: [source-demo-book]\n",
            f"sources: [source-demo-book]\nattachments:\n  - {SCAN_REL}\n", 1),
            encoding="utf-8")
    (root / SCAN_REL).parent.mkdir(parents=True, exist_ok=True)
    (root / SCAN_REL).write_bytes(data)
    (root / LOCAL_ATTACHMENTS_RELATIVE).write_text(
        "schema_version: 1\ncontract: learningos-local-attachments\nfiles:\n"
        f"  {SCAN_REL}:\n    bytes: {len(data)}\n"
        f"    sha256: sha256:{hashlib.sha256(data).hexdigest()}\n",
        encoding="utf-8")


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
