"""Bounded source spans report observed bytes and explicit unavailability."""

from __future__ import annotations

import copy
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

from learning_os.domain.material_refs import unit_routes
from learning_os.store.loader import load_repo
from learning_os.store.materials.slices import SliceResolutionError, _read_pdf_part


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


def _thirty_page_deck(root: Path) -> str:
    """A 30-page local deck whose relevant section sits on page 25."""
    add_curriculum(root)
    _add_material_overview(root)
    source_path = root / "sources/sources.yaml"
    sources = yaml.safe_load(source_path.read_text(encoding="utf-8"))
    sources["sources"][0]["material"] = "material://demo"
    write_yaml(source_path, sources)
    material = root.parent / "materials/demo/lecture-01.pdf"
    texts = [f"filler page {n}" for n in range(1, 31)]
    texts[24] = "TARGET-25 expectation example"
    write_minimal_pdf(material, texts)
    return _route(root)


def test_pages_flag_reads_past_the_default_twenty_page_bound(mini_repo: Path):
    route_id = _thirty_page_deck(mini_repo)
    bounded = run_los(mini_repo, "material-span", "unit-demo-l01",
                      route_id, "--extract")
    assert bounded.returncode == 0, bounded.stderr
    default_span = json.loads(bounded.stdout)["spans"][0]
    assert default_span["extraction"] == "truncated"
    assert default_span["pages"] == list(range(1, 21))
    assert "TARGET-25" not in default_span["excerpt"]
    explicit = run_los(mini_repo, "material-span", "unit-demo-l01",
                       route_id, "--extract", "--pages", "pdf pp. 21-26")
    assert explicit.returncode == 0, explicit.stderr
    span = json.loads(explicit.stdout)["spans"][0]
    assert span["extraction"] == "complete"
    assert span["pages"] == list(range(21, 27))
    assert span["page_total"] == 30
    assert "TARGET-25" in span["excerpt"]
    # The binding fields are identical to the default span's: same bytes,
    # same recorded digest, same canonical binding block.
    assert span["file_sha256"] == default_span["file_sha256"]
    assert span["binding"] == default_span["binding"]


def test_pages_flag_keeps_the_cap_and_the_out_of_range_refusal(mini_repo: Path):
    route_id = _thirty_page_deck(mini_repo)
    capped = run_los(mini_repo, "material-span", "unit-demo-l01",
                     route_id, "--extract", "--pages", "pp. 1-25")
    assert capped.returncode == 0, capped.stderr
    span = json.loads(capped.stdout)["spans"][0]
    assert span["extraction"] == "range-truncated"
    assert span["pages"] == list(range(1, 21))
    beyond = run_los(mini_repo, "material-span", "unit-demo-l01",
                     route_id, "--extract", "--pages", "pp. 31-40")
    assert beyond.returncode == 0, beyond.stderr
    span = json.loads(beyond.stdout)["spans"][0]
    assert span["extraction"] == "unreadable"
    assert "outside this 30-page file" in span["reason"]


def test_pages_flag_refuses_blank_and_unparseable_values(mini_repo: Path):
    route_id = _thirty_page_deck(mini_repo)
    for value in ("", "21-26"):
        refused = run_los(mini_repo, "material-span", "unit-demo-l01",
                          route_id, "--extract", "--pages", value)
        assert refused.returncode == 2, refused.stdout
        assert "--pages" in refused.stderr


def test_pages_digest_recheck_still_refuses_changed_bytes(mini_repo, monkeypatch):
    """A file swapped mid-call is refused on the --pages path too (in process:
    the re-check compares the entry digest against a fresh hash of the bytes)."""
    import argparse

    import learning_os.app.handlers.materials as materials_handler
    from learning_os.app.pipeline import run_cli

    route_id = _thirty_page_deck(mini_repo)
    real_sha256_file = materials_handler.sha256_file
    calls = {"n": 0}

    def flaky(path):
        calls["n"] += 1
        if calls["n"] >= 2:
            return "sha256:" + "ff" * 32
        return real_sha256_file(path)

    monkeypatch.setattr(materials_handler, "sha256_file", flaky)
    outcome = run_cli(mini_repo, "material.span", argparse.Namespace(
        root=str(mini_repo), unit_id="unit-demo-l01", route_id=route_id,
        stage_id=None, resource_index=None, extract=True,
        pages="pdf pp. 21-26", expected_snapshot=None))
    assert outcome.exit_code == 0, outcome.stderr
    span = json.loads(outcome.stdout)["spans"][0]
    assert span["extraction"] == "unreadable"
    assert "file changed during inspection" in span["reason"]


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


def _placement_parts(root: Path):
    """Direct-call fixtures for ``_placement_route`` sibling tests."""
    from learning_os.app.context import OpContext

    repo = load_repo(root)
    unit = repo.units["unit-demo-l01"]
    source_map = repo.module_source_maps[unit.module_id]
    routes = unit_routes(source_map, unit.module_id, unit.id)
    assert len(routes) == 1
    ctx = OpContext(root=root, operation="material.span",
                    channel="cli", invocation="query", gateway=None)
    return ctx, repo, unit, source_map, routes, routes[0]


def test_zero_matching_stage_is_a_typed_notfound(mini_repo):
    """SPEC (cq) 3: only the zero-stage branch is typed."""
    from learning_os.app.handlers._shared import map_for_unit as _map_for_unit
    from learning_os.app.handlers.materials import _placement_route
    from learning_os.domain import suggest as suggest_mod
    from learning_os.domain.failures import NotFound

    _placement_setup(mini_repo)
    ctx, repo, unit, source_map, routes, route = _placement_parts(mini_repo)
    study_map = _map_for_unit(repo, unit.id)
    expected_ids = [row["id"] for row in study_map.data.get("stages", [])
                    if isinstance(row, dict) and row.get("id")]
    assert expected_ids == ["stage-demo"]
    with pytest.raises(NotFound) as caught:
        _placement_route(ctx, repo, unit, source_map, routes, route,
                         {"stage_id": "stage-ghost", "resource_index": 0})
    exc = caught.value
    assert type(exc) is NotFound
    assert str(exc) == "placement is missing or ambiguous in this unit"
    assert exc.site == "material.span.unknown-placement"
    assert exc.reason == "NOT_FOUND"
    assert exc.suggestions == suggest_mod.suggestions(
        "stage-ghost", expected_ids)
    assert exc.suggestions == ["stage-demo"]
    assert exc.gateway_message is None
    assert exc.exit_code is None


@pytest.mark.parametrize("mutate", ["duplicate-stage", "negative-index",
                                    "index-past-end"])
def test_duplicate_stage_and_bad_index_stay_untyped(mini_repo, mutate):
    """SPEC (cq) 3: the sibling branches keep the plain refusal."""
    from learning_os.app.handlers._shared import map_for_unit as _map_for_unit
    from learning_os.app.handlers.materials import _placement_route
    from learning_os.domain.failures import WriteRefused

    _placement_setup(mini_repo)
    ctx, repo, unit, source_map, routes, route = _placement_parts(mini_repo)
    if mutate == "duplicate-stage":
        study_map = _map_for_unit(repo, unit.id)
        study_map.data["stages"].append(
            copy.deepcopy(study_map.data["stages"][0]))
        request = {"stage_id": "stage-demo", "resource_index": 0}
    elif mutate == "negative-index":
        request = {"stage_id": "stage-demo", "resource_index": -1}
    else:
        request = {"stage_id": "stage-demo", "resource_index": 99}
    with pytest.raises(WriteRefused) as caught:
        _placement_route(ctx, repo, unit, source_map, routes, route, request)
    exc = caught.value
    assert type(exc) is WriteRefused
    assert str(exc) == "placement is missing or ambiguous in this unit"
    assert exc.site == "material.span.unknown-placement"
    assert exc.reason is None
    assert not hasattr(exc, "suggestions")


def test_foreign_placement_and_source_mismatch_stay_distinct(mini_repo):
    """SPEC (cq) 3: the later sibling guards keep site and message."""
    from learning_os.app.handlers.materials import _placement_route
    from learning_os.domain.failures import WriteRefused

    _placement_setup(mini_repo)
    study_path = mini_repo / "curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml"
    study_map = yaml.safe_load(study_path.read_text(encoding="utf-8"))
    study_map["stages"][0]["resources"][0]["route_id"] = "route-" + "f" * 24
    write_yaml(study_path, study_map)
    ctx, repo, unit, source_map, routes, route = _placement_parts(mini_repo)
    with pytest.raises(WriteRefused) as caught:
        _placement_route(ctx, repo, unit, source_map, routes, route,
                         {"stage_id": "stage-demo", "resource_index": 0})
    exc = caught.value
    assert type(exc) is WriteRefused
    assert str(exc) == "placement is missing or does not belong to this route"
    assert exc.site == "material.span.placement-foreign"

    study_map["stages"][0]["resources"][0]["route_id"] = route["id"]
    study_map["stages"][0]["resources"][0]["source_id"] = "source-other"
    write_yaml(study_path, study_map)
    ctx, repo, unit, source_map, routes, route = _placement_parts(mini_repo)
    with pytest.raises(WriteRefused) as caught:
        _placement_route(ctx, repo, unit, source_map, routes, route,
                         {"stage_id": "stage-demo", "resource_index": 0})
    exc = caught.value
    assert type(exc) is WriteRefused
    assert str(exc) == "placement source does not match its route"
    assert exc.site == "material.span.placement-source-mismatch"


def test_zero_stage_cli_refusal_keeps_the_legacy_line_and_writes_nothing(mini_repo):
    """SPEC (cq) 3: the typed miss renders the legacy line; no write."""
    route_id = _placement_setup(mini_repo)
    before = {path: path.read_bytes() for path in mini_repo.rglob("*") if path.is_file()}
    result = run_los(mini_repo, "material-span", "unit-demo-l01", route_id,
                     "--stage", "stage-ghost", "--resource-index", "0")
    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == (
        "los: INVALID_REQUEST: placement is missing or ambiguous in this unit\n"
        "  did you mean: stage-demo\n")
    typed = run_los(mini_repo, "material-span", "unit-demo-l01", route_id,
                    "--stage", "stage-ghost", "--resource-index", "0", "--json")
    assert typed.returncode == 2
    assert typed.stdout == ""
    error = json.loads(typed.stderr)["error"]
    assert error["code"] == "INVALID_REQUEST"
    assert error["message"] == "placement is missing or ambiguous in this unit"
    assert error["retryable"] is False
    assert error["details"] == {"reason": "NOT_FOUND",
                                "suggestions": ["stage-demo"]}
    assert before == {path: path.read_bytes() for path in mini_repo.rglob("*") if path.is_file()}


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


def test_cut_off_pdf_extract_points_at_material_search(mini_repo: Path):
    route_id = _thirty_page_deck(mini_repo)
    result = run_los(mini_repo, "material-span", "unit-demo-l01",
                     route_id, "--extract")
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["spans"][0]["extraction"] == "truncated"
    hint = data["next_action"]
    assert hint is not None
    assert "This excerpt is cut off" in hint
    assert 'material-search --unit unit-demo-l01 "terms"' in hint
    assert f"material-span unit-demo-l01 {route_id}" in hint
    assert "UNIT_ID" not in hint


def test_located_pages_extract_carries_no_hint(mini_repo: Path):
    route_id = _thirty_page_deck(mini_repo)
    result = run_los(mini_repo, "material-span", "unit-demo-l01",
                     route_id, "--extract", "--pages", "pdf pp. 21-26")
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["spans"][0]["extraction"] == "complete"
    assert data["next_action"] is None


def test_short_pdf_extract_carries_no_hint(mini_repo: Path):
    add_curriculum(mini_repo)
    _add_material_overview(mini_repo)
    source_path = mini_repo / "sources/sources.yaml"
    sources = yaml.safe_load(source_path.read_text(encoding="utf-8"))
    sources["sources"][0]["material"] = "material://demo"
    write_yaml(source_path, sources)
    material = mini_repo.parent / "materials/demo/lecture-01.pdf"
    write_minimal_pdf(material, ["A worked expected value example"])
    result = run_los(mini_repo, "material-span", "unit-demo-l01",
                     _route(mini_repo), "--extract")
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["spans"][0]["extraction"] == "complete"
    assert data["next_action"] is None


def test_plain_text_extract_carries_no_hint(mini_repo: Path):
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
    data = json.loads(result.stdout)
    assert data["spans"][0]["format"] != "pdf"
    assert data["next_action"] is None


# ---- the PDF-only material form (Plan A step 2) -------------------------------


def _material_pdf(root: Path, relative: str, texts: list[str]) -> Path:
    path = root.parent / "materials" / relative
    write_minimal_pdf(path, texts)
    return path


def _material_span(root: Path, relative: str, *extra: str, pages: str = "pdf p. 2"):
    return run_los(root, "material-span", "--material", relative, "--pages", pages,
                   "--extract", *extra)


def _site(root: Path, req: dict) -> str:
    from learning_os.app.context import OpContext
    from learning_os.app.handlers.materials import material_span
    from learning_os.domain.failures import WriteRefused

    ctx = OpContext(root=root, operation="material.span", channel="cli",
                    invocation="query", gateway=None)
    with pytest.raises(WriteRefused) as caught:
        material_span(ctx, {"unit_id": None, "route_id": None, **req})
    return caught.value.site


def _validate_span(payload: dict) -> None:
    import jsonschema

    schema = json.loads((Path(__file__).resolve().parents[1]
                         / "system/schema/material-span.schema.json").read_text(encoding="utf-8"))
    jsonschema.validate(payload, schema)


def test_material_form_reads_an_unrouted_pdf_page(mini_repo: Path):
    import hashlib

    add_curriculum(mini_repo)
    path = _material_pdf(mini_repo, "_unsorted/review/notes.pdf",
                         ["cover page", "naive Bayes worked example", "appendix"])
    digest = "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
    result = _material_span(mini_repo, "_unsorted/review/notes.pdf",
                            "--file-sha256", digest)
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    _validate_span(data)
    assert (data["unit_id"], data["module_id"], data["route_id"]) == (None, None, None)
    assert data["source_id"] is None and data["bindings"] == [] and data["bindings_total"] == 0
    assert data["material"] == "_unsorted/review/notes.pdf"
    span = data["spans"][0]
    assert span["file_sha256"] == digest and span["extraction"] == "complete"
    assert span["pages"] == [2] and span["page_total"] == 3
    assert "naive Bayes worked example" in span["excerpt"]
    assert "cover page" not in span["excerpt"]
    assert span["binding"]["source_id"] is None
    # A bare hex pin is the same pin.
    bare = _material_span(mini_repo, "_unsorted/review/notes.pdf",
                          "--file-sha256", digest.removeprefix("sha256:"))
    assert bare.returncode == 0, bare.stderr


def test_material_form_keeps_the_page_and_excerpt_limits(mini_repo: Path):
    add_curriculum(mini_repo)
    _material_pdf(mini_repo, "_unsorted/long.pdf",
                  [f"page {n} " + "x" * 400 for n in range(1, 31)])
    result = _material_span(mini_repo, "_unsorted/long.pdf", pages="pdf pp. 1-30")
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    span = data["spans"][0]
    assert span["extraction"] == "range-truncated" and span["pages"] == list(range(1, 21))
    assert len(span["excerpt"]) == 6000 and span["excerpt_truncated"] is True
    assert "fewer --pages" in data["next_action"]
    beyond = json.loads(_material_span(mini_repo, "_unsorted/long.pdf",
                                       pages="pdf p. 31").stdout)["spans"][0]
    assert beyond["extraction"] == "unreadable"
    assert "outside this 30-page file" in beyond["reason"]


def test_material_form_names_the_routes_that_bind_the_file(mini_repo: Path):
    add_curriculum(mini_repo)
    _add_material_overview(mini_repo)
    source_path = mini_repo / "sources/sources.yaml"
    sources = yaml.safe_load(source_path.read_text(encoding="utf-8"))
    sources["sources"][0]["material"] = "material://demo"
    write_yaml(source_path, sources)
    _material_pdf(mini_repo, "demo/lecture-01.pdf", ["one", "two"])
    route_id = _route(mini_repo)
    data = json.loads(_material_span(mini_repo, "demo/lecture-01.pdf").stdout)
    assert data["bindings"] == [{"module": "module-demo", "unit": "unit-demo-l01",
                                 "route": route_id, "source_id": "source-demo-book"}]
    assert data["source_id"] == "source-demo-book"
    assert data["spans"][0]["binding"]["source_id"] == "source-demo-book"


@pytest.mark.parametrize("relative", [
    "/etc/notes.pdf", "../outside.pdf", "_unsorted/../_unsorted/notes.pdf",
    "_unsorted//notes.pdf", "./_unsorted/notes.pdf", "_unsorted\\notes.pdf",
    ".flat/source-demo-book/notes.pdf", "_unsorted/notes.txt",
])
def test_material_form_refuses_paths_outside_the_physical_tree(mini_repo, relative):
    add_curriculum(mini_repo)
    _material_pdf(mini_repo, "_unsorted/notes.pdf", ["a", "b"])
    result = _material_span(mini_repo, relative)
    assert result.returncode == 2, result.stdout
    assert result.stdout == ""
    assert _site(mini_repo, {"material": relative, "pages": "pdf p. 1",
                             "extract": True}) == "material.span.bad-material"


def test_material_form_refuses_links_below_the_root_but_not_a_linked_root(mini_repo, tmp_path):
    add_curriculum(mini_repo)
    _material_pdf(mini_repo, "_unsorted/notes.pdf", ["a", "naive Bayes"])
    materials = mini_repo.parent / "materials"
    (materials / "linked-dir").symlink_to(materials / "_unsorted", target_is_directory=True)
    (materials / "_unsorted" / "linked.pdf").symlink_to(materials / "_unsorted" / "notes.pdf")
    (materials / "_unsorted" / "folder.pdf").mkdir()
    for relative in ("linked-dir/notes.pdf", "_unsorted/linked.pdf", "_unsorted/folder.pdf"):
        assert _material_span(mini_repo, relative).returncode == 2, relative
        assert _site(mini_repo, {"material": relative, "pages": "pdf p. 1",
                                 "extract": True}) == "material.span.bad-material"
    assert _site(mini_repo, {"material": "_unsorted/absent.pdf", "pages": "pdf p. 1",
                             "extract": True}) == "material.span.material-missing"
    # A copied trial world reaches its materials through a link: the root is
    # resolved first, so reads below it still work (review D4).
    real = tmp_path / "real-materials"
    materials.rename(real)
    materials.symlink_to(real, target_is_directory=True)
    linked_root = _material_span(mini_repo, "_unsorted/notes.pdf")
    assert linked_root.returncode == 0, linked_root.stderr
    assert "naive Bayes" in json.loads(linked_root.stdout)["spans"][0]["excerpt"]


@pytest.mark.parametrize("req", [
    {"material": "_unsorted/notes.pdf", "pages": "pdf p. 1", "extract": True,
     "unit_id": "unit-demo-l01"},
    {"material": "_unsorted/notes.pdf", "pages": "pdf p. 1", "extract": True,
     "stage_id": "stage-demo", "resource_index": 0},
    {"material": "_unsorted/notes.pdf", "pages": "pdf p. 1", "extract": False},
    {"material": "_unsorted/notes.pdf", "pages": None, "extract": True},
    {"material": "_unsorted/notes.pdf", "pages": "21-26", "extract": True},
    {"material": "_unsorted/notes.pdf", "pages": "pdf p. 1", "extract": True,
     "file_sha256": "sha256:short"},
    {"unit_id": "unit-demo-l01"},
    {},
])
def test_material_span_refuses_mixed_or_incomplete_forms(mini_repo, req):
    add_curriculum(mini_repo)
    _material_pdf(mini_repo, "_unsorted/notes.pdf", ["a", "b"])
    assert _site(mini_repo, req) == "material.span.bad-form"


def test_a_stale_pin_refuses_changed_bytes_with_exit_3(mini_repo: Path):
    """A reference from an earlier search never reads bytes that changed since."""
    import hashlib

    add_curriculum(mini_repo)
    path = _material_pdf(mini_repo, "_unsorted/notes.pdf", ["a", "naive Bayes"])
    pinned = "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
    write_minimal_pdf(path, ["a", "replaced after the search"])
    stale = _material_span(mini_repo, "_unsorted/notes.pdf", "--file-sha256", pinned)
    assert stale.returncode == 3, stale.stdout
    assert stale.stdout == ""
    assert "changed since the reference was made" in stale.stderr
    assert _site(mini_repo, {"material": "_unsorted/notes.pdf", "pages": "pdf p. 2",
                             "extract": True, "file_sha256": pinned}) == "material.span.file-changed"


def test_route_form_pin_reads_a_single_file_route_and_refuses_a_changed_one(mini_repo):
    import hashlib

    route_id = _thirty_page_deck(mini_repo)
    path = mini_repo.parent / "materials/demo/lecture-01.pdf"
    pinned = "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
    plain = run_los(mini_repo, "material-span", "unit-demo-l01", route_id,
                    "--extract", "--pages", "pdf p. 25")
    pinned_run = run_los(mini_repo, "material-span", "unit-demo-l01", route_id,
                         "--extract", "--pages", "pdf p. 25", "--file-sha256", pinned)
    assert pinned_run.returncode == 0, pinned_run.stderr
    # The pin changes nothing about the answer; it only adds the refusal.
    assert json.loads(pinned_run.stdout) == json.loads(plain.stdout)
    wrong = run_los(mini_repo, "material-span", "unit-demo-l01", route_id,
                    "--extract", "--file-sha256", "sha256:" + "0" * 64)
    assert wrong.returncode == 3 and wrong.stdout == ""


def test_route_form_pin_refuses_a_route_without_exactly_one_local_file(mini_repo):
    add_curriculum(mini_repo)
    _add_material_overview(mini_repo)
    source_path = mini_repo / "sources/sources.yaml"
    sources = yaml.safe_load(source_path.read_text(encoding="utf-8"))
    sources["sources"][0].pop("material", None)
    sources["sources"][0]["url"] = "https://example.invalid/book"
    write_yaml(source_path, sources)
    route_id = _route(mini_repo)
    refused = run_los(mini_repo, "material-span", "unit-demo-l01", route_id,
                      "--extract", "--file-sha256", "sha256:" + "0" * 64)
    assert refused.returncode == 2 and "pins one file" in refused.stderr
    assert _site(mini_repo, {"unit_id": "unit-demo-l01", "route_id": route_id,
                             "extract": True,
                             "file_sha256": "sha256:" + "0" * 64}) == "material.span.bad-form"
