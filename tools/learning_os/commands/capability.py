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
    verified_gateway_snapshot,
)
from learning_os.diagnostics import conventions as diag_conventions
from learning_os.diagnostics import tracer as diag_tracer
from learning_os.diagnostics.context import record_debug, trace_context_from_env
from learning_os.diagnostics.store import bind_store as _bind_diag_store
from learning_os.fingerprint import canonical_fingerprint
from learning_os.transactions import (
    PostCommitFailure,
    ProjectionFailure,
    ReplayEvidenceError,
    TransactionFailure,
    TransactionIdempotencyConflict,
    TransactionRecoveryConflict,
    TransactionResult,
    TransactionSnapshotConflict,
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
    "source.intake.record",
    "unit.material-synthesis.publish",
    "unit.plan.revise",
})

#: Capabilities admitted to ``direct-user-gesture`` approval from any channel.
#:
#: The gesture kind means "the user herself acted", so the test is what the
#: write *is*, not which process sent it: admitted exactly when the record
#: being written is the learner's own study activity or her own choice among
#: material someone already authored — her progress, her prose, her files,
#: her experience of a resource, her questions, her selections — bounded to
#: one unit, stage or workspace and guarded by exact artifact revisions.
#:
#: Canonical semantics, plan structure and content are not on this list. Some
#: of them are admitted through ``UI_REVIEWED_ALLOWLIST`` below, which is a
#: narrower thing: the same approval kind, restricted to the ``ui`` channel,
#: for the workflows where the application shows the exact change before an
#: explicit Save or Apply. Everything else — every agent-origin semantic
#: write — keeps the approved operator/delivery path.
#:
#: Until 2026-09-13 this list held only the three writers that happened to
#: exist when it was introduced, and its comment described `capture.create`
#: and `garden.seed.create` as "the pre-existing UI-originated writers" —
#: which was never true. The installed UI drove eleven more write paths
#: through the same gesture, and Core refused four ordinary study actions in
#: the learner's face (audit `synthetic-learner-2026-09-12`, F01). The
#: policy above is the one this list now implements; the mirror in
#: ``system/contracts/capabilities.yaml`` (``admission:``) is pinned to it by
#: ``tests/test_observation_gesture.py``, and the UI's own producer-side copy
#: is pinned by its ``scripts/check-contract.mjs``.
GESTURE_ALLOWLIST = frozenset({
    # Aram's own evidence: append-only ledger, tested ``--supersedes``
    # correction path, one JSONL line of blast radius, and a local
    # `los observe` command where the terminal session is the approval.
    "learner.observation.append",
    # Unrouted, unclassified inbox and Garden input; the handler names the
    # file, so both guard the request rather than an artifact.
    "capture.create",
    "garden.seed.create",
    # Her own study record for one stage or unit.
    "stage.progress.update",
    "unit.note.append",
    "stage.attachment.add",
    "detour.create",
    "detour.resolve",
    # Her own contextual experience of a resource. The source record's own
    # identity and evaluations are untouched — that judgment stays canonical
    # and stays off this list.
    "source.feedback.record",
    # Her own question, and its open/resolved state (ADR-017). Wording and
    # target are preserved by the handler; this never describes mastery.
    "atlas.question.save",
    # Her choice among the routes the module map already offers. The complete
    # material menu is authored content and is unchanged by a selection.
    "unit.source-selection.set",
})

#: Canonical changes this application may authorize, and only this application.
#:
#: ADR-017 designed the Atlas for Aram to author concept connections by hand,
#: without an AI provider, an external editor, or handwritten YAML. Refusing
#: that legibly is still refusing it, and a readable refusal does not satisfy
#: a current, binding architecture decision (review
#: `workbench/audits/repair-review-2026-09-13`, D1). The same reasoning covers
#: the rest: shelving *preparation* applies nothing at all, while shelving
#: *application*, a study-map import, and the two append-only ability records
#: (a confirmed claim and a tentative connection, added 2026-09-23) each show
#: the exact change first and then wait for a deliberate control.
#:
#: **A deliberate Save or Apply on an exact visible preview is the review.**
#: That is what these contracts already meant by explicit approval; the review
#: was happening on screen and the envelope had no way to say so. There is no
#: second approval protocol here, no extra confirmation dialog, and no
#: relabelling of a click as operator approval — the same V2 envelope, the same
#: guards, the same receipt.
#:
#: The restriction to ``channel == "ui"`` is what keeps this from widening
#: agent authority: a codex- or system-task-origin envelope claiming a gesture
#: for these still fails closed. The channel label is provenance inside this
#: trusted local application, not cryptographic proof that a human was present,
#: and it is not treated as more than that. Every guard these capabilities
#: already carry — exact previous rows, registry and artifact revisions, the
#: snapshot, duplicate/endpoint/cycle checks, exact-byte binding of reviewed
#: files, the import preflight — is unchanged, and that is what actually
#: protects canonical state.
UI_REVIEWED_ALLOWLIST = frozenset({
    # Connections Aram authored, applied from the exact-row preview (ADR-017).
    "concept.relations.change",
    # Preparing a shelving packet proposes; it applies nothing.
    "review.prepare",
    # Applying the selected items, after their proposed changes were shown.
    "review.apply",
    # A reviewed map file, after its no-write `--check` preflight.
    "unit.map.import",
    # Aram's own ability claim, recorded from Review only after the exact
    # record — claim, result, assistance, conditions, criteria, work pointer —
    # is on screen, with "Confirm & record" as the deliberate control. Its
    # confirmation pointer names that app request, so the receipt is the
    # confirmation. Append-only: corrections supersede, never rewrite, and the
    # reviewed ability identity is still bound by its claim, conditions, and criteria hash.
    # Admitted over `ui` only (Aram, 2026-09-23): an agent that records a
    # claim Aram confirmed in conversation keeps the operator path.
    "learner.ability-observation.append",
    # A tentative connection Aram noticed, recorded from the same exact
    # preview. It carries no evidence and never changes a reviewed bridge,
    # readiness or transfer; promotion to a bridge stays an operator review.
    "ability.candidate.append",
})

#: Channels a reviewed-UI admission accepts. One entry, deliberately.
UI_REVIEWED_CHANNELS = frozenset({"ui"})

#: Why a gesture is not enough, per capability, for the write paths an
#: interface can legitimately reach from a human click. Core answers with this
#: instead of naming the approval kind: "direct-user-gesture is not admitted
#: for X" is true, and tells a learner nothing she can act on.
GESTURE_REFUSAL_RECOVERY: dict[str, str] = {
    "module.plan.import": (
        "a module plan is applied from a reviewed file after its required "
        "preflight, through an operator request (WORKFLOWS §25a)"
    ),
    "route.patch": (
        "material details change through the reviewed `route-patch --check` "
        "preflight and an operator request (WORKFLOWS §25a)"
    ),
    "note.revise": (
        "revising a note body is a semantic edit: it needs an explicit "
        "request and a reviewable diff, not a gesture"
    ),
    "stage.note.write": (
        "this is a retired compatibility surface; save the note against the "
        "unit with unit.note.append instead"
    ),
}


def gesture_allowed(capability: str, channel: str | None = None) -> bool:
    """Whether a capability admits ``direct-user-gesture`` from this channel.

    ``channel`` is optional so a focused caller that already knows the request
    is user-originated (``los observe``) need not restate it; a reviewed-UI
    capability, however, is admitted only when the channel is actually named.
    """
    if capability in GESTURE_ALLOWLIST:
        return True
    return (capability in UI_REVIEWED_ALLOWLIST
            and channel in UI_REVIEWED_CHANNELS)


def gesture_refusal(capability: str, channel: str | None = None) -> str:
    """Explain a gesture refusal in terms of what to do instead."""
    if capability in UI_REVIEWED_ALLOWLIST:
        # Not "this needs approval" — it has one, from the wrong producer.
        return (
            f"{capability} is authorized by a reviewed action in the "
            f"LearningOS app, not by a {channel or 'remote'}-channel request: "
            f"apply it from the screen that shows the exact change, or send it "
            f"through the approved operator path"
        )
    recovery = GESTURE_REFUSAL_RECOVERY.get(capability)
    if recovery:
        return (
            f"{capability} cannot be authorized by a direct user gesture: "
            f"{recovery}"
        )
    return (
        f"{capability} cannot be authorized by a direct user gesture: it "
        f"writes canonical content, which needs an approved operator request "
        f"rather than a click"
    )

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


def _dispatch(
    root: Path,
    definition,
    envelope: dict,
    payload: dict,
    *,
    parser_factory,
) -> tuple[int, dict]:
    """Run one capability through the same handler its named CLI command uses.

    There is deliberately no second implementation here. The envelope is
    translated into the arguments the command already accepts, so the two
    interfaces cannot diverge in behaviour — only in how they are called.
    """
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
    commands = subparsers(parser_factory())
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
    diag_tracer.emit_event(
        diag_conventions.EVENT_HANDLER_COMPLETED,
        status="ok" if code == 0 else "error",
        attrs={"capability": definition.name, "exit_code": code})

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


def prepare_review_envelope(capability_name: str, payload: dict,
                            snapshot: str, revisions: dict) -> dict:
    """Prepare a recoverable request during preflight, while its lock is held."""
    import uuid

    envelope = {
        "schema_version": 2,
        "request_id": f"request-reviewed-{uuid.uuid4().hex}",
        "idempotency_key": f"reviewed-{uuid.uuid4().hex}",
        "capability": capability_name,
        "channel": "codex",
        "expected_snapshot": snapshot,
        "expected_revisions": revisions,
        "payload": payload,
        "approval": {"kind": "operator-approval", "subject_sha256": ""},
    }
    envelope["approval"]["subject_sha256"] = intent_sha256(envelope)
    return envelope


def reviewed_envelope_apply(*, root: Path, capability_name: str, payload: dict,
                            reviewed_content: bytes, reviewed_sha256: str,
                            review_report: str | None, parser_factory) -> int:
    """Dispatch the saved preflight request without refreshing its authority.

    The caller parsed exactly reviewed_content. The saved report retains the
    complete envelope, including its identity, for exact retry after a lost
    response. Neither snapshot nor revisions are silently rebased here.
    """
    import argparse as _argparse
    import tempfile as _tempfile

    if parser_factory is None:
        print("los: reviewed apply needs the CLI parser factory", file=sys.stderr)
        return 2
    actual = "sha256:" + hashlib.sha256(reviewed_content).hexdigest()
    if actual != reviewed_sha256:
        print("los: reviewed bytes changed since --check; re-run --check, review "
              "the new report and its SHA, then apply that SHA", file=sys.stderr)
        print(json.dumps({"expected": reviewed_sha256, "actual": actual}),
              file=sys.stderr)
        return 2
    if not review_report:
        print("los: reviewed apply requires --review-report with the saved --check JSON",
              file=sys.stderr)
        return 2
    try:
        report = _read_structured_file(review_report)
        envelope = report.get("gateway_envelope")
        if not isinstance(envelope, dict):
            raise WriteRefused("review report has no prepared gateway envelope")
        _validate_capability_envelope(root, envelope, kind="request")
        _context_from_v2(envelope)
        if report.get("ok") is not True or report.get("mode") != "check" \
                or report.get("reviewed_file_sha256") != actual \
                or envelope.get("capability") != capability_name \
                or envelope.get("payload") != payload \
                or envelope.get("expected_snapshot") != report.get("expected_snapshot") \
                or envelope.get("expected_revisions") != report.get("expected_revisions"):
            raise WriteRefused("review report does not match the exact reviewed input and guards")
    except (OSError, ValueError, WriteRefused) as exc:
        print(f"los: {exc}", file=sys.stderr)
        return 2
    fd, tmp_name = _tempfile.mkstemp(prefix="learningos-reviewed-", suffix=".json")
    try:
        with open(fd, "w", encoding="utf-8") as handle:
            json.dump(envelope, handle, ensure_ascii=False)
        args = _argparse.Namespace(
            root=str(root),
            name=capability_name,
            payload_file=tmp_name,
            replay_only=False,
            _parser_factory=parser_factory,
        )
        return cmd_capability(args)
    finally:
        with contextlib.suppress(OSError):
            Path(tmp_name).unlink()


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


def _classify_failure(code: int, message: str, *,
                      failure: BaseException | None = None) -> dict:
    if getattr(failure, "pre_existing_defect", False):
        # Typed pre-existing-defect case (JF-11): canonical rollback
        # completed but the restored pre-state itself does not publish —
        # the shadow-validation refusal. Recognized by flag, never by
        # message tokens, so defect prose can never trip an earlier
        # classifier token. Same refusal the tokens used to select.
        return _gateway_error("VALIDATION_FAILED", message)
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


def _projection_error(exc: ProjectionFailure) -> dict:
    """Typed projection outcome: subsystem proven, prose not consulted.

    A complete rollback proves the write never committed; an incomplete
    one leaves the outcome unknown however the message reads. A complete
    rollback over a pre-state that itself does not publish is a
    shadow-validation refusal (JF-11), reported like one.
    """
    if exc.rollback_complete:
        if exc.pre_existing_defect:
            return _gateway_error(
                "VALIDATION_FAILED", str(exc), retryable=False,
                details={"stage": "core.projection", "rollback_complete": True,
                         "pre_existing_defect": True})
        return _gateway_error(
            "PROJECTION_FAILED", str(exc), retryable=True,
            details={"stage": "core.projection", "rollback_complete": True})
    return _gateway_error(
        "INTERNAL_FAILURE", str(exc), retryable=True,
        details={"stage": "core.projection", "rollback_complete": False})


def _post_commit_error(exc: PostCommitFailure) -> dict:
    """Committed yet failed: never a definitive refusal."""
    return _gateway_error(
        "INTERNAL_FAILURE", str(exc), retryable=True,
        details={"stage": "core.commit", "committed": True})


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
        expected_snapshot=envelope["expected_snapshot"],
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


class _ReplayRecoveryError(Exception):
    """The committed receipt cannot prove what the original call wrote."""


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


def cmd_capability(args) -> int:
    # Research track #2, Phase 1: observe the UI-propagated trace context.
    # Pure env read plus an opt-in debug record; behavior is identical when
    # tracing is absent, malformed, or its sink fails. Never an input to any
    # guard, hash, receipt, or ledger below.
    record_debug(trace_context_from_env(), operation="capability",
                 extra={"capability": getattr(args, "name", None)})
    root = _root(args)
    # Phase 3A: bind this repository's disposable trace store first, so the
    # attempt span below persists like every later record. Binding is a pure
    # path assignment; persistence itself stays best-effort.
    _bind_diag_store(root)
    # Phase 2A: one attempt span per gateway invocation. All emissions below
    # are sink-gated no-ops by default; every return below closes the span.
    attempt = diag_tracer.begin_attempt(
        {"capability": getattr(args, "name", None)})
    definitions = command_definitions(root)
    # Preserve the legacy no-I/O refusal for an unknown name when there is no
    # envelope to classify. If a real V2 envelope exists, read it so the same
    # unknown name receives the required typed GatewayResultV2 error.
    if args.name not in definitions and args.payload_file != "-" \
            and not Path(args.payload_file).expanduser().is_file():
        print(f"los: unknown or non-public capability: {args.name}", file=sys.stderr)
        return _close_attempt(attempt, 2, "error", {"stage": "core.admission"})
    envelope = _read_structured_file(args.payload_file)
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
            error=_gateway_error("INVALID_REQUEST", str(exc)),
        )
        _validate_capability_envelope(root, response, kind="result")
        print(json.dumps(response, indent=2, ensure_ascii=False))
        return _close_attempt(attempt, 2, "error", {"stage": "core.admission"})
    attempt.event(diag_conventions.EVENT_ENVELOPE_VALIDATED,
                  attrs={"request_id": envelope.get("request_id"),
                         "idempotency_key": envelope.get("idempotency_key")})
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
            return _close_attempt(attempt, 2, "error", {"stage": "core.admission"})
        print("los: envelope capability does not match requested capability", file=sys.stderr)
        return _close_attempt(attempt, 2, "error", {"stage": "core.admission"})
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
            return _close_attempt(attempt, 2, "error", {"stage": "core.admission"})
        print(f"los: unknown or non-public capability: {args.name}", file=sys.stderr)
        return _close_attempt(attempt, 2, "error", {"stage": "core.admission"})
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
            return _close_attempt(attempt, 2, "error", {"stage": "core.approval"})
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
                    "UNCONFIRMED",
                    gesture_refusal(context.capability, context.channel),
                ),
            )
            _validate_capability_envelope(root, response, kind="result")
            print(json.dumps(response, indent=2, ensure_ascii=False))
            return _close_attempt(attempt, 2, "error", {"stage": "core.approval"})
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
                    _repair_replayed_session_ownership(root, replay)
        except TransactionIdempotencyConflict as exc:
            response = _v2_response(
                envelope,
                ok=False,
                error=_gateway_error("IDEMPOTENCY_CONFLICT", str(exc)),
            )
            _validate_capability_envelope(root, response, kind="result")
            print(json.dumps(response, indent=2, ensure_ascii=False))
            attempt.event(diag_conventions.EVENT_REPLAY_CHECKED,
                          status="error", attrs={"outcome": "conflict"})
            return _close_attempt(attempt, 2, "error", {"stage": "core.replay"})
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
            attempt.event(diag_conventions.EVENT_REPLAY_CHECKED,
                          status="error", attrs={"outcome": "evidence-error"})
            return _close_attempt(attempt, 2, "error", {"stage": "core.replay"})
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
                    "INTERNAL_FAILURE", str(exc), retryable=False,
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
            print(json.dumps(response, indent=2, ensure_ascii=False))
            attempt.event(diag_conventions.EVENT_REPLAY_CHECKED,
                          status="error", attrs={"outcome": "recovery-conflict"})
            return _close_attempt(attempt, 2, "error", {"stage": "core.replay"})
        except TransactionFailure as exc:
            response = _v2_response(
                envelope,
                ok=False,
                error=_gateway_error("INTERNAL_FAILURE", str(exc), retryable=True),
            )
            _validate_capability_envelope(root, response, kind="result")
            print(json.dumps(response, indent=2, ensure_ascii=False))
            attempt.event(diag_conventions.EVENT_REPLAY_CHECKED,
                          status="error", attrs={"outcome": "lookup-failed"})
            return _close_attempt(attempt, 2, "error", {"stage": "core.replay"})
        attempt.event(diag_conventions.EVENT_REPLAY_CHECKED,
                      attrs={"outcome": "hit" if replay is not None else "miss"})
        if replay is not None:
            print(json.dumps(response, indent=2, ensure_ascii=False))
            return _close_attempt(attempt, 0, "ok", {"replayed": True})
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
            return _close_attempt(attempt, 2, "error", {"stage": "core.replay"})
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
                    return _close_attempt(
                        attempt, 3, "error", {"stage": "core.snapshot_guard"})
                attempt.event(diag_conventions.EVENT_SNAPSHOT_GUARD_PASSED)
                with gateway_request_context(context), verified_gateway_snapshot(
                    root, actual_snapshot
                ):
                    code, result = _dispatch(
                        root,
                        definitions[args.name],
                        envelope,
                        payload,
                        parser_factory=args._parser_factory,
                    )
        except WriteRefused as exc:
            code, result = 2, {"error": str(exc)}
        except TransactionSnapshotConflict as exc:
            response = _v2_response(
                envelope,
                ok=False,
                error=_gateway_error(
                    "STALE_SNAPSHOT",
                    "canonical state changed before the transaction write window",
                    retryable=True,
                    details={"expected": exc.expected, "actual": exc.actual},
                ),
            )
            _validate_capability_envelope(root, response, kind="result")
            print(json.dumps(response, indent=2, ensure_ascii=False))
            return _close_attempt(
                attempt, 3, "error", {"stage": "core.snapshot_guard"})
        except ProjectionFailure as exc:
            response = _v2_response(
                envelope,
                ok=False,
                error=_projection_error(exc),
            )
            _validate_capability_envelope(root, response, kind="result")
            print(json.dumps(response, indent=2, ensure_ascii=False))
            return _close_attempt(
                attempt, 2, "error", {"stage": "core.projection"})
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
            print(json.dumps(response, indent=2, ensure_ascii=False))
            return _close_attempt(
                attempt, 2, "error", {"stage": "core.commit"})
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
                    "INTERNAL_FAILURE", str(exc), retryable=False,
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
            print(json.dumps(response, indent=2, ensure_ascii=False))
            return _close_attempt(attempt, 2, "error", {"code": "INTERNAL_FAILURE"})
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
                    "INTERNAL_FAILURE", str(exc) or type(exc).__name__, retryable=True,
                ),
            )
            _validate_capability_envelope(root, response, kind="result")
            print(json.dumps(response, indent=2, ensure_ascii=False))
            # The precise stage is already on record: the transaction span
            # names the boundary that broke; this close carries the outcome.
            return _close_attempt(attempt, 2, "error", {"code": "INTERNAL_FAILURE"})
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
            error=None if code == 0 else _classify_failure(
                code, complaint, failure=failure),
        )
        _validate_capability_envelope(root, response, kind="result")
        print(json.dumps(response, indent=2, ensure_ascii=False))
        return _close_attempt(
            attempt, code, "ok" if code == 0 else "error",
            {"replayed": bool(confirmation.get("replayed", False))} if code == 0 else {})

    try:
        code, result = _dispatch(
            root,
            definitions[args.name],
            envelope,
            payload,
            parser_factory=args._parser_factory,
        )
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
    return _close_attempt(attempt, code, "ok" if code == 0 else "error")
