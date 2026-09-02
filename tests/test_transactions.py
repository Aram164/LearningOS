from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest
import yaml

import learning_os.ai_actions.projection as ai_projection
import learning_os.commands.support as command_support
import learning_os.fingerprint as fingerprint_module
import learning_os.transactions as transaction_module
from learning_os.contracts.gateway import (
    GatewayRequestContext,
    gateway_request_context,
    verified_gateway_snapshot,
)
from learning_os.contracts.json_schema import (
    ContractValidationError,
    validate_contract,
)
from learning_os.fingerprint import source_fingerprint
from learning_os.loader import load_repo
from learning_os.rules.common import Issue
from learning_os.transactions import (
    TransactionConflict,
    TransactionFailure,
    TransactionService,
    TransactionSnapshotConflict,
    artifact_revision,
    canonical_fingerprint,
)

TOOLS = Path(__file__).resolve().parent.parent / "tools"


def _gateway_context(capability: str, suffix: str) -> GatewayRequestContext:
    intent = "sha256:" + "a" * 64
    return GatewayRequestContext(
        request_id=f"request-{suffix}",
        idempotency_key=f"idempotency-{suffix}",
        capability=capability,
        channel="operator",
        intent_sha256=intent,
        approval_kind="operator-approval",
        approval_subject_sha256=intent,
    )


# --------------------------------------------------------------------------
# One fingerprint, one root list.
#
# Two implementations existed until 2026-08-18: `transactions.canonical_
# fingerprint` produced the value a receipt records as snapshot_before/after,
# and `genout.source_fingerprint` produced the value the projection publishes
# as `_generated.snapshot_id` — the token the UI hands back to guard its next
# write. Same roots, same algorithm, nothing holding them together. Add a
# canonical root to one and forget the other and the receipt starts describing
# a different state than the one the write was checked against, silently.
#
# Value equality on a fixture is too weak to guard this on its own: a root the
# fixture happens not to contain could diverge without moving either digest.
# So the structure is asserted too.
# --------------------------------------------------------------------------

def test_the_receipt_and_the_projection_share_one_digest_function():
    assert canonical_fingerprint is fingerprint_module.canonical_fingerprint


def test_only_one_module_declares_the_canonical_root_list():
    """No second copy of the root list may appear anywhere under tools/."""
    roots = set(fingerprint_module.CANONICAL_ROOTS)
    declaring: list[str] = []
    for path in sorted(TOOLS.rglob("*.py")):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if not isinstance(node, (ast.Tuple, ast.List, ast.Set)):
                continue
            try:
                literal = set(ast.literal_eval(node))
            except (ValueError, TypeError, SyntaxError):
                continue
            if roots <= literal:
                declaring.append(path.relative_to(TOOLS).as_posix())
                break
    assert declaring == ["learning_os/fingerprint.py"], (
        f"the canonical root list is declared in more than one place: {declaring}"
    )


def test_the_receipt_and_the_projection_agree_on_a_real_repository(mini_repo: Path):
    assert source_fingerprint(load_repo(mini_repo)) == canonical_fingerprint(mini_repo)


def test_source_fingerprint_cache_does_not_mutate_the_loaded_repo(
        mini_repo: Path, monkeypatch: pytest.MonkeyPatch):
    repo = load_repo(mini_repo)
    calls = 0
    original = fingerprint_module.canonical_fingerprint

    def counted(root: Path):
        nonlocal calls
        calls += 1
        return original(root)

    monkeypatch.setattr(fingerprint_module, "canonical_fingerprint", counted)
    first = source_fingerprint(repo)
    assert source_fingerprint(repo) == first
    assert calls == 1
    assert not hasattr(repo, "_source_fingerprint_cache")


def test_a_transaction_refuses_an_already_invalid_repository(
        mini_repo: Path, monkeypatch: pytest.MonkeyPatch):
    target = mini_repo / "work/inbox/strict-validation.md"
    monkeypatch.setattr(
        command_support,
        "validate",
        lambda _repo, online=False: [
            Issue("E", "PREEXISTING", "the repository is already invalid", "somewhere.yaml")
        ],
    )
    monkeypatch.setattr(command_support, "_publish", lambda _root: None)

    artifact = "capture-test:strict-validation"
    with gateway_request_context(
        _gateway_context("capture.create", "strict-validation")
    ):
        code, errors, confirmation = command_support._write_transaction(
            mini_repo,
            {target: "must roll back\n"},
            capability="capture.create",
            expected_revisions={artifact: 0},
            artifact_ids=[artifact],
        )

    assert code == 2
    assert "PREEXISTING" in errors[0]
    assert confirmation == {}
    assert not target.exists()


def test_validation_and_publication_share_one_loaded_repository(
        mini_repo: Path, monkeypatch: pytest.MonkeyPatch):
    target = mini_repo / "work/inbox/one-load.md"
    loads = 0
    original = command_support.load_repo

    def counted(root: Path):
        nonlocal loads
        loads += 1
        return original(root)

    monkeypatch.setattr(command_support, "load_repo", counted)

    def unexpected_projection_load(_root: Path):
        raise AssertionError(
            "manifest projection must reuse the repository loaded for validation"
        )

    monkeypatch.setattr(ai_projection, "load_repo", unexpected_projection_load)
    artifact = "capture-test:one-load"
    with gateway_request_context(_gateway_context("capture.create", "one-load")):
        code, errors, confirmation = command_support._write_transaction(
            mini_repo,
            {target: "one load\n"},
            capability="capture.create",
            expected_revisions={artifact: 0},
            artifact_ids=[artifact],
        )

    assert (code, errors) == (0, [])
    assert confirmation["transaction_id"]
    assert loads == 1


def test_locked_v2_handler_skips_only_its_duplicate_fingerprint(
        mini_repo: Path, monkeypatch: pytest.MonkeyPatch):
    """Keep entry/final/projection safety while removing the handler duplicate."""
    expected = f"sha256:{canonical_fingerprint(mini_repo)}"
    base = _gateway_context("capture.create", "bounded-fingerprints")
    context = GatewayRequestContext(
        request_id=base.request_id,
        idempotency_key=base.idempotency_key,
        capability=base.capability,
        channel=base.channel,
        intent_sha256=base.intent_sha256,
        approval_kind=base.approval_kind,
        approval_subject_sha256=base.approval_subject_sha256,
        expected_snapshot=expected,
    )
    calls = 0
    original = fingerprint_module.canonical_fingerprint

    def counted(root: Path) -> str:
        nonlocal calls
        calls += 1
        return original(root)

    monkeypatch.setattr(fingerprint_module, "canonical_fingerprint", counted)
    monkeypatch.setattr(command_support, "canonical_fingerprint", counted)
    monkeypatch.setattr(transaction_module, "canonical_fingerprint", counted)
    target = mini_repo / "work/inbox/bounded-fingerprints.md"
    artifact = "capture-test:bounded-fingerprints"

    with command_support._operator_lock(mini_repo):
        with gateway_request_context(context), verified_gateway_snapshot(
            mini_repo, expected
        ):
            # cmd_capability owns the locked entry comparison. This assertion
            # represents the named handler's former duplicate and must not scan.
            assert command_support._expected_ok(mini_repo, expected) is True
            code, errors, confirmation = command_support._write_transaction(
                mini_repo,
                {target: "bounded\n"},
                capability="capture.create",
                expected_revisions={artifact: 0},
                artifact_ids=[artifact],
            )

    assert (code, errors) == (0, [])
    assert confirmation["snapshot_after"].startswith("sha256:")
    assert calls == 3, (
        "the transaction needs a final pre-write scan, the projected identity, "
        "and a fresh post-publication scan"
    )


def test_operator_lock_is_reentrant_in_one_dispatch(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    calls: list[int] = []
    monkeypatch.setattr(
        command_support.fcntl,
        "flock",
        lambda _fd, operation: calls.append(operation),
    )

    with command_support._operator_lock(tmp_path):
        with command_support._operator_lock(tmp_path):
            assert calls == [command_support.fcntl.LOCK_EX]

    assert calls == [command_support.fcntl.LOCK_EX, command_support.fcntl.LOCK_UN]


def test_projection_publication_refuses_a_changed_canonical_snapshot(
        mini_repo: Path, monkeypatch: pytest.MonkeyPatch):
    target = mini_repo / "work/inbox/projection-race.md"
    external = mini_repo / "knowledge/notes/mathematics/external-race.md"
    original_publish = command_support._publish_repo

    def publish_then_mutate(repo):
        original_publish(repo)
        external.write_text("changed outside the transaction\n", encoding="utf-8")

    monkeypatch.setattr(command_support, "_publish_repo", publish_then_mutate)
    artifact = "capture-test:projection-race"
    with gateway_request_context(
        _gateway_context("capture.create", "projection-race")
    ):
        code, errors, confirmation = command_support._write_transaction(
            mini_repo,
            {target: "transaction content\n"},
            capability="capture.create",
            expected_revisions={artifact: 0},
            artifact_ids=[artifact],
        )

    assert code == 2
    assert any("changed during projection publication" in error for error in errors)
    assert confirmation == {}
    assert not target.exists()
    assert external.is_file(), "rollback must not erase an unrelated external edit"
    assert not list((mini_repo / "operations/transactions").glob("transaction-*.yaml"))


def test_transaction_rechecks_approved_snapshot_before_writing(tmp_path: Path):
    canonical = tmp_path / "knowledge/note.md"
    canonical.parent.mkdir(parents=True)
    canonical.write_text("approved\n", encoding="utf-8")
    expected = f"sha256:{canonical_fingerprint(tmp_path)}"
    canonical.write_text("changed elsewhere\n", encoding="utf-8")
    target = tmp_path / "projects/registry/project-demo.yaml"

    with pytest.raises(TransactionSnapshotConflict) as refusal:
        TransactionService(tmp_path).commit(
            capability="project.create",
            writes={target: "id: project-demo\n"},
            artifact_ids=["project-demo"],
            expected_snapshot=expected,
        )

    assert refusal.value.expected == expected
    assert refusal.value.actual == f"sha256:{canonical_fingerprint(tmp_path)}"
    assert not target.exists()
    assert not list((tmp_path / "operations/transactions").glob("transaction-*.yaml"))


def test_snapshot_conflict_precedes_a_revision_conflict(tmp_path: Path):
    canonical = tmp_path / "knowledge/note.md"
    canonical.parent.mkdir(parents=True)
    canonical.write_text("approved\n", encoding="utf-8")
    approved = f"sha256:{canonical_fingerprint(tmp_path)}"
    canonical.write_text("changed\n", encoding="utf-8")
    ledger = tmp_path / "operations/transactions/revisions.yaml"
    ledger.parent.mkdir(parents=True)
    ledger.write_text(
        "schema_version: 1\ntype: artifact-revision-ledger\nrevisions:\n"
        "  project-demo: 1\n",
        encoding="utf-8",
    )

    with pytest.raises(TransactionSnapshotConflict):
        TransactionService(tmp_path).commit(
            capability="project.update",
            writes={tmp_path / "projects/registry/project-demo.yaml": "id: project-demo\n"},
            artifact_ids=["project-demo"],
            expected_revisions={"project-demo": 0},
            expected_snapshot=approved,
        )


def test_snapshot_check_does_not_parse_the_repository(
        mini_repo: Path, monkeypatch: pytest.MonkeyPatch):
    expected = f"sha256:{canonical_fingerprint(mini_repo)}"

    def unexpected_load(_root: Path):
        raise AssertionError("a content digest must not require a domain parse")

    monkeypatch.setattr(command_support, "load_repo", unexpected_load)

    assert command_support._expected_ok(mini_repo, expected) is True


def test_session_ledger_excludes_every_canvas_filename(mini_repo: Path):
    canvas = mini_repo / "Untitled 37.canvas"
    regular = mini_repo / "work/inbox/kept.md"
    command_support._record_touched(mini_repo, [canvas, regular])
    recorded = json.loads(
        command_support._session_ledger(mini_repo).read_text(encoding="utf-8")
    )
    assert "Untitled 37.canvas" not in recorded["paths"]
    assert recorded["paths"]["work/inbox/kept.md"] == {"state": "absent"}


def test_failed_transaction_restores_canonical_state(tmp_path: Path):
    root = tmp_path
    target = root / "projects/registry/project-demo.yaml"
    target.parent.mkdir(parents=True)
    target.write_text("old\n", encoding="utf-8")
    before = canonical_fingerprint(root)
    service = TransactionService(root)
    with pytest.raises(TransactionFailure):
        service.commit(
            capability="project.update", writes={target: "new\n"},
            artifact_ids=["project-demo"], validate_state=lambda: ["forced failure"],
        )
    assert target.read_text(encoding="utf-8") == "old\n"
    assert canonical_fingerprint(root) == before
    assert not list((root / "operations/transactions").glob("transaction-*.yaml"))


def test_atomic_transaction_write_fsyncs_file_and_parent_directory(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    calls: list[int] = []
    monkeypatch.setattr(transaction_module.os, "fsync", lambda fd: calls.append(fd))
    target = tmp_path / "durable.yaml"

    transaction_module._atomic_write_bytes(target, b"durable\n")

    assert target.read_bytes() == b"durable\n"
    assert len(calls) == 2


def test_artifact_revision_conflicts_are_scoped(tmp_path: Path):
    root = tmp_path
    a = root / "projects/registry/project-a.yaml"
    b = root / "projects/registry/project-b.yaml"
    a.parent.mkdir(parents=True)
    service = TransactionService(root)
    first = service.commit(capability="project.create", writes={a: "a\n"}, artifact_ids=["project-a"])
    assert first.revisions == {"project-a": 1}
    # A write to another artifact does not conflict with project-a changing.
    second = service.commit(
        capability="project.create", writes={b: "b\n"}, artifact_ids=["project-b"],
        expected_revisions={"project-b": 0},
    )
    assert second.revisions == {"project-b": 1}
    with pytest.raises(TransactionConflict):
        service.commit(
            capability="project.update", writes={a: "a2\n"}, artifact_ids=["project-a"],
            expected_revisions={"project-a": 0},
        )
    assert artifact_revision(root, "project-a") == 1


def test_each_commit_has_exactly_one_append_only_receipt(tmp_path: Path):
    root = tmp_path
    target = root / "projects/registry/project-demo.yaml"
    result = TransactionService(root).commit(
        capability="project.create", writes={target: "demo\n"}, artifact_ids=["project-demo"]
    )
    receipts = list((root / "operations/transactions").glob("transaction-*.yaml"))
    assert receipts == [result.receipt_path]
    receipt = yaml.safe_load(result.receipt_path.read_text(encoding="utf-8"))
    assert receipt["status"] == "committed"
    assert receipt["capability"] == "project.create"
    assert receipt["artifact_revisions"]["project-demo"] == {"before": 0, "after": 1}


def _receipt_contract_fixture(*, schema_version: int, metadata: dict) -> dict:
    receipt = {
        "schema_version": schema_version,
        "id": "transaction-20260825-120000-001",
        "type": "transaction-receipt",
        "status": "committed",
        "capability": "capture.create",
        "committed_at": "2026-08-25T12:00:00+00:00",
        "snapshot_before": "sha256:" + "1" * 64,
        "snapshot_after": "sha256:" + "2" * 64,
        "expected_revisions": {},
        "artifact_revisions": {},
        "writes": [],
        "metadata": metadata,
    }
    if schema_version == 2:
        receipt.update({
            "authority": {
                "capability_contract_version": 2,
                "enforced": True,
                "grants": [],
            },
            "request": {
                "channel": "operator",
                "request_id": "request-demo",
                "idempotency_key": "idempotency-demo",
                "intent_sha256": "sha256:" + "3" * 64,
                "approval": {
                    "kind": "operator-approval",
                    "subject_sha256": "sha256:" + "3" * 64,
                },
            },
        })
    return receipt


@pytest.mark.parametrize("metadata", [
    {"credential": "synthetic-secret"},
    {
        "request_id": "ai-request-demo",
        "delivery_id": "delivery-demo",
        "action_id": "garden-shelve",
        "approved_delivery": {
            "delivery_sha256": "sha256:" + "4" * 64,
            "artifact_sha256": {},
        },
        "created_ids": ["/Users/example/private-record"],
        "updated_ids": [],
        "deleted_ids": [],
        "superseded_ids": [],
        "validation": {
            "schemas": "passed",
            "references": "passed",
            "boundaries": "passed",
            "projection": "passed",
        },
    },
    {
        "request_id": "ai-request-demo",
        "delivery_id": "delivery-demo",
        "action_id": "garden.shelve",
        "approved_delivery": {
            "delivery_sha256": "sha256:" + "4" * 64,
            "artifact_sha256": {"../private.txt": "sha256:" + "5" * 64},
        },
        "created_ids": [],
        "updated_ids": [],
        "deleted_ids": [],
        "superseded_ids": [],
        "validation": {
            "schemas": "passed",
            "references": "passed",
            "boundaries": "passed",
            "projection": "passed",
        },
    },
])
def test_receipt_v2_rejects_sensitive_or_absolute_path_metadata(
    mini_repo: Path,
    metadata: dict,
):
    with pytest.raises(ContractValidationError):
        validate_contract(
            mini_repo,
            "transaction-receipt.schema.json",
            _receipt_contract_fixture(schema_version=2, metadata=metadata),
        )


def test_receipt_v1_metadata_remains_readable_for_history(mini_repo: Path):
    validate_contract(
        mini_repo,
        "transaction-receipt.schema.json",
        _receipt_contract_fixture(
            schema_version=1,
            metadata={"historical_extension": {"legacy_shape": True}},
        ),
    )


def test_receipt_v2_allows_only_the_known_safe_ai_metadata_shape(mini_repo: Path):
    validate_contract(
        mini_repo,
        "transaction-receipt.schema.json",
        _receipt_contract_fixture(
            schema_version=2,
            metadata={
                "request_id": "ai-request-demo",
                "delivery_id": "delivery-demo",
                "action_id": "garden.shelve",
                "approved_delivery": {
                    "delivery_sha256": "sha256:" + "4" * 64,
                    "artifact_sha256": {
                        "artifacts/transcription.md": "sha256:" + "5" * 64,
                    },
                },
                "created_ids": ["transcription-garden-demo"],
                "updated_ids": ["garden-demo"],
                "deleted_ids": [],
                "superseded_ids": [],
                "validation": {
                    "schemas": "passed",
                    "references": "passed",
                    "boundaries": "passed",
                    "projection": "passed",
                },
            },
        ),
    )


def test_failed_transaction_removes_new_binary_files(tmp_path: Path):
    root = tmp_path
    target = root / "curriculum/modules/module-demo/units/unit-demo/attachments/note.png"
    service = TransactionService(root)
    with pytest.raises(TransactionFailure):
        service.commit(
            capability="unit.note.append",
            writes={target: b"not-really-a-png"},
            artifact_ids=["unit-demo"],
            validate_state=lambda: ["forced failure"],
        )
    assert not target.exists()
    assert artifact_revision(root, "unit-demo") == 0
    assert not list((root / "operations/transactions").glob("transaction-*.yaml"))


def test_post_commit_bookkeeping_failure_rolls_back_receipt_and_state(tmp_path: Path):
    root = tmp_path
    target = root / "projects/registry/project-demo.yaml"
    target.parent.mkdir(parents=True)
    target.write_text("old\n", encoding="utf-8")

    def fail_bookkeeping(_paths):
        raise RuntimeError("forced touched-ledger failure")

    with pytest.raises(TransactionFailure):
        TransactionService(root).commit(
            capability="project.update",
            writes={target: "new\n"},
            artifact_ids=["project-demo"],
            touched=fail_bookkeeping,
        )

    assert target.read_text(encoding="utf-8") == "old\n"
    assert artifact_revision(root, "project-demo") == 0
    assert not list((root / "operations/transactions").glob("transaction-*.yaml"))


def test_transaction_owned_writes_share_the_receipt_identity(tmp_path: Path):
    root = tmp_path
    target = root / "projects/registry/project-demo.yaml"
    request = root / "operations/ai-actions/requests/request-demo/request.yaml"
    observed: list[str] = []

    def complete_request(transaction_id: str):
        observed.append(transaction_id)
        return {request: f"status: completed\nreceipt_id: {transaction_id}\n"}

    result = TransactionService(root).commit(
        capability="ai-action.demo",
        writes={target: "demo\n"},
        artifact_ids=["project-demo"],
        transaction_writes=complete_request,
    )

    assert observed == [result.transaction_id]
    assert f"receipt_id: {result.transaction_id}" in request.read_text(encoding="utf-8")
    receipt = yaml.safe_load(result.receipt_path.read_text(encoding="utf-8"))
    assert {row["path"] for row in receipt["writes"]} == {
        "operations/ai-actions/requests/request-demo/request.yaml",
        "projects/registry/project-demo.yaml",
    }


def test_incomplete_rollback_is_reported_with_the_unrestored_path(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    root = tmp_path
    target = root / "projects/registry/project-demo.yaml"
    target.parent.mkdir(parents=True)
    target.write_text("old\n", encoding="utf-8")
    original_write = transaction_module._atomic_write_bytes

    def fail_only_when_restoring(path: Path, content: bytes):
        if path == target and content == b"old\n":
            raise TransactionFailure("forced restore failure")
        return original_write(path, content)

    monkeypatch.setattr(transaction_module, "_atomic_write_bytes", fail_only_when_restoring)
    with pytest.raises(TransactionFailure, match="rollback incomplete for: projects/registry/project-demo.yaml"):
        TransactionService(root).commit(
            capability="project.update",
            writes={target: "new\n"},
            artifact_ids=["project-demo"],
            validate_state=lambda: ["forced validation failure"],
        )

    # The caller is told the truth: this is not presented as a clean rollback.
    assert target.read_text(encoding="utf-8") == "new\n"
