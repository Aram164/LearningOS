import sys, hashlib, shutil
from pathlib import Path
sys.path.insert(0, "lib")
import canvaslib as C

w = C.build_world(Path("..") / "worlds", "probe-e1")
src = w.root / "curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml"
text = src.read_text(encoding="utf-8")

agent_stage = """- id: stage-agent-improvised
  knowledge_node_id: knowledge-demo-expectation
  title: Agent-improvised scope
  status: pending
  objective: Scope the next lecture the agent decided on its own.
  done_when:
  - Nothing human was consulted.
  scope_triage: required-now
  resources:
  - kind: read
    label: Demo Book §9
    source_id: source-demo-book
    locator: §9
  working_note: curriculum/modules/module-demo/units/unit-demo-l01/stages/stage-agent-improvised/notes.md
  attachments: []
  source_feedback: []
"""

new_text = text.rstrip("\n") + "\n" + agent_stage
body = w.scratch("agent-study-map.yaml")
body.write_text(new_text, encoding="utf-8")
digest = "sha256:" + hashlib.sha256(body.read_bytes()).hexdigest()

check = w.los("unit-map-import", "unit-demo-l01", "--file", str(body),
              "--file-sha256", digest, "--replace", "--check")
print("CHECK exit", check.exit_code)
print((check.stdout or check.stderr)[:2500])
print()
seal, apply = w.write("unit.map.import", {
    "unit_id": "unit-demo-l01",
    "file": str(body),
    "file_sha256": digest,
    "replace": True,
}, "e1-probe")
print("SEAL exit", seal.exit_code, seal.stderr[:600])
print("APPLY exit", apply.exit_code)
print((apply.stdout or apply.stderr)[:1200])
after = src.read_text(encoding="utf-8")
print("AGENT STAGE LANDED:", "stage-agent-improvised" in after)
