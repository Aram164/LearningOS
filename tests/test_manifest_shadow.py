"""Stage-3 manifest proof: shadow equivalence plus exact rebuild closures.

Each scenario warms the derived cache on a synthetic repo, applies one
localized mutation, and pins the complete node partition — output-changed,
output-unchanged (pruned), and hit — alongside byte-exact shadow/legacy
equality. The closures below were derived from the graph definition and
verified against the dependency structure; a mismatch is a graph bug,
not a stale expectation.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml
from repo_builders import (
    add_manifest_fixtures,
    curriculum_mini,
    rewrite_yaml_doc,
    stage_manifest_producers,
    trace_summary,
)

from learning_os.contracts.manifest_contract import ManifestContractError
from learning_os.derived.store import derived_dir, read_state
from learning_os.genout.concepts import build_backlinks
from learning_os.genout.derived_generation import BACKLINKS_SEMANTIC_ID
from learning_os.genout.manifest import build_manifest
from learning_os.genout.manifest_derived import (
    AI_ACTIONS_ID,
    COLLECTIONS_ID,
    CONCEPTS_ID,
    COORDINATION_ID,
    COUNTS_ID,
    DEADLINES_ID,
    EDGES_ID,
    GARDEN_ID,
    INDEXES_ID,
    LEARNING_PATHS_ID,
    MODULES_ID,
    NOTES_ID,
    PROGRAMS_ID,
    PROGRESS_ID,
    PROJECT_ALIASES_ID,
    PROJECT_RELATIONSHIPS_ID,
    PROJECTS_ID,
    RECORDS_ID,
    RELATIONS_ID,
    REVIEW_ITEMS_ID,
    REVISIONS_ID,
    SEMANTIC_PAYLOAD_ID,
    SEMESTERS_ID,
    SOURCE_MAPS_ID,
    SOURCES_ID,
    STAGES_ID,
    STUDY_MAPS_ID,
    SYNTHSES_ID,
    THEMATIC_GROUPS_ID,
    TOPICS_ID,
    TYPED_COLLECTIONS_ID,
    UNIT_PROJECT_EDGES_ID,
    UNITS_ID,
    WORKSPACES_ID,
    build_manifest_shadow,
    compare_shadow_manifest,
)
from learning_os.loader import load_repo

REPO_ROOT = Path(__file__).resolve().parent.parent
GENERATE = REPO_ROOT / "tools" / "generate.py"
STAMP = "2026-09-20T00:00:00+02:00"

NOTE = "knowledge/notes/mathematics/note-demo.md"
UNIT = "curriculum/modules/module-demo/units/unit-demo-l01/unit.yaml"
SMAP = "curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml"
SOMAP = "curriculum/modules/module-demo/source-map.yaml"
MODULE = "curriculum/modules/module-demo/module.yaml"


def _warmed(tmp_path: Path, *, rich: bool = False) -> Path:
    mini = curriculum_mini(tmp_path)
    if rich:
        add_manifest_fixtures(mini)
    repo = load_repo(mini)
    stage_manifest_producers(mini, repo)
    assert compare_shadow_manifest(repo, STAMP).equivalent
    return mini


def _mutate_and_compare(mini: Path, mutate) -> tuple[dict, object]:
    mutate(mini)
    trace: list = []
    comparison = compare_shadow_manifest(load_repo(mini), STAMP, trace=trace)
    assert comparison.equivalent
    return trace_summary(trace), comparison


def _assert_partition(summary, *, changed: set[str], same: set[str]) -> None:
    actual_changed = {
        node for node, (_, reason) in summary.items()
        if reason == "node-key-changed-output-changed"
    }
    actual_same = {
        node for node, (_, reason) in summary.items()
        if reason == "node-key-changed-output-same"
    }
    assert actual_changed == changed
    assert actual_same == same
    for node, (status, reason) in summary.items():
        if node not in changed and node not in same:
            assert (status, reason) == ("hit", "node-key-equal"), node


def _replace_text(path: Path, old: str, new: str) -> None:
    path.write_text(path.read_text(encoding="utf-8").replace(old, new), encoding="utf-8")


# A. The mutation matrix: one localized change, one exact closure.
# ---------------------------------------------------------------------------


def test_matrix_no_change_hits_everything(tmp_path: Path):
    mini = _warmed(tmp_path)
    trace: list = []
    assert compare_shadow_manifest(load_repo(mini), STAMP, trace=trace).equivalent
    _assert_partition(trace_summary(trace), changed=set(), same=set())


def test_matrix_note_body_append_prunes_at_the_leaf(tmp_path: Path):
    mini = _warmed(tmp_path)

    def mutate(root: Path) -> None:
        note = root / NOTE
        note.write_text(note.read_text(encoding="utf-8") + "\nTrailing.\n",
                        encoding="utf-8")

    summary, _ = _mutate_and_compare(mini, mutate)
    _assert_partition(
        summary, changed=set(), same={BACKLINKS_SEMANTIC_ID, COUNTS_ID, NOTES_ID}
    )


def test_matrix_note_title(tmp_path: Path):
    mini = _warmed(tmp_path)
    summary, _ = _mutate_and_compare(
        mini, lambda root: _replace_text(root / NOTE, "title: Demo note", "title: Re"))
    _assert_partition(
        summary,
        changed={NOTES_ID, RECORDS_ID, SEMANTIC_PAYLOAD_ID},
        same={BACKLINKS_SEMANTIC_ID, COUNTS_ID, INDEXES_ID, TYPED_COLLECTIONS_ID},
    )


def test_matrix_concept_label(tmp_path: Path):
    mini = _warmed(tmp_path)
    summary, _ = _mutate_and_compare(
        mini,
        lambda root: rewrite_yaml_doc(
            root / "knowledge/concepts.yaml",
            lambda data: data["concepts"][0].update(label="Renamed")),
    )
    _assert_partition(
        summary,
        changed={CONCEPTS_ID, RECORDS_ID, SEMANTIC_PAYLOAD_ID},
        same={COUNTS_ID, INDEXES_ID, EDGES_ID, TYPED_COLLECTIONS_ID},
    )


def test_matrix_concept_relation(tmp_path: Path):
    mini = _warmed(tmp_path)

    def mutate(root: Path) -> None:
        rewrite_yaml_doc(
            root / "knowledge/concept-relations.yaml",
            lambda data: data["relations"].append(
                {"from": "concept-expected-value", "type": "builds-on",
                 "to": "concept-variance"}),
        )

    summary, _ = _mutate_and_compare(mini, mutate)
    _assert_partition(
        summary,
        changed={BACKLINKS_SEMANTIC_ID, COUNTS_ID, RELATIONS_ID, SEMANTIC_PAYLOAD_ID},
        same=set(),
    )


def test_matrix_source_title(tmp_path: Path):
    mini = _warmed(tmp_path)
    summary, _ = _mutate_and_compare(
        mini,
        lambda root: rewrite_yaml_doc(
            root / "sources/sources.yaml",
            lambda data: data["sources"][0].update(title="Retitled")),
    )
    _assert_partition(
        summary,
        changed={SOURCES_ID, RECORDS_ID, SEMANTIC_PAYLOAD_ID},
        same={COUNTS_ID, INDEXES_ID, LEARNING_PATHS_ID, SOURCE_MAPS_ID,
              STUDY_MAPS_ID, TYPED_COLLECTIONS_ID},
    )


def test_matrix_collection_title(tmp_path: Path):
    mini = _warmed(tmp_path, rich=True)
    summary, _ = _mutate_and_compare(
        mini,
        lambda root: rewrite_yaml_doc(
            root / "sources/collections/shelf.yaml",
            lambda data: data.update(title="Reshelved")),
    )
    _assert_partition(
        summary,
        changed={COLLECTIONS_ID, RECORDS_ID, SEMANTIC_PAYLOAD_ID},
        same={COUNTS_ID, INDEXES_ID, TYPED_COLLECTIONS_ID},
    )


def test_matrix_project_title(tmp_path: Path):
    mini = _warmed(tmp_path, rich=True)
    summary, _ = _mutate_and_compare(
        mini,
        lambda root: rewrite_yaml_doc(
            root / "projects/registry/project-demo.yaml",
            lambda data: data.update(title="Renamed")),
    )
    _assert_partition(
        summary,
        changed={PROJECTS_ID, RECORDS_ID, SEMANTIC_PAYLOAD_ID, TYPED_COLLECTIONS_ID},
        same={COUNTS_ID, INDEXES_ID, EDGES_ID, PROGRESS_ID, REVIEW_ITEMS_ID,
              SEMESTERS_ID, STAGES_ID, UNIT_PROJECT_EDGES_ID},
    )


def test_matrix_module_title(tmp_path: Path):
    mini = _warmed(tmp_path)
    summary, _ = _mutate_and_compare(
        mini,
        lambda root: rewrite_yaml_doc(
            root / MODULE, lambda data: data.update(title="Renamed")),
    )
    _assert_partition(
        summary,
        changed={DEADLINES_ID, MODULES_ID, RECORDS_ID, SEMANTIC_PAYLOAD_ID,
                 TYPED_COLLECTIONS_ID},
        same={BACKLINKS_SEMANTIC_ID, COUNTS_ID, INDEXES_ID, EDGES_ID, PROGRESS_ID,
              REVIEW_ITEMS_ID, SEMESTERS_ID, STAGES_ID, UNITS_ID},
    )


def test_matrix_unit_title(tmp_path: Path):
    mini = _warmed(tmp_path)
    summary, _ = _mutate_and_compare(
        mini,
        lambda root: rewrite_yaml_doc(
            root / UNIT, lambda data: data.update(title="Renamed")),
    )
    _assert_partition(
        summary,
        changed={RECORDS_ID, SEMANTIC_PAYLOAD_ID, TYPED_COLLECTIONS_ID, UNITS_ID},
        same={BACKLINKS_SEMANTIC_ID, COUNTS_ID, INDEXES_ID, EDGES_ID, MODULES_ID,
              PROGRESS_ID, REVIEW_ITEMS_ID, SEMESTERS_ID, STAGES_ID, SYNTHSES_ID},
    )


def test_matrix_working_note_content(tmp_path: Path):
    mini = curriculum_mini(tmp_path)
    note = mini / "work/active/workspace-demo/NOTES-demo.md"
    note.write_text("v1\n", encoding="utf-8")
    rewrite_yaml_doc(mini / UNIT, lambda data: data.update(
        working_note="work/active/workspace-demo/NOTES-demo.md"))
    repo = load_repo(mini)
    stage_manifest_producers(mini, repo)
    assert compare_shadow_manifest(repo, STAMP).equivalent
    note.write_text("v2 changed\n", encoding="utf-8")
    trace: list = []
    assert compare_shadow_manifest(load_repo(mini), STAMP, trace=trace).equivalent
    _assert_partition(
        trace_summary(trace),
        changed={RECORDS_ID, SEMANTIC_PAYLOAD_ID, TYPED_COLLECTIONS_ID, UNITS_ID},
        same={COUNTS_ID, INDEXES_ID, LEARNING_PATHS_ID, EDGES_ID, MODULES_ID,
              PROGRESS_ID, REVIEW_ITEMS_ID, SEMESTERS_ID, STAGES_ID, STUDY_MAPS_ID},
    )


def test_matrix_study_map_stage_status(tmp_path: Path):
    mini = _warmed(tmp_path)
    summary, _ = _mutate_and_compare(
        mini,
        lambda root: rewrite_yaml_doc(
            root / SMAP, lambda data: data["stages"][0].update(status="complete")),
    )
    _assert_partition(
        summary,
        changed={COUNTS_ID, PROGRESS_ID, RECORDS_ID, SEMANTIC_PAYLOAD_ID,
                 STAGES_ID, STUDY_MAPS_ID, TYPED_COLLECTIONS_ID},
        same={BACKLINKS_SEMANTIC_ID, INDEXES_ID, EDGES_ID, REVIEW_ITEMS_ID,
              SEMESTERS_ID},
    )


def test_matrix_source_map_angle_prose(tmp_path: Path):
    mini = _warmed(tmp_path)
    summary, _ = _mutate_and_compare(
        mini,
        lambda root: rewrite_yaml_doc(
            root / SOMAP,
            lambda data: data["sources"][0].update(why="Changed rationale")),
    )
    _assert_partition(
        summary,
        changed={RECORDS_ID, SEMANTIC_PAYLOAD_ID, SOURCE_MAPS_ID, TYPED_COLLECTIONS_ID},
        same={BACKLINKS_SEMANTIC_ID, COUNTS_ID, INDEXES_ID, EDGES_ID, PROGRESS_ID,
              REVIEW_ITEMS_ID, SEMESTERS_ID, STAGES_ID, STUDY_MAPS_ID,
              SYNTHSES_ID, UNITS_ID},
    )


def test_matrix_workspace_objective(tmp_path: Path):
    mini = _warmed(tmp_path)

    def mutate(root: Path) -> None:
        context = root / "work/active/workspace-demo/CONTEXT.md"
        text = context.read_text(encoding="utf-8")
        assert "## Objective\n" in text
        context.write_text(text.replace("## Objective\n", "## Objective\nNew line.\n"),
                           encoding="utf-8")

    summary, _ = _mutate_and_compare(mini, mutate)
    _assert_partition(
        summary,
        changed={RECORDS_ID, SEMANTIC_PAYLOAD_ID, WORKSPACES_ID},
        same={BACKLINKS_SEMANTIC_ID, COUNTS_ID, INDEXES_ID, TYPED_COLLECTIONS_ID},
    )


def test_matrix_workspace_trailing_body_prunes(tmp_path: Path):
    mini = _warmed(tmp_path)

    def mutate(root: Path) -> None:
        context = root / "work/active/workspace-demo/CONTEXT.md"
        context.write_text(context.read_text(encoding="utf-8") + "\nMore.\n",
                           encoding="utf-8")

    summary, _ = _mutate_and_compare(mini, mutate)
    _assert_partition(
        summary,
        changed=set(),
        same={BACKLINKS_SEMANTIC_ID, COUNTS_ID, WORKSPACES_ID},
    )


def test_matrix_revision_ledger_bump(tmp_path: Path):
    mini = _warmed(tmp_path, rich=True)
    summary, _ = _mutate_and_compare(
        mini,
        lambda root: rewrite_yaml_doc(
            root / "operations/transactions/revisions.yaml",
            lambda data: data["revisions"].update({"unit-demo-l01": 4})),
    )
    _assert_partition(
        summary,
        changed={RECORDS_ID, REVISIONS_ID, SEMANTIC_PAYLOAD_ID,
                 TYPED_COLLECTIONS_ID, UNITS_ID},
        same={COLLECTIONS_ID, COUNTS_ID, INDEXES_ID, LEARNING_PATHS_ID, EDGES_ID,
              MODULES_ID, PROGRAMS_ID, PROGRESS_ID, PROJECTS_ID, REVIEW_ITEMS_ID,
              SEMESTERS_ID, SOURCE_MAPS_ID, SOURCES_ID, STAGES_ID, STUDY_MAPS_ID,
              SYNTHSES_ID, WORKSPACES_ID},
    )


def test_matrix_garden_add(tmp_path: Path):
    mini = _warmed(tmp_path, rich=True)

    def mutate(root: Path) -> None:
        (root / "knowledge/garden/seed2.md").write_text("More. #idea\n",
                                                       encoding="utf-8")

    summary, _ = _mutate_and_compare(mini, mutate)
    _assert_partition(
        summary,
        changed={AI_ACTIONS_ID, COUNTS_ID, GARDEN_ID, SEMANTIC_PAYLOAD_ID},
        same=set(),
    )


def test_matrix_ai_request_status(tmp_path: Path):
    mini = _warmed(tmp_path, rich=True)
    summary, _ = _mutate_and_compare(
        mini,
        lambda root: rewrite_yaml_doc(
            root / "operations/ai-actions/requests/ai-request-demo/request.yaml",
            lambda data: data.update(status="completed")),
    )
    _assert_partition(
        summary,
        changed={AI_ACTIONS_ID, SEMANTIC_PAYLOAD_ID},
        same={COUNTS_ID},
    )


def test_matrix_learning_path_title(tmp_path: Path):
    mini = _warmed(tmp_path, rich=True)
    summary, _ = _mutate_and_compare(
        mini,
        lambda root: rewrite_yaml_doc(
            root / "work/active/workspace-demo/paths/path-demo.yaml",
            lambda data: data.update(title="Repathed")),
    )
    _assert_partition(
        summary,
        changed={LEARNING_PATHS_ID, RECORDS_ID, SEMANTIC_PAYLOAD_ID},
        same={COUNTS_ID, INDEXES_ID, TYPED_COLLECTIONS_ID},
    )


def test_matrix_program_title(tmp_path: Path):
    mini = _warmed(tmp_path)
    summary, _ = _mutate_and_compare(
        mini,
        lambda root: rewrite_yaml_doc(
            root / "curriculum/programs/program-bachelors.yaml",
            lambda data: data.update(title="Reprogrammed")),
    )
    _assert_partition(
        summary,
        changed={PROGRAMS_ID, RECORDS_ID, SEMANTIC_PAYLOAD_ID, TYPED_COLLECTIONS_ID},
        same={COUNTS_ID, INDEXES_ID, EDGES_ID, PROGRESS_ID, REVIEW_ITEMS_ID,
              SEMESTERS_ID, STAGES_ID},
    )


def test_matrix_thematic_title(tmp_path: Path):
    mini = _warmed(tmp_path, rich=True)
    summary, _ = _mutate_and_compare(
        mini,
        lambda root: rewrite_yaml_doc(
            root / "curriculum/thematic-groups.yaml",
            lambda data: data["thematic_groups"][0].update(title="Renamed")),
    )
    _assert_partition(
        summary,
        changed={SEMANTIC_PAYLOAD_ID, THEMATIC_GROUPS_ID},
        same={COLLECTIONS_ID, COUNTS_ID, MODULES_ID, SOURCES_ID},
    )


def test_matrix_topic_title(tmp_path: Path):
    mini = _warmed(tmp_path, rich=True)
    summary, _ = _mutate_and_compare(
        mini,
        lambda root: rewrite_yaml_doc(
            root / "sources/topics.yaml",
            lambda data: data["topics"][0].update(title="Renamed")),
    )
    _assert_partition(
        summary,
        changed={SEMANTIC_PAYLOAD_ID, TOPICS_ID},
        same={COUNTS_ID},
    )


def test_matrix_resume_pointer(tmp_path: Path):
    mini = _warmed(tmp_path, rich=True)
    summary, _ = _mutate_and_compare(
        mini,
        lambda root: rewrite_yaml_doc(
            root / "curriculum/resume.yaml",
            lambda data: data.update(stage_id="stage-demo-2")),
    )
    _assert_partition(summary, changed={SEMANTIC_PAYLOAD_ID}, same=set())


def test_matrix_inbox_add(tmp_path: Path):
    mini = _warmed(tmp_path)

    def mutate(root: Path) -> None:
        (root / "work/inbox/new.md").write_text("# New\n", encoding="utf-8")

    summary, _ = _mutate_and_compare(mini, mutate)
    _assert_partition(
        summary,
        changed={COUNTS_ID, REVIEW_ITEMS_ID, SEMANTIC_PAYLOAD_ID},
        same=set(),
    )


def test_matrix_project_alias_add(tmp_path: Path):
    mini = _warmed(tmp_path, rich=True)
    summary, _ = _mutate_and_compare(
        mini,
        lambda root: rewrite_yaml_doc(
            root / "projects/aliases.yaml",
            lambda data: data["aliases"].update({"older": "project-demo"})),
    )
    _assert_partition(
        summary,
        changed={INDEXES_ID, PROJECT_ALIASES_ID, RECORDS_ID, SEMANTIC_PAYLOAD_ID},
        same={TYPED_COLLECTIONS_ID},
    )


def test_matrix_project_relation_add(tmp_path: Path):
    mini = _warmed(tmp_path, rich=True)

    def mutate(root: Path) -> None:
        rewrite_yaml_doc(
            root / "projects/relations/project-relations.yaml",
            lambda data: data["relations"].append(
                {"id": "relationship-demo-2", "from_project_id": "project-demo",
                 "to_id": "module-demo", "to_type": "module",
                 "relation_type": "uses", "reason": "Second.",
                 "contribution": "Second shelf."}),
        )

    summary, _ = _mutate_and_compare(mini, mutate)
    _assert_partition(
        summary,
        changed={INDEXES_ID, PROJECT_RELATIONSHIPS_ID, PROJECTS_ID, RECORDS_ID,
                 SEMANTIC_PAYLOAD_ID, TYPED_COLLECTIONS_ID},
        same={COUNTS_ID, EDGES_ID, PROGRESS_ID, REVIEW_ITEMS_ID, SEMESTERS_ID,
              STAGES_ID, UNIT_PROJECT_EDGES_ID},
    )


def test_matrix_coordination(tmp_path: Path):
    mini = _warmed(tmp_path)

    def mutate(root: Path) -> None:
        (root / "work/COORDINATION.md").write_text(
            "# Commitments\n\n- Ship it.\n", encoding="utf-8")

    summary, _ = _mutate_and_compare(mini, mutate)
    _assert_partition(
        summary,
        changed={COORDINATION_ID, RECORDS_ID, SEMANTIC_PAYLOAD_ID},
        same={INDEXES_ID, TYPED_COLLECTIONS_ID},
    )


def test_matrix_unrelated_transcription_is_invisible(tmp_path: Path):
    mini = _warmed(tmp_path)

    def mutate(root: Path) -> None:
        target = root / "knowledge/garden/transcriptions/t.md"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("excluded\n", encoding="utf-8")

    summary, _ = _mutate_and_compare(mini, mutate)
    _assert_partition(summary, changed=set(), same=set())


# B. Producer invalidation, corruption, contract handling.
# ---------------------------------------------------------------------------


def test_producer_change_rebuilds_only_its_node(tmp_path: Path):
    mini = _warmed(tmp_path)
    staged = mini / "tools/learning_os/genout/projection/lifecycle.py"
    staged.write_text(staged.read_text(encoding="utf-8") + "\n# probe\n",
                      encoding="utf-8")
    trace: list = []
    assert compare_shadow_manifest(load_repo(mini), STAMP, trace=trace).equivalent
    _assert_partition(trace_summary(trace), changed=set(), same={MODULES_ID})


def test_corrupt_blob_self_heals(tmp_path: Path):
    mini = _warmed(tmp_path)
    state = read_state(mini)
    blob_rel = state[NOTES_ID].blob
    blob = derived_dir(mini) / blob_rel
    assert blob.is_file()
    blob.write_bytes(b"forged-bytes")
    trace: list = []
    assert compare_shadow_manifest(load_repo(mini), STAMP, trace=trace).equivalent
    summary = trace_summary(trace)
    assert summary[NOTES_ID] == ("rebuilt", "cache-miss")
    for node, (status, reason) in summary.items():
        if node != NOTES_ID:
            assert (status, reason) == ("hit", "node-key-equal"), node
    healed: list = []
    assert compare_shadow_manifest(load_repo(mini), STAMP, trace=healed).equivalent
    assert all(status == "hit" for status, _ in trace_summary(healed).values())


def test_contract_comment_is_semantically_invisible(tmp_path: Path):
    mini = _warmed(tmp_path, rich=True)
    contract = mini / "system/contracts/manifest-contract.yaml"
    contract.write_text(contract.read_text(encoding="utf-8") + "\n# probe\n",
                        encoding="utf-8")
    trace: list = []
    assert compare_shadow_manifest(load_repo(mini), STAMP, trace=trace).equivalent
    _assert_partition(trace_summary(trace), changed=set(), same=set())


def test_schema_change_fails_identically_on_both_sides(tmp_path: Path):
    mini = _warmed(tmp_path, rich=True)
    contract_doc = yaml.safe_load(
        (mini / "system/contracts/manifest-contract.yaml").read_text(encoding="utf-8"))
    schema = mini / contract_doc["schema_path"]
    schema.write_text(schema.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    repo = load_repo(mini)
    with pytest.raises(ManifestContractError) as legacy_exc:
        build_manifest(repo, STAMP, build_backlinks(repo, STAMP))
    with pytest.raises(ManifestContractError) as shadow_exc:
        build_manifest_shadow(repo, STAMP)
    assert str(shadow_exc.value) == str(legacy_exc.value)


# C. The CLI proof harness.
# ---------------------------------------------------------------------------


def _run_generate(mini: Path, *args: str):
    return subprocess.run(
        [sys.executable, str(GENERATE), "--root", str(mini), *args],
        capture_output=True, text=True, timeout=300,
    )


def test_cli_shadow_manifest_reports_exact(tmp_path: Path):
    mini = _warmed(tmp_path)
    result = _run_generate(mini, "--shadow-manifest")
    assert result.returncode == 0, result.stderr
    assert "shadow manifest: exact" in result.stdout
    assert "manifest.semantic-payload: hit" in result.stdout


def test_cli_shadow_manifest_json_reports_nodes(tmp_path: Path):
    mini = _warmed(tmp_path)
    result = _run_generate(mini, "--shadow-manifest", "--json")
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["equivalent"] is True
    assert report["artifact"] == "manifest.json"
    assert report["legacy_sha256"] == report["shadow_sha256"]
    assert report["nodes"][SEMANTIC_PAYLOAD_ID] == {"status": "hit"}
    assert report["nodes"][NOTES_ID] == {"status": "hit"}


def test_cli_json_requires_a_shadow_mode(tmp_path: Path):
    mini = _warmed(tmp_path)
    result = _run_generate(mini, "--json")
    assert result.returncode != 0
    assert "--json requires" in result.stderr


def test_cli_shadow_modes_are_exclusive(tmp_path: Path):
    mini = _warmed(tmp_path)
    result = _run_generate(mini, "--shadow-derived", "--shadow-manifest")
    assert result.returncode != 0
    assert "choose one shadow mode" in result.stderr
