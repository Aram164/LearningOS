from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml
from gateway_helpers import file_sha256
from jsonschema import Draft202012Validator

from learning_os.commands.capability import _classify_failure
from learning_os.commands.support import _read_content_bound_file
from learning_os.contracts.gateway import GatewayRequestContext, intent_sha256
from learning_os.fingerprint import canonical_fingerprint
from learning_os.transactions import TransactionIdempotencyConflict, TransactionService


def _envelope(root: Path, *, text: str = "bounded capture",
              key: str = "capture-v2-001") -> dict:
    envelope = {
        "schema_version": 2,
        "request_id": "request-capture-v2-001",
        "idempotency_key": key,
        "capability": "capture.create",
        "channel": "ui",
        "expected_snapshot": f"sha256:{canonical_fingerprint(root)}",
        "expected_revisions": {f"capture-request:{key}": 0},
        "approval": {
            "kind": "direct-user-gesture",
            "subject_sha256": "sha256:" + "0" * 64,
        },
        "payload": {"text": text},
    }
    envelope["approval"]["subject_sha256"] = intent_sha256(envelope)
    return envelope


def _run(
    repo_root: Path,
    root: Path,
    request_file: Path,
    envelope: dict,
    *,
    stdin: str | None = None,
):
    request_file.write_text(json.dumps(envelope), encoding="utf-8")
    return subprocess.run(
        [
            sys.executable,
            str(repo_root / "tools/los.py"),
            "--root",
            str(root),
            "capability",
            envelope["capability"],
            "--payload-file",
            str(request_file),
        ],
        cwd=repo_root,
        text=True,
        capture_output=True,
        input=stdin,
    )


def test_transaction_service_writes_and_replays_receipt_v2(mini_repo: Path):
    target = mini_repo / "work/inbox/direct-v2.md"
    context = GatewayRequestContext(
        request_id="request-direct-v2",
        idempotency_key="direct-v2-001",
        capability="capture.create",
        channel="codex",
        intent_sha256="sha256:" + "1" * 64,
        approval_kind="operator-approval",
        approval_subject_sha256="sha256:" + "1" * 64,
    )
    service = TransactionService(mini_repo)
    first = service.commit(
        capability="capture.create",
        writes={target: "direct\n"},
        artifact_ids=["capture:direct-v2"],
        expected_revisions={"capture:direct-v2": 0},
        gateway_request=context,
    )
    receipt = yaml.safe_load(first.receipt_path.read_text(encoding="utf-8"))
    assert receipt["schema_version"] == 2
    assert receipt["request"]["idempotency_key"] == context.idempotency_key
    assert receipt["authority"]["grants"] == [{
        "capability": "capture.create",
        "declared_writes": ["work/inbox/**"],
    }]

    replay = service.commit(
        capability="capture.create",
        writes={target: "would not be applied\n"},
        artifact_ids=["capture:direct-v2"],
        expected_revisions={"capture:direct-v2": 0},
        gateway_request=context,
    )
    assert replay.replayed is True
    assert replay.transaction_id == first.transaction_id
    assert target.read_text(encoding="utf-8") == "direct\n"

    conflicting = GatewayRequestContext(
        request_id=context.request_id,
        idempotency_key=context.idempotency_key,
        capability=context.capability,
        channel=context.channel,
        intent_sha256="sha256:" + "2" * 64,
        approval_kind=context.approval_kind,
        approval_subject_sha256="sha256:" + "2" * 64,
    )
    with pytest.raises(TransactionIdempotencyConflict):
        service.commit(
            capability="capture.create",
            writes={target: "conflict\n"},
            artifact_ids=["capture:direct-v2"],
            expected_revisions={"capture:direct-v2": 0},
            gateway_request=conflicting,
        )


def test_transaction_service_refuses_incomplete_v2_revision_authority(mini_repo: Path):
    target = mini_repo / "work/inbox/missing-revision.md"
    context = GatewayRequestContext(
        request_id="request-missing-revision",
        idempotency_key="missing-revision-001",
        capability="capture.create",
        channel="codex",
        intent_sha256="sha256:" + "3" * 64,
        approval_kind="operator-approval",
        approval_subject_sha256="sha256:" + "3" * 64,
    )
    with pytest.raises(Exception, match="cover exactly every transaction artifact"):
        TransactionService(mini_repo).commit(
            capability="capture.create",
            writes={target: "refuse\n"},
            artifact_ids=["capture:missing-revision"],
            expected_revisions={},
            gateway_request=context,
        )
    assert not target.exists()


def test_gateway_v2_receipt_and_exact_retry_are_idempotent(
    mini_repo: Path, repo_root: Path, tmp_path: Path
):
    envelope = _envelope(mini_repo)
    first = _run(repo_root, mini_repo, tmp_path / "request.json", envelope)
    assert first.returncode == 0, first.stderr or first.stdout
    first_response = json.loads(first.stdout)
    assert first_response["schema_version"] == 2
    assert first_response["ok"] is True
    assert first_response["replayed"] is False
    assert first_response["snapshot_after"]

    receipt_path = mini_repo / first_response["receipt_path"]
    receipt = yaml.safe_load(receipt_path.read_text(encoding="utf-8"))
    assert receipt["schema_version"] == 2
    assert receipt["authority"]["enforced"] is True
    assert receipt["request"]["intent_sha256"] == intent_sha256(envelope)
    schema = json.loads(
        (mini_repo / "system/schema/transaction-receipt.schema.json").read_text(
            encoding="utf-8"
        )
    )
    Draft202012Validator(schema).validate(receipt)

    receipts_before = sorted(
        (mini_repo / "operations/transactions").glob("transaction-*.yaml")
    )
    captures_before = sorted((mini_repo / "work/inbox").glob("*.md"))
    second = _run(repo_root, mini_repo, tmp_path / "retry.json", envelope)
    assert second.returncode == 0, second.stderr or second.stdout
    second_response = json.loads(second.stdout)
    assert second_response["replayed"] is True
    assert second_response["transaction_id"] == first_response["transaction_id"]
    assert second_response["receipt_path"] == first_response["receipt_path"]
    assert sorted((mini_repo / "operations/transactions").glob("transaction-*.yaml")) \
        == receipts_before
    assert sorted((mini_repo / "work/inbox").glob("*.md")) == captures_before


def test_gateway_v2_refuses_idempotency_key_reuse_for_changed_intent(
    mini_repo: Path, repo_root: Path, tmp_path: Path
):
    first_envelope = _envelope(mini_repo, text="first")
    first = _run(repo_root, mini_repo, tmp_path / "first.json", first_envelope)
    assert first.returncode == 0, first.stderr or first.stdout

    changed = _envelope(mini_repo, text="different payload")
    changed["expected_snapshot"] = first_envelope["expected_snapshot"]
    changed["approval"]["subject_sha256"] = intent_sha256(changed)
    refused = _run(repo_root, mini_repo, tmp_path / "changed.json", changed)
    assert refused.returncode == 2
    response = json.loads(refused.stdout)
    assert response["ok"] is False
    assert response["error"]["code"] == "IDEMPOTENCY_CONFLICT"


def test_gateway_v2_binds_approval_to_exact_intent(
    mini_repo: Path, repo_root: Path, tmp_path: Path
):
    envelope = _envelope(mini_repo)
    envelope["payload"]["text"] = "changed after approval"
    refused = _run(repo_root, mini_repo, tmp_path / "unapproved.json", envelope)
    assert refused.returncode == 2
    response = json.loads(refused.stdout)
    assert response["error"]["code"] == "UNCONFIRMED"
    assert not list((mini_repo / "work/inbox").glob("*.md"))


def test_gateway_v2_file_payload_requires_an_approved_content_digest(
    mini_repo: Path, repo_root: Path, tmp_path: Path
):
    source = tmp_path / "unbound-input.txt"
    source.write_text("reviewed bytes", encoding="utf-8")
    key = "capture-missing-file-sha-001"
    envelope = _approved_v2(
        mini_repo,
        capability="capture.create",
        payload={"file": str(source)},
        revisions={f"capture-request:{key}": 0},
        key=key,
    )
    refused = _run(repo_root, mini_repo, tmp_path / "missing-file-sha.json", envelope)
    assert refused.returncode == 2
    response = json.loads(refused.stdout)
    assert response["error"]["code"] == "INVALID_REQUEST"
    assert "file_sha256" in response["error"]["message"]
    assert not list((mini_repo / "work/inbox").iterdir())


def test_gateway_v2_never_uses_unapproved_stdin_as_write_content(
    mini_repo: Path, repo_root: Path, tmp_path: Path
):
    key = "capture-unapproved-stdin-001"
    envelope = _approved_v2(
        mini_repo,
        capability="capture.create",
        payload={},
        revisions={f"capture-request:{key}": 0},
        key=key,
    )
    refused = _run(
        repo_root,
        mini_repo,
        tmp_path / "unapproved-stdin.json",
        envelope,
        stdin="bytes outside the approved payload",
    )
    assert refused.returncode == 2
    response = json.loads(refused.stdout)
    assert response["error"]["code"] == "INVALID_REQUEST"
    assert not list((mini_repo / "work/inbox").iterdir())


def test_gateway_v2_refuses_file_mutated_after_approval_before_read(
    mini_repo: Path, repo_root: Path, tmp_path: Path
):
    source = tmp_path / "mutable-input.txt"
    source.write_text("bytes the learner reviewed", encoding="utf-8")
    key = "capture-mutated-file-001"
    envelope = _approved_v2(
        mini_repo,
        capability="capture.create",
        payload={"file": str(source), "file_sha256": file_sha256(source)},
        revisions={f"capture-request:{key}": 0},
        key=key,
    )
    source.write_text("different bytes after approval", encoding="utf-8")

    refused = _run(repo_root, mini_repo, tmp_path / "mutated-file.json", envelope)
    assert refused.returncode == 2
    response = json.loads(refused.stdout)
    assert response["error"]["code"] == "INVALID_REQUEST"
    assert "changed before use" in response["error"]["message"]
    assert "create a new approval" in response["error"]["message"]
    assert not list((mini_repo / "work/inbox").iterdir())
    assert not list((mini_repo / "operations/transactions").glob("transaction-*.yaml"))


def test_gateway_v2_exact_replay_does_not_reopen_external_file(
    mini_repo: Path, repo_root: Path, tmp_path: Path
):
    source = tmp_path / "replay-input.txt"
    source.write_bytes(b"approved replay bytes")
    key = "capture-file-replay-001"
    envelope = _approved_v2(
        mini_repo,
        capability="capture.create",
        payload={"file": str(source), "file_sha256": file_sha256(source)},
        revisions={f"capture-request:{key}": 0},
        key=key,
    )

    first = _run(repo_root, mini_repo, tmp_path / "file-first.json", envelope)
    assert first.returncode == 0, first.stderr or first.stdout
    first_response = json.loads(first.stdout)
    captured = mini_repo / first_response["result"]["captured"]
    assert captured.read_bytes() == b"approved replay bytes"

    source.write_bytes(b"different bytes after the completed transaction")
    replay = _run(repo_root, mini_repo, tmp_path / "file-replay.json", envelope)
    assert replay.returncode == 0, replay.stderr or replay.stdout
    replay_response = json.loads(replay.stdout)
    assert replay_response["replayed"] is True
    assert replay_response["transaction_id"] == first_response["transaction_id"]
    assert captured.read_bytes() == b"approved replay bytes"


def test_verified_file_bytes_cannot_observe_a_later_source_mutation(
    tmp_path: Path,
):
    source = tmp_path / "approved.txt"
    source.write_bytes(b"approved bytes")
    approved_hash = file_sha256(source)
    _path, approved_bytes = _read_content_bound_file(
        str(source), approved_hash, label="test input"
    )
    source.write_bytes(b"mutated after verification")
    assert approved_bytes == b"approved bytes"


def test_gateway_v2_returns_typed_stale_snapshot_refusal(
    mini_repo: Path, repo_root: Path, tmp_path: Path
):
    envelope = _envelope(mini_repo)
    envelope["expected_snapshot"] = "sha256:" + "f" * 64
    envelope["approval"]["subject_sha256"] = intent_sha256(envelope)
    refused = _run(repo_root, mini_repo, tmp_path / "stale.json", envelope)
    assert refused.returncode == 3
    response = json.loads(refused.stdout)
    assert response["error"]["code"] == "STALE_SNAPSHOT"
    assert response["error"]["retryable"] is True
    assert not list((mini_repo / "work/inbox").glob("*.md"))


def test_gateway_v2_classifies_in_lock_snapshot_race_as_stale_snapshot():
    error = _classify_failure(
        3,
        "approved delivery snapshot changed before commit",
    )
    assert error["code"] == "STALE_SNAPSHOT"
    assert error["retryable"] is True


def test_gateway_v2_returns_typed_unknown_capability(
    mini_repo: Path, repo_root: Path, tmp_path: Path
):
    envelope = _envelope(mini_repo)
    envelope["capability"] = "unknown.write"
    envelope["approval"]["subject_sha256"] = intent_sha256(envelope)
    refused = _run(repo_root, mini_repo, tmp_path / "unknown.json", envelope)
    assert refused.returncode == 2
    response = json.loads(refused.stdout)
    assert response["ok"] is False
    assert response["error"]["code"] == "UNKNOWN_CAPABILITY"


def test_gateway_v2_rejects_duplicate_payload_approval(
    mini_repo: Path, repo_root: Path, tmp_path: Path
):
    envelope = _envelope(mini_repo)
    envelope["payload"]["approve"] = True
    envelope["approval"]["subject_sha256"] = intent_sha256(envelope)
    refused = _run(repo_root, mini_repo, tmp_path / "duplicate-approval.json", envelope)
    assert refused.returncode == 2
    response = json.loads(refused.stdout)
    assert response["error"]["code"] == "INVALID_REQUEST"
    assert "belongs only in the envelope" in response["error"]["message"]


def _legacy_lock() -> dict:
    return {
        "schema_version": 1,
        "id": "legacy-archive-lock",
        "type": "legacy-archive-lock",
        "created_at": "2026-08-25T12:00:00+00:00",
        "entries": [],
        "excluded": {"count": 1, "status": "sealed-not-inspected"},
        "verification": {
            "verified_at": "2026-08-25T12:00:00+00:00",
            "status": "verified",
            "issues": [],
        },
    }


def _approved_v2(root: Path, *, capability: str, payload: dict,
                 revisions: dict[str, int], key: str) -> dict:
    envelope = {
        "schema_version": 2,
        "request_id": f"request-{key}",
        "idempotency_key": key,
        "capability": capability,
        "channel": "codex",
        "expected_snapshot": f"sha256:{canonical_fingerprint(root)}",
        "expected_revisions": revisions,
        "approval": {
            "kind": "operator-approval",
            "subject_sha256": "sha256:" + "0" * 64,
        },
        "payload": payload,
    }
    envelope["approval"]["subject_sha256"] = intent_sha256(envelope)
    return envelope


def test_vnext_v2_approval_binds_inline_record_and_needs_no_payload_boolean(
    mini_repo: Path, repo_root: Path, tmp_path: Path
):
    envelope = _approved_v2(
        mini_repo,
        capability="legacy.archive.lock.publish",
        payload={"record": _legacy_lock()},
        revisions={"legacy-archive-lock": 0},
        key="legacy-inline-001",
    )
    applied = _run(repo_root, mini_repo, tmp_path / "legacy-inline.json", envelope)
    assert applied.returncode == 0, applied.stderr or applied.stdout
    response = json.loads(applied.stdout)
    assert response["ok"] is True
    assert response["transaction_id"]
    receipt = yaml.safe_load((mini_repo / response["receipt_path"]).read_text())
    assert receipt["schema_version"] == 2
    assert receipt["request"]["intent_sha256"] == intent_sha256(envelope)


def test_vnext_v2_refuses_file_path_as_approval_subject(
    mini_repo: Path, repo_root: Path, tmp_path: Path
):
    draft = tmp_path / "mutable-lock.yaml"
    draft.write_text(yaml.safe_dump(_legacy_lock()), encoding="utf-8")
    envelope = _approved_v2(
        mini_repo,
        capability="legacy.archive.lock.publish",
        payload={"file": str(draft)},
        revisions={"legacy-archive-lock": 0},
        key="legacy-file-001",
    )
    refused = _run(repo_root, mini_repo, tmp_path / "legacy-file.json", envelope)
    assert refused.returncode == 2
    response = json.loads(refused.stdout)
    assert response["error"]["code"] == "INVALID_REQUEST"
    assert "requires an inline record" in response["error"]["message"]
    assert not (mini_repo / "operations/legacy/archive-lock.yaml").exists()


def test_vnext_direct_cli_cannot_create_a_receipt_v1(
    mini_repo: Path, repo_root: Path
):
    result = subprocess.run(
        [
            sys.executable,
            str(repo_root / "tools/los.py"),
            "--root", str(mini_repo),
            "legacy-archive-lock-publish",
            "--record", json.dumps(_legacy_lock()),
            "--approve",
            "--expected-snapshot", f"sha256:{canonical_fingerprint(mini_repo)}",
            "--expected-revision", "legacy-archive-lock=0",
        ],
        cwd=repo_root,
        text=True,
        capture_output=True,
    )
    assert result.returncode == 2
    assert "must use GatewayEnvelopeV2" in result.stderr
    assert not (mini_repo / "operations/legacy/archive-lock.yaml").exists()
    assert not list((mini_repo / "operations/transactions").glob("transaction-*.yaml"))


def test_ordinary_direct_cli_cannot_create_a_receipt_v1(
    mini_repo: Path, repo_root: Path
):
    result = subprocess.run(
        [
            sys.executable,
            str(repo_root / "tools/los.py"),
            "--root", str(mini_repo),
            "capture",
            "--json",
            "--title", "direct-write-refusal",
            "--text", "must pass through the gateway",
        ],
        cwd=repo_root,
        text=True,
        capture_output=True,
    )
    assert result.returncode == 2
    assert "must use GatewayEnvelopeV2" in result.stderr
    assert not list((mini_repo / "work/inbox").glob("*.md"))
    assert not list((mini_repo / "operations/transactions").glob("transaction-*.yaml"))
