"""Completed migrations are evidence, never standing writers for future formats."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from learning_os.store.contracts.capability_catalog import (
    domain_capability_definitions,
)
from learning_os.store.contracts.migration_lifecycle import (
    MigrationLifecycleError,
    retired_migration,
)
from learning_os.store.fingerprint import canonical_fingerprint


def test_pre_contract_fixture_can_replay_a_pre_contract_migration(tmp_path: Path):
    assert retired_migration(
        tmp_path,
        "curriculum-v2",
        supported_through=0,
    ) is None


def test_advanced_contract_retires_an_old_migration(tmp_path: Path):
    contract = tmp_path / "system/contracts/data-contract.yaml"
    contract.parent.mkdir(parents=True)
    contract.write_text(yaml.safe_dump({"contract_version": 11}), encoding="utf-8")
    retired = retired_migration(
        tmp_path,
        "standardize-plan-template-v10",
        supported_through=10,
    )
    assert retired is not None
    assert "declares v11" in retired.message()


def test_unreadable_contract_never_enables_migration_replay(tmp_path: Path):
    contract = tmp_path / "system/contracts/data-contract.yaml"
    contract.parent.mkdir(parents=True)
    contract.write_text("contract_version: [broken\n", encoding="utf-8")
    with pytest.raises(MigrationLifecycleError):
        retired_migration(tmp_path, "anything", supported_through=99)


@pytest.mark.full_repo
@pytest.mark.parametrize(
    "command",
    [
        ["tools/migrations/curriculum_v2.py", "--apply", "--root", "."],
        ["tools/migrations/route_identity_v13.py", "--apply", "--root", "."],
    ],
)
def test_completed_migration_refuses_live_apply_without_writes(
    repo_root: Path,
    command: list[str],
):
    before = canonical_fingerprint(repo_root)
    result = subprocess.run(
        [sys.executable, *command],
        cwd=repo_root,
        text=True,
        capture_output=True,
        timeout=30,
    )
    assert result.returncode == 2, result.stderr or result.stdout
    assert "is retired" in result.stdout
    assert canonical_fingerprint(repo_root) == before


@pytest.mark.parametrize(
    ("capability", "supported_through"),
    [
        ("migration.projects-to-modules-v62", 62),
        ("migration.python-topic-sessions-v63", 63),
    ],
)
def test_retired_migration_capability_replay_is_refused_as_retired(
    repo_root: Path, capability: str, supported_through: int,
):
    """A10: an exact replay names a retired migration, never the ledger.

    The two domain capabilities were deleted with their programs (rev3
    Group 9). The catalogue no longer declares them, and the lifecycle
    guard still classifies each id as retired on the live contract, so a
    replay request is refused as a retired migration instead of being
    answered from committed receipts.
    """
    assert capability not in domain_capability_definitions(repo_root)
    retired = retired_migration(
        repo_root, capability, supported_through=supported_through)
    assert retired is not None
    assert "retired" in retired.message()
