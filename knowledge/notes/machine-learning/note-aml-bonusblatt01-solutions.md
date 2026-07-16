---
id: note-aml-bonusblatt01-solutions
type: note
title: "AML — Bonusaufgabe zu Übungsblatt 1 — Worked Solution"
created: "2026-07-11"
role: exercise-bank
state: evolving
authorship: mixed
concepts: [concept-k-nearest-neighbors, concept-bias-variance-tradeoff]
sources: [source-aml-ss26-lectures]
contexts: [workspace-aml-exam-prep]
---

> **Migration note (2026-07-17, Stage 2):** body preserved verbatim from
> `Plans/ML/foundations/AML/my notes/lect02 KNN-classifier/AML_BonusSheet01_Solution.md` (legacy tree).

# AML — Bonusaufgabe zu Übungsblatt 1 — Worked Solution

> **Unofficial.** The sheet states there is no Moodle correction; official solutions are only discussed in the tutorials (ab 26.05.26). This is a self-check key — all numerical parts are computer-verified. Topic: Vektorisierung + k-NN regression. (Klausur-prep, freiwillig.)

---

## Aufgabe 1 — Vektorisierung (dimensionality of each expression)

| Nr. | Ausdruck | Ergebnis | Why |
|-----|----------|----------|-----|
| Bsp | hₘ(x) = w·x + w₀ | **ℝ** (scalar) | dot product + scalar |
| (1) | f(x,z) = ‖x − z‖₂² , x,z ∈ ℝⁿ | **ℝ** (scalar) | a squared norm is a single number |
| (2) | x xᵀ , x ∈ ℝⁿˣ¹ | **ℝⁿˣⁿ** | outer product: (n×1)(1×n) = n×n matrix |
| (3) | X Xᵀ , X ∈ ℝᵐˣⁿ | **ℝᵐˣᵐ** | (m×n)(n×m) = m×m (the Gram matrix of rows) |
| (4) | (XᵀX)⁻¹ Xᵀy , X ∈ ℝᵐˣⁿ, y ∈ ℝᵐ | **ℝⁿ** | (n×n)(n×m)(m×1) = n×1 — the OLS weight vector |
| (5) | Σᵢ₌₁ᵐ αᵢ y⁽ⁱ⁾ x⁽ⁱ⁾ , α ∈ ℝᵐ, y⁽ⁱ⁾ ∈ ℝ, x⁽ⁱ⁾ ∈ ℝⁿ | **ℝⁿ** | each term = scalar·scalar·(n-vector); sum of n-vectors stays an n-vector |

**Dimension-tracking trick:** write each factor's shape and cancel inner dimensions — (a×b)(b×c) = a×c. A 1×1 result is a scalar (ℝ); an n×1 result is a vector (ℝⁿ).

Note (4) is exactly the **normal-equation solution** for linear regression — useful to recognize for VL 03.

---

## Aufgabe 2 — k-Nearest Neighbors (Regression, Manhattan / L₁ distance)

Setup: the "feature" is the **day**, distance = |day_query − day_data|, prediction ŷ = **mean of the k nearest days' prices**. Tie-rule: if the k-th and (k+1)-th neighbor are equidistant, take the **earlier date**.

Data: 13.→8200, 15.→8400, 17.→8300, 19.→8300, 21.→8500, 23.→8700.

### a) Predictions

| Tag (2018) | nearest @ k=2 | ŷ (k=2) | nearest @ k=3 | ŷ (k=3) |
|------------|---------------|---------|----------------|---------|
| 10.04 | 13, 15 | **8300** | 13, 15, 17 | **8300** |
| 14.04 | 13, 15 | **8300** | 13, 15, 17 | **8300** |
| 18.04 | 17, 19 | **8300** | 17, 19, 15 | **8333.3** |
| 21.04 | 21, 19 | **8400** | 21, 19, 23 | **8500** |
| 25.04 | 23, 21 | **8600** | 23, 21, 19 | **8500** |

Worked examples:

- **10.04, k=2:** distances to 13/15/17/… = 3/5/7/… → nearest = {13, 15} → (8200+8400)/2 = **8300**.
- **18.04, k=3:** distances = 17:1, 19:1, 15:3, 21:3, 13:5, 23:5. The 3rd and 4th neighbors tie at distance 3 (days 15 and 21) → take the **earlier date, 15** → mean(8300, 8300, 8400) = **8333.3**.
- **21.04, k=2:** day 21 is itself a data point (distance 0). The 2nd and 3rd neighbors tie at distance 2 (days 19 and 23) → take **19** → mean(8500, 8300) = **8400**.

### b) k = 2 regression line, 09.–27.04 (values to plot)

k-NN regression is a **step function** (piecewise constant), changing only between data days:

| Days | ŷ (k=2) |
|------|---------|
| 09.–15.04 | 8300 |
| 16.–17.04 | 8350 |
| 18.–19.04 | 8300 |
| 20.–21.04 | 8400 |
| 22.–27.04 | 8600 |

Plot it as flat horizontal segments at those heights. Notice the line is **completely flat (8300) from 09–15** and **flat (8600) from 22–27** — that flat behaviour at the two ends is the setup for part (c).

### c) Limitation outside the recorded range

**k-NN cannot extrapolate.** For any query day before the first or after the last data point, the k nearest neighbors are always the same boundary points, so the prediction **saturates to a constant** (the mean of those endpoint values) — e.g. every day from 09–14.04 predicts 8300, every day from 24–27.04 predicts 8600. It can't capture or continue a trend beyond the data; it only interpolates within the observed range.

### d) Train vs test error (MSE) vs k — sketch

```
MSE
 │                                    ● test (U-shaped)
 │  ●                              ●
 │    ●                        ●
 │      ●●              ●●●
 │          ●●●  ●●●            ← test minimum = optimal k
 │    ___________________  train (rises from 0)
 │   /
 0 ●__________________________________→ k
     1    3    5    7    9
```

- **Training MSE (lower curve):** starts at **0 at k=1** — each training point is its own nearest neighbor, so it predicts its own value exactly. Rises monotonically as k grows (more averaging → predictions drift from the actual training values).
- **Test MSE (upper curve):** **U-shaped.** High at k=1 (**overfitting / high variance** — predictions chase noise), drops to a minimum at an intermediate k, then rises again for large k (**underfitting / high bias** — ŷ approaches the global mean).
- Label the lower curve "Trainingsfehler", the U-curve "Testfehler", and mark the U-minimum as the best k.

### e) Choosing an "optimal" k from the training data

**Notation first — this is the trap.** Two unrelated things are both called "k":

- **κ** = the **neighbor count**, the hyperparameter we want to optimize.
- **r** = the **number of folds** in cross-validation.

To find the best κ we use **r-fold cross-validation**: we carve a stand-in validation set *out of the training data*, so the real test set is never touched. That is how you tune κ "anhand der Trainingsdaten."

**The procedure, explicitly:**

1. Fix the candidate values to try, e.g. **κ ∈ {1, 2, 3, 4, 5}**.
2. Split the training set into **r** equal folds f₁,…,f_r. For a dataset this tiny, take r = n → **LOOCV** (each fold is one single point).
3. **Outer loop — for each candidate κ:**
   - **Inner loop — for each fold f_j:**
     - Use the *other* r−1 folds as the neighbor pool (the "training" part — for k-NN this just means: these are the points allowed to be neighbors).
     - Predict every point in f_j with κ-NN drawn from that pool.
     - Record the validation **MSE** on f_j.
   - Average the r fold-MSEs → **CV-MSE(κ)**.
4. Choose **κ\* = argmin_κ CV-MSE(κ)** — the neighbor count with the lowest average validation error.
5. **Refit** the final model on the *full* training set using κ\* (for k-NN: use all training points as the neighbor pool).

**Why it works:** each point is scored only while it sits in the held-out fold — never as its own neighbor — so the error is an honest generalization estimate. Rotating the held-out fold means every point is used for validation exactly once, and nothing leaks from the test set.

**Worked example on this dataset (LOOCV, r = n = 6).** Leave out each day, predict it from the other five with κ-NN, square the error, average over all six:

| κ (neighbors) | LOOCV-MSE |
|---------------|-----------|
| 1 | 28,333 |
| **2** | **24,583 ← minimum** |
| 3 | 26,852 |
| 4 | 30,104 |
| 5 | 38,400 |

So CV selects **κ\* = 2**. The error is **U-shaped in κ** — exactly the curve from part (d): κ = 1 overfits (each prediction copies a single noisy neighbor), large κ underfits (predictions drift toward the global mean ≈ 8,400). Sample fold at κ = 2: leave out 21.04 (actual 8500); the two nearest remaining days are 19 and 23 → ŷ = (8300 + 8700)/2 = 8500 → squared error 0.

(General algorithm: §9.4–§9.5 and §10.2 of your L02 reference.)

---

*Verify against the tutorial discussion if a recording is available; the numerical answers above are computed and checked. Next: `zusatz-blatt02`.*
