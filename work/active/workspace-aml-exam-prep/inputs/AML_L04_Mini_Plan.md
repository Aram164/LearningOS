# AML Lecture 04 — Mini Learning Plan (Non-linear Regression)

> **📌 Closes step: F.H1** (AML L04) · supports **F.H-test** (+ the multivariate half feeds F.E). Log completion in `SESSION-LOG.md` + tick SEMESTER-STATUS §3.

Sequenced study path for L04, in the **lecture's own order** (VL04 agenda: Multivariate → Non-linear/Polynomial → Regularization). Each step pairs **concept → lecture video → reading → practice**.

**Primary course material:** `…/SoSe 2026/lecture slides/VL 04-non-linear-regression.pdf` + tutorial `…/Exercise slides/Übung 04.pdf`.
**Reference:** `AML_L04_Ultimate_Reference.md` (this folder — detailed, with TOC + self-test).

> **Reading scope (important):** every reading below is matched to what AML L04 *actually* covers — **multivariate regression + normal equation, polynomial/computed features, Ridge/Lasso** — and assumes only earlier AML lectures (L02 bias-variance/CV, L03 linear regression). Sections that go past the lecture or need extra prerequisites are marked **skip / optional depth**. Pull the named section only, not whole chapters.
>
> **Andrew Ng videos:** they're all in the [Coursera ML playlist](https://www.youtube.com/playlist?list=PLiPvV5TNogxIS4bHQVW4pMkj4CHA8COdX), titled *"Lecture 02-xx …"* (the multiple-variables section) and the regularization section. Find them by title; the specific ones are named per step.

---

## Step 1 — Multivariate regression & the normal equation  (~1.5 h)

Many features at once: `h_𝐰(x) = w₁x₁ + … + wₙxₙ + w₀ = 𝐰·𝐱` (a hyper-plane); the **closed-form** solution `𝐰 = (XᵀX)⁻¹Xᵀ𝐲`, when `XᵀX` is singular, and `pinv`.

- 🎥 **Andrew Ng — "Linear Regression with multiple variables"** (Lecture 02-01 — *the video you linked*, [watch](https://www.youtube.com/watch?v=ViTUqw8kXPQ&list=PLiPvV5TNogxIS4bHQVW4pMkj4CHA8COdX&index=4)) → then **"Normal Equation"** and **"Normal Equation Noninvertibility"** (same 02-xx section). These are the *core* L04 videos — the one you found is the right starting point.
- 🔗 **Eli Bendersky — "Derivation of the Normal Equation"** ⭐ — [link](https://eli.thegreenplace.net/2014/derivation-of-the-normal-equation-for-linear-regression/) — derives `𝐰 = (XᵀX)⁻¹Xᵀ𝐲` in *exactly* Ng's notation; fills the proof AML leaves out.
- 📖 **ISLP §3.2 "Multiple Linear Regression"** — readable now (you did Ch 3 for L03). Local: `…/Bücher/Introduction to Statistical Learning .pdf`. · **Toronto CSC411 Ch 2** (concise).
- 📝 Reference §1–§5 (multivariate, gradient, normal equation, singular `XᵀX`, NE vs GD).

## Step 2 — Non-linear / polynomial regression  (~1 h)

Going non-linear by **adding computed/polynomial features** (x → x, x², x³, …) to a linear model — **a curve in x is a straight line in feature space, so it's still ordinary linear regression** (same loss, same normal equation; you only widen `X`). *AML stops here: no splines, GAMs, or local regression.*

> 🧭 **Read the "through-line" box at the top of Reference §6 first.** It connects polynomial features → overfitting → regularization into one story — the piece the lecture slides leave out (and the reason they feel random).

- 🎥 **Andrew Ng — "Features and Polynomial Regression"** ⭐ (a course we *already have* — [Coursera ML playlist](https://www.youtube.com/playlist?list=PLiPvV5TNogxIS4bHQVW4pMkj4CHA8COdX), Week 2) — the canonical, gentle "just add x² as a feature" walkthrough; the most on-point video for this topic.
- 📖 **MIT 6.036 (AML spine) — the *Features* unit** (Lecture 3) covers feature transformations incl. **polynomial features** and the overfitting they cause, with auto-graded exercises — [course](https://openlearninglibrary.mit.edu/courses/course-v1:MITx+6.036+1T2019/course/).
- 🔗 **scikit-learn — "Underfitting vs. Overfitting"** ⭐ — [interactive demo](https://scikit-learn.org/stable/auto_examples/model_selection/plot_underfitting_overfitting.html) — **the single best *visual* for polynomial regression**: degree 1 (underfit) → 4 (just right) → 15 (wild overfit), with runnable code. *(Reused in Step 3.)*
- 📖 **ISLP §7.1 Polynomial Regression (p.290) — *this section only.*** Light extension of Ch 3. **Skip §7.3 Basis Functions / §7.4 Splines (beyond L04).**
- 📖 **Toronto CSC411 §3 "Nonlinear Regression"** — best-scoped book match. Local: `…/Bücher/Machine Learning and Data Mining…CSC 411…pdf`.
- 📕 *Skip for now:* **ESL Ch 5** is graduate-level (splines/wavelets) — well beyond L04.
- 📝 Reference §6–§8.

## Step 3 — Overfitting & bias–variance  (~45 min)

*(Comes before regularization — regularization is the **fix** for the overfitting you see here.)* More features always lower *train* error; the *test* error is U-shaped in model flexibility / polynomial degree.

- 🔗 **scikit-learn — "Underfitting vs. Overfitting"** ⭐ — [interactive example](https://scikit-learn.org/stable/auto_examples/model_selection/plot_underfitting_overfitting.html) — polynomial degree 1 / 4 / 15 with train vs test curves and code. Directly previews the Übungsblatt 2 task.
- 📖 **ISLP §2.2.2 "The Bias-Variance Trade-Off"** — you already read it for L02; re-skim through the *polynomial-degree* lens.
- 🔗 **Pedro Domingos — "A Few Useful Things to Know About Machine Learning"** ⭐ — [pdf](https://homes.cs.washington.edu/~pedrod/papers/cacm12.pdf) — its "overfitting has many faces" and "more data beats a cleverer algorithm" sections are the perfect L04 framing (if you read it for L02, just re-read those two parts).
- 📝 Cross-link `lect02 KNN-classifier/AML_L02_Ultimate_Reference.md` §8 (incl. §8.1.1); Reference §9–§10.

## Step 4 — Regularization: Ridge & Lasso  (~1.5 h)

Penalizing weight size (L2 = Ridge `λΣwⱼ²`, L1 = Lasso `λΣ|wⱼ|`) to control overfitting; the λ knob; never penalize `w₀`. **The intuition:** a wiggly overfit curve needs *big* weights to make sharp turns; penalizing weight size forces a *smoother* curve. Ridge shrinks all weights; Lasso zeros some out. *(Reference §11–§14 has the through-line + both the geometric and the gradient "why L1 zeros weights".)*

- 🎥 **StatQuest — the regularization trilogy** ⭐⭐ (watch in order — this is the intuition the slides skip):
  1. [*Regularization Part 1: Ridge (L2)*](https://www.youtube.com/watch?v=Q81RR3yKn30) — shrink the slope to **desensitize** the fit.
  2. [*Regularization Part 2: Lasso (L1)*](https://www.youtube.com/watch?v=NGf0voTMlcs) — same idea, but it can drive a weight **to exactly 0**.
  3. [*Ridge vs Lasso, Visualized!!!*](https://www.youtube.com/watch?v=Xm2C_gTAl8c) — animates the **diamond-vs-circle** (Reference §14).
- 🎥 **Andrew Ng — Coursera ML, the full regularization set** ⭐ (a course we *already have*, and the most on-point): **"The Problem of Overfitting" → "Cost Function" (the regularized cost) → "Regularized Linear Regression" → "Regularized Logistic Regression"** — Week 3 of the [playlist](https://www.youtube.com/playlist?list=PLiPvV5TNogxIS4bHQVW4pMkj4CHA8COdX). The gentlest, exactly AML's level.
- 🎥 **Stanford CS229 2022 (AML spine) — Lecture 10 "Bias-Variance & Regularization"** ([playlist](https://www.youtube.com/playlist?list=PLoROMvodv4rNyWOpJg_Yh4NSqI4Z4vOYy)) — the rigorous version; frames **Ridge = MAP**. Heavier than Ng.
- 📖 **MIT 6.036 (AML spine) — the *Regression* chapter** derives **ridge regression** (`J_ridge = MSE + λ‖θ‖²`) with auto-graded exercises — [course](https://openlearninglibrary.mit.edu/courses/course-v1:MITx+6.036+1T2019/course/) · [notes](https://introml.mit.edu/notes/regression.html).
- 🔗 **Brandon Rohrer Ch 18 — Regularization** ⭐ — [link](https://brandonrohrer.com/regularization.html) (the index tags this *to L04*).
- 🔗 **scikit-learn user guide §1.1.2 Ridge / §1.1.3 Lasso** — [Linear Models](https://scikit-learn.org/stable/modules/linear_model.html) — authoritative, free, the math + the `+λI` closed form.
- 📖 **ISLP §6.2.1 Ridge + §6.2.2 Lasso (p.240)** — matches AML exactly. *(Skip §6.1 subset selection.)* · **Toronto CSC411 §3.2** (p.11).
- 📖 **CS229 Lecture Notes §9.1 "Regularization"** ⭐ — `…/Bücher/CS229 Lecture Notes.pdf` (p.125) — **the cleanest L04 treatment**: the regularized loss `Jλ = J + λR(θ)`, **L2 = weight decay** (with the `θ ← (1−λη)θ − η∇J` gradient derivation — *why* the weights shrink), and **L1 = ‖θ‖₁ = Lasso/sparsity**. Companion to your video spine. *(Feature-maps view of polynomial features: §5.1–5.2.)*
- 📕 *Optional depth:* **ESL §3.4 Shrinkage** (rigorous) · **Murphy PML1** ridge (in Ch 11, dense).
- 📝 Reference §11–§15 (Ridge, Lasso, L1/L2 geometry, Lₚ norms).

## Step 5 — Practice & self-test

- **Bonusblatt 2** (`…/Bonus-exercises/zusatz-blatt02.pdf`) — regression + decision-boundary/classification (Aufgabe 3). ✓ **solution key**: `../lect03 linear regression/AML_BonusSheet02_Solution.md`.
- **ISLP exercises** — **Ch 3** (multiple regression) + **§7.1** (polynomial) + **Ch 6** (Ridge/Lasso); solutions on [botlnec Ch 3](https://botlnec.github.io/islp/sols/chapter3/exercise1/) / [Ch 6](https://botlnec.github.io/islp/sols/chapter6/exercise1/) / [Ch 7](https://botlnec.github.io/islp/sols/chapter7/exercise1/). *(For Ch 7 do the polynomial problems only.)*
- **Caltech LFD HW4 + HW6** (overfitting, regularization, validation) ⭐ — [HW4](https://work.caltech.edu/homework/hw4.pdf)/[sol](https://work.caltech.edu/homework/hw4_sol.pdf), [HW6](https://work.caltech.edu/homework/hw6.pdf)/[sol](https://work.caltech.edu/homework/hw6_sol.pdf).
- **Géron *Hands-On ML* Ch 4** exercises (local) — polynomial + Ridge/Lasso, **solutions in Appendix A**.
- **MIT 6.036 (OLL)** regularization unit — auto-graded; **Ng Coursera ex1** (multivariate/normal-equation) + **ex2/ex3** (regularization).
- ✓ **CS4780 HW (local)** — `…/CS4780-homeworks/2018Spring/HW6/` **Problem 1 (GD) + Problem 2 (Linear Regression) + Problem 3 (Weighted Ridge)** and `2018Fall/HW6/` **Problem 1 (l2/ridge)**, with full solutions. ⭐

---

### Suggested schedule (~5 h)

| Session | Steps |
|---|---|
| 1 | Step 1 (multivariate + normal equation) — incl. the Eli Bendersky derivation |
| 2 | Step 2 (polynomial) + Step 3 (overfitting; run the sklearn demo) |
| 3 | Step 4 (Ridge/Lasso) + Bonusblatt 2 regularization tasks |
| 4 | ISLP / CS4780 / Caltech selected exercises → self-check |
