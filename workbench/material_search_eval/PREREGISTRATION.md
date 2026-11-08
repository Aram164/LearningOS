# Pre-Registration: LearningOS Material Search Held-Out v2 Benchmark

**Date:** 2026-11-08  
**Target Evaluation Set:** `workbench/material_search_eval/questions_heldout_v2.yaml`  
**Dataset SHA256:** `aab7d34bc258a643ffdbc157008e5e576e8173fe4142e5289dc38fe21f58a20a`  

## 1. Context & Objectives
To resolve audit finding H4 (compromised evaluation integrity / consumed test set) without bias, a fresh held-out evaluation set `questions_heldout_v2.yaml` of 24 queries (20 answerable + 4 unanswerable controls) was authored by an independent subagent reading document tables of contents and physical pages, strictly without keyword search or FTS5 queries.

## 2. Competing Arms
1. **FTS5 Production:** SQLite FTS5 lexical index using `unicode61 remove_diacritics 2`, frozen stopwords, body-only index (no title column), and deterministic tie-breaking (`ORDER BY rank, sha256, page_no`), executed via production entrypoint `execute_search`.
2. **Baseline B (Lexical Grep Scan):** Exact multi-term coordination scan over all 71,120 cached text pages.
3. **Baseline A (Official Workflow):** Multi-step tool-use path (`material.context` -> route locator scoring -> `material.span`).

## 3. Pre-Registered Decision Rule
The benchmark is evaluated under 3C metrics (strict R@1, R@3, R@5, bytes transferred, retrieval latency p50/p95, and exact McNemar test for paired binary accuracy).

**Primary Decision Rule (FTS5 vs Grep Scan):**
FTS5 is selected as the production backend if and only if **both** of the following conditions hold:
1. **Strict Recall@5:** $\text{Strict R@5}(\text{FTS5}) \ge \text{Strict R@5}(\text{Grep Scan}) - 2$ (out of 20 answerable questions; i.e., at most 2 fewer hits than scan).
2. **Latency:** $\text{p50 Latency}(\text{FTS5}) < \text{p50 Latency}(\text{Grep Scan})$.

**Contingency Branch (Scan Branch):**
If either condition fails, the system switches to the **Scan Branch**:
- Phase 4 is skipped (no SQLite FTS5 database builder, no `SEARCH_TOP_DIR` keep-list entry, no SQLite migration).
- The scan is implemented directly inside `learning_os.store.materials.search_index.execute_search` using coordination scoring behind the exact same contract.
- Phases 5–10 still apply to the scan implementation.

**Product Viability Gate (Baseline A):**
If neither backend (FTS5 or Grep Scan) beats Baseline A on strict R@3, execution is paused and reported to Aram for a product call on whether the material search capability provides sufficient value to ship.
