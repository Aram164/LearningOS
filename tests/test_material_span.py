"""Bounded source spans report observed bytes and explicit unavailability."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml
from repo_builders import (
    _add_material_overview,
    add_curriculum,
    run_los,
    write_minimal_pdf,
    write_yaml,
)

from learning_os.loader import load_repo
from learning_os.material_refs import unit_routes
from learning_os.material_slices import SliceResolutionError, _read_pdf_part


def _route(root: Path) -> str:
    repo = load_repo(root)
    routes = unit_routes(repo.module_source_maps["module-demo"],
                         "module-demo", "unit-demo-l01")
    assert len(routes) == 1
    return routes[0]["id"]


def test_local_span_is_observed_and_extraction_is_on_demand(mini_repo: Path):
    add_curriculum(mini_repo)
    _add_material_overview(mini_repo)
    source_path = mini_repo / "sources/sources.yaml"
    sources = yaml.safe_load(source_path.read_text(encoding="utf-8"))
    sources["sources"][0]["material"] = "material://demo"
    write_yaml(source_path, sources)
    material = mini_repo.parent / "materials/demo/lecture-01.pdf"
    write_minimal_pdf(material, ["A worked expected value example"])
    route_id = _route(mini_repo)
    brief = run_los(mini_repo, "material-span", "unit-demo-l01", route_id)
    assert brief.returncode == 0, brief.stderr
    data = json.loads(brief.stdout)
    assert data["availability"] == "local-observed"
    assert data["spans"][0]["file_sha256"].startswith("sha256:")
    assert data["spans"][0]["extraction"] == "not-requested"
    assert "excerpt" not in data["spans"][0]
    expanded = run_los(mini_repo, "material-span", "unit-demo-l01",
                       route_id, "--extract")
    assert expanded.returncode == 0, expanded.stderr
    span = json.loads(expanded.stdout)["spans"][0]
    assert span["extraction"] == "complete"
    assert "worked expected value" in span["excerpt"]
    assert span["file_sha256"] == data["spans"][0]["file_sha256"]


def test_remote_span_is_never_fetched_implicitly(mini_repo: Path):
    add_curriculum(mini_repo)
    _add_material_overview(mini_repo)
    source_path = mini_repo / "sources/sources.yaml"
    sources = yaml.safe_load(source_path.read_text(encoding="utf-8"))
    sources["sources"][0].pop("material", None)
    sources["sources"][0]["url"] = "https://example.invalid/book"
    write_yaml(source_path, sources)
    result = run_los(mini_repo, "material-span", "unit-demo-l01",
                     _route(mini_repo), "--extract")
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["availability"] == "remote-unobserved"
    assert data["spans"] == []
    assert data["url"] == "https://example.invalid/book"


def test_out_of_range_pdf_locator_names_the_actual_problem(tmp_path: Path):
    material = tmp_path / "one-page.pdf"
    write_minimal_pdf(material, ["One page only"])
    with pytest.raises(SliceResolutionError, match="outside this 1-page file"):
        _read_pdf_part("route-one", "material://demo/one-page.pdf", material, "PDF pp. 8-9")
