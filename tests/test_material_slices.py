"""Bounded material slices for unit.compare-materials (Commit 1 test suite)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml
from repo_builders import add_curriculum, run_los, write_minimal_pdf, write_yaml

from learning_os import material_slices
from learning_os.ai_actions import (
    ActionPolicyError,
    AIActionService,
    ContinuationRefusedError,
    UnresolvedMaterialError,
)
from learning_os.loader import load_repo
from learning_os.material_slices import (
    MAX_SLICE_PAGES,
    MAX_SLICE_PASSES,
    SliceResolutionError,
    build_unit_slices,
    continuation_record_dict,
    parse_locator_page_ranges,
    plan_continuation,
)
from learning_os.material_synthesis import (
    MaterialSynthesisError,
    current_unit_material_basis,
    inspected_pages_by_route,
    validate_synthesis_page_provenance,
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
    pages = [f"content line {n}" for n in range(1, 26)]
    _add_sliced_unit(mini_repo, [_route("route-demo-long", "long.pdf")], {"long.pdf": pages})
    [(slice_, _)] = _slices(mini_repo, [_route("route-demo-long", "long.pdf")])
    (part,) = slice_.parts
    assert part.pages == tuple(range(1, MAX_SLICE_PAGES + 1))
    assert part.page_total == 25
    assert part.status == "truncated"
    assert "content line 1" in part.text
    assert "content line 20" in part.text
    assert "content line 25" not in part.text


def test_first_pass_can_contain_twenty_pages(mini_repo):
    pages = [f"content line {n}" for n in range(1, 21)]
    locator = "full.pdf"
    _add_sliced_unit(mini_repo, [_route("route-demo-twenty", locator)], {"full.pdf": pages})
    [(slice_, _)] = _slices(mini_repo, [_route("route-demo-twenty", locator)])
    (part,) = slice_.parts
    assert part.pages == tuple(range(1, 21))
    assert part.status == "complete"


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


LONG_PAGES = [f"content line {n}" for n in range(1, 31)]

LONG_REQUEST = "ai-request-long"


def _prepared_long_route(root: Path, request_id: str = LONG_REQUEST):
    routes = [_route("route-demo-long", "long.pdf")]
    _add_sliced_unit(root, routes, {"long.pdf": LONG_PAGES})
    app = AIActionService(root)
    request = app.prepare(
        action_id="unit.compare-materials",
        target_kind="unit",
        target_id="unit-demo-l01",
        provider="manual-bundle",
        request_id=request_id,
    )
    return app, request


def _append(app: AIActionService, **overrides):
    args = {
        "request_id": LONG_REQUEST,
        "route_id": "route-demo-long",
        "start": 21,
        "end": 30,
        "kind": "example",
        "concept_ids": ["concept-expected-value"],
        "reason": "worked examples follow the definition section",
    }
    args.update(overrides)
    return app.append_slices(**args)


def _bundle(root: Path, request_id: str = LONG_REQUEST) -> Path:
    return root / "operations/ai-actions/requests" / request_id


def test_short_source_needs_no_second_pass(mini_repo):
    _add_sliced_unit(mini_repo, [_route("route-demo-short", "short.pdf")],
                     {"short.pdf": ["only page one", "only page two"]})
    app = AIActionService(mini_repo)
    request = app.prepare(
        action_id="unit.compare-materials",
        target_kind="unit",
        target_id="unit-demo-l01",
        provider="manual-bundle",
        request_id="ai-request-short",
    )
    assert request.get("reading_passes") is None
    bundle = _bundle(mini_repo, "ai-request-short")
    assert not (bundle / "attachments/slices/continuations").exists()
    index = json.loads((bundle / "attachments/slices/index.json").read_text(encoding="utf-8"))
    assert [(entry["pass"], entry["route_id"]) for entry in index] == [
        (1, "route-demo-short")]


def test_sufficient_first_pass_validates_without_continuation(mini_repo):
    _add_sliced_unit(mini_repo, [_route("route-demo-book", "lecture-01.pdf")],
                     {"lecture-01.pdf": ["expected-value lecture"]})
    AIActionService(mini_repo).prepare(
        action_id="unit.compare-materials",
        target_kind="unit",
        target_id="unit-demo-l01",
        provider="manual-bundle",
        request_id="ai-request-solo",
    )
    bundle = _bundle(mini_repo, "ai-request-solo")
    index = json.loads((bundle / "attachments/slices/index.json").read_text(encoding="utf-8"))
    inspected = inspected_pages_by_route(index)
    assert inspected == {"route-demo-book": [1]}
    validate_synthesis_page_provenance(inspected, {
        "id": "material-synthesis-demo-l01",
        "unit_id": "unit-demo-l01",
        "route_assessments": [{
            "route_id": "route-demo-book",
            "review_status": "deep-reviewed",
            "evidence": [{"locator": "lecture-01.pdf p.1"}],
        }],
        "comparisons": [],
    })


def test_explicit_gap_triggers_targeted_second_pass(mini_repo):
    app, _ = _prepared_long_route(mini_repo)
    result = _append(app)
    assert result["pass"] == 2
    assert result["pages"] == list(range(21, 31))
    bundle = _bundle(mini_repo)
    assert (bundle / result["bundle_path"]).is_file()
    record = yaml.safe_load(
        (bundle / "attachments/slices/continuations/pass-2-route-demo-long.yaml"
         ).read_text(encoding="utf-8"))
    assert record["pass_number"] == 2
    assert record["unresolved_claim"]["kind"] == "example"
    assert record["unresolved_claim"]["concept_ids"] == ["concept-expected-value"]
    assert "examples follow" in record["unresolved_claim"]["reason"]
    assert record["requested_pages"] == {"start": 21, "end": 30}
    assert record["prior_inspected_pages"] == list(range(1, 21))
    index = json.loads((bundle / "attachments/slices/index.json").read_text(encoding="utf-8"))
    assert [(entry["pass"], entry["route_id"]) for entry in index] == [
        (1, "route-demo-long"), (2, "route-demo-long")]
    request = app.repository.get_request(LONG_REQUEST)
    assert request["reading_passes"] == [{
        "route_id": "route-demo-long", "pass": 2,
        "bundle_path": result["bundle_path"],
        "continuation": "attachments/slices/continuations/pass-2-route-demo-long.yaml",
    }]


def test_second_pass_uses_only_the_requested_range(mini_repo):
    app, _ = _prepared_long_route(mini_repo)
    result = _append(app)
    body = (_bundle(mini_repo) / result["bundle_path"]).read_text(encoding="utf-8")
    assert "content line 25" in body
    assert "content line 5" not in body
    assert "PDF pp. 21-30 of 30" in body


def test_pass_cap_refuses_a_fourth_pass(mini_repo):
    app, _ = _prepared_long_route(mini_repo)
    _append(app, start=21, end=25)
    _append(app, start=26, end=30)
    with pytest.raises(ContinuationRefusedError, match=f"{MAX_SLICE_PASSES} passes"):
        _append(app, start=21, end=25)


def test_bundle_budget_is_enforced_on_append(mini_repo, monkeypatch):
    app, _ = _prepared_long_route(mini_repo)
    monkeypatch.setattr("learning_os.ai_actions.service.MAX_SLICE_BYTES_TOTAL", 0)
    with pytest.raises(ContinuationRefusedError, match="byte ceiling"):
        _append(app)


def test_out_of_range_continuation_fails_clearly(mini_repo):
    app, _ = _prepared_long_route(mini_repo)
    with pytest.raises(ContinuationRefusedError, match="outside this 30-page file"):
        _append(app, start=28, end=35)
    with pytest.raises(ContinuationRefusedError, match="not an explicit bounded range"):
        _append(app, start=1, end=MAX_SLICE_PAGES + 1)
    with pytest.raises(ContinuationRefusedError, match="not an explicit bounded range"):
        _append(app, start=0, end=5)


def test_continuation_needs_a_known_kind_and_gap(mini_repo):
    app, _ = _prepared_long_route(mini_repo)
    with pytest.raises(ContinuationRefusedError, match="unknown gap kind"):
        _append(app, kind="vibes")
    with pytest.raises(ContinuationRefusedError, match="unknown concept ids"):
        _append(app, concept_ids=["concept-nope"])
    with pytest.raises(ContinuationRefusedError, match="stated evidence gap"):
        _append(app, reason="   ")


def test_changed_material_between_passes_refuses_reprepare(mini_repo):
    app, _ = _prepared_long_route(mini_repo)
    write_minimal_pdf(
        mini_repo.parent / "materials/source-demo-book/long.pdf",
        ["replaced content"] * 30)
    with pytest.raises(ContinuationRefusedError, match="changed since pass 1"):
        _append(app)


def test_continuation_without_first_pass_is_refused(mini_repo):
    routes = [
        _route("route-demo-current", "current.pdf"),
        _route("route-demo-optional", "gone.pdf", scope="optional"),
    ]
    _add_sliced_unit(mini_repo, routes, {"current.pdf": ["current content"]})
    app = AIActionService(mini_repo)
    app.prepare(
        action_id="unit.compare-materials",
        target_kind="unit",
        target_id="unit-demo-l01",
        provider="manual-bundle",
        request_id="ai-request-nofirst",
    )
    with pytest.raises(ContinuationRefusedError, match="no first-pass slice"):
        app.append_slices(
            request_id="ai-request-nofirst", route_id="route-demo-optional",
            start=1, end=2, kind="example", concept_ids=["concept-expected-value"],
            reason="optional route follow-up without a first pass")


def test_append_refuses_non_compare_requests_and_delivered_ones(mini_repo):
    _prepared_long_route(mini_repo)
    app = AIActionService(mini_repo)
    with pytest.raises(ActionPolicyError, match="not part of this request's unit"):
        app.append_slices(
            request_id=LONG_REQUEST, route_id="route-demo-ghost",
            start=1, end=2, kind="example", concept_ids=["concept-expected-value"],
            reason="unknown route")
    request = app.repository.get_request(LONG_REQUEST)
    request["status"] = "delivery-ready"
    app.repository.update_request(request)
    with pytest.raises(ActionPolicyError, match="only prepared requests"):
        _append(app)


def test_page_provenance_accepts_inspected_and_prose():
    inspected = {"route-demo-a": [1, 2, 3], "route-demo-b": [5]}
    validate_synthesis_page_provenance(inspected, {
        "id": "material-synthesis-x", "unit_id": "unit-demo-l01",
        "route_assessments": [
            {"route_id": "route-demo-a", "review_status": "deep-reviewed",
             "evidence": [{"locator": "book.pdf, pdf pp. 1-3"}]},
            {"route_id": "route-demo-b", "review_status": "deep-reviewed",
             "evidence": [{"locator": "Aufgabe 6.19(a-b) only"}]},
            {"route_id": "route-demo-c", "review_status": "deep-reviewed",
             "evidence": [{"locator": "other.pdf p.99"}]},
            {"route_id": "route-demo-a", "review_status": "screened",
             "reason": "metadata only"},
        ],
        "comparisons": [{
            "left_route_id": "route-demo-a", "right_route_id": "route-demo-b",
            "evidence": {
                "left": [{"locator": "book.pdf p.2"}],
                "right": [{"locator": "notes.pdf p.5"}],
            },
        }],
    })


def test_page_provenance_refuses_uninspected_pages():
    inspected = {"route-demo-a": [1, 2]}
    with pytest.raises(MaterialSynthesisError, match="never inspected"):
        validate_synthesis_page_provenance(inspected, {
            "id": "material-synthesis-x", "unit_id": "unit-demo-l01",
            "route_assessments": [{
                "route_id": "route-demo-a", "review_status": "deep-reviewed",
                "evidence": [{"locator": "book.pdf, pdf pp. 1-9"}],
            }],
            "comparisons": [],
        })


def test_page_provenance_checks_both_comparison_sides():
    inspected = {"route-demo-a": [1], "route-demo-b": [1]}
    with pytest.raises(MaterialSynthesisError, match="comparison right"):
        validate_synthesis_page_provenance(inspected, {
            "id": "material-synthesis-x", "unit_id": "unit-demo-l01",
            "route_assessments": [],
            "comparisons": [{
                "left_route_id": "route-demo-a", "right_route_id": "route-demo-b",
                "evidence": {
                    "left": [{"locator": "a.pdf p.1"}],
                    "right": [{"locator": "b.pdf p.7"}],
                },
            }],
        })


def test_continuation_record_round_trips_through_yaml(mini_repo):
    _prepared_long_route(mini_repo)
    repo = load_repo(mini_repo)
    route = _route("route-demo-long", "long.pdf")
    record, _, _ = plan_continuation(
        repo, route, basis=_basis(mini_repo), inspected=list(range(1, 21)),
        passes_used=1, start=21, end=30, kind="derivation",
        concept_ids=["concept-expected-value"],
        reason="the derivation continues past page 20")
    as_yaml = yaml.safe_dump(continuation_record_dict(record), sort_keys=False)
    reloaded = yaml.safe_load(as_yaml)
    assert reloaded["route_id"] == "route-demo-long"
    assert reloaded["pass_number"] == 2
    assert reloaded["unresolved_claim"] == {
        "kind": "derivation",
        "concept_ids": ["concept-expected-value"],
        "reason": "the derivation continues past page 20",
    }
    assert reloaded["requested_pages"] == {"start": 21, "end": 30}
    assert reloaded["prior_inspected_pages"] == list(range(1, 21))


def test_append_slices_cli_reports_the_new_pass(mini_repo):
    _prepared_long_route(mini_repo, request_id="ai-request-cli")
    routes_before = _bundle(mini_repo, "ai-request-cli")
    assert routes_before.is_dir()
    proc = run_los(
        mini_repo, "ai-action-append-slices",
        "--request-id", "ai-request-cli", "--route-id", "route-demo-long",
        "--start", "21", "--end", "30", "--kind", "derivation",
        "--concept-id", "concept-expected-value",
        "--reason", "the derivation continues past page 20")
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["ok"] is True
    assert payload["continuation"]["pass"] == 2
    assert payload["continuation"]["pages"] == list(range(21, 31))
