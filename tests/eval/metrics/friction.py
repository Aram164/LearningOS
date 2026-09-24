#!/usr/bin/env python3
"""Aggregate consumer friction across one or more runs.

    python tests/eval/metrics/friction.py RUN_DIR [RUN_DIR ...] [--out friction.json]

Reads RUN_DIR/results/*.json (schema: public/schemas/scenario-result.schema.json)
from every run and reports:

* per scenario, across runs: classification counts; median and max of tool
  calls, commands, retries, documents consulted, implementation files read,
  questions asked to the learner, minutes; how often implementation knowledge
  was needed;
* friction tags: how many runs and scenarios reported each tag — a tag seen in
  two or more independent runs is listed under `repeated`, the evidence the
  campaign prioritizes;
* implementation files read, by file, across runs (which internals consumers
  were forced into).

Counts come only from what runs recorded; a missing field is reported as
missing, never as zero.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

NUMERIC = ("tool_calls", "commands", "retries", "docs_consulted", "impl_files_read",
           "questions_asked_to_learner", "wall_minutes")


def _count(consumer: dict, key: str):
    value = consumer.get(key)
    if value is None:
        return None
    if isinstance(value, list):
        return len(value)
    return value


def load(run: Path) -> list[dict]:
    rows = []
    for path in sorted((run / "results").glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        data["_run"] = run.name
        rows.append(data)
    return rows


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("runs", nargs="+", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    rows = [row for run in args.runs for row in load(run)]
    by_scenario = defaultdict(list)
    for row in rows:
        by_scenario[row.get("scenario", "?")].append(row)

    scenarios = {}
    for sid, items in sorted(by_scenario.items()):
        entry = {"runs": sorted({r["_run"] for r in items}),
                 "classification": dict(Counter(r.get("classification", "MISSING")
                                                for r in items))}
        for key in NUMERIC:
            vals = [v for v in (_count(r.get("consumer") or {}, key) for r in items)
                    if v is not None]
            entry[key] = ({"median": statistics.median(vals), "max": max(vals), "n": len(vals)}
                          if vals else "missing")
        needed = [bool((r.get("consumer") or {}).get("implementation_knowledge_needed"))
                  for r in items if "implementation_knowledge_needed" in (r.get("consumer") or {})]
        entry["implementation_knowledge_needed"] = (f"{sum(needed)}/{len(needed)}"
                                                    if needed else "missing")
        scenarios[sid] = entry

    tag_runs = defaultdict(set)
    tag_scenarios = defaultdict(set)
    tag_examples = defaultdict(list)
    impl_files = Counter()
    for row in rows:
        for item in row.get("friction") or []:
            tag = item.get("tag", "other")
            tag_runs[tag].add(row["_run"])
            tag_scenarios[tag].add(row.get("scenario", "?"))
            if len(tag_examples[tag]) < 5:
                tag_examples[tag].append(f"{row['_run']}/{row.get('scenario')}: "
                                         f"{item.get('description', '')[:200]}")
        for path in (row.get("consumer") or {}).get("impl_files_read") or []:
            impl_files[str(path)] += 1
    tags = {tag: {"runs": len(tag_runs[tag]), "scenarios": sorted(tag_scenarios[tag]),
                  "examples": tag_examples[tag]} for tag in sorted(tag_runs)}
    report = {
        "friction_version": 1,
        "runs": [str(r) for r in args.runs],
        "scenario_results": len(rows),
        "scenarios": scenarios,
        "friction_tags": tags,
        "repeated": sorted(t for t, v in tags.items() if v["runs"] >= 2),
        "implementation_files_read": dict(impl_files.most_common()),
    }
    text = json.dumps(report, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
