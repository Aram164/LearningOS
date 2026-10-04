"""The rich_world scenario fixture builds, validates and is deterministic."""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

import pytest
import yaml
from conftest import build_mini_repo
from scenario_fixtures import rich_world

from learning_os.loader import load_repo
from learning_os.materials_resolution import material_location

REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(autouse=True)
def _berlin_time(monkeypatch):
    """Pin TZ=Europe/Berlin in-process, restoring afterwards (SPEC §0)."""
    old = os.environ.get("TZ")
    monkeypatch.setenv("TZ", "Europe/Berlin")
    if hasattr(time, "tzset"):
        time.tzset()
    yield
    if old is None:
        os.environ.pop("TZ", None)
    else:
        os.environ["TZ"] = old
    if hasattr(time, "tzset"):
        time.tzset()


def _build(container: Path) -> Path:
    root = build_mini_repo(container)
    rich_world(root)
    return root


def test_rich_world_validates_with_zero_errors(tmp_path):
    root = _build(tmp_path)
    env = {**os.environ, "TZ": "Europe/Berlin"}
    proc = subprocess.run(
        [sys.executable, str(REPO_ROOT / "tools" / "validate.py"),
         "--root", str(root)],
        capture_output=True, text=True, timeout=300, env=env)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "0 error(s)" in proc.stdout


def test_every_family_is_present(tmp_path):
    root = _build(tmp_path)
    repo = load_repo(root)
    assert any(module.get("attempts")
               and (module.get("examination") or {}).get("sittings")
               for module in repo.modules.values())
    assert "unit-demo-l01" in repo.units
    assert {"pending", "active"} <= {
        stage.get("status") for study_map in repo.study_maps.values()
        for stage in study_map.data["stages"]}
    assert "source-demo-book" in repo.sources and any(
        route for source_map in repo.module_source_maps.values()
        for source in source_map.get("sources", [])
        for route in source.get("unit_routes", []))
    assert repo.notes["note-demo"].meta.get("role") == "synthesis" and \
        repo.notes["note-demo-analysis"].meta.get(
            "material_analysis", {}).get("resolution") == "resolved"
    assert "concept-expected-value" in repo.concepts and repo.relations
    assert {"workspace-demo", "workspace-second"} <= set(repo.workspaces)
    assert "path-demo" in repo.learning_paths
    assert (root / "work/inbox/note-drop.md").is_file() \
        and (root / "work/inbox/pack/one.md").is_file()
    assert len(repo.garden_notes) >= 1
    assert "project-demo" in repo.projects
    ledger = yaml.safe_load(
        (root / "operations/goal-ledger.yaml").read_text(encoding="utf-8"))
    assert set(ledger["decisions"]) == {"goal-demo-deferred", "goal-demo-rejected"}
    assert "ability-demo-derive" in repo.abilities and \
        (root / "work/active/workspace-demo/ability-observations.jsonl").is_file()
    assert (root / "operations/ai-actions/requests/ai-request-demo"
            / "request.yaml").is_file()
    assert material_location(
        repo, "material://source-demo-book/book.pdf")["material_exists"] is True


def _tree_files(top: Path) -> dict[str, bytes]:
    return {path.relative_to(top).as_posix(): path.read_bytes()
            for path in sorted(top.rglob("*")) if path.is_file()}


def test_two_builds_are_byte_identical(tmp_path):
    first = _build(tmp_path / "first")
    second = _build(tmp_path / "second")
    assert _tree_files(first.parent) == _tree_files(second.parent)


def test_ids_name_the_world(tmp_path):
    root = build_mini_repo(tmp_path)
    ids = rich_world(root)
    assert ids["unit"] == "unit-demo-l01"
    assert ids["stage_pending"] == "stage-demo-pending"
