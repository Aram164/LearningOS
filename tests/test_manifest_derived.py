"""Stage-2 manifest proof: input digests pin every read, the graph is sound.

These tests pin the dependency graph definition itself: each digest moves
exactly when its domain moves, every spec resolves (deps, inputs,
producers), and cold/warm evaluation on a synthetic repo matches legacy
with the expected reuse shape. Mutation matrices and the CLI arrive in
stage 3; the shadow comparison harness here is the shared helper.
"""

from __future__ import annotations

import datetime
import shutil
from pathlib import Path

import yaml
from repo_builders import curriculum_mini as _curriculum_mini
from repo_builders import moved_only as _moved_only
from repo_builders import rewrite_yaml_doc as _rewrite_yaml
from repo_builders import stage_manifest_producers as _stage_manifest_producers
from repo_builders import trace_summary as _trace_summary
from repo_builders import write_yaml

from learning_os.derived.engine import evaluate_many
from learning_os.genout.concepts import build_backlinks
from learning_os.genout.derived_generation import (
    generation_input_digests,
    generation_registry,
)
from learning_os.genout.manifest import RECORD_SPLICE_ORDER, build_manifest
from learning_os.genout.manifest_derived import (
    _RECORD_GROUP_NODES,
    COUNTS_ID,
    EDGES_ID,
    INDEXES_ID,
    PROGRESS_ID,
    RECORDS_ID,
    RELATIONS_ID,
    SEMANTIC_PAYLOAD_ID,
    STAGES_ID,
    TYPED_COLLECTIONS_ID,
    manifest_input_digests,
    manifest_registry,
    materials_digest,
    notes_git_digest,
    today_digest,
    working_notes_digest,
)
from learning_os.loader import load_repo

REPO_ROOT = Path(__file__).resolve().parent.parent


def _evaluate(root: Path, repo, trace=None):
    registry = {**generation_registry(repo), **manifest_registry(repo)}
    inputs = {
        **generation_input_digests(root),
        **manifest_input_digests(root, repo),
    }
    return evaluate_many(
        root, [SEMANTIC_PAYLOAD_ID], registry=registry, inputs=inputs, trace=trace
    )


# A. Digest sensitivity: one domain moves, the rest stand still.
# ---------------------------------------------------------------------------


def test_manifest_digests_are_deterministic(tmp_path: Path):
    mini = _curriculum_mini(tmp_path)
    repo = load_repo(mini)
    assert manifest_input_digests(mini, repo) == manifest_input_digests(mini, repo)


def test_source_edit_moves_only_sources_digest(tmp_path: Path):
    mini = _curriculum_mini(tmp_path)
    before = manifest_input_digests(mini, load_repo(mini))
    _rewrite_yaml(
        mini / "sources" / "sources.yaml",
        lambda data: data["sources"][0].update(title="Retitled Book"),
    )
    after = manifest_input_digests(mini, load_repo(mini))
    assert _moved_only(before, after) == {"manifest.sources"}


def test_collection_edit_moves_only_collections_digest(tmp_path: Path):
    mini = _curriculum_mini(tmp_path)
    (mini / "sources" / "collections").mkdir(exist_ok=True)
    write_yaml(mini / "sources" / "collections" / "shelf.yaml", {
        "id": "shelf", "collection_kind": "catalogue", "title": "Shelf",
        "entries": [{"source": "source-demo-book"}],
    })
    before = manifest_input_digests(mini, load_repo(mini))
    _rewrite_yaml(
        mini / "sources" / "collections" / "shelf.yaml",
        lambda data: data.update(title="Reshelved"),
    )
    after = manifest_input_digests(mini, load_repo(mini))
    assert _moved_only(before, after) == {"manifest.collections"}


def test_program_edit_moves_only_programs_digest(tmp_path: Path):
    mini = _curriculum_mini(tmp_path)
    before = manifest_input_digests(mini, load_repo(mini))
    _rewrite_yaml(
        mini / "curriculum" / "programs" / "program-bachelors.yaml",
        lambda data: data.update(title="Renamed Program"),
    )
    after = manifest_input_digests(mini, load_repo(mini))
    assert _moved_only(before, after) == {"manifest.programs"}


def test_coordination_edit_moves_only_coordination_digest(tmp_path: Path):
    mini = _curriculum_mini(tmp_path)
    coord = mini / "work" / "COORDINATION.md"
    coord.write_text("# Commitments\n\n- Ship it.\n", encoding="utf-8")
    before = manifest_input_digests(mini, load_repo(mini))
    coord.write_text("# Commitments\n\n- Ship it twice.\n", encoding="utf-8")
    after = manifest_input_digests(mini, load_repo(mini))
    assert _moved_only(before, after) == {"manifest.coordination"}


def test_revision_ledger_edit_moves_only_revisions_digest(tmp_path: Path):
    mini = _curriculum_mini(tmp_path)
    ledger = mini / "operations" / "transactions" / "revisions.yaml"
    ledger.parent.mkdir(parents=True, exist_ok=True)
    ledger.write_text(yaml.safe_dump({
        "schema_version": 1, "type": "artifact-revision-ledger",
        "revisions": {"unit-demo-l01": 3},
    }), encoding="utf-8")
    before = manifest_input_digests(mini, load_repo(mini))
    ledger.write_text(yaml.safe_dump({
        "schema_version": 1, "type": "artifact-revision-ledger",
        "revisions": {"unit-demo-l01": 4},
    }), encoding="utf-8")
    after = manifest_input_digests(mini, load_repo(mini))
    assert _moved_only(before, after) == {"manifest.revisions"}


def test_resume_edit_moves_only_resume_digest(tmp_path: Path):
    mini = _curriculum_mini(tmp_path)
    resume = mini / "curriculum" / "resume.yaml"
    resume.write_text(yaml.safe_dump({"unit_id": "unit-demo-l01"}), encoding="utf-8")
    before = manifest_input_digests(mini, load_repo(mini))
    resume.write_text(yaml.safe_dump({"unit_id": "unit-demo-l02"}), encoding="utf-8")
    after = manifest_input_digests(mini, load_repo(mini))
    assert _moved_only(before, after) == {"manifest.resume"}


def test_study_map_content_and_presence_move_together_on_edit(tmp_path: Path):
    mini = _curriculum_mini(tmp_path)
    before = manifest_input_digests(mini, load_repo(mini))
    study_map = (
        mini / "curriculum" / "modules" / "module-demo"
        / "units" / "unit-demo-l01" / "study-map.yaml"
    )
    _rewrite_yaml(study_map, lambda data: data.update(status="complete"))
    after = manifest_input_digests(mini, load_repo(mini))
    assert after["manifest.study_map_files"] != before["manifest.study_map_files"]
    # Presence is unchanged: no map was added or removed.
    assert after["manifest.study_map_presence"] == before["manifest.study_map_presence"]
    assert _moved_only(before, after) == {"manifest.study_map_files"}


def test_new_study_map_moves_presence_digest(tmp_path: Path):
    mini = _curriculum_mini(tmp_path)
    unit_dir = mini / "curriculum" / "modules" / "module-demo" / "units" / "unit-demo-l02"
    unit_dir.mkdir(parents=True)
    write_yaml(unit_dir / "unit.yaml", {
        "id": "unit-demo-l02", "type": "unit", "module_id": "module-demo",
        "title": "Second unit", "status": "active",
    })
    before = manifest_input_digests(mini, load_repo(mini))
    write_yaml(unit_dir / "study-map.yaml", {
        "id": "study-map-demo-l02", "type": "study-map", "unit_id": "unit-demo-l02",
        "status": "active", "stages": [],
    })
    after = manifest_input_digests(mini, load_repo(mini))
    assert _moved_only(before, after) == {
        "manifest.study_map_files", "manifest.study_map_presence",
    }


def test_source_map_edit_moves_only_source_map_digest(tmp_path: Path):
    mini = _curriculum_mini(tmp_path)
    before = manifest_input_digests(mini, load_repo(mini))
    _rewrite_yaml(
        mini / "curriculum" / "modules" / "module-demo" / "source-map.yaml",
        lambda data: data["sources"][0].update(role="reference"),
    )
    after = manifest_input_digests(mini, load_repo(mini))
    assert _moved_only(before, after) == {"manifest.source_map_files"}


def test_synthesis_edit_moves_only_syntheses_digest(tmp_path: Path):
    mini = _curriculum_mini(tmp_path)
    unit_dir = mini / "curriculum" / "modules" / "module-demo" / "units" / "unit-demo-l01"
    write_yaml(unit_dir / "material-synthesis.yaml", {
        "id": "synthesis-demo", "unit_id": "unit-demo-l01",
        "route_assessments": [],
    })
    before = manifest_input_digests(mini, load_repo(mini))
    _rewrite_yaml(
        unit_dir / "material-synthesis.yaml",
        lambda data: data.update(route_assessments=[{"route_id": "route-x"}]),
    )
    after = manifest_input_digests(mini, load_repo(mini))
    assert _moved_only(before, after) == {"manifest.syntheses"}


def test_inbox_file_and_directory_both_move_inbox_digest(tmp_path: Path):
    mini = _curriculum_mini(tmp_path)
    inbox = mini / "work" / "inbox"
    (inbox / "capture.md").write_text("# Idea\n", encoding="utf-8")
    before = manifest_input_digests(mini, load_repo(mini))
    (inbox / "capture.md").write_text("# Better idea\n", encoding="utf-8")
    assert (
        manifest_input_digests(mini, load_repo(mini))["manifest.inbox"]
        != before["manifest.inbox"]
    )
    mid = manifest_input_digests(mini, load_repo(mini))
    # An empty subdirectory moves the count though no review row reads it.
    (inbox / "nested").mkdir()
    assert (
        manifest_input_digests(mini, load_repo(mini))["manifest.inbox"]
        != mid["manifest.inbox"]
    )
    assert _moved_only(before, manifest_input_digests(mini, load_repo(mini))) == {
        "manifest.inbox"
    }


def test_garden_sidecar_moves_garden_digest(tmp_path: Path):
    mini = _curriculum_mini(tmp_path)
    seed = mini / "knowledge" / "garden" / "seed.md"
    seed.parent.mkdir(parents=True, exist_ok=True)
    seed.write_text("A thought. #idea\n", encoding="utf-8")
    before = manifest_input_digests(mini, load_repo(mini))
    (seed.parent / "README.md").write_text("meta\n", encoding="utf-8")
    assert (
        manifest_input_digests(mini, load_repo(mini))["manifest.garden"]
        == before["manifest.garden"]
    )
    sidecars = mini / "operations" / "ai-actions" / "garden-state"
    sidecars.mkdir(parents=True, exist_ok=True)
    (sidecars / "garden-note-seed.yaml").write_text(
        yaml.safe_dump({"state": "sprout"}), encoding="utf-8"
    )
    after = manifest_input_digests(mini, load_repo(mini))
    assert _moved_only(before, after) == {"manifest.garden"}


def test_ai_request_moves_only_ai_digest(tmp_path: Path):
    mini = _curriculum_mini(tmp_path)
    bundle = mini / "operations" / "ai-actions" / "requests" / "req-1"
    bundle.mkdir(parents=True, exist_ok=True)
    (bundle / "request.yaml").write_text(yaml.safe_dump({
        "id": "req-1", "action_id": "summarize", "status": "open",
    }), encoding="utf-8")
    before = manifest_input_digests(mini, load_repo(mini))
    (bundle / "request.yaml").write_text(yaml.safe_dump({
        "id": "req-1", "action_id": "summarize", "status": "delivered",
    }), encoding="utf-8")
    after = manifest_input_digests(mini, load_repo(mini))
    assert _moved_only(before, after) == {"manifest.ai_files"}


def test_today_digest_is_today():
    assert today_digest() == datetime.date.today().isoformat()


def test_notes_git_digest_is_stable_without_history(tmp_path: Path):
    mini = _curriculum_mini(tmp_path)
    assert notes_git_digest(mini) == notes_git_digest(mini)


def test_working_note_content_moves_working_notes_digest(tmp_path: Path):
    mini = _curriculum_mini(tmp_path)
    note = mini / "work" / "active" / "workspace-demo" / "NOTES.md"
    note.parent.mkdir(parents=True, exist_ok=True)
    note.write_text("hello\n", encoding="utf-8")
    unit_file = (
        mini / "curriculum" / "modules" / "module-demo"
        / "units" / "unit-demo-l01" / "unit.yaml"
    )
    _rewrite_yaml(
        unit_file,
        lambda data: data.update(
            working_note="work/active/workspace-demo/NOTES.md"
        ),
    )
    before = manifest_input_digests(mini, load_repo(mini))
    note.write_text("hello again\n", encoding="utf-8")
    after = manifest_input_digests(mini, load_repo(mini))
    assert _moved_only(before, after) == {"manifest.working_notes"}
    assert working_notes_digest(mini, load_repo(mini)) == after["manifest.working_notes"]


def test_materials_digest_ignores_unreferenced_files(tmp_path: Path):
    mini = _curriculum_mini(tmp_path)
    materials = mini.parent / "materials"
    (materials / "stray.pdf").write_bytes(b"%PDF-stray")
    before = manifest_input_digests(mini, load_repo(mini))
    (materials / "stray.pdf").write_bytes(b"%PDF-stray-changed")
    (materials / "another.pdf").write_bytes(b"%PDF-new")
    after = manifest_input_digests(mini, load_repo(mini))
    assert after["manifest.materials"] == before["manifest.materials"]


def test_materials_digest_tracks_referenced_file_bytes(tmp_path: Path):
    mini = _curriculum_mini(tmp_path)
    materials = mini.parent / "materials"
    deck = materials / "demo-book.pdf"
    deck.write_bytes(b"%PDF-v1")
    _rewrite_yaml(
        mini / "sources" / "sources.yaml",
        lambda data: data["sources"][0].update(
            material="material://demo/demo-book.pdf"
        ),
    )
    # The authority must resolve under materials_root for the reference
    # to bind; point the farm at the file through the .flat layout.
    flat = materials / ".flat" / "demo"
    flat.mkdir(parents=True, exist_ok=True)
    (flat / "demo-book.pdf").write_bytes(b"%PDF-v1")
    before = manifest_input_digests(mini, load_repo(mini))
    (flat / "demo-book.pdf").write_bytes(b"%PDF-v2")
    after = manifest_input_digests(mini, load_repo(mini))
    assert _moved_only(before, after) == {"manifest.materials"}
    assert materials_digest(mini, load_repo(mini)) == after["manifest.materials"]


# B. Graph soundness: specs resolve, producers exist, order is covered.
# ---------------------------------------------------------------------------


def test_registry_specs_match_their_keys(tmp_path: Path):
    mini = _curriculum_mini(tmp_path)
    for node_id, (spec, _) in manifest_registry(load_repo(mini)).items():
        assert spec.id == node_id


def test_every_dependency_and_input_resolves(tmp_path: Path):
    mini = _curriculum_mini(tmp_path)
    repo = load_repo(mini)
    registry = {**generation_registry(repo), **manifest_registry(repo)}
    inputs = {
        **generation_input_digests(mini),
        **manifest_input_digests(mini, repo),
    }
    for node_id, (spec, _) in registry.items():
        for dep in spec.dependencies:
            assert dep in registry, f"{node_id} depends on unknown {dep}"
        for name in spec.direct_inputs:
            assert name in inputs, f"{node_id} wants unknown input {name}"


def test_every_producer_file_exists(tmp_path: Path):
    mini = _curriculum_mini(tmp_path)
    for _, (spec, _) in manifest_registry(load_repo(mini)).items():
        for rel in spec.producer_files:
            assert (REPO_ROOT / rel).is_file(), f"producer missing: {rel}"


def test_record_groups_cover_the_splice_order():
    assert set(_RECORD_GROUP_NODES) == set(RECORD_SPLICE_ORDER)
    assert len(_RECORD_GROUP_NODES) == len(RECORD_SPLICE_ORDER)


# C. Cold/warm evaluation matches legacy with the expected reuse shape.
# ---------------------------------------------------------------------------


def test_cold_evaluation_matches_legacy_semantic_payload(tmp_path: Path):
    mini = _curriculum_mini(tmp_path)
    repo = load_repo(mini)
    _stage_manifest_producers(mini, repo)
    legacy = build_manifest(repo, "T1", build_backlinks(repo, "T1"))
    trace: list = []
    results = _evaluate(mini, repo, trace)
    shadow = results[SEMANTIC_PAYLOAD_ID].value
    assert shadow == {k: v for k, v in legacy.items() if k != "_generated"}
    assert len(trace) == len({event.node for event in trace})
    assert {event.node for event in trace} >= set(_RECORD_GROUP_NODES.values())


def test_warm_evaluation_hits_every_node(tmp_path: Path):
    mini = _curriculum_mini(tmp_path)
    repo = load_repo(mini)
    _stage_manifest_producers(mini, repo)
    _evaluate(mini, repo)
    trace: list = []
    results = _evaluate(mini, load_repo(mini), trace)
    summary = _trace_summary(trace)
    assert summary
    assert all(status == "hit" for status, _ in summary.values())
    assert all(
        reason == "node-key-equal" for _, reason in summary.values()
    )
    legacy = build_manifest(load_repo(mini), "T1", build_backlinks(load_repo(mini), "T1"))
    assert results[SEMANTIC_PAYLOAD_ID].value == {
        k: v for k, v in legacy.items() if k != "_generated"
    }


def test_relation_edit_rebuilds_only_relations_and_payload(tmp_path: Path):
    """Relations bypass records: everything downstream of records still hits."""
    mini = _curriculum_mini(tmp_path)
    repo = load_repo(mini)
    _stage_manifest_producers(mini, repo)
    _evaluate(mini, repo)
    _rewrite_yaml(
        mini / "knowledge" / "concept-relations.yaml",
        lambda data: data["relations"].append(
            {"from": "concept-expected-value", "type": "builds-on",
             "to": "concept-variance"}
        ),
    )
    trace: list = []
    results = _evaluate(mini, load_repo(mini), trace)
    summary = _trace_summary(trace)
    assert summary[RELATIONS_ID][0] == "rebuilt"
    assert summary[SEMANTIC_PAYLOAD_ID][0] == "rebuilt"
    assert summary[RECORDS_ID][0] == "hit"
    assert summary[TYPED_COLLECTIONS_ID][0] == "hit"
    assert summary[INDEXES_ID][0] == "hit"
    assert summary[PROGRESS_ID][0] == "hit"
    # Counts reads the raw relation count, so it rebuilds too.
    assert summary[COUNTS_ID][0] == "rebuilt"
    legacy = build_manifest(load_repo(mini), "T1", build_backlinks(load_repo(mini), "T1"))
    assert results[SEMANTIC_PAYLOAD_ID].value == {
        k: v for k, v in legacy.items() if k != "_generated"
    }


def test_note_title_edit_prunes_typed_collections(tmp_path: Path):
    """Depth-2 pruning: notes -> records -> pruned collections -> hit progress."""
    mini = _curriculum_mini(tmp_path)
    repo = load_repo(mini)
    _stage_manifest_producers(mini, repo)
    _evaluate(mini, repo)
    note = mini / "knowledge" / "notes" / "mathematics" / "note-demo.md"
    note.write_text(
        note.read_text(encoding="utf-8").replace("title: Demo note", "title: Renamed note"),
        encoding="utf-8",
    )
    trace: list = []
    results = _evaluate(mini, load_repo(mini), trace)
    summary = _trace_summary(trace)
    assert summary[TYPED_COLLECTIONS_ID] == (
        "rebuilt", "node-key-changed-output-same",
    )
    assert summary[PROGRESS_ID][0] == "hit"
    assert summary[STAGES_ID][0] == "hit"
    assert summary[EDGES_ID][0] == "hit"
    assert summary[RECORDS_ID] == ("rebuilt", "node-key-changed-output-changed")
    legacy = build_manifest(load_repo(mini), "T1", build_backlinks(load_repo(mini), "T1"))
    assert results[SEMANTIC_PAYLOAD_ID].value == {
        k: v for k, v in legacy.items() if k != "_generated"
    }


def test_note_body_append_prunes_at_the_leaf(tmp_path: Path):
    """Trailing prose moves no summary: the payload itself hits."""
    mini = _curriculum_mini(tmp_path)
    repo = load_repo(mini)
    _stage_manifest_producers(mini, repo)
    _evaluate(mini, repo)
    note = mini / "knowledge" / "notes" / "mathematics" / "note-demo.md"
    note.write_text(
        note.read_text(encoding="utf-8") + "\nTrailing prose.\n", encoding="utf-8"
    )
    trace: list = []
    results = _evaluate(mini, load_repo(mini), trace)
    summary = _trace_summary(trace)
    assert summary[RECORDS_ID][0] == "hit"
    assert summary[SEMANTIC_PAYLOAD_ID][0] == "hit"
    legacy = build_manifest(load_repo(mini), "T1", build_backlinks(load_repo(mini), "T1"))
    assert results[SEMANTIC_PAYLOAD_ID].value == {
        k: v for k, v in legacy.items() if k != "_generated"
    }


def test_deleting_derived_state_restores_clean_execution(tmp_path: Path):
    mini = _curriculum_mini(tmp_path)
    repo = load_repo(mini)
    _stage_manifest_producers(mini, repo)
    _evaluate(mini, repo)
    shutil.rmtree(mini / "generated" / "derived-state")
    trace: list = []
    results = _evaluate(mini, load_repo(mini), trace)
    assert all(status == "rebuilt" for status, _ in _trace_summary(trace).values())
    legacy = build_manifest(load_repo(mini), "T1", build_backlinks(load_repo(mini), "T1"))
    assert results[SEMANTIC_PAYLOAD_ID].value == {
        k: v for k, v in legacy.items() if k != "_generated"
    }
