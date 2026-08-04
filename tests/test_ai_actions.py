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
    shutil.copytree(ROOT / "system" / "contracts", mini_repo / "system" / "contracts")
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
    assert projection["ai_actions"]["provider_adapters"][0] == {
        "id": "manual-bundle", "available": True,
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
