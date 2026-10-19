"""Retain exact candidate/input identity and complete command evidence."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
CORE = HERE / "candidate/repository"
UI = HERE / "candidate/obsidian-ui"


def source_identity(root: Path) -> dict:
    proc = subprocess.run(["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
                          cwd=root, capture_output=True, check=True)
    files = {}
    for name in sorted(set(proc.stdout.decode().strip("\0").split("\0"))):
        path = root / name
        if path.is_file():
            files[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, text=True,
                          capture_output=True, check=True).stdout.strip()
    return {"head": head, "files_sha256": hashlib.sha256(
        json.dumps(files, sort_keys=True).encode()).hexdigest(), "files": files}


def main() -> int:
    name, *command = sys.argv[1:]
    if command and command[0] == "--":
        command.pop(0)
    target = HERE / "receipts" / name
    target.mkdir(parents=True, exist_ok=False)
    before = {"core": source_identity(CORE), "ui": source_identity(UI)}
    started = time.monotonic()
    with (target / "stdout.txt").open("w") as out, (target / "stderr.txt").open("w") as err:
        proc = subprocess.run(command, cwd=CORE, stdout=out, stderr=err)
    after = {"core": source_identity(CORE), "ui": source_identity(UI)}
    receipt = {"command": command, "cwd": str(CORE), "exit": proc.returncode,
               "elapsed_seconds": time.monotonic() - started,
               "before": before, "after": after, "source_unchanged": before == after}
    (target / "receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print((target / "stdout.txt").read_text()[-5000:])
    if proc.returncode:
        print((target / "stderr.txt").read_text()[-5000:], file=sys.stderr)
    print(f"Receipt: {target}; exit={proc.returncode}; unchanged={before == after}")
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
