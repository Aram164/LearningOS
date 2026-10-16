"""AI action rows as projected into the manifest."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from learning_os.derive.garden import project_garden_entries
from learning_os.domain.ai_errors import AIActionError
from learning_os.domain.snapshot import Repo
from learning_os.store.ai_actions.storage import FilesystemAIActionRepository
from learning_os.store.loader import load_repo

from .registry import (
    DEFAULT_ADAPTERS,
    ActionRegistry,
    AdapterDefinition,
    AdapterRegistry,
)


def _projection(*, garden_entries: list[dict[str, Any]], available: list[dict[str, Any]],
                adapters: list[dict[str, Any]], requests: list[dict[str, Any]]) -> dict[str, Any]:
    """The one place the manifest's AI shape is defined."""
    return {
        "garden_entries": garden_entries,
        "ai_actions": {
            "contract_version": 1,
            "available": available,
            "provider_adapters": adapters,
            "requests": requests,
        },
    }


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
