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

from .atlas_question import question_schema as atlas_question_schema
from .batch_notes import bundle_schema as batch_notes_schema

# Owned by the envelope, never by the payload.
#
# `approve` is the operator's gesture on the envelope, and the concurrency
# tokens live there so a caller cannot send two answers to the same question.
# The CLI keeps `--approve` for direct human use; only the generated V2
# payload schema excludes it. `check` is deliberately NOT here: it is a
# per-command dry-run mode the gateway honors, and existing callers request
# `--check` through the envelope payload. Both revision spellings stay
# excluded: the CLI flag is `--expected-revision` (singular) while the
# envelope carries `expected_revisions` (plural). `apply_reviewed_sha256`
# is a CLI-only reviewed-apply gesture and never crosses the gateway.
# `report_out` is a CLI-only output file: presentation, not approved content.
ENVELOPE_OWNED = frozenset({
    "approve",
    "apply_reviewed_sha256",
    "report_out",
    "review_report",
    "expected_snapshot",
    "expected_revision",
    "expected_revisions",
})
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
    "unit.plan.revise": ("record",),
}

#: Nested subschemas for object-typed payload fields the CLI parser cannot
#: express. Argparse declares only that a field IS an object; the registered
#: fragment states what the gateway requires inside it. Keyed by
#: (capability, field) so the merge stays scoped, and the generated files
#: remain a deterministic function of parser plus registry. Each fragment is
#: built by its own contract module — which the handler imports too — never
#: written inline here: one source of truth, mirrored nowhere. A nested shape
#: must mirror its handler's checks, never invent stricter ones: direct CLI
#: use never sees the schema.
_NESTED_SCHEMAS: dict[tuple[str, str], dict] = {
    ("note.analysis.save_batch", "bundle"): batch_notes_schema(),
    ("atlas.question.save", "question"): atlas_question_schema(),
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
        schema: dict = {"type": "integer"}
    elif action.type is float:
        # First used by module-attempt --grade: without this a float
        # argument derives {"type": "string"}, and a gateway envelope
        # carrying the JSON number the CLI itself parses is refused.
        schema = {"type": "number"}
    else:
        schema = {"type": "string"}
    choices = getattr(action, "choices", None)
    # Argparse `choices` are the CLI's accepted vocabulary. The generated
    # schema used to say bare `string` here, so the gateway accepted values
    # the named command refuses — and one handler recorded an unknown status
    # as `skipped`. A dict `choices` is a subparsers action, never a payload
    # field; anything else enumerates the accepted values verbatim.
    if choices and not isinstance(choices, dict):
        schema["enum"] = list(choices)
    return schema


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


def json_object_fields(command_parser: argparse.ArgumentParser) -> set[str]:
    """Payload fields the parser declares as opaque structured objects."""
    return {
        action.dest for action in payload_fields(command_parser)
        if action.type is json_object
    }


def payload_schema(
    name: str,
    command_parser: argparse.ArgumentParser,
    *,
    payload_records: dict[tuple[str, str], dict] | None = None,
) -> dict:
    """A Draft 2020-12 schema for one capability's payload.

    ``payload_records`` carries the catalogue-declared accepted input
    shapes (``contracts.payload_records.resolve_all``), merged over the
    parser-derived surface exactly like the contract-module fragments.
    """
    properties, required = {}, []
    for action in payload_fields(command_parser):
        properties[action.dest] = _json_type(action)
        # The schema is the declared payload agents read before any write, so
        # each field carries its CLI help verbatim — no extra --help call per
        # capability to learn what drop_sha256 or replace means.
        if action.help and action.help != argparse.SUPPRESS:
            properties[action.dest]["description"] = action.help
        if action.required or not action.option_strings:
            required.append(action.dest)
    for (capability_name, field), nested in _NESTED_SCHEMAS.items():
        if capability_name == name and field in properties:
            # A fragment with its own description keeps it; otherwise the
            # parser help still describes the field.
            if "description" not in nested and "description" in properties[field]:
                nested = {**nested,
                          "description": properties[field]["description"]}
            properties[field] = nested
    for (capability_name, field), fragment in (payload_records or {}).items():
        if capability_name == name and field in properties:
            if "description" not in fragment \
                    and "description" in properties[field]:
                fragment = {**fragment,
                            "description": properties[field]["description"]}
            properties[field] = fragment
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
    # `--progress-next` without `--progress-summary` is refused inside the
    # handler; the contract says so too, so the gateway refuses at payload
    # validation. The handler keeps its check: direct CLI use never sees
    # this schema, and only the handler can refuse a blank summary.
    if name == "stage.progress.update" and "progress_next" in properties \
            and "progress_summary" in properties:
        dependent["progress_next"] = ["progress_summary"]
    if dependent:
        schema["dependentRequired"] = dependent
    return schema


def all_payload_schemas(
    parser: argparse.ArgumentParser,
    definitions,
    *,
    payload_records: dict[tuple[str, str], dict] | None = None,
) -> dict[str, dict]:
    """name -> schema, for every declared command capability with a CLI command.

    A catalogue declaration that names no ``json_object`` payload field is
    a typo, not a no-op: it fails loudly here, in the generator and in the
    derivation test alike, instead of silently declaring nothing.
    """
    commands = subparsers(parser)
    for capability_name, field in (payload_records or {}):
        definition = definitions.get(capability_name)
        command_parser = commands.get(definition.cli_command or "") \
            if definition is not None else None
        if command_parser is None or \
                field not in json_object_fields(command_parser):
            raise ValueError(
                f"payload_records {capability_name}.{field} declares no "
                "json_object payload field"
            )
    out = {}
    for name, definition in sorted(definitions.items()):
        command_parser = commands.get(definition.cli_command or "")
        if command_parser is None:
            continue
        out[name] = payload_schema(name, command_parser,
                                   payload_records=payload_records)
    return out


def _check_payload_choices(field: str, action: argparse.Action,
                           value: object) -> None:
    """Refuse a payload value the named command's `choices` would refuse.

    Mirrors argparse's own check, including its leniency: an explicit null
    is absence, not a value, and each element of a repeated flag is checked
    on its own. A dict `choices` is a subparsers action, never a payload
    field.
    """
    choices = getattr(action, "choices", None)
    if not choices or isinstance(choices, dict) or value is None:
        return
    allowed = list(choices)
    candidates = list(value) if isinstance(value, list) else [value]
    for candidate in candidates:
        if candidate is None:
            continue
        if candidate not in allowed:
            # Deferred: the commands package imports this module at dispatch.
            from learning_os.commands.support import WriteRefused

            raise WriteRefused(
                f"invalid payload: {field} must be one of {allowed}, "
                f"got {candidate!r}"
            )


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

    Argparse `choices` are enforced here as well as in the generated schema:
    the schema is the contract agents read, and this is the defence in depth
    for any field whose schema was regenerated without them.
    """
    namespace = argparse.Namespace()
    by_dest = {}
    for action in command_parser._actions:
        if isinstance(action, argparse._HelpAction):
            continue
        setattr(namespace, action.dest, action.default)
        by_dest[action.dest] = action
    for key, value in payload.items():
        action = by_dest.get(key)
        if action is not None:
            _check_payload_choices(key, action, value)
        setattr(namespace, key, value)
    namespace.root = root
    namespace.expected_snapshot = expected_snapshot
    namespace.expected_revision = [
        f"{artifact}={revision}" for artifact, revision in (expected_revisions or {}).items()
    ]
    return namespace
