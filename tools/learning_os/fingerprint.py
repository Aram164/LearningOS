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

The root list and the walk now live here once. ``transactions`` re-exports the
path-taking form; ``genout.projection.fingerprint`` wraps it with the ``Repo``
memoisation that publishing depends on.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

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
        files = [base] if base.is_file() else sorted(
            path for path in base.rglob("*") if path.is_file()
        )
        for path in files:
            rel = path.relative_to(root)
            if any(part.startswith(".") for part in rel.parts):
                continue
            digest.update(rel.as_posix().encode("utf-8"))
            digest.update(b"\0")
            digest.update(path.read_bytes())
            digest.update(b"\0")
    return digest.hexdigest()
