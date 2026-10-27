"""Non-gating runtime measurements on a disposable, deterministic repository.

Each timed sample starts a fresh process; fixture setup and warmup are excluded.
Generation stays in memory. --root opts into an existing read-only repository;
make bench always uses the synthetic workload and the committed baseline.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))


def sample(root: Path, *, python_loader: bool = False) -> dict:
    if python_loader:
        import yaml

        if hasattr(yaml, "CSafeLoader"):
            del yaml.CSafeLoader

    from learning_os.derive.projection import generate_all
    from learning_os.derive.validation import validate
    from learning_os.store.loader import load_repo

    started = time.perf_counter()
    repo = load_repo(root)
    loaded = time.perf_counter()
    issues = validate(repo, online=False)
    validated = time.perf_counter()
    outputs = generate_all(repo)
    generated = time.perf_counter()
    return {
        "seconds": {
            "load": loaded - started,
            "validate_loaded_repo": validated - loaded,
            "generate_loaded_repo": generated - validated,
            "total": generated - started,
        },
        "issues": [str(issue) for issue in issues],
        "output_sha256": {
            path: hashlib.sha256(content.encode("utf-8")).hexdigest()
            for path, content in sorted(outputs.items())
        },
        "output_bytes": sum(len(content.encode("utf-8")) for content in outputs.values()),
    }


def _measure(args, root: Path, env: dict) -> dict:
    command = [sys.executable, __file__, "--sample", "--root", str(root)]
    if args.python_loader:
        command.append("--python-loader")
    rows = [json.loads(subprocess.check_output(command, cwd=ROOT, text=True, env=env))
            for _ in range(args.warmup + args.samples)]
    samples = rows[args.warmup:]
    first = samples[0]
    semantic = {key: first[key] for key in ("issues", "output_sha256", "output_bytes")}
    if any(any(row[key] != value for key, value in semantic.items()) for row in rows):
        raise SystemExit("output changed between samples; repeat the benchmark")
    report = {
        "schema_version": 1,
        "measurement_source": {
            "head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
            "dirty": bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT)),
            "producer_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "fixture_builders_sha256": {
                name: hashlib.sha256((ROOT / "tests" / name).read_bytes()).hexdigest()
                for name in ("conftest.py", "repo_builders.py")
            },
        },
        "workload": "existing-repository" if args.root else "synthetic-demo-v1",
        "environment": {"python": platform.python_version(), "system": platform.system(),
                        "machine": platform.machine(), "python_loader": args.python_loader},
        "warmup_excluded": args.warmup,
        "sample_seconds": [row["seconds"] for row in samples],
        "median_seconds": {
            phase: statistics.median(row["seconds"][phase] for row in samples)
            for phase in first["seconds"]
        },
        "semantic": semantic,
    }
    if args.baseline:
        baseline = json.loads(args.baseline.read_text())
        if baseline["workload"] != report["workload"]:
            raise SystemExit("baseline uses a different workload")
        report["comparison"] = {
            "semantic_match": baseline["semantic"] == semantic,
            "environment_match": baseline["environment"] == report["environment"],
            "percent_change": {
                phase: 100 * (seconds / baseline["median_seconds"][phase] - 1)
                for phase, seconds in report["median_seconds"].items()
            },
            "interpretation": "negative is faster; informational only, no timing threshold",
        }
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples", type=int, default=3)
    parser.add_argument("--warmup", type=int, default=1)
    parser.add_argument("--python-loader", action="store_true")
    parser.add_argument("--root", type=Path, help="explicit opt-in to an existing read-only tree")
    parser.add_argument("--baseline", type=Path, help="print changes against this retained measurement")
    parser.add_argument("--write-baseline", type=Path, help="retain these measurements for future comparisons")
    parser.add_argument("--sample", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.sample:
        print(json.dumps(sample(args.root, python_loader=args.python_loader)))
        return
    if args.samples < 1 or args.warmup < 0:
        parser.error("--samples must be positive and --warmup nonnegative")
    with tempfile.TemporaryDirectory(prefix="los-runtime-bench-") as temporary:
        env = dict(os.environ)
        if args.root:
            root = args.root.resolve()
        else:
            from conftest import build_mini_repo
            from repo_builders import add_curriculum

            root = build_mini_repo(Path(temporary) / "fixture").resolve()
            add_curriculum(root)
            observations = Path(temporary) / "observations.json"
            observations.write_text(json.dumps({
                "now": "2026-10-01T09:00:00+02:00", "mtimes": {},
                "git": {"head": None, "head_time": None, "dates": {}, "timestamps": {}},
            }))
            env["LOS_OBSERVATIONS"] = str(observations)
        report = _measure(args, root, env)
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.write_baseline:
        args.write_baseline.write_text(rendered)
    print(rendered, end="")


if __name__ == "__main__":
    main()
