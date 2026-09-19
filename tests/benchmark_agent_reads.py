"""Measure agent response volume and batched reads without canonical writes.

Run with .venv/bin/python tests/benchmark_agent_reads.py. Fresh CLI processes
exercise the old and recommended startup paths against the same repository.
Bytes measure response volume, not model tokens or billed cost. The triage
arm reads gitignored generated views, so no snapshot guard applies to it.
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


def triage_sample() -> dict:
    """Summary-vs-full read volume over cached chapters.

    Phase 0 runs denominator-only: with no summaries cached, the arm
    reports the text-cache totals a full-read triage must ingest.
    """
    rows = []
    for meta in sorted((ROOT / "generated").glob("summaries/*/pages-*/meta.json")):
        try:
            record = json.loads(meta.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        digest = record.get("sha256")
        span = record.get("page_range") or []
        if not digest or len(span) != 2:
            continue
        try:
            summary_bytes = len((meta.parent / "summary.md").read_bytes())
        except OSError:
            continue
        full_bytes = 0
        for page in range(span[0], span[1] + 1):
            page_path = (ROOT / "generated" / "text-cache" / digest
                         / f"pp-{page:04d}.txt")
            try:
                full_bytes += len(page_path.read_bytes())
            except OSError:
                full_bytes = 0
                break
        if not full_bytes:
            continue
        rows.append({"material": record.get("material"), "digest": digest,
                     "page_range": span, "summary_bytes": summary_bytes,
                     "full_bytes": full_bytes})
    cached_materials = len(list((ROOT / "generated").glob("text-cache/*/index.json")))
    totals = {"chapters": len(rows),
              "summary_bytes": sum(row["summary_bytes"] for row in rows),
              "full_bytes": sum(row["full_bytes"] for row in rows),
              "cached_materials": cached_materials}
    totals["ratio"] = (totals["summary_bytes"] / totals["full_bytes"]
                       if totals["full_bytes"] else None)
    return {"rows": rows, "totals": totals}


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
        "triage": triage_sample(),
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
