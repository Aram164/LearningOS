"""The capability envelope gateway — the machine-facing write surface (ADR-006)."""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
import re
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

from learning_os.contracts.capability_catalog import command_definitions
from learning_os.contracts.gateway import (
    GatewayRequestContext,
    gateway_request_context,
    intent_sha256,
)
from learning_os.fingerprint import canonical_fingerprint
from learning_os.transactions import (
    ReplayEvidenceError,
    TransactionFailure,
    TransactionIdempotencyConflict,
    TransactionResult,
    replay_for_request,
)

from .support import (
    WriteRefused,
    _atomic_text,
    _load_session_paths,
    _operator_lock,
    _read_structured_file,
    _root,
    _session_ledger,
    _session_path_state,
)

_CONTENT_BOUND_V2 = frozenset({
    "legacy.archive.lock.publish",
    "masters-planning.catalog.update",
    "masters-planning.comparison.publish",
    "unit.material-synthesis.publish",
})

# Older human-facing commands intentionally keep path forms for shell use and
# no-write preflights. A V2 approval must additionally name the digest of every
# external file. Each named handler uses the shared single-read helper and
# parses or writes the same byte string that helper verified; reopening the
# pathname after hashing is forbidden.
_FILE_INPUTS_V2: dict[str, tuple[tuple[str, str, bool], ...]] = {
    "capture.create": (("file", "file_sha256", False),),
    "module.plan.import": (("file", "file_sha256", False),),
    "note.revise": (("file", "file_sha256", False),),
    "path.attachment.add": (("file", "file_sha256", False),),
    "project.create": (("file", "file_sha256", False),),
    "project.update": (("file", "file_sha256", False),),
    "review.prepare": (("items_file", "items_file_sha256", False),),
    "stage.attachment.add": (("file", "file_sha256", False),),
    "unit.map.import": (("file", "file_sha256", False),),
    "unit.note.append": (("attachment", "attachment_sha256", True),),
}


def _payload_schema_path(root: Path, name: str) -> Path:
    return root / "system" / "schema" / "capabilities" / f"{name}.schema.json"


def _validate_payload(root: Path, name: str, payload: dict) -> None:
    """Refuse a payload the capability never declared.

    A missing schema is itself a refusal: an undeclared payload surface means
    the capability is not actually specified, and guessing would let the
    gateway accept fields no contract describes.
    """
    path = _payload_schema_path(root, name)
    if not path.is_file():
        raise WriteRefused(f"no declared payload schema for capability {name}")
    schema = json.loads(path.read_text(encoding="utf-8"))
    errors = sorted(Draft202012Validator(schema).iter_errors(payload),
                    key=lambda error: list(error.path))
    if errors:
        detail = "; ".join(f"{'/'.join(str(p) for p in e.path) or '<payload>'}: {e.message}"
                           for e in errors[:4])
        raise WriteRefused(f"invalid payload for {name}: {detail}")


def _dispatch(root: Path, definition, envelope: dict, payload: dict) -> tuple[int, dict]:
    """Run one capability through the same handler its named CLI command uses.

    There is deliberately no second implementation here. The envelope is
    translated into the arguments the command already accepts, so the two
    interfaces cannot diverge in behaviour — only in how they are called.
    """
    import los  # local: los imports this module, so the cycle must stay lazy
    from learning_os.contracts.payloads import payload_to_namespace, subparsers

    if envelope.get("schema_version") == 2 and "approve" in payload:
        raise WriteRefused(
            "GatewayEnvelopeV2 approval belongs only in the envelope, not its payload"
        )
    if envelope.get("schema_version") == 2 \
            and definition.name in _CONTENT_BOUND_V2 \
            and "file" in payload:
        raise WriteRefused(
            f"GatewayEnvelopeV2 {definition.name} requires an inline record so "
            "approval is bound to the exact content"
        )
    _validate_payload(root, definition.name, payload)
    commands = subparsers(los.build_parser())
    command_parser = commands.get(definition.cli_command or "")
    if command_parser is None:
        raise WriteRefused(f"capability {definition.name} declares no CLI command to dispatch to")
    handler = command_parser.get_default("func")
    if handler is None:
        raise WriteRefused(f"capability {definition.name} has no bound handler")

    namespace = payload_to_namespace(
        command_parser, payload,
        root=str(root),
        expected_snapshot=envelope.get("expected_snapshot"),
        expected_revisions=envelope.get("expected_revisions", {}),
    )
    # A validated V2 envelope has already bound an approved user gesture to
    # the exact intent hash.  Requiring an unrelated payload boolean would
    # create two approval authorities that can disagree.  V1 keeps its legacy
    # payload flag; direct CLI commands still use ``--approve`` themselves.
    if envelope.get("schema_version") == 2 and hasattr(namespace, "approve"):
        namespace.approve = True
    # Handlers that can report either prose or JSON must report JSON here.
    if hasattr(namespace, "json"):
        namespace.json = True

    captured, errors = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(captured), contextlib.redirect_stderr(errors):
        code = handler(namespace)

    text, complaint = captured.getvalue().strip(), errors.getvalue().strip()
    if code:
        return code, {"error": complaint or text or f"{definition.name} failed"}
    if not text:
        raise WriteRefused(
            f"{definition.name} reported success without a JSON result"
        )
    try:
        result = json.loads(text)
    except json.JSONDecodeError as exc:
        raise WriteRefused(
            f"{definition.name} reported success with non-JSON output"
        ) from exc
    if not isinstance(result, dict):
        raise WriteRefused(
            f"{definition.name} reported success with a non-object JSON result"
        )
    return 0, result


def _validate_capability_envelope(root: Path, envelope: dict, *, kind: str) -> None:
    schema = json.loads((root / "system/schema/capability-envelope.schema.json").read_text(encoding="utf-8"))
    try:
        schema["$defs"][kind]
    except KeyError as exc:  # pragma: no cover - a repository contract defect
        raise WriteRefused(f"capability envelope schema has no {kind} definition") from exc
    directional_schema = {
        "$schema": schema.get("$schema", "https://json-schema.org/draft/2020-12/schema"),
        "$defs": schema["$defs"],
        "$ref": f"#/$defs/{kind}",
    }
    errors = sorted(
        Draft202012Validator(directional_schema).iter_errors(envelope),
        key=lambda error: list(error.path),
    )
    if errors:
        raise WriteRefused("invalid capability envelope: " + "; ".join(error.message for error in errors[:4]))


def _gateway_error(code: str, message: str, *, retryable: bool = False,
                   details: dict | None = None) -> dict:
    return {
        "code": code,
        "message": message,
        "retryable": retryable,
        "details": dict(details or {}),
    }


def _classify_failure(code: int, message: str) -> dict:
    lowered = message.lower()
    # TransactionService normally rolls every authored byte back before a
    # refusal reaches this boundary.  When it explicitly reports an incomplete
    # rollback, however, the repository may contain part of the attempted
    # write.  Never let a more specific word later in the message (validation,
    # projection, approval, …) turn that unknown outcome into a typed
    # "nothing committed" refusal: recovery must keep the original request and
    # reconcile it under the same idempotency key.
    if "rollback incomplete" in lowered:
        return _gateway_error("INTERNAL_FAILURE", message, retryable=True)
    if "belongs only in the envelope" in lowered \
            or "requires an inline record" in lowered \
            or "changed before use" in lowered \
            or "unbound stdin" in lowered \
            or "requires a sha-256 bound" in lowered:
        return _gateway_error("INVALID_REQUEST", message)
    if "snapshot" in lowered or "projection conflict" in lowered:
        return _gateway_error("STALE_SNAPSHOT", message, retryable=True)
    if code == 3 or "revision conflict" in lowered:
        return _gateway_error("REVISION_CONFLICT", message, retryable=True)
    if any(token in lowered for token in (
        "write scope", "may not write", "unknown write authority", "symlink",
        "escapes repository", "out of scope",
    )):
        return _gateway_error("OUT_OF_SCOPE", message)
    if "idempotency" in lowered:
        return _gateway_error("IDEMPOTENCY_CONFLICT", message)
    if "ambiguous" in lowered:
        return _gateway_error("AMBIGUOUS_MIGRATION", message)
    if "canonical validation" in lowered or "validation failed" in lowered:
        return _gateway_error("VALIDATION_FAILED", message)
    if "projection" in lowered or "publication" in lowered:
        return _gateway_error("PROJECTION_FAILED", message, retryable=True)
    if any(token in lowered for token in ("approval", "approve", "confirm")):
        return _gateway_error("UNCONFIRMED", message)
    return _gateway_error("INVALID_REQUEST", message)


def _context_from_v2(envelope: dict) -> GatewayRequestContext:
    subject_hash = intent_sha256(envelope)
    approval = envelope["approval"]
    if approval["subject_sha256"] != subject_hash:
        raise WriteRefused(
            "approval subject does not match the current capability intent"
        )
    return GatewayRequestContext(
        request_id=envelope["request_id"],
        idempotency_key=envelope["idempotency_key"],
        capability=envelope["capability"],
        channel=envelope["channel"],
        intent_sha256=subject_hash,
        approval_kind=approval["kind"],
        approval_subject_sha256=approval["subject_sha256"],
    )


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


class _ReplayRecoveryError(Exception):
    """The committed receipt cannot prove what the original call wrote."""


def _replayed_domain_result(root: Path, capability: str,
                            replay: TransactionResult) -> dict:
    """Recover the original domain path from the already-validated receipt.

    ``replay.receipt`` has already been schema-validated and cross-bound to
    this exact request by ``replay_for_request`` — its capability, status, and
    transaction id are trustworthy. This checks only the domain-specific shape
    every capture-like capability's receipt must have: exactly one created
    write inside the capability's own directory. Rereading or re-verifying the
    generic fields here would be the "weaker helper" the recovery design
    forbids.
    """
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
                                       replay: TransactionResult) -> None:
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
    if not _session_ledger(root).is_file():
        raise _ReplayRecoveryError(
            "cannot repair session ownership: the session ledger is gone, and this "
            "receipt cannot prove the bytes of the shared revision and idempotency "
            "ledgers — reconcile this transaction by hand"
        )
    try:
        existing = _load_session_paths(root)
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
        if _session_path_state(root, relative) != state:
            raise _ReplayRecoveryError(
                "cannot repair session ownership: "
                f"{relative} changed since its recorded transaction"
            )

    merged = dict(existing)
    merged.update(authored)
    try:
        _atomic_text(_session_ledger(root), json.dumps({
            "schema_version": 1,
            "paths": dict(sorted(merged.items())),
        }, indent=2, sort_keys=True) + "\n")
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
        **_replayed_domain_result(root, str(envelope.get("capability")), replay),
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


def cmd_capability(args) -> int:
    root = _root(args)
    definitions = command_definitions(root)
    # Preserve the legacy no-I/O refusal for an unknown name when there is no
    # envelope to classify. If a real V2 envelope exists, read it so the same
    # unknown name receives the required typed GatewayResultV2 error.
    if args.name not in definitions and args.payload_file != "-" \
            and not Path(args.payload_file).expanduser().is_file():
        print(f"los: unknown or non-public capability: {args.name}", file=sys.stderr)
        return 2
    envelope = _read_structured_file(args.payload_file)
    is_v2 = envelope.get("schema_version") == 2
    try:
        _validate_capability_envelope(root, envelope, kind="request")
    except WriteRefused as exc:
        if not is_v2:
            raise
        response = _v2_response(
            envelope,
            ok=False,
            error=_gateway_error("INVALID_REQUEST", str(exc)),
        )
        _validate_capability_envelope(root, response, kind="result")
        print(json.dumps(response, indent=2, ensure_ascii=False))
        return 2
    if envelope.get("capability") != args.name:
        if is_v2:
            response = _v2_response(
                envelope,
                ok=False,
                error=_gateway_error(
                    "INVALID_REQUEST",
                    "envelope capability does not match requested capability",
                ),
            )
            _validate_capability_envelope(root, response, kind="result")
            print(json.dumps(response, indent=2, ensure_ascii=False))
            return 2
        print("los: envelope capability does not match requested capability", file=sys.stderr)
        return 2
    # ``command_definitions`` is the public allowlist.  V2 always gets a typed
    # response, including when the requested name has no declaration.
    if args.name not in definitions:
        if is_v2:
            response = _v2_response(
                envelope,
                ok=False,
                error=_gateway_error(
                    "UNKNOWN_CAPABILITY",
                    f"unknown or non-public capability: {args.name}",
                ),
            )
            _validate_capability_envelope(root, response, kind="result")
            print(json.dumps(response, indent=2, ensure_ascii=False))
            return 2
        print(f"los: unknown or non-public capability: {args.name}", file=sys.stderr)
        return 2
    payload = envelope.get("payload", {})
    request_id = envelope["request_id"]
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
                error=_gateway_error("UNCONFIRMED", str(exc)),
            )
            _validate_capability_envelope(root, response, kind="result")
            print(json.dumps(response, indent=2, ensure_ascii=False))
            return 2
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
                    _repair_replayed_session_ownership(root, replay)
        except TransactionIdempotencyConflict as exc:
            response = _v2_response(
                envelope,
                ok=False,
                error=_gateway_error("IDEMPOTENCY_CONFLICT", str(exc)),
            )
            _validate_capability_envelope(root, response, kind="result")
            print(json.dumps(response, indent=2, ensure_ascii=False))
            return 2
        except (ReplayEvidenceError, _ReplayRecoveryError) as exc:
            # Fail closed. Evidence is contradictory or the original write
            # already happened; rerunning the handler here would risk
            # duplicating it, and answering with a guessed path would be a lie
            # about canonical state. Never retryable: the fix is manual
            # reconciliation, not a client resend.
            response = _v2_response(
                envelope,
                ok=False,
                error=_gateway_error("INTERNAL_FAILURE", str(exc), retryable=False),
            )
            _validate_capability_envelope(root, response, kind="result")
            print(json.dumps(response, indent=2, ensure_ascii=False))
            return 2
        except TransactionFailure as exc:
            response = _v2_response(
                envelope,
                ok=False,
                error=_gateway_error("INTERNAL_FAILURE", str(exc), retryable=True),
            )
            _validate_capability_envelope(root, response, kind="result")
            print(json.dumps(response, indent=2, ensure_ascii=False))
            return 2
        if replay is not None:
            print(json.dumps(response, indent=2, ensure_ascii=False))
            return 0
        if args.replay_only:
            # A persisted UI confirmation is only untrusted settings JSON until
            # Core proves that this exact approved intent is present in the
            # idempotency ledger with a valid Receipt V2.  This probe must never
            # turn a forged or corrupt confirmation into a new canonical write.
            response = _v2_response(
                envelope,
                ok=False,
                error=_gateway_error(
                    "UNCONFIRMED",
                    "no committed receipt exists for this exact request",
                ),
            )
            _validate_capability_envelope(root, response, kind="result")
            print(json.dumps(response, indent=2, ensure_ascii=False))
            return 2
        actual_snapshot = f"sha256:{canonical_fingerprint(root)}"
        if envelope["expected_snapshot"] != actual_snapshot:
            response = _v2_response(
                envelope,
                ok=False,
                error=_gateway_error(
                    "STALE_SNAPSHOT",
                    "canonical state changed since this request was approved",
                    retryable=True,
                    details={
                        "expected": envelope["expected_snapshot"],
                        "actual": actual_snapshot,
                    },
                ),
            )
            _validate_capability_envelope(root, response, kind="result")
            print(json.dumps(response, indent=2, ensure_ascii=False))
            return 3
        try:
            with gateway_request_context(context):
                code, result = _dispatch(
                    root, definitions[args.name], envelope, payload
                )
        except WriteRefused as exc:
            code, result = 2, {"error": str(exc)}
        except TransactionFailure as exc:
            code, result = 2, {"error": str(exc)}
        except ValueError as exc:
            code, result = 2, {"error": str(exc)}
        except Exception as exc:  # fail closed behind a typed V2 boundary
            response = _v2_response(
                envelope,
                ok=False,
                error=_gateway_error(
                    "INTERNAL_FAILURE", str(exc) or type(exc).__name__, retryable=True,
                ),
            )
            _validate_capability_envelope(root, response, kind="result")
            print(json.dumps(response, indent=2, ensure_ascii=False))
            return 2
        confirmation = result if code == 0 else {}
        complaint = str(result.get("error") or f"{args.name} failed")
        response = _v2_response(
            envelope,
            ok=code == 0,
            replayed=bool(confirmation.get("replayed", False)),
            transaction_id=confirmation.get("transaction_id"),
            receipt_path=confirmation.get("receipt_path"),
            snapshot_after=confirmation.get("snapshot_after"),
            result=result if code == 0 else {},
            error=None if code == 0 else _classify_failure(code, complaint),
        )
        _validate_capability_envelope(root, response, kind="result")
        print(json.dumps(response, indent=2, ensure_ascii=False))
        return code

    try:
        code, result = _dispatch(root, definitions[args.name], envelope, payload)
    except WriteRefused as exc:
        code, result = 2, {"error": str(exc)}
    # The handler folds its own receipt facts into `result`, so the response
    # reads them from there rather than re-deriving them.
    confirmation = result if code == 0 else {}
    response = {
        "request_id": request_id,
        "capability": args.name,
        "ok": code == 0,
        "transaction_id": confirmation.get("transaction_id"),
        "receipt_path": confirmation.get("receipt_path"),
        "result": result if code == 0 else {},
        "error": None if code == 0 else result.get("error", "capability failed"),
    }
    _validate_capability_envelope(root, response, kind="result")
    print(json.dumps(response, indent=2, ensure_ascii=False))
    return code
