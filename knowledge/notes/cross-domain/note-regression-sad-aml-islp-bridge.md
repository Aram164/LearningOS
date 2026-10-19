---
id: note-regression-sad-aml-islp-bridge
type: note
title: "Regression — The SaD × AML × ISLP Bridge"
created: "2026-06-06"
role: synthesis
state: evolving
authorship: mixed
concepts: [concept-linear-regression, concept-mean-squared-error, concept-normal-equation,
  concept-regularization, concept-variance, concept-descriptive-statistics,
  concept-statistical-estimation, concept-gradient-descent, concept-bias-variance-tradeoff]
sources: [source-sad-ss26-lectures, source-aml-ss26-lectures, source-islp,
  source-fahrmeir-statistik, source-statquest]
contexts: [workspace-m2-exam-prep]
---

> **Migration note (2026-07-17, Stage-1 pilot):** body preserved verbatim from
> `Plans/ML/foundations/reference/Regression_SaD-AML-ISLP_Bridge.md` (legacy tree).
> Built KW 23 (June 2026) to answer: what do AML L03/L04 apply that SaD 03 teaches,
> and how do the three notations (k = β₁ = w) fit together — the study script for
> Foundations Blocks E + H.

# Regression — The SaD × AML × ISLP Bridge

*A connected study plan for the single topic that links both modules: **regression**.*
*Created KW 23 (Jun 2026) | Companion to `AML_L02_Ultimate_Reference`*
*Goal: understand what AML L03/L04 are **applying**, pass the SaD exam, and build masters/BIFOLD-grade depth — all from one topic studied once, properly.*

---

## 0. Why this document exists

You noticed that **AML lectures 3 and 4 feel like "pure application"** — and you're right. Patrick Schäfer's slides hand you the *machinery* (MSE loss, the normal equation `w = (XᵀX)⁻¹Xᵀy`, Ridge/Lasso) but assume you already own the *statistics and the why*. That "why" is exactly what SaD (Akbik) teaches, and what ISLP fills in at textbook depth.

So regression is the perfect spine: **one topic, three views.**

| View | Source | What it gives you | Question it answers |
|---|---|---|---|
| **Statistical** | SaD 03, 06, 08, 09 | Correlation → regression line; the error model; *why* squared error; how good is the estimate | "What is the relationship in the data, and how confident am I?" |
| **ML / applied** | AML L03, L04 | Loss minimization, vectorization, normal equation, regularization | "How do I fit and generalize a predictor by minimizing a loss?" |
| **Textbook depth** | ISLP Ch 3, Ch 6.2 | Rigorous derivations, inference (SE, CI, t-test), R², shrinkage geometry | "Why does each piece work, and how do I interpret it?" |

The three are the **same object** seen from three angles. SaD writes the line as `f(x) = kx + d`. ISLP writes `ŷ = β₀ + β₁x`. AML writes `h_w(x) = wᵀx`. **k = β₁ = w.** Once you see that, you study for both modules at the same time.

---

## 1. What AML L03 and L04 actually apply (the demand list)

I read both decks slide by slide. Here is everything they *use* but don't *teach*:

**AML L03 — Linear Regression (one predictor)**
- Parametrize a line `h_w(x) = w₁x + w₀` (slope/intercept) — *precalc*
- Loss = **Mean Squared Error** `MSE = (1/2m) Σ (w₁x⁽ⁱ⁾+w₀ − y⁽ⁱ⁾)²` — *needs: variance / sum-of-squares idea (SaD 02)*
- Minimize by **taking the derivative and setting it to 0**; MSE is a convex parabola → unique minimum — *needs: single-variable calculus + convexity*
- 2-parameter case → **paraboloid**, minimize via **partial derivatives** `dL/dw₀ = dL/dw₁ = 0` — *needs: multivariable calculus*
- **Linear algebra refresher**: transpose, dot product, matrix–vector & matrix–matrix product, matrix inverse, vectorization

**AML L04 — Multivariate / Non-linear / Regularization**
- **Design matrix** `X ∈ ℝ^(m×(n+1))` with a **bias column of 1s**; vectorized loss `L(w) = (1/2m)‖Xw − y‖²`
- **Normal equation**: take `n+1` partial derivatives, set the gradient to 0 →
  `dL/dw = (1/m)(XᵀXw − Xᵀy) = 0` ⟹ **`w = (XᵀX)⁻¹Xᵀy`** — *needs: gradient of a quadratic form, matrix inverse*
- **Polynomial / basis features** (non-linear in x, still **linear in the parameters**)
- **Regularization**: Ridge (L2, `+λ‖w‖²`), Lasso (L1, `+λ‖w‖₁`) — *needs: overfitting/bias-variance (you have this from Block D), and the geometry of the penalty*

**The punchline:** AML L03/L04 are 80% *one statistics lecture (SaD 03) + one calculus skill (partial derivatives) + one linear-algebra skill (matrix calculus)*. Master those and the lectures stop feeling like magic.

---

## 2. The SaD concepts you must own — ranked, with the AML payoff

This is the heart of your request: **which SaD concepts to understand really well, and why.** Ordered by dependency. Each tier unlocks the next. The 🎥 links are vetted explainers — watch the one for any concept that isn't automatic yet.

### Tier 0 — Foundations (make these reflexive)
| # | Concept | SaD home | Why AML needs it |
|---|---|---|---|
| 0.1 | Sample mean `x̄`, variance `s²`, std dev `s` | SaD 02 | MSE *is* a mean of squared errors; the variance formula `Σ(xᵢ−x̄)²` is the same sum-of-squares you minimize |
| 0.2 | Summation `Σ`, function/line `y = kx + d` | SaD 01–02 | Every loss is a sum; the hypothesis is a line |
| 0.3 | **Derivative = 0 to find a minimum**; convex parabola | (calculus prereq) | This is *literally* how L03 solves regression |
| 0.4 | **Partial derivatives & the gradient** | (calculus prereq) | L03's 2-var case and L04's n-var normal equation are "set every partial to 0" |

🎥 Calculus intuition (optional but excellent): [3Blue1Brown — Gradient descent, how neural networks learn](https://www.youtube.com/watch?v=IHZwWFHWa-w) shows the "follow the slope downhill" picture that derivative-=-0 and gradient descent share.

### Tier 1 — The statistical bridge (SaD 03 — study this one *cold*)
This single lecture is the most important thing you can master for both modules.

| # | Concept | SaD home | The AML / ISLP connection |
|---|---|---|---|
| 1.1 | **Covariance** `s_xy` | SaD 03 (slides ~7–12) | Numerator of the slope; "do x and y move together?" |
| 1.2 | **Pearson correlation** `r_xy = s_xy/(s_x·s_y) ∈ [−1,1]` (Cauchy–Schwarz proof) | SaD 03 | Normalized covariance. Its square is **R²** in ISLP 3.1.3 |
| 1.3 | **Simple regression closed form**: `k = r_xy·(s_y/s_x)`, `d = ȳ − k·x̄`, derived by `∂S/∂k = ∂S/∂d = 0` | SaD 03 (slides 13–16) | **Same minimization AML L03 does**, just scalar instead of matrix. This is the cross-wire: `k = β₁ = w₁` |
| 1.4 | **Why squared error (L2)?** differentiable (unlike MAD `Σ|·|`); SaD even notes "optimal under normal errors" | SaD 03 + foreshadows SaD 08 | Justifies AML's choice of MSE — it's not arbitrary |
| 1.5 | **Multivariate form** `k = (AᵀA)⁻¹Aᵀy` | SaD 03 (MLR section) | **Identical** to AML's `w = (XᵀX)⁻¹Xᵀy`. You've already seen the normal equation! |
| 1.6 | **Gradient descent**: error surface, learning rate α, update rule, convergence | SaD 03 (slides 29–37) | The alternative to the matrix inverse; becomes THE algorithm in AML L06 and all of deep learning |

🎥 [StatQuest — Covariance, Clearly Explained](https://www.youtube.com/watch?v=qtaqvPAeEJY) → [Pearson's Correlation](https://www.youtube.com/watch?v=xZ_z8KWkhXE) → [Linear Regression / Least Squares, the Main Ideas](https://www.youtube.com/watch?v=PaFPbb66DxQ) → [Gradient Descent, Step-by-Step](https://www.youtube.com/watch?v=sDv4f4s2SB8).

### Tier 2 — Linear algebra (turns SaD's scalars into AML's matrices)
| # | Concept | Where | Why |
|---|---|---|---|
| 2.1 | Vectors & **dot product** `wᵀx` | AML L03 refresher | The hypothesis `h_w(x) = wᵀx` is one dot product |
| 2.2 | **Transpose, matrix–vector, matrix–matrix product** | AML L03 | To read `Xw`, `XᵀX`, `Xᵀy` |
| 2.3 | **Matrix inverse** & the **normal equation** `(XᵀX)⁻¹Xᵀy` | AML L04 | The closed-form solution; also *why* it can fail (collinearity → `XᵀX` not invertible → motivates Ridge) |
| 2.4 | **Design matrix + bias-column trick** (column of 1s absorbs `w₀`) | AML L04 | The slick move that makes `h_w(x) = wᵀx` cover the intercept too |

🎥 [3Blue1Brown — Matrix multiplication as composition](https://www.youtube.com/watch?v=XkY2DOUCWMU) and [Dot products and duality](https://www.youtube.com/watch?v=LyGKycYT2v0) (from *Essence of Linear Algebra* — the whole [playlist](https://www.youtube.com/playlist?list=PLZHQObOWTQDPD3MizzM2xVFitgF8hE_ab) is worth it for your masters).

### Tier 3 — The probabilistic "why" (SaD 06 + 08 — masters-grade depth)
This is where you stop *applying* MSE and start *understanding* it.

| # | Concept | SaD home | Payoff |
|---|---|---|---|
| 3.1 | **Random variable, E[X], Var(X)**; population vs sample (`x̄ ↔ E[X]`, `s² ↔ Var(X)`) | SaD 06 (slides 1–35) | The notation `E[(Y−Ŷ)²]` in ISLP becomes readable; foundation for inference |
| 3.2 | **The error model** `Y = f(X) + ε`, `ε ~ N(0, σ²)`; normal distribution, CLT | SaD 08 | The statistical *model* behind the line; `σ²` is the irreducible noise |
| 3.3 | ⭐ **MLE → MSE derivation** (assume normal errors → maximize likelihood → minimize `Σεᵢ²`) | SaD 08 (slides 29–36) | The deepest "aha": MSE is **not a choice, it's a consequence** of assuming Gaussian noise. This is the bridge between SaD's probability half and AML's loss half |

🎥 [StatQuest — Maximum Likelihood, Clearly Explained](https://www.youtube.com/watch?v=XepXtl9YKwc) and the prerequisite [Probability is not Likelihood](https://www.youtube.com/watch?v=pYxNSUDSFH4).

### Tier 4 — Inference / "how good is the fit?" (SaD 09–10 + ISLP 3.1.2–3.1.3)
This is the section that was tripping you up earlier. It's **not needed for AML L03/L04**, but it's a **major SaD exam topic** and it's what separates a statistician from someone who just runs `.fit()`. Do it *after* Tier 3.

| # | Concept | Home | Note |
|---|---|---|---|
| 4.1 | **Estimator is a random variable**; sampling distribution; unbiasedness `E[β̂]=β` | SaD 09 / ISLP 3.1.2 | Different sample → different `β̂`. ISLP's Fig 3.3 (10 datasets → 10 lines) *is* this |
| 4.2 | **Standard error** `SE(μ̂)=σ/√n` → `SE(β̂₀), SE(β̂₁)` | SaD 09 / ISLP 3.1.2 | The whole section is the `μ̂` story applied to `β̂` |
| 4.3 | **Confidence interval** `β̂₁ ± 2·SE` | SaD 09 / ISLP 3.1.2 | |
| 4.4 | **Hypothesis test on a coefficient**: `t = β̂₁/SE(β̂₁)`, p-value, `H₀: β₁=0` | SaD 10 / ISLP 3.1.2 | "Is this predictor actually useful?" |
| 4.5 | **Model accuracy**: RSE (estimates σ), **R² = correlation²** | ISLP 3.1.3 | R² ties straight back to Tier 1.2 |
| 4.6 | Multiple regression questions, **F-test**, variable selection | ISLP 3.2 | Extends 4.4 to "are *any* predictors useful?" |

🎥 [StatQuest — The Standard Error](https://www.youtube.com/watch?v=XNgt7F6FqDU) → [Confidence Intervals](https://www.youtube.com/watch?v=TqOeMYtOc1w) → [p-values: what they are & how to interpret them](https://www.youtube.com/watch?v=vemZtEM63GY) → [R-squared, Clearly Explained](https://www.youtube.com/watch?v=2AQKmw14mHM).

### Tier 5 — Regularization (AML L04 + ISLP 6.2 — high masters/BIFOLD value)
| # | Concept | Home | Note |
|---|---|---|---|
| 5.1 | Overfitting / bias-variance (recap) | Block D ✅ | The *problem* regularization solves |
| 5.2 | Polynomial & basis features (linear in params) | AML L04 / ISLP 3.3.2 | How "linear" models fit curves |
| 5.3 | **Ridge (L2)** `w = (XᵀX + λI)⁻¹Xᵀy`; also *fixes* the non-invertible `XᵀX` from Tier 2.3 | AML L04 / ISLP 6.2 | Shrinks all weights |
| 5.4 | **Lasso (L1)** → sparsity (some weights → exactly 0 = feature selection); diamond-vs-circle geometry | AML L04 / ISLP 6.2 | |

🎥 [StatQuest — Ridge (L2) Regression](https://www.youtube.com/watch?v=Q81RR3yKn30) → [Lasso (L1) Regression](https://www.youtube.com/watch?v=NGf0voTMlcs) → [Ridge vs Lasso, Visualized](https://www.youtube.com/watch?v=Xm2C_gTAl8c).

---

## 3. The 5 cross-wire moments (the connections to actively hunt for)

These are the specific "same idea, two modules" links. Spotting them is how studying one studies the other.

1. **The regression line, three notations →** SaD `k = r_xy·s_y/s_x` = ISLP `β₁` = AML `w₁`. (Tier 1.3)
2. **The normal equation appears in SaD first →** SaD's `k = (AᵀA)⁻¹Aᵀy` (Tier 1.5) is *identical* to AML's `w = (XᵀX)⁻¹Xᵀy` (Tier 2.3). AML just renames the matrices.
3. **Why MSE? →** SaD 03 says "differentiable, unlike MAD"; SaD 08 *proves* it via MLE under Gaussian errors (Tier 3.3). AML simply *uses* MSE. You'll know the reason they don't state.
4. **R² is just correlation² →** ISLP 3.1.3's headline goodness-of-fit metric is the square of SaD 03's Pearson `r_xy` (Tier 1.2 ↔ 4.5).
5. **Gradient descent: "alternative" → "everything" →** SaD 03 introduces GD as a fallback when the inverse is expensive (Tier 1.6); AML L06 + deep learning reveal it as the universal training algorithm.

---

## 4. The ordered study sequence (your actual plan)

Maps onto your Foundations **Block E** (+ touches H, G, J). Roughly 3 focused sessions; do the videos *before* the reading in each step.

**Session 1 — The bridge (≈3h). Goal: never feel "magic" in AML L03 again.**
1. Re-anchor Tier 0 (15 min self-check: can you minimize `f(w)=Σ(wx−y)²` by hand?).
2. **SaD 03 in full** (Tiers 1.1–1.6). This is the keystone lecture.
3. Watch StatQuest Covariance → Pearson → Least Squares.
4. **ISLP 3.1.1** (Estimating the Coefficients) — *not* 3.1.2 yet.
5. **AML L03** — now it reads as "SaD 03 in matrix form." Reproduce the MSE-vs-`w₁` parabola from the slides.
- ✅ Checkpoint: derive `k` and `d` from `∂S/∂k=∂S/∂d=0` on paper.

**Session 2 — Matrices & the normal equation (≈3h). Goal: own `w=(XᵀX)⁻¹Xᵀy`.**
1. Tier 2 linear algebra (3B1B matrix mult + dot product if rusty).
2. **AML L04 slides 1–22** (design matrix → vectorized loss → normal-equation derivation). Follow the partial-derivative proof line by line.
3. **ISLP 3.2** (Multiple Linear Regression).
- ✅ Checkpoint: explain why `XᵀX` must be invertible, and what breaks when features are collinear.

**Session 3 — The "why" + regularization (≈3h). Goal: depth + AML L04's second half.**
1. Tier 3: **SaD 06 (E[X], Var)** recap → **SaD 08 slides 29–36 (MLE→MSE)**. Watch StatQuest Maximum Likelihood first.
2. **AML L04 regularization slides** + Tier 5 videos (Ridge → Lasso → Visualized) + **ISLP 6.2**.
- ✅ Checkpoint: write the MLE→MSE chain in 5 steps; draw the L1-diamond vs L2-circle and explain why L1 zeroes weights.

**Session 4 (SaD-exam-focused, schedule later in Block J) — Inference (≈3h).**
- Tier 4: **SaD 09 + 10**, then **re-read ISLP 3.1.2 + 3.1.3** — it will finally click as "the `μ̂` story applied to `β̂`." Watch StatQuest Standard Error → CI → p-values → R².
- This is the part you correctly *parked* for AML; it's where the SaD exam points live.

---

## 5. Dual-purpose self-test (proves you're ready for both exams)

**AML / applied side**
- [ ] Starting from `L(w)=(1/2m)‖Xw−y‖²`, derive `∇L = (1/m)(XᵀXw − Xᵀy)` and the normal equation.
- [ ] Why is the bias handled by adding a column of 1s to X?
- [ ] Write Ridge's closed form and explain how `+λI` also cures a non-invertible `XᵀX`.
- [ ] When would you pick Lasso over Ridge?

**SaD / statistical side**
- [ ] From 5 points, compute `s_xy`, `r_xy`, then `k` and `d` by hand.
- [ ] Why minimize `Σ(yᵢ−kxᵢ−d)²` and not `Σ|yᵢ−kxᵢ−d|`? Give *both* reasons (differentiability + MLE).
- [ ] Walk the MLE→MSE derivation (normal errors → likelihood → log → drop constants → minimize `Σεᵢ²`).
- [ ] Construct a 95% CI for `β₁` given `β̂₁` and `SE(β̂₁)`; state `H₀`, compute `t`, interpret the p-value.

**The connection (the real test of understanding)**
- [ ] Show `k = β₁ = w₁` by writing all three formulas and reducing them to the same quantity.
- [ ] Explain in 3 sentences how R² relates to Pearson's `r_xy`.

---

## 6. For the masters / BIFOLD trajectory — where to go deeper

Once the above is solid, these are the threads worth pulling (beyond exam scope, high research value):
- **The normal equation vs. iterative solvers** — why large-scale ML never inverts `XᵀX` (O(n³) + numerical stability) and uses SGD instead. Directly relevant to systems/optimizer work (your AMLS + Stratum job).
- **Regularization as a prior** — Ridge = Gaussian prior on weights, Lasso = Laplace prior (the Bayesian view of Tier 3.3 + 5). This reframes regularization as MLE → MAP.
- **The bias-variance decomposition formally** (ISLP 2.2.2) as the theoretical backbone of why regularization helps.
- **Generalized linear models** (ISLP 4.6) — logistic/Poisson regression as the same machinery with a different link function; your next AML lectures (L05 logistic) live here.

---

## 7. Curated video library (all verified)

**Statistical bridge (SaD 03)**
- [Covariance, Clearly Explained — StatQuest](https://www.youtube.com/watch?v=qtaqvPAeEJY)
- [Pearson's Correlation — StatQuest](https://www.youtube.com/watch?v=xZ_z8KWkhXE)
- [Fitting a Line / Least Squares, Main Ideas — StatQuest](https://www.youtube.com/watch?v=PaFPbb66DxQ)
- [Linear Regression, Clearly Explained — StatQuest](https://www.youtube.com/watch?v=7ArmBVF2dCs)

**Linear algebra (AML refresher)**
- [Matrix multiplication as composition — 3Blue1Brown](https://www.youtube.com/watch?v=XkY2DOUCWMU)
- [Dot products and duality — 3Blue1Brown](https://www.youtube.com/watch?v=LyGKycYT2v0)
- [Essence of Linear Algebra (full playlist) — 3Blue1Brown](https://www.youtube.com/playlist?list=PLZHQObOWTQDPD3MizzM2xVFitgF8hE_ab)

**Optimization (SaD 03 GD → AML L06)**
- [Gradient Descent, Step-by-Step — StatQuest](https://www.youtube.com/watch?v=sDv4f4s2SB8)
- [Stochastic Gradient Descent — StatQuest](https://www.youtube.com/watch?v=vMh0zPT0tLI)
- [Gradient descent, how neural networks learn — 3Blue1Brown](https://www.youtube.com/watch?v=IHZwWFHWa-w)

**The "why" (SaD 08 MLE→MSE)**
- [Maximum Likelihood, Clearly Explained — StatQuest](https://www.youtube.com/watch?v=XepXtl9YKwc)
- [Probability is not Likelihood — StatQuest](https://www.youtube.com/watch?v=pYxNSUDSFH4)

**Inference (SaD 09–10 / ISLP 3.1.2–3.1.3)**
- [The Standard Error — StatQuest](https://www.youtube.com/watch?v=XNgt7F6FqDU)
- [Confidence Intervals — StatQuest](https://www.youtube.com/watch?v=TqOeMYtOc1w)
- [p-values: what they are & how to interpret them — StatQuest](https://www.youtube.com/watch?v=vemZtEM63GY)
- [R-squared, Clearly Explained — StatQuest](https://www.youtube.com/watch?v=2AQKmw14mHM)

**Regularization (AML L04 / ISLP 6.2)**
- [Ridge (L2) Regression — StatQuest](https://www.youtube.com/watch?v=Q81RR3yKn30)
- [Lasso (L1) Regression — StatQuest](https://www.youtube.com/watch?v=NGf0voTMlcs)
- [Ridge vs Lasso, Visualized — StatQuest](https://www.youtube.com/watch?v=Xm2C_gTAl8c)

---

*Sources synthesized from: AML L03 + L04 (Schäfer, HU SoSe 2025/26); SaD 03/06/08/09 (Akbik, HU); ISLP Ch 3 + 6.2 (James, Witten, Hastie, Tibshirani). Maps to Foundations Block E (primary), with H, G, J touchpoints.*
