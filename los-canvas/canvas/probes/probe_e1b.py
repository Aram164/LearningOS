import sys, hashlib
from pathlib import Path
sys.path.insert(0, "lib")
import canvaslib as C

w = C.build_world(Path("..") / "worlds", "probe-e1b")
tpl = w.los("plan-template", "curriculum", "--title", "Synthetic agent scope",
            "--unit-id", "unit-demo-l01", "--module-id", "module-demo")
assert tpl.exit_code == 0, tpl.stderr

# The agent extends the template with a stage nobody taught.
agent_stage = """- id: stage-agent-second
  number: 2
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
  working_note: curriculum/modules/module-demo/units/unit-demo-l01/stages/stage-agent-second/notes.md
  attachments: []
  source_feedback: []
"""
text = tpl.stdout
text = text.replace("shelving:\n  state: none\n", agent_stage + "shelving:\n  state: none\n")
body = w.scratch("agent-study-map.yaml")
body.write_text(text, encoding="utf-8")
digest = "sha256:" + hashlib.sha256(body.read_bytes()).hexdigest()

seal, apply = w.write("unit.map.import", {
    "unit_id": "unit-demo-l01",
    "file": str(body),
    "file_sha256": digest,
    "replace": True,
}, "e1b-probe")
print("SEAL exit", seal.exit_code, "|", seal.stderr[:500])
print("APPLY exit", apply.exit_code)
src = w.root / "curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml"
after = src.read_text(encoding="utf-8")
print("AGENT STAGE LANDED:", "stage-agent-second" in after)
print("---- resulting map ----")
print(after[:1400])
v = w.los("validate")
print("VALIDATE exit", v.exit_code, [l for l in v.stdout.splitlines() if l.startswith("E ")][:3])
