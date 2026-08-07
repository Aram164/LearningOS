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

# Owned by the envelope, never by the payload.
ENVELOPE_OWNED = frozenset({"expected_snapshot", "expected_revision"})
# Argparse bookkeeping that is not part of any capability's surface.
NOT_A_PAYLOAD_FIELD = frozenset({"help", "func", "command", "root", "json"})


def _json_type(action: argparse.Action) -> dict:
    if isinstance(action, argparse._StoreTrueAction | argparse._StoreFalseAction):
        return {"type": "boolean"}
    if isinstance(action, argparse._AppendAction):
        return {"type": "array", "items": {"type": "string"}}
    if action.nargs in ("*", "+"):
        return {"type": "array", "items": {"type": "string"}}
    if action.type is int:
        return {"type": "integer"}
    return {"type": "string"}


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
    return {
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
