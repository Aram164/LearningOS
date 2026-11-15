"""Locking and temp-file hygiene for projection publication (D-08)."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from learning_os.app.lock import operator_lock
from learning_os.derive.projection.outputs import _remove_stale

REPO_ROOT = Path(__file__).resolve().parent.parent
GENERATE = REPO_ROOT / "tools" / "generate.py"


def test_generate_refuses_when_operator_lock_held(mini_repo: Path):
    gen_manifest = mini_repo / "generated" / "manifest.json"
    before = gen_manifest.read_bytes() if gen_manifest.is_file() else None
    env = {**os.environ, "LOS_LOCK_TIMEOUT": "0"}
    with operator_lock(mini_repo):
        proc = subprocess.run(
            [sys.executable, str(GENERATE), "--root", str(mini_repo)],
            capture_output=True, text=True, timeout=60, env=env,
        )
    assert proc.returncode == 2
    assert "operator lock" in proc.stdout + proc.stderr
    after = gen_manifest.read_bytes() if gen_manifest.is_file() else None
    assert after == before


def test_remove_stale_preserves_declared_output_temp_files(mini_repo: Path):
    gen = mini_repo / "generated"
    gen.mkdir(parents=True, exist_ok=True)
    exact_tmp = gen / ".manifest.json.tmp"
    unique_tmp = gen / ".manifest.json.abc123.tmp"
    stale_tmp = gen / ".obsolete-view.md.tmp"
    exact_tmp.write_text("in-flight\n", encoding="utf-8")
    unique_tmp.write_text("in-flight-2\n", encoding="utf-8")
    stale_tmp.write_text("stale\n", encoding="utf-8")

    _remove_stale(gen, {"manifest.json": "{}\n"})

    assert exact_tmp.is_file()
    assert unique_tmp.is_file()
    assert not stale_tmp.exists()


def test_post_commit_hook_does_not_rebuild_generated(mini_repo: Path):
    subprocess.run(["git", "init", "-q", "--initial-branch=main"], cwd=mini_repo, check=True)
    subprocess.run(["git", "config", "user.email", "tests@example.invalid"], cwd=mini_repo, check=True)
    subprocess.run(["git", "config", "user.name", "Tests"], cwd=mini_repo, check=True)
    subprocess.run(["git", "add", "."], cwd=mini_repo, check=True)
    subprocess.run(["git", "commit", "-qm", "baseline"], cwd=mini_repo, check=True)

    hook_dst = mini_repo / ".git" / "hooks" / "post-commit"
    hook_dst.write_text((REPO_ROOT / "tools" / "hooks" / "post-commit").read_text(encoding="utf-8"),
                        encoding="utf-8")
    hook_dst.chmod(0o755)
    gen_manifest = mini_repo / "generated" / "manifest.json"
    if gen_manifest.exists():
        gen_manifest.unlink()

    note = mini_repo / "work" / "inbox" / "hook-note.md"
    note.parent.mkdir(parents=True, exist_ok=True)
    note.write_text("hook test\n", encoding="utf-8")
    subprocess.run(["git", "add", "work/inbox/hook-note.md"], cwd=mini_repo, check=True)
    proc = subprocess.run(["git", "commit", "-m", "add note"], cwd=mini_repo,
                          capture_output=True, text=True, timeout=60)
    assert proc.returncode == 0, proc.stderr
    assert not gen_manifest.exists()
