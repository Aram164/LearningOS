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
import json
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))

from learning_os.store.receipt_chain import RECEIPT_DIR as _RECEIPT_DIR  # noqa: E402
from learning_os.store.receipt_chain import report_findings  # noqa: E402

RECEIPT_DIR = _RECEIPT_DIR.as_posix()


def report(root: Path) -> dict:
    return report_findings(root)


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
    for brk in findings.get("chain_breaks", []):
        print(f"CHAIN-BREAK {brk['path']} — sha256_before "
              f"{brk['actual_sha256_before']} != {brk['previous_receipt']} "
              f"sha256_after {brk['expected_sha256_before']} "
              f"(receipt {brk['receipt']})")
    for name in findings["malformed_receipts"]:
        print(f"MALFORMED {name} — not a readable, schema-shaped transaction receipt")
    for err in findings.get("baseline_errors", []):
        print(f"BASELINE-ERROR {err}")
    total = (len(findings["drift"]) + len(findings["untracked"])
             + len(findings["malformed_receipts"])
             + len(findings.get("chain_breaks", []))
             + len(findings.get("baseline_errors", [])))
    baselined = findings.get("baselined_chain_breaks", 0)
    migrated = findings.get("migration_exempt_breaks", 0)
    print(f"report-only: {total} finding(s) "
          f"(baselined breaks: {baselined}, migration-exempt: {migrated}); "
          f"use --check to gate")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path,
                        default=Path(__file__).resolve().parents[1])
    parser.add_argument("--json", action="store_true",
                        help="print the findings as JSON")
    parser.add_argument("--check", action="store_true",
                        help="exit 1 if un-baselined chain breaks, drift, "
                             "untracked records, or malformed receipts exist")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    findings = report(args.root)
    if args.json:
        print(json.dumps(findings, indent=2, sort_keys=True))
    else:
        _print(findings)
    if args.check:
        has_findings = any([
            findings["drift"],
            findings["untracked"],
            findings["malformed_receipts"],
            findings.get("chain_breaks"),
            findings.get("baseline_errors"),
        ])
        return 1 if has_findings else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
