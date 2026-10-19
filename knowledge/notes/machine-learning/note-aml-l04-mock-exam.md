---
id: note-aml-l04-mock-exam
type: note
title: "AML Lecture 04 — Mock Exam (Non-linear Regression: Multivariate, Normal Equation, Polynomial, Regularization)"
created: "2026-07-11"
role: mock-exam
state: evolving
authorship: mixed
concepts: [concept-basis-functions, concept-normal-equation, concept-regularization, concept-linear-regression]
sources: [source-aml-ss26-lectures]
contexts: [workspace-aml-exam-prep]
---

> **Migration note (2026-07-17, Stage 2):** body preserved verbatim from
> `Plans/ML/foundations/AML/my notes/lect04 non-linear regression/AML_L04_Mock_Exam.md` (legacy tree).

# AML Lecture 04 — Mock Exam (Non-linear Regression: Multivariate, Normal Equation, Polynomial, Regularization)

**Topic:** multivariate regression + the normal equation, singular `XᵀX`, polynomial/computed features, overfitting & bias–variance, Ridge & Lasso.
**Companion:** `AML_L04_Ultimate_Reference.md` (section refs in the answer key).
**Suggested time:** 75 minutes, closed-book. Solve everything before opening the key, then self-grade.

> Scoring: Part A = 20 (2 each), Part B = 40, Part C = 15 (3 each), Part D = 25. Total 100.

---

## Part A — Conceptual Short Answer (2 pts each)

**A1.** Write the multivariate hypothesis `h_𝐰(x)` for `n` features. What geometric object is it?

**A2.** State the **normal equation**. What is `(XᵀX)⁻¹Xᵀ` called?

**A3.** Give **two** reasons `XᵀX` can be **singular** (non-invertible).

**A4.** Name **two fixes** when `XᵀX` is singular.

**A5.** Why is the normal equation impractical for **very large `n`**? What replaces it?

**A6.** How do **polynomial features** let a *linear* model fit a curve? What exactly stays "linear"?

**A7.** Why does adding more features **always** lower the *training* error?

**A8.** In **Ridge**, which weight is **not** penalized, and why?

**A9.** Lasso vs Ridge: which produces **exactly-zero** weights? What is that property called?

**A10.** Besides reducing overfitting, what problem does the Ridge closed form `(XᵀX + λI)⁻¹Xᵀ𝐲` fix?

---

## Part B — Numerical Problems (show your work)

### B1. The Normal Equation (14 pts)

Design matrix (bias column + one feature) `X = [[1,1],[1,2],[1,3]]`, targets `𝐲 = (1, 2, 2)`.
(a) Compute `XᵀX`. (b) Compute `Xᵀ𝐲`. (c) Compute `det(XᵀX)` and `(XᵀX)⁻¹`. (d) Solve `𝐰 = (XᵀX)⁻¹Xᵀ𝐲`. (e) Write `h_𝐰(x)`.

### B2. Singular `XᵀX` (8 pts)

A design matrix's feature columns satisfy **column 3 = 2 × column 2** (e.g. size in ft² and size in "half-ft²").
(a) Why is `XᵀX` singular? (b) What is `det(XᵀX)`? (c) Give two ways to still fit the model.

### B3. Ridge shrinkage (10 pts)

Reuse `XᵀX = [[3,6],[6,14]]` and `Xᵀ𝐲 = [5, 11]` from B1. Apply **Ridge with `λ = 1`**, penalizing the *feature* weight but **not** the bias — i.e. add `diag(0, λ)`:
solve `𝐰 = (XᵀX + diag(0,1))⁻¹ Xᵀ𝐲`. Compare the **slope** to the OLS slope from B1. What happened, and to which weight?

### B4. Polynomial features (8 pts)

Feature map `φ(x) = (1, x, x²)`.
(a) Compute `φ(3)`. (b) Given the fitted model `h(x) = 2 + 3x − x²`, predict at `x = 3`. (c) Is this model linear in `x`? Linear in the **weights**? Explain why that distinction matters.

---

## Part C — True / False + One-Line Justification (3 pts each)

**C1.** The normal equation gives a valid solution even when `m < n`.

**C2.** Adding `+λI` to `XᵀX` can turn a singular matrix invertible.

**C3.** Lasso (L1) tends to drive weights to exactly 0; Ridge (L2) usually does not.

**C4.** Polynomial regression is **non-linear in the weights**.

**C5.** As `λ → ∞` in Ridge, **every** weight including the intercept `w₀` goes to 0.

---

## Part D — Synthesis & Derivation (25 pts)

**D1. (9 pts)** Starting from `∇L(𝐰) = (1/m) Xᵀ(X𝐰 − 𝐲)`, derive the **normal equation** `𝐰 = (XᵀX)⁻¹Xᵀ𝐲`. Give the **shape** of every factor and confirm the result is in `ℝⁿ⁺¹`.

**D2. (8 pts)** Explain how a **curve in x-space becomes a straight line in φ(x)-space**, and why the *entire* least-squares machinery (loss, gradient, normal equation) carries over **unchanged** to polynomial regression.

**D3. (8 pts) Ridge vs Lasso geometry.** Write both loss functions. Draw/describe the **L1 diamond** vs the **L2 circle** and explain why **L1 yields exact zeros** while L2 doesn't. Which weight is excluded from the penalty?

---
---

# ANSWER KEY

> Section references (§) point to `AML_L04_Ultimate_Reference.md`.

## Part A

**A1.** (§1) `h_𝐰(x) = w₁x₁ + … + wₙxₙ + w₀ = Σⱼ wⱼxⱼ = 𝐰·𝐱` (with `x₀=1`). Geometrically a **hyper-plane** in `(n+1)`-D.

**A2.** (§3) `𝐰 = (XᵀX)⁻¹Xᵀ𝐲`. `(XᵀX)⁻¹Xᵀ` is the **Moore–Penrose pseudo-inverse `X⁺`**.

**A3.** (§4) (1) **Redundant / linearly-dependent features** (one column a multiple/combination of others); (2) **too few examples**, `m ≤ n`.

**A4.** (§4) (1) `np.linalg.pinv` (pseudo-inverse / SVD); (2) **Ridge regularization** (`+λI`). *(Also: drop the redundant feature.)*

**A5.** (§5) Inverting an `(n+1)×(n+1)` matrix costs ≈ `O(n³)` — prohibitive for large `n`. **Gradient descent** (`𝐰 ← 𝐰 − α∇L`, L06) replaces it.

**A6.** (§6, §8) Transform the input with `φ(x)=(1,x,x²,…)` and regress on the expanded features. The model can be non-linear in `x` but is a **linear combination of (transformed) features with weights `𝐰`** — i.e. **linear in the weights** — so all the linear machinery still applies.

**A7.** (§9) If a new feature is useless, the model can just learn `wₖ = 0` and lose nothing — so training error can only **decrease or stay equal**. (That's why low train error is a trap; judge on test error.)

**A8.** (§12) The **intercept `w₀`** is not penalized — shifting the whole fit up/down isn't "complexity." The penalty sums `j = 1…n` only.

**A9.** (§13–14) **Lasso (L1)** → exactly-zero weights; this is **sparsity / automatic feature selection**. Ridge (L2) shrinks toward small but generally nonzero values.

**A10.** (§4, §12) It makes a **singular `XᵀX` invertible** (`XᵀX + λI` is positive-definite for `λ>0`).

## Part B

**B1.** (§3)
(a) `XᵀX = [[3, 6], [6, 14]]`.  (b) `Xᵀ𝐲 = [1+2+2, 1·1+2·2+3·2] = [5, 11]`.
(c) `det = 3·14 − 6·6 = 6`; `(XᵀX)⁻¹ = (1/6)[[14, −6], [−6, 3]]`.
(d) `𝐰 = (1/6)[[14,−6],[−6,3]]·[5,11] = (1/6)[70−66, −30+33] = (1/6)[4, 3] = [2/3, 1/2]`. So **`w₀ = 2/3 ≈ 0.667`, `w₁ = 1/2 = 0.5`**.
(e) **`h_𝐰(x) = 0.5x + 2/3`**. *(Cross-check with the L03 closed form: `x̄=2, ȳ=5/3`, `cov=1, var=2` → `w₁=0.5` ✓.)*

**B2.** (§4) (a) Column 3 is a scalar multiple of column 2, so the columns are **linearly dependent** → `X` is rank-deficient → `XᵀX` is **singular** (not full rank, no inverse). (b) `det(XᵀX) = 0`. (c) **Drop one of the duplicate features**, or use **`pinv`**, or **Ridge `+λI`**.

**B3.** (§12) `XᵀX + diag(0,1) = [[3, 6], [6, 15]]`; `det = 3·15 − 36 = 9`; inverse `(1/9)[[15,−6],[−6,3]]`.
`𝐰 = (1/9)[[15,−6],[−6,3]]·[5,11] = (1/9)[75−66, −30+33] = (1/9)[9, 3] = [1, 1/3]`.
So **`w₁` shrank from `0.5` → `1/3 ≈ 0.333`** (toward 0), exactly as Ridge intends; the **bias `w₀` was not shrunk** (it moved `2/3 → 1`, free to adjust because it's outside the penalty).

**B4.** (§6, §8) (a) `φ(3) = (1, 3, 9)`. (b) `h(3) = 2 + 3·3 − 3² = 2 + 9 − 9 = 2`. (c) It is **non-linear in `x`** (the `x²` term curves), but **linear in the weights** `(2, 3, −1)` — `h = 𝐰·φ(x)` is a linear combination of fixed features. That's why the **normal equation still works** (just with the expanded design matrix `φ(X)`).

## Part C

**C1.** **False.** With `m < n`, `XᵀX` is singular → `(XᵀX)⁻¹` doesn't exist. (§4)

**C2.** **True.** `XᵀX + λI` is positive-definite for `λ > 0`, hence invertible. (§4, §12)

**C3.** **True.** The L1 penalty's diamond has corners on the axes → optimum often lands at a zero; L2's circle is smooth → small but nonzero. (§14)

**C4.** **False.** Polynomial regression is **linear in the weights** (non-linear only in `x`). (§6)

**C5.** **False.** Only the **feature** weights `w₁…wₙ → 0`; the unpenalized intercept `w₀` stays free → the model becomes a flat line at the mean, not 0. (§12)

## Part D

**D1.** (§2–3) Set `∇L = 0`: `(1/m)Xᵀ(X𝐰 − 𝐲) = 0` ⟹ `XᵀX𝐰 = Xᵀ𝐲` ⟹ (multiply by `(XᵀX)⁻¹`) `𝐰 = (XᵀX)⁻¹Xᵀ𝐲`. Shapes: `Xᵀ (n+1)×m`, `X (m)×(n+1)` → `XᵀX (n+1)×(n+1)`, `(XᵀX)⁻¹ (n+1)×(n+1)`, `Xᵀ𝐲 (n+1)×1` → product **`(n+1)×1` ∈ ℝⁿ⁺¹** ✓.

**D2.** (§8) Apply `φ` to each input (e.g. `x → (1,x,x²)`). In the **original** `x`-axis the fitted function curves; in the **expanded `φ(x)`-axis** it's a flat hyper-plane `𝐰·φ(x)`. Because the model is still a linear combination of features with weights `𝐰`, the loss `(1/2m)‖φ(X)𝐰 − 𝐲‖²`, its gradient, and the solution `𝐰 = (φ(X)ᵀφ(X))⁻¹φ(X)ᵀ𝐲` are **identical in form** — only the design matrix changed from `X` to `φ(X)`.

**D3.** (§12–14) Losses (penalties exclude `w₀`):
`Ridge: (1/2m)‖X𝐰−𝐲‖² + λΣⱼ₌₁ⁿ wⱼ²` ; `Lasso: (1/2m)‖X𝐰−𝐲‖² + λΣⱼ₌₁ⁿ |wⱼ|`.
The penalty is a constraint region; the solution is where the elliptical MSE contours first touch it. The **L1 diamond** has **corners on the axes**, so the touch point tends to sit where some weight is **exactly 0** → sparsity. The **L2 circle** is smooth (no corners), so the touch is generically off-axis → small but nonzero weights. The **intercept `w₀` is excluded** from both penalties.

---

*Self-grade, then reread the cited § in `AML_L04_Ultimate_Reference.md` for any miss. All numerical answers are computer-verified.*
