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


class GitStatusError(Exception):
    """Repository status could not be established.

    Every caller must treat this as a safety failure, not as "nothing is
    dirty" — unknown is never clean.
    """


def dirty_paths() -> set[str]:
    """Every path git considers dirty, including a rename's source and destination.

    ``-z`` is not a formatting nicety here: the quoted line form the wrapper
    used to parse renders a rename as ``R  old -> new`` and gives no
    unambiguous way to split "old" from "new" when either name contains
    literal " -> " or embedded quoting, and it discarded "old" outright. NUL
    output instead gives one unquoted path per record, with rename and copy
    records carrying the source as a *second* NUL-terminated field
    immediately after the destination — both are folded into the returned
    set, so an out-of-scope source can never hide behind an in-scope
    destination.
    """
    try:
        proc = subprocess.run(
            ["git", "status", "--porcelain=v1", "-z", "--untracked-files=all", "--", "."],
            cwd=ROOT, capture_output=True, timeout=30)
    except subprocess.TimeoutExpired as exc:
        raise GitStatusError(f"git status timed out: {exc}") from exc
    except OSError as exc:
        raise GitStatusError(f"git status could not be run: {exc}") from exc
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout).decode("utf-8", "replace").strip() or "no output"
        raise GitStatusError(f"git status exited {proc.returncode}: {detail}")

    raw = proc.stdout
    if raw.endswith(b"\0"):
        raw = raw[:-1]
    records = raw.split(b"\0") if raw else []

    def decoded(token: bytes) -> str:
        try:
            return token.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise GitStatusError(
                f"git status produced an undecodable record: {token!r}"
            ) from exc

    paths: set[str] = set()
    index = 0
    while index < len(records):
        record = decoded(records[index])
        index += 1
        # Porcelain: two status characters, one space, then the path. Anything
        # shorter or missing that separator is not a record this wrapper
        # understands.
        if len(record) < 4 or record[2] != " ":
            raise GitStatusError(f"git status produced a record this wrapper cannot parse: {record!r}")
        status, path = record[:2], record[3:]
        if not path:
            raise GitStatusError(f"git status produced a record this wrapper cannot parse: {record!r}")
        paths.add(path)
        if "R" in status or "C" in status:
            # Rename/copy records carry their source as the next NUL-terminated
            # field. A record ending the stream with no source field left is a
            # truncated record, not an ordinary one, and must not be silently
            # treated as if it named no source at all.
            if index >= len(records):
                raise GitStatusError(
                    f"git status truncated the rename/copy source for: {record!r}"
                )
            source = decoded(records[index])
            index += 1
            if not source:
                raise GitStatusError(
                    f"git status produced an empty rename/copy source for: {record!r}"
                )
            paths.add(source)
    return paths


def outside_scope(paths: set[str], prefixes: tuple[str, ...]) -> set[str]:
    return {path for path in paths
            if Path(path).suffix.lower() != ".canvas"
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
        try:
            before = dirty_paths()
        except GitStatusError as exc:
            print(f"learningos-codex: cannot establish repository status before "
                  f"launching Codex ({exc}); refusing to start — review the working "
                  "tree manually", file=sys.stderr)
            return 2
        unrelated = outside_scope(before, prefixes)
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

    try:
        after = dirty_paths()
    except GitStatusError as exc:
        print(f"learningos-codex: cannot establish repository status after Codex ran "
              f"({exc}); refusing to validate or publish — the diff cannot be proven "
              "bounded, review the working tree manually", file=sys.stderr)
        return 2

    escaped = outside_scope(after, prefixes)
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
