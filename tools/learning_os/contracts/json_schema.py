"""Shared JSON-Schema enforcement for public read and write contracts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker


class ContractValidationError(ValueError):
    """A value does not satisfy the producer-owned contract named by its schema."""


def validate_contract(
    root: Path,
    schema_name: str,
    value: Any,
    *,
    label: str | None = None,
) -> None:
    """Validate *value* against one schema under ``system/schema``.

    Public boundaries call this before emitting or persisting a value.  A
    missing schema is therefore a closed boundary, not an invitation to infer
    a shape from the current implementation.
    """
    path = root / "system" / "schema" / schema_name
    if not path.is_file():
        raise ContractValidationError(f"missing contract schema: {schema_name}")
    try:
        schema = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractValidationError(f"cannot read contract schema {schema_name}: {exc}") from exc

    errors = sorted(
        Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(value),
        key=lambda error: [str(part) for part in error.absolute_path],
    )
    if not errors:
        return
    details = []
    for error in errors[:8]:
        location = "/".join(str(part) for part in error.absolute_path) or "<root>"
        details.append(f"{location}: {error.message}")
    name = label or schema.get("title") or schema_name
    raise ContractValidationError(f"{name} contract violation: {'; '.join(details)}")
