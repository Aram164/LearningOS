#!/usr/bin/env python3
"""Stage 3b Comprehensive Benchmark Runner for LearningOS Material Search.

Implements the 4 methodological requirements from Aram:
1. Dual-Target Evaluation:
   - Strict Target Match (original pre-designated primary target).
   - Topical / Evidence Match (all independently verified legitimate targets).
2. Two-Dimensional Failure Taxonomy:
   - Retrieval: FOUND, RANKING_MISS, NO_MATCH, WRONG_SOURCE, INDEX_PAGE_CONFUSION
   - Evidence: VERIFIED, ROUTE_UNMAPPED, EXTRACTOR_DIVERGENCE, SPAN_FAILURE, NOT_ATTEMPTED
3. Exact Latency Separation:
   - t_sql_ms: Pure SQLite database query execution time.
   - t_retrieval_e2e_ms: Complete deterministic search, ranking, route resolution, and span extraction.
4. Unanswerable evaluation:
   - false-positive rate and unjustified verification tracking.

Compares 4 ranking configurations under unicode61:
- Arm 1: FTS5_Raw (unmodified Stage 3 baseline query)
- Arm 2: FTS5_Tiered_Stopwords (exact phrase -> AND -> OR with function words filtered)
- Arm 3: FTS5_Tiered_Diversified (tiered search with max 2 hits per SHA)
- Arm 4: FTS5_Optimized (tiered search + max 2 per SHA + index-page demotion)

Strictly isolated under workbench/material_search_eval/.
Never modifies Core, schemas, or canonical records.
Held-out questions remain untouched.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sqlite3
import sys
import time
import unicodedata
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
TOOLS_DIR = REPO_ROOT / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import yaml
from learning_os.store.loading import load_repo
from learning_os.domain.material_refs import unit_routes
from learning_os.store.materials.resolution import resolve_route_material_files, sha256_file
import learning_os.app.handlers
from learning_os.app.context import OpContext
from learning_os.app.registry import REGISTRY
from eval_metrics import evaluate_query_3b, calculate_summary_3b, BenchmarkSummary, QueryEvaluation
from fts5_reranker import (
    build_tiered_queries,
    apply_diversification_and_reranking,
    is_index_or_toc_page,
)

DB_FILE = SCRIPT_DIR / "indices" / "fts5_unicode61.sqlite3"
QUESTIONS_DEV_FILE = SCRIPT_DIR / "questions_dev.yaml"
CACHE_DIR = REPO_ROOT / "generated" / "text-cache"


def norm(text: str) -> str:
    n = unicodedata.normalize("NFC", text)
    return " ".join(n.split()).lower()


def build_sha_route_map(repo) -> dict[str, tuple[str, str]]:
    """Map SHA-256 to (unit_id, route_id) for material.span verification."""
    mapping = {}
    for unit_id, unit in repo.units.items():
        sm = repo.module_source_maps.get(unit.module_id)
        if not sm:
            continue
        for r in unit_routes(sm, unit.module_id, unit.id):
            files = resolve_route_material_files(repo, r)
            for f in files:
                sha = sha256_file(Path(f.path)).removeprefix("sha256:")
                if sha not in mapping:
                    mapping[sha] = (unit.id, r.get("id"))
    return mapping


class Stage3bArmEvaluator:
    """Evaluates an FTS5 configuration under Stage 3b criteria."""

    def __init__(
        self, arm_name: str, ranking_mode: str, repo, sha_to_route: dict[str, tuple[str, str]]
    ):
        self.arm_name = arm_name
        self.ranking_mode = ranking_mode
        self.repo = repo
        self.sha_to_route = sha_to_route

        # Connect strictly read-only
        uri = f"file:{DB_FILE.resolve()}?mode=ro"
        self.con = sqlite3.connect(uri, uri=True)
        self.cur = self.con.cursor()

    def query_sqlite(self, raw_query: str) -> tuple[list[dict[str, Any]], float]:
        """Execute SQLite queries according to arm strategy and measure pure t_sql_ms."""
        t0 = time.perf_counter()
        raw_candidates = []
        seen_keys = set()

        if self.ranking_mode == "raw":
            # Stage 3 raw query formulation
            clean = re.sub(r"[^\w\s]", " ", raw_query).strip()
            words = [w for w in clean.split() if len(w) > 0]
            if words:
                exact_phrase = f'"{clean}"'
                and_terms = " AND ".join(f'"{w}"' for w in words)
                or_terms = " OR ".join(f'"{w}"' for w in words)
                fts_expr = f"{exact_phrase} OR ({and_terms}) OR ({or_terms})"
                sql = """
                SELECT source_sha256, page_no, source_id, title,
                       bm25(material_fts) AS score, body,
                       snippet(material_fts, 4, '[', ']', ' … ', 20) AS excerpt
                FROM material_fts
                WHERE material_fts MATCH ?
                ORDER BY rank
                LIMIT 50;
                """
                try:
                    self.cur.execute(sql, (fts_expr,))
                    for r in self.cur.fetchall():
                        raw_candidates.append(
                            {
                                "source_sha256": r[0],
                                "physical_page": int(r[1]),
                                "source_id": r[2],
                                "title": r[3],
                                "score": float(r[4]),
                                "_body": r[5],
                                "snippet": r[6],
                            }
                        )
                except Exception:
                    pass

        else:
            # Tiered query formulation (exact_phrase -> conjunction -> disjunction)
            tiers = build_tiered_queries(raw_query)
            for tier_name, expr in tiers:
                if len(raw_candidates) >= 50:
                    break
                sql = """
                SELECT source_sha256, page_no, source_id, title,
                       bm25(material_fts) AS score, body,
                       snippet(material_fts, 4, '[', ']', ' … ', 20) AS excerpt
                FROM material_fts
                WHERE material_fts MATCH ?
                ORDER BY rank
                LIMIT 50;
                """
                try:
                    self.cur.execute(sql, (expr,))
                    for r in self.cur.fetchall():
                        key = (r[0], int(r[1]))
                        if key not in seen_keys:
                            seen_keys.add(key)
                            raw_candidates.append(
                                {
                                    "source_sha256": r[0],
                                    "physical_page": int(r[1]),
                                    "source_id": r[2],
                                    "title": r[3],
                                    "score": float(r[4]),
                                    "_body": r[5],
                                    "snippet": r[6],
                                    "tier": tier_name,
                                }
                            )
                except Exception:
                    pass

        t_sql_ms = (time.perf_counter() - t0) * 1000.0
        return raw_candidates, t_sql_ms

    def run_query(self, query_entry: dict[str, Any]) -> dict[str, Any]:
        t0_e2e = time.perf_counter()
        raw_query = query_entry.get("query") or query_entry.get("question")
        expected_status = query_entry.get("expected_status", "answerable")
        all_targets = query_entry.get("targets", [])

        # Step 1: Database Query
        raw_candidates, t_sql_ms = self.query_sqlite(raw_query)

        # Step 2: Reranking & Diversification
        if self.ranking_mode == "raw":
            final_candidates = raw_candidates[:5]
        elif self.ranking_mode == "tiered_stopwords":
            final_candidates = raw_candidates[:5]
        elif self.ranking_mode == "tiered_diversified":
            final_candidates = apply_diversification_and_reranking(
                raw_candidates, max_per_sha=2, penalize_index_pages=False, limit=5
            )
        elif self.ranking_mode == "optimized":
            final_candidates = apply_diversification_and_reranking(
                raw_candidates, max_per_sha=2, penalize_index_pages=True, limit=5
            )
        else:
            final_candidates = raw_candidates[:5]

        # Step 3: Authoritative Evidence Verification via material.span
        tool_calls = 1  # 1 call for search query
        bytes_transferred = len(json.dumps(final_candidates, default=str).encode("utf-8"))
        verified_evidence = False
        target_route_unmapped = False
        is_index_detected = False

        target_quotes = [t["evidence_quote"] for t in all_targets if t.get("evidence_quote")]
        topical_pairs = {(t["source_sha256"], int(t["physical_page"])) for t in all_targets}

        for cand in final_candidates[:3]:
            sha = cand["source_sha256"]
            page = cand["physical_page"]
            cand_pair = (sha, page)
            route_binding = self.sha_to_route.get(sha)

            if is_index_or_toc_page(cand.get("_body", "")):
                is_index_detected = True

            if route_binding:
                tool_calls += 1
                uid, rid = route_binding
                span_req = {
                    "unit_id": uid,
                    "route_id": rid,
                    "pages": f"pdf p. {page}",
                    "extract": True,
                }
                ctx_span = OpContext(
                    root=REPO_ROOT,
                    operation="material.span",
                    channel="cli",
                    invocation="query",
                    gateway=None,
                )
                try:
                    span_res = REGISTRY["material.span"].handler(ctx_span, span_req)
                    span_data = span_res.payload if span_res else {}
                except Exception as e:
                    span_data = {}
                span_bytes = len(json.dumps(span_data, default=str).encode("utf-8"))
                bytes_transferred += span_bytes

                if isinstance(span_data, dict):
                    spans = span_data.get("spans", [])
                    for sp in spans:
                        excerpt = sp.get("excerpt", "")
                        for tq in target_quotes:
                            if norm(tq) in norm(excerpt):
                                verified_evidence = True
            else:
                # Unmapped material
                if cand_pair in topical_pairs:
                    target_route_unmapped = True

                p_file = CACHE_DIR / sha / f"pp-{page:04d}.txt"
                if p_file.exists():
                    try:
                        raw_txt = p_file.read_text(encoding="utf-8", errors="ignore")
                        for tq in target_quotes:
                            if norm(tq) in norm(raw_txt):
                                verified_evidence = True
                    except OSError:
                        pass

            if verified_evidence:
                break

        t_retrieval_e2e_ms = (time.perf_counter() - t0_e2e) * 1000.0

        for c in final_candidates:
            if "_body" in c:
                c["body_chars"] = len(c.pop("_body"))
            if "snippet" in c:
                c["snippet_chars"] = len(c.pop("snippet"))

        return {
            "query_id": query_entry["id"],
            "query": raw_query,
            "expected_status": expected_status,
            "candidates": final_candidates,
            "t_sql_ms": t_sql_ms,
            "t_retrieval_e2e_ms": t_retrieval_e2e_ms,
            "tool_calls": tool_calls,
            "bytes_transferred": bytes_transferred,
            "verified_evidence": verified_evidence,
            "target_route_unmapped": target_route_unmapped,
            "is_index_detected": is_index_detected,
        }

    def close(self):
        self.con.close()


def run_benchmark_arm(
    arm_name: str,
    ranking_mode: str,
    questions: list[dict[str, Any]],
    repo,
    sha_to_route: dict[str, tuple[str, str]],
) -> tuple[BenchmarkSummary, list[QueryEvaluation]]:
    """Execute complete Stage 3b evaluation for one arm."""
    print(f"\n============================================================")
    print(f"RUNNING BENCHMARK ARM: {arm_name} ({ranking_mode})")
    print(f"============================================================")

    evaluator = Stage3bArmEvaluator(arm_name, ranking_mode, repo, sha_to_route)
    query_evaluations: list[QueryEvaluation] = []

    for idx, q in enumerate(questions, start=1):
        res = evaluator.run_query(q)
        q_eval = evaluate_query_3b(
            query_entry=q,
            retrieved_candidates=res["candidates"],
            tool_calls=res["tool_calls"],
            bytes_transferred=res["bytes_transferred"],
            t_sql_ms=res["t_sql_ms"],
            t_retrieval_e2e_ms=res["t_retrieval_e2e_ms"],
            verified_span_success=res["verified_evidence"],
            route_unmapped_for_target=res["target_route_unmapped"],
            is_index_page=res["is_index_detected"],
        )
        query_evaluations.append(q_eval)

        ret_stat = q_eval.retrieval_status
        evi_stat = q_eval.evidence_status
        flag = (
            "✓ Strict@1"
            if q_eval.strict_hit_at_1
            else (
                "✓ Top@3"
                if q_eval.topical_hit_at_3
                else ("✓ Top@5" if q_eval.topical_hit_at_5 else "✗ Miss")
            )
        )
        print(
            f"[{idx:02d}/{len(questions):02d}] {q['id']:6s} ({q['category']:14s}) -> {flag:10s} [Ret:{ret_stat:18s} Evi:{evi_stat:18s}] in {res['t_retrieval_e2e_ms']:5.1f}ms (SQL: {res['t_sql_ms']:4.1f}ms)"
        )

    evaluator.close()
    summary = calculate_summary_3b(arm_name, query_evaluations)
    return summary, query_evaluations


def main():
    parser = argparse.ArgumentParser(description="Run Stage 3b FTS5 Benchmarks")
    parser.add_argument(
        "--arm", choices=["all", "raw", "tiered", "diversified", "optimized"], default="all"
    )
    args = parser.parse_args()

    print("Loading LearningOS repository context...")
    repo = load_repo(REPO_ROOT)
    sha_to_route = build_sha_route_map(repo)
    print(f"Mapped {len(sha_to_route)} material SHAs to authoritative unit routes.")

    questions = yaml.safe_load(QUESTIONS_DEV_FILE.read_text(encoding="utf-8"))
    print(f"Loaded {len(questions)} dev questions with dual-target annotations.")

    arms = []
    if args.arm in ("all", "raw"):
        arms.append(("FTS5_1_Raw", "raw"))
    if args.arm in ("all", "tiered"):
        arms.append(("FTS5_2_Tiered_Stopwords", "tiered_stopwords"))
    if args.arm in ("all", "diversified"):
        arms.append(("FTS5_3_Tiered_Diversified", "tiered_diversified"))
    if args.arm in ("all", "optimized"):
        arms.append(("FTS5_4_Optimized", "optimized"))

    results = {}
    for arm_name, mode in arms:
        summary, evals = run_benchmark_arm(arm_name, mode, questions, repo, sha_to_route)
        results[arm_name] = {
            "summary": summary.__dict__,
            "evaluations": [e.__dict__ for e in evals],
        }

    out_file = SCRIPT_DIR / "stage_3b_results.json"
    out_file.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\n============================================================")
    print(f"All Stage 3b Arms evaluated. Results exported to {out_file.name}")
    print(f"============================================================")

    # Print comparison table
    headers = ["Metric"] + [name for name, _ in arms]
    row_fmt = "{:<32} " + " | {:<16}" * len(arms)
    print(row_fmt.format(*headers))
    print("-" * (35 + 19 * len(arms)))

    def sval(arm_k, f_key, is_pct=False, is_ms=False):
        v = results[arm_k]["summary"][f_key]
        if is_pct:
            return f"{v * 100:.1f} %"
        if is_ms:
            return f"{v:.1f} ms"
        if isinstance(v, float):
            return f"{v:.3f}"
        return str(v)

    metrics = [
        ("Strict Recall@1", "strict_recall_at_1", True, False),
        ("Strict Recall@3", "strict_recall_at_3", True, False),
        ("Strict Recall@5", "strict_recall_at_5", True, False),
        ("Strict MRR", "strict_mrr", False, False),
        ("Topical Recall@1", "topical_recall_at_1", True, False),
        ("Topical Recall@3", "topical_recall_at_3", True, False),
        ("Topical Recall@5", "topical_recall_at_5", True, False),
        ("Topical MRR", "topical_mrr", False, False),
        ("Verified Evidence Rate", "verified_evidence_rate", True, False),
        ("False Source Rate", "false_source_rate", True, False),
        ("Unanswerable FP Rate", "unanswerable_false_positive_rate", True, False),
        ("Avg Tool Calls", "avg_tool_calls", False, False),
        ("Avg Bytes Transferred", "avg_bytes_transferred", False, False),
        ("t_sql_ms P50", "t_sql_p50_ms", False, True),
        ("t_retrieval_e2e_ms P50", "t_retrieval_e2e_p50_ms", False, True),
        ("t_retrieval_e2e_ms P95", "t_retrieval_e2e_p95_ms", False, True),
    ]

    for label, key, is_p, is_m in metrics:
        vals = [sval(name, key, is_p, is_m) for name, _ in arms]
        print(row_fmt.format(label, *vals))


if __name__ == "__main__":
    main()
