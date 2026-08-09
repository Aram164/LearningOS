"""Content identity of the authored inputs behind one projection."""

from __future__ import annotations

import hashlib

from ...loader import Repo

_FINGERPRINT_ROOTS = (
    "knowledge", "sources", "records", "work", "curriculum", "projects",
    "system/schema", "system/contracts",
)


def source_fingerprint(repo: Repo) -> str:
    """Content identity of every authored input used by the projection.

    Memoised on the ``Repo``. A ``Repo`` is the result of one ``load_repo``
    walk and is never mutated afterwards, so every caller holding the same
    instance is asking about the same bytes. Publishing alone asked twice —
    once for backlinks, once for the manifest — and each answer costs a full
    read-and-hash of every authored file. A write that changes the repository
    loads it again, which produces a new instance and therefore a new answer.
    """
    cached = getattr(repo, "_source_fingerprint_cache", None)
    if cached is not None:
        return cached
    digest = hashlib.sha256()
    for rel_root in _FINGERPRINT_ROOTS:
        base = repo.root / rel_root
        if not base.exists():
            continue
        files = [base] if base.is_file() else sorted(p for p in base.rglob("*") if p.is_file())
        for path in files:
            rel = path.relative_to(repo.root).as_posix()
            if any(part.startswith(".") for part in path.relative_to(repo.root).parts):
                continue
            digest.update(rel.encode("utf-8"))
            digest.update(b"\0")
            digest.update(path.read_bytes())
            digest.update(b"\0")
    result = digest.hexdigest()
    try:
        repo._source_fingerprint_cache = result
    except (AttributeError, TypeError):
        pass          # a frozen or slotted Repo simply recomputes
    return result
