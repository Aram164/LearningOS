"""Search index builders and the exhaustive-vs-index differential suite.

Commits 3-4 of the incremental-computation plan: the pure builder layer
plus the oracle proving indexed search equals exhaustive search across a
fixed battery, a seeded randomized corpus, every mutation class, and
every cache-corruption class.
"""

from __future__ import annotations

import random
import re
from pathlib import Path
from types import SimpleNamespace

import pytest

import learning_os.commands.reads as reads_module
import learning_os.search.index as search_index_module
from learning_os.commands.reads import (
    _exhaustive_content_search,
    _indexed_content_search,
    _note_collection,
    content_search,
)
from learning_os.derived import DerivedError, Evaluation, NodeSpec
from learning_os.search.index import (
    NoteBlob,
    build_postings,
    build_registry,
    build_segment,
    postings_spec,
    segment_spec,
)
from learning_os.search.model import (
    INDEX_FORMAT_VERSION,
    POSTINGS_NODE_ID,
    POSTINGS_PRODUCER_FILES,
    SEGMENT_PRODUCER_FILES,
    segment_node_id,
    valid_postings,
    valid_segment,
)
from learning_os.search.normalize import is_ascii, note_grams, term_grams
from learning_os.search.query import candidates

REPO_ROOT = Path(__file__).resolve().parent.parent


def _blob(note_id: str, text: str, title: str | None = None) -> NoteBlob:
    raw = text.encode("utf-8")
    return NoteBlob(
        note_id=note_id, relpath=f"knowledge/notes/{note_id}.md",
        title=title if title is not None else note_id, raw=raw)


# ---------------------------------------------------------------------------
# Grams.
# ---------------------------------------------------------------------------

def test_is_ascii():
    assert is_ascii(b"plain text 123")
    assert is_ascii(b"")
    assert not is_ascii("Größe".encode())


def test_note_grams_cover_substrings():
    uni, bi, tri = note_grams("gradient")
    assert "g" in uni and "t" in uni
    assert "gr" in bi and "nt" in bi
    assert tri == ["adi", "die", "ent", "gra", "ien", "rad"]
    assert uni == sorted(set(uni))
    assert bi == sorted(set(bi))


def test_note_grams_empty():
    assert note_grams("") == ([], [], [])


def test_term_grams_by_length():
    assert term_grams("a") == (["a"], [], [])
    assert term_grams("ab") == ([], ["ab"], [])
    assert term_grams("abc") == ([], [], ["abc"])
    assert term_grams("gradient")[2] == ["adi", "die", "ent", "gra", "ien", "rad"]


# ---------------------------------------------------------------------------
# Segments.
# ---------------------------------------------------------------------------

def test_build_segment_shape():
    segment = build_segment(_blob("n1", "The gradient descent converges."))
    assert valid_segment(segment)
    assert segment["note_id"] == "n1"
    assert segment["path"] == "knowledge/notes/n1.md"
    assert segment["ascii_safe"] is True
    assert "gra" in segment["trigrams"]
    assert "des" in segment["trigrams"]


def test_build_segment_non_ascii_has_no_grams():
    segment = build_segment(_blob("n1", "Größe und Richtung"))
    assert valid_segment(segment)
    assert segment["ascii_safe"] is False
    assert segment["unigrams"] == [] and segment["bigrams"] == [] and segment["trigrams"] == []


def test_build_segment_rejects_non_utf8_like_exhaustive():
    blob = NoteBlob(note_id="n1", relpath="knowledge/notes/n1.md", title="n1", raw=b"\xff\xfe")
    with pytest.raises(UnicodeDecodeError):
        build_segment(blob)


def test_segment_is_deterministic_in_bytes():
    first = build_segment(_blob("n1", "same text"))
    second = build_segment(_blob("n1", "same text"))
    assert first == second


def test_valid_segment_rejects_wrong_shapes():
    good = build_segment(_blob("n1", "text"))
    assert valid_segment(good)
    for broken in (
        {**good, "format": 999},
        {**good, "note_id": ""},
        {**good, "content_sha256": "zz"},
        {**good, "ascii_safe": "yes"},
        {**good, "trigrams": "gra"},
        {**good, "trigrams": [1]},
        {"not": "a segment"},
        ["a", "list"],
    ):
        assert not valid_segment(broken)


# ---------------------------------------------------------------------------
# Postings merge.
# ---------------------------------------------------------------------------

def _postings_ctx(*segments, root=None):
    from learning_os.derived import BuildContext

    root = root or Path("/nonexistent")
    dependencies = {
        segment_node_id(segment["note_id"]): Evaluation(
            value=segment, output_sha256="0" * 64, status="rebuilt", node_key="k")
        for segment in segments
    }
    spec = NodeSpec(id=POSTINGS_NODE_ID, version=INDEX_FORMAT_VERSION)
    return BuildContext(root=root, spec=spec, inputs={}, dependencies=dependencies)


def test_build_postings_merges_grams():
    postings = build_postings(_postings_ctx(
        build_segment(_blob("a", "gradient descent")),
        build_segment(_blob("b", "descent into detail")),
    ))
    assert valid_postings(postings)
    import hashlib

    assert postings["tri"]["gra"] == ["a"]
    assert postings["tri"]["des"] == ["a", "b"]
    assert postings["notes"]["a"]["content_sha256"] == hashlib.sha256(b"gradient descent").hexdigest()
    assert set(postings["notes"]) == {"a", "b"}


def test_build_postings_skips_grams_but_keeps_non_ascii_notes():
    postings = build_postings(_postings_ctx(build_segment(_blob("u", "Größe"))))
    assert valid_postings(postings)
    assert postings["tri"] == {}
    assert postings["notes"]["u"]["ascii_safe"] is False


def test_build_postings_is_order_independent():
    first = build_segment(_blob("a", "alpha"))
    second = build_segment(_blob("b", "beta"))
    assert build_postings(_postings_ctx(first, second)) == build_postings(
        _postings_ctx(second, first))


def test_build_postings_rejects_misshapen_segments(tmp_path: Path):
    from learning_os.derived import BuildContext

    ctx = BuildContext(
        root=tmp_path,
        spec=NodeSpec(id=POSTINGS_NODE_ID, version=INDEX_FORMAT_VERSION),
        inputs={},
        dependencies={
            segment_node_id("bad"): Evaluation(
                value={"format": 999}, output_sha256="0" * 64,
                status="rebuilt", node_key="k")
        },
    )
    with pytest.raises(DerivedError, match="invalid shape"):
        build_postings(ctx)


def test_valid_postings_rejects_wrong_shapes():
    good = build_postings(_postings_ctx(build_segment(_blob("a", "alpha"))))
    assert valid_postings(good)
    for broken in (
        {**good, "format": 2},
        {**good, "uni": {"a": "not-a-list"}},
        {**good, "notes": {"a": {"path": 1}}},
        {**good, "notes": []},
        {"format": INDEX_FORMAT_VERSION},
    ):
        assert not valid_postings(broken)


# ---------------------------------------------------------------------------
# Registry.
# ---------------------------------------------------------------------------

def test_build_registry_resolves_every_input():
    blobs = [_blob("a", "alpha"), _blob("b", "beta")]
    registry, inputs = build_registry(blobs)
    assert set(registry) == {segment_node_id("a"), segment_node_id("b"), POSTINGS_NODE_ID}
    for _node_id, (spec, _build) in registry.items():
        for name in spec.direct_inputs:
            assert name in inputs
    _spec, _build = registry[POSTINGS_NODE_ID]
    assert _spec.dependencies == (segment_node_id("a"), segment_node_id("b"))


def test_build_registry_rejects_duplicate_note_ids():
    with pytest.raises(DerivedError, match="duplicate"):
        build_registry([_blob("a", "one"), _blob("a", "two")])


def test_specs_carry_format_version():
    assert segment_spec("a").version == INDEX_FORMAT_VERSION
    assert postings_spec(()).version == INDEX_FORMAT_VERSION
    assert segment_spec("a").id == "search.note:a"


def test_declared_producer_files_exist():
    for rel in list(SEGMENT_PRODUCER_FILES) + list(POSTINGS_PRODUCER_FILES):
        assert (REPO_ROOT / rel).is_file(), f"renamed producer is untracked: {rel}"


# ---------------------------------------------------------------------------
# Candidate retrieval (pure).
# ---------------------------------------------------------------------------

def _indexed(*texts: str):
    blobs = [_blob(f"n{i}", text) for i, text in enumerate(texts)]
    segments = [build_segment(blob) for blob in blobs]
    return build_postings(_postings_ctx(*segments))


def test_candidates_narrow_ascii_queries(tmp_path: Path):
    postings = _indexed("gradient descent converges", "nothing relevant here")
    assert candidates(tmp_path, postings, ["gradient"]) == ["n0"]
    assert candidates(tmp_path, postings, ["nothing", "relevant"]) == ["n1"]
    assert candidates(tmp_path, postings, ["missing"]) == []
    assert candidates(tmp_path, postings, ["grad"]) == ["n0"]


def test_candidates_intersect_terms_and_case(tmp_path: Path):
    postings = _indexed("Gradient Descent", "gradient ascent")
    assert candidates(tmp_path, postings, ["gradient", "descent"]) == ["n0"]
    assert candidates(tmp_path, postings, ["GRADIENT"]) == ["n0", "n1"]


def test_candidates_bypass_on_unicode_query(tmp_path: Path):
    postings = _indexed("gradient descent")
    assert candidates(tmp_path, postings, ["Größe"]) is None


def test_candidates_always_include_non_ascii_notes(tmp_path: Path):
    postings = _indexed("plain ascii text", "Größe und Richtung")
    assert candidates(tmp_path, postings, ["xyzzy"]) == ["n1"]
    assert candidates(tmp_path, postings, ["plain"]) == ["n0", "n1"]


def test_candidates_reject_misshapen_postings(tmp_path: Path):
    with pytest.raises(DerivedError, match="invalid shape"):
        candidates(tmp_path, {"format": 999}, ["x"])


# ---------------------------------------------------------------------------
# Differential harness: indexed must equal exhaustive, byte for byte.
# ---------------------------------------------------------------------------

#: (filename, note id, title or None, body, extra frontmatter lines)
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


def _write_note(notes_dir: Path, filename: str, note_id: str,
                title: str | None, body: str, extra=()) -> Path:
    lines = ["---", f"id: {note_id}"]
    if title is not None:
        lines.append(f"title: {title}")
    lines.extend(extra)
    lines.append("---")
    target = notes_dir / filename
    target.write_text("\n".join(lines) + "\n" + body, encoding="utf-8")
    return target


def _write_corpus(root: Path, notes=FIXED_NOTES) -> Path:
    notes_dir = root / "knowledge" / "notes"
    notes_dir.mkdir(parents=True, exist_ok=True)
    for filename, note_id, title, body, *rest in notes:
        _write_note(notes_dir, filename, note_id, title, body, *(rest or [()]))
    return notes_dir


def _stage_producers(root: Path) -> None:
    """Copy the real producer bytes under a mini root (real wiring, real bytes)."""
    for rel in dict.fromkeys([*SEGMENT_PRODUCER_FILES, *POSTINGS_PRODUCER_FILES]):
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((REPO_ROOT / rel).read_bytes())


def _compiled(query: str):
    return [re.compile(re.escape(term), re.IGNORECASE) for term in query.split()]


def _ordered_notes(root: Path):
    repo = _note_collection(root)
    assert not repo.parse_failures, repo.parse_failures
    return sorted(repo.notes.values(), key=lambda note: note.id)


def _assert_agree(root: Path, query: str):
    """Full match-list equality: ids, order, paths, hashes, snippets."""
    ordered = _ordered_notes(root)
    terms = _compiled(query)
    expected = _exhaustive_content_search(root, ordered, terms)
    got = _indexed_content_search(root, ordered, terms, query.split())
    assert got == expected
    return expected


def _counting_builds(monkeypatch):
    counts = {"segments": 0, "postings": 0}
    original_segment = search_index_module.build_segment
    original_postings = search_index_module.build_postings

    def segment(note):
        counts["segments"] += 1
        return original_segment(note)

    def postings(ctx):
        counts["postings"] += 1
        return original_postings(ctx)

    monkeypatch.setattr(search_index_module, "build_segment", segment)
    monkeypatch.setattr(search_index_module, "build_postings", postings)
    return counts


def test_fixed_battery_agrees_fresh_and_warm(tmp_path: Path, monkeypatch):
    _write_corpus(tmp_path)
    _stage_producers(tmp_path)
    counts = _counting_builds(monkeypatch)
    for query in QUERIES:
        _assert_agree(tmp_path, query)
    # One corpus: every segment built once on the first query, then hits.
    assert counts == {"segments": len(FIXED_NOTES), "postings": 1}
    for query in QUERIES:
        _assert_agree(tmp_path, query)
    assert counts == {"segments": len(FIXED_NOTES), "postings": 1}


def test_battery_result_shapes(tmp_path: Path):
    _write_corpus(tmp_path)
    _stage_producers(tmp_path)
    assert _assert_agree(tmp_path, "missing-term") == []
    some = _assert_agree(tmp_path, "the")
    assert some
    assert [match["id"] for match in some] == sorted(match["id"] for match in some)
    assert len(_assert_agree(tmp_path, "gradient")) >= 1


def test_randomized_corpus_and_queries_agree(tmp_path: Path):
    rng = random.Random(20260920)
    words = ["alpha", "beta", "gamma", "gradient", "descent", "x", "ab", "A",
             "MiXeD", "Größe", "日本", "a+b", "(x)", "[01]", "c.d", "e*f",
             "UPPER", "with-dash", "under_score", "dot.t", "123", ""]
    title_words = ["alpha", "beta", "gamma", "gradient", "descent", "UPPER",
                   "plain", "note", "with-dash", "under_score", "dot.t", "123", "A"]
    notes = []
    for index in range(24):
        body = " ".join(rng.choice(words) for _ in range(rng.randint(0, 40)))
        title = " ".join(rng.choice(title_words) for _ in range(rng.randint(0, 3))) or None
        notes.append((f"r{index}.md", f"r{index}", title, body, ()))
    _write_corpus(tmp_path, notes)
    _stage_producers(tmp_path)
    for _ in range(40):
        terms = []
        for _ in range(rng.randint(1, 3)):
            word = rng.choice(words)
            if word and rng.random() < 0.4:
                start = rng.randint(0, len(word) - 1)
                word = word[start : rng.randint(start + 1, len(word))]
            if word and rng.random() < 0.3:
                word = "".join(c.upper() if rng.random() < 0.5 else c.lower() for c in word)
            terms.append(word or "zz-missing")
        _assert_agree(tmp_path, " ".join(terms))


# ---------------------------------------------------------------------------
# Mutations: equality plus the expected rebuild closure.
# ---------------------------------------------------------------------------

def _warm_corpus(tmp_path: Path, monkeypatch):
    _write_corpus(tmp_path)
    _stage_producers(tmp_path)
    counts = _counting_builds(monkeypatch)
    _assert_agree(tmp_path, "gradient")
    counts.update(segments=0, postings=0)
    return counts


def test_body_edit_rebuilds_one_segment(tmp_path: Path, monkeypatch):
    counts = _warm_corpus(tmp_path, monkeypatch)
    notes_dir = tmp_path / "knowledge" / "notes"
    _write_note(notes_dir, "n1.md", "n1", "Gradient Methods", "rewritten body text")
    _assert_agree(tmp_path, "rewritten")
    _assert_agree(tmp_path, "gradient")
    assert counts == {"segments": 1, "postings": 1}


def test_title_change_rebuilds_one_segment(tmp_path: Path, monkeypatch):
    counts = _warm_corpus(tmp_path, monkeypatch)
    notes_dir = tmp_path / "knowledge" / "notes"
    _write_note(notes_dir, "n1.md", "n1", "Renamed Title",
                "Gradient descent converges under mild conditions.\n")
    assert _assert_agree(tmp_path, "Renamed")[0]["title"] == "Renamed Title"
    assert counts == {"segments": 1, "postings": 1}


def test_added_note_builds_one_segment(tmp_path: Path, monkeypatch):
    counts = _warm_corpus(tmp_path, monkeypatch)
    _write_note(tmp_path / "knowledge" / "notes", "new.md", "new", "New",
                "brand new content")
    assert _assert_agree(tmp_path, "brand")[0]["id"] == "new"
    assert counts == {"segments": 1, "postings": 1}


def test_deleted_note_rebuilds_postings_only(tmp_path: Path, monkeypatch):
    counts = _warm_corpus(tmp_path, monkeypatch)
    (tmp_path / "knowledge" / "notes" / "n1.md").unlink()
    assert _assert_agree(tmp_path, "gradient") == []
    assert counts == {"segments": 0, "postings": 1}


def test_renamed_note_rebuilds_one_segment(tmp_path: Path, monkeypatch):
    counts = _warm_corpus(tmp_path, monkeypatch)
    notes_dir = tmp_path / "knowledge" / "notes"
    (notes_dir / "n2.md").rename(notes_dir / "subdir-n2.md")
    found = _assert_agree(tmp_path, "Short")
    assert [match["id"] for match in found] == ["n2"]
    assert found[0]["path"] == "knowledge/notes/subdir-n2.md"
    assert counts == {"segments": 1, "postings": 1}


def test_changed_note_id_rebuilds_one_segment(tmp_path: Path, monkeypatch):
    counts = _warm_corpus(tmp_path, monkeypatch)
    notes_dir = tmp_path / "knowledge" / "notes"
    (notes_dir / "n2.md").unlink()
    _write_note(notes_dir, "n2.md", "n2-renamed", "Short", "ab")
    assert [match["id"] for match in _assert_agree(tmp_path, "Short")] == ["n2-renamed"]
    assert counts == {"segments": 1, "postings": 1}


def test_indexer_version_bump_rebuilds_everything(tmp_path: Path, monkeypatch):
    import learning_os.search.model as search_model

    counts = _warm_corpus(tmp_path, monkeypatch)
    # A coherent bump moves builders and validators together.
    monkeypatch.setattr(search_model, "INDEX_FORMAT_VERSION", 999)
    monkeypatch.setattr(search_index_module, "INDEX_FORMAT_VERSION", 999)
    for query in QUERIES:
        _assert_agree(tmp_path, query)
    assert counts == {"segments": len(FIXED_NOTES), "postings": 1}


def test_verification_reads_no_note_bytes(tmp_path: Path, monkeypatch):
    _write_corpus(tmp_path)
    _stage_producers(tmp_path)
    ordered = _ordered_notes(tmp_path)
    verifying = {"active": False}
    reads = []
    original_bytes = reads_module._note_bytes
    original_query = reads_module.candidates

    def counting_bytes(root, note):
        if verifying["active"]:
            reads.append(note.id)
        return original_bytes(root, note)

    def gated(root, postings, terms):
        try:
            return original_query(root, postings, terms)
        finally:
            verifying["active"] = True

    monkeypatch.setattr(reads_module, "_note_bytes", counting_bytes)
    monkeypatch.setattr(reads_module, "candidates", gated)
    terms = _compiled("gradient")
    got = _indexed_content_search(tmp_path, ordered, terms, ["gradient"])
    assert [match["id"] for match in got] == ["n1"]
    assert reads == []
    assert got == _exhaustive_content_search(tmp_path, ordered, terms)


# ---------------------------------------------------------------------------
# Cache states: every corruption class still agrees (and heals).
# ---------------------------------------------------------------------------

def _derived_state_dir(root: Path) -> Path:
    return root / "generated" / "derived-state"


def test_deleted_cache_rebuilds(tmp_path: Path, monkeypatch):
    counts = _warm_corpus(tmp_path, monkeypatch)
    import shutil

    shutil.rmtree(_derived_state_dir(tmp_path))
    for query in QUERIES:
        _assert_agree(tmp_path, query)
    assert counts == {"segments": len(FIXED_NOTES), "postings": 1}


def test_corrupt_state_rebuilds(tmp_path: Path):
    _write_corpus(tmp_path)
    _stage_producers(tmp_path)
    _assert_agree(tmp_path, "gradient")
    (_derived_state_dir(tmp_path) / "state-v1.json").write_text("{corrupt", encoding="utf-8")
    for query in QUERIES:
        _assert_agree(tmp_path, query)


def test_tampered_blob_rebuilds_and_heals(tmp_path: Path, monkeypatch):
    counts = _warm_corpus(tmp_path, monkeypatch)
    blobs = list((_derived_state_dir(tmp_path) / "blobs").iterdir())
    assert blobs
    blobs[0].write_bytes(b"tampered")
    for query in QUERIES:
        _assert_agree(tmp_path, query)
    counts.update(segments=0, postings=0)
    for query in QUERIES:
        _assert_agree(tmp_path, query)
    assert counts == {"segments": 0, "postings": 0}


def test_missing_blob_rebuilds_and_heals(tmp_path: Path, monkeypatch):
    counts = _warm_corpus(tmp_path, monkeypatch)
    blobs = list((_derived_state_dir(tmp_path) / "blobs").iterdir())
    blobs[0].unlink()
    for query in QUERIES:
        _assert_agree(tmp_path, query)
    counts.update(segments=0, postings=0)
    for query in QUERIES:
        _assert_agree(tmp_path, query)
    assert counts == {"segments": 0, "postings": 0}


def test_wrongly_shaped_postings_self_heals(tmp_path: Path):
    import hashlib
    import json

    from learning_os.derived import canonical_bytes, read_state

    _write_corpus(tmp_path)
    _stage_producers(tmp_path)
    _assert_agree(tmp_path, "gradient")
    state_dir = _derived_state_dir(tmp_path)
    forged = canonical_bytes({"format": 999, "notes": {}})
    digest = hashlib.sha256(forged).hexdigest()
    (state_dir / "blobs" / digest).write_bytes(forged)
    payload = json.loads((state_dir / "state-v1.json").read_text(encoding="utf-8"))
    # Keep the true node key so the engine hits the forged blob.
    payload["nodes"][POSTINGS_NODE_ID]["output_sha256"] = digest
    payload["nodes"][POSTINGS_NODE_ID]["blob"] = f"blobs/{digest}"
    (state_dir / "state-v1.json").write_text(json.dumps(payload), encoding="utf-8")
    ordered = _ordered_notes(tmp_path)
    terms = _compiled("gradient")
    with pytest.raises(DerivedError, match="invalid shape"):
        _indexed_content_search(tmp_path, ordered, terms, ["gradient"])
    assert POSTINGS_NODE_ID not in read_state(tmp_path)
    for query in QUERIES:
        _assert_agree(tmp_path, query)


def test_wrongly_shaped_segment_self_heals(tmp_path: Path):
    import hashlib
    import json

    from learning_os.derived import canonical_bytes, read_state

    _write_corpus(tmp_path)
    _stage_producers(tmp_path)
    _assert_agree(tmp_path, "gradient")
    state_dir = _derived_state_dir(tmp_path)
    forged = canonical_bytes({"format": 999})
    digest = hashlib.sha256(forged).hexdigest()
    (state_dir / "blobs" / digest).write_bytes(forged)
    payload = json.loads((state_dir / "state-v1.json").read_text(encoding="utf-8"))
    victim = segment_node_id("n1")
    # Keep the true node key so the engine hits the forged blob.
    payload["nodes"][victim]["output_sha256"] = digest
    payload["nodes"][victim]["blob"] = f"blobs/{digest}"
    (state_dir / "state-v1.json").write_text(json.dumps(payload), encoding="utf-8")
    ordered = _ordered_notes(tmp_path)
    terms = _compiled("gradient")
    with pytest.raises(DerivedError, match="invalid shape"):
        _indexed_content_search(tmp_path, ordered, terms, ["gradient"])
    assert victim not in read_state(tmp_path)
    for query in QUERIES:
        _assert_agree(tmp_path, query)


# ---------------------------------------------------------------------------
# CLI envelope: production must equal the oracle end to end.
# ---------------------------------------------------------------------------

def _run_search(root: Path, query: str, *, capsys,
                offset=0, limit=100, expected_snapshot=None, type_="note"):
    args = SimpleNamespace(
        query=query, type=type_, offset=offset, limit=limit,
        expected_snapshot=expected_snapshot, root=str(root))
    code = content_search(args)
    out, err = capsys.readouterr()
    return code, out, err


def test_cli_matches_exhaustive_oracle(tmp_path: Path, capsys):
    import json

    _write_corpus(tmp_path)
    _stage_producers(tmp_path)
    for query in QUERIES:
        code, out, err = _run_search(tmp_path, query, capsys=capsys)
        assert code == 0, err
        payload = json.loads(out)
        ordered = _ordered_notes(tmp_path)
        expected = _exhaustive_content_search(tmp_path, ordered, _compiled(query))
        assert payload["contract"] == "note-content-search"
        assert payload["items"] == expected[:100]
        assert payload["total"] == len(expected)
        assert payload["next_offset"] == (100 if 100 < len(expected) else None)


def test_cli_uses_index_not_fallback(tmp_path: Path, monkeypatch, capsys):
    _write_corpus(tmp_path)
    _stage_producers(tmp_path)

    def boom(*args, **kwargs):
        raise AssertionError("exhaustive fallback taken")

    monkeypatch.setattr(reads_module, "_exhaustive_content_search", boom)
    for query in QUERIES:
        code, _out, err = _run_search(tmp_path, query, capsys=capsys)
        assert code == 0, err


def test_cli_falls_back_on_derived_error(tmp_path: Path, monkeypatch, capsys):
    import json

    _write_corpus(tmp_path)
    _stage_producers(tmp_path)

    def broken(*args, **kwargs):
        raise DerivedError("injected")

    monkeypatch.setattr(reads_module, "candidates", broken)
    code, out, err = _run_search(tmp_path, "gradient", capsys=capsys)
    assert code == 0, err
    ordered = _ordered_notes(tmp_path)
    expected = _exhaustive_content_search(tmp_path, ordered, _compiled("gradient"))
    assert json.loads(out)["items"] == expected


def test_cli_pagination_pages_the_oracle(tmp_path: Path, capsys):
    import json

    _write_corpus(tmp_path)
    _stage_producers(tmp_path)
    ordered = _ordered_notes(tmp_path)
    expected = _exhaustive_content_search(tmp_path, ordered, _compiled("the"))
    assert len(expected) >= 2
    seen = []
    snapshot = None
    for offset in range(len(expected)):
        code, out, err = _run_search(
            tmp_path, "the", capsys=capsys, offset=offset, limit=1,
            expected_snapshot=snapshot)
        assert code == 0, err
        payload = json.loads(out)
        assert payload["total"] == len(expected)
        seen.extend(payload["items"])
        snapshot = payload["snapshot_id"]
    assert seen == expected


def test_cli_malformed_note_still_refuses(tmp_path: Path, capsys):
    notes_dir = _write_corpus(tmp_path)
    _stage_producers(tmp_path)
    (notes_dir / "broken.md").write_text("---\nid: [unclosed\n---\nbody\n", encoding="utf-8")
    code, out, err = _run_search(tmp_path, "gradient", capsys=capsys)
    assert code == 2
    assert out == "" and "search" in err
    # Repair: production answers again.
    (notes_dir / "broken.md").write_text(
        "---\nid: repaired\ntitle: Repaired\n---\nrepaired body\n", encoding="utf-8")
    code, out, err = _run_search(tmp_path, "repaired", capsys=capsys)
    assert code == 0, err


def test_cli_snapshot_mismatch_still_refuses(tmp_path: Path, capsys):
    _write_corpus(tmp_path)
    _stage_producers(tmp_path)
    code, _out, err = _run_search(
        tmp_path, "gradient", capsys=capsys, expected_snapshot="sha256:" + "0" * 64)
    assert code == 3
    assert "snapshot" in err
