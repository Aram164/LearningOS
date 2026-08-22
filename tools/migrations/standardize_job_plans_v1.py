#!/usr/bin/env python3
"""Route every active Job plan through Core's canonical plan-save gateway."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import yaml

from learning_os.contracts.migration_lifecycle import (
    refuse_retired_apply,
    retired_migration,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--repository-root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
    )
    parser.add_argument("--job-root", type=Path, required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    repository_root = args.repository_root.resolve()
    retired = retired_migration(
        repository_root,
        "standardize-job-plans-v1",
        supported_through=10,
    )
    if refuse_retired_apply(retired, apply=args.apply):
        return 2 if args.apply else 0
    if not args.apply:
        print("dry-run: pass --apply to migrate eligible Job plans through the gateway")
        return 0
    job_root = args.job_root.resolve()
    plans = sorted((job_root / "plans").glob("*.yaml"))
    migrated = 0
    for path in plans:
        plan = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(plan, dict) or plan.get("type") != "job-learning-plan":
            raise SystemExit(f"refusing non-plan target: {path}")
        if plan.get("plan_template_version") == 1:
            continue
        command = [
            sys.executable,
            str(repository_root / "tools" / "los.py"),
            "--root",
            str(repository_root),
            "job-plan-save",
            "--confirm-job-access",
            "--approve",
            "--plan",
            json.dumps(plan, ensure_ascii=False),
        ]
        result = subprocess.run(command, capture_output=True, text=True, timeout=120)
        if result.returncode:
            raise SystemExit(
                f"gateway rejected {path.name}: {result.stderr or result.stdout}"
            )
        migrated += 1
    print(f"{migrated} Job plan(s) migrated through job-plan-save")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
