"""The fixed quotation comparison preserves mathematical distinctions."""

from __future__ import annotations

import unicodedata

import pytest

from learning_os.domain.verbatim import (
    QuoteError,
    excerpt_digest,
    language,
    matches,
    normalise,
    quote_from_mapping,
)


@pytest.mark.parametrize(("excerpt", "page"), [
    ("ff fi fl ffi ffl", "ﬀ ﬁ ﬂ ﬃ ﬄ"),
    ("a'b'c'", "a′b’c‘"),
    ("Vollständigkeit", "Vollständig-\nkeit"),
    ("Bolzano-Weierstraß", "Bolzano-\nWeierstraß"),
    ("Wahrscheinlichkeit", "Wahr\u00adscheinlichkeit"),
    ("then ∃M", "then∃M"),
    ("GRÖSSE", unicodedata.normalize("NFD", "Größe")),
])
def test_fixed_variants_match(excerpt, page):
    assert matches(excerpt, page)


def test_matching_does_not_compatibility_fold_math_or_punctuation():
    assert not matches("x2", "x²")
    assert not matches("R", "ℝ")
    assert not matches("x-y", "x+y")
    assert not matches("", "any material")
    assert normalise("Vollständig-keit") != normalise("Vollständigkeit")


def test_digest_is_of_the_same_normalized_excerpt():
    assert excerpt_digest(" Die   Größe ") == excerpt_digest("DIEGRÖSSE")


@pytest.mark.parametrize(("text", "expected"), [
    ("Wenn die Folge einen Grenzwert hat, dann ist dieser für die Folge eindeutig.", "de"),
    ("If the sequence has a limit then this limit is unique for the sequence.", "en"),
    ("The Folge ist schön.", "und"),
])
def test_language_is_a_reported_observation(text, expected):
    assert language(text) == expected


@pytest.mark.parametrize(("text", "accepted"), [
    ("a" * 39, False), ("a" * 40, True),
    ("a" * 300, True), ("a" * 301, False),
    ("a " * 39, False),
])
def test_quote_bounds(text, accepted):
    item = {"ref": "material://source-book/book.pdf", "text": text, "page": 1}
    if accepted:
        assert quote_from_mapping(item).text == text
    else:
        with pytest.raises(QuoteError):
            quote_from_mapping(item)


@pytest.mark.parametrize("place", [
    {}, {"page": True}, {"page": 0}, {"page": 1, "window": "00:00-00:30"},
    {"page": 1, "page_end": 3}, {"window": "00:00-00:30", "page_end": 2},
])
def test_quote_requires_one_explicit_valid_place(place):
    with pytest.raises(QuoteError):
        quote_from_mapping({"ref": "material://source-book/book.pdf", "text": "a" * 40, **place})
