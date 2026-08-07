#!/usr/bin/env python3
"""The repository's declared data-format version, and the gate that keeps it honest.

    python tools/schema_contract.py              # check: do the schemas match the record?
    python tools/schema_contract.py --fingerprint
    python tools/schema_contract.py --bump --note "units gained a stage_kind field" \\
        [--migration tools/migrations/units_v3.py]

WHY THIS EXISTS
---------------
Canonical records carry no per-record version, and every record schema is
``additionalProperties: false``. That combination is strict — good — but it
means a schema edit silently redefines what "valid" means for data already on
disk, with nothing recording that the meaning changed. Years later there is no
way to answer "which format was this note written under, and what brings it
forward?" except by reading Git history and guessing.

This contract answers it. ``system/contracts/data-contract.yaml`` records the
current format version and a fingerprint over the record schemas. The validator
compares the two on every run, so a schema change cannot land without a
deliberate bump — and every bump is an entry in a chain that names its migration
and its format fixture.

SCOPE
-----
The fingerprint covers ``system/schema/*.schema.json`` — the schemas that govern
*stored records*. It deliberately excludes ``system/schema/capabilities/``:
those validate incoming request payloads, so changing one cannot invalidate data
already written to disk.

A single repository-level version rather than a field on every record is the
right granularity here: this repository migrates as one unit, so mixed-version
records never coexist. What must be provable is the other direction — that data
written under an older format still loads today. ``tests/fixtures/formats/``
holds a frozen sample per version and the test suite proves exactly that.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CONTRACT = ROOT / "system" / "contracts" / "data-contract.yaml"
SCHEMA_DIR = ROOT / "system" / "schema"

_HEADER = """\
# The repository's data-format contract.
#
# `contract_version` is the format canonical records are written in. The
# fingerprint is a sha256 over system/schema/*.schema.json — the schemas that
# govern stored records (capability payload schemas are excluded: they validate
# requests, not data at rest).
#
# `make check` fails when the schemas change and this file does not, so a schema
# edit cannot silently redefine what "valid" means for data already on disk.
# When that fires, the fix is a decision, not a rubber stamp:
#
#   1. does existing data still validate?  tests/fixtures/formats/ answers this
#   2. if not, write the migration under tools/migrations/
#   3. python tools/schema_contract.py --bump --note "…" [--migration …]
#   4. freeze the new shape as tests/fixtures/formats/v<N>/
#
# Rebuild with: python tools/schema_contract.py --bump
"""


def record_schemas(schema_dir: Path = SCHEMA_DIR) -> list[Path]:
    """The schemas governing stored records, in stable order."""
    return sorted(schema_dir.glob("*.schema.json"))


def fingerprint(schema_dir: Path = SCHEMA_DIR) -> str:
    """A content hash over the record schemas, insensitive to filesystem order."""
    digest = hashlib.sha256()
    for path in record_schemas(schema_dir):
        digest.update(path.name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return f"sha256:{digest.hexdigest()}"


def load_contract(path: Path = CONTRACT) -> dict | None:
    if not path.exists():
        return None
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def write_contract(data: dict, path: Path = CONTRACT) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_HEADER + yaml.safe_dump(data, sort_keys=False, allow_unicode=True),
                    encoding="utf-8")


def check(schema_dir: Path = SCHEMA_DIR, path: Path = CONTRACT) -> tuple[bool, str]:
    """Return (ok, message). Not ok means the schemas moved without a bump."""
    contract = load_contract(path)
    if contract is None:
        return False, (f"no {path.name} — declare the current format with "
                       "`python tools/schema_contract.py --bump --note 'baseline'`")
    recorded = contract.get("schema_fingerprint")
    current = fingerprint(schema_dir)
    if recorded == current:
        return True, (f"contract v{contract.get('contract_version')} matches "
                      f"{len(record_schemas(schema_dir))} record schemas")
    return False, (
        f"record schemas changed but the data contract still declares "
        f"v{contract.get('contract_version')}.\n"
        f"  recorded: {recorded}\n"
        f"  current:  {current}\n"
        "A schema edit redefines what 'valid' means for data already on disk.\n"
        "Confirm tests/fixtures/formats/ still loads, write a migration under\n"
        "tools/migrations/ if it does not, then run:\n"
        "  python tools/schema_contract.py --bump --note \"<what changed>\"")


def bump(note: str, migration: str | None = None,
         schema_dir: Path = SCHEMA_DIR, path: Path = CONTRACT) -> dict:
    contract = load_contract(path) or {"contract_version": 0, "history": []}
    version = int(contract.get("contract_version", 0)) + 1
    entry = {
        "version": version,
        "adopted": _dt.date.today().isoformat(),
        "note": note,
        "migration": migration,
        "fixture": f"tests/fixtures/formats/v{version}/",
    }
    updated = {
        "contract_version": version,
        "schema_fingerprint": fingerprint(schema_dir),
        "record_schemas": len(record_schemas(schema_dir)),
        "history": list(contract.get("history") or []) + [entry],
    }
    write_contract(updated, path)
    return updated


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--fingerprint", action="store_true",
                        help="print the current record-schema fingerprint and exit")
    parser.add_argument("--bump", action="store_true",
                        help="declare a new format version from the current schemas")
    parser.add_argument("--note", default=None, help="what changed (required with --bump)")
    parser.add_argument("--migration", default=None,
                        help="path to the migration that brings the previous version forward")
    args = parser.parse_args()

    if args.fingerprint:
        print(fingerprint())
        return 0

    if args.bump:
        if not args.note:
            print("--bump requires --note describing what changed", file=sys.stderr)
            return 2
        updated = bump(args.note, args.migration)
        print(f"declared contract v{updated['contract_version']} "
              f"over {updated['record_schemas']} record schemas")
        if args.migration is None:
            print("note: no migration recorded — if existing data needs one, "
                  "add it and re-run with --migration")
        return 0

    ok, message = check()
    print(message)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
