"""Probe: what did the F-01 A fix close, and what did it leave?

The fix requires a stage resource to resolve to material its module
adopted. Two cases must be distinguished:

  A. the resource names a source the module's source map never adopted
     -> the case the fix was written for;
  B. the resource names an ADOPTED source, at a locator no route in the
     module's map declares
     -> the narrower case, which the source-level rule may not reach.

Run against both trees and compare.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))

import canvaslib as C          # noqa: E402

UNIT = "unit-demo-l01"


def sha(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def stage_text(source_id: str, locator: str) -> str:
    return (
        "- id: stage-probe-scope\n"
        "  number: 3\n"
        "  title: A stage on material the module never adopted\n"
        "  status: pending\n"
        "  objective: Read a book this module never listed.\n"
        "  done_when:\n  - The scope was invented by an agent.\n"
        "  exam_critical: false\n  concepts: []\n"
        "  scope_triage: required-now\n"
        "  resources:\n"
        "  - kind: read\n"
        "    label: Probe reader chapter 42\n"
        f"    source_id: {source_id}\n"
        f"    locator: {locator}\n"
        "  working_note: curriculum/modules/module-demo/units/"
        "unit-demo-l01/stages/stage-probe-scope/notes.md\n"
        "  attachments: []\n  source_feedback: []\n")


def probe(world: C.World, label: str, source_id: str, locator: str) -> dict:
    """Register the source if needed, then try to place a stage on it."""
    if source_id not in ("source-demo-book",):
        record = {"records": [{
            "action": "create", "id": source_id, "partition": "sources.yaml",
            "title": "Probe source not in the module map", "type": "book",
            "authors": ["Probe"], "year": 2026,
            "discovery": {"observed": "2026-10-19",
                          "basis": [{"kind": "catalogue-entry",
                                     "ref": "https://example.invalid/probe"}],
                          "possible_use": "Probe."}}]}
        check = world.los("source-intake", "--record", json.dumps(record),
                           "--check", "--json")
        diff = (check.json or {}).get("diff_sha256") if isinstance(
            check.json, dict) else None
        world.write("source.intake.record",
                    {"record": record, "expected_diff_sha256": diff},
                    f"probe-src-{label.split('.')[0].strip().lower()}")

    src = (world.root / "curriculum/modules/module-demo/units/"
                         f"{UNIT}/study-map.yaml")
    text = src.read_text(encoding="utf-8")
    text = text.replace("id: study-map-demo-l01\ntype: study-map\n",
                        "id: study-map-demo-l01\ntype: study-map\n"
                        "plan_template_version: 1\n")
    text = text.replace("- id: stage-demo\n",
                        "- id: stage-demo\n  number: 1\n  exam_critical: false\n"
                        "  concepts: []\n")
    text = text.replace("- id: stage-demo-pending\n",
                        "- id: stage-demo-pending\n  number: 2\n"
                        "  exam_critical: false\n  concepts: []\n")
    text = text.rstrip("\n") + "\n" + stage_text(source_id, locator)
    body = world.scratch("probe-map.yaml")
    body.write_text(text, encoding="utf-8")
    seal, apply = world.write("unit.map.import", {
        "unit_id": UNIT, "file": str(body),
        "file_sha256": sha(body), "replace": True},
        f"probe-map-{label.split('.')[0].strip().lower()}")
    landed = "stage-probe-scope" in src.read_text(encoding="utf-8")
    body = apply.json
    error = (body or {}).get("error") if isinstance(body, dict) else None
    validate = world.los("validate")
    return {
        "case": label,
        "source_id": source_id,
        "locator": locator,
        "seal_exit": seal.exit_code,
        "apply_exit": apply.exit_code,
        "refusal": (seal.stderr.strip() or apply.stderr.strip())[:300],
        "error_code": (error or {}).get("code") if isinstance(error, dict) else None,
        "error_message": ((error or {}).get("message")
                           if isinstance(error, dict) else None),
        "stage_landed": landed,
        "validate_exit": validate.exit_code,
        "validate_errors": [l for l in validate.stdout.splitlines()
                             if l.startswith("E ")][:3],
    }


def main() -> int:
    out = {"tree": str(C.CORE_CLONE), "cases": []}
    for label, source_id, locator in (
        ("A. source the module never adopted",
         "source-probe-offmap", "chapter 42"),
        ("B. adopted source, locator no route declares",
         "source-demo-book", "§9"),
    ):
        world = C.build_world(Path("..") / "worlds",
                               f"scope-{label.split('.')[0]}")
        out["cases"].append(probe(world, label, source_id, locator))
        print(f"--- {label}")
        for key, value in out["cases"][-1].items():
            print(f"    {key}: {value}")
        print()
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
