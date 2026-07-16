---
id: note-aml-l04-exercise-bank
type: note
title: "AML Lecture 04 — Exercise Bank (Non-linear Regression: Multivariate, Normal Equation, Polynomial, Regularization)"
created: "2026-07-11"
role: exercise-bank
state: evolving
authorship: mixed
concepts: [concept-basis-functions, concept-normal-equation, concept-regularization, concept-linear-regression]
sources: [source-aml-ss26-lectures]
contexts: [workspace-aml-exam-prep]
---

> **Migration note (2026-07-17, Stage 2):** body preserved verbatim from
> `Plans/ML/foundations/AML/my notes/lect04 non-linear regression/AML_L04_Exercise_Bank.md` (legacy tree).

# AML Lecture 04 — Exercise Bank (Non-linear Regression: Multivariate, Normal Equation, Polynomial, Regularization)

All practice for L04 in one place: the normal equation, singular `XᵀX`, polynomial features, overfitting, and Ridge/Lasso. External links verified live; everything here has **solutions** to self-check against.

**Reading-scope rule:** practice is matched to what AML L04 covers — **multivariate + normal equation, polynomial/computed features, Ridge/Lasso**. Material on **subset selection** (ISLP §6.1) and **splines/GAMs** (ISLP Ch 7) is **beyond L04** and flagged skip.

---

## 1. Local material (this folder)

| File | What it is |
|------|-----------|
| `AML_L04_Ultimate_Reference.md` | Full topic reference (TOC + self-test) — the recall source |
| `AML_L04_Mock_Exam.md` | 100-pt mock exam (normal equation + ridge by hand), verified key |
| `AML_L04_Mini_Plan.md` | Sequenced study path (videos + readings, in lecture order) |
| `../lect03 linear regression/AML_BonusSheet02_Solution.md` | Worked solution to **Bonusblatt 2** — Aufgabe 3 (classification, basis transform) is the L04 part |

## 2. Source sheets to solve (in the repo)

- **Bonusblatt 2** Aufgabe 3 (classification / decision boundary / **basis transform** → 0% error) — `…/Bonus-exercises/zusatz-blatt02.pdf`; ✓ solution key above.
- **Übung 04 notebook (Übungsblatt 2)** — multivariate **normal equation via `pinv`** + **polynomial features** + **Ridge/Lasso** (`λ=1`). The core "implement it" practice for L04.

### Übungsblatt 2 — the graded notebook, **non-linear + regularization part** (from `Übung 04.pdf`)

This is the second half of the same graded *2. Übungsblatt* (the linear half lives in `../lect03 linear regression/AML_L03_Exercise_Bank.md`).

**Worked polynomial example the deck does by hand (computer-verified):** basis-expand the single *Size* feature into `φ(x) = [1, x, x², √x]`, giving a **4×4** design matrix with `y = (660, 232, 315, 175)`. Then
`w = (XᵀX)⁻¹Xᵀy = np.linalg.pinv(X) @ y = (14265, 19.71, −0.002, −1008.6)`, i.e. the fitted curve `h(x) = 14265 + 19.71·x − 0.002·x² − 1008·√x`.
> ⚠️ The deck's punch-line: **don't form `(XᵀX)⁻¹` by hand** — `XᵀX` is badly conditioned here; use `np.linalg.pinv(X)` directly. (Exactly the singular-`XᵀX` lesson in §-normal-equation of the reference.)

**Regularization the deck covers:** Ridge `L = MSE + λΣwⱼ²` and Lasso `L = MSE + λΣ|wⱼ|`, solved as `w = (XᵀX + λI′)⁻¹Xᵀy` where `I′` zeros out the **bias** entry. The L2-vs-L1 geometry: **Lasso**'s diamond constraint meets the loss **on an axis → sparse weights (some exactly 0)**; **Ridge**'s circle → many **small** weights. Demo: a high-degree polynomial **overfits** (Linear + Poly) and is tamed by **Lasso + Poly (λ=1)** and **Ridge + Poly (λ=1)**.

**The graded non-linear / regularization tasks:** compute **polynomial features**; multivariate/**polynomial regression** (Tasks 4–7); **`PolynomialFeatures`** in scikit-learn (Tasks 8–9); **Bias (underfitting) vs Variance (overfitting)** (Task 10); **high-degree-polynomial overfitting with Lasso & Ridge** (Tasks 11–12); plus **RMSE on the test set** and **RMSE vs polynomial degree**. *(Abgabe was 09.06.26.)*

## 3. External practice — solution-checked, matched to L04

- ✓ **CS4780 HW (local)** ⭐ — `…/CS4780-homeworks/2018Spring/HW6/` **P1 (Gradient Descent) + P2 (Linear Regression) + P3 (Weighted Ridge)**, and `2018Fall/HW6/` **P1 (l2/ridge regularization)** + **P2 (bias-variance of regression)** — full solution PDFs.
- ✓ **Caltech LFD HW4 + HW6** (overfitting, regularization, validation) ⭐ — [HW4](https://work.caltech.edu/homework/hw4.pdf)/[sol](https://work.caltech.edu/homework/hw4_sol.pdf), [HW6](https://work.caltech.edu/homework/hw6.pdf)/[sol](https://work.caltech.edu/homework/hw6_sol.pdf).
- **Géron *Hands-On ML* Ch 4** (local PDF) — polynomial regression + Ridge/Lasso (+ the normal equation), **solutions in Appendix A**.
- 🔗 **scikit-learn "Underfitting vs. Overfitting"** — [runnable demo](https://scikit-learn.org/stable/auto_examples/model_selection/plot_underfitting_overfitting.html) (degree 1/4/15) — basically Übungsblatt 2 worked.
- **MIT 6.036 (OLL)** — auto-graded regularization unit · **Ng Coursera ex2/ex3** (regularization).
- 🔗 **Reading:** **[Pedro Domingos — "A Few Useful Things to Know About Machine Learning"](https://homes.cs.washington.edu/~pedrod/papers/cacm12.pdf)** — "overfitting has many faces" + "more data beats a cleverer algorithm" are the L04 framing for why you regularize.

## 4. Key ISLP exercises (scoped to L04)

ISLP §6.6 (Ch 6) exercises; solutions on **botlnec**. Read the prompt in the book, solve, then check.

**Regularization — in-scope (do these):**
- **6.4 ⭐⭐** — as **λ increases from 0** in ridge, what happens to (a) training RSS (b) test RSS (c) variance (d) squared bias (e) irreducible error? *The* regularization bias-variance exercise. [solution](https://botlnec.github.io/islp/sols/chapter6/exercise4/)
- **6.2 ⭐** — Lasso & Ridge **relative to least squares**: more/less flexible, and the bias–variance consequence. [solution](https://botlnec.github.io/islp/sols/chapter6/exercise2/)
- **6.3** — the **constraint-budget form** (minimize RSS s.t. `Σ|βⱼ| ≤ s`) as `s` grows. [solution](https://botlnec.github.io/islp/sols/chapter6/exercise3/)
- **6.5** — **two identical features**: ridge splits the weight equally, lasso doesn't → the sparsity contrast. [solution](https://botlnec.github.io/islp/sols/chapter6/exercise5/)

**From Ch 3 (multivariate / overfitting):**
- **3.3 ⭐** — five predictors incl. **gender interaction** (`x₅ = GPA·gender`) — this *is* Bonusblatt 2 Aufgabe 2; great cross-check. [solution](https://botlnec.github.io/islp/sols/chapter3/exercise3/)
- **3.4** — cubic vs linear **training/test RSS** (overfitting reasoning). [solution](https://botlnec.github.io/islp/sols/chapter3/exercise4/)
- **3.14** — **collinearity** → why it wrecks the fit (the data-side cause of a singular `XᵀX`). [solution](https://botlnec.github.io/islp/sols/chapter3/exercise14/)

**⚠️ Skip (beyond AML L04):** ISLP **6.1** (best-subset / forward / backward selection — AML doesn't do subset selection) and **all of Chapter 7's exercises** (splines, smoothing splines, GAMs). For the polynomial part, Géron Ch 4 + the sklearn demo are the right level.

---

## 5. Suggested sequence

1. **`AML_L04_Mock_Exam.md`** (normal equation + ridge shrinkage by hand, 75 min) → self-grade.
2. **ISLP 6.4 + 6.2** (regularization reasoning) → botlnec.
3. **CS4780 2018Spring HW6** (P1 GD, P2 linear regression, P3 weighted ridge) + **2018Fall HW6 P1** (ridge) → solutions. *Or* **Caltech LFD HW4 + HW6**.
4. **Géron Ch 4 exercises** (polynomial + Ridge/Lasso) → Appendix A; run the **sklearn overfitting demo**.
5. **Bonusblatt 2 Aufgabe 3** (basis transform) → solution key.

Anything you miss → reread the cited § in `AML_L04_Ultimate_Reference.md`.

---

*No HU AML Altklausuren are public (see `LEARNING-RESOURCES.md` §6). The above is matched, solution-bearing practice, scoped to the lecture.*
