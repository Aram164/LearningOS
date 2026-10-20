import sys, hashlib, copy
from pathlib import Path
sys.path.insert(0, "lib")
import canvaslib as C

def build(w, tpl_text, agent_stage, current_stage=None):
    text = tpl_text.replace("shelving:\n  state: none\n", "")
    text = text.rstrip("\n") + "\n" + agent_stage + "shelving:\n  state: none\n"
    if current_stage:
        text = text.replace("current_stage: stage-synthetic-agent-scope",
                            f"current_stage: {current_stage}")
    text = text.replace("path: replace-with-reviewed-plan.yaml",
                        "path: work/active/workspace-demo/CONTEXT.md")
    body = w.scratch("agent-study-map.yaml")
    body.write_text(text, encoding="utf-8")
    return body, "sha256:" + hashlib.sha256(body.read_bytes()).hexdigest()

AGENT_STAGE = """- id: stage-agent-second
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

for i, variant in enumerate(["plain", "current-stage"]):
    w = C.build_world(Path("..") / "worlds", f"probe-e1g-{i}")
    tpl = w.los("plan-template", "curriculum", "--title", "Synthetic agent scope",
                "--unit-id", "unit-demo-l01", "--module-id", "module-demo")
    cur = "stage-agent-second" if variant == "current-stage" else None
    body, digest = build(w, tpl.stdout, AGENT_STAGE, cur)
    payload = {
        "unit_id": "unit-demo-l01", "file": str(body), "file_sha256": digest,
        "replace": True,
        "retire_stage": ["stage-demo", "stage-demo-pending"],
        "retire_reason": "Agent decided to reprocess this lecture unattended.",
    }
    seal, apply = w.write("unit.map.import", payload, f"e1g-{i}")
    src = w.root / "curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml"
    print(f"### variant={variant}")
    print("  SEAL exit", seal.exit_code, "|", seal.stderr.strip()[:500])
    print("  APPLY exit", apply.exit_code)
    print("  AGENT STAGE LANDED:", "stage-agent-second" in src.read_text(encoding="utf-8"))
