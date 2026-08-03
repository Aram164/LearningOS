#!/usr/bin/env python3
"""Safety wrapper for Agentic Copilot's generic CLI adapter.

The upstream adapter passes one prompt argument and cannot participate in
Codex app-server approval requests. This wrapper therefore keeps Codex
read-only by default and grants workspace-write only when a LearningOS UI
action has inserted one of the explicit approval markers below.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
JOB_ROOT = ROOT.parent.parent / "Job"

OPERATIONAL = "[LearningOS approved operational write]"
SHELVING = "[LearningOS approved shelving apply]"
JOB_TASK = "[LearningOS approved Job task]"


def codex_binary() -> str | None:
    configured = os.environ.get("LEARNINGOS_CODEX_BIN")
    candidates = [
        configured,
        shutil.which("codex"),
        "/Applications/ChatGPT.app/Contents/Resources/codex",
        "/Applications/Codex.app/Contents/Resources/codex",
    ]
    return next((c for c in candidates if c and Path(c).is_file()), None)


def python_binary() -> str:
    venv = ROOT / ".venv" / "bin" / "python"
    return str(venv) if venv.is_file() else sys.executable


def main() -> int:
    if len(sys.argv) != 2 or not sys.argv[1].strip():
        print("learningos-codex: expected one prompt argument", file=sys.stderr)
        return 2
    binary = codex_binary()
    if binary is None:
        print("learningos-codex: Codex CLI not found", file=sys.stderr)
        return 2

    prompt = sys.argv[1]
    approved_write = OPERATIONAL in prompt or SHELVING in prompt or JOB_TASK in prompt
    cmd = [binary, "exec", "--ephemeral", "--color", "never",
           "--sandbox", "workspace-write" if approved_write else "read-only",
           "-C", str(ROOT)]
    if JOB_TASK in prompt:
        if not JOB_ROOT.is_dir():
            print(f"learningos-codex: Job root missing: {JOB_ROOT}", file=sys.stderr)
            return 2
        cmd += ["--add-dir", str(JOB_ROOT)]
    cmd.append(prompt)

    result = subprocess.run(cmd, cwd=ROOT)
    if result.returncode != 0 or not approved_write:
        return result.returncode

    # A write-enabled UI action never silently finishes with an invalid OS.
    validate = subprocess.run(
        [python_binary(), str(ROOT / "tools" / "los.py"), "validate"], cwd=ROOT)
    if validate.returncode != 0:
        print("learningos-codex: authored changes remain for review; validation failed",
              file=sys.stderr)
        return validate.returncode
    return subprocess.run(
        [python_binary(), str(ROOT / "tools" / "los.py"), "generate"], cwd=ROOT).returncode


if __name__ == "__main__":
    raise SystemExit(main())
