"""Tests for material.search capability and FTS5 index generation lifecycle."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

import learning_os.app.handlers  # noqa: F401
from learning_os.app.context import OpContext
from learning_os.app.registry import REGISTRY
from learning_os.domain.failures import WriteRefused
from learning_os.store.loading import load_repo
from learning_os.store.materials.search_index import (
    build_tiered_queries,
    execute_search,
    open_pinned_generation,
)


@pytest.fixture
def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


@pytest.fixture
def repo(repo_root: Path):
    return load_repo(repo_root)


def test_query_sanitization_and_tiering():
    """Verify tiered query formulation and safe term escaping."""
    # Test 1: Simple multi-word query with German stopwords
    q = "der Beweis für die vollständige Induktion"
    tiers = build_tiered_queries(q)
    assert len(tiers) == 3
    tier_names = [t[0] for t in tiers]
    assert tier_names == ["exact_phrase", "conjunction", "disjunction"]

    # Stopwords ('der', 'für', 'die') should be stripped in conjunction tier
    conj_expr = tiers[1][1]
    assert '"Beweis"' in conj_expr
    assert '"vollständige"' in conj_expr
    assert '"Induktion"' in conj_expr
    assert '"der"' not in conj_expr
    assert '"die"' not in conj_expr

    # Test 2: Special characters and mathematical notation
    math_q = 'lim sup_{n -> \\infty} a_n <= "M"'
    math_tiers = build_tiered_queries(math_q)
    assert len(math_tiers) >= 2
    # Ensure no unescaped quotes break FTS5
    for _, expr in math_tiers:
        assert '"""' not in expr

    # Test 3: Single word query
    single_tiers = build_tiered_queries("Determinante")
    assert len(single_tiers) == 1
    assert single_tiers[0][0] == "conjunction"
    assert single_tiers[0][1] == '"Determinante"'


def test_index_generation_reader_and_pinning(repo_root: Path):
    """Verify pinned read-only index access."""
    reader = open_pinned_generation(repo_root)
    assert reader.generation_id.startswith("gen_")
    assert reader.db_path.exists()

    con = reader.connect()
    # Test that connection is read-only
    with pytest.raises(sqlite3.OperationalError):
        con.execute("CREATE TABLE test_mutation(id INT);")

    cur = con.cursor()
    cur.execute("SELECT count(*) FROM material_fts;")
    row_count = cur.fetchone()[0]
    assert row_count > 0

    reader.close()


def test_search_execution_and_route_resolution(repo_root: Path, repo):
    """Verify execute_search returns valid hits with route bindings."""
    res = execute_search(repo_root, "topologische Sortierung", limit=5)
    assert res.status == "ok"
    assert res.generation_id is not None
    assert len(res.hits) > 0

    hit1 = res.hits[0]
    assert hit1["rank"] == 1
    assert "source_sha256" in hit1
    assert "physical_page" in hit1
    assert "snippet" in hit1
    assert (
        "[Topologische Sortierung]" in hit1["snippet"]
        or "[topologische]" in hit1["snippet"].lower()
    )


def test_unavailable_index_handling(tmp_path: Path):
    """Verify explicit unavailable status when index is missing or corrupt."""
    # 1. Missing index
    res_missing = execute_search(tmp_path, "test query")
    assert res_missing.status == "unavailable"
    assert res_missing.reason == "index_missing"
    assert res_missing.hits == []

    # 2. Corrupt pointer
    search_dir = tmp_path / "generated" / "material-search"
    search_dir.mkdir(parents=True)
    (search_dir / "current.json").write_text("invalid json", encoding="utf-8")

    res_corrupt = execute_search(tmp_path, "test query")
    assert res_corrupt.status == "unavailable"
    assert res_corrupt.reason == "index_corrupt"


def test_material_search_handler(repo_root: Path):
    """Verify material.search handler registered in LearningOS pipeline."""
    handler = REGISTRY.get("material.search")
    assert handler is not None
    assert handler.kind == "query"

    ctx = OpContext(
        root=repo_root, operation="material.search", channel="cli", invocation="query", gateway=None
    )

    # Test empty query refusal
    with pytest.raises(WriteRefused) as exc:
        handler.handler(ctx, {"query": ""})
    assert exc.value.site == "material.search.empty-query"

    # Test valid query
    outcome = handler.handler(ctx, {"query": "Dijkstra Algorithmus", "limit": 3})
    assert outcome is not None
    payload = outcome.payload
    assert payload["status"] == "ok"
    assert len(payload["hits"]) <= 3
    assert "snapshot_id" in payload

    # Test span reference format
    mapped_hits = [h for h in payload["hits"] if h.get("is_mapped")]
    if mapped_hits:
        h = mapped_hits[0]
        span_ref = h["span_reference"]
        assert "unit_id" in span_ref
        assert "route_id" in span_ref
        assert span_ref["pages"].startswith("pdf p. ")


def test_span_retrieval_integration(repo_root: Path):
    """Verify that span_reference from material.search cleanly feeds into material.span."""
    ctx_search = OpContext(
        root=repo_root, operation="material.search", channel="cli", invocation="query", gateway=None
    )
    search_res = REGISTRY["material.search"].handler(
        ctx_search, {"query": "Topologische Sortierung", "limit": 5}
    )

    mapped_hits = [
        h for h in search_res.payload["hits"] if h.get("is_mapped") and h.get("span_reference")
    ]
    assert len(mapped_hits) > 0, "Expected at least one mapped hit for topologische Sortierung"

    target_hit = mapped_hits[0]
    span_ref = target_hit["span_reference"]

    ctx_span = OpContext(
        root=repo_root, operation="material.span", channel="cli", invocation="query", gateway=None
    )
    span_req = {
        "unit_id": span_ref["unit_id"],
        "route_id": span_ref["route_id"],
        "pages": span_ref["pages"],
        "extract": True,
    }
    span_res = REGISTRY["material.span"].handler(ctx_span, span_req)
    assert span_res is not None
    span_payload = span_res.payload
    assert len(span_payload["spans"]) > 0
    assert "excerpt" in span_payload["spans"][0]
    assert len(span_payload["spans"][0]["excerpt"]) > 0


def test_page_accounting_and_blank_page_manifest(repo_root: Path):
    """Verify that the 1,079 blank pages are completely and deterministically accounted for."""
    search_dir = repo_root / "generated" / "material-search"
    current_json = search_dir / "current.json"
    assert current_json.exists()
    cur_data = json.loads(current_json.read_text(encoding="utf-8"))
    gen_id = cur_data["generation_id"]

    gen_dir = search_dir / "generations" / gen_id
    gen_json = gen_dir / "generation.json"
    blank_json = gen_dir / "blank_pages.json"

    assert gen_json.exists()
    assert blank_json.exists()

    gen_meta = json.loads(gen_json.read_text(encoding="utf-8"))
    assert gen_meta["total_pages_scanned"] == 72199
    assert gen_meta["blank_pages_skipped"] == 1079
    assert gen_meta["indexed_pages"] == 71120
    assert (
        gen_meta["total_pages_scanned"]
        == gen_meta["indexed_pages"] + gen_meta["blank_pages_skipped"]
    )
    assert gen_meta["materials_digest"]
    assert gen_meta["manifest_sha256"]
    assert gen_meta["extractor"] == "pdftotext+pypdf"

    blank_data = json.loads(blank_json.read_text(encoding="utf-8"))
    assert blank_data["total_pages_scanned"] == 72199
    assert blank_data["blank_pages_skipped"] == 1079
    assert blank_data["indexed_pages"] == 71120
    assert len(blank_data["blank_pages"]) == 1079

    # Spot check that entries in blank_pages actually have empty text in text-cache
    text_cache = repo_root / "generated" / "text-cache"
    for entry in blank_data["blank_pages"][:10]:
        sha = entry["source_sha256"]
        page = entry["page_no"]
        page_file = text_cache / sha / f"pp-{page:04d}.txt"
        assert page_file.exists()
        assert page_file.read_text(encoding="utf-8", errors="ignore").strip() == ""


def test_freshness_and_staleness_detection(tmp_path: Path):
    """Verify that modified PDFs, manifests, or extractor versions trigger index_stale."""
    base_dir = tmp_path / "generated" / "material-search"
    gen_dir = base_dir / "generations" / "gen_test1"
    gen_dir.mkdir(parents=True)

    # Create dummy SQLite FTS5 database
    db_path = gen_dir / "search.sqlite3"
    con = sqlite3.connect(str(db_path))
    con.execute(
        "CREATE VIRTUAL TABLE material_fts USING fts5("
        "source_sha256 UNINDEXED, page_no UNINDEXED, source_id UNINDEXED, title, body);"
    )
    con.execute("INSERT INTO material_fts VALUES ('sha1', 1, 'u1:r1', 'Doc1', 'test content');")
    con.commit()
    con.close()

    # Create generation.json with pinned digests
    gen_meta = {
        "generation_id": "gen_test1",
        "schema_version": 1,
        "extractor": "pdftotext+pypdf",
        "materials_digest": "digest_A_initial",
        "manifest_sha256": "sha256:manifest_A_initial",
    }
    (gen_dir / "generation.json").write_text(json.dumps(gen_meta), encoding="utf-8")

    # Create current.json pointer
    current_data = {"generation_id": "gen_test1", "db_file": "generations/gen_test1/search.sqlite3"}
    (base_dir / "current.json").write_text(json.dumps(current_data), encoding="utf-8")

    # Create matching manifest.identity.json
    gen_root = tmp_path / "generated"
    identity_file = gen_root / "manifest.identity.json"
    identity_file.write_text(
        json.dumps(
            {
                "materials_digest": "digest_A_initial",
                "manifest_sha256": "sha256:manifest_A_initial",
            }
        ),
        encoding="utf-8",
    )

    # 1. Matching state: search succeeds
    res_ok = execute_search(tmp_path, "content")
    assert res_ok.status == "ok"
    assert len(res_ok.hits) == 1

    # 2. Materials corpus modified (materials_digest mismatch): refuses stale search
    identity_file.write_text(
        json.dumps(
            {
                "materials_digest": "digest_B_MODIFIED",
                "manifest_sha256": "sha256:manifest_A_initial",
            }
        ),
        encoding="utf-8",
    )
    res_stale_mat = execute_search(tmp_path, "content")
    assert res_stale_mat.status == "unavailable"
    assert res_stale_mat.reason == "index_stale"
    assert "materials corpus changed" in res_stale_mat.message

    # 3. Explicit allow_stale=True bypasses staleness check
    res_allow_stale = execute_search(tmp_path, "content", allow_stale=True)
    assert res_allow_stale.status == "ok"
    assert len(res_allow_stale.hits) == 1

    # 4. Manifest modified (manifest_sha256 mismatch): refuses stale search
    identity_file.write_text(
        json.dumps(
            {
                "materials_digest": "digest_A_initial",
                "manifest_sha256": "sha256:manifest_B_MODIFIED",
            }
        ),
        encoding="utf-8",
    )
    res_stale_man = execute_search(tmp_path, "content")
    assert res_stale_man.status == "unavailable"
    assert res_stale_man.reason == "index_stale"
    assert "manifest changed" in res_stale_man.message

    # 5. Extractor mismatch in generation.json
    identity_file.write_text(
        json.dumps(
            {
                "materials_digest": "digest_A_initial",
                "manifest_sha256": "sha256:manifest_A_initial",
            }
        ),
        encoding="utf-8",
    )
    gen_meta["extractor"] = "legacy_extractor_v0"
    (gen_dir / "generation.json").write_text(json.dumps(gen_meta), encoding="utf-8")
    res_stale_ext = execute_search(tmp_path, "content")
    assert res_stale_ext.status == "unavailable"
    assert res_stale_ext.reason == "index_stale"
    assert "extractor mismatch" in res_stale_ext.message.lower()

    # 6. Schema mismatch in generation.json
    gen_meta["extractor"] = "pdftotext+pypdf"
    gen_meta["schema_version"] = 99
    (gen_dir / "generation.json").write_text(json.dumps(gen_meta), encoding="utf-8")
    res_stale_schema = execute_search(tmp_path, "content")
    assert res_stale_schema.status == "unavailable"
    assert res_stale_schema.reason == "index_stale"
    assert "schema version mismatch" in res_stale_schema.message.lower()


def test_concurrent_generation_replacement_and_pinning(tmp_path: Path):
    """Verify active readers pinned to Gen A continue querying when Gen B is published."""
    base_dir = tmp_path / "generated" / "material-search"
    gen_a_dir = base_dir / "generations" / "gen_A"
    gen_b_dir = base_dir / "generations" / "gen_B"
    gen_a_dir.mkdir(parents=True)
    gen_b_dir.mkdir(parents=True)

    # Build DB A
    con_a = sqlite3.connect(str(gen_a_dir / "search.sqlite3"))
    con_a.execute(
        "CREATE VIRTUAL TABLE material_fts USING fts5("
        "source_sha256 UNINDEXED, page_no UNINDEXED, source_id UNINDEXED, title, body);"
    )
    con_a.execute(
        "INSERT INTO material_fts VALUES ('shaA', 1, 'u1:r1', 'DocA', 'Alpha generation content');"
    )
    con_a.commit()
    con_a.close()

    # Build DB B
    con_b = sqlite3.connect(str(gen_b_dir / "search.sqlite3"))
    con_b.execute(
        "CREATE VIRTUAL TABLE material_fts USING fts5("
        "source_sha256 UNINDEXED, page_no UNINDEXED, source_id UNINDEXED, title, body);"
    )
    con_b.execute(
        "INSERT INTO material_fts VALUES ('shaB', 1, 'u1:r1', 'DocB', 'Beta generation content');"
    )
    con_b.commit()
    con_b.close()

    meta = {"schema_version": 1, "extractor": "pdftotext+pypdf"}
    (gen_a_dir / "generation.json").write_text(
        json.dumps({**meta, "generation_id": "gen_A"}), encoding="utf-8"
    )
    (gen_b_dir / "generation.json").write_text(
        json.dumps({**meta, "generation_id": "gen_B"}), encoding="utf-8"
    )

    current_pointer = base_dir / "current.json"
    current_pointer.write_text(
        json.dumps({"generation_id": "gen_A", "db_file": "generations/gen_A/search.sqlite3"}),
        encoding="utf-8",
    )

    # Reader 1 opens and pins Gen A
    reader_1 = open_pinned_generation(tmp_path, allow_stale=True)
    assert reader_1.generation_id == "gen_A"
    cur1 = reader_1.connect().cursor()
    cur1.execute("SELECT body FROM material_fts WHERE material_fts MATCH 'Alpha';")
    assert cur1.fetchone()[0] == "Alpha generation content"

    # Now simulate atomic publication of Gen B
    tmp_pointer = base_dir / "current.json.tmp"
    tmp_pointer.write_text(
        json.dumps({"generation_id": "gen_B", "db_file": "generations/gen_B/search.sqlite3"}),
        encoding="utf-8",
    )
    tmp_pointer.replace(current_pointer)

    # Reader 1 must continue querying Gen A uninterrupted
    cur1.execute("SELECT body FROM material_fts WHERE material_fts MATCH 'Alpha';")
    assert cur1.fetchone()[0] == "Alpha generation content"
    cur1.execute("SELECT count(*) FROM material_fts WHERE material_fts MATCH 'Beta';")
    assert cur1.fetchone()[0] == 0

    # New reader 2 pins Gen B
    reader_2 = open_pinned_generation(tmp_path, allow_stale=True)
    assert reader_2.generation_id == "gen_B"
    cur2 = reader_2.connect().cursor()
    cur2.execute("SELECT body FROM material_fts WHERE material_fts MATCH 'Beta';")
    assert cur2.fetchone()[0] == "Beta generation content"
    cur2.execute("SELECT count(*) FROM material_fts WHERE material_fts MATCH 'Alpha';")
    assert cur2.fetchone()[0] == 0

    reader_1.close()
    reader_2.close()


def test_interrupted_build_safety(tmp_path: Path):
    """Verify that interrupted builds in .tmp leave current pointer and index untouched."""
    base_dir = tmp_path / "generated" / "material-search"
    gen_a_dir = base_dir / "generations" / "gen_A"
    gen_a_dir.mkdir(parents=True)

    con_a = sqlite3.connect(str(gen_a_dir / "search.sqlite3"))
    con_a.execute(
        "CREATE VIRTUAL TABLE material_fts USING fts5("
        "source_sha256 UNINDEXED, page_no UNINDEXED, source_id UNINDEXED, title, body);"
    )
    con_a.execute(
        "INSERT INTO material_fts VALUES ('shaA', 1, 'u1:r1', 'DocA', 'Stable active content');"
    )
    con_a.commit()
    con_a.close()

    (gen_a_dir / "generation.json").write_text(
        json.dumps({"generation_id": "gen_A", "schema_version": 1, "extractor": "pdftotext+pypdf"}),
        encoding="utf-8",
    )
    (base_dir / "current.json").write_text(
        json.dumps({"generation_id": "gen_A", "db_file": "generations/gen_A/search.sqlite3"}),
        encoding="utf-8",
    )

    # Simulate an interrupted build leaving a partial .tmp directory
    tmp_build_dir = base_dir / "generations" / "gen_B.tmp"
    tmp_build_dir.mkdir(parents=True)
    (tmp_build_dir / "search.sqlite3").write_bytes(b"partial incomplete bytes")

    # Active searches must remain 100% operational against Gen A
    res = execute_search(tmp_path, "Stable", allow_stale=True)
    assert res.status == "ok"
    assert res.generation_id == "gen_A"
    assert len(res.hits) == 1

    # Pointer was never touched
    cur_data = json.loads((base_dir / "current.json").read_text(encoding="utf-8"))
    assert cur_data["generation_id"] == "gen_A"
