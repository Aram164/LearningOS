#!/usr/bin/env python3
"""Time ordinary LearningOS operations on one world, repeatedly.

    python tests/eval/tools/scale_bench.py --world WORLD_REPO --reps 3 --out bench.json

Measures wall-clock time (median, min, max over --reps) for: validate,
generate (cold: generated/ removed first), generate (warm), search (metadata),
search --content, inspect (one note), related, bootstrap --brief, resume, and
an incremental cycle — append one line to one note body, then generate and
search again. Also records the note count, the bytes under generated/, and the
world HEAD. The note's original bytes are written back afterwards, so the world
ends as it started except for generated/.

Timings in a shared container are noisy. The report keeps every sample; a
reader should not quote a median whose spread (max − min) exceeds it.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import statistics
import subprocess
import sys
import time
from pathlib import Path


def run(repo: Path, args: list[str]) -> tuple[float, int]:
    start = time.perf_counter()
    proc = subprocess.run([sys.executable, *args], cwd=repo, capture_output=True, text=True,
                          timeout=3600)
    return time.perf_counter() - start, proc.returncode


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

    ops = {
        "validate": ["tools/validate.py", "--compact", "--no-report"],
        "generate_warm": ["tools/generate.py"],
        "search_metadata": ["tools/los.py", "search", "scheduling"],
        "search_content": ["tools/los.py", "search", "stride", "--content", "--type", "note"],
        "inspect_note": ["tools/los.py", "inspect", args.note],
        "related_note": ["tools/los.py", "related", args.note],
        "bootstrap_brief": ["tools/los.py", "bootstrap", "--brief"],
        "resume": ["tools/los.py", "resume", "--json"],
    }
    samples: dict[str, list[float]] = {name: [] for name in ["generate_cold", *ops,
                                                             "incremental_generate",
                                                             "incremental_search"]}
    exits: dict[str, set] = {name: set() for name in samples}
    for _ in range(args.reps):
        clear_generated(repo)
        t, code = run(repo, ["tools/generate.py"])
        samples["generate_cold"].append(t)
        exits["generate_cold"].add(code)
        for name, cmd in ops.items():
            t, code = run(repo, cmd)
            samples[name].append(t)
            exits[name].add(code)
        original = note_path.read_text(encoding="utf-8")
        try:
            note_path.write_text(original + "\nIncremental probe line.\n", encoding="utf-8")
            t, code = run(repo, ["tools/generate.py"])
            samples["incremental_generate"].append(t)
            exits["incremental_generate"].add(code)
            t, code = run(repo, ops["search_content"])
            samples["incremental_search"].append(t)
            exits["incremental_search"].add(code)
        finally:
            note_path.write_text(original, encoding="utf-8")
    run(repo, ["tools/generate.py"])
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True,
                          text=True, env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"}).stdout.strip()
    report = {
        "bench_version": 1,
        "world": str(repo),
        "world_head": head,
        "notes": sum(1 for _ in (repo / "knowledge/notes").rglob("*.md")),
        "reps": args.reps,
        "derived_bytes": derived_bytes(repo),
        "operations": {name: {**stats(vals), "exit_codes": sorted(exits[name])}
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
