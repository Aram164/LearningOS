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
    from learning_os.app.ai_actions.service import AIActionService as AIActionService

_EXPORTS = {
    "AIActionService": (".service", "AIActionService"),
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
