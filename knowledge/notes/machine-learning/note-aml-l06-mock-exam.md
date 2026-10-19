---
id: note-aml-l06-mock-exam
type: note
title: "AML Lecture 06 — Mock Exam (Gradient Descent)"
created: "2026-07-11"
role: mock-exam
state: evolving
authorship: mixed
concepts: [concept-gradient-descent, concept-adam-optimizer, concept-convexity, concept-feature-scaling]
sources: [source-aml-ss26-lectures]
contexts: [workspace-aml-exam-prep]
---

> **Migration note (2026-07-17, Stage 2):** body preserved verbatim from
> `Plans/ML/foundations/AML/my notes/lect06 gradient descent/AML_L06_Mock_Exam.md` (legacy tree).

# AML Lecture 06 — Mock Exam (Gradient Descent)

**Topic:** the GD algorithm & update rule, the gradient (linear = logistic), convexity, the learning rate, feature scaling, cost vs the normal equation, and batch / stochastic / mini-batch GD.
**Companion:** `AML_L06_Ultimate_Reference.md` (section refs in the answer key).
**Suggested time:** 75 minutes, closed-book. Solve everything before opening the key, then self-grade.

> Scoring: Part A = 20 (2 each), Part B = 40, Part C = 15 (3 each), Part D = 25. Total 100.
> Sigmoid: σ(0) = 0.5.

---

## Part A — Conceptual Short Answer (2 pts each)

**A1.** Write the gradient-descent **update rule**. What is `α`?

**A2.** GD steps in which direction relative to the **gradient**, and **why**?

**A3.** Give the **vectorized gradient**. What's the *only* difference between the linear- and logistic-regression cases?

**A4.** What happens to GD if `α` is **too large**? **Too small**?

**A5.** How do you **check** that GD is working correctly?

**A6.** Why must features be **scaled** before running GD?

**A7.** Give one advantage of **batch GD** and one of **SGD**.

**A8.** When is GD **preferable** to the normal equation?

**A9.** Is GD guaranteed to find the **global** optimum? When yes, when no?

**A10.** What is an **epoch**? What is **mini-batch** GD (typical batch sizes)?

---

## Part B — Numerical Problems (show your work)

### B1. Gradient-descent iterations (14 pts)

`L(w) = (w − 3)²`, so `∇L(w) = 2(w − 3)`. Take `α = 0.25`, start `w = 0`.
(a) Compute `w₁`, `w₂`, `w₃` (three updates). (b) What value does it converge to? (c) Each step multiplies the distance-to-the-optimum by a constant `r` — what is `r` (in terms of `α`), and its value here?

### B2. Learning-rate behaviour (10 pts)

For the same `L(w)=(w−3)²`, the update multiplies the distance to 3 by `r = (1 − 2α)`. For `α = 0.5`, `α = 1`, `α = 1.5`:
(a) compute `r`. (b) For each, state whether GD **converges in one step**, **converges**, **oscillates forever**, or **diverges**.

### B3. One GD step — linear regression (8 pts)

`X = [[1,1],[1,2]]` (bias + one feature), `𝐲 = (1, 3)`, weights `𝐰 = (0, 0)`. Use `∇L = (1/m)Xᵀ(X𝐰 − 𝐲)` and `α = 0.1`.
(a) Compute the predictions `X𝐰` and residuals `X𝐰 − 𝐲`. (b) Compute `∇L`. (c) One update `𝐰 ← 𝐰 − α∇L`.

### B4. One GD step — logistic regression (8 pts)

Same `X`, but `𝐲 = (0, 1)` and `𝐰 = (0,0)` so every `h = σ(0) = 0.5`. Use `∇L = (1/m)Xᵀ(σ(X𝐰) − 𝐲)`, `α = 0.1`.
(a) Residuals `σ(X𝐰) − 𝐲`. (b) `∇L`. (c) One update.

---

## Part C — True / False + One-Line Justification (3 pts each)

**C1.** To make GD converge you must decrease `α` over time.

**C2.** GD is guaranteed to find the global minimum for **any** loss function.

**C3.** The linear-regression MSE has no local optima other than the global one.

**C4.** The gradient `∇L` points in the direction of steepest **decrease** of the loss.

**C5.** SGD computes its update from the **whole** dataset.

---

## Part D — Synthesis (25 pts)

**D1. (9 pts)** For linear regression, write `∇L` (MSE) and the GD update. Explain the **"(h − y)·x" rationale**: for a point the model gets wrong in each direction, show how the update moves the weight the right way.

**D2. (8 pts) GD vs the normal equation.** Give the computational cost of each. When is each preferred, and **why is GD necessary for logistic regression**?

**D3. (8 pts) Convexity & learning rate.** (a) Why does GD reach the **global** optimum for linear/logistic regression but possibly **not** for a deep net? (b) Describe the effect of too-large vs too-small `α`, and how you'd **diagnose and fix** a bad `α`.

---
---

# ANSWER KEY

> Section references (§) point to `AML_L06_Ultimate_Reference.md`.

## Part A

**A1.** (§4) `𝐰 ← 𝐰 − α·∇L(𝐰)` (update all weights simultaneously). `α` = **learning rate** (step size).

**A2.** (§4, §11) **Opposite** the gradient. The gradient points in the steepest **uphill** direction; to *minimize* we go downhill, i.e. `−∇L`.

**A3.** (§5) `∇L = (1/m)Xᵀ(h_𝐰(X) − 𝐲)`. Only `h_𝐰` differs: **`X𝐰` (linear)** vs **`σ(X𝐰)` (logistic)** — same "(prediction − label)·feature" skeleton.

**A4.** (§8) **Too large** → overshoot → loss oscillates or **diverges**. **Too small** → converges but **very slowly**.

**A5.** (§8) **Monitor the training loss over epochs** — for a good `α` it decreases every epoch; rising/oscillating ⇒ α too large.

**A6.** (§10) Unequal scales make the loss contours **elliptical** → GD **zig-zags** slowly. Scaling → **circular** contours → the gradient points straight at the minimum (fast).

**A7.** (§15) **Batch:** deterministic, loss decreases every step (exact gradient). **SGD:** cheap/frequent updates, scales to massive data, and its noise can **escape shallow local minima**.

**A8.** (§12) When `n` is **large** (the normal equation's `O(n²m + n³)` matrix inverse is too costly), or when there's **no closed form** at all (logistic regression, neural nets).

**A9.** (§7) Only for **convex** loss (one global optimum) — true for linear & logistic regression. For **non-convex** loss (deep nets) GD can land in a **local** minimum (depends on initialization).

**A10.** (§0, §14) An **epoch** = one full pass over the training data. **Mini-batch GD** updates from a batch of points (typically **32, 64, 128**) — the practical default.

## Part B

**B1.** (§9) `w ← w − 0.25·2(w−3) = w·0.5 + 1.5`.
(a) `w₁ = 0 − 0.25·(−6) = 1.5`; `w₂ = 1.5 − 0.25·(−3) = 2.25`; `w₃ = 2.25 − 0.25·(−1.5) = 2.625`.
(b) Converges to **`w = 3`**. (c) `r = (1 − 2α) = 0.5` — distance to 3 **halves** each step (3 → 1.5 → 0.75 → …).

**B2.** (§9)

| `α` | `r = 1−2α` | behaviour |
|---|---|---|
| 0.5 | 0 | **converges in one step** (`w₁ = 3`) |
| 1 | −1 | **oscillates forever** (0 → 6 → 0 → …) |
| 1.5 | −2 | **diverges** (\|r\| > 1) |

**B3.** (§5) (a) `X𝐰 = (0, 0)`; residuals `X𝐰 − 𝐲 = (−1, −3)`. (b) `Xᵀ(res) = (1·(−1)+1·(−3),\ 1·(−1)+2·(−3)) = (−4, −7)`; `∇L = (1/2)(−4,−7) = (−2, −3.5)`. (c) `𝐰 ← (0,0) − 0.1·(−2,−3.5) = `**`(0.2, 0.35)`**.

**B4.** (§5) (a) `h = (0.5, 0.5)`; residuals `(0.5 − 0, 0.5 − 1) = (0.5, −0.5)`. (b) `Xᵀ(res) = (0.5−0.5,\ 0.5−1.0) = (0, −0.5)`; `∇L = (1/2)(0,−0.5) = (0, −0.25)`. (c) `𝐰 ← (0,0) − 0.1·(0,−0.25) = `**`(0, 0.025)`**.

## Part C

**C1.** **False.** A **fixed** α converges fine if it's not too large; decaying α is optional. (§8)

**C2.** **False.** Only for **convex** losses; non-convex losses have local minima. (§7)

**C3.** **True.** The MSE is convex (one global optimum). (§7)

**C4.** **False.** `∇L` points in the steepest **increase**; we step **opposite** it (`−∇L`). (§3, §11)

**C5.** **False.** SGD uses **one** random point per update; batch GD uses the whole set. (§13)

## Part D

**D1.** (§5–6) MSE gradient: `∇L = (1/m)Xᵀ(X𝐰 − 𝐲)`, update `𝐰 ← 𝐰 − α∇L`. Per weight: `∂L/∂wⱼ = (1/m)Σ(h−y)xⱼ`. Rationale via the **signed error** `h − y`: if the model **under**-predicts a point (`h < y`, so `h−y < 0`), the term `−α(h−y)xⱼ` is **positive** → `wⱼ` **increases** → next prediction rises toward `y`. If it **over**-predicts (`h > y`), the update **decreases** `wⱼ`. Correctly-fit points (`h ≈ y`) contribute ≈ 0.

**D2.** (§12) **Normal equation** `𝐰=(XᵀX)⁻¹Xᵀ𝐲`: `O(n²m + n³)` (build + invert an n×n matrix) — fine for small `n`. **GD:** `O(c·n·m)` over `c` epochs, **no inverse**, scales to large `n`/`m`. GD is **necessary for logistic regression** because its cross-entropy loss has **no closed-form minimizer** — you *must* solve it iteratively.

**D3.** (§7–8) (a) Linear/logistic losses are **convex** (one global optimum), so GD descends straight to it; a deep net's loss is **non-convex** (many local minima/saddles), so GD's result depends on initialization and it can get stuck. (b) **Too large α** → overshoot → loss oscillates/diverges; **too small** → painfully slow. **Diagnose** by plotting the **training loss vs epochs**: if it rises or zig-zags, α is too big (shrink it, e.g. ÷10); if it crawls down, α is too small (increase it). Also **scale features** to keep contours circular.

---

*Self-grade, then reread the cited § in `AML_L06_Ultimate_Reference.md` for any miss. All numerical answers are computer-verified.*
