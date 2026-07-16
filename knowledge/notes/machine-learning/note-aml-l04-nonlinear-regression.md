---
id: note-aml-l04-nonlinear-regression
type: note
title: "AML Lecture 04 — Ultimate Reference: Non-Linear Regression (Multivariate, Polynomial, Regularization)"
created: "2026-07-11"
role: reference
state: evolving
authorship: mixed
concepts: [concept-basis-functions, concept-normal-equation, concept-regularization, concept-linear-regression]
sources: [source-aml-ss26-lectures, source-islp]
contexts: [workspace-aml-exam-prep]
---

> **Migration note (2026-07-17, Stage 2):** body preserved verbatim from
> `Plans/ML/foundations/AML/my notes/lect04 non-linear regression/AML_L04_Ultimate_Reference.md` (legacy tree).

# AML Lecture 04 — Ultimate Reference: Non-Linear Regression (Multivariate, Polynomial, Regularization)

*Covers AML VL04 (67 slides): multivariate regression + the normal equation, non-linear/polynomial regression via basis expansion, overfitting & the bias–variance picture, and regularization (Ridge, Lasso, the L1/L2 geometry). Builds directly on `../lect03 linear regression/AML_L03_Ultimate_Reference.md` (notation, dot products, design matrix, vectorized loss). Companion: `AML_L02_Ultimate_Reference.md` (bias–variance, cross-validation). Deep bridge: `Plans/ML/foundations/reference/Regression_SaD-AML-ISLP_Bridge.md`.*

---

## Table of Contents

0. [Notation recap](#0-notation)
1. [Multivariate regression — many features](#1-multivariate)
2. [The vectorized gradient](#2-gradient)
3. [The Normal Equation (closed form)](#3-normal-equation)
4. [When the Normal Equation breaks](#4-singular)
5. [Normal equation vs gradient descent](#5-ne-vs-gd)
6. [Non-linear regression: the two tricks](#6-nonlinear)
7. [Computed features](#7-computed)
8. [Basis expansion (polynomial features)](#8-polynomial)
9. [Overfitting: more features always lower *train* error](#9-overfitting)
10. [The bias–variance picture](#10-bias-variance)
11. [Two ways to fight overfitting](#11-two-ways)
12. [Ridge regression (L2)](#12-ridge)
13. [Lasso regression (L1)](#13-lasso)
14. [Why L1 zeros weights: diamond vs circle](#14-geometry)
15. [General Lₚ norms](#15-lp)
16. [Übungsblatt 2 checklist](#16-ueb2)
17. [Summary](#17-summary)
18. [Self-test](#18-self-test)

---

## 0. Notation recap <a name="0-notation"></a>

All notation is shared with L03 (see that sheet §0). The two distinctions that bite in L04:

- **Weight vector `𝐰`** (the whole thing, ∈ ℝⁿ⁺¹) vs a **single weight `wⱼ`** vs the **bias `w₀`**. Regularization penalizes the *feature* weights `w₁…wₙ` but **leaves `w₀` free**.
- **Matrix products vs dot products vs Hadamard** — every normal-equation step is a shape check. `m` = #examples, `n` = #features, `X ∈ ℝ^{m×(n+1)}`.

---

## 1. Multivariate regression — many features <a name="1-multivariate"></a>

**[Source: VL04 slides 3, 9–10]**

The housing data now has **`n` features** per example (size, #bedrooms, #floors, age):

$$h_𝐰(x) = w_1x_1 + w_2x_2 + \dots + w_nx_n + w_0\cdot 1 = \sum_{j=0}^{n} w_jx_j = 𝐰·𝐱, \qquad 𝐰,𝐱 \in \mathbb{R}^{n+1}.$$

Geometrically the model is now a **hyper-plane** instead of a line. With the bias trick, the **design matrix** becomes `X ∈ ℝ^{m×(n+1)}` (one leading 1-column + n feature columns), and the **vectorized loss is unchanged from L03**:

$$L(𝐰) = \frac{1}{2m}\|X𝐰 - 𝐲\|_2^2.$$

That invariance is the whole payoff of vectorizing: one feature or one hundred, the loss is the same expression.

---

## 2. The vectorized gradient <a name="2-gradient"></a>

**[Source: VL04 slides ~11–24]**

Differentiating `L(𝐰) = (1/2m)‖X𝐰−𝐲‖²` with respect to the weight *vector* gives a single closed expression:

$$\nabla L(𝐰) = \frac{1}{m}X^{T}(X𝐰 - 𝐲) = \frac{1}{m}\big(X^{T}X𝐰 - X^{T}𝐲\big) \;\in\; \mathbb{R}^{n+1}.$$

**Dimensionality sanity check** (VL04 slide 24) — every term must land in ℝⁿ⁺¹:

```
   X  ∈ ℝ^{m×(n+1)}     Xᵀ ∈ ℝ^{(n+1)×m}     𝐰 ∈ ℝⁿ⁺¹      𝐲 ∈ ℝᵐ
   XᵀX  ∈ ℝ^{(n+1)×(n+1)}     XᵀX𝐰 ∈ ℝⁿ⁺¹     Xᵀ𝐲 ∈ ℝⁿ⁺¹    ✓
```

The factor `Xᵀ(X𝐰−𝐲)` reads as "**each feature column dotted with the residual vector**" — feature j's gradient component is large when feature j correlates with the current errors.

---

## 3. The Normal Equation (closed form) <a name="3-normal-equation"></a>

**[Source: VL04 normal-equation slides]**

Set the gradient to zero and solve. The `1/m` scales away:

$$X^{T}X𝐰 - X^{T}𝐲 = 0 \;\Longleftrightarrow\; X^{T}X𝐰 = X^{T}𝐲 \;\xrightarrow{\;\times (X^TX)^{-1}\;}\; \boxed{\;𝐰 = (X^{T}X)^{-1}X^{T}𝐲\;}$$

This is **THE normal equation** — the exact least-squares solution in one shot, no iteration.

> 🔍 **Mind the products:** `XᵀX` is a **matrix product** → an `(n+1)×(n+1)` matrix. `Xᵀ𝐲` is a **matrix–vector product** → a vector ∈ ℝⁿ⁺¹. The combination `(XᵀX)⁻¹Xᵀ` is the **Moore–Penrose pseudo-inverse** `X⁺`, so `𝐰 = X⁺𝐲`.

> 🔗 **SaD bridge:** SaD 03's multivariate solution `k = (AᵀA)⁻¹Aᵀy` **is** this equation, renamed. Same matrices.

---

## 4. When the Normal Equation breaks <a name="4-singular"></a>

`XᵀX` is square, but it is **non-invertible (singular)** — so `(XᵀX)⁻¹` doesn't exist — when:

1. **Redundant / linearly-dependent features** — e.g. size in ft² *and* size in m² (one is a scalar multiple of the other), so the columns are linearly dependent.
2. **Too many features, too few examples** — `m ≤ n` (not enough data to pin down the weights).

**Fixes:**

- Use `numpy.linalg.pinv` — it computes `(XᵀX)⁻¹Xᵀ` robustly (via the pseudo-inverse / SVD) even when `XᵀX` is ill-conditioned. **Übung 04 is emphatic: form `w = np.linalg.pinv(X) @ y` — never invert `XᵀX` explicitly by hand.**
- **Ridge regularization** (§12) adds `+λI`, which makes the matrix invertible *and* fights overfitting — two birds.

---

## 5. Normal equation vs gradient descent <a name="5-ne-vs-gd"></a>

The normal equation is exact but inverting an `(n+1)×(n+1)` matrix costs ≈ `O(n³)` — fine for a handful of features, **prohibitive when `n` is large** (thousands of features, deep learning). The iterative alternative, **gradient descent** (`𝐰 ← 𝐰 − α∇L`, AML L06), avoids the inverse and scales to huge `n` and `m`. Rule of thumb: small `n` → normal equation; large `n` / streaming / deep nets → gradient descent.

---

## 6. Non-linear regression: the two tricks <a name="6-nonlinear"></a>

**[Source: VL04 non-linear slides]**

> ### 🧭 The through-line — read this first (why the rest of the lecture isn't random)
>
> The whole second half of L04 is **one story in five beats**. The slides present the beats but not the arrows between them — here are the arrows:
>
> 1. **Plain linear regression only fits straight lines / flat planes.** But real data **curves** (price vs size bends, etc.). We want curves.
> 2. **Trick to get curves without leaving linear regression:** *expand the features* — feed the model `x, x², x³, …` (or `√x`, `width×height`, …) as **extra columns**. A **curve in `x` is just a straight line in this bigger feature space**, so the model is still *linear in the weights* → **the exact same loss and normal equation still solve it** (§7–§8). Nothing new to learn mechanically; you just widen `X`.
> 3. **But flexibility has a cost.** The more powers/features you add, the more the curve can **wiggle to pass through every training point** — including the noise. Training error keeps dropping, but **test error turns back up** (overfitting / high variance, §9–§10). Degree is a flexibility dial.
> 4. **The fix isn't to throw features away — it's to *penalize big weights*.** A wiggly overfit curve needs **large** weights to make those sharp turns; a smooth curve has **small** weights. So we add a penalty on weight size to the loss, and a knob **λ** trades *fit* against *smoothness* (§11–§12). Turn λ up → weights shrink → curve smooths → less overfitting.
> 5. **Two flavors of penalty, one difference:** **Ridge (L2)** shrinks *all* weights smoothly toward (but not to) zero; **Lasso (L1)** drives *some* weights **exactly to 0**, deleting useless features (§13–§14).
>
> **So the lecture is just:** want curves → add features → that overfits → penalize weight size to smooth it → Ridge shrinks, Lasso zeros. Keep this map open while you read the slides and they stop looking random.
>
> 🎥 *Intuition videos (the ones missing from the slides) are pinned at §12–§14 and in the mini-plan Step 4.*

Real data often isn't linear. Two tricks let a **linear** regressor fit **curves** — and crucially, both keep the model **linear in the weights `𝐰`**, so the *entire* machinery above (loss, gradient, normal equation) still applies unchanged:

1. **Computed features** (§7), and
2. **Basis expansion / polynomial features** (§8).

"Linear in the weights" is the key phrase: the model can be wildly non-linear in `x`, as long as it's a linear combination of (possibly transformed) features with weights `𝐰`.

---

## 7. Computed features <a name="7-computed"></a>

Engineer a new feature from existing ones, then regress on it. E.g. from `width` and `height` compute `area = width × height`, and fit

$$h_𝐰(x) = w_1\cdot\text{width} + w_2\cdot\text{height} + w_3\cdot\text{area} + w_0.$$

The model is non-linear in the raw inputs but linear in `𝐰`.

---

## 8. Basis expansion (polynomial features) <a name="8-polynomial"></a>

**[Source: VL04 polynomial slides + Übung 04]**

Transform the input with a feature map `φ(x)` that appends powers: `x → (1, x, x², x³, …)`. Then

$$h_𝐰(x) = w_0 + w_1 x + w_2 x^2 + w_3 x^3 + \dots = 𝐰·φ(𝐱).$$

The trick visualized:

```
   y |        •••              y |      •  •         In ORIGINAL space the data
     |     ••     •              |    •      •        curves (a line fits badly).
     |   •          •            |  •          •      Plot the SAME data vs x²:
     | •     line ✗   •          |•   line ✓          a straight line fits well.
     +------------------ x       +------------------ x²
```

**Key insight:** a curve in `x`-space is a **straight line in `φ(x)`-space.** We still minimize `L(𝐰) = (1/2m)‖φ(X)𝐰 − 𝐲‖²`, and the solution is still `𝐰 = (φ(X)ᵀφ(X))⁻¹φ(X)ᵀ𝐲` — just with the **expanded** design matrix `φ(X)`. We "embed the data in a higher-dimensional feature space and fit a hyper-plane there."

**Worked example (Übung 04):** with features `(1, size, size², √size)`, solving via `pinv` gives `𝐰 = (14265, 19.71, −0.002, −1008)`, i.e. `h_𝐰(x) = 14265 + 19.71·x − 0.002·x² − 1008·√x`.

---

## 9. Overfitting: more features always lower *train* error <a name="9-overfitting"></a>

**[Source: VL04 overfitting slides]**

Adding **any** feature can only **decrease (or equal)** the *training* MSE: if a new feature `xₖ` is useless, the model can simply learn `wₖ = 0` and lose nothing. So "more features ⟹ smaller train MSE" is **always** true — and therefore a **trap**: low training error doesn't mean a good model. The truth is told by **test** error.

---

## 10. The bias–variance picture <a name="10-bias-variance"></a>

**[Source: VL04 + cross-ref `AML_L02_Ultimate_Reference.md` §8]**

```
   underfit / high bias     good generalization      overfit / high variance
      (too simple)             (just right)              (too complex)
   y|   •                   y|    ___                 y|    /\    /\
    |  ___•__•              |   •/  •\•                |  •/  \  /•  \•  wiggles through
    | •      •  •           |  •      •  •             | •  •  \/ • •  \  every point
    +------------ x         +------------ x            +-------------- x
   bad on train+test       good on both              train≈0, test BAD
```

```
   error                              TEST error is U-shaped:
     |\          test                  too simple → high bias,
     | \        /                      too complex → high variance.
     |  \      /                       Pick complexity at the bottom.
     |   \__  /  ___ train (keeps ↓)
     +----------------- model complexity / polynomial degree
```

The **degree is a hyperparameter**, chosen by **cross-validation** (train on `r−1` folds, validate on the held-out fold, average, pick the smallest validation error — see `AML_L02_Ultimate_Reference.md` §9). Problem: too many degrees/feature-subsets to check exhaustively → we want a knob that *continuously* controls complexity → **regularization.**

---

## 11. Two ways to fight overfitting <a name="11-two-ways"></a>

1. **Reduce features** — manual selection, cross-validation, or feature-selection algorithms (discrete, combinatorial).
2. **Regularize** — keep all features but **penalize large weights** (continuous, scales to many features). This is the lecture's focus.

**Idea:** add a penalty on weight size to the loss. If you add e.g. `1000·w₃² + 1000·w₄²`, the minimizer is *forced* to shrink `w₃, w₄ ≈ 0`, smoothing the fitted curve. Regularization generalizes this to *all* feature weights with one knob `λ`.

---

## 12. Ridge regression (L2) <a name="12-ridge"></a>

**[Source: VL04 regularization slides]**

Penalize the **squared length of the weight vector, excluding the bias:**

$$L(𝐰) = \underbrace{\frac{1}{2m}\sum_{i=1}^{m}(𝐰·𝐱^{(i)} - y^{(i)})^2}_{\text{MSE (fit)}} + \underbrace{\lambda\sum_{j=1}^{n} w_j^2}_{\text{penalty (simplicity)}} = \frac{1}{2m}\|X𝐰-𝐲\|^2 + \lambda(\|𝐰\|^2 - w_0^2).$$

> 🔑 **Weight-vector vs weight again:** the sum runs `j = 1…n` (the *feature* weights), **not** `j = 0`. We never regularize the **intercept `w₀`** — shifting the whole fit up/down isn't "complexity." The form `λ(‖𝐰‖² − w₀²)` reads as "length of the weight *vector*, minus the bias *weight* back out."

`λ ∈ ℝ₊` is a hyperparameter (tune by CV over `…, 10, 1, 0.1, 0.01, …`):

- `λ = 0` → ordinary least squares (overfit risk).
- `λ → ∞` → every `wⱼ (j≥1) → 0`; only the unpenalized `w₀` survives → **flat line** → underfit.

**Closed form** (one tiny change — and it *also* cures the singular-`XᵀX` problem of §4):

$$𝐰 = (X^{T}X + \lambda I)^{-1}X^{T}𝐲 \qquad\text{— the "}+\lambda I\text{" makes the matrix invertible.}$$

🎥 **Watch — Ridge:** StatQuest, [*Regularization Part 1: Ridge (L2) Regression*](https://www.youtube.com/watch?v=Q81RR3yKn30) — the clearest "shrink the slope to **desensitize** the fit to the training data" intuition; it maps onto this section line for line.

---

## 13. Lasso regression (L1) <a name="13-lasso"></a>

**[Source: VL04 regularization slides]**

Penalize the **sum of absolute** weights instead:

$$L(𝐰) = \frac{1}{2m}\|X𝐰-𝐲\|^2 + \lambda\sum_{j=1}^{n}|w_j| = \frac{1}{2m}\|X𝐰-𝐲\|^2 + \lambda(\|𝐰\|_1 - |w_0|).$$

- **Lasso (L1) → sparse `𝐰`:** drives many weights to **exactly 0** ⇒ automatic **feature selection**.
- **Ridge (L2) → small `𝐰`:** shrinks weights toward small values, but rarely exactly 0.

So choose **Lasso** when you suspect many features are irrelevant and want a sparse, interpretable model; **Ridge** when most features contribute a little and you mainly want to damp variance.

🎥 **Watch — Lasso:** StatQuest, [*Regularization Part 2: Lasso (L1) Regression*](https://www.youtube.com/watch?v=NGf0voTMlcs) — same setup as the Ridge video, then the one big difference: Lasso can shrink a weight **all the way to 0** and delete the feature.

---

## 14. Why L1 zeros weights: diamond vs circle <a name="14-geometry"></a>

The penalty defines a **constraint region**; the solution is where the MSE contours (ellipses) first touch that region.

```
   L2 (Ridge): circle            L1 (Lasso): diamond
        w₂                            w₂
        |   ___                       |   /\        MSE contours (ellipses)
        |  /   \ ⊙ MSE min            |  /  \ ⊙     hit the DIAMOND at a
        | | •   |                     | <  • >      CORNER → w₁ = 0
        |  \___/                      |  \  /       (a weight zeroed out).
   -----+-------- w₁            ------+--\/----- w₁  The CIRCLE has no corners
        |                             |             → touch is off-axis → small,
                                                      nonzero weights.
```

The diamond's **corners sit on the axes**, so the optimum tends to land where some weight is exactly 0. The circle is smooth, so its touch point is generically off-axis → small but nonzero weights. That geometric difference *is* why L1 is sparse and L2 is not.

**Second way to see it — the gradient / "force" view** (often clicks faster than the geometry):
- **L2 (Ridge)** penalty `λw²` has gradient `2λw` — the pull toward 0 is **proportional to the weight**. As `w` gets small, the pull gets weak, so it *shrinks* weights but **never quite reaches 0** (asymptotic).
- **L1 (Lasso)** penalty `λ|w|` has gradient `λ·sign(w)` — a **constant push of fixed size**, regardless of how small `w` already is. That steady push keeps going until the weight hits **exactly 0** and stops there.

So: **Ridge's pull fades near zero (shrink); Lasso's push is constant (snap to zero).** The diamond-vs-circle picture and this force picture are the same fact seen two ways.

🎥 **Watch — the geometry:** StatQuest, [*Ridge vs Lasso Regression, Visualized!!!*](https://www.youtube.com/watch?v=Xm2C_gTAl8c) — animates exactly this diamond-vs-circle touch point. Watch it right after the Ridge + Lasso videos above.

---

## 15. General Lₚ norms <a name="15-lp"></a>

$$\|𝐰\|_p = \Big(\sum_j |w_j|^p\Big)^{1/p}.$$

The constraint-region shape interpolates with `p`: **`p=1` diamond (Lasso)** → **`p=2` circle (Ridge)** → larger `p` a rounded square (→ `p=∞` is the square / max-norm). **Smaller `p` ⟹ sparser solutions** (sharper corners on the axes). This is the same `Lₚ`/Minkowski family used for distances in L02 §4 — there it shaped *neighbourhoods*, here it shapes the *penalty region*.

---

## 16. Übungsblatt 2 checklist <a name="16-ueb2"></a>

**[Abgabe 09.06.26]** — what the sheet asks you to implement:

**Pure NumPy**
- [ ] Compute the vectorized loss `L(𝐰) = (1/2m)‖X𝐰−𝐲‖²`.
- [ ] **Normal equation**: `𝐰 = (XᵀX)⁻¹Xᵀ𝐲` via `np.linalg.pinv` (never invert by hand).

**Scikit-Learn**
- [ ] Polynomial regression (Parts 1 & 2): `PolynomialFeatures` + `LinearRegression`.
- [ ] Bias (underfit) vs variance (overfit): vary the degree, compare train vs test error.
- [ ] High-degree overfitting: watch test error blow up, then tame it with Ridge/Lasso (`λ=1`).

*(Verified solution key: `../lect03 linear regression/AML_BonusSheet02_Solution.md`.)*

---

## 17. Summary <a name="17-summary"></a>

- **Multivariate** regression = same vectorized loss `(1/2m)‖X𝐰−𝐲‖²`, wider `X`. Model = hyper-plane.
- **Normal equation:** `𝐰 = (XᵀX)⁻¹Xᵀ𝐲` — exact, one shot; breaks when `XᵀX` is singular (redundant features, `m≤n`) → use `pinv` or Ridge `+λI`; costs `O(n³)` so large-`n` prefers gradient descent (L06).
- **Non-linear** fits come from **computed/polynomial features** — the model stays **linear in `𝐰`**, so all the machinery is reused; a curve in `x` is a line in `φ(x)`.
- **Overfitting:** more features always lower *train* error → judge on *test* error → U-shaped bias–variance curve → pick complexity by CV.
- **Regularization:** Ridge (L2, `λΣwⱼ²`, small weights, closed form `+λI`) vs Lasso (L1, `λΣ|wⱼ|`, sparse weights). **Never penalize `w₀`.** Diamond-vs-circle geometry explains the sparsity difference.

---

## 18. Self-test <a name="18-self-test"></a>

- [ ] Derive `𝐰 = (XᵀX)⁻¹Xᵀ𝐲` from `∇L = 0`; give the shape of every factor.
- [ ] Name two reasons `XᵀX` is singular and two fixes.
- [ ] Why does the normal equation become impractical for large `n`? What replaces it?
- [ ] How do polynomial features let a *linear* model fit a curve? What stays "linear"?
- [ ] Write the Ridge and Lasso losses. Which weight is **not** penalized, and why?
- [ ] `λ = 0` gives ___ ; `λ → ∞` gives ___ .
- [ ] Draw the L1 diamond vs L2 circle and explain why L1 produces exact zeros.
- [ ] Give the Ridge closed form and explain how `+λI` also fixes singularity.

---

*Source: AML VL04 (Schäfer, HU SoSe 2026) + Übung 04 (Übungsblatt 2, due 2026-06-09). SaD 03 cross-links (Akbik). Builds on `AML_L03_Ultimate_Reference.md`; companion to `AML_L02_Ultimate_Reference.md`. Maps to Foundations Blocks E + H.*
