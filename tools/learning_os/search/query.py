"""Candidate retrieval over a validated postings value.

The index is a prefilter with one hard property: the candidate set must
contain every true match (``candidates ⊇ matches``). False positives are
harmless — the caller verifies every candidate with the current regex
implementation — so every uncertain case widens rather than narrows:

* a non-ASCII query term bypasses the prefilter entirely (None);
* a non-ASCII note is always a candidate;
* an empty term list matches everything (callers refuse empty queries
  before reaching here; this is the safe direction, not a code path).

The only IO is self-healing: a hash-verified but wrongly shaped postings
value is invalidated before raising, so the next call rebuilds it.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..derived.model import DerivedError
from ..derived.store import invalidate
from .model import POSTINGS_NODE_ID, valid_postings
from .normalize import term_grams


def candidates(root: Path, postings: dict[str, Any], terms: list[str]) -> list[str] | None:
    """Sorted note ids that may match ALL terms; None when unfilterable.

    Raises DerivedError on a postings value without our exact shape —
    hash-verified blobs can only arrive misshapen through tampering.
    """
    if not valid_postings(postings):
        invalidate(root, POSTINGS_NODE_ID)
        raise DerivedError("derived postings value has an invalid shape")
    notes = postings["notes"]
    if not terms:
        return sorted(notes)
    if any(not term.isascii() for term in terms):
        return None
    narrowed: set[str] | None = None
    for term in terms:
        uni, bi, tri = term_grams(term.lower())
        required: set[str] | None = None
        for table, grams in (
            (postings["uni"], uni),
            (postings["bi"], bi),
            (postings["tri"], tri),
        ):
            for gram in grams:
                holders = set(table.get(gram, ()))
                required = holders if required is None else required & holders
        # A term always requires at least one gram (terms are nonempty).
        assert required is not None
        narrowed = required if narrowed is None else narrowed & required
    assert narrowed is not None
    always = {note_id for note_id, info in notes.items() if not info["ascii_safe"]}
    return sorted((narrowed or set()) | always)
