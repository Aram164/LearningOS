# Stage 5 Report — Material Search Production Evaluation & Ranking Hardening

Date: 2026-11-08  
Branch: `feature/material-search-fts5`  
Evaluator: Production runner `run_production.py` (`learning_os.store.materials.search_index.execute_search`)

---

## 1. Frozen Index Parity Check (Step 3.1)

Production search execution logic was pointed directly at the frozen Stage-3c index (`indices/fts5_unicode61.sqlite3`).

- **Target:** Reproduce stored Stage-3c top-5 candidate rankings across all 37 queries (27 dev + 10 heldout).
- **Result:** **37 / 37 exact top-5 matches** (`Frozen index parity check: 37/37 exact top-5 matches.`).
- **Conclusion:** Confirms that `execute_search` faithfully executes the evaluated query and ranking algorithm.

---

## 2. Production Index Dev Regression (Step 3.2 & 3.3)

Evaluation of the newly built production index generation (`gen_d054a3d02c25715e`) featuring:
- Tokenizer: `unicode61 remove_diacritics 2`
- Stopwords: Exactly matching frozen Stage-3c (`fts5_reranker.py:20`)
- Pure body-only text index (no `title` column, D2/D13)
- Deterministic order by `rank, source_sha256, page_no` (D11)

### Development Set (27 queries, 25 answerable, 2 unanswerable)

| Metric | Stage 3c Stored | Production Index (`gen_d054a3d02c25715e`) | Delta |
|---|---|---|---|
| **Strict R@1** | 0.04 (1/25) | **0.12 (3/25)** | +0.08 (+2 hits) |
| **Strict R@3** | 0.40 (10/25) | **0.44 (11/25)** | +0.04 (+1 hit) |
| **Strict R@5** | 0.52 (13/25) | **0.52 (13/25)** | 0.00 (parity preserved) |
| **Topical R@5** | 0.76 (19/25) | **0.76 (19/25)** | 0.00 |

*Condition check:* Strict R@5 (13/25) did not fall below the stored 13/25 (threshold was falling 3 or more). Parity holds without needing a title column.

---

## 3. Consumed Held-Out Set (Regression Check Only)

> [!WARNING]
> This held-out set was consumed during the audit and prior iterations. It serves exclusively as a regression sanity check, not for claims or tuning.

### Held-Out Set (10 queries, 9 answerable, 1 unanswerable)

| Metric | Stage 3c Stored | Production Index | Delta |
|---|---|---|---|
| **Strict R@1** | 0.11 (1/9) | **0.11 (1/9)** | 0.00 |
| **Strict R@3** | 0.22 (2/9) | **0.22 (2/9)** | 0.00 |
| **Strict R@5** | 0.56 (5/9) | **0.56 (5/9)** | 0.00 (5/9 preserved) |
| **Topical R@5** | 0.56 (5/9) | **0.56 (5/9)** | 0.00 |

---

## 4. Pre-Registered Fresh Held-Out v2 Benchmark (Step 3.4 & 3.5)

- **Dataset:** `workbench/material_search_eval/questions_heldout_v2.yaml` (24 queries: 20 answerable + 4 unanswerable controls).
- **Pre-Registration Commit:** `4d60b81` (`PREREGISTRATION.md`, pinned to SHA256 `aab7d34bc258a643ffdbc157008e5e576e8173fe4142e5289dc38fe21f58a20a` before execution).
- **Result File:** `workbench/material_search_eval/stage_5_results_heldout_v2.json` (B3 compliant: character counts only, zero page text).

### Aggregate Results Across Competing Arms

| Metric | FTS5 Production | Baseline B (Grep Scan) | Baseline A (Official Workflow) |
|---|---|---|---|
| **Strict R@1** | **0.25 (5/20)** | 0.15 (3/20) | 0.00 (0/20) |
| **Strict R@3** | **0.45 (9/20)** | 0.35 (7/20) | 0.05 (1/20) |
| **Strict R@5** | **0.65 (13/20)** | 0.35 (7/20) | 0.10 (2/20) |
| **Strict MRR** | **0.3892** | 0.2333 | 0.0267 |
| **Verified Target Evidence @5** | **0.40 (8/20)** | 0.25 (5/20) | 0.00 (0/20) |
| **Avg Tool Calls** | 3.75 | 2.63 | 4.00 |
| **Avg Bytes Transferred** | **11,701.2 B** | 12,447.5 B | 15,623.8 B |
| **Index Query p50 Latency** | **43.33 ms** (p95: 81.67 ms) | N/A (full scan) | N/A |
| **E2E Retrieval p50 Latency** | **1,994.52 ms** (p95: 3,600.66 ms) | 6,836.91 ms (p95: 8,300.37 ms) | 2,745.29 ms (p95: 3,318.75 ms) |

### Paired Comparison: Exact McNemar Test (Strict R@5 on 20 Answerable Queries)

| Cell | Count | Queries |
|---|---|---|
| **Both Hit (FTS5+ / Grep+)** | 6 | `HELD2-10`, `HELD2-11`, `HELD2-12`, `HELD2-14`, `HELD2-15`, `HELD2-20` |
| **FTS5 Only ($b$: FTS5+ / Grep-)** | **7** | `HELD2-01`, `HELD2-02`, `HELD2-05`, `HELD2-06`, `HELD2-08`, `HELD2-09`, `HELD2-16` |
| **Grep Only ($c$: Grep+ / FTS5-)** | **1** | `HELD2-07` |
| **Both Miss (FTS5- / Grep-)** | 6 | `HELD2-03`, `HELD2-04`, `HELD2-13`, `HELD2-17`, `HELD2-18`, `HELD2-19` |
| **Exact Two-Sided McNemar $p$-value** | **0.0703** (`0.0703125`) | — |

### Evaluation of Pre-Registered Decision Rule

1. **Condition 1 — Strict Recall@5:**
   $$\text{Strict R@5}(\text{FTS5}) = 13/20 \ge \text{Strict R@5}(\text{Grep Scan}) - 2 = 7/20 - 2/20 = 5/20$$
   FTS5 met the pre-registered non-inferiority floor (at most 2 fewer hits than Scan). Because a helper subagent authored `questions_heldout_v2.yaml` after the development results had already been seen and the exact two-sided McNemar test gives $p = 0.0703$, 13/20 vs 7/20 is recorded strictly as satisfying the pre-registered decision rule ($\ge \text{Scan} - 2$), not as proof that FTS5 beats the scan on recall. **PASS.**
2. **Condition 2 — p50 Latency:**
   $$\text{p50 Latency}(\text{FTS5}) < \text{p50 Latency}(\text{Grep Scan})$$
   Both SQL query p50 (`43.33 ms`) and end-to-end retrieval p50 (`1,994.52 ms`) are strictly below Grep Scan p50 (`6,836.91 ms`). **PASS.**
3. **Product Viability Gate — Baseline A Comparison:**
   $$\text{Strict R@3}(\text{FTS5}) = 0.45 > \text{Strict R@3}(\text{Baseline A}) = 0.05$$
   FTS5 beats Baseline A by $+40$ percentage points on Strict R@3 while transferring fewer average bytes (`11,701 B` vs `15,624 B`). **PASS.**

### Decision Outcome

**FTS5 stays as the production backend.** Proceed to Phase 4 (Index Identity & Lifecycle) and Phase 5 (Query Path).

---

## 5. Phase 5 Latency & Bounded-Cost Verification (Steps 5.6 & 5.8)

Measured against the redesigned self-describing index (`index-4ed250ab63629926.sqlite3`, 71,120 indexed pages, 242.6 MB) in the live-like scratch world:

| Check | Target | Before Fix (Audit) | Measured After Fix | Status |
|---|---|---|---|---|
| **In-process handler p50** (27 dev queries, full `material.search` handler including `ctx.repo()` load) | $\le 1,500\text{ ms}$ | $5,190\text{ ms}$ | **$529.7\text{ ms}$** (p95: $593.2\text{ ms}$) | **PASS** |
| **In-process `execute_search` p50** (27 dev queries, preloaded `Repo` snapshot + stat table) | $\le 1,500\text{ ms}$ | $4,220\text{ ms}$ | **$122.0\text{ ms}$** (p95: $125.3\text{ ms}$) | **PASS** |
| **Worst allowed query** (32 single-character common terms, `offset=200`, `limit=50`, deferred `snippet()`) | $\le 2,000\text{ ms}$ | $285,900\text{ ms}$ | **$638.2\text{ ms}$** (~1.97M VM steps; budget = 20M steps) | **PASS** |

