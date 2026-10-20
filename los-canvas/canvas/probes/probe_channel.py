import sys, hashlib
from pathlib import Path
sys.path.insert(0, "lib")
import canvaslib as C

AGENT_STAGE = (
    "- id: stage-agent-third\n  number: 3\n"
    "  title: Scope the agent decided on its own\n"
    "  status: pending\n"
    "  objective: Process a lecture the agent scoped by itself.\n"
    "  done_when:\n  - A human never approved this scope.\n"
    "  exam_critical: false\n  concepts: []\n"
    "  scope_triage: required-now\n  resources:\n"
    "  - kind: read\n    label: Demo Book §9\n"
    "    source_id: source-demo-book\n    locator: §9\n"
    "  working_note: curriculum/modules/module-demo/units/"
    "unit-demo-l01/stages/stage-agent-third/notes.md\n"
    "  attachments: []\n  source_feedback: []\n")

def build(world):
    src = (world.root / "curriculum/modules/module-demo/units/"
                     "unit-demo-l01/study-map.yaml")
    text = src.read_text(encoding="utf-8")
    text = text.replace("id: study-map-demo-l01\ntype: study-map\n",
                        "id: study-map-demo-l01\ntype: study-map\nplan_template_version: 1\n")
    text = text.replace("- id: stage-demo\n",
                        "- id: stage-demo\n  number: 1\n  exam_critical: false\n  concepts: []\n")
    text = text.replace("- id: stage-demo-pending\n",
                        "- id: stage-demo-pending\n  number: 2\n  exam_critical: false\n  concepts: []\n")
    text = text.rstrip("\n") + "\n" + AGENT_STAGE
    body = world.scratch("agent-study-map.yaml")
    body.write_text(text, encoding="utf-8")
    return body, "sha256:" + hashlib.sha256(body.read_bytes()).hexdigest()

for channel, approval in (("codex", "direct-user-gesture"),
                          ("ui", "direct-user-gesture"),
                          ("operator", "operator-approval")):
    w = C.build_world(Path("..") / "worlds", f"probe-ch-{channel}-{approval[:6]}")
    body, digest = build(w)
    payload = {"unit_id": "unit-demo-l01", "file": str(body),
               "file_sha256": digest, "replace": True}
    seal, apply = w.write("unit.map.import", payload,
                           f"ch-{channel}-{approval[:6]}", channel=channel,
                           approval_kind=approval)
    src = (w.root / "curriculum/modules/module-demo/units/"
                     "unit-demo-l01/study-map.yaml")
    landed = "stage-agent-third" in src.read_text(encoding="utf-8")
    print(f"channel={channel:<9} approval={approval:<22} seal={seal.exit_code} apply={apply.exit_code} installed={landed}")
    msg = (seal.stderr.strip() or apply.stderr.strip())[:220]
    if msg:
        print("   ", msg)
