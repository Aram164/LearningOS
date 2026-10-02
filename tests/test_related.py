"""Ranked symmetric connection retrieval.

`related` walks one hop over declared edges plus every backlink table in
both directions, so membership one way always implies the reverse edge
(JF-15). Results rank deterministically — more distinct edges first,
then recorded stage use-evidence per source exactly as material-context
ranks it, then stable id — and each result names its edges in `via`.
"""

from __future__ import annotations

import hashlib
import json
from types import SimpleNamespace

import yaml
from repo_builders import run_los

from learning_os.commands.reads import related_records


def _record(rid, rtype="note", **fields):
    record = {"id": rid, "type": rtype, "title": rid, "path": f"{rid}.md"}
    record.update(fields)
    return record


def _manifest(records, backlinks=None, relations=None,
              project_relationships=None, project_aliases=None,
              module_concept_edges=None):
    return {
        "records": records,
        "backlinks": backlinks or {},
        "relations": relations or [],
        "project_relationships": project_relationships or [],
        "project_aliases": project_aliases or {},
        "module_concept_edges": module_concept_edges or [],
    }


def _stage_edge(concept_id, unit_id, stage_id, kind="stage-concept"):
    return {
        "module_id": "module-demo",
        "concept_id": concept_id,
        "evidence": [{
            "kind": kind,
            "unit_id": unit_id,
            "study_map_id": "study-map-demo",
            "stage_id": stage_id,
        }],
    }


def _repo_with_feedback(entries):
    study_map = SimpleNamespace(data={"stages": [{"source_feedback": entries}]})
    return SimpleNamespace(study_maps={"map-demo": study_map})


def test_cli_related_is_symmetric_between_note_and_workspace(mini_repo):
    note_side = run_los(mini_repo, "related", "note-demo")
    assert note_side.returncode == 0, note_side.stderr
    from_note = {row["id"]: row for row in json.loads(note_side.stdout)}
    assert "workspace-demo" in from_note
    assert "inverse:workspace_to_notes" in from_note["workspace-demo"]["via"]
    assert "concept-expected-value" in from_note
    assert "source-demo-book" in from_note

    ws_side = run_los(mini_repo, "related", "workspace-demo")
    assert ws_side.returncode == 0, ws_side.stderr
    from_ws = {row["id"]: row for row in json.loads(ws_side.stdout)}
    assert "note-demo" in from_ws


def test_cli_related_unknown_id_refuses(mini_repo):
    result = run_los(mini_repo, "related", "note-missing")
    assert result.returncode == 2
    assert "record not found" in result.stderr


def test_ranking_prefers_edges_then_evidence_then_id():
    center = _record("r", "unit", concepts=["a"], sources=["a", "s-pos", "s-neg", "s-none"],
                     notes=["a", "b"])
    manifest = _manifest([
        center, _record("a"), _record("b"), _record("s-pos", "source"),
        _record("s-neg", "source"), _record("s-none", "source"),
    ])
    repo = _repo_with_feedback([
        {"source_id": "s-pos", "feedback": "helpful"},
        {"source_id": "s-pos", "feedback": "skipped"},
        {"source_id": "s-neg", "feedback": "too-advanced"},
    ])
    out = related_records(manifest, "r", repo)
    assert [row["id"] for row in out] == ["a", "s-pos", "b", "s-none", "s-neg"]
    assert out[0]["via"] == ["concepts", "notes", "sources"]
    assert out[1]["via"] == ["sources"]


def test_ranking_without_repo_is_stable_by_edges_then_id():
    center = _record("r", "unit", concepts=["a"], notes=["a", "b"])
    manifest = _manifest([center, _record("a"), _record("b"), _record("c")])
    out = related_records(manifest, "r")
    assert [row["id"] for row in out] == ["a", "b"]


def test_backlink_tables_are_walked_both_ways():
    note = _record("note-a", concepts=["concept-x"])
    manifest = _manifest(
        [note, _record("note-b"), _record("concept-x", "concept"),
         _record("workspace-w", "workspace")],
        backlinks={
            "workspace_to_notes": {"workspace-w": ["note-a"]},
            "concept_to_notes": {"concept-x": ["note-a", "note-b"]},
            "note_incoming": {"note-a": ["note-b"]},
        },
    )
    from_note = {row["id"]: row for row in related_records(manifest, "note-a")}
    assert from_note["workspace-w"]["via"] == ["inverse:workspace_to_notes"]
    assert from_note["concept-x"]["via"] == ["concepts", "inverse:concept_to_notes"]
    assert from_note["note-b"]["via"] == ["backlink:note_incoming"]
    from_other = {row["id"]: row for row in related_records(manifest, "note-b")}
    assert from_other["note-a"]["via"] == ["inverse:note_incoming"]
    assert from_other["concept-x"]["via"] == ["inverse:concept_to_notes"]
    from_concept = {row["id"]: row for row in related_records(manifest, "concept-x")}
    assert from_concept["note-a"]["via"] == ["backlink:concept_to_notes"]
    assert from_concept["note-b"]["via"] == ["backlink:concept_to_notes"]


def test_relations_walk_both_ways_with_alias_resolution():
    manifest = _manifest(
        [_record("project-a", "project"), _record("project-b", "project"),
         _record("concept-a", "concept"), _record("concept-b", "concept")],
        relations=[{"from": "concept-a", "to": "concept-b", "type": "builds-on"}],
        project_relationships=[
            {"from_project_id": "project-a", "to_id": "project-b",
             "type": "depends-on"},
        ],
        project_aliases={"alias-a": "project-a"},
    )
    assert [row["id"] for row in related_records(manifest, "alias-a")] == ["project-b"]
    assert related_records(manifest, "alias-a") == related_records(manifest, "project-a")
    assert related_records(manifest, "project-b")[0]["via"] == ["project_relationship"]
    assert related_records(manifest, "concept-a")[0]["id"] == "concept-b"
    assert related_records(manifest, "concept-b")[0]["id"] == "concept-a"


def test_unknown_id_answers_empty():
    manifest = _manifest([_record("a")])
    assert related_records(manifest, "missing") == []
    assert related_records(manifest, "missing", _repo_with_feedback([])) == []


def test_stage_concept_edges_link_concept_and_unit_both_ways():
    """Stage tags answer both directions, reasoned by the stage (#97)."""
    manifest = _manifest(
        [_record("concept-x", "concept"), _record("unit-u", "unit")],
        module_concept_edges=[_stage_edge("concept-x", "unit-u", "stage-s")],
    )
    from_concept = {row["id"]: row
                    for row in related_records(manifest, "concept-x")}
    assert from_concept["unit-u"]["via"] == ["stage-concept:stage-s"]
    from_unit = {row["id"]: row
                 for row in related_records(manifest, "unit-u")}
    assert from_unit["concept-x"]["via"] == ["stage-concept:stage-s"]


def test_stage_concept_edges_ignore_knowledge_node_evidence():
    """Node links are not stage tags, so they earn no stage edge (#97)."""
    manifest = _manifest(
        [_record("concept-x", "concept"), _record("unit-u", "unit")],
        module_concept_edges=[
            _stage_edge("concept-x", "unit-u", "stage-s",
                        kind="knowledge-node")],
    )
    assert related_records(manifest, "concept-x") == []
    assert related_records(manifest, "unit-u") == []


def test_stage_concept_edges_leave_existing_rows_untouched():
    """New edges add rows; existing content, order and via hold (#97)."""
    records = [_record("concept-x", "concept"),
               _record("note-a", concepts=["concept-x"]),
               _record("unit-u", "unit")]
    backlinks = {"concept_to_notes": {"concept-x": ["note-a"]}}
    edges = [_stage_edge("concept-x", "unit-u", "stage-s")]
    before = related_records(
        _manifest(records, backlinks=backlinks), "concept-x")
    after = related_records(
        _manifest(records, backlinks=backlinks,
                  module_concept_edges=edges), "concept-x")
    kept = [row for row in after if row["id"] != "unit-u"]
    assert kept == before
    assert [row["id"] for row in after
            if row["id"] != "unit-u"] == [row["id"] for row in before]
    added = [row for row in after if row["id"] == "unit-u"][0]
    assert added["via"] == ["stage-concept:stage-s"]


def test_analysis_edges_are_labelled_distinctly_in_via():
    """A note analysing a source says `analyses`, not just the backlink (#81)."""
    analysis = _record("note-analysis", material_analysis={
        "resolution": "resolved", "source_id": "source-x"})
    citing = _record("note-citing", sources=["source-x"])
    manifest = _manifest(
        [analysis, citing, _record("source-x", "source")],
        backlinks={"source_to_notes": {
            "source-x": ["note-analysis", "note-citing"]}},
    )
    from_source = {row["id"]: row for row in related_records(manifest, "source-x")}
    assert from_source["note-analysis"]["via"] == ["analyses", "backlink:source_to_notes"]
    assert from_source["note-citing"]["via"] == ["backlink:source_to_notes"]
    from_note = {row["id"]: row for row in related_records(manifest, "note-analysis")}
    assert from_note["source-x"]["via"] == ["analyses", "inverse:source_to_notes"]


def test_unresolved_analysis_binds_no_label():
    """Only a resolved binding names a registered source, so only it labels."""
    for binding in ({"resolution": "unresolved"},
                    {"resolution": "resolved", "source_id": "source-other"},
                    None):
        note = _record("note-draft", material_analysis=binding)
        manifest = _manifest(
            [note, _record("source-x", "source")],
            backlinks={"source_to_notes": {"source-x": ["note-draft"]}},
        )
        [row] = related_records(manifest, "source-x")
        assert row["via"] == ["backlink:source_to_notes"]


def _plant_analysis_note(root, note_id, source_id):
    """A saved source analysis bound to one registered source, citing none."""
    body = "The density chapter explains probability mass over intervals.\n"
    meta = {"id": note_id, "type": "note", "role": "reference",
            "title": "Planted analysis", "created": "2026-09-21",
            "state": "rough", "authorship": "operator-drafted",
            "semantic_review": "unreviewed",
            "material_analysis": {
                "resolution": "resolved", "material": "demo/chapter.pdf",
                "source_id": source_id,
                "recorded_source_digest": "0" * 64,
                "live_source_digest": "0" * 64,
                "inspected_range": {"start": 1, "end": 3},
                "frozen_input_sha256": hashlib.sha256(body.encode()).hexdigest(),
                "frozen_input_bytes": len(body.encode()),
            }}
    path = root / "knowledge/notes/mathematics" / f"{note_id}.md"
    path.write_bytes(
        ("---\n" + yaml.safe_dump(meta, sort_keys=False).rstrip()
         + "\n---\n\n" + body).encode("utf-8"))
    return path


def test_cli_related_surfaces_saved_analyses_of_a_source(mini_repo):
    """Saved analyses are reachable from their source, labelled (#81)."""
    _plant_analysis_note(mini_repo, "note-planted", "source-demo-book")

    source_side = run_los(mini_repo, "related", "source-demo-book")
    assert source_side.returncode == 0, source_side.stderr
    from_source = {row["id"]: row for row in json.loads(source_side.stdout)}
    assert "note-planted" in from_source
    assert from_source["note-planted"]["via"] == ["analyses", "backlink:source_to_notes"]
    # Existing citation edges keep their reasons: no new token leaks onto them.
    assert from_source["note-demo"]["via"] == ["backlink:source_to_notes"]

    note_side = run_los(mini_repo, "related", "note-planted")
    assert note_side.returncode == 0, note_side.stderr
    from_note = {row["id"]: row for row in json.loads(note_side.stdout)}
    assert "source-demo-book" in from_note
    assert from_note["source-demo-book"]["via"] == ["analyses", "inverse:source_to_notes"]

    # The edge is a backlink only: the note's `sources` stay empty (#81.3).
    inspected = run_los(mini_repo, "inspect", "note-planted")
    assert inspected.returncode == 0, inspected.stderr
    assert json.loads(inspected.stdout)["sources"] == []
