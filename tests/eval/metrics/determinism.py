#!/usr/bin/env python3
"""Derived-state determinism and rebuild checks for evaluation worlds.

    python tests/eval/metrics/determinism.py WORLD_REPO [--out report.json]
    python tests/eval/metrics/determinism.py --compare WORLD_A WORLD_B [--out report.json]

Single world: copy the world repository to a temporary directory (the world
itself is never touched), build the views, record every derived file, delete
all derived state (generated/ and the diagnostic store), build again, and
compare file by file.

Two worlds: compare their HEAD commits and canonical trees, then build views
in temporary copies of both and compare derived files.

Comparison is reported three ways: raw bytes; after normalizing timestamps
(ISO-8601 date-times and "YYYY-MM-DD HH:MM" stamps become <TS>); and, for two
worlds, after also replacing each world's absolute path with <ROOT>. A file
that differs only in raw bytes is timestamp-only; one that differs after
normalization is a determinism finding.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

TS = re.compile(rb"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?(?:Z|[+-]\d{2}:?\d{2})?")


def _hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def derived(repo: Path, root_token: bytes | None = None) -> dict[str, dict[str, str]]:
    out = {}
    base = repo / "generated"
    for path in sorted(p for p in base.rglob("*") if p.is_file()):
        data = path.read_bytes()
        norm = TS.sub(b"<TS>", data)
        rooted = norm.replace(root_token, b"<ROOT>") if root_token else norm
        out[path.relative_to(repo).as_posix()] = {
            "raw": _hash(data), "normalized": _hash(norm), "rooted": _hash(rooted)}
    return out


def build(repo: Path) -> dict:
    proc = subprocess.run([sys.executable, "tools/generate.py"], cwd=repo, capture_output=True,
                          text=True, timeout=3600)
    return {"exit": proc.returncode, "tail": (proc.stdout + proc.stderr).strip().splitlines()[-3:]}


def wipe_derived(repo: Path) -> None:
    for rel in ("generated", "operations/diagnostics"):
        base = repo / rel
        if not base.is_dir():
            continue
        for child in base.iterdir():
            if child.name == ".gitkeep":
                continue
            shutil.rmtree(child) if child.is_dir() else child.unlink()


def compare(a: dict, b: dict, key: str) -> dict:
    only_a = sorted(set(a) - set(b))
    only_b = sorted(set(b) - set(a))
    differ = sorted(k for k in set(a) & set(b) if a[k][key] != b[k][key])
    return {"only_first": only_a, "only_second": only_b, "differ": differ,
            "identical": not (only_a or only_b or differ)}


def copy_world(repo: Path, into: Path) -> Path:
    target = into / "LearningOS" / "repository"
    shutil.copytree(repo, target, symlinks=True)
    materials = repo.parent / "materials"
    if materials.is_dir():
        shutil.copytree(materials, into / "LearningOS" / "materials", symlinks=True)
    return target


def single(repo: Path) -> dict:
    with tempfile.TemporaryDirectory(prefix="los-determinism-") as tmp:
        work = copy_world(repo, Path(tmp))
        first_build = build(work)
        first = derived(work)
        wipe_derived(work)
        second_build = build(work)
        second = derived(work)
        return {
            "mode": "rebuild-after-delete",
            "world": str(repo),
            "builds": [first_build, second_build],
            "files": len(first),
            "raw": compare(first, second, "raw"),
            "timestamp_normalized": compare(first, second, "normalized"),
        }


def pair(repo_a: Path, repo_b: Path) -> dict:
    heads = [subprocess.run(["git", "rev-parse", "HEAD"], cwd=r, capture_output=True,
                            text=True).stdout.strip() for r in (repo_a, repo_b)]
    trees = [subprocess.run(["git", "rev-parse", "HEAD^{tree}"], cwd=r, capture_output=True,
                            text=True).stdout.strip() for r in (repo_a, repo_b)]
    with tempfile.TemporaryDirectory(prefix="los-det-a-") as ta, \
            tempfile.TemporaryDirectory(prefix="los-det-b-") as tb:
        wa, wb = copy_world(repo_a, Path(ta)), copy_world(repo_b, Path(tb))
        builds = [build(wa), build(wb)]
        da = derived(wa, str(wa).encode())
        db = derived(wb, str(wb).encode())
        return {
            "mode": "two-builds",
            "worlds": [str(repo_a), str(repo_b)],
            "heads": heads, "heads_equal": heads[0] == heads[1],
            "trees_equal": trees[0] == trees[1],
            "builds": builds,
            "raw": compare(da, db, "raw"),
            "timestamp_normalized": compare(da, db, "normalized"),
            "timestamp_and_root_normalized": compare(da, db, "rooted"),
        }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("world", nargs="?", type=Path)
    parser.add_argument("--compare", nargs=2, type=Path, metavar=("WORLD_A", "WORLD_B"))
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    if args.compare:
        report = pair(args.compare[0].resolve(), args.compare[1].resolve())
        ok = report["heads_equal"] and report["timestamp_and_root_normalized"]["identical"]
    elif args.world:
        report = single(args.world.resolve())
        ok = report["timestamp_normalized"]["identical"]
    else:
        parser.error("give WORLD_REPO or --compare WORLD_A WORLD_B")
    text = json.dumps(report, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    sys.stdout.write(text)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
