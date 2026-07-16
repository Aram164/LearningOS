# AML Lecture 03 — Mini Learning Plan (Linear Regression)

> **📌 Closes step: F.E4** (AML L03) · supports **F.E-test**. Log completion in `SESSION-LOG.md` + tick SEMESTER-STATUS §3.

Sequenced study path for L03, extracted from `LEARNING-RESOURCES.md`. Each step pairs **concept → lecture video → book chapter(s) → practice**. Book sections verified against your local PDFs.

**Primary course material:** `…/SoSe 2026/lecture slides/VL 03-linear-regression.pdf` + tutorial `…/Exercise slides/Übung 03.pdf` (vectorization → single-predictor regression).
**Reference:** `AML_L03_Ultimate_Reference.md` (this folder — detailed, with TOC + self-test).

> For L03 the video weight shifts to **Andrew Ng** — Schäfer reuses his housing/tumor examples, so it's the closest fit.

---

## Step 1 — Simple & multiple linear regression  (~1.5 h)

The model hₘ(x) = w₁x + w₀ (and the multivariate w·x); fitting a line by least squares.

- 🎥 **Andrew Ng — Coursera ML** Weeks 1–2 (linear regression, one & multiple variables) — [playlist](https://www.youtube.com/playlist?list=PLiPvV5TNogxIS4bHQVW4pMkj4CHA8COdX) · or **CS229 Lecture 2** ([playlist](https://www.youtube.com/playlist?list=PLoROMvodv4rMiGQp3WXShtMGgzqpfVfbU))
- 📖 **ISLP** Ch 3 — §3.1 (simple), §3.2 (multiple) — `Bücher/Introduction to Statistical Learning .pdf`
- 📖 **Murphy PML1** Ch 11 "Linear Regression" — `Bücher/probabilistic ML.pdf`
- 📖 **Toronto CSC411** Ch 2 "Linear Regression"
- 📖 **MML** Ch 9 (Linear Regression) — [free](https://mml-book.github.io/) · **ESL** Ch 3 (depth)

## Step 2 — The normal equation & vectorized OLS  (~1 h)

Closed-form w₁ = (x−x̄)·(y−ȳ)/‖x−x̄‖²; the matrix form (XᵀX)⁻¹Xᵀy (your bonus-sheet 1 expression #4).

- 🎥 **3B1B — Essence of Linear Algebra** ([playlist](https://www.youtube.com/playlist?list=PLZHQObOWTQDPD3MizzM2xVFitgF8hE_ab)) — the visuals behind the normal equation (projection, dot products)
- 🎥 **CS4780 #17 — Linear Regression** (OLS = MLE) — https://www.youtube.com/watch?v=_21o_ylL0q4
- 📖 **ISLP** §3.2; **Murphy PML1** §11 "Example: MLE for linear regression"
- 📖 **CS229 Lecture Notes §1.1–1.3** ⭐ — `…/Bücher/CS229 Lecture Notes.pdf` (p.9–17) — **the written companion to your CS229 video spine**: §1.1 GD/LMS (also your L06), §1.2 the **normal equations via matrix calculus**, §1.3 **why squared-error = MLE under Gaussian noise** (the probabilistic justification the slides skip).
- 📝 Reference: the regression bridge doc (vectorized w₁/w₀ derivation)

## Step 3 — MSE loss & assessing the fit  (~45 min)

The ½m·‖w₁x+w₀−y‖² loss; R², RSE, the MSE-vs-w loss curve.

- 🔗 **Brandon Rohrer Ch 3** (choosing a loss function) — [link](https://brandonrohrer.com/how_modeling_works_3.html)
- 📖 **ISLP** §3.1.3 (assessing accuracy), §3.3 (other considerations)
- 🔗 StatQuest: linear regression / least squares / R² singles
- 🔗 *Optional depth:* **Setosa.io — "Ordinary Least Squares Regression" (visual)** — [interactive](https://setosa.io/ev/ordinary-least-squares-regression/) — drag the points and watch the least-squares line move; the cleanest intuition for what minimizing the MSE *does*.

## Step 4 — Practice & self-test

- **Bonusblatt 2** (`…/Bonus-exercises/zusatz-blatt02.pdf`) — Aufgabe 1 (linear regression, loss choice/differentiability) + Aufgabe 2 (multivariate regression). ✓ **solution key**: `AML_BonusSheet02_Solution.md` (this folder).
- **Übung 03 notebook** — the vectorized single-predictor regression implementation.
- **ISLP Ch 3 exercises** — conceptual + applied, solutions on [botlnec](https://botlnec.github.io/islp/sols/chapter3/exercise1/).
- **Caltech LFD Homework 2** (linear regression) ⭐ — [HW](https://work.caltech.edu/homework/hw2.pdf) + [solution key](https://work.caltech.edu/homework/hw2_sol.pdf). Solved, exam-style.
- **Géron *Hands-On ML* Ch 4** exercises (local PDF) — linear regression + normal equation, **solutions in Appendix A**.
- **MIT 6.036 (Open Learning Library)** regression units — auto-graded; **Ng Coursera ex1** — linear regression + GD ([repo](https://github.com/blitz70/ML)).
- ✓ **CS4780 HW (local)** — `…/CS4780-homeworks/2018Spring/HW6/` **Problem 2 (Linear Regression)** + Problem 1 (Gradient Descent), with full solution. ⭐

---

### Suggested schedule (~4–5 h)

| Session | Steps |
|---|---|
| 1 | Steps 1–2 (model + normal equation) |
| 2 | Step 3 + Bonusblatt 2 Aufgabe 1–2 |
| 3 | ISLP Ch 3 selected exercises → self-check |
