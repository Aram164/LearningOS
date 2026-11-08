#!/usr/bin/env python3
"""FTS5 Query & Benchmark Runner for LearningOS Material Search Research Spike.

Evaluates three FTS5 tokenizer arms against questions_dev.yaml:
1. unicode61: standard word tokenization with diacritic removal
2. prefix: unicode61 with prefix matching policy (term*)
3. trigram: 3-gram substring matching

Metrics collected:
- Exact cold & warm query latency (mean, P50, P95)
- Recall@1, Recall@3, Recall@5
- MRR (Mean Reciprocal Rank)
- False Source Rate (% queries where top hit is an unrelated document)
- Evidence Verification Rate (authoritative verification via material.span)
- Unanswerable rejection accuracy
- Tool calls & payload bytes transferred

Strictly isolated under workbench/material_search_eval/.
Never modifies Core, schemas, or canonical records.
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
from eval_metrics import evaluate_query, calculate_summary, BenchmarkSummary, QueryEvaluation

INDICES_DIR = SCRIPT_DIR / "indices"
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


def sanitize_query_unicode61(raw_q: str) -> str:
    """Sanitize and format query for standard FTS5 unicode61.
    
    Generates exact phrase boost OR conjunct terms OR disjunct terms.
    """
    clean = re.sub(r"[^\w\s]", " ", raw_q).strip()
    words = [w for w in clean.split() if len(w) > 0]
    if not words:
        return '""'
    if len(words) == 1:
        return f'"{words[0]}"'
    exact_phrase = f'"{clean}"'
    and_terms = " AND ".join(f'"{w}"' for w in words)
    or_terms = " OR ".join(f'"{w}"' for w in words)
    return f"{exact_phrase} OR ({and_terms}) OR ({or_terms})"


def sanitize_query_prefix(raw_q: str) -> str:
    """Sanitize and format query for FTS5 with prefix matching (term*)."""
    clean = re.sub(r"[^\w\s]", " ", raw_q).strip()
    words = [w for w in clean.split() if len(w) > 0]
    if not words:
        return '""'
    if len(words) == 1:
        return f'"{words[0]}"*'
    exact_phrase = f'"{clean}"'
    and_prefix = " AND ".join(f'"{w}"*' for w in words)
    or_prefix = " OR ".join(f'"{w}"*' for w in words)
    return f"{exact_phrase} OR ({and_prefix}) OR ({or_prefix})"


def sanitize_query_trigram(raw_q: str) -> str:
    """Sanitize and format query for FTS5 trigram tokenizer.
    
    Trigram requires tokens of length >= 3.
    """
    clean = re.sub(r"[^\w\s]", " ", raw_q).strip()
    words = [w for w in clean.split() if len(w) >= 3]
    if not words:
        if len(clean) >= 3:
            return f'"{clean[:10]}"'
        return '""'
    if len(words) == 1:
        return f'"{words[0]}"'
    exact_phrase = f'"{clean}"' if len(clean) >= 3 else ""
    and_terms = " AND ".join(f'"{w}"' for w in words)
    or_terms = " OR ".join(f'"{w}"' for w in words)
    if exact_phrase:
        return f"{exact_phrase} OR ({and_terms}) OR ({or_terms})"
    return f"({and_terms}) OR ({or_terms})"


class FTS5ArmEvaluator:
    """Evaluates an FTS5 search arm over questions_dev.yaml."""

    def __init__(
        self,
        arm_name: str,
        db_path: Path,
        query_sanitizer,
        repo,
        sha_to_route: dict[str, tuple[str, str]]
    ):
        self.arm_name = arm_name
        self.db_path = db_path
        self.query_sanitizer = query_sanitizer
        self.repo = repo
        self.sha_to_route = sha_to_route

        # Connect strictly with read-only URI mode
        uri = f"file:{db_path.resolve()}?mode=ro"
        self.con = sqlite3.connect(uri, uri=True)
        self.cur = self.con.cursor()

    def run_query(self, query_entry: dict[str, Any]) -> dict[str, Any]:
        raw_query = query_entry.get("query") or query_entry.get("question")
        expected_status = query_entry.get("expected_status", "answerable")
        targets = query_entry.get("targets", [])

        fts_query = self.query_sanitizer(raw_query)

        # 1. Measure Cold Query Latency
        t0_cold = time.perf_counter()
        candidates = []
        try:
            if fts_query != '""':
                sql = """
                SELECT source_sha256, page_no, source_id, title,
                       bm25(material_fts) AS score,
                       snippet(material_fts, 4, '[', ']', ' … ', 20) AS excerpt
                FROM material_fts
                WHERE material_fts MATCH ?
                ORDER BY rank
                LIMIT 5;
                """
                self.cur.execute(sql, (fts_query,))
                rows = self.cur.fetchall()
                for r in rows:
                    candidates.append({
                        "source_sha256": r[0],
                        "physical_page": int(r[1]),
                        "source_id": r[2],
                        "title": r[3],
                        "score": float(r[4]),
                        "snippet_chars": len(r[5]) if r[5] else 0
                    })
        except Exception as e:
            # e.g. syntax error or empty
            pass
        cold_lat_ms = (time.perf_counter() - t0_cold) * 1000.0

        # 2. Measure Warm Query Latency (average of 3 repeated runs)
        warm_runs = []
        for _ in range(3):
            t0_w = time.perf_counter()
            try:
                if fts_query != '""':
                    self.cur.execute(sql, (fts_query,))
                    _ = self.cur.fetchall()
            except Exception:
                pass
            warm_runs.append((time.perf_counter() - t0_w) * 1000.0)
        warm_lat_ms = sum(warm_runs) / len(warm_runs)

        # 3. Simulated Agent Evidence Acquisition
        tool_calls = 1  # 1 tool call for the search query
        bytes_transferred = len(json.dumps(candidates).encode("utf-8"))
        verified_evidence = False

        target_quotes = [t["evidence_quote"] for t in targets]

        for cand in candidates[:3]:
            sha = cand["source_sha256"]
            page = cand["physical_page"]
            route_binding = self.sha_to_route.get(sha)

            if route_binding:
                # Call material.span via OpContext
                tool_calls += 1
                uid, rid = route_binding
                span_req = {
                    "unit_id": uid,
                    "route_id": rid,
                    "pages": f"pdf pp. {page}",
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
                p_file = CACHE_DIR / sha / f"pp-{page:04d}.txt"
                if p_file.exists():
                    try:
                        raw = p_file.read_text(encoding="utf-8", errors="ignore")
                        for tq in target_quotes:
                            if norm(tq) in norm(raw):
                                verified_evidence = True
                    except OSError:
                        pass

            if verified_evidence:
                break

        # Check multi-target / topical match as well
        target_pairs = {(t["source_sha256"], int(t["physical_page"])) for t in targets}
        retrieval_hit = any((c["source_sha256"], c["physical_page"]) in target_pairs for c in candidates[:5])

        return {
            "query_id": query_entry["id"],
            "query": raw_query,
            "fts_query": fts_query,
            "expected_status": expected_status,
            "candidates": candidates,
            "cold_latency_ms": cold_lat_ms,
            "warm_latency_ms": warm_lat_ms,
            "tool_calls": tool_calls,
            "bytes_transferred": bytes_transferred,
            "verified_evidence": verified_evidence,
            "retrieval_hit": retrieval_hit
        }

    def close(self):
        self.con.close()


def run_arm(
    arm_name: str,
    db_path: Path,
    sanitizer,
    questions: list[dict[str, Any]],
    repo,
    sha_to_route: dict[str, tuple[str, str]]
) -> tuple[BenchmarkSummary, list[dict[str, Any]]]:
    """Execute complete evaluation benchmark for one FTS5 arm."""
    print(f"\n--- Running Benchmark: {arm_name} ---")
    evaluator = FTS5ArmEvaluator(arm_name, db_path, sanitizer, repo, sha_to_route)

    query_evaluations: list[QueryEvaluation] = []
    raw_details: list[dict[str, Any]] = []

    for idx, q in enumerate(questions, start=1):
        res = evaluator.run_query(q)
        raw_details.append(res)

        q_eval = evaluate_query(
            query_entry=q,
            retrieved_candidates=res["candidates"],
            tool_calls=res["tool_calls"],
            bytes_transferred=res["bytes_transferred"],
            duration_ms=res["warm_latency_ms"],  # warm latency as standard query performance
            verified_span_success=res["verified_evidence"]
        )
        query_evaluations.append(q_eval)

        status_str = "HIT" if q_eval.hit_at_3 or q_eval.unanswerable_correctly_rejected else "MISS"
        print(f"[{idx:02d}/{len(questions):02d}] {q['id']} ({status_str}) cold: {res['cold_latency_ms']:.1f}ms, warm: {res['warm_latency_ms']:.1f}ms, top: {len(res['candidates'])} hits")

    evaluator.close()
    summary = calculate_summary(arm_name, query_evaluations)
    return summary, raw_details


def main():
    parser = argparse.ArgumentParser(description="Run FTS5 Material Search Benchmark")
    parser.add_argument("--arm", choices=["all", "unicode61", "prefix", "trigram"], default="all")
    args = parser.parse_args()

    print("Loading LearningOS repository context...")
    repo = load_repo(REPO_ROOT)
    sha_to_route = build_sha_route_map(repo)
    print(f"Mapped {len(sha_to_route)} material SHAs to authoritative unit routes.")

    questions = yaml.safe_load(QUESTIONS_DEV_FILE.read_text(encoding="utf-8"))
    print(f"Loaded {len(questions)} dev questions (Held-out strictly excluded).")

    arms_to_run = []
    if args.arm in ("all", "unicode61"):
        arms_to_run.append(("FTS5_unicode61", INDICES_DIR / "fts5_unicode61.sqlite3", sanitize_query_unicode61))
    if args.arm in ("all", "prefix"):
        arms_to_run.append(("FTS5_prefix", INDICES_DIR / "fts5_prefix.sqlite3", sanitize_query_prefix))
    if args.arm in ("all", "trigram"):
        arms_to_run.append(("FTS5_trigram", INDICES_DIR / "fts5_trigram.sqlite3", sanitize_query_trigram))

    all_summaries = {}
    all_details = {}

    for arm_name, db_file, sanitizer in arms_to_run:
        if not db_file.exists():
            print(f"ERROR: Database file {db_file} does not exist. Run fts5_builder.py first.")
            sys.exit(1)
        summary, details = run_arm(arm_name, db_file, sanitizer, questions, repo, sha_to_route)
        all_summaries[arm_name] = summary.__dict__
        all_details[arm_name] = details

    output_payload = {
        "timestamp": time.time(),
        "total_dev_questions": len(questions),
        "summaries": all_summaries,
        "details": all_details
    }

    out_file = SCRIPT_DIR / "fts5_spike_results.json"
    out_file.write_text(json.dumps(output_payload, indent=2), encoding="utf-8")
    print(f"\n==========================================")
    print(f"Benchmark run complete. Results saved to {out_file.name}")
    print(f"==========================================")
    for name, s in all_summaries.items():
        print(f"\nArm: {name}")
        print(f"  Recall@1: {s['recall_at_1']:.1%}")
        print(f"  Recall@3: {s['recall_at_3']:.1%}")
        print(f"  Recall@5: {s['recall_at_5']:.1%}")
        print(f"  MRR: {s['mrr']:.3f}")
        print(f"  Verified Evidence: {s['verified_evidence_rate']:.1%}")
        print(f"  False Source Rate: {s['false_source_rate']:.1%}")
        print(f"  Unanswerable Accuracy: {s['unanswerable_accuracy']:.1%}")
        print(f"  Latency P50: {s['latency_p50_ms']:.2f} ms (Mean: {s['latency_mean_ms']:.2f} ms, P95: {s['latency_p95_ms']:.2f} ms)")


if __name__ == "__main__":
    main()
