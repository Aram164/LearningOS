"""Content identity of the authored inputs behind one projection."""

from __future__ import annotations

from ...fingerprint import canonical_fingerprint
from ...loader import Repo


def source_fingerprint(repo: Repo) -> str:
    """Content identity of every authored input used by the projection.

    The digest itself lives in ``learning_os.fingerprint`` and is the same one
    a transaction receipt records, so the token the UI guards a write with and
    the token the receipt reports cannot drift apart. What this wrapper adds is
    memoisation.

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
    result = canonical_fingerprint(repo.root)
    try:
        repo._source_fingerprint_cache = result
    except (AttributeError, TypeError):
        pass          # a frozen or slotted Repo simply recomputes
    return result
