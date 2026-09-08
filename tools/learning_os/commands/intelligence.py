"""Read-only intelligence commands. Nothing here writes: the scan reads
the current world, proposes candidate investigations on stdout, and
exits. Filing anything into the proposal queue is the operator's job."""

from __future__ import annotations

import json

from learning_os.semantics.goals import goal_to_dict
from learning_os.semantics.scan import intelligence_scan

from .support import _root


def cmd_intelligence_scan(args) -> int:
    """Run one observation loop: observe, interpret, propose."""
    if args.days < 0:
        print("intelligence scan: --days is never negative")
        return 2
    root = _root(args)
    goals = intelligence_scan(root, days=args.days)
    if args.json:
        print(json.dumps(
            {"goals": [goal_to_dict(goal) for goal in goals]},
            indent=2, sort_keys=True, ensure_ascii=False))
        return 0
    if not goals:
        print("intelligence scan: no candidates — "
              "nothing moved that the detectors cover")
        return 0
    print(f"intelligence scan: {len(goals)} candidate investigation(s) — "
          "filing is yours:")
    for number, goal in enumerate(goals, start=1):
        print(f"{number}. {goal.title}")
        print(f"   why: {goal.rationale}")
        print(f"   evidence: {', '.join(goal.evidence)}")
    return 0
