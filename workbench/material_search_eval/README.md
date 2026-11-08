# LearningOS Material Search Evaluation Suite (Stage 1 & 2)

Reproducible evaluation harness comparing LearningOS material retrieval methods:
- **Baseline A**: The current official porcelain workflow (`material.context`, route locators, and `material.span --extract`).
- **Baseline B**: Direct lexical search over `generated/text-cache/` (simple file scan without SQLite).
- **Target (Future Stage 3)**: Disposable SQLite FTS5 search index.

---

## Structure

```
workbench/material_search_eval/
├── questions_dev.yaml            # 27 verified development questions (German/English, Math, Algorithms, etc.)
├── questions_heldout.yaml        # 10 verified held-out questions (retained for blind final evaluation)
├── ground_truth_verifier.py      # Independent verification tool for ground-truth integrity
├── eval_metrics.py               # Standardized metrics (Recall@K, MRR, tool calls, bytes, latency)
├── baseline_runner.py            # Executable benchmark runner for Baseline A and Baseline B
├── baseline_results_dev.json     # Measured raw benchmark results from the baseline execution
├── BASELINE_REPORT.md            # Comprehensive analysis report comparing Baseline A and Baseline B
└── README.md                     # This document
```

---

## Reproduction Commands

### 1. Verify Ground Truth Integrity
To verify that every question in the evaluation dataset points to an actual cached text page, that every quote is an exact substring, and that claimed routes resolve correctly:

```bash
# In repository root:
.venv/bin/python workbench/material_search_eval/ground_truth_verifier.py
```

### 2. Run the Baseline Benchmark
To execute both Baseline A and Baseline B on the development dataset:

```bash
# Run both baselines on questions_dev.yaml:
.venv/bin/python workbench/material_search_eval/baseline_runner.py \
  --dataset dev \
  --arm all \
  --json-out workbench/material_search_eval/baseline_results_dev.json
```

To run a specific arm only:
```bash
# Baseline A only:
.venv/bin/python workbench/material_search_eval/baseline_runner.py --dataset dev --arm baseline_a

# Baseline B only:
.venv/bin/python workbench/material_search_eval/baseline_runner.py --dataset dev --arm baseline_b
```

---

## Dataset Categories Covered

The 37 total questions (27 dev, 10 held-out) cover:
1. `german_terms`: German technical compound words (e.g., *Vollständige Induktion*, *Mittelwertsatz der Differentialrechnung*, *Bernoulli-Ungleichung*).
2. `english_terms`: Standard English machine learning terms (e.g., *Stochastic gradient descent*, *PageRank*, *K-means clustering*).
3. `math_notation`: Formulas with symbols, indices, and Greek letters (e.g., $(1+x)^n \ge 1+nx$, $f'(x_0) = \frac{f(b)-f(a)}{b-a}$, $w(u,v) \ge 0$).
4. `definitions`: Formal mathematical and algorithmic definitions.
5. `algorithms`: Algorithmic procedures (e.g., Dijkstra, Quicksort, Backpropagation).
6. `derivations`: Formal proof steps and theorem deductions.
7. `examples`: Concrete calculation and conceptual expansion examples.
8. `paraphrases`: Natural language phrasing differing from the literal slide headings.
9. `unmapped`: Materials present in `materials/` and `text-cache/` that have no active LearningOS unit route.
10. `unanswerable`: Realistic questions about topics not present in the curriculum to test refusal and false-hit behavior.

---

## Archive Notice

Result JSON files tracked in this repository have had copyrighted page body and snippet text stripped to character counts (`body_chars`, `snippet_chars`). Full-text original evaluation results are archived outside the repository at `~/LearningOS-archive-2026-11-08/material_search_eval-fulltext/`.
