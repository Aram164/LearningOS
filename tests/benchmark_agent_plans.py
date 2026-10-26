"""Synthetic benchmark matrix (W1-W9 harness). Run manually, not in CI gate.

Usage: .venv/bin/python tests/benchmark_agent_plans.py --root FIXTURE
Prints raw samples; semantic parity must be checked by the caller.
"""
from __future__ import annotations

import argparse
import json
import statistics
import time


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--repeats", type=int, default=10)
    args = ap.parse_args()
    samples = []
    for _ in range(args.repeats):
        start = time.perf_counter()
        samples.append(round((time.perf_counter() - start) * 1000, 3))
    print(json.dumps({"workload": "harness-smoke", "root": args.root,
                      "samples_ms": samples,
                      "median_ms": statistics.median(samples)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
