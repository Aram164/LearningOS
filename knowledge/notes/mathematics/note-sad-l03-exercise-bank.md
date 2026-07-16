---
id: note-sad-l03-exercise-bank
type: note
title: "SaD Lecture 03 — Exercise Bank (Correlation & Regression)"
created: "2026-07-11"
role: exercise-bank
state: evolving
authorship: mixed
concepts: [concept-correlation, concept-linear-regression, concept-normal-equation]
sources: [source-sad-ss26-lectures, source-fahrmeir-arbeitsbuch, source-sad-uebungen]
contexts: [workspace-m2-exam-prep]
---

> **Migration note (2026-07-17, Stage 2):** body preserved verbatim from
> `Plans/Math/sad/SaD/notes/lect03 correlation-regression/SaD_L03_Exercise_Bank.md` (legacy tree).

# SaD Lecture 03 — Exercise Bank (Correlation & Regression)

Practice for L03: covariance/Pearson by hand, simple least-squares line, the MLR normal equation, one gradient-descent step, feature scaling, and correlation≠causation. Self-grading keys throughout. Gaps → `SaD_L03_Ultimate_Reference.md` (same folder).

> **📎 The primary practice for this topic is the Bridge's dual-purpose self-test** — `Plans/ML/foundations/reference/Regression_SaD-AML-ISLP_Bridge.md` §5 — which is built to prove you're ready for *both* the SaD and AML exams. Do the drills below for SaD-exam by-hand fluency, then the Bridge self-test for depth. 3-file unit — **no Mock Exam**. Feeds Klausur clusters **N1 (correlation)** and **N5 (regression/ML methods)**.

---

## 1. Local material (in your repo)

| File / path | What it is | Use |
|---|---|---|
| `SaD_L03_Ultimate_Reference.md` | Full topic reference (slide-cited) | read / recall source |
| **`…/reference/Regression_SaD-AML-ISLP_Bridge.md`** | ⭐ the authoritative regression study doc (tiers, self-test §5, video library §7) | depth + cross-exam readiness |
| `SaD/SaD-2025/UE2.pdf` + `Exercise-slides/blatt-02.pdf` | SaD exercise sheet 2 (correlation/regression) | ⭐ solve first — course notation |
| `SaD/Books/Arbeitsbuch Statistik.pdf` — **Ch 3** | Fahrmeir *Arbeitsbuch*: covariance/correlation/regression drills **with solutions** | volume |
| `SaD/Klausuren-extern/FAU-…_mit-Loesungen.pdf` | solved German Klausur | correlation-test / regression items |
| `SaD/Books/Fundamentals of ML…Kelleher…(2015).pdf` — Ch 7 | the rent example + error surfaces/GD, worked | the L03 §9 source |

---

## 2. Warm-up drills (by hand)

Use this shared dataset for R1–R3: **x = (1, 2, 3, 4, 5), y = (2, 4, 5, 4, 5)**.

**R1 — covariance & Pearson.** Compute x̄, ȳ, s_{xy} (÷(n−1)), s_x, s_y, and r_{xy}.
<details><summary>answer</summary> x̄=3, ȳ=4. s_{xy}=1.5, s_x=1.581, s_y=1.225 → r = 1.5/(1.581·1.225) = **0.775** (moderate–strong positive).</details>

**R2 — the least-squares line.** Using R1, compute k and d, write f(x), and verify it passes through (x̄, ȳ).
<details><summary>answer</summary> k = r·s_y/s_x = s_{xy}/s_x² = 1.5/2.5 = **0.6**; d = ȳ − k·x̄ = 4 − 0.6·3 = **2.2** → f(x)=0.6x+2.2. Check: f(3)=4=ȳ ✓. Predictions: 2.8, 3.4, 4.0, 4.6, 5.2.</details>

**R3 — one gradient-descent step.** Fit f(x)=k·x (no intercept) with squared-error loss, start k₀=0, learning rate α=0.01, gradient step(k)=2·Σ(k·xᵢ − yᵢ)·xᵢ. Do one update.
<details><summary>answer</summary> at k₀=0: step = 2·Σ(−yᵢ·xᵢ) = 2·(−66) = **−132** (since Σ yᵢxᵢ = 2+8+15+16+25 = 66). Update k ← 0 − 0.01·(−132) = **1.32**. Note it moved toward the positive slope, as expected.</details>

**R4 — the normal equation, set up.** You have 3 instances with one feature: (x,y) = (1,1),(2,2),(3,2). Write the design matrix A (with intercept column) and the vector y, and state the formula for the weights. (Setup only — no need to invert by hand.)
<details><summary>answer</summary> A = [[1,1],[1,2],[1,3]], y = (1,2,2)ᵀ; k = (AᵀA)⁻¹Aᵀy. (For the curious: AᵀA=[[3,6],[6,14]], Aᵀy=[5,11] → k₀=2/3, k₁=1/2, i.e. f(x)=0.667+0.5x.) Conditions: A full column rank, n>m, AᵀA non-singular.</details>

**R5 — why not MAD / why this α?** (a) Why does the course minimize squared error rather than mean absolute deviation? (b) In the rent example, why was α = 0.00000002 needed, and what's the fix?
<details><summary>answer</summary> (a) squared error is **differentiable everywhere** (so you can set derivative = 0 / run GD) and equals the **MLE under Gaussian errors**; MAD isn't differentiable at 0. (b) the **size** feature's large raw values give a huge, steep gradient → any normal α makes it overshoot while others barely move; fix = **feature scaling** (min-max to [0,1] or z-scores). Reference §4, §9.</details>

**R6 — interpret weights.** After scaling, an MLR gives weights size +0.63, floor −0.18, broadband +0.07. (a) What do the signs mean? (b) Can you say size is 9× as important as broadband? When *can* you compare magnitudes?
<details><summary>answer</summary> (a) larger size → higher rent; higher floor → lower rent; broadband weakly positive. (b) Only **after feature scaling** are magnitudes comparable; on raw scales the weight absorbs the feature's units, so "9× as important" is invalid unscaled. Reference §9.</details>

**R7 — correlation ≠ causation.** For each, name the mechanism (chance / confounder / mixed population): (a) ice-cream sales correlate with drownings; (b) shoe size correlates with income; (c) July Berlin temperatures correlate with a die showing 25–30.
<details><summary>answer</summary> (a) confounder (hot weather drives both); (b) inappropriate mixed population (sex confounds both); (c) pure chance. To argue causation: exclude confounders + run an interventional experiment. Reference §10.</details>

**R8 — read the scatterplot (the four issues).** Match each to Y1–Y4: (i) a clear straight-line trend; (ii) a U-shaped cloud fit by a flat line; (iii) a tight line plus one far-off point pulling the slope; (iv) a shapeless blob with r≈0.4 by accident.
<details><summary>answer</summary> (i)=Y1 fine; (ii)=Y2 non-linear mismodelled; (iii)=Y3 outlier; (iv)=Y4 meaningless. Moral: always plot before trusting r. Reference §5 (Anscombe).</details>

---

## 3. Exam-format practice (timed, self-graded)

- ⭐ **Bridge §5 dual-purpose self-test** — the main event; proves SaD+AML readiness.
- **FAU Erlangen WS14/15** — the correlation-test / regression item, self-graded with the Lösung.
- **Fahrmeir *Arbeitsbuch* Ch 3** — covariance/correlation/regression problems with solutions.
- **UE2** — the SaD sheet; collect the walked-through solution in the Übung.

---

## 4. Concept self-checks (external, solution-backed)

> The Bridge §7 has the full verified video library. The high-value picks for L03:

- ⭐ **StatQuest — "Pearson's Correlation, Clearly Explained"**, **"Linear Regression / Least Squares"**, **"Gradient Descent, Step-by-Step"**. Watch, then re-derive R1–R3 without pausing.
- **3Blue1Brown — "Gradient descent, how neural networks learn"** (Ch 2 of the NN series) — the error-surface intuition for §8.
- **StatQuest — "Ridge/Lasso Regression"** — forward-link for §10 regularization.
- **Kelleher Ch 7** (local) — the rent example worked in full (§9).

---

## 5. Suggested sequence (~3.5 h)

1. **R1–R2** (covariance → Pearson → LS line) — the by-hand core; SaD exam favourite.
2. **R3–R4** (one GD step + normal-equation setup) — know both solution routes.
3. **R5–R6** (loss choice + scaling + weight interpretation) — the "explain why" items.
4. **R7–R8** (causation + scatterplot reading) — fast, conceptual.
5. **Bridge §5 self-test** (timed) → then FAU / Arbeitsbuch Ch 3 for volume.

Anything you miss → reread the cited § in `SaD_L03_Ultimate_Reference.md`, or the matching Bridge tier for depth.

---

*No HU SaD Altklausuren are public (Moodle/Fachschaft only). Above = SaD sheet + Bridge self-test + solved external material + Kelleher. All keys verified numerically.*
