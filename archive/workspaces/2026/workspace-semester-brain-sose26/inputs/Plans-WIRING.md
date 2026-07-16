# Plans — Cross-Domain Wiring

> **Purpose:** This file is the routing table between domain folders. When you open a plan in one domain, check the relevant section here to see what connects to it in other domains — and what must come first.
>
> **Scope:** Domain-to-domain dependencies only. For step-level hard deps (e.g. "PY.01 blocks M.1.1.2") → `SEMESTER-STATUS.md § 2`. For lecture-level ML↔SaD wiring → `Plans/ML/foundations/reference/AML-SaD_Master_Wiring.md`.

---

## Domain Map (what lives where)

| Folder | What it holds | Step prefixes |
|---|---|---|
| `ML/foundations/` | AML study home + the joint AML↔SaD plan (Chat1) | F, (PY supplement) |
| `Math/sad/` | **SaD material + module docs** (moved from ML/foundations KW 27 — Kombimodul twin of analysis; still *studied* via Chat1/F) | F (SaD half) |
| `ML/foundations/reference/` | All AML↔SaD reference docs + bridges | — |
| `ML/systems/` | AMLS theory, AMLS project, DL supplement | S, P, DL |
| `ML/mlprov/` | PPDS mlprov library project | M |
| `Math/analysis/` | Analysis (Kombimodul w/ SaD — one grade, same exam window; grade-twin lives in `Math/sad/`) | AN |
| `CS-Theory/algo2/` | AlgoDat II (Kratsch) | AL |
| `Libraries/sklearn/` | sklearn crash plan + mlprov object map | — |
| `Libraries/skrub/` | skrub DataOps DAG + Evaluation Engine refs | — |
| `Programming/python/` | Fluent Python roadmap, OOP repair, toolbox bootcamp | PY |
| `Programming/rust/` | Rust learning plan | — |
| `crosscutting/job/` | BIFOLD/DEEM job onboarding (Stratum) | JK |
| `crosscutting/seminar/` | Seminar IuG (Plattformregulierung) | SE |

---

## Wiring by Domain Pair

### ML.foundations ↔ Math.analysis

**Relationship:** Kombimodul — SaD and Analysis share one grade (M2.1). They are studied in separate chats (F and AN) but examined together.

| From ML.foundations | To Math.analysis | The wire |
|---|---|---|
| SaD L06–08 (probability / distributions) | AN.0 (ℝ foundations) → AN.A (sequences) | Probability lives on ℝ; limits underpin E[X] convergence proofs |
| SaD L09–10 (estimation / testing) | AN.E (derivatives/MVT) + AN.F (Taylor) | MLE derivations use derivatives; confidence intervals use Taylor expansion |
| SaD L14–15 (neural nets) | AN.G (integration) | Activation integrals, normalization constants |
| F.G (distributions → why MSE) | AN.F (Taylor → Taylor-expanding loss) | MSE derivation from MLE connects to Taylor approx of log-likelihood |
| F.N (SaD exam prep) | AN.X (Analysis exam prep) | SaD Block N and AN.X are **concurrent exam prep** — interleave sessions in the late-Jul window |

→ Exam prep order: **do SaD Block N and AN.X in the same weeks**, not sequentially. They share the Kombimodul grade.

---

### ML.foundations ↔ ML.systems (AML-first strategy)

**Relationship:** AML (F blocks) must be completed before deeply processing matching AMLS (S blocks). AMLS is incomprehensible without ML foundations.

| ML.foundations block | Unlocks ML.systems block | Why |
|---|---|---|
| F.E (Regression) | S.B (Compilation) — deep processing | Must know what β̂=(XᵀX)⁻¹Xᵀy IS before studying how to compile it as a DAG |
| F.J (GD formal) | S.C (Parallel execution) — deep processing | Need SGD concept before studying data-parallel SGD |
| F.L (Neural networks) | S.D+E (LLMs, Hardware) — deep processing | Need forward pass/backprop before studying system-level NN optimization |
| DL.L1 (6.S191 Intro) | F.D–H (foundations fast path) | Watch alongside F blocks for DL framing of loss, optimization, regularization |
| DL.L3 (Computer Vision) | P.1.2.8 (Reference CNN in project) | CNN architecture needed before building CNN |

→ Never schedule an S block study session without first checking which F block it requires.

---

### ML.foundations + Programming.python ↔ ML.mlprov

**Relationship:** mlprov is the intersection of Python OOP, ML pipeline concepts, and sklearn. Programming.python unlocks ML.mlprov phases.

| Programming.python chapter | Unlocks ML.mlprov phase | Why |
|---|---|---|
| PY.01 (Ch 1 — Data Model) | M.1.1.2 (ProvDataFrame) | `__repr__`, `__getitem__` needed |
| PY.02 (Ch 6 — References) | M.1.1.2 (ProvDataFrame) | Aliasing/mutability for provenance objects |
| PY.08 (Ch 14 — Inheritance) | M.1.1.2 (ProvDataFrame) | ProvDataFrame subclasses pd.DataFrame |
| PY.03 (Ch 2 — Sequences) | M.2.x (Data operations) | Sequence internals for data op provenance |
| PY.06 (Ch 17 — Iterators) | M.2.x, JK phases | Generator patterns in data pipelines |

→ `Plans/Libraries/sklearn/Sklearn-mlprov-Object-Map.md` is the bridge between the two — read it when starting M.Phase 3 (sklearn wrappers).

→ `Plans/Libraries/sklearn/Sklearn-5h-Crash-Plan.md` is a prerequisite sprint for M.Phase 3. Complete it first.

---

### ML.systems ↔ CS-Theory.algo2

**Relationship:** Several AMLS systems concepts map directly to Algo2 topics, and vice versa. Not hard prereqs, but synergy windows where studying both together gives double return.

| ML.systems topic | Algo2 topic | The connection |
|---|---|---|
| S.B (Compilation — operator DAGs, matrix chain) | AL.A (schnellere Multiplikation) + AL.B (amortized) | DAG optimization is a form of algebraic reduction; complexity analysis shared |
| P/M (CNN convolution layers) | AL.K (FFT) | Convolution in DL = pointwise multiplication in frequency domain via FFT |
| JK.3 (Stratum internals — B-tree indexes) | AL.C (B-Bäume) | Stratum uses B-tree-like index structures; understanding one deepens the other |
| M.Phase 1 (ProvDataFrame — pandas growth patterns) | AL.B (amortisierte Analyse) | Dynamic arrays / amortized growth is how pandas resizes — same analysis |
| S.C (Parallel execution — data parallelism) | AL.H/I (max flow / matching) | Parallel scheduling is a flow problem; matching workers to tasks = bipartite matching |

→ **Best scheduling:** Study AL.B (amortized) alongside M.Phase 1; AL.C (B-trees) alongside JK.3 (Stratum); AL.K (FFT) alongside F.M (Deep Architectures / CNNs). These are § 4 Rule 5 synergy windows.

---

### Libraries ↔ ML.mlprov + crosscutting.job

**Relationship:** Both mlprov (M) and the job (JK) instrument pandas/sklearn/skrub pipelines. The library reference docs serve both.

| Library doc | Serves M (mlprov) | Serves JK (job) |
|---|---|---|
| `Libraries/sklearn/Sklearn-mlprov-Object-Map.md` | M.Phase 3 — which sklearn classes to wrap | JK.2 (skrub internals share sklearn's estimator protocol) |
| `Libraries/sklearn/Sklearn-5h-Crash-Plan.md` | M.3.0 prerequisite sprint | JK.1A (pandas profiling — sklearn mental model helps) |
| `Libraries/skrub/skrub-DataOp-DAG-Reference.md` | M.Phase 2 (join/groupby provenance maps to skrub's DAG model) | JK.2 (skrub deep dive) |
| `Libraries/skrub/skrub-Evaluation-Engine-Reference.md` | M.Phase 4 (provenance analyses parallel skrub evaluations) | JK.2–JK.3 (Stratum uses skrub evaluation engine) |

→ mlprov patching pattern (M.Phase 1) is **structurally identical** to Stratum's patching pattern (JK.3). Work done in Chat 4 directly transfers to Chat 6.

---

### Programming.python ↔ Libraries ↔ crosscutting.job

**Relationship:** Job onboarding (JK) draws on Python chapters AND library references. The job is the integration point for everything in Programming + Libraries.

| Programming prerequisite | Job phase | What it enables |
|---|---|---|
| PY.05 (Ch 7 — Functions as First-Class) | JK.2 (skrub deep dive) | skrub uses callable pipelines heavily |
| PY.06 (Ch 17 — Iterators/Generators) | JK.1A–1D (DataFrame mastery) | pandas/polars lazy evaluation is generator-based |
| PY.10 (Ch 9 — Decorators) | JK.6 (first contributions) | Stratum uses decorator patterns for pipeline instrumentation |
| `Programming/rust/Rust-Learning-Plan.md` | JK.7 (Rust ramp) | Direct feed — JK.7 IS the Rust plan applied to Stratum's Rust codebase |
| `Programming/python/Programming-Toolbox-Bootcamp.md` | JK.0.4 (repo build) | Shell, git, venv, pytest needed to clone and build Stratum |

---

### Math.analysis ↔ ML.foundations (cross-wire registry)

The 15-wire registry between Analysis blocks and SaD/AML is embedded in `Plans/Math/analysis/Chat8_Analysis_SaD_Plan.md` (§ "Cross-wires"). Summary of the key ones:

| Analysis block | SaD/AML wire | Direction |
|---|---|---|
| AN.A (sequences/limits) | SaD L06 (E[X] as a limit) | AN → SaD: formalize the convergence |
| AN.C (continuity/Stetigkeit) | AML L05 (sigmoid continuity) | AN → AML: formal justification |
| AN.E (derivatives + MVT) | AML L03–04 (gradient descent) | AN → AML: formalize ∂L/∂w |
| AN.F (Taylor) | SaD L10 (asymptotic normality of MLE) | AN → SaD: Taylor proof of the CLT/MLE result |
| AN.G (integration) | SaD L07–08 (pdf normalization, E[X] for continuous RVs) | AN → SaD: integration IS the expectation |

---

## Navigation Cheatsheet

When you're about to start a session in domain X, first glance at:

| You're starting in… | First check… |
|---|---|
| `ML/foundations/` (F blocks) | Which S blocks this unblocks (§ ML.foundations ↔ ML.systems above) |
| `ML/systems/` (S/P blocks) | Which F block is prerequisite (same section) |
| `ML/mlprov/` (M blocks) | Python chapter prerequisites + Library docs to have open (§ ML.foundations + Programming ↔ ML.mlprov) |
| `Math/analysis/` (AN blocks) | Matching SaD block to study in parallel (§ ML.foundations ↔ Math.analysis) |
| `CS-Theory/algo2/` (AL blocks) | Synergy window match in ML.systems or ML.mlprov (§ ML.systems ↔ CS-Theory.algo2) |
| `Libraries/` | Whether it's serving M or JK or both (§ Libraries ↔ ML.mlprov + crosscutting.job) |
| `Programming/python/` | Which M or JK phase it unlocks (§ Programming.python ↔ Libraries ↔ crosscutting.job) |
| `crosscutting/job/` | Which library docs and programming chapters are prereqs (same section) |

---

*Added KW 24 (Jun 13, 2026). Full step-level deps: `SEMESTER-STATUS.md § 2`. Lecture-level AML↔SaD wiring: `Plans/ML/foundations/reference/AML-SaD_Master_Wiring.md`.*
