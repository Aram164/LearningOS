"""Bounded material slices for unit.compare-materials (Commit 1 test suite)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml
from repo_builders import add_curriculum, write_minimal_pdf, write_yaml

from learning_os import material_slices
from learning_os.ai_actions import AIActionService, UnresolvedMaterialError
from learning_os.loader import load_repo
from learning_os.material_slices import (
    MAX_SLICE_PAGES,
    SliceResolutionError,
    build_unit_slices,
    parse_locator_page_ranges,
)
from learning_os.material_synthesis import (
    current_unit_material_basis,
    validate_unit_material_synthesis,
)
from learning_os.materials_resolution import resolve_route_material_files


def _add_sliced_unit(root: Path, routes: list[dict], files: dict[str, list[str] | bytes]) -> None:
    add_curriculum(root)
    unit_path = root / "curriculum/modules/module-demo/units/unit-demo-l01/unit.yaml"
    unit = yaml.safe_load(unit_path.read_text(encoding="utf-8"))
    unit["knowledge_map"] = {
        "summary": "Expected value connects outcomes to probability weights.",
        "nodes": [
            {"id": "knowledge-demo-outcomes", "title": "Outcomes",
             "summary": "A variable maps outcomes to values."},
            {"id": "knowledge-demo-expectation", "title": "Expectation",
             "summary": "Expectation is a probability-weighted average."},
        ],
    }
    write_yaml(unit_path, unit)

    source_map_path = root / "curriculum/modules/module-demo/source-map.yaml"
    source_map = yaml.safe_load(source_map_path.read_text(encoding="utf-8"))
    source_map["sources"][0]["unit_routes"] = routes
    write_yaml(source_map_path, source_map)

    registry_path = root / "sources/sources.yaml"
    registry = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    registry["sources"][0]["material"] = "material://source-demo-book/"
    write_yaml(registry_path, registry)
    for rel, content in files.items():
        target = root.parent / "materials/source-demo-book" / rel
        if isinstance(content, list):
            write_minimal_pdf(target, content)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)


def _route(route_id: str, locator: str, scope: str = "current") -> dict:
    return {
        "id": route_id,
        "unit_id": "unit-demo-l01",
        "source_id": "source-demo-book",
        "title": f"Route {route_id}",
        "format": "book",
        "angle": "A synthetic angle.",
        "covers": ["knowledge-demo-expectation"],
        "depth": "derivation",
        "scope": scope,
        "locator": locator,
    }


def _basis(root: Path) -> dict:
    return current_unit_material_basis(root, "unit-demo-l01")


def _slices(root: Path, routes: list[dict]) -> list:
    return build_unit_slices(load_repo(root), routes, basis=_basis(root))


@pytest.mark.parametrize(("locator", "expected"), [
    ("book.pdf, pdf pp. 310-322", [(310, 322)]),
    ("UE5.pdf, slides 20-38", [(20, 38)]),
    ("Statistics_And_Data_Science.pdf, pp. 1 and 3, Aufgaben 1 and 3", [(1, 1), (3, 3)]),
    ("Physical PDF p. 132 (printed p. 127), Aufgabe 6.19(a-b) only", [(132, 132)]),
    ("Ch 5 the normal distribution, pdf pp. 74-75", [(74, 75)]),
    ("Official PDF, Ch 8, PDF pp. 313-332, and Ch 9, PDF pp. 333-372",
     [(313, 332), (333, 372)]),
    ("Leuphana-Uebungsbuch.pdf, pp. 11-16, Aufgabenblatt 2", [(11, 16)]),
    ("Maximum Likelihood, Clearly Explained (≈12 min each)", []),
    ("The CLT, Clearly Explained, 01:06-04:04 for both demos", []),
    ("08_normal_distribution.pdf, 38 slides", []),
    ("Lectures 4-5 (maximum likelihood estimation)", []),
    ("08_normal_distribution_no_notes.pdf", []),
])
def test_locator_page_ranges_parse_only_pdf_house_style(locator, expected):
    assert parse_locator_page_ranges(locator) == expected


def test_locator_page_ranges_rejects_non_strings():
    assert parse_locator_page_ranges(None) == []


def test_resolver_is_centralized_single_multi_and_garbage(mini_repo):
    _add_sliced_unit(mini_repo, [_route("route-demo-a", "lecture-01.pdf")],
                     {"lecture-01.pdf": ["page one"]})
    repo = load_repo(mini_repo)
    single = resolve_route_material_files(repo, _route("route-demo-a", "lecture-01.pdf"))
    assert [row.material_uri for row in single] == ["material://source-demo-book/lecture-01.pdf"]
    assert single[0].path.is_file()

    write_minimal_pdf(
        mini_repo.parent / "materials/source-demo-book/lecture-02.pdf", ["exercises"])
    multi = resolve_route_material_files(
        repo, _route("route-demo-a", "lecture-01.pdf, reviewed; lecture-02.pdf"))
    assert len(multi) == 2

    assert resolve_route_material_files(repo, _route("route-demo-a", "gone.pdf")) == []


def test_slice_truncates_long_pdf_and_records_total(mini_repo):
    pages = [f"content line {n}" for n in range(1, 21)]
    _add_sliced_unit(mini_repo, [_route("route-demo-long", "long.pdf")], {"long.pdf": pages})
    [(slice_, _)] = _slices(mini_repo, [_route("route-demo-long", "long.pdf")])
    (part,) = slice_.parts
    assert part.pages == tuple(range(1, MAX_SLICE_PAGES + 1))
    assert part.page_total == 20
    assert part.status == "truncated"
    assert "content line 1" in part.text
    assert "content line 20" not in part.text


def test_slice_prefers_locator_ranges(mini_repo):
    pages = [f"content line {n}" for n in range(1, 11)]
    locator = "book.pdf, pdf pp. 2-4"
    _add_sliced_unit(mini_repo, [_route("route-demo-ranged", locator)], {"book.pdf": pages})
    [(slice_, _)] = _slices(mini_repo, [_route("route-demo-ranged", locator)])
    (part,) = slice_.parts
    assert part.pages == (2, 3, 4)
    assert part.status == "complete"
    assert "content line 2" in part.text
    assert "content line 5" not in part.text


def test_slice_range_truncates_beyond_cap_with_status(mini_repo):
    pages = [f"content line {n}" for n in range(1, 31)]
    locator = "book.pdf, pdf pp. 1-30"
    _add_sliced_unit(mini_repo, [_route("route-demo-big", locator)], {"book.pdf": pages})
    [(slice_, _)] = _slices(mini_repo, [_route("route-demo-big", locator)])
    (part,) = slice_.parts
    assert part.pages == tuple(range(1, MAX_SLICE_PAGES + 1))
    assert part.status == "range-truncated"


def test_non_mandatory_routes_get_no_slice(mini_repo):
    routes = [
        _route("route-demo-current", "current.pdf"),
        _route("route-demo-optional", "gone.pdf", scope="optional"),
    ]
    _add_sliced_unit(mini_repo, routes, {"current.pdf": ["current content"]})
    slices = _slices(mini_repo, routes)
    assert [slice_.route_id for slice_, _ in slices] == ["route-demo-current"]


def test_unresolvable_mandatory_route_fails_naming_it(mini_repo):
    routes = [_route("route-demo-missing", "gone.pdf")]
    _add_sliced_unit(mini_repo, routes, {})
    with pytest.raises(SliceResolutionError, match="route-demo-missing"):
        _slices(mini_repo, routes)


def test_unreadable_pdf_fails_naming_it(mini_repo):
    routes = [_route("route-demo-broken", "broken.pdf")]
    _add_sliced_unit(mini_repo, routes, {"broken.pdf": b"not a pdf at all"})
    with pytest.raises(SliceResolutionError, match="route-demo-broken"):
        _slices(mini_repo, routes)


def test_blank_pdf_fails_for_lack_of_grounding(mini_repo):
    routes = [_route("route-demo-blank", "blank.pdf")]
    _add_sliced_unit(mini_repo, routes, {"blank.pdf": ["", ""]})
    with pytest.raises(SliceResolutionError, match="no extractable text"):
        _slices(mini_repo, routes)


def test_unsupported_format_fails_naming_it(mini_repo):
    routes = [_route("route-demo-deck", "deck.pptx")]
    _add_sliced_unit(mini_repo, routes, {"deck.pptx": b"fake slides"})
    with pytest.raises(SliceResolutionError, match="route-demo-deck"):
        _slices(mini_repo, routes)


def test_text_slice_is_bounded(mini_repo):
    routes = [_route("route-demo-note", "note.md")]
    _add_sliced_unit(mini_repo, routes, {"note.md": b"x" * 300_000})
    [(slice_, _)] = _slices(mini_repo, routes)
    (part,) = slice_.parts
    assert part.kind == "text"
    assert part.status == "truncated"


def test_bundle_budget_names_the_tipping_route(mini_repo, monkeypatch):
    routes = [
        _route("route-demo-first", "first.pdf"),
        _route("route-demo-second", "second.pdf"),
    ]
    _add_sliced_unit(mini_repo, routes,
                     {"first.pdf": ["first content"], "second.pdf": ["second content"]})
    monkeypatch.setattr(material_slices, "MAX_SLICE_BYTES_TOTAL", 0)
    with pytest.raises(SliceResolutionError, match="route-demo-first"):
        _slices(mini_repo, routes)


def test_prepare_fails_closed_on_unresolvable_mandatory(mini_repo):
    _add_sliced_unit(mini_repo, [_route("route-demo-missing", "gone.pdf")], {})
    with pytest.raises(UnresolvedMaterialError, match="route-demo-missing"):
        AIActionService(mini_repo).prepare(
            action_id="unit.compare-materials",
            target_kind="unit",
            target_id="unit-demo-l01",
            provider="manual-bundle",
            request_id="ai-request-slice-fail",
        )
    assert not (mini_repo / "operations/ai-actions/requests/ai-request-slice-fail").exists()


def test_prepare_succeeds_with_unresolvable_optional(mini_repo):
    routes = [
        _route("route-demo-current", "current.pdf"),
        _route("route-demo-optional", "gone.pdf", scope="optional"),
    ]
    _add_sliced_unit(mini_repo, routes, {"current.pdf": ["current content"]})
    AIActionService(mini_repo).prepare(
        action_id="unit.compare-materials",
        target_kind="unit",
        target_id="unit-demo-l01",
        provider="manual-bundle",
        request_id="ai-request-slice-mixed",
    )
    bundle = mini_repo / "operations/ai-actions/requests/ai-request-slice-mixed"
    assert (bundle / "attachments/slices/route-demo-current.md").is_file()
    assert not (bundle / "attachments/slices/route-demo-optional.md").exists()
    index = json.loads((bundle / "attachments/slices/index.json").read_text(encoding="utf-8"))
    assert [entry["route_id"] for entry in index] == ["route-demo-current"]
    assert "route-demo-optional" in (bundle / "context.md").read_text(encoding="utf-8")


def test_slice_checksum_is_not_valid_evidence(mini_repo):
    _add_sliced_unit(mini_repo, [_route("route-demo-book", "lecture-01.pdf")],
                     {"lecture-01.pdf": ["expected-value lecture"]})
    request_id = "ai-request-slice-checksum"
    AIActionService(mini_repo).prepare(
        action_id="unit.compare-materials",
        target_kind="unit",
        target_id="unit-demo-l01",
        provider="manual-bundle",
        request_id=request_id,
    )
    bundle = mini_repo / f"operations/ai-actions/requests/{request_id}"
    index = json.loads((bundle / "attachments/slices/index.json").read_text(encoding="utf-8"))
    entry = index[0]
    assert entry["material_checksum"] != entry["slice_sha256"]

    basis = _basis(mini_repo)
    value = {
        "schema_version": 1,
        "id": "material-synthesis-demo-l01",
        "type": "unit-material-synthesis",
        "unit_id": "unit-demo-l01",
        "status": "approved",
        "basis": {**basis, "ai_provenance": {
            "request_id": request_id, "delivery_id": "ai-delivery-demo",
            "provider": "manual-bundle",
        }},
        "route_assessments": [{
            "route_id": "route-demo-book",
            "source_id": "source-demo-book",
            "locator": "lecture-01.pdf",
            "review_status": "deep-reviewed",
            "concept_ids": ["concept-expected-value"],
            "contribution": "A direct derivation of the weighted sum.",
            "assumptions": "Finite discrete outcomes are assumed.",
            "notation": "Uses uppercase X and lowercase outcome values.",
            "exercise_value": "Includes a small worked calculation.",
            "best_for": "Checking the lecture's core derivation.",
            "limitations": "Does not cover continuous variables.",
            "evidence": [{"locator": "lecture-01.pdf p.1",
                          "checksum": entry["slice_sha256"]}],
        }],
        "comparisons": [],
        "concept_groups": [
            {
                "concept_id": "concept-variance",
                "local_node_ids": ["knowledge-demo-outcomes"],
                "related_unit_ids": [],
                "bridge_note_ids": [],
                "narrative": "Outcome values are the inputs to later dispersion measures.",
            },
            {
                "concept_id": "concept-expected-value",
                "local_node_ids": ["knowledge-demo-expectation"],
                "related_unit_ids": ["unit-demo-l01"],
                "bridge_note_ids": ["note-demo"],
                "narrative": "The local derivation is the canonical expectation concept.",
            },
        ],
    }
    with pytest.raises(ValueError, match="evidence checksum"):
        validate_unit_material_synthesis(mini_repo, "unit-demo-l01", value)
