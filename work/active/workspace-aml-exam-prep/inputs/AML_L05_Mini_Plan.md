# AML Lecture 05 — Mini Learning Plan (Logistic Regression)

> **📌 Closes step: F.I2** (AML L05) · supports **F.I-test**. Log completion in `SESSION-LOG.md` + tick SEMESTER-STATUS §3.

Sequenced study path for L05, in the **lecture's own order** (VL05: classification → decision boundary → sigmoid → loss from MLE → gradient). Each step pairs **concept → lecture video → reading → practice**.

**Primary course material:** `…/SoSe 2026/lecture slides/VL 05-logistic-regression.pdf` + the graded notebook `…/Exercise slides/Übung 06 .pdf` (**3. Übungsblatt: Logistic Regression**).
**Reference:** `AML_L05_Ultimate_Reference.md` (this folder — detailed, with TOC + self-test).

> **Reading scope:** readings are matched to what AML L05 covers — **sigmoid, decision boundary, cross-entropy from MLE, the gradient, L2-regularized logistic regression** — and assume earlier AML lectures (L03 dot products/design matrix, L04 basis expansion + regularization). The **LDA / QDA / Naive Bayes** half of ISLP Ch 4 is a *different* classifier family → **skip** for L05. The optimizer (gradient descent) is fully covered in **L06**.
>
> **Andrew Ng videos** (Week 3 of the [Coursera ML playlist](https://www.youtube.com/playlist?list=PLiPvV5TNogxIS4bHQVW4pMkj4CHA8COdX)) mirror this lecture almost slide-for-slide: *"Classification" → "Hypothesis Representation" → "Decision Boundary" → "Cost Function" → "Simplified Cost Function and Gradient Descent."* Find them by title.

---

## Step 1 — From classification to the sigmoid hypothesis  (~1 h)

Why linear regression + threshold fails (outliers); the **sigmoid** `σ(z)=1/(1+e⁻ᶻ)` squashes the score into `[0,1]`; `h_𝐰(x)=σ(𝐰·𝐱)=P(y=1∣x)`.

- 🎥 **Andrew Ng — "Classification" → "Hypothesis Representation"** (Week 3).
- 🎥 **CS4780 #15 — Logistic Regression** — https://www.youtube.com/watch?v=GnkDzIOxfzI
- 📝 **CS4780 lecture notes (written companion)** — [Logistic Regression](http://www.cs.cornell.edu/courses/cs4780/2018fa/lectures/lecturenote06.html).
- 📖 **ISLP §4.3.1** (the logistic model) — local: `…/Bücher/Introduction to Statistical Learning .pdf`. · **Toronto CSC411 §8.2** (concise).
- 📝 Reference §1–§9.

## Step 2 — The decision boundary  (~45 min)

`𝐰·𝐱 = 0` is the boundary (line ↔ weight vector); it's **scale-invariant**; **basis expansion** gives non-linear boundaries (e.g. a circle).

- 🎥 **Andrew Ng — "Decision Boundary"** (Week 3).
- 📝 Reference §3–§5, §10. Worked: line `x₂=−x₁+4 ⟺ 𝐰=(−4,1,1)`; classify `(3,3)`/`(1,1)`.

## Step 3 — Cross-entropy loss & MLE  (~1.5 h)

Why not MSE (non-convex); the loss from **maximum likelihood**: product of per-sample likelihoods → log → sum → negate → **binary cross-entropy** `L(𝐰)=−(1/m)Σ[y·ln h + (1−y)·ln(1−h)]`.

- 🎥 **Andrew Ng — "Cost Function"** (logistic) + **CS229 Lecture 3** (the MLE/GLM derivation, [playlist](https://www.youtube.com/playlist?list=PLoROMvodv4rMiGQp3WXShtMGgzqpfVfbU)).
- 🔗 **StatQuest** — *Logistic Regression* + *Maximum Likelihood* singles ([video index](https://statquest.org/video-index/)) — clearest log-loss intuition.
- 🔗 **scikit-learn user guide §1.1.11 Logistic regression** — [link](https://scikit-learn.org/stable/modules/linear_model.html#logistic-regression) — authoritative, free.
- 📖 **ISLP §4.3.2** (estimating the coefficients — MLE) · **Murphy PML1 §10.2.3** (MLE, dense, optional) · *optional depth:* **ESL §4.4**.
- 📖 **CS229 Lecture Notes §2.1 (logistic regression) + §3.2.2 (logistic via GLM)** — `…/Bücher/CS229 Lecture Notes.pdf` (p.20, p.30) — the sigmoid + the log-likelihood gradient `(y − hθ(x))·x` (same "signed-error × feature" skeleton as L03), and the **GLM derivation of *why* the sigmoid is the right function**; §2.3 adds Newton's method. The written companion to the **CS229 Lecture 3** video above.
- 📝 Reference §11–§14.

## Step 4 — The gradient, convexity & regularization  (~1 h)

`∂L/∂wⱼ = (1/m)Σ(h−y)xⱼ` — same "signed-error × feature" form as linear regression; cross-entropy is **convex** but has **no closed form** → gradient descent (**L06**). On separable data weights blow up → **L2-regularized logistic regression** (exclude `w₀`).

- 🎥 **Andrew Ng — "Simplified Cost Function and Gradient Descent"** (Week 3).
- 📖 **Murphy PML1 §10.2.4** (SGD for logistic regression) — optional.
- 📝 Reference §15–§16 (gradient, convexity, regularized LR + the microchip/degree-6 setup).

## Step 5 — Practice & self-test

See **`AML_L05_Exercise_Bank.md`** (this folder) for the full, scoped list. Highlights:

- **Übungsblatt 3** (in `Übung 06 .pdf`) — the graded 10-task notebook (sigmoid → … → regularized LR → sentiment). **The main L05 practice.**
- **`AML_L05_Mock_Exam.md`** (75 min) → self-grade with its key.
- **ISLP 4.6** (compute `P` + boundary) + **4.1** (odds algebra) → botlnec. *(Skip 4.2–4.5/4.7 — LDA/QDA/NB, not L05.)*
- ✓ **CS4780 2018Fall HW4 Problem 3** (derive the logistic gradient) + **Caltech LFD HW5** (logistic + SGD) — local/linked, with solutions.
- **Bonusblatt 3** Aufgabe 2–3 → ✓ `AML_BonusSheet03_Solution.md`.

---

### Suggested schedule (~5 h)

| Session | Steps |
|---|---|
| 1 | Steps 1–2 (sigmoid + decision boundary) |
| 2 | Step 3 (cross-entropy / MLE) + start Übungsblatt 3 (Tasks 1–3) |
| 3 | Step 4 (gradient + regularization) + Übungsblatt 3 Tasks 4–8 |
| 4 | Mock exam (timed) → review; ISLP 4.6/4.1; CS4780 HW4 P3 |
