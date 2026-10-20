import sys, hashlib
from pathlib import Path
sys.path.insert(0, "lib")
import canvaslib as C

w = C.build_world(Path("..") / "worlds", "probe-e1f")
src = w.root / "curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml"
text = src.read_text(encoding="utf-8")

text = text.replace("id: study-map-demo-l01\ntype: study-map\n",
                    "id: study-map-demo-l01\ntype: study-map\nplan_template_version: 1\n")
text = text.replace("- id: stage-demo\n", "- id: stage-demo\n  number: 1\n")
text = text.replace("- id: stage-demo-pending\n", "- id: stage-demo-pending\n  number: 2\n")
agent_stage = """- id: stage-agent-third
  number: 3
  title: Scope the agent decided on its own
  status: pending
  objective: Process a lecture the agent scoped by itself.
  done_when:
  - A human never approved this scope.
  exam_critical: false
  concepts: []
  scope_triage: required-now
  resources:
  - kind: read
    label: Demo Book §9
    source_id: source-demo-book
    locator: §9
  working_note: curriculum/modules/module-demo/units/unit-demo-l01/stages/stage-agent-third/notes.md
  attachments: []
  source_feedback: []
"""
text = text.rstrip("\n") + "\n" + agent_stage
body = w.scratch("agent-study-map.yaml")
body.write_text(text, encoding="utf-8")
digest = "sha256:" + hashlib.sha256(body.read_bytes()).hexdigest()
payload = {"unit_id": "unit-demo-l01", "file": str(body),
           "file_sha256": digest, "replace": True}
seal, apply = w.write("unit.map.import", payload, "e1f-probe")
print("SEAL exit", seal.exit_code, "|", seal.stderr[:700])
print("APPLY exit", apply.exit_code)
after = src.read_text(encoding="utf-8")
print("AGENT STAGE LANDED:", "stage-agent-third" in after)
v = w.los("validate")
print("VALIDATE exit", v.exit_code, [l for l in v.stdout.splitlines() if l.startswith("E ")][:4])
