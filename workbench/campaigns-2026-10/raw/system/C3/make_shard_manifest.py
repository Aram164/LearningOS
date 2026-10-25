#!/usr/bin/env python3
"""Generate the C3 shard manifest from a CI-measured JUnit XML.

Input: junit.xml written by the C3 measurement run (unsharded, per-test
durations from a GitHub runner). Output: shard_manifest.json for the
workflow env, plus a balance report on stderr.

Rules:
  - the witness block (all witness-producing files + the two zz population
    files) stays atomic: either one shard ("witness") or, with
    --split-witness K, the producers balance over K legs and the two zz
    files move to the merge job ("zz-merge").
  - every other file is assigned whole (file granularity) to the labelled
    shard with the smallest running total (greedy longest-first).
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

WITNESS_BLOCK = [
    "tests/test_procedures.py",
    "tests/test_scenarios.py",
    "tests/test_scenarios_effects.py",
    "tests/test_scenarios_health_shim.py",
    "tests/test_scenarios_recovery.py",
    "tests/test_scenarios_session.py",
    "tests/test_scenarios_zz_operational_owners.py",
    "tests/test_scenarios_zz_refusal_sites.py",
]
ZZ_FILES = {
    "tests/test_scenarios_zz_operational_owners.py",
    "tests/test_scenarios_zz_refusal_sites.py",
}


def load(junit: Path) -> tuple[dict[str, float], dict[str, int]]:
    root = ET.parse(junit).getroot()
    suites = [root] if root.tag == "testsuite" else list(root)
    durations: dict[str, float] = defaultdict(float)
    counts: dict[str, int] = defaultdict(int)
    for suite in suites:
        for case in suite.iter("testcase"):
            # pytest's default junit family carries no file attribute; the
            # module path is the classname minus any trailing class name.
            # Every suite file lives directly under tests/.
            parts = (case.get("classname") or "").split(".")
            if len(parts) < 2 or parts[0] != "tests":
                continue
            rel = f"tests/{parts[1]}.py"
            durations[rel] += float(case.get("time", "0"))
            counts[rel] += 1
    return dict(durations), dict(counts)


def balance(items: dict[str, float], k: int) -> list[tuple[float, list[str]]]:
    shards: list[list] = [[0.0, []] for _ in range(k)]
    for f in sorted(items, key=lambda f: -items[f]):
        lightest = min(shards, key=lambda s: s[0])
        lightest[0] += items[f]
        lightest[1].append(f)
    return [(s[0], s[1]) for s in shards]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("junit", type=Path)
    ap.add_argument("--target-minutes", type=float, default=30.0)
    ap.add_argument("--witness-max-minutes", type=float, default=33.0)
    ap.add_argument("--split-witness", type=int, default=0, metavar="K")
    args = ap.parse_args()

    durations, counts = load(args.junit)
    witness_set = set(WITNESS_BLOCK)
    missing = sorted(witness_set - set(durations))
    if missing:
        print(f"FATAL: witness files absent from junit: {missing}", file=sys.stderr)
        return 2

    def mins(files: list[str]) -> float:
        return sum(durations[f] for f in files) / 60

    witness_total = mins(WITNESS_BLOCK)
    rest = {f: d for f, d in durations.items() if f not in witness_set}
    print(f"witness block (atomic): {witness_total:7.1f} min", file=sys.stderr)
    print(f"rest of suite:          {sum(rest.values())/60:7.1f} min", file=sys.stderr)

    manifest: dict[str, list[str]] = {}
    if args.split_witness > 0:
        producers = [f for f in WITNESS_BLOCK if f not in ZZ_FILES]
        zz = sorted(ZZ_FILES)
        for i, (leg_time, files) in enumerate(
                balance({f: durations[f] for f in producers}, args.split_witness)):
            manifest[f"witness-{i}"] = sorted(files)
            print(f"witness-{i}: {leg_time/60:7.1f} min ({len(files)} files)", file=sys.stderr)
        manifest["zz-merge"] = zz
        print(f"zz-merge (merge job):   {mins(zz):7.1f} min", file=sys.stderr)
    else:
        if witness_total > args.witness_max_minutes:
            print(f"FATAL: witness block {witness_total:.1f} min exceeds "
                  f"{args.witness_max_minutes} min; rerun with --split-witness K",
                  file=sys.stderr)
            return 3
        manifest["witness"] = sorted(WITNESS_BLOCK)
        print(f"witness shard:          {witness_total:7.1f} min", file=sys.stderr)

    k = max(1, math.ceil(sum(rest.values()) / 60 / args.target_minutes))
    for i, (leg_time, files) in enumerate(balance(rest, k)):
        manifest[str(i)] = sorted(files)
        print(f"shard {i}:     {leg_time/60:7.1f} min ({len(files)} files)", file=sys.stderr)

    pytest_legs = {n: mins(f) for n, f in manifest.items() if n != "zz-merge"}
    print(f"slowest pytest leg:     {max(pytest_legs.values()):7.1f} min "
          f"({max(pytest_legs, key=pytest_legs.get)})", file=sys.stderr)
    print(f"legs: {len(manifest)}", file=sys.stderr)

    covered = [f for files in manifest.values() for f in files]
    if len(covered) != len(set(covered)):
        print("FATAL: a file landed in two shards", file=sys.stderr)
        return 4
    print(f"files covered: {len(covered)} of {len(durations)} in junit; "
          f"counts: {sum(counts.values())} tests", file=sys.stderr)
    Path("shard_manifest.json").write_text(
        json.dumps(manifest, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
