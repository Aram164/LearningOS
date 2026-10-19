"""Deterministic quotation presence, without observing files or judging support."""

from __future__ import annotations

import hashlib
import re
import unicodedata
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal

Language = Literal["de", "en", "und"]
_CHARACTERS = str.maketrans({
    "ﬀ": "ff", "ﬁ": "fi", "ﬂ": "fl", "ﬃ": "ffi", "ﬄ": "ffl",
    "′": "'", "’": "'", "‘": "'", "\u00ad": "",
})
_LINE_HYPHEN = re.compile(r"(?<=\w)-[ \t]*\r?\n[ \t]*(?=\w)")
_GERMAN = frozenset("der die das den dem des ein eine einer eines und oder ist sind wird werden für von mit auf im in zu zum zur dass nicht sich als auch bei aus durch eine einen einem dieser diese dieses wir man kann können sei seien gilt wenn dann".split())
_ENGLISH = frozenset("the a an and or is are was were be been being for of with on in to that not as also by from through this these those we can may let if then which it its our has have".split())


class QuoteError(ValueError):
    """The declared excerpt or place is malformed."""


def normalise(text: str) -> str:
    value = unicodedata.normalize("NFC", text.translate(_CHARACTERS)).casefold()
    return "".join(character for character in value if not character.isspace())


def matches(excerpt: str, observed_text: str) -> bool:
    needle = normalise(excerpt)
    if not needle:
        return False
    return any(needle in normalise(variant) for variant in (
        observed_text, _LINE_HYPHEN.sub("", observed_text)))


def excerpt_digest(text: str) -> str:
    return "sha256:" + hashlib.sha256(normalise(text).encode("utf-8")).hexdigest()


def language(text: str) -> Language:
    words = re.findall(r"[^\W\d_]+", text.casefold())
    de = sum(word in _GERMAN for word in words)
    en = sum(word in _ENGLISH for word in words)
    if de >= 3 and de > 2 * en:
        return "de"
    if en >= 3 and en > 2 * de:
        return "en"
    return "und"


@dataclass(frozen=True)
class Quote:
    ref: str
    text: str
    page: int | None = None
    page_end: int | None = None
    window: str | None = None
    node: str = ""
    note: str = ""


def quote_from_mapping(item: Mapping[str, object]) -> Quote:
    ref, text = item.get("ref"), item.get("text")
    if not isinstance(ref, str) or not ref.startswith("material://"):
        raise QuoteError("quote ref must name a material:// file")
    if not isinstance(text, str) or len(text) > 300 or len(normalise(text)) < 40:
        raise QuoteError("quote text needs at least 40 normalized characters and at most 300 raw characters")
    page, page_end, window = item.get("page"), item.get("page_end"), item.get("window")
    if (page is None) == (window is None):
        raise QuoteError("quote needs exactly one PDF page or transcript window")
    if page is not None and (type(page) is not int or page < 1):
        raise QuoteError("quote page must be a positive PDF page number")
    if page_end is not None and (type(page_end) is not int or page is None or page_end != page + 1):
        raise QuoteError("quote page_end may only name the next PDF page")
    if window is not None and (not isinstance(window, str) or not window.strip()):
        raise QuoteError("quote window must be a nonempty timestamp range")
    node, note = item.get("node", ""), item.get("note", "")
    if not isinstance(node, str) or not isinstance(note, str):
        raise QuoteError("quote node and note must be strings")
    return Quote(ref=ref, text=text, page=page, page_end=page_end,
                 window=window, node=node, note=note)
