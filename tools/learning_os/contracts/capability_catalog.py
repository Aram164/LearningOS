"""Loader and consistency checks for ``system/contracts/capabilities.yaml``."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import yaml


class CapabilityCatalogError(Exception):
    pass


@dataclass(frozen=True)
class CapabilityDefinition:
    name: str
    handler: str
    cli_command: str | None
    writes: tuple[str, ...]
    invariants: tuple[str, ...]
    internal: bool = False


@dataclass(frozen=True)
class QueryDefinition:
    name: str
    handler: str
    result: str
    schema: str | None
    invariants: tuple[str, ...]


@dataclass(frozen=True)
class DomainCapabilityDefinition:
    name: str
    writes: tuple[str, ...]
    invariants: tuple[str, ...]
    allowed_fields: tuple[str, ...]


def _string_list(value, *, label: str, required: bool = False) -> tuple[str, ...]:
    if value is None:
        value = []
    if not isinstance(value, list) or any(
        not isinstance(item, str) or not item.strip() for item in value
    ):
        raise CapabilityCatalogError(f"{label} must be a list of non-empty strings")
    if required and not value:
        raise CapabilityCatalogError(f"{label} must not be empty")
    return tuple(item.strip() for item in value)


def load_capability_catalog(root: Path) -> dict:
    path = root / "system" / "contracts" / "capabilities.yaml"
    if not path.is_file():
        raise CapabilityCatalogError(f"capability catalogue not found: {path}")
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        raise CapabilityCatalogError(f"invalid capability catalogue: {exc}") from exc
    if not isinstance(data, dict) or data.get("contract_version") != 1:
        raise CapabilityCatalogError("capability catalogue contract_version must be 1")
    if data.get("contract") != "learningos-capabilities" or data.get("schema_version") != 1:
        raise CapabilityCatalogError(
            "capability catalogue must declare contract learningos-capabilities schema_version 1"
        )
    for section in ("queries", "commands", "internal_commands"):
        rows = data.get(section, {}) or {}
        if not isinstance(rows, dict):
            raise CapabilityCatalogError(f"capability catalogue {section} must be a mapping")
        for name, row in rows.items():
            if not isinstance(name, str) or not isinstance(row, dict):
                raise CapabilityCatalogError(f"invalid capability declaration in {section}")
            if not isinstance(row.get("handler"), str) or not row["handler"].strip():
                raise CapabilityCatalogError(f"capability {name} has no handler")
            _string_list(row.get("invariants"), label=f"capability {name} invariants")
            if section == "queries":
                if not isinstance(row.get("result"), str) or not row["result"].strip():
                    raise CapabilityCatalogError(f"query {name} has no result contract")
                schema = row.get("schema")
                if re.search(r"-v\d+$", row["result"].strip()) and schema is None:
                    raise CapabilityCatalogError(
                        f"versioned query {name} has no producer-owned schema"
                    )
                if schema is not None:
                    if not isinstance(schema, str) or not schema.strip():
                        raise CapabilityCatalogError(f"query {name} has an invalid schema path")
                    schema_path = (root / schema).resolve()
                    try:
                        schema_path.relative_to(root.resolve())
                    except ValueError as exc:
                        raise CapabilityCatalogError(
                            f"query {name} schema escapes the repository"
                        ) from exc
                    if not schema_path.is_file():
                        raise CapabilityCatalogError(
                            f"query {name} schema does not exist: {schema}"
                        )
            else:
                _string_list(
                    row.get("writes"), label=f"capability {name} writes", required=True
                )
                cli_command = row.get("cli_command")
                if section == "commands" and (
                    not isinstance(cli_command, str) or not cli_command.strip()
                ):
                    raise CapabilityCatalogError(
                        f"public command {name} has no CLI command"
                    )

    rows = data.get("domain_capabilities", {}) or {}
    if not isinstance(rows, dict):
        raise CapabilityCatalogError(
            "capability catalogue domain_capabilities must be a mapping"
        )
    for name, row in rows.items():
        if not isinstance(name, str) or not name.strip() or not isinstance(row, dict):
            raise CapabilityCatalogError("invalid domain capability declaration")
        _string_list(
            row.get("writes"), label=f"domain capability {name} writes", required=True
        )
        _string_list(
            row.get("invariants"), label=f"domain capability {name} invariants"
        )
        _string_list(
            row.get("allowed_fields"), label=f"domain capability {name} allowed_fields"
        )
    return data


def command_definitions(root: Path, *, include_internal: bool = False) -> dict[str, CapabilityDefinition]:
    data = load_capability_catalog(root)
    definitions: dict[str, CapabilityDefinition] = {}
    sections = [("commands", False)]
    if include_internal:
        sections.append(("internal_commands", True))
    for section, internal in sections:
        for name, row in (data.get(section, {}) or {}).items():
            definitions[name] = CapabilityDefinition(
                name=name,
                handler=row["handler"],
                cli_command=row.get("cli_command"),
                writes=tuple(row.get("writes", []) or []),
                invariants=tuple(row.get("invariants", []) or []),
                internal=internal,
            )
    return definitions


def query_definitions(root: Path) -> dict[str, QueryDefinition]:
    data = load_capability_catalog(root)
    return {
        name: QueryDefinition(
            name=name,
            handler=row["handler"],
            result=row["result"].strip(),
            schema=str(row["schema"]).strip() if row.get("schema") else None,
            invariants=tuple(row.get("invariants", []) or []),
        )
        for name, row in (data.get("queries", {}) or {}).items()
    }


def domain_capability_definitions(root: Path) -> dict[str, DomainCapabilityDefinition]:
    data = load_capability_catalog(root)
    return {
        name: DomainCapabilityDefinition(
            name=name,
            writes=_string_list(
                row.get("writes"), label=f"domain capability {name} writes", required=True
            ),
            invariants=_string_list(
                row.get("invariants"), label=f"domain capability {name} invariants"
            ),
            allowed_fields=_string_list(
                row.get("allowed_fields"),
                label=f"domain capability {name} allowed_fields",
            ),
        )
        for name, row in (data.get("domain_capabilities", {}) or {}).items()
    }
