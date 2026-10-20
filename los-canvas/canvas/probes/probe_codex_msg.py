import sys, hashlib
from pathlib import Path
sys.path.insert(0, "lib")
import canvaslib as C
exec(open("probe_channel.py").read().split("for channel, approval")[0].split("import canvaslib as C")[1])
w = C.build_world(Path("..") / "worlds", "probe-ch-codex-msg")
body, digest = build(w)
seal, apply = w.write("unit.map.import", {
    "unit_id": "unit-demo-l01", "file": str(body),
    "file_sha256": digest, "replace": True}, "codex-msg",
    channel="codex", approval_kind="direct-user-gesture")
print("APPLY exit:", apply.exit_code)
print("STDERR:", apply.stderr.strip()[:600])
print("STDOUT:", apply.stdout.strip()[:900])
