"""A study map is owed, not optional — and the producer decides who owes one.

Until 2026-08-22 `units_needing_map` counted units whose *authored status* was
literally `needs-map`. That made the obligation a label someone had to remember
to set, and nobody had: 27 lecture units across two enrolled modules had a full
material menu, a knowledge map, and no study map, while every count and badge
downstream read zero. The Review queue, which had always filtered on the map
itself, listed them the whole time — so the system disagreed with itself in
public.

These pin the derivation rather than any particular number, so they keep
working as the curriculum moves.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from learning_os.derive.projection.projection.records_curriculum import _needs_study_map


@pytest.mark.parametrize(
    ("unit", "module_status", "has_map", "owed", "why"),
    [
        ({"status": "not-started"}, "enrolled", False, True,
         "an enrolled lecture with no map is the case that was invisible"),
        ({"status": "active"}, "active", False, True, "so is an active one"),
        ({"status": "not-started"}, "enrolled", True, False,
         "a map discharges the obligation"),
        ({"status": "complete"}, "enrolled", False, False,
         "a finished unit is owed nothing"),
        ({"status": "archived"}, "enrolled", False, False,
         "nor is one explicitly set aside"),
        ({"status": "not-started"}, "dropped", False, False,
         "a dropped module is history, never asked for new plans"),
        ({"status": "paused"}, "archived", False, False, "nor is an archived one"),
        ({"status": "needs-map"}, "dropped", False, False,
         "an inactive module never owes a map, even if an old label says otherwise"),
        ({"status": "paused"}, "enrolled", False, False,
         "a paused unit is inactive and owes no new map"),
        ({"status": "ready-to-shelve"}, "active", False, False,
         "a unit leaving active study owes no new map"),
        ({"status": "not-started"}, None, False, False,
         "a unit whose module cannot be resolved is not accused"),
    ],
)
def test_the_obligation_is_derived_from_the_records(
    unit, module_status, has_map, owed, why,
):
    assert _needs_study_map(unit, module_status, has_map) is owed, why


@pytest.mark.full_repo
def test_the_count_the_badge_and_the_queue_read_one_answer(real_manifest):
    """The projected flag, the per-module tally and the global count must agree.

    They are three consumers of one derivation. Before it they were three
    independent readings of two different facts, and they disagreed by 29.
    """
    manifest = real_manifest
    units = {unit["id"]: unit for unit in manifest["units"]}

    owed = {uid for uid, unit in units.items() if unit.get("needs_study_map")}
    assert manifest["counts"]["units_needing_map"] == len(owed)

    # Every owed unit its module actually lists must be counted by that module.
    # The global total may legitimately exceed the per-module sum, but only for
    # units whose module is absent from the projection entirely — and the test
    # names those rather than letting the difference sit unexplained, because an
    # unexplained gap between a count and a badge is the drift being fixed here.
    in_some_module = {
        uid
        for module in manifest["modules"]
        for uid in module.get("unit_order", []) or []
    }
    projected_modules = {module["id"] for module in manifest["modules"]}
    per_module = sum(
        row["units_needing_map"] for row in manifest["progress"].values()
    )
    assert per_module == len(owed & in_some_module)

    for uid in owed - in_some_module:
        assert units[uid].get("module_id") not in projected_modules, (
            f"{uid} is owed a map and its module is projected, but the module "
            "does not list it — it would be counted globally and by no badge"
        )

    mapped = {study_map["unit_id"] for study_map in manifest["study_maps"]}
    assert not (owed & mapped), "a unit with a map cannot still owe one"

    # Every field the flag is derived from is itself projected, so a reader can
    # always check the producer's reasoning rather than trusting the verdict.
    for unit in units.values():
        assert isinstance(unit.get("needs_study_map"), bool)
        assert "status" in unit and "module_id" in unit


def test_review_planning_queue_follows_needs_study_map_not_legacy_status(
    mini_repo: Path,
):
    from repo_builders import add_curriculum, write_yaml

    from learning_os.derive.projection import generate_all
    from learning_os.store.loader import load_repo

    add_curriculum(mini_repo)
    unit_path = mini_repo / "curriculum/modules/module-demo/units/unit-demo-l01/unit.yaml"
    unit = yaml.safe_load(unit_path.read_text(encoding="utf-8"))
    # Remove study map while unit has status "not-started" (not legacy "needs-map"):
    # review planning queue must still include it because needs_study_map is True.
    (unit_path.parent / "study-map.yaml").unlink()
    unit.pop("current_study_map", None)
    unit["status"] = "not-started"
    write_yaml(unit_path, unit)

    manifest = json.loads(generate_all(load_repo(mini_repo), "T1")["manifest.json"])
    planning_ids = [
        item["id"] for item in manifest["review_items"] if item["category"] == "planning"
    ]
    assert "review-planning-unit-demo-l01" in planning_ids

    # Conversely, legacy status "needs-map" on a dropped module must NOT enter planning.
    mod_path = mini_repo / "curriculum/modules/module-demo/module.yaml"
    module = yaml.safe_load(mod_path.read_text(encoding="utf-8"))
    module["status"] = "dropped"
    write_yaml(mod_path, module)
    unit["status"] = "needs-map"
    write_yaml(unit_path, unit)

    manifest_dropped = json.loads(generate_all(load_repo(mini_repo), "T2")["manifest.json"])
    assert not [
        item for item in manifest_dropped["review_items"] if item["category"] == "planning"
    ]

