# Semester Status — SoSe 2026 — Central Brain

> **Last updated:** 2026-07-11 (KW 28) — **structure audit + drift fix:** 2 stray empty dirs deleted (crosscutting…programming + analysis…externe-klausuren, both unreferenced — details in SESSION-LOG); HANDOFF dir tree refreshed to post-Jul-10 reality; this header re-synced (was still claiming KW 27 / "Jul 2 TODAY"). KW-28 context: **Jul 10 = degree-level v2 rebuild** (Masters-Planning architecture, Obsidian+lychee tooling, material folders type-normalized per LEARNING-RESOURCES §0). Full change history: `SESSION-LOG.md`.
> **Current KW:** 28
> **Next deadlines:** 🔴 **AML Rücktritt via AGNES by Mi 15.07 (4 days — Open Loop #1c!)** · **AMLS Project + PPDS mlprov Jul 15 (4 days)** · Seminar written peer review **Jul 16** · **M2 Klausur Mo 27.07 12–15h** (16 days)
> **Exams (screenshot-verified from the Prüfungsplan, Jul 3):** **M2 = ONE combined Klausur for SaD+Analysis (Leser): Mo 27.07, 12:00–15:00, ESZ 110/115/307** (2. Termin: Fr 09.10, 13:00–16:00) · **AML (Schäfer): Mi 22.07, 15:00–18:00, ESZ 115** (⚠️ corrected from "21.07"; 2. Termin: **Mi 30.09, 09:00–12:00**, ESZ 110) · **AMLS (course-run): written, Jul 23 / Aug 06 / Aug 27, 4pm** · **Algo 2 mündlich 2. Termin: Oct 05–08 window (n.V.)**. **Plan: write only M2 on 27.07; AML → 30.09; AMLS → Aug 06 or Aug 27.** ⚠️ Rücktritt via AGNES = 1 week before: **AML by Mi 15.07, M2 by Mo 20.07**; 2.-PZ Anmeldung **31.08–10.09**. 1.-PZ Anmeldezeitraum ENDED 02.07 — check you were registered for M2!

---

## § 0.5 — Open Loops (check every session — the only list of unresolved actions)

> Consolidated 2026-07-02 from §9 notes, log entries, and LEARNING-RESOURCES action items. Rule: every new unresolved action lands HERE (not scattered); resolved items get ✅ + date and move to the bottom.

| # | Open loop | Why it matters | Due by | Status |
|---|---|---|---|---|
| 1 | 🔴 **Execute the exam plan (all dates verified Jul 3):** (a) ✅ resolved — **M2 = ONE combined SaD+Analysis Klausur, Mo 27.07 12–15h**; (b) **confirm you're REGISTERED for M2** (1.-PZ Anmeldung closed 02.07!); (c) if registered for AML: **withdraw via AGNES by Mi 15.07** (RR deadline), take the 2. Termin **Mi 30.09** instead; (d) pick AMLS sitting (**Aug 06 vs Aug 27**) and note AML-30.09 + Algo2-Oct-05–08 need **2.-PZ Anmeldung 31.08–10.09** | July = ONE exam (27.07) if executed; misses = full re-plan | **AML-Rücktritt by 15.07** | ◐ facts ✅, actions ⬜ |
| 2 | 🟠 Sequence the Aug–Okt exams (all dates known Jul 3): AMLS **Aug 06 or Aug 27** → then **AML Mi 30.09** → **Algo 2 mündlich Oct 05–08 (n.V., book slot)** → (M2 2. Termin Fr 09.10 only as fallback). 2.-PZ Anmeldung window **31.08–10.09** for the AGNES ones | ~3 exams in 5 weeks; prep blocks (S.X ~15–20h, F.N, AL ~40–50h) must be laid onto this spine | by mid-Aug | ◐ dates ✅, sequence ⬜ |
| 3 | ~~Confirm AMLS 2026 exam form~~ | — | — | ✅ Jul 2: **WRITTEN, 100%** (project = prerequisite +5 bonus) per [course page](https://mboehm7.github.io/teaching/ss26_amls/index.htm) → S.X = written drill (6.172 quizzes ⭐) |
| 4 | ~~Download **Fahrmeir Arbeitsbuch**~~ | — | — | ✅ Jul 2 (+ Dekking, OpenIntro, **Kelleher** — all in `SaD/Books/`; FAU Klausur in `SaD/Klausuren-extern/`. Blitzstein ✓ on Aram's Drive — copy into SaD/Books/ when convenient) |
| 5 | 🟡 Chase real Altklausuren: AML/SaD Moodle Probeklausuren · Fachschaft Informatik archive · last-year students; collect UE solutions in the SaD Übung as they're walked through | No public Altklausuren exist; these are the only channels | before late Jul | ⬜ |
| 6 | 🟡 Watch Moodle: **AML 2026 L11 (RNN) deck** → finalize crosswalk L11 rows + Block M3; **Algo 2 Kap. 10–12** literature → fill AL.J/K/I3 placeholders; **SaD Moodle literature list** → confirm Kelleher (FMLPDA) as the ML-half source text (crosswalk hypothesis) | All have placeholders waiting | ongoing | ⬜ |
| 7 | 🟡 On first 6.036 OLL login: verify the **unit names** cited in the crosswalk 🎥 layer; click-test one **tubcloud link** (Boehm SS23 AMLS recordings) | Cited from documentation, not yet opened | first use | ⬜ |
| 8 | 🟢 Decide: retire `tools/check_links.py` to `Plans/archive/` (role covered since Jul 10 by `check_system.py` + `lychee`) or keep as the semester-local check — then update its 3 references (HANDOFF, MASTERS-ARCHITECTURE, SEMESTER-KICKOFF template) | Three validators, two jobs — future sessions must know which to run | low priority | ⬜ |

---

## § 0 — How This Document Works

This is the **central control plane** for the entire semester. It is updated from each chat session and read from any chat. The Hub Chat (this one) is the brain — it uses this file to:

1. Track what's been completed (via step IDs)
2. Detect neglect (anything untouched for 2+ weeks during its active period)
3. Identify blocking dependencies ("you can't start X until Y is done")
4. Recommend priorities ("do X next because it unblocks Y and Z")

**Step ID Prefixes:**

| Prefix | Plan | File |
|---|---|---|
| **F** | Chat 1: Foundations (AML + SaD) | Plans/ML/foundations/Chat1_Foundations_AML_SaD_Plan.md |
| **S** | Chat 2: AMLS Theory | Plans/ML/systems/Chat2_AMLS_Theory_Plan.md |
| **P** | Chat 3: AMLS Project | Plans/ML/systems/Chat3_AMLS_Project_Plan.md |
| **M** | Chat 4: PPDS mlprov | Plans/ML/mlprov/Chat4_PPDS_mlprov_Plan.md |
| **PY** | Python (Fluent Python) | Cross-cutting, tracked here |
| **DL** | MIT 6.S191 (supplement, integrated into Chat 1 + Chat 3) | Cherry-picked: L1, L3, Lab 1, Lab 2 |
| **JK** | Chat 6: Job Onboarding (Phases 0–7) | Plans/crosscutting/job/Chat6_Job_Onboarding_Plan.md |
| **SE** | Chat 7: Seminar IuG (presentation + peer reviews) | Plans/crosscutting/seminar/Chat7_Seminar_Presentation_Sprint.md + Plans/crosscutting/seminar/Chat7_Seminar_IuG_Plan.md |
| **AN** | Chat 8: Analysis (Kombimodul with SaD — one module grade) | Plans/Math/analysis/Chat8_Analysis_SaD_Plan.md |
| **AL** | Chat 9: Algo 2 (Cormen-based, 12 topics) | Plans/CS-Theory/algo2/Chat9_Algo2_Plan.md |

**Format for step completion entries:** `F.A1 ✓ (KW 17)` or `M.2.1.1 ~ (KW 22, partial)`

**Symbols:** ✓ = done, ~ = partial/in-progress, ✗ = skipped, ⊘ = blocked

---

## § 1 — Quick Health Dashboard

| Area | Status | Last touched | Alert |
|---|---|---|---|
| **F** Foundations (AML+SaD) | F.A–C done, B done, D partially done (D2,D3,D3b,D4 ✅); Block E + SaD 06–10 reference docs built; **AML×SaD Master Wiring built (KW 24)** | KW 24 (Jun 10) | WATCH — fast path stalled; F.D1→D5→E3-4→H→I1→K(L07). Wiring spine: **`Plans/ML/foundations/reference/AML-SaD_Master_Wiring.md`** (lecture map, 4 pipelines, 18 cross-wires, Block K SVM-correction, session sequences for F/I/J/K/L/M) + bridge notes `Plans/ML/foundations/reference/Regression_SaD-AML-ISLP_Bridge.md`, `Plans/Math/sad/SaD/notes/SaD_06-10_Probability-Inference_DeepPlan.md` + **book crosswalk L02–L10** `Plans/ML/foundations/AML/my notes/AML_Book-Concept-Crosswalk_L02-L10.md` (KW 27) + **SaD side: `Plans/Math/sad/SaD_Source-Crosswalk_L01-L15.md` + `SaD-Module-Overview.md`** (KW 27 — SaD material moved there) |
| **S** AMLS Theory | L01–L04 attended (lag strategy) | KW 27 (crosswalk) | Deep processing deferred until matching F blocks done. **Exam: WRITTEN, sittings Jul 23/Aug 06/Aug 27 (verified Jul 2)** — Aram takes a later sitting. **NEW: `Plans/ML/systems/AMLS-Source-Crosswalk.md`** — SS26 slides+mp4 per lecture (course page links recordings for 01–11!), 10-414/6.172/CS149/MLSysBook mapped, unit-build order for S.X. **KW 27 (Jul 4): 📚 book layer added** — DMMLS (Boehm's own book, Springer pull pending), MLSysBook Vol 1+2 downloaded local, USP/HTSYM/MLC free web, per-lecture reading map |
| **P** AMLS Project | Task 1.1 ✅, Task 1.2 (CNN) ✅ | KW 22 | BEHIND — Task 1.3 (due Jun 4) OVERDUE, Task 1.4 due **Jun 11 (tomorrow)** — renegotiate both with Abdalla. Team buffer to Jul 15. DL Phase 1 plan (`Plans/ML/systems/DL-AMLS-Learning-Plan.md`) supports both tasks. |
| **M** mlprov (PPDS) | **7/20 tests green (utils, loaders, ndarray, DF init+projection); sklearn 0% but plan rebuilt** | KW 24 (Jun 10) | 🔴 CRITICAL but PLANNED — **KW 24 sklearn sprint in Chat4 plan** (10 ordered steps, each = one test file, ~17h core). Key finding: all transformers are row-preserving pass-through → far less work than feared; PY.10/11 no longer blockers. First step: fix DataFrame derive + `__getitem__`. Due Jul 15. |
| **PY** Python (Fluent Python) | 5/14 done (Ch 1,5,6,11,14) | KW 21 | OK — **PY.10/11 downgraded from blockers (KW 24):** mlprov skeleton already uses subclassing, no decorators needed. PY.03 still mildly useful. Resume reading post-Jun 18. |
| **DL** MIT 6.S191 (supplement) | not started | — | DEPRIORITIZED — CNN (its target) already done; now DL1-prep only, not this-semester critical |
| **JK** Job prep | Ongoing at DEEM (~10h/wk) | KW 23 | OK — work happening, just not step-logged. JK.2.1 next when capacity allows |
| **Seminar (SE)** | topic chosen, **draft NOT started** | — | 🔴 CRITICAL — Presentation **Jun 18** (~2 wks). Sprint plan exists (Plans/crosscutting/seminar/Chat7_Seminar_Presentation_Sprint.md) |
| **AN** Analysis (Kombi w/ SaD) | Ch 1–2 learned a year ago; Folgen→Integral untouched. Plan built KW 24 (AN.0–AN.X, ~48h); **Chat8 recalibrated + 5 Buecher-PDFs triaged KW 27 (Jul 4)** | KW 27 (Jul 4, plan work) | 🔴 **M2 Klausur Mo 27.07 12–15h (combined w/ SaD, final Jul 3) — ~3 wks, NO study logged yet.** Operative schedule: Chat8 **"KW-27 RECALIBRATION"** (~25–28h: AN.0 this wknd → A → B+C → exam week merged w/ F.N). Triage: Grieser/Fritzsche/Deitmar/Ableitinger identified + slotted in `AN_Source-Crosswalk.md`. Admin: verify M2 registration! |
| **AL** Algo 2 (AlgoDat II, Kratsch) | Plan built + Moodle-verified KW 24 (AL.A–AL.X, ~40–50h); lectures through Kap. 9; no study logged | KW 24 (Jun 12) | OK (dormant by design) — **mündliche Prüfung 30 min, 2. PZ (Sept/Okt)**, Übungen ungraded → zero hours until post-Jul 23. Action: book Prüfungstermin (Agnes + Prüfungs-Moodle), sequence vs AMLS/AN |

**Alert levels:** `—` on track · `WATCH` slightly behind · `BEHIND` action needed · `BLOCKED` dependency issue · `CRITICAL` deadline risk

---

## § 2 — Dependency Map (What Blocks What)

These are the **cross-plan dependencies** — when completing step X in one plan unblocks step Y in another. The brain checks these before recommending priorities.

### Hard Prerequisites (must be done before the dependent starts)

| Blocker | Unblocks | Why |
|---|---|---|
| PY.01 (FP Ch 1: Data Model) | M.1.1.2 (ProvDataFrame) | `__repr__`, `__getitem__` needed to build ProvDataFrame |
| PY.02 (FP Ch 6: References) | M.1.1.2 (ProvDataFrame) | Aliasing/mutability understanding for provenance objects |
| PY.08 (FP Ch 14: Inheritance) — *subclassing section only* | M.1.1.2 (ProvDataFrame) | ProvDataFrame subclasses pd.DataFrame |
| F.A-test (Stats vocabulary) | P.1.1.3 (Class distribution analysis) | Need mean/variance/histogram concepts |
| F.D-test (Bias-variance) | P.1.2.3 (Threshold calibration) | Need to understand precision/recall/FPR tradeoff |
| F.I (Classification block) | P.1.2.2 (Classical models) | Need logistic regression concept |
| F.L (Neural networks block) | P.1.2.8 (Reference CNN) | Need forward pass, backprop understanding — *but can start with reference CNN from exercise appendix before F.L is fully done* |
| DL.L1 (6.S191 Intro to DL) | F.D–H (foundations fast path) | Watch alongside F blocks for DL-specific framing of loss, optimization, regularization |
| DL.L3 (6.S191 Deep Computer Vision) | P.1.2.8 (Reference CNN) | CNN architecture, convolutions, pooling — needed before building CNN in project |
| M.Phase 1 complete | M.Phase 2 | ProvDataFrame must exist before data ops |
| M.Phase 2 complete | M.Phase 3 | Data ops must work before sklearn integration |
| M.Phase 3 complete | M.Phase 4 | MLProvManager must be populated before analyses |
| P.1.1 (Cleaning) | P.1.2 (Modeling) | Clean data needed for model training |
| P.1.2 (Modeling) | P.1.3 (Augmentation) + P.1.4 (Explainability) | Need a trained model |
| S.A-test | S.B1 (Compilation) | Systems vocabulary needed |
| F.E (Regression) | S.B (Compilation) — *deep processing* | Need to know what β̂=(XᵀX)⁻¹Xᵀy IS before studying how to compile it |
| F.J (GD formal) | S.C (Parallel execution) — *deep processing* | Need SGD concept before studying data-parallel SGD |
| F.L (Neural networks) | S.D+E (LLMs, Hardware) — *deep processing* | Need forward pass/backprop before studying system-level NN optimization |
| Bootcamp done | JK.0.4 (Repo build) | Shell, Git, venv, pytest needed to clone + build Stratum |
| JK.0 complete | JK.1A, JK.1B, JK.1C, JK.1D, JK.2 | Must understand Stratum/skrub concepts before diving into internals |
| JK.1A+1B+1C+1D+2 complete | JK.3 (Stratum internals) | DataFrame mastery + skrub understanding needed to read Stratum source |
| JK.3 complete | JK.4 (Benchmarking) | Must understand what you're benchmarking |
| JK.5 complete (C++ refresh) | JK.6 (First contributions) — *if contribution touches C-ABI kernels* | Need move semantics, RAII to work on C++ runtime code |
| JK.3+4 complete | JK.6 (First contributions) | Must understand codebase + know how to benchmark before submitting patches |
| JK.5 complete | JK.7 (Rust ramp) | C++ memory model concepts transfer to Rust ownership |

### Soft Prerequisites (helpful but work can start without)

| Helps with | If you've done | The connection |
|---|---|---|
| P.1.2.9 (CNN tuning) | S.C4 (Adam optimizer in AMLS) | Understand why Adam converges |
| P.1.4.1 (Explainability method choice) | S.G1 (AMLS L12 occlusion/LIME) | Theory behind the methods — but exercise spec describes them |
| M.2.2.2 (Join provenance) | Prior DB knowledge (relational algebra) | Formal σ/π/⋈ maps to provenance rules |
| M.5.2.1 (DuckDB joins) | S.B3 (Operator selection) | Systems view of choosing backends |
| M.4.3.1 (GroupFairness) | S.G2 (AMLS L12 fairness metrics) | Formal fairness metric definitions |
| JK.2 (skrub deep dive) | M.Phase 2+ (mlprov data ops) | skrub's DataOps patterns inform provenance instrumentation |
| JK.1A (pandas internals) | M.1.1.2 (ProvDataFrame) | Understanding pd.DataFrame internals helps subclassing |
| S.B (Compilation block) | JK.3 (Stratum internals) | AMLS compilation theory explains why Stratum's optimizer works the way it does |
| S.C (Parallel execution) | JK.3.5+ (Stratum runtime) | Data parallelism concepts from AMLS map to Stratum's runtime |
| M.Phase 1 (ProvDataFrame) | JK.3 (Stratum patching) | mlprov patching pattern is structurally identical to Stratum's |

---

## § 3 — Progress Tracker

### Foundations — F (Chat 1)

| Block | Steps | Status | Completion KW |
|---|---|---|---|
| A: Stats Vocabulary | F.A1, F.A2, F.A-test | ✅✅✅ | KW 17 |
| B: What Is ML? | F.B1, F.B2, F.B3, F.B-test | ✅✅✅✅ | KW 17–22 (F.B2 via SaD 2025 L11 KW 22) |
| C: Expected Value Bridge | F.C1, F.C2, F.C3, F.C-test | ✅✅✅✅ | KW 18 |
| D: Bias-Variance + K-NN | F.D1–F.D5, F.D-test | ⬜✅✅✅✅⬜ | KW 22 (D2,D3,D3b,D4 via AML L02 + SaD 2025 L11 + ISLP 5.1; D1,D5 remaining) |
| E: Correlation & Regression | F.E1–F.E5, F.E-test | ⬜⬜⬜⬜⬜⬜ | |
| F: Probability & Bayes | F.F1, F.F2, F.F-test | ⬜⬜⬜ | |
| G: Distributions & Why MSE | F.G1–F.G5, F.G-test | ⬜⬜⬜⬜⬜⬜ | |
| H: Regularization | F.H1, F.H2, F.H-test | ⬜⬜⬜ | |
| I: Classification | F.I1–F.I4, F.I-test | ⬜⬜⬜⬜⬜ | |
| J: GD Formal + Estimation | F.J1–F.J5, F.J-test | ⬜⬜⬜⬜⬜⬜ | |
| K: Trees + Linear Classifiers | F.K1–F.K4, F.K-test | ⬜⬜⬜⬜⬜ | |
| L: Neural Networks | F.L1–F.L5, F.L-test | ⬜⬜⬜⬜⬜⬜ | |
| M: Deep Architectures | F.M1–F.M4, F.M-test | ⬜⬜⬜⬜⬜ | |
| N: SaD Exam Prep (Phase 1: Cluster Review) | F.N1–F.N5 | ⬜⬜⬜⬜⬜ | |
| N: SaD Exam Prep (Phase 2: Cheat Sheets) | F.N6–F.N7 | ⬜⬜ | |
| N: SaD Exam Prep (Phase 3: Exam Practice) | F.N8–F.N10 | ⬜⬜⬜ | |

### AMLS Theory — S (Chat 2)

| Block | Steps | Status | Completion KW |
|---|---|---|---|
| A: What Is an ML System? | S.A1–S.A4, S.A-test | ✅⬜⬜⬜⬜ | S.A1 done KW 16 |
| B: Compilation | S.B1–S.B6, S.B-test | ⬜⬜⬜⬜⬜⬜⬜ | |
| C: Parallel Execution | S.C1–S.C6, S.C-test | ⬜⬜⬜⬜⬜⬜⬜ | |
| D: LLM Systems | S.D1–S.D5, S.D-test | ⬜⬜⬜⬜⬜⬜ | |
| E: Hardware | S.E1–S.E5, S.E-test | ⬜⬜⬜⬜⬜⬜ | |
| F: ML Lifecycle | S.F1–S.F5, S.F-test | ⬜⬜⬜⬜⬜⬜ | |
| G: Debugging & Fairness | S.G1–S.G4, S.G-test | ⬜⬜⬜⬜⬜ | |
| H: Model Serving | S.H1–S.H3, S.H-test | ⬜⬜⬜⬜ | |
| X: Exam Prep | S.X1–S.X6 | ⬜⬜⬜⬜⬜⬜ | |

### AMLS Project — P (Chat 3)

| Task | Steps | Status | Completion KW |
|---|---|---|---|
| 1.1: Data Exploration + Cleaning | P.1.1.1–P.1.1.7 | ✅✅✅✅✅✅✅ | KW 19 |
| 1.2a: Classical Baseline | P.1.2.1–P.1.2.5 | ✅✅✅✅✅ | KW 22 |
| 1.2b: CNN Model | P.1.2.6–P.1.2.11 | ✅✅✅✅✅✅ | KW 22 |
| 1.3: Data Augmentation | P.1.3.1–P.1.3.6 | ⬜⬜⬜⬜⬜⬜ | due Jun 4 — NOT STARTED |
| 1.4: Explainability | P.1.4.1–P.1.4.5 | ⬜⬜⬜⬜⬜ | |
| Report | P.Report | ⬜ | |
| Docker | P.Docker | ⬜ | |

### mlprov — M (Chat 4)

| Phase | Steps | Status | Completion KW |
|---|---|---|---|
| 1: Core Infrastructure | M.1.0.1–M.1.1.5 | ✅✅✅✅~ | KW 22–23 (numpy ndarray + pandas DataFrame subclassing done; csv loader works) |
| 2: Data Operations | M.2.1.1–M.2.2.4 | ~~⬜⬜⬜⬜⬜ | KW 23 partial — projection (col select) ✅; **bool-mask `__getitem__` buggy**, joins/groupby untouched |
| 3: ML Pipeline Integration | M.3.0–M.3.7 (re-stepped KW 24) | ⬜⬜⬜⬜⬜⬜⬜⬜ | sklearn 0% — NEXT BIG BLOCK, now planned: 8 ordered steps in Chat4 KW 24 sprint, each closes one test file (~13h). Old M.3.1.1–M.3.2.6 numbering superseded |
| 4: Provenance Applications | M.4.1.1–M.4.3.3 | ⬜⬜⬜⬜⬜⬜⬜ | |
| 5: DuckDB Optimization | M.5.1.1–M.5.3.2 | ⬜⬜⬜⬜⬜ | |
| 6: Polish + Submit | M.6.1–M.6.5 | ⬜⬜⬜⬜⬜ | |

### DL Supplement (integrated into Chat 1 + Chat 3)

> ⚠️ **DEPRIORITIZED (KW 23).** This supplement existed to support the AMLS CNN build — which is now done (Task 1.2 ✅). It is no longer this-semester critical. Treat remaining items as **DL1-prep for after July**, to be picked up only if the seminar + mlprov + exams are under control. Do not let it compete for KW 23–29 hours.
>
> 📌 **KW 24 (Jun 10): superseded by `Plans/ML/systems/DL-AMLS-Learning-Plan.md`** — a two-phase plan built from Aram's own YouTube playlist + NNDL (Nielsen) + curated additions. **Phase 1** (Jun 10–18, ~8–10h) is task-driven and rides inside the P-task hours (augmentation theory for Task 1.3, saliency/occlusion for Task 1.4, report vocabulary). **Phase 2** (gated on Jul 15 submission, ~22–28h) is the full foundation: F.L/F.M exam prep + DL 1 prep. The table below remains as item reference only.

**Cherry-picked resources only (~12–14h total). Freed DBT hours (~2–2.5h/week) allocated here.**

**MIT 6.S191 (Alexander Amini):**

| Item | Topic | Maps to | Status | Time est. |
|---|---|---|---|---|
| DL.L1 | Intro to Deep Learning (dense nets, backprop, optimization) | F.D–H (foundations fast path) | ⬜ | ~1.5h |
| DL.L3 | Deep Computer Vision (CNNs, convolutions, pooling) | P.1.2.8 (Reference CNN), F.L–M | ⬜ | ~1.5h |
| DL.Lab1 | Deep Learning in Python; Music Generation | Chat 3 (PyTorch tutorial) | ⬜ | ~3h |
| DL.Lab2 | Facial Detection Systems (CV lab) | Chat 3 (CNN build + tune) | ⬜ | ~3h |
| DL.L8 | Massively Parallel Training (optional) | S.C (AMLS parallel execution), JK.3 | ⬜ | ~1h |

[6.S191 playlist](https://www.youtube.com/playlist?list=PLtBw6njQRU-rwp5__7C0oIVt26ZgjG9NI) · [Slides + Labs](https://introtodeeplearning.com/)
Skipped (defer to DL 1): L2 (sequences), L4 (generative), L5 (RL), L6 (frontiers), L7 (ethics/science), Lab 3 (LLM)

**Additional resources:**

| Item | Topic | Maps to | Status | Time est. |
|---|---|---|---|---|
| DL.3B1B | [3Blue1Brown: Neural Networks](https://ki-campus.org/en/learning-opportunities/videos/neural-networks) (4 videos: what is a NN, gradient descent, backprop, backprop calculus) | F.L (neural nets), F.D–E (loss/GD intuition) | ⬜ | ~1.5h |
| DL.PT14 | [Patrick Loeber: PyTorch CNN Tutorial](https://www.youtube.com/watch?v=pDdP0TFzsoQ) (CIFAR-10 classification) | Chat 3 (CNN build — same task structure as AMLS project) | ⬜ | ~0.5h |

**SaD 2025 lecture videos (supplementary — use when 2026 slides alone aren't clear):**

Located in `Plans/Math/sad/SaD/SaD-2025/`. Videos available for lectures 01–13. Content nearly identical for the stats core (04–10), reorganized for ML lectures (11–15). Use as "watch the video if the slides don't click."

| 2026 Block | Watch 2025 video | Why |
|---|---|---|
| F.C (Expected Value Bridge) | 2025 L05 (random_variables) + L06 (expected_values) | 2025 splits E[X] into two lectures — more depth than 2026's single L06 |
| F.F (Probability & Bayes) | 2025 L04 (probability_with_notes) | Annotated version, same content |
| F.G (Distributions & MSE) | 2025 L07 (discrete_distributions) + L08 (normal_distribution) | Direct match, video helps with MLE→MSE derivation |
| F.J (GD Formal + Estimation) | 2025 L09 (point_interval_estimation) + L10 (statistical_significance) | Confidence intervals and hypothesis tests are easier with a walkthrough |
| F.K (Trees) | 2025 L12 (clustering) — different content but useful | K-means covered here |
| F.L (Neural Networks) | 2025 L14 + L15 (neural_nets_part1 + part2) | Two full lectures vs one in 2026 — significantly more depth on backprop |

### Analysis — AN (Chat 8, Kombimodul with SaD)

> Plan: `Plans/Math/analysis/Chat8_Analysis_SaD_Plan.md`. Exkurse excluded; Ausflüge low-priority. Chain: 0→A→C→E→F→G; B after A; D after B+C. ~48h total (~30–35h triaged if Scenario 1).

| Block | Steps | Status | Completion KW |
|---|---|---|---|
| 0: Refresh (Grundlagen + ℝ) | AN.0.1–AN.0.3, AN.0-test | ⬜⬜⬜⬜ | (learned 1 yr ago — refresh) |
| A: Folgen & Konvergenz | AN.A1–AN.A4, AN.A-test | ⬜⬜⬜⬜⬜ | |
| B: Reihen | AN.B1–AN.B3, AN.B-test | ⬜⬜⬜⬜ | |
| C: Grenzwerte & Stetigkeit | AN.C1–AN.C3, AN.C-test | ⬜⬜⬜⬜ | |
| D: exp/log + glm. Konvergenz | AN.D1–AN.D2, AN.D-test | ⬜⬜⬜ | |
| E: Ableitung, MWS, l'Hospital | AN.E1–AN.E4, AN.E-test | ⬜⬜⬜⬜⬜ | |
| F: Höhere Ableitungen + Taylor | AN.F1–AN.F2, AN.F-test | ⬜⬜⬜ | |
| G: Integralrechnung | AN.G1–AN.G4, AN.G-test | ⬜⬜⬜⬜⬜ | |
| X: Exam Prep | AN.X1–AN.X5, AN.X-test | ⬜⬜⬜⬜⬜⬜ | |

### Algo 2 — AL (Chat 9)

> Plan: `Plans/CS-Theory/algo2/Chat9_Algo2_Plan.md` (Moodle-verified). AlgoDat II, Prof. Kratsch. **Mündliche Prüfung 30 min, 2. PZ (Sept/Okt); Übungen ungraded.** Chain: A→B→{C,D,E,F}→G→H→I; J, K independent. ~40–50h. Dormant until post-Jul 23. "Buch" = CLRS 4. Aufl. Deutsch (= EN 3rd ed), in `Plans/CS-Theory/algo2/Algo2/`.

| Block | Topic | Steps | Status | Completion KW |
|---|---|---|---|---|
| A: Schnellere Multiplikation | DMS Kap. 1 (not CLRS!) | AL.A1–AL.A2, AL.A-test | ⬜⬜⬜ | |
| B: Amortisierte Analyse | CLRS Kap. 17 | AL.B1–AL.B2, AL.B-test | ⬜⬜⬜ | |
| C: B-Bäume | CLRS Kap. 18 | AL.C1–AL.C2, AL.C-test | ⬜⬜⬜ | |
| D: Fibonacci-Heaps | CLRS Kap. 19 | AL.D1–AL.D2, AL.D-test | ⬜⬜⬜ | |
| E: Splay-Bäume* | OW 5.4 + Sleator/Tarjan | AL.E1, AL.E-test | ⬜⬜ | |
| F: Cuckoo-Hashing* | Pagh [2006] | AL.F1, AL.F-test | ⬜⬜ | |
| G: Kürzeste Wege | CLRS Kap. 24+25 | AL.G1–AL.G2, AL.G-test | ⬜⬜⬜ | |
| H: Maximaler Fluss | CLRS 26.1–26.2 | AL.H1–AL.H2, AL.H-test | ⬜⬜⬜ | |
| I: Bipartites + Stable Matching* | OW 9.8 + TBD | AL.I1–AL.I2, AL.I-test | ⬜⬜⬜ | |
| J: Algorithmische Geometrie | CLRS Kap. 33 expected (not posted) | AL.J1–AL.J2, AL.J-test | ⬜⬜⬜ | |
| K: FFT* | CLRS Kap. 30 expected (not posted) | AL.K1–AL.K2, AL.K-test | ⬜⬜⬜ | |
| X: Oral exam prep | Explain sheets, hand-run drill, proof rehearsal, mock oral | AL.X1–AL.X4 | ⬜⬜⬜⬜ | |

### Python — PY (cross-cutting)

| # | Chapter | Status | Needed by |
|---|---|---|---|
| PY.01 | Ch 1 — Data Model | ✅ | M.Phase 1 (KW 19) |
| PY.02 | Ch 6 — References, Mutability | ✅ | M.Phase 1 (KW 19) |
| PY.03 | Ch 2 — Sequences | ⬜ | M.Phase 2 (KW 21) |
| PY.04 | Ch 3 — Dicts and Sets | ⬜ | M.Phase 2 (KW 21) |
| PY.05 | Ch 7 — Functions as First-Class | ⬜ | General (KW 19) |
| PY.06 | Ch 17 — Iterators, Generators | ⬜ | M.Phase 2, Job (KW 21) |
| PY.07 | Ch 11 — A Pythonic Object | ✅ | M.Phase 1 (KW 19) |
| PY.08 | Ch 14 — Inheritance | ✅ | Done KW 19 (super + subclassing built-ins) |
| PY.09 | Ch 5 — Data Class Builders | ✅ | M.Phase 3, Job (KW 23) |
| PY.10 | Ch 9 — Decorators and Closures | ⬜ | ~~M.Phase 3~~ Job only — **not an mlprov blocker (KW 24: skeleton uses subclassing)** |
| PY.11 | Ch 13 — Interfaces, Protocols, ABCs | ⬜ | ~~M.Phase 3~~ Job; optional enrichment for mlprov (ABCs already written in skeleton) |
| PY.12 | Ch 8 — Type Hints | ⬜ | Code quality (KW 25+) |
| PY.13 | Ch 15 — More Type Hints | ⬜ | Code quality (KW 25+) |
| PY.14 | Ch 18 — with, match, else | ⬜ | General (KW 26+) |

### Job Onboarding — JK (Chat 6)

| Phase | Key Steps | Status | Completion KW |
|---|---|---|---|
| 0: Orientation | JK.0.1 (paper skim), JK.0.2 (skrub docs), JK.0.3 (paper deep), JK.0.4 (repo build), JK.0.5 (map paper→code), JK.0-test | ✅✅⬜⬜⬜⬜ | |
| 1A: pandas internals | JK.1A.1–JK.1A.3 | ⬜⬜⬜ | |
| 1B: NumPy deep | JK.1B.1–JK.1B.2 | ⬜⬜ | |
| 1C: polars | JK.1C.1–JK.1C.3 | ⬜⬜⬜ | |
| 1D: Profiling tools | JK.1D.1–JK.1D.2 | ⬜⬜ | |
| 1-test | Phase 1 self-test | ⬜ | |
| 2: skrub deep dive | JK.2.1–JK.2.6, JK.2-test | ⬜⬜⬜⬜⬜⬜⬜ | |
| 3: Stratum internals | JK.3.1–JK.3.7, JK.3-test | ⬜⬜⬜⬜⬜⬜⬜⬜ | |
| 4: Benchmarking | JK.4.1–JK.4.6, JK.4-test | ⬜⬜⬜⬜⬜⬜⬜ | |
| 5: C++ refresh | JK.5.1–JK.5.4, JK.5-test | ⬜⬜⬜⬜⬜ | |
| 6: First contributions | JK.6.1–JK.6.7 | ⬜⬜⬜⬜⬜⬜⬜ | |
| 7: Rust ramp (summer) | JK.7.1–JK.7.6, JK.7-test | ⬜⬜⬜⬜⬜⬜⬜ | |

### Seminar IuG — SE (Chat 7)

Plattformregulierung (DSA/DMA, Big Tech), Prof. Vladova. 3 graded deliverables. Plan: `Plans/crosscutting/seminar/Chat7_Seminar_Presentation_Sprint.md`.

| Deliverable | Steps | Status | Hard date |
|---|---|---|---|
| Presentation (20min + 10min disc.) | SE.1 research, SE.2 outline, SE.3 slides, SE.4 rehearse | ⬜⬜⬜⬜ | **Jun 18** (finish Jun 16) |
| Oral peer review (Linus Kurth — Desinfo/Bots) | SE.5 | ⬜ | **Jul 2** |
| Written peer review (2–4 pp) | SE.6 | ⬜ | **Jul 16** |

---

## § 4 — Priority Rules (How the Brain Decides)

When you ask "what should I do next?", the brain applies these rules **in order**:

### Rule 1: Unblock before optimize
If step X is **blocked** because prerequisite Y isn't done, Y has priority. Check § 2 dependency map.

### Rule 2: Deadline proximity
Steps for the nearest deadline get priority. Current priority order (updated Jun 12 — AMLS exam moved):
1. **Seminar presentation (SE)** — Jun 18 (KW 25), hard *external* date, no buffer
2. **AMLS Project (P) + PPDS mlprov (M)** — both due Jul 15 (KW 29). *mlprov is the binding constraint; AMLS has team buffer.*
3. **Seminar peer reviews (SE)** — oral Jul 2, written Jul 16
4. **1. Termin exam cluster (late Jul, exact dates TBD — confirm all three):** AML Exam (F.N) + SaD Exam (F.N) + **Analysis Klausur (AN, Scenario 1)** — one shared Kombimodul grade rides on SaD+AN together
5. **2. Prüfungszeitraum block (Sept/Okt):** AMLS Exam (S.X, moved off Jul 23) + Algo 2 mündliche Prüfung (AL.X) + Analysis Klausur (AN.X, if Scenario 2) — sequence the three dates deliberately when booking
7. ~~DBT Exam~~ — **DROPPED KW 21**

### Rule 3: Lecture pace floor
Theory steps (F, S) must at minimum keep pace with lectures. If a lecture happened and you haven't processed it within 1 week, it becomes `WATCH`. Within 2 weeks: `BEHIND`.

### Rule 4: Neglect detection
Any active area (see § 5 below) untouched for 2 weeks → flag `WATCH`. Untouched for 3 weeks → flag `BEHIND`. The brain will tell you.

### Rule 5: Synergy windows
When two plans cover the same concept the same week, prioritize them together. Key synergy windows:

| KW | Synergy | Steps to do together |
|---|---|---|
| 18 | AML regression + AMLS compilation (β̂ as a DAG) | F.E + S.B |
| 21 | AML SGD + AMLS data parallelism | F.J + S.C |
| 23 | AML neural nets + AMLS project CNN | F.L + P.1.2.8 |
| 25 | AML CNNs + AMLS project augmentation | F.M + P.1.3 |
| 26 | AMLS L10 data cleaning + mlprov Phase 2 retrospective | S.F1-F2 + review M.Phase 2 |
| 28 | AMLS L12 fairness + mlprov GroupFairness | S.G + review M.4.3 |

### Rule 6: Projects over theory when deadlines approach
Starting KW 25 (3 weeks to deadline): project steps (P, M) take priority over theory (F, S) unless a theory step is needed as a prerequisite for the project.

---

## § 5 — Active Periods (When Each Area Should Be Touched)

| Area | Active from | Active until | Min frequency |
|---|---|---|---|
| F (Foundations) | KW 17 | KW 30 (exams) | Weekly |
| S (AMLS Theory) | KW 16 | 2. PZ (exam moved off Jul 23) | Weekly (follows lectures Thu); S.X exam prep now Aug/Sep |
| P (AMLS Project) | KW 19 | KW 29 (submit Jul 15) | Weekly once started |
| M (mlprov) | KW 19 | KW 29 (submit Jul 15) | Weekly once started |
| PY (Python) | KW 17 | KW 24 | ~1 chapter/week |
| DL (6.S191) | KW 21 | KW 25 | DEPRIORITIZED — DL1 prep only after July |
| JK (Job) | KW 17 (prep) | ongoing | ~10h/week (paid) — happening, log opportunistically |
| SE (Seminar) | KW 23 | KW 29 (written review Jul 16) | Daily during sprint (Jun 4–17), then Jul 2 + Jul 16 |
| AN (Analysis) | KW 25 (**Scenario 1 ACTIVE**) | Klausur 1. Termin (late Jul, exact date TBD) | AN.0 in KW 25 post-seminar; ~4h/wk KW 26–29; AN.E–G + X in the exam window per Scenario-1 table |
| AL (Algo 2) | post-Jul 23 | mündl. Prüfung (2. PZ, date TBD) | Dormant until Jul 23, then ~8–10h/wk interleaved with AN + S.X |

---

## § 6 — Neglect Tracker

> Updated automatically when session log entries are added.

| Area | Last session | Weeks idle | Status |
|---|---|---|---|
| F | KW 22 last *study* (F.B, F.D2-D4); KW 24 reference docs only (wiring spine) | 2 | WATCH — fast path stalled; F.D1→D5→E3-4→H→I1 next; wired sequences ready in `Plans/ML/foundations/reference/AML-SaD_Master_Wiring.md` for when hours open (KW 26+) |
| S | KW 16 (L01 attended; L02–L08 attended, not processed) | 8 | WATCH — lag strategy accepted, but processing backlog growing; exam-prep block X starts KW 29 |
| P | KW 22 (Task 1.2 CNN done) | 1 | BEHIND — Task 1.3 OVERDUE (Jun 4), Task 1.4 due Jun 11; renegotiate with Abdalla |
| M | KW 24 (Jun 10 — sklearn sprint plan built, suite re-verified 7/20) | 0 | 🔴 CRITICAL but PLANNED — follow Chat4 KW 24 sprint table: M.3.0 (getitem fix) → M.3.1 (ScoreResult) → transformers → tree → manager → fairness. Due Jul 15. |
| PY | KW 21 (PY.08 done) | 3 | OK — no longer blocking anything (KW 24 finding: mlprov needs no new PY chapters). Resume ~1 ch/week after Jun 18. |
| DL | — | — | DEPRIORITIZED — CNN target built; DL1-prep only, post-July |
| JK | KW 23 (ongoing at DEEM) | 0 | OK — ~10h/wk happening, log opportunistically |
| Seminar (SE) | none | — | 🔴 CRITICAL — draft not started, presentation Jun 18; sprint plan active |
| AN | KW 24 (Jun 12 — Scenario 1 activated, no study yet) | 0 | 🔴 ACTIVE from KW 25 — AN.0 is the first post-seminar action; from KW 26 apply normal neglect rules (~4h/wk floor) |
| AL | KW 24 (Jun 12 — plan Moodle-verified, no study yet) | 0 | OK (dormant by design) — mündl. Prüfung 2. PZ; one admin action open (book Prüfungstermin via Agnes + Prüfungs-Moodle) |

---

## § 7 — Weekly Load Planner

Target: ~36–40 hrs/week total. Job adds ~10 hrs/week starting KW 19.

**Re-baselined KW 23 (Jun 3).** Columns reordered by current priority. Job (~10h/wk paid) is constant — not shown, add on top. DL dropped (deprioritized). The binding constraint is now **mlprov (M)**, which absorbs the largest study block every week through submission.

| KW | Dates | SE (Seminar) | M (mlprov) | P (AMLS Proj) | F (AML/SaD) | S (AMLS) | Total study (+ ~10h job) |
|---|---|---|---|---|---|---|---|
| **23** | Jun 2–8 | 6h (research wk1) | 5h (Phase 1 start) | 4h (Task 1.3) | 2h (D1/D5) | 1h (attend) | ~18h |
| **24** | Jun 9–15 | 7h (slides + rehearse) | 6h (sprint M.3.0–M.3.4) | 5h (Task 1.4, Jun 11) | 1h | 1h (attend) | ~20h |
| **25** | Jun 16–22 | 3h (**DELIVER Jun 18**) | 8h (sprint M.3.4–M.3.6) | 4h (Report Jun 18) | 1h | 1h | ~17h |
| **26** | Jun 23–29 | — | 10h (M.3.7 full pipeline + M.4.x Fairness → **suite green target**) | 2h (polish) | 3h (E/H) | 3h (F) | ~18h |
| **27** | Jun 30–Jul 6 | 2h (**oral review Jul 2**) | 9h (DataLeakage/DataUsage, example pipelines, buffer) | 2h (buffer) | 4h (N start) | 4h (F+G) | ~21h |
| **28** | Jul 7–13 | 3h (written review draft) | 9h (polish, docs, presentation) | — | 4h (N) | 4h (G+H) | ~20h |
| **29** | Jul 14–20 | 3h (**written review Jul 16**) | 4h (**submit Jul 15**) | (submit Jul 15) | 10h (N exam prep) | 2h (attend last VL) | ~19h |
| **30** | Jul 21–27 | — | — | — | exam prep + **AML/SaD exams (late Jul, TBD)** | — | exam week |
| **31+** | Aug–Sep/Okt | — | — | — | — | S.X (2. PZ) | **2. PZ block: AL (~40–50h) + AN (~48h) + S.X (~15–20h) ≈ 105–120h @ ~15h/wk** |

> ⚠️ **Jun 12 restructure (final):** AMLS + Algo 2 → 2. PZ; **AML + SaD + Analysis all written in the 1. Termin (late Jul)**. KW 29–30 hours previously reserved for S.X flow to F.N + AN. **Add the AN Scenario-1 hours ON TOP of this table from KW 25: ≤2h (KW 25), 4h/wk (KW 26–29), then AN.E–G+X in the exam window** — see the Scenario-1 table in `Plans/Math/analysis/Chat8_Analysis_SaD_Plan.md`. The 2. PZ block shrinks to AL (~40–50h) + S.X (~15–20h) ≈ 55–70h Aug–Okt. ⚠️ Three written exams late July: get the exact dates NOW — spacing determines whether F.N and AN.X can be sequenced or must interleave.

**Notes:**
- **mlprov is the line that must not slip.** ~50h of implementation compressed into KW 23–29 (7 weeks). This is only feasible with triage — see the test-driven catch-up plan in Chat4 (KW23 re-baseline section). If a week is overloaded, cut F/S theory, not mlprov.
- **Seminar front-loaded into KW 23–25** per the sprint plan; must be done by Jun 16. After delivery, only the two peer reviews remain (Jul 2 oral, Jul 16 written).
- **AMLS project (P)** is half-done and team-shared; treat its internal dates as flexible. Coordinate with Abdalla so its hours can flex toward mlprov + seminar.
- **DBT dropped (KW 21); DL (6.S191) now deprioritized** — its target CNN is built. Revisit only as DL1 prep after July.
- **F** shifts to Block N (exam prep) from KW 27. **S** stays in lag mode (attend lectures) until exam-prep block X (KW 29–30).
- Totals look lighter than the old plan (~18–21h vs ~23–30h) because theory is deliberately suppressed to protect the two real deadlines (seminar + mlprov). Add ~10h job each week.

---

## § 8 — Key Dates

| Date | What | Step IDs affected |
|---|---|---|
| Apr 23 (Thu) | AMLS L02 | S.A2 |
| ~~Apr 29~~ | ~~DBT Ü1~~ — **DROPPED KW 21** | — |
| Apr 28 (approx) | AML L01 (KW 18 start) | F.B1 |
| Apr 30 (Thu) | AMLS L03 | S.B2, S.B3 |
| May 01 | Holiday | — |
| **May 04** | **AMLS Project: Setup done (internal)** | P.1.1.1 |
| **May 05** | **Job starts at DEEM** | JK.* |
| **May 07** | **AMLS Project: Task 1.1 done (internal)** | P.1.1.7 |
| May 07 (Thu) | AMLS L04 | S.B4, S.B5 |
| May 14 | Holiday (Ascension) — no AMLS | Catch-up week for S.B |
| **May 21** | **AMLS Project: Task 1.2 done (internal)** | P.1.2.11 |
| May 21 (Thu) | AMLS L05 | S.C1, S.C2, S.C3 |
| **KW 21** | **DBT DROPPED — hours reallocated to 6.S191** | DL.* |
| May 28 (Thu) | AMLS L06 | S.C4, S.C5 |
| **Jun 04** | **AMLS Project: Task 1.3 done (internal)** | P.1.3.6 |
| Jun 04 (Thu) | AMLS L07 | S.D1, S.D2, S.D3 |
| **Jun 11** | **AMLS Project: Task 1.4 done (internal)** | P.1.4.5 |
| Jun 11 (Thu) | AMLS L08 | S.E1, S.E2 |
| **Jun 18** | **AMLS Project: Report done (internal)** | P.Report |
| Jun 18 (Thu) | AMLS L09 | S.E3, S.E4 |
| Jun 25 (Thu) | AMLS L10 | S.F1, S.F2 |
| Jul 02 (Thu) | AMLS L11 | S.F3, S.F4 |
| Jul 09 (Thu) | AMLS L12 | S.G1, S.G2 |
| **Jul 15** | **AMLS Project + PPDS due** | P.Docker, M.6.5 |
| Jul 16 (Thu) | AMLS L13 (last) | S.H1, S.H2 |
| ~~Jul 23 16:00~~ | ~~AMLS Exam~~ — **MOVED to 2. PZ (Jun 12)** | S.X1–S.X6 |
| **Mi 22.07 15:00–18:00** | **AML Klausur 1. Termin (ESZ 115) — PLAN: SKIP (Rücktritt via AGNES by 15.07!), take 2. Termin** | F.N |
| ~~Late Jul~~ | ~~DBT Exam~~ — **DROPPED** | — |
| **Mo 27.07 12:00–15:00** | **M2 Klausur: SaD + Analysis COMBINED, one exam (ESZ 110/115/307)** ⭐ THE July exam | F.N + AN.X (merged prep!) |
| **2. PZ (Sept/Okt, TBD)** | **AMLS Exam** | S.X1–S.X6 |
| **2. PZ (Sept/Okt, TBD)** | **Algo 2 mündliche Prüfung (30 min, Zoom) — book via Agnes + Prüfungs-Moodle** | AL.X |
| **Mi 30.09 09:00–12:00** | **AML Klausur 2. Termin (ESZ 110)** — Anmeldung 31.08–10.09 | F.N |
| **Fr 09.10 13:00–16:00** | M2 2. Termin (fallback only) | — |
| **Oct 05–08 (n.V.)** | Algo 2 mündliche Prüfung window — book slot, Anmeldung 31.08–10.09 | AL.X |
| May 21 | Seminar: self-study, work on presentation draft | — |
| **May 28** | **Seminar: bring draft for feedback** | — |
| **Jun 18** | **Seminar: ARAM'S PRESENTATION** (Plattformregulierung / Big Tech) | — |
| **Jul 02** | **Seminar: oral peer review** of Linus Kurth (Desinformation/Bots) | — |
| **Jul 16** | **Seminar: written peer review due** (2–4 pages on Linus' talk) | — |

---

## § 9 — Current Priority Stack

> Updated each session. The brain recommends the top 3 items.

**As of KW 24 (Jun 10). Top 4:**

1. **🔴 Seminar presentation (Jun 18 — 8 days)** — per sprint plan, Week 1 (research + outline) should be DONE today; slide-building starts Fri Jun 12. If research/outline is NOT done, that's the only thing that matters this week. Real deadline: rehearsed by **Jun 16**.
2. **🟠 AMLS Task 1.4 (due TOMORROW Jun 11) + Task 1.3 (overdue Jun 4)** — talk to Abdalla *today/tomorrow* to reslot both. `Plans/ML/systems/DL-AMLS-Learning-Plan.md` Phase 1 carries the theory (augmentation, saliency/occlusion) inside P hours. Shared + buffered to Jul 15 → flex these, never the seminar.
3. **🔴 mlprov sklearn sprint (Jul 15)** — now PLANNED, not vague: Chat4 "KW 24 SKLEARN SPRINT" table, ~17h core, steps sized 0.5–2.5h to fit around the seminar. This week: M.3.0 (`__getitem__` + derive fix) → M.3.1 (ScoreResult). Suite-green target: end of KW 26.
4. **🟡 F fast path (F.D1→D5→E3-4→H→I1→K)** — exam-bound, not project-bound. Yields until 1–3 are stable; session sequences pre-wired in `Plans/ML/foundations/reference/AML-SaD_Master_Wiring.md` for KW 26+.

> **Note on Jun 18 collision:** Seminar + AMLS Report (internal) + AMLS L09 all land that day. Seminar must be *finished before* that week (Jun 16). Renegotiate the AMLS internal Report date with the team if needed — it has 4 weeks of slack; the seminar has none.
>
> **Exam restructure (Jun 12, final):** 1. Termin (late Jul) = **AML + SaD + Analysis, all written** → F.N and AN.X are now coupled exam-prep tracks (and SaD+AN share ONE Kombimodul grade). 2. PZ (Sept/Okt) = AMLS (S.X) + Algo 2 (AL, mündlich). Consequences: (a) **AN Scenario 1 active — AN.0 is the first post-seminar action (KW 25), ~4h/wk from KW 26**; (b) S.X + AL fully deferred to Aug/Sep; (c) F fast path gains urgency — it feeds BOTH late-Jul written exams. Admin actions: get the three 1.-Termin dates, book the two 2.-PZ Termine (Agnes + Prüfungs-Moodle). Top priorities (seminar Jun 18, mlprov, tasks) unchanged until Jun 18.
>
> **Deprioritized:** DL (6.S191) — DL1 prep after July (Phase 2 of DL-AMLS plan, gated on Jul 15). F.F/F.G/F.J/F.L–M theory — defer to exam-prep block N. DuckDB (mlprov old Phase 5) — cut unless suite is green with time to spare.

> *Historical priority stacks (KW 22 fast-path reasoning, KW 23 re-baseline) live in the §10 session log and §11 adjustment log; the F fast-path session sequences now live in `Plans/ML/foundations/reference/AML-SaD_Master_Wiring.md`.*


---

## § 10 + § 11 — Session Log & Adjustment Log → `SESSION-LOG.md`

> **Moved 2026-07-02 (KW 27).** The full session log (every work session, step IDs, decisions) and the adjustment log (plan changes, drops, shifts) live in **`SESSION-LOG.md`** at the repo root. **The append-after-each-session ritual is unchanged — it just happens there.** This file stays lean: live state only (§0–§9).
