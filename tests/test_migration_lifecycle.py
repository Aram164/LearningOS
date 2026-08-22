"""Completed migrations are evidence, never standing writers for future formats."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from learning_os.contracts.migration_lifecycle import (
    MigrationLifecycleError,
    retired_migration,
)
from learning_os.fingerprint import canonical_fingerprint


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
        ["tools/migrations/library_taxonomy_v1.py", "--apply"],
        ["tools/migrations/registry_partition_v1.py", "--apply"],
        ["tools/migrations/projects_v1.py", "--apply", "--root", "."],
        ["tools/migrations/standardize_plan_template_v10.py", "--apply", "--root", "."],
        [
            "tools/migrations/standardize_job_plans_v1.py",
            "--apply",
            "--job-root",
            "/path-that-must-never-be-read",
        ],
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
