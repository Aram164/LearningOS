"""SQLite FTS5 full-text search implementation for LearningOS (Task C.1).

Replaces the custom n-gram postings and candidate intersection engine
with SQLite FTS5 using the 'trigram' tokenizer. Maintains 100% contract parity:
- Empty terms: return all notes sorted
- Non-ASCII query term: return None (bypass prefilter, verify exhaustive)
- Non-ASCII notes: always included in candidates
- Substring recall: candidates ⊇ true matches (100% recall, zero false negatives)
- Fast trigram indexing via SQLite FTS5 virtual table
"""

from __future__ import annotations

import base64
import io
import os
import sqlite3
from pathlib import Path
from typing import Any, Mapping

import learning_os.derive.search.model as search_model
from learning_os.derive.search.model import (
    POSTINGS_NODE_ID,
    valid_postings,
    valid_segment,
)
from learning_os.derive.search.normalize import is_ascii, note_grams, term_grams
from learning_os.derive.search.index import (
    NoteBlob,
    content_digest,
    content_input_id,
    identity_digest,
    identity_input_id,
    segment_spec,
    postings_spec,
    _segment_build,
)
from learning_os.store.derived.engine import BuildContext, Registry
from learning_os.store.derived.model import DerivedError, NodeSpec
from learning_os.store.derived.store import invalidate

FTS5_SCHEMA = """
CREATE TABLE IF NOT EXISTS notes (
    note_id TEXT PRIMARY KEY,
    path TEXT,
    title TEXT,
    content_sha256 TEXT,
    ascii_safe INTEGER,
    body TEXT
);

CREATE VIRTUAL TABLE IF NOT EXISTS notes_fts USING fts5(
    note_id UNINDEXED,
    title,
    body,
    tokenize='trigram'
);
"""


def create_fts5_db() -> sqlite3.Connection:
    """Create an in-memory SQLite database initialized with FTS5 schema."""
    con = sqlite3.connect(":memory:")
    con.executescript(FTS5_SCHEMA)
    return con


def build_segment_sql(note: NoteBlob) -> dict[str, Any]:
    """Segment builder capturing note body for SQLite FTS5 while preserving n-grams."""
    text = note.raw.decode("utf-8")
    ascii_safe = is_ascii(note.raw)
    if ascii_safe:
        unigrams, bigrams, trigrams = note_grams(text.lower())
    else:
        unigrams, bigrams, trigrams = [], [], []
    return {
        "format": search_model.INDEX_FORMAT_VERSION,
        "note_id": note.note_id,
        "path": note.relpath,
        "title": note.title,
        "content_sha256": content_digest(note.raw),
        "ascii_safe": ascii_safe,
        "body": text,
        "unigrams": unigrams,
        "bigrams": bigrams,
        "trigrams": trigrams,
    }


def build_postings_sql(ctx: BuildContext) -> dict[str, Any]:
    """Merge segment outputs into SQLite FTS5 database and backward-compatible dict."""
    uni: dict[str, list[str]] = {}
    bi: dict[str, list[str]] = {}
    tri: dict[str, list[str]] = {}
    notes: dict[str, dict[str, Any]] = {}

    con = create_fts5_db()

    for node_id in sorted(ctx.dependencies):
        segment = ctx.dependencies[node_id].value
        if not valid_segment(segment):
            invalidate(ctx.root, node_id)
            raise DerivedError(f"derived segment has an invalid shape: {node_id}")
        note_id = segment["note_id"]
        body = segment.get("body", "")
        title = segment.get("title", "")
        path = segment.get("path", "")
        sha = segment.get("content_sha256", "")
        ascii_safe = bool(segment.get("ascii_safe"))

        notes[note_id] = {
            "path": path,
            "title": title,
            "content_sha256": sha,
            "ascii_safe": ascii_safe,
            "body": body,
        }

        con.execute(
            "INSERT OR REPLACE INTO notes VALUES (?, ?, ?, ?, ?, ?)",
            (note_id, path, title, sha, 1 if ascii_safe else 0, body),
        )
        if ascii_safe:
            con.execute(
                "INSERT INTO notes_fts VALUES (?, ?, ?)",
                (note_id, title, body),
            )

        if not ascii_safe:
            continue

        for table, grams in (
            (uni, segment.get("unigrams", [])),
            (bi, segment.get("bigrams", [])),
            (tri, segment.get("trigrams", [])),
        ):
            for gram in grams:
                table.setdefault(gram, []).append(note_id)

    for table in (uni, bi, tri):
        for gram in table:
            table[gram] = sorted(table[gram])

    # Commit all pending FTS5 transactions before serialization
    con.commit()
    sqlite_bytes = con.serialize()
    con.close()
    sqlite_b64 = base64.b64encode(sqlite_bytes).decode("ascii")

    return {
        "format": search_model.INDEX_FORMAT_VERSION,
        "uni": uni,
        "bi": bi,
        "tri": tri,
        "notes": notes,
        "_sqlite_b64": sqlite_b64,
    }


def query_fts5(con: sqlite3.Connection, terms: list[str]) -> list[str] | None:
    """Execute FTS5 candidate retrieval on an open SQLite connection."""
    if not terms:
        cur = con.execute("SELECT note_id FROM notes ORDER BY note_id")
        return [r[0] for r in cur.fetchall()]

    if any(not term.isascii() for term in terms):
        return None

    fts_terms = [t for t in terms if len(t) >= 3]
    short_terms = [t.lower() for t in terms if len(t) < 3]

    cand: set[str] | None = None

    if fts_terms:
        # Format as trigram search phrases
        escaped = [f'"{t.replace(chr(34), chr(34)+chr(34))}"' for t in fts_terms]
        match_expr = " AND ".join(escaped)
        try:
            cur = con.execute(
                "SELECT note_id FROM notes_fts WHERE notes_fts MATCH ?", (match_expr,)
            )
            cand = {r[0] for r in cur.fetchall()}
        except sqlite3.OperationalError:
            # Query phrase contains characters unsupported by FTS5 match syntax,
            # fall back to safe SQL LIKE substring search
            where = " AND ".join(["LOWER(title || ' ' || body) LIKE ?" for _ in fts_terms])
            params = [f"%{t.lower()}%" for t in fts_terms]
            cur = con.execute(f"SELECT note_id FROM notes WHERE {where}", params)
            cand = {r[0] for r in cur.fetchall()}

    if short_terms:
        where = " AND ".join(["LOWER(title || ' ' || body) LIKE ?" for _ in short_terms])
        params = [f"%{t}%" for t in short_terms]
        cur = con.execute(f"SELECT note_id FROM notes WHERE {where}", params)
        short_cand = {r[0] for r in cur.fetchall()}
        cand = short_cand if cand is None else cand & short_cand

    if cand is None:
        cand = set()

    # Invariant: non-ASCII notes are always included in candidates
    cur = con.execute("SELECT note_id FROM notes WHERE ascii_safe = 0")
    non_ascii = {r[0] for r in cur.fetchall()}

    return sorted(cand | non_ascii)


def candidates_sql(root: Path | None, postings: dict[str, Any], terms: list[str]) -> list[str] | None:
    """Candidate retrieval implementation using SQLite FTS5."""
    if not valid_postings(postings):
        if root is not None:
            invalidate(root, POSTINGS_NODE_ID)
        raise DerivedError("derived postings value has an invalid shape")

    notes = postings.get("notes", {})
    if not terms:
        return sorted(notes)

    if any(not term.isascii() for term in terms):
        return None

    # Check if we have serialized SQLite base64 or body available
    sqlite_b64 = postings.get("_sqlite_b64")
    if sqlite_b64:
        sqlite_bytes = base64.b64decode(sqlite_b64)
        con = sqlite3.connect(":memory:")
        con.deserialize(sqlite_bytes)
        try:
            return query_fts5(con, terms)
        finally:
            con.close()

    # If note bodies are present in notes dict, build ephemeral or use FTS5
    first_note = next(iter(notes.values()), None) if notes else None
    if first_note and "body" in first_note:
        con = create_fts5_db()
        try:
            for note_id, info in notes.items():
                title = info.get("title", "")
                body = info.get("body", "")
                path = info.get("path", "")
                sha = info.get("content_sha256", "")
                ascii_safe = bool(info.get("ascii_safe"))
                con.execute(
                    "INSERT INTO notes VALUES (?, ?, ?, ?, ?, ?)",
                    (note_id, path, title, sha, 1 if ascii_safe else 0, body),
                )
                if ascii_safe:
                    con.execute(
                        "INSERT INTO notes_fts VALUES (?, ?, ?)",
                        (note_id, title, body),
                    )
            return query_fts5(con, terms)
        finally:
            con.close()

    # Otherwise fall back to gram-based candidate filtering (for tests that construct synthetic postings)
    narrowed: set[str] | None = None
    for term in terms:
        uni, bi, tri = term_grams(term.lower())
        required: set[str] | None = None
        for table, grams in (
            (postings.get("uni", {}), uni),
            (postings.get("bi", {}), bi),
            (postings.get("tri", {}), tri),
        ):
            for gram in grams:
                holders = set(table.get(gram, ()))
                required = holders if required is None else required & holders
        assert required is not None
        narrowed = required if narrowed is None else narrowed & required

    assert narrowed is not None
    always = {note_id for note_id, info in notes.items() if not info.get("ascii_safe")}
    return sorted((narrowed or set()) | always)
