---
id: note-aml-l05-mock-exam
type: note
title: "AML Lecture 05 — Mock Exam (Logistic Regression)"
created: "2026-07-11"
role: mock-exam
state: evolving
authorship: mixed
concepts: [concept-logistic-regression, concept-maximum-likelihood, concept-cross-entropy]
sources: [source-aml-ss26-lectures]
contexts: [workspace-aml-exam-prep]
---

> **Migration note (2026-07-17, Stage 2):** body preserved verbatim from
> `Plans/ML/foundations/AML/my notes/lect05 logistic regression/AML_L05_Mock_Exam.md` (legacy tree).

# AML Lecture 05 — Mock Exam (Logistic Regression)

**Topic:** classification, the decision boundary, the sigmoid, the logistic hypothesis as a probability, the cross-entropy loss (from MLE), the gradient, convexity & regularization.
**Companion:** `AML_L05_Ultimate_Reference.md` (section refs in the answer key).
**Suggested time:** 75 minutes, closed-book. Solve everything before opening the key, then self-grade.

> Scoring: Part A = 20 (2 each), Part B = 40, Part C = 15 (3 each), Part D = 25. Total 100.
> **Sigmoid table** (for Part B): σ(−3)=0.05, σ(−2)=0.12, σ(−1)=0.27, σ(0)=0.50, σ(1)=0.73, σ(2)=0.88, σ(3)=0.95.

---

## Part A — Conceptual Short Answer (2 pts each)

**A1.** Why does **linear-regression-with-a-0.5-threshold** fail for classification?

**A2.** Write the sigmoid `σ(z)`. Give `σ(0)`, `σ(+∞)`, `σ(−∞)`.

**A3.** In terms of `𝐰·𝐱`, when is `σ(𝐰·𝐱) ≥ 0.5`?

**A4.** What does `h_𝐰(x)` represent **probabilistically**? What is `1 − h_𝐰(x)`?

**A5.** Why can't we use **MSE** as the logistic-regression loss?

**A6.** From what **principle** is the cross-entropy loss derived?

**A7.** Write `∂L/∂wⱼ` for logistic regression. How does it differ from the **linear-regression** gradient?

**A8.** Is there a **closed-form** solution for logistic regression? If not, what do we use?

**A9.** The boundary `𝐰·𝐱 = 0` is **scale-invariant**. What does that mean?

**A10.** How do you get a **non-linear** (e.g. circular) decision boundary from a *linear* logistic model?

---

## Part B — Numerical Problems (use the sigmoid table)

### B1. Sigmoid & prediction (12 pts)

Weights `𝐰 = (w₀, w₁, w₂) = (−4, 1, 1)`.
(a) Write the decision boundary as a line `x₂ = …`.
(b) For each point compute `𝐰·𝐱`, then `σ(𝐰·𝐱)`, then the predicted label: **(3, 3)**, **(1, 1)**, **(4, 1)**.

### B2. Decision boundary (8 pts)

`𝐰 = (−6, 2, 1)`.
(a) Rewrite `𝐰·𝐱 = 0` as a line `x₂ = a·x₁ + b`. (b) Classify the point **(1, 5)**.

### B3. Cross-entropy loss (12 pts)

Three samples `(y, h)`: `(1, 0.9)`, `(0, 0.2)`, `(1, 0.4)`. Compute the loss
`L = −(1/3) Σ [ y·ln h + (1−y)·ln(1−h) ]`.
Use `ln 0.9 ≈ −0.105`, `ln 0.8 ≈ −0.223`, `ln 0.4 ≈ −0.916`.

### B4. The gradient (8 pts)

Two examples `𝐱⁽¹⁾ = (1, 2, 1)` with `y⁽¹⁾ = 1`, and `𝐱⁽²⁾ = (1, 1, 3)` with `y⁽²⁾ = 0`. Start from `𝐰 = (0, 0, 0)`, so every `h = σ(0) = 0.5`.
(a) Compute the **signed errors** `h⁽ⁱ⁾ − y⁽ⁱ⁾`. (b) Compute the gradient `∇L = (1/m) Xᵀ(σ(X𝐰) − 𝐲)`.

---

## Part C — True / False + One-Line Justification (3 pts each)

**C1.** `h_𝐰(x) = σ(𝐰·𝐱)` can exceed 1.

**C2.** Thresholding the prediction at 0.5 is equivalent to `𝐰·𝐱 ≥ 0`.

**C3.** The cross-entropy loss for logistic regression is non-convex.

**C4.** Logistic regression has a closed-form solution analogous to the normal equation.

**C5.** The logistic-regression gradient has the same "(h − y)·x" form as linear regression.

---

## Part D — Synthesis & Derivation (25 pts)

**D1. (9 pts)** Starting from the per-sample cost `cost_𝐰(x,y) = h` if `y=1`, `1−h` if `y=0`, **derive** the combined cross-entropy `L(𝐰) = −(1/m) Σ [y·ln h + (1−y)·ln(1−h)]`. Explain the **product → log → sum → negate** steps, and verify the combined form reduces correctly for `y=0` and `y=1`.

**D2. (8 pts) Boundary geometry.** (a) Convert the line `x₂ = −x₁ + 4` into a weight vector `𝐰`. (b) Show `x₁+x₂−4 = 0` and `−x₁−x₂+4 = 0` describe the **same** boundary (scale invariance). (c) Why does scale invariance *motivate regularization*?

**D3. (8 pts) Why MSE fails + the fix.** (a) Give **two** reasons MSE is the wrong loss for classification. (b) On linearly-separable data, why do the weights blow up to `±∞`, and how does **L2 regularization** (excluding `w₀`) prevent it?

---
---

# ANSWER KEY

> Section references (§) point to `AML_L05_Ultimate_Reference.md`.

## Part A

**A1.** (§2) **Outliers drag the regression line**, shifting the 0.5-crossing and misclassifying points; the unbounded output `𝐰·𝐱` also has no probability interpretation.

**A2.** (§6) `σ(z) = 1/(1+e⁻ᶻ)`. `σ(0)=0.5`, `σ(+∞)→1`, `σ(−∞)→0`.

**A3.** (§6) When **`𝐰·𝐱 ≥ 0`** (the logit is non-negative).

**A4.** (§8) `h_𝐰(x) = P(y=1∣x)` — the estimated probability of the positive class; `1 − h_𝐰(x) = P(y=0∣x)`.

**A5.** (§11) The label is discrete (a confident wrong answer is barely penalized), and **MSE applied to `σ(𝐰·𝐱)` is non-convex** → local minima. We need a convex loss.

**A6.** (§12) **Maximum likelihood** — maximize the probability the model assigns to each correct label (product of per-sample likelihoods → log → sum).

**A7.** (§15) `∂L/∂wⱼ = (1/m) Σ (h_𝐰(x⁽ⁱ⁾) − y⁽ⁱ⁾) xⱼ⁽ⁱ⁾`. **Only difference** from linear regression: `h = σ(𝐰·𝐱)` instead of `𝐰·𝐱`. The "signed error × feature" skeleton is identical.

**A8.** (§16) **No closed form.** We minimize iteratively with **gradient descent** (`𝐰 ← 𝐰 − α∇L`, detailed in L06).

**A9.** (§5) `h_𝐰 = h_{α𝐰}` for any `α≠0` — scaling all weights gives the **same boundary line**; only the steepness of σ changes.

**A10.** (§10) **Basis expansion** — feed σ a non-linear feature map, e.g. `σ(w₁x₁+w₂x₂+w₃x₁²+w₄x₂²+w₀)` gives a **circle**. Still linear in the weights.

## Part B

**B1.** (§4, §6, §9) (a) `−4 + x₁ + x₂ = 0` ⟹ **`x₂ = −x₁ + 4`**.
(b) with `𝐰·𝐱 = x₁ + x₂ − 4`:

| point | `𝐰·𝐱` | `σ` | predict |
|---|---|---|---|
| (3,3) | +2 | 0.88 | **1** |
| (1,1) | −2 | 0.12 | **0** |
| (4,1) | +1 | 0.73 | **1** |

**B2.** (§4) (a) `−6 + 2x₁ + x₂ = 0` ⟹ **`x₂ = −2x₁ + 6`**. (b) `(1,5)`: `−6 + 2·1 + 5 = +1 ≥ 0` → **predict 1** (`σ(1)=0.73`).

**B3.** (§13) Terms `y·ln h + (1−y)·ln(1−h)`:
`(1,0.9) → ln 0.9 = −0.105`; `(0,0.2) → ln 0.8 = −0.223`; `(1,0.4) → ln 0.4 = −0.916`. Sum `= −1.244`.
**`L = −(1/3)(−1.244) = 0.415`**.

**B4.** (§15) With `𝐰=0`, `σ(0)=0.5` for both.
(a) signed errors: `h⁽¹⁾−y⁽¹⁾ = 0.5−1 = −0.5`; `h⁽²⁾−y⁽²⁾ = 0.5−0 = +0.5`.
(b) `∇L = (1/2)[ 𝐱⁽¹⁾·(−0.5) + 𝐱⁽²⁾·(0.5) ] = (1/2)[ (−0.5,−1,−0.5) + (0.5,0.5,1.5) ] = (1/2)(0,−0.5,1) = `**`(0, −0.25, 0.5)`**.

## Part C

**C1.** **False.** σ maps to `[0,1]`, so `h ≤ 1` always. (§6)

**C2.** **True.** `σ(𝐰·𝐱) ≥ 0.5 ⟺ 𝐰·𝐱 ≥ 0`. (§6, §9)

**C3.** **False.** Cross-entropy **is convex** in `𝐰` (one global optimum). *(It's MSE-on-σ that's non-convex.)* (§11, §16)

**C4.** **False.** **No** closed form — use gradient descent. (§16)

**C5.** **True.** Both are `(1/m)Σ(h−y)x`; only `h` differs (`σ(𝐰·𝐱)` vs `𝐰·𝐱`). (§15)

## Part D

**D1.** (§12–13) **Maximize** `𝓛(𝐰) = ∏ᵢ cost_𝐰(x⁽ⁱ⁾,y⁽ⁱ⁾)` (product of per-sample likelihoods). A product is hard to optimize and one tiny factor collapses it, so take the **log** (`ln∏ = Σln`); log is monotonic so the **maximizer is unchanged**. Maximizing `(1/m)Σ ln cost` is the same as **minimizing** `−(1/m)Σ ln cost`. Writing the two cases in one line: `cost = h` (when `y=1`) and `cost = 1−h` (when `y=0`) combine as `y·ln h + (1−y)·ln(1−h)` →
`L(𝐰) = −(1/m)Σ[y·ln h + (1−y)·ln(1−h)]`.
**Check:** `y=0` → only `ln(1−h)` survives; `y=1` → only `ln h` survives. ✓

**D2.** (§4–5, §16) (a) `x₂ = −x₁+4 ⟺ −4 + x₁ + x₂ = 0` → **`𝐰 = (−4, 1, 1)`**. (b) `−x₁−x₂+4 = −1·(x₁+x₂−4)`, i.e. `h'' = −1·h'`; multiplying all weights by `−1` is the `α=−1` case of `h_𝐰 = h_{α𝐰}` → **same boundary** (`σ` flips which side is which, but the line is identical). (c) Because *any* scaling gives the same boundary, on separable data the optimizer can shrink the loss toward 0 by **scaling `𝐰 → ∞`** (sharper σ) without improving the boundary → overfitting; **regularization** penalizes `‖𝐰‖` and stops this.

**D3.** (§11, §16) (a) (i) the label is discrete, so squared error barely punishes confident wrong predictions; (ii) **MSE on `σ(𝐰·𝐱)` is non-convex** (local minima). (b) On separable data, pushing `‖𝐰‖→∞` makes σ a hard step that assigns probability → 1/0 to every training point, driving cross-entropy → 0 — so the unregularized optimum has **infinite weights** (overfit). **L2 regularization** adds `(λ/2m)Σⱼ₌₁ⁿ wⱼ²`, which is minimized at small weights, **bounding `‖𝐰‖`** and smoothing the boundary. The bias `w₀` is left out (shifting the boundary isn't "complexity").

---

*Self-grade, then reread the cited § in `AML_L05_Ultimate_Reference.md` for any miss. All numerical answers are computer-verified.*
