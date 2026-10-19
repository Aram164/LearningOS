"""GatewayEnvelopeV2 admission: envelope and payload validation, approval-bound file inputs, and dispatch of a capability through its command handler."""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
import re
import sys
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

from learning_os.app.outcomes import take_gateway_refusal as _take_gateway_refusal
from learning_os.domain.failures import WriteRefused
from learning_os.store import observations
from learning_os.store.contracts.gateway import (
    GatewayRequestContext,
    current_gateway_request,
    intent_sha256,
)
from learning_os.store.diagnostics import conventions as diag_conventions
from learning_os.store.diagnostics import tracer as diag_tracer
from learning_os.store.session_ledger import DEFAULT_SESSION_CHANNEL


def read_content_bound_file(
    path_value: str,
    expected_sha256: str | None = None,
    *,
    label: str = "file input",
) -> tuple[Path, bytes]:
    """Read an external file once and verify the bytes a V2 request approved.

    The returned bytes are the bytes the caller must parse or write. Hashing
    and then reopening the pathname would merely move the TOCTOU window.
    Direct human CLI preflights may omit the digest; an active V2 gateway
    context may not.
    """
    if path_value == "-" and current_gateway_request() is not None:
        raise WriteRefused(
            f"GatewayEnvelopeV2 {label} must be a real path with an approved SHA-256; "
            "unbound stdin is not allowed"
        )
    source = Path(path_value).expanduser().resolve()
    if not source.is_file():
        raise WriteRefused(f"no such {label}: {source}")
    try:
        content = source.read_bytes()
    except OSError as exc:
        raise WriteRefused(f"cannot read {label} {source}: {exc}") from exc
    if expected_sha256 is None:
        if current_gateway_request() is not None:
            raise WriteRefused(
                f"GatewayEnvelopeV2 {label} requires a SHA-256 bound to the exact bytes"
            )
        return source, content
    if not re.fullmatch(r"sha256:[a-f0-9]{64}", expected_sha256):
        raise WriteRefused(
            f"{label} SHA-256 must use sha256:<64 lowercase hexadecimal digits>"
        )
    actual_sha256 = "sha256:" + hashlib.sha256(content).hexdigest()
    if actual_sha256 != expected_sha256:
        raise WriteRefused(
            f"approved {label} changed before use; expected {expected_sha256}, "
            f"found {actual_sha256}. Review the new bytes and create a new approval."
        )
    return source, content


def read_structured_file(
    path_value: str,
    *,
    expected_sha256: str | None = None,
    label: str = "structured input",
) -> dict:
    """Read a JSON/YAML object from a path, or from stdin when given ``-``.

    Stdin matters for callers that build an envelope in memory: writing it to
    a temp file first means a real file holding canonical intent has to be
    created, found, and cleaned up on every write path, including the ones
    that fail. ``-`` removes that lifecycle entirely.
    """
    if path_value == "-" and expected_sha256 is None \
            and current_gateway_request() is None:
        raw = sys.stdin.read()
        try:
            data = json.loads(raw)
        except ValueError as exc:
            raise WriteRefused(f"cannot parse structured input from stdin: {exc}") from exc
        if not isinstance(data, dict):
            raise WriteRefused("structured input must be an object")
        return data
    path, raw_bytes = read_content_bound_file(
        path_value,
        expected_sha256,
        label=label,
    )
    try:
        raw = raw_bytes.decode("utf-8")
        if path.suffix.lower() == ".json":
            data = json.loads(raw)
        else:
            data = yaml.safe_load(raw)
    except (UnicodeDecodeError, ValueError, yaml.YAMLError) as exc:
        raise WriteRefused(f"cannot parse {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise WriteRefused(f"structured input must be an object: {path}")
    return data


def prepare_review_envelope(capability_name: str, payload: dict,
                            snapshot: str, revisions: dict) -> dict:
    """Prepare a recoverable request during preflight, while its lock is held.

    The envelope names the channel whose session ledger the reviewed write
    joins: the active gateway request's channel, else the operator default
    a bare `session-end` resolves. A fixed agent channel split one
    operator's writes across two ledgers, so `session-end --commit-message`
    committed the shared ledgers without the receipt and note they name.
    """
    request = current_gateway_request()
    channel = request.channel if request is not None else DEFAULT_SESSION_CHANNEL
    envelope = {
        "schema_version": 2,
        "request_id": f"request-reviewed-{observations.new_hex()}",
        "idempotency_key": f"reviewed-{observations.new_hex()}",
        "capability": capability_name,
        "channel": channel,
        "expected_snapshot": snapshot,
        "expected_revisions": revisions,
        "payload": payload,
        "approval": {"kind": "operator-approval", "subject_sha256": ""},
    }
    envelope["approval"]["subject_sha256"] = intent_sha256(envelope)
    return envelope


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


def _payload_schema_path(root: Path, name: str) -> Path:
    return root / "system" / "schema" / "capabilities" / f"{name}.schema.json"


def validate_payload(root: Path, name: str, payload: dict) -> None:
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
    parser_factory=None,
):
    """Shared gateway admission for legacy and registered dispatch (SPEC 11.2 K1).

    Refuses misplaced approval and content-bound file payloads, validates
    the payload, and builds the namespace with the envelope guards.
    Admission derives the namespace from the request schema — it never
    constructs a CLI parser. Only legacy dispatch passes a
    ``parser_factory`` (built by the adapters that own CLI parsing) to
    resolve the named command's handler; its namespace then comes from
    that same parser, exactly as before. Returns
    (command_parser, namespace); the parser is None on the schema path.
    """
    from learning_os.store.contracts.payloads import (
        payload_to_namespace,
        payload_to_namespace_from_schema,
        subparsers,
    )

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
    validate_payload(root, definition.name, payload)
    if parser_factory is None:
        namespace = payload_to_namespace_from_schema(
            root, definition.name, payload,
            root=str(root),
            expected_snapshot=envelope.get("expected_snapshot"),
            expected_revisions=envelope.get("expected_revisions", {}),
        )
        command_parser = None
    else:
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


def dispatch(
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
            result["error_code"] = refusal.code
            result["error_retryable"] = refusal.retryable
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


def validate_capability_envelope(root: Path, envelope: dict, *, kind: str) -> None:
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


def context_from_v2(envelope: dict) -> GatewayRequestContext:
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
