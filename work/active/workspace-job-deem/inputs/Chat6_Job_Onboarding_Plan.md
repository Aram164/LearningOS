# Chat 6: BIFOLD / DEEM Job — Onboarding & Ramp-Up Plan

*Generated: 3 May 2026 (KW 18) | Built from Stratum paper + repo, skrub DataOps docs, BIFOLD-DEEM-Job-Plan v1+v2, Chat 1–4 plans*
*Status: Not started. Job starts 2026-05-05 (in 2 days). Betreuer: Arnab.*
*This is the canonical job onboarding plan. Supersedes Plans/archive/BIFOLD-DEEM-Job-Plan.md and Plans/archive/BIFOLD-DEEM-Job-Vorbereitung-v2.md (kept as reference only).*

---

## Step ID Convention

All steps in this plan use the prefix **JK** (Job-Kompetenz). Reference format: **JK.{Phase}.{Step#}**

| ID | Meaning | Example |
|---|---|---|
| JK.0.1 | Phase 0, Step 1 (Stratum paper skim) | "Completed JK.0.1" |
| JK.2.3 | Phase 2, Step 3 (polars lazy API) | "Working on JK.2.3" |
| JK.0-test | Phase 0 self-test | "Passed JK.0-test" |

**When updating SEMESTER-STATUS.md:** write step IDs exactly as above.

---

## Why This Plan Exists

Your job at BIFOLD/DEEM is 40 h/month (~10 h/week) on the Stratum project — a system infrastructure for massive agent-centric ML workloads. The split is roughly 50 % features & optimizations, 30 % skrub components, 20 % tests & benchmarks. Stratum's core idea: LLM agents generate thousands of ML pipeline variants; Stratum batch-compiles them into optimized execution graphs and runs them on a heterogeneous Plans/Programming/rust/Rust/Python runtime. It builds on top of skrub's DataOps lazy DAG abstraction and integrates seamlessly with pandas, polars, and scikit-learn.

The danger: jumping into the repo without understanding the conceptual layers (lazy evaluation, DAG optimization, the skrub DataOps model, pandas/polars internals) and spending weeks fighting the code instead of contributing. This plan lays out logical phases with explicit prerequisites so each step builds on solid ground.

This plan is **not week-based**. Steps are ordered by prerequisite logic. Your pace depends on semester load, but the ordering is fixed: don't skip ahead.

---

## How This Chat Connects to Others

| Chat | What it gives you for the Job |
|---|---|
| **Chat 1 (Foundations: AML + SaD)** | ML theory (regression, NNs, CNNs) → you understand what the pipelines Stratum optimizes actually *do* |
| **Chat 2 (AMLS Theory)** | ML Systems architecture → you understand *why* Stratum exists: operator fusion (L04), distributed execution (L05–L06), data cleaning pipelines (L10), compilation & rewrites (L03) |
| **Chat 3 (AMLS Project)** | Hands-on sklearn `fit`/`predict`/`score` → you know the user-facing API that Stratum wraps |
| **Chat 4 (PPDS mlprov)** | Provenance tracking over pandas/sklearn pipelines → you've already built a system that instruments the same libraries Stratum optimizes. The `_patching.py` pattern in mlprov is structurally identical to Stratum's patching. Chat 4 is mlprov-only; all job content lives here in Chat 6. |
| **Bootcamp** | Shell, Git, pytest, Docker, Python env — the daily tools |

**Rule of thumb:** Chat 4 (mlprov) is your single strongest preparation. Every engineering pattern there — wrapping pandas, intercepting sklearn, DAG representations, performance profiling — transfers directly.

---

## Prerequisite Dependency Graph

```
BOOTCAMP (Shell, Git, pytest, venv, Docker)
  │
  ├──────────────────────────────────────────────────────────────────┐
  ▼                                                                  │
PHASE 0: Orientation                                                 │
  Stratum paper (skim → deep read),                                  │
  skrub docs (Getting Started + DataOps),                            │
  Repo clone + build + run example                                   │
  │                                                                  │
  ├────────────────────────────┐                                     │
  ▼                            ▼                                     │
PHASE 1: DataFrame           PHASE 2: skrub Deep Dive               │
  Mastery                      DataOps model, TableVectorizer,       │
  pandas internals,            MinHashEncoder, source reading,       │
  polars (eager + lazy),       polars/pandas dispatch                │
  NumPy vectorization,         │                                     │
  profiling tools              │                                     │
  │                            │                                     │
  ├────────────────────────────┤                                     │
  ▼                            ▼                                     │
PHASE 3: Stratum Internals                                           │
  Repo deep-dive: patching, IR, optimizer,                           │
  runtime, adapters. Read + annotate one                             │
  operator end-to-end. Identify 3 open                               │
  problems / contribution areas.                                     │
  │                                                                  │
  ▼                                                                  │
PHASE 4: Benchmarking & Performance Engineering                      │
  pytest-benchmark, hyperfine, profiling,                            │
  fair benchmarking methodology,                                     │
  produce a real benchmark suite                                     │
  │                                                                  │
  ▼                                                                  ▼
PHASE 5: C++ Refresh                              (parallel to Phases 1–4,
  Move semantics, smart pointers, RAII,            lower priority, ~8h total)
  CMake, read C-ABI kernel code                    
  │
  ▼
PHASE 6: First Contributions
  Pick an issue, write a patch,
  write tests, submit for review
  │
  ▼
PHASE 7: Rust Ramp (vorlesungsfreie Zeit, Jul–Sep)
  Rust Book + Rustlings + PyO3,
  read Stratum Rust kernels,
  write a Python extension in Rust
```

---

## Phase-by-Phase Detailed Plan

### PHASE 0: Orientation — "Know what you're walking into" (~12 h)

**Prerequisites:** Bootcamp done (Shell, Git, pytest, venv). Can navigate a terminal, clone a repo, run tests.

**Why this comes first:** Arnab will assume you know the paper. Every conversation in the lab will reference Stratum concepts — lazy graphs, operator fusion, backend scheduling, skrub DataOps. Without Phase 0, you'll nod along without understanding.

| Step | What to do | Time | Prereqs |
|------|-----------|------|---------|
| JK.0.1 | **Stratum paper — skim.** Read Abstract, Intro, Figures, Conclusion. Answer for yourself: What problem? Who are the stakeholders (LLM agents)? What's the central idea (decouple pipeline planning from execution)? What's the evaluation baseline? | 2h | — |
| JK.0.2 | **skrub docs — Getting Started + DataOps page.** Understand skrub's role: sklearn-compatible tabulare Preprocessing + lazy DAG evaluation via DataOps. Understand that Stratum builds *on top of* skrub's DataOps abstraction. Key concepts: `TableVectorizer`, `Cleaner`, selectors, deferred evaluation, multi-table workflows. | 2h | — |
| JK.0.3 | **Stratum paper — deep read.** Every section, with a pen. Write your own 2-page summary: Problem Statement, Core Contribution (batch compilation of agent-generated pipelines into optimized execution graphs), System Architecture (Python API → IR → Optimizer → Rust Runtime → Backends), Key Optimizations (intermediate reuse, operator fusion, cost-based rewrites), Evaluation (up to 16.6× speedup), Limitations. | 4h | JK.0.1 |
| JK.0.4 | **Stratum repo — clone, build, run.** `git clone`, read README, install with `pip install -e .` (uses maturin for Rust build). Understand the folder structure: `stratum/` (Python: config, API, adapters, optimizer/IR, runtime, patching, tests) and `_rust/` (Rust crate with PyO3 bindings). Run any example script. Print/inspect an execution graph if possible. | 2.5h | JK.0.1 |
| JK.0.5 | **Map paper → code.** For each architectural component in your paper summary, find the corresponding directory/file in the repo. Write a mapping table: "Paper Section X → `stratum/optimizer/ir/`", "Rust Runtime → `_rust/src/`", "Adapters (RustyStringEncoder etc.) → `stratum/adapters/`", "Patching mechanism → `stratum/_patching.py`". | 1.5h | JK.0.3, JK.0.4 |

**⟷ Cross-wire to Chat 4 (mlprov):** Stratum's `_patching.py` does at the module level what your `mlprov/pandas/__init__.py` does — intercepts library calls and routes them through a custom wrapper. Same pattern, different purpose (optimization vs. provenance). When you read Stratum's patching, you'll recognize it immediately.

**⟷ Cross-wire to Chat 2 (AMLS L03–L04):** AMLS L03 (compilation, rewrites, operator selection) and L04 (operator fusion, JIT, runtime adaptation) describe *exactly* the techniques Stratum implements. The paper is the practical instantiation of what those lectures teach abstractly.

#### ✅ Phase 0 Self-Test — you pass when:

- [ ] You explain Stratum's central idea in 3 sentences without looking at anything
- [ ] You name the 5 architectural layers (Python API, IR, Optimizer, Rust Runtime, Backends)
- [ ] You explain what "lazy execution graph" means and why it enables optimization
- [ ] You know what skrub DataOps is and how Stratum builds on it
- [ ] You can point to the file/directory in the repo that corresponds to each layer
- [ ] You've run at least one example end-to-end locally

---

### PHASE 1: DataFrame Mastery — "Speak the language of the data layer" (~20 h)

**Prerequisites:** Phase 0 done (you know *what* Stratum does). Python basics from Bootcamp. FP Ch. 1 (data model) started.

> **Optional supplement:** [TU Python-for-ML Sheet 2](https://github.com/mahmutoezmen/Python-for-ML-Course/tree/main/2.%20Sheet) — inheritance, NumPy internals, performance profiling, plotting. Directly relevant to JK.1A (pandas internals), JK.1B (NumPy), and JK.1D (profiling). Do early in Phase 1.

**Why this comes second:** Stratum optimizes pandas/polars/sklearn pipelines. If you don't deeply understand how these libraries work — their memory models, performance characteristics, lazy vs. eager evaluation — you can't reason about what Stratum's optimizations actually *do*. This phase makes you fluent in the data layer that Stratum sits on top of.

#### Block 1A: pandas Internals (~7 h)

| Step | What to do | Time | Prereqs |
|------|-----------|------|---------|
| JK.1A.1 | **pandas official docs: "10 minutes to pandas" + "Essential basic functionality".** Not a first tutorial — you already know basics. Read these for the *internal model*: how DataFrames store data (BlockManager, column-oriented), what `.values` returns (NumPy array), how indexing works (`__getitem__` dispatch for strings, lists, slices, boolean masks). | 2h | Bootcamp Python |
| JK.1A.2 | **pandas docs: "Enhancing Performance".** Read the Cython/Numba section. Understand *why* `iterrows()` is slow (row-by-row Python object creation, dtype coercion) and why vectorized operations are fast (C-level loops over contiguous memory). Understand `eval()` and `query()` for expression evaluation. | 1.5h | JK.1A.1 |
| JK.1A.3 | **Hands-on: Mini-Kernel-Projekt (pandas part).** Load a real dataset (NYC Taxi, ~1 GB). Implement a groupby-agg pipeline in three versions: (a) `iterrows` loop, (b) pandas vectorized, (c) pure NumPy arrays. Profile all three with `cProfile` + `line_profiler`. Document speedups. | 3.5h | JK.1A.1, JK.1A.2 |

#### Block 1B: NumPy Deep (~4 h)

| Step | What to do | Time | Prereqs |
|------|-----------|------|---------|
| JK.1B.1 | **NumPy docs: "Broadcasting", "Indexing", "Universal functions (ufuncs)".** Focus on the memory model: contiguous C-arrays, strides, views vs copies. Understand broadcasting rules (shape alignment from trailing dimensions). Understand why ufuncs are fast (compiled C loops, no Python overhead per element). | 2h | JK.1A.1 |
| JK.1B.2 | **Hands-on: Rewrite your Mini-Kernel NumPy version using explicit broadcasting and ufuncs.** No loops, no `apply`. Verify you get ≥10× speedup over the `iterrows` baseline. | 2h | JK.1B.1, JK.1A.3 |

#### Block 1C: polars — The Lazy Engine (~6 h)

**Why polars matters for Stratum:** polars' lazy API is conceptually identical to what Stratum does — build a computation graph, optimize it (predicate pushdown, projection pushdown, common subplan elimination), then execute. Understanding polars gives you intuition for Stratum's optimizer.

| Step | What to do | Time | Prereqs |
|------|-----------|------|---------|
| JK.1C.1 | **polars User Guide: "Getting Started" + "Concepts" + "Expressions".** Key idea: polars expressions are *context-free declarations* that the optimizer plans — not imperative commands. This is the mental shift from pandas (do this now) to polars (describe what you want, let the optimizer figure out how). | 2h | JK.1A.1 |
| JK.1C.2 | **polars User Guide: "Lazy API".** Read the lazy evaluation section completely. Understand `.lazy()`, `.collect()`, `.explain()` (prints query plan). Know the three key optimizations: predicate pushdown (filter early), projection pushdown (select only needed columns), common subplan elimination (don't compute the same thing twice). | 2h | JK.1C.1 |
| JK.1C.3 | **Hands-on: Port Mini-Kernel to polars.** Implement your pipeline in both eager and lazy polars. Call `.explain()` on the lazy version and read the query plan. Compare runtime with pandas. Write a paragraph explaining which optimizations polars applied. | 2h | JK.1C.1, JK.1C.2, JK.1A.3 |

#### Block 1D: Profiling Tools (~3 h)

| Step | What to do | Time | Prereqs |
|------|-----------|------|---------|
| JK.1D.1 | **Install and learn: `cProfile` + `snakeviz`, `line_profiler`, `py-spy`, `memray`.** Run each against your Mini-Kernel scripts. `cProfile` for function-level profiling, `line_profiler` for line-by-line, `py-spy` for flame graphs of running processes, `memray` for memory profiling. | 2h | JK.1A.3 |
| JK.1D.2 | **Produce a flame graph.** Use `py-spy record -o profile.svg -- python your_script.py`. Open the SVG. Identify the hottest call path. Write one sentence explaining the bottleneck. | 1h | JK.1D.1 |

**⟷ Cross-wire to Chat 2 (AMLS L03):** L03's "operator selection" is the systems-level version of what you see in polars' `.explain()` — the optimizer choosing between different implementations for each operation. When you study L03, the polars query plan will click.

**⟷ Cross-wire to Chat 4 (mlprov Phase 5):** Your DuckDB optimization in mlprov follows the same logic: profile → find bottleneck → replace with faster backend. The profiling skills from JK.1D transfer directly.

#### ✅ Phase 1 Self-Test — you pass when:

- [ ] You profile a 100-line pandas script in 15 min and name the 3 most expensive functions
- [ ] You explain `apply` vs `map` vs `transform` vs vectorized ops AND the performance difference
- [ ] You explain why `iterrows()` is slow (row materialization, type loss, Python object overhead)
- [ ] You correctly broadcast a NumPy operation and sketch the broadcasting rules from memory
- [ ] You run `py-spy` against a running process and read the flame graph
- [ ] Your Mini-Kernel shows ≥10× speedup from iterrows → NumPy
- [ ] You explain eager vs lazy polars in 2 sentences
- [ ] You name 3 polars lazy optimizer optimizations
- [ ] You translate a pandas snippet to idiomatic polars without looking at a cheat sheet
- [ ] You know what Apache Arrow is and why it matters (zero-copy, columnar, language-agnostic)

---

### PHASE 2: skrub Deep Dive — "30 % of your job lives here" (~12 h)

**Prerequisites:** Phase 0 done (you know skrub's role in the Stratum stack). Phase 1 Block 1A done (you understand pandas internals). Phase 1 Block 1C started (you know polars basics).

**Why this is a whole phase:** 30 % of your job is skrub components. Stratum's Python API is a façade over skrub. The DataOps lazy DAG abstraction that Stratum compiles and optimizes *comes from skrub*. You need to understand skrub both as a user and as a contributor reading source code.

| Step | What to do | Time | Prereqs |
|------|-----------|------|---------|
| JK.2.1 | **skrub docs: complete User Guide.** Work through every section. Focus on: (a) DataOps as lazy evaluation (deferred computation with preview), (b) selectors (column selection by dtype, name pattern), (c) multi-table workflows (joining multiple tables into a design matrix). Understand that DataOps is to skrub what LazyFrame is to polars — a deferred computation graph. | 3h | JK.0.2 |
| JK.2.2 | **skrub Tutorial-Notebooks.** Clone the skrub repo (`github.com/skrub-data/skrub`). Run the example notebooks in `examples/`. Focus on multi-table scenarios: how `AggJoiner` and `Joiner` work across tables. | 2h | JK.2.1 |
| JK.2.3 | **Key components deep-read.** For each of these, read the docstring + at least one example: `TableVectorizer` (the "do everything" preprocessor), `MinHashEncoder` (locality-sensitive hashing for high-cardinality categoricals), `GapEncoder` (Gamma-Poisson factorization), `DatetimeEncoder`, `Joiner`, `AggJoiner`, `Cleaner`, `DropUninformative`. | 2h | JK.2.1 |
| JK.2.4 | **Hands-on: skrub pipeline.** Take a Kaggle dataset with dirty categorical data (e.g., "Drug Review Dataset" or "Chicago Employees"). Build two pipelines: (a) sklearn only (`OneHotEncoder` + `Pipeline`), (b) skrub (`TableVectorizer` or `tabular_learner`). Compare: code lines, accuracy, runtime. | 2h | JK.2.3, Chat 3 sklearn knowledge |
| JK.2.5 | **Source-code dive: pandas/polars dispatch.** skrub supports both pandas and polars DataFrames. Find the module(s) where it dispatches between them (look for `_dataframe.py` or `_dispatch` patterns). Understand how a single `TableVectorizer` call works on both backends. This is directly relevant: Stratum's "seamless library support" depends on this abstraction. | 1.5h | JK.2.3, JK.1C.1 |
| JK.2.6 | **Source-code dive: `MinHashEncoder`.** Read the full source. Write 10 lines of comments explaining how it works internally (locality-sensitive hashing → n-gram shingling → multiple hash functions → fixed-width representation). Understand why this is better than one-hot for high cardinality (dimensionality explosion vs. fixed-width embeddings). | 1.5h | JK.2.3 |

**⟷ Cross-wire to Chat 4 (mlprov Phase 2):** mlprov's data operations (projection, selection, join with provenance) instrument exactly the same operations that skrub's DataOps orchestrate. You built the provenance layer; skrub builds the preprocessing layer; Stratum optimizes the execution.

**⟷ Cross-wire to Chat 2 (AMLS L10):** L10 covers data cleaning and feature transformation from a systems perspective. skrub is the library that implements this. When you study L10, you'll already know the tool.

#### ✅ Phase 2 Self-Test — you pass when:

- [ ] You name 5 skrub components that don't exist in sklearn and explain their purpose
- [ ] You explain how skrub handles high cardinality (MinHash / Gamma-Poisson factorization)
- [ ] You explain what DataOps is and how it relates to lazy evaluation
- [ ] You show a location in skrub source where polars and pandas are dispatched differently
- [ ] You've run `pytest` locally in the skrub repo
- [ ] You've built a working skrub pipeline on a real dataset and compared it to pure sklearn

---

### PHASE 3: Stratum Internals — "Navigate the codebase like a contributor" (~15 h)

**Prerequisites:** Phase 0 done (paper understood, repo cloned). Phase 1 done (you understand the data layer Stratum optimizes). Phase 2 done (you understand skrub DataOps, Stratum's foundational abstraction).

**Why this needs Phases 0–2 first:** Without understanding pandas/polars performance characteristics (Phase 1), you can't evaluate whether Stratum's optimizations make sense. Without understanding skrub DataOps (Phase 2), you can't read the Stratum Python layer. This phase takes you from "I understand the paper" to "I can navigate the code and find where to contribute."

| Step | What to do | Time | Prereqs |
|------|-----------|------|---------|
| JK.3.1 | **`stratum/_patching.py` — the entry point.** Read how Stratum intercepts pandas/sklearn calls and redirects them through its own pipeline. Compare with mlprov's patching (Chat 4). Draw a diagram: user code → patched import → Stratum IR → optimizer → runtime. | 2h | JK.0.5, Chat 4 Phase 1 |
| JK.3.2 | **`stratum/optimizer/ir/` — the intermediate representation.** Read how pipelines are represented as a DAG of operations. Understand the node types (data sources, transforms, estimators, joins). This is the "language" that the optimizer reasons about. | 2.5h | JK.3.1 |
| JK.3.3 | **`stratum/optimizer/` — the optimization passes.** Read what rewrites the optimizer applies. Look for: predicate pushdown, projection pushdown, operator fusion, intermediate reuse, cost-based operator selection. Map each optimization back to the paper and to the polars optimizations you studied in Phase 1. | 3h | JK.3.2, JK.1C.2 |
| JK.3.4 | **`stratum/adapters/` — the sklearn bridge.** Read `RustyStringEncoder`, `RustyOneHotEncoder` etc. These are sklearn estimator subclasses that replace Python implementations with Rust kernels. Understand the pattern: same sklearn interface, faster backend. Compare with your mlprov sklearn wrappers (Chat 4 Phase 3): same interface interception, different purpose. | 2h | JK.3.1, Chat 3/4 sklearn knowledge |
| JK.3.5 | **`_rust/` — the Rust runtime.** You won't write Rust yet, but *read* the structure: `src/lib.rs` (PyO3 module entry), kernel implementations, buffer pooling, scheduling. Understand at a high level: what does the Rust side do that Python can't? (Answer: memory control, parallelism without GIL, SIMD, zero-copy Arrow interop.) | 2h | JK.0.5 |
| JK.3.6 | **Trace one operator end-to-end.** Pick a single operation (e.g., a column transform or a join). Trace it from user-facing Python API call → patching → IR node creation → optimizer pass → runtime dispatch → Rust kernel execution (or Python fallback). Write a 1-page annotated trace with file paths and line numbers. | 2h | JK.3.1–JK.3.5 |
| JK.3.7 | **Identify 3 open problems / contribution areas.** Based on your reading: what's missing, buggy, or suboptimal? Look at GitHub Issues, TODOs in code, limitations in the paper. Write 3 bullet points, each with: what the problem is, where in the code it lives, and a rough idea of how to approach it. Bring this to your next meeting with Arnab. | 1.5h | JK.3.1–JK.3.6 |

**⟷ Cross-wire to Chat 2 (AMLS L03–L04):** The optimizer passes in JK.3.3 are concrete implementations of the compilation techniques from L03 (size inference, rewrites, operator selection) and L04 (operator fusion, runtime adaptation). Stratum is the running system that L03–L04 describe abstractly.

**⟷ Cross-wire to Chat 4 (mlprov Phase 5):** mlprov's DuckDB optimization (replace slow pandas joins with SQL) is a manual version of what Stratum's optimizer does automatically. You did by hand what JK.3.3 automates.

#### ✅ Phase 3 Self-Test — you pass when:

- [ ] You draw the Stratum architecture diagram freehand (API → Patching → IR → Optimizer → Runtime → Backends)
- [ ] You explain what `_patching.py` does and how it intercepts library calls
- [ ] You describe the IR node types and how a pipeline becomes a DAG
- [ ] You name 3 optimizer passes and explain what each does
- [ ] You show a specific adapter (e.g., `RustyStringEncoder`) and explain the pattern
- [ ] You've traced one operator end-to-end from user code to kernel execution
- [ ] You have 3 concrete contribution ideas written down

---

### PHASE 4: Benchmarking & Performance Engineering — "20 % of your job" (~8 h)

**Prerequisites:** Phase 1 done (profiling tools, Mini-Kernel). Phase 3 started (you know where performance matters in Stratum).

> **Optional supplement:** [TU Python-for-ML Sheet 5](https://github.com/mahmutoezmen/Python-for-ML-Course/tree/main/5.%20Sheet) — Numba JIT compilation, Cython, and automatic differentiation. The Numba/Cython parts show how to accelerate Python numerics — directly relevant to Stratum's performance engineering. Do during Phase 4.

**Why this has its own phase:** 20 % of your job is tests & benchmarks. At DEEM, a feature without a benchmark is an anecdote, not a contribution. Sloppy benchmarks waste everyone's time. This phase teaches you the discipline.

| Step | What to do | Time | Prereqs |
|------|-----------|------|---------|
| JK.4.1 | **Read: "Fair Benchmarking Considered Difficult" (Raasveldt et al., DBTest 2018).** Short paper. Key takeaways: warm-up runs matter, report median not just mean, vary input sizes, define your baseline, ensure reproducibility. | 1.5h | — |
| JK.4.2 | **Watch: "How NOT to Measure Latency" (Gil Tene, YouTube, 45 min).** Sharpens your thinking about tail latencies, coordinated omission, and why percentiles beat averages. | 1h | — |
| JK.4.3 | **Learn `pytest-benchmark`.** Install it. Write a benchmark test for your Mini-Kernel Project (3 implementations × 5 input sizes). Understand the output: mean, median, stddev, rounds, iterations. | 2h | JK.1A.3 |
| JK.4.4 | **Learn `hyperfine`.** Install (`brew install hyperfine`). Benchmark two CLI commands against each other. Understand: warm-up runs, statistical output, export to JSON/CSV. | 1h | Bootcamp Shell |
| JK.4.5 | **Build your Benchmark Checkliste.** Memorize and internalize these 7 points: (1) Warm-up runs before measurement, (2) Multiple iterations, report median + stddev, (3) Vary input sizes (1k, 10k, 100k, 1M) and plot scaling, (4) Baseline clearly defined, (5) CPU frequency scaling disabled on Linux, (6) Reproducibility recipe (1 command or 1 Dockerfile), (7) Statistical significance (non-overlapping CIs or Mann-Whitney U). | 1h | JK.4.1, JK.4.2 |
| JK.4.6 | **Produce a real benchmark report.** Using your Mini-Kernel Project: 3 implementations × 5 input sizes, pytest-benchmark, matplotlib plots, median + p95 + stddev table. This is a portfolio piece — show it to Arnab. | 1.5h | JK.4.3, JK.4.5, JK.1A.3 |

**⟷ Cross-wire to Chat 4 (mlprov Phase 5):** The benchmark methodology here is exactly what you'll apply to mlprov's DuckDB performance report. Same checklist, same tools, different codebase.

#### ✅ Phase 4 Self-Test — you pass when:

- [ ] You recite 5 of 7 benchmark checklist points from memory
- [ ] You explain why "mean" alone is misleading (outliers, tails)
- [ ] You write a `pytest-benchmark` test that produces mean + median + stddev
- [ ] You run a `hyperfine` command for two CLI variants and interpret the output
- [ ] Your first question when seeing a benchmark number is "what was the baseline?"
- [ ] You have a clean benchmark report with plots

---

### PHASE 5: C++ Refresh — "The bridge to Rust" (~8 h, parallel to Phases 1–4)

**Prerequisites:** Prior C++ experience (tunadb project). Can be done in parallel with other phases at low priority.

**Why C++ before Rust:** Your C++ is sunk investment with high leverage. 8 h refresh brings you back to productivity. The concepts (ownership, RAII, move semantics, no-GC, stack-vs-heap) transfer to Rust at ~80 %. The job requires "at least one systems language" — you satisfy that with C++. Rust comes in the vorlesungsfreie Zeit.

| Step | What to do | Time | Prereqs |
|------|-----------|------|---------|
| JK.5.1 | **Move Semantics + Smart Pointers.** Effective Modern C++ Items 1–10, 17–25. In tunadb: convert raw pointers → `unique_ptr`. Understand `std::move` vs `T&&`. | 2h | Prior C++ |
| JK.5.2 | **RAII + Rule of 5.** Effective Modern C++ Items 11–16. Write a class with Rule of 5 and explain each special member function. | 2h | JK.5.1 |
| JK.5.3 | **Templates + `const`-Correctness.** cppreference + Godbolt. Write a small template function. Understand `constexpr`. | 2h | JK.5.2 |
| JK.5.4 | **CMake + Gesamtreview.** Write a `CMakeLists.txt` for tunadb. Build with CMake. Review all concepts. | 2h | JK.5.3 |

#### ✅ Phase 5 Self-Test — you pass when:

- [ ] You explain Rule of 5 and when you need it
- [ ] You distinguish `unique_ptr`, `shared_ptr`, `weak_ptr` in one sentence each
- [ ] You explain `std::move(x)` (cast to rvalue) vs `T&&` (rvalue reference type)
- [ ] You write a CMakeLists.txt for a project with two source files + one external library
- [ ] You look at a function in Godbolt and roughly understand if the compiler inlined it

---

### PHASE 6: First Contributions — "From learner to contributor" (~10+ h)

**Prerequisites:** Phases 0–4 done. Phase 5 at least partially done. You've identified contribution areas in JK.3.7.

**Why this is the transition point:** Everything before this was learning. Phase 6 is where you start producing value. The steps here are templates — fill them with whatever Arnab assigns or whatever you identified in JK.3.7.

| Step | What to do | Time | Prereqs |
|------|-----------|------|---------|
| JK.6.1 | **Pick your first issue.** Either Arnab assigns one, or you propose one from JK.3.7. Ideal first issue: small scope, clear test criteria, touches one layer (not cross-cutting). Examples: add a missing operator, fix a bug in an adapter, improve a benchmark. | 0.5h | JK.3.7 |
| JK.6.2 | **Read all related code.** Before writing a single line, read every file your change will touch. Understand the existing patterns (error handling style, test conventions, docstring format). | 2h | JK.3.1–JK.3.6 |
| JK.6.3 | **Write tests first.** Define what "done" looks like as a test. If the issue is a bug, write a test that reproduces it. If it's a feature, write a test that validates the expected behavior. | 2h | JK.4.3, Bootcamp pytest |
| JK.6.4 | **Implement the change.** Write the code. Follow existing patterns. Keep the diff small. | 3h | JK.6.2, JK.6.3 |
| JK.6.5 | **Benchmark if performance-relevant.** If your change touches a hot path, add a benchmark that shows the before/after. Use the methodology from Phase 4. | 1.5h | JK.4.5 |
| JK.6.6 | **Submit for review.** Push to a branch, open a PR (or whatever the team uses). Write a clear description: what, why, how. Reference the issue. | 1h | JK.6.4 |
| JK.6.7 | **Identify a skrub "good first issue".** Browse skrub's GitHub Issues for the "good first issue" label. Read the issue, read the related code, write a 5-sentence approach description. Even if you don't submit a PR, this exercise proves you can navigate an open-source codebase. | 2h | Phase 2 |

---

### PHASE 7: Rust Ramp — "The runtime language" (~40–60 h, vorlesungsfreie Zeit Jul–Sep)

**Prerequisites:** Phases 0–6 done. C++ refresh done (concepts transfer). No semester courses competing for time.

**Why this waits:** You won't write Rust at BIFOLD in the first 2–3 months. You'll read Python, profile, benchmark, write patches in Python, understand the system. Rust kernel authoring comes after you understand *what* to optimize. Learning Rust during the semester would split your attention fatally.

| Step | What to do | Time | Prereqs |
|------|-----------|------|---------|
| JK.7.1 | **Rust Book Ch. 1–5.** Variables, data types, functions, control flow, ownership. + Rustlings Ch. 1–6. | 10h | JK.5.1–JK.5.2 (C++ ownership maps to Rust) |
| JK.7.2 | **Rust Book Ch. 6–10.** Enums, error handling, generics, traits, lifetimes. + Rustlings Ch. 7–12. | 10h | JK.7.1 |
| JK.7.3 | **Rust Book Ch. 11–12 + porting project.** Testing, closures. Port a C++ hotspot from tunadb to Rust. | 10h | JK.7.2 |
| JK.7.4 | **PyO3: Rust → Python extension.** Follow the PyO3 User Guide. Build a Python-callable Rust function. Understand `#[pyfunction]`, `#[pyclass]`, maturin build. This is exactly how Stratum's `_rust/` crate works. | 10h | JK.7.3 |
| JK.7.5 | **Read Stratum Rust code with comprehension.** Reread `_rust/src/` — now you understand the language. Identify: kernel implementations, buffer pooling, parallelism primitives, PyO3 bindings. Write annotations for one kernel. | 5h | JK.7.4, JK.3.5 |
| JK.7.6 | **First Rust contribution.** Implement or optimize one Rust kernel in Stratum. Benchmark before/after. | 5–15h | JK.7.5, JK.6.1–JK.6.6 |

#### ✅ Phase 7 Self-Test — you pass when:

- [ ] You explain Ownership, Borrowing, Lifetimes in 2 sentences each
- [ ] You know `String` vs `&str` and when to use which
- [ ] You've completed Rustlings (~100 exercises)
- [ ] You routinely run `cargo new` + `cargo build` + `cargo test` + `cargo bench`
- [ ] You open a Stratum Rust file and understand ≥70 % of what's happening
- [ ] You've built a PyO3 Python extension (`pip install -e .`-ready)
- [ ] You've written or optimized one Rust kernel in Stratum with a benchmark

---

## The Competency Map — Summary

| # | Competency | Phase | Priority | Feeds into |
|---|-----------|-------|----------|------------|
| K1 | Python profiling + vectorization | Phase 1 | 🔴 critical | Everything — daily work language |
| K2 | pandas internals | Phase 1A | 🔴 critical | skrub, Stratum patching, mlprov |
| K3 | polars (eager + lazy + optimizer) | Phase 1C | 🔴 critical | Stratum optimizer intuition |
| K4 | NumPy deep | Phase 1B | 🟡 high | Vectorization patterns, sklearn internals |
| K5 | skrub (30 % of your job) | Phase 2 | 🔴 critical | Stratum Python layer, daily contributions |
| K6 | Stratum understanding (paper + repo) | Phases 0 + 3 | 🔴 critical | Every contribution you make |
| K7 | Benchmarking discipline (20 % of your job) | Phase 4 | 🔴 critical | Every performance claim |
| K8 | C++ refresh | Phase 5 | 🟡 high | Bridge to Rust, reading kernel code |
| K9 | Rust | Phase 7 | 🟢 later | Runtime kernel authoring |

---

## What This Chat Does NOT Cover (Handled Elsewhere)

| Topic | Where it lives | Why not here |
|-------|---------------|-------------|
| Python basics, venv, git, Docker, pytest | **Bootcamp** (Plans/Programming/python/Programming-Toolbox-Bootcamp.md) | Prerequisites assumed |
| AML theory (regression, NNs, CNNs) | **Chat 1** (Plans/ML/foundations/Chat1_Foundations_AML_SaD_Plan.md) | Background ML knowledge |
| AMLS systems theory (compilation, parallelism, lifecycle) | **Chat 2** (Plans/ML/systems/Chat2_AMLS_Theory_Plan.md) | Cross-referenced, not duplicated |
| AMLS Project (AI Image Detection) | **Chat 3** (Plans/ML/systems/Chat3_AMLS_Project_Plan.md) | Separate deliverable |
| PPDS mlprov (provenance tracking) | **Chat 4** (Plans/ML/mlprov/Chat4_PPDS_mlprov_Plan.md) | Strongest practical preparation, cross-referenced |
| DBT (Datenbanktheorie) | **Chat 5** (if opened) | Query optimization concepts help, but not required |

---

## Deliverables Checklist (show Arnab when asked)

- [ ] **Stratum Summary** (2 pages): Problem, Architecture, Key Optimizations, Limitations (JK.0.3)
- [ ] **Paper → Code mapping table** (JK.0.5)
- [ ] **Mini-Kernel Projekt** (repo): pandas vs NumPy vs polars, profiled, benchmarked (JK.1A.3, JK.1C.3, JK.4.6)
- [ ] **skrub pipeline** on real dataset, compared to sklearn (JK.2.4)
- [ ] **End-to-end operator trace** (1 page, annotated with file paths) (JK.3.6)
- [ ] **3 contribution ideas** (JK.3.7)
- [ ] **Benchmark report** with plots (JK.4.6)
- [ ] **First PR / patch** (JK.6.4–JK.6.6)

---

## Entscheidungs-Log

- **2026-04-22** Plan created as logical-steps (not week-based) to accommodate variable semester load.
- **2026-04-22** Phase ordering driven by prerequisite logic: Orientation → DataFrame Mastery → skrub → Stratum Internals → Benchmarking → Contributions → Rust.
- **2026-04-22** C++ refresh runs in parallel (lower priority) because it's a refresh, not new learning.
- **2026-04-22** Rust deferred to vorlesungsfreie Zeit (Jul–Sep) — you won't need it in the first 2–3 months.
- **2026-04-22** Mini-Kernel Projekt serves as red thread across Phases 1, 4 (same project, escalating rigor).
- **2026-04-22** Cross-wires to Chat 1–4 documented per phase to leverage semester synergies.

---

*This plan is a living document. Update it when Arnab assigns tickets — it transitions from "onboarding" to "backlog" at that point.*
