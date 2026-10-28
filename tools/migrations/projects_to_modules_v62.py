#!/usr/bin/env python3
"""Draft the bounded thesis migration; apply only an exact reviewed JSON draft."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from learning_os.app.project_migration import apply, plan_sha256, prepare  # noqa: E402
from learning_os.domain.failures import TransactionFailure, WriteRefused  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--plan", type=Path, help="reviewed JSON file (required to apply)")
    parser.add_argument("--reviewed-sha256", help="SHA-256 printed by the dry run")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.apply and (not args.plan or not args.reviewed_sha256):
        parser.error("--apply requires --plan and --reviewed-sha256")
    try:
        if args.apply:
            report = json.loads(args.plan.read_text(encoding="utf-8"))
            result = apply(args.root, report, reviewed_sha256=args.reviewed_sha256)
        else:
            report = prepare(args.root)
            print(f"reviewed SHA-256: {plan_sha256(report)}", file=sys.stderr)
            result = report
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, RuntimeError, WriteRefused, TransactionFailure) as exc:
        print(f"migration did not complete normally: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
