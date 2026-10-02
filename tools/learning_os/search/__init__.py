"""Exact note search over the derived-state index.

A conservative n-gram prefilter narrows candidates; the current regex
verification still decides every hit. See model.py (shapes), normalize.py
(grams), index.py (builders), query.py (candidate retrieval).
"""

from __future__ import annotations

from .index import (
    NoteBlob,
    build_postings,
    build_registry,
    build_segment,
    content_digest,
    identity_digest,
    postings_spec,
    segment_spec,
)
from .model import (
    INDEX_FORMAT_VERSION,
    POSTINGS_NODE_ID,
    valid_postings,
    valid_segment,
)
from .query import candidates

__all__ = [
    "INDEX_FORMAT_VERSION",
    "POSTINGS_NODE_ID",
    "NoteBlob",
    "build_postings",
    "build_registry",
    "build_segment",
    "candidates",
    "content_digest",
    "identity_digest",
    "postings_spec",
    "segment_spec",
    "valid_postings",
    "valid_segment",
]
