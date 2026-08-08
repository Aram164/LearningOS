"""First provider-independent AI-action vertical slice: garden.shelve."""

from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

import pytest
import yaml

from learning_os.ai_actions import (
    ActionPolicyError,
    AIActionService,
    ConfidentialityError,
    DeliveryValidationError,
    StaleDeliveryError,
)

ROOT = Path(__file__).resolve().parent.parent
FIXED = datetime(2026, 8, 4, 1, 0, tzinfo=timezone.utc)


def write_yaml(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(value, sort_keys=False, allow_unicode=True), encoding="utf-8")


@pytest.fixture()
def ai_repo(mini_repo: Path) -> Path:
    shutil.copytree(
        ROOT / "system" / "contracts",
        mini_repo / "system" / "contracts",
        dirs_exist_ok=True,
    )
    for rel in (
        "operations/ai-actions/requests",
        "operations/ai-actions/deliveries",
        "operations/ai-actions/receipts",
        "operations/ai-actions/garden-state",
        "knowledge/garden",
    ):
        (mini_repo / rel).mkdir(parents=True, exist_ok=True)
    (mini_repo / "knowledge/garden/handwritten-import-registration.md").write_text(
        "# Import registration\n\nThe decorator stores the function during import. #python #optimizer\n",
        encoding="utf-8",
    )
    write_yaml(mini_repo / "knowledge/relationships.yaml", {
        "schema_version": 1,
        "relationships": [],
    })
    return mini_repo


def service(root: Path) -> AIActionService:
    return AIActionService(root, clock=lambda: FIXED)


def target_id(root: Path) -> str:
    [target] = service(root).list_garden_targets()
    return target["id"]


def make_delivery(root: Path, tmp_path: Path, *, capability: str | None = None):
    app = service(root)
    tid = target_id(root)
    request = app.prepare(
        action_id="garden.shelve",
        target_kind="garden-note",
        target_id=tid,
        provider="manual-bundle",
        request_id="ai-request-test-001",
    )
    source = tmp_path / "approved-delivery"
    (source / "artifacts").mkdir(parents=True)
    (source / "artifacts/transcription.md").write_text(
        "The decorator factory receives the family first; its returned decorator later receives the function.\n",
        encoding="utf-8",
    )
    operations = [
        {
            "capability": capability or "garden.add-transcription",
            "target_id": tid,
            "artifact_ref": "artifacts/transcription.md",
        },
        {
            "capability": "garden.update",
            "target_id": tid,
            "patch": {"title": "Import-Time Registration", "state": "developing"},
        },
        {
            "capability": "relationship.create",
            "payload": {
                "id": "relationship-garden-module-demo",
                "from": {"kind": "garden-note", "id": tid},
                "relation": "supports",
                "to": {"kind": "module", "id": "module-demo"},
            },
        },
    ]
    write_yaml(source / "delivery.yaml", {
        "schema_version": 1,
        "id": "ai-delivery-test-001",
        "type": "ai-action-delivery",
        "request_id": request["id"],
        "action_id": "garden.shelve",
        "status": "ready",
        "producer": {"provider": "manual", "adapter": "manual-bundle"},
        "approval": {"user_approved": True, "approved_at": "2026-08-04T01:00:00+00:00"},
        "operations": operations,
        "preconditions": request["preconditions"],
    })
    return app, request, source


def test_registry_and_manifest_projection_are_additive(ai_repo: Path):
    app = service(ai_repo)
    assert [row["id"] for row in app.list_actions()] == ["garden.shelve"]
    projection = app.manifest_projection()
    assert projection["ai_actions"]["contract_version"] == 1
    adapters = projection["ai_actions"]["provider_adapters"]
    # The projection is additive: consumers key on id + available, and the
    # adapter identity travels alongside the provider name.
    assert adapters[0]["id"] == "manual-bundle"
    assert adapters[0]["available"] is True
    assert adapters[0]["adapter"] == "manual-bundle"
    assert {row["id"]: row["available"] for row in adapters} == {
        "manual-bundle": True, "claude": False, "chatgpt": False,
    }
    assert projection["garden_entries"][0]["type"] == "garden-note"


def test_prepare_writes_exact_bounded_bundle_without_job(ai_repo: Path):
    app = service(ai_repo)
    tid = target_id(ai_repo)
    request = app.prepare(
        action_id="garden.shelve", target_kind="garden-note", target_id=tid,
        request_id="ai-request-bounded",
    )
    bundle = app.repository.request_dir(request["id"])
    assert (bundle / "request.yaml").is_file()
    assert (bundle / "context.md").is_file()
    assert (bundle / "attachments/handwritten-import-registration.md").is_file()
    assert (bundle / "allowed-capabilities.json").is_file()
    assert not any("Job" in path.parts for path in bundle.rglob("*"))
    assert "repository.read-job" not in (bundle / "allowed-capabilities.json").read_text()
    assert request["preconditions"]["snapshot_id"].startswith("sha256:")


def test_job_derived_export_requires_explicit_confirmation(ai_repo: Path):
    app = service(ai_repo)
    tid = target_id(ai_repo)
    write_yaml(app.repository.state_path(tid), {"id": tid, "job_derived": True})
    with pytest.raises(ConfidentialityError):
        app.prepare(
            action_id="garden.shelve", target_kind="garden-note", target_id=tid,
            request_id="ai-request-job",
        )
    request = app.prepare(
        action_id="garden.shelve", target_kind="garden-note", target_id=tid,
        request_id="ai-request-job-confirmed", job_export_confirmed=True,
    )
    assert request["confidentiality"]["export_confirmed"] is True
    assert request["confidentiality"]["employer_repository_access"] is False


def test_forbidden_capability_is_rejected_and_import_cleaned(ai_repo: Path, tmp_path: Path):
    app, _request, source = make_delivery(ai_repo, tmp_path, capability="artifact.delete")
    with pytest.raises(DeliveryValidationError):
        app.import_delivery(source)
    assert not app.repository.delivery_dir("ai-delivery-test-001").exists()


def test_stale_delivery_is_rejected(ai_repo: Path, tmp_path: Path):
    app, _request, source = make_delivery(ai_repo, tmp_path)
    note = ai_repo / "knowledge/garden/handwritten-import-registration.md"
    note.write_text(note.read_text(encoding="utf-8") + "\nChanged after preparation.\n", encoding="utf-8")
    with pytest.raises(StaleDeliveryError):
        app.import_delivery(source)
    assert not app.repository.delivery_dir("ai-delivery-test-001").exists()


def test_full_round_trip_preserves_original_and_commits_receipt(ai_repo: Path, tmp_path: Path):
    original = ai_repo / "knowledge/garden/handwritten-import-registration.md"
    before = hashlib.sha256(original.read_bytes()).hexdigest()
    app, request, source = make_delivery(ai_repo, tmp_path)
    delivery = app.import_delivery(source)
    assert app.request_status(request["id"])["status"] == "delivery-ready"
    receipt = app.apply_delivery(delivery["id"])
    assert hashlib.sha256(original.read_bytes()).hexdigest() == before
    assert receipt["status"] == "committed"
    assert receipt["pre_snapshot"] != receipt["post_snapshot"]
    assert receipt["deleted_ids"] == []
    assert (ai_repo / f"knowledge/garden/transcriptions/{target_id(ai_repo)}.md").is_file()
    state = yaml.safe_load(app.repository.state_path(target_id(ai_repo)).read_text())
    assert state["title"] == "Import-Time Registration"
    assert state["state"] == "developing"
    relations = yaml.safe_load((ai_repo / "knowledge/relationships.yaml").read_text())
    assert relations["relationships"][0]["to"]["id"] == "module-demo"
    request_state = app.request_status(request["id"])
    assert request_state["status"] == "completed"
    assert request_state["receipt_id"] == receipt["id"]
    manifest = json.loads((ai_repo / "generated/manifest.json").read_text(encoding="utf-8"))
    assert manifest["ai_actions"]["requests"][0]["status"] == "completed"
    assert manifest["garden_entries"][0]["transcription_path"].startswith(
        "knowledge/garden/transcriptions/"
    )


# --------------------------------------------------------------- regressions
# Each test below pins one defect found in the 2026-08-04 audit of this slice.

def test_garden_identity_does_not_depend_on_sibling_files(ai_repo: Path):
    """Adding an unrelated note must never rename an already-shelved one.

    Identity keys garden-state, transcriptions, receipts and relationship
    endpoints; a positional id silently orphans all of them.
    """
    app = service(ai_repo)
    before = target_id(ai_repo)
    nested = ai_repo / "knowledge/garden/topic"
    nested.mkdir(parents=True, exist_ok=True)
    (nested / "handwritten-import-registration.md").write_text(
        "# Unrelated\n\nDifferent note that happens to share a stem.\n", encoding="utf-8")
    ids = {row["path"]: row["id"] for row in app.list_garden_targets()}
    assert ids["knowledge/garden/handwritten-import-registration.md"] == before
    assert len(set(ids.values())) == 2


def test_unrelated_repository_edit_does_not_invalidate_a_delivery(ai_repo: Path, tmp_path: Path):
    """Staleness is scoped to the target, not to the whole repository."""
    app, _request, source = make_delivery(ai_repo, tmp_path)
    note = ai_repo / "knowledge/notes/mathematics/note-demo.md"
    note.write_text(note.read_text(encoding="utf-8") + "\nAn unrelated sentence.\n",
                    encoding="utf-8")
    delivery = app.import_delivery(source)
    receipt = app.apply_delivery(delivery["id"])
    assert receipt["status"] == "committed"


def test_core_refuses_a_provider_with_no_available_adapter(ai_repo: Path):
    """The adapter boundary is enforced by the core, not only by the UI."""
    app = service(ai_repo)
    with pytest.raises(ActionPolicyError, match="no available adapter"):
        app.prepare(action_id="garden.shelve", target_kind="garden-note",
                    target_id=target_id(ai_repo), provider="claude",
                    request_id="ai-request-no-adapter")


def test_registry_drives_implementation_status(ai_repo: Path):
    """A registered but unbuilt action refuses from contract data, not a literal."""
    write_yaml(ai_repo / "system/contracts/ai-actions/resource.place.yaml", {
        "schema_version": 1, "id": "resource.place", "title": "Place with AI",
        "target_kinds": ["garden-note"], "interaction_mode": "discussion",
        "approval_required": True, "context_selection": "exact", "status": "planned",
        "supported_providers": ["manual-bundle"],
        "allowed_capabilities": ["relationship.create"], "forbidden_capabilities": [],
    })
    app = service(ai_repo)
    assert "resource.place" in [row["id"] for row in app.list_actions()]
    with pytest.raises(ActionPolicyError, match="declared planned"):
        app.prepare(action_id="resource.place", target_kind="garden-note",
                    target_id=target_id(ai_repo), request_id="ai-request-planned")


def test_reshelving_will_not_silently_replace_a_transcription(ai_repo: Path, tmp_path: Path):
    """A second reading of the same seed must supersede explicitly and be receipted."""
    app, _request, source = make_delivery(ai_repo, tmp_path)
    app.apply_delivery(app.import_delivery(source)["id"])
    tid = target_id(ai_repo)
    transcription = ai_repo / f"knowledge/garden/transcriptions/{tid}.md"
    first = transcription.read_text(encoding="utf-8")

    second = tmp_path / "second-delivery"
    (second / "artifacts").mkdir(parents=True)
    (second / "artifacts/transcription.md").write_text("A revised reading.\n", encoding="utf-8")
    request2 = app.prepare(action_id="garden.shelve", target_kind="garden-note",
                           target_id=tid, provider="manual-bundle",
                           request_id="ai-request-test-002")
    body = {
        "schema_version": 1, "id": "ai-delivery-test-002", "type": "ai-action-delivery",
        "request_id": request2["id"], "action_id": "garden.shelve", "status": "ready",
        "producer": {"provider": "manual", "adapter": "manual-bundle"},
        "approval": {"user_approved": True, "approved_at": "2026-08-04T01:00:00+00:00"},
        "operations": [{"capability": "garden.add-transcription", "target_id": tid,
                        "artifact_ref": "artifacts/transcription.md"}],
        "preconditions": request2["preconditions"],
    }
    write_yaml(second / "delivery.yaml", body)
    with pytest.raises(DeliveryValidationError, match="already exists"):
        app.apply_delivery(app.import_delivery(second)["id"])
    assert transcription.read_text(encoding="utf-8") == first

    third = tmp_path / "third-delivery"
    shutil.copytree(second, third)
    body["id"] = "ai-delivery-test-003"
    body["operations"][0]["supersedes"] = f"transcription-{tid}"
    write_yaml(third / "delivery.yaml", body)
    receipt = app.apply_delivery(app.import_delivery(third)["id"])
    assert receipt["superseded_ids"] == [f"transcription-{tid}"]
    assert "A revised reading." in transcription.read_text(encoding="utf-8")


def test_rejected_delivery_never_lands_in_the_deliveries_directory(ai_repo: Path, tmp_path: Path):
    """Untrusted provider output is quarantined until it validates."""
    app, _request, source = make_delivery(ai_repo, tmp_path, capability="artifact.delete")
    with pytest.raises(DeliveryValidationError):
        app.import_delivery(source)
    assert not app.repository.delivery_dir("ai-delivery-test-001").exists()
    assert list(app.repository.deliveries.glob("*")) == []
    assert not any(app.repository.quarantine.glob("*"))


def test_a_delivery_without_relations_leaves_the_registry_byte_identical(
        ai_repo: Path, tmp_path: Path):
    """An untouched authored file must not be re-serialised by an unrelated apply."""
    registry = ai_repo / "knowledge/relationships.yaml"
    registry.write_text(
        "schema_version: 1\n"
        "# hand-written comment that a YAML round-trip would destroy\n"
        "relationships:\n"
        "  - id: relationship-authored-by-hand\n"
        "    from: {kind: note, id: note-demo}\n"
        "    relation: supports\n"
        "    to: {kind: module, id: module-demo}\n",
        encoding="utf-8")
    before = registry.read_bytes()

    app = service(ai_repo)
    tid = target_id(ai_repo)
    request = app.prepare(action_id="garden.shelve", target_kind="garden-note",
                          target_id=tid, provider="manual-bundle",
                          request_id="ai-request-no-relations")
    source = tmp_path / "no-relation-delivery"
    (source / "artifacts").mkdir(parents=True)
    (source / "artifacts/t.md").write_text("Transcribed.\n", encoding="utf-8")
    write_yaml(source / "delivery.yaml", {
        "schema_version": 1, "id": "ai-delivery-no-relations",
        "type": "ai-action-delivery", "request_id": request["id"],
        "action_id": "garden.shelve", "status": "ready",
        "producer": {"provider": "manual", "adapter": "manual-bundle"},
        "approval": {"user_approved": True, "approved_at": "2026-08-04T01:00:00+00:00"},
        "operations": [{"capability": "garden.add-transcription", "target_id": tid,
                        "artifact_ref": "artifacts/t.md"}],
        "preconditions": request["preconditions"],
    })
    receipt = app.apply_delivery(app.import_delivery(source)["id"])
    assert receipt["status"] == "committed"
    assert registry.read_bytes() == before


def test_capability_write_scope_is_enforced_from_the_contract(ai_repo: Path, tmp_path: Path):
    """Hard rule 12's post-action scope check refuses an out-of-scope write."""
    contract = ai_repo / "system/contracts/capabilities.yaml"
    value = yaml.safe_load(contract.read_text(encoding="utf-8"))
    value["domain_capabilities"]["garden.add-transcription"]["writes"] = ["knowledge/elsewhere/"]
    write_yaml(contract, value)
    app, _request, source = make_delivery(ai_repo, tmp_path)
    delivery = app.import_delivery(source)
    with pytest.raises(DeliveryValidationError, match="may not write"):
        app.apply_delivery(delivery["id"])
    assert not (ai_repo / f"knowledge/garden/transcriptions/{target_id(ai_repo)}.md").exists()

def test_ai_bundle_locks_current_manifest_contract(ai_repo: Path):
    from learning_os.contracts.manifest_contract import declared_version

    app = service(ai_repo)
    request = app.prepare(
        action_id="garden.shelve",
        target_kind="garden-note",
        target_id=target_id(ai_repo),
        provider="manual-bundle",
        request_id="ai-request-contract-lock",
    )

    lock = json.loads(
        (
            app.repository.request_dir(request["id"])
            / "contract-lock.json"
        ).read_text(encoding="utf-8")
    )

    assert (
        lock["manifest_contract_version"]
        == declared_version(ai_repo)
    )
