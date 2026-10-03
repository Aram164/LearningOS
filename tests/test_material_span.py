"""Bounded source spans report observed bytes and explicit unavailability."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml
from gateway_helpers import run_v2_capability
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


def test_markdown_span_reports_physical_lines_of_displayed_excerpt(mini_repo: Path):
    add_curriculum(mini_repo)
    _add_material_overview(mini_repo)
    source_path = mini_repo / "sources/sources.yaml"
    sources = yaml.safe_load(source_path.read_text(encoding="utf-8"))
    sources["sources"][0]["material"] = "material://demo"
    write_yaml(source_path, sources)
    map_path = mini_repo / "curriculum/modules/module-demo/source-map.yaml"
    source_map = yaml.safe_load(map_path.read_text(encoding="utf-8"))
    source_map["sources"][0]["unit_routes"][0]["locator"] = "lecture-01.md"
    write_yaml(map_path, source_map)
    material = mini_repo.parent / "materials/demo/lecture-01.md"
    material.parent.mkdir(parents=True, exist_ok=True)
    material.write_text("# Section 1\n\nFirst point\nSecond point\n", encoding="utf-8")

    result = run_los(mini_repo, "material-span", "unit-demo-l01", _route(mini_repo),
                     "--extract")
    assert result.returncode == 0, result.stderr
    span = json.loads(result.stdout)["spans"][0]
    assert span["inspected_range_unit"] == "line"
    assert span["inspected_range"] == {"start": 1, "end": 4}


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
    assert "Open the URL explicitly" in data["next_action"]
    assert "register an authorized local copy" in data["next_action"]
    assert "make inventory" in data["next_action"]
    assert f"material-span unit-demo-l01 {_route(mini_repo)} --extract" in data["next_action"]


def test_out_of_range_pdf_locator_names_the_actual_problem(tmp_path: Path):
    material = tmp_path / "one-page.pdf"
    write_minimal_pdf(material, ["One page only"])
    with pytest.raises(SliceResolutionError, match="outside this 1-page file"):
        _read_pdf_part("route-one", "material://demo/one-page.pdf", material, "PDF pp. 8-9")


def _placement_setup(root: Path) -> str:
    add_curriculum(root)
    _add_material_overview(root)
    source_path = root / "sources/sources.yaml"
    sources = yaml.safe_load(source_path.read_text(encoding="utf-8"))
    sources["sources"][0]["material"] = "material://demo"
    write_yaml(source_path, sources)
    source_map_path = root / "curriculum/modules/module-demo/source-map.yaml"
    source_map = yaml.safe_load(source_map_path.read_text(encoding="utf-8"))
    route_id = _route(root)
    source_map["sources"][0]["unit_routes"][0].update(
        id=route_id, locator="All exercise sheets, topic matched")
    write_yaml(source_map_path, source_map)
    study_path = root / "curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml"
    study_map = yaml.safe_load(study_path.read_text(encoding="utf-8"))
    study_map["stages"][0]["resources"] = [
        {"route_id": route_id, "source_id": "source-demo-book", "kind": "read",
         "label": name, "vault_path": f"material://demo/{name}.pdf",
         "locator": f"{name}.pdf, PDF p. 2"}
        for name in ("first", "second")]
    write_yaml(study_path, study_map)
    for name in ("first", "second"):
        write_minimal_pdf(root.parent / f"materials/demo/{name}.pdf",
                          [f"{name} outside the selected span", f"{name} exact exercise"])
    return route_id


def test_stage_span_reads_the_exact_placement_and_not_its_broad_parent(mini_repo):
    route_id = _placement_setup(mini_repo)
    before = {path: path.read_bytes() for path in mini_repo.rglob("*") if path.is_file()}
    parent = run_los(mini_repo, "material-span", "unit-demo-l01", route_id, "--extract")
    assert json.loads(parent.stdout)["availability"] == "unavailable"
    for index, name in enumerate(("first", "second")):
        result = run_los(mini_repo, "material-span", "unit-demo-l01", route_id,
                         "--stage", "stage-demo", "--resource-index", str(index), "--extract")
        assert result.returncode == 0, result.stderr + result.stdout
        data = json.loads(result.stdout)
        assert data["availability"] == "local-observed"
        assert data["route_id"] == route_id
        assert data["locator"] == f"{name}.pdf, PDF p. 2"
        span, = data["spans"]
        assert span["material_uri"] == f"material://demo/{name}.pdf"
        assert span["pages"] == [2]
        assert f"{name} exact exercise" in span["excerpt"]
        assert "outside the selected span" not in span["excerpt"]
    assert before == {path: path.read_bytes() for path in mini_repo.rglob("*") if path.is_file()}


@pytest.mark.parametrize("flags", [
    ["--stage", "stage-demo"], ["--resource-index", "0"],
    ["--stage", "stage-ghost", "--resource-index", "0"],
    ["--stage", "stage-demo", "--resource-index", "-1"],
    ["--stage", "stage-demo", "--resource-index", "2"],
])
def test_stage_span_refuses_incomplete_or_wrong_placement_identity(mini_repo, flags):
    route_id = _placement_setup(mini_repo)
    result = run_los(mini_repo, "material-span", "unit-demo-l01", route_id, *flags, "--extract")
    assert result.returncode == 2
    assert "Traceback" not in result.stderr
    assert "los: error: unrecognized arguments" not in result.stderr


def test_stage_span_refuses_a_resource_bound_to_another_route(mini_repo):
    route_id = _placement_setup(mini_repo)
    study_path = mini_repo / "curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml"
    study_map = yaml.safe_load(study_path.read_text(encoding="utf-8"))
    study_map["stages"][0]["resources"][0]["route_id"] = "route-" + "f" * 24
    write_yaml(study_path, study_map)
    result = run_los(mini_repo, "material-span", "unit-demo-l01", route_id,
                     "--stage", "stage-demo", "--resource-index", "0", "--extract")
    assert result.returncode == 2
    assert "placement" in result.stderr


def test_stage_span_supports_compact_references_and_refuses_a_stale_snapshot(mini_repo):
    route_id = _placement_setup(mini_repo)
    study_path = mini_repo / "curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml"
    study_map = yaml.safe_load(study_path.read_text(encoding="utf-8"))
    resource = study_map["stages"][0]["resources"][0]
    resource.pop("source_id")
    resource.pop("route_id")
    resource["material_ref"] = {"route_id": route_id, "inherit": ["source_id"]}
    write_yaml(study_path, study_map)
    args = ("material-span", "unit-demo-l01", route_id, "--stage", "stage-demo",
            "--resource-index", "0", "--extract")
    result = run_los(mini_repo, *args)
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["spans"][0]["material_uri"] == "material://demo/first.pdf"
    resource["locator"] = "first.pdf, PDF p. 1"
    write_yaml(study_path, study_map)
    stale = run_los(mini_repo, *args, "--expected-snapshot", data["snapshot_id"])
    assert stale.returncode == 3


def test_stage_span_refuses_a_source_mismatch(mini_repo):
    route_id = _placement_setup(mini_repo)
    study_path = mini_repo / "curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml"
    study_map = yaml.safe_load(study_path.read_text(encoding="utf-8"))
    study_map["stages"][0]["resources"][0]["source_id"] = "source-other"
    write_yaml(study_path, study_map)
    result = run_los(mini_repo, "material-span", "unit-demo-l01", route_id,
                     "--stage", "stage-demo", "--resource-index", "0", "--extract")
    assert result.returncode == 2
    assert "placement source" in result.stderr


def test_span_binding_round_trips_through_prepare(mini_repo: Path, tmp_path: Path):
    """F8: each span carries a ready binding the draft accepts unchanged."""
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
    span, = data["spans"]
    binding = span["binding"]
    assert set(binding) == {"resolution", "source_id", "material",
                            "recorded_source_digest", "live_source_digest"}
    assert binding["resolution"] == "resolved"
    assert binding["source_id"] == data["source_id"]
    assert binding["material"] == "demo/lecture-01.pdf"
    assert binding["recorded_source_digest"] == binding["live_source_digest"]
    assert binding["live_source_digest"] == span["file_sha256"].removeprefix("sha256:")
    note_id = "note-analysis-span-roundtrip"
    drafts = {"notes": [{
        "id": note_id, "title": "Span round trip",
        "path": f"knowledge/notes/mathematics/{note_id}.md",
        "binding": {**binding, "inspected_range": {"start": 1, "end": 1}},
        "body": "Analysis of the spanned page.\n",
    }]}
    drafts_file = tmp_path / "drafts-span.json"
    drafts_file.write_text(json.dumps(drafts), encoding="utf-8")
    out = tmp_path / "staging-span"
    prepared = run_los(mini_repo, "note-analysis-prepare",
                       "--drafts", str(drafts_file), "--out", str(out))
    assert prepared.returncode == 0, prepared.stderr
    envelope = json.loads((out / "envelope.json").read_text(encoding="utf-8"))
    submitted = run_v2_capability(mini_repo, envelope)
    assert submitted.returncode == 0, submitted.stdout + submitted.stderr
    stored = load_repo(mini_repo).notes[note_id].meta["material_analysis"]
    assert stored["material"] == "demo/lecture-01.pdf"
    assert stored["recorded_source_digest"] == binding["recorded_source_digest"]
