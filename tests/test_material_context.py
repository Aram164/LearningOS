"""Material-context retrieval: explanations by need, honestly labeled.

Finds saved analysis notes and approved unit assessments through
deterministic lexical matching with concept, purpose, and unit filters.
Freshness is observed live, review state and resolution are reported, and
empty results describe the searched records without claiming absence.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import yaml
from gateway_helpers import approved_v2_cli, file_sha256
from repo_builders import _compact_setup, add_curriculum, run_los, write_yaml

from learning_os.material_synthesis import synthesis_destination

ANALYSIS_BODY = """# Density intuition

The density chapter explains probability mass spreading over intervals.
A worked example integrates the uniform density step by step.
"""


def _plant_note(root: Path, note_id: str, body: str, binding: dict,
                concepts: list[str] | None = None,
                title: str = "Planted analysis"):
    meta = {"id": note_id, "type": "note", "role": "reference",
            "title": title, "created": "2026-09-21",
            "state": "rough", "authorship": "operator-drafted",
            "semantic_review": "unreviewed",
            "material_analysis": binding}
    if concepts is not None:
        meta["concepts"] = concepts
    path = root / "knowledge/notes/mathematics" / f"{note_id}.md"
    front = "---\n" + yaml.safe_dump(meta, sort_keys=False).rstrip() + "\n---\n\n"
    raw = front.encode("utf-8") + body.encode("utf-8")
    path.write_bytes(raw)
    return path


def _binding(material: str, digest: str, body: str, **overrides):
    binding = {
        "resolution": "resolved",
        "material": material,
        "source_id": "source-demo-book",
        "recorded_source_digest": digest,
        "live_source_digest": digest,
        "inspected_range": {"start": 1, "end": 3},
        "frozen_input_sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
        "frozen_input_bytes": len(body.encode("utf-8")),
    }
    binding.update(overrides)
    if binding["resolution"] != "resolved":
        # Only a resolved binding names a registered source (schema else-branch).
        binding.pop("source_id", None)
    if binding["resolution"] == "unavailable":
        binding.pop("live_source_digest", None)
    return binding


def _seed_material(root: Path, name: str, data: bytes) -> str:
    target = root.parent / "materials" / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    return hashlib.sha256(data).hexdigest()


def test_unit_note_scope_uses_the_sources_declared_material_authority(mini_repo):
    from repo_builders import _sliced_route, _sliced_unit

    from learning_os.commands.reads import _route_material_files, _unit_note_scope
    from learning_os.loader import load_repo

    route = _sliced_route("route-demo-alias", "shared.pdf, PDF pp. 1-3")
    _sliced_unit(mini_repo, [route])
    registry_path = mini_repo / "sources/sources.yaml"
    registry = yaml.safe_load(registry_path.read_text())
    registry["sources"][0]["material"] = "material://source-shared-library/"
    write_yaml(registry_path, registry)
    _seed_material(mini_repo, "source-shared-library/shared.pdf", b"observed shared bytes")
    repo = load_repo(mini_repo)
    binding = {"source_id": "source-demo-book", "material": "source-shared-library/shared.pdf",
               "inspected_range": {"start": 1, "end": 3}}
    assert _route_material_files(repo, "source-demo-book", route) == {binding["material"]}
    assert _unit_note_scope(repo, binding, [("source-demo-book", route)]) == "direct"
    # Identity still requires the exact file; a same-folder neighbor is related.
    binding["material"] = "source-shared-library/neighbor.pdf"
    assert _unit_note_scope(repo, binding, [("source-demo-book", route)]) == "related"


def _seed_unit(root: Path):
    # Expanded routes, not the bare add_curriculum string joins: unit scope
    # is route-based, so a same-source note proves nothing until a route
    # names its file. The source-id-prefixed materials layout lets
    # material:// URIs resolve without a .flat farm.
    from repo_builders import _sliced_route, _sliced_unit

    _sliced_unit(root, [_sliced_route("route-demo-density", "deck.pdf, pp. 1-3")])
    unit_dir = root / "curriculum/modules/module-demo/units/unit-demo-l01"
    write_yaml(unit_dir / "material-synthesis.yaml", {
        "schema_version": 1, "id": "material-synthesis-demo-l01",
        "type": "unit-material-synthesis", "unit_id": "unit-demo-l01",
        "status": "approved",
        "route_assessments": [{
            "route_id": "route-demo-density",
            "source_id": "source-demo-book",
            "locator": "deck.pdf, pp. 1-3",
            "review_status": "deep-reviewed",
            "concept_ids": ["concept-expected-value"],
            "contribution": "Derives density intuition from first principles.",
            "best_for": "A worked example of uniform density integration.",
        }],
    })


def _context(root: Path, *args: str):
    proc = run_los(root, "material-context", *args)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    return json.loads(proc.stdout)


def test_finds_analysis_by_need_with_freshness_and_open_refs(mini_repo):
    digest = _seed_material(mini_repo, "deck.pdf", b"live bytes")
    _plant_note(mini_repo, "note-context-density-pp001-003", ANALYSIS_BODY,
                 _binding("deck.pdf", digest, ANALYSIS_BODY))
    first = _context(mini_repo, "density worked example")
    assert first["contract"] == "material-context"
    assert first["total"] == 1
    item = first["items"][0]
    assert item["origin"] == "analysis-note"
    assert item["id"] == "note-context-density-pp001-003"
    assert item["match"]["terms"] == ["density", "worked", "example"]
    assert any("density" in snippet["text"].lower()
               for snippet in item["match"]["snippets"])
    assert item["source"] == {"ref": "deck.pdf", "pages": [1, 3],
                              "freshness": "current"}
    assert item["review"] == {"semantic_review": "unreviewed",
                              "resolution": "resolved"}
    assert item["path"].endswith(".md")
    assert first["searched"]["analysis_notes"] == 1
    # Stable order: a second run returns the identical item sequence.
    second = _context(mini_repo, "density worked example")
    assert [row["id"] for row in second["items"]] == [item["id"]]


def test_concept_alias_purpose_and_unit_filters(mini_repo):
    digest = _seed_material(mini_repo, "source-demo-book/deck.pdf", b"live bytes")
    _plant_note(mini_repo, "note-context-density-pp001-003", ANALYSIS_BODY,
                 _binding("source-demo-book/deck.pdf", digest, ANALYSIS_BODY,
                          anchors=[{"topic": "Density", "purpose": "intuition",
                                    "locator": "p. 2"}]),
                 concepts=["concept-expected-value"])
    _plant_note(mini_repo, "note-context-other-pp001-003",
                 "Density without the concept link.\n",
                 _binding("other.pdf", "ef" * 32, "Density without the concept link.\n",
                          resolution="unavailable"))
    _seed_unit(mini_repo)

    aliased = _context(mini_repo, "density", "--concept", "Erwartungswert")
    assert [row.get("id", row.get("route_id")) for row in aliased["items"]] == [
        "note-context-density-pp001-003", "route-demo-density"]
    assert aliased["items"][0]["match"]["concept"] == "concept-expected-value"
    assert aliased["items"][1]["origin"] == "unit-assessment"
    assert aliased["items"][1]["unit_id"] == "unit-demo-l01"
    assert aliased["items"][1]["open"]["route_id"] == "route-demo-density"

    purposed = _context(mini_repo, "density", "--purpose", "intuition")
    assert [row.get("id", row.get("route_id")) for row in purposed["items"]] == [
        "note-context-density-pp001-003"]

    _plant_note(mini_repo, "note-context-related-pp001-003",
                 "Density from an unrouted file.\n",
                 _binding("source-demo-book/other.pdf", "ee" * 32,
                          "Density from an unrouted file.\n"))
    scoped = _context(mini_repo, "density", "--unit", "unit-demo-l01")
    assert [row.get("id", row.get("route_id")) for row in scoped["items"]] == [
        "note-context-density-pp001-003", "route-demo-density"]
    assert scoped["items"][0]["scope"] == "direct"
    assert scoped["pool"]["related_analysis_notes"] == 1
    widened = _context(mini_repo, "density", "--unit", "unit-demo-l01",
                       "--include-related")
    widened_notes = [row for row in widened["items"]
                     if row["origin"] == "analysis-note"]
    assert [row["id"] for row in widened_notes] == [
        "note-context-density-pp001-003", "note-context-related-pp001-003"]
    assert [row["scope"] for row in widened_notes] == ["direct", "related"]
    assert widened["searched"]["include_related"] is True

    unknown = run_los(mini_repo, "material-context", "density",
                       "--concept", "concept-nope")
    assert unknown.returncode == 2
    assert "unknown concept" in unknown.stderr
    bad_unit = run_los(mini_repo, "material-context", "density",
                        "--unit", "unit-nope")
    assert bad_unit.returncode == 2
    assert "unknown unit" in bad_unit.stderr


def test_stale_unreadable_and_unresolved_keep_their_labels(mini_repo):
    live = _seed_material(mini_repo, "deck.pdf", b"live bytes")
    _plant_note(mini_repo, "note-context-stale-pp001-003", "Density ages.\n",
                 _binding("deck.pdf", "00" * 32, "Density ages.\n",
                          resolution="stale", live_source_digest=live))
    (mini_repo.parent / "materials" / "deck.pdf").write_bytes(b"changed bytes")
    _plant_note(mini_repo, "note-context-gone-pp001-003", "Density gone.\n",
                 _binding("gone.pdf", "ab" * 32, "Density gone.\n",
                          resolution="unavailable"))
    result = _context(mini_repo, "density")
    by_id = {row["id"]: row for row in result["items"]}
    assert by_id["note-context-stale-pp001-003"]["source"]["freshness"] == "stale"
    assert by_id["note-context-stale-pp001-003"]["review"]["resolution"] == "stale"
    assert by_id["note-context-gone-pp001-003"]["source"]["freshness"] == "unreadable"
    assert result["pool"]["analysis_unreviewed"] == 2
    assert result["pool"]["analysis_by_resolution"]["unavailable"] == 1


def test_empty_results_describe_the_corpus_and_refuse_empty_queries(mini_repo):
    digest = _seed_material(mini_repo, "deck.pdf", b"live bytes")
    _plant_note(mini_repo, "note-context-density-pp001-003", ANALYSIS_BODY,
                 _binding("deck.pdf", digest, ANALYSIS_BODY))
    result = _context(mini_repo, "quasistrophoid")
    assert result["total"] == 0 and result["items"] == []
    assert result["searched"]["analysis_notes"] == 1
    assert "never proves" in result["empty"]
    blank = run_los(mini_repo, "material-context", "   ")
    assert blank.returncode == 2
    assert "nonempty query" in blank.stderr


def test_pagination_continuation_refuses_changed_snapshots(mini_repo):
    digest = _seed_material(mini_repo, "deck.pdf", b"live bytes")
    _plant_note(mini_repo, "note-context-density-pp001-003", ANALYSIS_BODY,
                 _binding("deck.pdf", digest, ANALYSIS_BODY))
    _plant_note(mini_repo, "note-context-density-pp004-006",
                 "More density notes.\n",
                 _binding("deck2.pdf", "cd" * 32, "More density notes.\n",
                          resolution="unavailable"))
    first = _context(mini_repo, "density", "--limit", "1")
    assert first["total"] == 2 and len(first["items"]) == 1
    assert first["next_offset"] == 1
    assert first["observations_sha256"].startswith("sha256:")
    second = _context(mini_repo, "density", "--limit", "1", "--offset", "1",
                       "--expected-snapshot", first["snapshot_id"],
                       "--expected-observations", first["observations_sha256"])
    assert [row["id"] for row in second["items"]] == ["note-context-density-pp004-006"]
    assert second["next_offset"] is None
    assert second["observations_sha256"] == first["observations_sha256"]
    (mini_repo / "knowledge/notes/mathematics/note-context-density-pp004-006.md"
     ).write_text("changed", encoding="utf-8")
    moved = run_los(mini_repo, "material-context", "density", "--limit", "1",
                     "--offset", "1", "--expected-snapshot", first["snapshot_id"],
                     "--expected-observations", first["observations_sha256"])
    assert moved.returncode == 3
    assert "snapshot" in moved.stderr


def test_pagination_binds_observed_material(mini_repo):
    digest = _seed_material(mini_repo, "deck.pdf", b"live bytes")
    _plant_note(mini_repo, "note-context-density-pp001-003", ANALYSIS_BODY,
                 _binding("deck.pdf", digest, ANALYSIS_BODY))
    _plant_note(mini_repo, "note-context-density-pp004-006",
                 "More density notes.\n",
                 _binding("deck2.pdf", "cd" * 32, "More density notes.\n",
                          resolution="unavailable"))
    first = _context(mini_repo, "density", "--limit", "1")
    assert first["total"] == 2
    # A continuation without the observations binding is refused outright.
    bare = run_los(mini_repo, "material-context", "density", "--limit", "1",
                   "--offset", "1", "--expected-snapshot", first["snapshot_id"])
    assert bare.returncode == 2
    assert "expected-observations" in bare.stderr
    # Changed bytes between pages refuse under the same continuation.
    (mini_repo.parent / "materials" / "deck.pdf").write_bytes(b"drifted bytes")
    drifted = run_los(mini_repo, "material-context", "density", "--limit", "1",
                       "--offset", "1", "--expected-snapshot",
                       first["snapshot_id"], "--expected-observations",
                       first["observations_sha256"])
    assert drifted.returncode == 2
    assert "changed between pages" in drifted.stderr
    # A fresh first page rebinds to the moved bytes.
    rebound = _context(mini_repo, "density", "--limit", "1")
    assert rebound["observations_sha256"] != first["observations_sha256"]
    assert rebound["items"][0]["source"]["freshness"] == "stale"


def _seed_dossier_with_ref(root: Path):
    _compact_setup(root)
    anchor = {"topic": "Expected value", "purpose": "derivation",
              "locator": "lecture-01.pdf p.1"}
    note_id = "note-context-weighted-derivation"
    material = "source-demo-book/lecture-01.pdf"
    digest = hashlib.sha256((root.parent / "materials" / material).read_bytes()).hexdigest()
    note_path = _plant_note(root, note_id, "Weighted sums derive expectation.\n",
                            _binding(material,
                                     digest, "Weighted sums derive expectation.\n",
                                     anchors=[anchor]))
    note_digest = f"sha256:{hashlib.sha256(note_path.read_bytes()).hexdigest()}"
    destination = synthesis_destination(root, "unit-demo-l01")
    dossier = yaml.safe_load(destination.read_text(encoding="utf-8"))
    dossier["route_assessments"][0]["analysis_refs"] = [{
        "note_id": note_id, "note_revision": 0, "note_digest": note_digest,
        "anchor": anchor, "material": "source-demo-book/lecture-01.pdf",
        "inspected_range": {"start": 1, "end": 3}}]
    destination.write_text(yaml.safe_dump(dossier, sort_keys=False),
                           encoding="utf-8")
    return note_id


def test_assessment_items_carry_live_dossier_freshness(mini_repo, tmp_path):
    note_id = _seed_dossier_with_ref(mini_repo)
    result = _context(mini_repo, "weighted")
    items = [row for row in result["items"] if row["origin"] == "unit-assessment"]
    assert len(items) == 1
    assert items[0]["review_status"] == "deep-reviewed"
    assert items[0]["use_evidence"] == {"counts": {}, "positive": 0,
                                        "mismatch": 0}
    assert items[0]["freshness"] == {"status": "current", "reasons": []}
    # A governed note edit stales the referencing dossier; the stored
    # review status is still reported, now with its freshness warning.
    note_path = mini_repo / "knowledge/notes/mathematics" / f"{note_id}.md"
    revised = tmp_path / "revised.md"
    revised.write_bytes(note_path.read_bytes() + b"\nEdited.\n")
    proc = approved_v2_cli(
        mini_repo, "note-revise", note_id,
        "--file", str(revised), "--approve",
        "--file-sha256", file_sha256(revised),
        artifact_ids=[note_id],
        idempotency_key="context-dossier-stale",
    )
    assert proc.returncode == 0, proc.stderr
    result = _context(mini_repo, "weighted")
    items = [row for row in result["items"] if row["origin"] == "unit-assessment"]
    assert len(items) == 1
    assert items[0]["review_status"] == "deep-reviewed"
    assert items[0]["freshness"]["status"] == "stale"
    assert "analysis-refs-stale" in items[0]["freshness"]["reasons"]


def _register_source(root: Path, source_id: str, title: str):
    registry_path = root / "sources/sources.yaml"
    registry = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    registry["sources"].append({"id": source_id, "title": title,
                                "type": "paper", "authors": ["B. Author"]})
    write_yaml(registry_path, registry)


def _record_feedback(root: Path, entries: list[dict]):
    sm_path = (root / "curriculum/modules/module-demo/units/unit-demo-l01"
               / "study-map.yaml")
    data = yaml.safe_load(sm_path.read_text(encoding="utf-8"))
    data["stages"][0].setdefault("source_feedback", []).extend(entries)
    write_yaml(sm_path, data)


def test_recorded_use_evidence_ranks_and_labels_results(mini_repo):
    add_curriculum(mini_repo)
    _register_source(mini_repo, "source-demo-paper", "Demo Paper")
    book = _seed_material(mini_repo, "book.pdf", b"book bytes")
    paper = _seed_material(mini_repo, "paper.pdf", b"paper bytes")
    body_a = "Shared density intuition from the book.\n"
    body_b = "Shared density intuition from the paper.\n"
    _plant_note(mini_repo, "note-rank-aaa", body_a,
                _binding("book.pdf", book, body_a))
    _plant_note(mini_repo, "note-rank-zzz", body_b,
                _binding("paper.pdf", paper, body_b,
                         source_id="source-demo-paper"))
    _record_feedback(mini_repo, [
        {"source_id": "source-demo-paper", "feedback": "helpful",
         "recorded": "2026-09-21"},
        {"source_id": "source-demo-paper", "feedback": "useful-for-review",
         "recorded": "2026-09-21"},
        {"source_id": "source-demo-book", "feedback": "too-advanced",
         "recorded": "2026-09-21"},
        {"source_id": "source-demo-book", "feedback": "skipped",
         "recorded": "2026-09-21"},
    ])
    result = _context(mini_repo, "density")
    # Stable order would list aaa first; positive evidence promotes zzz.
    assert [row["id"] for row in result["items"]] == ["note-rank-zzz",
                                                     "note-rank-aaa"]
    first, second = result["items"]
    assert first["use_evidence"] == {
        "counts": {"helpful": 1, "useful-for-review": 1},
        "positive": 2, "mismatch": 0}
    assert second["use_evidence"] == {
        "counts": {"skipped": 1, "too-advanced": 1},
        "positive": 0, "mismatch": 1}
    assert "use-evidence" in result["ranked_by"]


def test_ranking_keeps_stable_order_without_recorded_feedback(mini_repo):
    book = _seed_material(mini_repo, "book.pdf", b"book bytes")
    paper = _seed_material(mini_repo, "paper.pdf", b"paper bytes")
    body_a = "Shared density intuition from the book.\n"
    body_b = "Shared density intuition from the paper.\n"
    _plant_note(mini_repo, "note-rank-aaa", body_a,
                _binding("book.pdf", book, body_a))
    _plant_note(mini_repo, "note-rank-zzz", body_b,
                _binding("paper.pdf", paper, body_b,
                         source_id="source-demo-paper"))
    result = _context(mini_repo, "density")
    assert [row["id"] for row in result["items"]] == ["note-rank-aaa",
                                                     "note-rank-zzz"]
    for row in result["items"]:
        assert row["use_evidence"] == {"counts": {}, "positive": 0,
                                       "mismatch": 0}


# ------------------------------------------------- route-based unit scope
def _seed_routed_unit(root: Path):
    """Expanded routes over a source-id-prefixed materials layout.

    materials/source-demo-book/<file> is seeded per route file, so
    material:// URIs resolve without a .flat farm. Routes cover every
    material-derivation path: vault_path, locator file, source-record
    inheritance, and a multi-range locator (identity only).
    """
    from repo_builders import _sliced_route, _sliced_unit

    _sliced_unit(root, [
        {**_sliced_route("route-demo-vault", "deck.pdf, pp. 1-3"),
         "vault_path": "material://source-demo-book/deck.pdf"},
        _sliced_route("route-demo-locator", "slides.pdf, PDF pp. 1-2"),
        _sliced_route("route-demo-inherit",
                      "Lecture reader, curated selection"),
        {**_sliced_route("route-demo-multi", "multi.pdf, pp. 1-2; pp. 5-6"),
         "vault_path": "material://source-demo-book/multi.pdf"},
    ])
    registry_path = root / "sources/sources.yaml"
    registry = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    registry["sources"][0]["material"] = \
        "material://source-demo-book/reader.pdf"
    write_yaml(registry_path, registry)
    digests = {}
    for name, data in (("deck.pdf", b"deck bytes"),
                       ("slides.pdf", b"slides bytes"),
                       ("reader.pdf", b"reader bytes"),
                       ("multi.pdf", b"multi bytes"),
                       ("other.pdf", b"other bytes")):
        digests[name] = _seed_material(
            root, f"source-demo-book/{name}", data)
    return digests


def _scope_binding(material: str, digest: str, body: str, start: int,
                   end: int, **overrides):
    return _binding(material, digest, body,
                    inspected_range={"start": start, "end": end},
                    **overrides)


def test_unit_scope_splits_direct_from_related_by_route(mini_repo):
    digests = _seed_routed_unit(mini_repo)
    _register_source(mini_repo, "source-demo-paper", "Demo Paper")
    bodies = {
        "note-scope-a-vault-direct": "Density from the deck.\n",
        "note-scope-b-locator-direct": "Density from the slides.\n",
        "note-scope-c-inherit-direct": "Density from the reader.\n",
        "note-scope-d-multi-direct": "Density from the multi-range file.\n",
        "note-scope-e-vault-disjoint": "Density from disjoint deck pages.\n",
        "note-scope-f-other-file": "Density from an unrouted file.\n",
        "note-scope-g-unavailable-file": "Density from an unverified binding.\n",
        "note-scope-h-foreign": "Density from another source.\n",
    }
    specs = {
        "note-scope-a-vault-direct": ("deck.pdf", 2, 4, {}),
        "note-scope-b-locator-direct": ("slides.pdf", 2, 2, {}),
        "note-scope-c-inherit-direct": ("reader.pdf", 5, 9, {}),
        "note-scope-d-multi-direct": ("multi.pdf", 99, 100, {}),
        "note-scope-e-vault-disjoint": ("deck.pdf", 10, 12, {}),
        "note-scope-f-other-file": ("other.pdf", 1, 3, {}),
        "note-scope-g-unavailable-file": (
            "deck.pdf", 1, 2, {"resolution": "unavailable"}),
        "note-scope-h-foreign": ("paper.pdf", 1, 2,
                                 {"source_id": "source-demo-paper"}),
    }
    for note_id, body in bodies.items():
        name, start, end, overrides = specs[note_id]
        digest = digests.get(name, "ef" * 32)
        _plant_note(mini_repo, note_id, body,
                    _scope_binding(f"source-demo-book/{name}"
                                   if name != "paper.pdf" else name,
                                   digest, body, start, end, **overrides))
    scoped = _context(mini_repo, "density", "--unit", "unit-demo-l01")
    notes = [row for row in scoped["items"]
             if row["origin"] == "analysis-note"]
    assert [row["id"] for row in notes] == [
        "note-scope-a-vault-direct", "note-scope-b-locator-direct",
        "note-scope-c-inherit-direct", "note-scope-d-multi-direct"]
    assert {row["scope"] for row in notes} == {"direct"}
    assert scoped["pool"]["related_analysis_notes"] == 3
    widened = _context(mini_repo, "density", "--unit", "unit-demo-l01",
                       "--include-related", "--limit", "20")
    notes = [row for row in widened["items"]
             if row["origin"] == "analysis-note"]
    assert [row["id"] for row in notes] == [
        "note-scope-a-vault-direct", "note-scope-b-locator-direct",
        "note-scope-c-inherit-direct", "note-scope-d-multi-direct",
        "note-scope-e-vault-disjoint", "note-scope-f-other-file",
        "note-scope-g-unavailable-file"]
    assert [row["scope"] for row in notes] == ["direct"] * 4 + ["related"] * 3
    world = _context(mini_repo, "density", "--limit", "20")
    assert "note-scope-h-foreign" in [row["id"] for row in world["items"]]


def test_title_and_body_match_with_true_lines_and_no_provenance_hits(
        mini_repo):
    deck = _seed_material(mini_repo, "deck.pdf", b"deck bytes")
    _plant_note(mini_repo, "note-title-density",
                 "Uniform variables explained.\n",
                 _binding("deck.pdf", deck, "Uniform variables explained.\n"),
                 title="Density overview")
    body = "Alpha line.\nBeta density line.\nGamma line.\n"
    line_path = _plant_note(mini_repo, "note-body-density", body,
                            _binding("deck.pdf", deck, body))
    _plant_note(mini_repo, "note-provenance-trap",
                 "Unrelated text about integrals.\n",
                 _binding("density.pdf", "ef" * 32,
                          "Unrelated text about integrals.\n"))
    result = _context(mini_repo, "density", "--limit", "20")
    by_id = {row["id"]: row for row in result["items"]}
    assert set(by_id) == {"note-title-density", "note-body-density"}
    assert by_id["note-title-density"]["match"]["snippets"] == [
        {"label": "title", "text": "Density overview"}]
    expected = next(i + 1 for i, line in enumerate(
        line_path.read_text(encoding="utf-8").splitlines())
        if "Beta density line." in line)
    assert by_id["note-body-density"]["match"]["snippets"] == [
        {"line": expected, "text": "Beta density line."}]
    assert _context(mini_repo, "density integrals",
                     "--limit", "20")["total"] == 0


def test_include_related_is_refused_without_unit(mini_repo):
    proc = run_los(mini_repo, "material-context", "density",
                   "--include-related")
    assert proc.returncode == 2
    assert "needs --unit" in proc.stderr


def _seed_routed_dossier(root: Path):
    unit_dir = root / "curriculum/modules/module-demo/units/unit-demo-l01"
    write_yaml(unit_dir / "material-synthesis.yaml", {
        "schema_version": 1, "id": "material-synthesis-demo-l01",
        "type": "unit-material-synthesis", "unit_id": "unit-demo-l01",
        "status": "approved",
        "route_assessments": [
            {"route_id": "route-demo-vault", "source_id": "source-demo-book",
             "locator": "deck.pdf, pp. 1-3", "review_status": "deep-reviewed",
             "concept_ids": ["concept-expected-value"],
             "contribution": "Derives density intuition from first principles.",
             "best_for": "A worked example of uniform density integration."},
            {"route_id": "route-demo-ghost", "source_id": "source-demo-book",
             "locator": "ghost.pdf, pp. 1-3", "review_status": "deep-reviewed",
             "concept_ids": ["concept-expected-value"],
             "contribution": "Density from an assessment without a route.",
             "best_for": "Proves the material filter follows routes."},
        ],
    })


def test_material_filter_and_material_only_requests(mini_repo):
    digests = _seed_routed_unit(mini_repo)
    _seed_routed_dossier(mini_repo)
    deck_body = "Density from the deck.\n"
    _plant_note(mini_repo, "note-filter-deck", deck_body,
                _scope_binding("source-demo-book/deck.pdf",
                               digests["deck.pdf"], deck_body, 1, 2))
    slides_body = "Density from the slides.\n"
    _plant_note(mini_repo, "note-filter-slides", slides_body,
                _scope_binding("source-demo-book/slides.pdf",
                               digests["slides.pdf"], slides_body, 1, 2))
    only = _context(mini_repo, "--material", "source-demo-book/deck.pdf")
    assert only["searched"]["material"] == "source-demo-book/deck.pdf"
    assert only["searched"]["query_terms"] == []
    assert {(row.get("id"), row.get("route_id")) for row in only["items"]} == {
        ("note-filter-deck", None), (None, "route-demo-vault")}
    assert only["items"][0]["match"]["terms"] == []
    queried = _context(mini_repo, "density", "--material",
                       "source-demo-book/slides.pdf")
    assert [row.get("id", row.get("route_id"))
            for row in queried["items"]] == ["note-filter-slides"]
    assert queried["items"][0]["match"]["material"] == \
        "source-demo-book/slides.pdf"
    assert _context(mini_repo, "quasistrophoid", "--material",
                     "source-demo-book/deck.pdf")["total"] == 0
    for bad in ("../escape.pdf", "/abs.pdf", ""):
        proc = run_los(mini_repo, "material-context", "--material", bad)
        assert proc.returncode == 2, bad
        assert "materials-tree-relative" in proc.stderr, bad


def _second_unit_with_same_file_route(root: Path):
    from repo_builders import _sliced_route

    module_dir = root / "curriculum/modules/module-demo"
    module = yaml.safe_load((module_dir / "module.yaml").read_text(
        encoding="utf-8"))
    module["unit_order"].append("unit-demo-l02")
    write_yaml(module_dir / "module.yaml", module)
    unit = yaml.safe_load(
        (module_dir / "units/unit-demo-l01/unit.yaml").read_text(
            encoding="utf-8"))
    unit.update(id="unit-demo-l02", title="Second lecture", order=2)
    unit.pop("current_study_map", None)
    write_yaml(module_dir / "units/unit-demo-l02/unit.yaml", unit)
    source_map = yaml.safe_load(
        (module_dir / "source-map.yaml").read_text(encoding="utf-8"))
    route = _sliced_route("route-demo-l02-deck", "deck.pdf, pp. 1-3")
    route["unit_id"] = "unit-demo-l02"
    source_map["sources"][0]["unit_routes"].append(route)
    write_yaml(module_dir / "source-map.yaml", source_map)


def test_continuation_refuses_changed_filters(mini_repo):
    digests = _seed_routed_unit(mini_repo)
    _second_unit_with_same_file_route(mini_repo)
    anchor = {"topic": "Density", "purpose": "intuition", "locator": "p. 1"}
    for note_id, body in (("note-page-a", "Density alpha.\n"),
                          ("note-page-b", "Density beta.\n")):
        _plant_note(mini_repo, note_id, body,
                    _scope_binding("source-demo-book/deck.pdf",
                                   digests["deck.pdf"], body, 1, 2,
                                   anchors=[anchor]))
    first = _context(mini_repo, "density", "--unit", "unit-demo-l01",
                     "--limit", "1")
    assert first["total"] == 2 and first["next_offset"] == 1
    guards = ["--offset", "1", "--expected-snapshot", first["snapshot_id"],
              "--expected-observations", first["observations_sha256"]]
    same = _context(mini_repo, "density", "--unit", "unit-demo-l01",
                     "--limit", "1", *guards)
    assert [row["id"] for row in same["items"]] == ["note-page-b"]
    # Every flip keeps the same observed bytes: only the filter binding
    # moves, so each refusal proves the filters are bound.
    for argv in (["density alpha", "--unit", "unit-demo-l01"],
                ["density", "--unit", "unit-demo-l01",
                 "--purpose", "intuition"],
                ["density", "--unit", "unit-demo-l01",
                 "--material", "source-demo-book/deck.pdf"],
                ["density", "--unit", "unit-demo-l01", "--include-related"],
                ["density", "--unit", "unit-demo-l02"]):
        proc = run_los(mini_repo, "material-context", *argv,
                       "--limit", "1", *guards)
        assert proc.returncode == 2, argv
        assert "changed between pages" in proc.stderr, argv


def test_continuation_allows_normalized_equivalent_filters(mini_repo):
    digests = _seed_routed_unit(mini_repo)
    for note_id, body in (("note-norm-a", "Density worked example.\n"),
                          ("note-norm-b", "Worked density drill.\n")):
        _plant_note(mini_repo, note_id, body,
                    _scope_binding("source-demo-book/deck.pdf",
                                   digests["deck.pdf"], body, 1, 2),
                    concepts=["concept-expected-value"])
    first = _context(mini_repo, "density worked", "--limit", "1")
    guards = ["--offset", "1", "--expected-snapshot", first["snapshot_id"],
              "--expected-observations", first["observations_sha256"]]
    reordered = _context(mini_repo, "worked density", "--limit", "1",
                         *guards)
    assert [row["id"] for row in reordered["items"]] == ["note-norm-b"]
    assert reordered["observations_sha256"] == first["observations_sha256"]
    aliased = _context(mini_repo, "density", "--concept", "Erwartungswert",
                       "--limit", "1")
    id_guards = ["--offset", "1", "--expected-snapshot",
                 aliased["snapshot_id"], "--expected-observations",
                 aliased["observations_sha256"]]
    by_id = _context(mini_repo, "density", "--concept",
                      "concept-expected-value", "--limit", "1", *id_guards)
    assert [row["id"] for row in by_id["items"]] == ["note-norm-b"]


def test_string_route_units_list_same_source_notes_as_related_only(
        mini_repo):
    add_curriculum(mini_repo)
    digest = _seed_material(mini_repo, "deck.pdf", b"deck bytes")
    body = "Density from a string-routed source.\n"
    _plant_note(mini_repo, "note-legacy-density", body,
                _binding("deck.pdf", digest, body))
    scoped = _context(mini_repo, "density", "--unit", "unit-demo-l01")
    assert scoped["items"] == []
    assert scoped["pool"]["related_analysis_notes"] == 1
    widened = _context(mini_repo, "density", "--unit", "unit-demo-l01",
                       "--include-related")
    assert [row["id"] for row in widened["items"]] == ["note-legacy-density"]
    assert widened["items"][0]["scope"] == "related"


def test_unit_note_scope_defensive_branches(tmp_path):
    from types import SimpleNamespace

    from learning_os.commands.reads import _unit_note_scope

    learningos = tmp_path / "LearningOS"
    materials = learningos / "materials"
    (materials / "source-demo-book").mkdir(parents=True)
    repo = SimpleNamespace(materials_root=materials,
                           learningos_root=learningos,
                           sources={"source-demo-book": {}})
    routes = [("source-demo-book", {"locator": "deck.pdf, pp. 1-3"})]
    good = {"source_id": "source-demo-book",
            "material": "source-demo-book/deck.pdf",
            "inspected_range": {"start": 2, "end": 2}}
    assert _unit_note_scope(repo, good, routes) == "direct"
    assert _unit_note_scope(repo, {}, routes) is None
    assert _unit_note_scope(repo, None, routes) is None
    for broken in ({"start": "1", "end": 3}, {"start": 1}, {}, None):
        binding = dict(good, inspected_range=broken)
        assert _unit_note_scope(repo, binding, routes) == "related"


def test_two_file_route_labels_both_files_direct(mini_repo):
    from repo_builders import _sliced_route, _sliced_unit

    _sliced_unit(mini_repo, [
        _sliced_route("route-demo-dual",
                      "dual-a.pdf, pp. 1-2; dual-b.pdf, pp. 5-6"),
    ])
    digests = {}
    for name, data in (("dual-a.pdf", b"a bytes"),
                       ("dual-b.pdf", b"b bytes"),
                       ("other.pdf", b"other bytes")):
        digests[name] = _seed_material(
            mini_repo, f"source-demo-book/{name}", data)
    bodies = {
        "note-dual-a": "Density from the first file.\n",
        "note-dual-b": "Density from the second file.\n",
        "note-dual-other": "Density from an unrouted file.\n",
    }
    for note_id, body in bodies.items():
        name = {"note-dual-a": "dual-a.pdf",
                "note-dual-b": "dual-b.pdf",
                "note-dual-other": "other.pdf"}[note_id]
        _plant_note(mini_repo, note_id, body,
                    _scope_binding(f"source-demo-book/{name}",
                                   digests[name], body, 1, 2))
    scoped = _context(mini_repo, "density", "--unit", "unit-demo-l01")
    notes = [row for row in scoped["items"]
             if row["origin"] == "analysis-note"]
    assert [row["id"] for row in notes] == ["note-dual-a", "note-dual-b"]
    assert {row["scope"] for row in notes} == {"direct"}
    assert scoped["pool"]["related_analysis_notes"] == 1
    widened = _context(mini_repo, "density", "--unit", "unit-demo-l01",
                       "--include-related", "--limit", "20")
    by_id = {row["id"]: row for row in widened["items"]
             if row["origin"] == "analysis-note"}
    assert by_id["note-dual-other"]["scope"] == "related"

    unit_dir = mini_repo / "curriculum/modules/module-demo/units/unit-demo-l01"
    write_yaml(unit_dir / "material-synthesis.yaml", {
        "schema_version": 1, "id": "material-synthesis-demo-l01",
        "type": "unit-material-synthesis", "unit_id": "unit-demo-l01",
        "status": "approved",
        "route_assessments": [{
            "route_id": "route-demo-dual",
            "source_id": "source-demo-book",
            "locator": "dual-a.pdf, pp. 1-2; dual-b.pdf, pp. 5-6",
            "review_status": "deep-reviewed",
            "concept_ids": ["concept-expected-value"],
            "contribution": "Density from the deliberate two-file route.",
            "best_for": "Proves the material filter follows both files.",
        }],
    })
    for name in ("dual-a.pdf", "dual-b.pdf"):
        filtered = _context(mini_repo, "--material",
                            f"source-demo-book/{name}")
        note_id = "note-dual-a" if name == "dual-a.pdf" else "note-dual-b"
        assert {(row.get("id"), row.get("route_id"))
               for row in filtered["items"]} == {
            (note_id, None), (None, "route-demo-dual")}
    other = _context(mini_repo, "--material", "source-demo-book/other.pdf")
    assert all(row.get("route_id") != "route-demo-dual"
               for row in other["items"])


def _seed_anchored_note(root: Path, count: int, matches=frozenset({0})):
    digest = _seed_material(root, "deck.pdf", b"live bytes")
    anchors = [{
        "topic": f"Topic {number}",
        "purpose": ("integration" if number in matches
                    else "separate-topic reference"),
        "locator": f"deck.pdf, p. {number + 1}",
        "note": f"Anchor note {number}.",
    } for number in range(count)]
    _plant_note(root, "note-context-anchored", ANALYSIS_BODY,
                _binding("deck.pdf", digest, ANALYSIS_BODY, anchors=anchors))
    return anchors


def test_anchor_preview_bounds_the_default_response(mini_repo):
    _seed_anchored_note(mini_repo, 100)
    payload = _context(mini_repo, "density", "--limit", "1")
    item = payload["items"][0]
    assert item["anchor_total"] == 100
    assert item["anchor_returned"] == 8
    assert item["anchors_truncated"] is True
    assert [anchor["topic"] for anchor in item["anchors"]] == [
        f"Topic {number}" for number in range(8)]
    assert all(anchor["clipped_fields"] == [] for anchor in item["anchors"])
    assert "expand" in payload and "anchors" in payload["expand"]


def test_anchor_preview_ignores_index_growth(mini_repo):
    _seed_anchored_note(mini_repo, 100)
    small = run_los(mini_repo, "material-context", "density", "--limit", "1")
    assert small.returncode == 0, small.stderr
    path = mini_repo / "knowledge/notes/mathematics/note-context-anchored.md"
    text = path.read_text(encoding="utf-8")
    _head, sep, body = text.partition("\n---\n\n")
    meta = yaml.safe_load(_head.removeprefix("---\n"))
    grown = meta["material_analysis"]["anchors"] + [{
        "topic": f"Topic {number}", "purpose": "separate-topic reference",
        "locator": f"deck.pdf, p. {number + 1}",
        "note": f"Anchor note {number}.",
    } for number in range(100, 200)]
    meta["material_analysis"]["anchors"] = grown
    path.write_bytes(("---\n" + yaml.safe_dump(meta, sort_keys=False).rstrip()
                      + "\n---\n\n" + body).encode("utf-8"))
    big = run_los(mini_repo, "material-context", "density", "--limit", "1")
    assert big.returncode == 0, big.stderr
    grown_item = json.loads(big.stdout)["items"][0]
    assert grown_item["anchor_total"] == 200
    assert grown_item["anchor_returned"] == 8
    assert len(big.stdout) - len(small.stdout) < 300
    full = run_los(mini_repo, "material-context", "density", "--limit", "1",
                   "--include-anchors")
    assert full.returncode == 0, full.stderr
    assert len(json.loads(full.stdout)["items"][0]["anchors"]) == 200


def test_anchor_preview_puts_purpose_matches_first(mini_repo):
    _seed_anchored_note(mini_repo, 100, matches=frozenset({50, 51}))
    payload = _context(mini_repo, "density", "--purpose", "integration",
                       "--limit", "1")
    item = payload["items"][0]
    assert item["anchor_total"] == 100
    assert item["purpose_match_count"] == 2
    assert item["purpose_other_count"] == 98
    assert [anchor["topic"] for anchor in item["anchors"]] == [
        "Topic 50", "Topic 51"] + [f"Topic {number}" for number in range(6)]
    assert all(anchor["clipped_fields"] == [] for anchor in item["anchors"])


def test_anchor_preview_clips_long_text_with_markers(mini_repo):
    digest = _seed_material(mini_repo, "deck.pdf", b"live bytes")
    _plant_note(mini_repo, "note-context-anchored", ANALYSIS_BODY, _binding(
        "deck.pdf", digest, ANALYSIS_BODY, anchors=[
            {"topic": "Short topic", "purpose": "integration",
             "locator": "L" * 300, "note": "N" * 300},
            {"topic": "Second", "purpose": "separate-topic reference",
             "locator": "deck.pdf, p. 2", "note": "Short note."},
        ]))
    payload = _context(mini_repo, "density", "--limit", "1")
    item = payload["items"][0]
    assert item["anchor_total"] == 2
    assert item["anchors_truncated"] is False
    first, second = item["anchors"]
    assert len(first["locator"]) == 200 and len(first["note"]) == 200
    assert sorted(first["clipped_fields"]) == ["locator", "note"]
    assert first["topic"] == "Short topic"
    assert second["clipped_fields"] == []
    assert "expand" in payload


def test_include_anchors_returns_the_complete_verbatim_index(mini_repo):
    import shlex

    anchors = _seed_anchored_note(mini_repo, 100, matches=frozenset({50}))
    preview = _context(mini_repo, "density", "--purpose", "integration",
                       "--limit", "1")
    proc = run_los(mini_repo, *shlex.split(preview["expand"]["anchors"]))
    assert proc.returncode == 0, proc.stderr
    full = json.loads(proc.stdout)
    assert full["snapshot_id"] == preview["snapshot_id"]
    assert full["observations_sha256"] == preview["observations_sha256"]
    item = full["items"][0]
    assert item["anchors"] == anchors
    assert item["anchor_total"] == 100
    assert item["anchor_returned"] == 100
    assert item["anchors_truncated"] is False
    assert item["purpose_match_count"] == 1
    assert item["purpose_other_count"] == 99
    assert "clipped_fields" not in json.dumps(item["anchors"])
    assert "expand" not in full


def test_anchor_preview_empty_and_single_notes_stay_compact(mini_repo):
    digest = _seed_material(mini_repo, "deck.pdf", b"live bytes")
    _plant_note(mini_repo, "note-context-bare", ANALYSIS_BODY,
                _binding("deck.pdf", digest, ANALYSIS_BODY))
    payload = _context(mini_repo, "density", "--limit", "5")
    item = next(row for row in payload["items"]
                if row.get("id") == "note-context-bare")
    assert item["anchors"] == []
    assert item["anchor_total"] == 0
    assert item["anchor_returned"] == 0
    assert item["anchors_truncated"] is False
    assert "expand" not in payload
    _plant_note(mini_repo, "note-context-single", ANALYSIS_BODY, _binding(
        "deck.pdf", digest, ANALYSIS_BODY, anchors=[
            {"topic": "Only", "purpose": "integration",
             "locator": "deck.pdf, p. 1"},
        ]))
    payload = _context(mini_repo, "density", "--limit", "5")
    item = next(row for row in payload["items"]
                if row.get("id") == "note-context-single")
    assert len(item["anchors"]) == 1
    assert item["anchors"][0]["clipped_fields"] == []
    assert "note" not in item["anchors"][0]
    assert item["anchors_truncated"] is False
