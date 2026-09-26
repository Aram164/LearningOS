"""Structural IDs resolve through inspect with their owners.

Curriculum and path stages, detours, project nodes, and milestones are
not manifest records, but agents meet their IDs in schemas, plans, and
errors. `inspect` resolves each to its row plus owners instead of
archaeology; stage edits still start at plan-edit-context for the
revision guards.
"""

from __future__ import annotations

import json
from types import SimpleNamespace

import yaml
from repo_builders import add_curriculum, add_manifest_fixtures, run_los, write_yaml

from learning_os.commands.reads import structural_payload


def _manifest(stages=(), study_maps=(), records=()):
    return {"stages": list(stages), "study_maps": list(study_maps),
            "records": list(records)}


def _stage(sid, unit="unit-a", sm="map-a", module="module-a", **extra):
    row = {"id": sid, "title": sid, "status": "active", "unit_id": unit,
           "study_map_id": sm, "module_id": module}
    row.update(extra)
    return row


def _path(pid, ws="workspace-a", stages=(), archived=False):
    return SimpleNamespace(id=pid, workspace_id=ws, archived=archived,
                           data={"stages": list(stages)})


def _repo(*paths):
    return SimpleNamespace(learning_paths={path.id: path for path in paths})


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


def test_path_stage_needs_the_repo_and_loses_to_no_one():
    manifest = _manifest()
    assert structural_payload(manifest, "stage-p") is None
    repo = _repo(_path("path-a", stages=[{"id": "stage-p", "title": "P"}]))
    payload = structural_payload(manifest, "stage-p", repo)
    assert payload["structural_kind"] == "path-stage"
    assert payload["path_id"] == "path-a"
    assert payload["workspace_id"] == "workspace-a"
    assert payload["archived"] is False


def test_curriculum_and_path_collision_lists_both():
    manifest = _manifest(stages=[_stage("stage-both")])
    repo = _repo(_path("path-a", stages=[{"id": "stage-both"}]))
    payload = structural_payload(manifest, "stage-both", repo)
    assert payload["structural_kind"] == "ambiguous"
    assert [candidate["structural_kind"] for candidate in payload["candidates"]] == [
        "curriculum-stage", "path-stage"]


def test_detour_answers_with_owners():
    manifest = _manifest(study_maps=[{
        "id": "map-a", "unit_id": "unit-a", "module_id": "module-a",
        "detours": [{"id": "detour-a", "reason": "R"}],
    }])
    payload = structural_payload(manifest, "detour-a")
    assert payload["structural_kind"] == "detour"
    assert payload["detour"] == {"id": "detour-a", "reason": "R"}
    assert payload["unit_id"] == "unit-a"


def test_project_node_answers_with_path_and_record():
    manifest = _manifest(records=[{
        "id": "project-a", "type": "project", "path": "projects/registry/a.yaml",
        "milestone_ids": [],
        "structure": {"kind": "linear", "nodes": [{
            "id": "workstream-a", "title": "W", "kind": "workstream",
            "status": "active", "children": [{
                "id": "step-a", "title": "S", "kind": "step",
                "status": "active",
            }],
        }]},
    }])
    payload = structural_payload(manifest, "step-a")
    assert payload["structural_kind"] == "project-node"
    assert payload["project_id"] == "project-a"
    assert payload["node_path"] == ["workstream-a", "step-a"]
    assert payload["record_path"] == "projects/registry/a.yaml"
    assert payload["node"]["title"] == "S"


def test_bare_milestone_answers_with_owning_projects():
    manifest = _manifest(records=[
        {"id": "project-a", "type": "project", "path": "projects/registry/a.yaml",
         "milestone_ids": ["milestone-ship"], "structure": {"kind": "linear", "nodes": []}},
        {"id": "project-b", "type": "project", "path": "projects/registry/b.yaml",
         "milestone_ids": ["milestone-ship"], "structure": {"kind": "linear", "nodes": []}},
    ])
    payload = structural_payload(manifest, "milestone-ship")
    assert payload["structural_kind"] == "ambiguous"
    assert [candidate["project_id"] for candidate in payload["candidates"]] == [
        "project-a", "project-b"]
    assert "no record of their own" in payload["candidates"][0]["note"]


def test_milestone_node_and_listing_merge_to_the_node():
    manifest = _manifest(records=[{
        "id": "project-a", "type": "project", "path": "projects/registry/a.yaml",
        "milestone_ids": ["milestone-both"],
        "structure": {"kind": "linear", "nodes": [{
            "id": "milestone-both", "title": "M", "kind": "milestone",
            "status": "active",
        }]},
    }])
    payload = structural_payload(manifest, "milestone-both")
    assert payload["structural_kind"] == "project-node"


def test_unknown_id_answers_none():
    manifest = _manifest(stages=[_stage("stage-a")])
    assert structural_payload(manifest, "stage-missing") is None
    assert structural_payload(manifest, "note-missing") is None


def _fixture_repo(mini_repo):
    add_curriculum(mini_repo)
    add_manifest_fixtures(mini_repo)
    project_file = mini_repo / "projects/registry/project-demo.yaml"
    project = yaml.safe_load(project_file.read_text(encoding="utf-8"))
    project["milestone_ids"] = ["milestone-demo-ship"]
    project["structure"] = {"kind": "linear", "nodes": [{
        "id": "workstream-demo", "title": "Demo stream", "kind": "workstream",
        "status": "active", "children": [{
            "id": "step-demo-ship", "title": "Ship it", "kind": "step",
            "status": "active",
        }],
    }]}
    write_yaml(project_file, project)
    return mini_repo


def test_cli_inspect_resolves_curriculum_and_path_stages(mini_repo):
    root = _fixture_repo(mini_repo)
    curriculum = run_los(root, "inspect", "stage-demo")
    assert curriculum.returncode == 0, curriculum.stderr
    payload = json.loads(curriculum.stdout)
    assert payload["structural_kind"] == "curriculum-stage"
    assert payload["unit_id"] == "unit-demo-l01"
    assert payload["edit_via"] == "plan-edit-context unit-demo-l01 --stage-id stage-demo"
    path = run_los(root, "inspect", "stage-demo-path")
    assert path.returncode == 0, path.stderr
    staged = json.loads(path.stdout)
    assert staged["structural_kind"] == "path-stage"
    assert staged["path_id"] == "path-demo"


def test_cli_inspect_resolves_project_nodes_and_milestones(mini_repo):
    root = _fixture_repo(mini_repo)
    node = run_los(root, "inspect", "step-demo-ship")
    assert node.returncode == 0, node.stderr
    payload = json.loads(node.stdout)
    assert payload["structural_kind"] == "project-node"
    assert payload["node_path"] == ["workstream-demo", "step-demo-ship"]
    milestone = run_los(root, "inspect", "milestone-demo-ship")
    assert milestone.returncode == 0, milestone.stderr
    owned = json.loads(milestone.stdout)
    assert owned["structural_kind"] == "project-milestone"
    assert owned["project_id"] == "project-demo"


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
    assert "no curriculum stage, path stage" in missing.stderr
    assert "record not found: stage-missing" in missing.stderr
    plain = run_los(root, "inspect", "note-missing")
    assert plain.returncode == 2
    assert plain.stderr.strip() == "los: record not found: note-missing"
