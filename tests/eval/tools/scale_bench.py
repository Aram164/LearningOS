#!/usr/bin/env python3
"""Time ordinary LearningOS operations on one world, repeatedly.

    python tests/eval/tools/scale_bench.py --world WORLD_REPO --reps 3 --out bench.json

Measures wall-clock time (median, min, max over --reps) for: validate,
generate (cold: generated/ removed first), generate (warm), search (metadata),
first content search after each rebuild, immediate repeat of the same content
search, inspect (one note), related, bootstrap --brief, resume, and
an incremental cycle — append one line to one note body, then generate and
search again. Also records the note count, the bytes under generated/, and the
world HEAD. The note's original bytes are written back afterwards, so the world
ends as it started except for generated/.

The first-after-rebuild sample is an application cold path; the script does not
flush the operating system's file cache. Timings in a shared container are
noisy. The report keeps every sample and output digest; a reader should not
quote a median whose spread (max − min) exceeds it.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import statistics
import subprocess
import sys
import time
from pathlib import Path


def run(repo: Path, args: list[str]) -> tuple[float, int, str]:
    start = time.perf_counter()
    proc = subprocess.run([sys.executable, *args], cwd=repo, capture_output=True, text=True,
                          timeout=3600)
    return (time.perf_counter() - start, proc.returncode,
            hashlib.sha256(proc.stdout.encode("utf-8")).hexdigest())


def stats(samples: list[float]) -> dict:
    return {"median_s": round(statistics.median(samples), 3), "min_s": round(min(samples), 3),
            "max_s": round(max(samples), 3), "samples_s": [round(s, 3) for s in samples]}


def derived_bytes(repo: Path) -> int:
    base = repo / "generated"
    return sum(p.stat().st_size for p in base.rglob("*") if p.is_file()) if base.is_dir() else 0


def clear_generated(repo: Path) -> None:
    base = repo / "generated"
    for child in base.iterdir():
        if child.name == ".gitkeep":
            continue
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--world", required=True, type=Path)
    parser.add_argument("--reps", type=int, default=3)
    parser.add_argument("--note", default="note-cfs-fair-share",
                        help="note edited for the incremental cycle")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    repo = args.world.resolve()
    if not (repo.parent.parent / "EVAL-WORLD.json").is_file():
        raise SystemExit("scale_bench: not an evaluation world (EVAL-WORLD.json missing)")
    note_path = next((repo / "knowledge/notes").rglob(f"{args.note}.md"), None)
    if note_path is None:
        raise SystemExit(f"scale_bench: note {args.note} not found")

    content_cmd = ["tools/los.py", "search", "stride", "--content", "--type", "note"]
    ops = {
        "validate": ["tools/validate.py", "--compact", "--no-report"],
        "generate_warm": ["tools/generate.py"],
        "search_metadata": ["tools/los.py", "search", "scheduling"],
        "inspect_note": ["tools/los.py", "inspect", args.note],
        "related_note": ["tools/los.py", "related", args.note],
        "bootstrap_brief": ["tools/los.py", "bootstrap", "--brief"],
        "resume": ["tools/los.py", "resume", "--json"],
    }
    samples: dict[str, list[float]] = {name: [] for name in ["generate_cold",
                                                             "search_content_first_after_rebuild",
                                                             "search_content_immediate_repeat", *ops,
                                                             "incremental_generate",
                                                             "incremental_search"]}
    exits: dict[str, set] = {name: set() for name in samples}
    output_hashes: dict[str, list[str]] = {name: [] for name in samples}
    host_load: list[list[float] | None] = []

    def record(name: str, result: tuple[float, int, str]) -> None:
        elapsed, code, digest = result
        samples[name].append(elapsed)
        exits[name].add(code)
        output_hashes[name].append(digest)

    for _ in range(args.reps):
        host_load.append(list(os.getloadavg()) if hasattr(os, "getloadavg") else None)
        clear_generated(repo)
        record("generate_cold", run(repo, ["tools/generate.py"]))
        record("search_content_first_after_rebuild", run(repo, content_cmd))
        record("search_content_immediate_repeat", run(repo, content_cmd))
        for name, cmd in ops.items():
            record(name, run(repo, cmd))
        original = note_path.read_text(encoding="utf-8")
        try:
            note_path.write_text(original + "\nIncremental probe line.\n", encoding="utf-8")
            record("incremental_generate", run(repo, ["tools/generate.py"]))
            record("incremental_search", run(repo, content_cmd))
        finally:
            note_path.write_text(original, encoding="utf-8")
    run(repo, ["tools/generate.py"])
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True,
                          text=True, env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"}).stdout.strip()
    report = {
        "bench_version": 2,
        "world": str(repo),
        "world_head": head,
        "notes": sum(1 for _ in (repo / "knowledge/notes").rglob("*.md")),
        "reps": args.reps,
        "host_load_1_5_15_per_rep": host_load,
        "derived_bytes": derived_bytes(repo),
        "operations": {name: {**stats(vals), "exit_codes": sorted(exits[name]),
                              "stdout_sha256_per_rep": output_hashes[name]}
                       for name, vals in samples.items()},
    }
    text = json.dumps(report, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
