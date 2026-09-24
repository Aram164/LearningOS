#!/usr/bin/env python3
"""Score connection-discovery results against the (private) oracle.

    python tests/eval/metrics/score_connections.py --oracle ORACLE_DIR \
        --results RUN_DIR [--world WORLD_REPO] [--probes C01,C02,...]

Reads RUN_DIR/connections.jsonl (schema: public/schemas/connection-result.schema.json)
and ORACLE_DIR/relations.yaml. Writes RUN_DIR/metrics-connections.json and
RUN_DIR/connections-worksheet.md, and prints a summary.

Definitions (per probe; targets that are not material ids are dropped before
ranking and counted):

  relevant            MUST_CONNECT ∪ USEFUL_CONNECT
  recall@k            |MUST ∩ top-k| / |MUST|              (undefined if no MUST)
  relevant_recall@k   |relevant ∩ top-k| / |relevant|
  precision@5         |relevant ∩ top-5| / 5               (unjudged = not relevant)
  judged_precision@5  |relevant ∩ top-5| / |(relevant ∪ MUST_NOT) ∩ top-5|
  must_not_rate@10    |MUST_NOT ∩ top-10| / |MUST_NOT|     (the false-positive rate)
  decoy_hit@5         any MUST_NOT in the top 5
  mrr                 1 / rank of the first MUST in the top 10 (0 if none)
  outdated_uncaveated superseded targets returned without an outdated/superseded caveat

Also reported: breakdowns by probe group (canon / arrival), by judgment
category, by lexical overlap, and the HEURISTIC explanation coverage (share of
the oracle's "should mention" items whose content words appear in the given
reason). Heuristic numbers support the judge; the worksheet is the record.

Missing probes are listed. Macro averages are given twice: over answered
probes, and over all requested probes with a missing probe scored as 0.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import (  # noqa: E402
    flags_outdated,
    is_material,
    load_yaml,
    mention_covered,
    normalize_target,
    read_jsonl,
    resolvable,
    world_ids,
)

KS = (5, 10)


def ranked(row: dict) -> tuple[list[dict], int]:
    seen, out, dropped = set(), [], 0
    for item in sorted(row.get("results") or [], key=lambda r: r.get("rank", 10**6)):
        target = normalize_target(item.get("target", ""))
        if not is_material(target):
            dropped += 1
            continue
        if target in seen:
            continue
        seen.add(target)
        out.append({**item, "target": target})
    return out[:10], dropped


def score_probe(pid: str, oracle: dict, row: dict | None, ids: set[str] | None,
                repo: Path | None) -> dict:
    judg = {j["t"]: j for j in oracle["judgments"]}
    must = {t for t, j in judg.items() if j["c"] == "MUST_CONNECT"}
    useful = {t for t, j in judg.items() if j["c"] == "USEFUL_CONNECT"}
    mustnot = {t for t, j in judg.items() if j["c"] == "MUST_NOT_CONNECT"}
    relevant = must | useful
    if row is None:
        return {"probe": pid, "answered": False, "n_must": len(must),
                "n_relevant": len(relevant), "n_must_not": len(mustnot)}
    items, dropped = ranked(row)
    targets = [i["target"] for i in items]

    def top(k):
        return set(targets[:k])

    out = {"probe": pid, "answered": True, "returned": len(targets),
           "non_material_dropped": dropped, "n_must": len(must), "n_relevant": len(relevant),
           "n_must_not": len(mustnot)}
    for k in KS:
        out[f"recall@{k}"] = len(must & top(k)) / len(must) if must else None
        out[f"relevant_recall@{k}"] = len(relevant & top(k)) / len(relevant) if relevant else None
    out["precision@5"] = len(relevant & top(5)) / 5
    decisive = (relevant | mustnot) & top(5)
    out["judged_precision@5"] = len(relevant & top(5)) / len(decisive) if decisive else None
    out["must_not_rate@10"] = len(mustnot & top(10)) / len(mustnot) if mustnot else None
    out["decoy_hit@5"] = bool(mustnot & top(5))
    first = next((r for r, t in enumerate(targets, start=1) if t in must), None)
    out["mrr"] = (1 / first) if first else (0.0 if must else None)
    out["unjudged_returned"] = sorted(t for t in targets if t not in judg)

    coverage, uncaveated, cited, resolved = [], [], 0, 0
    for item in items:
        j = judg.get(item["target"])
        reason = str(item.get("reason", ""))
        if j and j["c"] in ("MUST_CONNECT", "USEFUL_CONNECT") and j.get("m"):
            hits = sum(1 for m in j["m"] if mention_covered(m, reason))
            coverage.append(hits / len(j["m"]))
        if j and j.get("chron") == "superseded" and not flags_outdated(
                reason, item.get("flags") or []):
            uncaveated.append(item["target"])
        for ev in item.get("evidence") or []:
            ref = ev.get("ref") if isinstance(ev, dict) else ev
            if ref:
                cited += 1
                if ids is not None and resolvable(str(ref), ids, repo):
                    resolved += 1
    out["explanation_coverage_HEURISTIC"] = statistics.mean(coverage) if coverage else None
    out["outdated_uncaveated"] = uncaveated
    out["evidence_cited"] = cited
    out["evidence_resolvable_rate"] = (resolved / cited) if (cited and ids is not None) else None
    out["targets"] = [{"rank": r, "target": t, "class": judg.get(t, {}).get("c", "UNJUDGED")}
                      for r, t in enumerate(targets, start=1)]
    return out


def mean(values) -> float | None:
    vals = [v for v in values if v is not None]
    return round(statistics.mean(vals), 4) if vals else None


def aggregate(rows: list[dict]) -> dict:
    answered = [r for r in rows if r["answered"]]
    keys = ["recall@5", "recall@10", "relevant_recall@5", "relevant_recall@10",
            "precision@5", "judged_precision@5", "must_not_rate@10", "mrr",
            "explanation_coverage_HEURISTIC", "evidence_resolvable_rate"]
    out = {"probes": len(rows), "answered": len(answered),
           "macro_answered": {k: mean(r.get(k) for r in answered) for k in keys}}

    def missing_as_zero(r: dict, k: str):
        if r["answered"]:
            return r.get(k)
        if k.startswith("relevant"):
            return 0.0 if r["n_relevant"] else None
        if k.startswith("precision"):
            return 0.0
        return 0.0 if r["n_must"] else None

    out["macro_all_missing_as_zero"] = {
        k: mean(missing_as_zero(r, k) for r in rows)
        for k in ("recall@5", "recall@10", "relevant_recall@10", "precision@5", "mrr")}
    out["decoy_hit@5_rate"] = mean(1.0 if r["decoy_hit@5"] else 0.0 for r in answered
                                   if r.get("n_must_not"))
    out["outdated_uncaveated_total"] = sum(len(r["outdated_uncaveated"]) for r in answered)
    return out


def breakdowns(rows: list[dict], relations: dict) -> dict:
    by_cat = defaultdict(lambda: {"relevant": 0, "found@10": 0, "must_not": 0, "hit@10": 0})
    by_lex = defaultdict(lambda: {"must": 0, "found@10": 0})
    by_class = defaultdict(lambda: {"judged": 0, "returned@10": 0})
    for r in rows:
        if not r["answered"]:
            continue
        returned = {t["target"] for t in r["targets"][:10]}
        for j in relations[r["probe"]]["judgments"]:
            hit = j["t"] in returned
            by_class[j["c"]]["judged"] += 1
            by_class[j["c"]]["returned@10"] += int(hit)
            for cat in j["cat"]:
                bucket = by_cat[cat]
                if j["c"] in ("MUST_CONNECT", "USEFUL_CONNECT"):
                    bucket["relevant"] += 1
                    bucket["found@10"] += int(hit)
                elif j["c"] == "MUST_NOT_CONNECT":
                    bucket["must_not"] += 1
                    bucket["hit@10"] += int(hit)
            if j["c"] == "MUST_CONNECT":
                by_lex[j["lex"]]["must"] += 1
                by_lex[j["lex"]]["found@10"] += int(hit)

    def rate(n, d):
        return round(n / d, 4) if d else None

    return {
        "by_category": {c: {**v, "recall@10": rate(v["found@10"], v["relevant"]),
                            "must_not_rate@10": rate(v["hit@10"], v["must_not"])}
                        for c, v in sorted(by_cat.items())},
        "by_lexical_overlap_of_MUST": {k: {**v, "recall@10": rate(v["found@10"], v["must"])}
                                       for k, v in sorted(by_lex.items())},
        "by_class": {k: {**v, "returned_rate@10": rate(v["returned@10"], v["judged"])}
                     for k, v in sorted(by_class.items())},
    }


def worksheet(rows: list[dict], relations: dict, results: dict[str, dict]) -> str:
    lines = ["# Connection worksheet (judge)", "",
             "Grade each returned relevant target: explanation 0 (wrong/absent) · 1 (partly) · "
             "2 (correct), provenance 0/1. Oracle mentions are guidance, not wording.", ""]
    for r in rows:
        pid = r["probe"]
        oracle = relations[pid]
        lines.append(f"## {pid} — {oracle['query']}")
        if not r["answered"]:
            lines += ["", "_not answered_", ""]
            continue
        judg = {j["t"]: j for j in oracle["judgments"]}
        items, _ = ranked(results[pid])
        lines += ["", "| rank | target | oracle | reason given | should mention | expl | prov |",
                  "|---|---|---|---|---|---|---|"]
        for rank, item in enumerate(items, start=1):
            j = judg.get(item["target"], {})
            reason = str(item.get("reason", "")).replace("|", "/").replace("\n", " ")[:300]
            mention = "; ".join(j.get("m", [])).replace("|", "/")
            lines.append(f"| {rank} | {item['target']} | {j.get('c', 'UNJUDGED')} | {reason} | "
                         f"{mention} |  |  |")
        missed = [t for t, j in judg.items() if j["c"] == "MUST_CONNECT"
                  and t not in {i["target"] for i in items}]
        if missed:
            lines += ["", "Missed MUST_CONNECT: " + ", ".join(missed)]
        lines.append("")
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--oracle", required=True, type=Path)
    parser.add_argument("--results", required=True, type=Path,
                        help="run directory holding connections.jsonl, or the file itself")
    parser.add_argument("--world", type=Path, help="world repository, for provenance checks")
    parser.add_argument("--probes", help="comma-separated probe ids (default: all in oracle)")
    parser.add_argument("--out-dir", type=Path)
    args = parser.parse_args(argv)
    relations = load_yaml(args.oracle / "relations.yaml")["probes"]
    path = args.results if args.results.is_file() else args.results / "connections.jsonl"
    out_dir = args.out_dir or (args.results if args.results.is_dir() else args.results.parent)
    results: dict[str, dict] = {}
    for row in read_jsonl(path):
        results[str(row.get("probe"))] = row
    wanted = args.probes.split(",") if args.probes else list(relations)
    unknown = sorted(set(results) - set(relations))
    repo = args.world.resolve() if args.world else None
    ids = world_ids(repo) if repo else None
    rows = [score_probe(pid, relations[pid], results.get(pid), ids, repo) for pid in wanted]
    groups = {"canon": [r for r in rows if r["probe"].startswith("C")],
              "arrival": [r for r in rows if r["probe"].startswith("A")]}
    report = {
        "scorer_version": 1,
        "results_file": str(path),
        "missing_probes": [r["probe"] for r in rows if not r["answered"]],
        "unknown_probes_in_results": unknown,
        "overall": aggregate(rows),
        "by_group": {g: aggregate(rs) for g, rs in groups.items() if rs},
        **breakdowns(rows, relations),
        "per_probe": rows,
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "metrics-connections.json").write_text(json.dumps(report, indent=2) + "\n",
                                                      encoding="utf-8")
    (out_dir / "connections-worksheet.md").write_text(worksheet(rows, relations, results),
                                                      encoding="utf-8")
    print(json.dumps({"overall": report["overall"],
                      "by_category_recall@10": {c: v["recall@10"] for c, v in
                                                report["by_category"].items()}}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
