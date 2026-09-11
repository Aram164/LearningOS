"""Shared synthetic-repository builders for the test suite.

`add_curriculum`, `write_yaml`, `_add_material_overview` and `run_los` used to
live in `test_curriculum_v2.py`, which made fifteen other test modules import
from a test module — so renaming or splitting the biggest test file would have
broken the whole suite. They are pure builders/drivers with no assertions, so
they live here now; behaviour is unchanged.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml

from learning_os.loader import parse_frontmatter
from learning_os.routes import deterministic_route_id

LOS = Path(__file__).resolve().parent.parent / "tools" / "los.py"


def run_los(root: Path, *args: str, stdin: str | None = None):
    return subprocess.run([sys.executable, str(LOS), "--root", str(root), *args],
                          capture_output=True, text=True, input=stdin, timeout=120)


def write_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")


def add_curriculum(root: Path) -> None:
    write_yaml(root / "curriculum/programs/program-bachelors.yaml", {
        "id": "program-bachelors", "type": "program", "title": "Bachelor’s",
        "kind": "academic", "status": "active", "default": True,
        "semester_bound": True,
        "semesters": [{"id": "semester-sose-2026", "title": "SoSe 2026",
                       "status": "current", "order": 1}],
    })
    module_dir = root / "curriculum/modules/module-demo"
    write_yaml(module_dir / "module.yaml", {
        "id": "module-demo", "type": "module", "kind": "academic",
        "area_id": "program-bachelors", "institution": "HU Berlin",
        "title": "Demo Module", "semester": "sose-2026", "status": "enrolled",
        "unit_order": ["unit-demo-l01"], "source_map": "source-map.yaml",
        "examination": {
            "type": "klausur",
            "sittings": [
                {"termin": 3, "date": "2000-01-01", "label": "Elapsed unregistered sitting"},
                {"termin": 2, "date": "2026-10-09",
                 "time": "13:00-16:00", "label": "2. Termin"},
            ],
            "registration_windows": [{"opens": "2026-08-31", "closes": "2026-09-10",
                                      "label": "2.-PZ Anmeldung",
                                      "action": "Register via AGNES.", "termins": [2]}],
        },
        "attempts": [
            {"termin": 1, "date": "2026-07-27", "result": "withdrawn"},
            {"termin": 2, "date": "2026-10-09", "result": "registered"},
        ],
    })
    write_yaml(module_dir / "source-map.yaml", {
        "type": "module-source-map", "module_id": "module-demo",
        "sources": [{"source_id": "source-demo-book", "role": "spine",
                     "why": "Scoped demo reading.", "priority": 0,
                     "unit_routes": ["unit-demo-l01"]}],
    })
    unit_dir = module_dir / "units/unit-demo-l01"
    write_yaml(unit_dir / "unit.yaml", {
        "id": "unit-demo-l01", "type": "unit", "module_id": "module-demo",
        "kind": "lecture", "title": "Expected value", "order": 1,
        "scope": "The lecture as taught.", "status": "active",
        "scope_sources": [{"source_id": "source-demo-book", "authority": "slides",
                           "locator": "Lecture 1"}],
        "source_selections": [{"source_id": "source-demo-book", "locator": "§1 Erwartungswert",
                               "purpose": "Current derivation"}],
        "current_study_map": "study-map-demo-l01",
        "artifacts": {"ultimate_reference": "note-demo"},
        "workspace_ids": ["workspace-demo"],
    })
    note_rel = "curriculum/modules/module-demo/units/unit-demo-l01/stages/stage-demo/notes.md"
    (root / note_rel).parent.mkdir(parents=True, exist_ok=True)
    (root / note_rel).write_text("", encoding="utf-8")
    write_yaml(unit_dir / "study-map.yaml", {
        "id": "study-map-demo-l01", "type": "study-map", "unit_id": "unit-demo-l01",
        "status": "active", "current_stage": "stage-demo",
        "source_plan": {"path": "work/active/workspace-demo/CONTEXT.md",
                        "provenance": "operator"},
        "detours": [], "shelving": {"state": "none"},
        "stages": [{
            "id": "stage-demo", "title": "Derive expected value", "status": "active",
            "objective": "Derive and explain expected value.",
            "done_when": ["Explain the derivation."], "scope_triage": "required-now",
            "resources": [
                {"id": "resource-demo-book-ch01", "kind": "read",
                 "label": "Demo Book §1", "source_id": "source-demo-book",
                 "locator": "§1"},
                {"id": "resource-demo-book-appendix", "kind": "read",
                 "label": "Demo Book Appendix", "source_id": "source-demo-book",
                 "locator": "Appendix A"},
                # no id: the pre-v3 shape must keep working
                {"kind": "watch", "label": "Demo companion video",
                 "source_id": "source-demo-book"},
            ],
            "working_note": note_rel, "attachments": [], "source_feedback": [],
        }],
    })
    write_yaml(root / "curriculum/resume.yaml", {
        "type": "resume-pointer", "module_id": "module-demo", "unit_id": "unit-demo-l01",
        "study_map_id": "study-map-demo-l01", "stage_id": "stage-demo",
        "updated": "2026-08-03",
    })
    ws_path = root / "work/active/workspace-demo/CONTEXT.md"
    meta, body = parse_frontmatter(ws_path.read_text(encoding="utf-8"), ws_path)
    meta.update({"program_ids": ["program-bachelors"], "module_ids": ["module-demo"],
                 "unit_ids": ["unit-demo-l01"]})
    ws_path.write_text("---\n" + yaml.safe_dump(meta, sort_keys=False).rstrip() +
                       "\n---\n\n" + body.lstrip(), encoding="utf-8")


def _add_material_overview(root: Path, *, covers=None, builds_on=None) -> None:
    """Give the synthetic lecture one v5 knowledge map and rich source route."""
    unit_path = root / "curriculum/modules/module-demo/units/unit-demo-l01/unit.yaml"
    unit = yaml.safe_load(unit_path.read_text(encoding="utf-8"))
    unit["knowledge_map"] = {
        "summary": "Expected value connects outcome values to their probabilities.",
        "nodes": [
            {
                "id": "knowledge-demo-outcomes",
                "title": "Outcome values",
                "summary": "A random variable assigns a number to each outcome.",
            },
            {
                "id": "knowledge-demo-expectation",
                "title": "Probability-weighted average",
                "summary": "Expectation weights every value by its probability.",
                "builds_on": builds_on or ["knowledge-demo-outcomes"],
            },
        ],
    }
    write_yaml(unit_path, unit)

    source_map_path = root / "curriculum/modules/module-demo/source-map.yaml"
    source_map = yaml.safe_load(source_map_path.read_text(encoding="utf-8"))
    source_map["sources"][0]["unit_routes"] = [{
        "unit_id": "unit-demo-l01",
        "title": "Demo book — expected-value derivation",
        "format": "book",
        "angle": "Derives the weighted sum and works a discrete example.",
        "covers": covers or ["knowledge-demo-outcomes", "knowledge-demo-expectation"],
        "depth": "derivation",
        "scope": "current",
        "locator": "lecture-01.pdf",
    }]
    write_yaml(source_map_path, source_map)

    registry_path = root / "sources/sources.yaml"
    registry = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    registry["sources"][0]["material"] = "material://source-demo-book/book.pdf"
    write_yaml(registry_path, registry)


def rich_fixture(root):
    """Curriculum plus one rich route, with the selection wired to it.

    Returns the deterministic route id and the route dict. Public because
    several test modules share it; behaviour is unchanged from the helper
    that lived in `test_manifest_v7_routes.py`.
    """
    add_curriculum(root)
    _add_material_overview(root)
    source_map_path = root / "curriculum/modules/module-demo/source-map.yaml"
    source_map = yaml.safe_load(source_map_path.read_text(encoding="utf-8"))
    route = source_map["sources"][0]["unit_routes"][0]
    route_id = deterministic_route_id(
        "module-demo", "source-demo-book", route
    )
    unit_path = root / "curriculum/modules/module-demo/units/unit-demo-l01/unit.yaml"
    unit = yaml.safe_load(unit_path.read_text(encoding="utf-8"))
    unit["source_selections"][0]["locator"] = route["locator"]
    unit["knowledge_map"]["nodes"][1]["concept_ids"] = [
        "concept-expected-value"
    ]
    write_yaml(unit_path, unit)
    return route_id, route
