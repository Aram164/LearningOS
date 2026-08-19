#!/usr/bin/env python3
"""The repository's declared data-format version and schema drift gate.

Canonical records carry no per-record version. The producer-owned contract in
``system/contracts/data-contract.yaml`` therefore fingerprints the stored-record
schemas and records each deliberate format bump and migration. Capability
payload schemas live in a subdirectory and are intentionally excluded.
"""

from __future__ import annotations

import argparse
import sys

from learning_os.contracts.data_contract import bump, check, fingerprint


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--fingerprint", action="store_true",
        help="print the current record-schema fingerprint and exit",
    )
    parser.add_argument(
        "--bump", action="store_true",
        help="declare a new format version from the current schemas",
    )
    parser.add_argument("--note", default=None, help="what changed (required with --bump)")
    parser.add_argument(
        "--migration", default=None,
        help="path to the migration that brings the previous version forward",
    )
    args = parser.parse_args()

    if args.fingerprint:
        print(fingerprint())
        return 0

    if args.bump:
        if not args.note:
            print("--bump requires --note describing what changed", file=sys.stderr)
            return 2
        updated = bump(args.note, args.migration)
        print(
            f"declared contract v{updated['contract_version']} "
            f"over {updated['record_schemas']} record schemas"
        )
        if args.migration is None:
            print(
                "note: no migration recorded — if existing data needs one, "
                "add it and re-run with --migration"
            )
        return 0

    ok, message = check()
    print(message)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
