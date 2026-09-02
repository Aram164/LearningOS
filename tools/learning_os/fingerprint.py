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
"""

from __future__ import annotations

import hashlib
import os
import weakref
from pathlib import Path
from typing import TYPE_CHECKING

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

_SOURCE_FINGERPRINTS: weakref.WeakKeyDictionary[Repo, str] = weakref.WeakKeyDictionary()


def canonical_fingerprint(root: Path) -> str:
    """Return a stable digest of the authored canonical inputs under ``root``.

    Generated outputs and the revision ledger are excluded by the root list;
    dot-prefixed paths are skipped so editor scratch and VCS metadata cannot
    move the digest.
    """
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
            digest.update(rel.as_posix().encode("utf-8"))
            digest.update(b"\0")
            try:
                digest.update(read_bytes_inside(root, path))
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
