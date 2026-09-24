#!/usr/bin/env python3
"""Check a run directory's records against the public schemas.

    python tests/eval/tools/check_run.py tests/eval/runs/<run-id>

Validates run.json, results/*.json, answers.jsonl, connections.jsonl and
failures.jsonl against public/schemas/, and checks that scenario, question,
probe and failure ids exist. It never reads the oracle and says nothing about
whether an answer is right.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator, FormatChecker

EVAL = Path(__file__).resolve().parents[1]
SCHEMAS = EVAL / "public" / "schemas"


def validator(name: str) -> Draft202012Validator:
    schema = json.loads((SCHEMAS / name).read_text(encoding="utf-8"))
    return Draft202012Validator(schema, format_checker=FormatChecker())


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("run", type=Path)
    args = parser.parse_args(argv)
    run = args.run
    problems: list[str] = []
    scenarios = {s["id"] for s in yaml.safe_load(
        (EVAL / "public/scenarios.yaml").read_text())["scenarios"]}
    questions = {q["id"] for q in yaml.safe_load(
        (EVAL / "public/questions.yaml").read_text())["questions"]}
    probes_doc = yaml.safe_load((EVAL / "public/connection-probes.yaml").read_text())
    probes = {p["id"] for p in probes_doc["canon"]} | set(probes_doc["arrivals"])

    def validate(v: Draft202012Validator, data, where: str) -> None:
        for err in v.iter_errors(data):
            loc = "/".join(str(p) for p in err.absolute_path) or "<root>"
            problems.append(f"{where}: {loc}: {err.message}")

    run_json = run / "run.json"
    if run_json.exists():
        validate(validator("run.schema.json"), json.loads(run_json.read_text()), "run.json")
    else:
        problems.append("run.json missing")

    failure_ids = set()
    failures = run / "failures.jsonl"
    if failures.exists():
        v = validator("failure.schema.json")
        for n, line in enumerate(failures.read_text().splitlines(), start=1):
            if line.strip():
                row = json.loads(line)
                validate(v, row, f"failures.jsonl:{n}")
                failure_ids.add(row.get("id"))

    v = validator("scenario-result.schema.json")
    seen = 0
    for path in sorted((run / "results").glob("*.json")):
        seen += 1
        data = json.loads(path.read_text())
        validate(v, data, f"results/{path.name}")
        if data.get("scenario") not in scenarios:
            problems.append(f"results/{path.name}: unknown scenario {data.get('scenario')}")
        for fid in data.get("failures") or []:
            if fid not in failure_ids:
                problems.append(f"results/{path.name}: failure {fid} not in failures.jsonl")

    for fname, schema, key, known in (("answers.jsonl", "answer-result.schema.json", "question",
                                       questions),
                                      ("connections.jsonl", "connection-result.schema.json",
                                       "probe", probes)):
        path = run / fname
        if not path.exists():
            continue
        v = validator(schema)
        ids = []
        for n, line in enumerate(path.read_text().splitlines(), start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            validate(v, row, f"{fname}:{n}")
            ids.append(row.get(key))
            if row.get(key) not in known:
                problems.append(f"{fname}:{n}: unknown {key} {row.get(key)}")
        dup = sorted({i for i in ids if ids.count(i) > 1})
        if dup:
            problems.append(f"{fname}: duplicate {key} ids {dup} (keep one record per id)")

    for line in problems:
        print(line)
    print(f"check_run: {seen} scenario results, {len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
