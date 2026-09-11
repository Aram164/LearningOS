"""Shared material storage must preserve learning behavior and write guards."""

from __future__ import annotations

import copy
import json

import pytest
import yaml
from gateway_helpers import (
    approved_v2_call,
    approved_v2_cli,
    approved_v2_envelope,
    file_sha256,
    run_v2_capability,
)
from repo_builders import rich_fixture, run_los, write_yaml

from learning_os.commands.material import compaction_plan, route_patch_plan
from learning_os.fingerprint import canonical_fingerprint
from learning_os.genout import build_manifest
from learning_os.loader import load_repo
from learning_os.material_refs import (
    MaterialReferenceError,
    compact_map,
    expand_map,
    preserve_map_refs,
)
from learning_os.warning_baseline import collect, write_baseline


def material_fixture(root):
    route_id, _ = _rich_fixture(root)
    source_path = root / "curriculum/modules/module-demo/source-map.yaml"
    source_map = yaml.safe_load(source_path.read_text())
    route = source_map["sources"][0]["unit_routes"][0]
    route["angle_detail"] = "Überprüfung: a fully preserved explanation. " * 30
    write_yaml(source_path, source_map)
    repo = load_repo(root)
    sm = next(iter(repo.study_maps.values()))
    sm.data["plan_template_version"] = 1
    for number, stage in enumerate(sm.data["stages"], 1):
        stage["number"] = number
        stage.setdefault("exam_critical", False)
        stage.setdefault("concepts", ["concept-expected-value"])
    row = {"kind": "read", "label": route["title"], "source_id": "source-demo-book",
           "locator": route["locator"], "angle": route["angle"],
           "angle_detail": route["angle_detail"], "scope_triage": "required-now"}
    sm.data["stages"][0]["resources"] = [
        row, {**row, "angle": "This stage needs a distinct treatment.", "scope_triage": "helpful-now"},
        {"kind": "read", "label": "An independent resource", "source_id": "source-demo-book",
         "locator": "Independent chapter", "scope_triage": "reference-only"},
    ]
    write_yaml(sm.path, sm.data)
    material = repo.materials_root / "source-demo-book/lecture-01.pdf"
    material.parent.mkdir(parents=True, exist_ok=True)
    material.write_text("synthetic lecture")
    signatures, errors = collect(root)
    assert not errors, errors
    write_baseline(root, signatures, "Pre-existing warnings in this synthetic fixture")
    return load_repo(root), route_id, sm.id


def compact_via_gateway(root):
    check = run_los(root, "module-materials-compact", "module-demo", "--check")
    assert check.returncode == 0, check.stderr
    plan = json.loads(check.stdout)
    response = approved_v2_call(
        root, capability="module.materials.compact",
        payload={"module_id": "module-demo", "plan_sha256": plan["plan_sha256"]},
        artifact_ids=plan["artifact_ids"], idempotency_key="compact-demo",
    )
    assert response.returncode == 0, response.stdout + response.stderr
    return json.loads(response.stdout)


def test_compaction_is_lossless_and_leaves_ambiguity_and_independent_resources_inline(mini_repo):
    repo, _, smid = material_fixture(mini_repo)
    sm = repo.study_maps[smid]
    original = copy.deepcopy(sm.data)
    source_map = repo.module_source_maps[sm.module_id]
    compact, used = compact_map(original, source_map, sm.module_id, sm.unit_id)
    assert used
    assert expand_map(compact, source_map, sm.module_id, sm.unit_id) == original
    assert original == sm.data
    resources = compact["stages"][0]["resources"]
    assert "angle_detail" not in resources[0]
    assert resources[1]["angle"] == original["stages"][0]["resources"][1]["angle"]
    assert "angle" not in resources[1]["material_ref"]["inherit"]
    assert resources[2] == original["stages"][0]["resources"][2]
    ambiguous = copy.deepcopy(source_map)
    ambiguous["sources"][0]["unit_routes"].append(copy.deepcopy(ambiguous["sources"][0]["unit_routes"][0]))
    assert compact_map(original, ambiguous, sm.module_id, sm.unit_id) == (original, set())


@pytest.mark.parametrize("mutation", [
    lambda ref: ref.update(route_id="route-missing"),
    lambda ref: ref.update(inherit=["scope_triage"]),
    lambda ref: ref.update(inherit=["angle", "angle"]),
    lambda ref: ref.update(extra="undeclared"),
])
def test_malformed_references_fail_closed(mini_repo, mutation):
    repo, _, smid = material_fixture(mini_repo)
    sm = repo.study_maps[smid]
    compact, _ = compact_map(sm.data, repo.module_source_maps[sm.module_id], sm.module_id, sm.unit_id)
    mutation(compact["stages"][0]["resources"][0]["material_ref"])
    write_yaml(sm.path, compact)
    assert load_repo(mini_repo).parse_failures
    response = run_los(mini_repo, "inspect", smid)
    assert response.returncode != 0


def test_reference_cannot_cross_unit_or_conflict_with_local_fields(mini_repo):
    repo, _, smid = material_fixture(mini_repo)
    sm = repo.study_maps[smid]
    source = repo.module_source_maps[sm.module_id]
    compact, _ = compact_map(sm.data, source, sm.module_id, sm.unit_id)
    with pytest.raises(MaterialReferenceError, match="missing or ambiguous"):
        expand_map(compact, source, sm.module_id, "unit-another")
    compact["stages"][0]["resources"][0]["label"] = "Overlapping field"
    with pytest.raises(MaterialReferenceError, match="also override"):
        expand_map(compact, source, sm.module_id, sm.unit_id)


def test_gateway_compacts_with_receipt_and_stage_progress_keeps_references(mini_repo):
    repo, _, smid = material_fixture(mini_repo)
    before = repo.study_maps[smid].data
    manifest = build_manifest(repo, "T1")
    result = compact_via_gateway(mini_repo)
    assert result["receipt_path"]
    assert result["snapshot_after"] == "sha256:" + canonical_fingerprint(mini_repo)
    current = load_repo(mini_repo)
    sm = current.study_maps[smid]
    assert sm.data == before
    assert "material_ref" in sm.authored_data["stages"][0]["resources"][0]
    assert current.module_source_maps[sm.module_id]["sources"][0]["unit_routes"][0].get("id")
    projected = build_manifest(current, "T1")
    assert projected["study_maps"][0]["stages"] == manifest["study_maps"][0]["stages"]
    stage = sm.data["stages"][0]["id"]
    progressed = approved_v2_cli(
        mini_repo, "stage-progress", sm.unit_id, stage, "active",
        artifact_ids=[sm.unit_id, sm.id], idempotency_key="progress-compact",
    )
    assert progressed.returncode == 0, progressed.stdout + progressed.stderr
    saved = load_repo(mini_repo).study_maps[smid]
    assert saved.data["stages"][0]["status"] == "active"
    assert saved.data["stages"][0]["resources"] == before["stages"][0]["resources"]
    assert "material_ref" in saved.authored_data["stages"][0]["resources"][0]


def test_route_patch_updates_inheritance_and_exact_selections_but_preserves_overrides(mini_repo):
    repo, rid, smid = material_fixture(mini_repo)
    compact_via_gateway(mini_repo)
    repo = load_repo(mini_repo)
    unit_id = repo.study_maps[smid].unit_id
    changes = {"angle": "A new common explanation", "locator": "lecture-02.pdf"}
    writes, artifacts, _ = route_patch_plan(repo, unit_id, rid, changes)
    assert artifacts == {"module-demo", unit_id, smid}
    # Fully inherited descriptions need no study-map write at all.
    assert repo.study_maps[smid].path not in writes
    (repo.materials_root / "source-demo-book/lecture-02.pdf").write_text("new synthetic lecture")
    response = approved_v2_call(
        mini_repo, capability="route.patch", payload={"unit_id": unit_id, "route_id": rid, "changes": changes},
        artifact_ids=sorted(artifacts), idempotency_key="patch-demo",
    )
    assert response.returncode == 0, response.stdout + response.stderr
    changed = load_repo(mini_repo)
    resources = changed.study_maps[smid].data["stages"][0]["resources"]
    assert resources[0]["angle"] == changes["angle"]
    assert resources[1]["angle"] == "This stage needs a distinct treatment."
    assert resources[0]["locator"] == resources[1]["locator"] == changes["locator"]
    assert resources[2]["locator"] == "Independent chapter"
    assert changed.units[unit_id].data["source_selections"][0]["locator"] == changes["locator"]
    route = changed.module_source_maps["module-demo"]["sources"][0]["unit_routes"][0]
    assert route["id"] == rid


def test_direct_application_stale_snapshot_and_wrong_plan_hash_refuse(mini_repo):
    repo, rid, smid = material_fixture(mini_repo)
    before = canonical_fingerprint(mini_repo)
    direct = run_los(mini_repo, "route-patch", repo.study_maps[smid].unit_id, rid,
                     "--changes", json.dumps({"angle": "Changed"}))
    assert direct.returncode != 0
    assert canonical_fingerprint(mini_repo) == before
    writes, artifacts, _ = compaction_plan(repo, "module-demo")
    assert writes
    envelope = approved_v2_envelope(
        mini_repo, capability="module.materials.compact",
        payload={"module_id": "module-demo", "plan_sha256": "sha256:" + "0" * 64},
        artifact_ids=sorted(artifacts), idempotency_key="bad-plan",
    )
    result = run_v2_capability(mini_repo, envelope)
    assert result.returncode != 0
    assert canonical_fingerprint(mini_repo) == before
    stale = run_los(mini_repo, "plan-edit-context", repo.study_maps[smid].unit_id,
                    "--expected-snapshot", "sha256:" + "0" * 64)
    assert stale.returncode != 0
    assert not stale.stdout


def test_compact_edit_context_reconstructs_plan_and_preserves_explicit_edits(mini_repo):
    repo, _, smid = material_fixture(mini_repo)
    sm = repo.study_maps[smid]
    response = run_los(mini_repo, "plan-edit-context", sm.unit_id)
    assert response.returncode == 0, response.stderr
    context = json.loads(response.stdout)
    assert expand_map(context["study_map"], repo.module_source_maps[sm.module_id], sm.module_id, sm.unit_id) == sm.data
    compact_via_gateway(mini_repo)
    sm = load_repo(mini_repo).study_maps[smid]
    edited = copy.deepcopy(sm.data)
    edited["stages"][0]["resources"][0]["angle_detail"] = "An explicit new stage-specific treatment."
    stored = preserve_map_refs(sm, edited)
    assert "angle_detail" not in stored["stages"][0]["resources"][0]["material_ref"]["inherit"]
    assert expand_map(stored, load_repo(mini_repo).module_source_maps[sm.module_id], sm.module_id, sm.unit_id) == edited


def test_compact_map_import_and_feedback_preserve_storage(mini_repo, tmp_path):
    _, _, smid = material_fixture(mini_repo)
    compact_via_gateway(mini_repo)
    sm = load_repo(mini_repo).study_maps[smid]
    incoming = copy.deepcopy(sm.authored_data)
    incoming["stages"][0]["objective"] += " Preserve the reviewed material choices."
    draft = tmp_path / "reviewed-map.yaml"
    write_yaml(draft, incoming)
    imported = approved_v2_cli(
        mini_repo, "unit-map-import", sm.unit_id, "--file", str(draft), "--file-sha256", file_sha256(draft), "--replace",
        artifact_ids=[sm.unit_id, smid], idempotency_key="import-compact",
    )
    assert imported.returncode == 0, imported.stdout + imported.stderr
    feedback = approved_v2_cli(
        mini_repo, "source-feedback", sm.unit_id, sm.data["stages"][0]["id"],
        "source-demo-book", "helpful", artifact_ids=[sm.unit_id, smid],
        idempotency_key="feedback-compact",
    )
    assert feedback.returncode == 0, feedback.stdout + feedback.stderr
    saved = load_repo(mini_repo).study_maps[smid]
    assert saved.data["stages"][0]["source_feedback"][0]["feedback"] == "helpful"
    assert "material_ref" in saved.authored_data["stages"][0]["resources"][0]
    assert saved.data["stages"][0]["resources"] == sm.data["stages"][0]["resources"]


def test_reordered_resources_cannot_inherit_from_previous_position(mini_repo):
    _, _, smid = material_fixture(mini_repo)
    compact_via_gateway(mini_repo)
    repo = load_repo(mini_repo)
    sm = repo.study_maps[smid]
    edited = copy.deepcopy(sm.data)
    resources = edited["stages"][0]["resources"]
    resources[0], resources[2] = resources[2], resources[0]
    saved = preserve_map_refs(sm, edited)
    assert "material_ref" not in saved["stages"][0]["resources"][0]
    assert expand_map(saved, repo.module_source_maps[sm.module_id], sm.module_id, sm.unit_id) == edited


def test_explicit_override_equal_to_owner_is_not_updated_and_patch_replays(mini_repo):
    _, rid, smid = material_fixture(mini_repo)
    compact_via_gateway(mini_repo)
    repo = load_repo(mini_repo)
    sm = repo.study_maps[smid]
    raw = copy.deepcopy(sm.authored_data)
    res = raw["stages"][0]["resources"][1]
    old_detail = sm.data["stages"][0]["resources"][1]["angle_detail"]
    res["material_ref"]["inherit"].remove("angle_detail")
    res["angle_detail"] = old_detail
    write_yaml(sm.path, raw)
    repo = load_repo(mini_repo)
    context = run_los(mini_repo, "plan-edit-context", sm.unit_id, "--route-id", rid)
    assert context.returncode == 0, context.stderr
    uses = json.loads(context.stdout)["uses"]
    assert uses[1]["overrides"]["angle_detail"] == old_detail
    changes = {"angle_detail": "Changed common material explanation."}
    _, artifacts, _ = route_patch_plan(repo, sm.unit_id, rid, changes)
    envelope = approved_v2_envelope(
        mini_repo, capability="route.patch",
        payload={"unit_id": sm.unit_id, "route_id": rid, "changes": changes},
        artifact_ids=sorted(artifacts), idempotency_key="override-patch",
    )
    first = run_v2_capability(mini_repo, envelope)
    assert first.returncode == 0, first.stdout + first.stderr
    snapshot = canonical_fingerprint(mini_repo)
    replay = run_v2_capability(mini_repo, envelope)
    assert replay.returncode == 0, replay.stdout + replay.stderr
    assert json.loads(replay.stdout)["replayed"] is True
    assert canonical_fingerprint(mini_repo) == snapshot
    resources = load_repo(mini_repo).study_maps[smid].data["stages"][0]["resources"]
    assert resources[0]["angle_detail"] == changes["angle_detail"]
    assert resources[1]["angle_detail"] == old_detail
