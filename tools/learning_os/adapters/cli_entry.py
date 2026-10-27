"""The los process step after parsing: apply --lock-timeout, run the command, and map an escaping failure to its exit."""

from __future__ import annotations

import sys

from learning_os.app.lock import lock_wait_budget
from learning_os.app.outcomes import classify, resolve


def run(args) -> int:
    try:
        with lock_wait_budget(args.lock_timeout):
            return args.func(args)
    except Exception as exc:
        row = classify(exc, "cli")
        if row is None:
            raise
        print(f"los: {exc}", file=sys.stderr)
        return resolve(row, exc)["exit"]
