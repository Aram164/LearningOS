#!/usr/bin/env python3
"""Prune the disposable diagnostic trace store (track #2, Phase 3A).

    python tools/diagnostics_prune.py [--keep-last 500] [--pin REQUEST_ID ...]
        [--dry-run] [--root PATH]

Keeps the newest `--keep-last` operations plus every operation referenced by
a pinned request id (e.g. the request an unresolved Gateway recovery record
still references — pass those ids explicitly; retention never guesses).
Rewrites the store atomically. Reports counts; exits non-zero with a clear
error if the store cannot be read or rewritten.

Explicit maintenance only: nothing in the write path prunes, and pruning is
never required for correct operation — an unpruned store just grows.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from learning_os.diagnostics.store import (  # noqa: E402
    DEFAULT_KEEP_LAST,
    prune_store,
    traces_path,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=None,
                        help="repository root (default: parent of tools/)")
    parser.add_argument("--keep-last", type=int, default=DEFAULT_KEEP_LAST,
                        help="newest operations to keep apart from pins")
    parser.add_argument("--pin", action="append", default=[],
                        help="request id whose operations must survive "
                             "(repeatable)")
    parser.add_argument("--dry-run", action="store_true",
                        help="report what would be evicted without rewriting")
    args = parser.parse_args()
    if args.keep_last < 0:
        parser.error("--keep-last must not be negative")

    root = Path(args.root).resolve() if args.root else Path(__file__).resolve().parent.parent
    if not traces_path(root).is_file():
        print(f"no trace store at {traces_path(root)}; nothing to prune")
        return 0
    try:
        result = prune_store(root, keep_last=args.keep_last,
                             pinned_request_ids=frozenset(args.pin),
                             dry_run=args.dry_run)
    except (OSError, ValueError) as exc:
        print(f"diagnostics-prune: cannot prune the trace store: {exc}")
        return 1
    action = "would keep" if args.dry_run else "kept"
    print(f"{action} {result['kept_operations']} operations "
          f"({result['kept_records']} records); evicted "
          f"{result['evicted_operations']} operations "
          f"({result['evicted_records']} records)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
