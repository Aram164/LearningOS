#!/usr/bin/env python3
"""Run evaluation using production search logic (execute_search).

Evaluates search and retrieval against LearningOS evaluation question sets.
Supports FTS5 (via learning_os.store.materials.search_index.execute_search)
and the Baseline B scan comparator (from fts5_runner_3c.py).
Never stores full-text excerpts or body contents in JSON output.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import pathlib
import shutil
import sys
import tempfile
import time
import unicodedata
from typing import Any

SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent
TOOLS_DIR = REPO_ROOT / "tools"

if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import yaml
from eval_metrics import calculate_summary_3c, evaluate_query_3c
from fts5_reranker import is_index_or_toc_page
from fts5_runner_3c import BaselineBEvaluator, build_sha_route_map
from learning_os.app.context import OpContext
from learning_os.app.registry import REGISTRY
import learning_os.app.handlers  # noqa: F401
from learning_os.domain.material_refs import unit_routes
from learning_os.store.loading import load_repo
from learning_os.store.materials import search_index as prod
from learning_os.store.materials.resolution import resolve_route_material_files, sha256_file


def norm(text: str) -> str:
    n = unicodedata.normalize("NFC", text)
    return " ".join(n.split()).lower()


def mcnemar_exact(b: int, c: int) -> float:
    """Exact two-sided McNemar test using Binomial distribution."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    p_val = sum(math.comb(n, i) for i in range(k + 1)) * (0.5**n) * 2.0
    return min(1.0, float(p_val))


class BaselineAEvaluator:
    """Evaluates Baseline A: The existing official LearningOS retrieval path."""

    def __init__(self, repo, repo_root: pathlib.Path):
        self.repo = repo
        self.repo_root = repo_root
        self.routes_catalog: list[dict[str, Any]] = []
        for unit_id, unit in repo.units.items():
            sm = repo.module_source_maps.get(unit.module_id)
            if not sm:
                continue
            for r in unit_routes(sm, unit.module_id, unit.id):
                files = resolve_route_material_files(repo, r)
                file_shas = [sha256_file(pathlib.Path(f.path)).removeprefix("sha256:") for f in files]
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

    def run_query(self, query_entry: dict[str, Any]) -> dict[str, Any]:
        t0_e2e = time.perf_counter()
        raw_query = query_entry.get("query") or query_entry.get("question")
        expected_status = query_entry.get("expected_status", "answerable")
        all_targets = query_entry.get("targets", [])

        tool_calls = 0
        bytes_transferred = 0
        candidates: list[dict[str, Any]] = []
        verified_evidence = False

        # Step 1: Run material.context
        tool_calls += 1
        req_payload = {
            "query": raw_query,
            "limit": 10
        }
        ctx = OpContext(root=self.repo_root, operation="material.context", channel="cli", invocation="query", gateway=None)
        try:
            res_result = REGISTRY["material.context"].handler(ctx, req_payload)
            res_data = res_result.payload if res_result else {}
        except Exception:
            res_data = {}
        ctx_bytes = len(json.dumps(res_data, default=str).encode("utf-8"))
        bytes_transferred += ctx_bytes

        found_routes: list[tuple[str, str]] = []
        if isinstance(res_data, dict):
            items = res_data.get("items", [])
            for item in items:
                rid = item.get("route_id")
                uid = item.get("unit_id")
                if rid and uid:
                    found_routes.append((uid, rid))

        # Step 2: If material.context found no items, emulate agent scanning route locators
        if not found_routes:
            q_terms = [t for t in norm(raw_query).split() if len(t) > 2]
            scored_routes = []
            for r in self.routes_catalog:
                score = sum(1 for term in q_terms if term in r["searchable_text"])
                if score > 0:
                    scored_routes.append((score, r["unit_id"], r["route_id"]))
            scored_routes.sort(key=lambda x: -x[0])
            found_routes = [(uid, rid) for _, uid, rid in scored_routes[:3]]

        # Step 3: Call material.span for top candidate routes
        target_quotes = [t["evidence_quote"] for t in all_targets if t.get("evidence_quote")]
        topical_pairs = {(t["source_sha256"], int(t["physical_page"])) for t in all_targets}

        target_verified_at_3 = False
        target_verified_at_5 = False

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
            span_bytes = len(json.dumps(span_data, default=str).encode("utf-8"))
            bytes_transferred += span_bytes

            if isinstance(span_data, dict):
                spans = span_data.get("spans", [])
                for sp in spans:
                    sha = sp.get("file_sha256", "").removeprefix("sha256:")
                    excerpt = sp.get("excerpt", "")
                    pages = sp.get("pages", [])

                    for p in pages:
                        candidates.append({
                            "source_sha256": sha,
                            "physical_page": p,
                            "score": 1.0,
                            "snippet_chars": len(excerpt[:100]),
                            "is_mapped": True,
                            "title": ""
                        })

                    for tq in target_quotes:
                        if norm(tq) in norm(excerpt):
                            verified_evidence = True

            if verified_evidence:
                break

        for idx, cand in enumerate(candidates[:5], start=1):
            cand_pair = (cand["source_sha256"], cand["physical_page"])
            if cand_pair in topical_pairs and verified_evidence:
                if idx <= 3:
                    target_verified_at_3 = True
                if idx <= 5:
                    target_verified_at_5 = True

        t_e2e_ms = (time.perf_counter() - t0_e2e) * 1000.0

        return {
            "query_id": query_entry["id"],
            "query": raw_query,
            "expected_status": expected_status,
            "candidates": candidates[:5],
            "t_sql_ms": 0.0,
            "t_retrieval_e2e_ms": t_e2e_ms,
            "tool_calls": tool_calls,
            "bytes_transferred": bytes_transferred,
            "target_verified_at_3": target_verified_at_3,
            "target_verified_at_5": target_verified_at_5,
            "legacy_loose_verified": verified_evidence,
            "target_route_unmapped": False,
            "is_index_detected": False,
        }


class ProductionFTS5Evaluator:
    """Evaluates search using production execute_search."""

    def __init__(
        self,
        repo,
        repo_root: pathlib.Path,
        sha_to_route: dict[str, tuple[str, str]],
        index_file: pathlib.Path | None = None,
    ):
        self.repo = repo
        self.repo_root = repo_root
        self.sha_to_route = sha_to_route
        self.index_file = index_file

    def run_query(self, query_entry: dict[str, Any]) -> dict[str, Any]:
        t0_e2e = time.perf_counter()
        raw_query = query_entry.get("query") or query_entry.get("question")
        expected_status = query_entry.get("expected_status", "answerable")
        all_targets = query_entry.get("targets", [])

        # Execute search through production entrypoint
        t0_sql = time.perf_counter()
        search_res = prod.execute_search(
            self.repo_root,
            raw_query,
            limit=5,
            repo=self.repo,
            index_path=self.index_file,
        )
        t_sql_ms = (time.perf_counter() - t0_sql) * 1000.0

        hits = search_res.hits if search_res.status == "ok" else []

        final_candidates = []
        for h in hits:
            # Handle both dict and object hits
            if isinstance(h, dict):
                sha = str(h.get("sha256") or h.get("source_sha256", ""))
                page = int(h.get("page") or h.get("physical_page", 0))
                score = float(h.get("score", 0.0))
                snippet = str(h.get("snippet", ""))
                is_mapped = bool(h.get("is_mapped", False))
                title = str(h.get("title", ""))
            else:
                sha = str(getattr(h, "sha256", None) or getattr(h, "source_sha256", ""))
                page = int(getattr(h, "page", None) or getattr(h, "physical_page", 0))
                score = float(getattr(h, "score", 0.0))
                snippet = str(getattr(h, "snippet", ""))
                is_mapped = bool(getattr(h, "is_mapped", False))
                title = str(getattr(h, "title", ""))

            final_candidates.append(
                {
                    "source_sha256": sha,
                    "physical_page": page,
                    "score": score,
                    "snippet_chars": len(snippet) if snippet else 0,
                    "is_mapped": is_mapped,
                    "title": title,
                }
            )

        tool_calls = 1
        bytes_transferred = len(json.dumps(final_candidates, default=str).encode("utf-8"))

        target_verified_at_3 = False
        target_verified_at_5 = False
        legacy_loose_verified = False
        target_route_unmapped = False
        is_index_detected = False

        topical_pairs = {(t["source_sha256"], int(t["physical_page"])) for t in all_targets}
        target_quotes = [t["evidence_quote"] for t in all_targets if t.get("evidence_quote")]

        for idx, cand in enumerate(final_candidates, start=1):
            sha = cand["source_sha256"]
            page = cand["physical_page"]
            cand_pair = (sha, page)
            is_target_page = cand_pair in topical_pairs
            route_binding = self.sha_to_route.get(sha)

            extracted_text = ""
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
                    root=self.repo_root,
                    operation="material.span",
                    channel="cli",
                    invocation="query",
                    gateway=None,
                )
                try:
                    span_res = REGISTRY["material.span"].handler(ctx_span, span_req)
                    span_data = span_res.payload if span_res else {}
                    spans = span_data.get("spans", [])
                    extracted_text = " ".join(sp.get("excerpt", "") for sp in spans)
                    bytes_transferred += len(json.dumps(span_data, default=str).encode("utf-8"))
                except Exception:
                    pass
            else:
                if is_target_page:
                    target_route_unmapped = True

            norm_extracted = norm(extracted_text)
            matches_any_quote = (
                any(norm(tq) in norm_extracted for tq in target_quotes) if target_quotes else False
            )

            if idx <= 3 and matches_any_quote:
                legacy_loose_verified = True
            if is_target_page and matches_any_quote:
                if idx <= 3:
                    target_verified_at_3 = True
                if idx <= 5:
                    target_verified_at_5 = True

        t_retrieval_e2e_ms = (time.perf_counter() - t0_e2e) * 1000.0

        return {
            "query_id": query_entry["id"],
            "query": raw_query,
            "expected_status": expected_status,
            "candidates": final_candidates,
            "t_sql_ms": t_sql_ms,
            "t_retrieval_e2e_ms": t_retrieval_e2e_ms,
            "tool_calls": tool_calls,
            "bytes_transferred": bytes_transferred,
            "target_verified_at_3": target_verified_at_3,
            "target_verified_at_5": target_verified_at_5,
            "legacy_loose_verified": legacy_loose_verified,
            "target_route_unmapped": target_route_unmapped,
            "is_index_detected": is_index_detected,
        }

    def close(self) -> None:
        pass


def run_benchmark(
    repo,
    repo_root: pathlib.Path,
    questions: list[dict[str, Any]],
    evaluator: Any,
    arm_name: str,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    evaluations = []
    query_eval_objs = []
    for q in questions:
        raw_res = evaluator.run_query(q)
        eval_obj = evaluate_query_3c(
            query_entry=q,
            retrieved_candidates=raw_res["candidates"],
            tool_calls=raw_res["tool_calls"],
            bytes_transferred=raw_res["bytes_transferred"],
            t_sql_ms=raw_res["t_sql_ms"],
            t_retrieval_e2e_ms=raw_res["t_retrieval_e2e_ms"],
            target_verified_at_3=raw_res["target_verified_at_3"],
            target_verified_at_5=raw_res["target_verified_at_5"],
            legacy_loose_verified=raw_res["legacy_loose_verified"],
            route_unmapped_for_target=raw_res["target_route_unmapped"],
            is_index_page=raw_res["is_index_detected"],
        )
        query_eval_objs.append(eval_obj)
        eval_dict = raw_res.copy()
        eval_dict.update(
            {
                "strict_hit_at_1": eval_obj.strict_hit_at_1,
                "strict_hit_at_3": eval_obj.strict_hit_at_3,
                "strict_hit_at_5": eval_obj.strict_hit_at_5,
                "strict_reciprocal_rank": eval_obj.strict_reciprocal_rank,
                "topical_hit_at_1": eval_obj.topical_hit_at_1,
                "topical_hit_at_3": eval_obj.topical_hit_at_3,
                "topical_hit_at_5": eval_obj.topical_hit_at_5,
                "topical_reciprocal_rank": eval_obj.topical_reciprocal_rank,
                "verified_evidence": eval_obj.verified_evidence,
                "false_source": eval_obj.false_source,
                "unanswerable_correctly_rejected": eval_obj.unanswerable_correctly_rejected,
                "level_1_candidates_found": eval_obj.level_1_candidates_found,
                "level_2_evidence_verified": eval_obj.level_2_evidence_verified,
                "level_3_decision": eval_obj.level_3_decision,
                "retrieval_status": eval_obj.retrieval_status,
                "evidence_status": eval_obj.evidence_status,
                "category": eval_obj.category,
            }
        )
        evaluations.append(eval_dict)

    summary = calculate_summary_3c(arm_name, query_eval_objs)
    return summary.__dict__, evaluations


def main() -> int:
    parser = argparse.ArgumentParser(description="Run production search benchmarks.")
    parser.add_argument("--repo-root", type=pathlib.Path, default=REPO_ROOT)
    parser.add_argument("--index", type=pathlib.Path, default=None, help="Explicit index file")
    parser.add_argument(
        "--dataset",
        choices=["dev", "heldout", "heldout_v2", "all"],
        default="dev",
        help="Dataset to evaluate",
    )
    parser.add_argument(
        "--arm", choices=["fts5", "grep", "baseline_a", "all"], default="all", help="Arm to run"
    )
    parser.add_argument("--json-out", type=pathlib.Path, default=None)
    parser.add_argument("--check-parity", action="store_true", help="Check parity vs 3C frozen top-5")
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    repo = load_repo(repo_root)
    sha_to_route = build_sha_route_map(repo)

    index_path = args.index
    if index_path is None and (SCRIPT_DIR / "indices" / "fts5_unicode61.sqlite3").exists():
        index_path = SCRIPT_DIR / "indices" / "fts5_unicode61.sqlite3"

    if args.check_parity:
        # Check parity with frozen stage 3c results
        ev = SCRIPT_DIR
        same_count = 0
        total_queries = 0
        evaluator = ProductionFTS5Evaluator(
            repo=repo,
            repo_root=repo_root,
            sha_to_route=sha_to_route,
            index_file=index_path,
        )
        try:
            for ds in ("dev", "heldout"):
                with open(ev / f"questions_{ds}.yaml") as f:
                    qs = yaml.safe_load(f)
                with open(ev / f"stage_3c_results_{ds}.json") as f:
                    stored = {e["query_id"]: e for e in json.load(f)["FTS5_Arm2_Tiered"]["evaluations"]}
                for q in qs:
                    total_queries += 1
                    raw_res = evaluator.run_query(q)
                    st = [(c["source_sha256"], int(c["physical_page"])) for c in stored[q["id"]]["candidates"]]
                    pr = [(c["source_sha256"], int(c["physical_page"])) for c in raw_res["candidates"]]
                    if st == pr:
                        same_count += 1
                    else:
                        print(f"Parity diff for {q['id']}: stored={st} vs prod={pr}")
        finally:
            evaluator.close()
        print(f"Frozen index parity check: {same_count}/{total_queries} exact top-5 matches.")
        return 0 if same_count == total_queries else 1

    datasets = ["dev", "heldout"] if args.dataset == "all" else [args.dataset]
    all_results = {}

    for ds in datasets:
        q_file = SCRIPT_DIR / f"questions_{ds}.yaml"
        if not q_file.exists():
            print(f"Dataset questions file not found: {q_file}", file=sys.stderr)
            continue
        with open(q_file, encoding="utf-8") as f:
            questions = yaml.safe_load(f)

        ds_results = {}

        if args.arm in ("fts5", "all"):
            evaluator = ProductionFTS5Evaluator(
                repo=repo,
                repo_root=repo_root,
                sha_to_route=sha_to_route,
                index_file=index_path,
            )
            try:
                summary, evals = run_benchmark(
                    repo, repo_root, questions, evaluator, f"FTS5_Production_{ds}"
                )
                ds_results["FTS5_Production"] = {"summary": summary, "evaluations": evals}
                print(
                    f"[{ds} | FTS5] Strict R@1: {summary['strict_recall_at_1']:.2f} | "
                    f"R@3: {summary['strict_recall_at_3']:.2f} | R@5: {summary['strict_recall_at_5']:.2f} | "
                    f"Topical R@5: {summary['topical_recall_at_5']:.2f}"
                )
            finally:
                evaluator.close()

        if args.arm in ("grep", "all"):
            evaluator = BaselineBEvaluator(repo=repo, sha_to_route=sha_to_route)
            try:
                summary, evals = run_benchmark(
                    repo, repo_root, questions, evaluator, f"Grep_Scan_{ds}"
                )
                ds_results["Baseline_B_Grep"] = {"summary": summary, "evaluations": evals}
                print(
                    f"[{ds} | Grep] Strict R@1: {summary['strict_recall_at_1']:.2f} | "
                    f"R@3: {summary['strict_recall_at_3']:.2f} | R@5: {summary['strict_recall_at_5']:.2f} | "
                    f"Topical R@5: {summary['topical_recall_at_5']:.2f}"
                )
            finally:
                pass

        if args.arm in ("baseline_a", "all"):
            eval_a = BaselineAEvaluator(repo=repo, repo_root=repo_root)
            try:
                summary, evals = run_benchmark(
                    repo, repo_root, questions, eval_a, f"Baseline_A_{ds}"
                )
                ds_results["Baseline_A_Official"] = {"summary": summary, "evaluations": evals}
                print(
                    f"[{ds} | Baseline A] Strict R@1: {summary['strict_recall_at_1']:.2f} | "
                    f"R@3: {summary['strict_recall_at_3']:.2f} | R@5: {summary['strict_recall_at_5']:.2f} | "
                    f"Topical R@5: {summary['topical_recall_at_5']:.2f}"
                )
            finally:
                pass

        if "FTS5_Production" in ds_results and "Baseline_B_Grep" in ds_results:
            fts5_evals = {e["query_id"]: e for e in ds_results["FTS5_Production"]["evaluations"]}
            grep_evals = {e["query_id"]: e for e in ds_results["Baseline_B_Grep"]["evaluations"]}
            b = 0
            c = 0
            both_hit = 0
            both_miss = 0
            for qid, fe in fts5_evals.items():
                if fe.get("expected_status") == "unanswerable":
                    continue
                ge = grep_evals.get(qid, {})
                f_hit = fe.get("strict_hit_at_5", False)
                g_hit = ge.get("strict_hit_at_5", False)
                if f_hit and not g_hit:
                    b += 1
                elif g_hit and not f_hit:
                    c += 1
                elif f_hit and g_hit:
                    both_hit += 1
                else:
                    both_miss += 1
            p_val = mcnemar_exact(b, c)
            print(
                f"[{ds} | McNemar] FTS5+ Grep-: {b} | Grep+ FTS5-: {c} | "
                f"Both+: {both_hit} | Both-: {both_miss} | Exact McNemar p-value: {p_val:.4f}"
            )
            ds_results["mcnemar"] = {
                "b_fts5_only": b,
                "c_grep_only": c,
                "both_hit": both_hit,
                "both_miss": both_miss,
                "p_value": p_val,
            }

        all_results[ds] = ds_results

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        with open(args.json_out, "w", encoding="utf-8") as f:
            json.dump(all_results, f, indent=2)

    if args.check_parity:
        # Check parity with frozen stage 3c results
        ev = SCRIPT_DIR
        same_count = 0
        total_queries = 0
        for ds in ("dev", "heldout"):
            with open(ev / f"questions_{ds}.yaml") as f:
                qs = yaml.safe_load(f)
            with open(ev / f"stage_3c_results_{ds}.json") as f:
                stored = {e["query_id"]: e for e in json.load(f)["FTS5_Arm2_Tiered"]["evaluations"]}
            evaluator = ProductionFTS5Evaluator(
                repo=repo,
                repo_root=repo_root,
                sha_to_route=sha_to_route,
                index_file=args.index or (SCRIPT_DIR / "indices" / "fts5_unicode61.sqlite3"),
            )
            try:
                for q in qs:
                    total_queries += 1
                    raw_res = evaluator.run_query(q)
                    st = [(c["source_sha256"], int(c["physical_page"])) for c in stored[q["id"]]["candidates"]]
                    pr = [(c["source_sha256"], int(c["physical_page"])) for c in raw_res["candidates"]]
                    if st == pr:
                        same_count += 1
                    else:
                        print(f"Parity diff for {q['id']}: stored={st} vs prod={pr}")
            finally:
                evaluator.close()
        print(f"Frozen index parity check: {same_count}/{total_queries} exact top-5 matches.")
        if same_count != total_queries:
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
