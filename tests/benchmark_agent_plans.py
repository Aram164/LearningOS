"""Real public-process benchmarks. All writes use newly built disposable fixtures.

Run with --baseline-source pointing at the tested 3604c43 checkout.
Fixture setup and view preparation are excluded from samples. JSON retains
every measured sample and semantic check; bytes are not token counts.
"""
from __future__ import annotations

import argparse
import json
import platform
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
READS = [
    (["capabilities", "--compact", "--json"], ["contract_version"]),
    (["bootstrap", "--brief"], ["counts.modules", "counts.units", "counts.stages"]),
    (["inspect", "note-demo"], ["id", "type"]),
    (["intelligence-scan", "--brief", "--json"], ["total_goals"]),
    (["capabilities", "capture.create", "--json"], ["payload_schema.type"]),
]


def invoke(source, data, argv):
    proc = subprocess.run([PYTHON, str(source / "tools/los.py"), "--root", str(data), *argv],
                          capture_output=True, timeout=120)
    assert proc.returncode == 0, (argv, proc.stdout[-1000:], proc.stderr[-1000:])
    return proc


def selected(payload, fields):
    out = {}
    for field in fields:
        value = payload
        for part in field.split("."):
            assert isinstance(value, dict) and part in value, (field, payload)
            value = value[part]
        out[field] = value
    return out


def fixture(source, parent, name, *, warm=True):
    root = parent / name
    code = ("import sys; from pathlib import Path; "
            "sys.path[:0]=[str(Path(sys.argv[1])/'tools'),str(Path(sys.argv[1])/'tests')]; "
            "from conftest import build_mini_repo; from repo_builders import add_curriculum; "
            "root=build_mini_repo(Path(sys.argv[2])); add_curriculum(root)")
    subprocess.run([PYTHON, "-c", code, str(source), str(root)], check=True,
                   capture_output=True, timeout=120)
    data = root / "LearningOS/repository"
    if warm:
        invoke(source, data, ["generate"])
    return data


def read_plan(repeats=None, workers=1, budget=65536):
    entries = READS if repeats is None else [READS[2]] * repeats
    return {"read_workers": workers, "report_max_bytes": budget, "steps": [
        {"id": "read-" + str(i), "argv": argv, "summary": {"fields": fields}}
        for i, (argv, fields) in enumerate(entries)]}


def runner(source, data, plan, parent):
    path = parent / "plan.json"
    path.write_text(json.dumps(plan))
    begin = time.perf_counter()
    proc = subprocess.run([PYTHON, str(source / "tools/agent_run.py"), str(path),
                           "--root", str(data)], capture_output=True, timeout=120)
    elapsed = (time.perf_counter() - begin) * 1000
    assert proc.returncode == 0, (proc.stdout[-2000:], proc.stderr[-1000:])
    report = json.loads(proc.stdout)
    assert report["totals"]["ok"] == len(plan["steps"]), report
    values = []
    complete = json.loads(Path(report["full_report"]).read_text()) if any("output" not in r for r in report["steps"]) else report
    for spec, row in zip(plan["steps"], complete["steps"], strict=True):
        fields = spec.get("summary", {}).get("fields", [])
        if fields:
            assert not row["output"].get("_missing_fields"), row
            values.append(selected(row["output"], fields))
    return {"ms": elapsed, "wire_bytes": len(proc.stdout) + len(proc.stderr),
            "raw_bytes": report["totals"]["raw_bytes"],
            "processes": report["totals"].get("process_count", 1),
            "memo_hits": report["totals"].get("memo_hits"),
            "model_loads": report["totals"].get("model_loads"),
            "resources": report["totals"].get("resources"), "semantic_values": values,
            "receipt_count": len(list((data / "operations/transactions").glob("transaction-*.yaml")))}


def separate(source, data, commands):
    begin = time.perf_counter()
    wire = raw = 0
    values = []
    for argv, fields in commands:
        proc = invoke(source, data, argv)
        raw += len(proc.stdout)
        wire += len(proc.stdout) + len(proc.stderr)
        if fields:
            values.append(selected(json.loads(proc.stdout), fields))
    return {"ms": (time.perf_counter() - begin) * 1000, "wire_bytes": wire,
            "raw_bytes": raw, "processes": len(commands), "semantic_values": values}


def direct_writes(source, data, number):
    begin = time.perf_counter()
    wire = raw = 0
    for i in range(number):
        proc = subprocess.run([PYTHON, str(source / "tools/seal_envelope.py"), "--root", str(data),
            "--capability", "capture.create", "--payload", json.dumps({"text": "benchmark-" + str(i)}),
            "--key", "intent-" + str(i), "--session-id", "benchmark-session", "--submit"],
            capture_output=True, timeout=120)
        assert proc.returncode == 0, (proc.stdout, proc.stderr)
        wire += len(proc.stdout) + len(proc.stderr)
        raw += len(proc.stdout)
    proc = invoke(source, data, READS[2][0])
    return {"ms": (time.perf_counter() - begin) * 1000,
            "wire_bytes": wire + len(proc.stdout) + len(proc.stderr),
            "raw_bytes": raw + len(proc.stdout), "processes": number + 1,
            "semantic_values": [selected(json.loads(proc.stdout), READS[2][1])],
            "receipt_count": len(list((data / "operations/transactions").glob("transaction-*.yaml")))}


def write_plan(number):
    steps = [{"id": "write-" + str(i), "kind": "log", "text": "benchmark-" + str(i),
              "key": "intent-" + str(i),
              "depends_on": ["write-" + str(i - 1)] if i else []} for i in range(number)]
    steps.append({"id": "after", "argv": READS[2][0], "summary": {"fields": READS[2][1]},
                  "depends_on": [s["id"] for s in steps]})
    return {"session_id": "benchmark-session", "steps": steps}


def summarize(samples):
    arms = samples[0].keys()
    out = {}
    for arm in arms:
        times = [sample[arm]["ms"] for sample in samples]
        out[arm] = {"median_ms": statistics.median(times), "min_ms": min(times),
                    "max_ms": max(times), "stdev_ms": statistics.stdev(times),
                    "p95_nearest_rank_ms": sorted(times)[min(len(times) - 1, int(0.95 * len(times)))],
                    "median_wire_bytes": statistics.median(s[arm]["wire_bytes"] for s in samples),
                    "last": samples[-1][arm]}
    return out


def delay_sample(data, delay):
    import threading

    from learning_os.app.projection_readiness import dependency_ready

    direct_writes(ROOT, data, 1)
    receipts = sorted((data / "operations/transactions").glob("transaction-*.yaml"))
    import yaml
    receipt = yaml.safe_load(receipts[-1].read_text())
    record = {"receipt_path": str(receipts[-1].relative_to(data)), "snapshot_after": receipt["snapshot_after"]}
    identity = data / "generated/manifest.identity.json"
    raw = identity.read_bytes()
    identity.unlink()
    timer = threading.Timer(delay, identity.write_bytes, args=(raw,)) if delay is not None else None
    if timer is not None:
        timer.start()
    begin = time.perf_counter()
    polls = 0
    ready = False
    until = begin + (delay + 2 if delay is not None else 0.05)
    try:
        while time.perf_counter() < until:
            polls += 1
            ready, reason = dependency_ready(data, [record], [record])
            if ready:
                break
            time.sleep(0.005)
        wait_ms = (time.perf_counter() - begin) * 1000
        if ready:
            assert selected(json.loads(invoke(ROOT, data, READS[2][0]).stdout), READS[2][1])["id"] == "note-demo"
        assert ready == (delay is not None)
        return {"requested_delay_s": delay, "ready_wait_ms": wait_ms, "polls": polls,
                "ready": ready, "dependent_read_executions": int(ready)}
    finally:
        if timer is not None:
            timer.join()


def preflight_sample(data):
    import shutil
    from unittest.mock import patch

    from learning_os.app import validation_service

    # Only this cache-owner fixture stages its declared producer bytes, as
    # tests/test_validation_cache.py does. Other workloads remain data-only.
    from learning_os.store.validation_cache import VALIDATION_PRODUCER_FILES
    for relative in VALIDATION_PRODUCER_FILES:
        target = data / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / relative).read_bytes())
    shutil.rmtree(data / "generated/derived-state", ignore_errors=True)
    real = validation_service.validate
    samples = {}
    with patch.object(validation_service, "validate", wraps=real) as validator:
        for label in ["fresh", "unchanged", "authored-change"]:
            if label == "authored-change":
                note = data / "knowledge/notes/mathematics/note-demo.md"
                note.write_text(note.read_text() + "\nChanged fixture content.\n")
            before = validator.call_count
            begin = time.perf_counter()
            report = validation_service.diagnostic_report(data)
            elapsed = (time.perf_counter() - begin) * 1000
            assert report["trustworthy"]
            samples[label] = {"ms": elapsed, "validator_invocations": validator.call_count - before,
                              "errors": report["errors"]}
        assert samples["fresh"]["validator_invocations"] >= 1
        assert samples["unchanged"]["validator_invocations"] == 0
        assert samples["authored-change"]["validator_invocations"] >= 1
    return samples


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-source", type=Path, required=True)
    parser.add_argument("--samples", type=int, default=10)
    parser.add_argument("--warmup", type=int, default=2)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.samples < 2 or args.warmup < 0:
        parser.error("at least two samples and nonnegative warmup are required")
    old = args.baseline_source.resolve()
    source_heads = {name: subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=source).decode().strip()
                    for name, source in [("candidate", ROOT), ("original", old)]}
    report = {"environment": {"python": sys.version, "platform": platform.platform()},
              "source_heads": source_heads, "source_diff_sha256": {name: __import__("hashlib").sha256(subprocess.check_output(["git", "diff", "HEAD", "--", "tools", "system", "tests"], cwd=source)).hexdigest() for name, source in [("candidate", ROOT), ("original", old)]}, "samples": args.samples, "warmup_excluded": args.warmup,
              "limits": ["synthetic fixtures; setup/views excluded", "semantic selections verified",
                         "memory is per-process peak; worker sum is an upper bound",
                         "original source and candidate use their own declared fixture contracts"],
              "workloads": {}}
    with tempfile.TemporaryDirectory(prefix="los-benchmark-worlds-") as temp:
        parent = Path(temp)
        definitions = [
            ("W1-distinct-warm", None, 1, True),
            ("W2-repeated", 20, 1, True),
            ("W3-distinct-cold", None, 1, False),
            ("W9-workers-2", None, 2, True),
            ("W9-workers-4", None, 4, True),
        ]
        for label, repeats, workers, warm in definitions:
            samples = []
            for i in range(args.samples + args.warmup):
                commands = READS if repeats is None else [READS[2]] * repeats
                arms = ["separate", "original", "candidate"]
                shift = i % len(arms)
                arms = arms[shift:] + arms[:shift]
                sample = {}
                for arm in arms:
                    source = old if arm == "original" else ROOT
                    data = fixture(source, parent, f"{label}-{i}-{arm}", warm=warm)
                    sample[arm] = (separate(source, data, commands) if arm == "separate"
                                   else runner(source, data, read_plan(repeats, workers if arm == "candidate" else 1), parent))
                assert sample["separate"]["semantic_values"] == sample["candidate"]["semantic_values"] == sample["original"]["semantic_values"], sample
                if i >= args.warmup:
                    samples.append(sample)
            report["workloads"][label] = {"raw_samples": samples, "summary": summarize(samples)}
            print(label + " complete", file=sys.stderr, flush=True)
        for number in [1, 2]:
            label = "W4-write-read" if number == 1 else "W5-two-writes-replay"
            samples = []
            for i in range(args.samples + args.warmup):
                sample = {}
                arms = ["separate", "original", "candidate"]
                shift = i % len(arms)
                for arm in arms[shift:] + arms[:shift]:
                    source = old if arm == "original" else ROOT
                    data = fixture(source, parent, f"{label}-{i}-{arm}")
                    sample[arm] = (direct_writes(source, data, number) if arm == "separate"
                                   else runner(source, data, write_plan(number), parent))
                    assert sample[arm]["receipt_count"] == number
                    if number == 2:
                        replay = direct_writes(source, data, number) if arm == "separate" else runner(source, data, write_plan(number), parent)
                        assert replay["receipt_count"] == number
                        sample[arm]["replay_ms"] = replay["ms"]
                assert sample["separate"]["semantic_values"] == sample["candidate"]["semantic_values"] == sample["original"]["semantic_values"]
                if i >= args.warmup:
                    samples.append(sample)
            report["workloads"][label] = {"raw_samples": samples, "summary": summarize(samples)}
            print(label + " complete", file=sys.stderr, flush=True)

        delay_rows = {}
        for delay in [0, 0.05, 0.25, 1.0, None]:
            raw_rows = []
            for i in range(args.samples + args.warmup):
                data = fixture(ROOT, parent, "W6-" + str(delay) + "-" + str(i))
                row = delay_sample(data, delay)
                if i >= args.warmup:
                    raw_rows.append(row)
            delay_rows[str(delay)] = raw_rows
        report["workloads"]["W6-publication"] = delay_rows
        preflight_rows = []
        for i in range(args.samples + args.warmup):
            data = fixture(ROOT, parent, "W7-" + str(i))
            row = preflight_sample(data)
            if i >= args.warmup:
                preflight_rows.append(row)
        report["workloads"]["W7-preflight"] = preflight_rows
        print("W6 and W7 complete", file=sys.stderr, flush=True)
        for count, budget in [(50, 32768), (256, 65536)]:
            data = fixture(ROOT, parent, "W8-" + str(count))
            result = runner(ROOT, data, read_plan(count, budget=budget), parent)
            assert result["wire_bytes"] <= budget
            report["workloads"]["W8-report-" + str(count)] = result
    report["behavioral_workloads"] = {
        "W6-delayed-partial-never-ready": "tests/test_agent_run.py::test_pending_write_waits_and_stale_read_never_executes; test_takeover_global_deadline_bounds_readiness",
        "W7-preflight": "tests/test_validation_cache.py plus test_takeover_typed_preflight_keeps_error_severity",
        "W10-shared-material-plan": "existing material-scope/prospective-plan owning regressions; no new latency claim"}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({label: value.get("summary", value) if isinstance(value, dict) else value for label, value in report["workloads"].items()}, indent=2))


if __name__ == "__main__":
    main()
