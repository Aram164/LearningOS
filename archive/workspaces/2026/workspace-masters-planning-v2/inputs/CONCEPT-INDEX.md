---
id: concept-index
type: index
status: live
---

# CONCEPT-INDEX — concept → your worked note

> **Created:** 2026-07-10 · **The retrieval layer of the degree system** (`MASTERS-ARCHITECTURE.md` §2). When any module, paper, or job task mentions a concept: look it up here, jump to YOUR worked version — don't re-derive, don't re-search.
>
> **Rules:** the index points INTO units/bridges, never copies content. One line per concept, best note first. Add lines whenever a tier-3 unit is completed (semester ritual) and at each promotion. Paths root-relative from `semestercontext/`.
>
> **Depth:** 🟢 full tier-3 unit (Ultimate Reference + Exercise Bank + Mock Exam) · 🟡 crosswalk/bridge/deep-plan section, no dedicated unit · ⚪ plan-level only (not yet worked)

## Statistics & Probability (SaD-SoSe26)

| Concept | Best worked note | Depth | Also see |
|---|---|---|---|
| Descriptive statistics (mean/variance/quantiles/histograms) | `Plans/Math/sad/SaD/notes/lect02 basics/SaD_L02_Ultimate_Reference.md` | 🟢 | SaD source crosswalk |
| Correlation + simple linear regression (statistics view) | `Plans/Math/sad/SaD/notes/lect03 correlation-regression/SaD_L03_Ultimate_Reference.md` | 🟢 | Regression bridge (below) |
| Probability, conditional probability, Bayes | `Plans/Math/sad/SaD/notes/lect04 probability/SaD_L04_Ultimate_Reference.md` | 🟢 | SaD 06–10 deep plan |
| Combinatorics | `Plans/Math/sad/SaD/notes/lect05 combinatorics/SaD_L05_Ultimate_Reference.md` | 🟢 | |
| Random variables, expectation, variance | `Plans/Math/sad/SaD/notes/SaD_06-10_Probability-Inference_DeepPlan.md` | 🟡 | 2025 videos L05–06 |
| Distributions (discrete, normal) | same deep plan | 🟡 | 2025 videos L07–08 |
| Estimation: MLE, point/interval, confidence intervals | same deep plan | 🟡 | AML L05 unit (MLE→cross-entropy) |
| Hypothesis testing, significance | same deep plan | 🟡 | feeds CSB benchmarking methodology |
| Instance-based / similarity-based learning (SaD view) | `Plans/Math/sad/SaD/notes/lect11 instance-based/SaD_L11_Reference.md` | 🟡 | AML L02 unit (KNN) |

## Machine Learning (AML-SoSe26)

| Concept | Best worked note | Depth | Also see |
|---|---|---|---|
| KNN classification, curse of dimensionality | `Plans/ML/foundations/AML/my notes/lect02 KNN-classifier/AML_L02_Ultimate_Reference.md` | 🟢 | SaD L11 reference |
| Bias–variance, over-/underfitting, train/test split | AML L02 unit + `Plans/ML/foundations/AML/my notes/AML_Book-Concept-Crosswalk_L02-L10.md` (L02 rows) | 🟢 | ISLP 5.1 |
| Linear regression, OLS, normal equations β̂=(XᵀX)⁻¹Xᵀy | `Plans/ML/foundations/AML/my notes/lect03 linear regression/AML_L03_Ultimate_Reference.md` | 🟢 | Regression bridge |
| Regression: SaD↔AML↔ISLP unified view (Tiers 0–5) | `Plans/ML/foundations/reference/Regression_SaD-AML-ISLP_Bridge.md` | 🟡 | |
| Non-linear regression, basis functions | `Plans/ML/foundations/AML/my notes/lect04 non-linear regression/AML_L04_Ultimate_Reference.md` | 🟢 | ⚠️ scope: lecture-matched, NOT ISLP Ch 7 |
| Logistic regression, MLE → cross-entropy | `Plans/ML/foundations/AML/my notes/lect05 logistic regression/AML_L05_Ultimate_Reference.md` | 🟢 | SaD estimation (deep plan) |
| Gradient descent (batch/SGD) | `Plans/ML/foundations/AML/my notes/lect06 gradient descent/AML_L06_Ultimate_Reference.md` | 🟢 | AN.E (derivatives) once worked |
| Linear classifiers, perceptron (⚠️ NO SVM in AML L07) | `Plans/ML/foundations/AML/my notes/lect07 linear classifiers/AML_L07_Ultimate_Reference.md` | 🟢 | |
| L08–L10 concepts (trees, NN + regularization — L09 owns NN regularization, NO batch norm) | crosswalk L08–L10 rows | 🟡 | units not built yet — build during F.N, then upgrade to 🟢 |
| AML↔SaD full lecture map, 18 cross-wires, pipelines | `Plans/ML/foundations/reference/AML-SaD_Master_Wiring.md` | 🟡 | THE spine for anything joint |
| CNN build (PyTorch, end-to-end) | `Plans/ML/systems/AMLS/AMLS-project/amls-project/` (Task 1.2) | 🟢 | DL-AMLS-Learning-Plan |

## ML Systems (AMLS-SoSe26) & Data Engineering (PPDS-SoSe26)

| Concept | Best worked note | Depth | Also see |
|---|---|---|---|
| ML systems: compilation, operator DAGs, parallelism, per-lecture sources | `Plans/ML/systems/AMLS-Source-Crosswalk.md` | 🟡 | DMMLS book layer; feeds DBT/TPS |
| Data provenance for ML pipelines (why/how, implementation) | `Plans/ML/mlprov/Chat4_PPDS_mlprov_Plan.md` + mlprov repo | 🟢 (code) | feeds EDML, thesis |
| sklearn estimator/transformer object model | `Plans/Libraries/sklearn/Sklearn-mlprov-Object-Map.md` | 🟡 | 5h crash plan |
| skrub DataOps DAG + evaluation engine | `Plans/Libraries/skrub/skrub-DataOp-DAG-Reference.md` + `…Evaluation-Engine-Reference.md` | 🟡 | Stratum (job) |

## Analysis (AN-SoSe26) — ⚪ until AN blocks are worked (exam Jul 27)

| Concept | Best entry today | Depth |
|---|---|---|
| Sequences/limits, continuity, derivatives/MVT, Taylor, integration | `Plans/Math/analysis/AN_Source-Crosswalk.md` (per-block 📒🎥🧪) + `Chat8_Analysis_SaD_Plan.md` cross-wires | ⚪ → upgrade after AN.X |

## Algorithms (Algo2-SoSe26) — ⚪ dormant until post-Jul 23

| Concept | Best entry today | Depth |
|---|---|---|
| Amortized analysis, B-trees, Fib-heaps, flows/matching, FFT … | `Plans/CS-Theory/algo2/Chat9_Algo2_Plan.md` (Moodle-verified per-topic literature) | ⚪ → upgrade after AL.X (feeds HA directly) |

## Programming & Tools (semester-independent)

| Concept | Best worked note | Depth |
|---|---|---|
| Python OOP: scope, super(), subclassing built-ins | `Plans/Programming/python/Python-OOP-Scope-Repair-Plan.md` | 🟢 |
| Python intermediate (symptom-indexed lookup, 21 steps) | `Plans/Programming/python/Python-Intermediate-Roadmap.md` | 🟡 |
| Rust (3 phases) | `Plans/Programming/rust/Rust-Learning-Plan.md` | ⚪ |
| Git/GitHub mental model (4-block interactive HTML) | `Plans/Programming/Git/` | 🟢 |
| Shell/git/pytest/Docker toolbox | `Plans/Programming/python/Programming-Toolbox-Bootcamp.md` | 🟡 |
