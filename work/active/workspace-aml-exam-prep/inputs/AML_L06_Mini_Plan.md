# AML Lecture 06 — Mini Learning Plan (Gradient Descent)

> **📌 Closes step: F.J2** (AML L06) · supports **F.J-test**. Log completion in `SESSION-LOG.md` + tick SEMESTER-STATUS §3.

Sequenced study path for L06, in the **lecture's own order** (VL06: local search → gradient → GD algorithm → convexity → learning rate → feature scaling → SGD/mini-batch). Each step pairs **concept → lecture video → reading → practice**.

**Primary course material:** `…/SoSe 2026/lecture slides/VL 06-gradient_descent.pdf`.
**Reference:** `AML_L06_Ultimate_Reference.md` (this folder — detailed, with TOC + self-test).

> L06 is the **optimizer**: it fits the models of L03–L05 when there's no closed form (logistic regression) — and it underpins everything from here to neural nets.
>
> **Reading scope:** readings are matched to what AML L06 covers (the GD algorithm, learning rate, feature scaling, SGD/mini-batch). **GD is barely an ISLP topic** (ISLP uses closed-form/`glmnet` solvers), so the book matches are **Murphy Ch 8 / MML Ch 7**, *not* ISLP. The momentum/Adam/Newton material is a brief outlook → **optional depth**.
>
> **Andrew Ng videos** (in the [Coursera ML playlist](https://www.youtube.com/playlist?list=PLiPvV5TNogxIS4bHQVW4pMkj4CHA8COdX)): *"Gradient Descent" → "Gradient Descent Intuition" → "Gradient Descent For Linear Regression"* (Week 1), then *"Gradient Descent in Practice I – Feature Scaling"* and *"II – Learning Rate"* (Week 2). Find them by title.

---

## Step 1 — The gradient & the GD algorithm  (~1 h)

Local search (step opposite the derivative); the **gradient** = vector of partials; `𝐰 ← 𝐰 − α∇L(𝐰)`. The vectorized gradient `∇L = (1/m)Xᵀ(h_𝐰(X) − 𝐲)` is the **same** for linear (`h=X𝐰`) and logistic (`h=σ(X𝐰)`).

- 🎥 **Andrew Ng — "Gradient Descent" → "Gradient Descent Intuition" → "Gradient Descent For Linear Regression"** (Week 1).
- 🎥 **CS4780 #16 — Gradient Descent** — https://www.youtube.com/watch?v=o6FfdP2uYh4 · 📝 [written notes](http://www.cs.cornell.edu/courses/cs4780/2018fa/lectures/lecturenote07.html).
- 🎥 **3B1B — Neural Networks #2** "Gradient descent, how networks learn" ([playlist](https://www.youtube.com/playlist?list=PLZHQObOWTQDNU6R1_67000Dx_ZCJB-3pi)).
- 🔗 **Stanford CS231n — "Optimization: Stochastic Gradient Descent"** ⭐ — [notes](https://cs231n.github.io/optimization-1/) — the "walking downhill blindfolded" framing, the gradient as the slope, step-size effects, and SGD; course-quality and free.
- 📖 **CS229 Lecture Notes §1.1 "LMS algorithm"** ⭐ — `…/Bücher/CS229 Lecture Notes.pdf` (p.9) — **the written companion to your CS229 video spine**: derives **batch GD**, the LMS update `θ := θ + α(y − hθ(x))·x` (magnitude ∝ error), and **stochastic gradient descent**, in the lectures' exact notation. The best book match for L06.
- 📖 **Murphy PML1 Ch 8 §8.1–8.3** (Optimization: local/global, convex, smooth) — `…/Bücher/probabilistic ML.pdf` · **MML Ch 7** ([free](https://mml-book.github.io/)) · **Toronto CSC411 "Gradient Descent"**.
- 📝 Reference §1–§7.

## Step 2 — Convexity & the learning rate  (~45 min)

Convex loss → one global optimum (linear & logistic both convex); `α` too large → overshoot/diverge, too small → slow; **monitor the loss curve over epochs**.

- 🎥 **Andrew Ng — "Gradient Descent in Practice II – Learning Rate"** (Week 2).
- 🔗 **Brandon Rohrer — How optimization works** (4-part) — [link](https://brandonrohrer.com/how_optimization_works_1.html).
- 📝 Slides VL06 (the `α=100` diverges vs `α=0.05` slow plots); Reference §7–§9 (incl. the worked `L(w)=(w−3)²` table).

## Step 3 — Feature scaling  (~30 min)

Unequal feature scales → **elliptical** contours → GD zig-zags; scale → **circular** contours → straight to the minimum. Zero-mean and min-max normalization.

- 🎥 **Andrew Ng — "Gradient Descent in Practice I – Feature Scaling"** (Week 2).
- 📝 Reference §10–§11; cross-link `lect02 KNN-classifier/AML_L02_Ultimate_Reference.md` §6 (same scaling methods).

## Step 4 — Stochastic & mini-batch GD  (~45 min)

Batch (whole set, exact, slow) → **SGD** (one point, noisy, scalable) → **mini-batch** (32–128, the practical default). GD cost vs the normal equation. *(Brief outlook: momentum/Adam — optional.)*

- 📖 **Murphy PML1 §8.4** Stochastic gradient descent (+ "SGD for fitting linear regression").
- 🔗 *Optional depth:* **Sebastian Ruder — "An overview of gradient-descent optimization algorithms"** — [link](https://www.ruder.io/optimizing-gradient-descent/) (SGD → momentum → Adam; the outlook part of the lecture).
- 🔗 *Optional depth:* **distill.pub — "Why Momentum Really Works"** (Gabriel Goh, 2017) — [interactive](https://distill.pub/2017/momentum/) — gorgeous live demo of momentum; the **outlook** part of the lecture, beyond the core GD you're examined on.
- ⚠️ *Skip:* **ISLP §10.7.2** (SGD inside the **deep-learning** chapter) — beyond L06.
- 📝 Reference §12–§16.

## Step 5 — Practice & self-test

See **`AML_L06_Exercise_Bank.md`** (this folder) for the full, scoped list. Highlights:

- **By-hand:** the `L(w)=(w−3)²`, `α=0.25` iteration table; then vary `α` (0.5 → 1 step, 1 → oscillates). *The best 5-minute GD drill.*
- **Bonusblatt 3 Aufgabe 1** (*Gradientenabstieg*) → ✓ `../lect05 logistic regression/AML_BonusSheet03_Solution.md`.
- **`AML_L06_Mock_Exam.md`** (75 min) → self-grade with its key.
- **Übungsblatt 3 Tasks 4–5** (code GD + learning-rate sensitivity).
- ✓ **CS4780 2018Spring HW6 P1** (Optimization with GD) + **Caltech LFD HW5** (SGD experiment) + **Géron Ch 4** (batch/SGD/mini-batch) — local/linked, with solutions.

---

### Suggested schedule (~4 h)

| Session | Steps |
|---|---|
| 1 | Step 1 (gradient + algorithm) + the by-hand `(w−3)²` drill |
| 2 | Steps 2–3 (learning rate + feature scaling) + Bonusblatt 3 Aufgabe 1 |
| 3 | Step 4 (SGD/mini-batch) + Übungsblatt 3 Tasks 4–5 (code GD) |
| 4 | Mock exam (timed) → review; Caltech HW5 / CS4780 HW6 P1 |
