"""The los process step after parsing: apply --lock-timeout, run the command, and map an escaping failure to its exit."""

from __future__ import annotations

import os
import sys

from learning_os.app.lock import LOS_LOCK_TIMEOUT_ENV
from learning_os.app.outcomes import classify, resolve


def run(args) -> int:
    if args.lock_timeout is not None:
        os.environ[LOS_LOCK_TIMEOUT_ENV] = str(args.lock_timeout)
    try:
        return args.func(args)
    except Exception as exc:
        row = classify(exc, "cli")
        if row is None:
            raise
        print(f"los: {exc}", file=sys.stderr)
        return resolve(row, exc)["exit"]
