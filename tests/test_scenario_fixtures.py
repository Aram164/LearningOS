"""The rich_world scenario fixture builds, validates and is deterministic."""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

import materials_manifest
import pypdf
import pytest
import yaml
from conftest import build_mini_repo
from scenario_fixtures import INITIAL_WARNING_SIGNATURES, rich_world

from learning_os.app.handlers.routes import compaction_plan
from learning_os.derive.learning_runtime import collect_requirements
from learning_os.derive.semantics.lineage import load_ledger
from learning_os.domain.material_inventory import render_manifest
from learning_os.domain.material_refs import compact_map, expand_map, unit_routes
from learning_os.store.loader import load_repo
from learning_os.store.materials.resolution import (
    material_location,
    resolve_route_material_files,
)
from learning_os.store.warning_baseline import collect, load_baseline

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
    assert any(stage.get("notes_path")
               and (root / stage["notes_path"]).is_file()
               and (root / stage["notes_path"]).stat().st_size > 0
               for stage in repo.learning_paths["path-demo"].data["stages"])
    assert any(stage.get("id") == "stage-demo-path-next"
               and not stage.get("notes_path")
               for stage in repo.learning_paths["path-demo"].data["stages"])
    assert repo.learning_paths["path-demo"].data["current_stage"] == "stage-demo-path"
    assert [req["id"] for req in collect_requirements(repo)] == ["req-demo-l01-demo"]
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
    # Amendment (y) item 1(a): the main unit's route carries its migrated
    # id, and the unit selection binds the same id.
    routes = repo.module_source_maps["module-demo"]["sources"][0]["unit_routes"]
    main_route = next(route for route in routes
                      if route["unit_id"] == "unit-demo-l01")
    assert main_route["id"].startswith("route-")
    assert (repo.units["unit-demo-l01"].data["source_selections"][0]
            ["route_id"] == main_route["id"])
    # Amendment (y) item 1(b): the legacy unit's route has no id.
    assert "unit-demo-l02" in repo.units
    legacy_route = next(route for route in routes
                        if route["unit_id"] == "unit-demo-l02")
    assert "id" not in legacy_route
    assert repo.modules["module-demo"]["unit_order"] == [
        "unit-demo-l01", "unit-demo-l02"]
    # Amendment (y) item 1(c): a second active ability.
    assert "ability-demo-variance" in repo.abilities
    # Amendment (y) item 1(d): a route-covers claim with its receipt.
    assert any(record.claim_kind == "route-covers"
               for record in load_ledger(root).values())
    assert (root / "operations/transactions"
            / "transaction-20200102-000000-001.yaml").is_file()
    # Amendment (z) item 2: the l01 route locator resolves to one PDF of
    # at least 24 pages of distinct extractable text.
    (l01_route,) = unit_routes(repo.module_source_maps["module-demo"],
                               "module-demo", "unit-demo-l01")
    resolved = resolve_route_material_files(repo, l01_route)
    assert len(resolved) == 1
    assert resolved[0].path.is_file() and not resolved[0].path.is_symlink()
    pages = pypdf.PdfReader(str(resolved[0].path)).pages
    assert len(pages) >= 24
    texts = [(page.extract_text() or "").strip() for page in pages]
    assert all(texts) and len(set(texts)) == len(texts)
    # Amendment (ag) item 1: a schema-valid shelf catalogue, never the
    # invalid `id` key the repair dropped.
    shelf = yaml.safe_load(
        (root / "sources/collections/shelf.yaml").read_text(encoding="utf-8"))
    assert shelf["title"] == "Scenario shelf"
    assert shelf["entries"] == [
        {"source": "source-demo-book", "group": "Demo",
         "why": "The main demo reading."}]
    assert "id" not in shelf
    # Amendment (ag) item 1: coverage-audit evidence with all markers.
    audit = (root / "work/active/workspace-demo/outputs"
             / "demo-coverage-audit.md").read_text(encoding="utf-8")
    assert "## Local" in audit
    assert "## Linked" in audit
    assert "## Completeness" in audit
    # Amendment (ag) item 1: readable unbound-source material; nope.pdf
    # stays absent.
    book_bytes = (root.parent / "materials/source-demo-book"
                  / "book.pdf").read_bytes()
    attached = (root.parent / "materials/source-scenario-bare/attached.pdf")
    assert attached.is_file() and attached.read_bytes() == book_bytes
    assert not (root.parent / "materials/source-scenario-bare"
                / "nope.pdf").exists()
    # Amendment (ag) item 1: the exact generated inventory.
    manifest_text = (root / "records/materials-manifest.yaml").read_text(
        encoding="utf-8")
    expected_manifest = materials_manifest.build(root.parent / "materials")
    expected_manifest["captured"] = "2026-09-20"
    assert manifest_text == render_manifest(expected_manifest)
    # Amendment (ag) item 1: the route mirror on stage-demo, after the
    # existing resources, spelling every route material field.
    study_map = repo.study_maps["study-map-demo-l01"]
    assert [res.get("id") for res in
            study_map.data["stages"][0]["resources"][:3]] == [
        "resource-demo-book-ch01", "resource-demo-book-appendix", None]
    mirror = study_map.data["stages"][0]["resources"][-1]
    assert mirror["id"] == "resource-demo-route-mirror"
    assert mirror["kind"] == "read"
    assert mirror["source_id"] == "source-demo-book"
    assert mirror["label"] == l01_route["title"]
    assert mirror["locator"] == l01_route["locator"]
    assert mirror["angle"] == l01_route["angle"]
    # Amendment (ag) item 1: a nonempty, lossless compaction plan.
    writes, _artifacts, detail = compaction_plan(repo, "module-demo")
    assert writes
    assert detail["referenced_routes"] == 1
    raw = study_map.authored_data or study_map.data
    compact, _used = compact_map(
        raw, repo.module_source_maps["module-demo"],
        "module-demo", "unit-demo-l01")
    assert compact != raw
    assert expand_map(compact, repo.module_source_maps["module-demo"],
                      "module-demo", "unit-demo-l01") == study_map.data
    # Amendment (ag) item 1: the stored initial counter, uncollected.
    stored, baseline_data = load_baseline(root)
    assert stored == INITIAL_WARNING_SIGNATURES
    assert baseline_data["recorded"] == "2026-09-20"


def _tree_files(top: Path) -> dict[str, bytes]:
    return {path.relative_to(top).as_posix(): path.read_bytes()
            for path in sorted(top.rglob("*")) if path.is_file()}


def test_two_builds_are_byte_identical(tmp_path):
    first = _build(tmp_path / "first")
    second = _build(tmp_path / "second")
    assert _tree_files(first.parent) == _tree_files(second.parent)


def test_initial_warning_counter_is_independently_measured(tmp_path):
    # Amendment (ag) item 1: two complete builds are byte-identical
    # including every fixture file, and a fresh completed fixture
    # independently measures the stored counter with zero errors.
    first = _build(tmp_path / "first")
    second = _build(tmp_path / "second")
    assert _tree_files(first.parent) == _tree_files(second.parent)
    measured, errors = collect(first)
    assert errors == []
    assert measured == load_baseline(first)[0]
    assert measured == INITIAL_WARNING_SIGNATURES


def test_ids_name_the_world(tmp_path):
    root = build_mini_repo(tmp_path)
    ids = rich_world(root)
    assert ids["unit"] == "unit-demo-l01"
    assert ids["stage_pending"] == "stage-demo-pending"
