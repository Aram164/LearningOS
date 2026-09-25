"""Versioned semantic conventions for causal diagnostics (track #2).

This module is the single source of truth for the operation/span/event
vocabulary. The version is explicit and boring on purpose: a consumer never
sniffs shapes, it reads ``VOCAB_VERSION``. Bumping the version is a reviewable
contract-adjacent event, exactly like the manifest and data contracts.

Phase 1 uses only the identity and carrier sections; span, event and
failure-stage names are declared now so Phase 2 instrumentation cannot invent
competing spellings.

v2 changelog: commit-boundary events (the transaction service publishes the
projection *inside* the commit and rolls everything back on failure, so
`transaction.committed` names only the irrevocable point), execution outcomes,
recovery requirements, and the definitive-no-commit mirror.
"""

from __future__ import annotations

VOCAB_VERSION = 2

# ---------------------------------------------------------------------------
# Identity.
# ---------------------------------------------------------------------------
#
# operation_id: 32 lowercase hex chars, carried as the W3C trace-id. Stable
# across every attempt (dispatch, in-session replay, restart recovery) of one
# user-approved operation while the issuing process lives.
#
# attempt_id: 16 lowercase hex chars, carried as the W3C span-id. Fresh for
# every physical child-process dispatch, so a replay is distinguishable from
# its original and concurrent operations can never share an identity.

OPERATION_ID_RE = r"[0-9a-f]{32}"
ATTEMPT_ID_RE = r"[0-9a-f]{16}"

# ---------------------------------------------------------------------------
# Carrier.
# ---------------------------------------------------------------------------
#
# Context crosses the UI -> Core process boundary as environment, never as
# Gateway payload: the approved envelope (and its approval hash) must not
# change shape because diagnostics exists.

TRACEPARENT_ENV = "TRACEPARENT"

#: Opt-in JSONL debug sink, one record per gateway admission that observed a
#: context. Unset (the default) means no record is written anywhere. Strictly
#: a Phase-1 proof and diagnosis aid, in the spirit of SSLKEYLOGFILE: it must
#: never become a behavior input, and a write failure here must never fail or
#: alter the gateway call it observed.
TRACE_DEBUG_FILE_ENV = "LOS_TRACE_DEBUG_FILE"

# ---------------------------------------------------------------------------
# Span names (emitted from Phase 2; declared here).
# ---------------------------------------------------------------------------

SPAN_OPERATION = "los.operation"
SPAN_GATEWAY_DISPATCH = "los.gateway.dispatch"
SPAN_GATEWAY_ADMISSION = "los.gateway.admission"
SPAN_TRANSACTION_GUARDS = "los.transaction.guards"
SPAN_TRANSACTION_COMMIT = "los.transaction.commit"
SPAN_PROJECTION_PUBLISH = "los.projection.publish"
SPAN_UI_RECONCILE = "los.ui.reconcile"
SPAN_RECOVERY_SETTLE = "los.recovery.settle"

SPAN_NAMES = frozenset({
    SPAN_OPERATION, SPAN_GATEWAY_DISPATCH, SPAN_GATEWAY_ADMISSION,
    SPAN_TRANSACTION_GUARDS, SPAN_TRANSACTION_COMMIT, SPAN_PROJECTION_PUBLISH,
    SPAN_UI_RECONCILE, SPAN_RECOVERY_SETTLE,
})

# ---------------------------------------------------------------------------
# Event names (emitted from Phase 2; declared here).
# ---------------------------------------------------------------------------

EVENT_ENVELOPE_PREPARED = "gateway.envelope.prepared"
EVENT_ENVELOPE_DISPATCHED = "gateway.envelope.dispatched"
EVENT_TRANSACTION_COMMITTED = "transaction.committed"
EVENT_TRANSACTION_REFUSED = "transaction.refused"
EVENT_REPLAY_RECOGNIZED = "replay.recognized"
EVENT_PROJECTION_OBSERVED = "projection.observed"
EVENT_RECOVERY_SETTLED = "recovery.settled"
EVENT_RECOVERY_BLOCKED = "recovery.blocked"
EVENT_UI_RESPONSE_RECEIVED = "ui.response.received"

EVENT_NAMES = frozenset({
    EVENT_ENVELOPE_PREPARED, EVENT_ENVELOPE_DISPATCHED,
    EVENT_TRANSACTION_COMMITTED, EVENT_TRANSACTION_REFUSED,
    EVENT_REPLAY_RECOGNIZED, EVENT_PROJECTION_OBSERVED,
    EVENT_RECOVERY_SETTLED, EVENT_RECOVERY_BLOCKED,
    EVENT_UI_RESPONSE_RECEIVED,
})

# ---------------------------------------------------------------------------
# Commit-boundary events (v2): the causal stages inside one gateway attempt.
# ---------------------------------------------------------------------------
#
# `TRANSACTION_COMMITTED` is emitted only at the irrevocable point in
# `TransactionService.commit` — after the receipt bytes are durably written
# and rollback is no longer possible. Canonical files written earlier in the
# attempt are staged, not committed: a projection failure after them still
# rolls the whole attempt back (measured Phase 0, scenario S7).

EVENT_TRANSACTION_STARTED = "core.transaction.started"
EVENT_HANDLER_COMPLETED = "core.handler.completed"
EVENT_VALIDATION_PASSED = "core.validation.passed"
EVENT_PROJECTION_STARTED = "core.projection.started"
EVENT_PROJECTION_PUBLISHED = "core.projection.published"
EVENT_ROLLBACK_STARTED = "core.rollback.started"
EVENT_ROLLBACK_COMPLETED = "core.rollback.completed"
EVENT_CORE_TRANSACTION_COMMITTED = "core.transaction.committed"
EVENT_RECEIPT_PERSISTED = "core.receipt.persisted"

EVENT_ENVELOPE_VALIDATED = "gw.envelope.validated"
EVENT_APPROVAL_PASSED = "gw.approval.passed"
EVENT_REPLAY_CHECKED = "gw.replay.checked"
EVENT_SNAPSHOT_GUARD_PASSED = "gw.snapshot_guard.passed"
EVENT_RESPONSE_EMITTED = "gw.response.emitted"

#: The one generic failure record. `stage` (a FAILURE_STAGES member) names
#: the boundary that refused or broke; `error` carries the short reason.
#: The resolver reads the FIRST such event as first_failure_stage.
EVENT_STAGE_FAILED = "core.stage.failed"

COMMIT_BOUNDARY_EVENTS = frozenset({
    EVENT_TRANSACTION_STARTED, EVENT_HANDLER_COMPLETED,
    EVENT_VALIDATION_PASSED, EVENT_PROJECTION_STARTED,
    EVENT_PROJECTION_PUBLISHED, EVENT_ROLLBACK_STARTED,
    EVENT_ROLLBACK_COMPLETED, EVENT_CORE_TRANSACTION_COMMITTED,
    EVENT_RECEIPT_PERSISTED, EVENT_ENVELOPE_VALIDATED, EVENT_APPROVAL_PASSED,
    EVENT_REPLAY_CHECKED, EVENT_SNAPSHOT_GUARD_PASSED,
    EVENT_RESPONSE_EMITTED, EVENT_STAGE_FAILED,
})

# ---------------------------------------------------------------------------
# Outcome classification (consumed by the Phase-3 resolver; fixed now).
# ---------------------------------------------------------------------------

#: The first stage known to have failed, or null when the operation settled.
#: UI-side stages name the UI component; core-side stages name the gateway
#: phase. A refusal names the guard that refused, never a downstream stage.
FAILURE_STAGES = frozenset({
    "ui.prepare", "ui.transport",
    "core.admission", "core.snapshot_guard", "core.revision_guard",
    "core.approval", "core.replay", "core.validation", "core.commit",
    "core.receipt", "core.projection", "ui.reconcile", "ui.recovery",
})

#: What the canonical store definitely did. AMBIGUOUS means the evidence
#: cannot decide — it is an honest answer, never a guess, and it must always
#: resolve toward keeping the recovery record open.
CANONICAL_OUTCOMES = frozenset({"COMMITTED", "NOT_COMMITTED", "AMBIGUOUS"})

#: What the UI may tell the learner. SETTLED requires a receipt *and* an
#: observed projection containing the committed state (the existing recovery
#: rule, unchanged).
UI_OUTCOMES = frozenset({"SETTLED", "BLOCKED", "REFUSED", "UNKNOWN"})

#: What execution instrumentation observed. Weaker than canonical outcome by
#: construction: `rolled-back` means rollback *appeared* to complete, which
#: the resolver must never promote into a definitive no-commit conclusion.
EXECUTION_OUTCOMES = frozenset({
    "committed", "rolled-back", "refused", "transport-lost", "unknown",
})

#: What must still happen. `none` only when the authority plane proves the
#: write is settled or definitively absent; `verify-observation` when a
#: receipt exists but no projection observation is on record;
#: `reconcile-exact-request` whenever the outcome is ambiguous.
RECOVERY_REQUIREMENTS = frozenset({
    "none", "verify-observation", "reconcile-exact-request",
})

#: Error codes that prove the write cannot have committed. An exact mirror
#: of the UI's `DEFINITIVE_NO_COMMIT_CODES` (contracts/gateway-v2.ts) —
#: `test_causal_resolver.py` fails if the two lists drift, because a missed
#: code keeps a dead request recoverable and an added code retires a live one.
#:
#: TODO(track-3): derive definitive-no-commit codes from the producer-owned
#: contract instead of mirroring. This list is the concrete cross-boundary
#: semantic contract Track #3 exists to unify; until then the mirror plus
#: the drift-failing parity test is the deliberate mechanism. Do not pull
#: contract generation into Track #2 to fix this sooner.
#:
#: IDEMPOTENCY_CONFLICT joined in S12 (JF-19): a refused attempt proves its
#: own request wrote nothing, and the per-attempt coverage rule already
#: withholds proof when an earlier attempt is ambiguous. The UI mirror in
#: contracts/gateway-v2.ts needs the same addition; the parity test fails
#: until it lands.
DEFINITIVE_NO_COMMIT_CODES = frozenset({
    "INVALID_REQUEST",
    "UNKNOWN_CAPABILITY",
    "STALE_SNAPSHOT",
    "REVISION_CONFLICT",
    "OUT_OF_SCOPE",
    "AMBIGUOUS_MIGRATION",
    "VALIDATION_FAILED",
    "PROJECTION_FAILED",
    "UNCONFIRMED",
    "IDEMPOTENCY_CONFLICT",
})

# ---------------------------------------------------------------------------
# Privacy.
# ---------------------------------------------------------------------------
#
# Trace context carries correlation IDs only: operation_id, attempt_id, and
# (from Phase 2) structural attributes such as capability name and error code.
# Payload text, learner prose, note titles, file bytes and AI prompts must
# never enter a span, an event, the carrier, or the debug sink.
