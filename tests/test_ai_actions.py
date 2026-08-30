"""First provider-independent AI-action vertical slice: garden.shelve."""

from __future__ import annotations

import hashlib
import json
import shutil
from datetime import UTC, datetime
from pathlib import Path

import pytest
import yaml

from learning_os.ai_actions import (
    ActionPolicyError,
    AIActionService,
    DeliveryValidationError,
    StaleDeliveryError,
)
from learning_os.contracts import validate_contract
from learning_os.contracts.gateway import (
    GatewayRequestContext,
    gateway_request_context,
    intent_sha256,
)
from learning_os.fingerprint import canonical_fingerprint
from learning_os.transactions import TransactionFailure, TransactionService, artifact_revision

ROOT = Path(__file__).resolve().parent.parent
FIXED = datetime(2026, 8, 4, 1, 0, tzinfo=UTC)


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
        "operations/ai-actions/garden-state",
        "knowledge/garden",
    ):
        (mini_repo / rel).mkdir(parents=True, exist_ok=True)
    (mini_repo / "knowledge/garden/handwritten-import-registration.md").write_text(
        "# Import registration\n\nThe decorator stores the function during import. #python #optimizer\n",
        encoding="utf-8",
    )
    write_yaml(mini_repo / "operations/ai-actions/relationships.yaml", {
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


def apply_approved_delivery(
    app: AIActionService,
    delivery_id: str,
    *,
    idempotency_key: str | None = None,
    expected_snapshot: str | None = None,
    expected_revisions: dict[str, int] | None = None,
):
    """Exercise the same content-bound authority the public V2 gateway supplies."""
    delivery, directory = app.repository.get_delivery(delivery_id)
    request = app.repository.get_request(str(delivery["request_id"]))
    target_id = str(request["target"]["id"])
    artifact_ids = {target_id}
    artifact_hashes: dict[str, str] = {}
    for operation in delivery["operations"]:
        ref = operation.get("artifact_ref")
        if ref:
            path = directory / str(ref)
            artifact_hashes[str(ref)] = "sha256:" + hashlib.sha256(
                path.read_bytes()
            ).hexdigest()
        if operation["capability"] == "garden.add-transcription":
            artifact_ids.add(f"transcription-{target_id}")
        elif operation["capability"] == "relationship.create":
            artifact_ids.add(str(operation["payload"]["id"]))
        elif operation["capability"] == "unit.material-synthesis.publish":
            record = yaml.safe_load((directory / str(ref)).read_text(encoding="utf-8"))
            artifact_ids.add(str(record["id"]))
    delivery_hash = "sha256:" + hashlib.sha256(
        (directory / "delivery.yaml").read_bytes()
    ).hexdigest()
    expected_revisions = expected_revisions or {
        artifact_id: artifact_revision(app.root, artifact_id)
        for artifact_id in sorted(artifact_ids)
    }
    envelope = {
        "schema_version": 2,
        "request_id": f"apply-{delivery_id}",
        "idempotency_key": idempotency_key or f"apply-{delivery_id}",
        "capability": "ai-action.delivery.apply",
        "channel": "operator",
        "expected_snapshot": expected_snapshot or f"sha256:{canonical_fingerprint(app.root)}",
        "expected_revisions": expected_revisions,
        "approval": {
            "kind": "approved-delivery",
            "subject_sha256": "sha256:" + "0" * 64,
        },
        "payload": {
            "delivery_id": delivery_id,
            "delivery_sha256": delivery_hash,
            "artifact_sha256": artifact_hashes,
        },
    }
    envelope["approval"]["subject_sha256"] = intent_sha256(envelope)
    context = GatewayRequestContext(
        request_id=envelope["request_id"],
        idempotency_key=envelope["idempotency_key"],
        capability=envelope["capability"],
        channel=envelope["channel"],
        intent_sha256=envelope["approval"]["subject_sha256"],
        approval_kind="approved-delivery",
        approval_subject_sha256=envelope["approval"]["subject_sha256"],
    )
    with gateway_request_context(context):
        return app.apply_delivery(
            delivery_id,
            delivery_sha256=delivery_hash,
            artifact_sha256=artifact_hashes,
            expected_snapshot=envelope["expected_snapshot"],
            expected_revisions=expected_revisions,
        )


def test_registry_and_manifest_projection_are_additive(ai_repo: Path):
    app = service(ai_repo)
    assert [row["id"] for row in app.list_actions()] == [
        "garden.shelve", "unit.compare-materials",
    ]
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


def test_prepare_writes_exact_bounded_bundle_without_external_repository_access(
    ai_repo: Path,
):
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
    allowed = (bundle / "allowed-capabilities.json").read_text(encoding="utf-8")
    assert "repository.read-external" not in allowed
    assert request["confidentiality"] == {
        "classification": "private",
        "external_repository_access": False,
    }
    assert request["preconditions"]["snapshot_id"].startswith("sha256:")


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
    receipt = apply_approved_delivery(app, delivery["id"])
    assert hashlib.sha256(original.read_bytes()).hexdigest() == before
    assert receipt["status"] == "committed"
    assert receipt["schema_version"] == 2
    assert receipt["capability"] == "ai-action.delivery.apply"
    assert receipt["request"]["approval"]["kind"] == "approved-delivery"
    assert {row["capability"] for row in receipt["authority"]["grants"]} == {
        "ai-action.delivery.apply", "garden.add-transcription", "garden.update",
        "relationship.create",
    }
    assert receipt["snapshot_before"] != receipt["snapshot_after"]
    assert receipt["metadata"]["deleted_ids"] == []
    assert receipt["receipt_path"].startswith("operations/transactions/")
    assert (ai_repo / receipt["receipt_path"]).is_file()
    validate_contract(
        ai_repo,
        "transaction-receipt.schema.json",
        yaml.safe_load((ai_repo / receipt["receipt_path"]).read_text(encoding="utf-8")),
        label="AI transaction receipt",
    )
    assert artifact_revision(ai_repo, target_id(ai_repo)) == 1
    assert (ai_repo / f"knowledge/garden/transcriptions/{target_id(ai_repo)}.md").is_file()
    state = yaml.safe_load(app.repository.state_path(target_id(ai_repo)).read_text())
    assert state["title"] == "Import-Time Registration"
    assert state["state"] == "developing"
    relations = yaml.safe_load((ai_repo / "operations/ai-actions/relationships.yaml").read_text())
    assert relations["relationships"][0]["to"]["id"] == "module-demo"
    request_state = app.request_status(request["id"])
    assert request_state["status"] == "completed"
    assert request_state["receipt_id"] == receipt["id"]
    manifest = json.loads((ai_repo / "generated/manifest.json").read_text(encoding="utf-8"))
    assert manifest["ai_actions"]["requests"][0]["status"] == "completed"
    assert manifest["garden_entries"][0]["transcription_path"].startswith(
        "knowledge/garden/transcriptions/"
    )


def test_replay_refuses_a_delegated_grant_its_bound_delivery_never_used(
    ai_repo: Path, tmp_path: Path
):
    """A tampered receipt cannot buy a domain grant its own delivery never proves.

    ``ai-action.delivery.apply`` may legitimately delegate to several domain
    capabilities, but only the ones its hash-verified delivery actually named
    as operations. Appending a real, catalogue-valid grant for a capability
    this delivery never used (here ``unit.material-synthesis.publish``, which
    the ``garden.shelve`` delivery in ``make_delivery`` never names) must be
    refused on replay, never accepted because the grant happens to be real.
    """
    app, request, source = make_delivery(ai_repo, tmp_path)
    delivery = app.import_delivery(source)
    tid = target_id(ai_repo)
    snapshot = f"sha256:{canonical_fingerprint(ai_repo)}"
    revisions = {
        artifact_id: artifact_revision(ai_repo, artifact_id)
        for artifact_id in (
            tid, f"transcription-{tid}", "relationship-garden-module-demo",
        )
    }
    receipt = apply_approved_delivery(
        app, delivery["id"], expected_snapshot=snapshot, expected_revisions=revisions,
    )
    receipt_path = ai_repo / receipt["receipt_path"]
    on_disk = yaml.safe_load(receipt_path.read_text(encoding="utf-8"))
    on_disk["authority"]["grants"].append({
        "capability": "unit.material-synthesis.publish",
        "declared_writes": ["curriculum/modules/**/units/**/material-synthesis.yaml"],
    })
    receipt_path.write_text(yaml.safe_dump(on_disk, sort_keys=False), encoding="utf-8")

    # An exact retry must reuse the identical intent — the same explicit
    # expected_snapshot and expected_revisions the first call bound its
    # approval to — so this call reaches replay-evidence validation rather
    # than a stale-intent refusal.
    with pytest.raises(DeliveryValidationError, match="does not prove"):
        apply_approved_delivery(
            app, delivery["id"], expected_snapshot=snapshot, expected_revisions=revisions,
        )


def test_an_untampered_ai_action_replay_still_returns_its_original_receipt(
    ai_repo: Path, tmp_path: Path
):
    """Proving delegation must not break the legitimate exact retry.

    Delegated grants are now re-derived by re-reading the bound delivery, so
    this pins the other side of that change: an untouched receipt still
    replays, returns the same transaction, and re-runs nothing.
    """
    app, _request, source = make_delivery(ai_repo, tmp_path)
    delivery = app.import_delivery(source)
    tid = target_id(ai_repo)
    snapshot = f"sha256:{canonical_fingerprint(ai_repo)}"
    revisions = {
        artifact_id: artifact_revision(ai_repo, artifact_id)
        for artifact_id in (
            tid, f"transcription-{tid}", "relationship-garden-module-demo",
        )
    }
    first = apply_approved_delivery(
        app, delivery["id"], expected_snapshot=snapshot, expected_revisions=revisions,
    )
    replayed = apply_approved_delivery(
        app, delivery["id"], expected_snapshot=snapshot, expected_revisions=revisions,
    )
    assert replayed["id"] == first["id"]
    assert replayed["receipt_path"] == first["receipt_path"]
    assert artifact_revision(ai_repo, tid) == 1, "an exact replay must not re-apply the write"


def test_replay_refuses_a_receipt_repointed_at_another_real_delivery(
    ai_repo: Path, tmp_path: Path
):
    """Naming a real delivery is not the same as naming *this* one.

    ``metadata.delivery_id`` is part of the evidence under review, so a
    tampered receipt could point at a different, genuinely-present delivery
    whose operations carry the capability it wants proven — every hash would
    check out. The delivery's request must therefore match the request record
    this transaction actually wrote.
    """
    app, _request, source = make_delivery(ai_repo, tmp_path)
    delivery = app.import_delivery(source)
    tid = target_id(ai_repo)
    snapshot = f"sha256:{canonical_fingerprint(ai_repo)}"
    revisions = {
        artifact_id: artifact_revision(ai_repo, artifact_id)
        for artifact_id in (
            tid, f"transcription-{tid}", "relationship-garden-module-demo",
        )
    }
    receipt = apply_approved_delivery(
        app, delivery["id"], expected_snapshot=snapshot, expected_revisions=revisions,
    )

    # A second, genuinely-present delivery belonging to a different request.
    other_dir = app.repository.delivery_dir("ai-delivery-other-001")
    shutil.copytree(app.repository.delivery_dir(delivery["id"]), other_dir)
    other = yaml.safe_load((other_dir / "delivery.yaml").read_text(encoding="utf-8"))
    other["id"] = "ai-delivery-other-001"
    other["request_id"] = "ai-request-other-001"
    write_yaml(other_dir / "delivery.yaml", other)

    receipt_path = ai_repo / receipt["receipt_path"]
    on_disk = yaml.safe_load(receipt_path.read_text(encoding="utf-8"))
    on_disk["metadata"]["delivery_id"] = "ai-delivery-other-001"
    on_disk["metadata"]["approved_delivery"]["delivery_sha256"] = "sha256:" + hashlib.sha256(
        (other_dir / "delivery.yaml").read_bytes()
    ).hexdigest()
    receipt_path.write_text(yaml.safe_dump(on_disk, sort_keys=False), encoding="utf-8")

    with pytest.raises(DeliveryValidationError, match="different request"):
        apply_approved_delivery(
            app, delivery["id"], expected_snapshot=snapshot, expected_revisions=revisions,
        )


def test_replay_refuses_a_receipt_naming_an_unsafe_delivery_id(
    ai_repo: Path, tmp_path: Path
):
    """An id the schema allows but the repository refuses must fail closed.

    The receipt schema's `safeArtifactId` accepts a two-character id, while
    the exchange-identifier rule requires three. Resolving it therefore raises
    an AI-action error from inside replay-evidence validation, which must
    surface as an ordinary typed refusal rather than escaping the gateway as
    an unhandled traceback.
    """
    app, _request, source = make_delivery(ai_repo, tmp_path)
    delivery = app.import_delivery(source)
    tid = target_id(ai_repo)
    snapshot = f"sha256:{canonical_fingerprint(ai_repo)}"
    revisions = {
        artifact_id: artifact_revision(ai_repo, artifact_id)
        for artifact_id in (
            tid, f"transcription-{tid}", "relationship-garden-module-demo",
        )
    }
    receipt = apply_approved_delivery(
        app, delivery["id"], expected_snapshot=snapshot, expected_revisions=revisions,
    )
    receipt_path = ai_repo / receipt["receipt_path"]
    on_disk = yaml.safe_load(receipt_path.read_text(encoding="utf-8"))
    on_disk["metadata"]["delivery_id"] = "ab"
    receipt_path.write_text(yaml.safe_dump(on_disk, sort_keys=False), encoding="utf-8")

    with pytest.raises(DeliveryValidationError, match="cannot re-verify the delivery"):
        apply_approved_delivery(
            app, delivery["id"], expected_snapshot=snapshot, expected_revisions=revisions,
        )


def test_import_rolls_back_delivery_if_request_transition_fails(
    ai_repo: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    app, request, source = make_delivery(ai_repo, tmp_path)
    request_path = app.repository.request_path(request["id"])
    before = request_path.read_bytes()

    def fail_update(_request):
        raise OSError("synthetic request update failure")

    monkeypatch.setattr(app.repository, "update_request", fail_update)
    with pytest.raises(OSError, match="synthetic request update failure"):
        app.import_delivery(source)

    assert request_path.read_bytes() == before
    assert not app.repository.delivery_dir("ai-delivery-test-001").exists()


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
    receipt = apply_approved_delivery(app, delivery["id"])
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
    apply_approved_delivery(app, app.import_delivery(source)["id"])
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
        apply_approved_delivery(app, app.import_delivery(second)["id"])
    assert transcription.read_text(encoding="utf-8") == first

    third = tmp_path / "third-delivery"
    shutil.copytree(second, third)
    body["id"] = "ai-delivery-test-003"
    body["operations"][0]["supersedes"] = f"transcription-{tid}"
    write_yaml(third / "delivery.yaml", body)
    receipt = apply_approved_delivery(app, app.import_delivery(third)["id"])
    assert receipt["metadata"]["superseded_ids"] == [f"transcription-{tid}"]
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
    registry = ai_repo / "operations/ai-actions/relationships.yaml"
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
    receipt = apply_approved_delivery(app, app.import_delivery(source)["id"])
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
        apply_approved_delivery(app, delivery["id"])
    assert not (ai_repo / f"knowledge/garden/transcriptions/{target_id(ai_repo)}.md").exists()


def test_garden_state_bookkeeping_is_not_exempt_from_its_declared_scope(
        ai_repo: Path, tmp_path: Path):
    """garden.update's only destination must be checked, not blanket-exempted."""
    contract = ai_repo / "system/contracts/capabilities.yaml"
    value = yaml.safe_load(contract.read_text(encoding="utf-8"))
    value["domain_capabilities"]["garden.update"]["writes"] = [
        "operations/ai-actions/somewhere-else/"
    ]
    write_yaml(contract, value)
    app, _request, source = make_delivery(ai_repo, tmp_path)
    delivery = app.import_delivery(source)
    with pytest.raises(DeliveryValidationError, match="garden.update may not write"):
        apply_approved_delivery(app, delivery["id"])
    assert not any(app.repository.garden_state.glob("*.yaml"))


def test_approved_delivery_request_status_uses_the_outer_capability_scope(
        ai_repo: Path, tmp_path: Path):
    contract = ai_repo / "system/contracts/capabilities.yaml"
    value = yaml.safe_load(contract.read_text(encoding="utf-8"))
    value["commands"]["ai-action.delivery.apply"]["writes"] = [
        "operations/ai-actions/somewhere-else/**"
    ]
    write_yaml(contract, value)
    app, _request, source = make_delivery(ai_repo, tmp_path)
    delivery = app.import_delivery(source)
    with pytest.raises(DeliveryValidationError, match="ai-action.delivery.apply may not write"):
        apply_approved_delivery(app, delivery["id"])
    assert not (
        ai_repo / f"knowledge/garden/transcriptions/{target_id(ai_repo)}.md"
    ).exists()


def test_approved_delivery_stages_only_hash_verified_artifact_bytes(
        ai_repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    app, _request, source = make_delivery(ai_repo, tmp_path)
    delivery = app.import_delivery(source)
    _record, directory = app.repository.get_delivery(delivery["id"])
    artifact = directory / "artifacts/transcription.md"
    approved_bytes = artifact.read_bytes()
    captured: dict[Path, str | bytes] = {}

    original_target_check = app._assert_target_unchanged
    target_checks = 0

    def mutate_after_verified_read(request):
        nonlocal target_checks
        target = original_target_check(request)
        target_checks += 1
        if target_checks == 1:
            artifact.write_bytes(b"unapproved race content\n")
        return target

    original_scope_check = app._assert_in_scope

    def restore_before_final_hash(capability, path, scopes=None):
        artifact.write_bytes(approved_bytes)
        return original_scope_check(capability, path, scopes)

    def stop_before_write(_service, **kwargs):
        captured.update(kwargs["writes"])
        raise TransactionFailure("synthetic stop before write")

    monkeypatch.setattr(app, "_assert_target_unchanged", mutate_after_verified_read)
    monkeypatch.setattr(app, "_assert_in_scope", restore_before_final_hash)
    monkeypatch.setattr(TransactionService, "commit", stop_before_write)

    with pytest.raises(DeliveryValidationError, match="synthetic stop before write"):
        apply_approved_delivery(app, delivery["id"])
    transcription = next(
        content for path, content in captured.items()
        if "transcriptions" in path.parts
    )
    assert "The decorator factory receives the family first" in str(transcription)
    assert "unapproved race content" not in str(transcription)


def test_garden_update_fields_are_enforced_from_the_catalogue(
        ai_repo: Path, tmp_path: Path):
    contract = ai_repo / "system/contracts/capabilities.yaml"
    value = yaml.safe_load(contract.read_text(encoding="utf-8"))
    value["domain_capabilities"]["garden.update"]["allowed_fields"] = ["title"]
    write_yaml(contract, value)
    app, _request, source = make_delivery(ai_repo, tmp_path)
    delivery = app.import_delivery(source)
    with pytest.raises(DeliveryValidationError, match="forbidden fields.*state"):
        apply_approved_delivery(app, delivery["id"])

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
