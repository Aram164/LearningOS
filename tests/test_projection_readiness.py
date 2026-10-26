"""Shared readiness uses real gateway authority and exact projection bytes."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from learning_os.app.projection_readiness import (
    dependency_ready,
    observe,
    receipt_completed,
    settlement_ready,
)

ROOT = Path(__file__).resolve().parents[1]


def capture(root, key):
    proc = subprocess.run([sys.executable, str(ROOT / "tools/seal_envelope.py"),
        "--root", str(root), "--session-id", "readiness-test", "--capability", "capture.create",
        "--payload", json.dumps({"text": key}), "--key", key, "--submit"],
        capture_output=True, text=True)
    assert proc.returncode == 0, (proc.stdout, proc.stderr)
    response = json.loads(proc.stdout)
    return {"receipt_path": response["receipt_path"], "snapshot_after": response["snapshot_after"]}


def test_dependency_ready_at_latest_and_later_known_write(mini_repo):
    a = capture(mini_repo, "ready-a")
    b = capture(mini_repo, "ready-b")
    assert dependency_ready(mini_repo, [a], [a, b]) == (True, "ready")
    assert dependency_ready(mini_repo, [b], [a])[0] is False
    assert dependency_ready(mini_repo, [a, b], [a, b]) == (True, "ready")


def test_unknown_projection_and_missing_receipt_refuse(mini_repo):
    a = capture(mini_repo, "ready-a")
    assert not receipt_completed(mini_repo, a["receipt_path"], "sha256:wrong")
    bad = {"receipt_path": "operations/transactions/nope.yaml", "snapshot_after": a["snapshot_after"]}
    assert not dependency_ready(mini_repo, [bad], [bad])[0]
    path = mini_repo / "generated/manifest.json"
    data = json.loads(path.read_text())
    data["_generated"]["snapshot_id"] = "sha256:wrong"
    path.write_text(json.dumps(data))
    assert observe(mini_repo)["published"] is False


def test_settlement_mode_separates_completion_from_currency(mini_repo):
    a = capture(mini_repo, "ready-a")
    capture(mini_repo, "ready-b")
    out = settlement_ready(mini_repo, a["receipt_path"], a["snapshot_after"])
    assert out["write_completed"] is True and out["settled"] is True
    assert out["current_snapshot_id"] != a["snapshot_after"]
    # Authored edits without publication invalidate currency, not history.
    note = mini_repo / "knowledge/notes/mathematics/note-demo.md"
    note.write_text(note.read_text() + "\nNew authored text.\n")
    out = settlement_ready(mini_repo, a["receipt_path"], a["snapshot_after"])
    assert out["write_completed"] is True and out["settled"] is False


def test_forged_receipt_is_not_completion(mini_repo):
    path = mini_repo / "operations/transactions/forged.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("status: committed\nsnapshot_after: sha256:fake\n")
    assert not receipt_completed(mini_repo, str(path.relative_to(mini_repo)), "sha256:fake")
