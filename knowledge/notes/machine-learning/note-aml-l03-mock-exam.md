---
id: note-aml-l03-mock-exam
type: note
title: "AML Lecture 03 — Mock Exam (Linear Regression, one predictor + Linear Algebra + Vectorization)"
created: "2026-07-11"
role: mock-exam
state: evolving
authorship: mixed
concepts: [concept-linear-regression, concept-mean-squared-error, concept-normal-equation]
sources: [source-aml-ss26-lectures]
contexts: [workspace-aml-exam-prep]
---

> **Migration note (2026-07-17, Stage 2):** body preserved verbatim from
> `Plans/ML/foundations/AML/my notes/lect03 linear regression/AML_L03_Mock_Exam.md` (legacy tree).

# AML Lecture 03 — Mock Exam (Linear Regression, one predictor + Linear Algebra + Vectorization)

**Topic:** regression problem, MSE loss, the closed-form solution, dot products / matrix algebra, the bias trick & vectorization.
**Companion:** `AML_L03_Ultimate_Reference.md` (section refs given in the answer key).
**Suggested time:** 75 minutes, closed-book. Answer everything on paper *before* opening the answer key, then self-grade.

> Scoring: Part A = 20 (2 each), Part B = 40, Part C = 15 (3 each), Part D = 25. Total 100.

---

## Part A — Conceptual Short Answer (2 pts each)

**A1.** What distinguishes **regression** from **classification**? Give the output space for each.

**A2.** Why is **squared** error preferred over **absolute** error as the regression loss? (Mention differentiability.)

**A3.** What does the **`1/2`** in the `(1/2m)` MSE accomplish? Does it change the optimal `𝐰`?

**A4.** Is the dot product `𝐱·𝐲` a scalar or a vector? What about the Hadamard product `𝐱⊙𝐲`?

**A5.** The MSE loss for linear regression is **convex**. What does that guarantee about its minimum?

**A6.** What does a dot product of **0** between two vectors mean geometrically?

**A7.** Explain the **bias trick** (`x₀ = 1`). What problem does it solve?

**A8.** Give the shapes of `𝐱ᵀ𝐱` and `𝐱𝐱ᵀ` for `𝐱 ∈ ℝⁿ`. Why do they differ?

**A9.** In `w₁ = Σ(xⁱ−x̄)(yⁱ−ȳ) / Σ(xⁱ−x̄)²`, what statistical quantities are the **numerator** and **denominator**?

**A10.** Through which point does the fitted regression line **always** pass?

---

## Part B — Numerical Problems (show your work)

### B1. Closed-form simple regression (12 pts)

Data: **(1, 1), (2, 3), (3, 2), (4, 4)**.
(a) Compute `x̄` and `ȳ`. (b) Compute `w₁` and `w₀`. (c) Write `h_𝐰(x)`. (d) Compute the MSE `(1/2m)Σ(h−y)²` at the optimum.

### B2. Dot products & norms (10 pts)

`𝐱 = (2, −1, 2)`, `𝐲 = (1, 2, 0)`.
(a) Compute `𝐱·𝐲`. (b) Are `𝐱` and `𝐲` orthogonal? (c) Compute `‖𝐱‖₂`. (d) Verify `𝐱·𝐱 = ‖𝐱‖₂²`.

### B3. The line-fitting parabola (10 pts)

Data **(1, 1), (2, 2), (3, 3)**, intercept fixed at `w₀ = 0`.
Compute `MSE(w₁)` for `w₁ = 0`, `0.5`, `1`. Which is the minimum? What shape does `MSE(w₁)` trace, and why does that shape matter?

### B4. Matrix shapes (8 pts)

For `X ∈ ℝ^{m×(n+1)}`, `𝐰 ∈ ℝⁿ⁺¹`, `𝐲 ∈ ℝᵐ`, give the shape of each:
(a) `Xᵀ`  (b) `X𝐰`  (c) `XᵀX`  (d) `Xᵀ𝐲`  (e) `(XᵀX)⁻¹Xᵀ𝐲`.
(f) For `𝐮, 𝐯 ∈ ℝⁿ`: is `𝐮ᵀ𝐯` a scalar or a matrix? What about `𝐮𝐯ᵀ`?

---

## Part C — True / False + One-Line Justification (3 pts each)

**C1.** The dot product of two vectors is itself a vector.

**C2.** In NumPy, `x * y` computes the dot product.

**C3.** Matrix multiplication is commutative (`AB = BA`).

**C4.** Minimizing MSE and minimizing `½·MSE` yield the same weights.

**C5.** `𝐱ᵀ𝐱` and `𝐱𝐱ᵀ` have the same shape.

---

## Part D — Synthesis & Derivation (25 pts)

**D1. (9 pts)** Starting from `L = (1/2m) Σᵢ (w₁x⁽ⁱ⁾ + w₀ − y⁽ⁱ⁾)²`, derive the partial derivatives **`∂L/∂w₀`** and **`∂L/∂w₁`** using the chain rule. State the two equations you'd set to zero.

**D2. (8 pts)** Show that the closed-form slope equals **`cov(x,y)/var(x)`**, and show the regression line **passes through `(x̄, ȳ)`**.

**D3. (8 pts) Bias trick & vectorization.** (a) Rewrite `h_𝐰(x) = w₁x₁ + w₀` as a single dot product. (b) Write the **whole-dataset** loss as the (scaled) squared norm of a matrix–vector expression. (c) Why is the vectorized form ~20× faster than a Python for-loop?

---
---

# ANSWER KEY

> Section references (§) point to `AML_L03_Ultimate_Reference.md`.

## Part A

**A1.** (§1) **Regression** predicts a **continuous** output (`Y = [0, ∞)`, e.g. price); **classification** predicts a **discrete** label (`Y = {0,…,9}`, e.g. MNIST digit).

**A2.** (§4) The square is **differentiable everywhere**; the absolute value has a non-differentiable kink at 0. Differentiability is what enables a clean **closed form** and **gradient descent**. (It also penalizes large errors more.)

**A3.** (§4) The `1/2` cancels the factor 2 that drops out when you differentiate the square, keeping gradients clean. It **does not** change the optimal `𝐰` (scaling a loss doesn't move its minimizer).

**A4.** (§0, §10) `𝐱·𝐲` → **scalar** (`Σ xⱼyⱼ`). `𝐱⊙𝐲` → **vector** (component-wise, no sum).

**A5.** (§5) Convexity guarantees a **single global minimum** — no local minima/traps; setting `∇L = 0` finds the unique best `𝐰`.

**A6.** (§10) The two vectors are **orthogonal (perpendicular, 90°)**.

**A7.** (§15) Append a constant feature `x₀ = 1` so the intercept `w₀` becomes "just another weight." Then `h_𝐰(x) = 𝐰·𝐱` is a **single dot product** — it lets the intercept ride inside the vectorized machinery.

**A8.** (§12) `𝐱ᵀ𝐱` = (1×n)(n×1) = **scalar** (`= ‖𝐱‖²`). `𝐱𝐱ᵀ` = (n×1)(1×n) = **n×n matrix** (outer product). Order of the transpose flips the shape.

**A9.** (§8) Numerator = (unnormalized) **covariance** `cov(x,y)`; denominator = (unnormalized) **variance** `var(x)`. So `w₁ = cov(x,y)/var(x)`.

**A10.** (§7) The **centroid `(x̄, ȳ)`** — since `w₀ = ȳ − w₁x̄` ⟹ `h_𝐰(x̄) = ȳ`.

## Part B

**B1.** (§7)
(a) `x̄ = (1+2+3+4)/4 = 2.5`, `ȳ = (1+3+2+4)/4 = 2.5`.
(b) numerator `Σ(x−x̄)(y−ȳ) = (−1.5)(−1.5)+(−0.5)(0.5)+(0.5)(−0.5)+(1.5)(1.5) = 2.25−0.25−0.25+2.25 = 4`; denominator `Σ(x−x̄)² = 2.25+0.25+0.25+2.25 = 5`. So **`w₁ = 4/5 = 0.8`**, **`w₀ = 2.5 − 0.8·2.5 = 0.5`**.
(c) **`h_𝐰(x) = 0.8x + 0.5`**.
(d) predictions `1.3, 2.1, 2.9, 3.7`; residuals `−0.3, 0.9, −0.9, 0.3`; squares `0.09, 0.81, 0.81, 0.09` → sum `1.8`; **MSE = 1.8/(2·4) = 0.225**.

**B2.** (§9–10) (a) `𝐱·𝐲 = 2·1 + (−1)·2 + 2·0 = 0`. (b) **Yes, orthogonal** (dot product 0). (c) `‖𝐱‖₂ = √(4+1+4) = √9 = 3`. (d) `𝐱·𝐱 = 4+1+4 = 9 = 3² = ‖𝐱‖₂²` ✓.

**B3.** (§5) With `h(x)=w₁x`: residuals `(w₁·i − i)` for `i=1,2,3`.

| `w₁` | MSE = (1/6)Σ(w₁x−y)² |
|---|---|
| 0 | (1+4+9)/6 = **2.333** |
| 0.5 | (0.25+1+2.25)/6 = **0.583** |
| 1 | 0 → **0 (minimum)** |

`MSE(w₁)` is a **parabola** (convex) → it has a single minimum, which is exactly why setting the derivative to zero finds the best slope. (At `w₁=1` the line `y=x` fits perfectly.)

**B4.** (§12, §16) (a) `Xᵀ` → **(n+1)×m**. (b) `X𝐰` → **m×1** (all predictions). (c) `XᵀX` → **(n+1)×(n+1)**. (d) `Xᵀ𝐲` → **(n+1)×1**. (e) `(XᵀX)⁻¹Xᵀ𝐲` → **(n+1)×1** (the weight vector). (f) `𝐮ᵀ𝐯` = **scalar** (the dot product); `𝐮𝐯ᵀ` = **n×n matrix** (outer product).

## Part C

**C1.** **False.** It's a **scalar** — `𝐱·𝐲 = Σxⱼyⱼ ∈ ℝ`. (§0/§10)

**C2.** **False.** `x * y` is **element-wise (Hadamard)**; the dot product is `x @ y` / `np.dot`. (§14, §17)

**C3.** **False.** `AB ≠ BA` in general (matrix product is **not** commutative); it **is** associative. (§12)

**C4.** **True.** Scaling a loss by a positive constant doesn't move its minimizer. (§4)

**C5.** **False.** `𝐱ᵀ𝐱` is a **scalar** (1×1); `𝐱𝐱ᵀ` is an **n×n matrix**. (§12)

## Part D

**D1.** (§6) Let `g = w₁x⁽ⁱ⁾ + w₀ − y⁽ⁱ⁾`, `f(g)=g²`. By the chain rule `∂(g²)/∂w = 2g·∂g/∂w`. The `2` cancels the `1/2`:

$$\frac{\partial L}{\partial w_0} = \frac{1}{m}\sum_i (w_1x^{(i)}+w_0-y^{(i)})\cdot 1, \qquad \frac{\partial L}{\partial w_1} = \frac{1}{m}\sum_i (w_1x^{(i)}+w_0-y^{(i)})\cdot x^{(i)}.$$

Set both to **0** and solve the two equations simultaneously.

**D2.** (§7–8) From `∂L/∂w₀ = 0`: `Σ(w₁x+w₀−y) = 0` ⟹ `w₀ = ȳ − w₁x̄`, so `h_𝐰(x̄) = w₁x̄ + (ȳ − w₁x̄) = ȳ` — the line passes through **`(x̄, ȳ)`**. Substituting `w₀` into `∂L/∂w₁ = 0` and simplifying gives `w₁ = Σ(x−x̄)(y−ȳ)/Σ(x−x̄)²`, whose numerator/denominator are (unnormalized) **cov(x,y)** and **var(x)** → `w₁ = cov/var`.

**D3.** (§15–17) (a) With `x₀=1`: `𝐰=(w₀,w₁)`, `𝐱=(1,x₁)` ⟹ `h_𝐰(x) = 𝐰·𝐱 = w₀ + w₁x₁`. (b) Stacking examples as rows of `X`, predictions are `X𝐰` and residuals `X𝐰−𝐲`, so `L(𝐰) = (1/2m)‖X𝐰 − 𝐲‖₂²`. (c) The vectorized form runs as **compiled C/BLAS loops** instead of a slow Python interpreter loop — Übung 03 measured ~20× (`for-loop 0.0112s → dot 0.00056s`).

---

*Self-grade, then for any miss reread the cited § in `AML_L03_Ultimate_Reference.md`. Numerical answers are computer-verified.*
