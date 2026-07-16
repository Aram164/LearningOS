# SaD Lecture 03 — Mini Learning Plan (Correlation & Regression)

> **📌 Supports Block N1 (correlation) + N5 (regression).** SaD steps stay **F.*** in Chat1 — log completions in `SESSION-LOG.md` + tick SEMESTER-STATUS §3. Third per-lecture SaD unit (3-file variant, no Mock Exam).

> **📎 Use the Regression Bridge as your spine.** `Plans/ML/foundations/reference/Regression_SaD-AML-ISLP_Bridge.md` already has the ordered study sequence (§4), the tiered concept list (§2), and the verified video library (§7) for this exact topic across SaD + AML + ISLP. This mini-plan is the **SaD-lecture-scoped** entry point into it — do these steps for the Klausur, then follow the Bridge tiers for masters/BIFOLD depth.

Each step: **concept → video → book/tier → practice**. Practice in `SaD_L03_Exercise_Bank.md`; reference `SaD_L03_Ultimate_Reference.md` (same folder). Budget ~3.5 h.

---

## Step 1 — Covariance & Pearson correlation  (~40 min)

Scatterplots; covariance (direction, unit-dependent); Pearson r ∈ [−1,1] (scale-free); r as cosine of centered vectors (Cauchy–Schwarz).

- 🎥 ⭐ **StatQuest — "Pearson's Correlation, Clearly Explained."**
- 📖 **Fahrmeir Ch 3** (Kovarianz/Korrelation) *or* the **Bridge Tier 1** (study this cold).
- 📝 Reference §1–§2.
- ✍️ Exercise Bank **R1**.

## Step 2 — Simple linear regression + why L2  (~45 min)

The least-squares line k = r·s_y/s_x, d = ȳ − k·x̄; the derivation; why squared error (differentiable, = Gaussian MLE); the four scatterplot issues.

- 🎥 ⭐ **StatQuest — "Linear Regression, Clearly Explained" / "Least Squares."**
- 📖 **Bridge Tier 1** + Reference §3–§5.
- ✍️ Exercise Bank **R2** + **R8** (read the scatterplot) + **R5(a)** (why not MAD).

## Step 3 — MLR: the normal equation  (~40 min)

The model f = k₀+k₁x₁+…; design matrix A; k = (AᵀA)⁻¹Aᵀy; conditions (full rank, n>m, non-singular); O(m³) cost + numerical issues.

- 🎥 **3Blue1Brown — Essence of Linear Algebra** (matrix mult / dot products) for the algebra intuition.
- 📖 **Bridge Tier 2** (linear-algebra upgrade — turns SaD's scalars into AML's matrices).
- 📝 Reference §6–§7.
- ✍️ Exercise Bank **R4** (set up the normal equation).

## Step 4 — Gradient descent  (~50 min)

Error surface; the downhill step; learning rate / start / stopping; local minima (convex for L2 MLR); the gradient step 2Σ(f(xᵢ)−yᵢ)x_{j,i}; stochastic GD; complexity.

- 🎥 ⭐ **StatQuest — "Gradient Descent, Step-by-Step"** + **3B1B — "Gradient descent, how neural networks learn."**
- 📖 **Kelleher Ch 7** (error surfaces, learning rate, the rent example) — the SaD source.
- 📝 Reference §8.
- ✍️ Exercise Bank **R3** (one GD step by hand).

## Step 5 — Feature scaling, weight interpretation, beyond MLR  (~35 min)

Why scaling makes GD converge and weights comparable; sign vs magnitude; logistic/non-linear/ridge/lasso = regularization; correlation ≠ causation.

- 🎥 **StatQuest — "Ridge and Lasso Regression"** (forward-link) + any correlation≠causation explainer.
- 📖 **Bridge Tier 5** (regularization — high masters/BIFOLD value).
- 📝 Reference §9–§10.
- ✍️ Exercise Bank **R5(b), R6, R7**.

## Step 6 — Practice & self-test  (→ exercise bank + Bridge)

1. **UE2** → collect walked-through solution in the Übung.
2. **R1–R8** → keys in the bank.
3. ⭐ **Bridge §5 dual-purpose self-test** (timed) → proves SaD + AML readiness.
4. **FAU** correlation/regression item + **Arbeitsbuch Ch 3** for volume.

---

### Suggested schedule (~3.5 h)

| Session | Steps | Output |
|---|---|---|
| 1 | Steps 1–2 | covariance/Pearson + LS line cold; R1/R2/R5a/R8 |
| 2 | Steps 3–4 | both MLR solution routes; R3/R4 |
| 3 | Steps 5–6 | scaling/interpretation/causation; R5b/R6/R7 + Bridge self-test |

Next unit: **L04 (Probability & Bayes + Naïve Bayes)** — the formal home of L01's medical-test example; Blitzstein Ch 1–2 + Fahrmeir Ch 4 are the sources.
