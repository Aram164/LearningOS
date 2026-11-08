"""Evaluation metrics for LearningOS Material Search benchmarks (Stage 3c).

Features:
- Dual-Target Metrics:
  1. Strict Target Match (original pre-designated primary target).
  2. Topical / Evidence Match (all independently verified legitimate targets).
- Two-Dimensional Failure Taxonomy:
  * Retrieval: FOUND, RANKING_MISS, NO_MATCH, WRONG_SOURCE, INDEX_PAGE_CONFUSION
  * Evidence: VERIFIED, ROUTE_UNMAPPED, EXTRACTOR_DIVERGENCE, SPAN_FAILURE, NOT_ATTEMPTED
- Target-Bound Evidence Verification (Audit Correction):
  * verified_target_evidence_at_3: Candidate in top 3 is an independently confirmed target AND its span verifies the evidence quote.
  * verified_target_evidence_at_5: Candidate in top 5 is an independently confirmed target AND its span verifies the evidence quote.
  * legacy_loose_verified: Any candidate in top 3 contained target quote substring (historical diagnostic).
- Three-Level Decision Model:
  * Level 1: Candidates retrieved (BM25 matches > 0).
  * Level 2: Substantive evidence verified (target-bound verified == True).
  * Level 3: Final Decision: "ANSWERABLE_WITH_EVIDENCE" vs "INSUFFICIENT_EVIDENCE_ABSTAIN".
- Exact Latency Separation:
  * t_sql_ms: Pure SQLite query execution time.
  * t_retrieval_e2e_ms: Complete deterministic search, ranking, route resolution, and span extraction.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class QueryEvaluation:
    query_id: str
    category: str
    expected_status: str  # "answerable" or "unanswerable"
    candidates: list[dict[str, Any]] = field(default_factory=list)
    tool_calls: int = 0
    bytes_transferred: int = 0
    t_sql_ms: float = 0.0
    t_retrieval_e2e_ms: float = 0.0

    # Strict target metrics (original single primary target)
    strict_hit_at_1: bool = False
    strict_hit_at_3: bool = False
    strict_hit_at_5: bool = False
    strict_reciprocal_rank: float = 0.0

    # Topical target metrics (all independently verified valid targets)
    topical_hit_at_1: bool = False
    topical_hit_at_3: bool = False
    topical_hit_at_5: bool = False
    topical_reciprocal_rank: float = 0.0

    # Target-Bound Evidence Verification (Stage 3c Rigorous Standard)
    verified_target_evidence_at_3: bool = False
    verified_target_evidence_at_5: bool = False
    verified_evidence: bool = False  # Bounded to verified_target_evidence_at_5
    legacy_loose_verified: bool = False  # For metric audit comparison

    # Quality & Reliability
    false_source: bool = False
    unanswerable_correctly_rejected: bool = False

    # Three-Level Decision Model
    level_1_candidates_found: bool = False
    level_2_evidence_verified: bool = False
    level_3_decision: str = "INSUFFICIENT_EVIDENCE_ABSTAIN"  # or "ANSWERABLE_WITH_EVIDENCE"

    # Orthogonal Taxonomy Dimensions
    retrieval_status: str = "NO_MATCH"  # FOUND, RANKING_MISS, NO_MATCH, WRONG_SOURCE, INDEX_PAGE_CONFUSION
    evidence_status: str = "NOT_ATTEMPTED"  # VERIFIED, ROUTE_UNMAPPED, EXTRACTOR_DIVERGENCE, SPAN_FAILURE, NOT_ATTEMPTED
    details: str = ""


@dataclass
class BenchmarkSummary:
    arm_name: str
    total_queries: int
    answerable_queries: int
    unanswerable_queries: int

    # Strict target metrics
    strict_recall_at_1: float
    strict_recall_at_3: float
    strict_recall_at_5: float
    strict_mrr: float

    # Topical target metrics
    topical_recall_at_1: float
    topical_recall_at_3: float
    topical_recall_at_5: float
    topical_mrr: float

    # Target-Bound Evidence Verification
    verified_target_evidence_rate_at_3: float
    verified_target_evidence_rate_at_5: float
    verified_evidence_rate: float  # Same as verified_target_evidence_rate_at_5
    legacy_loose_verified_rate: float

    # Precision & Unanswerables
    false_source_rate: float
    unanswerable_accuracy: float
    unanswerable_false_positive_rate: float
    unjustified_verified_rate: float

    # Three-Level Decision Model Summary
    level_1_retrieval_rate: float
    level_2_verification_rate: float
    level_3_abstention_accuracy: float  # % of unanswerable queries correctly resulting in INSUFFICIENT_EVIDENCE_ABSTAIN

    # Operations & Performance
    avg_tool_calls: float
    avg_bytes_transferred: float
    t_sql_mean_ms: float
    t_sql_p50_ms: float
    t_sql_p95_ms: float
    t_retrieval_e2e_mean_ms: float
    t_retrieval_e2e_p50_ms: float
    t_retrieval_e2e_p95_ms: float

    # Taxonomic Breakdown
    retrieval_breakdown: dict[str, int] = field(default_factory=dict)
    evidence_breakdown: dict[str, int] = field(default_factory=dict)
    per_category: dict[str, dict[str, float]] = field(default_factory=dict)


def evaluate_query_3c(
    query_entry: dict[str, Any],
    retrieved_candidates: list[dict[str, Any]],
    tool_calls: int,
    bytes_transferred: int,
    t_sql_ms: float,
    t_retrieval_e2e_ms: float,
    target_verified_at_3: bool = False,
    target_verified_at_5: bool = False,
    legacy_loose_verified: bool = False,
    route_unmapped_for_target: bool = False,
    is_index_page: bool = False
) -> QueryEvaluation:
    """Evaluate candidate rankings against primary and topical ground-truth targets."""
    qid = query_entry["id"]
    category = query_entry["category"]
    expected_status = query_entry.get("expected_status", "answerable")

    # Primary strict target: targets[0]
    all_targets = query_entry.get("targets", [])
    primary_target = all_targets[0] if all_targets else None

    # Topical targets: all targets in targets list (including alternatives)
    topical_pairs = {(t["source_sha256"], int(t["physical_page"])) for t in all_targets}
    topical_shas = {t["source_sha256"] for t in all_targets}

    strict_pairs = set()
    if primary_target:
        strict_pairs = {(primary_target["source_sha256"], int(primary_target["physical_page"]))}

    eval_res = QueryEvaluation(
        query_id=qid,
        category=category,
        expected_status=expected_status,
        candidates=retrieved_candidates,
        tool_calls=tool_calls,
        bytes_transferred=bytes_transferred,
        t_sql_ms=t_sql_ms,
        t_retrieval_e2e_ms=t_retrieval_e2e_ms,
        verified_target_evidence_at_3=target_verified_at_3,
        verified_target_evidence_at_5=target_verified_at_5,
        verified_evidence=target_verified_at_5,
        legacy_loose_verified=legacy_loose_verified,
        level_1_candidates_found=(len(retrieved_candidates) > 0),
        level_2_evidence_verified=target_verified_at_5,
        level_3_decision="ANSWERABLE_WITH_EVIDENCE" if target_verified_at_5 else "INSUFFICIENT_EVIDENCE_ABSTAIN"
    )

    if expected_status == "unanswerable":
        if not retrieved_candidates:
            eval_res.unanswerable_correctly_rejected = True
            eval_res.retrieval_status = "FOUND"
            eval_res.evidence_status = "NOT_ATTEMPTED"
        else:
            eval_res.unanswerable_correctly_rejected = False
            eval_res.false_source = True
            eval_res.retrieval_status = "WRONG_SOURCE"
            eval_res.evidence_status = "NOT_ATTEMPTED"
        return eval_res

    # 1. Evaluate Strict Target Rank
    strict_rank = 0
    for idx, cand in enumerate(retrieved_candidates[:5], start=1):
        pair = (cand.get("source_sha256"), int(cand.get("physical_page", -1)))
        if pair in strict_pairs:
            if strict_rank == 0:
                strict_rank = idx
            if idx == 1:
                eval_res.strict_hit_at_1 = True
            if idx <= 3:
                eval_res.strict_hit_at_3 = True
            if idx <= 5:
                eval_res.strict_hit_at_5 = True
    eval_res.strict_reciprocal_rank = (1.0 / strict_rank) if strict_rank > 0 else 0.0

    # 2. Evaluate Topical Target Rank
    topical_rank = 0
    for idx, cand in enumerate(retrieved_candidates[:5], start=1):
        pair = (cand.get("source_sha256"), int(cand.get("physical_page", -1)))
        if pair in topical_pairs:
            if topical_rank == 0:
                topical_rank = idx
            if idx == 1:
                eval_res.topical_hit_at_1 = True
            if idx <= 3:
                eval_res.topical_hit_at_3 = True
            if idx <= 5:
                eval_res.topical_hit_at_5 = True
    eval_res.topical_reciprocal_rank = (1.0 / topical_rank) if topical_rank > 0 else 0.0

    # 3. False Source Detection (top-1 hit source not among any valid topical sources)
    if retrieved_candidates:
        top_sha = retrieved_candidates[0].get("source_sha256")
        if top_sha not in topical_shas:
            eval_res.false_source = True

    # 4. Two-Dimensional Failure Taxonomy
    # Dimension A: Retrieval Status
    if eval_res.topical_hit_at_5:
        eval_res.retrieval_status = "FOUND"
    elif not retrieved_candidates:
        eval_res.retrieval_status = "NO_MATCH"
    elif is_index_page:
        eval_res.retrieval_status = "INDEX_PAGE_CONFUSION"
    else:
        cand_shas = {c.get("source_sha256") for c in retrieved_candidates[:5]}
        if cand_shas.intersection(topical_shas):
            eval_res.retrieval_status = "RANKING_MISS"
        else:
            eval_res.retrieval_status = "WRONG_SOURCE"

    # Dimension B: Evidence Status
    if target_verified_at_5:
        eval_res.evidence_status = "VERIFIED"
    elif not retrieved_candidates:
        eval_res.evidence_status = "NOT_ATTEMPTED"
    elif route_unmapped_for_target:
        eval_res.evidence_status = "ROUTE_UNMAPPED"
    elif eval_res.retrieval_status == "FOUND":
        eval_res.evidence_status = "EXTRACTOR_DIVERGENCE"
    else:
        eval_res.evidence_status = "NOT_ATTEMPTED"

    return eval_res


def calculate_summary_3c(arm_name: str, query_evals: list[QueryEvaluation]) -> BenchmarkSummary:
    """Aggregate query evaluations into a comprehensive Stage 3c BenchmarkSummary."""
    ans = [q for q in query_evals if q.expected_status == "answerable"]
    unans = [q for q in query_evals if q.expected_status == "unanswerable"]

    n_ans = len(ans)
    n_unans = len(unans)
    n_tot = len(query_evals)

    # Strict metrics
    s_r1 = (sum(1 for q in ans if q.strict_hit_at_1) / n_ans) if n_ans else 0.0
    s_r3 = (sum(1 for q in ans if q.strict_hit_at_3) / n_ans) if n_ans else 0.0
    s_r5 = (sum(1 for q in ans if q.strict_hit_at_5) / n_ans) if n_ans else 0.0
    s_mrr = (sum(q.strict_reciprocal_rank for q in ans) / n_ans) if n_ans else 0.0

    # Topical metrics
    t_r1 = (sum(1 for q in ans if q.topical_hit_at_1) / n_ans) if n_ans else 0.0
    t_r3 = (sum(1 for q in ans if q.topical_hit_at_3) / n_ans) if n_ans else 0.0
    t_r5 = (sum(1 for q in ans if q.topical_hit_at_5) / n_ans) if n_ans else 0.0
    t_mrr = (sum(q.topical_reciprocal_rank for q in ans) / n_ans) if n_ans else 0.0

    # Target-Bound Verified Evidence Rates
    ver_3 = (sum(1 for q in ans if q.verified_target_evidence_at_3) / n_ans) if n_ans else 0.0
    ver_5 = (sum(1 for q in ans if q.verified_target_evidence_at_5) / n_ans) if n_ans else 0.0
    legacy_ver = (sum(1 for q in ans if q.legacy_loose_verified) / n_ans) if n_ans else 0.0

    fsr = (sum(1 for q in ans if q.false_source) / n_ans) if n_ans else 0.0

    unans_acc = (sum(1 for q in unans if q.unanswerable_correctly_rejected) / n_unans) if n_unans else 0.0
    unans_fp = 1.0 - unans_acc
    unjustified_ver = (sum(1 for q in unans if q.verified_target_evidence_at_5) / n_unans) if n_unans else 0.0

    # Three-Level Model
    lvl1_rate = (sum(1 for q in ans if q.level_1_candidates_found) / n_ans) if n_ans else 0.0
    lvl2_rate = ver_5
    # For unanswerables: did Level 3 correctly decide INSUFFICIENT_EVIDENCE_ABSTAIN?
    lvl3_abstain_acc = (sum(1 for q in unans if q.level_3_decision == "INSUFFICIENT_EVIDENCE_ABSTAIN") / n_unans) if n_unans else 1.0

    # Latencies
    sql_durs = sorted(q.t_sql_ms for q in query_evals)
    sql_mean = (sum(sql_durs) / n_tot) if n_tot else 0.0
    sql_p50 = sql_durs[int(len(sql_durs) * 0.50)] if sql_durs else 0.0
    sql_p95 = sql_durs[int(len(sql_durs) * 0.95)] if sql_durs else 0.0

    e2e_durs = sorted(q.t_retrieval_e2e_ms for q in query_evals)
    e2e_mean = (sum(e2e_durs) / n_tot) if n_tot else 0.0
    e2e_p50 = e2e_durs[int(len(e2e_durs) * 0.50)] if e2e_durs else 0.0
    e2e_p95 = e2e_durs[int(len(e2e_durs) * 0.95)] if e2e_durs else 0.0

    # Operational
    calls = (sum(q.tool_calls for q in query_evals) / n_tot) if n_tot else 0.0
    bytes_trans = (sum(q.bytes_transferred for q in query_evals) / n_tot) if n_tot else 0.0

    # Taxonomic distributions
    ret_breakdown: dict[str, int] = {}
    evi_breakdown: dict[str, int] = {}
    for q in ans:
        ret_breakdown[q.retrieval_status] = ret_breakdown.get(q.retrieval_status, 0) + 1
        evi_breakdown[q.evidence_status] = evi_breakdown.get(q.evidence_status, 0) + 1

    # Per-category metrics
    per_cat: dict[str, dict[str, float]] = {}
    cat_groups: dict[str, list[QueryEvaluation]] = {}
    for q in ans:
        cat_groups.setdefault(q.category, []).append(q)

    for cat, items in cat_groups.items():
        k = len(items)
        per_cat[cat] = {
            "count": float(k),
            "topical_recall@3": sum(1 for x in items if x.topical_hit_at_3) / k,
            "topical_recall@5": sum(1 for x in items if x.topical_hit_at_5) / k,
            "verified_target_evidence@5": sum(1 for x in items if x.verified_target_evidence_at_5) / k,
            "topical_mrr": sum(x.topical_reciprocal_rank for x in items) / k,
        }

    return BenchmarkSummary(
        arm_name=arm_name,
        total_queries=n_tot,
        answerable_queries=n_ans,
        unanswerable_queries=n_unans,
        strict_recall_at_1=s_r1,
        strict_recall_at_3=s_r3,
        strict_recall_at_5=s_r5,
        strict_mrr=s_mrr,
        topical_recall_at_1=t_r1,
        topical_recall_at_3=t_r3,
        topical_recall_at_5=t_r5,
        topical_mrr=t_mrr,
        verified_target_evidence_rate_at_3=ver_3,
        verified_target_evidence_rate_at_5=ver_5,
        verified_evidence_rate=ver_5,
        legacy_loose_verified_rate=legacy_ver,
        false_source_rate=fsr,
        unanswerable_accuracy=unans_acc,
        unanswerable_false_positive_rate=unans_fp,
        unjustified_verified_rate=unjustified_ver,
        level_1_retrieval_rate=lvl1_rate,
        level_2_verification_rate=lvl2_rate,
        level_3_abstention_accuracy=lvl3_abstain_acc,
        avg_tool_calls=calls,
        avg_bytes_transferred=bytes_trans,
        t_sql_mean_ms=sql_mean,
        t_sql_p50_ms=sql_p50,
        t_sql_p95_ms=sql_p95,
        t_retrieval_e2e_mean_ms=e2e_mean,
        t_retrieval_e2e_p50_ms=e2e_p50,
        t_retrieval_e2e_p95_ms=e2e_p95,
        retrieval_breakdown=ret_breakdown,
        evidence_breakdown=evi_breakdown,
        per_category=per_cat
    )
