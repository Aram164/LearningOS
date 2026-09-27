#!/usr/bin/env python3
"""Install a clean UI clone into one disposable synthetic Core vault.

The ordinary UI installer treats every full Core repository as a real vault
and requires a clean exact pair. This tool satisfies that gate with a local
UI clone beside the synthetic Core; it never targets the learner's vault.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

EVAL = Path(__file__).resolve().parents[1]
REAL_CORE = EVAL.parents[1]
REAL_TREE = REAL_CORE.parents[1]
DEFAULT_UI = REAL_CORE.parent / "obsidian-ui"


def call(args: list[str], *, cwd: Path | None = None) -> str:
    result = subprocess.run(args, cwd=cwd, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(f"{' '.join(args)} failed ({result.returncode}):\n"
                           + result.stdout[-3000:] + result.stderr[-3000:])
    return result.stdout.strip()


def prepare(world_dir: Path, ui_source: Path, ui_rev: str, node: str | None,
            python_venv: Path) -> dict:
    world_dir = world_dir.resolve(strict=True)
    if world_dir.is_relative_to(REAL_TREE):
        raise ValueError("synthetic world must be outside semestercontext")
    record_path = world_dir / "EVAL-WORLD.json"
    record = json.loads(record_path.read_text(encoding="utf-8"))
    core = world_dir / "LearningOS/repository"
    if Path(record["paths"]["repository"]).resolve() != core:
        raise ValueError("EVAL-WORLD.json does not name this synthetic Core")
    if call(["git", "status", "--porcelain"], cwd=core):
        raise ValueError("synthetic Core has authored changes; prepare native UI on a fresh world")
    python_venv = python_venv.resolve(strict=True)
    if not (python_venv / "bin/python").is_file():
        raise ValueError(f"no working Python virtual environment at {python_venv}")
    ui = world_dir / "LearningOS/obsidian-ui"
    if ui.exists() or ui.is_symlink():
        raise ValueError(f"UI destination already exists: {ui}")
    ui_source = ui_source.resolve(strict=True)
    candidate = call(["git", "rev-parse", "--verify", f"{ui_rev}^{{commit}}"],
                     cwd=ui_source)
    # Clone locally so build-info records the exact UI commit and the synthetic
    # Core HEAD. A direct build from the real UI checkout would bind to Aram's
    # Core checkout instead of the disposable vault.
    call(["git", "clone", "--quiet", "--shared", "--no-checkout", str(ui_source), str(ui)])
    call(["git", "checkout", "--quiet", "--detach", candidate], cwd=ui)
    core_exclude = core / ".git/info/exclude"
    core_exclude.write_text(core_exclude.read_text(encoding="utf-8") + "\n/.venv\n",
                            encoding="utf-8")
    os.symlink(python_venv, core / ".venv", target_is_directory=True)
    modules = ui_source / "node_modules"
    if modules.is_dir() and not (ui / "node_modules").exists():
        # The UI repository does not ignore a symlink named node_modules by
        # default. Exclude it only in this disposable clone's Git metadata so
        # build-info can prove the authored UI tree is clean.
        exclude = ui / ".git/info/exclude"
        exclude.write_text(exclude.read_text(encoding="utf-8") + "\n/node_modules\n",
                           encoding="utf-8")
        os.symlink(modules, ui / "node_modules", target_is_directory=True)
    call([sys.executable, "tools/generate.py"], cwd=core)
    command = [sys.executable, "install.py", "--vault", str(core)]
    if node:
        command.extend(["--node", node])
    call(command, cwd=ui)
    call(["node", "scripts/check-install-current.mjs", str(core)], cwd=ui)
    return {
        "world": str(world_dir),
        "vault": str(core),
        "product_core_revision": record["product_revision"],
        "synthetic_core_head": call(["git", "rev-parse", "HEAD"], cwd=core),
        "ui_revision": candidate,
        "ui_checkout": str(ui),
        "installed": True,
        "live_observed": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--world", required=True, type=Path,
                        help="directory containing EVAL-WORLD.json")
    parser.add_argument("--ui-source", type=Path, default=DEFAULT_UI)
    parser.add_argument("--ui-rev", default="HEAD")
    parser.add_argument("--node", help="Node executable accepted by install.py")
    parser.add_argument("--python-venv", type=Path, default=REAL_CORE / ".venv")
    args = parser.parse_args(argv)
    try:
        print(json.dumps(prepare(args.world, args.ui_source, args.ui_rev, args.node,
                                 args.python_venv),
                         indent=2))
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"prepare_native: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
