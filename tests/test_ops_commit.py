"""commit_proposal tests (S13 Task 2): engine call shapes, omissions, failures.

The kwargs reaching ``TransactionService.commit`` equal the pinned
pre-change shapes for the standard legacy call and the AI-delivery call
(``scratch/S13-completion-20261009/evidence/commit-kwarg-baseline.json``),
with no added keyword on the AI shape. Failure chaining, translate-first order
and the STANDARD hook wirings are pinned against the moved legacy body.
"""

from __future__ import annotations

import types
from pathlib import Path

import pytest
from test_ai_actions import apply_approved_delivery, make_delivery

from learning_os.app import commit as ops_commit
from learning_os.app import outcomes as plumbing
from learning_os.app.context import OpContext
from learning_os.app.proposal import TransactionProposal
from learning_os.domain.ai_errors import (
    DeliveryRevisionConflict,
    DeliveryValidationError,
    StaleDeliveryError,
)
from learning_os.domain.codes import (
    IDEMPOTENCY_CONFLICT,
    REVISION_CONFLICT,
    VALIDATION_FAILED,
)
from learning_os.domain.failures import (
    PostCommitFailure,
    ProjectionFailure,
    TransactionConflict,
    TransactionFailure,
    TransactionIdempotencyConflict,
    TransactionSnapshotConflict,
    TransactionValidationFailure,
)
from learning_os.store import session_ledger as session_support
from learning_os.store.contracts.gateway import (
    GatewayRequestContext,
    current_gateway_request,
    gateway_request_context,
)
from learning_os.store.session_ledger import DEFAULT_SESSION_CHANNEL

# Pinned from the pre-change capture (evidence/commit-kwarg-baseline.json).
STANDARD_KEYS = [
    "artifact_ids", "capability", "deletes", "expected_revisions",
    "metadata", "publish", "rollback_publish", "touched",
    "validate_state", "writes",
]
AI_KEYS = [
    "artifact_ids", "capability", "expected_revisions",
    "expected_snapshot", "metadata", "publish", "rollback_publish",
    "transaction_writes", "validate_state", "write_authorities", "writes",
]


def _gateway_context(capability: str, suffix: str) -> GatewayRequestContext:
    intent = "sha256:" + "c" * 64
    return GatewayRequestContext(
        request_id=f"request-{suffix}",
        idempotency_key=f"idempotency-{suffix}",
        capability=capability,
        channel="operator",
        intent_sha256=intent,
        approval_kind="operator-approval",
        approval_subject_sha256=intent,
    )


def _ctx(root: Path, capability: str, gateway=None) -> OpContext:
    return OpContext(
        root=root, operation=capability, channel="operator",
        invocation="command", gateway=gateway,
    )


def _legacy_write_transaction(root, writes, *, capability="legacy.write",
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


def _stub_result():
    return types.SimpleNamespace(
        receipt_path=Path("operations/transactions/transaction-20260101-000000-001.yaml"),
        transaction_id="transaction-20260101-000000-001",
        revisions={"a:1": 2},
        snapshot_after="sha256:stub",
        replayed=False,
    )


def test_no_gateway_refusal_text_is_unchanged(mini_repo: Path):
    assert ops_commit.current_gateway_request() is None
    proposal = TransactionProposal(
        capability="capture.create", writes={}, artifact_ids=())
    code, errors, confirmation = ops_commit.commit_proposal(
        _ctx(mini_repo, "capture.create"), proposal)
    assert code == 2
    assert errors == [
        "canonical writes must use GatewayEnvelopeV2; direct CLI application "
        "is disabled — apply it with `los capability capture.create "
        "--payload-file ENVELOPE.json` (payload schema: `los capabilities "
        "capture.create --json`; envelope: WORKFLOWS §25c)"
    ]
    assert confirmation == {}


def test_legacy_wrapper_forwards_context_and_proposal(mini_repo: Path, monkeypatch):
    seen = {}

    def capture(ctx, proposal):
        seen["ctx"] = ctx
        seen["proposal"] = proposal
        return 0, [], {"ok": True}

    monkeypatch.setattr(ops_commit, "commit_proposal", capture)
    writes = {mini_repo / "work/inbox/x.md": "x\n"}
    artifacts = ["a:1"]
    deletes: list = []
    revisions = {"a:1": 0}
    metadata = {"k": "v"}

    def extra(repo, issues):
        return []

    context = _gateway_context("capture.create", "wrap")
    with gateway_request_context(context):
        assert _legacy_write_transaction(
            mini_repo, writes, capability="capture.create",
            expected_revisions=revisions, artifact_ids=artifacts,
            deletes=deletes, metadata=metadata,
            validate_extra=extra) == (0, [], {"ok": True})
    ctx = seen["ctx"]
    assert ctx.root == mini_repo
    assert ctx.operation == "capture.create"
    assert ctx.channel == "operator"
    assert ctx.invocation == "command"
    assert ctx.gateway is context
    proposal = seen["proposal"]
    assert proposal.capability == "capture.create"
    assert proposal.writes is writes
    assert proposal.artifact_ids is artifacts
    assert proposal.deletes is deletes
    assert proposal.expected_revisions is revisions
    assert proposal.metadata is metadata
    assert proposal.validate_extra is extra
    assert proposal.validate_state == "STANDARD"
    assert proposal.publish == "STANDARD"
    assert proposal.rollback_publish == "STANDARD"
    assert proposal.touched == "STANDARD"
    assert proposal.clock is None
    assert proposal.expected_snapshot is None
    assert proposal.translate is None


def test_legacy_wrapper_without_gateway_names_operator_channel(
        mini_repo: Path, monkeypatch):
    seen = {}

    def capture(ctx, proposal):
        seen["ctx"] = ctx
        return 2, ["refused"], {}

    monkeypatch.setattr(ops_commit, "commit_proposal", capture)
    assert ops_commit.current_gateway_request() is None
    code, errors, _ = _legacy_write_transaction(
        mini_repo, {}, capability="capture.create")
    assert (code, errors) == (2, ["refused"])
    assert seen["ctx"].channel == "operator"
    assert seen["ctx"].gateway is None


def test_standard_shape_kwargs_and_constructor(mini_repo: Path, monkeypatch):
    import learning_os.store.transactions as transaction_module

    captured: dict = {}
    init_kwargs: dict = {}
    real_class = ops_commit.TransactionService

    class RecordingService(real_class):
        def __init__(self, root, **kwargs):
            init_kwargs.update(kwargs)
            super().__init__(root, **kwargs)

    def recording_commit(self, *args, **kwargs):
        captured.update(kwargs)
        return _stub_result()

    monkeypatch.setattr(ops_commit, "TransactionService", RecordingService)
    monkeypatch.setattr(
        transaction_module.TransactionService, "commit", recording_commit)
    writes = {mini_repo / "work/inbox/std.md": "std\n"}
    artifacts = ["capture-test:std"]
    revisions = {"capture-test:std": 0}
    metadata = {"origin": "test"}
    proposal = TransactionProposal(
        capability="capture.create", writes=writes, artifact_ids=artifacts,
        expected_revisions=revisions, metadata=metadata)
    with gateway_request_context(_gateway_context("capture.create", "std")):
        code, errors, confirmation = ops_commit.commit_proposal(
            _ctx(mini_repo, "capture.create"), proposal)
    assert (code, errors) == (0, [])
    assert confirmation["transaction_id"] == "transaction-20260101-000000-001"
    assert sorted(captured) == STANDARD_KEYS
    assert captured["writes"] is writes
    assert captured["artifact_ids"] is artifacts
    assert captured["expected_revisions"] is revisions
    assert captured["metadata"] is metadata
    assert captured["deletes"] == ()
    assert callable(captured["validate_state"])
    assert callable(captured["publish"])
    assert callable(captured["rollback_publish"])
    assert callable(captured["touched"])
    assert "expected_snapshot" not in captured
    assert "transaction_writes" not in captured
    assert "write_authorities" not in captured
    assert init_kwargs == {}


def test_ai_shape_kwargs_constructor_and_omissions(mini_repo: Path, monkeypatch):
    import learning_os.store.transactions as transaction_module

    captured: dict = {}
    init_kwargs: dict = {}
    real_class = ops_commit.TransactionService

    class RecordingService(real_class):
        def __init__(self, root, **kwargs):
            init_kwargs.update(kwargs)
            super().__init__(root, **kwargs)

    def recording_commit(self, *args, **kwargs):
        captured.update(kwargs)
        return _stub_result()

    monkeypatch.setattr(ops_commit, "TransactionService", RecordingService)
    monkeypatch.setattr(
        transaction_module.TransactionService, "commit", recording_commit)

    def validate_state():
        return []

    def publish(snapshot_after_id=None):
        return "sha256:ai"

    def rollback_publish():
        return None

    def transaction_writes(transaction_id):
        return {}

    clock = object()
    writes = {mini_repo / "knowledge/garden/ai.md": "ai\n"}
    artifacts = {"target-1", "target-2"}
    revisions = {"target-1": 0, "target-2": 0}
    authorities = {mini_repo / "knowledge/garden/ai.md": "garden.add-transcription"}
    proposal = TransactionProposal(
        capability="ai-action.delivery.apply", writes=writes, deletes=None,
        artifact_ids=artifacts, expected_revisions=revisions,
        metadata={"request_id": "r"}, write_authorities=authorities,
        transaction_writes=transaction_writes,
        validate_state=validate_state, publish=publish,
        rollback_publish=rollback_publish, touched=None,
        clock=clock, expected_snapshot="sha256:ai-snapshot",
        translate=lambda exc: None)
    with gateway_request_context(
            _gateway_context("ai-action.delivery.apply", "ai")):
        code, errors, _ = ops_commit.commit_proposal(
            _ctx(mini_repo, "ai-action.delivery.apply"), proposal)
    assert (code, errors) == (0, [])
    assert sorted(captured) == AI_KEYS
    assert "deletes" not in captured
    assert captured["writes"] is writes
    assert captured["artifact_ids"] is artifacts
    assert captured["expected_revisions"] is revisions
    assert captured["write_authorities"] is authorities
    assert captured["expected_snapshot"] == "sha256:ai-snapshot"
    assert captured["validate_state"] is validate_state
    assert captured["publish"] is publish
    assert captured["rollback_publish"] is rollback_publish
    assert captured["transaction_writes"] is transaction_writes
    assert "touched" not in captured
    assert init_kwargs == {"clock": clock}


def test_ai_shape_matches_the_live_ai_call(mini_repo: Path, tmp_path: Path, monkeypatch):
    """The AI proposal shape mirrors the real service call, key for key.

    Since S15 the service returns its proposal and the commit step makes the
    engine call, so the live call is captured there; AI_KEYS and the clock-only
    constructor are the pre-conversion call's shape.
    """
    import learning_os.store.transactions as transaction_module

    for rel in ("operations/ai-actions/requests",
                "operations/ai-actions/deliveries",
                "operations/ai-actions/garden-state",
                "knowledge/garden"):
        (mini_repo / rel).mkdir(parents=True, exist_ok=True)
    (mini_repo / "knowledge/garden/handwritten-import-registration.md").write_text(
        "# Import registration\n\nThe decorator stores the function during import. #python #optimizer\n",
        encoding="utf-8",
    )
    (mini_repo / "operations/ai-actions/relationships.yaml").write_text(
        "schema_version: 1\nrelationships: []\n", encoding="utf-8")
    app, request, source = make_delivery(mini_repo, tmp_path)
    delivery = app.import_delivery(source)

    live_kwargs: dict = {}
    live_init: dict = {}
    real_commit = transaction_module.TransactionService.commit
    real_class = transaction_module.TransactionService

    class LiveRecordingService(real_class):
        def __init__(self, root, **kwargs):
            live_init.update(kwargs)
            super().__init__(root, **kwargs)

    def live_recording_commit(self, *args, **kwargs):
        live_kwargs.update(kwargs)
        return real_commit(self, *args, **kwargs)

    monkeypatch.setattr(ops_commit, "TransactionService", LiveRecordingService)
    monkeypatch.setattr(
        transaction_module.TransactionService, "commit", live_recording_commit)
    receipt = apply_approved_delivery(app, delivery["id"])
    assert receipt["status"] == "committed"
    assert sorted(live_kwargs) == AI_KEYS
    assert sorted(live_init) == ["clock"]

    # The same engine call through a proposal: exact omission, containers,
    # callbacks and constructor clock, captured from the actual AI call.
    seen_kwargs: dict = {}
    seen_init: dict = {}

    class ProposalRecordingService(real_class):
        def __init__(self, root, **kwargs):
            seen_init.update(kwargs)
            super().__init__(root, **kwargs)

    def proposal_recording_commit(self, *args, **kwargs):
        seen_kwargs.update(kwargs)
        return _stub_result()

    monkeypatch.setattr(ops_commit, "TransactionService", ProposalRecordingService)
    monkeypatch.setattr(
        transaction_module.TransactionService, "commit", proposal_recording_commit)
    proposal = TransactionProposal(
        capability="ai-action.delivery.apply", writes=live_kwargs["writes"],
        deletes=None, artifact_ids=live_kwargs["artifact_ids"],
        expected_revisions=live_kwargs["expected_revisions"],
        metadata=live_kwargs["metadata"],
        write_authorities=live_kwargs["write_authorities"],
        transaction_writes=live_kwargs["transaction_writes"],
        validate_state=live_kwargs["validate_state"],
        publish=live_kwargs["publish"],
        rollback_publish=live_kwargs["rollback_publish"],
        touched=None, clock=live_init["clock"],
        expected_snapshot=live_kwargs["expected_snapshot"],
        translate=lambda exc: None)
    with gateway_request_context(
            _gateway_context("ai-action.delivery.apply", "ai-live")):
        code, errors, _ = ops_commit.commit_proposal(
            _ctx(mini_repo, "ai-action.delivery.apply"), proposal)
    assert (code, errors) == (0, [])
    assert sorted(seen_kwargs) == sorted(live_kwargs)
    assert list(seen_kwargs) == list(live_kwargs)
    for key, value in live_kwargs.items():
        if isinstance(value, (str, int, bool)) or value is None:
            assert type(seen_kwargs[key]) is type(value)
            assert seen_kwargs[key] == value
        else:
            assert seen_kwargs[key] is value
    assert seen_init == live_init


def test_conflict_returns_3_with_legacy_lines_and_refusal(
        mini_repo: Path, monkeypatch, capsys):
    import learning_os.store.transactions as transaction_module

    def raising_commit(self, *args, **kwargs):
        raise TransactionConflict({"a:1": (0, 1)})

    monkeypatch.setattr(
        transaction_module.TransactionService, "commit", raising_commit)
    proposal = TransactionProposal(
        capability="capture.create", writes={}, artifact_ids=())
    with gateway_request_context(_gateway_context("capture.create", "conflict")):
        code, errors, confirmation = ops_commit.commit_proposal(
            _ctx(mini_repo, "capture.create"), proposal)
    assert (code, errors, confirmation) == (3, [
        "artifact revision conflict — reload the affected record before writing"], {})
    assert errors.details == {
        "conflicts": {"a:1": {"expected": 0, "actual": 1}}}
    assert capsys.readouterr().err == ""
    assert plumbing.take_gateway_refusal() == (REVISION_CONFLICT, True)


@pytest.mark.parametrize("failure,snapshot", [
    (TransactionSnapshotConflict("sha256:e", "sha256:a"), True),
    (ProjectionFailure("projection broke", rollback_complete=True), False),
    (PostCommitFailure("post broke", transaction_id="t",
                       receipt_path="r", snapshot_after="s"), False),
])
def test_typed_engine_failures_propagate(
        mini_repo: Path, monkeypatch, failure, snapshot):
    import learning_os.store.transactions as transaction_module

    def raising_commit(self, *args, **kwargs):
        raise failure

    monkeypatch.setattr(
        transaction_module.TransactionService, "commit", raising_commit)
    proposal = TransactionProposal(
        capability="capture.create", writes={}, artifact_ids=())
    with gateway_request_context(_gateway_context("capture.create", "prop")):
        with pytest.raises(type(failure)) as caught:
            ops_commit.commit_proposal(_ctx(mini_repo, "capture.create"), proposal)
    assert caught.value is failure
    assert plumbing.take_gateway_refusal() is None


@pytest.mark.parametrize("failure,recorded", [
    (TransactionFailure("plain boom"), None),
    (TransactionValidationFailure("staged write invalid"), (VALIDATION_FAILED, False)),
    (TransactionIdempotencyConflict("key reused"), (IDEMPOTENCY_CONFLICT, False)),
])
def test_transaction_failures_return_2_with_optional_refusal(
        mini_repo: Path, monkeypatch, failure, recorded):
    import learning_os.store.transactions as transaction_module

    def raising_commit(self, *args, **kwargs):
        raise failure

    monkeypatch.setattr(
        transaction_module.TransactionService, "commit", raising_commit)
    proposal = TransactionProposal(
        capability="capture.create", writes={}, artifact_ids=())
    with gateway_request_context(_gateway_context("capture.create", "tfail")):
        code, errors, confirmation = ops_commit.commit_proposal(
            _ctx(mini_repo, "capture.create"), proposal)
    assert code == 2
    assert errors == [str(failure)]
    assert confirmation == {}
    assert plumbing.take_gateway_refusal() == recorded


def test_translate_runs_before_legacy_catches(mini_repo: Path, monkeypatch, capsys):
    import learning_os.store.transactions as transaction_module

    original = TransactionConflict({"a:1": (0, 1)})
    translated = DeliveryRevisionConflict("delivery raced")

    def raising_commit(self, *args, **kwargs):
        raise original

    monkeypatch.setattr(
        transaction_module.TransactionService, "commit", raising_commit)
    proposal = TransactionProposal(
        capability="ai-action.delivery.apply", writes={}, artifact_ids=(),
        translate=lambda exc: translated)
    with gateway_request_context(
            _gateway_context("ai-action.delivery.apply", "translate")):
        with pytest.raises(DeliveryRevisionConflict) as caught:
            ops_commit.commit_proposal(
                _ctx(mini_repo, "ai-action.delivery.apply"), proposal)
    assert caught.value is translated
    assert caught.value.__cause__ is original
    assert capsys.readouterr().err == ""
    assert plumbing.take_gateway_refusal() is None


def test_translate_none_re_raises_into_legacy_handling(
        mini_repo: Path, monkeypatch, capsys):
    import learning_os.store.transactions as transaction_module

    original = TransactionConflict({"a:1": (0, 1)})

    def raising_commit(self, *args, **kwargs):
        raise original

    monkeypatch.setattr(
        transaction_module.TransactionService, "commit", raising_commit)
    proposal = TransactionProposal(
        capability="ai-action.delivery.apply", writes={}, artifact_ids=(),
        translate=lambda exc: None)
    with gateway_request_context(
            _gateway_context("ai-action.delivery.apply", "translate-none")):
        code, errors, confirmation = ops_commit.commit_proposal(
            _ctx(mini_repo, "ai-action.delivery.apply"), proposal)
    assert (code, errors, confirmation) == (3, [
        "artifact revision conflict — reload the affected record before writing"], {})
    assert errors.details == {
        "conflicts": {"a:1": {"expected": 0, "actual": 1}}}
    assert capsys.readouterr().err == ""
    assert plumbing.take_gateway_refusal() == (REVISION_CONFLICT, True)


def test_ai_translate_chain_semantics(mini_repo: Path, monkeypatch):
    """The service's own except chain as a translate: same types, from originals."""
    import learning_os.store.transactions as transaction_module
    from learning_os.domain.failures import TransactionConflict as Conflict

    def ai_translate(exc):
        try:
            raise exc
        except Conflict as conflict:
            return DeliveryRevisionConflict(str(conflict))
        except TransactionSnapshotConflict as stale:
            return StaleDeliveryError(str(stale))
        except TransactionIdempotencyConflict as conflict:
            return DeliveryValidationError(f"delivery idempotency conflict: {conflict}")
        except TransactionFailure as failed:
            return DeliveryValidationError(f"delivery transaction failed: {failed}")

    cases = [
        (Conflict({"a:1": (0, 1)}), DeliveryRevisionConflict),
        (TransactionSnapshotConflict("e", "a"), StaleDeliveryError),
        (TransactionIdempotencyConflict("reused"), DeliveryValidationError),
        (TransactionValidationFailure("invalid"), DeliveryValidationError),
    ]
    for original, translated_type in cases:
        def raising_commit(self, *args, _failure=original, **kwargs):
            raise _failure

        monkeypatch.setattr(
            transaction_module.TransactionService, "commit", raising_commit)
        proposal = TransactionProposal(
            capability="ai-action.delivery.apply", writes={}, artifact_ids=(),
            translate=ai_translate)
        with gateway_request_context(
                _gateway_context("ai-action.delivery.apply", "ai-chain")):
            with pytest.raises(translated_type) as caught:
                ops_commit.commit_proposal(
                    _ctx(mini_repo, "ai-action.delivery.apply"), proposal)
        assert caught.value.__cause__ is original
    assert plumbing.take_gateway_refusal() is None


def test_standard_hooks_wire_validation_publish_and_touched(mini_repo: Path, monkeypatch):
    import learning_os.store.transactions as transaction_module

    captured: dict = {}

    def recording_commit(self, *args, **kwargs):
        captured.update(kwargs)
        return _stub_result()

    monkeypatch.setattr(
        transaction_module.TransactionService, "commit", recording_commit)
    validate_calls: list = []

    def fake_validate(repo, online=False):
        validate_calls.append((repo, online))
        return []

    monkeypatch.setattr(ops_commit, "validate", fake_validate)
    proposal = TransactionProposal(
        capability="capture.create", writes={}, artifact_ids=())
    with gateway_request_context(_gateway_context("capture.create", "hooks")):
        code, _, _ = ops_commit.commit_proposal(
            _ctx(mini_repo, "capture.create"), proposal)
    assert code == 0
    assert captured["validate_state"]() == []
    assert len(validate_calls) == 1
    assert validate_calls[0][1] is False

    extra_calls: list = []

    def extra(repo, issues):
        extra_calls.append((repo, issues))
        return ["refused by gate"]

    proposal = TransactionProposal(
        capability="capture.create", writes={}, artifact_ids=(),
        validate_extra=extra)
    with gateway_request_context(_gateway_context("capture.create", "hooks-extra")):
        ops_commit.commit_proposal(_ctx(mini_repo, "capture.create"), proposal)
    assert captured["validate_state"]() == ["refused by gate"]
    assert len(extra_calls) == 1
    assert extra_calls[0][1] == []

    published: list = []
    monkeypatch.setattr(
        ops_commit, "_publish_repo", lambda repo: published.append(repo))
    snapshot = captured["publish"]("sha256:" + "e" * 64)
    assert snapshot.startswith("sha256:")
    assert len(published) == 1
    rollback_calls: list = []
    monkeypatch.setattr(
        ops_commit, "_publish", lambda root: rollback_calls.append(root))
    assert captured["rollback_publish"]() is None
    assert rollback_calls == [mini_repo]
    touched_path = mini_repo / "work/inbox/touched-by-hook.md"
    touched_path.write_text("hooked\n", encoding="utf-8")
    captured["touched"]([touched_path])
    rows = session_support.load_session_paths(mini_repo)
    assert rows["work/inbox/touched-by-hook.md"]["state"] == "file"


def test_none_hooks_are_omitted(mini_repo: Path, monkeypatch):
    import learning_os.store.transactions as transaction_module

    captured: dict = {}

    def recording_commit(self, *args, **kwargs):
        captured.update(kwargs)
        return _stub_result()

    monkeypatch.setattr(
        transaction_module.TransactionService, "commit", recording_commit)
    proposal = TransactionProposal(
        capability="capture.create", writes={}, artifact_ids=(),
        validate_state=None, publish=None, rollback_publish=None,
        touched=None)
    with gateway_request_context(_gateway_context("capture.create", "none-hooks")):
        code, errors, _ = ops_commit.commit_proposal(
            _ctx(mini_repo, "capture.create"), proposal)
    assert (code, errors) == (0, [])
    assert sorted(captured) == [
        "artifact_ids", "capability", "deletes",
        "expected_revisions", "metadata", "writes",
    ]


def test_non_regular_file_precheck_skips_commit(mini_repo: Path, monkeypatch):
    import learning_os.store.transactions as transaction_module

    calls: list = []

    def recording_commit(self, *args, **kwargs):
        calls.append(kwargs)
        return _stub_result()

    monkeypatch.setattr(
        transaction_module.TransactionService, "commit", recording_commit)
    target = mini_repo / "work/inbox"
    proposal = TransactionProposal(
        capability="capture.create", writes={target: "x"}, artifact_ids=())
    with gateway_request_context(_gateway_context("capture.create", "precheck")):
        code, errors, confirmation = ops_commit.commit_proposal(
            _ctx(mini_repo, "capture.create"), proposal)
    assert code == 2
    assert errors == [f"cannot change {target}: target is not a regular file"]
    assert confirmation == {}
    assert calls == []


def test_deletes_normalize_to_paths(mini_repo: Path, monkeypatch):
    import learning_os.store.transactions as transaction_module

    captured: dict = {}

    def recording_commit(self, *args, **kwargs):
        captured.update(kwargs)
        return _stub_result()

    monkeypatch.setattr(
        transaction_module.TransactionService, "commit", recording_commit)
    victim = mini_repo / "work/inbox/gone.md"
    victim.write_text("bye\n", encoding="utf-8")
    proposal = TransactionProposal(
        capability="capture.create", writes={mini_repo / "work/inbox/kept.md": "kept\n"},
        artifact_ids=(), deletes=[str(victim)])
    with gateway_request_context(_gateway_context("capture.create", "deletes")):
        code, errors, _ = ops_commit.commit_proposal(
            _ctx(mini_repo, "capture.create"), proposal)
    assert (code, errors) == (0, [])
    assert captured["deletes"] == (victim,)


def test_sequential_refusals_carry_their_own_classification(
        mini_repo: Path, monkeypatch):
    """S3: typed outcomes replace the tuple/ambient channel without leakage.

    Three commits in one process — a revision conflict, a validation
    failure, then a success — must each carry exactly their own refusal
    (or none), never an earlier one's classification.
    """
    import learning_os.store.transactions as transaction_module

    failures = [
        TransactionConflict({"a:1": (0, 1)}),
        TransactionValidationFailure("staged write invalid"),
    ]

    def flaky_commit(self, *args, **kwargs):
        if failures:
            raise failures.pop(0)
        return _stub_result()

    monkeypatch.setattr(
        transaction_module.TransactionService, "commit", flaky_commit)
    proposal = TransactionProposal(
        capability="capture.create", writes={}, artifact_ids=())
    outcomes = []
    for suffix in ("seq-1", "seq-2", "seq-3"):
        with gateway_request_context(_gateway_context("capture.create", suffix)):
            outcomes.append(ops_commit.commit_proposal(
                _ctx(mini_repo, "capture.create"), proposal))
    assert outcomes[0].code == 3
    assert outcomes[0].refusal is not None
    assert (outcomes[0].refusal.code, outcomes[0].refusal.retryable) == (
        REVISION_CONFLICT, True)
    assert outcomes[1].code == 2
    assert outcomes[1].refusal is not None
    assert (outcomes[1].refusal.code, outcomes[1].refusal.retryable) == (
        VALIDATION_FAILED, False)
    assert outcomes[2].code == 0
    assert outcomes[2].refusal is None, "a success must not inherit a refusal"
    assert outcomes[2].confirmation["transaction_id"]


def test_commit_family_is_selected_by_the_owning_capability():
    from learning_os.app.proposal import CommitFamily, commit_family

    assert commit_family("capture.create") is CommitFamily.ORDINARY
    assert commit_family("goal.decision.record") is CommitFamily.GOAL
    assert commit_family("ai-action.delivery.apply") is CommitFamily.AI
    proposal = TransactionProposal(
        capability="goal.decision.record", writes={}, artifact_ids=())
    assert proposal.family is CommitFamily.GOAL


def test_family_substitution_refuses_before_any_write(mini_repo: Path):
    """A gateway request cannot substitute another capability's family.

    The engine admits a transaction only for the capability its sealed
    request names; a mismatched capability (a substituted family) is
    refused before any canonical byte or receipt exists.
    """
    from learning_os.domain.failures import TransactionFailure
    from learning_os.store.transactions import TransactionService

    target = mini_repo / "work/inbox/substituted.md"
    context = _gateway_context("goal.decision.record", "family-sub")
    with pytest.raises(TransactionFailure, match="does not match"):
        TransactionService(mini_repo).commit(
            capability="capture.create",
            writes={target: "smuggled\n"},
            artifact_ids=["capture:family-sub"],
            expected_revisions={"capture:family-sub": 0},
            gateway_request=context,
        )
    assert not target.exists()
    assert not list(
        (mini_repo / "operations/transactions").glob("transaction-*.yaml"))
