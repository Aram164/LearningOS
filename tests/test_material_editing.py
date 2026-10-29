"""Shared material storage must preserve learning behavior and write guards."""

from __future__ import annotations

import copy
import json

import pytest
from gateway_helpers import (
    approved_v2_call,
    approved_v2_cli,
    approved_v2_envelope,
    file_sha256,
    run_v2_capability,
)
from repo_builders import material_fixture, run_los, write_minimal_pdf, write_yaml

from learning_os.app.handlers.maps import unit_map_import
from learning_os.app.handlers.routes import compaction_plan, route_patch_plan
from learning_os.derive.projection import build_manifest
from learning_os.domain.material_refs import (
    MaterialReferenceError,
    compact_map,
    expand_map,
    preserve_map_refs,
)
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
def _structural_fixture(root):
    import yaml
    from repo_builders import _compact_setup

    from learning_os.app.validation_service import collect
    from learning_os.store.warning_baseline import write_baseline

    _compact_setup(root)
    path = root / 'curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml'
    data = yaml.safe_load(path.read_text())
    data['plan_template_version'] = 1
    first = data['stages'][0]
    first.update(number=1, exam_critical=False, concepts=[])
    first['resources'][0]['id'] = 'resource-original'
    second = copy.deepcopy(first['resources'][0])
    second['id'] = 'resource-second'
    first['resources'].append(second)
    for resource in first['resources']:
        preserved = {key: resource[key] for key in ('id', 'kind', 'scope_triage') if key in resource}
        resource.clear()
        resource.update(preserved, material_ref={'route_id': 'route-demo-book', 'inherit': ['label', 'source_id', 'locator', 'angle', 'angle_detail']})
    attachment = path.parent / 'stages/stage-demo/attachments/proof.txt'
    attachment.parent.mkdir(parents=True, exist_ok=True)
    attachment.write_text('Learner attachment.\n')
    first['attachments'] = [{'path': str(attachment.relative_to(root)), 'label': 'Proof'}]
    first['source_feedback'] = [{'source_id': 'source-demo-book', 'resource_id': 'resource-original', 'feedback': 'helpful', 'recorded': '2026-10-01', 'note': 'My wording.'}]
    for number in (2, 3):
        stage = copy.deepcopy(first)
        stage.update(id=f'stage-{number}', number=number, status='pending')
        stage['resources'] = []
        stage['attachments'] = []
        stage['source_feedback'] = []
        stage['working_note'] = str(path.parent.relative_to(root) / f'stages/stage-{number}/notes.md')
        note = root / stage['working_note']
        note.parent.mkdir(parents=True)
        note.write_text('Preserve this working note.\n')
        data['stages'].append(stage)
    write_yaml(path, data)
    write_baseline(root, collect(root)[0], 'structural fixture')
    return path, data


@pytest.mark.parametrize('edit', [
    {'stage_move': {'stage_id': 'stage-3', 'before_id': 'stage-demo'}},
    {'resource_move': {'stage_id': 'stage-demo', 'resource_id': 'resource-second', 'before_id': 'resource-original'}},
    {'resource_insert': {'stage_id': 'stage-demo', 'after_id': 'resource-original', 'resource': {
        'id': 'resource-new', 'kind': 'read', 'scope_triage': 'helpful-now',
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
