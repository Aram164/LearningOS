"""Search index builders: grams, segments, postings, registry.

Commit 3 of the incremental-computation plan (unit scope): the pure
builder layer with no CLI wiring. The differential suite comparing
indexed vs exhaustive search lands in commit 4.
"""

from __future__ import annotations

from pathlib import Path

import pytest

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
