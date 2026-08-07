"""AI action rows as projected into the manifest."""

from __future__ import annotations

import yaml
from pathlib import Path
from typing import Any
from .errors import AIActionError
from .registry import DEFAULT_ADAPTERS, AdapterDefinition
from .service import AIActionService
from .support import _projection

def manifest_ai_projection(root: Path) -> dict[str, Any]:
    """Best-effort additive projection; a missing optional subsystem stays empty."""
    try:
        return AIActionService(root).manifest_projection()
    except (OSError, ValueError, yaml.YAMLError, AIActionError):
        return _projection(
            garden_entries=[], available=[], requests=[],
            adapters=[AdapterDefinition.from_mapping(dict(DEFAULT_ADAPTERS[0])).project()],
        )
