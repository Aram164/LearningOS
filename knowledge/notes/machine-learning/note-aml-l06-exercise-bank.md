---
id: note-aml-l06-exercise-bank
type: note
title: "AML Lecture 06 — Exercise Bank (Gradient Descent)"
created: "2026-07-11"
role: exercise-bank
state: evolving
authorship: mixed
concepts: [concept-gradient-descent, concept-adam-optimizer, concept-convexity, concept-feature-scaling]
sources: [source-aml-ss26-lectures]
contexts: [workspace-aml-exam-prep]
---

> **Migration note (2026-07-17, Stage 2):** body preserved verbatim from
> `Plans/ML/foundations/AML/my notes/lect06 gradient descent/AML_L06_Exercise_Bank.md` (legacy tree).

# AML Lecture 06 — Exercise Bank (Gradient Descent)

All practice for L06 in one place: the GD update, the learning rate, convexity, feature scaling, and batch / SGD / mini-batch. External links verified live; everything here has **solutions** to self-check against.

**Reading-scope rule:** practice is matched to what AML L06 covers — **the GD algorithm, the gradient, learning rate, feature scaling, and SGD/mini-batch**. Note: **ISLP barely covers GD** (it uses closed-form/`glmnet` solvers), so the book matches here are **Murphy Ch 8 / MML Ch 7**, not ISLP — don't go hunting for ISLP "gradient descent" exercises.

---

## 1. Local material

| File | What it is | Where |
|------|-----------|-------|
| `AML_L06_Ultimate_Reference.md` | Full topic reference (TOC + self-test) | this folder |
| `AML_L06_Mock_Exam.md` | 100-pt mock exam (iterations, learning rate, GD steps), verified key | this folder |
| `AML_L06_Mini_Plan.md` | Sequenced study path (videos + readings) | this folder |
| `AML_BonusSheet03_Solution.md` | Worked solution to **Bonusblatt 3** — **Aufgabe 1 (Gradientenabstieg)** is the L06 part | `../lect05 logistic regression/` |

## 2. Source sheets to solve (in the repo)

- **Bonusblatt 3 Aufgabe 1** (*Gradientenabstieg*): GD vs SGD, why normalize the data, learning-rate effect on the train loss. ✓ solution in `../lect05 logistic regression/AML_BonusSheet03_Solution.md`. **The main conceptual L06 drill.**
- **Übungsblatt 3 Tasks 4–5** (inside `…/Exercise slides/Übung 06 .pdf`) — implement **gradient descent** + study **learning-rate sensitivity** (`α=100` diverges, `α=0.05` slow). The hands-on coding.
- **By-hand:** re-derive the `L(w)=(w−3)²`, `α=0.25` iteration table (→ 0, 1.5, 2.25, 2.625, …); then redo with `α=0.5` (1 step), `α=1` (oscillates). *The single best 5-minute GD drill.*

## 3. External practice — solution-checked, matched to L06

- ✓ **CS4780 HW (local)** ⭐ — `…/CS4780-homeworks/2018Spring/HW6/` **Problem 1 (Optimization with Gradient Descent)** + `2018Fall/HW4/` **Problem 3 (GD for the logistic-regression MLE)**, full solution PDFs.
- ✓ **Caltech LFD Homework 5** (logistic regression via **stochastic gradient descent** — the classic experiment) ⭐ — [HW](https://work.caltech.edu/homework/hw5.pdf) + [solution](https://work.caltech.edu/homework/hw5_sol.pdf).
- **Géron *Hands-On ML* Ch 4** (local PDF) — batch vs stochastic vs mini-batch GD, learning schedules, **solutions in Appendix A**. ⭐ (best book-level GD practice).
- **MIT 6.036 (OLL)** — auto-graded gradient-descent unit · **Ng Coursera ex1** (GD for linear regression, [repo](https://github.com/blitz70/ML)).
- 🔗 **Reading:** **[Stanford CS231n — Optimization / SGD](https://cs231n.github.io/optimization-1/)** ⭐ — read it, then re-derive the numerical-gradient-vs-analytic-gradient check and the SGD update by hand. *Optional depth:* **[distill.pub — "Why Momentum Really Works"](https://distill.pub/2017/momentum/)** (momentum = the L06 outlook, beyond the examinable core).

## 4. Books (scoped to L06 — GD is *not* an ISLP topic)

- **Murphy PML1 Ch 8 "Optimization"** — §8.1–8.3 (local/convex, step size) + **§8.4 Stochastic gradient descent** — the on-scope reference. Local: `…/Bücher/probabilistic ML.pdf`.
- **MML Ch 7 "Continuous Optimization"** — [free PDF](https://mml-book.github.io/) — gradient descent + the math.
- ⚠️ **Skip:** there's no good *ISLP* exercise set for GD (ISLP §10.7.2 only mentions SGD inside the **deep-learning** chapter — beyond L06). Use the sheets + Géron + CS4780 instead.

---

## 5. Suggested sequence

1. **By-hand `L(w)=(w−3)²`** iteration table; vary `α` (0.25 → 0.5 → 1) and watch convergence/oscillation.
2. **Bonusblatt 3 Aufgabe 1** (GD vs SGD, normalization, learning rate) → solution key.
3. **`AML_L06_Mock_Exam.md`** (75 min, timed) → self-grade.
4. **Übungsblatt 3 Tasks 4–5** (code GD + learning-rate sensitivity).
5. **Caltech LFD HW5** (SGD experiment) + **CS4780 2018Spring HW6 P1** + **Géron Ch 4** exercises.

Anything you miss → reread the cited § in `AML_L06_Ultimate_Reference.md`.

---

*No HU AML Altklausuren are public (see `LEARNING-RESOURCES.md` §6). The above is matched, solution-bearing practice, scoped to the lecture.*
