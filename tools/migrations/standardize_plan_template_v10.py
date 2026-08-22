#!/usr/bin/env python3
"""Stamp current study maps with plan-template v1 and ordered stage numbers.

The migration is intentionally line-preserving: authored comments, wrapping,
and scalar style remain untouched. Frozen fixtures v1-v9 are never targets.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import yaml

from learning_os.contracts.migration_lifecycle import (
    refuse_retired_apply,
    retired_migration,
)


def migrate_text(text: str) -> str:
    data = yaml.safe_load(text)
    if not isinstance(data, dict) or data.get("type") != "study-map":
        raise ValueError("target is not a study-map record")
    lines = text.splitlines(keepends=True)
    output: list[str] = []
    in_stages = False
    stage_number = 0
    stamped = False
    stages = list(data.get("stages") or [])
    for line_index, line in enumerate(lines):
        output.append(line)
        if (
            line.rstrip("\r\n") == "type: study-map"
            and data.get("plan_template_version") != 1
        ):
            output.append("plan_template_version: 1\n")
            stamped = True
            continue
        if line.rstrip("\r\n") == "stages:":
            in_stages = True
            continue
        if in_stages and re.match(r"^[a-zA-Z_]", line):
            in_stages = False
        if in_stages and re.match(r"^- id:\s+", line):
            stage_number += 1
            stage = stages[stage_number - 1]
            next_line = lines[line_index + 1] if line_index + 1 < len(lines) else ""
            if not re.match(r"^  number:\s+", next_line):
                output.append(f"  number: {stage_number}\n")
                if "exam_critical" not in stage:
                    output.append("  exam_critical: false\n")
                if "concepts" not in stage:
                    output.append("  concepts: []\n")
        elif in_stages and re.match(r"^  number:\s+", line):
            stage = stages[stage_number - 1]
            if "exam_critical" not in stage:
                output.append("  exam_critical: false\n")
            if "concepts" not in stage:
                output.append("  concepts: []\n")
    if data.get("plan_template_version") == 1:
        stamped = True
    if not stamped or stage_number == 0:
        raise ValueError("study map lacks a type marker or stages")
    return "".join(output)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    retired = retired_migration(root, "standardize-plan-template-v10", supported_through=10)
    if refuse_retired_apply(retired, apply=args.apply):
        return 2 if args.apply else 0
    paths = sorted((root / "curriculum" / "modules").glob("**/study-map.yaml"))
    changed = 0
    for path in paths:
        before = path.read_text(encoding="utf-8")
        after = migrate_text(before)
        if after == before:
            continue
        changed += 1
        if args.apply:
            path.write_text(after, encoding="utf-8")
    outcome = "migrated" if args.apply else "need migration"
    print(f"{changed} study map(s) {outcome}")
    return 1 if args.check and changed else 0


if __name__ == "__main__":
    raise SystemExit(main())
