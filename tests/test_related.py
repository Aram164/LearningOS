"""Ranked symmetric connection retrieval.

`related` walks one hop over declared edges plus every backlink table in
both directions, so membership one way always implies the reverse edge
(JF-15). Results rank deterministically — more distinct edges first,
then recorded stage use-evidence per source exactly as material-context
ranks it, then stable id — and each result names its edges in `via`.
"""

from __future__ import annotations

import json
from types import SimpleNamespace

from repo_builders import run_los

from learning_os.commands.reads import related_records


def _record(rid, rtype="note", **fields):
    record = {"id": rid, "type": rtype, "title": rid, "path": f"{rid}.md"}
    record.update(fields)
    return record


def _manifest(records, backlinks=None, relations=None,
              project_relationships=None, project_aliases=None):
    return {
        "records": records,
        "backlinks": backlinks or {},
        "relations": relations or [],
        "project_relationships": project_relationships or [],
        "project_aliases": project_aliases or {},
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
