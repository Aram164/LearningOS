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

import json
import sys
from pathlib import Path

from learning_os.contracts.gateway import current_gateway_request
from learning_os.domain.codes import REVISION_CONFLICT
from learning_os.fingerprint import seed_source_fingerprint, source_fingerprint
from learning_os.loader import load_repo
from learning_os.ops._legacy_plumbing import (
    _confirmation_from,
    _publish,
    _publish_repo,
    _record_gateway_refusal,
    _record_touched,
    _refusal_from_failure,
)
from learning_os.ops.context import OpContext
from learning_os.ops.proposal import TransactionProposal
from learning_os.rules import validate
from learning_os.transactions import (
    PostCommitFailure,
    ProjectionFailure,
    TransactionConflict,
    TransactionFailure,
    TransactionService,
    TransactionSnapshotConflict,
)


def commit_proposal(ctx: OpContext, proposal: TransactionProposal) -> tuple[int, list[str], dict]:
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
        return 2, [
            "canonical writes must use GatewayEnvelopeV2; direct CLI application "
            f"is disabled — apply it with `los capability {proposal.capability} "
            f"--payload-file ENVELOPE.json` (payload schema: `los capabilities "
            f"{proposal.capability} --json`; envelope: WORKFLOWS §25c)"
        ], {}
    if proposal.clock is None:
        service = TransactionService(root)
    else:
        service = TransactionService(root, clock=proposal.clock)
    delete_paths = tuple(Path(path) for path in (proposal.deletes or ()))
    for path in (*proposal.writes, *delete_paths):
        if path.exists() and not path.is_file():
            return 2, [f"cannot change {path}: target is not a regular file"], {}
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
        print("los: artifact revision conflict — reload the affected record before writing",
              file=sys.stderr)
        print(json.dumps({
            "conflicts": {artifact: {"expected": expected, "actual": actual}
                          for artifact, (expected, actual) in exc.conflicts.items()}
        }, ensure_ascii=False), file=sys.stderr)
        _record_gateway_refusal(REVISION_CONFLICT, True)
        return 3, [], {}
    except TransactionSnapshotConflict:
        # The V2 gateway owns the typed stale-snapshot response. Let the exact
        # expected/actual values cross that boundary without being flattened
        # into a generic transaction failure.
        raise
    except (ProjectionFailure, PostCommitFailure):
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
            _record_gateway_refusal(*refusal)
        return 2, [str(exc)], {}
    return 0, [], _confirmation_from(result)
