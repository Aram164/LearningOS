"""The warning policy as a library: zero errors, no new or grown signature.

`tools/warning_baseline.py` is the CLI over this; `commands/module.py` uses it
for the module-plan preflight. They were two implementations of one policy
until 2026-08-29, and they disagreed: the CLI compared against the recorded
baseline, while the plan preflight treated *every* non-exempt warning anywhere
in the repository as blocking. That made the second gate unsatisfiable — the
535 baselined warnings of CRITIQUE-POINTS §1 are deferred content debt, so any
module's plan import failed on another module's deferred locators.

The policy, stated once (CLAUDE.md hard rule 9, README, and the baseline file's
own header):

    Zero errors, always. Warnings stay visible and never block. No NEW warning
    signature, and no existing signature that grows.

A signature is the pair (code, path) with its multiplicity, so trading one
warning for another in a different file reads as one regression and one repair
rather than as a wash.
"""

from __future__ import annotations

import datetime as dt
from collections import Counter
from pathlib import Path

import yaml

from .loader import load_repo
from .rules import validate
from .rules.common import BASELINE_EXEMPT_WARNINGS

BASELINE_RELATIVE = "operations/validation-warning-baseline.yaml"


def signatures_from_issues(issues) -> tuple[Counter, list[str]]:
    """Split validation issues into (baseline-managed signatures, error strings).

    Environmental and dynamic-advisory warnings are dropped by exact code, never
    by prefix or heuristic, so an unknown future code stays baseline-managed.
    """
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


def collect(root: Path) -> tuple[Counter, list[str]]:
    """(signature counter, error strings) for the repository at ``root``."""
    return signatures_from_issues(validate(load_repo(root), online=False))


def load_baseline(root: Path) -> tuple[Counter, dict]:
    path = Path(root) / BASELINE_RELATIVE
    if not path.is_file():
        return Counter(), {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    counter: Counter = Counter()
    for row in data.get("signatures") or ():
        counter[(row["code"], row.get("path", ""))] = int(row["count"])
    return counter, data


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
    path = Path(root) / BASELINE_RELATIVE
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        _HEADER + yaml.safe_dump(payload, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
