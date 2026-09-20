"""Index shapes, node identities, and producer declarations (pure data).

A note segment is the immutable searchable unit for one durable note —
same note bytes always mean the same segment, so unchanged notes are
never re-indexed when another note changes. The postings node merges all
segments into gram -> note-id lookup tables plus per-note metadata.

Values crossing the engine boundary are plain JSON dicts; the validators
below treat a hash-verified blob with the wrong shape as tampering (loud),
because our own writers can never produce it.
"""

from __future__ import annotations

import re
from typing import Any

from ..derived.model import DERIVED_SUBSTRATE_FILES

#: Bumped whenever a segment or postings shape changes. Carried as the
#: node version, so a format change invalidates every cached index node.
INDEX_FORMAT_VERSION = 1

POSTINGS_NODE_ID = "search.postings"


def segment_node_id(note_id: str) -> str:
    """Logical derived node holding one note's searchable segment."""
    return f"search.note:{note_id}"


#: Implementation files whose bytes feed the segment/postings node keys.
#: Conservative on purpose: an extra producer only costs a rebuild, while
#: a missing one risks a stale index. query.py is deliberately absent —
#: candidate retrieval always runs fresh and produces no cached value.
SEGMENT_PRODUCER_FILES = (
    "tools/learning_os/search/index.py",
    "tools/learning_os/search/model.py",
    "tools/learning_os/search/normalize.py",
    *DERIVED_SUBSTRATE_FILES,
)
POSTINGS_PRODUCER_FILES = (
    "tools/learning_os/search/index.py",
    "tools/learning_os/search/model.py",
    *DERIVED_SUBSTRATE_FILES,
)

_HEX64_RE = re.compile(r"[0-9a-f]{64}")


def _is_str_list(value: Any) -> bool:
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


def valid_segment(value: Any) -> bool:
    """True when a loaded value has exactly the segment shape we write."""
    if not isinstance(value, dict):
        return False
    if value.get("format") != INDEX_FORMAT_VERSION:
        return False
    if not isinstance(value.get("note_id"), str) or not value["note_id"]:
        return False
    if not isinstance(value.get("path"), str) or not isinstance(value.get("title"), str):
        return False
    if not isinstance(value.get("content_sha256"), str) or not _HEX64_RE.fullmatch(
        value["content_sha256"]
    ):
        return False
    if type(value.get("ascii_safe")) is not bool:
        return False
    return all(_is_str_list(value.get(name)) for name in ("unigrams", "bigrams", "trigrams"))


def _valid_note_info(value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    if not isinstance(value.get("path"), str) or not isinstance(value.get("title"), str):
        return False
    if not isinstance(value.get("content_sha256"), str) or not _HEX64_RE.fullmatch(
        value["content_sha256"]
    ):
        return False
    return type(value.get("ascii_safe")) is bool


def valid_postings(value: Any) -> bool:
    """True when a loaded value has exactly the postings shape we write."""
    if not isinstance(value, dict):
        return False
    if value.get("format") != INDEX_FORMAT_VERSION:
        return False
    for name in ("uni", "bi", "tri"):
        table = value.get(name)
        if not isinstance(table, dict):
            return False
        if not all(isinstance(gram, str) and _is_str_list(ids) for gram, ids in table.items()):
            return False
    notes = value.get("notes")
    if not isinstance(notes, dict):
        return False
    return all(
        isinstance(note_id, str) and note_id and _valid_note_info(info)
        for note_id, info in notes.items()
    )
