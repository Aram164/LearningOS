"""Commit one transaction proposal through the canonical engine (PLAN D4).

The body of ``commands/support.py:_write_transaction``, moved: same returns,
same exception propagation, same printed lines. ``_write_transaction`` is now
a thin call into :func:`commit_proposal`. Every proposal field forwards to
``TransactionService.commit`` (SPEC §11.1, amendment (i) K9): hooks resolve as
STANDARD / None (omitted) / callable, ``clock=None`` and
``expected_snapshot=None`` omit their engine argument, and ``translate`` runs
before the standard legacy catches.
"""

from __future__ import annotations

from pathlib import Path

from learning_os.app.context import OpContext
from learning_os.app.outcomes import record_gateway_refusal as _record_gateway_refusal
from learning_os.app.outcomes import refusal_from_failure as _refusal_from_failure
from learning_os.app.projection import publish as _publish
from learning_os.app.projection import publish_repo as _publish_repo
from learning_os.app.proposal import (
    CommitIssues,
    CommitOutcome,
    TransactionProposal,
)
from learning_os.derive.validation import validate
from learning_os.domain.codes import REVISION_CONFLICT
from learning_os.domain.failures import (
    Refusal,
    TransactionConflict,
    TransactionSnapshotConflict,
    WriteRefused,
)
from learning_os.store.contracts.gateway import current_gateway_request
from learning_os.store.fingerprint import seed_source_fingerprint, source_fingerprint
from learning_os.store.loader import load_repo
from learning_os.store.session_ledger import load_session_ledger as _load_session_ledger
from learning_os.store.session_ledger import record_touched as _record_touched
from learning_os.store.transactions import (
    PostCommitFailure,
    ProjectionFailure,
    TransactionFailure,
    TransactionPublicationUncertain,
    TransactionService,
)


def _confirmation_from(result) -> dict:
    """Receipt facts a command reports after its own successful transaction."""
    if result is None:
        return {}
    parts = result.receipt_path.parts
    try:
        relative = Path(*parts[parts.index("operations"):]).as_posix()
    except ValueError:
        relative = result.receipt_path.name
    return {
        "transaction_id": result.transaction_id,
        "receipt_path": relative,
        "artifact_revisions": dict(result.revisions),
        "snapshot_after": result.snapshot_after,
        "replayed": bool(result.replayed),
    }


def commit_proposal(ctx: OpContext, proposal: TransactionProposal) -> CommitOutcome:
    """Commit one named, receipt-producing canonical transaction.

    Returns ``(code, errors, confirmation)``. The confirmation travels back to
    the caller explicitly rather than through module state: a command reports
    the receipt for *its own* transaction, and a module global could not
    express that — it outlived the operator lock and was read after release.
    On any failure the confirmation is empty, so a caller cannot accidentally
    report a receipt for a write that did not happen.

    ``validate_extra`` is one plan-class gate: ``validate_extra(repo, issues)``
    receives the staged repository and that run's complete validation issues
    (errors and warnings alike) and returns the refusal list the transaction
    fails on. It runs inside the commit's validation step — after the writes
    land, before anything is published — so a refusal still rolls everything
    back. Without it the gate is the historical errors-only list.
    """
    root = ctx.root
    if current_gateway_request() is None:
        # Name the way through, not only the refusal: the bare named command
        # is what agents find first, and without a pointer the envelope format
        # has to be reverse-engineered from the gateway source.
        return CommitOutcome(2, [
            "canonical writes must use GatewayEnvelopeV2; direct CLI application "
            f"is disabled — apply it with `los capability {proposal.capability} "
            f"--payload-file ENVELOPE.json` (payload schema: `los capabilities "
            f"{proposal.capability} --json`; envelope: WORKFLOWS §25c)"
        ], {})
    # PLAN D7: after a failed push only the stored-SHA retry or close may
    # follow, so a new canonical write owned by that session refuses here,
    # before any canonical mutation or receipt. Identity resolves exactly
    # as the touched callback claims it (explicit, then the sealed
    # envelope, then the environment, then the channel — including the
    # goal handler's sealed override); another session's write proceeds.
    # The read fails closed: a missing ledger is a session with no window
    # yet (allowed), but unreadable/unsupported own metadata cannot
    # authorize the write, so the loader's complaint refuses it. The
    # committed_unpushed refusal keys on the state, never on the SHA
    # being non-null. The message reuses the session machine's §13 row-8
    # refusal verbatim, naming the stored SHA exactly as that machine
    # does for the same bytes.
    try:
        own = _load_session_ledger(root)
    except WriteRefused as exc:
        return CommitOutcome(2, [str(exc)], {})
    if own is not None and own["state"] == "committed_unpushed":
        return CommitOutcome(2, [f"already committed as {own['commit_sha']}; "
                   "use --push or --close"], {})
    # The proposal's family (proposal.family) is selected by its owning
    # capability; the engine refuses a gateway request whose capability
    # does not match the transaction it carries, so a family cannot be
    # substituted at commit time.
    if proposal.clock is None:
        service = TransactionService(root)
    else:
        service = TransactionService(root, clock=proposal.clock)
    delete_paths = tuple(Path(path) for path in (proposal.deletes or ()))
    for path in (*proposal.writes, *delete_paths):
        if path.exists() and not path.is_file():
            return CommitOutcome(
                2, [f"cannot change {path}: target is not a regular file"], {})
    validated_repo = None

    def validation_errors():
        nonlocal validated_repo
        validated_repo = load_repo(root)
        issues = validate(validated_repo, online=False)
        if proposal.validate_extra is not None:
            return proposal.validate_extra(validated_repo, issues)
        return [issue for issue in issues if issue.severity == "E"]

    def publish_validated_state(snapshot_after_id: str | None = None) -> str:
        nonlocal validated_repo
        repo = validated_repo or load_repo(root)
        if snapshot_after_id is not None:
            seed_source_fingerprint(repo, snapshot_after_id)
        _publish_repo(repo)
        projected_snapshot = f"sha256:{source_fingerprint(repo)}"
        validated_repo = None
        return projected_snapshot

    if proposal.validate_state == "STANDARD":
        validate_state = validation_errors
    else:
        validate_state = proposal.validate_state
    if proposal.publish == "STANDARD":
        publish = publish_validated_state
    else:
        publish = proposal.publish
    def standard_rollback_publish() -> None:
        _publish(root)

    def standard_touched(paths) -> None:
        _record_touched(root, paths)

    if proposal.rollback_publish == "STANDARD":
        rollback_publish = standard_rollback_publish
    else:
        rollback_publish = proposal.rollback_publish
    if proposal.touched == "STANDARD":
        touched = standard_touched
    else:
        touched = proposal.touched

    kwargs: dict = {"capability": proposal.capability, "writes": proposal.writes}
    if proposal.deletes is not None:
        kwargs["deletes"] = delete_paths
    kwargs["artifact_ids"] = proposal.artifact_ids
    kwargs["expected_revisions"] = (
        {} if proposal.expected_revisions is None else proposal.expected_revisions)
    if validate_state is not None:
        kwargs["validate_state"] = validate_state
    if publish is not None:
        kwargs["publish"] = publish
    if rollback_publish is not None:
        kwargs["rollback_publish"] = rollback_publish
    if touched is not None:
        kwargs["touched"] = touched
    kwargs["metadata"] = proposal.metadata
    if proposal.expected_snapshot is not None:
        kwargs["expected_snapshot"] = proposal.expected_snapshot
    if proposal.transaction_writes is not None:
        kwargs["transaction_writes"] = proposal.transaction_writes
    if proposal.write_authorities is not None:
        kwargs["write_authorities"] = proposal.write_authorities

    try:
        if proposal.translate is None:
            result = service.commit(**kwargs)
        else:
            try:
                result = service.commit(**kwargs)
            except BaseException as exc:
                translated = proposal.translate(exc)
                if translated is None:
                    raise
                raise translated from exc
    except TransactionConflict as exc:
        _record_gateway_refusal(REVISION_CONFLICT, True)
        return CommitOutcome(3, CommitIssues(
            ["artifact revision conflict — reload the affected record before writing"],
            details={"conflicts": {
                artifact: {"expected": expected, "actual": actual}
                for artifact, (expected, actual) in exc.conflicts.items()
            }}), {}, refusal=Refusal(REVISION_CONFLICT, True))
    except TransactionSnapshotConflict:
        # The V2 gateway owns the typed stale-snapshot response. Let the exact
        # expected/actual values cross that boundary without being flattened
        # into a generic transaction failure.
        raise
    except (ProjectionFailure, PostCommitFailure, TransactionPublicationUncertain):
        # Typed failure provenance crosses the (code, errors) channel by
        # propagation: the gateway classifies by its attrs, and direct CLI
        # use still exits 2 through los.py's TransactionFailure handler.
        raise
    except TransactionFailure as exc:
        # Canonical write refusal is a handled operator error, not an internal
        # process failure. Preserve the gateway's established exit-code 2.
        # A typed failure also records its V2 code for the gateway dispatch;
        # an untyped one stays prose and classifies as INVALID_REQUEST.
        refusal = _refusal_from_failure(exc)
        if refusal is not None:
            _record_gateway_refusal(refusal.code, refusal.retryable)
        return CommitOutcome(2, [str(exc)], {}, refusal=refusal)
    return CommitOutcome(0, [], _confirmation_from(result))
