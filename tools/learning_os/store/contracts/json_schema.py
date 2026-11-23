"""Shared JSON-Schema enforcement for public read and write contracts."""

from __future__ import annotations

import functools
import json
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker, ValidationError
from referencing import Registry, Resource

# --- formats ---------------------------------------------------------------
# jsonschema's FormatChecker() checks "date-time" and "uri" only when the
# optional rfc3339-validator / rfc3987 distributions are installed; without
# them both formats silently validate anything. The UI's Ajv (ajv-formats
# 3.0.1, full mode) enforces both. These checkers port ajv-formats' full
# definitions, so Core — the producer and the only writer — refuses what the
# UI would refuse, and the answer no longer depends on which optional
# packages happen to be installed. tests/test_contract_differential.py
# compares the two sides on a set of edge cases.

_DATE = re.compile(r"(\d\d\d\d)-(\d\d)-(\d\d)", re.ASCII)
_DAYS = (0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
_TIME = re.compile(
    r"(\d\d):(\d\d):(\d\d(?:\.\d+)?)(z|([+-])(\d\d)(?::?(\d\d))?)?",
    re.ASCII | re.IGNORECASE)
_DATE_TIME_SEPARATOR = re.compile(r"t|\s", re.IGNORECASE)
_NOT_URI_FRAGMENT = re.compile(r"/|:")
_URI = re.compile(
    (
        r"(?:[a-z][a-z0-9+\-.]*:)(?:\/?\/(?:(?:[a-z0-9\-._~!$&'()*+,;=:]|%[0-9a-f]{2})*@)?(?:"
        r"\[(?:(?:(?:(?:[0-9a-f]{1,4}:){6}|::(?:[0-9a-f]{1,4}:){5}|(?:[0-9a-f]{1,4})?::(?:[0-9a"
        r"-f]{1,4}:){4}|(?:(?:[0-9a-f]{1,4}:){0,1}[0-9a-f]{1,4})?::(?:[0-9a-f]{1,4}:){3}|(?:(?"
        r":[0-9a-f]{1,4}:){0,2}[0-9a-f]{1,4})?::(?:[0-9a-f]{1,4}:){2}|(?:(?:[0-9a-f]{1,4}:){0,"
        r"3}[0-9a-f]{1,4})?::[0-9a-f]{1,4}:|(?:(?:[0-9a-f]{1,4}:){0,4}[0-9a-f]{1,4})?::)(?:[0-"
        r"9a-f]{1,4}:[0-9a-f]{1,4}|(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d"
        r"|[01]?\d\d?))|(?:(?:[0-9a-f]{1,4}:){0,5}[0-9a-f]{1,4})?::[0-9a-f]{1,4}|(?:(?:[0-9a-f"
        r"]{1,4}:){0,6}[0-9a-f]{1,4})?::)|[Vv][0-9a-f]+\.[a-z0-9\-._~!$&'()*+,;=:]+)\]|(?:(?:2"
        r"5[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)|(?:[a-z0-9\-._~!$&'"
        r"()*+,;=]|%[0-9a-f]{2})*)(?::\d*)?(?:\/(?:[a-z0-9\-._~!$&'()*+,;=:@]|%[0-9a-f]{2})*)*"
        r"|\/(?:(?:[a-z0-9\-._~!$&'()*+,;=:@]|%[0-9a-f]{2})+(?:\/(?:[a-z0-9\-._~!$&'()*+,;=:@]"
        r"|%[0-9a-f]{2})*)*)?|(?:[a-z0-9\-._~!$&'()*+,;=:@]|%[0-9a-f]{2})+(?:\/(?:[a-z0-9\-._~"
        r"!$&'()*+,;=:@]|%[0-9a-f]{2})*)*)(?:\?(?:[a-z0-9\-._~!$&'()*+,;=:@/?]|%[0-9a-f]{2})*)"
        r"?(?:#(?:[a-z0-9\-._~!$&'()*+,;=:@/?]|%[0-9a-f]{2})*)?"
    ),
    re.ASCII | re.IGNORECASE)


def _is_full_date(value: str) -> bool:
    match = _DATE.fullmatch(value)
    if match is None:
        return False
    year, month, day = (int(part) for part in match.groups())
    leap = year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
    return 1 <= month <= 12 and 1 <= day <= (29 if month == 2 and leap else _DAYS[month])


def _is_full_time(value: str) -> bool:
    match = _TIME.fullmatch(value)
    if match is None:
        return False
    hour, minute = int(match[1]), int(match[2])
    second = float(match[3])
    zone, sign = match[4], -1 if match[5] == "-" else 1
    zone_hour, zone_minute = int(match[6] or 0), int(match[7] or 0)
    if zone_hour > 23 or zone_minute > 59 or not zone:
        return False
    if hour <= 23 and minute <= 59 and second < 60:
        return True
    # A leap second is valid only at 23:59 UTC.
    utc_minute = minute - zone_minute * sign
    utc_hour = hour - zone_hour * sign - (1 if utc_minute < 0 else 0)
    return utc_hour in (23, -1) and utc_minute in (59, -1) and second < 61


def is_date_time(value: object) -> bool:
    """RFC 3339 date-time with a required offset, as ajv-formats checks it."""
    if not isinstance(value, str):
        return True
    parts = _DATE_TIME_SEPARATOR.split(value)
    return len(parts) == 2 and _is_full_date(parts[0]) and _is_full_time(parts[1])


def is_uri(value: object) -> bool:
    """An absolute RFC 3986 URI, as ajv-formats checks it."""
    if not isinstance(value, str):
        return True
    return bool(_NOT_URI_FRAGMENT.search(value)) and _URI.fullmatch(value) is not None


def core_format_checker() -> FormatChecker:
    """jsonschema's format checker, with Core's own date-time and uri checks."""
    checker = FormatChecker()
    checker.checks("date-time")(is_date_time)
    checker.checks("uri")(is_uri)
    return checker


@functools.lru_cache(maxsize=64)
def _compiled_validator_for_dir(
    schema_text: str,
    registry_fingerprint: tuple[tuple[str, str], ...],
    *,
    use_format: bool,
) -> Draft202012Validator:
    schema = json.loads(schema_text)
    registry = Registry()
    for name, text in registry_fingerprint:
        ref_schema = json.loads(text)
        resource = Resource.from_contents(ref_schema)
        schema_id = ref_schema.get("$id")
        if isinstance(schema_id, str) and schema_id:
            registry = registry.with_resource(schema_id, resource)
        alias = f"https://learningos.local/schema/{name}"
        if alias != schema_id:
            registry = registry.with_resource(alias, resource)
    return Draft202012Validator(
        schema,
        registry=registry,
        format_checker=core_format_checker() if use_format else None,
    )


def _registry_snapshot(schema_dir: Path) -> tuple[tuple[str, str], ...]:
    items: list[tuple[str, str]] = []
    if not schema_dir.is_dir():
        return ()
    for candidate in sorted(schema_dir.glob("*.schema.json")):
        try:
            items.append((candidate.name, candidate.read_text(encoding="utf-8")))
        except OSError:
            continue
    return tuple(items)


def load_standalone_validator(
    schema_path: Path,
    *,
    format_checker: bool = False,
) -> Draft202012Validator:
    """Compile and cache a standalone validator keyed by live schema text."""
    return _compiled_validator_for_dir(
        schema_path.read_text(encoding="utf-8"),
        _registry_snapshot(schema_path.parent),
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
    validator = load_standalone_validator(schema_path, format_checker=True)
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
            format_checker=core_format_checker(),
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
