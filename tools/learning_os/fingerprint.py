"""One content identity for the authored canonical inputs.

Two implementations of this digest existed until 2026-08-18:
``transactions.canonical_fingerprint`` produced the value a receipt records as
``snapshot_before``/``snapshot_after``, and ``genout.source_fingerprint``
produced the value the projection publishes as ``_generated.snapshot_id`` — the
token the UI hands back to guard its next write. They had the same root list and
the same walk, and nothing held them together. Adding a canonical root to one
and forgetting the other would leave the receipt describing a different state
than the one the write was guarded against, silently, which is exactly the class
of failure the receipt chain exists to prevent.

The root list, walk, and projection memoisation now live here once.
``transactions`` re-exports the path-taking form; projection code calls the
``Repo``-taking form without making validators depend on generation modules.

Every content read goes through the shared per-process digest layer
(``digests``): the second read of unchanged bytes in a process is a stat
plus a dict lookup, and snapshots are byte-identical warm or cold.
"""

from __future__ import annotations

import hashlib
import os
import re
import weakref
from pathlib import Path
from typing import TYPE_CHECKING

from . import digests
from .contracts.local_attachments import local_paths
from .pathing import PathBoundaryError, read_bytes_inside

if TYPE_CHECKING:
    from .loader import Repo

CANONICAL_ROOTS = (
    "knowledge",
    "sources",
    "records",
    "work",
    "curriculum",
    "projects",
    "system/schema",
    "system/contracts",
)

#: Fingerprint roots that are code contracts, not authored data. A move
#: confined to these roots still invalidates sealed envelopes (the write
#: guard keeps the full root list); it only lets the causal resolver tell
#: "contracts moved" apart from "data moved without a receipt".
CONTRACT_ROOTS = (
    "system/schema",
    "system/contracts",
)

#: The authored-data half of the canonical roots. Receipts record this
#: digest as ``metadata.data_roots_sha256`` so the resolver can compare
#: the current data state against the newest receipt's without trusting
#: any file the receipt did not describe.
DATA_ROOTS = tuple(
    root for root in CANONICAL_ROOTS if root not in CONTRACT_ROOTS
)

#: What the snapshot hex digests mean. 1 hashed every canonical file,
#: including declared local-only attachments; 2 excludes the declared
#: local-only bytes. The declaration file itself stays inside the walk,
#: so re-pinning still moves the snapshot, and the pin check still hashes
#: every present scan on a full validation. New receipts record this in
#: ``metadata.fingerprint_definition``; the operations resolver compares
#: a pre-exclusion receipt under its own definition.
FINGERPRINT_DEFINITION_VERSION = 2

#: Every definition this code can compute: the current one plus each
#: historical shape the resolver may need for an old receipt.
_KNOWN_DEFINITIONS = frozenset({1, FINGERPRINT_DEFINITION_VERSION})

_SOURCE_FINGERPRINTS: weakref.WeakKeyDictionary[Repo, str] = weakref.WeakKeyDictionary()


def seed_source_fingerprint(repo: Repo, snapshot_id: str) -> None:
    """Reuse a locked read's start snapshot while building its fresh manifest.

    The caller must keep the end-of-read fingerprint check: an external edit
    during the build still invalidates the result. No cache survives this Repo.
    """
    if not re.fullmatch(r"sha256:[a-f0-9]{64}", snapshot_id):
        raise ValueError("source fingerprint seed must be a SHA-256 snapshot ID")
    _SOURCE_FINGERPRINTS[repo] = snapshot_id.removeprefix("sha256:")


def _read(root: Path, path: Path) -> bytes:
    """One boundary-checked content read through the shared digest layer.

    The walk-counting tests patch ``read_bytes_inside`` in this module;
    that stays the disk-read seam, and a layer hit never reaches it.
    """
    return digests.file_content(root, path, lambda: read_bytes_inside(root, path))


def _excluded_local_paths(root: Path, definition: int) -> frozenset[str]:
    """Declared local-only attachments, excluded from definition 2 on.

    An unreadable declaration excludes nothing: hashing bytes that failed
    to declare is the fail-closed direction (the validator reports the
    declaration itself).
    """
    if definition < FINGERPRINT_DEFINITION_VERSION:
        return frozenset()
    return frozenset(local_paths(root))


def _check_definition(definition: int) -> None:
    if definition not in _KNOWN_DEFINITIONS:
        raise ValueError(f"unknown fingerprint definition: {definition!r}")


def _fingerprint_roots(
    root: Path, rel_roots, *, definition: int = FINGERPRINT_DEFINITION_VERSION,
) -> str:
    """The canonical walk over an explicit root list. One walk, two lists:
    the write guard keeps ``CANONICAL_ROOTS``; the data-roots digest keeps
    ``DATA_ROOTS``. Same bytes per root either way."""
    _check_definition(definition)
    excluded = _excluded_local_paths(root, definition)
    digest = hashlib.sha256()
    for rel_root in rel_roots:
        base = root / rel_root
        if not base.exists():
            continue
        files = [base] if base.is_file() or base.is_symlink() else sorted(
            path for path in base.rglob("*")
            if path.is_file() or path.is_symlink()
        )
        for path in files:
            rel = path.relative_to(root)
            if any(part.startswith(".") for part in rel.parts):
                continue
            if rel.as_posix() in excluded:
                continue
            digest.update(rel.as_posix().encode("utf-8"))
            digest.update(b"\0")
            try:
                digest.update(_read(root, path))
            except (OSError, PathBoundaryError):
                # An inadmissible link is still canonical filesystem state, so
                # make it move the guard without reading the external target.
                digest.update(b"<inadmissible-symlink>\0")
                if path.is_symlink():
                    try:
                        digest.update(os.readlink(path).encode("utf-8"))
                    except OSError:
                        digest.update(b"<unreadable>")
            digest.update(b"\0")
    return digest.hexdigest()


def _stat_line(path: Path) -> bytes:
    """Stat identity for change detection: size, times, mode, link value.

    No content reads: a second traversal over the same enumeration detects
    any realistic mutation (add, delete, replace, rewrite, retarget,
    permission change) without re-hashing bytes. ctime is included so a
    content change with a preserved mtime still moves the digest.
    """
    try:
        st = path.stat()
        line = f"{st.st_size}\0{st.st_mtime_ns}\0{st.st_ctime_ns}\0{st.st_mode}"
    except OSError:
        line = "<unstatable>"
    try:
        if path.is_symlink():
            try:
                line += f"\0link:{os.readlink(path)}"
            except OSError:
                line += "\0link:<unreadable>"
    except OSError:
        line += "\0link:<unreadable>"
    return line.encode("utf-8", errors="replace")


def canonical_data_and_stat_fingerprints(
    root: Path, *, definition: int = FINGERPRINT_DEFINITION_VERSION,
) -> tuple[str, str, str]:
    """One walk yielding canonical, data-roots, and stat digests.

    The canonical and data hex digests are byte-identical to calling
    :func:`canonical_fingerprint` and :func:`data_roots_fingerprint`
    separately: the data roots keep their relative order inside the
    canonical walk, and each file's content is read once for both. The
    stat digest covers the same enumeration without content reads, for
    cheap post-publication change detection.
    """
    _check_definition(definition)
    excluded = _excluded_local_paths(root, definition)
    data_set = set(DATA_ROOTS)
    canonical = hashlib.sha256()
    data = hashlib.sha256()
    stat = hashlib.sha256()
    for rel_root in CANONICAL_ROOTS:
        base = root / rel_root
        if not base.exists():
            continue
        files = [base] if base.is_file() or base.is_symlink() else sorted(
            path for path in base.rglob("*")
            if path.is_file() or path.is_symlink()
        )
        for path in files:
            rel = path.relative_to(root)
            if any(part.startswith(".") for part in rel.parts):
                continue
            if rel.as_posix() in excluded:
                continue
            rel_bytes = rel.as_posix().encode("utf-8")
            try:
                content = _read(root, path)
            except (OSError, PathBoundaryError):
                content = None
            for digest, want in ((canonical, True), (data, rel_root in data_set)):
                if not want:
                    continue
                digest.update(rel_bytes)
                digest.update(b"\0")
                if content is not None:
                    digest.update(content)
                else:
                    digest.update(b"<inadmissible-symlink>\0")
                    if path.is_symlink():
                        try:
                            digest.update(os.readlink(path).encode("utf-8"))
                        except OSError:
                            digest.update(b"<unreadable>")
                digest.update(b"\0")
            stat.update(rel_bytes)
            stat.update(b"\0")
            stat.update(_stat_line(path))
            stat.update(b"\0")
    return canonical.hexdigest(), data.hexdigest(), stat.hexdigest()


def canonical_stat_digest(
    root: Path, *, definition: int = FINGERPRINT_DEFINITION_VERSION,
) -> str:
    """Stat-only digest over the canonical enumeration, for change checks.

    Same file set and order as the content walk, but no content reads.
    Any realistic mutation moves it; identical content with identical
    stat (same size, times, mode, link value) is accepted as unchanged.
    """
    _check_definition(definition)
    excluded = _excluded_local_paths(root, definition)
    digest = hashlib.sha256()
    for rel_root in CANONICAL_ROOTS:
        base = root / rel_root
        if not base.exists():
            continue
        files = [base] if base.is_file() or base.is_symlink() else sorted(
            path for path in base.rglob("*")
            if path.is_file() or path.is_symlink()
        )
        for path in files:
            rel = path.relative_to(root)
            if any(part.startswith(".") for part in rel.parts):
                continue
            if rel.as_posix() in excluded:
                continue
            digest.update(rel.as_posix().encode("utf-8"))
            digest.update(b"\0")
            digest.update(_stat_line(path))
            digest.update(b"\0")
    return digest.hexdigest()


def canonical_fingerprint(
    root: Path, *, definition: int = FINGERPRINT_DEFINITION_VERSION,
) -> str:
    """Return a stable digest of the authored canonical inputs under ``root``.

    Generated outputs and the revision ledger are excluded by the root list;
    dot-prefixed paths are skipped so editor scratch and VCS metadata cannot
    move the digest. Declared local-only attachments are excluded from
    definition 2 on; definition 1 reproduces the pre-exclusion digest for
    the operations resolver's transition comparison.
    """
    return _fingerprint_roots(root, CANONICAL_ROOTS, definition=definition)


def data_roots_fingerprint(
    root: Path, *, definition: int = FINGERPRINT_DEFINITION_VERSION,
) -> str:
    """Return a stable digest of the authored-data roots under ``root``.

    The same walk as :func:`canonical_fingerprint` over ``DATA_ROOTS``
    only: ``system/schema`` and ``system/contracts`` moves leave this
    digest alone. Read-only diagnostics compare it against the newest
    receipt's recorded value; it never guards a write.
    """
    return _fingerprint_roots(root, DATA_ROOTS, definition=definition)


def source_fingerprint(repo: Repo) -> str:
    """Memoise the digest externally for one loaded repository snapshot.

    A ``Repo`` is a read snapshot and must be reloaded after writes. Keeping the
    cache in a weak identity map makes that lifecycle explicit without silently
    adding mutable, undeclared state to the model object.
    """
    cached = _SOURCE_FINGERPRINTS.get(repo)
    if cached is not None:
        return cached
    result = canonical_fingerprint(repo.root)
    _SOURCE_FINGERPRINTS[repo] = result
    return result
