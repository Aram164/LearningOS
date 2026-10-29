"""The thesis migration is exercised only in disposable repositories."""

from __future__ import annotations

import copy
import json
import shutil

import pytest
import yaml
from jsonschema import Draft202012Validator
from repo_builders import add_curriculum, run_los, write_yaml

from learning_os.app import project_migration as migration
from learning_os.app.handlers.platform import record_payload
from learning_os.derive.projection.manifest import build_manifest
from learning_os.derive.validation import validate
from learning_os.domain.failures import TransactionFailure, WriteRefused
from learning_os.store.fingerprint import snapshot
from learning_os.store.loader import load_repo, parse_frontmatter
from learning_os.store.revisions import load_revisions
from learning_os.store.transactions import TransactionService, reconcile_inflight_transactions
from learning_os.store.warning_baseline import signatures_from_issues, write_baseline


@pytest.fixture
def thesis(mini_repo, repo_root):
    root = mini_repo
    add_curriculum(root)
    frozen = repo_root / "tests/fixtures/migrations/projects-to-modules-v62"
    shutil.copytree(frozen, root, dirs_exist_ok=True)
    project = yaml.safe_load((root / migration.PROJECT_PATH).read_text())
    for module_id in project["linked_module_ids"]:
        write_yaml(root / f"curriculum/modules/{module_id}/module.yaml", {
            "id": module_id, "type": "module", "kind": "project", "title": module_id,
            "status": "planned", "area_id": "program-bachelors", "unit_order": [],
            "source_map": "source-map.yaml",
        })
        write_yaml(root / f"curriculum/modules/{module_id}/source-map.yaml", {
            "type": "module-source-map", "module_id": module_id, "sources": []})
    write_yaml(root / "sources/collections/project-toolbox.yaml", {
        "title": "Test toolbox", "collection_kind": "topic-pack", "purpose": "Fixture tools.",
        "entries": [{"source": "source-demo-book", "why": "Fixture reference."}],
    })
    for row in project["files"]:
        path = root / row["path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        if row["path"].startswith("knowledge/"):
            path.write_text("---\nid: note-bachelor-thesis-medical-mle-exploration\n"
                            "type: note\ntitle: Test research note\ncreated: '2026-07-20'\n"
                            "role: synthesis\nconcepts: []\nsources: []\n---\nResearch.\n")
        else:
            path.write_text(f"# Fixture deliverable\n\n{row['label']}\n")
    issues = validate(load_repo(root))
    signatures, errors = signatures_from_issues(issues)
    assert not errors, errors
    write_baseline(root, signatures, "Synthetic thesis migration content debt.")
    return root


def commit(root, report=None):
    report = report or migration.prepare(root)
    return migration.apply(root, report, reviewed_sha256=migration.plan_sha256(report))


def file_bytes(root):
    return {path.relative_to(root).as_posix(): path.read_bytes()
            for path in root.rglob("*") if path.is_file()}


def test_dry_run_is_read_only_and_field_map_is_exhaustive(thesis, repo_root):
    before = file_bytes(thesis)
    report = migration.prepare(thesis)
    assert file_bytes(thesis) == before
    project = yaml.safe_load(before[migration.PROJECT_PATH])
    relations = yaml.safe_load(before[migration.RELATIONS_PATH])["relations"]
    assert len(report["field_map"]) == 71 + 22
    context = report["writes"][migration.WORKSPACE_PATH]
    blocks = context.split("```yaml\n")[1:]
    sections = [yaml.safe_load(block.split("```", 1)[0]) for block in blocks]
    restored = {key: value for data in sections for key, value in data.items()
                if key not in {"relationships", "owners"}}
    assert restored == project
    assert next(data["relationships"] for data in sections if "relationships" in data) == relations
    for source in migration.SOURCES:
        assert report["writes"][f"{migration.BASE}/before/{source}"].encode() == before[source]
    old_schema = json.loads((repo_root / "system/contracts/manifest-v15.schema.json").read_text())
    assert not Draft202012Validator(old_schema["$defs"]["compatibilityAlias"]).is_valid({
        "id": migration.PROJECT, "type": "compatibility-alias", "target_id": migration.MODULE,
        "target_type": "module", "path": migration.ALIASES_PATH})


@pytest.mark.parametrize("resume_present", [True, False])
def test_atomic_apply_preserves_study_history_and_normal_lookup(thesis, resume_present):
    resume = thesis / "curriculum/resume.yaml"
    if not resume_present:
        resume.unlink()
    before = file_bytes(thesis)
    original_ws, body = parse_frontmatter(before[migration.WORKSPACE_PATH].decode(),
                                          thesis / migration.WORKSPACE_PATH)
    report = migration.prepare(thesis)
    result = commit(thesis, report)
    assert not result["replayed"]
    assert not (thesis / migration.PROJECT_PATH).exists()
    changed = {*migration.SOURCES}
    for relative, content in before.items():
        if relative not in changed and not relative.startswith("operations/transactions/"):
            assert (thesis / relative).read_bytes() == content, relative
    assert resume.exists() == resume_present
    ws, migrated_body = parse_frontmatter((thesis / migration.WORKSPACE_PATH).read_text(),
                                          thesis / migration.WORKSPACE_PATH)
    assert migrated_body.startswith(body)
    assert "project_id" not in ws
    assert ws["module_ids"] == original_ws["module_ids"]
    assert ws["unit_ids"] == original_ws["unit_ids"]
    assert ws["program_ids"] == ["program-bachelors"]
    module = yaml.safe_load((thesis / migration.MODULE_PATH).read_text())
    assert module["kind"] == "project" and module["status"] == "active"
    assert module["area_id"] == "program-bachelors"
    assert not {"credits", "institution", "semester", "examination", "attempts"} & module.keys()
    assert module["related_module_ids"] == ["module-hu-aml", "module-hu-amls"]
    assert len(module["thematic_group_ids"]) == 3
    manifest = build_manifest(load_repo(thesis), "2026-10-29")
    assert manifest["projects"] == [] and manifest["project_relationships"] == []
    for legacy, owner in report["redirects"].items():
        payload = record_payload(manifest, legacy)
        assert payload["id"] == owner and payload["resolved_from"] == legacy
        alias = next(row for row in manifest["records"] if row["id"] == legacy)
        assert alias["target_type"] == payload["type"]
    assert record_payload(manifest, migration.MODULE)["id"] == migration.MODULE
    assert "resolved_from" not in record_payload(manifest, migration.MODULE)
    assert migration._validation_errors(thesis) == []
    receipt = yaml.safe_load((thesis / result["receipt_path"]).read_text())
    assert receipt["expected_revisions"] == report["expected_revisions"]
    assert set(receipt["artifact_revisions"]) == {migration.PROJECT, migration.MODULE, migration.WORKSPACE}
    assert receipt["artifact_revisions"][migration.PROJECT]["after"] == 1


def test_supplied_academic_facts_are_preserved(thesis):
    path = thesis / migration.MODULE_PATH
    module = yaml.safe_load(path.read_text())
    facts = {"institution": "HU Berlin", "semester": "sose-2026", "credits": 12,
             "examination": {"type": "other", "sittings": []}}
    module.update(facts)
    write_yaml(path, module)
    commit(thesis)
    updated = yaml.safe_load(path.read_text())
    assert {key: updated[key] for key in facts} == facts


def test_replay_proves_receipt_and_never_overwrites_evolved_state(thesis):
    report = migration.prepare(thesis)
    first = commit(thesis, report)
    path = thesis / migration.WORKSPACE_PATH
    path.write_text(path.read_text() + "\nLater research decision.\n")
    before = file_bytes(thesis)
    again = commit(thesis, report)
    assert again["replayed"] and again["transaction_id"] == first["transaction_id"]
    assert file_bytes(thesis) == before
    (thesis / first["receipt_path"]).unlink()
    with pytest.raises((WriteRefused, FileNotFoundError)):
        commit(thesis, report)


@pytest.mark.parametrize("evidence", [f"{migration.BASE}/before/{migration.PROJECT_PATH}",
                                     f"{migration.BASE}/evidence.json", migration.MARKER])
def test_replay_refuses_changed_evidence(thesis, evidence):
    report = migration.prepare(thesis)
    commit(thesis, report)
    path = thesis / evidence
    if evidence == migration.MARKER:
        marker = json.loads(path.read_text())
        marker["transaction_id"] = "transaction-missing"
        path.write_text(json.dumps(marker))
    else:
        path.write_text(path.read_text() + "\nchanged evidence\n")
    with pytest.raises((WriteRefused, FileNotFoundError)):
        commit(thesis, report)


def test_historical_revisions_remain_literal_and_related_resolves_owner(thesis):
    write_yaml(thesis / "operations/transactions/revisions.yaml", {
        "schema_version": 1, "type": "artifact-revision-ledger",
        "revisions": {migration.PROJECT: 2, migration.MODULE: 1, migration.WORKSPACE: 2}})
    # A real historical receipt, whose Project artifact identity must not be aliased.
    catalogue_path = thesis / "system/contracts/capabilities.yaml"
    current_catalogue = catalogue_path.read_bytes()
    catalogue = yaml.safe_load(current_catalogue)
    catalogue["domain_capabilities"]["project.update"] = {"writes": ["projects/registry/*"]}
    write_yaml(catalogue_path, catalogue)
    previous = TransactionService(thesis).commit(
        capability="project.update",
        writes={thesis / migration.PROJECT_PATH: (thesis / migration.PROJECT_PATH).read_bytes()},
        artifact_ids=[migration.PROJECT], expected_revisions={migration.PROJECT: 2})
    catalogue_path.write_bytes(current_catalogue)
    previous_bytes = previous.receipt_path.read_bytes()
    report = migration.prepare(thesis)
    result = commit(thesis, report)
    assert previous.receipt_path.read_bytes() == previous_bytes
    receipt = yaml.safe_load((thesis / result["receipt_path"]).read_text())
    assert receipt["artifact_revisions"][migration.PROJECT] == {"before": 3, "after": 4}
    assert receipt["artifact_revisions"][migration.MODULE] == {"before": 1, "after": 2}
    inspected = run_los(thesis, "inspect", migration.PROJECT)
    assert inspected.returncode == 0, inspected.stderr
    payload = json.loads(inspected.stdout)
    assert payload["id"] == migration.MODULE and payload["resolved_from"] == migration.PROJECT
    for legacy, owner in [(migration.PROJECT, migration.MODULE),
                          ("workstream-thesis-landscape", migration.WORKSPACE)]:
        related = run_los(thesis, "related", legacy)
        canonical = run_los(thesis, "related", owner)
        assert related.returncode == canonical.returncode == 0, related.stderr
        aliased = json.loads(related.stdout)
        direct = json.loads(canonical.stdout)
        assert aliased == direct


@pytest.mark.parametrize("change", ["source", "snapshot", "revision", "resume"])
def test_stale_inputs_refuse_without_a_transaction(thesis, change):
    report = migration.prepare(thesis)
    if change == "source":
        path = thesis / migration.WORKSPACE_PATH
        path.write_text(path.read_text() + "\nExternal edit.\n")
    elif change == "snapshot":
        path = thesis / "work/COORDINATION.md"
        path.write_text(path.read_text() + "\nPriority change.\n")
    elif change == "resume":
        (thesis / "curriculum/resume.yaml").unlink()
    else:
        write_yaml(thesis / "operations/transactions/revisions.yaml", {
            "schema_version": 1, "type": "artifact-revision-ledger",
            "revisions": {migration.MODULE: 7}})
    before = file_bytes(thesis)
    with pytest.raises(WriteRefused, match="changed"):
        commit(thesis, report)
    assert file_bytes(thesis) == before


def test_review_and_authority_cannot_expand_write_set(thesis):
    report = migration.prepare(thesis)
    changed = copy.deepcopy(report)
    changed["writes"]["work/COORDINATION.md"] = "overwrite"
    with pytest.raises(WriteRefused, match="hash"):
        migration.apply(thesis, changed, reviewed_sha256=migration.plan_sha256(report))
    with pytest.raises(WriteRefused, match="changed"):
        commit(thesis, changed)
    from learning_os.domain.failures import TransactionScopeError
    with pytest.raises(TransactionScopeError):
        TransactionService(thesis).commit(
            capability=migration.AUTHORITY,
            writes={thesis / "work/COORDINATION.md": "forbidden"}, artifact_ids=[])


@pytest.mark.parametrize("location", [migration.WORKSPACE_PATH, migration.BASE])
def test_symlink_sources_and_destinations_refuse(thesis, tmp_path, location):
    path = thesis / location
    outside = tmp_path / "outside"
    if path.is_file():
        outside.write_bytes(path.read_bytes())
        path.unlink()
    else:
        outside.mkdir()
        path.parent.mkdir(parents=True, exist_ok=True)
    path.symlink_to(outside, target_is_directory=outside.is_dir())
    with pytest.raises((WriteRefused, ValueError)):
        migration.prepare(thesis)


def test_unknown_project_field_and_future_generation_refuse(thesis):
    path = thesis / migration.PROJECT_PATH
    original = path.read_bytes()
    project = yaml.safe_load(original)
    project["unmapped_research_fact"] = "must not disappear"
    write_yaml(path, project)
    with pytest.raises(WriteRefused):
        migration.prepare(thesis)
    path.write_bytes(original)
    report = migration.prepare(thesis)
    path = thesis / "system/contracts/data-contract.yaml"
    contract = yaml.safe_load(path.read_text())
    contract["contract_version"] = 63
    write_yaml(path, contract)
    with pytest.raises(WriteRefused, match="retired"):
        commit(thesis, report)


def test_validation_failure_rolls_back_all_changes(thesis, monkeypatch):
    report = migration.prepare(thesis)
    before = snapshot(thesis)
    original = migration._validation_errors
    calls = 0

    def reject_after_apply(root):
        nonlocal calls
        calls += 1
        return original(root) if calls == 1 else ["injected post-write refusal"]

    monkeypatch.setattr(migration, "_validation_errors", reject_after_apply)
    with pytest.raises(TransactionFailure, match="injected"):
        commit(thesis, report)
    assert calls == 2 and snapshot(thesis) == before
    assert not (thesis / migration.MARKER).exists()
    assert not list((thesis / "operations/transactions").glob("transaction-*.yaml"))
    assert load_revisions(thesis) == {}
    assert not (thesis / migration.BASE).exists()


def test_uncertain_receipt_reconciles_without_second_commit(thesis, monkeypatch):
    import learning_os.store.transactions as engine
    from learning_os.domain.failures import TransactionPublicationUncertain

    report = migration.prepare(thesis)
    real_write = engine.atomic_write_bytes
    fired = False

    def uncertain_receipt(path, data):
        nonlocal fired
        real_write(path, data)
        if path.parent == thesis / "operations/transactions" and path.name.startswith("transaction-"):
            fired = True
            raise OSError("receipt directory synchronization uncertain")

    monkeypatch.setattr(engine, "atomic_write_bytes", uncertain_receipt)
    with pytest.raises(TransactionPublicationUncertain):
        commit(thesis, report)
    assert fired and not (thesis / migration.PROJECT_PATH).exists()
    monkeypatch.setattr(engine, "atomic_write_bytes", real_write)
    reconcile_inflight_transactions(thesis)
    again = commit(thesis, report)
    assert again["replayed"]
    assert len(list((thesis / "operations/transactions").glob("transaction-*.yaml"))) == 1


@pytest.mark.parametrize("aliases", [
    {"project-old": "project-old"},
    {"project-old": "module-demo", "project-older": "project-old"},
    {"module-demo": migration.PROJECT},
    {"workstream-thesis-landscape": "workspace-demo"},
    {"project-old": "workspace-missing"},
])
def test_invalid_aliases_fail_closed(thesis, aliases):
    write_yaml(thesis / migration.ALIASES_PATH, {"aliases": aliases})
    issues = validate(load_repo(thesis))
    assert any(issue.severity == "E" and issue.code in {"PROJECT-ALIAS", "REF-PROJECT"}
               for issue in issues)
