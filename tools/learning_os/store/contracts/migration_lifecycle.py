"""Lifecycle guard for one-time stored-record migrations.

A completed migration is executable history, not a standing writer for every
future record shape.  Replaying it after the data contract has advanced can
silently re-introduce fields, defaults, and ownership assumptions that later
contracts deliberately retired.  A migration therefore declares the last data
contract generation it understands and refuses to apply beyond that boundary.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


class MigrationLifecycleError(RuntimeError):
    """The data-contract declaration cannot safely govern migration replay."""


@dataclass(frozen=True)
class RetiredMigration:
    migration_id: str
    supported_through: int
    current_contract: int

    def message(self) -> str:
        return (
            f"migration {self.migration_id} is retired: it understands data-contract "
            f"v{self.supported_through}, while this repository declares v{self.current_contract}. "
            "Write a new migration for the current contract instead of replaying old assumptions."
        )


def declared_data_contract(root: Path) -> int | None:
    """Return the repository's declared stored-record generation, if present."""
    path = root / "system" / "contracts" / "data-contract.yaml"
    if not path.is_file():
        return None
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError) as exc:
        raise MigrationLifecycleError(f"cannot read data contract at {path}: {exc}") from exc
    value = data.get("contract_version") if isinstance(data, dict) else None
    if not isinstance(value, int) or value < 0:
        raise MigrationLifecycleError(
            f"data contract at {path} has no non-negative integer contract_version"
        )
    return value


def retired_migration(
    root: Path,
    migration_id: str,
    *,
    supported_through: int,
) -> RetiredMigration | None:
    """Describe a retired migration, or return ``None`` when replay is valid.

    A pre-contract fixture has no declaration and remains replayable.  This is
    what lets the historical program prove it can still migrate the historical
    input without giving it authority over today's live repository.
    """
    current = declared_data_contract(root)
    if current is None or current <= supported_through:
        return None
    return RetiredMigration(migration_id, supported_through, current)


def refuse_retired_apply(retired: RetiredMigration | None, *, apply: bool) -> bool:
    """Print the lifecycle decision and return whether the caller must stop."""
    if retired is None:
        return False
    print(retired.message())
    if not apply:
        print("dry-run: 0 action(s); historical migration is already superseded")
    return True
