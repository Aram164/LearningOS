---
id: degree-wiring
type: wiring
status: live
---

# DEGREE-WIRING — Module↔Module Routing Table (whole degree)

> **Created:** 2026-07-10 · **Pattern:** `Plans/WIRING.md` generalized from domain↔domain (one semester) to module↔module (all years). When planning or starting any Masters module, check its row here first: what feeds it, what it feeds.
>
> **Node naming:** stable module IDs (`AML-SoSe26`, `DBT-WiSe2728` …) per `MASTERS-ARCHITECTURE.md` §6. Masters slots per `MASTERS-MODULE-PLAN.md` (Entwurf C v2); re-verify in Moses before relying on any slot.
>
> **Maintenance:** edges are added at each semester's promotion ritual + whenever planning reveals one. Seeded 2026-07-10 from the SoSe-26 modules × the 6 menu axes.

---

## §1 Outgoing edges from SoSe 2026 (what this semester feeds forward)

### AML-SoSe26 (HU, Schäfer) → 🤖 ML axis

| Feeds | The wire | Entry point back into worked content |
|---|---|---|
| **ML 2-X** (M2) | Entire supervised-learning foundation: KNN, regression, logistic regression, GD, linear classifiers, bias-variance, MLE→cross-entropy | `CONCEPT-INDEX.md` rows → `Plans/ML/foundations/AML/my notes/lectNN…/` units |
| **Deep Learning 1** (M3) | L05 MLE→cross-entropy, L06 GD, L09 NN regularization (AML L09 owns regularization, NO batch norm), L10+ NN lectures | crosswalk `AML_Book-Concept-Crosswalk_L02-L10.md` + units |
| **MI I/II, Adversarial ML** (alternatives) | classifier fundamentals, decision boundaries | same units |
| **MLMMI** (M4) | model understanding presupposes the full AML model zoo | Module Card `AML-SoSe26` |

### SaD-SoSe26 (HU, Leser — Kombimodul M2 with Analysis) → 🧮 Math + 🤖 ML axes

| Feeds | The wire | Entry point |
|---|---|---|
| **Mathematics of ML** (menu) | probability, distributions, estimation, testing — MathML assumes all of it | `Plans/Math/sad/SaD_Source-Crosswalk_L01-L15.md` + `SaD/notes/SaD_06-10_Probability-Inference_DeepPlan.md` |
| **Foundations of Stochastic Processes** (menu) | random variables, expectation, convergence | same |
| **ML 2-X / DL1** | statistical learning vocabulary (estimators, likelihood, significance) | same + AML L05 unit (MLE) |
| **CSB** (M2) 📊 | statistics of measurement: confidence intervals, hypothesis tests = benchmarking methodology | SaD L09–10 worked content |

### Analysis-SoSe26 (HU — Kombimodul twin) → 🧮 Math axis

| Feeds | The wire | Entry point |
|---|---|---|
| **OptAlgos / MathML** | limits, derivatives/MVT, Taylor, integration — the proof toolkit | `Plans/Math/analysis/AN_Source-Crosswalk.md` + Chat8 plan cross-wires |
| **DL1** | Taylor expansion of loss, gradient formalism | AN.E/AN.F blocks ↔ AML L06 unit |

### AMLS-SoSe26 (TU, Böhm — ⚠️ Bachelor-ÜWP, LP-gesperrt im Master; knowledge reusable) → 🔧🚀 axes

| Feeds | The wire | Entry point |
|---|---|---|
| **DBT** (M1) + **DBTLAB** (M3) | operator DAGs, compilation, rewrites — AMLS L02–04 are the ML-systems face of the same ideas | `Plans/ML/systems/AMLS-Source-Crosswalk.md` (incl. DMMLS book layer) |
| **TPS** (M1, Steuwer) + Compiler line | compilation of linear algebra, IR thinking → Stratum-IR/thesis ramp | same + `MASTERS-RUNTIME-RESOURCES.md` |
| **MDS** (M1) / **DMH** (M2) | data-lifecycle, cleaning, ML-pipeline systems view | AMLS L10+ crosswalk rows |
| **CSB** (M2) 📊 | AMLS benchmarking/measurement sections | crosswalk |

### PPDS-mlprov-SoSe26 (⚠️ Bachelor-ÜWP, LP-gesperrt; knowledge reusable) → 🔧 axis + DEEM line

| Feeds | The wire | Entry point |
|---|---|---|
| **EDML** (M3, Schelter) + **Responsible DE Project** (M4) | provenance, pipeline instrumentation, fairness/leakage analyses — mlprov IS a mini-EDML | `Plans/ML/mlprov/Chat4_PPDS_mlprov_Plan.md` + repo |
| **Thesis (M5, Stratum)** | patching pattern structurally identical to Stratum's (proven: WIRING.md Libraries section) | mlprov repo + `Libraries/` reference docs |

### Algo2-SoSe26 (HU, Kratsch) → ⚙️ Algorithms axis

| Feeds | The wire | Entry point |
|---|---|---|
| **Höhere Algorithmik** (M1) | amortized analysis, B-trees, Fib-heaps, flows/matching, FFT — HA builds directly on this | `Plans/CS-Theory/algo2/Chat9_Algo2_Plan.md` blocks + future units |
| **RandAlgo / ParamAlgo / ADS** (menu) | same foundation | same |
| **DBT/DBTLAB** | B-trees + external memory = index structures in DB systems | AL.C block |

### Job-Stratum (ongoing, DEEM) → everything on the 🚀 line

| Feeds | The wire |
|---|---|
| TPS → DILA/ML&DMS (Böhm) → EDML/MLMMI (Schelter) → Responsible DE Project → **Thesis** | The job is the through-line; module choices exist to serve it (`MASTERS-MODULE-PLAN.md` §1 "DEEM-Rampe") |
| Rust/Python/skrub skills (`Plans/Programming/`, `Plans/Libraries/`) | language- and library-level knowledge is semester-independent — index it, reuse everywhere |

---

## §2 Incoming-edge view for M1 (WiSe 27/28) — the first consumer

At M1 kickoff, the plans for these modules should open with:

| M1 module | Read first (prerequisite passports + concepts) |
|---|---|
| **DBT** | `module-cards/AMLS-SoSe26.md` + AMLS crosswalk compilation rows; Algo2 AL.C (B-trees) |
| **HA** | `module-cards/Algo2-SoSe26.md` — full overlap; treat Algo2 units as revision layer 0 |
| **MDS** | AMLS lifecycle rows + mlprov card |
| **TPS** | AMLS compilation rows + `MASTERS-RUNTIME-RESOURCES.md` Schicht 1–2 |

*(Repeat this table for M2–M4 at their kickoffs; ML 2-X's version will be the big one — essentially the whole AML+SaD knowledge layer.)*

---

## §3 Cross-axis synergy edges (the "study together" list, degree level)

| Edge | Why (same trick, two faces) |
|---|---|
| HA (FFT) ↔ DL1 (convolutions) | convolution = pointwise mult. in frequency domain (proven wire from `Plans/WIRING.md`) |
| CSB ↔ any Portfolio module with experiments | measurement methodology transfers 1:1; also feeds thesis evaluation chapter |
| TPS ↔ DILA/ML&DMS | Steuwer compilation ↔ Böhm ML-systems: the two professor lines meet at Stratum |
| MathML ↔ ML 2-X | proofs for the algorithms studied concurrently |

*Add here whenever two same-semester modules share a concept — the semester WIRING.md of that semester holds the fine-grained version; this table only keeps degree-relevant edges.*
