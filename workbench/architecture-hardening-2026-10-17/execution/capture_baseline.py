"""Independent, read-only inventory around the existing captured-world tool."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path


HERE = Path(__file__).resolve().parent
LEARNING_OS = HERE.parents[2]
CORE = LEARNING_OS / "repository"
UI = LEARNING_OS / "obsidian-ui"
OUTER = LEARNING_OS.parent
# Reviewed explicitly, independently of production DATA_ROOTS and backup roots.
AUTHORED = ("knowledge", "sources", "records", "projects", "work", "curriculum", "archive")
OPERATIONAL = ("operations",)


def digest(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def inventory(root: Path, names: tuple[str, ...]) -> dict:
    rows = {}
    for name in names:
        base = root / name
        if not base.exists() and not base.is_symlink():
            rows[name] = {"kind": "absent"}
            continue
        paths = [base]
        if base.is_dir() and not base.is_symlink():
            for parent, dirs, files in os.walk(base, followlinks=False):
                dirs.sort()
                for child in [*dirs, *sorted(files)]:
                    paths.append(Path(parent) / child)
        for path in paths:
            relative = path.relative_to(root).as_posix()
            if path.is_symlink():
                target = os.readlink(path)
                rows[relative] = {"kind": "symlink", "target": target,
                                  "sha256": digest(os.fsencode(target))}
            elif path.is_file():
                blob = path.read_bytes()
                rows[relative] = {"kind": "file", "bytes": len(blob), "sha256": digest(blob)}
    return rows


def run(*argv: str, cwd: Path = CORE) -> str:
    result = subprocess.run(argv, cwd=cwd, text=True, capture_output=True, check=True)
    return (result.stdout + result.stderr).strip()


def save(name: str, data: object) -> None:
    (HERE / name).write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def main() -> None:
    before = inventory(CORE, AUTHORED + OPERATIONAL + (".obsidian",))
    dirty_names = run("git", "ls-files", "--modified", "--others", "--exclude-standard", cwd=OUTER)
    outer = inventory(OUTER, tuple(dirty_names.splitlines()))
    save("independent-inputs.json", before)
    save("outer-dirty-inputs.json", outer)
    settings = CORE / ".obsidian/plugins/learningos-ui/data.json"
    raw = HERE / "vault-safety-baseline"
    raw.mkdir(mode=0o700)
    # Preserve raw settings even when they are malformed or an old format.
    if settings.is_file() and not settings.is_symlink():
        shutil.copy2(settings, raw / "data.json")
        (raw / "data.json").chmod(0o600)
    save("vault-settings-baseline.json", {
        "source": str(settings), "present": settings.exists(),
        "symlink": settings.is_symlink(),
        "sha256": digest(settings.read_bytes()) if settings.is_file() else None,
    })
    python = CORE / ".venv/bin/python"
    capture_output = run(str(python), "tools/capture_world.py", "--root", str(CORE),
                         "--out", str(HERE / "world"))
    after = inventory(CORE, AUTHORED + OPERATIONAL + (".obsidian",))
    if before != after:
        save("capture-conflict.json", {"before": before, "after": after})
        raise RuntimeError("source changed during capture; do not accept this world")
    assert outer == inventory(OUTER, tuple(dirty_names.splitlines())), "unrelated dirty bytes changed"
    save("baseline-receipt.json", {
        "core": run("git", "rev-parse", "HEAD"),
        "ui": run("git", "rev-parse", "HEAD", cwd=UI),
        "core_status": run("git", "status", "--porcelain"),
        "ui_status": run("git", "status", "--porcelain", cwd=UI),
        "independent_inventory_sha256": digest((HERE / "independent-inputs.json").read_bytes()),
        "outer_dirty_inventory_sha256": digest((HERE / "outer-dirty-inputs.json").read_bytes()),
        "source_unchanged_during_capture": True,
        "quiescence": "No LearningOS/Obsidian/Muse/test writer found by process inspection before capture",
        "python": run(str(python), "--version"),
        "mypy": run(str(python), "-m", "mypy", "--version"),
        "node": run("node", "--version"),
        "npm": run("npm", "--version"),
        "platform": run("uname", "-a"),
        "capture_output": capture_output,
        "inventory_entries": len(before),
    })
    print(f"Captured quiescent world; {len(before)} independently inventoried entries unchanged.")


if __name__ == "__main__":
    main()
