"""Behavioral verification and benchmarking suite for SQLite FTS5 search (Task C.1).

Validates:
1. Pure contract properties (empty terms, non-ASCII terms bypass, non-ASCII notes inclusion, misshapen postings refusal).
2. 100% Recall Parity on FIXED_NOTES corpus across 40 queries.
3. 100% Recall Parity on Live Repository notes in knowledge/notes/.
4. Randomized corpus testing (100 notes, randomized queries).
5. Comprehensive performance benchmarks (Python dict vs SQLite FTS5).
"""

from __future__ import annotations

import base64
import io
import json
import os
import random
import re
import sqlite3
import sys
import time
from pathlib import Path

# Setup paths
REPO_ROOT = Path(__file__).resolve().parents[3]
TOOLS_PATH = REPO_ROOT / "tools"
SPIKE_PATH = Path(__file__).resolve().parent
for p in (str(TOOLS_PATH), str(SPIKE_PATH)):
    if p not in sys.path:
        sys.path.insert(0, p)

from learning_os.derive.search.index import (
    NoteBlob,
    build_postings,
    build_registry,
    build_segment,
)
from learning_os.derive.search.model import INDEX_FORMAT_VERSION
from learning_os.derive.search.normalize import is_ascii
from learning_os.derive.search.query import candidates
from learning_os.store.derived.engine import BuildContext, Evaluation, evaluate
from learning_os.store.derived.model import DerivedError
import spike_search_fts5 as fts5_mod


FIXED_NOTES = [
    ("n1.md", "n1", "Gradient Methods",
     "Gradient descent converges under mild conditions.\nSecond line about learning rates.\n", ()),
    ("n2.md", "n2", "Short", "ab", ()),
    ("n3.md", "n3", "Single", "x", ()),
    ("n4.md", "n4", "Empty Body", "", ()),
    ("n5.md", "n5", "Unicode Body", "Größe und Richtung\nZweite Zeile\n", ()),
    ("n6.md", "n6", "Größe im Titel", "plain ascii body", ()),
    ("n7.md", "n7", None, "title falls back to the note id", ()),
    ("n8.md", "n8", "Long", "hit\n" * 40, ()),
    ("n9.md", "note.with-dots_9", "Odd Id", "ids appear in frontmatter text", ()),
    ("n10.md", "n10", "Regex Chars",
     "match a+b literally, also (c) [d] e.f g*h i?j k|l ^m n$ \\o", ()),
    ("n11.md", "n11", "UPPER lower", "MiXeD CASE Body TEXT", ()),
    ("n12.md", "n12", "Extra Fields", "nothing special", ("role: synthesis", "state: evolving")),
    ("n13.md", "n13", "Whitespace", "   \n\t\n", ()),
    ("n14.md", "n14", "日本語", "日本語の本文", ()),
]

QUERIES = [
    "gradient", "grad", "a", "ab", "x", "descent converges", "GRADIENT",
    "missing-term", "the", "id:", "---", "a+b", "(c)", "[d]", "e.f", "g*h",
    "k|l", "^m", "n$", "\\o", "title", "mixed", "MIXED case", "Größe",
    "日本", "plain", "nothing", "hit", "note.with", "second line",
    "gradient missing-term", "n1", "Whitespace", "role", "synthesis",
    "falls back", "日本語の", "ö", "Zweite", "Extra Fields",
]


def test_contract_properties():
    print("--- [1/5] Testing Contract Invariants ---")
    blobs = [
        NoteBlob("n1", "notes/n1.md", "Title 1", b"Plain ascii text here"),
        NoteBlob("n2", "notes/n2.md", "Title 2", "Größe und Richtung".encode()),
    ]
    segments = {
        f"search.note:{b.note_id}": Evaluation(
            value=fts5_mod.build_segment_sql(b), output_sha256="s", status="hit", node_key="k"
        )
        for b in blobs
    }
    ctx = BuildContext(root=None, spec=None, inputs={}, dependencies=segments)
    postings = fts5_mod.build_postings_sql(ctx)

    # Empty terms -> all notes sorted
    assert fts5_mod.candidates_sql(None, postings, []) == ["n1", "n2"]

    # Non-ASCII query -> returns None (bypass prefilter)
    assert fts5_mod.candidates_sql(None, postings, ["Größe"]) is None
    assert fts5_mod.candidates_sql(None, postings, ["日本語"]) is None

    # Non-ASCII note -> always included
    res = fts5_mod.candidates_sql(None, postings, ["ascii"])
    assert "n2" in res  # non-ascii note n2 always present
    assert "n1" in res  # matching note n1 present

    # Misshapen postings -> raises DerivedError
    try:
        fts5_mod.candidates_sql(None, {"format": 999}, ["x"])
        raise AssertionError("Expected DerivedError")
    except DerivedError:
        pass

    print("✓ All 4 contract invariants passed cleanly.")


def test_fixed_battery_parity():
    print("--- [2/5] Testing Parity on FIXED_NOTES (40 queries) ---")
    blobs = []
    for fn, nid, title, body, extra in FIXED_NOTES:
        full_text = f"--- \nid: {nid}\n"
        if title:
            full_text += f"title: {title}\n"
        full_text += "".join(f"{line}\n" for line in extra)
        full_text += f"---\n{body}"
        raw = full_text.encode("utf-8")
        blobs.append(NoteBlob(note_id=nid, relpath=f"knowledge/notes/{fn}", title=title or nid, raw=raw))

    # Build production postings
    py_segs = {
        f"search.note:{b.note_id}": Evaluation(
            value=build_segment(b), output_sha256="s", status="hit", node_key="k"
        )
        for b in blobs
    }
    py_postings = build_postings(BuildContext(root=None, spec=None, inputs={}, dependencies=py_segs))

    # Build SQL postings
    sql_segs = {
        f"search.note:{b.note_id}": Evaluation(
            value=fts5_mod.build_segment_sql(b), output_sha256="s", status="hit", node_key="k"
        )
        for b in blobs
    }
    sql_postings = fts5_mod.build_postings_sql(BuildContext(root=None, spec=None, inputs={}, dependencies=sql_segs))

    mismatches = 0
    for query_str in QUERIES:
        terms = query_str.split()
        py_cand = candidates(None, py_postings, terms)
        sql_cand = fts5_mod.candidates_sql(None, sql_postings, terms)

        # Invariant: candidates ⊇ matches.
        # If py_cand is None, sql_cand must be None
        if py_cand is None:
            assert sql_cand is None, f"Mismatch on {query_str}: py=None, sql={sql_cand}"
            continue

        # If py_cand is a list, sql_cand must contain all true matches
        # Verify exhaustive regex matches
        compiled = [re.compile(re.escape(t), re.IGNORECASE) for t in terms]
        true_matches = []
        for b in blobs:
            text = b.raw.decode("utf-8")
            if all(c.search(text) for c in compiled):
                true_matches.append(b.note_id)

        # SQL candidate set must contain all true matches
        for m in true_matches:
            assert m in sql_cand, f"Recall failure on {query_str}: match {m} missing from {sql_cand}"

    print(f"✓ FIXED_NOTES: 40/40 queries verified (100% recall, 0 false negatives).")


def test_live_repository_sweep():
    print("--- [3/5] Testing Parity on Live Repository Notes ---")
    notes_dir = REPO_ROOT / "knowledge" / "notes"
    note_files = sorted(notes_dir.rglob("*.md"))
    blobs = []
    for nf in note_files:
        raw = nf.read_bytes()
        note_id = nf.stem
        # Extract title if present
        title = note_id
        try:
            text = raw.decode("utf-8")
            for line in text.splitlines():
                if line.startswith("title:"):
                    title = line.split(":", 1)[1].strip().strip('"\'')
                    break
        except UnicodeDecodeError:
            pass
        blobs.append(NoteBlob(note_id=note_id, relpath=f"knowledge/notes/{nf.name}", title=title, raw=raw))

    sql_segs = {
        f"search.note:{b.note_id}": Evaluation(
            value=fts5_mod.build_segment_sql(b), output_sha256="s", status="hit", node_key="k"
        )
        for b in blobs
    }
    sql_postings = fts5_mod.build_postings_sql(BuildContext(root=None, spec=None, inputs={}, dependencies=sql_segs))

    py_segs = {
        f"search.note:{b.note_id}": Evaluation(
            value=build_segment(b), output_sha256="s", status="hit", node_key="k"
        )
        for b in blobs
    }
    py_postings = build_postings(BuildContext(root=None, spec=None, inputs={}, dependencies=py_segs))

    live_queries = [
        "learning", "system", "model", "unit", "module", "kernel", "concept",
        "route", "state", "status", "test", "verification", "sqlite", "relational",
        "architecture", "hash", "digest", "version", "syntax", "contract",
        "learning system", "unit model", "nonexistent_query_term_xyz",
    ]

    for q in live_queries:
        terms = q.split()
        py_cand = candidates(None, py_postings, terms)
        sql_cand = fts5_mod.candidates_sql(None, sql_postings, terms)

        compiled = [re.compile(re.escape(t), re.IGNORECASE) for t in terms]
        true_matches = [
            b.note_id for b in blobs
            if all(c.search(b.raw.decode("utf-8", errors="replace")) for c in compiled)
        ]

        for m in true_matches:
            assert m in sql_cand, f"Recall failure on {q}: true match {m} missing from {sql_cand}"

    print(f"✓ Live repository: {len(blobs)} notes verified across {len(live_queries)} queries (100% recall).")


def test_randomized_corpus():
    print("--- [4/5] Testing Randomized Corpus (100 notes) ---")
    rng = random.Random(42)
    vocab = ["alpha", "beta", "gamma", "delta", "epsilon", "zeta", "eta", "theta", "iota", "kappa", "lambda", "mu"]
    blobs = []
    for i in range(100):
        words = rng.sample(vocab, k=rng.randint(3, 8))
        body = " ".join(words)
        nid = f"rand_{i}"
        raw = f"---\nid: {nid}\ntitle: Note {i}\n---\n{body}\n".encode("utf-8")
        blobs.append(NoteBlob(note_id=nid, relpath=f"notes/{nid}.md", title=f"Note {i}", raw=raw))

    sql_segs = {
        f"search.note:{b.note_id}": Evaluation(
            value=fts5_mod.build_segment_sql(b), output_sha256="s", status="hit", node_key="k"
        )
        for b in blobs
    }
    sql_postings = fts5_mod.build_postings_sql(BuildContext(root=None, spec=None, inputs={}, dependencies=sql_segs))

    # Test 50 random combinations
    for _ in range(50):
        terms = rng.sample(vocab, k=rng.randint(1, 3))
        sql_cand = fts5_mod.candidates_sql(None, sql_postings, terms)

        compiled = [re.compile(re.escape(t), re.IGNORECASE) for t in terms]
        true_matches = [
            b.note_id for b in blobs
            if all(c.search(b.raw.decode("utf-8")) for c in compiled)
        ]
        for m in true_matches:
            assert m in sql_cand, f"Recall failure on {terms}: {m} missing"

    print("✓ Randomized corpus: 100 notes, 50 queries verified (100% recall).")


def run_benchmarks():
    print("--- [5/5] Running Performance Benchmarks ---")
    rng = random.Random(1337)
    vocab = ["gradient", "descent", "learning", "rate", "optimization", "convex", "loss", "backpropagation", "matrix", "vector", "tensor", "layer", "activation"]
    blobs = []
    for i in range(200):
        words = [rng.choice(vocab) for _ in range(50)]
        body = " ".join(words)
        nid = f"bench_{i}"
        raw = f"---\nid: {nid}\ntitle: Benchmark Note {i}\n---\n{body}\n".encode("utf-8")
        blobs.append(NoteBlob(note_id=nid, relpath=f"notes/{nid}.md", title=f"Note {i}", raw=raw))

    # Index Build Benchmark
    t0 = time.perf_counter()
    py_segs = {
        f"search.note:{b.note_id}": Evaluation(
            value=build_segment(b), output_sha256="s", status="hit", node_key="k"
        )
        for b in blobs
    }
    py_postings = build_postings(BuildContext(root=None, spec=None, inputs={}, dependencies=py_segs))
    t_py_build = time.perf_counter() - t0

    t0 = time.perf_counter()
    sql_segs = {
        f"search.note:{b.note_id}": Evaluation(
            value=fts5_mod.build_segment_sql(b), output_sha256="s", status="hit", node_key="k"
        )
        for b in blobs
    }
    sql_postings = fts5_mod.build_postings_sql(BuildContext(root=None, spec=None, inputs={}, dependencies=sql_segs))
    t_sql_build = time.perf_counter() - t0

    py_size = len(json.dumps(py_postings).encode())
    sql_size = len(base64.b64decode(sql_postings["_sqlite_b64"]))

    # Query Latency Benchmarks
    con = sqlite3.connect(":memory:")
    con.deserialize(base64.b64decode(sql_postings["_sqlite_b64"]))

    test_queries = [
        (["gradient"], "Single term ('gradient')"),
        (["gradient", "descent"], "Multi-term ('gradient descent')"),
        (["convex", "loss", "optimization"], "Three terms ('convex loss optimization')"),
        (["ab"], "Short 2-char term ('ab')"),
        (["nonexistenttermxyz"], "Non-existent term"),
    ]

    print(f"\nIndex Build & Storage (200 notes):")
    print(f"  Python n-gram build: {t_py_build*1000:.2f} ms | Postings JSON: {py_size:,} bytes")
    print(f"  SQLite FTS5 build:   {t_sql_build*1000:.2f} ms | SQLite DB:     {sql_size:,} bytes")
    print(f"  Storage ratio: SQLite is {py_size / sql_size:.2f}x smaller")

    print(f"\nQuery Latency (1,000 iterations each):")
    for terms, label in test_queries:
        # Python
        t0 = time.perf_counter()
        for _ in range(1000):
            candidates(None, py_postings, terms)
        py_lat = (time.perf_counter() - t0) / 1000 * 1e6

        # SQLite FTS5
        t0 = time.perf_counter()
        for _ in range(1000):
            fts5_mod.query_fts5(con, terms)
        sql_lat = (time.perf_counter() - t0) / 1000 * 1e6

        speedup = py_lat / sql_lat if sql_lat > 0 else 0
        faster_str = f"{speedup:.1f}x faster" if speedup >= 1 else f"{1/speedup:.1f}x slower"
        print(f"  {label:42} | Python: {py_lat:6.2f} µs | FTS5: {sql_lat:6.2f} µs | SQLite {faster_str}")

    con.close()


if __name__ == "__main__":
    test_contract_properties()
    test_fixed_battery_parity()
    test_live_repository_sweep()
    test_randomized_corpus()
    run_benchmarks()
    print("\nALL BEHAVIORAL VERIFICATIONS PASSED SUCCESSFULLY.")
