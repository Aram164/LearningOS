"""Compute each byte once (#112, S3): the shared digest layer, one walk per
validation, text-cache and local-only pins, the GEN-INPUT pre-filter, the
receipt sidecar, and the fingerprint exclusion of declared local-only
attachments with its resolver transition."""

from __future__ import annotations

import hashlib
from pathlib import Path

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
