---
id: note-aml-l06-gradient-descent
type: note
title: "AML Lecture 06 — Ultimate Reference: Gradient Descent"
created: "2026-07-11"
role: reference
state: evolving
authorship: mixed
concepts: [concept-gradient-descent, concept-adam-optimizer, concept-convexity, concept-feature-scaling]
sources: [source-aml-ss26-lectures, source-murphy-pml1, source-cs229-notes, source-mml]
contexts: [workspace-aml-exam-prep]
---

> **Migration note (2026-07-17, Stage 2):** body preserved verbatim from
> `Plans/ML/foundations/AML/my notes/lect06 gradient descent/AML_L06_Ultimate_Reference.md` (legacy tree).

# AML Lecture 06 — Ultimate Reference: Gradient Descent

*Covers AML VL06 (111 slides): local search, the gradient, the gradient-descent algorithm (batch / stochastic / mini-batch), convexity, the learning rate, feature scaling, cost vs the normal equation, and a glimpse of modern optimizers (momentum/Adam/Newton). This is the **optimizer** that fits the models of L03–L05 when there's no closed form. Builds on `../lect03 linear regression/AML_L03_Ultimate_Reference.md` (the linear-regression gradient) and `../lect05 logistic regression/AML_L05_Ultimate_Reference.md` (the logistic gradient — same form).*

---

## Table of Contents

0. [Notation](#0-notation)
1. [The optimization problem](#1-problem)
2. [Local search in 1-D](#2-local-search)
3. [The gradient](#3-gradient)
4. [The gradient-descent algorithm](#4-algorithm)
5. [The vectorized gradient (linear = logistic)](#5-vectorized)
6. [Why the update works (the rationale)](#6-rationale)
7. [Convexity & local optima](#7-convexity)
8. [The learning rate α](#8-learning-rate)
9. [Worked example: `L(w)=(w−3)²`](#9-worked)
10. [Feature scaling](#10-feature-scaling)
11. [Gradient direction & contours](#11-contours)
12. [Cost: gradient descent vs the normal equation](#12-cost)
13. [Stochastic gradient descent (SGD)](#13-sgd)
14. [Mini-batch gradient descent](#14-minibatch)
15. [Batch vs SGD vs mini-batch](#15-comparison)
16. [Beyond: momentum, Adam, Newton](#16-beyond)
17. [Summary](#17-summary)
18. [Self-test](#18-self-test)

---

## 0. Notation <a name="0-notation"></a>

Shared with L03–L05. New emphasis:

| Symbol | Meaning |
|---|---|
| `L(w)` | the loss to minimize (MSE for linear reg., cross-entropy for logistic) |
| `∇L(w)` | the **gradient** — vector of partial derivatives `∂L/∂wⱼ` |
| `α` | the **learning rate** (step size) |
| `h_𝐰(x)` | the model prediction (`𝐰·𝐱` linear, `σ(𝐰·𝐱)` logistic) |
| epoch | one full pass over the training data |

---

## 1. The optimization problem <a name="1-problem"></a>

**[Source: VL06 slides 3, 63]**

Almost all ML reduces to: **optimize parameters `𝐰 ∈ ℝⁿ⁺¹` by minimizing a loss `L(𝐰) ∈ ℝ`.**

$$\min_𝐰 L(𝐰), \qquad \text{MSE: } L=\tfrac{1}{2m}\textstyle\sum(𝐰·𝐱^{(i)}-y^{(i)})^2, \quad \text{logistic: } L=-\tfrac1m\textstyle\sum \ln \text{cost}_𝐰.$$

In principle the minimum is where all partials vanish (`∇L = 0`). When that has **no closed-form solution** (logistic regression!) or is too expensive (large `n`), we solve it by **iterative local search**.

---

## 2. Local search in 1-D <a name="2-local-search"></a>

**[Source: VL06 slides 5–7]**

For a single weight: to decrease `L(w)`, step in the direction where `L` is falling — i.e. **opposite the derivative**:

- `dL/dw > 0` (slope up to the right) → move **left**;
- `dL/dw < 0` (slope down to the right) → move **right**.

```
 initialize w randomly
 repeat until w converges:
   if dL/dw > 0:  move left
   else:          move right
```

---

## 3. The gradient <a name="3-gradient"></a>

**[Source: VL06 slides 12–15, 64–65]**

For `f: ℝⁿ → ℝ`, the first derivative is a **vector** — the **gradient** — holding the partial derivative w.r.t. every dimension:

$$\nabla L(𝐰) = \begin{bmatrix}\partial L/\partial w_0 \\ \vdots \\ \partial L/\partial w_n\end{bmatrix} \in \mathbb{R}^{n+1}.$$

Interpretation: the gradient **points in the steepest *uphill* direction**, and its size says how sensitive the loss is to each weight (large component → loss changes fast in that direction; small → near-flat / near a minimum).

---

## 4. The gradient-descent algorithm <a name="4-algorithm"></a>

**[Source: VL06 slides 17–20, 48]**

Step *downhill* = opposite the gradient, scaled by the learning rate `α`:

```
 randomly initialize 𝐰
 while not converged:
     𝐰 = 𝐰 − α · ∇L(𝐰)
```

Per-component: `wⱼ = wⱼ − α·(∂L/∂wⱼ)` for `j = 0…n` (update all weights **simultaneously** from the old gradient).

---

## 5. The vectorized gradient (linear = logistic) <a name="5-vectorized"></a>

**[Source: VL06 slides 13–16, 48]**

The magic of L03–L05: the gradient has the **same form** for linear and logistic regression — "**(prediction − label) × feature**", averaged:

$$\frac{\partial L}{\partial w_j} = \frac{1}{m}\sum_{i=1}^{m}\big(h_𝐰(x^{(i)}) - y^{(i)}\big)x_j^{(i)}, \qquad \nabla L(𝐰) = \frac{1}{m}X^{T}\big(h_𝐰(X) - 𝐲\big).$$

Only `h_𝐰` differs: **`h_𝐰(X) = X𝐰`** (linear) vs **`h_𝐰(X) = σ(X𝐰)`** (logistic). So *one* gradient-descent routine fits both.

---

## 6. Why the update works (the rationale) <a name="6-rationale"></a>

**[Source: VL06 slides 21–22]**

The "signed error" `h_𝐰(x) − y` drives each weight the right way (logistic example):
- **Case (a):** model predicts ~0 but `y = 1` → `(h − y) < 0` → the update **increases** `wⱼ` (push the score up).
- **Case (b):** model predicts ~1 but `y = 0` → `(h − y) > 0` → the update **decreases** `wⱼ` (push the score down).

Correct predictions give `h ≈ y` → near-zero update. The weights stop moving when every point is fit (or the loss is minimized).

---

## 7. Convexity & local optima <a name="7-convexity"></a>

**[Source: VL06 slides 23–27, 50]**

- **Non-convex** loss → multiple **local optima / saddle points**; GD's result depends on the **initialization**.
- **Convex** loss → **one global optimum**; GD converges to it (for a reasonable α).
- **Test:** a 1-D function is convex if every chord lies on/above the graph; in n-D, the **Hessian (second derivative) is positive semi-definite**.
- **Both** the linear-regression MSE **and** the logistic cross-entropy are **convex** (PSD Hessian) → GD finds the global optimum for our models. (Deep nets are non-convex — hence init/learning-rate matter there.)

---

## 8. The learning rate α <a name="8-learning-rate"></a>

**[Source: VL06 slides 29–33]**

`α` controls the step size and is the key hyperparameter:
- **too small** → very slow progress (many epochs);
- **too large** → **overshoot** the minimum → loss oscillates or **diverges** (worst case: loss never decreases).

**How to check it's working:** monitor the **training loss `L(𝐰)` over epochs**. For sufficiently small `α` it should **decrease every epoch**; if it rises/oscillates, α is too large. **No optimal formula** — try a few fixed values `{0.001, 0.01, 0.1, 1}`, or **decay** on a schedule (e.g. `α ∝ 1/epoch`).

---

## 9. Worked example: `L(w)=(w−3)²` <a name="9-worked"></a>

**[Source: Übungsblatt 3 tutorial — "Optimization using GD"]**

`∇L(w) = 2(w−3)`. Take `α = 0.25`, start `w = 0`. Update `w ← w − α·2(w−3) = w·(1−2α) + 6α`, i.e. each step the **distance to the optimum 3 is multiplied by `(1−2α) = 0.5`**:

| iter | `w` | `∇L = 2(w−3)` | update `−α∇L` | distance to 3 |
|------|-----|---------------|---------------|---------------|
| 0 | 0 | −6 | +1.5 | 3 |
| 1 | 1.5 | −3 | +0.75 | 1.5 |
| 2 | 2.25 | −1.5 | +0.375 | 0.75 |
| 3 | 2.625 | −0.75 | +0.1875 | 0.375 |
| 4 | 2.8125 | … | … | 0.1875 |

→ converges to **`w = 3`**. The **convergence factor is `r = (1−2α)`**: `α=0.25 → r=0.5` (halves), `α=0.5 → r=0` (one step!), `α=1 → r=−1` (**oscillates forever**), `α>1 → |r|>1` (**diverges**).

---

## 10. Feature scaling <a name="10-feature-scaling"></a>

**[Source: VL06 slides 34–46]**

When features have **very different scales** (size 0–2000 vs #bedrooms 1–5), the loss contours become **stretched ellipses** → GD **zig-zags** slowly. **Scaling** features to a common range makes the contours **circular** → the gradient points (almost) straight at the minimum → fast convergence. Aim for `xⱼ ∈ [−1,1]` or `[0,1]`. Two techniques:

- **Zero-mean (standardization):** `xⱼ ← (xⱼ − μⱼ)/σⱼ` (mean 0, std 1).
- **Min–max:** `xⱼ ← (xⱼ − min)/(max − min)` → `[0,1]`.

*(Same scaling ideas as L02 §6 and L04 — here the motivation is GD speed.)*

---

## 11. Gradient direction & contours <a name="11-contours"></a>

**[Source: VL06 slides 35–37, 64–66]**

The gradient is **perpendicular (orthogonal) to the contour lines** and points to the steepest increase. So `−∇L` points perpendicular to the contour toward lower loss. With **circular** contours that's straight at the centre (minimum); with **elliptical** contours it points *away* from the centre at most points → the zig-zag — which is exactly why scaling helps.

---

## 12. Cost: gradient descent vs the normal equation <a name="12-cost"></a>

**[Source: VL06 slides 52–53]**

- **Normal equation** (linear regression closed form `𝐰=(XᵀX)⁻¹Xᵀ𝐲`): cost `O(n²m + n³)` — must build and **invert an n×n matrix**. Great for small `n`, **prohibitive for large `n`**.
- **Gradient descent:** each gradient is `O(c·n·m)` over `c` epochs — **no inverse**, scales to large `n` and `m`, and works when there's **no closed form** (logistic regression, neural nets). This is *why* GD is the default at scale.

---

## 13. Stochastic gradient descent (SGD) <a name="13-sgd"></a>

**[Source: VL06 slides 52, 54–58]**

Batch GD uses the **whole dataset** for every update — `O(mn)` per step, slow/memory-heavy for big `m`. Because the loss is **decomposable** (`L = (1/m)Σ cost_𝐰`), so is the gradient. **SGD** updates from **one random point** at a time:

```
 randomly initialize 𝐰
 while not converged:
     pick a random (x⁽ⁱ⁾, y⁽ⁱ⁾)
     𝐰 = 𝐰 − α · ∇cost_𝐰(x⁽ⁱ⁾, y⁽ⁱ⁾)
```

Very cheap, frequent updates; the loss **fluctuates** (doesn't drop every step) but trends down.

---

## 14. Mini-batch gradient descent <a name="14-minibatch"></a>

**[Source: VL06 slide 59]**

The middle ground: update from a **batch B** of points (typical sizes **32, 64, 128**):

$$𝐰 = 𝐰 - \alpha\sum_{(x,y)\in B}\nabla\text{cost}_𝐰(x,y).$$

Smoother than SGD, cheaper than full batch — **the default in practice**, especially deep learning on GPUs.

---

## 15. Batch vs SGD vs mini-batch <a name="15-comparison"></a>

**[Source: VL06 slides 60–61]**

| | Batch GD | SGD | Mini-batch |
|---|---|---|---|
| data per update | whole set | 1 point | batch (32–128) |
| updates | slow, infrequent | very frequent | frequent |
| loss curve | decreases every step | fluctuates | mostly smooth |
| determinism | deterministic | non-deterministic | ~ |
| escapes shallow local minima | no | **yes** (noise) | somewhat |
| scalability | must fit in memory | massive data | massive data |

All find a (local) optimum with a reasonable α; **mini-batch is what's used in practice**.

**Comments:** GD is a very general optimizer; converges to the **global** optimum for **convex** loss, can stick in **local** minima for non-convex; **sensitive to initialization and learning rate**.

---

## 16. Beyond: momentum, Adam, Newton <a name="16-beyond"></a>

**[Source: VL06 slides 62, 68+]**

Plain GD oscillates in elliptical valleys. Modern optimizers fix this:
- **Momentum:** add an exponential moving average of past gradients → damps oscillation, accelerates along consistent directions.
- **Adam:** momentum **+ per-parameter adaptive learning rates** (the deep-learning default).
- **Newton's method:** uses the **Hessian** (2nd derivative) for the step — fast but `O(n³)` per step; AML/SciPy use Hessian-free Newton variants for logistic regression (Übungsblatt 3 Task 6).

---

## 17. Summary <a name="17-summary"></a>

- **Gradient descent** minimizes a loss by repeatedly stepping **opposite the gradient**: `𝐰 ← 𝐰 − α∇L(𝐰)`.
- The gradient is `(1/m)Xᵀ(h_𝐰(X) − 𝐲)` — **identical form** for linear (`h=X𝐰`) and logistic (`h=σ(X𝐰)`).
- Both losses are **convex** → GD reaches the **global** optimum (for reasonable α). Non-convex losses (deep nets) → local minima, init matters.
- **Learning rate** is critical: too small = slow, too large = diverge; tune by watching the loss curve. **Scale features** so contours are circular (faster).
- **Batch** (exact, slow) → **SGD** (one point, noisy, scalable) → **mini-batch** (32–128, the practical default). GD beats the normal equation for **large n** and is the *only* option without a closed form.

---

## 18. Self-test <a name="18-self-test"></a>

- [ ] Write the gradient-descent update rule. What is `α`?
- [ ] Give the vectorized gradient; how do the linear and logistic cases differ?
- [ ] For `L(w)=(w−3)²`, `α=0.25`, `w₀=0`: compute `w₁, w₂`. What is the convergence factor?
- [ ] What `α` makes this example oscillate forever? Diverge?
- [ ] Why must features be scaled for fast GD? Name two scaling methods.
- [ ] In which direction does `∇L` point relative to the contour lines?
- [ ] When is GD preferable to the normal equation? When is the normal equation fine?
- [ ] Contrast batch GD, SGD, and mini-batch (cost, noise, scalability).
- [ ] Why does GD reach the global optimum for linear/logistic regression but not for a deep net?
- [ ] What problem do momentum/Adam solve over plain GD?

---

*Source: AML VL06 (Schäfer, HU SoSe 2026) + Übung 06 (GD tutorial). Builds on `AML_L03/L05_Ultimate_Reference.md`. Companion to `AML_L02_Ultimate_Reference.md`. Maps to Foundations Block (optimization, used across E/H/I/L).*
