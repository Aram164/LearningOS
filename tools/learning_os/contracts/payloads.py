"""Capability payload schemas, derived from the CLI parser.

A capability envelope's ``payload`` carries exactly the arguments its named
CLI command accepts. Rather than maintaining a second, hand-written copy of
that surface, the schema is *derived* from the very parser that defines the
command — so the two cannot drift, and adding a CLI flag cannot silently leave
the machine interface behind.

Concurrency tokens are deliberately excluded from the payload: the envelope
already carries ``expected_snapshot`` and ``expected_revisions`` as
first-class fields, and accepting them twice would let a caller send two
different answers to the same question.
"""

from __future__ import annotations

import argparse
import json
import re

# Owned by the envelope, never by the payload.
ENVELOPE_OWNED = frozenset({"expected_snapshot", "expected_revision"})
# Argparse bookkeeping that is not part of any capability's surface.
NOT_A_PAYLOAD_FIELD = frozenset({"help", "func", "command", "root", "json"})

# These CLI commands accept stdin for human convenience. A capability envelope
# cannot approve bytes that arrive on a different process channel, so V2
# payload schemas require the content inline (or, for capture, the separately
# hash-bound file alternative).
_GATEWAY_INLINE_REQUIRED = {
    "path.note.write": ("text",),
    "stage.note.write": ("text",),
    "unit.note.append": ("text",),
}


def json_object(value: str) -> dict:
    """argparse converter for an argument that IS a structured record.

    Most command arguments are scalars, and a record-shaped one used to be
    passed by writing a file and naming the path. That works from a shell and is
    hostile to the gateway: an agent holding a project object in memory had to
    invent a temporary file to send it. The alternative taken previously was
    worse — a gateway-only branch that accepted an inline object no schema
    described, and skipped payload validation to do it (engineering audit
    2026-08-08, finding 2).

    Declaring the shape here keeps one surface: the CLI accepts JSON text, the
    gateway sends a real object, and both are described by the same generated
    schema.
    """
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise argparse.ArgumentTypeError(f"expected a JSON object: {exc}") from exc
    if not isinstance(parsed, dict):
        raise argparse.ArgumentTypeError("expected a JSON object")
    return parsed


def sha256_value(value: str) -> str:
    """Argparse converter for one canonical ``sha256:<hex>`` digest."""
    if not re.fullmatch(r"sha256:[a-f0-9]{64}", value):
        raise argparse.ArgumentTypeError(
            "expected SHA-256 as sha256:<64 lowercase hexadecimal digits>"
        )
    return value


def _scalar_json_type(action: argparse.Action) -> dict:
    if action.type is json_object:
        return {"type": "object"}
    if action.type is sha256_value:
        return {"type": "string", "pattern": "^sha256:[a-f0-9]{64}$"}
    if action.type is int:
        return {"type": "integer"}
    return {"type": "string"}


def _json_type(action: argparse.Action) -> dict:
    if isinstance(action, argparse._StoreTrueAction | argparse._StoreFalseAction):
        return {"type": "boolean"}
    if isinstance(action, argparse._AppendAction):
        return {"type": "array", "items": _scalar_json_type(action)}
    if action.nargs in ("*", "+"):
        return {"type": "array", "items": _scalar_json_type(action)}
    return _scalar_json_type(action)


def _exclusive_choices(command_parser: argparse.ArgumentParser) -> list[dict]:
    """`oneOf` branches for each REQUIRED mutually exclusive argument group.

    Without this the generated schema would say both alternatives are optional
    and stay silent about the fact that exactly one is needed — a contract that
    accepts a payload the handler will refuse. The gateway is the deterministic
    boundary around probabilistic agents, so its machine-readable contract has
    to be the trustworthy part.
    """
    out = []
    for group in command_parser._mutually_exclusive_groups:
        if not group.required:
            continue
        names = sorted(
            action.dest for action in group._group_actions
            if action.dest not in NOT_A_PAYLOAD_FIELD and action.dest not in ENVELOPE_OWNED
        )
        if len(names) > 1:
            out.append({"oneOf": [{"required": [name]} for name in names]})
    return out


def subparsers(parser: argparse.ArgumentParser) -> dict[str, argparse.ArgumentParser]:
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            return dict(action.choices)
    return {}


def payload_fields(command_parser: argparse.ArgumentParser) -> list[argparse.Action]:
    return [
        action for action in command_parser._actions
        if action.dest not in NOT_A_PAYLOAD_FIELD
        and action.dest not in ENVELOPE_OWNED
        and not isinstance(action, argparse._HelpAction)
    ]


def payload_schema(name: str, command_parser: argparse.ArgumentParser) -> dict:
    """A Draft 2020-12 schema for one capability's payload."""
    properties, required = {}, []
    for action in payload_fields(command_parser):
        properties[action.dest] = _json_type(action)
        if action.required or not action.option_strings:
            required.append(action.dest)
    required.extend(_GATEWAY_INLINE_REQUIRED.get(name, ()))
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"capabilities/{name}.schema.json",
        "title": f"payload for capability {name}",
        "description": (
            "Derived from the los CLI parser for this capability's named "
            "command. Do not hand-edit; regenerate with "
            "tools/generate_capability_schemas.py."
        ),
        "type": "object",
        "additionalProperties": False,
        "required": sorted(required),
        "properties": dict(sorted(properties.items())),
    }
    choices = _exclusive_choices(command_parser)
    if name == "capture.create":
        choices.append({
            "oneOf": [
                {"required": ["file"], "not": {"required": ["text"]}},
                {"required": ["text"], "not": {"required": ["file"]}},
            ]
        })
    if len(choices) == 1:
        schema["oneOf"] = choices[0]["oneOf"]
    elif choices:
        schema["allOf"] = choices
    # A path identifies where bytes may be read; the companion digest binds
    # which bytes were approved.  Keep both directions closed so a gateway
    # payload can never supply one without the other. Direct CLI parsers leave
    # the digest optional so human-only no-write preflights remain convenient.
    dependent: dict[str, list[str]] = {}
    for digest_field in sorted(properties):
        if not digest_field.endswith("_sha256"):
            continue
        input_field = digest_field.removesuffix("_sha256")
        if input_field in properties:
            dependent[input_field] = [digest_field]
            dependent[digest_field] = [input_field]
    if dependent:
        schema["dependentRequired"] = dependent
    return schema


def all_payload_schemas(parser: argparse.ArgumentParser, definitions) -> dict[str, dict]:
    """name -> schema, for every declared command capability with a CLI command."""
    commands = subparsers(parser)
    out = {}
    for name, definition in sorted(definitions.items()):
        command_parser = commands.get(definition.cli_command or "")
        if command_parser is None:
            continue
        out[name] = payload_schema(name, command_parser)
    return out


def payload_to_namespace(
    command_parser: argparse.ArgumentParser,
    payload: dict,
    *,
    root: str | None,
    expected_snapshot: str | None,
    expected_revisions: dict[str, int] | None,
) -> argparse.Namespace:
    """Build the args a handler expects from a validated payload.

    Defaults come from the parser, so a payload that omits an optional field
    behaves exactly as the named CLI command would with the flag absent.
    """
    namespace = argparse.Namespace()
    for action in command_parser._actions:
        if isinstance(action, argparse._HelpAction):
            continue
        setattr(namespace, action.dest, action.default)
    for key, value in payload.items():
        setattr(namespace, key, value)
    namespace.root = root
    namespace.expected_snapshot = expected_snapshot
    namespace.expected_revision = [
        f"{artifact}={revision}" for artifact, revision in (expected_revisions or {}).items()
    ]
    return namespace
