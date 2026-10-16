"""ASCII-only n-grams for the conservative first index.

Current search is case-insensitive *substring* search, so the index is a
candidate prefilter only: every true match must survive filtering, while
false positives are harmless (the existing regex verification removes
them). Unicode case folding is deliberately out of scope for version 1 —
non-ASCII queries bypass the prefilter and non-ASCII notes are always
candidates — so ``str.lower`` here only ever sees ASCII text, where it
coincides with ``re.IGNORECASE``.
"""

from __future__ import annotations


def is_ascii(data: bytes) -> bool:
    """True when every byte is ASCII (equivalently: the text has no non-ASCII)."""
    return all(byte < 0x80 for byte in data)


def note_grams(lowered: str) -> tuple[list[str], list[str], list[str]]:
    """Sorted unique 1-, 2-, and 3-grams of already-lowered ASCII text."""
    unigrams = sorted(set(lowered))
    bigrams = sorted({lowered[index : index + 2] for index in range(len(lowered) - 1)})
    trigrams = sorted({lowered[index : index + 3] for index in range(len(lowered) - 2)})
    return unigrams, bigrams, trigrams


def term_grams(lowered_term: str) -> tuple[list[str], list[str], list[str]]:
    """Grams a lowered ASCII term requires of any text containing it.

    A 1- or 2-character term is its own gram; a longer term occurring in a
    text implies every one of its trigrams occurs there, so the conjunction
    is a necessary (not sufficient) condition for a substring match.
    """
    if len(lowered_term) <= 1:
        return [lowered_term], [], []
    if len(lowered_term) == 2:
        return [], [lowered_term], []
    return [], [], sorted(
        {lowered_term[index : index + 3] for index in range(len(lowered_term) - 2)}
    )
