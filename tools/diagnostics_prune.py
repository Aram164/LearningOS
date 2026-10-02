#!/usr/bin/env python3
"""Prune disposable stores: the diagnostic trace store and derived-state blobs.

    python tools/diagnostics_prune.py [--keep-last 500] [--pin REQUEST_ID ...]
        [--dry-run] [--root PATH]
    python tools/diagnostics_prune.py --derived-state [--dry-run] [--root PATH]

Trace mode keeps the newest `--keep-last` operations plus every operation
referenced by a pinned request id (e.g. the request an unresolved Gateway
recovery record still references — pass those ids explicitly; retention
never guesses). Rewrites the store atomically. Reports counts; exits
non-zero with a clear error if the store cannot be read or rewritten.

Derived-state mode deletes content-addressed blobs under
``generated/derived-state/blobs/`` that the current ``state-v1.json`` no
longer references, under the operator lock and only after the state is
durable. A crash mid-sweep only leaves extra orphans.

Explicit maintenance only: nothing in the write path prunes the trace
store, and pruning is never required for correct operation — an unpruned
store just grows. Derived-state publication collects its own orphans;
this mode reclaims pre-existing ones.
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
    parser.add_argument("--derived-state", action="store_true",
                        help="sweep unreferenced derived-state blobs instead of "
                             "the trace store")
    args = parser.parse_args()
    if args.keep_last < 0:
        parser.error("--keep-last must not be negative")

    root = Path(args.root).resolve() if args.root else Path(__file__).resolve().parent.parent
    if args.derived_state:
        from learning_os.commands.support import _operator_lock  # noqa: E402
        from learning_os.derived.store import sweep_unreferenced_blobs  # noqa: E402

        with _operator_lock(root):
            result = sweep_unreferenced_blobs(root, dry_run=args.dry_run)
        action = "would delete" if args.dry_run else "deleted"
        print(f"{action} {result['deleted']} unreferenced blob(s); kept "
              f"{result['kept']} referenced blob(s) "
              f"({result['referenced']} state entries, "
              f"{result['skipped']} skipped)")
        return 0
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
