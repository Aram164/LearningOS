"""Segment/postings builders and registry construction.

Pure over caller-supplied note bytes: admission (symlink refusal, owner
containment) stays with the caller — commands/reads.py reads with its own
``_note_bytes`` — so this layer can neither widen nor narrow what the
reader admits. Builders close over the discovered bytes they hash; the
before/after snapshot guard stays the race authority, not the cache.
"""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from ..derived.engine import BuildContext, Registry
from ..derived.model import DerivedError, NodeSpec
from ..derived.store import invalidate
from .model import (
    INDEX_FORMAT_VERSION,
    POSTINGS_NODE_ID,
    POSTINGS_PRODUCER_FILES,
    SEGMENT_PRODUCER_FILES,
    segment_node_id,
    valid_segment,
)
from .normalize import is_ascii, note_grams


@dataclass(frozen=True)
class NoteBlob:
    """One note's admitted bytes plus the identity it was read under."""

    note_id: str
    relpath: str
    title: str
    raw: bytes


def content_digest(raw: bytes) -> str:
    """Content identity of one note's raw bytes."""
    return hashlib.sha256(raw).hexdigest()


def identity_digest(note_id: str, relpath: str, title: str) -> str:
    """Identity binding id, path, and title: any of them moves the key."""
    return hashlib.sha256(f"{note_id}\0{relpath}\0{title}".encode()).hexdigest()


def content_input_id(note_id: str) -> str:
    return f"search.content:{note_id}"


def identity_input_id(note_id: str) -> str:
    return f"search.identity:{note_id}"


def build_segment(note: NoteBlob) -> dict[str, Any]:
    """Deterministic searchable segment for one note's bytes.

    Raises UnicodeDecodeError on non-UTF-8 bytes — the same refusal the
    exhaustive path produces when it decodes the same bytes.
    """
    text = note.raw.decode("utf-8")
    ascii_safe = is_ascii(note.raw)
    if ascii_safe:
        unigrams, bigrams, trigrams = note_grams(text.lower())
    else:
        unigrams, bigrams, trigrams = [], [], []
    return {
        "format": INDEX_FORMAT_VERSION,
        "note_id": note.note_id,
        "path": note.relpath,
        "title": note.title,
        "content_sha256": content_digest(note.raw),
        "ascii_safe": ascii_safe,
        "unigrams": unigrams,
        "bigrams": bigrams,
        "trigrams": trigrams,
    }


def segment_spec(note_id: str) -> NodeSpec:
    """Derived node holding one note's segment (inputs resolved by registry)."""
    return NodeSpec(
        id=segment_node_id(note_id),
        version=INDEX_FORMAT_VERSION,
        producer_files=SEGMENT_PRODUCER_FILES,
        direct_inputs=(content_input_id(note_id), identity_input_id(note_id)),
    )


def build_postings(ctx: BuildContext) -> dict[str, Any]:
    """Merge validated segment outputs into gram tables plus note metadata."""
    uni: dict[str, list[str]] = {}
    bi: dict[str, list[str]] = {}
    tri: dict[str, list[str]] = {}
    notes: dict[str, dict[str, Any]] = {}
    for node_id in sorted(ctx.dependencies):
        segment = ctx.dependencies[node_id].value
        if not valid_segment(segment):
            # Hash-verified but wrongly shaped: tampering, not staleness.
            # Invalidate first so the next evaluation rebuilds from bytes.
            invalidate(ctx.root, node_id)
            raise DerivedError(f"derived segment has an invalid shape: {node_id}")
        note_id = segment["note_id"]
        notes[note_id] = {
            "path": segment["path"],
            "title": segment["title"],
            "content_sha256": segment["content_sha256"],
            "ascii_safe": segment["ascii_safe"],
        }
        if not segment["ascii_safe"]:
            continue
        for table, grams in (
            (uni, segment["unigrams"]),
            (bi, segment["bigrams"]),
            (tri, segment["trigrams"]),
        ):
            for gram in grams:
                table.setdefault(gram, []).append(note_id)
    for table in (uni, bi, tri):
        for gram in table:
            table[gram] = sorted(table[gram])
    return {"format": INDEX_FORMAT_VERSION, "uni": uni, "bi": bi, "tri": tri, "notes": notes}


def postings_spec(segment_ids: tuple[str, ...]) -> NodeSpec:
    """Derived node merging every segment; membership changes move the key."""
    return NodeSpec(
        id=POSTINGS_NODE_ID,
        version=INDEX_FORMAT_VERSION,
        producer_files=POSTINGS_PRODUCER_FILES,
        dependencies=tuple(sorted(segment_ids)),
    )


def build_registry(blobs: list[NoteBlob]) -> tuple[Registry, dict[str, str]]:
    """Registry plus resolved inputs for one evaluation over these notes.

    Duplicate note ids fail closed: two blobs for one node would make the
    registry ambiguous about which bytes the key attests.
    """
    seen: set[str] = set()
    for blob in blobs:
        if blob.note_id in seen:
            raise DerivedError(f"duplicate search note id: {blob.note_id!r}")
        seen.add(blob.note_id)
    registry: dict[str, tuple[NodeSpec, Any]] = {}
    inputs: dict[str, str] = {}
    for blob in blobs:
        node_id = segment_node_id(blob.note_id)
        registry[node_id] = (segment_spec(blob.note_id), _segment_build(blob))
        inputs[content_input_id(blob.note_id)] = content_digest(blob.raw)
        inputs[identity_input_id(blob.note_id)] = identity_digest(
            blob.note_id, blob.relpath, blob.title)
    segment_ids = tuple(segment_node_id(blob.note_id) for blob in blobs)
    registry[POSTINGS_NODE_ID] = (postings_spec(segment_ids), build_postings)
    return registry, inputs


def _segment_build(note: NoteBlob) -> Callable[[BuildContext], dict[str, Any]]:
    """Build closure over the discovered bytes the input digests attest."""

    def build(_ctx: BuildContext) -> dict[str, Any]:
        return build_segment(note)

    return build
