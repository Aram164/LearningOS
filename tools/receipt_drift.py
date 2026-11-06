#!/usr/bin/env python3
"""Report canonical-file drift against the transaction receipt ledger.

Boundary 16's residual hole: a hand-edited plan or module record produces a
file the validator accepts while skipping every guarantee the gateway path
exists for — no receipt, no snapshot, no revision. The receipt ledger is the
only structure that would know. This tool walks
``operations/transactions/transaction-*.yaml`` in id order and reports,
report-only:

- ``DRIFT`` — a file whose current sha256 differs from the ``sha256_after``
  of the last receipt that wrote it, including a file deleted after a
  receipt recorded bytes for it, and a canonical record that is a symlink
  (byte-identical content is not provenance: the ledger cannot vouch for
  where a symlink's bytes live).
- ``UNTRACKED`` — a plan or module record under the declared plan globs that
  appears in no receipt row: written before the ledger began, or never
  through any declared path. The 2026-11-05 sizing run attributed these to
  the pre-ledger era (the earliest receipt is 2026-08-06), not to hand
  edits — the class sizes history, it does not accuse.
- ``MALFORMED`` — a file in the ledger directory that is not a readable
  transaction receipt, or one whose authority-relevant shape violates
  ``system/schema/transaction-receipt.schema.json``: an ``id`` outside the
  schema's pattern (the id sort is only chronological for canonical ids), a
  ``writes`` value that is not a list of objects carrying a non-empty string
  ``path`` and a 64-hex-or-null ``sha256_after``, or two write rows for one
  path in a single receipt (the journal refuses that at commit time; this
  re-checks the ledger after the fact). A malformed receipt never
  contributes last-write authority.

Snapshot contiguity between consecutive receipts is deliberately NOT a
finding class: the sizing run found 123 non-contiguous pairs in ordinary
history, because the snapshot fingerprint hashes the on-disk tree including
untracked canonical files, which legitimately change between commits. A
non-contiguous pair is therefore normal, not evidence of a hand edit.

This is a detector, not a preventer: nothing here blocks a write, a hand
editor who also forges receipts defeats it, and it proves bytes, not intent
(a ``git restore`` of an older version drifts the same way a hand edit
does). Gate status is deliberately unassigned — size the classes first,
then decide whether a class becomes a warning-level rule.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

import yaml

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))

from plan_write_audit import PLAN_PATHS  # noqa: E402

RECEIPT_GLOB = "transaction-*.yaml"
RECEIPT_DIR = "operations/transactions"

#: Plan globs plus the module records boundary 16 names alongside plans.
#: module.create writes a receipt, so a legitimate module record is tracked.
RECORD_GLOBS = (*PLAN_PATHS, "curriculum/modules/*/module.yaml")

#: The receipt schema (system/schema/transaction-receipt.schema.json) pins
#: the id to zero-padded timestamps and every write path/hash to exact
#: shapes. Enforcing that slice here is what makes "sort by id" mean
#: "order by commit time", and makes last-write-wins well-defined.
_ID_PATTERN = re.compile(r"^transaction-[0-9]{8}-[0-9]{6}-[0-9]{3}$")
_HASH_PATTERN = re.compile(r"^[a-f0-9]{64}$")


def _receipt_shape_ok(receipt: dict) -> bool:
    """The authority-relevant slice of the receipt schema, re-checked.

    The drift verdict trusts exactly three things about a receipt: its id
    (ordering authority), its write rows (path and sha256_after), and one
    write per path. Anything else the schema constrains does not change the
    verdict and is left to the schema validator.
    """
    receipt_id = receipt.get("id")
    if not isinstance(receipt_id, str) or not _ID_PATTERN.match(receipt_id):
        return False
    writes = receipt.get("writes")
    if not isinstance(writes, list):
        return False
    seen: set[str] = set()
    for row in writes:
        if not isinstance(row, dict):
            return False
        path = row.get("path")
        if not isinstance(path, str) or not path:
            return False
        sha_after = row.get("sha256_after")
        if sha_after is not None and (not isinstance(sha_after, str)
                                      or not _HASH_PATTERN.match(sha_after)):
            return False
        if path in seen:
            return False
        seen.add(path)
    return True


def _sha256(path: Path) -> str | None:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_receipts(root: Path) -> tuple[list[dict], list[str]]:
    """Parse every receipt in id order; collect unusable ones by name.

    Unusable = unparseable, not a transaction receipt, or failing
    :func:`_receipt_shape_ok`. The sort is lexicographic on the id, which is
    chronological only because the schema pins the id shape — the shape gate
    is what makes the sort safe.
    """
    receipts: list[dict] = []
    malformed: list[str] = []
    directory = root / RECEIPT_DIR
    if not directory.is_dir():
        return receipts, malformed
    for path in sorted(directory.glob(RECEIPT_GLOB)):
        try:
            raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError):
            malformed.append(path.name)
            continue
        if (isinstance(raw, dict) and raw.get("type") == "transaction-receipt"
                and _receipt_shape_ok(raw)):
            receipts.append(raw)
        else:
            malformed.append(path.name)
    receipts.sort(key=lambda receipt: str(receipt.get("id", "")))
    return receipts, malformed


def last_writes(receipts: list[dict]) -> tuple[dict[str, tuple[str | None, str]], int]:
    """path -> (sha256_after, receipt id), last committed receipt winning.

    Only ``status: committed`` receipts count as the last-write authority; a
    non-committed ledger row is not yet a guarantee, and its hashes must not
    shadow the committed ones. Returns the skipped count separately. Rows
    arrive shape-validated from load_receipts, so ``row.get`` cannot raise
    here and a counted receipt always carries well-formed rows.
    """
    last: dict[str, tuple[str | None, str]] = {}
    skipped = 0
    for receipt in receipts:
        if receipt.get("status") != "committed":
            skipped += 1
            continue
        for row in receipt.get("writes") or []:
            path = row.get("path")
            if path:
                last[path] = (row.get("sha256_after"), str(receipt.get("id", "")))
    return last, skipped


def record_files(root: Path) -> list[str]:
    files: set[str] = set()
    for pattern in RECORD_GLOBS:
        for path in sorted(root.glob(pattern)):
            if path.is_file():
                files.add(path.relative_to(root).as_posix())
    return sorted(files)


def report(root: Path) -> dict:
    receipts, malformed = load_receipts(root)
    last, non_committed = last_writes(receipts)
    records = record_files(root)

    drift: list[dict] = []
    for path in sorted(last):
        expected, receipt_id = last[path]
        actual_path = root / path
        if not actual_path.is_file():
            if expected:
                drift.append({"path": path, "receipt": receipt_id,
                              "expected": expected, "actual": None,
                              "note": "file deleted after the receipt recorded it"})
            continue
        actual = _sha256(actual_path)
        if actual_path.is_symlink():
            drift.append({"path": path, "receipt": receipt_id,
                          "expected": expected, "actual": actual,
                          "note": "canonical record is a symlink; the ledger "
                                  "cannot vouch for where its bytes live"})
            continue
        if expected is None:
            drift.append({"path": path, "receipt": receipt_id,
                          "expected": None, "actual": actual,
                          "note": "file exists but the last receipt recorded its deletion"})
            continue
        if actual != expected:
            drift.append({"path": path, "receipt": receipt_id,
                          "expected": expected, "actual": actual,
                          "note": "bytes differ from the last receipt"})

    tracked = set(last)
    untracked = [path for path in records if path not in tracked]

    return {
        "receipts": len(receipts),
        "non_committed_skipped": non_committed,
        "tracked_paths": len(last),
        "records_checked": len(records),
        "drift": drift,
        "untracked": untracked,
        "malformed_receipts": malformed,
    }


def _print(findings: dict) -> None:
    print(f"receipts: {findings['receipts']}  "
          f"tracked paths: {findings['tracked_paths']}  "
          f"plan/module records: {findings['records_checked']}  "
          f"non-committed skipped: {findings['non_committed_skipped']}")
    for row in findings["drift"]:
        print(f"DRIFT {row['path']} — {row['note']} "
              f"(receipt {row['receipt']})")
    for path in findings["untracked"]:
        print(f"UNTRACKED {path} — in no receipt row")
    for name in findings["malformed_receipts"]:
        print(f"MALFORMED {name} — not a readable, schema-shaped transaction receipt")
    total = (len(findings["drift"]) + len(findings["untracked"])
             + len(findings["malformed_receipts"]))
    print(f"report-only: {total} finding(s); this tool gates nothing")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path,
                        default=Path(__file__).resolve().parents[1])
    parser.add_argument("--json", action="store_true",
                        help="print the findings as JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    findings = report(args.root)
    if args.json:
        print(json.dumps(findings, indent=2, sort_keys=True))
    else:
        _print(findings)
    return 0


if __name__ == "__main__":
    sys.exit(main())
