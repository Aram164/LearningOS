from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml
from gateway_helpers import file_sha256, request_artifact_id
from jsonschema import Draft202012Validator

from learning_os.commands.capability import _classify_failure
from learning_os.commands.support import _read_content_bound_file, _session_ledger
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
        "expected_revisions": {request_artifact_id("capture.create", key): 0},
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
    replay_only: bool = False,
):
    request_file.write_text(json.dumps(envelope), encoding="utf-8")
    command = [
            sys.executable,
            str(repo_root / "tools/los.py"),
            "--root",
            str(root),
            "capability",
            envelope["capability"],
            "--payload-file",
            str(request_file),
        ]
    if replay_only:
        command.append("--replay-only")
    return subprocess.run(
        command,
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


def test_gateway_v2_replay_only_verifies_a_receipt_without_creating_one(
    mini_repo: Path, repo_root: Path, tmp_path: Path
):
    envelope = _envelope(mini_repo, key="capture-replay-only-001")
    absent = _run(
        repo_root, mini_repo, tmp_path / "absent.json", envelope,
        replay_only=True,
    )
    assert absent.returncode == 2
    absent_response = json.loads(absent.stdout)
    assert absent_response["ok"] is False
    assert absent_response["error"]["code"] == "UNCONFIRMED"
    assert not list((mini_repo / "work/inbox").glob("*.md"))
    assert not list((mini_repo / "operations/transactions").glob("transaction-*.yaml"))

    committed = _run(repo_root, mini_repo, tmp_path / "commit.json", envelope)
    assert committed.returncode == 0, committed.stderr or committed.stdout
    committed_response = json.loads(committed.stdout)
    receipts_before = sorted(
        (mini_repo / "operations/transactions").glob("transaction-*.yaml")
    )
    captures_before = sorted((mini_repo / "work/inbox").glob("*.md"))

    verified = _run(
        repo_root, mini_repo, tmp_path / "verify.json", envelope,
        replay_only=True,
    )
    assert verified.returncode == 0, verified.stderr or verified.stdout
    verified_response = json.loads(verified.stdout)
    assert verified_response["replayed"] is True
    assert verified_response["transaction_id"] == committed_response["transaction_id"]
    assert sorted((mini_repo / "operations/transactions").glob("transaction-*.yaml")) \
        == receipts_before
    assert sorted((mini_repo / "work/inbox").glob("*.md")) == captures_before


def test_gateway_v2_replay_repairs_session_ownership_after_a_crash_window(
    mini_repo: Path, repo_root: Path, tmp_path: Path
):
    subprocess.run(["git", "init", "-q"], cwd=mini_repo, check=True)
    subprocess.run(
        ["git", "config", "user.email", "learningos-tests@example.invalid"],
        cwd=mini_repo, check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "LearningOS Tests"],
        cwd=mini_repo, check=True,
    )
    subprocess.run(["git", "add", "."], cwd=mini_repo, check=True)
    subprocess.run(
        ["git", "commit", "-qm", "fixture baseline"],
        cwd=mini_repo, check=True,
    )
    envelope = _envelope(mini_repo, key="capture-replay-ownership-001")
    committed = _run(repo_root, mini_repo, tmp_path / "commit-owned.json", envelope)
    assert committed.returncode == 0, committed.stderr or committed.stdout
    response = json.loads(committed.stdout)
    captured = response["result"]["captured"]

    # Simulate a process death after the receipt/idempotency commit but before
    # the ephemeral session ledger write.  The exact replay must reconstruct
    # ownership from Receipt V2 rather than rerun the handler.
    _session_ledger(mini_repo).unlink(missing_ok=True)
    replayed = _run(
        repo_root, mini_repo, tmp_path / "replay-owned.json", envelope,
        replay_only=True,
    )
    assert replayed.returncode == 0, replayed.stderr or replayed.stdout
    assert json.loads(replayed.stdout)["replayed"] is True

    ended = subprocess.run(
        [
            sys.executable,
            str(repo_root / "tools/los.py"),
            "--root",
            str(mini_repo),
            "session-end",
        ],
        cwd=repo_root,
        text=True,
        capture_output=True,
    )
    assert ended.returncode == 0, ended.stderr or ended.stdout
    review = json.loads(ended.stdout)
    assert captured in review["touched"]
    assert any(row[3:] == captured for row in review["owned_changes"]), review


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
        revisions={request_artifact_id("capture.create", key): 0},
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
        revisions={request_artifact_id("capture.create", key): 0},
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
        revisions={request_artifact_id("capture.create", key): 0},
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
        revisions={request_artifact_id("capture.create", key): 0},
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


@pytest.mark.parametrize(
    "message",
    [
        "transaction failed canonical validation; rollback incomplete for: work/inbox/a.md",
        "projection publication failed; rollback incomplete for: generated/manifest.json",
        "disk full; rollback incomplete for: work/inbox/a.md",
    ],
)
def test_gateway_v2_never_classifies_an_incomplete_rollback_as_no_commit(
    message: str,
):
    error = _classify_failure(2, message)
    assert error["code"] == "INTERNAL_FAILURE"
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


# --------------------------------------------------------------------------
# The request-scoped guard, end to end.
#
# `capture.create` and `garden.seed.create` name their own target file, so they
# guard the request rather than a path. That makes the guard string itself the
# contract between Core and every interface — and until 2026-08-29 the literal
# was written out in five places, the UI derived it after hashing the approval,
# and every capture and Garden seed the UI sent was refused. These tests derive
# the id from the one production helper, so a test can no longer agree with a
# copy of the bug.
# --------------------------------------------------------------------------


def test_request_scoped_guard_is_derived_from_one_production_helper():
    assert request_artifact_id("capture.create", "key-001") \
        == "capture-request:key-001"
    assert request_artifact_id("garden.seed.create", "key-001") \
        == "garden-request:key-001"
    with pytest.raises(ValueError, match="request-scoped"):
        request_artifact_id("stage.note.write", "key-001")
    with pytest.raises(ValueError, match="idempotency key"):
        request_artifact_id("capture.create", "   ")


def test_gateway_v2_guarded_capture_succeeds_and_returns_its_path(
    mini_repo: Path, repo_root: Path, tmp_path: Path
):
    envelope = _envelope(mini_repo, text="guarded", key="capture-guarded-001")
    applied = _run(repo_root, mini_repo, tmp_path / "guarded.json", envelope)
    assert applied.returncode == 0, applied.stderr or applied.stdout
    response = json.loads(applied.stdout)
    assert response["ok"] is True
    assert response["replayed"] is False
    captured = response["result"]["captured"]
    assert captured.startswith("work/inbox/")
    assert (mini_repo / captured).read_text(encoding="utf-8").strip() == "guarded"
    assert response["result"]["artifact_revisions"] == {
        request_artifact_id("capture.create", "capture-guarded-001"): 1
    }


def test_gateway_v2_refuses_capture_with_an_empty_revision_guard(
    mini_repo: Path, repo_root: Path, tmp_path: Path
):
    """An unguarded V2 write is a refusal, never a permissive default."""
    envelope = _envelope(mini_repo, key="capture-empty-guard-001")
    envelope["expected_revisions"] = {}
    envelope["approval"]["subject_sha256"] = intent_sha256(envelope)
    refused = _run(repo_root, mini_repo, tmp_path / "empty-guard.json", envelope)
    assert refused.returncode == 2
    response = json.loads(refused.stdout)
    assert response["ok"] is False
    assert "cover exactly every transaction artifact" in response["error"]["message"]
    assert not list((mini_repo / "work/inbox").glob("*.md"))
    assert not list((mini_repo / "operations/transactions").glob("transaction-*.yaml"))


def test_gateway_v2_refuses_capture_with_a_stale_revision_guard(
    mini_repo: Path, repo_root: Path, tmp_path: Path
):
    envelope = _envelope(mini_repo, key="capture-stale-guard-001")
    envelope["expected_revisions"] = {
        request_artifact_id("capture.create", "capture-stale-guard-001"): 7
    }
    envelope["approval"]["subject_sha256"] = intent_sha256(envelope)
    refused = _run(repo_root, mini_repo, tmp_path / "stale-guard.json", envelope)
    assert refused.returncode == 3
    response = json.loads(refused.stdout)
    assert response["ok"] is False
    assert response["error"]["code"] == "REVISION_CONFLICT"
    assert response["error"]["retryable"] is True
    assert not list((mini_repo / "work/inbox").glob("*.md"))


def test_gateway_v2_refuses_a_guard_naming_someone_elses_request(
    mini_repo: Path, repo_root: Path, tmp_path: Path
):
    """The guard has to be this request's, not merely well-formed."""
    envelope = _envelope(mini_repo, key="capture-foreign-guard-001")
    envelope["expected_revisions"] = {
        request_artifact_id("capture.create", "some-other-request"): 0
    }
    envelope["approval"]["subject_sha256"] = intent_sha256(envelope)
    refused = _run(repo_root, mini_repo, tmp_path / "foreign-guard.json", envelope)
    assert refused.returncode == 2
    response = json.loads(refused.stdout)
    assert response["ok"] is False
    assert "cover exactly every transaction artifact" in response["error"]["message"]
    assert not list((mini_repo / "work/inbox").glob("*.md"))


def test_gateway_v2_replay_returns_the_identical_capture_path(
    mini_repo: Path, repo_root: Path, tmp_path: Path
):
    """A retry must answer the question the first call answered.

    Returning only bookkeeping forces the caller to guess where its capture
    went, or to send the write again to find out — which is precisely what
    idempotency exists to prevent.
    """
    envelope = _envelope(mini_repo, text="replayed body", key="capture-replay-path-001")
    first = _run(repo_root, mini_repo, tmp_path / "replay-first.json", envelope)
    assert first.returncode == 0, first.stderr or first.stdout
    first_response = json.loads(first.stdout)

    receipts_before = sorted(
        (mini_repo / "operations/transactions").glob("transaction-*.yaml")
    )
    captures_before = sorted((mini_repo / "work/inbox").glob("*.md"))
    assert len(captures_before) == 1

    second = _run(repo_root, mini_repo, tmp_path / "replay-second.json", envelope)
    assert second.returncode == 0, second.stderr or second.stdout
    second_response = json.loads(second.stdout)
    assert second_response["replayed"] is True
    assert second_response["result"]["replayed"] is True
    assert second_response["result"]["captured"] == first_response["result"]["captured"]
    assert second_response["transaction_id"] == first_response["transaction_id"]
    assert second_response["receipt_path"] == first_response["receipt_path"]
    assert second_response["snapshot_after"] == first_response["snapshot_after"]
    assert second_response["result"]["artifact_revisions"] \
        == first_response["result"]["artifact_revisions"]

    assert sorted((mini_repo / "work/inbox").glob("*.md")) == captures_before
    assert sorted(
        (mini_repo / "operations/transactions").glob("transaction-*.yaml")
    ) == receipts_before
    assert (mini_repo / second_response["result"]["captured"]).read_text(
        encoding="utf-8"
    ).strip() == "replayed body"


def test_gateway_v2_replay_of_a_tampered_receipt_fails_closed(
    mini_repo: Path, repo_root: Path, tmp_path: Path
):
    """A receipt that cannot prove what was written is not evidence.

    The safe answer is a typed refusal. Rerunning the handler would duplicate a
    write that already committed, and inventing a path would be a lie about
    canonical state.
    """
    envelope = _envelope(mini_repo, text="tamper", key="capture-tampered-001")
    first = _run(repo_root, mini_repo, tmp_path / "tamper-first.json", envelope)
    assert first.returncode == 0, first.stderr or first.stdout
    first_response = json.loads(first.stdout)
    receipt_path = mini_repo / first_response["receipt_path"]

    captures_before = sorted((mini_repo / "work/inbox").glob("*.md"))
    receipt = yaml.safe_load(receipt_path.read_text(encoding="utf-8"))
    # A second write row: the receipt no longer describes one unambiguous file.
    receipt["writes"] = [
        *receipt["writes"],
        {
            "path": "work/inbox/not-this-one.md",
            "sha256_before": None,
            "sha256_after": "0" * 64,
            "created": True,
        },
    ]
    receipt_path.write_text(yaml.safe_dump(receipt, sort_keys=False), encoding="utf-8")

    refused = _run(repo_root, mini_repo, tmp_path / "tamper-replay.json", envelope)
    assert refused.returncode == 2
    response = json.loads(refused.stdout)
    assert response["ok"] is False
    assert response["error"]["code"] == "INTERNAL_FAILURE"
    assert response["error"]["retryable"] is False
    assert "exactly one write" in response["error"]["message"]
    assert sorted((mini_repo / "work/inbox").glob("*.md")) == captures_before


def test_gateway_v2_replay_refuses_a_receipt_written_out_of_scope(
    mini_repo: Path, repo_root: Path, tmp_path: Path
):
    envelope = _envelope(mini_repo, text="scope", key="capture-out-of-scope-001")
    first = _run(repo_root, mini_repo, tmp_path / "scope-first.json", envelope)
    assert first.returncode == 0, first.stderr or first.stdout
    receipt_path = mini_repo / json.loads(first.stdout)["receipt_path"]

    receipt = yaml.safe_load(receipt_path.read_text(encoding="utf-8"))
    receipt["writes"][0]["path"] = "knowledge/notes/elsewhere.md"
    receipt_path.write_text(yaml.safe_dump(receipt, sort_keys=False), encoding="utf-8")

    refused = _run(repo_root, mini_repo, tmp_path / "scope-replay.json", envelope)
    assert refused.returncode == 2
    response = json.loads(refused.stdout)
    assert response["error"]["code"] == "INTERNAL_FAILURE"
    assert response["error"]["retryable"] is False, (
        "contradictory replay evidence is never retryable"
    )
    assert "declared scope" in response["error"]["message"]


def test_gateway_v2_replay_returns_the_identical_file_capture_path(
    mini_repo: Path, repo_root: Path, tmp_path: Path
):
    """The file-capture replay answers from the receipt, not from the source."""
    source = tmp_path / "file-replay-path.txt"
    source.write_bytes(b"approved file bytes")
    key = "capture-file-replay-path-001"
    envelope = _approved_v2(
        mini_repo,
        capability="capture.create",
        payload={"file": str(source), "file_sha256": file_sha256(source)},
        revisions={request_artifact_id("capture.create", key): 0},
        key=key,
    )
    first = _run(repo_root, mini_repo, tmp_path / "file-path-first.json", envelope)
    assert first.returncode == 0, first.stderr or first.stdout
    first_response = json.loads(first.stdout)

    # Deleting the source proves the replay never reopens it: a reread would
    # fail, and a reread of different bytes would silently answer about a file
    # nobody approved.
    source.unlink()
    replay = _run(repo_root, mini_repo, tmp_path / "file-path-replay.json", envelope)
    assert replay.returncode == 0, replay.stderr or replay.stdout
    replay_response = json.loads(replay.stdout)
    assert replay_response["replayed"] is True
    assert replay_response["result"]["captured"] \
        == first_response["result"]["captured"]
    assert (mini_repo / replay_response["result"]["captured"]).read_bytes() \
        == b"approved file bytes"


# ============================================================================
# Phase 2 — replay-evidence cross-binding (release-hardening 2026-08-29)
#
# One immutable, schema-validated evidence object is built from the
# idempotency ledger row and its named Receipt V2 before session ownership is
# touched. Every field named in the plan is cross-bound; a mismatch is always
# a non-retryable INTERNAL_FAILURE and never invokes the capability handler.
# ============================================================================

def _idempotency_ledger_path(root: Path) -> Path:
    return root / "operations" / "transactions" / "idempotency.yaml"


def _load_idempotency(root: Path) -> dict:
    return yaml.safe_load(_idempotency_ledger_path(root).read_text(encoding="utf-8"))


def _save_idempotency(root: Path, data: dict) -> None:
    _idempotency_ledger_path(root).write_text(
        yaml.safe_dump(data, sort_keys=False), encoding="utf-8"
    )


def _committed(repo_root: Path, mini_repo: Path, tmp_path: Path,
              key: str) -> tuple[dict, dict, Path]:
    """Commit one ordinary capture; return (envelope, response, receipt_path).

    The caller must reuse the returned envelope object for any later replay
    call — rebuilding a fresh envelope from the current repository state would
    recompute ``expected_snapshot`` against post-commit state and change the
    intent hash, which is not what an exact retry ever does.
    """
    envelope = _envelope(mini_repo, text=key, key=key)
    result = _run(repo_root, mini_repo, tmp_path / f"{key}-commit.json", envelope)
    assert result.returncode == 0, result.stderr or result.stdout
    response = json.loads(result.stdout)
    return envelope, response, mini_repo / response["receipt_path"]


def _replay_refusal(repo_root: Path, mini_repo: Path, tmp_path: Path,
                    envelope: dict, key: str) -> dict:
    result = _run(
        repo_root, mini_repo, tmp_path / f"{key}-replay.json", envelope,
        replay_only=True,
    )
    assert result.returncode == 2, (result.returncode, result.stdout, result.stderr)
    response = json.loads(result.stdout)
    assert response["ok"] is False
    return response


def test_replay_missing_receipt_fails_closed(mini_repo: Path, repo_root: Path, tmp_path: Path):
    key = "capture-missing-receipt-001"
    envelope, _, receipt_path = _committed(repo_root, mini_repo, tmp_path, key)
    captures_before = sorted((mini_repo / "work/inbox").glob("*.md"))
    receipt_path.unlink()

    response = _replay_refusal(repo_root, mini_repo, tmp_path, envelope, key)
    assert response["error"]["code"] == "INTERNAL_FAILURE"
    assert response["error"]["retryable"] is False
    assert "missing or non-canonical receipt" in response["error"]["message"]
    assert sorted((mini_repo / "work/inbox").glob("*.md")) == captures_before


def test_replay_receipt_path_outside_transaction_directory_fails_closed(
    mini_repo: Path, repo_root: Path, tmp_path: Path,
):
    key = "capture-escaping-receipt-001"
    envelope, _, _ = _committed(repo_root, mini_repo, tmp_path, key)
    ledger = _load_idempotency(mini_repo)
    ledger["entries"][key]["receipt_path"] = "../outside-the-repository.yaml"
    _save_idempotency(mini_repo, ledger)

    response = _replay_refusal(repo_root, mini_repo, tmp_path, envelope, key)
    assert response["error"]["code"] == "INTERNAL_FAILURE"
    assert response["error"]["retryable"] is False
    assert "unsafe receipt" in response["error"]["message"]


def test_replay_malformed_receipt_fails_closed(mini_repo: Path, repo_root: Path, tmp_path: Path):
    key = "capture-malformed-receipt-001"
    envelope, _, receipt_path = _committed(repo_root, mini_repo, tmp_path, key)
    # A receipt that parses as YAML but is not a mapping at all.
    receipt_path.write_text("- just\n- a\n- list\n", encoding="utf-8")

    response = _replay_refusal(repo_root, mini_repo, tmp_path, envelope, key)
    assert response["error"]["code"] == "INTERNAL_FAILURE"
    assert response["error"]["retryable"] is False
    assert "not a mapping" in response["error"]["message"]


def test_replay_duplicate_yaml_key_in_receipt_fails_closed(
    mini_repo: Path, repo_root: Path, tmp_path: Path,
):
    """The unique-key loader must catch what ``yaml.safe_load`` silently allows."""
    key = "capture-duplicate-key-001"
    envelope, _, receipt_path = _committed(repo_root, mini_repo, tmp_path, key)
    text = receipt_path.read_text(encoding="utf-8")
    # Any top-level scalar key repeated is a duplicate under the unique-key
    # loader, regardless of what the second value is.
    tampered = text + "\nstatus: committed\n"
    receipt_path.write_text(tampered, encoding="utf-8")

    response = _replay_refusal(repo_root, mini_repo, tmp_path, envelope, key)
    assert response["error"]["code"] == "INTERNAL_FAILURE"
    assert response["error"]["retryable"] is False
    assert "unreadable" in response["error"]["message"]


def test_replay_transaction_id_mismatch_fails_closed(
    mini_repo: Path, repo_root: Path, tmp_path: Path,
):
    key = "capture-txid-mismatch-001"
    envelope, _, receipt_path = _committed(repo_root, mini_repo, tmp_path, key)
    receipt = yaml.safe_load(receipt_path.read_text(encoding="utf-8"))
    receipt["id"] = "transaction-99999999-999999-999"
    receipt_path.write_text(yaml.safe_dump(receipt, sort_keys=False), encoding="utf-8")

    response = _replay_refusal(repo_root, mini_repo, tmp_path, envelope, key)
    assert response["error"]["code"] == "INTERNAL_FAILURE"
    assert response["error"]["retryable"] is False
    assert "id does not match" in response["error"]["message"]


def test_replay_receipt_capability_mismatch_fails_closed(
    mini_repo: Path, repo_root: Path, tmp_path: Path,
):
    key = "capture-capability-mismatch-001"
    envelope, _, receipt_path = _committed(repo_root, mini_repo, tmp_path, key)
    receipt = yaml.safe_load(receipt_path.read_text(encoding="utf-8"))
    receipt["capability"] = "garden.seed.create"
    receipt_path.write_text(yaml.safe_dump(receipt, sort_keys=False), encoding="utf-8")

    response = _replay_refusal(repo_root, mini_repo, tmp_path, envelope, key)
    assert response["error"]["code"] == "INTERNAL_FAILURE"
    assert response["error"]["retryable"] is False
    assert "different capability" in response["error"]["message"]


def test_replay_non_committed_status_fails_closed(
    mini_repo: Path, repo_root: Path, tmp_path: Path,
):
    """The receipt schema pins ``status`` to ``committed`` (a receipt is only
    ever written once a transaction commits), so an altered status is caught
    by schema validation before reaching the explicit status check — both
    layers refuse it, and either is an acceptable failure mode here.
    """
    key = "capture-not-committed-001"
    envelope, _, receipt_path = _committed(repo_root, mini_repo, tmp_path, key)
    receipt = yaml.safe_load(receipt_path.read_text(encoding="utf-8"))
    receipt["status"] = "rolled-back"
    receipt_path.write_text(yaml.safe_dump(receipt, sort_keys=False), encoding="utf-8")

    response = _replay_refusal(repo_root, mini_repo, tmp_path, envelope, key)
    assert response["error"]["code"] == "INTERNAL_FAILURE"
    assert response["error"]["retryable"] is False
    assert "status" in response["error"]["message"] or "schema validation" in response["error"]["message"]


def test_replay_request_id_mismatch_fails_closed(
    mini_repo: Path, repo_root: Path, tmp_path: Path,
):
    """Same idempotency key and intent, a genuinely different request id.

    ``intent_sha256`` deliberately excludes request identities, so this cannot
    be caught by the idempotency-conflict check alone — it needs its own
    cross-binding.
    """
    key = "capture-request-id-mismatch-001"
    envelope, _, _ = _committed(repo_root, mini_repo, tmp_path, key)

    resent = dict(envelope)
    resent["request_id"] = "request-a-completely-different-retry"
    result = _run(repo_root, mini_repo, tmp_path / "reqid-replay.json", resent, replay_only=True)
    assert result.returncode == 2, (result.returncode, result.stdout, result.stderr)
    response = json.loads(result.stdout)
    assert response["error"]["code"] == "INTERNAL_FAILURE"
    assert response["error"]["retryable"] is False
    assert "request id" in response["error"]["message"]


def test_replay_channel_mismatch_fails_closed(mini_repo: Path, repo_root: Path, tmp_path: Path):
    """Channel is part of the intent hash, so this can only be a tampered ledger."""
    key = "capture-channel-mismatch-001"
    envelope, _, _ = _committed(repo_root, mini_repo, tmp_path, key)
    ledger = _load_idempotency(mini_repo)
    ledger["entries"][key]["channel"] = "codex"
    _save_idempotency(mini_repo, ledger)

    response = _replay_refusal(repo_root, mini_repo, tmp_path, envelope, key)
    assert response["error"]["code"] == "INTERNAL_FAILURE"
    assert response["error"]["retryable"] is False
    assert "channel" in response["error"]["message"]


def test_replay_snapshot_mismatch_fails_closed(mini_repo: Path, repo_root: Path, tmp_path: Path):
    key = "capture-snapshot-mismatch-001"
    envelope, _, receipt_path = _committed(repo_root, mini_repo, tmp_path, key)
    receipt = yaml.safe_load(receipt_path.read_text(encoding="utf-8"))
    receipt["snapshot_after"] = "sha256:" + "f" * 64
    receipt_path.write_text(yaml.safe_dump(receipt, sort_keys=False), encoding="utf-8")

    response = _replay_refusal(repo_root, mini_repo, tmp_path, envelope, key)
    assert response["error"]["code"] == "INTERNAL_FAILURE"
    assert response["error"]["retryable"] is False
    assert "snapshot does not match" in response["error"]["message"]


def test_replay_artifact_revision_mismatch_fails_closed(
    mini_repo: Path, repo_root: Path, tmp_path: Path,
):
    key = "capture-revision-mismatch-001"
    envelope, _, receipt_path = _committed(repo_root, mini_repo, tmp_path, key)
    receipt = yaml.safe_load(receipt_path.read_text(encoding="utf-8"))
    artifact = next(iter(receipt["artifact_revisions"]))
    receipt["artifact_revisions"][artifact]["after"] += 1
    receipt_path.write_text(yaml.safe_dump(receipt, sort_keys=False), encoding="utf-8")

    response = _replay_refusal(repo_root, mini_repo, tmp_path, envelope, key)
    assert response["error"]["code"] == "INTERNAL_FAILURE"
    assert response["error"]["retryable"] is False
    assert "artifact revision does not match" in response["error"]["message"]


def test_replay_approval_subject_mismatch_fails_closed(
    mini_repo: Path, repo_root: Path, tmp_path: Path,
):
    key = "capture-approval-mismatch-001"
    envelope, _, receipt_path = _committed(repo_root, mini_repo, tmp_path, key)
    receipt = yaml.safe_load(receipt_path.read_text(encoding="utf-8"))
    receipt["request"]["approval"]["subject_sha256"] = "sha256:" + "a" * 64
    receipt_path.write_text(yaml.safe_dump(receipt, sort_keys=False), encoding="utf-8")

    response = _replay_refusal(repo_root, mini_repo, tmp_path, envelope, key)
    assert response["error"]["code"] == "INTERNAL_FAILURE"
    assert response["error"]["retryable"] is False
    assert "approval subject" in response["error"]["message"]


def test_replay_unsafe_write_path_fails_closed(mini_repo: Path, repo_root: Path, tmp_path: Path):
    key = "capture-unsafe-path-001"
    envelope, _, receipt_path = _committed(repo_root, mini_repo, tmp_path, key)
    receipt = yaml.safe_load(receipt_path.read_text(encoding="utf-8"))
    receipt["writes"][0]["path"] = "../escaped.md"
    receipt_path.write_text(yaml.safe_dump(receipt, sort_keys=False), encoding="utf-8")

    response = _replay_refusal(repo_root, mini_repo, tmp_path, envelope, key)
    assert response["error"]["code"] == "INTERNAL_FAILURE"
    assert response["error"]["retryable"] is False


def test_replay_only_with_no_ledger_row_never_invokes_the_handler(
    mini_repo: Path, repo_root: Path, tmp_path: Path,
):
    envelope = _envelope(mini_repo, text="never-committed", key="capture-never-committed-001")
    result = _run(
        repo_root, mini_repo, tmp_path / "no-row.json", envelope, replay_only=True,
    )
    assert result.returncode == 2
    response = json.loads(result.stdout)
    assert response["error"]["code"] == "UNCONFIRMED"
    assert not list((mini_repo / "work/inbox").glob("*.md"))
    assert not list((mini_repo / "operations/transactions").glob("transaction-*.yaml"))


def test_two_concurrent_replays_of_distinct_transactions_retain_both_rows(
    mini_repo: Path, repo_root: Path, tmp_path: Path,
):
    """Concurrent exact replays for distinct writes must not lose either row.

    Before the operator lock wrapped replay lookup through session-ledger
    repair, this read-modify-write on the session ledger could race across
    processes and silently drop one gesture's ownership row.
    """
    from concurrent.futures import ThreadPoolExecutor

    keys = [f"capture-concurrent-{i:03d}" for i in range(4)]
    envelopes: dict[str, dict] = {}
    captured_paths = []
    for key in keys:
        envelope, response, _ = _committed(repo_root, mini_repo, tmp_path, key)
        envelopes[key] = envelope
        captured_paths.append(response["result"]["captured"])

    _session_ledger(mini_repo).unlink(missing_ok=True)

    def replay(key: str):
        return _run(
            repo_root, mini_repo, tmp_path / f"{key}-concurrent-replay.json",
            envelopes[key], replay_only=True,
        )

    with ThreadPoolExecutor(max_workers=len(keys)) as pool:
        results = list(pool.map(replay, keys))

    for result in results:
        assert result.returncode == 0, (result.returncode, result.stdout, result.stderr)
        assert json.loads(result.stdout)["replayed"] is True

    ended = subprocess.run(
        [sys.executable, str(repo_root / "tools/los.py"), "--root", str(mini_repo), "session-end"],
        cwd=repo_root, text=True, capture_output=True,
    )
    assert ended.returncode == 0, ended.stderr or ended.stdout
    review = json.loads(ended.stdout)
    for path in captured_paths:
        assert path in review["touched"], (
            f"{path} is missing from session ownership — a concurrent replay lost this row"
        )
    assert len(set(captured_paths)) == len(captured_paths)


def test_two_concurrent_replays_of_the_same_transaction_do_not_duplicate_rows(
    mini_repo: Path, repo_root: Path, tmp_path: Path,
):
    key = "capture-same-transaction-concurrent-001"
    envelope, response, _ = _committed(repo_root, mini_repo, tmp_path, key)
    captured = response["result"]["captured"]
    _session_ledger(mini_repo).unlink(missing_ok=True)

    from concurrent.futures import ThreadPoolExecutor

    def replay(i: int):
        return _run(
            repo_root, mini_repo, tmp_path / f"same-txn-replay-{i}.json",
            envelope, replay_only=True,
        )

    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(replay, range(4)))

    for result in results:
        assert result.returncode == 0, (result.returncode, result.stdout, result.stderr)

    ledger = json.loads(_session_ledger(mini_repo).read_text(encoding="utf-8"))
    assert list(ledger["paths"]).count(captured) == 1, (
        "concurrent replays of the same transaction must not duplicate the ownership row"
    )
