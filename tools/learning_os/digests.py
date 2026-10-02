"""One per-process, stat-gated cache for file bytes and hashes (#112).

Five costs share one cause: nothing remembers what was already proven about
a file. The canonical fingerprint, the status-cache pins, the validator's
receipt checks and the local-attachment pin check each re-read the same
bytes in one process — a transaction fingerprints pre and post, a manifest
rebuild fingerprints live and stamps, a status miss pins and then validates.
This module is the one choke point they read through instead: the second
read of unchanged bytes in a process is a stat plus a dict lookup.

The gate is the file's stat, never the path alone: ``(inode, size, mtime_ns,
ctime_ns)``. Any realistic mutation — add, delete, replace, rewrite,
retarget, permission change — misses and re-reads; only a stat-preserving
rewrite (same size with forged times under a reused inode) would slip, the
same trust the status pins and the publication-window stat digest already
place in stat. There is deliberately no cross-process persistence: a
persisted stat-to-digest map would reduce the write guard to stat-equality
across processes, while the receipt sidecar (``rules.receipt_cache``)
persists per-receipt validation results instead, which recompute their
cross-receipt checks on every run.

Each caller keeps its own read semantics by injecting a reader: the
fingerprint passes its boundary-checked read, the local-attachment check
its plain streaming read. The layer never changes what a successful read
returns — it only skips the second one — so snapshots and validation
output are byte-identical with the cache warm or cold.

Memory is bounded: file contents cache up to ``_MAX_CACHED_FILE_BYTES``
per file and ``_MAX_CACHED_TOTAL_BYTES`` total (least-recently-used
eviction; larger files read through without storing), and digests up to
``_MAX_DIGEST_ENTRIES`` entries. Concurrent readers may duplicate a read
but never observe wrong bytes: every hit re-stats first.
"""

from __future__ import annotations

import hashlib
import os
from collections import OrderedDict
from collections.abc import Callable, Iterable
from pathlib import Path

__all__ = ["file_content", "file_sha256", "clear"]

#: Files larger than this are hashed without caching their bytes: one
#: giant file must not flush the whole cache. The largest canonical file
#: today is a ~2.3 MB workspace plan.
_MAX_CACHED_FILE_BYTES = 8 * 1024 * 1024

#: Total cached bytes across all roots in this process. The canonical
#: tree is ~39 MB without the local-only scans; this covers it with
#: headroom, and anything past it degrades to today's re-reads.
_MAX_CACHED_TOTAL_BYTES = 64 * 1024 * 1024

#: Memoized digests across all roots: hex strings, so the bound is a
#: count. Past it the oldest entries re-hash on next use.
_MAX_DIGEST_ENTRIES = 32768

#: (root, relpath) -> ((inode, size, mtime_ns, ctime_ns), bytes).
_CONTENT: OrderedDict[tuple[str, str], tuple[tuple, bytes]] = OrderedDict()
_CONTENT_BYTES = 0

#: (root, relpath) -> ((inode, size, mtime_ns, ctime_ns), hex digest).
_DIGESTS: OrderedDict[tuple[str, str], tuple[tuple, str]] = OrderedDict()

#: Distinct root spellings seen -> their canonical path. Callers mix
#: resolved and unresolved spellings of one repository in a process
#: (the transaction service resolves, the loader keeps what it was
#: given); without this the same file caches twice and the second walk
#: never hits. A pure path memo, not cached proof: entries are never
#: stat-gated and ``clear()`` leaves them alone. One small entry per
#: distinct spelling (one per repository in production).
_ROOTS: dict[str, str] = {}


def _canonical_root(root: Path) -> str:
    spelling = os.path.normpath(os.fspath(root))
    resolved = _ROOTS.get(spelling)
    if resolved is None:
        resolved = os.path.realpath(spelling)
        _ROOTS[spelling] = resolved
    return resolved


def _key(root: Path, path: Path) -> tuple[str, str] | None:
    """The cache key, or None for a path outside ``root`` (never cached)."""
    try:
        rel = path.relative_to(root)
    except ValueError:
        return None
    return (_canonical_root(root), rel.as_posix())


def _stat_tuple(path: Path) -> tuple[int, int, int, int]:
    """The identity a cached entry is gated on. Raises OSError like a read."""
    stat = path.stat()
    return (stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns)


def _store_content(key: tuple[str, str], stat: tuple, data: bytes) -> None:
    global _CONTENT_BYTES
    old = _CONTENT.pop(key, None)
    if old is not None:
        _CONTENT_BYTES -= len(old[1])
    _CONTENT[key] = (stat, data)
    _CONTENT_BYTES += len(data)
    while _CONTENT_BYTES > _MAX_CACHED_TOTAL_BYTES and _CONTENT:
        _evicted_key, (_evicted_stat, evicted) = _CONTENT.popitem(last=False)
        _CONTENT_BYTES -= len(evicted)


def _store_digest(key: tuple[str, str], stat: tuple, digest: str) -> None:
    _DIGESTS.pop(key, None)
    _DIGESTS[key] = (stat, digest)
    while len(_DIGESTS) > _MAX_DIGEST_ENTRIES:
        _DIGESTS.popitem(last=False)


def file_content(root: Path, path: Path, reader: Callable[[], bytes]) -> bytes:
    """The file's bytes, reading through ``reader`` at most once per stat.

    ``reader`` is the caller's own read (whatever errors it raises
    propagate unchanged, and nothing is stored). Files larger than
    ``_MAX_CACHED_FILE_BYTES`` always read through.
    """
    key = _key(root, path)
    stat = _stat_tuple(path)
    if key is not None:
        hit = _CONTENT.get(key)
        if hit is not None and hit[0] == stat:
            _CONTENT.move_to_end(key)
            return hit[1]
    data = reader()
    if key is not None and len(data) <= _MAX_CACHED_FILE_BYTES:
        _store_content(key, stat, data)
    return data


def file_sha256(
    root: Path, path: Path, read_blocks: Callable[[], Iterable[bytes]],
) -> str:
    """The file's hex SHA-256, hashing its blocks at most once per stat.

    ``read_blocks`` is the caller's own streaming read. A digest hit
    re-stats and returns; a content hit hashes the cached bytes without
    touching disk; otherwise the stream is hashed once, the digest is
    memoized, and the bytes join the content cache when they fit the
    per-file cap.
    """
    key = _key(root, path)
    stat = _stat_tuple(path)
    if key is not None:
        hit = _DIGESTS.get(key)
        if hit is not None and hit[0] == stat:
            _DIGESTS.move_to_end(key)
            return hit[1]
        content = _CONTENT.get(key)
        if content is not None and content[0] == stat:
            digest = hashlib.sha256(content[1]).hexdigest()
            _store_digest(key, stat, digest)
            return digest
    digest = hashlib.sha256()
    chunks: list[bytes] = []
    total = 0
    fits = True
    for block in read_blocks():
        digest.update(block)
        if fits:
            chunks.append(block)
            total += len(block)
            if total > _MAX_CACHED_FILE_BYTES:
                fits = False
                chunks = []
    hex_digest = digest.hexdigest()
    if key is not None:
        _store_digest(key, stat, hex_digest)
        if fits:
            _store_content(key, stat, b"".join(chunks))
    return hex_digest


def clear() -> None:
    """Empty both caches. Tests call this; production code never needs to."""
    global _CONTENT_BYTES
    _CONTENT.clear()
    _CONTENT_BYTES = 0
    _DIGESTS.clear()
