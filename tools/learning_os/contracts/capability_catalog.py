"""Loader and consistency checks for ``system/contracts/capabilities.yaml``."""

from __future__ import annotations

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
    for section in ("queries", "commands", "internal_commands"):
        rows = data.get(section, {}) or {}
        if not isinstance(rows, dict):
            raise CapabilityCatalogError(f"capability catalogue {section} must be a mapping")
        for name, row in rows.items():
            if not isinstance(name, str) or not isinstance(row, dict):
                raise CapabilityCatalogError(f"invalid capability declaration in {section}")
            if not isinstance(row.get("handler"), str) or not row["handler"].strip():
                raise CapabilityCatalogError(f"capability {name} has no handler")
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
