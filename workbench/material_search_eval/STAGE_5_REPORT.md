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
