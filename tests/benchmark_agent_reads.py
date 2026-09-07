"""Measure agent response volume and batched reads without canonical writes.

Run with .venv/bin/python tests/benchmark_agent_reads.py. Fresh CLI processes
exercise the old and recommended startup paths against the same repository.
Bytes measure response volume, not model tokens or billed cost.
"""

from __future__ import annotations

import argparse
import json
import statistics
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOS = ROOT / "tools/los.py"


def invoke(*arguments: str) -> tuple[dict, int]:
    raw = subprocess.check_output([sys.executable, str(LOS), *arguments], cwd=ROOT)
    return json.loads(raw), len(raw)


def sample() -> dict:
    catalogue, old_catalogue_bytes = invoke("capabilities", "--json")
    index, index_bytes = invoke("capabilities", "--compact", "--json")
    full, full_bytes = invoke("bootstrap")
    summary, summary_bytes = invoke("bootstrap", "--compact")
    for section in ("queries", "commands"):
        if index[section] != sorted(catalogue[section]):
            raise SystemExit("capability index lost public names")
    if full["snapshot"]["snapshot_id"] != summary["snapshot_id"]:
        raise SystemExit("repository changed during startup comparison")
    ids = [row["id"] for row in summary["collections"]["modules"]["items"][:3]]
    if len(ids) < 2:
        raise SystemExit("benchmark requires at least two visible modules")
    started = time.perf_counter()
    single_results = [invoke("inspect", record_id) for record_id in ids]
    single_seconds = time.perf_counter() - started
    started = time.perf_counter()
    batch, batch_bytes = invoke("inspect", *ids)
    batch_seconds = time.perf_counter() - started
    if batch["records"] != [record for record, _size in single_results]:
        raise SystemExit("batch differs from individual reads; check for concurrent changes")
    if batch["snapshot_id"] != summary["snapshot_id"]:
        raise SystemExit("repository changed during inspection comparison")
    return {
        "snapshot_id": batch["snapshot_id"], "inspected_ids": ids,
        "stdout_bytes": {
            "full_catalogue": old_catalogue_bytes, "capability_index": index_bytes,
            "full_bootstrap": full_bytes, "compact_bootstrap": summary_bytes,
            "old_claude_startup": old_catalogue_bytes + full_bytes,
            "previous_compact_startup": old_catalogue_bytes + summary_bytes,
            "recommended_startup": index_bytes + summary_bytes,
            "individual_inspections": sum(size for _record, size in single_results),
            "batch_inspection": batch_bytes,
        },
        "seconds": {"individual_inspections": single_seconds, "batch_inspection": batch_seconds},
        "records_identical": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples", type=int, default=3)
    args = parser.parse_args()
    if args.samples < 1:
        parser.error("--samples must be positive")
    samples = [sample() for _ in range(args.samples)]
    if any(row["snapshot_id"] != samples[0]["snapshot_id"] for row in samples):
        raise SystemExit("repository changed between samples")
    print(json.dumps({
        "samples": samples,
        "median_seconds": {
            key: statistics.median(row["seconds"][key] for row in samples)
            for key in samples[0]["seconds"]
        },
    }, indent=2))


if __name__ == "__main__":
    main()
