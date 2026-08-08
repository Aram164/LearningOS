"""Core Garden projection must not depend on the optional AI subsystem."""

from __future__ import annotations

import json

from learning_os.ai_actions import AIActionService
from learning_os.garden import garden_id
from learning_os.genout import generate_all
from learning_os.loader import load_repo


def test_core_projects_garden_without_ai_state(mini_repo):
    garden = mini_repo / "knowledge/garden"
    garden.mkdir(parents=True, exist_ok=True)

    note = garden / "plain-seed.md"
    note.write_text(
        "# Plain seed\n\nA loose idea. #python\n",
        encoding="utf-8",
    )

    manifest = json.loads(
        generate_all(
            load_repo(mini_repo),
            "T1",
        )["manifest.json"]
    )

    [entry] = manifest["garden_entries"]

    assert entry["id"] == garden_id(
        garden,
        note,
    )
    assert entry["title"] == "Plain seed"
    assert entry["tags"] == ["python"]
    assert entry["state"] == "seed"
    assert entry["revision"].startswith("sha256:")


def test_malformed_optional_ai_state_cannot_erase_garden(mini_repo):
    garden = mini_repo / "knowledge/garden"
    garden.mkdir(parents=True, exist_ok=True)

    note = garden / "survives-ai-failure.md"
    note.write_text(
        "# Survives\n\nStill here. #optimizer\n",
        encoding="utf-8",
    )

    target_id = garden_id(
        garden,
        note,
    )

    state = (
        mini_repo
        / "operations/ai-actions/garden-state"
        / f"{target_id}.yaml"
    )
    state.parent.mkdir(parents=True, exist_ok=True)
    state.write_text(
        "state: [\n",
        encoding="utf-8",
    )

    manifest = json.loads(
        generate_all(
            load_repo(mini_repo),
            "T1",
        )["manifest.json"]
    )

    [entry] = manifest["garden_entries"]

    assert entry["id"] == target_id
    assert entry["title"] == "Survives"
    assert entry["state"] == "seed"
    assert entry["tags"] == ["optimizer"]


def test_ai_service_and_manifest_share_garden_identity(mini_repo):
    garden = mini_repo / "knowledge/garden"
    nested = garden / "python"
    nested.mkdir(parents=True, exist_ok=True)

    original = nested / "decorators.md"
    original.write_text(
        "# Decorators\n\nImport-time registration. #python\n",
        encoding="utf-8",
    )

    first_manifest = json.loads(
        generate_all(
            load_repo(mini_repo),
            "T1",
        )["manifest.json"]
    )
    [first] = first_manifest["garden_entries"]

    service = AIActionService(mini_repo)
    [ai_target] = service.list_garden_targets()

    assert first["id"] == ai_target["id"]

    # Adding a sibling cannot rename an existing Garden artifact.
    (garden / "other.md").write_text(
        "# Other\n\nUnrelated.\n",
        encoding="utf-8",
    )

    second_manifest = json.loads(
        generate_all(
            load_repo(mini_repo),
            "T2",
        )["manifest.json"]
    )

    by_path = {
        row["path"]: row["id"]
        for row in second_manifest["garden_entries"]
    }

    assert by_path[
        "knowledge/garden/python/decorators.md"
    ] == first["id"]


def test_garden_existence_does_not_auto_create_review_decision(mini_repo):
    garden = mini_repo / "knowledge/garden"
    garden.mkdir(parents=True, exist_ok=True)

    (garden / "young-or-old-does-not-matter.md").write_text(
        "# No maturity guess\n\nHuman judgment decides when this is ready.\n",
        encoding="utf-8",
    )

    manifest = json.loads(
        generate_all(
            load_repo(mini_repo),
            "T1",
        )["manifest.json"]
    )

    assert manifest["garden_entries"]
    assert not [
        row
        for row in manifest["review_items"]
        if row["category"] == "garden"
    ]
