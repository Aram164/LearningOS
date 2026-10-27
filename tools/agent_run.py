#!/usr/bin/env python3
"""Run an experimental bounded agent plan or expand its retained report."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from learning_os.adapters import agent_runner
from learning_os.app.agent_presentation import encode_json
from learning_os.domain.agent_plans import PlanStepError
from learning_os.domain.codes import INVALID_REQUEST, INVALID_STEP_OUTPUT

TOOLS = Path(__file__).resolve().parent

def _finite_number(value: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise PlanStepError("nonfinite JSON number in plan", INVALID_STEP_OUTPUT)
    return number


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", nargs="?", help="plan JSON file")
    parser.add_argument("--expand-report", help="verify and expand a finalized full report")
    parser.add_argument("--step", help="expand only this step (with --expand-report)")
    parser.add_argument("--root", default=None, help="selected data root (default: tool repository)")
    parser.add_argument("--poll-s", type=float, default=0.1)
    parser.add_argument("--report-dir", default=None,
                        help="directory for the full report artifact (bounded stdout)")
    parser.add_argument("--keep-report", action="store_true", help="exclude this run from report retention")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    root = Path(args.root).resolve() if args.root else TOOLS.parent
    try:
        if args.expand_report:
            from learning_os.app.agent_reporting import expand_report
            if args.plan:
                raise PlanStepError("choose a plan or --expand-report")
            print(encode_json(expand_report(Path(args.expand_report), args.step)))
            return 0
        if not args.plan or args.step:
            raise PlanStepError("a plan is required; --step needs --expand-report")
        if Path(args.plan).stat().st_size > 1048576:
            raise PlanStepError("plan input exceeds 1 MiB")
        report = agent_runner.run_plan(json.loads(Path(args.plan).read_text(encoding="utf-8"), parse_float=_finite_number, parse_constant=_finite_number), root, poll_s=args.poll_s, report_dir=args.report_dir, keep_report=args.keep_report)
    except (OSError, ValueError, KeyError, TypeError, PlanStepError) as exc:
        print(encode_json({"error": {"code": getattr(exc, "code", INVALID_REQUEST),
                               "message": str(exc), "retryable": False}}))
        return 2
    print(encode_json(report))
    return 0 if all(row["status"] == "ok" for row in report["steps"]) else 3


if __name__ == "__main__":
    raise SystemExit(main())
