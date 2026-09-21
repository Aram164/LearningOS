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


def _seed_unit(root: Path):
    add_curriculum(root)
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
    digest = _seed_material(mini_repo, "deck.pdf", b"live bytes")
    _plant_note(mini_repo, "note-context-density-pp001-003", ANALYSIS_BODY,
                 _binding("deck.pdf", digest, ANALYSIS_BODY,
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

    scoped = _context(mini_repo, "density", "--unit", "unit-demo-l01")
    assert [row.get("id", row.get("route_id")) for row in scoped["items"]] == [
        "note-context-density-pp001-003", "route-demo-density"]

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
    note_path = _plant_note(root, note_id, "Weighted sums derive expectation.\n",
                            _binding("source-demo-book/lecture-01.pdf",
                                     "ab" * 32, "Weighted sums derive expectation.\n",
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
    assert "use-evidence" in result["ranked_by"]
