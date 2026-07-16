---
id: note-aml-bonusblatt02-solutions
type: note
title: "AML — Bonusaufgabe zu Übungsblatt 2 — Worked Solution"
created: "2026-07-11"
role: exercise-bank
state: evolving
authorship: mixed
concepts: [concept-linear-regression, concept-mean-squared-error, concept-normal-equation]
sources: [source-aml-ss26-lectures]
contexts: [workspace-aml-exam-prep]
---

> **Migration note (2026-07-17, Stage 2):** body preserved verbatim from
> `Plans/ML/foundations/AML/my notes/lect03 linear regression/AML_BonusSheet02_Solution.md` (legacy tree).

# AML — Bonusaufgabe zu Übungsblatt 2 — Worked Solution

> **Unofficial.** No Moodle correction; official solutions are discussed in the tutorials (ab 09.06.26). Self-check key — all numbers computer-verified. Covers **L03** (linear + multivariate regression) and **L04** (classification, basis transform). Cross-ref: `AML_L03_Ultimate_Reference.md` + `../lect04 non-linear regression/AML_L04_Ultimate_Reference.md`.

---

## Aufgabe 1 — Lineare Regression (MSE / MAE)

True ratings **y = [5, 1, 2, 3, 5, 4]**. Predictions per model below. Using **MSE = 1/m Σ(y−ŷ)²** and **MAE = 1/m Σ|y−ŷ|**, m = 6.

### a) MSE (fractions)

| Model | squared errors | Σ | **MSE = Σ/6** |
|-------|----------------|---|---------------|
| h⁽¹⁾ | .04+.16+.04+.04+.09+.01 | 0.38 | **19/300 ≈ 0.0633** |
| h⁽²⁾ | .04+.25+.25+.01+.36+.01 | 0.92 | **23/150 ≈ 0.1533** |
| h⁽³⁾ | .01+.09+.01+.01+.25+.04 | 0.41 | **41/600 ≈ 0.0683** |

### b) MAE (fractions)

| Model | abs errors | Σ | **MAE = Σ/6** |
|-------|-----------|---|---------------|
| h⁽¹⁾ | .2+.4+.2+.2+.3+.1 | 1.4 | **7/30 ≈ 0.2333** |
| h⁽²⁾ | .2+.5+.5+.1+.6+.1 | 2.0 | **1/3 ≈ 0.3333** |
| h⁽³⁾ | .1+.3+.1+.1+.5+.2 | 1.3 | **13/60 ≈ 0.2167** |

*Nice subtlety to notice:* h⁽¹⁾ has the lowest **MSE**, but h⁽³⁾ has the lowest **MAE** — the two losses can rank models differently. (If you use the lecture's L = 1/2m Σ(·)², just halve the MSE values.)

### c) Why prefer MSE over MAE (differentiability + GD)

**MSE is differentiable everywhere**; **MAE has a non-differentiable kink at error = 0** (|·| has no derivative there; its slope jumps from −1 to +1). For **gradient descent** this matters:

- MSE's gradient is smooth and **proportional to the error** (∝ (ŷ−y)·x) → larger errors produce larger corrections, and the convex quadratic has a clean **closed-form optimum** (the normal equation).
- MAE's (sub)gradient is a constant **±1** regardless of error size → no closed form, harder/oscillatory convergence near the minimum.

(Trade-off, worth a sentence: MAE is more robust to outliers; MSE punishes large errors quadratically. But for *optimization*, MSE's smoothness wins.)

---

## Aufgabe 2 — Multivariate Regression

Weights w₀=50, w₁=20, w₂=0.07, w₃=35, w₄=0.01, w₅=−10. Features x₁=GPA, x₂=IQ, x₃=Geschlecht (1 = weiblich, 0 = männlich), x₄=x₁·x₂, x₅=x₁·x₃.

**a)** hₘ(x) = **50 + 20·x₁ + 0.07·x₂ + 35·x₃ + 0.01·x₁x₂ − 10·x₁x₃**

**b) Male** (x₃ = 0 ⇒ x₅ = 0): hₘ,male(x) = **50 + 20·x₁ + 0.07·x₂ + 0.01·x₁x₂**

**c) Male, IQ 100, GPA 5.0:** 50 + 20·5 + 0.07·100 + 0.01·5·100 = 50 + 100 + 7 + 5 = **162** (thousand €).

**d) Female** (x₃ = 1 ⇒ x₅ = x₁): hₘ,female(x) = 50 + 20·x₁ + 0.07·x₂ + 35 + 0.01·x₁x₂ − 10·x₁ = **85 + 10·x₁ + 0.07·x₂ + 0.01·x₁x₂**

**e) Female, IQ 100, GPA 5.0:** 85 + 10·5 + 0.07·100 + 0.01·5·100 = 85 + 50 + 7 + 5 = **147** (thousand €).

**f) Identical?** No. female − male = (35·x₃ − 10·x₁x₃) with x₃=1 = **35 − 10·x₁**. So the gap *depends on GPA*: females are predicted **higher** for GPA < 3.5, **equal** at GPA = 3.5, and **lower** for GPA > 3.5 (the negative interaction x₅ = −10·x₁x₃ dominates at high GPA). At GPA 5.0 the gap is 35 − 50 = **−15** → female 147 vs male 162, matching (c)/(e). *(This is the classic ISLP 3.4-Q3 interaction-term point.)*

---

## Aufgabe 3 — Klassifikation (Alien-Stimmungsanalyse)

Sentence → (x₁ = #aack, x₂ = #beep), class:

| Satz | aack/beep | (x₁,x₂) | y |
|------|-----------|---------|---|
| 1 "aack aack aack beep" | 3/1 | (3,1) | Glücklich +1 |
| 2 "beep aack" | 1/1 | (1,1) | Traurig −1 |
| 3 "beep beep beep aack" | 1/3 | (1,3) | Glücklich +1 |
| 4 "aack aack beep beep beep aack" | 3/3 | (3,3) | Traurig −1 |

**a)** Plot x₁ (aack) horizontal, x₂ (beep) vertical: **+** at (3,1) and (1,3); **−** at (1,1) and (3,3). Both classes share the same centroid (2,2) → this is an **XOR pattern, not linearly separable.**

**b) Best linear boundary (min training error).** Since D is XOR, **no line achieves 0 error — the minimum is 1 misclassified point.** One optimal choice:

**w = (w₀, w₁, w₂) = (−3, 1, 1)** → boundary **x₁ + x₂ = 3**.
Check ŷ = sign(−3 + x₁ + x₂): (3,1)→+1 ✓, (1,1)→−1 ✓, (1,3)→+1 ✓, (3,3)→+1 ✗ (only (3,3) wrong). *(The answer isn't unique — any line with 1 error is valid.)*

**c)** Draw the line x₁ + x₂ = 3 (through (3,0) and (0,3)).

**d) Fifth alien "beep beep beep beep"** → (x₁,x₂) = (0,4). hₘ = −3 + 0 + 4 = **+1 ≥ 0 ⇒ sign = +1 ⇒ Glücklich.**

**e) Two classifiers that reach 0% training error on D** (i.e. handle the non-linear/XOR boundary):
1. **k-NN** (e.g. 1-NN) — flexible, non-linear boundary; 1-NN classifies every training point perfectly.
2. **Neural network** (with a hidden layer) — *or* logistic/linear classifier **with a non-linear feature transform** (exactly part f).

**f) Basis transform.** Products x₁·x₂: (3,1)→3, (1,3)→3 (the **+** class); (1,1)→1, (3,3)→9 (the **−** class). Centering on the + value 3 separates them:

> **missing value = −3**, i.e. Φ(x)₃ = **(x₁·x₂ − 3)²**

giving Φ₃: (3,1)→0, (1,3)→0, (1,1)→4, (3,3)→36 → now linearly separable on Φ₃ alone.

**Weights** (use only Φ₃; threshold between 0 and 4):
**w = (w₀, w₁, w₂, w₃) = (1, 0, 0, −1)** → hₘ = 1 − Φ₃.
Check: + points 1 − 0 = 1 ≥ 0 ✓; − points 1 − 4 = −3 < 0 and 1 − 36 < 0 ✓ → **0% training error.**

---

*Verify against the tutorial discussion if recordings appear; numbers above are computed and checked.*
