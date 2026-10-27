"""CLI adapter: invoke registered operations (SPEC 11.2)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from learning_os.app.pipeline import Outcome, run_cli


def invoke(args) -> int:
    """Run the registered operation bound to ``args``; return its exit code."""

    # S13 candidate J8: the default spells cli_parser._repository_root
    # inline (adapters.cli cannot import cli_parser: cycle). Equality with
    # _repository_root and support._root is pinned in test_ops_pipeline.
    if args.root:
        root = Path(args.root).resolve()
    else:
        root = Path(__file__).resolve().parents[3]
    outcome = run_cli(root, args._operation, args)
    sys.stdout.write(outcome.stdout)
    sys.stderr.write(outcome.stderr)
    return outcome.exit_code


def invoke_outcome(args: argparse.Namespace) -> Outcome:
    """Outcome-returning execution (D03): same pipeline, no global capture."""
    if args.root:
        root = Path(args.root).resolve()
    else:
        root = Path(__file__).resolve().parents[3]
    return run_cli(root, args._operation, args)
