from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from learning_os.genout import build_backlinks, build_manifest, stable_generated_at
from learning_os.loader import load_repo

pytestmark = pytest.mark.full_repo


def manifest(root: Path) -> dict:
    repo = load_repo(root)
    at = stable_generated_at(root)
    return build_manifest(repo, at, build_backlinks(repo, at))


def test_bachelor_thesis_is_a_first_class_project(repo_root: Path):
    data = manifest(repo_root)
    assert [row["id"] for row in data["projects"]] == ["project-bachelor-thesis"]
    assert "module-project-bachelor-thesis" not in {row["id"] for row in data["modules"]}
    assert data["project_aliases"]["module-project-bachelor-thesis"] == "project-bachelor-thesis"
    project = data["projects"][0]
    thesis_units = {row["id"]: row for row in data["units"] if row["id"].startswith("unit-thesis-")}
    assert thesis_units
    assert all(row.get("project_ids") == ["project-bachelor-thesis"] for row in thesis_units.values())
    assert project["structure"]["kind"] == "parallel"
    assert any(
        child.get("kind") == "step-map"
        for node in project["structure"]["nodes"]
        for child in node.get("children", [])
    )
    assert "%" not in json.dumps(project)
    assert len(data["project_relationships"]) == 3
    assert all(row.get("contribution") for row in data["project_relationships"])


def test_project_cli_resolves_compatibility_alias(repo_root: Path):
    result = subprocess.run(
        [sys.executable, str(repo_root / "tools/los.py"), "inspect", "module-project-bachelor-thesis"],
        cwd=repo_root, text=True, capture_output=True, check=True,
    )
    payload = json.loads(result.stdout)
    assert payload["id"] == "project-bachelor-thesis"
    assert payload["resolved_from"] == "module-project-bachelor-thesis"


def test_project_migration_is_retired_on_current_contract(repo_root: Path):
    result = subprocess.run(
        [sys.executable, str(repo_root / "tools/migrations/projects_v1.py"), "--apply", "--root", str(repo_root)],
        cwd=repo_root, text=True, capture_output=True,
    )
    assert result.returncode == 2
    assert "migration projects-v1 is retired" in result.stdout
