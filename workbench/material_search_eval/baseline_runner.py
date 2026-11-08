#!/usr/bin/env python3
"""Baseline Runner for LearningOS Material Search Evaluation (Stage 2).

Executes two distinct baseline arms across the evaluation questions:
- Baseline A (Current LearningOS Official Workflow):
    1. Executes `material.context` search across registered notes and assessments.
    2. Gathers candidate routes (or falls back to route-locator inspection).
    3. Executes `material.span` with `--extract` to inspect the candidate passage.
- Baseline B (Direct Lexical Grep over `generated/text-cache/`):
    1. Performs direct lexical scanning across the 72,199 cached page texts.
    2. Ranks pages by term frequency / exact phrase matching.
    3. Resolves candidate coordinates to routes and verifies via `material.span`.

Collects: Recall@1/3/5, MRR, tool calls, bytes transferred, wall latency, verified evidence rate.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import unicodedata
from pathlib import Path
from typing import Any

import yaml

# Add tools/ to sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
TOOLS_DIR = REPO_ROOT / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from learning_os.store.loading import load_repo
from learning_os.domain.material_refs import unit_routes
from learning_os.store.materials.resolution import resolve_route_material_files, sha256_file
import learning_os.app.handlers  # registers handlers
from learning_os.app.context import OpContext
from learning_os.app.registry import REGISTRY
from eval_metrics import evaluate_query_3b, calculate_summary_3b, BenchmarkSummary, QueryEvaluation


def norm(text: str) -> str:
    n = unicodedata.normalize("NFC", text)
    return " ".join(n.split()).lower()


class BaselineAEvaluator:
    """Evaluates Baseline A: The existing official LearningOS retrieval path."""

    def __init__(self, repo, repo_root: Path):
        self.repo = repo
        self.repo_root = repo_root

        # Precompute locator / route lookup table for fallbacks
        self.routes_catalog = []
        for unit_id, unit in repo.units.items():
            sm = repo.module_source_maps.get(unit.module_id)
            if not sm:
                continue
            for r in unit_routes(sm, unit.module_id, unit.id):
                files = resolve_route_material_files(repo, r)
                file_shas = [sha256_file(Path(f.path)).removeprefix("sha256:") for f in files]
                locator = r.get("locator", "")
                title = r.get("title", "")
                self.routes_catalog.append({
                    "unit_id": unit.id,
                    "route_id": r.get("id"),
                    "module_id": unit.module_id,
                    "source_id": r.get("source_id"),
                    "locator": locator,
                    "title": title,
                    "file_shas": file_shas,
                    "searchable_text": norm(f"{title} {locator} {r.get('id')}")
                })

    def run_query(self, query_entry: dict[str, Any]) -> tuple[list[dict[str, Any]], int, int, float, bool]:
        t0 = time.perf_counter()
        query_text = query_entry.get("query") or query_entry.get("question")
        targets = query_entry.get("targets", [])
        expected_status = query_entry.get("expected_status", "answerable")

        tool_calls = 0
        bytes_transferred = 0
        candidates: list[dict[str, Any]] = []
        verified_evidence = False

        # Step 1: Run material.context
        tool_calls += 1
        req_payload = {
            "query": query_text,
            "limit": 10
        }
        ctx = OpContext(root=self.repo_root, operation="material.context", channel="cli", invocation="query", gateway=None)
        try:
            res_result = REGISTRY["material.context"].handler(ctx, req_payload)
            res_data = res_result.payload if res_result else {}
        except Exception:
            res_data = {}
        ctx_bytes = len(json.dumps(res_data).encode("utf-8"))
        bytes_transferred += ctx_bytes

        found_routes = []
        if isinstance(res_data, dict):
            # Extract routes from matching items
            items = res_data.get("items", [])
            for item in items:
                rid = item.get("route_id")
                uid = item.get("unit_id")
                if rid and uid:
                    found_routes.append((uid, rid))

        # Step 2: If material.context found no items, emulate agent scanning route locators
        if not found_routes:
            # Score routes by keyword overlap in title and locator
            q_terms = [t for t in norm(query_text).split() if len(t) > 2]
            scored_routes = []
            for r in self.routes_catalog:
                score = sum(1 for term in q_terms if term in r["searchable_text"])
                if score > 0:
                    scored_routes.append((score, r["unit_id"], r["route_id"], r))
            scored_routes.sort(key=lambda x: -x[0])
            found_routes = [(uid, rid) for _, uid, rid, _ in scored_routes[:3]]

        # Step 3: Call material.span for top candidate routes
        target_quotes = [t["evidence_quote"] for t in targets]
        for uid, rid in found_routes[:3]:
            tool_calls += 1
            span_req = {
                "unit_id": uid,
                "route_id": rid,
                "extract": True
            }
            ctx_span = OpContext(root=self.repo_root, operation="material.span", channel="cli", invocation="query", gateway=None)
            try:
                span_res = REGISTRY["material.span"].handler(ctx_span, span_req)
                span_data = span_res.payload if span_res else {}
            except Exception:
                span_data = {}
            span_bytes = len(json.dumps(span_data).encode("utf-8"))
            bytes_transferred += span_bytes

            if isinstance(span_data, dict):
                spans = span_data.get("spans", [])
                for sp in spans:
                    sha = sp.get("file_sha256", "").removeprefix("sha256:")
                    excerpt = sp.get("excerpt", "")
                    pages = sp.get("pages", [])

                    # Add candidates per page
                    for p in pages:
                        candidates.append({
                            "source_sha256": sha,
                            "physical_page": p,
                            "score": 1.0,
                            "snippet_chars": len(excerpt[:100])
                        })

                    # Check if evidence quote was verified
                    for tq in target_quotes:
                        if norm(tq) in norm(excerpt):
                            verified_evidence = True

            if verified_evidence:
                break

        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        return candidates, tool_calls, bytes_transferred, elapsed_ms, verified_evidence


class BaselineBEvaluator:
    """Evaluates Baseline B: Direct lexical grep over generated/text-cache/."""

    def __init__(self, repo, cache_dir: Path):
        self.repo = repo
        self.cache_dir = cache_dir

        # Precompute sha -> primary route
        self.sha_to_route = {}
        for unit_id, unit in repo.units.items():
            sm = repo.module_source_maps.get(unit.module_id)
            if not sm:
                continue
            for r in unit_routes(sm, unit.module_id, unit.id):
                files = resolve_route_material_files(repo, r)
                for f in files:
                    h = sha256_file(Path(f.path)).removeprefix("sha256:")
                    self.sha_to_route.setdefault(h, (unit.id, r.get("id")))

        # Load list of page files
        self.index_entries = []
        for d in sorted(self.cache_dir.iterdir()):
            if not d.is_dir():
                continue
            sha = d.name
            for p in sorted(d.glob("pp-*.txt")):
                page_no = int(p.stem.split("-")[1])
                self.index_entries.append((sha, page_no, p))

    def run_query(self, query_entry: dict[str, Any]) -> tuple[list[dict[str, Any]], int, int, float, bool]:
        t0 = time.perf_counter()
        query_text = query_entry.get("query") or query_entry.get("question")
        targets = query_entry.get("targets", [])

        tool_calls = 0
        bytes_transferred = 0
        verified_evidence = False

        q_terms = [t for t in norm(query_text).split() if len(t) > 1]
        exact_phrase = norm(query_text)

        matches = []
        # Search page text files
        for sha, page_no, path in self.index_entries:
            try:
                raw = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue

            txt = norm(raw)
            if not txt:
                continue

            score = 0
            if exact_phrase in txt:
                score += 10.0

            matched_terms = sum(1 for term in q_terms if term in txt)
            if matched_terms > 0:
                score += matched_terms
                matches.append((score, sha, page_no, raw[:200]))

        # Sort descending by score
        matches.sort(key=lambda x: -x[0])

        candidates = []
        for score, sha, page_no, snippet in matches[:5]:
            candidates.append({
                "source_sha256": sha,
                "physical_page": page_no,
                "score": score,
                "snippet_chars": len(snippet[:100])
            })

        # Measure bytes transferred (search output payload)
        bytes_transferred += len(json.dumps(candidates).encode("utf-8"))

        # Step 2: Verification step via material.span or direct text check
        target_quotes = [t["evidence_quote"] for t in targets]
        for cand in candidates[:3]:
            sha = cand["source_sha256"]
            page = cand["physical_page"]
            route_binding = self.sha_to_route.get(sha)

            if route_binding:
                # Call material.span to verify coordinate through Core
                tool_calls += 1
                uid, rid = route_binding
                span_req = {
                    "unit_id": uid,
                    "route_id": rid,
                    "pages": f"pdf p. {page}",
                    "extract": True
                }
                ctx_span = OpContext(root=REPO_ROOT, operation="material.span", channel="cli", invocation="query", gateway=None)
                try:
                    span_res = REGISTRY["material.span"].handler(ctx_span, span_req)
                    span_data = span_res.payload if span_res else {}
                except Exception:
                    span_data = {}
                span_bytes = len(json.dumps(span_data).encode("utf-8"))
                bytes_transferred += span_bytes

                if isinstance(span_data, dict):
                    spans = span_data.get("spans", [])
                    for sp in spans:
                        excerpt = sp.get("excerpt", "")
                        for tq in target_quotes:
                            if norm(tq) in norm(excerpt):
                                verified_evidence = True
            else:
                # Unmapped material: verify directly against cached page file
                p_file = self.cache_dir / sha / f"pp-{page:04d}.txt"
                if p_file.exists():
                    raw = p_file.read_text(encoding="utf-8", errors="ignore")
                    for tq in target_quotes:
                        if norm(tq) in norm(raw):
                            verified_evidence = True

            if verified_evidence:
                break

        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        return candidates, tool_calls, bytes_transferred, elapsed_ms, verified_evidence


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Baseline A and B for LearningOS Material Search.")
    parser.add_argument("--dataset", choices=["dev", "heldout", "all"], default="dev", help="Which dataset to evaluate.")
    parser.add_argument("--arm", choices=["all", "baseline_a", "baseline_b"], default="all", help="Which baseline arm to run.")
    parser.add_argument("--json-out", type=str, default="", help="Path to write JSON benchmark results.")
    args = parser.parse_args()

    cache_dir = REPO_ROOT / "generated/text-cache"
    if not cache_dir.exists():
        print(f"Error: Text cache missing at {cache_dir}", file=sys.stderr)
        return 1

    print(f"Loading LearningOS repository from {REPO_ROOT}...")
    repo = load_repo(REPO_ROOT)

    queries = []
    if args.dataset in ("dev", "all"):
        with open(SCRIPT_DIR / "questions_dev.yaml", "r", encoding="utf-8") as f:
            queries.extend(yaml.safe_load(f))
    if args.dataset in ("heldout", "all"):
        with open(SCRIPT_DIR / "questions_heldout.yaml", "r", encoding="utf-8") as f:
            queries.extend(yaml.safe_load(f))

    print(f"Loaded {len(queries)} evaluation queries ({args.dataset}).")

    eval_a = BaselineAEvaluator(repo, REPO_ROOT)
    eval_b = BaselineBEvaluator(repo, cache_dir)

    results_data = {}

    if args.arm in ("all", "baseline_a"):
        print("\n" + "=" * 60)
        print("RUNNING BASELINE A: Current Official LearningOS Workflow")
        print("=" * 60)
        evals_a: list[QueryEvaluation] = []
        for i, q in enumerate(queries, 1):
            qid = q["id"]
            cat = q["category"]
            cands, tc, bt, dur, ver = eval_a.run_query(q)
            q_eval = evaluate_query_3b(
                query_entry=q,
                retrieved_candidates=cands,
                tool_calls=tc,
                bytes_transferred=bt,
                t_sql_ms=0.0,
                t_retrieval_e2e_ms=dur,
                verified_span_success=ver
            )
            evals_a.append(q_eval)
            hit_flag = "✓ Strict@1" if q_eval.strict_hit_at_1 else ("✓ Top@3" if q_eval.topical_hit_at_3 else ("✓ Top@5" if q_eval.topical_hit_at_5 else "✗ Miss"))
            ver_flag = "✓ Ver" if ver else "–"
            print(f"[{i:02d}/{len(queries)}] {qid} ({cat:15s}) -> {hit_flag} [{ver_flag}] in {dur:6.1f}ms ({tc} calls, {bt} B)")

        summary_a = calculate_summary_3b("Baseline A (LearningOS official)", evals_a)
        results_data["baseline_a"] = {
            "summary": summary_a.__dict__,
            "queries": [e.__dict__ for e in evals_a]
        }

    if args.arm in ("all", "baseline_b"):
        print("\n" + "=" * 60)
        print("RUNNING BASELINE B: Direct Lexical Grep over Text Cache")
        print("=" * 60)
        evals_b: list[QueryEvaluation] = []
        for i, q in enumerate(queries, 1):
            qid = q["id"]
            cat = q["category"]
            cands, tc, bt, dur, ver = eval_b.run_query(q)
            q_eval = evaluate_query_3b(
                query_entry=q,
                retrieved_candidates=cands,
                tool_calls=tc,
                bytes_transferred=bt,
                t_sql_ms=0.0,
                t_retrieval_e2e_ms=dur,
                verified_span_success=ver
            )
            evals_b.append(q_eval)
            hit_flag = "✓ Strict@1" if q_eval.strict_hit_at_1 else ("✓ Top@3" if q_eval.topical_hit_at_3 else ("✓ Top@5" if q_eval.topical_hit_at_5 else "✗ Miss"))
            ver_flag = "✓ Ver" if ver else "–"
            print(f"[{i:02d}/{len(queries)}] {qid} ({cat:15s}) -> {hit_flag} [{ver_flag}] in {dur:6.1f}ms ({tc} calls, {bt} B)")

        summary_b = calculate_summary_3b("Baseline B (Direct lexical grep)", evals_b)
        results_data["baseline_b"] = {
            "summary": summary_b.__dict__,
            "queries": [e.__dict__ for e in evals_b]
        }

    # Print summary comparison table
    print("\n" + "=" * 80)
    print("BASELINE EVALUATION SUMMARY RESULTS")
    print("=" * 80)
    headers = ["Metric", "Baseline A (Official LearningOS)", "Baseline B (Lexical Grep)"]
    row_fmt = "{:<32} | {:<28} | {:<28}"
    print(row_fmt.format(*headers))
    print("-" * 92)

    def sval(arm_key, field_name, is_pct=False, is_ms=False):
        if arm_key not in results_data:
            return "N/A"
        val = results_data[arm_key]["summary"][field_name]
        if is_pct:
            return f"{val * 100:.1f} %"
        if is_ms:
            return f"{val:.1f} ms"
        if isinstance(val, float):
            return f"{val:.2f}"
        return str(val)

    metrics = [
        ("Answerable Queries", "answerable_queries", False, False),
        ("Unanswerable Queries", "unanswerable_queries", False, False),
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
        ("Unanswerable Accuracy", "unanswerable_accuracy", True, False),
        ("Unanswerable FP Rate", "unanswerable_false_positive_rate", True, False),
        ("Avg Tool Calls per Query", "avg_tool_calls", False, False),
        ("Avg Bytes Transferred", "avg_bytes_transferred", False, False),
        ("Mean Retrieval E2E Latency", "t_retrieval_e2e_mean_ms", False, True),
        ("Median (P50) E2E Latency", "t_retrieval_e2e_p50_ms", False, True),
        ("P95 E2E Latency", "t_retrieval_e2e_p95_ms", False, True),
    ]

    for label, field_key, is_pct, is_ms in metrics:
        print(row_fmt.format(label, sval("baseline_a", field_key, is_pct, is_ms), sval("baseline_b", field_key, is_pct, is_ms)))

    print("=" * 92)

    if args.json_out:
        out_p = Path(args.json_out)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        with open(out_p, "w", encoding="utf-8") as f:
            json.dump(results_data, f, indent=2, sort_keys=True)
        print(f"\nRaw results exported to {out_p}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
