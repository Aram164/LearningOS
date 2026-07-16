---
id: note-aml-l05-logistic-regression
type: note
title: "AML Lecture 05 — Ultimate Reference: Logistic Regression"
created: "2026-07-11"
role: reference
state: evolving
authorship: mixed
concepts: [concept-logistic-regression, concept-maximum-likelihood, concept-cross-entropy, concept-sigmoid, concept-decision-boundary]
sources: [source-aml-ss26-lectures, source-islp, source-murphy-pml1, source-cs229-notes]
contexts: [workspace-aml-exam-prep]
---

> **Migration note (2026-07-17, Stage 2):** body preserved verbatim from
> `Plans/ML/foundations/AML/my notes/lect05 logistic regression/AML_L05_Ultimate_Reference.md` (legacy tree).

# AML Lecture 05 — Ultimate Reference: Logistic Regression

*Covers AML VL05 (66 slides): from regression to classification, the decision boundary, the sigmoid, the logistic hypothesis as a probability, the cross-entropy loss derived from maximum likelihood, the vectorized loss & gradient, convexity, and non-linear (basis-expanded) boundaries + regularized logistic regression (Übungsblatt 3). Builds on `../lect03 linear regression/AML_L03_Ultimate_Reference.md` (dot products, design matrix) and `../lect04 non-linear regression/AML_L04_Ultimate_Reference.md` (basis expansion, regularization). The optimizer (gradient descent) is **L06**.*

---

## Table of Contents

0. [Notation](#0-notation)
1. [From regression to classification](#1-from-regression)
2. [Three attempts: line → separator → logistic](#2-three-attempts)
3. [The decision boundary `w·x = 0`](#3-decision-boundary)
4. [Reading a boundary: line ↔ vector](#4-line-vector)
5. [Scale invariance of the boundary](#5-scale-invariance)
6. [The sigmoid (squashing) function](#6-sigmoid)
7. [The logistic hypothesis](#7-hypothesis)
8. [Probabilistic interpretation](#8-probability)
9. [Prediction: the 4-step pipeline](#9-prediction)
10. [Non-linear decision boundaries (basis expansion)](#10-nonlinear)
11. [Why not MSE? (convexity)](#11-not-mse)
12. [The loss from maximum likelihood](#12-mle)
13. [Binary cross-entropy (combined form)](#13-cross-entropy)
14. [Vectorized loss](#14-vectorized)
15. [The gradient](#15-gradient)
16. [Regularized logistic regression](#16-regularized)
17. [Übungsblatt 3 overview](#17-ueb3)
18. [Summary](#18-summary)
19. [Self-test](#19-self-test)

---

## 0. Notation <a name="0-notation"></a>

Shared with L03/L04 (dot product `𝐰·𝐱`, design matrix `X ∈ ℝ^{m×(n+1)}`, bias trick `x₀=1`). New to L05:

| Symbol | Meaning |
|---|---|
| `y ∈ {0,1}` | **binary** label — 0 = negative class (benign), 1 = positive class (malignant) |
| `σ(z)` | the **sigmoid / logistic** function, `1/(1+e⁻ᶻ) ∈ [0,1]` |
| `z = 𝐰·𝐱` | the **logit** (linear score) fed into σ |
| `h_𝐰(x) = σ(𝐰·𝐱)` | the **logistic hypothesis** — estimated `P(y=1∣x)` |
| `L(𝐰)` | the **cross-entropy / log-loss** (not MSE here) |
| `cost_𝐰(x,y)` | per-sample likelihood: `h` if `y=1`, `1−h` if `y=0` |

---

## 1. From regression to classification <a name="1-from-regression"></a>

**[Source: VL05 slides 3–5]**

**Classification** predicts a **discrete** label; here **binary**: `y ∈ {0,1}` (e.g. tumor malignant=1 / benign=0; spam/not; fraud/not). The negative class is 0, the positive class is 1. It looks like regression but the output must be a *small set of discrete values*, not `y ∈ ℝ`.

---

## 2. Three attempts: line → separator → logistic <a name="2-three-attempts"></a>

**[Source: VL05 slides 6–9]**

1. **Linear regression + threshold 0.5** — fit `h_𝐰(x)=𝐰·𝐱`, predict 1 if `h ≥ 0.5`. ❌ **Fails: outliers drag the line**, moving the 0.5-crossing and misclassifying points.
2. **Separator (decision boundary)** — fit `h_𝐰(x)=𝐰·𝐱 = 0` and predict by the *sign*. Better, but `𝐰·𝐱` is **unbounded** → no notion of **confidence** (how certain is the prediction?).
3. **Logistic regression** — pass the score through a **squashing function `σ: ℝ → [0,1]`**, giving a bounded, probability-like output. ✅ This is the lecture's model.

---

## 3. The decision boundary `w·x = 0` <a name="3-decision-boundary"></a>

**[Source: VL05 slides 12–17]**

We look for a **line / hyperplane** that separates the classes:

$$w_0\cdot 1 + w_1x_1 + \dots + w_nx_n = 𝐰·𝐱 = 0.$$

(In *linear* regression the same dot product equalled a real-valued target `y`; here it equals **0** and defines a boundary.) One side (`𝐰·𝐱 > 0`) is the positive class, the other (`𝐰·𝐱 < 0`) the negative class.

---

## 4. Reading a boundary: line ↔ vector <a name="4-line-vector"></a>

**[Source: VL05 slides 13–16]**

A 2-D boundary can be written as a **slope-intercept line** or as a **weight vector** — convert between them.

**Worked example (slide 15):** the line `x₂ = −x₁ + 4` ⟺ `−4 + x₁ + x₂ = 0` ⟺ `𝐰·𝐱 = 0` with

$$𝐰 = (w_0, w_1, w_2) = (-4,\,1,\,1).$$

**Classify points (slide 17)** with `h_𝐰(x) = x₁ + x₂ − 4`:
- `(3,3)`: `3+3−4 = +2 > 0` → predict **1**.
- `(1,1)`: `1+1−4 = −2 < 0` → predict **0**.

---

## 5. Scale invariance of the boundary <a name="5-scale-invariance"></a>

**[Source: VL05 slides 18–20]**

The boundary `𝐰·𝐱 = 0` is **scale-invariant**: `h_𝐰(x) = h_{α𝐰}(x)` for any `α ≠ 0` — multiplying every weight by a constant gives the **same line**.

**Example:** `x₁+2x₂−2 = 0` and `−x₁−2x₂+2 = 0` describe the **same** boundary (the second = `−1 ×` the first). *(This matters later: regularization is what stops the weights from blowing up to `±∞` even though the boundary is unchanged — see §16.)*

---

## 6. The sigmoid (squashing) function <a name="6-sigmoid"></a>

**[Source: VL05 slides 23–25]**

$$\sigma(z) = \frac{1}{1+e^{-z}} \in [0,1], \qquad \sigma(𝐰·𝐱) = \frac{1}{1+e^{-(𝐰·𝐱)}}.$$

Key values & behavior:
- `σ(0) = 0.5` (the boundary); `σ(+∞) → 1`; `σ(−∞) → 0`.
- **`𝐰·𝐱 > 0 ⇒ σ > 0.5`** (positive class); **`𝐰·𝐱 < 0 ⇒ σ < 0.5`** (negative class).
- Rough table: `σ(1)≈0.73`, `σ(2)≈0.88`, `σ(3)≈0.95`, `σ(−2)≈0.12`.

As `‖𝐰‖` grows, σ becomes steeper — approaching a hard **step function** (a sharp cut between classes). See §16.

---

## 7. The logistic hypothesis <a name="7-hypothesis"></a>

**[Source: VL05 slides 22–23]**

| | hypothesis |
|---|---|
| Linear regression | `h_𝐰(x) = 𝐰·𝐱` (unbounded ∈ ℝ) |
| **Logistic regression** | **`h_𝐰(x) = σ(𝐰·𝐱)` ∈ [0,1]** |

Same linear score `𝐰·𝐱`, then squashed into [0,1].

---

## 8. Probabilistic interpretation <a name="8-probability"></a>

**[Source: VL05 slides 30–32]**

`h_𝐰(x)` is the **estimated probability that `y = 1`**:

$$h_𝐰(x) = \sigma(𝐰·𝐱) = p_𝐰(y=1 \mid x), \qquad 1 - h_𝐰(x) = p_𝐰(y=0 \mid x),$$

and they sum to 1. E.g. `σ(𝐰·𝐱) = 0.9` ⇒ "90% chance the tumor is malignant." This is what makes logistic regression a **probabilistic** classifier (unlike a bare separator).

---

## 9. Prediction: the 4-step pipeline <a name="9-prediction"></a>

**[Source: VL05 slides 26–29]**

Given a point `x`:
1. **Decision boundary / dot product:** compute `𝐰·𝐱`.
2. **Sigmoid:** `h_𝐰(x) = σ(𝐰·𝐱)`.
3. **Threshold:** predict `y = 1` if `h_𝐰(x) ≥ 0.5`, else `0` — equivalently `𝐰·𝐱 ≥ 0`.

**Worked (slides 26–28):** boundary `x₁+x₂−4`. Point `(3,3)`: `𝐰·𝐱 = 2`, `σ(2)≈0.88 ≥ 0.5` → **malignant (1)**. Point `(1,1)`: `𝐰·𝐱 = −2`, `σ(−2)≈0.12 < 0.5` → **benign (0)**.

**Quiz (slide 36):** boundary `x₁+2x₂−2=0`, point `p=(2,0)`: `𝐰·𝐱 = 2+0−2 = 0` → `σ(0)=0.5` → classified **1 with exactly 50% probability** (it sits *on* the boundary).

---

## 10. Non-linear decision boundaries (basis expansion) <a name="10-nonlinear"></a>

**[Source: VL05 slides 33–34]**

The input to σ **doesn't have to be linear in `x`** — use the **basis-expansion trick from L04**. To fit a **circle** `x₁² + x₂² = 1`:

$$h_𝐰(x) = \sigma\big(w_1x_1 + w_2x_2 + w_3x_1^2 + w_4x_2^2 + w_0\big), \quad\text{with } w_3=1,\,w_4=1,\,w_0=-1.$$

Predict `y=1` if `x₁²+x₂²−1 ≥ 0` ⇒ `σ(x₁²+x₂²−1) ≥ 0.5`. Same idea as polynomial regression: **linear in the weights**, non-linear in `x` — so all the machinery still applies. (Übungsblatt 3 uses degree-6 polynomial features for the microchip data.)

---

## 11. Why not MSE? (convexity) <a name="11-not-mse"></a>

**[Source: VL05 slides 39, 53]**

Two reasons MSE is wrong for classification:
1. The label is **discrete** (correct/not); squared error treats a confident wrong answer almost like a near-miss.
2. **MSE applied to `σ(𝐰·𝐱)` is non-convex** → many local minima, gradient descent can get stuck.

So we need a different loss whose surface is **convex**. That loss comes from maximum likelihood (next).

---

## 12. The loss from maximum likelihood <a name="12-mle"></a>

**[Source: VL05 slides 40–47]**

**Idea:** maximize the probability the model assigns to the *correct* label of each sample. Define the per-sample likelihood:

$$\text{cost}_𝐰(x,y) = \begin{cases} h_𝐰(x), & y=1 \\ 1-h_𝐰(x), & y=0 \end{cases} \in [0,1].$$

Over all `m` independent samples, the **likelihood** is a product:

$$\mathcal{L}(𝐰) = \prod_{i=1}^{m} \text{cost}_𝐰(x^{(i)}, y^{(i)}).$$

**Problem:** one tiny factor pushes the whole product toward 0; products are hard to optimize. **Fix:** take the **log** (`ln(AB)=ln A + ln B`), turning the product into a **sum**. Log is monotonic, so it **doesn't move the maximizer**: `argmax 𝐰 𝓛 = argmax 𝐰 ln 𝓛`.

$$L(𝐰) = \frac{1}{m}\sum_{i=1}^{m} \ln \text{cost}_𝐰(x^{(i)},y^{(i)}) \quad(\text{maximize}).$$

When all predictions are correct, every `cost = 1`, `ln 1 = 0`, so the max is **0**. To make it a **minimization**, multiply by `−1`:

$$L(𝐰) = -\frac{1}{m}\sum_{i=1}^{m} \ln \text{cost}_𝐰(x^{(i)},y^{(i)}).$$

---

## 13. Binary cross-entropy (combined form) <a name="13-cross-entropy"></a>

**[Source: VL05 slides 56–58]**

The two cases (`y=1` → `h`, `y=0` → `1−h`) collapse into **one expression** — the **binary cross-entropy / log-loss**:

$$\boxed{\,L(𝐰) = -\frac{1}{m}\sum_{i=1}^{m}\Big[ y^{(i)}\ln h_𝐰(x^{(i)}) + (1-y^{(i)})\ln\big(1-h_𝐰(x^{(i)})\big)\Big]\,}$$

**Check the trick works:**
- `y=0`: the `y·ln h` term vanishes → `−(1/m)Σ ln(1−h)` ✓
- `y=1`: the `(1−y)·ln(1−h)` term vanishes → `−(1/m)Σ ln h` ✓

Each label "switches on" exactly the right log term.

---

## 14. Vectorized loss <a name="14-vectorized"></a>

**[Source: VL05 slides 59–61]**

With the design matrix `X` (rows = examples), apply σ element-wise to the score vector `X𝐰`:

$$L(𝐰) = -\frac{1}{m}\Big[\, 𝐲·\ln\sigma(X𝐰) + (1-𝐲)·\ln\big(1-\sigma(X𝐰)\big)\,\Big].$$

Reading the pieces (each a vector or a scalar):
- `X𝐰` = vector of logits `(𝐰·𝐱⁽¹⁾, …, 𝐰·𝐱⁽ᵐ⁾)ᵀ` — "**project onto the line**."
- `σ(X𝐰)` = element-wise sigmoid — "**apply sigmoid**."
- `𝐲·ln σ(X𝐰)` = a **dot product** → `Σᵢ y⁽ⁱ⁾ ln h_𝐰(x⁽ⁱ⁾)` (a scalar) — "**combined form**."

*(Implementation note from Übungsblatt 3: use `ln(σ(X𝐰) + ε)` for tiny `ε` since `ln 0` is undefined.)*

---

## 15. The gradient <a name="15-gradient"></a>

**[Source: VL05 slide 59]**

The partial derivative w.r.t. each weight has the **same beautiful form as linear regression** — `(prediction − label) × feature`:

$$\frac{\partial L}{\partial w_j} = \frac{1}{m}\sum_{i=1}^{m}\big(h_𝐰(x^{(i)}) - y^{(i)}\big)\,x_j^{(i)}, \qquad h_𝐰(x^{(i)}) = \sigma(𝐰·𝐱^{(i)}).$$

Vectorized: `∇L(𝐰) = (1/m) Xᵀ(σ(X𝐰) − 𝐲)`. The *only* difference from linear-regression's gradient is the `σ(·)` wrapped around `X𝐰` — the "error × feature" skeleton is identical (the "signed error" `h − y`).

---

## 16. Convexity & why no closed form → gradient descent <a name="16-regularized"></a>

**[Source: VL05 slides 52–54]**

- **Good news:** cross-entropy `L(𝐰)` is **convex** in `𝐰` (one global optimum).
- **Bad news:** there is **no closed-form solution** (no analogue of `𝐰=(XᵀX)⁻¹Xᵀ𝐲`). We must **minimize iteratively** with **gradient descent** (`𝐰 ← 𝐰 − α∇L`) — detailed in **L06**.

### Regularized logistic regression (Übungsblatt 3)

On separable data the weights would grow to **±∞** (the sigmoid → a hard step) to drive the loss to 0 → **overfitting** (recall scale-invariance, §5: the boundary is unchanged but confidence explodes). Fix: add an **L2 penalty** (exactly like Ridge, exclude the bias):

$$L(𝐰) = -\frac{1}{m}\sum_i\big[y^{(i)}\ln h + (1-y^{(i)})\ln(1-h)\big] + \frac{\lambda}{2m}\sum_{j=1}^{n} w_j^2,$$

and the gradient gains a `+ (λ/m)w_j` term for `j ≥ 1` (the bias `w₀` is **not** penalized). Larger `λ` → smoother boundary. Übungsblatt 3 applies this to the **microchip** data with **degree-6 polynomial features**.

---

## 17. Übungsblatt 3 overview <a name="17-ueb3"></a>

**[Source: Übung 06 / "3. Übungsblatt: Logistic Regression"]**

The graded notebook (10 tasks, 3 datasets):

- **University Admittance:** Task 1 sigmoid · Task 2 hypothesis `σ(w·x)` · Task 3 cost + gradient · Task 4 gradient descent · Task 5 learning-rate sensitivity (`α=100` diverges, `α=0.05` slow).
- **SciPy optimize:** Task 6 evaluation (`predict`, accuracy). Uses a Newton-variant minimizer.
- **Microchip (regularized):** Task 7 regularized cost + gradient · Task 8 effect of `λ` (degree-6 poly features → ellipsoid boundary; large `λ` → simpler).
- **Sentiment Analysis:** Task 9 fit `SGDClassifier` (bag-of-words; train err < 3%, test < 20%) · Task 10 words with largest weight (great/love vs worst/disappointment).

✓ Verified solution to the **bonus sheet** (Bonusblatt 3): `AML_BonusSheet03_Solution.md` (this folder).

---

## 18. Summary <a name="18-summary"></a>

- **Classification** needs a bounded output → squash the linear score with the **sigmoid**: `h_𝐰(x) = σ(𝐰·𝐱) = P(y=1∣x)`.
- **Predict** by thresholding at 0.5 (⟺ `𝐰·𝐱 ≥ 0`); the **boundary `𝐰·𝐱=0`** is a line/hyperplane (and **scale-invariant**). Basis expansion → non-linear boundaries (circles, degree-6).
- **MSE is wrong** (non-convex). The right loss is **binary cross-entropy**, derived from **maximum likelihood** (product of per-sample likelihoods → log → sum → negate).
- The **gradient** is the same "`(h − y)·x`" skeleton as linear regression, just with `h = σ(𝐰·𝐱)`. It's **convex** but has **no closed form** → **gradient descent (L06)**.
- **Regularize** (L2, exclude `w₀`) to stop weights blowing up on separable data.

---

## 19. Self-test <a name="19-self-test"></a>

- [ ] Why does linear-regression-with-threshold fail for classification? (outliers)
- [ ] Write the sigmoid; what are `σ(0)`, `σ(+∞)`, `σ(−∞)`? When is `σ(𝐰·𝐱) ≥ 0.5`?
- [ ] Convert the line `x₂ = −x₁ + 4` to a weight vector `𝐰`; classify `(3,3)` and `(1,1)`.
- [ ] What does `h_𝐰(x)` mean probabilistically? What is `1 − h_𝐰(x)`?
- [ ] Why can't we use MSE? What property does cross-entropy have that MSE-on-σ lacks?
- [ ] Derive the combined cross-entropy from the `y=1`/`y=0` cost cases; check both labels.
- [ ] Write `∂L/∂wⱼ`. How does it differ from the linear-regression gradient?
- [ ] Why is there no closed form? What do we use instead, and which lecture covers it?
- [ ] On separable data, why do weights blow up, and how does L2 regularization fix it?
- [ ] How do you get a **circular** decision boundary from a *linear* logistic model?

---

*Source: AML VL05 (Schäfer, HU SoSe 2026) + Übung 06 (3. Übungsblatt). Builds on `AML_L03/L04_Ultimate_Reference.md`; the optimizer is in the L06 reference. Companion to `AML_L02_Ultimate_Reference.md`. Maps to Foundations Block I.*
