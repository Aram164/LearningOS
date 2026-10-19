---
id: note-aml-l05-exercise-bank
type: note
title: "AML Lecture 05 — Exercise Bank (Logistic Regression)"
created: "2026-07-11"
role: exercise-bank
state: evolving
authorship: mixed
concepts: [concept-logistic-regression, concept-maximum-likelihood, concept-cross-entropy]
sources: [source-aml-ss26-lectures, source-cs4780-homeworks]
contexts: [workspace-aml-exam-prep]
---

> **Migration note (2026-07-17, Stage 2):** body preserved verbatim from
> `Plans/ML/foundations/AML/my notes/lect05 logistic regression/AML_L05_Exercise_Bank.md` (legacy tree).

# AML Lecture 05 — Exercise Bank (Logistic Regression)

All practice for L05 in one place: the sigmoid, decision boundaries, the cross-entropy loss & gradient, and regularized logistic regression. External links verified live; everything here has **solutions** to self-check against.

**Reading-scope rule:** practice is matched to what AML L05 covers — **sigmoid, decision boundary, cross-entropy from MLE, the gradient, L2-regularized logistic regression**. Material on **LDA / QDA / Naive Bayes** (ISLP Ch 4's other half) is a *different* classifier family — flagged **skip** for L05.

---

## 1. Local material (this folder)

| File | What it is |
|------|-----------|
| `AML_L05_Ultimate_Reference.md` | Full topic reference (TOC + self-test) — the recall source |
| `AML_L05_Mock_Exam.md` | 100-pt mock exam (sigmoid, cross-entropy, gradient, boundary), verified key |
| `AML_BonusSheet03_Solution.md` | Worked solution to **Bonusblatt 3** — Aufgabe 2 (classifier comparison) + Aufgabe 3 (decision-boundary geometry) are the L05 parts |
| `AML_L05_Mini_Plan.md` | Sequenced study path (videos + readings) |

## 2. Source sheets to solve (in the repo)

- **Übungsblatt 3** (the graded notebook, inside `…/Exercise slides/Übung 06 .pdf`) — **the main L05 practice**: Task 1 sigmoid · 2 hypothesis · 3 cost + gradient · 4 gradient descent · 5 learning-rate sensitivity · 6 evaluation · 7 **regularized** cost + gradient · 8 effect of λ (microchip, degree-6) · 9–10 sentiment analysis (`SGDClassifier`).
- **Bonusblatt 3** Aufgabe 2 (1-NN/5-NN/logistic/perceptron comparison) + Aufgabe 3 (decision-boundary lines for `𝐰·𝐱 = 0, ±1`) — ✓ solution key above.

## 3. External practice — solution-checked, matched to L05

- ✓ **CS4780 HW (local)** ⭐ — `…/CS4780-homeworks/2018Fall/HW4/` **Problem 3 (Logistic Regression — derive the gradient of the log-likelihood / MLE)**, full solution PDF. Same course as your lecture videos.
- ✓ **Caltech LFD Homework 5** (logistic regression + the SGD experiment) ⭐ — [HW](https://work.caltech.edu/homework/hw5.pdf) + [solution](https://work.caltech.edu/homework/hw5_sol.pdf).
- **Géron *Hands-On ML* Ch 4** (local PDF) — logistic + softmax regression, **solutions in Appendix A**.
- **MIT 6.036 (OLL)** — auto-graded logistic-regression unit · **Ng Coursera ex2** — logistic regression ([repo](https://github.com/blitz70/ML)).

## 4. Key ISLP exercises (scoped to L05)

ISLP §4.8 (Ch 4) exercises; solutions on **botlnec**.

**Logistic regression — in-scope (do these):**
- **4.6 ⭐⭐** — by-hand logistic regression: given coefficients `β₀=−6, β₁=0.05 (hours), β₂=1 (GPA)`, (a) compute `P(A)` for a student with 40h & GPA 3.5; (b) find the hours for a 50% chance. *Exactly the σ(w·x) + boundary skills.* [solution](https://botlnec.github.io/islp/sols/chapter4/exercise6/)
- **4.1 ⭐** — show the **logistic form ⟺ the odds form** (`p/(1−p) = e^{β₀+β₁X}`). The algebra behind the sigmoid. [solution](https://botlnec.github.io/islp/sols/chapter4/exercise1/)

**⚠️ Skip for L05 (different classifier family — LDA/QDA/Naive Bayes, not AML L05):** ISLP **4.2, 4.3, 4.4, 4.5, 4.7**. (They belong to later SaD/AML topics, not logistic regression.)

---

## 5. Suggested sequence

1. **Übungsblatt 3 Tasks 1–5** (sigmoid → hypothesis → cost + gradient → gradient descent → learning rate) — the core build.
2. **ISLP 4.6** (compute P + boundary) + **4.1** (odds algebra) → botlnec.
3. **`AML_L05_Mock_Exam.md`** (75 min, timed) → self-grade.
4. **CS4780 2018Fall HW4 Problem 3** (derive the logistic gradient) + **Caltech LFD HW5** → check solutions.
5. **Übungsblatt 3 Tasks 7–10** (regularized LR on microchip + sentiment analysis) + **Bonusblatt 3** Aufgabe 2–3.

Anything you miss → reread the cited § in `AML_L05_Ultimate_Reference.md`.

---

*No HU AML Altklausuren are public (see `LEARNING-RESOURCES.md` §6). The above is matched, solution-bearing practice, scoped to the lecture.*
