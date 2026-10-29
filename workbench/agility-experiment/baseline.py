#!/usr/bin/env python3
"""Measure three supported plan changes on disposable synthetic repositories.

This is experimental development evidence, not a production writer or a model
benchmark. All mutations target TemporaryDirectory fixtures; no root argument is
accepted. Setup and assertion work is excluded from command/validation timings.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "tools"), str(ROOT / "tests")]

import yaml  # noqa: E402
from conftest import build_mini_repo  # noqa: E402
from repo_builders import (  # noqa: E402
    SLICED_LECTURE_TEXT,
    _compact_setup,
    _plan_contract,
    write_yaml,
)

from learning_os.app.validation_service import collect  # noqa: E402
from learning_os.store.contracts.gateway import intent_sha256  # noqa: E402
from learning_os.store.fingerprint import canonical_fingerprint  # noqa: E402
from learning_os.store.warning_baseline import write_baseline  # noqa: E402

MODULE = "curriculum/modules/module-demo"
UNIT = MODULE + "/units/unit-demo-l01"
MAP = UNIT + "/study-map.yaml"

INSTRUMENT = '''\
import json, os, time
from learning_os.derive.validation.core import Validator
original = Validator.run
def measured(self):
    start = time.perf_counter()
    try:
        return original(self)
    finally:
        with open(os.environ["LOS_AGILITY_VALIDATIONS"], "a") as stream:
            stream.write(json.dumps({"seconds": time.perf_counter() - start}) + "\\n")
Validator.run = measured
'''


def read(root: Path, path: str) -> dict:
    return yaml.safe_load((root / path).read_text(encoding="utf-8"))


def owned_bytes(root: Path) -> dict[str, bytes]:
    """The fixture's authored data, excluding receipts and disposable output."""
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for directory in ("curriculum", "knowledge", "sources", "records", "work")
        for path in sorted((root / directory).rglob("*"))
        if path.is_file()
    }


def prepare(base: Path, stages: int = 1) -> tuple[Path, dict]:
    root = build_mini_repo(base)
    _compact_setup(root)
    study = read(root, MAP)
    study["plan_template_version"] = 1
    first = study["stages"][0]
    first.update(number=1, exam_critical=False, concepts=[])
    first["resources"][0]["id"] = "resource-demo-original"
    for number in range(2, stages + 1):
        stage = copy.deepcopy(first)
        stage.update(id=f"stage-demo-{number}", number=number,
                     title=f"Stage {number}", status="pending")
        stage["working_note"] = f"{UNIT}/stages/{stage['id']}/notes.md"
        stage["resources"][0]["id"] = f"resource-demo-{number}"
        note = root / stage["working_note"]
        note.parent.mkdir(parents=True)
        note.write_text("", encoding="utf-8")
        study["stages"].append(stage)
    write_yaml(root / MAP, study)
    write_baseline(root, collect(root)[0], "agility baseline fixture")
    return root, study


def execute(root: Path, argv: list[str], env: dict, rows: list) -> dict:
    start = time.perf_counter()
    result = subprocess.run(
        [sys.executable, str(ROOT / "tools/los.py"), "--root", str(root), *argv],
        text=True, capture_output=True, env=env, timeout=120,
    )
    rows.append({"command": argv[0], "seconds": time.perf_counter() - start,
                 "stdout_bytes": len(result.stdout.encode("utf-8"))})
    if result.returncode:
        raise RuntimeError(f"{argv[0]} refused:\n{result.stdout}\n{result.stderr}")
    return json.loads(result.stdout)


def run_scenario(base: Path, name: str, stage_count: int = 1, *, proportional: bool = False) -> dict:
    root, study = prepare(base, stages=stage_count)
    contract = _plan_contract("work/active/workspace-demo/outputs/demo-coverage-audit.md")
    command, target = "module-plan-import", "module-demo"
    extra: list[str] = []
    reason = "Move the second activity before the first for this fixture review."
    if name == "append-resource":
        package = {
            "module_id": target, "plan_contract": contract,
            "unit_revisions": [{"unit_id": "unit-demo-l01", "stage_patches": [{
                "stage_id": "stage-demo", "resources_append": [{
                    "id": "resource-demo-added", "kind": "read",
                    "scope_triage": "helpful-now", "material_ref": {
                        "route_id": "route-demo-book",
                        "inherit": ["label", "source_id", "locator", "angle", "angle_detail"],
                    },
                }],
            }]}],
        }
        repeated_stages, repeated_routes = 0, 0
    elif name == "move-stage":
        command, target = "unit-map-import", "unit-demo-l01"
        package = copy.deepcopy(study)
        package["stages"][0:2] = reversed(package["stages"][0:2])
        for number, stage in enumerate(package["stages"], 1):
            stage["number"] = number
        extra = ["--replace", "--intentional-reorder", reason]
        repeated_stages, repeated_routes = len(study["stages"]), 0
    else:
        module = read(root, MODULE + "/module.yaml")
        source_map = read(root, MODULE + "/source-map.yaml")
        repeated_routes = sum(len(row.get("unit_routes", [])) for row in source_map["sources"])
        new_route = copy.deepcopy(source_map["sources"][0]["unit_routes"][0])
        new_route.update(id="route-demo-book-l02", unit_id="unit-demo-l02",
                         locator="lecture-01.pdf, PDF p. 1")
        source_map["sources"][0]["unit_routes"].append(new_route)
        unit = copy.deepcopy(read(root, UNIT + "/unit.yaml"))
        unit.update(id="unit-demo-l02", title="Second lecture", order=2,
                    status="ready", current_study_map="study-map-demo-l02",
                    source_selections=[], workspace_ids=[])
        new_map = copy.deepcopy(study)
        new_map.update(id="study-map-demo-l02", unit_id="unit-demo-l02",
                       status="ready", current_stage="stage-demo-l02")
        stage = new_map["stages"][0]
        stage.update(id="stage-demo-l02", status="pending", attachments=[],
                     knowledge_node_id=new_route["covers"][0],
                     source_feedback=[], working_note=f"{MODULE}/units/unit-demo-l02/stages/stage-demo-l02/notes.md")
        stage.pop("completed", None)
        stage["resources"] = [{
            "id": "resource-demo-l02", "kind": "read", "scope_triage": "required-now",
            "material_ref": {"route_id": "route-demo-book-l02",
                             "inherit": ["label", "source_id", "locator", "angle", "angle_detail"]},
        }]
        package = {
            "module_id": target, "plan_contract": contract,
            "module_patch": {"unit_order": [*module["unit_order"], "unit-demo-l02"]},
            "source_map": source_map, "units": [{"unit": unit, "study_map": new_map}],
            "claim_evidence": [{"claim_id": "covers:route-demo-book-l02", "evidence": [{
                "kind": "quote", "ref": "material://source-demo-book/lecture-01.pdf",
                "page": 1, "text": SLICED_LECTURE_TEXT,
            }]}],
        }
        repeated_stages = 0

    if proportional and name == "move-stage":
        command, target, extra = "unit-map-import", "unit-demo-l01", ["--replace"]
        package = {"unit_id": target, "structural_edit": {
            "reason": reason, "stage_move": {"stage_id": "stage-demo-2", "before_id": "stage-demo"}}}
        repeated_stages = 0
    elif proportional and name == "add-unit":
        entry = package["units"][0]
        route = package["source_map"]["sources"][0]["unit_routes"][-1]
        package = {"module_id": target, "plan_contract": contract,
                   "unit_additions": [{**entry, "routes": [{"source_id": "source-demo-book", "route": route}]}],
                   "claim_evidence": package["claim_evidence"]}
        repeated_routes = 0

    draft = base / "draft.yaml"
    write_yaml(draft, package)
    before = owned_bytes(root)
    snapshot = canonical_fingerprint(root)
    instrumentation = base / "instrumentation"
    instrumentation.mkdir()
    (instrumentation / "sitecustomize.py").write_text(INSTRUMENT, encoding="utf-8")
    validation_log = base / "validation.jsonl"
    env = {**os.environ, "LOS_AGILITY_VALIDATIONS": str(validation_log),
           "PYTHONPATH": os.pathsep.join([str(instrumentation), str(ROOT / "tools")])}
    commands: list[dict] = []
    check = execute(root, [command, target, "--file", str(draft), *extra, "--check"], env, commands)
    if check.get("canonical_files_written") != 0 or canonical_fingerprint(root) != snapshot:
        raise AssertionError("preflight changed canonical state")
    review = base / "review.json"
    review.write_text(json.dumps(check), encoding="utf-8")
    if command == "unit-map-import":
        # Scripted review of the returned exact file digest, snapshot and
        # revisions. No live refresh or approval inferred from check success.
        envelope = {
            "schema_version": 2, "request_id": "request-agility-move-stage",
            "idempotency_key": "agility-move-stage", "capability": "unit.map.import",
            "channel": "ui", "expected_snapshot": check["snapshot_id"],
            "expected_revisions": check["expected_revisions"],
            "approval": {"kind": "direct-user-gesture", "subject_sha256": "sha256:" + "0" * 64},
            "payload": {"unit_id": target, "file": str(draft),
                        "file_sha256": check["file_sha256"], "replace": True,
                        **({"intentional_reorder": reason} if not proportional else {})},
        }
        envelope["approval"]["subject_sha256"] = intent_sha256(envelope)
        approved = base / "approved.json"
        approved.write_text(json.dumps(envelope), encoding="utf-8")
        apply = execute(root, ["capability", "unit.map.import", "--payload-file", str(approved)], env, commands)
    else:
        apply = execute(root, [command, target, "--file", str(draft),
                              "--review-report", str(review), "--apply-reviewed-sha256",
                              check["reviewed_file_sha256"]], env, commands)
    if apply.get("ok") is not True:
        raise AssertionError(apply)
    after = owned_bytes(root)
    changed = sorted(path for path in before.keys() | after.keys() if before.get(path) != after.get(path))
    after_map = read(root, MAP)
    if name == "append-resource":
        expected = copy.deepcopy(study)
        expected["stages"][0]["resources"].append(package["unit_revisions"][0]["stage_patches"][0]["resources_append"][0])
        assert after_map == expected
        assert changed == [MAP]
    elif name == "move-stage":
        expected = copy.deepcopy(study)
        expected["stages"][0:2] = reversed(expected["stages"][0:2])
        for number, stage in enumerate(expected["stages"], 1):
            stage["number"] = number
        assert after_map == expected
        assert changed == [MAP]
    else:
        assert after[MAP] == before[MAP]
        assert read(root, MODULE + "/module.yaml")["unit_order"][-1] == "unit-demo-l02"
        for path, content in before.items():
            if path not in {MODULE + "/module.yaml", MODULE + "/source-map.yaml"}:
                assert after[path] == content, path
    receipts = list((root / "operations/transactions").glob("transaction-*.yaml"))
    assert len(receipts) == 1
    validations = [json.loads(line) for line in validation_log.read_text().splitlines()] if validation_log.exists() else []
    return {
        "scenario": name, "existing_stages": stage_count,
        "proportional_intent": proportional,
        "input_bytes": draft.stat().st_size,
        "existing_stage_records_reproduced": repeated_stages,
        "existing_route_records_reproduced": repeated_routes,
        "commands": commands, "command_count": len(commands),
        "validation_runs": len(validations),
        "validation_seconds": sum(row["seconds"] for row in validations),
        "authored_files_changed": changed, "receipt_count": len(receipts),
        "preservation": "passed", "preflight_writes": 0,
        "model_decision_cycles": None, "model_tokens": None, "user_steps": None,
        "draft_sha256": hashlib.sha256(draft.read_bytes()).hexdigest(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--proportional", action="store_true", help="measure Stage 5 stable-ID edits instead of replacement drafts")
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="los-agility-") as scratch:
        rows = []
        for name, stage_count in (("append-resource", 1), ("move-stage", 2),
                                  ("move-stage", 10), ("move-stage", 50), ("add-unit", 1)):
            base = Path(scratch) / f"{name}-{stage_count}"
            base.mkdir()
            rows.append(run_scenario(base, name, stage_count, proportional=args.proportional))
    result = {
        "scope": "scripted synthetic fixtures; warm development environment; no model calls",
        "review": "scripted exact-content review; does not measure human review quality",
        "core_base": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "python": sys.version.split()[0],
        "source_sha256": {
            path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
            for path in ("workbench/agility-experiment/baseline.py", "tests/conftest.py",
                         "tests/repo_builders.py", "tools/learning_os/app/handlers/plan.py",
                         "tools/learning_os/app/handlers/maps.py", "tools/learning_os/app/_plan_gate.py",
                         "tools/learning_os/domain/plan_import.py")
        },
        "scenarios": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
