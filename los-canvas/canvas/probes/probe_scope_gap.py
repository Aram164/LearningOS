"""Probe: can a stage name a source the module's source map never adopted?"""
import sys, hashlib, yaml
from pathlib import Path
sys.path.insert(0, "lib")
import canvaslib as C

w = C.build_world(Path("..") / "worlds", "probe-scope-gap")

# 1. Register a source globally (through the gateway).
import json as _json
_record = {"records": [{
    "action": "create", "id": "source-probe-offmap", "partition": "sources.yaml",
    "title": "Probe source not in the module map", "type": "book",
    "authors": ["Probe"], "year": 2026,
    "discovery": {"observed": "2026-10-20",
                  "basis": [{"kind": "catalogue-entry",
                             "ref": "https://example.invalid/probe"}],
                  "possible_use": "Probe."}}]}
_check = w.los("source-intake", "--record", _json.dumps(_record), "--check", "--json")
_diff = (_check.json or {}).get("diff_sha256")
seal, apply = w.write("source.intake.record",
                      {"record": _record, "expected_diff_sha256": _diff},
                      "probe-source")
print("source registered:", (apply.json or {}).get("ok"), apply.stderr.strip()[:200])

# 2. Which sources does module-demo's source map actually declare?
sm = yaml.safe_load((w.root / "curriculum/modules/module-demo/source-map.yaml").read_text())
declared = {e["source_id"] for e in sm["sources"]}
print("module-demo declares:", sorted(declared))
print("probe source in module map:", "source-probe-offmap" in declared)

# 3. Put it on a stage, with a locator no route declares.
src = w.root / "curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml"
text = src.read_text(encoding="utf-8")
text = text.replace("id: study-map-demo-l01\ntype: study-map\n",
                    "id: study-map-demo-l01\ntype: study-map\nplan_template_version: 1\n")
text = text.replace("- id: stage-demo\n",
                    "- id: stage-demo\n  number: 1\n  exam_critical: false\n  concepts: []\n")
text = text.replace("- id: stage-demo-pending\n",
                    "- id: stage-demo-pending\n  number: 2\n  exam_critical: false\n  concepts: []\n")
text = text.rstrip("\n") + """
- id: stage-probe-offmap
  number: 3
  title: A stage on material the module never adopted
  status: pending
  objective: Read a book this module never listed.
  done_when:
  - The scope was invented by an agent.
  exam_critical: false
  concepts: []
  scope_triage: required-now
  resources:
  - kind: read
    label: Probe Book chapter 42
    source_id: source-probe-offmap
    locator: chapter 42
  working_note: curriculum/modules/module-demo/units/unit-demo-l01/stages/stage-probe-offmap/notes.md
  attachments: []
  source_feedback: []
"""
body = w.scratch("probe-map.yaml")
body.write_text(text, encoding="utf-8")
seal, apply = w.write("unit.map.import", {
    "unit_id": "unit-demo-l01", "file": str(body),
    "file_sha256": "sha256:" + hashlib.sha256(body.read_bytes()).hexdigest(),
    "replace": True}, "probe-map")
print("map import:", apply.exit_code, apply.stderr.strip()[:200])
print("stage landed:", "stage-probe-offmap" in src.read_text(encoding="utf-8"))
v = w.los("validate")
errs = [l for l in v.stdout.splitlines() if l.startswith("E ")]
print("VALIDATE exit:", v.exit_code, "| errors:", errs[:4])
