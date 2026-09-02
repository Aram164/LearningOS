"""Bounded AI actions with a lazy package facade.

Importing a read-only projection must not initialize the delivery service,
transaction engine, or generated-output package. Public names stay compatible
through PEP 562 lazy attributes while leaf modules remain independently usable.
"""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # Static dependency declaration for reachability/cycle analysis; runtime
    # access remains lazy through __getattr__ below.
    from .service import AIActionService as AIActionService

_EXPORTS = {
    "MAX_DELIVERY_BYTES": (".errors", "MAX_DELIVERY_BYTES"),
    "MAX_DELIVERY_ENTRIES": (".errors", "MAX_DELIVERY_ENTRIES"),
    "ActionNotFoundError": (".errors", "ActionNotFoundError"),
    "ActionPolicyError": (".errors", "ActionPolicyError"),
    "AIActionError": (".errors", "AIActionError"),
    "ConfidentialityError": (".errors", "ConfidentialityError"),
    "DeliveryValidationError": (".errors", "DeliveryValidationError"),
    "StaleDeliveryError": (".errors", "StaleDeliveryError"),
    "TargetNotFoundError": (".errors", "TargetNotFoundError"),
    "manifest_ai_projection": (".projection", "manifest_ai_projection"),
    "ActionDefinition": (".registry", "ActionDefinition"),
    "ActionRegistry": (".registry", "ActionRegistry"),
    "AdapterDefinition": (".registry", "AdapterDefinition"),
    "AdapterRegistry": (".registry", "AdapterRegistry"),
    "AIActionService": (".service", "AIActionService"),
    "FilesystemAIActionRepository": (
        ".storage",
        "FilesystemAIActionRepository",
    ),
    "parse_frontmatter_request_id": (
        ".support",
        "parse_frontmatter_request_id",
    ),
    "AIActionRequest": (".types", "AIActionRequest"),
    "ApplyDeliveryResult": (".types", "ApplyDeliveryResult"),
    "DeliveryRecord": (".types", "DeliveryRecord"),
    "DeliveryValidationResult": (".types", "DeliveryValidationResult"),
    "RequestStatus": (".types", "RequestStatus"),
}

__all__ = list(_EXPORTS)


def __getattr__(name: str):
    try:
        module_name, attribute = _EXPORTS[name]
    except KeyError as exc:  # pragma: no cover - Python's attribute protocol
        raise AttributeError(name) from exc
    value = getattr(import_module(module_name, __name__), attribute)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted({*globals(), *__all__})
