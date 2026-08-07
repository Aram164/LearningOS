"""Declared actions and provider adapters, loaded from contracts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
from .errors import ActionNotFoundError, ActionPolicyError
from .support import _read_yaml

@dataclass(frozen=True)
class ActionDefinition:
    id: str
    title: str
    description: str
    target_kinds: tuple[str, ...]
    interaction_mode: str
    approval_required: bool
    context_selection: str
    status: str
    supported_providers: tuple[str, ...]
    allowed_capabilities: tuple[str, ...]
    forbidden_capabilities: tuple[str, ...]
    confidentiality_policy: dict[str, Any]

    @classmethod
    def from_mapping(cls, value: dict[str, Any]) -> ActionDefinition:
        return cls(
            id=str(value["id"]),
            title=str(value["title"]),
            description=str(value.get("description", "")),
            target_kinds=tuple(str(v) for v in value.get("target_kinds", [])),
            interaction_mode=str(value.get("interaction_mode", "discussion")),
            approval_required=bool(value.get("approval_required", True)),
            context_selection=str(value.get("context_selection", "exact")),
            # Implementation status is contract data, not a literal in the
            # service: the registry stays independently updatable (feature
            # specification §27.18) while unbuilt actions still refuse cleanly.
            status=str(value.get("status", "planned")),
            supported_providers=tuple(str(v) for v in value.get("supported_providers", [])),
            allowed_capabilities=tuple(str(v) for v in value.get("allowed_capabilities", [])),
            forbidden_capabilities=tuple(str(v) for v in value.get("forbidden_capabilities", [])),
            confidentiality_policy=dict(value.get("confidentiality_policy", {}) or {}),
        )

    def project(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "target_kinds": list(self.target_kinds),
            "interaction_mode": self.interaction_mode,
            "status": self.status,
            "supported_providers": list(self.supported_providers),
        }


@dataclass(frozen=True)
class AdapterDefinition:
    """One provider adapter as declared by the contract, never by the UI."""

    id: str
    provider: str
    available: bool
    supported_modes: tuple[str, ...]
    supports_direct_delivery: bool
    supports_attachments: bool

    @classmethod
    def from_mapping(cls, value: dict[str, Any]) -> AdapterDefinition:
        return cls(
            id=str(value["id"]),
            provider=str(value.get("provider", value["id"])),
            available=bool(value.get("available", False)),
            supported_modes=tuple(str(v) for v in value.get("supported_modes", [])),
            supports_direct_delivery=bool(value.get("supports_direct_delivery", False)),
            supports_attachments=bool(value.get("supports_attachments", False)),
        )

    def project(self) -> dict[str, Any]:
        # ``id`` stays the *provider* name so existing manifest consumers keep
        # working; the adapter identity is additive alongside it.
        return {
            "id": self.provider,
            "adapter": self.id,
            "available": self.available,
            "supported_modes": list(self.supported_modes),
            "supports_direct_delivery": self.supports_direct_delivery,
        }


class AdapterRegistry:
    """Adapter availability is contract data read by the core.

    Before this existed the truth lived in a Python literal in the manifest
    projection while *enforcement* lived in the Obsidian UI, so the core would
    happily prepare a request naming a provider that has no adapter at all.
    """

    def __init__(self, path: Path):
        self.path = path

    def list(self) -> list[AdapterDefinition]:
        value = _read_yaml(self.path, {})
        rows = value.get("adapters") if isinstance(value, dict) else None
        if not isinstance(rows, list) or not rows:
            rows = list(DEFAULT_ADAPTERS)
        adapters = []
        for row in rows:
            if isinstance(row, dict) and row.get("id"):
                adapters.append(AdapterDefinition.from_mapping(row))
        return adapters or [AdapterDefinition.from_mapping(dict(DEFAULT_ADAPTERS[0]))]

    def resolve(self, provider: str) -> AdapterDefinition:
        """Map a requested provider onto the adapter that can actually serve it."""
        for adapter in self.list():
            if provider in (adapter.provider, adapter.id):
                if not adapter.available:
                    raise ActionPolicyError(
                        f"provider {provider} has no available adapter "
                        f"({adapter.id} is declared unavailable)"
                    )
                return adapter
        raise ActionPolicyError(f"no adapter is configured for provider {provider}")


class ActionRegistry:
    def __init__(self, root: Path):
        self.root = root

    def list(self) -> list[ActionDefinition]:
        if not self.root.is_dir():
            return []
        actions = []
        for path in sorted(self.root.glob("*.yaml")):
            value = _read_yaml(path, {})
            if isinstance(value, dict):
                actions.append(ActionDefinition.from_mapping(value))
        return actions

    def get(self, action_id: str) -> ActionDefinition:
        for action in self.list():
            if action.id == action_id:
                return action
        raise ActionNotFoundError(f"unknown AI action: {action_id}")
