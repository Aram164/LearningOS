import sys, hashlib
from pathlib import Path
sys.path.insert(0, "lib")
import canvaslib as C

w = C.build_world(Path("..") / "worlds", "probe-e1c")
tpl = w.los("plan-template", "curriculum", "--title", "Synthetic agent scope",
            "--unit-id", "unit-demo-l01", "--module-id", "module-demo")
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
text = tpl.stdout.replace("shelving:\n  state: none\n",
                          agent_stage + "shelving:\n  state: none\n")
body = w.scratch("agent-study-map.yaml")
body.write_text(text, encoding="utf-8")
digest = "sha256:" + hashlib.sha256(body.read_bytes()).hexdigest()
check = w.los("unit-map-import", "unit-demo-l01", "--file", str(body),
              "--file-sha256", digest, "--replace", "--check")
print("CHECK exit", check.exit_code)
print((check.stdout or check.stderr)[:3000])
