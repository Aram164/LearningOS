"""Legacy gateway dispatch, split for shared admission (SPEC 11.2 K1).

_dispatch moved verbatim from commands.capability, split into the shared
prepare_dispatch admission step plus its legacy remainder.
"""

from __future__ import annotations

import contextlib
import io
import json
from pathlib import Path

from jsonschema import Draft202012Validator

from learning_os.contracts.gateway import GatewayRequestContext, intent_sha256
from learning_os.diagnostics import conventions as diag_conventions
from learning_os.diagnostics import tracer as diag_tracer
from learning_os.domain.failures import WriteRefused
from learning_os.ops.outcomes import _take_gateway_refusal

_CONTENT_BOUND_V2 = frozenset({
    "legacy.archive.lock.publish",
    "masters-planning.catalog.update",
    "masters-planning.comparison.publish",
    "collection.entry.revise",
    "source.intake.record",
    "source.record.revise",
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
    # Her explicit decision on a proposed goal: one ledger map write,
    # batch-bound by the exact `--check` review, terminal-approved (D8).
    "goal.decision.record",
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


def prepare_dispatch(
    root: Path,
    definition,
    envelope: dict,
    payload: dict,
    *,
    parser_factory,
):
    """Shared gateway admission for legacy and registered dispatch (SPEC 11.2 K1).

    Refuses misplaced approval and content-bound file payloads, validates
    the payload, resolves the subparser and handler, and builds the
    namespace with parser defaults and the envelope guards. Returns
    (command_parser, namespace).
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
    return command_parser, namespace


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
    command_parser, namespace = prepare_dispatch(
        root, definition, envelope, payload, parser_factory=parser_factory)
    handler = command_parser.get_default("func")
    # A catching handler step records its typed refusal beside its non-zero
    # return; take it here so the V2 error carries the type, not a guess
    # from the prose. Cleared first so no earlier in-process failure leaks
    # into this dispatch, and cleared on success so a refusal can never
    # ride along with a later result.
    _take_gateway_refusal()
    captured, errors = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(captured), contextlib.redirect_stderr(errors):
        code = handler(namespace)
    diag_tracer.emit_event(
        diag_conventions.EVENT_HANDLER_COMPLETED,
        status="ok" if code == 0 else "error",
        attrs={"capability": definition.name, "exit_code": code})

    text, complaint = captured.getvalue().strip(), errors.getvalue().strip()
    if code:
        result = {"error": complaint or text or f"{definition.name} failed"}
        refusal = _take_gateway_refusal()
        if refusal is not None:
            result["error_code"], result["error_retryable"] = refusal
        return code, result
    _take_gateway_refusal()
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
    if kind == "request" and envelope.get("schema_version") != 2:
        # Before dispatch, and before the schema's oneOf can misread the
        # shape: an envelope without `schema_version: 2` used to travel all
        # the way to the handler, which answered with a circular pointer.
        # The general sealing recipe is WORKFLOWS §25c.
        raise WriteRefused(
            "invalid capability envelope: schema_version 2 required "
            "(WORKFLOWS §25c)"
        )
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


def _context_from_v2(envelope: dict) -> GatewayRequestContext:
    subject_hash = intent_sha256(envelope)
    approval = envelope["approval"]
    if approval["subject_sha256"] != subject_hash:
        raise WriteRefused(
            "approval subject does not match the current capability intent"
        )
    raw_session = envelope.get("session_id")
    sealed_session = raw_session.strip() if isinstance(raw_session, str) else None
    return GatewayRequestContext(
        request_id=envelope["request_id"],
        idempotency_key=envelope["idempotency_key"],
        capability=envelope["capability"],
        channel=envelope["channel"],
        intent_sha256=subject_hash,
        approval_kind=approval["kind"],
        approval_subject_sha256=approval["subject_sha256"],
        expected_snapshot=envelope["expected_snapshot"],
        session_id=sealed_session or None,
    )
