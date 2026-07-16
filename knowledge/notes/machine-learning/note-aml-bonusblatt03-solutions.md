---
id: note-aml-bonusblatt03-solutions
type: note
title: "AML — Bonusaufgabe zu Übungsblatt 3 — Worked Solution"
created: "2026-07-11"
role: exercise-bank
state: evolving
authorship: mixed
concepts: [concept-logistic-regression, concept-maximum-likelihood, concept-cross-entropy]
sources: [source-aml-ss26-lectures]
contexts: [workspace-aml-exam-prep]
---

> **Migration note (2026-07-17, Stage 2):** body preserved verbatim from
> `Plans/ML/foundations/AML/my notes/lect05 logistic regression/AML_BonusSheet03_Solution.md` (legacy tree).

# AML — Bonusaufgabe zu Übungsblatt 3 — Worked Solution

> **Unofficial.** No Moodle correction; official solutions discussed in the tutorials (ab 23.06.26). Self-check key. Covers **L06** (gradient descent — Aufgabe 1), **L02/L05** (classifier comparison — Aufgabe 2), **L05/L07** (decision-boundary geometry — Aufgabe 3). Cross-ref for Aufgabe 1: `../lect06 gradient descent/AML_L06_Mini_Plan.md`.

---

## Aufgabe 1 — Gradientenabstieg (conceptual)

**a) GD vs. SGD.**

- **Batch gradient descent** uses **all m** examples per update: w ← w − α·(1/m)Σᵢ∇Lᵢ. Each step is the *true* gradient. **+** stable, smooth, monotone decrease for small α, deterministic. **−** expensive per step (full pass), slow/memory-heavy on large data.
- **Stochastic gradient descent** uses **one** (or a mini-batch) random example per update: w ← w − α·∇Lᵢ. **+** very cheap per step → fast on big data, the update noise helps escape saddle points / shallow minima, works online/streaming. **−** noisy, non-monotone (loss bounces), needs a decaying learning rate to settle, never sits exactly at the minimum. *(Mini-batch is the middle ground.)*

**b) Preprocessing.** **Feature scaling / normalization** — standardize each feature to mean 0, std 1 (or min–max to [0,1]). **Why:** with very different feature scales the loss surface is a long, skewed valley, so GD zig-zags and converges slowly; scaling makes the contours near-circular so the gradient points (almost) straight at the minimum → faster, more stable convergence, and one learning rate works for all dimensions. (It also stops large-scale features from dominating the gradient — and is exactly why the lecture normalized the admittance data "for faster convergence".)

**c) Effect of learning rate α on train loss.**

- **Too small** → loss decreases, but *very slowly* (many epochs to converge).
- **Too large** → overshooting: the loss **oscillates or diverges** (increases).
- **Well-chosen** → loss decreases steadily each epoch toward the minimum. *Rule of thumb:* for sufficiently small α, L should drop on every iteration — monitor the curve; rising/oscillating ⇒ α too large, crawling ⇒ too small.

---

## Aufgabe 2 — (Nicht-)Linear Klassifikatoren

Classifiers: **1-NN, 5-NN, Linear Logistic Regression, Perceptron.** (Logistic regression and perceptron both give a **straight-line** boundary; k-NN gives a **non-linear** one — 1-NN very jagged, 5-NN smoother.)

**Dataset 1** — four clusters: **x** top-centre + bottom-centre, **o** left + right (both classes share the centre → an **XOR-like, non-linearly-separable** pattern).

- **Best: k-NN (1-NN or 5-NN).** A flexible non-linear boundary can carve out the interleaved clusters. *Why:* the classes aren't linearly separable, so only a non-linear method can reach low error.
- **Worst: Linear Logistic Regression / Perceptron.** A single straight line cannot separate an XOR arrangement (the class centroids coincide) → high training error no matter where the line goes.

**Dataset 2** — **x** in the upper-right, **o** in the lower-left, separated by a rough diagonal, with a couple of points mixed across the boundary (one o among the x's, one x among the o's) → **roughly linearly separable + a little boundary noise.**

- **Best: Linear Logistic Regression / Perceptron** (or 5-NN). A line captures the diagonal split and **generalizes**, ignoring the few noisy points.
- **Worst: 1-NN.** It memorizes the noise — each mislabeled point becomes its own little island → a jagged, overfit boundary that generalizes poorly.

*(The sheet notes "more than one right answer" — the key distinction it wants: non-linear data ⇒ k-NN beats linear; near-linear noisy data ⇒ linear beats 1-NN.)*

---

## Aufgabe 3 — Entscheidungsgrenze (Decision Boundary)

w = (w₀, w₁, w₂) = (−1, 1, 2), so hₘ(x) = w·x = **−1 + x₁ + 2x₂** (x = (1, x₁, x₂)).

**a) Point-slope form** (x = x₁ on the x-axis, y = x₂ on the y-axis). Set hₘ = 0:
−1 + x₁ + 2x₂ = 0 ⇒ 2x₂ = 1 − x₁ ⇒ **x₂ = −½·x₁ + ½**.
So **y = x₂**, slope **a = −w₁/w₂ = −1/2**, intercept **b = −w₀/w₂ = 1/2**.

**b) Line hₘ = 0:** x₂ = −½x₁ + ½ — through **(0, ½)** and **(1, 0)** (also (−1, 1), (3, −1)). Slope −½.

**c) Line hₘ = +1:** −1 + x₁ + 2x₂ = 1 ⇒ **x₂ = −½x₁ + 1** — through **(0, 1)** and **(2, 0)**.

**d) Line hₘ = −1:** −1 + x₁ + 2x₂ = −1 ⇒ **x₂ = −½x₁** — through **(0, 0)** and **(2, −1)**.

All three are **parallel** (slope −½), intercepts **0 (hₘ=−1), ½ (hₘ=0), 1 (hₘ=+1)** — equally spaced, the +1 line offset toward the positive side. Perpendicular gap between consecutive lines = 1/‖(w₁,w₂)‖ = 1/√5.

---

*Numbers/geometry above are computed and checked; confirm against the tutorial if recordings appear.*
