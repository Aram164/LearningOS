#!/usr/bin/env python3
"""How did the plans on disk actually get there?

This repository has a designed way to create and change a plan: a declared
capability, committed through the transaction service, snapshot-guarded,
validated whole, and recorded by an append-only receipt under
`operations/transactions/`. `module.plan.import` carries a module's source map
and its units together; `unit.map.import` carries one unit's map; the smaller
stage capabilities carry progress, notes, feedback and detours.

Nothing makes that path mandatory, and — the part that matters — nothing makes
its absence visible. A plan record edited with a text editor or an ad-hoc
script lands in exactly the same shape, passes the same validator, and is
indistinguishable from a gateway write the moment the commit is made.

So this tool asks the only question that separates them after the fact: for
every commit that changed a plan record, was a transaction receipt written in
the same commit? A commit with no receipt is not necessarily wrong — migrations
and the assembler's own drafts are legitimate — but it is a change the gateway
did not mediate, and the count is the honest size of that.

    python tools/plan_write_audit.py            # summary
    python tools/plan_write_audit.py --list     # every off-gateway commit
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

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
    return result.stdout.strip()


def commits_touching(paths) -> list[str]:
    out = git("log", "--format=%H", "--all", "--", *paths)
    return out.split() if out else []


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--list", action="store_true",
                        help="print every commit that changed a plan without a receipt")
    args = parser.parse_args(argv)

    plan_commits = commits_touching(PLAN_PATHS)
    with_receipt = set(commits_touching([RECEIPT_PATH]))
    if not plan_commits:
        print("no commits touch a plan record — is this a fresh clone?")
        return 0

    mediated = [c for c in plan_commits if c in with_receipt]
    unmediated = [c for c in plan_commits if c not in with_receipt]
    share = 100.0 * len(mediated) / len(plan_commits)

    print(f"commits that changed a plan record : {len(plan_commits)}")
    print(f"  carrying a transaction receipt   : {len(mediated)} ({share:.0f}%)")
    print(f"  with no receipt in the same commit: {len(unmediated)}")
    print()
    print(f"receipts on disk                   : "
          f"{len(list((REPO / RECEIPT_PATH).glob('*.yaml')))}")

    if args.list:
        print("\noff-gateway commits, newest first:")
        for commit in unmediated:
            print("  " + git("log", "-1", "--format=%h %ad %s",
                             "--date=short", commit)[:100])
    else:
        print("\nRun with --list to see which commits those were.")

    print(
        "\nA commit without a receipt is not automatically a defect — migrations\n"
        "under tools/migrations/ and the assembler's reviewed drafts are\n"
        "legitimate. What the number measures is how much of the plan surface\n"
        "changed outside the one path that leaves evidence."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
