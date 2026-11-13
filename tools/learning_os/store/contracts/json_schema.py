"""Shared JSON-Schema enforcement for public read and write contracts."""

from __future__ import annotations

import functools
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker, ValidationError
from referencing import Registry, Resource


@functools.lru_cache(maxsize=64)
def _compiled_validator(
    schema_text: str,
    *,
    use_format: bool,
) -> Draft202012Validator:
    schema = json.loads(schema_text)
    return Draft202012Validator(
        schema,
        format_checker=FormatChecker() if use_format else None,
    )


def load_standalone_validator(
    schema_path: Path,
    *,
    format_checker: bool = False,
) -> Draft202012Validator:
    """Compile and cache a standalone validator keyed by live schema text."""
    return _compiled_validator(
        schema_path.read_text(encoding="utf-8"),
        use_format=format_checker,
    )


def transaction_receipt_errors(
    schema_root: Path,
    receipt: Mapping[str, object],
) -> tuple[bool, list[ValidationError]]:
    """Return ``(schema_present, sorted_errors)`` for a transaction receipt."""
    schema_path = schema_root / "system" / "schema" / "transaction-receipt.schema.json"
    if not schema_path.is_file():
        return (False, [])
    validator = load_standalone_validator(schema_path)
    errors = sorted(
        validator.iter_errors(receipt),
        key=lambda error: list(error.path),
    )
    return (True, errors)


class ContractValidationError(ValueError):
    """A value does not satisfy the producer-owned contract named by its schema."""


def schema_registry(schema_dir: Path) -> Registry:
    """Register every producer-owned schema so cross-schema refs fail closed."""
    registry = Registry()
    for candidate in sorted(schema_dir.glob("*.schema.json")):
        try:
            schema = json.loads(candidate.read_text(encoding="utf-8"))
            resource = Resource.from_contents(schema)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            raise ContractValidationError(
                f"cannot register contract schema {candidate.name}: {exc}"
            ) from exc
        schema_id = schema.get("$id")
        if isinstance(schema_id, str) and schema_id:
            registry = registry.with_resource(schema_id, resource)
        # Older producer schemas use relative ``learning-os/...`` identifiers,
        # while newer cross-contract schemas use the stable local HTTPS
        # namespace.  Register a filename alias as well so an absolute public
        # contract (for example Manifest v6) can reuse those exact nested
        # definitions without URL-joining a relative id under its own path.
        alias = f"https://learningos.local/schema/{candidate.name}"
        if alias != schema_id:
            registry = registry.with_resource(alias, resource)
    return registry


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
        Draft202012Validator(
            schema,
            registry=schema_registry(path.parent),
            format_checker=FormatChecker(),
        ).iter_errors(value),
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
