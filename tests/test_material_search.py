"""Fixture-world tests for material.search and the self-describing FTS5 index (ADR-020)."""

from __future__ import annotations

import fcntl
import json
import os
import shutil
import sqlite3
import sys
import tempfile
import unicodedata
from pathlib import Path
from unittest.mock import patch

import jsonschema
import pytest
import yaml

TESTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TESTS_DIR.parent
TOOLS_DIR = REPO_ROOT / "tools"
for _p in (str(TESTS_DIR), str(TOOLS_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import build_material_search_index as builder  # noqa: E402
import material_outline  # noqa: E402
import material_text  # noqa: E402
import materials_manifest  # noqa: E402
from conftest import build_mini_repo  # noqa: E402
from repo_builders import run_los, write_minimal_pdf, write_yaml  # noqa: E402
from scenario_fixtures import FIXED_DAY, rich_world  # noqa: E402

import learning_os.app.handlers  # noqa: F401, E402
from learning_os.app.context import OpContext  # noqa: E402
from learning_os.app.registry import REGISTRY  # noqa: E402
from learning_os.derive.projection.outputs import generate_all, write_outputs  # noqa: E402
from learning_os.domain.failures import NotFound, WriteRefused  # noqa: E402
from learning_os.domain.material_inventory import render_manifest  # noqa: E402
from learning_os.store.loading import load_repo  # noqa: E402
from learning_os.store.materials import search_index  # noqa: E402
from learning_os.store.materials.search_index import (  # noqa: E402
    OutlineSection,
    build_tiered_queries,
    check_index_integrity,
    execute_search,
    expand_query_names,
    get_outline_base_dir,
    get_search_base_dir,
    load_outline,
    normalize_outline,
    open_index,
    outline_payload,
    parse_outline_payload,
    span_pages_for,
)

needs_pdftotext = pytest.mark.skipif(shutil.which("pdftotext") is None, reason="pdftotext missing")

RESPONSE_SCHEMA = json.loads(
    (REPO_ROOT / "system" / "schema" / "material-search.schema.json").read_text(encoding="utf-8")
)
DUMMY_SNAPSHOT = "sha256:" + "0" * 64


def _validate_response(payload: dict[str, object]) -> None:
    doc = dict(payload)
    doc.setdefault("snapshot_id", DUMMY_SNAPSHOT)
    jsonschema.validate(doc, RESPONSE_SCHEMA)


def _cached_pdf(world: Path, pdf: Path) -> tuple[str, int]:
    """(digest, page count) of a materials PDF, from its text-cache record."""
    import hashlib

    sha = hashlib.sha256(pdf.read_bytes()).hexdigest()
    record = json.loads(
        (world / "generated" / "text-cache" / sha / "index.json").read_text(encoding="utf-8"))
    return sha, int(record["pages"])


def _write_outline(world: Path, sha: str, page_total: int,
                   sections: list[OutlineSection], status: str = "present") -> Path:
    base = get_outline_base_dir(world)
    base.mkdir(parents=True, exist_ok=True)
    target = base / f"{sha}.json"
    target.write_text(json.dumps(outline_payload(
        sha, "fixture.pdf", page_total, status, sections, "tests"), indent=1), encoding="utf-8")
    return target


def _write_page_outline(world: Path, pdf: Path) -> str:
    """One section per page, as a slide deck with per-slide bookmarks has."""
    sha, pages = _cached_pdf(world, pdf)
    _write_outline(world, sha, pages, [
        OutlineSection(f"Slide {page}", 0, (), page, page) for page in range(1, pages + 1)])
    return sha


def _refresh_manifest_and_text_cache(root: Path) -> None:
    materials_dir = root.parent / "materials"
    manifest = materials_manifest.build(materials_dir)
    manifest["captured"] = FIXED_DAY
    manifest_path = root / "records" / "materials-manifest.yaml"
    manifest_path.write_text(render_manifest(manifest), encoding="utf-8")

    cache_dir = root / "generated" / "text-cache"
    rc = material_text.main(
        [
            "--cache-dir",
            str(cache_dir),
            "--manifest",
            str(manifest_path),
            "--materials-root",
            str(materials_dir),
        ]
    )
    assert rc == 0


@pytest.fixture(scope="module")
def _template_world() -> Path:
    """Build the rich_world + text-cache + FTS5 index once per module."""
    container = Path(tempfile.mkdtemp(prefix="los-mat-search-tpl-"))
    root = build_mini_repo(container)
    rich_world(root)
    if shutil.which("pdftotext") is not None:
        _refresh_manifest_and_text_cache(root)
        builder.build_index_generation(root)
    yield root
    shutil.rmtree(container, ignore_errors=True)


@pytest.fixture
def world(tmp_path: Path, _template_world: Path) -> Path:
    """Copy the pre-built fixture world into a fresh per-test directory."""
    dest = tmp_path / "LearningOS"
    shutil.copytree(_template_world.parent, dest)
    return dest / "repository"


def test_query_sanitization_and_tiering() -> None:
    """Verify tiered query formulation and safe term escaping."""
    q = "der Beweis für die vollständige Induktion"
    tiers = build_tiered_queries(q)
    assert [t[0] for t in tiers] == ["exact_phrase", "conjunction", "disjunction"]
    conj_expr = tiers[1][1]
    assert '"beweis"' in conj_expr
    assert '"vollständige"' in conj_expr
    assert '"induktion"' in conj_expr
    assert '"der"' not in conj_expr
    assert '"für"' not in conj_expr

    math_q = 'lim sup_{n -> \\infty} a_n <= "M"'
    math_tiers = build_tiered_queries(math_q)
    assert len(math_tiers) >= 2
    for _, expr in math_tiers:
        assert '"""' not in expr


@needs_pdftotext
def test_build_search_and_span_reference_integration(world: Path) -> None:
    """Row 1 (L5, D17, N1): build -> search ok; span_reference resolves through material.span --extract."""
    ctx_search = OpContext(
        root=world,
        operation="material.search",
        channel="cli",
        invocation="query",
        gateway=None,
    )
    outcome = REGISTRY["material.search"].handler(ctx_search, {"query": "Chebyshev", "limit": 5})
    assert outcome is not None
    payload = outcome.payload
    _validate_response(payload)

    assert payload["status"] == "ok"
    assert payload["contract"] == "material-search-v1"
    assert payload["schema_version"] == 1
    assert len(payload["hits"]) >= 1

    hit = payload["hits"][0]
    assert hit["rank"] == 1
    assert hit["page"] == 19
    assert hit["material"] == "source-demo-book/lecture-01.pdf"
    assert hit["is_mapped"] is True
    assert hit["bindings_total"] >= 1
    assert "source_id" not in hit

    span_ref = hit["span_reference"]
    assert span_ref is not None
    assert span_ref["pages"] == "pdf p. 19"
    assert span_ref["extract"] is True
    assert span_ref["file_sha256"] == f"sha256:{hit['sha256']}"

    ctx_span = OpContext(
        root=world,
        operation="material.span",
        channel="cli",
        invocation="query",
        gateway=None,
    )
    span_res = REGISTRY["material.span"].handler(
        ctx_span,
        {
            "unit_id": span_ref["unit"],
            "route_id": span_ref["route"],
            "pages": span_ref["pages"],
            "extract": span_ref["extract"],
        },
    )
    assert span_res is not None
    spans = span_res.payload["spans"]
    assert len(spans) == 1
    assert "Chebyshev squares the deviation bound" in spans[0]["excerpt"]


@needs_pdftotext
def test_index_survives_projection_publication(world: Path) -> None:
    """Row 2 (B1, D15): build -> projection publication -> index file intact -> search ok."""
    before_files = sorted(p.name for p in get_search_base_dir(world).iterdir())
    assert any(name.startswith("index-") for name in before_files)

    repo = load_repo(world)
    write_outputs(repo, generate_all(repo, generated_at="T1"))

    after_files = sorted(p.name for p in get_search_base_dir(world).iterdir())
    assert before_files == after_files

    res = execute_search(world, "Chebyshev", limit=5)
    _validate_response(res.to_dict())
    assert res.status == "ok"
    assert len(res.hits) == 1


@needs_pdftotext
def test_bound_pdf_replaced_excludes_old_hits_and_reports_coverage(world: Path) -> None:
    """Row 3 (B4, snapshot): bound PDF replaced -> old hits excluded and route appears in coverage."""
    res_before = execute_search(world, "Chebyshev", limit=5)
    assert res_before.status == "ok"
    assert len(res_before.hits) == 1
    old_sha = res_before.hits[0]["sha256"]

    lecture_pdf = world.parent / "materials" / "source-demo-book" / "lecture-01.pdf"
    write_minimal_pdf(lecture_pdf, ["Replacement lecture page one without old keywords"])

    res_after = execute_search(world, "Chebyshev", limit=5)
    _validate_response(res_after.to_dict())
    assert res_after.status == "ok"
    assert all(h["sha256"] != old_sha for h in res_after.hits)
    assert res_after.hits == []

    unindexed = res_after.coverage["unindexed_route_materials"]
    assert any(
        item["material"] == "source-demo-book/lecture-01.pdf"
        and item["reason"] == "not-in-text-cache"
        for item in unindexed
    )
    assert res_after.coverage["scope_complete"] is False


@needs_pdftotext
def test_canonical_write_keeps_matches_text_cache_true(world: Path) -> None:
    """Row 4 (B4, over-invalidation): canonical write + projection rebuild -> matches_text_cache stays true."""
    repo_before = load_repo(world)
    note_path = repo_before.notes["note-demo"].path
    note_path.write_text(
        note_path.read_text(encoding="utf-8") + "\nAdditional learner sentence.\n",
        encoding="utf-8",
    )
    # Also add a non-PDF working file under materials/
    (world.parent / "materials" / "scratch-notes.md").write_text(
        "# Working notes\n", encoding="utf-8"
    )
    repo = load_repo(world)
    write_outputs(repo, generate_all(repo, generated_at="T2"))

    res = execute_search(world, "Chebyshev", limit=5)
    _validate_response(res.to_dict())
    assert res.status == "ok"
    assert res.freshness == {"matches_text_cache": True, "changed_shas": []}
    assert len(res.hits) == 1


@needs_pdftotext
def test_cache_entry_added_serves_results_with_matches_text_cache_false(
    world: Path,
) -> None:
    """Row 5 (D6): cache entry added -> results still served (status ok), matches_text_cache false."""
    extra_sha = "e" * 64
    extra_dir = world / "generated" / "text-cache" / extra_sha
    extra_dir.mkdir(parents=True)
    (extra_dir / "index.json").write_text(
        json.dumps({"sha256": extra_sha, "pages": 1, "extractor": "pdftotext+pypdf"}),
        encoding="utf-8",
    )

    res = execute_search(world, "Chebyshev", limit=5)
    _validate_response(res.to_dict())
    assert res.status == "ok"
    assert len(res.hits) == 1
    assert res.freshness["matches_text_cache"] is False
    assert extra_sha in res.freshness["changed_shas"]


def test_missing_meta_and_incompatible_schema_or_tokenizer(tmp_path: Path) -> None:
    """Row 6 (B4, fail-open): missing index, missing meta, wrong schema_version or tokenizer."""
    res_missing = execute_search(tmp_path, "Chebyshev")
    _validate_response(res_missing.to_dict())
    assert res_missing.status == "unavailable"
    assert res_missing.reason == "index_missing"

    # 1. Database without schema_version in meta -> index_corrupt
    db_missing_meta = tmp_path / "index-1111111111111111.sqlite3"
    con = sqlite3.connect(str(db_missing_meta))
    con.execute("CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT);")
    con.execute("INSERT INTO meta VALUES ('tokenizer', 'unicode61 remove_diacritics 2');")
    con.commit()
    con.close()
    res_corrupt = execute_search(tmp_path, "Chebyshev", index_path=db_missing_meta)
    _validate_response(res_corrupt.to_dict())
    assert res_corrupt.status == "unavailable"
    assert res_corrupt.reason == "index_corrupt"

    # 2. Database with wrong schema_version -> index_incompatible
    db_incompat = tmp_path / "index-2222222222222222.sqlite3"
    con = sqlite3.connect(str(db_incompat))
    con.execute("CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT);")
    meta_rows = {
        "schema_version": "99",
        "tokenizer": "unicode61 remove_diacritics 2",
        "fingerprint": "2" * 64,
        "extractor": "pdftotext+pypdf",
        "built_at": "2026-11-08T00:00:00Z",
        "documents_indexed": "0",
        "documents_total": "0",
        "documents_without_text": "0",
        "pages_indexed": "0",
        "pages_without_text": "0",
        "pages_total": "0",
    }
    con.executemany("INSERT INTO meta VALUES (?, ?);", list(meta_rows.items()))
    con.commit()
    con.close()
    res_incompat = execute_search(tmp_path, "Chebyshev", index_path=db_incompat)
    _validate_response(res_incompat.to_dict())
    assert res_incompat.status == "unavailable"
    assert res_incompat.reason == "index_incompatible"

    # 3. Database with wrong tokenizer -> index_incompatible
    con = sqlite3.connect(str(db_incompat))
    con.execute("UPDATE meta SET value = '1' WHERE key = 'schema_version';")
    con.execute("UPDATE meta SET value = 'porter' WHERE key = 'tokenizer';")
    con.commit()
    con.close()
    res_tok = execute_search(tmp_path, "Chebyshev", index_path=db_incompat)
    _validate_response(res_tok.to_dict())
    assert res_tok.status == "unavailable"
    assert res_tok.reason == "index_incompatible"


@needs_pdftotext
def test_corrupted_cache_page_excluded_before_build(world: Path) -> None:
    """Row 7 (B4, cache validation): page corrupted before build -> entry excluded and reported."""
    res_initial = execute_search(world, "Chebyshev", limit=5)
    lecture_sha = str(res_initial.hits[0]["sha256"])

    page_19 = world / "generated" / "text-cache" / lecture_sha / "pp-0019.txt"
    page_19.write_text("CORRUPTED_PROBE_TOKEN_B4\n", encoding="utf-8")

    # Rebuild without --force: fingerprint changes because lecture_sha becomes excluded
    builder.build_index_generation(world, force=False)

    res_probe = execute_search(world, "CORRUPTED_PROBE_TOKEN_B4", limit=5)
    _validate_response(res_probe.to_dict())
    assert res_probe.status == "ok"
    assert res_probe.hits == []
    assert any(
        ex["sha256"] == lecture_sha and ex["reason"] == "cache-entry-invalid"
        for ex in res_probe.coverage["excluded_cache_entries"]
    )
    assert any(
        u["sha256"] == lecture_sha and u["reason"] == "cache-entry-invalid"
        for u in res_probe.coverage["unindexed_route_materials"]
    )


@needs_pdftotext
def test_zero_filled_or_damaged_db_returns_ok_or_index_corrupt_json(
    world: Path,
) -> None:
    """Row 8 (H3, D14): zero-filled or damaged region -> ok or index_corrupt, always valid JSON."""
    fp, active_db, _meta = check_index_integrity(world)
    assert fp.startswith(active_db.stem.removeprefix("index-"))

    # 1. Overwrite mid-file / FTS shadow data and header
    raw_bytes = active_db.read_bytes()

    # Overwrite header -> index_corrupt via both execute_search and CLI
    active_db.write_bytes(b"X" * 100 + raw_bytes[100:])
    res_hdr = execute_search(world, "Chebyshev")
    _validate_response(res_hdr.to_dict())
    assert res_hdr.status == "unavailable"
    assert res_hdr.reason == "index_corrupt"

    cli_proc = run_los(world, "material-search", "Chebyshev", "--json")
    assert cli_proc.returncode == 0
    cli_payload = json.loads(cli_proc.stdout)
    _validate_response(cli_payload)
    assert cli_payload["status"] == "unavailable"
    assert cli_payload["reason"] == "index_corrupt"

    assert builder.main(["--root", str(world), "--check"]) == 1

    # 2. Restore DB, then corrupt FTS5 _data shadow table so connect() succeeds but MATCH fails
    active_db.write_bytes(raw_bytes)
    con = sqlite3.connect(str(active_db))
    con.execute("DELETE FROM material_fts_data;")
    con.commit()
    con.close()

    res_fts = execute_search(world, "Chebyshev")
    _validate_response(res_fts.to_dict())
    assert res_fts.status in ("ok", "unavailable")
    if res_fts.status == "unavailable":
        assert res_fts.reason == "index_corrupt"


@needs_pdftotext
def test_os_replace_failure_preserves_old_index_and_busy_lock_exits_3(
    world: Path,
) -> None:
    """Row 9 (M1, L4): os.replace fails -> old index still served; busy lock -> exit 3."""
    active_db = open_index(world).db_path

    with patch("build_material_search_index.os.replace", side_effect=OSError(28, "ENOSPC")):
        with pytest.raises(OSError):
            builder.build_index_generation(world, force=True)

    assert active_db.is_file()
    leftovers = [
        p.name for p in get_search_base_dir(world).iterdir() if p.name.startswith(".build-")
    ]
    assert leftovers == []

    res = execute_search(world, "Chebyshev", limit=5)
    assert res.status == "ok"
    assert len(res.hits) == 1

    # Busy lock exits 3 and deletes nothing
    lock_path = get_search_base_dir(world) / ".build.lock"
    fd = os.open(str(lock_path), os.O_CREAT | os.O_RDWR, 0o644)
    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    try:
        rc = builder.main(["--root", str(world), "--force"])
        assert rc == 3
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)
    assert active_db.is_file()


@needs_pdftotext
def test_shared_pdf_across_units_and_sql_pre_limit_filtering(world: Path) -> None:
    """Row 10 (H1, D8): two units share one PDF; > 3*limit matches outside filter."""
    # Bind unit-demo-l02's route in source-map.yaml to the same lecture-01.pdf as unit-demo-l01
    smap_path = world / "curriculum" / "modules" / "module-demo" / "source-map.yaml"
    smap = yaml.safe_load(smap_path.read_text(encoding="utf-8"))
    for src in smap.get("sources", []):
        for route in src.get("unit_routes", []):
            if route.get("unit_id") == "unit-demo-l02":
                route["id"] = "route-demo-l02-shared"
                route["locator"] = "lecture-01.pdf"
    write_yaml(smap_path, smap)

    # Create an unbound distraction PDF with 20 pages (> 3 * limit for limit=5) matching "Expected"
    distractor_pdf = world.parent / "materials" / "source-demo-book" / "distractor.pdf"
    write_minimal_pdf(
        distractor_pdf,
        [f"Expected Expected Expected Expected distractor page {i}" for i in range(1, 21)],
    )
    _refresh_manifest_and_text_cache(world)
    builder.build_index_generation(world, force=True)
    # Hits are section groups: per-page sections keep every matching page its
    # own group, so the distractor's 20 sections still crowd a limit of 5 and
    # only a filter applied inside SQL before LIMIT can surface lecture-01.
    lecture_pdf = world.parent / "materials" / "source-demo-book" / "lecture-01.pdf"
    _write_page_outline(world, lecture_pdf)
    _write_page_outline(world, distractor_pdf)

    # Unfiltered search at limit=5 is dominated by distractor.pdf
    res_unfiltered = execute_search(world, "Expected", limit=5)
    assert res_unfiltered.status == "ok"
    assert any(h["material"].endswith("distractor.pdf") for h in res_unfiltered.hits)

    # Filtered by the second unit sharing lecture-01.pdf: returns 5 hits from lecture-01.pdf
    res_u2 = execute_search(world, "Expected", limit=5, unit_id="unit-demo-l02")
    _validate_response(res_u2.to_dict())
    assert res_u2.status == "ok"
    assert len(res_u2.hits) == 5
    for hit in res_u2.hits:
        assert hit["material"] == "source-demo-book/lecture-01.pdf"
        assert hit["bindings_total"] >= 2
        units_bound = {b["unit"] for b in hit["bindings"]}
        assert {"unit-demo-l01", "unit-demo-l02"}.issubset(units_bound)

    # Unknown unit / module refuses with NotFound
    with pytest.raises(NotFound) as exc_u:
        execute_search(world, "Expected", unit_id="unit-does-not-exist")
    assert exc_u.value.site == "material.search.unknown-unit"

    with pytest.raises(NotFound) as exc_m:
        execute_search(world, "Expected", module_id="module-does-not-exist")
    assert exc_m.value.site == "material.search.unknown-module"


@needs_pdftotext
def test_schema_refusals_term_cap_and_vm_step_budget(world: Path) -> None:
    """Row 11 (M3, D10): schema refusals, 32-term cap, and VM-step budget backstop."""
    with pytest.raises(WriteRefused) as exc_empty:
        execute_search(world, "   ")
    assert exc_empty.value.site == "material.search.empty-query"

    with pytest.raises(WriteRefused) as exc_long:
        execute_search(world, "x" * 501)
    assert exc_long.value.site == "material.search.query-too-long"

    with pytest.raises(WriteRefused) as exc_off:
        execute_search(world, "Expected", offset=201)
    assert exc_off.value.site == "material.search.offset-too-large"

    with pytest.raises(WriteRefused) as exc_lim:
        execute_search(world, "Expected", limit=51)
    assert exc_lim.value.site == "material.search.offset-too-large"

    with pytest.raises(WriteRefused) as exc_terms:
        execute_search(world, " ".join(f"term{i}" for i in range(33)))
    assert exc_terms.value.site == "material.search.too-many-terms"

    with pytest.raises(WriteRefused) as exc_budget:
        execute_search(world, "Expected", vm_step_budget=1)
    assert exc_budget.value.site == "material.search.query-too-expensive"


@needs_pdftotext
def test_nfd_input_punctuation_refusal_has_more_and_deterministic_order(
    world: Path,
) -> None:
    """Row 12 (L1-L3, D11, D12): NFD input, punctuation-only refusal, has_more, deterministic paging."""
    with pytest.raises(WriteRefused) as exc_punct:
        execute_search(world, "?!...")
    assert exc_punct.value.site == "material.search.no-terms"

    # Inject a diaeresis token into page 1 of lecture-01 cache and rebuild to test NFC vs NFD
    res0 = execute_search(world, "Chebyshev", limit=1)
    lecture_sha = str(res0.hits[0]["sha256"])
    cache_dir = world / "generated" / "text-cache"
    p1_path = cache_dir / lecture_sha / "pp-0001.txt"
    p1_path.write_text(
        p1_path.read_text(encoding="utf-8") + "\nÜbung zur Induktion\n",
        encoding="utf-8",
    )
    # Update pages_sha256 in index.json so cache entry stays valid
    idx_file = cache_dir / lecture_sha / "index.json"
    idx_data = json.loads(idx_file.read_text(encoding="utf-8"))
    del idx_data["pages_sha256"]
    idx_file.write_text(json.dumps(idx_data), encoding="utf-8")
    material_text._heal_index(cache_dir, lecture_sha, int(idx_data["pages"]))
    builder.build_index_generation(world, force=True)

    nfc_res = execute_search(world, unicodedata.normalize("NFC", "Übung"), limit=5)
    nfd_res = execute_search(world, unicodedata.normalize("NFD", "Übung"), limit=5)
    assert len(nfc_res.hits) == 1
    assert [(h["sha256"], h["page"]) for h in nfc_res.hits] == [
        (h["sha256"], h["page"]) for h in nfd_res.hits
    ]

    # Paging and deterministic order across pages 1-3 at limit=5 vs one call at limit=15.
    # Per-page sections make each matching page its own group (one hit each).
    _write_page_outline(world, world.parent / "materials" / "source-demo-book" / "lecture-01.pdf")
    one_15 = execute_search(world, "Expected", limit=15, offset=0)
    assert len(one_15.hits) == 15
    assert one_15.has_more is True

    paged_15 = []
    for off in (0, 5, 10):
        page_res = execute_search(world, "Expected", limit=5, offset=off)
        _validate_response(page_res.to_dict())
        assert page_res.has_more is True
        paged_15.extend((h["sha256"], h["page"]) for h in page_res.hits)

    assert [(h["sha256"], h["page"]) for h in one_15.hits] == paged_15

    # Final page (20 pages contain "Expected" out of 24)
    tail_res = execute_search(world, "Expected", limit=10, offset=15)
    assert len(tail_res.hits) == 5
    assert tail_res.has_more is False


@needs_pdftotext
def test_open_reader_survives_prune_and_search_writes_no_file(world: Path) -> None:
    """Row 13 (pinning, read-only): an open reader survives a prune; a search writes no file."""
    reader_a = open_index(world)
    db_a = reader_a.db_path
    con_a = reader_a.connect()

    # Read-only mode enforced
    with pytest.raises(sqlite3.OperationalError):
        con_a.execute("CREATE TABLE mutation_attempt (id INT);")

    # Add a new PDF and rebuild so a new index-<F16>.sqlite3 is published and db_a is pruned
    extra_pdf = world.parent / "materials" / "source-demo-book" / "extra.pdf"
    write_minimal_pdf(extra_pdf, ["Extra generation beta content"])
    _refresh_manifest_and_text_cache(world)
    builder.build_index_generation(world, force=True)

    assert not db_a.exists()
    # Open reader_a still queries the unlinked inode cleanly
    rows_a = con_a.execute(
        "SELECT count(*) FROM material_fts WHERE material_fts MATCH '\"Chebyshev\"';"
    ).fetchone()
    assert rows_a[0] == 1
    reader_a.close()

    # Snapshot all file mtimes and paths before search; verify search writes nothing
    def _tree_state(base: Path) -> dict[str, int]:
        return {
            str(p.relative_to(base)): p.stat().st_mtime_ns
            for p in sorted(base.rglob("*"))
            if p.is_file()
        }

    before_state = _tree_state(world.parent)
    res_b = execute_search(world, "Extra", limit=5)
    after_state = _tree_state(world.parent)
    assert res_b.status == "ok"
    assert len(res_b.hits) == 1
    assert before_state == after_state


@needs_pdftotext
def test_legacy_cache_records_labeled_and_empty_index_refused(
    world: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Legacy cache entries (missing pages_sha256) are labeled 'legacy — run --refresh',
    and the builder refuses to publish when no valid cache record remains.
    """
    res_initial = execute_search(world, "Chebyshev", limit=5)
    lecture_sha = str(res_initial.hits[0]["sha256"])
    cache_dir = world / "generated" / "text-cache"

    # Add a second valid PDF so one valid record remains when lecture_sha is made legacy
    second_pdf = world.parent / "materials" / "source-demo-book" / "second-valid.pdf"
    write_minimal_pdf(second_pdf, ["Second valid textbook page"])
    _refresh_manifest_and_text_cache(world)

    # Strip pages_sha256 from lecture_sha's index.json to simulate a pre-refresh legacy record
    lecture_idx = cache_dir / lecture_sha / "index.json"
    lecture_data = json.loads(lecture_idx.read_text(encoding="utf-8"))
    del lecture_data["pages_sha256"]
    lecture_idx.write_text(json.dumps(lecture_data), encoding="utf-8")

    builder.build_index_generation(world, force=True)
    res_mixed = execute_search(world, "Second", limit=5)
    _validate_response(res_mixed.to_dict())
    assert res_mixed.status == "ok"
    assert any(
        ex["sha256"] == lecture_sha and ex["reason"] == "legacy — run --refresh"
        for ex in res_mixed.coverage["excluded_cache_entries"]
    )
    assert any(
        u["sha256"] == lecture_sha and u["reason"] == "legacy — run --refresh"
        for u in res_mixed.coverage["unindexed_route_materials"]
    )

    # Now make every cache entry legacy (no pages_sha256) -> builder must refuse to publish
    active_db = open_index(world).db_path
    for entry in cache_dir.iterdir():
        idx = entry / "index.json"
        if idx.is_file():
            data = json.loads(idx.read_text(encoding="utf-8"))
            data.pop("pages_sha256", None)
            idx.write_text(json.dumps(data), encoding="utf-8")

    capsys.readouterr()
    rc = builder.main(["--root", str(world), "--force"])
    captured = capsys.readouterr()
    assert rc == 1
    assert "legacy — run --refresh" in captured.err
    assert active_db.is_file()


def test_outline_normalization_owns_pages_and_keeps_ancestors() -> None:
    """The last heading on a page owns it; ancestors come from outline order."""
    rows = [
        (0, "Front matter", 1),
        (0, "6 Probability", 10),
        (1, "6.1 Big idea", 11),
        (1, "6.2 Fundamentals", 12),
        (2, "6.2.1  Bayes\u2019 Theorem", 14),
        (2, "6.2.2 Prediction", 17),
        (1, "dangling", None),        # unresolvable destination: dropped
        (1, "out of range", 99),      # outside the document: dropped
        (0, "", 18),                  # untitled: dropped
        (0, "7 Errors", 20),
        (1, "7.1 Same page child", 20),   # same start page: the later row owns it
    ]
    status, sections = normalize_outline(rows, 25)
    assert status == "present"
    owned = [(row.title, row.start_page, row.end_page) for row in sections]
    assert owned == [
        ("Front matter", 1, 9), ("6 Probability", 10, 10), ("6.1 Big idea", 11, 11),
        ("6.2 Fundamentals", 12, 13), ("6.2.1 Bayes\u2019 Theorem", 14, 16),
        ("6.2.2 Prediction", 17, 19), ("7.1 Same page child", 20, 25),
    ]
    bayes = sections[4]
    assert bayes.level == 2 and bayes.path == ("6 Probability", "6.2 Fundamentals")
    assert normalize_outline([], 10) == ("absent", [])
    assert normalize_outline([(0, "x", None), (0, "y", 50)], 10) == ("unusable", [])

    record = search_index.OutlineRecord("present", 25, tuple(sections[1:]))
    assert record.locate(3) == (None, "before-first-heading")
    assert record.locate(15) == (3, None)
    assert search_index.OutlineRecord("absent", 25).locate(3) == (None, "no-outline")
    assert search_index.OutlineRecord("not-harvested").locate(3) == (None, "not-harvested")

    # The widest range equals material-span's page cap, and grows only
    # through neighbouring matched pages.
    from learning_os.store.materials.slices import MAX_SLICE_PAGES
    assert search_index.MAX_SPAN_PAGES == MAX_SLICE_PAGES
    assert span_pages_for(288, [287, 288, 289]) == "pdf pp. 287-289"
    assert span_pages_for(288, [288, 300]) == "pdf p. 288"
    assert span_pages_for(5, [1, 3, 5, 7]) == "pdf pp. 1-7"
    assert span_pages_for(1, list(range(1, 60))) == "pdf pp. 1-20"


def test_outline_payload_validation_fails_closed() -> None:
    sha = "a" * 64
    good = outline_payload(sha, "x.pdf", 10, "present",
                           [OutlineSection("One", 0, (), 1, 4),
                            OutlineSection("Two", 0, (), 5, 10)], "tests")
    assert parse_outline_payload(good, sha) is not None
    assert parse_outline_payload(good, "b" * 64) is None
    for mutate in (
        lambda d: d.update(schema_version=True),
        lambda d: d.update(normalizer="material-outline-0"),
        lambda d: d.update(status="mystery"),
        lambda d: d.update(status="absent"),                         # sections contradict status
        lambda d: d["sections"][1].update(start_page=4),            # overlap
        lambda d: d["sections"][1].update(end_page=11),             # beyond the page count
        lambda d: d["sections"][0].update(level=-1),
        lambda d: d["sections"][0].update(path="not-a-list"),
        lambda d: d["sections"][0].update(title=""),
    ):
        broken = json.loads(json.dumps(good))
        mutate(broken)
        assert parse_outline_payload(broken, sha) is None, broken


def test_query_names_expand_only_on_an_exact_concept_name() -> None:
    concepts = {
        "concept-bayes-theorem": {"label": "Bayes' theorem",
                                  "aliases": ["Satz von Bayes", "Bayes rule"]},
        "concept-other": {"label": "Other", "aliases": ["PDF"]},
    }
    names, ids = expand_query_names("Satz  von BAYES", concepts)
    assert ids == ["concept-bayes-theorem"]
    assert names == ["satz von bayes", "bayes theorem", "bayes rule"]
    assert expand_query_names("Bayes theorem", concepts)[0] == [
        "bayes theorem", "satz von bayes", "bayes rule"]
    # A concept name inside a longer question is not a request for the concept.
    assert expand_query_names("Satz von Bayes Beispiel", concepts) == (
        ["satz von bayes beispiel"], [])
    assert expand_query_names("pdf", None) == (["pdf"], [])
    # Without extra names the tiers are exactly the single-query tiers.
    assert build_tiered_queries("Satz von Bayes", []) == build_tiered_queries("Satz von Bayes")
    tiers = dict(build_tiered_queries("Erwartungswert", ["expected value"]))
    assert tiers["exact_phrase"] == '"erwartungswert" OR "expected value"'
    assert tiers["conjunction"] == '("erwartungswert") OR ("expected" AND "value")'
    assert "disjunction" not in tiers


@needs_pdftotext
def test_hits_group_by_outline_section_with_explicit_unsectioned_groups(world: Path) -> None:
    """One hit per section group; pages before the first heading and documents
    without an outline land in explicit unsectioned groups with a reason."""
    lecture = world.parent / "materials" / "source-demo-book" / "lecture-01.pdf"
    lecture_sha, pages = _cached_pdf(world, lecture)
    _write_outline(world, lecture_sha, pages, [
        OutlineSection("1 Expectation", 0, (), 3, 9),
        OutlineSection("2 Tail bounds", 0, (), 10, 24),
    ])
    res = execute_search(world, "Expected value", limit=10)
    _validate_response(res.to_dict())
    groups = [(h["section"]["title"] if h["section"] else None, h["unsectioned"],
               h["pages"], h["pages_total"]) for h in res.hits]
    # Equal BM25 scores tie-break by page, so groups rank at their first page.
    assert groups == [
        (None, "before-first-heading", [1, 2], 2),
        ("1 Expectation", None, [3, 4, 5, 6, 7, 8, 9], 7),
        ("2 Tail bounds", None, list(range(10, 21)), 11),
    ]
    assert [h["rank"] for h in res.hits] == [1, 2, 3]
    for hit in res.hits:
        assert hit["page"] in hit["pages"]
        assert (hit["section"] is None) != (hit["unsectioned"] is None)
        # span_reference still opens the best page, as before grouping.
        assert hit["span_reference"]["pages"] == f"pdf p. {hit['page']}"
    tail = next(h for h in res.hits if h["section"] and h["section"]["title"] == "2 Tail bounds")
    assert tail["section"] == {"title": "2 Tail bounds", "level": 0, "path": [],
                               "start_page": 10, "end_page": 24}
    assert tail["span_pages"] == "pdf pp. 10-20"

    # A cache file that fails validation, an outline-less document, and a
    # digest never harvested each say so.
    outline_file = get_outline_base_dir(world) / f"{lecture_sha}.json"
    outline_file.write_text("{not json", encoding="utf-8")
    assert {h["unsectioned"] for h in execute_search(world, "Expected", limit=5).hits} == {
        "cache-invalid"}
    assert load_outline(world, lecture_sha).status == "cache-invalid"
    _write_outline(world, lecture_sha, pages, [], status="absent")
    assert {h["unsectioned"] for h in execute_search(world, "Expected", limit=5).hits} == {
        "no-outline"}
    outline_file.unlink()
    only = execute_search(world, "Expected", limit=5).hits
    assert [(h["unsectioned"], h["pages_total"]) for h in only] == [("not-harvested", 20)]


@needs_pdftotext
def test_group_paging_is_stable_across_offsets(world: Path) -> None:
    """limit/offset count groups over one fixed scan: no group repeats or moves."""
    lecture = world.parent / "materials" / "source-demo-book" / "lecture-01.pdf"
    lecture_sha, pages = _cached_pdf(world, lecture)
    _write_outline(world, lecture_sha, pages, [
        OutlineSection(f"Part {i}", 0, (), start, min(start + 2, pages))
        for i, start in enumerate(range(1, pages + 1, 3), start=1)])
    whole = execute_search(world, "Expected", limit=50)
    keys = [(h["sha256"], h["section"]["title"]) for h in whole.hits]
    assert len(keys) == len(set(keys)) == 7 and whole.has_more is False
    paged: list[tuple[str, str]] = []
    for offset in range(0, 7, 2):
        window = execute_search(world, "Expected", limit=2, offset=offset)
        _validate_response(window.to_dict())
        assert window.has_more is (offset + 2 < 7)
        assert [h["rank"] for h in window.hits] == list(range(offset + 1, offset + 1 + len(window.hits)))
        paged.extend((h["sha256"], h["section"]["title"]) for h in window.hits)
    assert paged == keys
    assert sum(h["pages_total"] for h in whole.hits) == 20


@needs_pdftotext
def test_scan_cap_bounds_candidates_and_reports_truncation(
    world: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_page_outline(world, world.parent / "materials" / "source-demo-book" / "lecture-01.pdf")
    full = execute_search(world, "Expected", limit=50)
    assert full.scan_truncated is False and len(full.hits) == 20
    monkeypatch.setattr(search_index, "SCAN_PAGE_CAP", 6)
    capped = execute_search(world, "Expected", limit=50)
    _validate_response(capped.to_dict())
    assert capped.scan_truncated is True and capped.has_more is False
    assert [h["page"] for h in capped.hits] == [h["page"] for h in full.hits[:6]]


@needs_pdftotext
def test_concept_alias_finds_the_same_material_in_both_languages(world: Path) -> None:
    """`Erwartungswert` (alias) and `Expected value` (label) find the same pages."""
    german = world.parent / "materials" / "source-demo-book" / "skript-de.pdf"
    write_minimal_pdf(german, ["Der Erwartungswert gewichtet jedes Ergebnis",
                               "Varianz und Streuung"])
    _refresh_manifest_and_text_cache(world)
    builder.build_index_generation(world, force=True)

    by_alias = execute_search(world, "Erwartungswert", limit=50)
    by_label = execute_search(world, "Expected value", limit=50)
    for res in (by_alias, by_label):
        _validate_response(res.to_dict())
        assert res.expansion is not None
        assert res.expansion["concepts"] == ["concept-expected-value"]
    assert by_alias.expansion["names"] == ["erwartungswert", "expected value"]
    assert by_label.expansion["names"] == ["expected value", "erwartungswert"]
    found = {h["material"] for h in by_alias.hits}
    assert {"source-demo-book/skript-de.pdf", "source-demo-book/lecture-01.pdf"} <= found
    assert {h["material"] for h in by_label.hits} == found

    # No exact concept name, no expansion: the German page stays out of reach.
    plain = execute_search(world, "Erwartungswert gewichtet", limit=50)
    assert plain.expansion is None
    assert {h["material"] for h in plain.hits} == {"source-demo-book/skript-de.pdf"}


@needs_pdftotext
def test_material_outline_tool_harvests_bookmarks_and_skips_changed_bytes(world: Path) -> None:
    from pypdf import PdfReader, PdfWriter

    lecture = world.parent / "materials" / "source-demo-book" / "lecture-01.pdf"
    writer = PdfWriter(clone_from=PdfReader(str(lecture)))
    chapter = writer.add_outline_item("1 Expectation", 0)
    writer.add_outline_item("1.1 Weights", 1, parent=chapter)
    writer.add_outline_item("2 Bounds", 16)
    with lecture.open("wb") as handle:
        writer.write(handle)
    _refresh_manifest_and_text_cache(world)
    builder.build_index_generation(world, force=True)
    sha, pages = _cached_pdf(world, lecture)

    paths = {"text_cache": world / "generated" / "text-cache",
             "outline_dir": get_outline_base_dir(world),
             "materials_root": world.parent / "materials"}
    pending = material_outline.run(refresh=False, **paths)
    assert pending["outcomes"].get("not-harvested", 0) >= 1
    first = material_outline.run(refresh=True, **paths)
    assert first["outcomes"]["written-present"] == 1
    record = load_outline(world, sha)
    assert [(s.title, s.path, s.start_page, s.end_page) for s in record.sections] == [
        ("1 Expectation", (), 1, 1), ("1.1 Weights", ("1 Expectation",), 2, 16),
        ("2 Bounds", (), 17, pages)]
    assert material_outline.main(["--check", "--repo", str(world)]) == 0
    again = material_outline.run(refresh=True, **paths)
    assert not any(name.startswith("written") for name in again["outcomes"])

    hit = execute_search(world, "Chebyshev", limit=1).hits[0]
    assert hit["section"]["title"] == "2 Bounds" and hit["section"]["start_page"] == 17

    # An orphaned entry is pruned; bytes that no longer match the digest are
    # never cached under it.
    orphan = get_outline_base_dir(world) / f"{'e' * 64}.json"
    orphan.write_text("{}", encoding="utf-8")
    (get_outline_base_dir(world) / f"{sha}.json").unlink()
    lecture.write_bytes(lecture.read_bytes() + b"\n% changed\n")
    changed = material_outline.run(refresh=True, **paths)
    assert changed["outcomes"]["skipped-changed-file"] == 1 and changed["pruned"] == 1
    assert not (get_outline_base_dir(world) / f"{sha}.json").exists()


@pytest.mark.live_install
def test_live_install_smoke() -> None:
    """Optional live-install smoke test (skipped under -m 'not live_install' in CI)."""
    res = execute_search(REPO_ROOT, "Mittelwertsatz", limit=3)
    assert res.status in ("ok", "unavailable")
    _validate_response(res.to_dict())
