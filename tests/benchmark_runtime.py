"""Read-only runtime benchmark: python tests/benchmark_runtime.py [--samples 3].

Each sample uses a fresh process. Generation is computed in memory; neither
canonical data nor live generated files are written. Output digests allow
before/after comparisons to check that faster execution preserves results.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))


def sample(*, python_loader: bool = False) -> dict:
    if python_loader:
        import yaml

        # Reproduce the original parser without editing production code.
        if hasattr(yaml, "CSafeLoader"):
            del yaml.CSafeLoader

    from learning_os.genout import generate_all
    from learning_os.loader import load_repo
    from learning_os.rules import validate

    started = time.perf_counter()
    repo = load_repo(ROOT)
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


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples", type=int, default=3)
    parser.add_argument("--python-loader", action="store_true",
                        help="compare with the original pure-Python safe parser")
    parser.add_argument("--sample", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.sample:
        print(json.dumps(sample(python_loader=args.python_loader)))
        return
    if args.samples < 1:
        parser.error("--samples must be positive")
    command = [sys.executable, __file__, "--sample"]
    if args.python_loader:
        command.append("--python-loader")
    samples = [json.loads(subprocess.check_output(
        command, cwd=ROOT, text=True,
    )) for _ in range(args.samples)]
    first = samples[0]
    if any(row["issues"] != first["issues"]
           or row["output_sha256"] != first["output_sha256"] for row in samples):
        raise SystemExit("repository or output changed between samples; repeat the benchmark")
    print(json.dumps({
        "samples": samples,
        "median_seconds": {
            phase: statistics.median(row["seconds"][phase] for row in samples)
            for phase in first["seconds"]
        },
    }, indent=2))


if __name__ == "__main__":
    main()
