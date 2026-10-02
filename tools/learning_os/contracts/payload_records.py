"""Accepted input shapes for opaque ``json_object`` payload fields (#93).

A capability envelope's payload is derived from the CLI parser, but argparse
declares only that a record field IS an object — never which fields the
handler accepts inside it. The catalogue closes that gap per command with
``payload_records:``: either an inline accepted-field list, a
``record_schema:`` pointer the generator derives names from, or
``freeform: true`` for the documented free-form maps. The generator merges
each resolved fragment over the parser-derived ``{"type": "object"}``, so
``capabilities NAME --json`` shows the accepted input fields and the
gateway refuses unknown ones at payload validation, before any
transaction work.

A fragment mirrors its handler's checks, never stricter ones: direct CLI
use never sees the schema, and anything the handler accepts must still
pass the gateway. In particular a field the handler tolerates as an
explicit null carries a null-inclusive type, and a full-record shape
requires only what the handler does not default itself.
"""

from __future__ import annotations

import json
from pathlib import Path

from .capability_catalog import PAYLOAD_RECORD_KEYS, load_capability_catalog
from .payloads import _NESTED_SCHEMAS

JSON_TYPES = frozenset(
    {"string", "integer", "number", "boolean", "object", "array", "null"}
)

#: Keys allowed on a nested field declaration (``fields:`` / ``items:``).
_NESTED_KEYS = frozenset({
    "description",
    "type",
    "accepted",
    "required",
    "types",
    "fields",
    "items",
    "min_properties",
    "min_items",
    "max_items",
})


class PayloadRecordError(Exception):
    pass


def _fail(where: str, detail: str) -> None:
    raise PayloadRecordError(f"payload_records {where}: {detail}")


def _string_list(value: object, *, where: str, label: str,
                 allow_empty: bool) -> list[str]:
    if not isinstance(value, list) or any(
        not isinstance(item, str) or not item.strip() for item in value
    ):
        _fail(where, f"{label} must be a list of non-empty strings")
    names = [item.strip() for item in value]
    if len(set(names)) != len(names):
        _fail(where, f"{label} lists a field twice")
    if not allow_empty and not names:
        _fail(where, f"{label} must not be empty")
    return names


def _json_type(value: object, *, where: str, label: str) -> str | list[str]:
    candidates = value if isinstance(value, list) else [value]
    if not candidates or any(
        not isinstance(item, str) or item not in JSON_TYPES for item in candidates
    ):
        _fail(where, f"{label} must be a JSON type or list of them")
    if len(set(candidates)) != len(candidates):
        _fail(where, f"{label} repeats a type")
    return candidates[0] if isinstance(value, str) else list(candidates)


def _checked_keys(decl: object, *, where: str, allowed: frozenset[str]) -> dict:
    if not isinstance(decl, dict):
        _fail(where, "must be a mapping")
    unknown = sorted(set(decl) - allowed)
    if unknown:
        _fail(where, f"unknown keys: {', '.join(unknown)}")
    return decl


def _non_negative_int(value: object, *, where: str, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        _fail(where, f"{label} must be an integer >= 0")
    return value


def _object_fragment(decl: dict, *, where: str) -> dict:
    """An object shape from ``accepted`` / ``required`` / ``types`` / ``fields``."""
    accepted = _string_list(decl.get("accepted"), where=where,
                            label="accepted", allow_empty=False)
    required = _string_list(decl.get("required", []), where=where,
                            label="required", allow_empty=True)
    outside = sorted(set(required) - set(accepted))
    if outside:
        _fail(where, f"required names unaccepted fields: {', '.join(outside)}")
    raw_types = decl.get("types", {})
    if not isinstance(raw_types, dict):
        _fail(where, "types must map accepted fields to JSON types")
    types = {}
    for name, value in raw_types.items():
        if name not in accepted:
            _fail(where, f"types names an unaccepted field: {name}")
        types[name] = _json_type(value, where=where, label=f"types.{name}")
    fields = decl.get("fields", {})
    if not isinstance(fields, dict):
        _fail(where, "fields must map accepted fields to declarations")
    for name in fields:
        if name not in accepted:
            _fail(where, f"fields names an unaccepted field: {name}")
    properties = {}
    for name in accepted:
        if name in fields:
            properties[name] = _field_fragment(
                fields[name], where=f"{where}.{name}")
        elif name in types:
            properties[name] = {"type": types[name]}
        else:
            properties[name] = {}
    fragment: dict = {"type": "object", "properties": properties,
                      "additionalProperties": False}
    if required:
        fragment["required"] = sorted(required)
    if "min_properties" in decl:
        minimum = _non_negative_int(decl["min_properties"], where=where,
                                    label="min_properties")
        if minimum:
            fragment["minProperties"] = minimum
    if "description" in decl:
        fragment["description"] = _described(decl["description"], where=where)
    return fragment


def _described(value: object, *, where: str) -> str:
    if not isinstance(value, str) or not value.strip():
        _fail(where, "description must be a non-empty string")
    return value.strip()


def _field_fragment(decl: object, *, where: str) -> dict:
    """One accepted field's schema: a scalar type, a nested object, an array."""
    node = _checked_keys(decl, where=where, allowed=_NESTED_KEYS)
    fragment: dict = {}
    if "type" in node:
        fragment["type"] = _json_type(node["type"], where=where, label="type")
    if "description" in node:
        fragment["description"] = _described(node["description"], where=where)
    if "accepted" in node or "fields" in node:
        declared = fragment.get("type")
        if declared is not None and declared != "object":
            _fail(where, "a shaped field must be an object")
        fragment.update(_object_fragment(
            {key: node[key] for key in
             ("accepted", "required", "types", "fields", "min_properties")
             if key in node}, where=where))
    if "items" in node:
        if fragment.get("type") != "array":
            _fail(where, "items needs type array")
        fragment["items"] = _element_fragment(node["items"], where=f"{where}[]")
    for bound in ("min_items", "max_items"):
        if bound in node:
            if fragment.get("type") != "array":
                _fail(where, f"{bound} needs type array")
            value = _non_negative_int(node[bound], where=where, label=bound)
            fragment["minItems" if bound == "min_items" else "maxItems"] = value
    if not fragment:
        _fail(where, "declares neither a type nor a nested shape")
    return fragment


def _element_fragment(decl: object, *, where: str) -> dict:
    node = _checked_keys(decl, where=where, allowed=_NESTED_KEYS)
    if "accepted" in node or "fields" in node:
        if "type" in node and node["type"] != "object":
            _fail(where, "a shaped element must be an object")
        element = _object_fragment(
            {key: node[key] for key in
             ("accepted", "required", "types", "fields", "min_properties")
             if key in node}, where=where)
        if "description" in node:
            element["description"] = _described(node["description"], where=where)
        return element
    if "items" in node or "min_items" in node or "max_items" in node:
        _fail(where, "nested arrays are not declared")
    if "type" not in node:
        _fail(where, "an array element needs a type or a nested shape")
    element = {"type": _json_type(node["type"], where=where, label="type")}
    if "description" in node:
        element["description"] = _described(node["description"], where=where)
    return element


def _record_shape(root: Path, path: str, *, where: str) -> tuple[list[str], list[str]]:
    """Top-level accepted names and required names from a record schema.

    Only closed object records qualify: deriving a closed fragment from
    an open record would refuse at the gateway what the handler accepts.
    """
    candidate = (root / path).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError:
        _fail(where, f"record_schema escapes the repository: {path}")
    if not candidate.is_file():
        _fail(where, f"record_schema does not exist: {path}")
    try:
        schema = json.loads(candidate.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        _fail(where, f"record_schema does not parse: {exc}")
    target = schema
    seen = 0
    while isinstance(target, dict) and isinstance(target.get("$ref"), str):
        reference = target["$ref"]
        if not reference.startswith("#/"):
            _fail(where, f"record_schema has an external $ref: {reference}")
        node: object = schema
        for part in reference[2:].split("/"):
            node = node.get(part) if isinstance(node, dict) else None
        if not isinstance(node, dict):
            _fail(where, f"record_schema $ref resolves nowhere: {reference}")
        target = node
        seen += 1
        if seen > 4:
            _fail(where, "record_schema $ref chain is too deep")
    if not isinstance(target, dict) or target.get("type", "object") != "object":
        _fail(where, "record_schema is not an object record")
    properties = target.get("properties")
    if not isinstance(properties, dict) or not properties:
        _fail(where, "record_schema names no top-level properties")
    if target.get("additionalProperties") is not False and not (
            schema.get("unevaluatedProperties") is False
            or target.get("unevaluatedProperties") is False):
        _fail(where, "record_schema is not a closed record")
    required = target.get("required", [])
    if not isinstance(required, list) or any(not isinstance(name, str) for name in required):
        _fail(where, "record_schema required is not a list of names")
    return list(properties), [name for name in required if name in properties]


def _resolve_declaration(root: Path, capability: str, field: str,
                         decl: dict) -> dict:
    where = f"{capability}.{field}"
    if decl.get("freeform") is True:
        if set(decl) - {"freeform", "description"}:
            _fail(where, "freeform takes only a description")
        fragment = {"type": "object"}
        if "description" in decl:
            fragment["description"] = _described(decl["description"], where=where)
        return fragment
    if decl.get("freeform") is not None:
        _fail(where, "freeform must be true")
    if "record_schema" in decl:
        if set(decl) - {"record_schema", "required", "description"}:
            _fail(where, "record_schema takes only required and description")
        path = decl["record_schema"]
        if not isinstance(path, str) or not path.strip():
            _fail(where, "record_schema must be a repo-relative path")
        accepted, derived = _record_shape(root, path.strip(), where=where)
        if "required" in decl:
            required = _string_list(decl["required"], where=where,
                                    label="required", allow_empty=True)
            outside = sorted(set(required) - set(accepted))
            if outside:
                _fail(where, f"required names unaccepted fields: {', '.join(outside)}")
        else:
            required = derived
        fragment = {
            "type": "object",
            "properties": {name: {} for name in accepted},
            "additionalProperties": False,
        }
        if required:
            fragment["required"] = sorted(required)
        fragment["description"] = (
            _described(decl["description"], where=where)
            if "description" in decl
            else f"Accepted {field} fields; the stored record is governed by {path.strip()}."
        )
        return fragment
    if "accepted" not in decl:
        _fail(where, "needs accepted, record_schema, or freeform")
    return _object_fragment(
        {key: decl[key] for key in
         ("accepted", "required", "types", "fields", "min_properties",
          "description") if key in decl},
        where=where)


def resolve_all(root: Path) -> dict[tuple[str, str], dict]:
    """Every ``payload_records`` fragment, keyed by (capability, field).

    Raises :class:`PayloadRecordError` on a malformed declaration and on a
    declaration for a field that already has a contract-module fragment:
    one source of truth per field, never two.
    """
    data = load_capability_catalog(root)
    resolved: dict[tuple[str, str], dict] = {}
    for section in ("commands", "internal_commands"):
        for name, row in (data.get(section, {}) or {}).items():
            records = row.get("payload_records") or {}
            for field, decl in records.items():
                if (name, field) in _NESTED_SCHEMAS:
                    raise PayloadRecordError(
                        f"payload_records {name}.{field}: this field already "
                        "has a contract-module fragment; declare it once"
                    )
                resolved[(name, field)] = _resolve_declaration(
                    root, name, field, _checked_keys(
                        decl, where=f"{name}.{field}",
                        allowed=PAYLOAD_RECORD_KEYS))
    return resolved
