#!/usr/bin/env python3
"""Reproduce FIX-BRIEF-F01 Part A: can an agent install its own scope authority?

A source that is registered globally but is NOT in the module's source map is
placed on a stage at a locator no reviewed route declares, with no route_id.
The claim under test: the map import succeeds and the repository validates with
zero errors.

Run with the repository's own venv:
  PYTHONPATH=<repo>/tests <repo>/.venv/bin/python repro_part_a.py <repo>
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import yaml

REPO = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(REPO / "tests"))

from conftest import build_mini_repo  # noqa: E402
from gateway_helpers import approved_v2_cli  # noqa: E402
from repo_builders import add_curriculum, write_yaml  # noqa: E402

OUTSIDE_SOURCE = "source-demo-outside"   # registered globally, not in the module map
OUTSIDE_LOCATOR = "chapter 42"           # no reviewed route declares this


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    root = REPO.parent / "repro-part-a-world"
    if root.exists():
        subprocess.run(["rm", "-rf", str(root)], check=True)
    root.mkdir(parents=True)
    mini = build_mini_repo(root)
    add_curriculum(mini)

    # 1. Register a second source in the GLOBAL sources registry.
    registry_path = mini / "sources/sources.yaml"
    registry = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    registry["sources"].append({
        "id": OUTSIDE_SOURCE,
        "title": "A source the module never adopted",
        "type": "book",
        "material": "material://source-demo-outside/other.pdf",
    })
    write_yaml(registry_path, registry)

    # 2. Give the module a second unit that owes a study map.
    module_path = mini / "curriculum/modules/module-demo/module.yaml"
    module = yaml.safe_load(module_path.read_text(encoding="utf-8"))
    module["unit_order"].append("unit-demo-l02")
    write_yaml(module_path, module)
    unit_dir = module_path.parent / "units/unit-demo-l02"
    write_yaml(unit_dir / "unit.yaml", {
        "id": "unit-demo-l02", "type": "unit", "module_id": "module-demo",
        "kind": "lecture", "title": "Variance", "order": 2, "scope": "Lecture 2.",
        "status": "needs-map", "scope_sources": [], "source_selections": [],
        "artifacts": {}, "workspace_ids": [],
    })

    # 3. A study map whose stage teaches material the module never adopted.
    note_rel = ("curriculum/modules/module-demo/units/unit-demo-l02/"
                "stages/stage-variance/notes.md")
    incoming = root / "map.yaml"
    write_yaml(incoming, {
        "id": "study-map-demo-l02", "type": "study-map", "unit_id": "unit-demo-l02",
        "plan_template_version": 1,
        "status": "ready", "current_stage": "stage-variance",
        "source_plan": {"path": "proposal.json", "provenance": "ai-proposed"},
        "detours": [], "shelving": {"state": "none"},
        "stages": [{
            "id": "stage-variance", "number": 1, "title": "Variance",
            "status": "pending", "objective": "Derive variance.",
            "done_when": ["Derive it."], "exam_critical": False, "concepts": [],
            "scope_triage": "required-now",
            "resources": [{
                "kind": "read",
                "label": "Chapter 42 of a source the module never adopted",
                "source_id": OUTSIDE_SOURCE,
                "locator": OUTSIDE_LOCATOR,
                "scope_triage": "required-now",
            }],
            "working_note": note_rel, "attachments": [], "source_feedback": [],
        }],
    })

    proc = approved_v2_cli(
        mini, "unit-map-import", "unit-demo-l02", "--file", str(incoming),
        "--file-sha256", "sha256:" + sha256_file(incoming),
        artifact_ids=["unit-demo-l02", "study-map-demo-l02"],
        idempotency_key="repro-part-a",
    )
    print("=== map import ===")
    print("exit:", proc.returncode)
    print((proc.stderr or proc.stdout).strip()[:600])

    landed = False
    unit_yaml = unit_dir / "unit.yaml"
    if unit_yaml.is_file():
        landed = yaml.safe_load(unit_yaml.read_text(encoding="utf-8")).get(
            "current_study_map") == "study-map-demo-l02"
    print("stage landed:", landed)

    # 4. Validate the repository.
    print()
    print("=== validate ===")
    val = subprocess.run(
        [str(REPO / ".venv/bin/python"), "tools/validate.py", "--no-report"],
        cwd=REPO, capture_output=True, text=True,
    )
    print("VALIDATE exit:", val.returncode)
    tail = (val.stdout or "") + (val.stderr or "")
    for line in tail.strip().splitlines()[-6:]:
        print("   ", line)
    errors = [l for l in tail.splitlines() if l.startswith("E ")]
    print("error lines:", len(errors))
    for e in errors[:5]:
        print("   ", e)

    print()
    print("RESULT:",
          "DEFECT REPRODUCED — scope accepted, validation clean"
          if proc.returncode == 0 and landed and val.returncode == 0
          else "not reproduced")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
