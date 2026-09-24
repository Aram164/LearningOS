#!/usr/bin/env python3
"""Score retrieval answers against the (private) oracle.

    python tests/eval/metrics/score_retrieval.py --oracle ORACLE_DIR \
        --results RUN_DIR [--world WORLD_REPO] [--questions Q01,Q02,...]

Reads RUN_DIR/answers.jsonl (schema: public/schemas/answer-result.schema.json)
and ORACLE_DIR/answers.yaml. Writes RUN_DIR/metrics-retrieval.json and
RUN_DIR/retrieval-worksheet.md.

Per question:

  evidence_all        every `all` id of the oracle was cited (normalized ids)
  evidence_any        at least one `any` id was cited (true when none required)
  evidence_ok         evidence_all and evidence_any
  points_HEURISTIC    share of answer points whose keyword groups match the
                      answer text (a point with `min: n` needs n groups)
  forbidden_HEURISTIC forbidden claims whose keywords match — flags for the
                      judge, not verdicts (negations can trip them)
  provenance          share of cited references that resolve in the world

The judge grades each answer 0/1/2 in the worksheet; that grade is the result
of record. Aggregates are reported overall and per question category, never
only as one number.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import (  # noqa: E402,E501
    keyword_hit,
    load_yaml,
    normalize_target,
    read_jsonl,
    resolvable,
    world_ids,
)


def cited_ids(row: dict) -> list[str]:
    out = []
    for ev in row.get("evidence") or []:
        ref = ev.get("ref") if isinstance(ev, dict) else ev
        if ref:
            out.append(str(ref))
    return out


def score_question(qid: str, oracle: dict, row: dict | None, ids, repo) -> dict:
    if row is None:
        return {"question": qid, "answered": False, "cat": oracle["cat"]}
    refs = cited_ids(row)
    cited = {normalize_target(r) for r in refs}
    need_all = oracle["evidence"].get("all", [])
    need_any = oracle["evidence"].get("any", [])
    text = str(row.get("answer", ""))
    points = []
    for point in oracle.get("points", []):
        groups = point["kw"]
        if point.get("min"):
            hit = sum(1 for g in groups if keyword_hit([g], text)) >= point["min"]
        else:
            hit = keyword_hit(groups, text)
        points.append({"fact": point["fact"], "hit": hit})
    forbidden = [f["claim"] for f in oracle.get("forbidden", []) if keyword_hit(f["kw"], text)]
    resolved = [r for r in refs if ids is not None and resolvable(r, ids, repo)]
    return {
        "question": qid, "answered": True, "cat": oracle["cat"],
        "evidence_all": all(t in cited for t in need_all),
        "evidence_any": (not need_any) or any(t in cited for t in need_any),
        "missing_evidence": [t for t in need_all if t not in cited],
        "points_HEURISTIC": (sum(p["hit"] for p in points) / len(points)) if points else None,
        "points": points,
        "forbidden_HEURISTIC": forbidden,
        "provenance": (len(resolved) / len(refs)) if (refs and ids is not None) else None,
        "confidence": row.get("confidence"),
    }


def summarize(rows: list[dict]) -> dict:
    answered = [r for r in rows if r["answered"]]

    def avg(key):
        vals = [r[key] for r in answered if r.get(key) is not None]
        return round(statistics.mean(vals), 4) if vals else None

    ok = [r for r in answered if r["evidence_all"] and r["evidence_any"]]
    return {"questions": len(rows), "answered": len(answered),
            "evidence_ok_rate": round(len(ok) / len(rows), 4) if rows else None,
            "points_HEURISTIC_mean": avg("points_HEURISTIC"),
            "provenance_mean": avg("provenance"),
            "forbidden_flags": sum(len(r["forbidden_HEURISTIC"]) for r in answered)}


def worksheet(rows, oracle, results) -> str:
    lines = ["# Retrieval worksheet (judge)", "",
             "Grade: 0 wrong or unsupported · 1 partly right or weak evidence · 2 correct with "
             "evidence. Check forbidden flags by reading, not by keyword.", ""]
    for r in rows:
        q = oracle[r["question"]]
        lines.append(f"## {r['question']} ({', '.join(q['cat'])})")
        if not r["answered"]:
            lines += ["", "_not answered_", ""]
            continue
        row = results[r["question"]]
        answer = str(row.get("answer", "")).strip().replace("\n", "\n> ")
        lines += ["", "> " + answer, "",
                  "Evidence cited: " + ", ".join(cited_ids(row) or ["(none)"]),
                  "Expected all: " + ", ".join(q["evidence"].get("all", []) or ["—"]),
                  "Expected any: " + ", ".join(q["evidence"].get("any", []) or ["—"]), "",
                  "Points (HEURISTIC hit):"]
        lines += [f"- [{'x' if p['hit'] else ' '}] {p['fact']}" for p in r["points"]]
        if r["forbidden_HEURISTIC"]:
            lines += ["", "Forbidden-claim flags: " + "; ".join(r["forbidden_HEURISTIC"])]
        if q.get("judge"):
            lines += ["", "Judge note: " + q["judge"]]
        lines += ["", "Grade: __", ""]
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--oracle", required=True, type=Path)
    parser.add_argument("--results", required=True, type=Path)
    parser.add_argument("--world", type=Path)
    parser.add_argument("--questions")
    parser.add_argument("--out-dir", type=Path)
    args = parser.parse_args(argv)
    oracle = load_yaml(args.oracle / "answers.yaml")["questions"]
    path = args.results if args.results.is_file() else args.results / "answers.jsonl"
    out_dir = args.out_dir or (args.results if args.results.is_dir() else args.results.parent)
    results = {str(r.get("question")): r for r in read_jsonl(path)}
    wanted = args.questions.split(",") if args.questions else list(oracle)
    repo = args.world.resolve() if args.world else None
    ids = world_ids(repo) if repo else None
    rows = [score_question(q, oracle[q], results.get(q), ids, repo) for q in wanted]
    by_cat = defaultdict(list)
    for r in rows:
        for cat in r["cat"]:
            by_cat[cat].append(r)
    report = {"scorer_version": 1, "results_file": str(path),
              "missing": [r["question"] for r in rows if not r["answered"]],
              "overall": summarize(rows),
              "by_category": {c: summarize(rs) for c, rs in sorted(by_cat.items())},
              "per_question": rows}
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "metrics-retrieval.json").write_text(json.dumps(report, indent=2) + "\n",
                                                    encoding="utf-8")
    (out_dir / "retrieval-worksheet.md").write_text(worksheet(rows, oracle, results),
                                                    encoding="utf-8")
    print(json.dumps(report["overall"], indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
