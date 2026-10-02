"""Not-found suggestions and filter validation for read commands (#84).

A mistyped id costs one line of stderr instead of an extra discovery
read; an unknown filter value refuses with exit 2 instead of answering
a silent empty result. Suggestions are text, never an automatic retry.
"""

from __future__ import annotations

import json
from pathlib import Path

import yaml
from repo_builders import _add_material_overview, add_curriculum, run_los, write_yaml

from learning_os.commands.query import VALID_RECORD_TYPES
from learning_os.commands.suggest import (
    MAX_SUGGESTIONS,
    not_found,
    ranked,
    suggest,
    with_suggestions,
)
from learning_os.commands.unit import UNIT_STATUSES

SCHEMA = Path(__file__).resolve().parent.parent / "system" / "schema"


def test_ranking_prefers_case_fold_zero_padding_prefix_and_substring():
    pool = ["unit-m2-sad-l05", "unit-m2-sad-l15", "note-sad-l05-x",
            "UNIT-M2-SAD-L05-dup"]
    assert ranked("UNIT-m2-sad-l05", pool)[0] == "unit-m2-sad-l05"
    assert ranked("unit-m2-sad-l5", pool)[0] == "unit-m2-sad-l05"
    assert ranked("unit-m2-sad-l", pool) == [
        "UNIT-M2-SAD-L05-dup", "unit-m2-sad-l05", "unit-m2-sad-l15"]
    assert ranked("sad-l05", pool)[0] in {
        "note-sad-l05-x", "unit-m2-sad-l05", "UNIT-M2-SAD-L05-dup"}


def test_suggest_falls_back_to_difflib_and_bounds_to_five():
    pool = [f"note-06-random-variables-pp{i:03d}" for i in range(7)]
    shown = suggest("note-06-random-variables", pool)
    assert shown == sorted(pool)[:MAX_SUGGESTIONS]
    assert "worksapce" not in pool
    assert suggest("worksapce", ["workspace", "note"]) == ["workspace"]
    assert suggest("zzz-no-such-id", ["workspace", "note"]) == []
    assert suggest("unit-demo-l01", ["unit-demo-l01"]) == ["unit-demo-l01"]


def test_suggestion_suffix_counts_further_matches():
    pool = [f"note-06-random-variables-pp{i:03d}" for i in range(7)]
    message = not_found("note", "note-06-random-variables", pool)
    assert message.startswith("note not found: note-06-random-variables")
    assert "+2 more" in message
    assert with_suggestions("record not found: x", "x", []) == "record not found: x"


def test_inspect_suggests_zero_padded_and_substring_ids(mini_repo: Path):
    add_curriculum(mini_repo)
    proc = run_los(mini_repo, "inspect", "unit-demo-l1")
    assert proc.returncode == 2
    assert "record not found: unit-demo-l1" in proc.stderr
    assert proc.stderr.index("unit-demo-l01") > proc.stderr.index("did you mean")
    batch = run_los(mini_repo, "inspect", "unit-demo-l01", "note-dem")
    assert batch.returncode == 2
    assert "note-demo" in batch.stderr


def test_plan_edit_context_and_material_context_suggest_units(mini_repo: Path):
    add_curriculum(mini_repo)
    proc = run_los(mini_repo, "plan-edit-context", "unit-demo-l1", "--brief")
    assert proc.returncode == 2
    assert "unit not found: unit-demo-l1" in proc.stderr
    assert "unit-demo-l01" in proc.stderr
    context = run_los(mini_repo, "material-context", "density",
                      "--unit", "unit-demo-l1")
    assert context.returncode == 2
    assert "unknown unit" in context.stderr
    assert "unit-demo-l01" in context.stderr


def test_note_read_suggests_prefix_matches(mini_repo: Path):
    proc = run_los(mini_repo, "note-read", "note-dem")
    assert proc.returncode == 2
    assert "note not found: note-dem" in proc.stderr
    assert "note-demo" in proc.stderr


def test_atlas_context_echoes_the_concept_and_suggests(mini_repo: Path):
    proc = run_los(mini_repo, "atlas-context", "concept-expected")
    assert proc.returncode == 2
    assert "unknown concept: concept-expected" in proc.stderr
    assert "concept-expected-value" in proc.stderr


def test_material_span_echoes_the_route_and_lists_bounded_routes(mini_repo: Path):
    add_curriculum(mini_repo)
    _add_material_overview(mini_repo)
    brief = json.loads(run_los(
        mini_repo, "plan-edit-context", "unit-demo-l01", "--brief").stdout)
    route_id = brief["inventory"]["route_ids"][0]
    assert route_id
    proc = run_los(mini_repo, "material-span", "unit-demo-l01", "route-nope")
    assert proc.returncode == 2
    assert "route not found: route-nope in unit-demo-l01" in proc.stderr
    assert route_id in proc.stderr
    near = run_los(mini_repo, "material-span", "unit-demo-l01", route_id[:-1])
    assert near.returncode == 2
    assert route_id in near.stderr


def test_unit_list_refuses_unknown_filters_but_keeps_valid_empty(mini_repo: Path):
    add_curriculum(mini_repo)
    module_path = mini_repo / "curriculum/modules/module-demo/module.yaml"
    module = yaml.safe_load(module_path.read_text(encoding="utf-8"))
    module["components"] = [{"id": "component-demo-unused", "title": "Unused",
                               "short_title": "Unused", "order": 1}]
    write_yaml(module_path, module)
    bad_module = run_los(mini_repo, "unit-list", "--compact",
                         "--module-id", "module-dem")
    assert bad_module.returncode == 2
    assert "module not found: module-dem" in bad_module.stderr
    assert "module-demo" in bad_module.stderr
    bad_component = run_los(mini_repo, "unit-list", "--compact",
                            "--component-id", "component-demo-unuse")
    assert bad_component.returncode == 2
    assert "component-demo-unused" in bad_component.stderr
    bad_status = run_los(mini_repo, "unit-list", "--compact",
                         "--status", "actve")
    assert bad_status.returncode == 2
    assert "unknown status: actve" in bad_status.stderr
    assert "active" in bad_status.stderr
    # Valid filters with no matches still exit 0 with total 0.
    empty = run_los(mini_repo, "unit-list", "--compact",
                    "--component-id", "component-demo-unused")
    assert empty.returncode == 0, empty.stderr
    assert json.loads(empty.stdout)["total"] == 0
    paused = run_los(mini_repo, "unit-list", "--compact", "--status", "paused")
    assert paused.returncode == 0, paused.stderr
    assert json.loads(paused.stdout)["total"] == 0


def test_unit_statuses_match_the_schema_enum():
    declared = json.loads((SCHEMA / "unit.schema.json").read_text())
    assert UNIT_STATUSES == set(declared["properties"]["status"]["enum"])


def test_valid_record_types_cover_the_live_manifest(real_manifest):
    live = {row.get("type") for row in real_manifest["records"]}
    assert live <= VALID_RECORD_TYPES
    assert {"garden-note", "inbox-item"} <= VALID_RECORD_TYPES


def test_search_refuses_an_unknown_type_on_every_path(mini_repo: Path):
    for argv in (("search", "", "--type", "worksapce"),
                ("search", "", "--type", "worksapce", "--page"),
                ("search", "density", "--type", "worksapce", "--content")):
        proc = run_los(mini_repo, *argv)
        assert proc.returncode == 2, argv
        assert "unknown record type: worksapce" in proc.stderr, argv
        assert "workspace" in proc.stderr, argv
        assert "valid types:" in proc.stderr, argv
        assert not proc.stdout, argv
    ability = run_los(mini_repo, "search", "", "--type", "ability")
    assert ability.returncode == 2
    assert "unknown record type: ability" in ability.stderr
    valid = run_los(mini_repo, "search", "", "--type", "workspace")
    assert valid.returncode == 0, valid.stderr
    assert json.loads(valid.stdout)[0]["id"] == "workspace-demo"


def _seed_abilities(root: Path) -> None:
    ability = {
        "title": "Derive simple least squares", "claim": "Derive slope.",
        "conditions": ["intercept included"],
        "evidence_spec": ["correct derivation"],
        "concept_ids": ["concept-expected-value"], "module_ids": [],
        "review": {"state": "reviewed", "reviewed_by": "test",
                   "reviewed_on": "2026-09-23"},
    }
    (root / "knowledge/abilities.yaml").write_text(yaml.safe_dump({
        "abilities": [
            {**ability, "id": "ability-sad-ols",
             "preparation_routes": []},
            {**ability, "id": "ability-aml-ols",
             "preparation_routes": []},
        ],
        "bridges": [],
    }, sort_keys=False), encoding="utf-8")


def test_ability_context_flags_an_unknown_identity_additively(mini_repo: Path):
    from jsonschema import Draft202012Validator

    _seed_abilities(mini_repo)
    proc = run_los(mini_repo, "ability-context", "ability-sad-ol")
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["contract"] == "ability-context-v1"
    assert payload["state"] == "unmapped"
    assert payload["focus"] == "ability-sad-ol"
    assert payload["reason"] == "no reviewed ability maps this identity"
    assert payload["known_identity"] is False
    assert payload["suggestions"][0] == "ability-sad-ols"
    assert len(payload["suggestions"]) <= MAX_SUGGESTIONS
    schema = json.loads((SCHEMA / "ability-context.schema.json").read_text())
    Draft202012Validator(schema).validate(payload)
    known = json.loads(run_los(
        mini_repo, "ability-context", "ability-sad-ols").stdout)
    assert "known_identity" not in known
    assert "suggestions" not in known


def test_successful_reads_are_unchanged_by_suggestions(mini_repo: Path):
    add_curriculum(mini_repo)
    proc = run_los(mini_repo, "inspect", "unit-demo-l01")
    assert proc.returncode == 0, proc.stderr
    assert json.loads(proc.stdout)["id"] == "unit-demo-l01"
    note = run_los(mini_repo, "note-read", "note-demo")
    assert note.returncode == 0, note.stderr
    assert json.loads(note.stdout)["note_id"] == "note-demo"


def test_refusal_suggestions_stay_bounded(mini_repo: Path):
    proc = run_los(mini_repo, "note-read", "note-dem")
    base = "los: note not found: note-dem\n"
    assert len(proc.stderr.encode()) - len(base.encode()) <= 300
