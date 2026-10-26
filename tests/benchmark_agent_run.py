"""Counterbalanced read-only benchmark; full wire and output-field bytes.

Run with the checkout interpreter and --samples 6. Warm-up runs are excluded.
The same five public CLI operations run in both arms. The summaries select
less information; byte savings measure output selection, not less computation.
Writes and shared handler-level repository caching are outside this benchmark.
"""
from __future__ import annotations

import argparse
import json
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable
STEPS = [
    ["capabilities", "--compact", "--json"],
    ["bootstrap", "--brief"],
    ["inspect", "unit-aml-exam-prep"],
    ["intelligence-scan", "--brief", "--json"],
    ["capabilities", "capture.create", "--json"],
]
PLAN = {"steps": [
    {"id": "discover", "use": "discover-capabilities", "args": ["--compact", "--json"],
     "summary": {"fields": ["contract_version"]}},
    {"id": "boot", "use": "open-work-or-priority-question", "args": ["--brief"],
     "summary": {"fields": ["counts.modules", "counts.units", "counts.stages"]}},
    {"id": "unit", "use": "project.inspect", "args": ["unit-aml-exam-prep"],
     "summary": {"fields": ["id", "kind"]}},
    {"id": "queue", "use": "intelligence-scan", "args": ["--brief", "--json"], "clusters": True},
    {"id": "cap", "use": "capture.create", "describe": True,
     "summary": {"fields": ["payload_schema.type", "payload_schema.properties.text.type"]}},
]}


def baseline() -> dict:
    started = time.perf_counter()
    raw, wire = 0, 0
    for argv in STEPS:
        proc = subprocess.run([PY, str(ROOT / "tools/los.py"), *argv], cwd=ROOT,
                              capture_output=True, timeout=60)
        assert proc.returncode == 0, (argv, proc.stderr.decode()[-2000:])
        raw += len(proc.stdout)
        wire += len(proc.stdout) + len(proc.stderr)
    return {"ms": round((time.perf_counter() - started) * 1000), "raw_bytes": raw,
            "wire_bytes": wire, "step_output_bytes": raw, "processes": 5, "agent_calls": 5}


def runner(plan_path: Path) -> dict:
    started = time.perf_counter()
    proc = subprocess.run([PY, str(ROOT / "tools/agent_run.py"), str(plan_path)], cwd=ROOT,
                          capture_output=True, timeout=60)
    ms = round((time.perf_counter() - started) * 1000)
    assert proc.returncode == 0, (proc.stdout.decode()[-2000:], proc.stderr.decode()[-2000:])
    report = json.loads(proc.stdout)
    totals = report["totals"]
    assert totals["ok"] == len(STEPS), report
    assert not any(row.get("output", {}).get("_missing_fields") for row in report["steps"]), report
    return {"ms": ms, "raw_bytes": totals["raw_bytes"],
            "wire_bytes": len(proc.stdout) + len(proc.stderr),
            "step_output_bytes": totals["out_bytes"], "processes": 1,
            "agent_calls": totals["agent_calls"], "step_ms_sum": totals["ms"],
            "step_ms": {row["id"]: row["ms"] for row in report["steps"]}}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples", type=int, default=6)
    parser.add_argument("--warmup", type=int, default=1)
    args = parser.parse_args()
    if args.samples < 2 or args.warmup < 0:
        parser.error("use at least two samples and nonnegative warmup")
    samples = []
    with tempfile.TemporaryDirectory(prefix="agent-run-bench-") as directory:
        plan_path = Path(directory) / "plan.json"
        plan_path.write_text(json.dumps(PLAN))
        for _ in range(args.warmup):
            baseline()
            runner(plan_path)
        for i in range(args.samples):
            order = ["baseline", "runner"] if i % 2 == 0 else ["runner", "baseline"]
            row: dict = {"order": order}
            for arm in order:
                row[arm] = baseline() if arm == "baseline" else runner(plan_path)
            assert row["baseline"]["raw_bytes"] == row["runner"]["raw_bytes"], row
            samples.append(row)
            print(f"sample {i + 1}/{args.samples}: baseline {row['baseline']['ms']} ms; "
                  f"runner {row['runner']['ms']} ms", file=sys.stderr, flush=True)
    medians = {arm: {key: statistics.median(row[arm][key] for row in samples)
                     for key in ("ms", "raw_bytes", "wire_bytes", "step_output_bytes")}
               for arm in ("baseline", "runner")}
    spread = {arm: {"min_ms": min(row[arm]["ms"] for row in samples),
                    "max_ms": max(row[arm]["ms"] for row in samples),
                    "stdev_ms": round(statistics.stdev(row[arm]["ms"] for row in samples), 2)}
              for arm in ("baseline", "runner")}
    print(json.dumps({"samples": samples, "warmup_pairs_excluded": args.warmup,
        "medians": medians, "spread": spread,
        "wall_reduction_percent": round(100 * (1 - medians["runner"]["ms"] / medians["baseline"]["ms"]), 2),
        "wire_reduction_percent": round(100 * (1 - medians["runner"]["wire_bytes"] / medians["baseline"]["wire_bytes"]), 2),
        "limits": "One machine; selected summaries contain less information; report metadata included in wire bytes; read-only plan."}, indent=2))


if __name__ == "__main__":
    main()
