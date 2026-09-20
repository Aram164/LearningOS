"""Phase-0 projection benchmark: instrument before optimizing.

Read-only with respect to the live tree. Generation is computed in memory;
the mutation corpus runs against a scratch copy under $TMPDIR that is
deleted afterwards. Neither canonical data nor live generated files are
written, and no production module is edited to gain the timings — the
per-node timers wrap the projector functions from this script only.

Usage:
    .venv/bin/python tests/benchmark_projection.py [--samples 3] [--out PATH]
    .venv/bin/python tests/benchmark_projection.py --skip-mutations

Writes a JSON report (default: /tmp/projection-benchmark-<stamp>.json, kept
out of the repository so benchmark runs never dirty the working tree) and
prints a human-readable summary with Phase-0 GO/NO-GO signals.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

STAMP = "BENCH"
MARKER = " [bench-probe]"

# Top-level builders called by generate_all (wrapped in outputs' namespace).
OUTPUT_NODES = [
    "build_backlinks", "build_manifest",
    "build_learning_requirements_json", "build_learning_requirements_md",
    "build_learner_interpretations_json", "build_learner_interpretations_md",
    "build_concept_index", "build_source_index", "build_library",
    "build_module_view", "build_coordination_view", "build_dependency_report",
    "build_concept_map", "build_domain_atlas", "build_health", "build_nebula",
    "build_reading_room", "build_study_plan_view", "build_concept_canvas",
    "build_collection_view",
]

# Inner projectors assembled by build_manifest (wrapped in manifest's namespace).
MANIFEST_NODES = [
    "build_counts", "build_indexes", "build_module_concept_edges",
    "build_progress", "build_review_items", "enforce", "load_revisions",
    "project_garden_entries", "_academic_deadlines", "adoption_counts",
    "source_fingerprint", "_git_state",
    "project_collections", "project_concepts", "project_coordination",
    "project_learning_paths", "project_module_source_maps", "project_modules",
    "project_notes", "project_programs", "project_project_aliases",
    "project_project_relationships", "project_projects", "project_sources",
    "project_stages", "project_study_maps", "project_thematic_groups",
    "project_topics", "project_unit_material_syntheses", "project_units",
    "project_workspaces", "unit_to_project_ids",
]


def _install_timers() -> dict:
    """Wrap projector functions in place; returns the shared timing table."""
    import learning_os.genout.manifest as manifest_mod
    import learning_os.genout.outputs as outputs_mod

    table: dict[str, dict] = {}

    def wrap(module, name: str) -> None:
        original = getattr(module, name, None)
        if not callable(original):
            return
        key = f"{module.__name__.rsplit('.', 1)[-1]}.{name}"
        record = table.setdefault(key, {"calls": 0, "ms": 0.0, "bytes": 0})

        def inner(*args, **kwargs):
            started = time.perf_counter()
            try:
                return original(*args, **kwargs)
            finally:
                elapsed = (time.perf_counter() - started) * 1000.0
                record["calls"] += 1
                record["ms"] += elapsed

        inner.__name__ = getattr(original, "__name__", name)
        setattr(module, name, inner)

    for _name in OUTPUT_NODES:
        wrap(outputs_mod, _name)
    for _name in MANIFEST_NODES:
        wrap(manifest_mod, _name)
    return table


def _sha_map(outputs: dict[str, str]) -> tuple[dict[str, str], dict[str, int]]:
    shas, sizes = {}, {}
    for path in sorted(outputs):
        raw = outputs[path].encode("utf-8")
        shas[path] = hashlib.sha256(raw).hexdigest()
        sizes[path] = len(raw)
    return shas, sizes


def cold_sample() -> dict:
    """One cold sample on the live repo: fresh process, in-memory only."""
    from learning_os.genout import generate_all
    from learning_os.loader import load_repo
    from learning_os.rules import validate

    started = time.perf_counter()
    repo = load_repo(ROOT)
    loaded = time.perf_counter()
    issues = validate(repo, online=False)
    validated = time.perf_counter()

    table = _install_timers()
    outputs = generate_all(repo, STAMP)
    generated = time.perf_counter()

    # Warm pass: same loaded repo, timers kept separate by snapshotting.
    cold_nodes = {key: dict(value) for key, value in table.items()}
    for value in table.values():
        value.update(calls=0, ms=0.0)
    warm_outputs = generate_all(repo, STAMP)
    warmed = time.perf_counter()
    warm_nodes = {key: dict(value) for key, value in table.items()}

    manifest_raw = outputs["manifest.json"]
    parse_times = []
    for _ in range(3):
        begin = time.perf_counter()
        json.loads(manifest_raw)
        parse_times.append((time.perf_counter() - begin) * 1000.0)

    shas, sizes = _sha_map(outputs)
    warm_shas, _ = _sha_map(warm_outputs)
    return {
        "seconds": {
            "load": loaded - started,
            "validate_loaded_repo": validated - loaded,
            "generate_cold": generated - validated,
            "generate_warm": warmed - generated,
            "total": warmed - started,
        },
        "issues": [str(issue) for issue in issues],
        "cold_nodes": cold_nodes,
        "warm_nodes": warm_nodes,
        "manifest_parse_ms": statistics.median(parse_times),
        "manifest_bytes": len(manifest_raw.encode("utf-8")),
        "output_sha256": shas,
        "output_bytes": sizes,
        "warm_identical": warm_shas == shas,
    }


# ---------------------------------------------------------------------------
# Mutation corpus (runs against a scratch copy, never the live tree).
# ---------------------------------------------------------------------------

def _is_prose_key(key: str) -> bool:
    return not (
        key in {"id", "schema_version", "contract"}
        or key.endswith(("_id", "_ids", "_uri", "_path", "_ref"))
    )


def _tweak_prose(data, prefer: tuple[str, ...]) -> bool:
    """Append MARKER to one prose scalar, preferring the named keys.

    Only strings containing a space are touched, so stable IDs, patterns
    and URIs (which the manifest contract validates) are never mutated.
    Breadth-first: preferred keys first, then any other prose scalar.
    """
    queue: list = [data]
    fallback = None
    while queue:
        node = queue.pop(0)
        if isinstance(node, dict):
            for key in sorted(node):
                value = node[key]
                if isinstance(value, str) and " " in value \
                        and MARKER not in value \
                        and _is_prose_key(key):
                    if key in prefer:
                        node[key] = value + MARKER
                        return True
                    if fallback is None:
                        fallback = (node, key)
                elif isinstance(value, (dict, list)):
                    queue.append(value)
        elif isinstance(node, list):
            queue.extend(item for item in node
                         if isinstance(item, (dict, list)))
    if fallback is not None:
        node, key = fallback
        node[key] = node[key] + MARKER
        return True
    return False


def _yaml_mutation(rel: str, description: str,
                   prefer: tuple[str, ...] = ()):
    import yaml

    def apply(scratch: Path):
        target = scratch / rel
        if not target.exists():
            return None
        original = target.read_bytes()
        data = yaml.safe_load(original.decode("utf-8"))
        if not _tweak_prose(data, prefer):
            return None
        target.write_text(
            yaml.safe_dump(data, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
        return original

    apply.rel = rel
    apply.description = description
    return apply


def _mutation_b4_observation(scratch: Path):
    """First learner observation appears in a workspace ledger."""
    from learning_os.learning_runtime import collect_requirements
    from learning_os.loader import load_repo

    repo = load_repo(scratch)
    if not repo.workspaces:
        return None
    requirements = collect_requirements(repo)
    if not requirements:
        return None
    workspace = sorted(repo.workspaces.values(), key=lambda item: item.id)[0]
    ledger = scratch / workspace.path.parent / "observations.jsonl"
    if ledger.exists():
        return None  # corpus models the first observation only
    record = {
        "requirement": sorted(requirements, key=lambda req: req["id"])[0]["id"],
        "activity": "benchmark probe attempt",
        "result": "correct",
        "timestamp": "2026-09-20T00:00:00+00:00",
        "id": "observation-benchmark-probe",
    }
    ledger.write_text(json.dumps(record) + "\n", encoding="utf-8")
    return ledger


_mutation_b4_observation.rel = "<first workspace>/observations.jsonl (created)"
_mutation_b4_observation.description = "B4 learner observation append"


def _mutation_b5_note(scratch: Path):
    notes = sorted((scratch / "knowledge/notes").rglob("*.md"))
    if not notes:
        return None
    target = notes[0]
    original = target.read_bytes()
    target.write_bytes(original + f"\n{MARKER.strip()}\n".encode())
    return original


_mutation_b5_note.rel = "knowledge/notes/<first>.md (appended)"
_mutation_b5_note.description = "B5 note revision"


MUTATIONS = [
    ("B1", _yaml_mutation(
        "curriculum/modules/module-hu-m2-statistik-analysis/source-map.yaml",
        "B1 route angle patch", prefer=("angle",))),
    ("B2", _yaml_mutation(
        "curriculum/modules/module-hu-m2-statistik-analysis/units/unit-m2-sad-l04/study-map.yaml",
        "B2/B3 stage-affecting study-map patch",
        prefer=("action", "title", "summary", "objective"))),
    ("B4", _mutation_b4_observation),
    ("B5", _mutation_b5_note),
    ("B6", _yaml_mutation(
        "sources/registry/machine-learning.yaml",
        "B6 source metadata update", prefer=("title",))),
    ("B7", _yaml_mutation(
        "projects/registry/project-bachelor-thesis.yaml",
        "B7 project update", prefer=("title", "objective"))),
    ("B8", _yaml_mutation(
        "curriculum/modules/module-hu-m2-statistik-analysis/units/unit-m2-sad-l02/study-map.yaml",
        "B8 unit-plan revision",
        prefer=("action", "title", "summary", "objective"))),
]


def mutation_worker() -> dict:
    from learning_os.genout import generate_all
    from learning_os.loader import load_repo

    def ignore(directory: str, names: list[str]) -> set[str]:
        return {
            name for name in names
            if name in {".git", "generated", "__pycache__", ".pytest_cache",
                        ".venv", ".DS_Store"}
        }

    scratch = Path(tempfile.mkdtemp(prefix="projection-bench-"))
    try:
        copy_started = time.perf_counter()
        for child in ROOT.iterdir():
            if child.name in {".git", "generated", "__pycache__",
                              ".pytest_cache", ".venv"}:
                continue
            target = scratch / child.name
            if child.is_dir():
                shutil.copytree(child, target, ignore=ignore)
            else:
                shutil.copy2(child, target)
        copy_seconds = time.perf_counter() - copy_started

        base_repo = load_repo(scratch)
        base_outputs = generate_all(base_repo, STAMP)
        base_shas, base_sizes = _sha_map(base_outputs)
        total_bytes = sum(base_sizes.values())

        results = []
        for code, mutation in MUTATIONS:
            try:
                saved = mutation(scratch)
            except Exception as exc:  # noqa: BLE001 — corpus must not abort
                results.append(
                    {"code": code, "status": f"error: {exc}"[:300]})
                continue
            if saved is None:
                results.append({"code": code, "status": "skipped (target absent)"})
                continue
            try:
                started = time.perf_counter()
                repo = load_repo(scratch)
                loaded = time.perf_counter()
                outputs = generate_all(repo, STAMP)
                generated = time.perf_counter()
            except Exception as exc:  # noqa: BLE001
                results.append(
                    {"code": code, "status": f"error: {exc}"[:300]})
            else:
                shas, sizes = _sha_map(outputs)
                changed = sorted(
                    path for path in shas
                    if shas.get(path) != base_shas.get(path))
                results.append({
                    "code": code,
                    "status": "ok",
                    "target": getattr(mutation, "rel", "?"),
                    "load_ms": (loaded - started) * 1000.0,
                    "generate_ms": (generated - loaded) * 1000.0,
                    "changed_artifacts": changed,
                    "changed_count": len(changed),
                    "changed_bytes": sum(sizes[path] for path in changed),
                    "total_bytes": total_bytes,
                })
            finally:
                # Restore byte-identical state for the next mutation.
                try:
                    if isinstance(saved, Path):
                        saved.unlink(missing_ok=True)
                    else:
                        rel = getattr(mutation, "rel", "")
                        if rel.startswith("knowledge/notes/"):
                            notes = sorted(
                                (scratch / "knowledge/notes").rglob("*.md"))
                            if notes:
                                notes[0].write_bytes(saved)
                        else:
                            (scratch / rel).write_bytes(saved)
                except OSError:
                    pass
        return {
            "scratch_copy_seconds": copy_seconds,
            "artifact_count": len(base_shas),
            "total_bytes": total_bytes,
            "mutations": results,
        }
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


# ---------------------------------------------------------------------------
# Parent driver.
# ---------------------------------------------------------------------------

def _median_nodes(samples: list[dict], key: str) -> dict[str, dict]:
    names: set[str] = set()
    for row in samples:
        names.update(row[key])
    medians = {}
    for name in sorted(names):
        calls = [row[key].get(name, {}).get("calls", 0) for row in samples]
        msec = [row[key].get(name, {}).get("ms", 0.0) for row in samples]
        medians[name] = {
            "calls": int(statistics.median(calls)),
            "ms": statistics.median(msec),
        }
    return medians


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples", type=int, default=3)
    parser.add_argument("--skip-mutations", action="store_true")
    parser.add_argument("--out", default=None)
    parser.add_argument("--sample", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--mutate", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.sample:
        print(json.dumps(cold_sample()))
        return
    if args.mutate:
        print(json.dumps(mutation_worker()))
        return
    if args.samples < 1:
        parser.error("--samples must be positive")

    samples = [
        json.loads(subprocess.check_output(
            [sys.executable, __file__, "--sample"], cwd=ROOT, text=True))
        for _ in range(args.samples)
    ]
    first = samples[0]
    if any(row["issues"] != first["issues"]
           or row["output_sha256"] != first["output_sha256"]
           for row in samples):
        raise SystemExit(
            "repository or output changed between samples; repeat the benchmark")
    if not all(row["warm_identical"] for row in samples):
        raise SystemExit("warm regeneration disagreed with cold; investigate")

    report: dict = {
        "samples": args.samples,
        "median_seconds": {
            phase: statistics.median(row["seconds"][phase] for row in samples)
            for phase in first["seconds"]
        },
        "median_cold_nodes": _median_nodes(samples, "cold_nodes"),
        "median_warm_nodes": _median_nodes(samples, "warm_nodes"),
        "manifest_parse_ms": statistics.median(
            row["manifest_parse_ms"] for row in samples),
        "manifest_bytes": first["manifest_bytes"],
        "artifact_count": len(first["output_sha256"]),
        "output_bytes": sum(first["output_bytes"].values()),
    }
    if not args.skip_mutations:
        report["mutations"] = json.loads(subprocess.check_output(
            [sys.executable, __file__, "--mutate"], cwd=ROOT, text=True))

    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    out = Path(args.out) if args.out else Path(f"/tmp/projection-benchmark-{stamp}.json")
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")

    _print_summary(report)
    print(f"\nJSON report: {out}")


def _print_summary(report: dict) -> None:
    med = report["median_seconds"]
    print("== Phase-0 projection benchmark ==")
    print(f"samples: {report['samples']}")
    print(f"load:      {med['load'] * 1000:8.1f} ms")
    print(f"validate:  {med['validate_loaded_repo'] * 1000:8.1f} ms")
    print(f"generate (cold): {med['generate_cold'] * 1000:8.1f} ms")
    print(f"generate (warm): {med['generate_warm'] * 1000:8.1f} ms")
    print(f"total:     {med['total'] * 1000:8.1f} ms")
    print(f"artifacts: {report['artifact_count']} "
          f"({report['output_bytes'] / 1e6:.1f} MB)")
    print(f"manifest:  {report['manifest_bytes'] / 1e6:.1f} MB, "
          f"json.loads {report['manifest_parse_ms']:.1f} ms")
    print("\nTop cold nodes (median ms):")
    nodes = sorted(report["median_cold_nodes"].items(),
                   key=lambda item: item[1]["ms"], reverse=True)
    for name, stats in nodes[:14]:
        print(f"  {stats['ms']:8.1f} ms  x{stats['calls']:>3}  {name}")
    cold = report["median_cold_nodes"]
    inner = sum(stats["ms"] for name, stats in cold.items()
                if name.startswith("manifest."))
    total_manifest = cold.get("outputs.build_manifest", {}).get("ms", 0.0)
    print(f"  {total_manifest - inner:8.1f} ms        "
          f"manifest.assembly+serialize (residual)")
    if "mutations" in report:
        print("\nMutation blast radius (full-regenerate baseline):")
        for row in report["mutations"]["mutations"]:
            if row["status"] != "ok":
                print(f"  {row['code']}: {row['status']}")
                continue
            frac = row["changed_bytes"] / row["total_bytes"] * 100
            print(f"  {row['code']}: {row['changed_count']:>2} artifacts, "
                  f"{row['changed_bytes'] / 1e3:8.1f} KB of "
                  f"{row['total_bytes'] / 1e3:.0f} KB ({frac:.1f}%), "
                  f"gen {row['generate_ms']:.0f} ms")


if __name__ == "__main__":
    main()
