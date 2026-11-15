"""Direct tests for the ``workspace.complete`` capability (PLAN D-15)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent


def _run_los(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(REPO_ROOT / "tools" / "los.py"), "--root", str(root), *args],
        text=True,
        capture_output=True,
    )


def _seal_and_submit(
    root: Path,
    *,
    workspace_id: str,
    key: str,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "tools" / "seal_envelope.py"),
            "--root",
            str(root),
            "--capability",
            "workspace.complete",
            "--payload",
            json.dumps({"workspace_id": workspace_id}),
            "--key",
            key,
            "--request-id",
            f"request-{key}",
            "--guards",
            "auto",
            "--submit",
        ],
        text=True,
        capture_output=True,
    )


def test_complete_marks_active_workspace_complete_and_preserves_body(mini_repo: Path):
    ws_path = mini_repo / "work" / "active" / "workspace-demo" / "CONTEXT.md"
    before = ws_path.read_text(encoding="utf-8")
    _, _head, body_before = before.split("---\n", 2)

    proc = _seal_and_submit(mini_repo, workspace_id="workspace-demo", key="ws-complete-1")
    assert proc.returncode == 0, proc.stderr
    envelope = json.loads(proc.stdout)
    assert envelope["ok"] is True
    assert envelope["result"]["status"] == "complete"
    assert envelope["result"]["workspace_id"] == "workspace-demo"
    assert envelope["result"]["artifact_revisions"] == {"workspace-demo": 1}

    after = ws_path.read_text(encoding="utf-8")
    _, head_after, body_after = after.split("---\n", 2)
    meta_after = yaml.safe_load(head_after)
    assert meta_after["status"] == "complete"
    assert body_after.lstrip("\n") == body_before.lstrip("\n")


def test_bare_cli_command_never_writes(mini_repo: Path):
    ws_path = mini_repo / "work" / "active" / "workspace-demo" / "CONTEXT.md"
    before = ws_path.read_text(encoding="utf-8")
    proc = _run_los(mini_repo, "workspace-complete", "workspace-demo")
    assert proc.returncode == 2
    assert "gateway" in proc.stderr.lower()
    assert ws_path.read_text(encoding="utf-8") == before


def test_refuses_standing_workspace(mini_repo: Path):
    ws_path = mini_repo / "work" / "active" / "workspace-demo" / "CONTEXT.md"
    raw = ws_path.read_text(encoding="utf-8")
    ws_path.write_text(
        raw.replace("status: active\n", "status: active\nstanding: true\n", 1),
        encoding="utf-8",
    )
    proc = _seal_and_submit(mini_repo, workspace_id="workspace-demo", key="ws-standing")
    assert proc.returncode == 2
    assert "standing" in proc.stderr


def test_refuses_already_non_active_workspace(mini_repo: Path):
    ws_path = mini_repo / "work" / "active" / "workspace-demo" / "CONTEXT.md"
    raw = ws_path.read_text(encoding="utf-8")
    ws_path.write_text(raw.replace("status: active", "status: complete", 1), encoding="utf-8")
    proc = _seal_and_submit(mini_repo, workspace_id="workspace-demo", key="ws-already")
    assert proc.returncode == 2
    assert "only an active workspace" in proc.stderr


def test_refuses_when_coordination_references_workspace(mini_repo: Path):
    coord = mini_repo / "work" / "COORDINATION.md"
    coord.write_text(
        coord.read_text(encoding="utf-8") + "\n- Blocked on workspace-demo.\n",
        encoding="utf-8",
    )
    proc = _seal_and_submit(mini_repo, workspace_id="workspace-demo", key="ws-coord")
    assert proc.returncode == 2
    assert "COORDINATION.md" in proc.stderr
