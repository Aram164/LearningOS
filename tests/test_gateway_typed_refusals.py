"""Typed refusal classification: codes come from types, never prose (F1, F10).

F1: the write gateway classified refusals by substring search over the
message, which echoes user-supplied ids. A stage id containing "snapshot"
refused as STALE_SNAPSHOT (retryable); the same id containing "approval"
refused as UNCONFIRMED. Every code now comes from the refusal's type or
from a code a catching handler step recorded explicitly.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from types import SimpleNamespace

import pytest
from gateway_helpers import approved_v2_call, approved_v2_envelope, run_v2_capability
from repo_builders import add_curriculum

from learning_os.app import commit as ops_commit
from learning_os.app.ai_actions import AIActionService
from learning_os.app.context import OpContext
from learning_os.app.handlers import ai as ai_handler
from learning_os.app.handlers.ai import _ai_refusal
from learning_os.app.handlers.resume import _render as _render_resume
from learning_os.app.lock import operator_lock as _operator_lock
from learning_os.app.outcomes import refusal_from_failure as _refusal_from_failure
from learning_os.app.outcomes import take_gateway_refusal as _take_gateway_refusal
from learning_os.app.pipeline import _classify_failure, _v2_exit_code, run_cli
from learning_os.app.proposal import TransactionProposal
from learning_os.domain.ai_errors import (
    DeliveryBindingError,
    DeliveryIdempotencyConflict,
    DeliveryRevisionConflict,
    DeliveryScopeError,
    DeliveryValidationError,
    StaleDeliveryError,
)
from learning_os.domain.failures import (
    AmbiguousMigration,
    StaleSnapshot,
    TransactionConflict,
    TransactionFailure,
    TransactionScopeError,
    TransactionSnapshotConflict,
    Unconfirmed,
    ValidationFailed,
    WriteRefused,
)
from learning_os.domain.validation import Issue
from learning_os.store.contracts.gateway import (
    GatewayRequestContext,
    current_gateway_request,
    gateway_request_context,
)
from learning_os.store.contracts.write_scopes import WriteScopeError
from learning_os.store.layout import PathBoundaryError
from learning_os.store.session_ledger import DEFAULT_SESSION_CHANNEL
from learning_os.store.transactions import (
    ReplayEvidenceError,
    TransactionIdempotencyConflict,
    TransactionRecoveryConflict,
    TransactionRollbackIncomplete,
    TransactionService,
    TransactionValidationFailure,
)


def _write_transaction(root, writes, *, capability="legacy.write",
                       expected_revisions=None, artifact_ids=(),
                       deletes=(), metadata=None, validate_extra=None):
    """The dissolved support._write_transaction construction, inlined."""
    request = current_gateway_request()
    ctx = OpContext(
        root=root, operation=capability,
        channel=request.channel if request is not None else DEFAULT_SESSION_CHANNEL,
        invocation="command", gateway=request)
    proposal = TransactionProposal(
        capability=capability, writes=writes, artifact_ids=artifact_ids,
        deletes=deletes, expected_revisions=expected_revisions or {},
        metadata=metadata, validate_extra=validate_extra)
    return ops_commit.commit_proposal(ctx, proposal)

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
    from learning_os.domain.failures import Refusal

    error = _classify_failure(
        3,
        "artifact revision conflict — reload the affected record before writing",
        refusal=Refusal("REVISION_CONFLICT", True),
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
    """The handler raises the old catch's type, message and exit (SPEC (be))."""

    class _RefusingService(AIActionService):
        def apply_delivery_proposal(self, *args, **kwargs):
            raise failure

    monkeypatch.setattr(ai_handler, "AIActionService", _RefusingService)
    req = {
        "delivery_id": "ai-delivery-typed",
        "delivery_sha256": "sha256:" + "0" * 64,
        "artifact_sha256": {},
        "expected_snapshot": "sha256:" + "0" * 64,
        "expected_revision": None,
    }
    context = _ai_request_context()
    ctx = OpContext(root=mini_repo, operation="ai-action.delivery.apply",
                    channel="operator", invocation="command", gateway=context)
    with gateway_request_context(context), pytest.raises(WriteRefused) as raised:
        ai_handler.ai_action_apply_delivery(ctx, req)
    typed = raised.value
    assert (typed.gateway_code, typed.gateway_retryable) == (
        refusal or ("INVALID_REQUEST", False))
    assert typed.exit_code == exit_code
    assert str(typed) == str(failure)
    assert typed.gateway_message == str(failure)
    assert typed.__cause__ is failure


@pytest.mark.parametrize(
    ("engine", "exit_code", "refusal", "message"),
    [
        (TransactionConflict({"a": (1, 2)}), 3, ("REVISION_CONFLICT", True), None),
        (TransactionSnapshotConflict("sha256:e", "sha256:a"), 3,
         ("STALE_SNAPSHOT", True), None),
        (TransactionIdempotencyConflict("reused"), 2, ("INVALID_REQUEST", False),
         "delivery idempotency conflict: reused"),
        (TransactionFailure("engine refused"), 2, ("INVALID_REQUEST", False),
         "delivery transaction failed: engine refused"),
    ],
)
def test_ai_apply_commit_failures_translate_like_the_old_chain(
    engine, exit_code, refusal, message
):
    """Commit-time: the service chain, then the old command catch (SPEC (be))."""
    translated = AIActionService._translate_commit_failure(engine)
    typed = ai_handler._refusal(translated, "ai-action.delivery.apply")
    assert (typed.gateway_code, typed.gateway_retryable) == refusal
    assert typed.exit_code == exit_code
    assert str(typed) == (message or str(engine))
    assert AIActionService._translate_commit_failure(ValueError("x")) is None


@pytest.mark.parametrize(
    ("engine", "exit_code", "refusal", "message"),
    [
        (TransactionConflict({"a": (1, 2)}), 3, ("REVISION_CONFLICT", True), None),
        (TransactionSnapshotConflict("sha256:e", "sha256:a"), 3,
         ("STALE_SNAPSHOT", True), None),
        (TransactionIdempotencyConflict("reused"), 2, ("INVALID_REQUEST", False),
         "delivery idempotency conflict: reused"),
        (TransactionFailure("engine refused"), 2, ("INVALID_REQUEST", False),
         "delivery transaction failed: engine refused"),
    ],
)
def test_ai_apply_commit_failure_through_the_pipeline_path(
    mini_repo: Path, monkeypatch, engine, exit_code, refusal, message
):
    """Commit-time: the handler's translate over real commit wiring (SPEC (be)).

    The converted handler returns its Result carrying the composed translate;
    the real commit_proposal runs the engine, which raises; the translated
    typed refusal propagates with the old code, retryability and return, and
    the CLI dispatch renders both streams from it.
    """
    expected = message or str(engine)

    class _ProposalService(AIActionService):
        def apply_delivery_proposal(self, *args, **kwargs):
            return (
                TransactionProposal(
                    capability="ai-action.delivery.apply",
                    writes={}, artifact_ids=(), deletes=None, touched=None,
                ),
                None, [],
            )

    class _RaisingTransactionService:
        def __init__(self, root, clock=None):
            self.root = root

        def commit(self, **kwargs):
            raise engine

    monkeypatch.setattr(ai_handler, "AIActionService", _ProposalService)
    monkeypatch.setattr(
        ops_commit, "TransactionService", _RaisingTransactionService)
    context = _ai_request_context()
    req = {
        "delivery_id": "ai-delivery-typed",
        "delivery_sha256": "sha256:" + "0" * 64,
        "artifact_sha256": {},
        "expected_snapshot": "sha256:" + "0" * 64,
        "expected_revision": None,
    }
    with gateway_request_context(context):
        ctx = OpContext(root=mini_repo, operation="ai-action.delivery.apply",
                        channel="operator", invocation="command", gateway=context)
        result = ai_handler.ai_action_apply_delivery(ctx, req)
        assert result.proposal is not None
        with pytest.raises(WriteRefused) as raised:
            ops_commit.commit_proposal(ctx, result.proposal)
        typed = raised.value
        assert (typed.gateway_code, typed.gateway_retryable) == refusal
        assert typed.exit_code == exit_code
        assert str(typed) == expected
        assert typed.gateway_message == expected.strip()
        assert typed.__cause__ is engine
        args = SimpleNamespace(
            delivery_id=req["delivery_id"],
            delivery_sha256=req["delivery_sha256"],
            artifact_sha256=req["artifact_sha256"],
            expected_snapshot=req["expected_snapshot"],
            expected_revision=req["expected_revision"], json=True,
        )
        outcome = run_cli(mini_repo, "ai-action.delivery.apply", args)
    assert outcome.exit_code == exit_code
    assert outcome.ok is False
    assert outcome.commit == "none"
    assert outcome.stdout == ""
    error = json.loads(outcome.stderr)["error"]
    assert error["code"] == refusal[0]
    assert error["retryable"] is refusal[1]
    assert error["message"] == expected


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
    from learning_os.app import commit as commit_module

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
        commit_module,
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
    assert ".venv/bin/python tools/seal_envelope.py --capability stage.note.write" in rendered
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
