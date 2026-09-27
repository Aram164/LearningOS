#!/usr/bin/env python3
"""Validate campaign records for shape and completeness without the oracle."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator, FormatChecker

EVAL = Path(__file__).resolve().parents[1]
SCHEMAS = EVAL / "public" / "schemas"


def _read(path: Path, problems: list[str]) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        problems.append(f"{path}: missing or invalid JSON: {exc}")
        return {}
    if not isinstance(data, dict):
        problems.append(f"{path}: expected an object")
        return {}
    return data


def _schema(name: str, data: dict, where: str, problems: list[str]) -> None:
    schema = json.loads((SCHEMAS / name).read_text(encoding="utf-8"))
    for err in Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(data):
        loc = "/".join(str(p) for p in err.absolute_path) or "<root>"
        problems.append(f"{where}: {loc}: {err.message}")


def _artifact(run: Path, rel: str, problems: list[str]) -> None:
    try:
        path = (run / rel).resolve(strict=True)
        path.relative_to(run.resolve())
    except (OSError, ValueError):
        problems.append(f"missing or escaping run artifact: {rel}")
        return
    if not path.is_file():
        problems.append(f"not a run artifact file: {rel}")


def check_run(run: Path) -> list[str]:
    problems: list[str] = []
    scenarios = yaml.safe_load((EVAL / "public/scenarios.yaml").read_text())[
        "scenarios"
    ]
    known = {s["id"]: s for s in scenarios}
    data = _read(run / "run.json", problems)
    if data:
        _schema("run.schema.json", data, "run.json", problems)
        plan = data.get("plan")
        expected = {s["id"] for s in scenarios if plan in s["plans"]}
        declared = data.get("scenarios") or []
        if not isinstance(declared, list) or any(not isinstance(s, str) for s in declared):
            problems.append("run.json: scenarios must be a list of strings")
            declared = []
        if plan not in {"C", "V", "O"} and set(declared) != expected:
            problems.append(f"run.json: plan {plan} requires {sorted(expected)}, got {declared}")
        if plan in {"C", "V", "O"} and not declared:
            problems.append("run.json: an ad-hoc/verification plan must declare scenarios")
        if len(declared) != len(set(declared)):
            problems.append("run.json: duplicate scenario ids")
        unknown = sorted(set(declared) - set(known))
        if unknown:
            problems.append(f"run.json: unknown scenarios {unknown}")
        world = data.get("world_build") or {}
        if not isinstance(world, dict):
            world = {}
        if world:
            for key in ("world_head", "product_revision"):
                if world.get(key) != data.get(key):
                    problems.append(f"run.json: {key} differs from world_build")
    else:
        declared = []

    if not (run / "SESSION_REPORT.md").is_file():
        problems.append("missing SESSION_REPORT.md")
    failure_ids: dict[str, str] = {}
    failures = run / "failures.jsonl"
    if failures.exists():
        for n, line in enumerate(failures.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except ValueError as exc:
                problems.append(f"failures.jsonl:{n}: {exc}")
                continue
            if not isinstance(row, dict):
                problems.append(f"failures.jsonl:{n}: expected an object")
                continue
            _schema("failure.schema.json", row, f"failures.jsonl:{n}", problems)
            fid = row.get("id")
            if not isinstance(fid, str):
                problems.append(f"failures.jsonl:{n}: invalid failure id")
                continue
            if fid in failure_ids:
                problems.append(f"failures.jsonl:{n}: duplicate id {fid}")
            failure_ids[fid] = row.get("scenario")
            if row.get("scenario") not in declared:
                problems.append(f"failures.jsonl:{n}: scenario not declared")

    found: set[str] = set()
    for path in sorted((run / "results").glob("*.json")):
        row = _read(path, problems)
        _schema("scenario-result.schema.json", row, str(path), problems)
        sid = row.get("scenario")
        if sid != path.stem or sid not in known:
            problems.append(f"{path}: scenario id does not match a public scenario")
        if row.get("run_id") != run.name:
            problems.append(f"{path}: run_id differs from directory name")
        if isinstance(sid, str):
            found.add(sid)
        for fid in row.get("failures") or []:
            if fid not in failure_ids:
                problems.append(f"{path}: unknown failure {fid}")
            elif failure_ids[fid] != sid:
                problems.append(f"{path}: failure {fid} belongs to {failure_ids[fid]}")
        for state in (row.get("before") or {}, row.get("after") or {}):
            if state.get("snapshot_file"):
                _artifact(run, state["snapshot_file"], problems)
        internal = row.get("internal") or {}
        if internal.get("observe_diff_file"):
            _artifact(run, internal["observe_diff_file"], problems)
    if set(declared) != found:
        problems.append(f"results: declared {sorted(set(declared))}, found {sorted(found)}")
    if data.get("run_id") and data["run_id"] != run.name:
        problems.append("run.json: run_id differs from directory name")
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    args = parser.parse_args(argv)
    problems = check_run(args.run)
    for problem in problems:
        print(problem)
    print(f"check_run: {len(problems)} problem(s)")
    return int(bool(problems))


if __name__ == "__main__":
    sys.exit(main())
