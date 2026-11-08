#!/usr/bin/env python3
"""Stage 3c Comprehensive Benchmark Runner for LearningOS Material Search.

Implements the Stage 3c Final Gate Protocol:
1. Target-Bound Evidence Verification (Audit Correction):
   - Only counts evidence as verified if the candidate page is an independently confirmed target.
   - Measures verified evidence at both @3 and @5.
   - Preserves legacy loose verification for exact historical audit.
2. Three-Level Decision Model:
   - Level 1: Candidates retrieved (BM25 matches).
   - Level 2: Target-bound evidence verified.
   - Level 3: Final Decision: "ANSWERABLE_WITH_EVIDENCE" vs "INSUFFICIENT_EVIDENCE_ABSTAIN".
3. Frozen Configuration:
   - Evaluates FTS5 Arm 2 (Tiered Stopwords) and Baseline B (Lexical Grep).
   - Strict read-only SQLite index connection.
   - Strictly isolated under workbench/material_search_eval/.
"""

from __future__ import annotations

import argparse
import hashlib
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
from eval_metrics import evaluate_query_3c, calculate_summary_3c, BenchmarkSummary, QueryEvaluation
from fts5_reranker import build_tiered_queries, is_index_or_toc_page

DB_FILE = SCRIPT_DIR / "indices" / "fts5_unicode61.sqlite3"
QUESTIONS_DEV_FILE = SCRIPT_DIR / "questions_dev.yaml"
QUESTIONS_HELDOUT_FILE = SCRIPT_DIR / "questions_heldout.yaml"
CACHE_DIR = REPO_ROOT / "generated" / "text-cache"


def norm(text: str) -> str:
    n = unicodedata.normalize("NFC", text)
    return " ".join(n.split()).lower()


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


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


class FTS5Arm2Evaluator:
    """Evaluates FTS5 Arm 2 (Tiered Stopwords)."""

    def __init__(self, repo, sha_to_route: dict[str, tuple[str, str]]):
        self.repo = repo
        self.sha_to_route = sha_to_route
        uri = f"file:{DB_FILE.resolve()}?mode=ro"
        self.con = sqlite3.connect(uri, uri=True)
        self.cur = self.con.cursor()

    def query_sqlite(self, raw_query: str) -> tuple[list[dict[str, Any]], float]:
        t0 = time.perf_counter()
        raw_candidates = []
        seen_keys = set()

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
                        raw_candidates.append({
                            "source_sha256": r[0],
                            "physical_page": int(r[1]),
                            "source_id": r[2],
                            "title": r[3],
                            "score": float(r[4]),
                            "_body": r[5],
                            "snippet": r[6],
                            "tier": tier_name
                        })
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
        final_candidates = raw_candidates[:5]

        # Step 2: Authoritative Evidence Verification via material.span
        tool_calls = 1  # 1 call for search query
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

            if is_index_or_toc_page(cand.get("_body", "")):
                is_index_detected = True

            extracted_text = ""
            if route_binding:
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
                span_bytes = len(json.dumps(span_data, default=str).encode("utf-8"))
                bytes_transferred += span_bytes

                if isinstance(span_data, dict):
                    spans = span_data.get("spans", [])
                    extracted_text = " ".join(sp.get("excerpt", "") for sp in spans)
            else:
                if is_target_page:
                    target_route_unmapped = True
                p_file = CACHE_DIR / sha / f"pp-{page:04d}.txt"
                if p_file.exists():
                    try:
                        extracted_text = p_file.read_text(encoding="utf-8", errors="ignore")
                    except OSError:
                        extracted_text = ""

            # Check verification
            norm_extracted = norm(extracted_text)
            matches_any_quote = any(norm(tq) in norm_extracted for tq in target_quotes) if target_quotes else False

            # Diagnostic: legacy loose verification (did any top 3 hit match quote)
            if idx <= 3 and matches_any_quote:
                legacy_loose_verified = True

            # Rigorous Target-Bound Verification: Candidate MUST be a confirmed target
            if is_target_page and matches_any_quote:
                if idx <= 3:
                    target_verified_at_3 = True
                if idx <= 5:
                    target_verified_at_5 = True

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
            "target_verified_at_3": target_verified_at_3,
            "target_verified_at_5": target_verified_at_5,
            "legacy_loose_verified": legacy_loose_verified,
            "target_route_unmapped": target_route_unmapped,
            "is_index_detected": is_index_detected
        }

    def close(self):
        self.con.close()


class BaselineBEvaluator:
    """Evaluates Baseline B (Direct Lexical Grep over text cache)."""

    def __init__(self, repo, sha_to_route: dict[str, tuple[str, str]]):
        self.repo = repo
        self.sha_to_route = sha_to_route
        self.cache_dir = CACHE_DIR

        # Index all cached text files
        self.index_entries = []
        for d in sorted(self.cache_dir.iterdir()):
            if not d.is_dir():
                continue
            sha = d.name
            for p in sorted(d.glob("pp-*.txt")):
                page_no = int(p.stem.split("-")[1])
                self.index_entries.append((sha, page_no, p))

    def run_query(self, query_entry: dict[str, Any]) -> dict[str, Any]:
        t0_e2e = time.perf_counter()
        raw_query = query_entry.get("query") or query_entry.get("question")
        expected_status = query_entry.get("expected_status", "answerable")
        all_targets = query_entry.get("targets", [])

        tool_calls = 0
        bytes_transferred = 0

        q_terms = [t for t in norm(raw_query).split() if len(t) > 1]
        exact_phrase = norm(raw_query)

        matches = []
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

        matches.sort(key=lambda x: -x[0])

        candidates = []
        for score, sha, page_no, snippet in matches[:5]:
            candidates.append({
                "source_sha256": sha,
                "physical_page": page_no,
                "score": score,
                "snippet_chars": len(snippet[:100])
            })

        bytes_transferred += len(json.dumps(candidates).encode("utf-8"))

        target_verified_at_3 = False
        target_verified_at_5 = False
        legacy_loose_verified = False
        target_route_unmapped = False
        is_index_detected = False

        topical_pairs = {(t["source_sha256"], int(t["physical_page"])) for t in all_targets}
        target_quotes = [t["evidence_quote"] for t in all_targets if t.get("evidence_quote")]

        for idx, cand in enumerate(candidates, start=1):
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
                    "extract": True
                }
                ctx_span = OpContext(root=REPO_ROOT, operation="material.span", channel="cli", invocation="query", gateway=None)
                try:
                    span_res = REGISTRY["material.span"].handler(ctx_span, span_req)
                    span_data = span_res.payload if span_res else {}
                except Exception:
                    span_data = {}
                span_bytes = len(json.dumps(span_data, default=str).encode("utf-8"))
                bytes_transferred += span_bytes

                if isinstance(span_data, dict):
                    spans = span_data.get("spans", [])
                    extracted_text = " ".join(sp.get("excerpt", "") for sp in spans)
            else:
                if is_target_page:
                    target_route_unmapped = True
                p_file = self.cache_dir / sha / f"pp-{page:04d}.txt"
                if p_file.exists():
                    try:
                        extracted_text = p_file.read_text(encoding="utf-8", errors="ignore")
                    except OSError:
                        extracted_text = ""

            norm_extracted = norm(extracted_text)
            matches_any_quote = any(norm(tq) in norm_extracted for tq in target_quotes) if target_quotes else False

            if idx <= 3 and matches_any_quote:
                legacy_loose_verified = True

            if is_target_page and matches_any_quote:
                if idx <= 3:
                    target_verified_at_3 = True
                if idx <= 5:
                    target_verified_at_5 = True

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
            "candidates": candidates,
            "t_sql_ms": 0.0,
            "t_retrieval_e2e_ms": t_retrieval_e2e_ms,
            "tool_calls": tool_calls,
            "bytes_transferred": bytes_transferred,
            "target_verified_at_3": target_verified_at_3,
            "target_verified_at_5": target_verified_at_5,
            "legacy_loose_verified": legacy_loose_verified,
            "target_route_unmapped": target_route_unmapped,
            "is_index_detected": is_index_detected
        }


def run_evaluation(
    evaluator,
    arm_name: str,
    questions: list[dict[str, Any]]
) -> tuple[BenchmarkSummary, list[QueryEvaluation]]:
    evaluations: list[QueryEvaluation] = []
    print(f"\nEvaluating {arm_name} across {len(questions)} queries...")

    for idx, q in enumerate(questions, start=1):
        res = evaluator.run_query(q)
        q_eval = evaluate_query_3c(
            query_entry=q,
            retrieved_candidates=res["candidates"],
            tool_calls=res["tool_calls"],
            bytes_transferred=res["bytes_transferred"],
            t_sql_ms=res["t_sql_ms"],
            t_retrieval_e2e_ms=res["t_retrieval_e2e_ms"],
            target_verified_at_3=res["target_verified_at_3"],
            target_verified_at_5=res["target_verified_at_5"],
            legacy_loose_verified=res["legacy_loose_verified"],
            route_unmapped_for_target=res["target_route_unmapped"],
            is_index_page=res["is_index_detected"]
        )
        evaluations.append(q_eval)

        ret_stat = q_eval.retrieval_status
        evi_stat = q_eval.evidence_status
        hit_str = "✓ Top@3" if q_eval.topical_hit_at_3 else ("✓ Top@5" if q_eval.topical_hit_at_5 else "✗ Miss")
        ver_str = "✓ Ver@3" if q_eval.verified_target_evidence_at_3 else ("✓ Ver@5" if q_eval.verified_target_evidence_at_5 else "–")
        print(f"[{idx:02d}/{len(questions):02d}] {q['id']:10s} -> {hit_str:8s} [{ver_str:6s}] [Ret:{ret_stat:18s} Evi:{evi_stat:18s}] in {res['t_retrieval_e2e_ms']:5.1f}ms")

    summary = calculate_summary_3c(arm_name, evaluations)
    return summary, evaluations


def print_summary_table(arm_names: list[str], results: dict[str, dict[str, Any]]):
    headers = ["Metric"] + arm_names
    row_fmt = "{:<36} " + " | {:<16}" * len(arm_names)
    print("\n" + row_fmt.format(*headers))
    print("-" * (39 + 19 * len(arm_names)))

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
        ("Target-Bound Verified Evid@3", "verified_target_evidence_rate_at_3", True, False),
        ("Target-Bound Verified Evid@5", "verified_target_evidence_rate_at_5", True, False),
        ("Legacy Loose Verified Rate", "legacy_loose_verified_rate", True, False),
        ("False Source Rate", "false_source_rate", True, False),
        ("Unanswerable FP Rate", "unanswerable_false_positive_rate", True, False),
        ("Level 3 Abstention Accuracy", "level_3_abstention_accuracy", True, False),
        ("Avg Tool Calls", "avg_tool_calls", False, False),
        ("Avg Bytes Transferred", "avg_bytes_transferred", False, False),
        ("t_sql_ms P50", "t_sql_p50_ms", False, True),
        ("t_retrieval_e2e_ms P50", "t_retrieval_e2e_p50_ms", False, True),
        ("t_retrieval_e2e_ms P95", "t_retrieval_e2e_p95_ms", False, True),
    ]

    for label, key, is_p, is_m in metrics:
        vals = [sval(name, key, is_p, is_m) for name in arm_names]
        print(row_fmt.format(label, *vals))


def main():
    parser = argparse.ArgumentParser(description="Stage 3c Benchmark Runner")
    parser.add_argument("--dataset", choices=["dev", "heldout", "both"], default="dev")
    args = parser.parse_args()

    print("Loading LearningOS repository context...")
    repo = load_repo(REPO_ROOT)
    sha_to_route = build_sha_route_map(repo)
    print(f"Mapped {len(sha_to_route)} material SHAs to authoritative unit routes.")

    datasets = []
    if args.dataset in ("dev", "both"):
        q_dev = yaml.safe_load(QUESTIONS_DEV_FILE.read_text(encoding="utf-8"))
        datasets.append(("dev", QUESTIONS_DEV_FILE, q_dev))
    if args.dataset in ("heldout", "both"):
        q_heldout = yaml.safe_load(QUESTIONS_HELDOUT_FILE.read_text(encoding="utf-8"))
        datasets.append(("heldout", QUESTIONS_HELDOUT_FILE, q_heldout))

    for d_name, d_file, questions in datasets:
        print(f"\n================================================================================")
        print(f"STAGE 3C EVALUATION ON DATASET: {d_name.upper()} ({len(questions)} queries)")
        print(f"File: {d_file.name} | SHA-256: {file_sha256(d_file)}")
        print(f"================================================================================")

        results = {}

        # 1. Baseline B
        base_b = BaselineBEvaluator(repo, sha_to_route)
        summary_b, evals_b = run_evaluation(base_b, "Baseline_B_Grep", questions)
        results["Baseline_B_Grep"] = {
            "summary": summary_b.__dict__,
            "evaluations": [e.__dict__ for e in evals_b]
        }

        # 2. FTS5 Arm 2
        fts5_evaluator = FTS5Arm2Evaluator(repo, sha_to_route)
        summary_fts5, evals_fts5 = run_evaluation(fts5_evaluator, "FTS5_Arm2_Tiered", questions)
        fts5_evaluator.close()
        results["FTS5_Arm2_Tiered"] = {
            "summary": summary_fts5.__dict__,
            "evaluations": [e.__dict__ for e in evals_fts5]
        }

        # Print side-by-side table
        print_summary_table(["Baseline_B_Grep", "FTS5_Arm2_Tiered"], results)

        out_file = SCRIPT_DIR / f"stage_3c_results_{d_name}.json"
        out_file.write_text(json.dumps(results, indent=2), encoding="utf-8")
        print(f"\nResults exported to: {out_file.name}")


if __name__ == "__main__":
    main()
