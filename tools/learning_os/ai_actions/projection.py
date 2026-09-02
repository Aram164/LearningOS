"""AI action rows as projected into the manifest."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from learning_os.garden import project_garden_entries
from learning_os.loader import Repo, load_repo

from .errors import AIActionError
from .registry import (
    DEFAULT_ADAPTERS,
    ActionRegistry,
    AdapterDefinition,
    AdapterRegistry,
)
from .storage import FilesystemAIActionRepository
from .support import _projection


def _empty_projection() -> dict[str, Any]:
    return _projection(
        garden_entries=[],
        available=[],
        requests=[],
        adapters=[AdapterDefinition.from_mapping(dict(DEFAULT_ADAPTERS[0])).project()],
    )


def project_ai_actions(repo: Repo) -> dict[str, Any]:
    """Project optional AI state from an already loaded canonical snapshot."""
    root = repo.root
    try:
        contracts = root / "system" / "contracts"
        repository = FilesystemAIActionRepository(root)
        return _projection(
            garden_entries=project_garden_entries(repo),
            available=[
                action.project()
                for action in ActionRegistry(contracts / "ai-actions").list()
            ],
            adapters=[
                adapter.project()
                for adapter in AdapterRegistry(
                    contracts / "ai-adapters.yaml"
                ).list()
            ],
            requests=repository.request_projections(),
        )
    except (OSError, ValueError, yaml.YAMLError, AIActionError):
        return _empty_projection()


def manifest_ai_projection(root: Path) -> dict[str, Any]:
    """Compatibility wrapper for callers that do not already hold a ``Repo``."""
    try:
        return project_ai_actions(load_repo(root))
    except (OSError, ValueError, yaml.YAMLError, AIActionError):
        return _empty_projection()
