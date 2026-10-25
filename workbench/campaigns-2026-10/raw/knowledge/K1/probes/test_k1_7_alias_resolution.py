"""K1 invariant 7 (ARCHITECTURE §6 bilingual policy): a German alias declared
in knowledge/concepts.yaml reaches the same concept id through
material-context's concept filter, and through note search — probed through
the real CLI with a fixture whose note text never mentions the alias, so any
hit must come from the declared alias, never from shared prose."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import yaml
from repo_builders import run_los

ANALYSIS_BODY = """# Density intuition

The density chapter explains probability mass spreading over intervals.
A worked example integrates the uniform density step by step.
"""


def _seed_material(root: Path, name: str, data: bytes) -> str:
    target = root.parent / "materials" / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    return hashlib.sha256(data).hexdigest()


def _plant_note(root: Path, note_id: str, body: str, binding: dict,
                concepts: list[str] | None = None):
    meta = {"id": note_id, "type": "note", "role": "reference",
            "title": "Planted analysis", "created": "2026-09-21",
            "state": "rough", "authorship": "operator-drafted",
            "semantic_review": "unreviewed",
            "material_analysis": binding}
    if concepts is not None:
        meta["concepts"] = concepts
    front = "---\n" + yaml.safe_dump(meta, sort_keys=False).rstrip() + "\n---\n\n"
    (root / "knowledge/notes/mathematics" / f"{note_id}.md").write_text(
        front + body, encoding="utf-8")


def _binding(material: str, digest: str, body: str) -> dict:
    return {
        "resolution": "resolved",
        "material": material,
        "source_id": "source-demo-book",
        "recorded_source_digest": digest,
        "live_source_digest": digest,
        "inspected_range": {"start": 1, "end": 3},
        "frozen_input_sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
        "frozen_input_bytes": len(body.encode("utf-8")),
    }


def _context(root: Path, *args: str):
    proc = run_los(root, "material-context", *args)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    return json.loads(proc.stdout)


def test_german_alias_resolves_to_the_same_concept_id_as_the_id_itself(mini_repo):
    """material-context: --concept Erwartungswert and --concept
    concept-expected-value return the identical result set, and the response
    names the resolved canonical id."""
    from repo_builders import _sliced_route, _sliced_unit

    _sliced_unit(mini_repo, [_sliced_route("route-demo-density", "deck.pdf, pp. 1-3")])
    digest = _seed_material(mini_repo, "source-demo-book/deck.pdf", b"live bytes")
    # The body deliberately never mentions "Erwartungswert" (nor the id).
    _plant_note(mini_repo, "note-context-alias-pp001-003", ANALYSIS_BODY,
                _binding("source-demo-book/deck.pdf", digest, ANALYSIS_BODY),
                concepts=["concept-expected-value"])

    aliased = _context(mini_repo, "density", "--concept", "Erwartungswert")
    direct = _context(mini_repo, "density", "--concept", "concept-expected-value")
    aliased_ids = [row.get("id", row.get("route_id")) for row in aliased["items"]]
    direct_ids = [row.get("id", row.get("route_id")) for row in direct["items"]]
    assert aliased_ids == direct_ids
    assert "note-context-alias-pp001-003" in aliased_ids
    assert aliased["items"][0]["match"]["concept"] == "concept-expected-value"


def test_alias_case_insensitivity_and_ambiguity(mini_repo):
    from repo_builders import _sliced_route, _sliced_unit

    _sliced_unit(mini_repo, [_sliced_route("route-demo-density", "deck.pdf, pp. 1-3")])
    digest = _seed_material(mini_repo, "source-demo-book/deck.pdf", b"live bytes")
    _plant_note(mini_repo, "note-context-alias-pp001-003", ANALYSIS_BODY,
                _binding("source-demo-book/deck.pdf", digest, ANALYSIS_BODY),
                concepts=["concept-expected-value"])

    lowered = _context(mini_repo, "density", "--concept", "erwartungswert")
    assert [row.get("id", row.get("route_id")) for row in lowered["items"]] == [
        "note-context-alias-pp001-003"]
    assert lowered["items"][0]["match"]["concept"] == "concept-expected-value"

    unknown = run_los(mini_repo, "material-context", "density",
                      "--concept", "KeinBegriff")
    assert unknown.returncode == 2
    assert "matches no id or declared alias" in unknown.stderr


def test_note_search_reaches_the_concept_id_through_the_declared_alias(mini_repo):
    """Metadata search over concept records: the German alias must reach the
    concept row that carries it, so the id comes back."""
    proc = run_los(mini_repo, "search", "Erwartungswert", "--type", "concept")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    rows = json.loads(proc.stdout)
    concepts = [row for row in rows if row.get("type") == "concept"]
    assert [row["id"] for row in concepts] == ["concept-expected-value"]

    lowered = run_los(mini_repo, "search", "erwartungswert", "--type", "concept")
    assert [row["id"] for row in json.loads(lowered.stdout)
            if row.get("type") == "concept"] == ["concept-expected-value"]


def test_content_search_boundary_recorded(mini_repo):
    """Recorded observation, not a finding: content search matches note bytes
    and frontmatter VALUES only. A note whose frontmatter carries the concept
    id and whose body never names the alias is not hit by the alias string.
    The note.search contract declares no alias expansion, so this documents
    where the bilingual bridge ends (material-context and concept-record
    search resolve aliases; note-content search does not)."""
    from repo_builders import _sliced_route, _sliced_unit

    _sliced_unit(mini_repo, [_sliced_route("route-demo-density", "deck.pdf, pp. 1-3")])
    digest = _seed_material(mini_repo, "source-demo-book/deck.pdf", b"live bytes")
    _plant_note(mini_repo, "note-context-alias-pp001-003", ANALYSIS_BODY,
                _binding("source-demo-book/deck.pdf", digest, ANALYSIS_BODY),
                concepts=["concept-expected-value"])

    by_alias = json.loads(run_los(
        mini_repo, "search", "Erwartungswert", "--content").stdout)
    by_id = json.loads(run_los(
        mini_repo, "search", "concept-expected-value", "--content").stdout)
    # Two notes carry the id in frontmatter (the planted note and mini_repo's
    # own note-demo); the alias string matches neither — no expansion happens.
    assert by_alias["total"] == 0
    assert by_id["total"] == 2
    assert {row["id"] for row in by_id["items"]} == {
        "note-context-alias-pp001-003", "note-demo"}
