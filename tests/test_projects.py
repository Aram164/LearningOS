from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.full_repo


@pytest.mark.parametrize("kind,status,compatibility,expected", [
    ("academic", "enrolled", False, True),
    ("project", "active", False, True),
    ("project", "planned", False, True),
    ("project", "completed", False, False),
    ("project", "archived", False, False),
    ("project", "dropped", False, False),
    ("project", "active", True, False),
    ("boundary", "active", False, False),
    ("skill", "active", False, False),
])
def test_ordinary_module_listing_preserves_its_exclusions(kind, status, compatibility, expected):
    from learning_os.derive.semesters import is_listed
    assert is_listed({"kind": kind, "status": status, "compatibility_only": compatibility}) is expected


def test_bachelor_thesis_is_an_ordinary_module(real_manifest):
    assert real_manifest["projects"] == []
    assert real_manifest["project_relationships"] == []
    module = next(row for row in real_manifest["modules"] if row["id"] == "module-project-bachelor-thesis")
    assert module["kind"] == "project" and module["area_id"] == "program-bachelors"
    assert real_manifest["project_aliases"]["project-bachelor-thesis"] == module["id"]
    assert module["unit_order"] == ["unit-thesis-landscape", "unit-thesis-experiments"]
    assert all(not row.get("project_ids") for row in real_manifest["units"])


def test_project_cli_resolves_to_the_canonical_module(repo_root: Path):
    for identity in ["project-bachelor-thesis", "module-project-bachelor-thesis"]:
        result = subprocess.run(
            [sys.executable, str(repo_root / "tools/los.py"), "inspect", identity],
            cwd=repo_root, text=True, capture_output=True, check=True,
        )
        payload = json.loads(result.stdout)
        assert payload["id"] == "module-project-bachelor-thesis"
        assert payload.get("resolved_from") == (identity if identity.startswith("project-") else None)


def test_project_migration_is_retired_on_current_contract(repo_root: Path):
    result = subprocess.run(
        [sys.executable, str(repo_root / "tools/migrations/projects_v1.py"), "--apply", "--root", str(repo_root)],
        cwd=repo_root, text=True, capture_output=True,
    )
    assert result.returncode == 2
    assert "migration projects-v1 is retired" in result.stdout
