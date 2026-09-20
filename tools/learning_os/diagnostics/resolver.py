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
    response_code: str | None = None
    response_replayed: bool = False
    response_snapshot_after: str | None = None
    response_transaction_id: str | None = None
    transport_error: str | None = None
    observed_snapshot: str | None = None


def collect_authority(root: Path, *, request_id: str, idempotency_key: str,
                      capability: str, response: dict | None = None,
                      transport_error: str | None = None,
                      observed_snapshot: str | None = None) -> AuthorityEvidence:
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
    error = (response or {}).get("error") or {}
    return AuthorityEvidence(
        request_id=request_id,
        idempotency_key=idempotency_key,
        capability=capability,
        receipts=receipts,
        ledger=ledger if isinstance(ledger, dict) else {},
        response_code=error.get("code"),
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


def resolve(records: list[dict], authority: AuthorityEvidence) -> CausalDiagnosis:
    """One diagnosis from execution records plus authority evidence."""
    events = sorted(_events(records), key=lambda record: record.get("ts", 0))
    attempts = _attempt_spans(records)
    evidence: list[str] = []
    reasons: list[str] = []

    receipt = _matching_receipt(authority)
    ledger_entry = authority.ledger.get(authority.idempotency_key)
    if receipt is not None:
        evidence.append(f"receipt:{receipt['_path']}")
    if ledger_entry is not None:
        evidence.append(f"ledger:{authority.idempotency_key}")
    if authority.response_code is not None:
        evidence.append(f"response:{authority.response_code}")
    if authority.response_replayed:
        evidence.append("response:replayed=true")
    if authority.observed_snapshot is not None:
        evidence.append(f"observed:{authority.observed_snapshot}")

    # --- canonical outcome: authority decides ---------------------------
    canonical: str
    if receipt is not None and ledger_entry is not None \
            and ledger_entry.get("transaction_id") == receipt.get("id"):
        canonical = "COMMITTED"
        reasons.append("a committed receipt and its ledger entry agree")
    elif receipt is not None or ledger_entry is not None:
        canonical = "AMBIGUOUS"
        reasons.append("receipt and ledger disagree — contradiction, not proof")
    elif authority.response_code in conventions.DEFINITIVE_NO_COMMIT_CODES:
        canonical = "NOT_COMMITTED"
        reasons.append(f"{authority.response_code} is definitive: the write "
                       "cannot have committed")
    else:
        canonical = "AMBIGUOUS"
        if authority.response_code is not None:
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
