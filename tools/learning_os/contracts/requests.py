"""Effective request-schema loader (PLAN D2).

Single source of truth for request properties: primaries are returned
unchanged; aliases resolve to their primary with only ``$id`` replaced.
"""

from __future__ import annotations

import json
from pathlib import Path

REQUESTS_DIRNAME = "system/schema/requests"

_ALIAS_KEYS = frozenset({"$schema", "$id", "x-governs", "$ref"})


def _requests_dir(root: Path) -> Path:
    return Path(root) / REQUESTS_DIRNAME


def _check_operation(operation: str) -> str:
    if not operation or not isinstance(operation, str):
        raise ValueError(f"invalid operation name: {operation!r}")
    if "/" in operation or "\\" in operation or ".." in operation:
        raise ValueError(f"invalid operation name: {operation!r}")
    if ":" in operation or "#" in operation:
        raise ValueError(f"invalid operation name: {operation!r}")
    return operation


def _check_target(target: str) -> str:
    if not target or not isinstance(target, str):
        raise ValueError(f"invalid $ref target: {target!r}")
    if "/" in target or "\\" in target:
        raise ValueError(f"invalid $ref target (separator): {target!r}")
    if ".." in target:
        raise ValueError(f"invalid $ref target (traversal): {target!r}")
    if ":" in target:
        raise ValueError(f"invalid $ref target (URI scheme): {target!r}")
    if "#" in target:
        raise ValueError(f"invalid $ref target (fragment): {target!r}")
    if not target.endswith(".schema.json"):
        raise ValueError(f"invalid $ref target (must end .schema.json): {target!r}")
    return target


def request_schema(root: Path, operation: str) -> dict:
    """Return the effective request schema for ``operation``.

    A primary document is returned unchanged. An alias (exactly the four
    keys ``$schema``, ``$id``, ``x-governs``, ``$ref``) resolves to its
    primary with only ``$id`` replaced. Refuses separators, traversal,
    URI schemes, fragments, chains and cycles; no network.
    """
    _check_operation(operation)
    directory = _requests_dir(root)
    path = directory / f"{operation}.schema.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise
    except OSError as exc:
        raise FileNotFoundError(f"request schema not found: {operation}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"request schema {operation} is not an object")
    if "$ref" not in data:
        return data
    if set(data.keys()) != _ALIAS_KEYS:
        raise ValueError(
            f"alias {operation} must contain only {sorted(_ALIAS_KEYS)}"
        )
    target = _check_target(data["$ref"])
    target_path = directory / target
    try:
        primary = json.loads(target_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ValueError(f"alias {operation} targets missing {target}") from None
    if not isinstance(primary, dict):
        raise ValueError(f"primary {target} is not an object")
    if "$ref" in primary:
        raise ValueError(f"alias {operation} targets {target} which itself has $ref (chain)")
    effective = dict(primary)
    effective["$id"] = data["$id"]
    return effective
