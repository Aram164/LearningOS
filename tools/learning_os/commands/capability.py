"""The capability envelope gateway — the machine-facing write surface (ADR-006)."""

from __future__ import annotations

import contextlib
import io
import json
import sys
from jsonschema import Draft202012Validator
from learning_os.contracts.capability_catalog import command_definitions
from pathlib import Path
from .support import WriteRefused, _read_structured_file, _root


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
    from learning_os.contracts.payloads import payload_to_namespace, subparsers

    import los  # local: los imports this module, so the cycle must stay lazy

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
        directional_schema = schema["$defs"][kind]
    except KeyError as exc:  # pragma: no cover - a repository contract defect
        raise WriteRefused(f"capability envelope schema has no {kind} definition") from exc
    errors = sorted(
        Draft202012Validator(directional_schema).iter_errors(envelope),
        key=lambda error: list(error.path),
    )
    if errors:
        raise WriteRefused("invalid capability envelope: " + "; ".join(error.message for error in errors[:4]))


def cmd_capability(args) -> int:
    root = _root(args)
    definitions = command_definitions(root)
    # ``command_definitions`` already exposes only the public ``commands:``
    # section.  It is the allowlist; keeping a second dictionary here made
    # every new capability require two coordinated declarations.
    if args.name not in definitions:
        print(f"los: unknown or non-public capability: {args.name}", file=sys.stderr)
        return 2
    envelope = _read_structured_file(args.payload_file)
    _validate_capability_envelope(root, envelope, kind="request")
    if envelope.get("capability") != args.name:
        print("los: envelope capability does not match requested capability", file=sys.stderr)
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
