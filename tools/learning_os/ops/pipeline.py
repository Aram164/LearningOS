"""The operations pipeline for registered operations (SPEC §11.2).

``run_cli`` serves direct CLI invocations; ``run_gateway`` serves V2 gateway
envelopes. Both build an :class:`Outcome`: the commit facts plus the exact
bytes for the adapter to write and the process exit.
"""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
import re
from dataclasses import dataclass
from pathlib import Path

from learning_os.contracts.gateway import (
    gateway_request_context,
    verified_gateway_snapshot,
)
from learning_os.contracts.requests import request_schema
from learning_os.diagnostics import conventions as diag_conventions
from learning_os.diagnostics import tracer as diag_tracer
from learning_os.domain.codes import (
    IDEMPOTENCY_CONFLICT,
    INTERNAL_FAILURE,
    INVALID_REQUEST,
    STALE_SNAPSHOT,
    UNCONFIRMED,
    UNKNOWN_CAPABILITY,
)
from learning_os.domain.failures import (
    PostCommitFailure,
    ProjectionFailure,
    ReplayEvidenceError,
    TransactionFailure,
    TransactionIdempotencyConflict,
    TransactionRecoveryConflict,
    TransactionRollbackIncomplete,
    WriteRefused,
    _ReplayRecoveryError,
)
from learning_os.fingerprint import canonical_fingerprint
from learning_os.ops import handlers  # noqa: F401  (registration side effect)
from learning_os.ops._legacy_plumbing import (
    _current_session_id,
    _json_layout,
    _load_session_paths,
    _operator_lock,
    _row_proven_state,
    _session_ledger,
    _session_path_state,
    _stamp_session_row,
    _take_gateway_refusal,
    _write_session_ledger,
)
from learning_os.ops.check import check_proposal
from learning_os.ops.commit import commit_proposal
from learning_os.ops.context import OpContext
from learning_os.ops.legacy import (
    _context_from_v2,
    _dispatch,
    _validate_capability_envelope,
    gesture_allowed,
    gesture_refusal,
    prepare_dispatch,
)
from learning_os.ops.outcomes import classify, error_object, resolve
from learning_os.ops.registry import REGISTRY
from learning_os.ops.render import call_renderer
from learning_os.transactions import (
    TransactionResult,
    TransactionSnapshotConflict,
    replay_for_request,
)


@dataclass(frozen=True)
class Outcome:
    """The commit facts plus the exact bytes for the adapter to write."""

    commit: str                        # "none" | "committed" | "unknown"
    ok: bool
    payload: dict | None
    error: dict | None                 # error object §9.2
    exit_code: int
    receipt: dict | None               # transaction_id, receipt_path, snapshot_after
    replayed: bool
    stdout: str                        # exactly what the adapter prints
    stderr: str


_KIND_TO_INVOCATION = {
    "query": "query",
    "command": "command",
    "porcelain": "porcelain",
    # S13 candidate J7: tool-kind operations are lock-free reads; "query" is
    # the closest invocation enumerant. Unread by all S13 code paths.
    "tool": "query",
}


def run_cli(root: Path, operation: str, args) -> Outcome:
    """Run registered ``operation`` for a direct CLI invocation (SPEC 11.2).

    Takes the shared operator lock for a query, the exclusive lock for a
    command or porcelain operation, and no lock for a tool. Any other kind
    string takes the exclusive lock (fail-safe default, S13 candidate J17).
    """

    entry = REGISTRY[operation]
    if entry.kind == "query":
        with _operator_lock(root, shared=True):
            return _execute_cli(root, operation, entry, args)
    if entry.kind == "tool":
        return _execute_cli(root, operation, entry, args)
    with _operator_lock(root):
        return _execute_cli(root, operation, entry, args)


def _execute_cli(root: Path, operation: str, entry, args) -> Outcome:
    schema = request_schema(root, operation)
    properties = schema.get("properties", {})
    req = {key: value for key, value in vars(args).items() if key in properties}
    checking = req.get("check") is True
    ctx = OpContext(
        root=root,
        operation=operation,
        channel="operator",
        invocation="check" if checking else _KIND_TO_INVOCATION.get(
            entry.kind, "command"),
        gateway=None,
    )
    commit, receipt, replayed = "none", None, False
    try:
        result = entry.handler(ctx, req)
        if checking and result.proposal is not None:
            record = check_proposal(ctx, result.proposal)
            payload = (call_renderer(
                operation, "render_check", entry.render_check,
                record, result.payload)
                if entry.render_check is not None else record)
        elif result.proposal is not None:
            captured, errors = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(captured), \
                    contextlib.redirect_stderr(errors):
                code, commit_errors, confirmation = commit_proposal(
                    ctx, result.proposal)
                if code == 0:
                    commit = "committed"
                    receipt = {key: confirmation.get(key) for key in (
                        "transaction_id", "receipt_path", "snapshot_after")}
                    replayed = bool(confirmation.get("replayed", False))
                if result.after_commit is not None:
                    result.after_commit(code, commit_errors, confirmation)
            if code != 0:
                if (result.on_commit_refused is not None
                        or result.refused_stdout is not None):
                    stdout, stderr = _legacy_refusal_streams(
                        operation, result, commit_errors, errors.getvalue())
                    return Outcome(
                        commit=commit, ok=False, payload=None, error=None,
                        exit_code=code, receipt=receipt, replayed=replayed,
                        stdout=stdout, stderr=stderr)
                if errors.getvalue().strip():
                    lines = errors.getvalue().strip().splitlines()
                else:
                    lines = [f"los: {error}" for error in commit_errors]
                return Outcome(
                    commit=commit, ok=False, payload=None, error=None,
                    exit_code=code, receipt=receipt, replayed=replayed,
                    stdout="", stderr="".join(f"{line}\n" for line in lines))
            payload = (call_renderer(
                operation, "finish", result.finish, confirmation)
                if result.finish is not None
                else {**result.payload, **confirmation})
        elif result.finish is not None:
            payload = call_renderer(operation, "finish", result.finish, {})
        else:
            payload = result.payload
        exit_code = 1 if result.diagnostic_failed else 0
        if entry.human is not None and not getattr(args, "json", False):
            stdout = call_renderer(
                operation, "human", entry.human, payload) + "\n"
        elif result.json_dumps is not None:
            stdout = result.json_dumps(payload) + "\n"
        else:
            stdout = json.dumps(payload, **_json_layout()) + "\n"
    except Exception as exc:
        return _cli_refusal(exc, entry=entry, args=args, commit=commit,
                            receipt=receipt, replayed=replayed)
    return Outcome(
        commit=commit, ok=exit_code == 0, payload=payload, error=None,
        exit_code=exit_code, receipt=receipt, replayed=replayed,
        stdout=stdout, stderr="",
    )


def _legacy_refusal_streams(operation: str, result, commit_errors: list,
                            commit_stderr: str) -> tuple[str, str]:
    """A refused commit's legacy ``(stdout, stderr)`` (SPEC (bd)).

    A legacy handler let ``commit_proposal``'s own complaint (the revision
    conflict lines) reach stderr first, then printed its refusal lines to
    stderr, its refusal JSON to stdout, or both.
    """
    lines = (call_renderer(
        operation, "on_commit_refused",
        result.on_commit_refused, commit_errors)
        if result.on_commit_refused is not None else [])
    stdout = (call_renderer(
        operation, "refused_stdout",
        result.refused_stdout, commit_errors) + "\n"
        if result.refused_stdout is not None else "")
    return stdout, commit_stderr + "".join(f"{line}\n" for line in lines)


def _cli_error_code(exc: Exception) -> tuple[str, bool]:
    """The D16 stderr/JSON code: the gateway.refusal code for the failure.

    Failures the refusal table does not type fall back to INVALID_REQUEST,
    exactly as _classify_failure's untyped branch does.
    """

    row = classify(exc, "gateway.refusal")
    if row is not None:
        resolved = resolve(row, exc)
        if resolved["code"] is not None:
            return resolved["code"], bool(resolved["retryable"])
    return INVALID_REQUEST, False


def _cli_refusal(exc: Exception, *, entry=None, args=None,
                 commit="none", receipt=None, replayed=False) -> Outcome:
    """Registered-operation CLI refusal rendering (SPEC 9.4, D16).

    stderr carries `los: <CODE>: <message>`, then one `  did you mean:
    <id>` line per suggestion not already contained in the message, then
    `  next: <remedy>` when present. R2-style extra_stderr lines, if any,
    print verbatim last. With --json on a JSON-default command, stdout
    also carries {"error": <error object>}. Unregistered commands keep
    their current output (they never reach this path).
    """

    row = classify(exc, "cli")
    if row is None:
        raise
    message = str(exc)
    code, retryable = _cli_error_code(exc)
    reason = getattr(exc, "reason", None)
    suggestions = getattr(exc, "suggestions", None) or ()
    remedy = getattr(exc, "remedy", None)
    lines = [f"los: {code}: {message}"]
    for suggestion in suggestions:
        if suggestion not in message:
            lines.append(f"  did you mean: {suggestion}")
    if remedy is not None:
        lines.append(f"  next: {remedy}")
    for line in getattr(exc, "extra_stderr", ()) or ():
        lines.append(line)
    stderr = "\n".join(lines) + "\n"
    stdout = ""
    if getattr(args, "json", False) and entry.human is None:
        stdout = json.dumps({
            "error": error_object(
                code, message, retryable=retryable, reason=reason,
                suggestions=list(suggestions) or None, remedy=remedy),
        }, **_json_layout()) + "\n"
    if isinstance(exc, PostCommitFailure):
        commit = "committed"
        receipt = {key: getattr(exc, key) for key in (
            "transaction_id", "receipt_path", "snapshot_after")}
    elif isinstance(exc, TransactionRollbackIncomplete) or (
            isinstance(exc, ProjectionFailure) and not exc.rollback_complete):
        commit = "unknown"
    return Outcome(commit=commit, ok=False, payload=None, error=None,
                   exit_code=resolve(row, exc)["exit"], receipt=receipt,
                   replayed=replayed, stdout=stdout, stderr=stderr)


def _gateway_error(code: str, message: str, *, retryable: bool = False,
                   details: dict | None = None, reason: str | None = None,
                   suggestions: list | None = None,
                   remedy: str | None = None) -> dict:
    return error_object(code, message, retryable=retryable, details=details,
                        reason=reason, suggestions=suggestions, remedy=remedy)


def _classify_failure(code: int, message: str, *,
                      failure: BaseException | None = None,
                      refusal: tuple[str, bool] | None = None) -> dict:
    """Turn a failed dispatch into a typed V2 error by type, never by prose.

    ``code`` is the handler's exit status, retained for call compatibility
    and deliberately ignored: exit 3 alone is ambiguous (a snapshot guard,
    a revision conflict, and a stale reviewed digest all use it), and the
    message echoes user-supplied ids that may name snapshots, approvals,
    or any other lookalike. The V2 code comes from the refusal's type —
    either the ``failure`` that propagated out of the handler, or the
    ``refusal`` pair a catching handler step recorded for the gateway.
    An untyped refusal is ``INVALID_REQUEST``.
    """
    if refusal is not None:
        refused_code, retryable = refusal
        return _gateway_error(refused_code, message, retryable=retryable)
    if failure is not None:
        row = classify(failure, "gateway.refusal")
        if row is not None:
            resolved = resolve(row, failure)
            if resolved["code"] is not None:
                if (isinstance(failure, WriteRefused)
                        and failure.gateway_message is not None):
                    message = failure.gateway_message
                reason = remedy = suggestions = None
                if (isinstance(failure, WriteRefused)
                        and failure.reason is not None):
                    reason = failure.reason
                    suggestions = getattr(failure, "suggestions", None)
                    remedy = failure.remedy
                return _gateway_error(resolved["code"], message,
                                      retryable=resolved["retryable"],
                                      reason=reason, suggestions=suggestions,
                                      remedy=remedy)
    return _gateway_error(INVALID_REQUEST, message)


def _v2_exit_code(handler_code: int, error: dict | None) -> int:
    """Exit status for a V2 dispatch: STALE_SNAPSHOT exits 3 on every path.

    Every other refusal keeps the handler's own exit code.
    """
    if error is not None and error.get("code") == STALE_SNAPSHOT:
        return 3
    return handler_code


def _projection_error(exc: ProjectionFailure) -> dict:
    """Typed projection outcome: subsystem proven, prose not consulted.

    A complete rollback proves the write never committed; an incomplete
    one leaves the outcome unknown however the message reads. A complete
    rollback over a pre-state that itself does not publish is a
    shadow-validation refusal (JF-11), reported like one.
    """
    row = classify(exc, "gateway.dispatch")
    resolved = resolve(row, exc)
    return _gateway_error(resolved["code"], str(exc),
                          retryable=resolved["retryable"],
                          details=resolved["details"])


def _post_commit_error(exc: PostCommitFailure) -> dict:
    """Committed yet failed: never a definitive refusal."""
    row = classify(exc, "gateway.dispatch")
    resolved = resolve(row, exc)
    return _gateway_error(resolved["code"], str(exc),
                          retryable=resolved["retryable"],
                          details=resolved["details"])


def _v2_response(
    envelope: dict,
    *,
    ok: bool,
    replayed: bool = False,
    transaction_id: str | None = None,
    receipt_path: str | None = None,
    snapshot_after: str | None = None,
    result: dict | None = None,
    error: dict | None = None,
) -> dict:
    # Phase 4A: the persisted response summary. IDs and codes only — never
    # `result` (domain facts may echo learner content) and never the error
    # message (validator text may quote canonical prose). The Operations
    # view and the resolver rebuild responses from this alone.
    diag_tracer.emit_event(
        diag_conventions.EVENT_RESPONSE_EMITTED,
        status="ok" if ok else "error",
        attrs={
            "ok": ok,
            "code": (error or {}).get("code"),
            "retryable": (error or {}).get("retryable", False),
            "replayed": replayed,
            "transaction_id": transaction_id,
            "receipt_path": receipt_path,
            "snapshot_after": snapshot_after,
        })
    return {
        "schema_version": 2,
        "request_id": str(envelope.get("request_id") or "invalid-request"),
        "idempotency_key": str(envelope.get("idempotency_key") or "invalid-request"),
        "capability": str(envelope.get("capability") or "invalid-capability"),
        "ok": ok,
        "replayed": replayed,
        "transaction_id": transaction_id,
        "receipt_path": receipt_path,
        "snapshot_after": snapshot_after,
        "result": dict(result or {}),
        "error": error,
    }


# An exact retry must answer with the domain fact the first call answered
# with, not merely with bookkeeping. The caller asked "where did my capture
# go?", and a replay that omits `captured` forces the interface to either guess
# or send the write a second time. The path is recovered from the already
# committed receipt — the handler is never rerun, so a file capture never
# reopens or rereads the external source it was approved against.
_REPLAY_DOMAIN_RESULT: dict[str, tuple[str, str]] = {
    "capture.create": ("captured", "work/inbox/"),
    "garden.seed.create": ("seed_path", "knowledge/garden/"),
}


def _replayed_batch_result(payload: object,
                           replay: TransactionResult) -> dict:
    """Recover the original batch breakdown from verified evidence alone.

    A retry carries an envelope proven identical-intent to the approved one,
    so its bundle is the verified request record, in request order; the
    validated receipt's ``writes`` prove what the transaction created. The
    replayed set is exactly the difference — no handler rerun, no live
    canonical reads. Replayed-note paths come from the bundle rather than
    the receipt, which is sound only because durable notes are never
    deleted or moved (``artifact.delete`` is forbidden; ``note.revise``
    preserves id, path, and role).
    """
    if not isinstance(payload, dict) or not isinstance(
            payload.get("bundle"), dict):
        raise _ReplayRecoveryError(
            "replayed batch evidence carries no verified bundle")
    notes = payload["bundle"].get("notes")
    if not isinstance(notes, list) or not notes:
        raise _ReplayRecoveryError(
            "replayed batch evidence carries no verified notes list")
    requested: list[tuple[str, str]] = []
    for item in notes:
        analysis = item.get("analysis") if isinstance(item, dict) else None
        if not isinstance(analysis, dict) \
                or not isinstance(analysis.get("id"), str) \
                or not isinstance(analysis.get("path"), str):
            raise _ReplayRecoveryError(
                "replayed batch evidence carries a malformed bundle item")
        requested.append((analysis["id"], analysis["path"]))
    if len({note_id for note_id, _ in requested}) != len(requested):
        raise _ReplayRecoveryError(
            "replayed batch evidence carries duplicate note ids")
    receipt = replay.receipt
    if not isinstance(receipt, dict):
        raise _ReplayRecoveryError("replayed evidence carries no receipt")
    writes = receipt.get("writes")
    if not isinstance(writes, list):
        raise _ReplayRecoveryError("replayed batch receipt writes are malformed")
    by_id = dict(requested)
    created: set[str] = set()
    for row in writes:
        if not isinstance(row, dict) or not isinstance(row.get("path"), str):
            raise _ReplayRecoveryError(
                "replayed batch receipt write row is malformed")
        written = row["path"]
        if written in _UNPROVABLE_AGGREGATE_LEDGERS:
            continue
        if row.get("created") is not True \
                or not written.startswith("knowledge/notes/") \
                or ".." in written.split("/") \
                or not written.endswith(".md"):
            raise _ReplayRecoveryError(
                f"replayed batch receipt writes outside knowledge/notes/: "
                f"{written}")
        note_id = written.rsplit("/", 1)[-1][:-len(".md")]
        if note_id not in by_id or by_id[note_id] != written \
                or note_id in created:
            raise _ReplayRecoveryError(
                f"replayed batch receipt write matches no requested note: "
                f"{written}")
        created.add(note_id)
    return {
        "created_note_ids": [note_id for note_id, _ in requested
                             if note_id in created],
        "replayed_note_ids": [note_id for note_id, _ in requested
                              if note_id not in created],
        "note_paths": dict(requested),
    }


def _replayed_domain_result(root: Path, capability: str,
                            replay: TransactionResult,
                            payload: object = None) -> dict:
    """Recover the original domain facts from the already-validated receipt.

    ``replay.receipt`` has already been schema-validated and cross-bound to
    this exact request by ``replay_for_request`` — its capability, status, and
    transaction id are trustworthy. This checks only the domain-specific shape
    every capture-like capability's receipt must have: exactly one created
    write inside the capability's own directory. Rereading or re-verifying the
    generic fields here would be the "weaker helper" the recovery design
    forbids. A batch receipt instead carries the created subset of a verified
    bundle, recovered with the retry envelope's identical-intent payload.
    """
    if capability == "note.analysis.save_batch":
        return _replayed_batch_result(payload, replay)
    try:
        field, prefix = _REPLAY_DOMAIN_RESULT[capability]
    except KeyError:
        return {}
    receipt = replay.receipt
    if not isinstance(receipt, dict):
        raise _ReplayRecoveryError("replayed evidence carries no receipt")
    writes = receipt.get("writes")
    if not isinstance(writes, list) or len(writes) != 1:
        raise _ReplayRecoveryError(
            f"replayed receipt must record exactly one write, found "
            f"{len(writes) if isinstance(writes, list) else 'a non-list'}"
        )
    row = writes[0]
    if not isinstance(row, dict) or not row.get("created") \
            or not isinstance(row.get("path"), str):
        raise _ReplayRecoveryError("replayed receipt write row is malformed")
    written = row["path"]
    if not written.startswith(prefix) or ".." in written.split("/"):
        raise _ReplayRecoveryError(
            f"replayed receipt writes outside {prefix}: {written}"
        )
    return {field: written}


# Shared multi-entry ledgers a transaction only ever partially writes. Receipt
# V2 proves this transaction's own row inside each of them (cross-checked by
# `replay_for_request`), never their whole byte content — so replay-repair can
# only carry forward a *prior* row this session already proved by directly
# observing its own fresh write, never assert one from scratch.
_UNPROVABLE_AGGREGATE_LEDGERS = (
    "operations/transactions/revisions.yaml",
    "operations/transactions/idempotency.yaml",
)


def _repair_replayed_session_ownership(root: Path,
                                       replay: TransactionResult,
                                       session_id: str | None = None) -> None:
    """Rebuild ephemeral session ownership from the already-validated receipt.

    A process can die after Receipt V2 and the idempotency ledger are durable
    but before the temporary learning-session ledger is written.  Exact replay
    is the recovery boundary, so it also repairs that bookkeeping; otherwise
    the UI would retire its durable record while ``session-end`` forgot the
    canonical file the recovered gesture authored.

    This must never simply re-observe the current filesystem and adopt it as
    the ownership claim: an out-of-band edit between the original commit and
    this replay would then be laundered into the session's own authorship, and
    ``session-end`` would happily stage and commit it as though the gateway
    transaction had written it. Every claim made here is instead the
    *authored* state Receipt V2 itself proves — ``writes[].sha256_after``, or
    absence when it is ``null`` (each path already proven safe and canonical
    by ``replay_for_request``), plus the receipt's own bytes, which this
    function reads and hashes itself rather than trusting a second party's
    claim about them. That authored state is compared against the live file;
    a mismatch anywhere refuses the whole repair before a single byte of the
    ownership ledger is written, so an existing row is never overwritten with
    a laundered observation and no replacement ledger is created from an
    unproven one.
    """
    receipt = replay.receipt
    if not isinstance(receipt, dict):
        raise _ReplayRecoveryError(
            "cannot repair session ownership: replayed evidence carries no receipt"
        )
    writes = receipt.get("writes")
    if not isinstance(writes, list):
        raise _ReplayRecoveryError(
            "cannot repair session ownership: replayed receipt writes are malformed"
        )

    authored: dict[str, dict[str, str]] = {}
    for row in writes:
        relative = row.get("path") if isinstance(row, dict) else None
        if not isinstance(relative, str) or not relative:
            raise _ReplayRecoveryError(
                "cannot repair session ownership: replayed receipt path is unsafe"
            )
        sha_after = row.get("sha256_after") if isinstance(row, dict) else None
        if sha_after is None:
            authored[relative] = {"state": "absent"}
        elif isinstance(sha_after, str) and re.fullmatch(r"[0-9a-f]{64}", sha_after):
            authored[relative] = {"state": "file", "sha256": sha_after}
        else:
            raise _ReplayRecoveryError(
                "cannot repair session ownership: replayed receipt write has an "
                "unproven authored state"
            )

    try:
        receipt_bytes = replay.receipt_path.read_bytes()
        receipt_relative = replay.receipt_path.resolve().relative_to(
            root.resolve()
        ).as_posix()
    except (OSError, ValueError) as exc:
        raise _ReplayRecoveryError(
            f"cannot repair session ownership: {exc}"
        ) from exc
    authored[receipt_relative] = {
        "state": "file", "sha256": hashlib.sha256(receipt_bytes).hexdigest(),
    }

    # The repair runs outside any gateway request context, so ambient
    # session resolution would land in the default channel's ledger — not
    # the one the original write recorded. The replayed envelope's sealed
    # session recovers exactly that ledger; without one, the receipt names
    # the writing channel, which recovers the channel ledger when no
    # session is named. A named session still wins: that session is
    # performing the recovery.
    origin = receipt.get("request") if isinstance(receipt, dict) else None
    origin = origin.get("channel") if isinstance(origin, dict) else None
    if not isinstance(origin, str) or not origin:
        origin = None
    session = _current_session_id(channel=origin, explicit=session_id)

    # A lost session ledger is reconciled by hand, never reconstructed.
    #
    # Rebuilding one from scratch would mean deciding what this session owns
    # with no prior record to check against, and the shared revision and
    # idempotency ledgers make that undecidable: their bytes carry rows for
    # many transactions while this receipt proves only its own. Adopting them
    # would launder an unrelated edit into this session's authorship; omitting
    # them would let `session-end` commit an authored file while leaving the
    # revision bump that belongs to it out of the same commit. So a missing
    # ledger fails closed instead.
    if not _session_ledger(root, session).is_file():
        raise _ReplayRecoveryError(
            "cannot repair session ownership: the session ledger is gone, and this "
            "receipt cannot prove the bytes of the shared revision and idempotency "
            "ledgers — reconcile this transaction by hand"
        )
    try:
        existing = _load_session_paths(root, session)
    except WriteRefused as exc:
        raise _ReplayRecoveryError(
            f"cannot repair session ownership: {exc}"
        ) from exc

    for ledger_relative in _UNPROVABLE_AGGREGATE_LEDGERS:
        proven = existing.get(ledger_relative)
        if proven is not None:
            # Carried forward as *previously proven*, then re-checked against
            # the live file below. Never re-observed: a fresh hash taken here
            # is exactly the laundering this function exists to prevent.
            authored[ledger_relative] = proven
        # A row this session never held is left unclaimed rather than invented.
        # Not every write path claims these ledgers — an approved AI delivery
        # records only the files it staged — so a missing row is ordinary, and
        # the one thing that must not happen is adopting their current bytes.

    for relative, state in authored.items():
        if _session_path_state(root, relative) != _row_proven_state(state):
            raise _ReplayRecoveryError(
                "cannot repair session ownership: "
                f"{relative} changed since its recorded transaction"
            )

    merged = dict(existing)
    merged.update(authored)
    # The repaired rows are stamped, not bare: a receipt-derived row takes
    # its provenance from the receipt's own recorded channel, with the claim
    # time set to this repair — that is when this session took ownership of
    # the recovered write. Rows that already carry a stamp (carried-forward
    # aggregate claims) keep it.
    actor = origin or "unknown"
    for relative, state in merged.items():
        if state.get("channel") and state.get("recorded_at"):
            continue
        state["channel"] = actor
        state["recorded_at"] = _stamp_session_row(
            root, relative, actor)["recorded_at"]
    try:
        _write_session_ledger(root, merged, session)
    except WriteRefused as exc:
        raise _ReplayRecoveryError(
            f"cannot repair replayed session ownership: {exc}"
        ) from exc


def _replay_response(root: Path, envelope: dict,
                     replay: TransactionResult) -> dict:
    receipt_path = replay.receipt_path.relative_to(root).as_posix()
    confirmation = {
        "transaction_id": replay.transaction_id,
        "receipt_path": receipt_path,
        "artifact_revisions": dict(replay.revisions),
        "snapshot_after": replay.snapshot_after,
        "replayed": True,
        **_replayed_domain_result(root, str(envelope.get("capability")), replay,
                                  envelope.get("payload")),
    }
    return _v2_response(
        envelope,
        ok=True,
        replayed=True,
        transaction_id=replay.transaction_id,
        receipt_path=receipt_path,
        snapshot_after=replay.snapshot_after,
        result=confirmation,
    )


def _close_attempt(attempt, code: int, status: str,
                   attrs: dict | None = None) -> int:
    """Close the attempt span and report the exit code unchanged.

    The response emission is recorded here — the one place every gateway
    return funnels through — so no return site can forget its span.
    """
    stage = (attrs or {}).get("stage")
    if status == "error" and stage in diag_conventions.FAILURE_STAGES:
        diag_tracer.emit_event(
            diag_conventions.EVENT_STAGE_FAILED,
            span_id=attempt.span_id, context=attempt.context,
            stage=stage, status="error",
            attrs={"exit_code": code})
    attempt.close(status, {"exit_code": code, **(attrs or {})})
    return code


def _commit_from_response(response: dict | None) -> str:
    """The Outcome commit flag derived from the final V2 response (SPEC §11.2).

    ``"committed"`` when the response proves a commit (ok, a replay, or a
    transaction id); ``"unknown"`` when the error details prove an incomplete
    rollback; ``"none"`` otherwise. The two site-known unknowns — the
    ``gateway.dispatch`` Exception row and a carried
    ``TransactionRollbackIncomplete`` refusal — pass ``commit="unknown"``
    explicitly at their ``_finish`` call.
    """
    if response is None:
        return "none"
    if response.get("ok") or response.get("replayed") \
            or response.get("transaction_id") is not None:
        return "committed"
    error = response.get("error") or {}
    if (error.get("details") or {}).get("rollback_complete") is False:
        return "unknown"
    return "none"


def _finish(attempt, code: int, status: str, attrs: dict | None, *,
            stdout: list[str], stderr: list[str],
            response: dict | None = None,
            commit: str | None = None) -> Outcome:
    """Close the attempt exactly as before and build the Outcome.

    Calls ``_close_attempt`` with the same arguments today's code passes;
    ``exit_code`` is its return value. Every ordinary Outcome closes the
    same attempt at the same stage and in the same order.
    """
    exit_code = _close_attempt(attempt, code, status, attrs)
    if response is None:
        return Outcome(commit="none", ok=False, payload=None, error=None,
                       exit_code=exit_code, receipt=None, replayed=False,
                       stdout="".join(stdout), stderr="".join(stderr))
    transaction_id = response.get("transaction_id")
    if transaction_id is not None:
        receipt: dict | None = {
            "transaction_id": transaction_id,
            "receipt_path": response.get("receipt_path"),
            "snapshot_after": response.get("snapshot_after"),
        }
    else:
        receipt = None
    ok = bool(response.get("ok"))
    return Outcome(
        commit=commit if commit is not None else _commit_from_response(response),
        ok=ok,
        payload=dict(response.get("result") or {}) if ok else None,
        error=response.get("error"),
        exit_code=exit_code,
        receipt=receipt,
        replayed=bool(response.get("replayed", False)),
        stdout="".join(stdout),
        stderr="".join(stderr),
    )


def _registered_compute(root: Path, operation: str, envelope: dict,
                        payload: dict, *, context, parser_factory,
                        definitions) -> tuple[int, dict]:
    """Run a registered handler with ``_dispatch``'s (code, result) shape.

    Shared admission first (``prepare_dispatch``, identical to legacy), then
    the request filtered to the effective request-schema properties, then
    the handler. A proposal commits once via ``commit_proposal`` (whose own
    legacy prints are captured, as ``_dispatch`` captures handler prints);
    ``after_commit`` runs once even on a returned refusal; ``finish`` or the
    ``{**payload, **confirmation}`` default shapes success;
    ``on_commit_refused`` or the ``los: ``-prefixed default shapes a
    returned refusal. Raised typed refusals propagate to the dispatch
    except chain, which classifies them exactly as before. The refusal
    cellar clears at the same start/success/take boundaries as ``_dispatch``.
    In check mode the proposal is checked, never committed, and rendered
    with ``render_check``.
    """
    entry = REGISTRY[operation]
    command_parser, namespace = prepare_dispatch(
        root, definitions[operation], envelope, payload,
        parser_factory=parser_factory)
    properties = request_schema(root, operation).get("properties", {})
    req = {key: value for key, value in vars(namespace).items()
           if key in properties}
    checking = payload.get("check") is True
    ctx = OpContext(
        root=root,
        operation=operation,
        channel=context.channel,
        invocation="check" if checking else _KIND_TO_INVOCATION.get(
            entry.kind, "command"),
        gateway=context,
    )
    _take_gateway_refusal()
    res = entry.handler(ctx, req)
    if checking and res.proposal is not None:
        record = check_proposal(ctx, res.proposal)
        if entry.render_check is not None:
            rendered = call_renderer(
                operation, "render_check", entry.render_check,
                record, res.payload)
        else:
            rendered = record
        _take_gateway_refusal()
        return 0, rendered
    if res.proposal is None:
        if res.finish is not None:
            final = call_renderer(operation, "finish", res.finish, {})
        else:
            final = res.payload
        _take_gateway_refusal()
        if res.diagnostic_failed:
            return 1, {"error": json.dumps(final, separators=(",", ":"))}
        return 0, final
    captured, errors = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(captured), contextlib.redirect_stderr(errors):
        code, commit_errors, confirmation = commit_proposal(ctx, res.proposal)
        if res.after_commit is not None:
            res.after_commit(code, commit_errors, confirmation)
    if code != 0:
        refusal = _take_gateway_refusal()
        if res.on_commit_refused is not None or res.refused_stdout is not None:
            # Legacy _dispatch's rule: the complaint, else the printed text.
            text, complaint = _legacy_refusal_streams(
                operation, res, commit_errors, errors.getvalue())
            result = {"error": complaint.strip() or text.strip()
                      or f"{operation} failed"}
        else:
            if errors.getvalue().strip():
                lines = errors.getvalue().strip().splitlines()
            else:
                lines = [f"los: {error}" for error in commit_errors]
            result = {"error": "\n".join(lines)}
        if refusal is not None:
            result["error_code"], result["error_retryable"] = refusal
        return code, result
    _take_gateway_refusal()
    if res.finish is not None:
        final = call_renderer(
            operation, "finish", res.finish, confirmation)
    else:
        final = {**res.payload, **confirmation}
    if res.diagnostic_failed:
        return 1, {"error": json.dumps(final, separators=(",", ":"))}
    return 0, final


def run_gateway(root: Path, envelope: dict, *, requested: str, definitions,
                attempt, replay_only: bool, parser_factory) -> Outcome | None:
    """Run one gateway envelope through admission, replay and dispatch.

    Moved statement for statement from ``cmd_capability``'s V2 region (SPEC
    §11.2 K8): prints become outcome lines, attempt closes become
    ``_finish`` calls. Returns None only for the V1 fall-through, which
    stays in ``cmd_capability``.
    """
    stdout: list[str] = []
    stderr: list[str] = []
    is_v2 = envelope.get("schema_version") == 2
    try:
        _validate_capability_envelope(root, envelope, kind="request")
    except WriteRefused as exc:
        if not is_v2:
            _close_attempt(attempt, 2, "error", {"stage": "core.admission"})
            raise
        response = _v2_response(
            envelope,
            ok=False,
            error=_gateway_error(INVALID_REQUEST, str(exc)),
        )
        _validate_capability_envelope(root, response, kind="result")
        stdout.append(json.dumps(response, indent=2, ensure_ascii=False) + "\n")
        return _finish(attempt, 2, "error", {"stage": "core.admission"},
                       stdout=stdout, stderr=stderr, response=response)
    attempt.event(diag_conventions.EVENT_ENVELOPE_VALIDATED,
                  attrs={"request_id": envelope.get("request_id"),
                         "idempotency_key": envelope.get("idempotency_key")})
    if envelope.get("capability") != requested:
        if is_v2:
            response = _v2_response(
                envelope,
                ok=False,
                error=_gateway_error(
                    INVALID_REQUEST,
                    "envelope capability does not match requested capability",
                ),
            )
            _validate_capability_envelope(root, response, kind="result")
            stdout.append(json.dumps(response, indent=2, ensure_ascii=False) + "\n")
            return _finish(attempt, 2, "error", {"stage": "core.admission"},
                           stdout=stdout, stderr=stderr, response=response)
        stderr.append(
            "los: envelope capability does not match requested capability" + "\n")
        return _finish(attempt, 2, "error", {"stage": "core.admission"},
                       stdout=stdout, stderr=stderr)
    # ``command_definitions`` is the public allowlist.  V2 always gets a typed
    # response, including when the requested name has no declaration.
    if requested not in definitions:
        if is_v2:
            response = _v2_response(
                envelope,
                ok=False,
                error=_gateway_error(
                    UNKNOWN_CAPABILITY,
                    f"unknown or non-public capability: {requested}",
                ),
            )
            _validate_capability_envelope(root, response, kind="result")
            stdout.append(json.dumps(response, indent=2, ensure_ascii=False) + "\n")
            return _finish(attempt, 2, "error", {"stage": "core.admission"},
                           stdout=stdout, stderr=stderr, response=response)
        stderr.append(
            f"los: unknown or non-public capability: {requested}" + "\n")
        return _finish(attempt, 2, "error", {"stage": "core.admission"},
                       stdout=stdout, stderr=stderr)
    payload = envelope.get("payload", {})
    # Every capability takes the same path: declared payload schema, then the
    # handler its named CLI command already uses. `project.create` and
    # `project.update` were special-cased here until 2026-08-08 — the branch
    # accepted a `{"project": {...}}` shape no schema declared, and skipped
    # `_validate_payload` to do it, so an agent obeying the published contract
    # was rejected while an agent sending the undeclared shape was accepted.
    # A gateway is only worth having if its machine-readable contract is the
    # trustworthy part.
    if is_v2:
        try:
            context = _context_from_v2(envelope)
        except WriteRefused as exc:
            response = _v2_response(
                envelope,
                ok=False,
                error=_gateway_error(UNCONFIRMED, str(exc)),
            )
            _validate_capability_envelope(root, response, kind="result")
            stdout.append(json.dumps(response, indent=2, ensure_ascii=False) + "\n")
            return _finish(attempt, 2, "error", {"stage": "core.approval"},
                           stdout=stdout, stderr=stderr, response=response)
        if context.approval_kind == "direct-user-gesture" \
                and not gesture_allowed(context.capability, context.channel):
            # The gesture kind means the user herself acted, so it is
            # admitted only for the closed user-originated allowlist above.
            # Anything else claiming it — notably any canonical-semantics
            # capability — is the untrusted producer claiming to be the
            # trusted one, and fails closed here before the snapshot check.
            # The message names the route back to a permitted write, because
            # the learner reading it in the UI did nothing wrong.
            response = _v2_response(
                envelope,
                ok=False,
                error=_gateway_error(
                    UNCONFIRMED,
                    gesture_refusal(context.capability, context.channel),
                ),
            )
            _validate_capability_envelope(root, response, kind="result")
            stdout.append(json.dumps(response, indent=2, ensure_ascii=False) + "\n")
            return _finish(attempt, 2, "error", {"stage": "core.approval"},
                           stdout=stdout, stderr=stderr, response=response)
        attempt.event(diag_conventions.EVENT_APPROVAL_PASSED)
        # Replay lookup, evidence validation, response construction, and
        # session-ledger repair are one critical section under the repository
        # operator lock — the same lock every ordinary write-handling command
        # holds while it runs. Two concurrent exact replays for the same
        # request must not race the session ledger's read-modify-write, and a
        # replay must never be evaluated against a receipt an in-flight write
        # is still committing. Exactly this function owns the lock: neither
        # helper below acquires it again, so there is no re-entrant deadlock.
        replay: TransactionResult | None = None
        try:
            with _operator_lock(root):
                replay = replay_for_request(root, context)
                if replay is not None:
                    response = _replay_response(root, envelope, replay)
                    _validate_capability_envelope(root, response, kind="result")
                    _repair_replayed_session_ownership(
                        root, replay,
                        session_id=envelope.get("session_id"))
        except TransactionIdempotencyConflict as exc:
            response = _v2_response(
                envelope,
                ok=False,
                error=_gateway_error(IDEMPOTENCY_CONFLICT, str(exc)),
            )
            _validate_capability_envelope(root, response, kind="result")
            stdout.append(json.dumps(response, indent=2, ensure_ascii=False) + "\n")
            attempt.event(diag_conventions.EVENT_REPLAY_CHECKED,
                          status="error", attrs={"outcome": "conflict"})
            return _finish(attempt, 2, "error", {"stage": "core.replay"},
                           stdout=stdout, stderr=stderr, response=response)
        except (ReplayEvidenceError, _ReplayRecoveryError) as exc:
            # Fail closed. Evidence is contradictory or the original write
            # already happened; rerunning the handler here would risk
            # duplicating it, and answering with a guessed path would be a lie
            # about canonical state. Never retryable: the fix is manual
            # reconciliation, not a client resend.
            response = _v2_response(
                envelope,
                ok=False,
                error=_gateway_error(INTERNAL_FAILURE, str(exc), retryable=False),
            )
            _validate_capability_envelope(root, response, kind="result")
            stdout.append(json.dumps(response, indent=2, ensure_ascii=False) + "\n")
            attempt.event(diag_conventions.EVENT_REPLAY_CHECKED,
                          status="error", attrs={"outcome": "evidence-error"})
            return _finish(attempt, 2, "error", {"stage": "core.replay"},
                           stdout=stdout, stderr=stderr, response=response)
        except TransactionRecoveryConflict as exc:
            # A stale crash journal names paths the lookup cannot prove
            # transaction-owned. Nothing was modified and the journal was
            # preserved; the operator reconciles by hand. Never retryable
            # and never definitive: the fix is manual reconciliation, and
            # the request itself was never attempted.
            response = _v2_response(
                envelope,
                ok=False,
                error=_gateway_error(
                    INTERNAL_FAILURE, str(exc), retryable=False,
                    details={
                        "transaction_id": exc.transaction_id,
                        "conflicting_paths": [
                            entry.get("path") for entry in exc.conflicts
                        ],
                        "reasons": sorted({
                            entry.get("reason") for entry in exc.conflicts
                            if entry.get("reason")
                        }),
                    },
                ),
            )
            _validate_capability_envelope(root, response, kind="result")
            stdout.append(json.dumps(response, indent=2, ensure_ascii=False) + "\n")
            attempt.event(diag_conventions.EVENT_REPLAY_CHECKED,
                          status="error", attrs={"outcome": "recovery-conflict"})
            return _finish(attempt, 2, "error", {"stage": "core.replay"},
                           stdout=stdout, stderr=stderr, response=response)
        except TransactionFailure as exc:
            response = _v2_response(
                envelope,
                ok=False,
                error=_gateway_error(INTERNAL_FAILURE, str(exc), retryable=True),
            )
            _validate_capability_envelope(root, response, kind="result")
            stdout.append(json.dumps(response, indent=2, ensure_ascii=False) + "\n")
            attempt.event(diag_conventions.EVENT_REPLAY_CHECKED,
                          status="error", attrs={"outcome": "lookup-failed"})
            return _finish(attempt, 2, "error", {"stage": "core.replay"},
                           stdout=stdout, stderr=stderr, response=response)
        attempt.event(diag_conventions.EVENT_REPLAY_CHECKED,
                      attrs={"outcome": "hit" if replay is not None else "miss"})
        # The three D20 replay branches: an exact replay answers from the
        # committed receipt; replay-only without one is unconfirmed; a miss
        # falls through to fresh dispatch below.
        if replay is not None:
            stdout.append(json.dumps(response, indent=2, ensure_ascii=False) + "\n")
            return _finish(attempt, 0, "ok", {"replayed": True},
                           stdout=stdout, stderr=stderr, response=response)
        if replay_only:
            # A persisted UI confirmation is only untrusted settings JSON until
            # Core proves that this exact approved intent is present in the
            # idempotency ledger with a valid Receipt V2.  This probe must never
            # turn a forged or corrupt confirmation into a new canonical write.
            response = _v2_response(
                envelope,
                ok=False,
                error=_gateway_error(
                    UNCONFIRMED,
                    "no committed receipt exists for this exact request",
                ),
            )
            _validate_capability_envelope(root, response, kind="result")
            stdout.append(json.dumps(response, indent=2, ensure_ascii=False) + "\n")
            return _finish(attempt, 2, "error", {"stage": "core.replay"},
                           stdout=stdout, stderr=stderr, response=response)
        failure: BaseException | None = None
        try:
            # One lock spans the approved-state comparison and the handler.
            # Named handlers reuse this lock, so their historical in-lock
            # preflight remains safe without taking the same digest twice.
            with _operator_lock(root):
                actual_snapshot = f"sha256:{canonical_fingerprint(root)}"
                if envelope["expected_snapshot"] != actual_snapshot:
                    response = _v2_response(
                        envelope,
                        ok=False,
                        error=_gateway_error(
                            STALE_SNAPSHOT,
                            "canonical state changed since this request was approved",
                            retryable=True,
                            details={
                                "expected": envelope["expected_snapshot"],
                                "actual": actual_snapshot,
                            },
                        ),
                    )
                    _validate_capability_envelope(root, response, kind="result")
                    stdout.append(json.dumps(response, indent=2, ensure_ascii=False) + "\n")
                    return _finish(
                        attempt, 3, "error", {"stage": "core.snapshot_guard"},
                        stdout=stdout, stderr=stderr, response=response)
                attempt.event(diag_conventions.EVENT_SNAPSHOT_GUARD_PASSED)
                with gateway_request_context(context), verified_gateway_snapshot(
                    root, actual_snapshot
                ):
                    if envelope["capability"] in REGISTRY:
                        code, result = _registered_compute(
                            root, envelope["capability"], envelope, payload,
                            context=context, parser_factory=parser_factory,
                            definitions=definitions)
                    else:
                        code, result = _dispatch(
                            root,
                            definitions[requested],
                            envelope,
                            payload,
                            parser_factory=parser_factory,
                        )
        except WriteRefused as exc:
            code, result = 2, {"error": str(exc)}
            failure = exc
        except TransactionSnapshotConflict as exc:
            response = _v2_response(
                envelope,
                ok=False,
                error=_gateway_error(
                    STALE_SNAPSHOT,
                    "canonical state changed before the transaction write window",
                    retryable=True,
                    details={"expected": exc.expected, "actual": exc.actual},
                ),
            )
            _validate_capability_envelope(root, response, kind="result")
            stdout.append(json.dumps(response, indent=2, ensure_ascii=False) + "\n")
            return _finish(
                attempt, 3, "error", {"stage": "core.snapshot_guard"},
                stdout=stdout, stderr=stderr, response=response)
        except ProjectionFailure as exc:
            response = _v2_response(
                envelope,
                ok=False,
                error=_projection_error(exc),
            )
            _validate_capability_envelope(root, response, kind="result")
            stdout.append(json.dumps(response, indent=2, ensure_ascii=False) + "\n")
            return _finish(
                attempt, 2, "error", {"stage": "core.projection"},
                stdout=stdout, stderr=stderr, response=response)
        except PostCommitFailure as exc:
            response = _v2_response(
                envelope,
                ok=False,
                transaction_id=exc.transaction_id,
                receipt_path=exc.receipt_path,
                snapshot_after=exc.snapshot_after,
                error=_post_commit_error(exc),
            )
            _validate_capability_envelope(root, response, kind="result")
            stdout.append(json.dumps(response, indent=2, ensure_ascii=False) + "\n")
            return _finish(
                attempt, 2, "error", {"stage": "core.commit"},
                stdout=stdout, stderr=stderr, response=response)
        except TransactionRecoveryConflict as exc:
            # Defense in depth: the replay section's lock acquisition above
            # normally reconciles (and catches this) first, since the lock
            # is re-entrant. If that flow ever changes, a conflict reaching
            # the dispatch section must still refuse ambiguously — never
            # fall through to the definitive INVALID_REQUEST below.
            response = _v2_response(
                envelope,
                ok=False,
                error=_gateway_error(
                    INTERNAL_FAILURE, str(exc), retryable=False,
                    details={
                        "transaction_id": exc.transaction_id,
                        "conflicting_paths": [
                            entry.get("path") for entry in exc.conflicts
                        ],
                        "reasons": sorted({
                            entry.get("reason") for entry in exc.conflicts
                            if entry.get("reason")
                        }),
                    },
                ),
            )
            _validate_capability_envelope(root, response, kind="result")
            stdout.append(json.dumps(response, indent=2, ensure_ascii=False) + "\n")
            return _finish(attempt, 2, "error", {"code": INTERNAL_FAILURE},
                           stdout=stdout, stderr=stderr, response=response)
        except TransactionFailure as exc:
            code, result = 2, {"error": str(exc)}
            failure = exc
        except ValueError as exc:
            code, result = 2, {"error": str(exc)}
            failure = exc
        except Exception as exc:  # fail closed behind a typed V2 boundary
            response = _v2_response(
                envelope,
                ok=False,
                error=_gateway_error(
                    INTERNAL_FAILURE, str(exc) or type(exc).__name__, retryable=True,
                ),
            )
            _validate_capability_envelope(root, response, kind="result")
            stdout.append(json.dumps(response, indent=2, ensure_ascii=False) + "\n")
            # The precise stage is already on record: the transaction span
            # names the boundary that broke; this close carries the outcome.
            return _finish(attempt, 2, "error", {"code": INTERNAL_FAILURE},
                           stdout=stdout, stderr=stderr, response=response,
                           commit="unknown")
        confirmation = result if code == 0 else {}
        complaint = str(result.get("error") or f"{requested} failed")
        carried = result.get("error_code")
        refusal = (carried, bool(result.get("error_retryable"))) \
            if isinstance(carried, str) else None
        error = None if code == 0 else _classify_failure(
            code, complaint, failure=failure, refusal=refusal)
        response = _v2_response(
            envelope,
            ok=code == 0,
            replayed=bool(confirmation.get("replayed", False)),
            transaction_id=confirmation.get("transaction_id"),
            receipt_path=confirmation.get("receipt_path"),
            snapshot_after=confirmation.get("snapshot_after"),
            result=result if code == 0 else {},
            error=error,
        )
        _validate_capability_envelope(root, response, kind="result")
        stdout.append(json.dumps(response, indent=2, ensure_ascii=False) + "\n")
        # A carried (INTERNAL_FAILURE, True) pair is exactly the
        # TransactionRollbackIncomplete refusal row: no WriteRefused carries
        # it, and it is the row's only producer. The commit outcome is
        # genuinely unknown there.
        carried_unknown = refusal == (INTERNAL_FAILURE, True)
        return _finish(
            attempt, _v2_exit_code(code, error),
            "ok" if code == 0 else "error",
            {"replayed": bool(confirmation.get("replayed", False))} if code == 0 else {},
            stdout=stdout, stderr=stderr, response=response,
            commit="unknown" if carried_unknown else None)
    return None
