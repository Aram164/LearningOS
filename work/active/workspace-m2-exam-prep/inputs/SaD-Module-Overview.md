---
id: SaD-SoSe26-overview
type: overview
module: SaD-SoSe26
status: live
---

# SaD — Module Overview & Unit-Build Guide

*Created KW 27 (Jul 2, 2026), when SaD moved home from `Plans/ML/foundations/` to `Plans/Math/sad/` — it is a Math/statistics module and a **Kombimodul with Analysis (M2.1, ONE shared grade)**, written in the same exam window. The AML pairing remains didactic (Chat1 + Master Wiring); the grade pairing is with AN.*

## The module in one box

| | |
|---|---|
| **Course** | Statistik und Datenanalyse (SaD), HU, Leser/Akbik |
| **Exam** | ✅ **FINAL (verified Jul 3): ONE combined M2 Klausur (SaD + Analysis, Leser) — Mo 27.07, 12:00–15:00, ESZ 110/115/307.** 2. Termin Fr 09.10 (fallback). Rücktritt gate Mo 20.07; ⚠️ verify registration (1.-PZ Anmeldung closed 02.07). THE July exam — AML skipped → 30.09, AMLS → Aug |
| **Grade** | **Kombimodul M2.1 with Analysis — ⚠️ corrected Jul 3: ONE 3h Klausur covers BOTH halves**, one grade. **Merged prep track: Block N clusters interleave with AN blocks** (operative schedule: Chat8 "KW-27 RECALIBRATION"); one combined cheat sheet, not two |
| **Study home** | Chat 1 (joint with AML, step prefix **F** — unchanged; the didactic AML↔SaD wiring is real and slide-verified) |
| **Exam-prep program** | Chat1 **Block N** (N1–N10: cluster review → cheat sheets → exam practice) |
| **Material** | `SaD/` (this folder): Lecture-slides 01–15 · **exercises: `SaD-2025/UE1–7.pdf` + `SaD-2025/Exercise-slides/`** (top-level `execise slides/` is EMPTY — delete or ignore) · Books/ (Fahrmeir Statistik ⭐ + **Arbeitsbuch ✓** + Blitzstein ✓ + OpenIntro ✓ + Dekking ✓ + Kelleher ✓ + **🆕 KW 29: Pitman · Ross · Tijms · Schaum's** [all probability, cover L04–08 only]; ⚠️ `The Principles of Probability` mis-filed = math logic, ignore) · Klausuren-extern/ (FAU ⭐ + 4 more) · notes/ |
| **Source selector** | `SaD_Source-Crosswalk_L01-L15.md` (this folder) — 📒🎥🧪 per lecture · **book difficulty ladder: `SaD_Book-Difficulty-Map_L01-L15.md`** (🆕 KW 29 — every book × lecture × chapter × difficulty) |
| **Deep docs** | 06–10: `SaD/notes/SaD_06-10_Probability-Inference_DeepPlan.md` · 03: Regression Bridge · 11: `SaD/notes/lect11 instance-based/SaD_L11_Reference.md` · cross-module: Master Wiring |

## Lecture map → exam clusters → existing coverage

| Cluster (Block N) | Lectures | Exam format (typical) | Coverage today |
|---|---|---|---|
| **N1 Descriptive** | 01, 02 | compute x̄/s²/quantiles/boxplot; precision/recall from tables | Blocks A ✅ (studied KW 17) |
| **N2 Probability & Counting** | 04, 05 | Bayes application, NB by hand, counting | Block F ⬜ — deep sources in crosswalk row 04–05 |
| **N3 RVs & Distributions** | 06, 07, 08 | E[X]/Var by hand, Binomial/Poisson calc, z-scores, CLT, MLE→MSE | Block C ✅ (sl. 1–35) + G ⬜ — **deep plan Sessions 1–4** |
| **N4 Inference** | 09, 10 | CI construction, full hypothesis-test setups | Block J ⬜ — **deep plan Sessions 4–5** |
| **N5 ML Methods** | 03, 11, 12, 13, 14, 15 | apply algorithms on toy data: regression k/d, ID3+IG, k-NN, NB+smoothing, 1L-ANN=MLR, parameter counting | 03 ✅ · 11 ✅ (L11 Reference) · 13 ≈✅ (via AML L02 unit) · **12, 14, 15 ⬜** |

## Unit-build plan (the future 4-file suites) — deliberately lighter than AML

> ⚠️ **Update (KW 28) — building per-lecture units for L01–L05 on request**, using a **3-file variant (Reference + Exercise Bank + Mini Plan, NO Mock Exam)**, one lecture at a time. This overrides the "no-unit for 01–02" default in point 5 below. **L01–L05 ✅ ALL DONE (batch complete, KW 28):** `SaD/notes/lect01 introduction/`, `lect02 basics/`, `lect03 correlation-regression/`, `lect04 probability/`, `lect05 combinatorics/`. Corrections/quirks logged: L01 slide 40 names **Teschl & Teschl** (not Fahrmeir) as the official stats text; L02 variance *defined* ÷(n−1) but slide-31 numbers use ÷n; **L04 slide-47 Bayes misprint — prints ~0.99, correct is ~0.91 (P(ill|pos)≈9%)**. L03 Reference delegates deep theory to the Regression Bridge. **L06–L10 remain covered by the deep plan (`SaD_06-10…DeepPlan.md`); L11–L15 by the L11 Reference + AML L02 unit + crosswalk rows** — build per-lecture units for those only on request.

**Decision logic:** SaD's exam is hand-computation-heavy, and half its lectures are already covered by AML units or deep docs. Full AML-style 4-file units for all 15 lectures would be over-engineering. Priority order:

1. **SaD 12 (Trees) — full unit** ⭐ first build. Zero coverage, SaD-only (no AML twin), classic exam task (build ID3 by hand), self-contained. Folder: `SaD/notes/lect12 tree-based/`.
2. **SaD 14 (Probability-Based/NB) — full unit** ⭐ second. Only a §2-C wiring section exists; UE6-relevant; the CS229 §4.2 + verified book layer makes it cheap to build well.
3. **SaD 06–10 — NO separate units.** The deep plan **is** the unit layer for the probability/inference half (its 5 sessions ≈ 5 mini-plans); Block N3/N4 cluster sheets (N6 phase) serve as the reference/cheat-sheet component. Only add per-lecture mock exams if time allows after 1–2.
4. **SaD 15 (NN) — half unit.** Build only a **SaD-angle sheet** (1L-ANN=MLR proof, parameter counting, SaD's own XOR/ReLU example, backprop-in-3-sentences) once AML L08/L09 units exist — they carry the substance; the SaD sheet adds the exam-specific framing. Folder: `SaD/notes/lect15 neural-networks/`.
5. **SaD 01–02, 03, 04–05, 11, 13 — no units.** Covered by: Block A ✅, Regression Bridge, crosswalk rows + Blitzstein/Fahrmeir, L11 Reference, AML L02 unit respectively. Block N cluster sheets close the rest.
6. **UE solutions:** collect in the Übung as walked through (Open Loop #5); worked keys get added to the matching unit folder as they accumulate.

**Unit template** = the AML 4-file standard (Reference + Mini Plan + Exercise Bank + Mock Exam, numerics verified) — see `Plans/ML/foundations/HANDOFF-AML-SaD.md` §3. Mini Plans carry the step-ID hook line.

## What this module does NOT do

- No duplicate video/book lists — the crosswalk selects, `LEARNING-RESOURCES.md` stores.
- No separate step-ID prefix — SaD steps stay **F.\*** in Chat1 (renumbering mid-semester = chaos). What moved is the *folder home*, matching the domain layout (Math subject, AN grade-twin).
- No AML unwiring — Master Wiring + Chat1 remain the joint study machinery; `Plans/WIRING.md` routes the now-cross-domain link ML.foundations ↔ Math.sad.
