"""Shared material storage must preserve learning behavior and write guards."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from gateway_helpers import (
    approved_v2_call,
    approved_v2_cli,
    approved_v2_envelope,
    file_sha256,
    run_v2_capability,
)
from repo_builders import (
    _structural_fixture,
    material_fixture,
    run_los,
    write_minimal_pdf,
    write_yaml,
)

from learning_os.app.handlers.maps import unit_map_import
from learning_os.app.handlers.routes import compaction_plan, route_patch_plan
from learning_os.derive.projection import build_manifest
from learning_os.domain.material_refs import (
    MaterialReferenceError,
    compact_map,
    expand_map,
    preserve_map_refs,
)
from learning_os.store.contracts.gateway import intent_sha256
from learning_os.store.fingerprint import canonical_fingerprint
from learning_os.store.loader import load_repo


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
    text = "The expected value is the probability weighted sum of the possible outcomes."
    material = repo.materials_root / "source-demo-book/lecture-02.pdf"
    write_minimal_pdf(material, [text])
    write_minimal_pdf(material.with_name("book.pdf"), [text])
    write_yaml(mini_repo / "records/materials-manifest.yaml", {"files": {
        "source-demo-book/" + path.name: {"sha256": file_sha256(path), "size": path.stat().st_size}
        for path in material.parent.iterdir() if path.is_file()}})
    evidence = {"claim_id": "covers:" + rid, "evidence": [{
        "kind": "quote", "ref": "material://source-demo-book/lecture-02.pdf", "page": 1, "text": text}]}
    response = approved_v2_call(
        mini_repo, capability="route.patch", payload={"unit_id": unit_id, "route_id": rid,
                                                    "changes": changes, "claim_evidence": evidence},
        artifact_ids=sorted(artifacts | {"file:operations/transactions/lineage.yaml"}), idempotency_key="patch-demo",
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


def test_map_import_missing_unit_is_typed_with_the_legacy_complaint(
        mini_repo, tmp_path):
    """SPEC (cq) 4: only the class changes; message, site, exit, effects stay."""
    from learning_os.app.context import OpContext
    from learning_os.domain.failures import NotFound
    from learning_os.domain.suggest import not_found, suggestions

    repo, _, _ = material_fixture(mini_repo)
    draft = tmp_path / "reviewed-map.yaml"
    write_yaml(draft, {"unit_id": "unit-nope"})
    ctx = OpContext(root=mini_repo, operation="unit.map.import",
                    channel="cli", invocation="command", gateway=None)
    before = canonical_fingerprint(mini_repo)
    with pytest.raises(NotFound) as caught:
        unit_map_import(ctx, {"unit_id": "unit-nope", "file": str(draft),
                              "file_sha256": file_sha256(draft)})
    exc = caught.value
    assert type(exc) is NotFound
    assert str(exc) == not_found("unit", "unit-nope", repo.units)
    assert exc.site == "unit.map.import.unknown-unit"
    assert exc.gateway_message == f"los: {exc}"
    assert exc.exit_code == 2
    assert exc.reason == "NOT_FOUND"
    assert exc.suggestions == suggestions("unit-nope", repo.units)
    assert canonical_fingerprint(mini_repo) == before


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


def test_route_patch_check_reports_envelope_ready_apply_values(mini_repo):
    repo, rid, smid = material_fixture(mini_repo)
    unit_id = repo.study_maps[smid].unit_id
    changes = {"angle": "A check-then-apply explanation"}
    check = run_los(mini_repo, "route-patch", unit_id, rid,
                    "--changes", json.dumps(changes), "--check")
    assert check.returncode == 0, check.stderr
    report = json.loads(check.stdout)
    assert report["canonical_files_written"] == 0
    hint = report["next"]
    assert hint["apply_via"] == "GatewayEnvelopeV2"
    assert hint["capability"] == "route.patch"
    assert hint["payload"] == {"unit_id": unit_id, "route_id": rid, "changes": changes}
    assert hint["expected_snapshot"] == report["snapshot_id"]
    assert hint["expected_revisions"] == report["expected_revisions"]
    before = canonical_fingerprint(mini_repo)
    guard_args = ["--expected-snapshot", hint["expected_snapshot"]]
    for aid, rev in hint["expected_revisions"].items():
        guard_args += ["--expected-revision", f"{aid}={rev}"]
    direct = run_los(mini_repo, "route-patch", unit_id, rid,
                     "--changes", json.dumps(changes), *guard_args)
    assert direct.returncode != 0
    assert canonical_fingerprint(mini_repo) == before


# Agility Stage 5: small intents must preserve every unchanged authored byte.
@pytest.mark.parametrize('edit', [
    {'stage_move': {'stage_id': 'stage-3', 'before_id': 'stage-demo'}},
    {'resource_move': {'stage_id': 'stage-demo', 'resource_id': 'resource-second', 'before_id': 'resource-original'}},
    {'resource_insert': {'stage_id': 'stage-demo', 'after_id': 'resource-original', 'resource': {
        'id': 'resource-new', 'kind': 'read', 'scope_triage': 'helpful-now',
        'material_ref': {'route_id': 'route-demo-book', 'inherit': ['label', 'source_id', 'locator', 'angle', 'angle_detail']}}}},
    {'resource_append': {'stage_id': 'stage-demo', 'resource': {
        'id': 'resource-new-appended', 'kind': 'read', 'scope_triage': 'helpful-now',
        'material_ref': {'route_id': 'route-demo-book', 'inherit': ['label', 'source_id', 'locator', 'angle', 'angle_detail']}}}},
])
def test_structural_intent_exact_review_preserves_state_and_one_receipt(mini_repo, tmp_path, edit):
    import yaml

    from learning_os.domain.plan_import import apply_structural_edit

    path, before = _structural_fixture(mini_repo)
    edit = {'reason': 'Reviewed fixture sequence.', **edit}
    draft = tmp_path / 'intent.json'
    draft.write_text(json.dumps({'unit_id': 'unit-demo-l01', 'structural_edit': edit}))
    resume_before = (mini_repo / 'curriculum/resume.yaml').read_bytes()
    initial = canonical_fingerprint(mini_repo)
    check = run_los(mini_repo, 'unit-map-import', 'unit-demo-l01', '--file', str(draft), '--replace', '--check')
    assert check.returncode == 0, check.stderr
    review = json.loads(check.stdout)
    assert review['canonical_files_written'] == 0
    assert canonical_fingerprint(mini_repo) == initial
    assert review['diff']['stages_after'] == [s['id'] for s in apply_structural_edit(before, edit)['stages']]
    envelope = approved_v2_envelope(mini_repo, capability='unit.map.import', payload={
        'unit_id': 'unit-demo-l01', 'file': str(draft), 'file_sha256': review['file_sha256'], 'replace': True,
    }, artifact_ids=list(review['expected_revisions']), idempotency_key='structural')
    envelope['expected_snapshot'] = review['snapshot_id']
    envelope['expected_revisions'] = review['expected_revisions']
    result = run_v2_capability(mini_repo, envelope)
    assert result.returncode == 0, result.stdout + result.stderr
    assert yaml.safe_load(path.read_text()) == apply_structural_edit(before, edit)
    assert (mini_repo / 'curriculum/resume.yaml').read_bytes() == resume_before
    assert (path.parent / 'stages/stage-demo/attachments/proof.txt').read_text() == 'Learner attachment.\n'
    assert len(list((mini_repo / 'operations/transactions').glob('transaction-*.yaml'))) == 1
    # Exact replay cannot move the record a second time or append a receipt.
    assert run_v2_capability(mini_repo, envelope).returncode == 0
    assert len(list((mini_repo / 'operations/transactions').glob('transaction-*.yaml'))) == 1
    for stage in before['stages']:
        if stage['id'] != 'stage-demo':
            assert (mini_repo / stage['working_note']).read_text() == 'Preserve this working note.\n'


@pytest.mark.parametrize('drift', ['draft', 'snapshot', 'revision'])
def test_structural_review_refuses_drift_without_writes(mini_repo, tmp_path, drift):
    from learning_os.store.contracts.gateway import intent_sha256

    path, before = _structural_fixture(mini_repo)
    draft = tmp_path / 'intent.json'
    draft.write_text(json.dumps({'unit_id': 'unit-demo-l01', 'structural_edit': {
        'reason': 'Reviewed fixture.', 'stage_move': {'stage_id': 'stage-3', 'before_id': 'stage-demo'}}}))
    check = run_los(mini_repo, 'unit-map-import', 'unit-demo-l01', '--file', str(draft), '--replace', '--check')
    assert check.returncode == 0, check.stderr
    review = json.loads(check.stdout)
    envelope = approved_v2_envelope(mini_repo, capability='unit.map.import', payload={
        'unit_id': 'unit-demo-l01', 'file': str(draft), 'file_sha256': review['file_sha256'], 'replace': True,
    }, artifact_ids=list(review['expected_revisions']), idempotency_key='stale-structural')
    if drift == 'draft':
        draft.write_text(draft.read_text() + ' ')
    elif drift == 'snapshot':
        (mini_repo / before['stages'][0]['working_note']).write_text('New learner work.')
    else:
        envelope['expected_revisions']['unit-demo-l01'] += 1
        envelope['approval']['subject_sha256'] = intent_sha256(envelope)
    initial = canonical_fingerprint(mini_repo)
    result = run_v2_capability(mini_repo, envelope)
    assert result.returncode != 0
    assert canonical_fingerprint(mini_repo) == initial
    assert path.read_text()
    assert not list((mini_repo / 'operations/transactions').glob('transaction-*.yaml'))


@pytest.mark.parametrize('edit', [
    {}, {'stage_move': {'stage_id': 'stage-3', 'before_id': 'stage-3'}},
    {'stage_move': {'stage_id': 'stage-3', 'before_id': 'missing'}},
    {'stage_move': {'stage_id': 'stage-3', 'before_id': 'stage-demo', 'after_id': 'stage-2'}},
    {'stage_move': {'stage_id': 'stage-2', 'after_id': 'stage-demo'}},
    {'resource_move': {'stage_id': 'stage-demo', 'resource_id': 'missing', 'before_id': 'resource-original'}},
    {'resource_insert': {'stage_id': 'stage-demo', 'before_id': 'resource-original', 'resource': {'id': 'resource-original'}}},
    {'resource_insert': {'stage_id': 'stage-demo', 'before_id': 'resource-original', 'resource': {'id': 'resource-new'}}},
    {'stage_move': {'stage_id': 'stage-3', 'before_id': 'stage-demo', 'title': 'Unauthorized'}},
    {'resource_append': {'stage_id': 'missing-stage', 'resource': {'id': 'res-1', 'kind': 'read', 'material_ref': {'route_id': 'route-demo-book'}}}},
    {'resource_append': {'stage_id': 'stage-demo', 'resource': {'id': 'resource-original', 'kind': 'read', 'material_ref': {'route_id': 'route-demo-book'}}}},
    {'resource_append': {'stage_id': 'stage-demo', 'resource': {'id': '', 'kind': 'read', 'material_ref': {'route_id': 'route-demo-book'}}}},
    {'resource_append': {'stage_id': 'stage-demo', 'resource': 'not-a-dict'}},
    {'resource_append': {'stage_id': 'stage-demo', 'before_id': 'resource-original', 'resource': {'id': 'res-1'}}},
    {'resource_append': {'stage_id': 'stage-demo'}},
])
def test_structural_malformed_edits_fail_without_writes(mini_repo, tmp_path, edit):
    _structural_fixture(mini_repo)
    draft = tmp_path / 'intent.json'
    draft.write_text(json.dumps({'unit_id': 'unit-demo-l01', 'structural_edit': {'reason': 'Fixture', **edit}}))
    initial = canonical_fingerprint(mini_repo)
    check = run_los(mini_repo, 'unit-map-import', 'unit-demo-l01', '--file', str(draft), '--replace', '--check')
    assert check.returncode != 0
    assert canonical_fingerprint(mini_repo) == initial


def test_structural_apply_publication_failure_rolls_back_with_no_receipt(mini_repo, tmp_path, monkeypatch):
    from learning_os.adapters.cli_parser import build_parser
    from learning_os.app import commit, pipeline
    from learning_os.store.contracts.capability_catalog import command_definitions
    from learning_os.store.diagnostics import tracer
    from learning_os.store.diagnostics.store import bind_store

    _structural_fixture(mini_repo)
    draft = tmp_path / 'intent.json'
    draft.write_text(json.dumps({'unit_id': 'unit-demo-l01', 'structural_edit': {
        'reason': 'Reviewed fixture.', 'stage_move': {'stage_id': 'stage-3', 'before_id': 'stage-demo'}}}))
    envelope = approved_v2_envelope(mini_repo, capability='unit.map.import', payload={
        'unit_id': 'unit-demo-l01', 'file': str(draft), 'file_sha256': file_sha256(draft), 'replace': True,
    }, artifact_ids=['unit-demo-l01', 'study-map-demo-l01'], idempotency_key='structural-rollback')
    before = canonical_fingerprint(mini_repo)

    def fail_publication(_repo):
        raise OSError('fixture publication failure after canonical writes')

    monkeypatch.setattr(commit, '_publish_repo', fail_publication)
    bind_store(mini_repo)
    outcome = pipeline.run_gateway(mini_repo, envelope, requested='unit.map.import',
                                   definitions=command_definitions(mini_repo),
                                   attempt=tracer.begin_attempt({'capability': 'unit.map.import'}),
                                   replay_only=False, parser_factory=build_parser)
    assert outcome.exit_code != 0
    assert canonical_fingerprint(mini_repo) == before
    assert not list((mini_repo / 'operations/transactions').glob('transaction-*.yaml'))


def test_resource_append_empty_and_idless_stages_and_channel_refusal(mini_repo, tmp_path):
    import yaml
    from repo_builders import write_yaml

    from learning_os.app.validation_service import collect
    from learning_os.store.warning_baseline import write_baseline

    path, before = _structural_fixture(mini_repo)
    # Stage 3 is given an un-ID'd resource
    stage3 = next(s for s in before['stages'] if s['id'] == 'stage-3')
    stage3['resources'] = [{
        'kind': 'read',
        'scope_triage': 'helpful-now',
        'material_ref': {'route_id': 'route-demo-book', 'inherit': ['label', 'source_id', 'locator', 'angle', 'angle_detail']}
    }]
    write_yaml(path, before)
    write_baseline(mini_repo, collect(mini_repo)[0], 'idless fixture baseline')

    # 1. Append to empty stage (stage-2)
    draft_empty = tmp_path / 'append-empty.json'
    draft_empty.write_text(json.dumps({'unit_id': 'unit-demo-l01', 'structural_edit': {
        'reason': 'Append to empty stage.',
        'resource_append': {
            'stage_id': 'stage-2',
            'resource': {
                'id': 'resource-appended-to-empty',
                'kind': 'read',
                'scope_triage': 'helpful-now',
                'material_ref': {'route_id': 'route-demo-book', 'inherit': ['label', 'source_id', 'locator', 'angle', 'angle_detail']}
            }
        }
    }}))
    check_empty = run_los(mini_repo, 'unit-map-import', 'unit-demo-l01', '--file', str(draft_empty), '--replace', '--check')
    assert check_empty.returncode == 0, check_empty.stderr
    review_empty = json.loads(check_empty.stdout)
    assert review_empty['canonical_files_written'] == 0

    envelope_empty = approved_v2_envelope(mini_repo, capability='unit.map.import', payload={
        'unit_id': 'unit-demo-l01', 'file': str(draft_empty), 'file_sha256': review_empty['file_sha256'], 'replace': True,
    }, artifact_ids=list(review_empty['expected_revisions']), idempotency_key='append-to-empty')
    envelope_empty['expected_snapshot'] = review_empty['snapshot_id']
    envelope_empty['expected_revisions'] = review_empty['expected_revisions']
    res_empty = run_v2_capability(mini_repo, envelope_empty)
    assert res_empty.returncode == 0, res_empty.stdout + res_empty.stderr
    map_after_1 = yaml.safe_load(path.read_text())
    assert len(map_after_1['stages'][1]['resources']) == 1
    assert map_after_1['stages'][1]['resources'][0]['id'] == 'resource-appended-to-empty'

    # 2. Append to ID-less stage (stage-3)
    draft_idless = tmp_path / 'append-idless.json'
    draft_idless.write_text(json.dumps({'unit_id': 'unit-demo-l01', 'structural_edit': {
        'reason': 'Append to legacy ID-less stage.',
        'resource_append': {
            'stage_id': 'stage-3',
            'resource': {
                'id': 'resource-appended-to-idless',
                'kind': 'read',
                'scope_triage': 'helpful-now',
                'material_ref': {'route_id': 'route-demo-book', 'inherit': ['label', 'source_id', 'locator', 'angle', 'angle_detail']}
            }
        }
    }}))
    check_idless = run_los(mini_repo, 'unit-map-import', 'unit-demo-l01', '--file', str(draft_idless), '--replace', '--check')
    assert check_idless.returncode == 0, check_idless.stderr
    review_idless = json.loads(check_idless.stdout)

    envelope_idless = approved_v2_envelope(mini_repo, capability='unit.map.import', payload={
        'unit_id': 'unit-demo-l01', 'file': str(draft_idless), 'file_sha256': review_idless['file_sha256'], 'replace': True,
    }, artifact_ids=list(review_idless['expected_revisions']), idempotency_key='append-to-idless')
    envelope_idless['expected_snapshot'] = review_idless['snapshot_id']
    envelope_idless['expected_revisions'] = review_idless['expected_revisions']

    # Test direct CLI application without GatewayEnvelopeV2 is refused (exit code 2)
    cli_direct = run_los(mini_repo, 'unit-map-import', 'unit-demo-l01', '--file', str(draft_idless), '--replace')
    assert cli_direct.returncode == 2
    assert 'canonical writes must use GatewayEnvelopeV2' in cli_direct.stderr

    # Test wrong channel in envelope is refused
    wrong_channel_envelope = copy.deepcopy(envelope_idless)
    wrong_channel_envelope['channel'] = 'invalid-channel'
    wrong_channel_envelope['idempotency_key'] = 'wrong-channel'
    res_wrong_channel = run_v2_capability(mini_repo, wrong_channel_envelope)
    assert res_wrong_channel.returncode != 0

    # Valid gateway application succeeds
    res_idless = run_v2_capability(mini_repo, envelope_idless)
    assert res_idless.returncode == 0, res_idless.stdout + res_idless.stderr
    map_after_2 = yaml.safe_load(path.read_text())
    assert len(map_after_2['stages'][2]['resources']) == 2
    # First row still has no ID and was preserved untouched
    assert 'id' not in map_after_2['stages'][2]['resources'][0]
    # Second row is the newly appended resource
    assert map_after_2['stages'][2]['resources'][1]['id'] == 'resource-appended-to-idless'

    # Idempotent replay: running identical envelope again produces exit 0 and does not duplicate
    res_replay = run_v2_capability(mini_repo, envelope_idless)
    assert res_replay.returncode == 0
    map_after_replay = yaml.safe_load(path.read_text())
    assert len(map_after_replay['stages'][2]['resources']) == 2


def test_unit_map_import_warning_delta_consistency_between_replacement_and_append(mini_repo, tmp_path):
    import yaml
    from repo_builders import SLICED_LECTURE_TEXT, write_minimal_pdf, write_yaml

    from learning_os.app.validation_service import collect
    from learning_os.store.warning_baseline import write_baseline

    path, before = _structural_fixture(mini_repo)

    # Set stage-demo to map to knowledge-demo-expectation
    before['stages'][0]['knowledge_node_id'] = 'knowledge-demo-expectation'
    write_yaml(path, before)

    # Create second minimal pdf material
    mat = mini_repo.parent / 'materials/source-demo-book/lecture-02.pdf'
    write_minimal_pdf(mat, [SLICED_LECTURE_TEXT])

    # Add a route in source-map that does NOT cover knowledge-demo-expectation
    source_map_path = mini_repo / 'curriculum/modules/module-demo/source-map.yaml'
    source_map = yaml.safe_load(source_map_path.read_text())
    source_map['sources'][0]['unit_routes'].append({
        'id': 'route-demo-other-node',
        'unit_id': 'unit-demo-l01',
        'covers': ['knowledge-demo-outcomes'],
        'title': 'Other node route',
        'format': 'book',
        'angle': 'Different topic.',
        'angle_detail': 'Detailed explanation of unrelated topic.',
        'locator': 'lecture-02.pdf',
        'depth': 'derivation',
        'scope': 'current',
    })
    write_yaml(source_map_path, source_map)
    write_baseline(mini_repo, collect(mini_repo)[0], 'baseline with new route')

    # 1. Structural append WITHOUT node_scaffold_note introduces RESOURCE-NODE-ORPHAN
    orphan_append_draft = tmp_path / 'orphan-append.json'
    orphan_append_draft.write_text(json.dumps({'unit_id': 'unit-demo-l01', 'structural_edit': {
        'reason': 'Orphan append without scaffold note.',
        'resource_append': {
            'stage_id': 'stage-demo',
            'resource': {
                'id': 'resource-orphan-append',
                'kind': 'read',
                'scope_triage': 'helpful-now',
                'material_ref': {'route_id': 'route-demo-other-node', 'inherit': ['label', 'source_id', 'locator', 'angle', 'angle_detail']}
            }
        }
    }}))
    check_append = run_los(mini_repo, 'unit-map-import', 'unit-demo-l01', '--file', str(orphan_append_draft), '--replace', '--check')
    assert check_append.returncode == 1
    assert 'RESOURCE-NODE-ORPHAN' in check_append.stderr

    # 2. Full map replacement WITHOUT node_scaffold_note introduces the exact same RESOURCE-NODE-ORPHAN
    orphan_replacement_map = copy.deepcopy(before)
    orphan_replacement_map['stages'][0]['resources'].append({
        'id': 'resource-orphan-replace',
        'kind': 'read',
        'scope_triage': 'helpful-now',
        'material_ref': {'route_id': 'route-demo-other-node', 'inherit': ['label', 'source_id', 'locator', 'angle', 'angle_detail']}
    })
    orphan_replace_draft = tmp_path / 'orphan-replace.yaml'
    write_yaml(orphan_replace_draft, orphan_replacement_map)
    check_replace = run_los(mini_repo, 'unit-map-import', 'unit-demo-l01', '--file', str(orphan_replace_draft), '--replace', '--check')
    assert check_replace.returncode == 1
    assert 'RESOURCE-NODE-ORPHAN' in check_replace.stderr

    # 3. Adding node_scaffold_note makes BOTH preflights pass cleanly
    justified_append_draft = tmp_path / 'justified-append.json'
    justified_append_draft.write_text(json.dumps({'unit_id': 'unit-demo-l01', 'structural_edit': {
        'reason': 'Justified scaffold append.',
        'resource_append': {
            'stage_id': 'stage-demo',
            'resource': {
                'id': 'resource-justified-append',
                'kind': 'read',
                'scope_triage': 'helpful-now',
                'node_scaffold_note': 'Deliberate groundwork for future concept contrast.',
                'material_ref': {'route_id': 'route-demo-other-node', 'inherit': ['label', 'source_id', 'locator', 'angle', 'angle_detail']}
            }
        }
    }}))
    check_justified_append = run_los(mini_repo, 'unit-map-import', 'unit-demo-l01', '--file', str(justified_append_draft), '--replace', '--check')
    assert check_justified_append.returncode == 0, check_justified_append.stderr

    justified_replacement_map = copy.deepcopy(before)
    justified_replacement_map['stages'][0]['resources'].append({
        'id': 'resource-justified-replace',
        'kind': 'read',
        'scope_triage': 'helpful-now',
        'node_scaffold_note': 'Deliberate groundwork for future concept contrast.',
        'material_ref': {'route_id': 'route-demo-other-node', 'inherit': ['label', 'source_id', 'locator', 'angle', 'angle_detail']}
    })
    justified_replace_draft = tmp_path / 'justified-replace.yaml'
    write_yaml(justified_replace_draft, justified_replacement_map)
    check_justified_replace = run_los(mini_repo, 'unit-map-import', 'unit-demo-l01', '--file', str(justified_replace_draft), '--replace', '--check')
    assert check_justified_replace.returncode == 0, check_justified_replace.stderr

    # 4. Attempting to commit an orphan without scaffold justification rolls back
    review_raw = json.loads(check_justified_append.stdout)
    envelope_bad = approved_v2_envelope(mini_repo, capability='unit.map.import', payload={
        'unit_id': 'unit-demo-l01', 'file': str(orphan_append_draft), 'file_sha256': file_sha256(orphan_append_draft), 'replace': True,
    }, artifact_ids=list(review_raw['expected_revisions']), idempotency_key='bad-commit-orphan')
    envelope_bad['expected_snapshot'] = review_raw['snapshot_id']
    envelope_bad['expected_revisions'] = review_raw['expected_revisions']
    before_commit = canonical_fingerprint(mini_repo)
    commit_res = run_v2_capability(mini_repo, envelope_bad)
    assert commit_res.returncode != 0
    assert canonical_fingerprint(mini_repo) == before_commit


@pytest.mark.parametrize('form', ['compact', 'full'])
def test_warning_growth_refuses_at_preflight_and_apply_in_either_form(mini_repo, tmp_path, form):
    """A warning outside the RESOURCE-* family: the form of an edit cannot decide it."""
    _, before = _structural_fixture(mini_repo)
    resource = {
        'id': 'resource-diverging', 'kind': 'read', 'scope_triage': 'helpful-now',
        'angle': 'An angle its route does not carry.',
        'material_ref': {'route_id': 'route-demo-book', 'inherit': ['label', 'source_id', 'locator', 'angle_detail']},
    }
    if form == 'compact':
        proposal = {'unit_id': 'unit-demo-l01', 'structural_edit': {
            'reason': 'Diverging angle.',
            'resource_append': {'stage_id': 'stage-demo', 'resource': resource},
        }}
    else:
        proposal = copy.deepcopy(before)
        proposal['stages'][0]['resources'].append(resource)
    draft = tmp_path / 'draft.json'
    draft.write_text(json.dumps(proposal))

    check = run_los(mini_repo, 'unit-map-import', 'unit-demo-l01', '--file', str(draft), '--replace', '--check')
    assert check.returncode == 1
    assert 'W NEW-OR-GROWN-WARNING: ANGLE-DIVERGES-FROM-ROUTE' in check.stderr

    untouched = canonical_fingerprint(mini_repo)
    applied = approved_v2_call(mini_repo, capability='unit.map.import', payload={
        'unit_id': 'unit-demo-l01', 'file': str(draft), 'file_sha256': file_sha256(draft), 'replace': True,
    }, artifact_ids=['unit-demo-l01', before['id']], idempotency_key=f'diverging-{form}')
    assert applied.returncode != 0
    assert 'ANGLE-DIVERGES-FROM-ROUTE' in applied.stdout + applied.stderr
    assert canonical_fingerprint(mini_repo) == untouched


def test_first_map_preflight_reports_the_errors_apply_would_refuse(mini_repo, tmp_path):
    """A first map keeps its errors-only gate, and preflight now applies it too."""
    import yaml
    from scenario_fixtures import rich_world

    rich_world(mini_repo)
    first = Path(__file__).parent / 'scenarios/files/unit.map.import/first-import/map.yaml'
    proposal = yaml.safe_load(first.read_text())
    proposal['stages'][0]['resources'] = [{
        'id': 'resource-unknown', 'kind': 'read', 'label': 'Unknown', 'source_id': 'source-missing',
        'locator': 'p. 1', 'scope_triage': 'helpful-now',
    }]
    draft = tmp_path / 'first.yaml'
    write_yaml(draft, proposal)

    check = run_los(mini_repo, 'unit-map-import', 'unit-demo-l02', '--file', str(draft), '--check')
    assert check.returncode == 1
    assert 'E REF-SOURCE' in check.stderr


def test_operator_channel_cannot_present_a_learner_gesture_for_a_compact_edit(mini_repo, tmp_path):
    _, before = _structural_fixture(mini_repo)
    draft = tmp_path / 'append.json'
    draft.write_text(json.dumps({'unit_id': 'unit-demo-l01', 'structural_edit': {
        'reason': 'Claimed gesture.',
        'resource_append': {'stage_id': 'stage-demo', 'resource': {
            'id': 'resource-claimed', 'kind': 'read', 'scope_triage': 'helpful-now',
            'material_ref': {'route_id': 'route-demo-book', 'inherit': ['label', 'source_id', 'locator', 'angle', 'angle_detail']},
        }},
    }}))
    envelope = approved_v2_envelope(mini_repo, capability='unit.map.import', payload={
        'unit_id': 'unit-demo-l01', 'file': str(draft), 'file_sha256': file_sha256(draft), 'replace': True,
    }, artifact_ids=['unit-demo-l01', before['id']], idempotency_key='claimed-gesture')
    envelope['approval'] = {'kind': 'direct-user-gesture', 'subject_sha256': envelope['approval']['subject_sha256']}
    envelope['approval']['subject_sha256'] = intent_sha256(envelope)

    untouched = canonical_fingerprint(mini_repo)
    refused = run_v2_capability(mini_repo, envelope)
    assert refused.returncode != 0
    assert 'authorized by a reviewed action in the LearningOS app' in refused.stdout + refused.stderr
    assert canonical_fingerprint(mini_repo) == untouched
