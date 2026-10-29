#!/usr/bin/env python3
"""Measure remaining agility costs in disposable synthetic repositories only."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import statistics
import subprocess
import sys
import tempfile
import time
import tracemalloc
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "tools"), str(ROOT / "tests"), str(Path(__file__).parent)]

from baseline import owned_bytes, prepare  # noqa: E402
from repo_builders import _compact_revision, write_yaml  # noqa: E402
from test_plan_inventory import _block, _seed_materials, _write_audit  # noqa: E402
from test_validation_cache import _stage_validation_producers  # noqa: E402

from learning_os.store.fingerprint import canonical_fingerprint  # noqa: E402
from learning_os.store.materials.resolution import sha256_file  # noqa: E402

INSTRUMENT = """
import atexit, cProfile, json, os
from pathlib import Path
import learning_os.app._plan_gate as gate
import learning_os.app.handlers.plan as plan
counts = {"inventory_enumerations": 0, "material_opens": {}}
material_root = Path(os.environ["LOS_EFF_MATERIALS"]).resolve()
original_open = Path.open
def counted_open(self, *args, **kwargs):
    mode = kwargs.get("mode", args[0] if args else "r")
    if "r" in mode:
        target = self.resolve()
        if target.is_relative_to(material_root) and target.is_file():
            key = str(target.relative_to(material_root))
            row = counts["material_opens"].setdefault(key, {"opens": 0, "file_bytes": target.stat().st_size})
            row["opens"] += 1
    return original_open(self, *args, **kwargs)
Path.open = counted_open
original_inventory = gate.enumerate_inventory_roots
def counted_inventory(*args, **kwargs):
    counts["inventory_enumerations"] += 1
    return original_inventory(*args, **kwargs)
gate.enumerate_inventory_roots = counted_inventory
plan._enumerate_inventory_roots = counted_inventory
profile = cProfile.Profile()
profile.enable()
def finish():
    profile.disable()
    counts["validation_runs"] = sum(e.callcount for e in profile.getstats() if not isinstance(e.code, str) and e.code.co_name == "run" and e.code.co_filename.endswith("/derive/validation/core.py"))
    counts["repository_loads"] = sum(e.callcount for e in profile.getstats() if not isinstance(e.code, str) and e.code.co_name == "load_repo" and "/store/loading/" in e.code.co_filename)
    with open(os.environ["LOS_EFF_LOG"], "w") as stream:
        json.dump(counts, stream)
atexit.register(finish)
"""


def command(
    base: Path, root: Path, name: str, argv: list[str], *, tool: str = "los.py"
) -> tuple[dict, str]:
    control = base.parent / "controls" / base.name
    control.mkdir(parents=True, exist_ok=True)
    instrumentation = control / "instrumentation"
    instrumentation.mkdir(exist_ok=True)
    (instrumentation / "sitecustomize.py").write_text(INSTRUMENT)
    observations = control / "clock.json"
    observations.write_text(
        json.dumps(
            {
                "now": "2026-10-01T09:00:00+02:00",
                "git": {"head": None, "head_time": None, "dates": {}, "timestamps": {}},
            }
        )
    )
    log = control / f"{name}.json"
    env = {
        **os.environ,
        "PYTHONPATH": os.pathsep.join([str(instrumentation), str(ROOT / "tools")]),
        "LOS_EFF_LOG": str(log),
        "LOS_EFF_MATERIALS": str(root.parent / "materials"),
        "LOS_OBSERVATIONS": str(observations),
    }
    started = time.perf_counter()
    proc = subprocess.run(
        [sys.executable, str(ROOT / "tools" / tool), "--root", str(root), *argv],
        env=env,
        text=True,
        capture_output=True,
        timeout=120,
    )
    elapsed = time.perf_counter() - started
    if proc.returncode:
        raise RuntimeError(f"{name}: {proc.stdout}\n{proc.stderr}")
    metrics = json.loads(log.read_text())
    return {
        "name": name,
        "instrumented_seconds": elapsed,
        "stdout_bytes": len(proc.stdout.encode()),
        "stdout_sha256": hashlib.sha256(proc.stdout.encode()).hexdigest(),
        **metrics,
    }, proc.stdout


def sample(base: Path, mib: int) -> dict:
    root, _ = prepare(base, stages=10)
    _stage_validation_producers(root)
    initial = canonical_fingerprint(root)
    rows = []
    cold, cold_text = command(base, root, "status-cold", ["status", "--json"])
    warm, warm_text = command(base, root, "status-warm", ["status", "--json"])
    assert cold_text == warm_text
    rows.extend([cold, warm])
    for name, argv, tool in [
        ("status-no-validation", ["status", "--no-validate", "--json"], "los.py"),
        ("validate-first", ["--compact"], "validate.py"),
        ("validate-repeat", ["--compact"], "validate.py"),
        ("context-full", ["plan-edit-context", "unit-demo-l01"], "los.py"),
        ("context-brief", ["plan-edit-context", "unit-demo-l01", "--brief"], "los.py"),
        (
            "context-stage",
            ["plan-edit-context", "unit-demo-l01", "--stage-id", "stage-demo"],
            "los.py",
        ),
    ]:
        row, _ = command(base, root, name, argv, tool=tool)
        rows.append(row)
    assert canonical_fingerprint(root) == initial
    digests = _seed_materials(root)
    large = root.parent / "materials/inventory-demo/large.bin"
    digest = hashlib.sha256()
    chunk = b"agility synthetic material\n" * 4096
    remaining = mib * 1024 * 1024
    with large.open("wb") as stream:
        while remaining:
            block = chunk[:remaining]
            stream.write(block)
            digest.update(block)
            remaining -= len(block)
    digests["inventory-demo/large.bin"] = digest.hexdigest()
    checksum_rows = []
    for _ in range(3):
        tracemalloc.start()
        started = time.perf_counter()
        actual = sha256_file(large)
        elapsed = time.perf_counter() - started
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        assert actual == "sha256:" + digest.hexdigest()
        checksum_rows.append({"seconds": elapsed, "peak_python_bytes": peak})
    draft = base / "revision.yaml"
    write_yaml(
        draft,
        _compact_revision(
            root,
            route_changes={
                "update": [
                    {
                        "route_id": "route-demo-book",
                        "fields": {"angle": "A measured fixture angle."},
                    }
                ]
            },
        ),
    )
    _write_audit(root, _block(digests))
    before = owned_bytes(root)
    guarded = canonical_fingerprint(root)
    check, text = command(
        base,
        root,
        "inventory-preflight",
        ["unit-plan-revise", "unit-demo-l01", "--file", str(draft), "--check"],
    )
    assert canonical_fingerprint(root) == guarded
    report = json.loads(text)
    review = base / "review.json"
    review.write_text(text)
    apply, _ = command(
        base,
        root,
        "inventory-apply",
        [
            "unit-plan-revise",
            "unit-demo-l01",
            "--file",
            str(draft),
            "--review-report",
            str(review),
            "--apply-reviewed-sha256",
            report["reviewed_file_sha256"],
        ],
    )
    rows.extend([check, apply])
    after = owned_bytes(root)
    changed = sorted(p for p in before.keys() | after.keys() if before.get(p) != after.get(p))
    assert changed == ["curriculum/modules/module-demo/source-map.yaml"], changed
    assert len(list((root / "operations/transactions").glob("transaction-*.yaml"))) == 1
    return {
        "commands": rows,
        "checksum": checksum_rows,
        "material_bytes": large.stat().st_size,
        "draft_bytes": draft.stat().st_size,
        "preflight_writes": 0,
        "receipt_count": 1,
        "canonical_preservation": "passed",
        "status_cold_warm_identical": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--samples", type=int, default=3)
    parser.add_argument("--material-mib", type=int, default=16)
    args = parser.parse_args()
    if args.samples < 1 or args.material_mib < 1:
        parser.error("samples and material-mib must be positive")
    with tempfile.TemporaryDirectory(prefix="los-efficiency-") as scratch:
        samples = []
        for index in range(args.samples):
            base = Path(scratch) / str(index)
            base.mkdir()
            samples.append(sample(base, args.material_mib))
    result = {
        "scope": "disposable synthetic fixtures; instrumented fresh processes; OS disk caches not flushed; no model calls",
        "core_head": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "source_sha256": {
            p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
            for p in (
                "workbench/agility-experiment/efficiency.py",
                "tools/learning_os/store/materials/resolution.py",
                "tools/learning_os/app/_plan_gate.py",
                "tools/learning_os/app/handlers/plan.py",
                "tools/learning_os/app/handlers/materials.py",
                "tools/learning_os/derive/material_synthesis.py",
                "tools/learning_os/store/material_analysis.py",
                "tools/learning_os/store/validation_cache.py",
            )
        },
        "samples": samples,
        "median_checksum_seconds": statistics.median(
            r["seconds"] for s in samples for r in s["checksum"]
        ),
        "median_peak_python_bytes": statistics.median(
            r["peak_python_bytes"] for s in samples for r in s["checksum"]
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            {
                k: result[k]
                for k in ("core_head", "median_checksum_seconds", "median_peak_python_bytes")
            }
        )
    )


if __name__ == "__main__":
    main()
