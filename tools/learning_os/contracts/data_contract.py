"""Producer-owned version gate for canonical record schemas."""

from __future__ import annotations

import datetime as dt
import hashlib
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]
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
    return sorted(schema_dir.glob("*.schema.json"))


def fingerprint(schema_dir: Path = SCHEMA_DIR) -> str:
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
    path.write_text(
        _HEADER + yaml.safe_dump(data, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


def check(schema_dir: Path = SCHEMA_DIR, path: Path = CONTRACT) -> tuple[bool, str]:
    contract = load_contract(path)
    if contract is None:
        return False, (
            f"no {path.name} — declare the current format with "
            "`python tools/schema_contract.py --bump --note 'baseline'`"
        )
    recorded = contract.get("schema_fingerprint")
    current = fingerprint(schema_dir)
    if recorded == current:
        return True, (
            f"contract v{contract.get('contract_version')} matches "
            f"{len(record_schemas(schema_dir))} record schemas"
        )
    return False, (
        f"record schemas changed but the data contract still declares "
        f"v{contract.get('contract_version')}.\n"
        f"  recorded: {recorded}\n"
        f"  current:  {current}\n"
        "A schema edit redefines what 'valid' means for data already on disk.\n"
        "Confirm tests/fixtures/formats/ still loads, write a migration under\n"
        "tools/migrations/ if it does not, then run:\n"
        "  python tools/schema_contract.py --bump --note \"<what changed>\""
    )


def _newest_frozen_fixture(repo_root: Path, version: int) -> str:
    """Return the highest `tests/fixtures/formats/v<N>/` that exists on disk."""
    formats = repo_root / "tests" / "fixtures" / "formats"
    frozen = sorted(
        (int(p.name.removeprefix("v")) for p in formats.glob("v[0-9]*") if p.is_dir()),
        reverse=True,
    )
    return f"tests/fixtures/formats/v{frozen[0] if frozen else version}/"


def bump(
    note: str,
    migration: str | None = None,
    schema_dir: Path = SCHEMA_DIR,
    path: Path = CONTRACT,
) -> dict:
    contract = load_contract(path) or {"contract_version": 0, "history": []}
    version = int(contract.get("contract_version", 0)) + 1
    entry = {
        "version": version,
        "adopted": dt.date.today().isoformat(),
        "note": note,
        "migration": migration,
        # Point at the newest shape that is actually frozen, not at the one this
        # bump hopes will be. The freeze is step 4 of the README procedure and
        # has not happened yet at bump time, so writing `v{version}/` here
        # records a directory that does not exist — v13 carried exactly that
        # claim for three days and no test could see it. When a new fixture is
        # frozen, update this entry to name it;
        # `test_every_recorded_fixture_pointer_resolves` enforces the rest.
        "fixture": _newest_frozen_fixture(path.parent.parent.parent, version),
    }
    updated = {
        "contract_version": version,
        "schema_fingerprint": fingerprint(schema_dir),
        "record_schemas": len(record_schemas(schema_dir)),
        "history": list(contract.get("history") or []) + [entry],
    }
    write_contract(updated, path)
    return updated
