"""Artifact revision-ledger reads shared by projection and transactions.

Revision lookup is a small read concern. Keeping it below the transaction
orchestrator lets generators and validators consume concurrency metadata
without importing the write engine.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

import yaml

from .errors import TransactionFailure
from .pathing import PathBoundaryError, read_text_inside


def revision_ledger_path(root: Path) -> Path:
    return root / "operations" / "transactions" / "revisions.yaml"


def load_revisions(root: Path) -> dict[str, int]:
    path = revision_ledger_path(root)
    if not path.exists() and not path.is_symlink():
        return {}
    try:
        # Keep the broad loading facade out of transaction startup; Python
        # initialises a package before one of its submodules.
        from .loading.yamlio import UniqueKeySafeLoader

        data = yaml.load(
            read_text_inside(root, path),
            Loader=UniqueKeySafeLoader,
        )
    except (OSError, PathBoundaryError, yaml.YAMLError) as exc:
        raise TransactionFailure(
            f"artifact revision ledger is unreadable: {path}: {exc}"
        ) from exc
    if not isinstance(data, dict):
        raise TransactionFailure("artifact revision ledger must be a mapping")
    if data.get("schema_version") != 1 \
            or data.get("type") != "artifact-revision-ledger":
        raise TransactionFailure(
            "artifact revision ledger has an unsupported contract"
        )
    rows = data.get("revisions")
    if not isinstance(rows, dict):
        raise TransactionFailure("artifact revision ledger revisions must be a mapping")
    revisions: dict[str, int] = {}
    for artifact, value in rows.items():
        if not isinstance(artifact, str) or not artifact.strip() \
                or isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise TransactionFailure(
                f"artifact revision ledger contains an invalid row: {artifact!r}"
            )
        revisions[artifact] = value
    return revisions


def artifact_revision(root: Path, artifact_id: str) -> int:
    return load_revisions(root).get(artifact_id, 0)


def dump_revisions(revisions: Mapping[str, int]) -> str:
    return yaml.safe_dump(
        {
            "schema_version": 1,
            "type": "artifact-revision-ledger",
            "revisions": dict(sorted(revisions.items())),
        },
        sort_keys=False,
        allow_unicode=True,
    )
