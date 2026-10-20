import sys, hashlib, json
from pathlib import Path
sys.path.insert(0, "lib")
import canvaslib as C

w = C.build_world(Path("..") / "worlds", "probe-e1i")
src = w.root / "curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml"
text = src.read_text(encoding="utf-8")
text = text.replace("id: study-map-demo-l01\ntype: study-map\n",
                    "id: study-map-demo-l01\ntype: study-map\nplan_template_version: 1\n")
text = text.replace("- id: stage-demo\n",
                    "- id: stage-demo\n  number: 1\n  exam_critical: false\n  concepts: []\n")
text = text.replace("- id: stage-demo-pending\n",
                    "- id: stage-demo-pending\n  number: 2\n  exam_critical: false\n  concepts: []\n")
text = text.rstrip("\n") + """
- id: stage-agent-third
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
body = w.scratch("agent-study-map.yaml")
body.write_text(text, encoding="utf-8")
digest = "sha256:" + hashlib.sha256(body.read_bytes()).hexdigest()
seal, apply = w.write("unit.map.import", {
    "unit_id": "unit-demo-l01", "file": str(body),
    "file_sha256": digest, "replace": True}, "e1i-probe")
print("APPLY exit", apply.exit_code)

# 1. Does the study map record who wrote it?
import yaml
data = yaml.safe_load(src.read_text(encoding="utf-8"))
print("MAP TOP-LEVEL KEYS:", sorted(data.keys()))
print("STAGE KEYS:", sorted(data["stages"][-1].keys()))

# 2. Does the receipt record it?
receipts = sorted((w.root / "operations/transactions").glob("transaction-*.yaml"))
last = yaml.safe_load(receipts[-1].read_text(encoding="utf-8"))
print("RECEIPT KEYS:", sorted(last.keys()))
print("RECEIPT capability:", last.get("capability"))
print("RECEIPT channel/session:", {k: last.get(k) for k in ("channel","session_id","request_id","idempotency_key") if k in last})

# 3. Is the agent's stage visible in the operator's surfaces?
for label, args in (("resume", ("resume",)),
                    ("bootstrap-brief", ("bootstrap", "--brief")),
                    ("intelligence-scan", ("intelligence-scan", "--brief", "--json")),
                    ("inspect-stage", ("inspect", "stage-agent-third"))):
    run = w.los(*args)
    hit = "stage-agent-third" in run.stdout or "agent decided" in run.stdout
    print(f"  {label}: exit={run.exit_code} mentions_agent_stage={hit} bytes={len(run.stdout)}")

# 4. Does the UI projection carry it?
w.los_tool("generate.py")
man = json.loads((w.root / "generated/manifest.json").read_text())
print("MANIFEST mentions agent stage:",
      "stage-agent-third" in json.dumps(man))
