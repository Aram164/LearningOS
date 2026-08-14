#!/usr/bin/env python3
"""Scoped safety wrapper for Agentic Copilot's generic CLI adapter.

General conversation is read-only. A write sandbox is available only to a
named LearningOS gateway capability carrying explicit module/unit context.
Before and after the action the wrapper verifies that no unrelated authored
path is dirty; shelving additionally permits the two approval-gated knowledge
destinations. The old broad markers remain exported but fail closed.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# v1 compatibility constants: these strings no longer grant write access.
OPERATIONAL = "[LearningOS approved operational write]"
SHELVING = "[LearningOS approved shelving apply]"
JOB_TASK = "[LearningOS approved Job task]"

CAPABILITY_RE = re.compile(
    r"\[LearningOS capability:(?P<action>[a-z-]+)\s+"
    r"module=(?P<module>module-[a-z0-9-]+)\s+"
    r"unit=(?P<unit>unit-[a-z0-9-]+)"
    r"(?:\s+stage=(?P<stage>stage-[a-z0-9-]+))?\]"
)
WRITE_CAPABILITIES = {
    "unit-map-import", "unit-source-selection", "stage-note", "stage-progress", "stage-attach",
    "source-feedback", "detour-create", "detour-resolve",
    "shelving-prepare", "shelving-apply",
}
PROTECTED_UNTRACKED = {"Untitled.canvas", "Untitled 1.canvas", "Untitled 2.canvas"}


def codex_binary() -> str | None:
    configured = os.environ.get("LEARNINGOS_CODEX_BIN")
    candidates = [
        configured,
        shutil.which("codex"),
        "/Applications/ChatGPT.app/Contents/Resources/codex",
        "/Applications/Codex.app/Contents/Resources/codex",
    ]
    return next((candidate for candidate in candidates
                 if candidate and Path(candidate).is_file()), None)


def python_binary() -> str:
    venv = ROOT / ".venv" / "bin" / "python"
    return str(venv) if venv.is_file() else sys.executable


def parse_capability(prompt: str) -> dict | None:
    match = CAPABILITY_RE.search(prompt)
    if not match or match.group("action") not in WRITE_CAPABILITIES:
        return None
    data = match.groupdict()
    if data["action"].startswith("stage-") and not data.get("stage"):
        return None
    return data


def allowed_prefixes(capability: dict) -> tuple[str, ...]:
    unit_prefix = (f"curriculum/modules/{capability['module']}/units/"
                   f"{capability['unit']}/")
    if capability["action"] == "shelving-apply":
        return unit_prefix, "knowledge/notes/", "knowledge/garden/"
    return (unit_prefix,)


def dirty_paths() -> set[str]:
    proc = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all", "--", "."],
        cwd=ROOT, capture_output=True, text=True, timeout=30)
    if proc.returncode != 0:
        return set()
    paths = set()
    for line in proc.stdout.splitlines():
        path = line[3:]
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        paths.add(path)
    return paths


def outside_scope(paths: set[str], prefixes: tuple[str, ...]) -> set[str]:
    return {path for path in paths
            if path not in PROTECTED_UNTRACKED
            and not any(path.startswith(prefix) for prefix in prefixes)}


def main() -> int:
    if len(sys.argv) != 2 or not sys.argv[1].strip():
        print("learningos-codex: expected one prompt argument", file=sys.stderr)
        return 2
    binary = codex_binary()
    if binary is None:
        print("learningos-codex: Codex CLI not found", file=sys.stderr)
        return 2

    prompt = sys.argv[1]
    capability = parse_capability(prompt)
    approved_write = capability is not None
    prefixes = allowed_prefixes(capability) if capability else ()
    if capability:
        unrelated = outside_scope(dirty_paths(), prefixes)
        if unrelated:
            print("learningos-codex: refusing scoped write while unrelated changes exist: "
                  + ", ".join(sorted(unrelated)), file=sys.stderr)
            return 2

    cmd = [binary, "exec", "--ephemeral", "--color", "never",
           "--sandbox", "workspace-write" if approved_write else "read-only",
           "-C", str(ROOT)]
    guarded_prompt = prompt
    if capability:
        guarded_prompt += ("\n\nUse only tools/los.py capability '" + capability["action"]
                           + "' for module " + capability["module"]
                           + ", unit " + capability["unit"]
                           + (", stage " + capability["stage"] if capability.get("stage") else "")
                           + ". Do not write any other path.")
    cmd.append(guarded_prompt)

    result = subprocess.run(cmd, cwd=ROOT)
    if result.returncode != 0 or not approved_write:
        return result.returncode

    escaped = outside_scope(dirty_paths(), prefixes)
    if escaped:
        print("learningos-codex: scoped action changed files outside its capability: "
              + ", ".join(sorted(escaped)), file=sys.stderr)
        return 1

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
