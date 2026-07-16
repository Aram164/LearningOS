---
id: note-aml-l03-linear-regression
type: note
title: "AML Lecture 03 — Ultimate Reference: Linear Regression (one predictor), Linear Algebra & Vectorization"
created: "2026-07-11"
role: reference
state: evolving
authorship: mixed
concepts: [concept-linear-regression, concept-mean-squared-error, concept-normal-equation]
sources: [source-aml-ss26-lectures, source-islp, source-cs229-notes]
contexts: [workspace-aml-exam-prep]
---

> **Migration note (2026-07-17, Stage 2):** body preserved verbatim from
> `Plans/ML/foundations/AML/my notes/lect03 linear regression/AML_L03_Ultimate_Reference.md` (legacy tree).

# AML Lecture 03 — Ultimate Reference: Linear Regression (one predictor), Linear Algebra & Vectorization

*Covers AML VL03 (75 slides): the regression problem, the MSE loss, the closed-form solution for one predictor, the linear-algebra refresher (dot product, transpose, matrix products, inverse), and vectorization (bias trick, design matrix). Companion sheets: `AML_L02_Ultimate_Reference.md`, `../lect04 non-linear regression/AML_L04_Ultimate_Reference.md`. Deep cross-module bridge: `Plans/ML/foundations/reference/Regression_SaD-AML-ISLP_Bridge.md`.*

---

## Table of Contents

0. [Notation & the four products](#0-notation)
1. [The regression problem](#1-regression-problem)
2. [From k-NN to k-NN regression](#2-knn-regression)
3. [Parametrizing a line](#3-parametrizing)
4. [The loss function — Mean Squared Error](#4-loss)
5. [The line-fitting problem (geometry of the loss)](#5-geometry)
6. [Minimizing the loss — the calculus](#6-calculus)
7. [Closed-form solution (simple regression)](#7-closed-form)
8. [SaD ↔ AML bridge: slope = cov/var](#8-bridge)
9. [Linear algebra: vectors & length](#9-vectors)
10. [The dot product](#10-dot)
11. [Transpose](#11-transpose)
12. [Matrix–vector & matrix–matrix products](#12-matrix)
13. [Identity & inverse](#13-inverse)
14. [Element-wise (Hadamard) vs dot](#14-hadamard)
15. [Vectorization: the bias trick](#15-bias-trick)
16. [The design matrix & the vectorized loss](#16-design-matrix)
17. [NumPy & why vectorize](#17-numpy)
18. [Vectorized simple regression](#18-vectorized-simple)
19. [Summary](#19-summary)
20. [Self-test](#20-self-test)

---

## 0. Notation & the four products <a name="0-notation"></a>

Most confusion in this lecture is **notation, not ideas**. Two distinctions recur on every slide: the four kinds of "multiplication," and the weight *vector* vs a single *weight*.

### The four products — never blur these

| Operation | Notation | Inputs → output | Meaning |
|---|---|---|---|
| **Scalar multiplication** | `ab`, `λwⱼ` | scalar × scalar → **scalar** | number × number |
| **Scaling a vector** | `α𝐱` | scalar × vector → **vector** | stretch every component |
| **Dot product** ⭐ | `𝐰·𝐱 = 𝐰ᵀ𝐱 = ⟨𝐰,𝐱⟩` | vector · vector → **SCALAR** | `Σⱼ wⱼxⱼ` — *one number* |
| **Matrix product** | `X𝐰`, `XᵀX` | matrix · (vec/mat) → **vec/mat** | rows×columns, each entry a dot product |
| **Element-wise (Hadamard)** | `𝐱⊙𝐲` (NumPy `x*y`) | vector ⊙ vector → **vector** | multiply matching components, *no sum* |

> 🔑 **The single most important sentence in L03 (slide 46):** *"The dot product of two vectors is a real number, not a vector."* `𝐰·𝐱 = w₀x₀ + … + wₙxₙ ∈ ℝ` collapses two vectors into **one scalar**. The Hadamard product keeps a vector. Same raw multiplications — the dot product **adds them up**.

### Weight vector vs single weight

| Symbol | Type | Role |
|---|---|---|
| **𝐰** (bold) | vector ∈ ℝⁿ⁺¹ | the whole parameter vector we solve for |
| `wⱼ` | scalar | one weight (j-th component) |
| `w₀` | scalar | the **bias / intercept** (multiplied by the constant feature `x₀=1`) |
| `w₁…wₙ` | scalars | the feature weights (`w₁` = slope in 1-D) |

### Everything else

| Symbol | Meaning | | Symbol | Meaning |
|---|---|---|---|---|
| `m` | # training examples (rows) | | `X` | design matrix ∈ ℝ^{m×(n+1)} |
| `n` | # real features (excl. bias) | | `𝐲` | target vector ∈ ℝᵐ |
| `𝐱⁽ⁱ⁾` | i-th example (vector) | | `x̄, ȳ` | sample means |
| `xⱼ⁽ⁱ⁾` | j-th feature of example i | | `h_𝐰(x)` | hypothesis (prediction) `= 𝐰·𝐱` |
| `y⁽ⁱ⁾` | target of example i | | `‖𝐯‖₂²` | squared L2 norm `= Σvⱼ² = 𝐯·𝐯` |

---

## 1. The regression problem <a name="1-regression-problem"></a>

**[Source: VL03 slides 3–5]**

**Regression** predicts a **continuous** output, `h_𝐰: X → Y` with `Y = [0, ∞)` — e.g. a house price in dollars. Contrast with **classification** (L02), which predicts a **discrete** label, `Y = {0,…,9}` for MNIST digits.

The running example is **Portland housing prices**: feature `x` = size in ft², target `y` = price in \$1000s; `m = 47` examples.

```
 price y
   5 |              ?          Given scattered (xᵢ, yᵢ), fit a line.
   4 |        •   •  •         Typically NO exact line exists →
   3 |     •  •  •             we aim for a "good fit" by minimizing
   2 |   • •  •                the total error.
   1 | • •
   0 +------------------- size x
```

The job: find the line that best fits the cloud of points.

---

## 2. From k-NN to k-NN regression <a name="2-knn-regression"></a>

**[Source: VL03 slide 6]**

L02's k-NN **classifier** returns the **mode** (most frequent label) of the k nearest neighbours. To make k-NN do **regression** (real-valued targets), replace the mode with a numeric aggregate:

- **average()** of the k neighbours' targets (most common), or
- **median()** of the k neighbours' targets (robust to outliers).

(`max()` would not be a sensible regression aggregate.) This is the same lazy, non-parametric idea — only the aggregation changes. Linear regression, below, is the *parametric* alternative: it learns a compact `𝐰` instead of storing all the data.

---

## 3. Parametrizing a line <a name="3-parametrizing"></a>

**[Source: VL03 slides 7–10]**

A line is

$$h_𝐰(x) = w_1 x + w_0,$$

with **slope** `w₁` and **y-intercept** `w₀`. The weight *vector* is `𝐰 = (w₀, w₁)`. Different `𝐰` = different lines.

**Worked read-off (slide 8):** a line falling 2 units over a run of 4 has slope `w₁ = −2/4 = −0.5`; if it crosses the y-axis at 2 then `w₀ = 2`, giving `h_𝐰(x) = −0.5x + 2`.

| `𝐰` | line | shape |
|---|---|---|
| `w₁=0, w₀=2` | `h(x)=2` | flat |
| `w₁=0.5, w₀=0` | `h(x)=0.5x` | rising through origin |
| `w₁=0.5, w₀=1` | `h(x)=0.5x+1` | rising, shifted up |

The task is to **pick the (w₀, w₁) with the smallest error.**

---

## 4. The loss function — Mean Squared Error <a name="4-loss"></a>

**[Source: VL03 slides 11–14]**

For each example the **error** (residual) is `h_𝐰(x⁽ⁱ⁾) − y⁽ⁱ⁾`. Square it (so signs don't cancel and it is differentiable), then average over all `m` examples:

$$\text{MSE}(w_0,w_1) = \frac{1}{2m}\sum_{i=1}^{m}\big(h_𝐰(x^{(i)}) - y^{(i)}\big)^2 = \frac{1}{2m}\sum_{i=1}^{m}\big(w_1 x^{(i)} + w_0 - y^{(i)}\big)^2$$

- The **`1/2`** is a convenience: it cancels the 2 that drops out when differentiating the square. Minimizing `MSE` and `½·MSE` give the **same `𝐰`**.
- **Why squared, not absolute (`Σ|·|`, MAD)?** The square is **differentiable everywhere** (the absolute value has a kink at 0), which is what makes gradient methods and a clean closed form possible. (Bonusblatt 2 Aufgabe 1 makes exactly this point.) Squaring also penalizes large errors more heavily.

**Quiz (slide 14):** line `y = −2x + 8`; points `a=(1,2)`, `b=(3,4)`. Predicted: `h(1)=6`, `h(3)=2`. Errors: `a → (6−2)²=16`, `b → (2−4)²=4`. **Point b has the smaller squared error.**

We then solve `minimize_{w₀,w₁} MSE(w₀, w₁)`.

---

## 5. The line-fitting problem (geometry of the loss) <a name="5-geometry"></a>

**[Source: VL03 slides 16–22]**

Simplify first: fix `w₀ = 0` and sweep the slope `w₁`. Each `w₁` produces one MSE number. On the data `(1,1),(2,2),(3,3)`:

| `w₁` | line | MSE |
|---|---|---|
| 1 | `h(x)=x` | **0** (perfect) |
| 0.5 | `h(x)=0.5x` | 0.583 |
| 0 | `h(x)=0` | 2.33 |

Plotting MSE against `w₁` traces a **parabola** — convex, single minimum:

```
 MSE(w₁)
 2.33 |•                   • w₁=0
      |  \               /
 0.58 |    •_         _•      w₁=0.5
    0 |       \__•__/         w₁=1 (minimum)
      +---------------------- w₁
      0   0.5   1   1.5   2
```

With **both** `w₀` and `w₁` free, `L(w₀, w₁)` is a **paraboloid** (a convex bowl) over the `(w₀, w₁)` plane; its lowest point is the optimal line. Convexity ⇒ **one** global minimum, no local traps.

---

## 6. Minimizing the loss — the calculus <a name="6-calculus"></a>

**[Source: VL03 slides 23–30]**

**One variable:** to minimize `L(w₁)`, set the derivative to zero: `dL/dw₁ = 0`.

**Two variables:** set **both partial derivatives** to zero: `∂L/∂w₀ = 0` and `∂L/∂w₁ = 0`. The vector of all partials is the **gradient**:

$$\nabla L(𝐰) = \begin{bmatrix}\partial L/\partial w_0 \\ \vdots \\ \partial L/\partial w_n\end{bmatrix} \in \mathbb{R}^{n+1} \qquad\text{"one slope per dimension."}$$

**Deriving the partials** via the chain rule `(f∘g)' = f'(g)·g'`, with `g(𝐰) = w₁x+w₀−y` and `f(g)=g²`:

$$\frac{\partial L}{\partial w_0} = \frac{1}{m}\sum_i \big(w_1x^{(i)}+w_0-y^{(i)}\big)\cdot 1, \qquad \frac{\partial L}{\partial w_1} = \frac{1}{m}\sum_i \big(w_1x^{(i)}+w_0-y^{(i)}\big)\cdot x^{(i)}$$

(the `·1` and `·x⁽ⁱ⁾` are `g'(w₀)` and `g'(w₁)`). At the minimum both are zero.

---

## 7. Closed-form solution (simple regression) <a name="7-closed-form"></a>

**[Source: VL03 slide ~30 / VL04 slide 5]**

Setting both partials to zero and solving (the lecture states the result without the algebra):

$$w_1 = \frac{\sum_i (x^{(i)}-\bar x)(y^{(i)}-\bar y)}{\sum_i (x^{(i)}-\bar x)^2}, \qquad w_0 = \bar y - w_1\bar x$$

where `x̄ = (1/m)Σxⁱ` and `ȳ = (1/m)Σyⁱ`. Compute `w₁` first, then `w₀`. The line **always passes through the centroid `(x̄, ȳ)`** (substitute `x = x̄`).

> ⚠️ Some slide printouts show `w₀ = ȳ + w₁x̄`; the correct sign is **`w₀ = ȳ − w₁x̄`** (so that `h_𝐰(x̄) = ȳ`).

---

## 8. SaD ↔ AML bridge: slope = cov/var <a name="8-bridge"></a>

The closed form is **the statistician's slope in disguise**:

- numerator `Σ(x−x̄)(y−ȳ)` = (unnormalized) **covariance** of x and y;
- denominator `Σ(x−x̄)²` = (unnormalized) **variance** of x.

So `w₁ = cov(x,y)/var(x)`. Three notations, one number:

$$\underbrace{k = r_{xy}\tfrac{s_y}{s_x}}_{\text{SaD}} \;=\; \underbrace{\beta_1}_{\text{ISLP}} \;=\; \underbrace{w_1}_{\text{AML}}, \qquad \underbrace{d = \bar y - k\bar x}_{\text{SaD}} = w_0.$$

**Why squared error at all?** SaD 08 proves it: assume `y = f(x) + ε` with Gaussian noise `ε ~ N(0,σ²)`; maximizing the likelihood is equivalent to minimizing `Σεᵢ²` = MSE. AML just *uses* MSE — the MLE justification is the deep reason. (Full treatment: `Regression_SaD-AML-ISLP_Bridge.md`.)

---

## 9. Linear algebra: vectors & length <a name="9-vectors"></a>

**[Source: VL03 linear-algebra refresher]**

To extend from one feature to many we need vector/matrix algebra. A vector is an array (a geometric arrow). Its **length** (L2 norm) is the distance from the origin:

$$\|𝐱\|_2 = \sqrt{\sum_i x_i^2} \qquad\text{e.g. } 𝐱=(3,4)\Rightarrow \|𝐱\|_2 = \sqrt{9+16} = 5.$$

---

## 10. The dot product <a name="10-dot"></a>

**[Source: VL03 slides ~46–60]**

$$𝐱·𝐲 = \sum_i x_i y_i \in \mathbb{R} \quad(\text{a SCALAR}), \qquad 𝐱·𝐱 = \sum_i x_i^2 = \|𝐱\|^2.$$

**Orthogonality example:** `𝐱=(3,4)`, `𝐲=(−4,3)` → `𝐱·𝐲 = 3·(−4) + 4·3 = −12+12 = 0` ⟹ the vectors are **perpendicular (90°)**. A dot product of 0 means orthogonal.

---

## 11. Transpose <a name="11-transpose"></a>

`Aᵀ` flips rows ↔ columns: `(Aᵀ)ᵢⱼ = Aⱼᵢ`. A column vector `𝐯 ∈ ℝ⁴` (shape 4×1) transposes to a row vector `𝐯ᵀ` (1×4). `(Aᵀ)ᵀ = A`. Transpose is what lets us write a dot product as a matrix product: `𝐮·𝐯 = 𝐮ᵀ𝐯`.

---

## 12. Matrix–vector & matrix–matrix products <a name="12-matrix"></a>

**[Source: VL03 matrix-product slides]**

A **matrix–vector product is a stack of dot products** — each output entry is a row of `M` dotted with `𝐱`:

```
        ⎡— M₁,: —⎤        ⎡ M₁,:·𝐱 ⎤
   M𝐱 = ⎢— M₂,: —⎥ 𝐱  =   ⎢ M₂,:·𝐱 ⎥      (m×n)(n×1) = (m×1)
        ⎣— M₃,: —⎦        ⎣ M₃,:·𝐱 ⎦
```

**Matrix–matrix:** `(AB)ᵢⱼ = (row i of A)·(col j of B) = Σₖ AᵢₖBₖⱼ`, with `(r×k)(k×p) = (r×p)`.

> **Sanity check, always:** inner dimensions must match; outer dimensions give the result shape. `(3×2)(2×1) = (3×1)` ✓.

> ⚠️ For vectors `𝐮, 𝐯 ∈ ℝⁿ`: `𝐮ᵀ𝐯` = (1×n)(n×1) = **scalar** (the dot product); `𝐮𝐯ᵀ` = (n×1)(1×n) = **n×n matrix** (the outer product). Same two vectors, opposite shapes. And `𝐱ᵀ𝐱 = ‖𝐱‖²` (scalar) but `𝐱𝐱ᵀ` (n×n matrix). **Order matters.** Matrix product is **not commutative** (`AB ≠ BA`) but **is** associative (`(AB)C = A(BC)`).

---

## 13. Identity & inverse <a name="13-inverse"></a>

`Iₙ` is the n×n identity (`Iₙ𝐱 = 𝐱`). A matrix `A` has an inverse `A⁻¹` (with `A⁻¹A = AA⁻¹ = I`) **only if** it is (1) **square** and (2) has `det(A) ≠ 0` (non-singular). This requirement returns in the **normal equation** (L04 §4–5) — when `XᵀX` is singular, the closed form breaks.

---

## 14. Element-wise (Hadamard) vs dot <a name="14-hadamard"></a>

The **Hadamard product** `𝐱⊙𝐲` (NumPy `x*y`) multiplies component-by-component and **stays a vector** — *no summation*. The dot product `x@y` sums those products into a **scalar**. Keeping `x*y` (element-wise) and `x@y` (dot) straight is the **#1 NumPy bug** in this course. Broadcasting (adding a scalar/row to a matrix by copying) is a related convenience.

---

## 15. Vectorization: the bias trick <a name="15-bias-trick"></a>

**[Source: VL03 slides 6–7 (vectorization) / VL04 slides 6–7]**

To write `h_𝐰(x) = w₁x₁ + w₀` as a **single dot product**, append a constant feature **`x₀ = 1`**:

$$𝐰 = \begin{bmatrix}w_0\\w_1\end{bmatrix},\;\; 𝐱 = \begin{bmatrix}1\\x_1\end{bmatrix} \;\;\Rightarrow\;\; h_𝐰(x) = 𝐰·𝐱 = w_0\cdot 1 + w_1 x_1. \;✓$$

The intercept `w₀` becomes "just another weight" whose feature is always 1. (Vectorization quiz, VL04 slide 6: the right change is **"add a feature to X with value 1."**)

---

## 16. The design matrix & the vectorized loss <a name="16-design-matrix"></a>

**[Source: VL03 vectorization / VL04 slides 7–8]**

Stack all `m` examples (each with its leading 1) as rows of the **design matrix** `X`:

```
       ⎡ 1   x₁⁽¹⁾ ⎤          ⎡ y⁽¹⁾ ⎤        ⎡ w₀ ⎤
   X = ⎢ 1   x₁⁽²⁾ ⎥    𝐲 =   ⎢  ⋮   ⎥   𝐰 =  ⎣ w₁ ⎦
       ⎢ ⋮    ⋮    ⎥          ⎣ y⁽ᵐ⁾ ⎦
       ⎣ 1   x₁⁽ᵐ⁾ ⎦
        (m×2)                 (m×1)          (2×1)
```

Then `X𝐰` is the vector of all predictions and `X𝐰 − 𝐲` the vector of all residuals, so the **whole dataset's loss is one expression**:

$$\|X𝐰 - 𝐲\|_2^2 = \sum_i (𝐰·𝐱^{(i)} - y^{(i)})^2 \qquad\Rightarrow\qquad L(𝐰) = \frac{1}{2m}\|X𝐰 - 𝐲\|_2^2.$$

This single formula carries over **unchanged** to many features (L04) — only `X` gets wider.

---

## 17. NumPy & why vectorize <a name="17-numpy"></a>

**[Source: Übung 03]**

| Operation | NumPy |
|---|---|
| subtract vectors | `x - y` |
| **element-wise** (Hadamard) | `x * y` |
| **dot product** | `x @ y`, `x.dot(y)`, `np.dot(x,y)` |
| sum / square | `np.sum(x)`, `x**2` |
| L2 norm `‖𝐰‖₂` | `np.linalg.norm(w)` |
| Lₚ norm `‖𝐰‖ₚ` | `np.linalg.norm(w, ord=p)` |

Übung 03 benchmarks `f(x) = Σⱼ wⱼxⱼ`: **for-loop 0.0112 s → `np.sum` 0.0012 s → dot-product 0.00056 s** (~20× faster). Same math, vastly faster — this is *why* we reformulate everything as dot products and matrix ops (compiled C loops instead of Python loops).

---

## 18. Vectorized simple regression <a name="18-vectorized-simple"></a>

**[Source: Übung 03]**

The §7 closed form vectorizes cleanly with dot products and a norm:

$$w_1 = \frac{(𝐱-\bar x)\cdot(𝐲-\bar y)}{(𝐱-\bar x)\cdot(𝐱-\bar x)} = \frac{(𝐱-\bar x)\cdot(𝐲-\bar y)}{\|𝐱-\bar x\|_2^2}, \qquad w_0 = \bar y - w_1\bar x.$$

In code: `np.mean`, `@`, and `np.linalg.norm` — **no Python loops.**

---

## 19. Summary <a name="19-summary"></a>

- **Regression** = predict a continuous target; fit `h_𝐰(x) = w₁x + w₀` by minimizing **MSE = (1/2m)Σ(h−y)²**.
- The loss is **convex** (a bowl) → a unique minimum found by `∇L = 0`.
- **Closed form (1 predictor):** `w₁ = Σ(x−x̄)(y−ȳ)/Σ(x−x̄)² = cov/var`, `w₀ = ȳ − w₁x̄`.
- **Vectorize:** bias trick (`x₀=1`) → `h = 𝐰·𝐱`; design matrix → `L(𝐰) = (1/2m)‖X𝐰−𝐲‖²`. Carries straight into L04's multivariate/normal-equation form.
- Keep **dot (scalar)** vs **Hadamard (vector)** vs **outer product (matrix)** straight — that's 80 % of the exam's "what shape is this?" points.

---

## 20. Self-test <a name="20-self-test"></a>

- [ ] Write `h_𝐰(x)` as a dot product and explain the `x₀=1` bias trick.
- [ ] Is `𝐱·𝐲` a scalar or a vector? Is `𝐱⊙𝐲`? Is `𝐱𝐱ᵀ`? Is `𝐱ᵀ𝐱`?
- [ ] Derive `∂L/∂w₁` for simple regression via the chain rule.
- [ ] From `(1,1),(2,2),(3,3)`, give `w₁` and the MSE at the optimum. (→ `w₁=1`, MSE 0.)
- [ ] Why squared error instead of absolute error? (differentiability / closed form / GD)
- [ ] State the closed form for `w₁, w₀` and show the line passes through `(x̄, ȳ)`.
- [ ] Benchmark intuition: why is `x @ w` ~20× faster than a Python for-loop?

---

*Source: AML VL03 (Schäfer, HU SoSe 2026) + Übung 03. SaD 03/08 cross-links (Akbik/Leser). Companion to `AML_L02_Ultimate_Reference.md` and `AML_L04_Ultimate_Reference.md`. Maps to Foundations Block E.*
