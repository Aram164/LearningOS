#!/usr/bin/env python3
"""The warning policy, made executable.

    python tools/warning_baseline.py --check    # fail on any NEW warning
    python tools/warning_baseline.py --show     # print the current delta
    python tools/warning_baseline.py --update --note "…"   # adopt the current set

WHY THIS EXISTS
---------------
Two documents disagreed about what a clean repository is. `CLAUDE.md` hard rule
9 said work is not done until the validator prints "0 errors, 0 warnings". The
validator prints 535 warnings and exits 0, the pre-commit hook lets them
through by design, and `README.md` says plainly that warnings never block. So
the strictest statement of the rule was the one no run could satisfy — and a
rule that is always violated stops being read as a rule at all.

The warnings are not noise. They are the measured content debt of
CRITIQUE-POINTS §1: vague locators and missing angle detail across the study
maps, deliberately deferred because backfilling them is the expensive half.
Deferring them was a decision. Losing the ability to tell a deferred warning
from a new one was not.

WHAT THE POLICY IS, NOW THAT IT IS ONE
--------------------------------------
    Zero errors, always.  Warnings stay visible and never block.  No NEW
    warning signature, and no existing signature that grows.

WHY A SIGNATURE AND NOT A COUNT
--------------------------------
A total is trivially gamed: fix one locator, introduce one new warning
elsewhere, and 535 stays 535 while the repository is quietly worse. A signature
is the pair (code, path) with its multiplicity, so "one LOCATOR-VAGUE traded
for one ROUTE-ANGLE-DETAIL-MISSING in a different module" is visible as what it
is — one regression and one repair, not a wash.

WHAT IS DELIBERATELY EXCLUDED
------------------------------
`rules.common.BASELINE_EXEMPT_WARNINGS` is the exact union of two named sets,
each excluded for its own reason:

- `ENVIRONMENTAL_WARNINGS` — about the machine, not the content: an unmounted
  materials drive, a stale generated view, a crashed git process's lock file
  (`HYGIENE-LOCK`). True before and after any change, and they differ between
  Aram's laptop and CI; baselining them would make an unrelated commit fail
  because a drive happened to be offline.
- `DYNAMIC_ADVISORY_WARNINGS` — about elapsed wall-clock time, not an authored
  edit: `WS-NEGLECT` and `INBOX-STALE` can newly appear with zero authored
  files touched, purely because days passed. Baselining them would make an
  unrelated release fail on a clock tick.

Membership in either set is by exact warning code only — never a prefix, a
severity band, or a path heuristic — so an unknown future warning code is
baseline-managed by default, and every other authored-content warning (a new
`LOCATOR-VAGUE`, a grown `ROUTE-ANGLE-DETAIL-MISSING`) still fails the gate.
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys
from collections import Counter
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))

from learning_os.loader import load_repo  # noqa: E402
from learning_os.rules import validate  # noqa: E402
from learning_os.rules.common import BASELINE_EXEMPT_WARNINGS  # noqa: E402

BASELINE_RELATIVE = "operations/validation-warning-baseline.yaml"

_HEADER = """\
# The validation warning baseline — what is deferred, and nothing more.
#
# Validation success means ZERO ERRORS. Warnings stay visible and never block.
# What this file adds is the third clause: no NEW warning signature, and no
# existing signature that grows.
#
# A signature is (code, path) with its multiplicity, not a total. A total is
# gamed by trading one warning for another; a signature is not.
#
# Two exact sets are excluded on purpose: environmental warnings describe the
# machine (unmounted drive, stale view, crashed git lock), not the content,
# and differ between one checkout and the next; dynamic-advisory warnings
# (WS-NEGLECT, INBOX-STALE) are clock-derived and can appear with no authored
# edit. Both stay visible in normal validation output; neither is exempt by
# prefix or heuristic, only by exact code (learning_os.rules.common).
#
# These warnings are the measured content debt of CRITIQUE-POINTS §1. Adopting
# them here defers them; it does not close the point.
#
#   python tools/warning_baseline.py --check                 # gate
#   python tools/warning_baseline.py --show                  # the delta
#   python tools/warning_baseline.py --update --note "…"     # adopt current
"""


def collect(root: Path) -> tuple[Counter, list[str]]:
    """(signature counter, error strings) for the repository at ``root``."""
    issues = validate(load_repo(root), online=False)
    signatures: Counter = Counter()
    errors: list[str] = []
    for issue in issues:
        if issue.severity == "E":
            errors.append(str(issue))
            continue
        if issue.code in BASELINE_EXEMPT_WARNINGS:
            continue
        signatures[(issue.code, issue.path)] += 1
    return signatures, errors


def load_baseline(root: Path) -> tuple[Counter, dict]:
    path = root / BASELINE_RELATIVE
    if not path.is_file():
        return Counter(), {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    counter: Counter = Counter()
    for row in data.get("signatures") or ():
        counter[(row["code"], row.get("path", ""))] = int(row["count"])
    return counter, data


def write_baseline(root: Path, signatures: Counter, note: str) -> None:
    rows = [
        {"code": code, "path": path, "count": count}
        for (code, path), count in sorted(signatures.items())
    ]
    payload = {
        "baseline_version": 1,
        "recorded": dt.date.today().isoformat(),
        "note": note,
        "total": sum(signatures.values()),
        "distinct_signatures": len(rows),
        "signatures": rows,
    }
    path = root / BASELINE_RELATIVE
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        _HEADER + yaml.safe_dump(payload, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


def delta(baseline: Counter, current: Counter) -> tuple[list[str], list[str]]:
    """(regressions, repairs) as human-readable lines."""
    regressions: list[str] = []
    repairs: list[str] = []
    for key in sorted(set(baseline) | set(current)):
        before, after = baseline.get(key, 0), current.get(key, 0)
        if after > before:
            code, path = key
            regressions.append(
                f"{code} at {path or '<repository>'}: {before} → {after}")
        elif after < before:
            code, path = key
            repairs.append(
                f"{code} at {path or '<repository>'}: {before} → {after}")
    return regressions, repairs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true",
                      help="fail on any new or grown warning signature (default)")
    mode.add_argument("--show", action="store_true",
                      help="print the delta without deciding anything")
    mode.add_argument("--update", action="store_true",
                      help="adopt the current set as the baseline")
    parser.add_argument("--note", default="",
                        help="why the baseline moved (required with --update)")
    parser.add_argument("--root", default=None)
    args = parser.parse_args()

    root = Path(args.root).resolve() if args.root else Path(__file__).resolve().parent.parent
    current, errors = collect(root)
    baseline, meta = load_baseline(root)

    if args.update:
        if not args.note:
            print("warning-baseline: --update needs --note explaining the move",
                  file=sys.stderr)
            return 2
        write_baseline(root, current, args.note)
        print(f"warning-baseline: adopted {sum(current.values())} warning(s) "
              f"across {len(current)} signature(s) — {BASELINE_RELATIVE}")
        return 0

    regressions, repairs = delta(baseline, current)
    total_before = sum(baseline.values())
    total_after = sum(current.values())

    print(f"warning-baseline: {total_after} warning(s) across {len(current)} "
          f"signature(s); baseline {total_before} across {len(baseline)}"
          + (f" (recorded {meta['recorded']})" if meta.get("recorded") else ""))
    for line in repairs:
        print(f"  repaired  {line}")
    for line in regressions:
        print(f"  NEW       {line}")

    if args.show:
        return 0

    if errors:
        print(f"\nwarning-baseline: {len(errors)} validation ERROR(s) — "
              "validation success means zero errors", file=sys.stderr)
        for line in errors[:20]:
            print(f"  {line}", file=sys.stderr)
        return 1

    if regressions:
        print(f"\nwarning-baseline: {len(regressions)} new or grown warning "
              "signature(s). Fix them, or adopt them deliberately with "
              "`--update --note \"…\"`.", file=sys.stderr)
        return 1

    print("\nwarning-baseline: OK — zero errors, no new warning signature.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
