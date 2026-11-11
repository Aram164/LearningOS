"""Structural IDs resolve through inspect with their owners.

Curriculum stages and detours are not manifest records, but agents meet
their IDs in schemas, plans, and errors. `inspect` resolves each to its
row plus owners instead of archaeology; stage edits still start at
plan-edit-context for the revision guards.
"""

from __future__ import annotations

import json

from repo_builders import add_curriculum, add_manifest_fixtures, run_los

from learning_os.app.handlers.platform import structural_payload


def _manifest(stages=(), study_maps=(), records=()):
    return {"stages": list(stages), "study_maps": list(study_maps),
            "records": list(records)}


def _stage(sid, unit="unit-a", sm="map-a", module="module-a", **extra):
    row = {"id": sid, "title": sid, "status": "active", "unit_id": unit,
           "study_map_id": sm, "module_id": module}
    row.update(extra)
    return row


def test_curriculum_stage_answers_with_owners_and_edit_route():
    manifest = _manifest(stages=[_stage("stage-a")])
    payload = structural_payload(manifest, "stage-a")
    assert payload["structural_kind"] == "curriculum-stage"
    assert payload["unit_id"] == "unit-a"
    assert payload["study_map_id"] == "map-a"
    assert payload["module_id"] == "module-a"
    assert payload["stage"]["title"] == "stage-a"
    assert payload["edit_via"] == "plan-edit-context unit-a --stage-id stage-a"


def test_duplicate_stage_ids_answer_every_candidate_in_order():
    manifest = _manifest(stages=[_stage("stage-x", unit="unit-a"),
                                 _stage("stage-x", unit="unit-b")])
    payload = structural_payload(manifest, "stage-x")
    assert payload["structural_kind"] == "ambiguous"
    assert [candidate["unit_id"] for candidate in payload["candidates"]] == [
        "unit-a", "unit-b"]


def test_detour_answers_with_owners():
    manifest = _manifest(study_maps=[{
        "id": "map-a", "unit_id": "unit-a", "module_id": "module-a",
        "detours": [{"id": "detour-a", "reason": "R"}],
    }])
    payload = structural_payload(manifest, "detour-a")
    assert payload["structural_kind"] == "detour"
    assert payload["detour"] == {"id": "detour-a", "reason": "R"}
    assert payload["unit_id"] == "unit-a"


def test_unknown_id_answers_none():
    manifest = _manifest(stages=[_stage("stage-a")])
    assert structural_payload(manifest, "stage-missing") is None
    assert structural_payload(manifest, "note-missing") is None


def _fixture_repo(mini_repo):
    add_curriculum(mini_repo)
    add_manifest_fixtures(mini_repo)
    return mini_repo


def test_cli_inspect_resolves_curriculum_stages(mini_repo):
    root = _fixture_repo(mini_repo)
    curriculum = run_los(root, "inspect", "stage-demo")
    assert curriculum.returncode == 0, curriculum.stderr
    payload = json.loads(curriculum.stdout)
    assert payload["structural_kind"] == "curriculum-stage"
    assert payload["unit_id"] == "unit-demo-l01"
    assert payload["edit_via"] == "plan-edit-context unit-demo-l01 --stage-id stage-demo"


def test_cli_inspect_batch_mixes_records_and_structural_ids(mini_repo):
    root = _fixture_repo(mini_repo)
    batch = run_los(root, "inspect", "note-demo", "stage-demo")
    assert batch.returncode == 0, batch.stderr
    payload = json.loads(batch.stdout)
    assert payload["contract"] == "record-batch"
    assert payload["records"][0]["id"] == "note-demo"
    assert payload["records"][1]["structural_kind"] == "curriculum-stage"


def test_cli_inspect_unknown_structural_id_names_the_search(mini_repo):
    root = _fixture_repo(mini_repo)
    missing = run_los(root, "inspect", "stage-missing")
    assert missing.returncode == 2
    assert "no curriculum stage or detour carries this id" in missing.stderr
    assert "record not found: stage-missing" in missing.stderr
    plain = run_los(root, "inspect", "note-missing")
    assert plain.returncode == 2
    assert plain.stderr.strip() == "los: INVALID_REQUEST: record not found: note-missing"
