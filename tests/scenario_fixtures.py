"""Scenario fixtures: the rich_world characterization world (PLAN step 1.2).

``rich_world(root)`` layers the rich world onto an existing mini repository
(built by ``conftest.build_mini_repo``): the curriculum builders first, then
raw YAML only for families no builder covers. Every record validates, and
two builds are byte-identical: no clock or random values anywhere.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import yaml
from repo_builders import (
    add_manifest_fixtures,
    rich_fixture,
    seed_goal_ledger,
    write_minimal_pdf,
    write_yaml,
)

from learning_os.abilities import ability_fingerprint

PENDING_STAGE_ID = "stage-demo-pending"
SECOND_WORKSPACE_ID = "workspace-second"
ANALYSIS_NOTE_ID = "note-demo-analysis"
ABILITY_ID = "ability-demo-derive"
FIXED_DAY = "2026-09-20"


def _repair_manifest_fixtures(root: Path) -> None:
    # add_manifest_fixtures serves the shadow suites, which never validate:
    # its path row lacks two required keys, and four of its extra rows are
    # schema-invalid. Repair the required path; drop the invalid extras,
    # none of which is a §5.1 family.
    path_file = root / "work/active/workspace-demo/paths/path-demo.yaml"
    data = yaml.safe_load(path_file.read_text(encoding="utf-8"))
    data["type"] = "learning-path"
    data["area"] = "university"
    write_yaml(path_file, data)
    for rel in ("sources/collections/shelf.yaml",
                "curriculum/thematic-groups.yaml",
                "projects/aliases.yaml",
                "sources/topics.yaml"):
        (root / rel).unlink()


def _add_pending_stage(root: Path) -> None:
    map_path = root / "curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml"
    data = yaml.safe_load(map_path.read_text(encoding="utf-8"))
    note_rel = ("curriculum/modules/module-demo/units/unit-demo-l01/stages/"
                f"{PENDING_STAGE_ID}/notes.md")
    (root / note_rel).parent.mkdir(parents=True, exist_ok=True)
    (root / note_rel).write_text("", encoding="utf-8")
    data["stages"].append({
        "id": PENDING_STAGE_ID,
        "knowledge_node_id": "knowledge-demo-expectation",
        "title": "Apply expected value",
        "status": "pending",
        "objective": "Apply expected value to a worked example.",
        "done_when": ["Work the example."],
        "scope_triage": "required-now",
        "resources": [{"kind": "read", "label": "Demo Book §2",
                       "source_id": "source-demo-book", "locator": "§2"}],
        "working_note": note_rel,
        "attachments": [],
        "source_feedback": [],
    })
    write_yaml(map_path, data)


def _add_second_workspace(root: Path) -> None:
    ws = root / "work/active" / SECOND_WORKSPACE_ID
    ws.mkdir(parents=True)
    (ws / "CONTEXT.md").write_text(
        "---\n"
        f"id: {SECOND_WORKSPACE_ID}\n"
        "type: workspace\n"
        "title: Second workspace\n"
        "created: 2026-07-17\n"
        "status: active\n"
        "concepts: [concept-expected-value]\n"
        "notes: [note-demo]\n"
        "---\n"
        "\n"
        "## Objective\n"
        "\n"
        "Second.\n"
        "\n"
        "## Current Scope\n"
        "\n"
        "Small.\n"
        "\n"
        "## Open Questions\n"
        "\n"
        "None.\n"
        "\n"
        "## Next Action\n"
        "\n"
        "Do the second thing.\n",
        encoding="utf-8")


def _add_inbox_drops(root: Path) -> None:
    (root / "work/inbox/note-drop.md").write_text(
        "# Dropped note\n\nUnrouted.\n", encoding="utf-8")
    pack = root / "work/inbox/pack"
    pack.mkdir(parents=True, exist_ok=True)
    (pack / "one.md").write_text("one\n", encoding="utf-8")
    (pack / "two.md").write_text("two\n", encoding="utf-8")


def _add_fixture_book(root: Path) -> Path:
    book = root.parent / "materials/source-demo-book/book.pdf"
    write_minimal_pdf(book, ["Fixture book for source-demo-book"])
    return book


def _add_analysis_note(root: Path, book: Path) -> None:
    digest = hashlib.sha256(book.read_bytes()).hexdigest()
    body = ("# Expected value — analysis of Demo Book §1\n"
            "\n"
            "The derivation weights every outcome by its probability.\n")
    body_bytes = body.encode("utf-8")
    meta = {
        "id": ANALYSIS_NOTE_ID,
        "type": "note",
        "role": "reference",
        "title": "Expected value — analysis of Demo Book §1",
        "created": "2026-09-21",
        "concepts": ["concept-expected-value"],
        "sources": ["source-demo-book"],
        "material_analysis": {
            "resolution": "resolved",
            "material": "source-demo-book/book.pdf",
            "recorded_source_digest": digest,
            "live_source_digest": digest,
            "inspected_range": {"start": 1, "end": 1},
            "frozen_input_sha256": hashlib.sha256(body_bytes).hexdigest(),
            "frozen_input_bytes": len(body_bytes),
            "source_id": "source-demo-book",
        },
    }
    path = root / "knowledge/notes/mathematics" / f"{ANALYSIS_NOTE_ID}.md"
    path.write_text("---\n" + yaml.safe_dump(meta, sort_keys=False).rstrip()
                    + "\n---\n\n" + body, encoding="utf-8")


def _add_path_stage_note(root: Path) -> None:
    # Amendment (w): the path stage carries a notes_path naming an existing,
    # non-empty note, so path.note.write has a success case. The note stays
    # inside the owning workspace (rules/curriculum.py PATH-NOTE-OWNER).
    path_file = root / "work/active/workspace-demo/paths/path-demo.yaml"
    data = yaml.safe_load(path_file.read_text(encoding="utf-8"))
    note_rel = "work/active/workspace-demo/paths/stage-demo-path-notes.md"
    for stage in data["stages"]:
        if stage.get("id") == "stage-demo-path":
            stage["notes_path"] = note_rel
    write_yaml(path_file, data)
    (root / note_rel).write_text(
        "# First step — path notes\n\nBegun.\n", encoding="utf-8")


def _add_runtime_target(root: Path) -> None:
    # Amendment (w): the active stage of the unit's current study map
    # carries a runtime_target, so collect_requirements returns one
    # requirement (req-demo-l01-demo) and the observation operations have
    # success cases. The stage has no `concepts`, so the concept is a
    # knowledge-node id of the unit, as the amendment allows.
    map_path = root / "curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml"
    data = yaml.safe_load(map_path.read_text(encoding="utf-8"))
    for stage in data["stages"]:
        if stage.get("id") == "stage-demo":
            stage["runtime_target"] = {
                "concept": "knowledge-demo-expectation",
                "capability": {"kind": "explain", "operands": ["expectation"]},
                "conditions": ["unfamiliar-example"],
                "evidence_spec": ["explain-reason"],
            }
    write_yaml(map_path, data)


def _add_ability(root: Path) -> None:
    ability = {
        "id": ABILITY_ID,
        "title": "Derive expected value",
        "claim": "Derive expectation from stated outcomes.",
        "conditions": ["finite discrete outcomes", "probabilities sum to one"],
        "evidence_spec": ["correct derivation"],
        "concept_ids": ["concept-expected-value"],
        "module_ids": ["module-demo"],
        "preparation_routes": [],
        "review": {"state": "reviewed", "reviewed_by": "fixture",
                   "reviewed_on": "2026-09-23"},
    }
    write_yaml(root / "knowledge/abilities.yaml",
               {"abilities": [ability], "bridges": []})
    row = {
        "id": "ability-observation-1",
        "ability_id": ABILITY_ID,
        "ability_sha256": ability_fingerprint(ability),
        "claim": "I derived this from the stated problem.",
        "work_ref": "conversation://fixture/work-1",
        "confirmation_ref": "conversation://fixture/confirmation-1",
        "activity": "worked derivation",
        "result": "correct",
        "timestamp": "2026-09-23T10:01:00Z",
        "conditions": list(ability["conditions"]),
        "evidence_tags": list(ability["evidence_spec"]),
        "assistance": "none",
        "confirmed_by": "learner",
    }
    (root / "work/active/workspace-demo/ability-observations.jsonl").write_text(
        json.dumps(row, sort_keys=True) + "\n", encoding="utf-8")


def _add_goal_ledger(root: Path) -> dict[str, str]:
    decisions = {"goal-demo-deferred": "deferred", "goal-demo-rejected": "rejected"}
    path = seed_goal_ledger(root, decisions)
    # seed_goal_ledger stamps today; pin the clock for determinism.
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    for entry in data["decisions"].values():
        entry["decided_at"] = FIXED_DAY
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return decisions


def rich_world(root: Path) -> dict:
    """Layer the rich characterization world onto a mini repository.

    ``root`` is a ``build_mini_repo`` product. Returns the world's named
    ids for test use.
    """
    route_id, _route = rich_fixture(root)
    add_manifest_fixtures(root)
    _repair_manifest_fixtures(root)
    _add_pending_stage(root)
    _add_runtime_target(root)
    _add_path_stage_note(root)
    _add_second_workspace(root)
    _add_inbox_drops(root)
    book = _add_fixture_book(root)
    _add_analysis_note(root, book)
    _add_ability(root)
    _add_goal_ledger(root)
    return {
        "module": "module-demo",
        "unit": "unit-demo-l01",
        "study_map": "study-map-demo-l01",
        "stage_active": "stage-demo",
        "stage_pending": PENDING_STAGE_ID,
        "route": route_id,
        "source": "source-demo-book",
        "workspace": "workspace-demo",
        "workspace_second": SECOND_WORKSPACE_ID,
        "path": "path-demo",
        "project": "project-demo",
        "ability": ABILITY_ID,
        "note_synthesis": "note-demo",
        "note_analysis": ANALYSIS_NOTE_ID,
        "concept": "concept-expected-value",
        "goal_deferred": "goal-demo-deferred",
        "goal_rejected": "goal-demo-rejected",
        "ai_request": "ai-request-demo",
        "material": "material://source-demo-book/book.pdf",
    }
