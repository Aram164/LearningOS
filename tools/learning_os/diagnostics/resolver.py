"""Deterministic causal resolver prototype (track #2, Phase 2A).

Two evidence planes, strictly separated:

- The EXECUTION plane (spans/events) says what the software appeared to do:
  which stage broke, whether rollback appeared to complete.
- The AUTHORITY plane (receipt, typed refusal, idempotency ledger, observed
  snapshot) decides what definitively happened.

The resolver joins them into one diagnosis. Its central rule: execution
telemetry informs, authority decides. A `rolled-back` observation plus an
`INTERNAL_FAILURE` response is AMBIGUOUS, never NOT_COMMITTED — telemetry is
weaker than the receipt/recovery machinery and must never promote an
indeterminate response into a definitive conclusion.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

from ..contracts.gateway import GatewayRequestContext
from ..errors import (
    ReplayEvidenceError,
    TransactionFailure,
    TransactionIdempotencyConflict,
)
from ..evidence import verify_committed_evidence
from . import conventions

#: UI-side received outcomes that name a stage. Only transport losses map
#: today: an unreadable response means the child never answered, whatever
#: Core did or did not do. Anything else stays unstaged — the Core spans or
#: the response code must name it.
UI_RECEIVED_TO_STAGE = {
    "UNREADABLE_RESPONSE": "ui.transport",
}


#: Response code to the stage that produced it. INTERNAL_FAILURE and
#: IDEMPOTENCY_CONFLICT are deliberately absent: they name no stage, and the
#: spans must supply it.
CODE_TO_STAGE = {
    "STALE_SNAPSHOT": "core.snapshot_guard",
    "REVISION_CONFLICT": "core.revision_guard",
    "INVALID_REQUEST": "core.admission",
    "UNKNOWN_CAPABILITY": "core.admission",
    "OUT_OF_SCOPE": "core.admission",
    "AMBIGUOUS_MIGRATION": "core.admission",
    "UNCONFIRMED": "core.approval",
    "VALIDATION_FAILED": "core.validation",
    "PROJECTION_FAILED": "core.projection",
}


@dataclass
class AuthorityEvidence:
    """Everything that can prove (not merely suggest) an outcome."""

    request_id: str
    idempotency_key: str
    capability: str
    receipts: list[dict] = field(default_factory=list)
    ledger: dict = field(default_factory=dict)
    verified_receipt: dict | None = None
    verification_error: str | None = None
    response_code: str | None = None
    response_codes: list = field(default_factory=list)
    response_replayed: bool = False
    response_snapshot_after: str | None = None
    response_transaction_id: str | None = None
    transport_error: str | None = None
    observed_snapshot: str | None = None


def collect_authority(root: Path, *, request_id: str, idempotency_key: str,
                      capability: str, response: dict | None = None,
                      transport_error: str | None = None,
                      observed_snapshot: str | None = None,
                      response_codes: list | None = None) -> AuthorityEvidence:
    """Read receipts and the idempotency ledger; pure reads, no inference."""
    receipts = []
    for path in sorted((root / "operations" / "transactions").glob("transaction-*.yaml")):
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except (OSError, ValueError):
            continue
        if isinstance(data, dict):
            data = dict(data)
            data["_path"] = path.relative_to(root).as_posix()
            receipts.append(data)
    ledger: dict = {}
    ledger_path = root / "operations" / "transactions" / "idempotency.yaml"
    if ledger_path.is_file():
        try:
            ledger = (yaml.safe_load(ledger_path.read_text(encoding="utf-8"))
                      or {}).get("entries", {})
        except (OSError, ValueError):
            ledger = {}
    if not isinstance(ledger, dict):
        ledger = {}
    # Strict verification through the same checklist the Gateway replay
    # uses: the trace supplies this operation's identity, the ledger row
    # supplies the trusted channel/intent, and the approval subject is
    # bound by the admission invariant (approval == intent). A receipt
    # only proves COMMITTED when this passes; anything else is ambiguity.
    verified_receipt: dict | None = None
    verification_error: str | None = None
    raw_row = ledger.get(idempotency_key)
    if isinstance(raw_row, dict) and isinstance(raw_row.get("channel"), str) \
            and isinstance(raw_row.get("intent_sha256"), str):
        trusted = GatewayRequestContext(
            request_id=request_id, idempotency_key=idempotency_key,
            capability=capability, channel=raw_row["channel"],
            intent_sha256=raw_row["intent_sha256"],
            # Nominal: the verifier never reads the approval kind, only
            # the subject binding proven against the row's intent.
            approval_kind="direct-user-gesture",
            approval_subject_sha256=raw_row["intent_sha256"],
        )
        try:
            verified = verify_committed_evidence(root, trusted)
        except (ReplayEvidenceError, TransactionIdempotencyConflict,
                TransactionFailure) as exc:
            verification_error = str(exc)
        else:
            if verified is not None:
                verified_receipt = dict(verified[0])
                verified_receipt["_path"] = verified[1]["receipt_path"]
    error = (response or {}).get("error") or {}
    codes = list(response_codes) if response_codes is not None else [error.get("code")]
    return AuthorityEvidence(
        request_id=request_id,
        idempotency_key=idempotency_key,
        capability=capability,
        receipts=receipts,
        ledger=ledger,
        verified_receipt=verified_receipt,
        verification_error=verification_error,
        response_code=error.get("code"),
        response_codes=codes,
        response_replayed=bool((response or {}).get("replayed", False)),
        response_snapshot_after=(response or {}).get("snapshot_after"),
        response_transaction_id=(response or {}).get("transaction_id"),
        transport_error=transport_error,
        observed_snapshot=observed_snapshot,
    )


@dataclass
class CausalDiagnosis:
    first_failure_stage: str | None
    execution_outcome: str
    canonical_outcome: str
    projection_outcome: str
    recovery_requirement: str
    authoritative_evidence: list[str] = field(default_factory=list)
    attempts: list[dict] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "first_failure_stage": self.first_failure_stage,
            "execution_outcome": self.execution_outcome,
            "canonical_outcome": self.canonical_outcome,
            "projection_outcome": self.projection_outcome,
            "recovery_requirement": self.recovery_requirement,
            "authoritative_evidence": list(self.authoritative_evidence),
            "attempts": [dict(attempt) for attempt in self.attempts],
            "reasons": list(self.reasons),
        }


def matching_receipt(receipts: list[dict], request_id: str,
                     idempotency_key: str) -> dict | None:
    """The committed receipt for one request, or None (shared rule)."""
    for receipt in receipts:
        request = receipt.get("request") or {}
        if request.get("request_id") == request_id \
                and request.get("idempotency_key") == idempotency_key \
                and receipt.get("status") == "committed":
            return receipt
    return None


def _matching_receipt(authority: AuthorityEvidence) -> dict | None:
    return matching_receipt(authority.receipts, authority.request_id,
                            authority.idempotency_key)


def _events(records: list[dict]) -> list[dict]:
    return [record for record in records
            if record.get("v") == conventions.VOCAB_VERSION
            and record.get("kind") == "event"]


def _ui_dispatched_without_core(records: list[dict]) -> bool:
    kinds = {(record.get("kind"), record.get("name")) for record in records
             if record.get("v") == conventions.VOCAB_VERSION}
    return ("event", conventions.EVENT_ENVELOPE_DISPATCHED) in kinds \
        and not any(kind == "span-start" for kind, _ in kinds)


def _attempt_spans(records: list[dict]) -> list[dict]:
    """One row per attempt span, earliest first, replays linked to attempt 0."""
    starts = {}
    ends = {}
    for record in records:
        if record.get("v") != conventions.VOCAB_VERSION:
            continue
        if record.get("kind") == "span-start" and record.get("name") == "attempt":
            starts.setdefault(record.get("span"), record)
        elif record.get("kind") == "span-end" and record.get("name") == "attempt":
            ends[record.get("span")] = record
    ordered = sorted(starts, key=lambda span: starts[span].get("ts", 0))
    attempts = []
    for index, span in enumerate(ordered):
        end = ends.get(span, {})
        attempts.append({
            "span": span,
            "status": end.get("status", "unknown"),
            "replay_of": ordered[0] if index > 0 else None,
        })
    return attempts


def _refusals_prove_no_commit(records: list[dict],
                              authority: AuthorityEvidence) -> bool:
    """Whether the recorded refusals cover every counted attempt.

    A definitive refusal proves no-commit only for its own attempt. A
    recovery refusal (STALE/REVISION/INVALID on attempt 2) says nothing
    about an ambiguous attempt 1 — the UI-side rule, applied here to the
    merged trace. Attempts are counted from UI dispatches and Core
    attempt spans, whichever reports more, so a transport-lost dispatch
    or a crashed attempt without a response summary still withholds
    proof; success responses never count as refusals.
    """
    codes = authority.response_codes or [authority.response_code]
    if not all(code in conventions.DEFINITIVE_NO_COMMIT_CODES for code in codes):
        return False
    dispatches = sum(1 for record in records
                     if record.get("name") == conventions.EVENT_ENVELOPE_DISPATCHED)
    spans = sum(1 for record in records
                if record.get("kind") == "span-start"
                and record.get("name") == "attempt")
    return len(codes) >= max(dispatches, spans, 1)


def resolve(records: list[dict], authority: AuthorityEvidence) -> CausalDiagnosis:
    """One diagnosis from execution records plus authority evidence."""
    events = sorted(_events(records), key=lambda record: record.get("ts", 0))
    attempts = _attempt_spans(records)
    evidence: list[str] = []
    reasons: list[str] = []

    if authority.verified_receipt is not None:
        evidence.append(f"receipt:{authority.verified_receipt['_path']}")
    else:
        suspect = _matching_receipt(authority)
        if suspect is not None:
            evidence.append(f"receipt:{suspect['_path']}")
    ledger_entry = authority.ledger.get(authority.idempotency_key)
    if ledger_entry is not None:
        evidence.append(f"ledger:{authority.idempotency_key}")
    if authority.response_code is not None:
        evidence.append(f"response:{authority.response_code}")
    if authority.response_replayed:
        evidence.append("response:replayed=true")
    if authority.observed_snapshot is not None:
        evidence.append(f"observed:{authority.observed_snapshot}")

    # --- canonical outcome: authority decides ---------------------------
    # COMMITTED requires a receipt verified through the same strict
    # checklist the Gateway replay uses — agreement on one transaction id
    # was a weaker parallel truth system, and it is gone.
    canonical: str
    if authority.verified_receipt is not None:
        canonical = "COMMITTED"
        reasons.append("a committed receipt verified against its ledger entry, "
                       "the live revision floor, and the capability catalog")
    elif authority.verification_error is not None:
        canonical = "AMBIGUOUS"
        reasons.append("committed evidence failed strict verification: "
                       f"{authority.verification_error}")
    elif _matching_receipt(authority) is not None or ledger_entry is not None:
        canonical = "AMBIGUOUS"
        reasons.append("authority evidence is present but unverified — "
                       "contradiction, not proof")
    elif _refusals_prove_no_commit(records, authority):
        canonical = "NOT_COMMITTED"
        codes = authority.response_codes or [authority.response_code]
        reasons.append(f"every counted attempt ended in a definitive refusal "
                       f"({', '.join(sorted(set(codes)))}): the write "
                       "cannot have committed")
    else:
        canonical = "AMBIGUOUS"
        codes = authority.response_codes or [authority.response_code]
        if any(code in conventions.DEFINITIVE_NO_COMMIT_CODES for code in codes):
            reasons.append("a definitive refusal on a later attempt cannot prove "
                           "an earlier ambiguous attempt wrote nothing")
        elif authority.response_code is not None:
            reasons.append(f"{authority.response_code} is not a definitive "
                           "no-commit code, and no receipt exists")
        else:
            reasons.append("no response and no receipt: nothing is knowable")

    # --- execution outcome: spans report --------------------------------
    names = [event.get("name") for event in events]
    errored_end = any(
        record.get("v") == conventions.VOCAB_VERSION
        and record.get("kind") == "span-end"
        and record.get("status") == "error"
        for record in records)
    if conventions.EVENT_CORE_TRANSACTION_COMMITTED in names:
        execution = "committed"
    elif conventions.EVENT_ROLLBACK_COMPLETED in names:
        execution = "rolled-back"
    elif not records and authority.transport_error is not None:
        execution = "transport-lost"
    elif any(event.get("name") == conventions.EVENT_STAGE_FAILED
             for event in events) or errored_end:
        execution = "refused"
    elif authority.transport_error is not None and not events:
        execution = "transport-lost"
    elif _ui_dispatched_without_core(records):
        execution = "transport-lost"
        reasons.append("the UI dispatched but no Core attempt exists: "
                       "the child never ran")
    else:
        execution = "unknown"
        reasons.append("no execution records name an outcome")

    # --- first failure stage: first error, then close attrs, then code ---
    stage: str | None = None
    for event in events:
        if event.get("name") == conventions.EVENT_STAGE_FAILED \
                and event.get("stage") in conventions.FAILURE_STAGES:
            stage = event["stage"]
            break
    if stage is None:
        for record in records:
            candidate = (record.get("attrs") or {}).get("stage")
            if record.get("kind") == "span-end" and candidate in conventions.FAILURE_STAGES:
                stage = candidate
                break
    if stage is None and authority.response_code in CODE_TO_STAGE:
        stage = CODE_TO_STAGE[authority.response_code]
    if stage is None:
        for event in events:
            if event.get("name") == conventions.EVENT_UI_RESPONSE_RECEIVED:
                candidate = UI_RECEIVED_TO_STAGE.get(
                    (event.get("attrs") or {}).get("code"))
                if candidate is not None:
                    stage = candidate
                    break
    if stage is None and authority.transport_error is not None:
        stage = "ui.transport"
    if stage is None and execution == "transport-lost":
        stage = "ui.transport"

    # --- projection outcome ---------------------------------------------
    if conventions.EVENT_PROJECTION_PUBLISHED in names:
        projection = "published"
    elif stage == "core.projection" \
            or conventions.EVENT_PROJECTION_STARTED in names:
        projection = "failed"
    elif execution == "refused":
        projection = "skipped"
    else:
        projection = "unknown"

    # --- recovery requirement -------------------------------------------
    if canonical == "NOT_COMMITTED":
        recovery = "none"
        reasons.append("definitive refusal: nothing to reconcile")
    elif canonical == "COMMITTED":
        if authority.observed_snapshot is not None \
                and authority.response_snapshot_after is not None \
                and authority.observed_snapshot == authority.response_snapshot_after:
            recovery = "none"
            reasons.append("receipt observed in the projection: settled")
        else:
            recovery = "verify-observation"
            reasons.append("receipt exists but no observation is on record")
    else:
        recovery = "reconcile-exact-request"
        reasons.append("ambiguous outcome: the exact request stays recoverable")

    return CausalDiagnosis(
        first_failure_stage=stage,
        execution_outcome=execution,
        canonical_outcome=canonical,
        projection_outcome=projection,
        recovery_requirement=recovery,
        authoritative_evidence=evidence,
        attempts=attempts,
        reasons=reasons,
    )
