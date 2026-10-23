#!/usr/bin/env python3
"""Inspect plan changes and receipt additions committed together.

The transaction service records canonical writes with append-only receipts
under `operations/transactions/`. This tool measures a narrower fact: which
plan-changing commits also added a YAML document whose type is
`transaction-receipt`. Ledger updates, edits to existing receipts, and renames
recognized by Git do not count as additions. Receipt documents are identified
by their type marker; this audit does not validate their schemas or match their
write sets and content hashes to individual plan changes.

Co-occurrence is not proof that the gateway mediated a plan change. A receipt
may concern a different write, or be committed separately from its plan;
recorded migrations are also legitimate. Investigate the actual receipt and
change before making a provenance judgment.

History covers commits selected by `git log --all` for the declared plan
paths, using all refs available in this clone. It excludes uncommitted changes,
unreachable commits, and history absent from a shallow or incomplete clone.
The on-disk receipt count describes the current working tree separately.

    python tools/plan_write_audit.py            # summary
    python tools/plan_write_audit.py --list     # commits without receipt additions
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]

# The records a "plan" is made of. The source map is included deliberately: a
# lecture's material menu, its locators and its angles live there, so editing it
# changes the plan a learner reads even though the study map is untouched.
PLAN_PATHS = (
    "curriculum/modules/*/units/*/study-map.yaml",
    "curriculum/modules/*/source-map.yaml",
    "curriculum/paths/*.yaml",
)
RECEIPT_PATH = "operations/transactions"


def git(*args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(REPO), *args],
        capture_output=True, text=True, check=False,
    )
    if result.returncode != 0:
        sys.exit(f"history could not be inspected\n{result.stderr.strip()}")
    return result.stdout.strip()


def commits_touching(paths) -> list[str]:
    out = git("log", "--format=%H", "--all", "--", *paths)
    return out.split() if out else []


def is_receipt(text: str, location: str) -> bool:
    """Identify receipt documents without claiming schema or hash validation."""
    try:
        document = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        sys.exit(f"transaction YAML could not be inspected: {location}\n{exc}")
    return isinstance(document, dict) and document.get("type") == "transaction-receipt"


def receipt_added(commit: str) -> bool:
    """Does a commit add a receipt, rather than edit or rename one?

    Inspect the whole diff before filtering paths so renames from outside the
    transaction directory remain renames. For merges an addition must be new
    relative to every parent, rather than brought in from one parent branch.
    """
    parents = git("rev-list", "--parents", "-n", "1", commit).split()[1:]
    comparisons = [(parent, commit) for parent in parents] or [(commit,)]
    additions = None
    for comparison in comparisons:
        changes = git("diff-tree", "--root", "--no-commit-id", "--name-status",
                      "-r", "--find-renames", "--diff-filter=A", "-z", *comparison)
        fields = changes.rstrip("\0").split("\0") if changes else []
        paths = {path for status, path in zip(fields[::2], fields[1::2], strict=True)
                 if status == "A" and Path(path).parent.as_posix() == RECEIPT_PATH
                 and Path(path).suffix == ".yaml"}
        additions = paths if additions is None else additions & paths
    for path in sorted(additions):
        if is_receipt(git("show", f"{commit}:{path}"), f"{commit}:{path}"):
            return True
    return False


def receipts_on_disk() -> int:
    count = 0
    for path in (REPO / RECEIPT_PATH).glob("*.yaml"):
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            sys.exit(f"transaction YAML could not be inspected: {path}\n{exc}")
        count += is_receipt(text, str(path))
    return count


def build_parser() -> argparse.ArgumentParser:
    """The tool's CLI surface (SPEC §7.4, PLAN D11)."""
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--list", action="store_true",
                        help="print plan-changing commits without a receipt addition")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    plan_commits = commits_touching(PLAN_PATHS)
    if not plan_commits:
        print("no commits touch a plan record — is this a fresh clone?")
        return 0

    with_receipt = {c for c in plan_commits if receipt_added(c)}
    without_receipt = [c for c in plan_commits if c not in with_receipt]
    share = 100.0 * len(with_receipt) / len(plan_commits)
    on_disk = receipts_on_disk()

    print("history scope: all refs available in this clone (git log --all)")
    print(f"commits that changed a plan record : {len(plan_commits)}")
    print(f"  also adding a receipt document   : {len(with_receipt)} ({share:.0f}%)")
    print(f"  without a receipt addition       : {len(without_receipt)}")
    print()
    print(f"receipt documents in working tree  : {on_disk}")

    if args.list:
        print("\nplan-changing commits without a receipt addition, newest first:")
        for commit in without_receipt:
            print("  " + git("log", "-1", "--format=%h %ad %s",
                             "--date=short", commit)[:100])
    else:
        print("\nRun with --list to see which commits those were.")

    print(
        "\nThis measures commit co-occurrence, not gateway mediation or per-write\n"
        "provenance. A receipt may concern a different write or be committed\n"
        "separately; recorded migrations are legitimate. Receipt schemas, write\n"
        "sets and hashes are not verified here. Ledger and existing-receipt\n"
        "updates are excluded. Uncommitted, unreachable and unavailable history\n"
        "is excluded; a shallow or incomplete clone can omit earlier changes."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
