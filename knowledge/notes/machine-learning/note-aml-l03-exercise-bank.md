---
id: note-aml-l03-exercise-bank
type: note
title: "AML Lecture 03 — Exercise Bank (Linear Regression, one predictor + Linear Algebra + Vectorization)"
created: "2026-07-11"
role: exercise-bank
state: evolving
authorship: mixed
concepts: [concept-linear-regression, concept-mean-squared-error, concept-normal-equation]
sources: [source-aml-ss26-lectures]
contexts: [workspace-aml-exam-prep]
---

> **Migration note (2026-07-17, Stage 2):** body preserved verbatim from
> `Plans/ML/foundations/AML/my notes/lect03 linear regression/AML_L03_Exercise_Bank.md` (legacy tree).

# AML Lecture 03 — Exercise Bank (Linear Regression, one predictor + Linear Algebra + Vectorization)

All practice for L03 in one place: the closed-form line fit, the MSE loss, dot products / matrix shapes, the bias trick & vectorization. External links verified live; everything here has **solutions** to self-check against.

**Reading-scope rule:** practice is matched to what AML L03 covers (fit a line by MSE + the linear-algebra/vectorization toolkit). Anything needing **statistical inference** (standard errors, t-tests, p-values, confidence intervals — that's SaD, not AML L03) is flagged **skip**.

---

## 1. Local material (this folder)

| File | What it is |
|------|-----------|
| `AML_L03_Ultimate_Reference.md` | Full topic reference (TOC + self-test) — the recall source |
| `AML_L03_Mock_Exam.md` | 100-pt mock exam, all parts, verified answer key |
| `AML_BonusSheet02_Solution.md` | Worked solution to **Bonusblatt 2** Aufgabe 1 (MSE/MAE) + Aufgabe 2 (multivariate regression) |
| `AML_L03_Mini_Plan.md` | Sequenced study path (videos + readings) |

## 2. Source sheets to solve (in the repo)

- **Bonusblatt 1** Aufgabe 1 (*Vektorisierung* — dimensionality of expressions) — `…/Bonus-exercises/zusatz-blatt01.pdf`; ✓ solution in `../lect02 KNN-classifier/AML_BonusSheet01_Solution.md`. *(Directly drills the L03 dot-product/shape skills.)*
- **Bonusblatt 2** Aufgabe 1–2 (linear + multivariate regression) — `…/Bonus-exercises/zusatz-blatt02.pdf`; ✓ solution key local (above).
- **Übung 03 notebook** — vectorization (for-loop vs `np.sum` vs dot, ~20×) → single-predictor closed-form regression. The "implement it" practice.

### Übungsblatt 2 — the graded notebook, **linear-regression part** (from `Übung 04.pdf`)

The graded *2. Übungsblatt* spans L03 **and** L04 (linear → non-linear → regularization). The **linear** half belongs here; the polynomial/regularization half is in `../lect04 non-linear regression/AML_L04_Exercise_Bank.md`.

**Data:** house prices in Oregon, **m = 47** points; design matrix `X` carries a **bias column `x₀ = 1`** next to the size feature `x₁`.

**Worked walk-through the deck does by hand (recompute these as a drill):**
- **Vectorized hypothesis** — `Xw` computes `h_w(x⁽ⁱ⁾)` for *every* row at once. With `h_w(x) = 12.98·x + 63.58` (so `w = (63.58, 12.98)`): `x=44.78 → 644.8`, `19.85 → 321.2`, `12.36 → 224.0`, `18.11 → 298.7`, `12.68 → 228.2`. *(computer-checked)*
- **Vectorized residual & loss** — `Xw − y` is the per-row error vector; `‖Xw − y‖² = Σ(w·x⁽ⁱ⁾ − y⁽ⁱ⁾)²`; the **MSE** is `L(w) = (1/2m)·‖Xw − y‖²`.
- **Closed form (normal equation)** — set all `∂L/∂wⱼ = 0` → `w = (XᵀX)⁻¹Xᵀy` (the Moore–Penrose pseudo-inverse, `np.linalg.pinv`).

**The graded linear tasks (Tasks 1–3):** compute the **loss `L(w)`**; the **normal-equation** closed-form solution; **predict `y` from a single feature** (fit + plot the regression line). *(Abgabe was 09.06.26.)*

## 3. External practice — solution-checked, matched to L03

- ✓ **CS4780 HW (local)** — `…/CS4780-homeworks/2018Spring/HW6/` **Problem 2 (Linear Regression)** + **Problem 1 (Gradient Descent)**, full solution PDFs. ⭐ Same course as your lecture videos.
- ✓ **Caltech LFD Homework 2** (linear regression) ⭐ — [HW](https://work.caltech.edu/homework/hw2.pdf) + [solution](https://work.caltech.edu/homework/hw2_sol.pdf).
- **Géron *Hands-On ML* Ch 4** (local PDF) — linear regression + normal equation, **solutions in Appendix A**.
- **MIT 6.036 (Open Learning Library)** — auto-graded regression units · **Ng Coursera ex1** — linear regression + GD ([repo](https://github.com/blitz70/ML)).
- 🔗 **Reading:** **[Pedro Domingos — "A Few Useful Things to Know About Machine Learning"](https://homes.cs.washington.edu/~pedrod/papers/cacm12.pdf)** (the famous overview — overfitting/bias-variance, spans L02–L04). *Optional depth:* **[Setosa.io OLS visual](https://setosa.io/ev/ordinary-least-squares-regression/)** — drag points, watch the least-squares line move.

## 4. Key ISLP Chapter 3 exercises (scoped to L03)

ISLP §3.7 exercises; community solutions on **botlnec**. Read the prompt in the book, solve, then check.

**In-scope (do these):**
- **3.6 ⭐** — show the simple-regression line **passes through `(x̄, ȳ)`** — exactly the derivation in your reference §7 / mock-exam D2. [solution](https://botlnec.github.io/islp/sols/chapter3/exercise6/)
- **3.5** — show fitted values are a **linear combination `Σ aᵢ' yᵢ`** of the responses (linear smoother). [solution](https://botlnec.github.io/islp/sols/chapter3/exercise5/)
- **3.2** — **KNN classifier vs KNN regression** — ties back to L02. [solution](https://botlnec.github.io/islp/sols/chapter3/exercise2/)
- **3.7** — simple regression **R² = cor(X,Y)²** (light; touches SaD correlation). [solution](https://botlnec.github.io/islp/sols/chapter3/exercise7/)
- *Applied (coding):* **3.8** (simple regression on Auto), **3.13** (simulate + fit) — good NumPy/sklearn practice.

**⚠️ Skip for now (statistical inference — SaD, not AML L03):** **3.1** (null hypotheses / p-values), **3.11** (the t-statistic). AML L03 stops at fitting the line; SE/t-tests/CIs come from SaD.

---

## 5. Suggested sequence

1. **Bonusblatt 1 Aufgabe 1** (vectorization/shapes) + **Bonusblatt 2 Aufgabe 1–2** → check keys.
2. **ISLP 3.6 + 3.5** (the two derivations) → botlnec.
3. **`AML_L03_Mock_Exam.md`** (75 min, timed) → self-grade.
4. **CS4780 2018Spring HW6 Problem 2** *or* **Caltech LFD HW2** → check solution.

Anything you miss → reread the cited § in `AML_L03_Ultimate_Reference.md`.

---

*No HU AML Altklausuren are public (see `LEARNING-RESOURCES.md` §6). The above is matched, solution-bearing practice.*
