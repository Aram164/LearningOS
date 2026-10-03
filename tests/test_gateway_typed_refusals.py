"""Typed refusal classification: codes come from types, never prose (F1, F10).

F1: the write gateway classified refusals by substring search over the
message, which echoes user-supplied ids. A stage id containing "snapshot"
refused as STALE_SNAPSHOT (retryable); the same id containing "approval"
refused as UNCONFIRMED. Every code now comes from the refusal's type or
from a code a catching handler step recorded explicitly.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from types import SimpleNamespace

import pytest
from gateway_helpers import approved_v2_call, approved_v2_envelope, run_v2_capability
from repo_builders import add_curriculum

from learning_os.ai_actions import (
    AIActionService,
    DeliveryBindingError,
    DeliveryIdempotencyConflict,
    DeliveryRevisionConflict,
    DeliveryScopeError,
    DeliveryValidationError,
    StaleDeliveryError,
)
from learning_os.commands import ai as ai_command
from learning_os.commands.ai import _ai_refusal
from learning_os.commands.capability import _classify_failure, _v2_exit_code
from learning_os.commands.resume import _render as _render_resume
from learning_os.commands.support import (
    AmbiguousMigration,
    StaleSnapshot,
    Unconfirmed,
    ValidationFailed,
    WriteRefused,
    _operator_lock,
    _refusal_from_failure,
    _take_gateway_refusal,
    _write_transaction,
)
from learning_os.contracts.gateway import (
    GatewayRequestContext,
    gateway_request_context,
)
from learning_os.contracts.write_scopes import WriteScopeError
from learning_os.errors import TransactionFailure
from learning_os.pathing import PathBoundaryError
from learning_os.rules.common import Issue
from learning_os.transactions import (
    ReplayEvidenceError,
    TransactionConflict,
    TransactionIdempotencyConflict,
    TransactionRecoveryConflict,
    TransactionRollbackIncomplete,
    TransactionScopeError,
    TransactionService,
    TransactionSnapshotConflict,
    TransactionValidationFailure,
)

FORMER_TOKENS = [
    "snapshot",
    "projection",
    "publication",
    "approval",
    "approve",
    "confirm",
    "symlink",
    "ambiguous",
    "idempotency",
    "validation failed",
    "out of scope",
]


def _key_slug(token: str) -> str:
    return re.sub(r"[^A-Za-z0-9._:-]", "-", token)


@pytest.mark.parametrize("token", [*FORMER_TOKENS, "plain"])
def test_token_in_unknown_stage_id_never_changes_the_refusal(
    mini_repo: Path, token: str
):
    """The same not-found refusal refuses identically whatever the id names."""
    add_curriculum(mini_repo)
    stage_id = "stage-plain-review" if token == "plain" else f"stage-{token}-review"
    proc = approved_v2_call(
        mini_repo,
        capability="stage.progress.update",
        payload={
            "unit_id": "unit-demo-l01",
            "stage_id": stage_id,
            "status": "active",
        },
        artifact_ids=["unit-demo-l01", "study-map-demo-l01"],
        idempotency_key=f"typed-refusal-{_key_slug(token)}",
    )
    assert proc.returncode == 2, proc.stderr or proc.stdout
    body = json.loads(proc.stdout)
    assert body["ok"] is False
    assert body["error"]["code"] == "INVALID_REQUEST"
    assert body["error"]["retryable"] is False
    # The token-bearing id is echoed in the message — and ignored.
    assert stage_id in body["error"]["message"]


def test_misclassified_refusals_are_invalid_request_by_type():
    """F1's known misclassifications carry no type, so no foreign code."""
    cases = [
        WriteRefused("stage not found: stage-snapshot-review"),
        ValueError("source fingerprint seed must be a SHA-256 snapshot ID"),
        WriteRefused("unit unit-demo-l01 has ambiguous study maps"),
        WriteRefused("stage stage-x is missing or ambiguous in this unit"),
        WriteRefused("route route-x is ambiguous in its module"),
        WriteRefused(
            "sid: replacement dossier for 'unit-demo-l01' is not needed "
            "(no approved dossier basis changes there)"
        ),
        TransactionFailure(
            "transaction expected snapshot does not match its gateway approval"
        ),
        TransactionFailure("idempotency ledger is unreadable: /x: oops"),
    ]
    for failure in cases:
        mapped = _refusal_from_failure(failure)
        assert mapped is None or mapped == ("INVALID_REQUEST", False), failure
        error = _classify_failure(2, str(failure), failure=failure)
        assert error["code"] == "INVALID_REQUEST", failure
        assert error["retryable"] is False, failure


def test_genuine_refusal_types_keep_their_codes():
    """Every legitimately produced code still maps from its own type."""
    conflicts = {"unit-demo-l01": (7, 0)}
    cases = [
        (StaleSnapshot("snapshot changed"), ("STALE_SNAPSHOT", True)),
        (AmbiguousMigration("ambiguous migration is not applicable"),
         ("AMBIGUOUS_MIGRATION", False)),
        (ValidationFailed("canonical validation failed: E X"),
         ("VALIDATION_FAILED", False)),
        (Unconfirmed("requires approved-delivery approval"),
         ("UNCONFIRMED", False)),
        (TransactionConflict(conflicts), ("REVISION_CONFLICT", True)),
        (TransactionSnapshotConflict("expected", "actual"),
         ("STALE_SNAPSHOT", True)),
        (TransactionIdempotencyConflict("already used"),
         ("IDEMPOTENCY_CONFLICT", False)),
        (TransactionScopeError("unknown write authority x; refusing y"),
         ("OUT_OF_SCOPE", False)),
        (TransactionValidationFailure("transaction failed canonical validation: E"),
         ("VALIDATION_FAILED", False)),
        (TransactionRollbackIncomplete("x; rollback incomplete for: y"),
         ("INTERNAL_FAILURE", True)),
        (TransactionFailure("rolled back but unrestorable",
                            pre_existing_defect=True),
         ("VALIDATION_FAILED", False)),
        (WriteScopeError("transaction target escapes repository: ../x"),
         ("OUT_OF_SCOPE", False)),
        (PathBoundaryError("too many symlink hops under a: b"),
         ("OUT_OF_SCOPE", False)),
        (ReplayEvidenceError("ledger row contradicts its receipt"),
         ("INTERNAL_FAILURE", False)),
        (TransactionRecoveryConflict("cannot prove paths", transaction_id="t"),
         ("INTERNAL_FAILURE", False)),
    ]
    for failure, expected in cases:
        assert _refusal_from_failure(failure) == expected, failure
        error = _classify_failure(2, str(failure), failure=failure)
        assert error["code"] == expected[0], failure
        assert error["retryable"] is expected[1], failure
        assert error["message"] == str(failure), failure


def test_carried_refusal_wins_over_nothing_else():
    """A handler-recorded code crosses the boundary; prose never overrides."""
    error = _classify_failure(
        3,
        "artifact revision conflict — reload the affected record before writing",
        refusal=("REVISION_CONFLICT", True),
    )
    assert error["code"] == "REVISION_CONFLICT"
    assert error["retryable"] is True
    # And a bare exit code with no carried type is just an invalid request.
    bare = _classify_failure(3, "reviewed content changed before use")
    assert bare["code"] == "INVALID_REQUEST"


def test_stale_snapshot_always_exits_three():
    assert _v2_exit_code(2, {"code": "STALE_SNAPSHOT"}) == 3
    assert _v2_exit_code(3, {"code": "STALE_SNAPSHOT"}) == 3
    assert _v2_exit_code(3, {"code": "REVISION_CONFLICT"}) == 3
    assert _v2_exit_code(2, {"code": "INVALID_REQUEST"}) == 2
    assert _v2_exit_code(2, {"code": "UNCONFIRMED"}) == 2
    assert _v2_exit_code(0, None) == 0


def test_ai_refusal_maps_delivery_subtypes_by_type():
    assert _ai_refusal(DeliveryScopeError("no write scope")) == ("OUT_OF_SCOPE", False)
    assert _ai_refusal(DeliveryIdempotencyConflict("conflict")) == (
        "IDEMPOTENCY_CONFLICT", False)
    assert _ai_refusal(DeliveryBindingError("hash does not match")) == (
        "UNCONFIRMED", False)
    assert _ai_refusal(DeliveryValidationError("must contain a mapping")) is None


def _ai_request_context() -> GatewayRequestContext:
    return GatewayRequestContext(
        request_id="request-ai-typed-001",
        idempotency_key="ai-typed-001",
        capability="ai-action.delivery.apply",
        channel="operator",
        intent_sha256="sha256:" + "1" * 64,
        approval_kind="approved-delivery",
        approval_subject_sha256="sha256:" + "1" * 64,
    )


@pytest.mark.parametrize(
    ("failure", "exit_code", "refusal"),
    [
        (StaleDeliveryError("approved delivery snapshot conflict (expected e, actual a)"),
         3, ("STALE_SNAPSHOT", True)),
        (StaleDeliveryError("Garden target changed after request preparation"),
         3, ("STALE_SNAPSHOT", True)),
        (DeliveryRevisionConflict("artifact revision conflict (a: expected 1, actual 2)"),
         3, ("REVISION_CONFLICT", True)),
        (DeliveryScopeError("capability x declares no write scope; refusing to write y"),
         2, ("OUT_OF_SCOPE", False)),
        (DeliveryIdempotencyConflict("delivery idempotency conflict: reused"),
         2, ("IDEMPOTENCY_CONFLICT", False)),
        (DeliveryBindingError("approved delivery content hash does not match the imported bytes"),
         2, ("UNCONFIRMED", False)),
        (DeliveryValidationError("delivery.yaml must contain a mapping"), 2, None),
    ],
)
def test_ai_apply_handler_carries_typed_refusals(
    mini_repo: Path, monkeypatch, failure, exit_code, refusal
):
    """The ai handler's catches record the type beside the unchanged exit code."""

    class _RefusingService(AIActionService):
        def apply_delivery(self, *args, **kwargs):
            raise failure

    monkeypatch.setattr(ai_command, "AIActionService", _RefusingService)
    args = argparse.Namespace(
        root=str(mini_repo),
        delivery_id="ai-delivery-typed",
        delivery_sha256="sha256:" + "0" * 64,
        artifact_sha256={},
        expected_snapshot="sha256:" + "0" * 64,
        expected_revision=None,
    )
    with gateway_request_context(_ai_request_context()):
        code = ai_command.cmd_ai_action_apply_delivery(args)
    assert code == exit_code
    assert _take_gateway_refusal() == refusal


def test_ai_apply_with_the_wrong_approval_kind_is_unconfirmed(mini_repo: Path):
    """An envelope approved for another path is unconfirmed, not invalid."""
    envelope = approved_v2_envelope(
        mini_repo,
        capability="ai-action.delivery.apply",
        payload={
            "delivery_id": "ai-delivery-typed",
            "delivery_sha256": "sha256:" + "0" * 64,
            "artifact_sha256": {},
        },
        artifact_ids=[],
        idempotency_key="ai-typed-approval-001",
    )
    assert envelope["approval"]["kind"] == "operator-approval"
    proc = run_v2_capability(mini_repo, envelope)
    assert proc.returncode == 2, proc.stderr or proc.stdout
    body = json.loads(proc.stdout)
    assert body["error"]["code"] == "UNCONFIRMED"
    assert body["error"]["retryable"] is False
    assert "approved-delivery approval" in body["error"]["message"]


def test_unready_migration_plan_is_ambiguous_migration(mini_repo: Path):
    """The genuine migration refusal keeps its code end to end."""
    add_curriculum(mini_repo)
    envelope = approved_v2_envelope(
        mini_repo,
        capability="route.identity.migrate",
        payload={"plan_sha256": "sha256:" + "0" * 64},
        artifact_ids=["module-demo", "unit-demo-l01"],
        idempotency_key="typed-migration-001",
    )
    proc = run_v2_capability(mini_repo, envelope)
    assert proc.returncode == 2, proc.stderr or proc.stdout
    body = json.loads(proc.stdout)
    assert body["error"]["code"] == "AMBIGUOUS_MIGRATION"
    assert body["error"]["retryable"] is False
    assert "resolve problems" in body["error"]["message"]


def test_failed_canonical_validation_is_typed(mini_repo: Path):
    """The commit's validation gate raises typed, not prose to match."""
    target = mini_repo / "work/inbox/typed-validation.md"
    service = TransactionService(mini_repo)
    with pytest.raises(TransactionValidationFailure, match="canonical validation"):
        service.commit(
            capability="capture.create",
            writes={target: "new\n"},
            artifact_ids=["capture:typed-validation"],
            validate_state=lambda: ["E UNIT-TEST: induced failure"],
        )
    assert not target.exists()


def test_write_transaction_records_a_validation_refusal(
    mini_repo: Path, monkeypatch
):
    """A validation failure crosses the (code, errors) channel typed."""
    from learning_os.commands import support as support_module

    key = "typed-validation-write-001"
    request_artifact = f"capture-request:{key}"
    context = GatewayRequestContext(
        request_id=f"request-{key}",
        idempotency_key=key,
        capability="capture.create",
        channel="operator",
        intent_sha256="sha256:" + "2" * 64,
        approval_kind="operator-approval",
        approval_subject_sha256="sha256:" + "2" * 64,
    )
    monkeypatch.setattr(
        support_module,
        "validate",
        lambda repo, online=False: [
            Issue(severity="E", code="UNIT-TEST", message="induced failure",
                  path="work/inbox/typed.md")
        ],
    )
    target = mini_repo / "work/inbox/typed.md"
    with gateway_request_context(context):
        with _operator_lock(mini_repo):
            code, errors, _confirmation = _write_transaction(
                mini_repo,
                {target: "new\n"},
                capability="capture.create",
                expected_revisions={request_artifact: 0},
                artifact_ids=[request_artifact],
            )
    assert code == 2
    assert any("canonical validation" in issue for issue in errors)
    assert _take_gateway_refusal() == ("VALIDATION_FAILED", False)
    assert not target.exists()


def test_out_of_scope_write_records_a_scope_refusal(mini_repo: Path):
    """A write escaping the repository crosses typed as OUT_OF_SCOPE."""
    key = "typed-scope-001"
    context = GatewayRequestContext(
        request_id=f"request-{key}",
        idempotency_key=key,
        capability="capture.create",
        channel="operator",
        intent_sha256="sha256:" + "3" * 64,
        approval_kind="operator-approval",
        approval_subject_sha256="sha256:" + "3" * 64,
    )
    escape = mini_repo / ".." / "typed-escape.md"
    with gateway_request_context(context):
        with _operator_lock(mini_repo):
            code, errors, _confirmation = _write_transaction(
                mini_repo,
                {escape: "new\n"},
                capability="capture.create",
                expected_revisions={},
                artifact_ids=[],
            )
    assert code == 2
    assert errors
    assert _take_gateway_refusal() == ("OUT_OF_SCOPE", False)
    assert not escape.exists()


def test_resume_next_line_without_requirement_names_the_envelope_path():
    """F10: the Next line seals and submits instead of bare stage-note."""
    dossier = SimpleNamespace(unit_id="unit-demo-l01", stage_id="stage-demo")
    rendered = _render_resume(
        dossier, None, [], [], [],
        {"module": "Demo Module", "unit": "Expected value"}, "test-detail",
    )
    assert "los stage-note" not in rendered
    assert "tools/seal_envelope.py --capability stage.note.write" in rendered
    assert "{unit_id, stage_id, text}" in rendered
    assert "--guards auto" in rendered
    assert "los capability stage.note.write --payload-file ENVELOPE.json" in rendered


def test_resume_next_line_with_requirement_still_names_observe():
    """The requirement branch writes directly, so it keeps its command."""
    dossier = SimpleNamespace(unit_id="unit-demo-l01", stage_id="stage-demo")
    rendered = _render_resume(
        dossier, {"id": "req-demo-001"}, [], [], [],
        {"module": "Demo Module", "unit": "Expected value"}, "test-detail",
    )
    assert "los observe req-demo-001 --activity <what-you-did>" in rendered
