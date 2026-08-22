#!/usr/bin/env python3
"""Route every active Job plan through Core's canonical plan-save gateway."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import yaml


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--repository-root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
    )
    parser.add_argument("--job-root", type=Path, required=True)
    args = parser.parse_args()
    repository_root = args.repository_root.resolve()
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
