# AML Lecture 02 — Mini Learning Plan (k-Nearest Neighbors)

> **📌 Closes step: F.D3** (AML L02 — ✅ done KW 22) · supports **F.D-test**. Log completions in `SESSION-LOG.md` + tick SEMESTER-STATUS §3.

A sequenced study path for L02, extracted from `LEARNING-RESOURCES.md` and mapped to this lecture. Each step pairs the **concept → a lecture video → book chapter(s) → practice**. Practice details live in `AML_L02_Exercise_Bank.md` (same folder); the topic reference is `AML_L02_Ultimate_Reference.md`.

**Primary course material:** `…/SoSe 2026/lecture slides/VL 02-nearest-neighbor.pdf` + tutorial `…/Exercise slides/Übung 02 .pdf`. Everything below *supplements* those.

> Video note: Andrew Ng's Coursera course (great for L03+) **skips k-NN**, so L02's videos come from **Cornell CS4780 (Weinberger)**. Book page/section numbers are verified against your local PDFs.

---

## Step 1 — k-NN algorithm & distance metrics  (~1.5 h)

The core: store the data, classify a query by its nearest neighbours; distance choice (Lp), majority vote, k-NN regression.

- 🎥 **CS4780 #3 — k-NN** — https://www.youtube.com/watch?v=oymtGlGdT-k
- 📝 **CS4780 lecture notes** (written companion to videos #3/#4) — https://www.cs.cornell.edu/courses/cs4780/2018fa/lectures/lecturenote02_kNN.html — k-NN algorithm, the **Bayes optimal classifier** + Cover–Hart (1-NN ≤ 2× Bayes error) bound, and the curse of dimensionality
- 📖 **ISLP** §2.2.3 (k-NN intro) + **§4.7.6** "K-Nearest Neighbors" (p.183) — `Bücher/Introduction to Statistical Learning .pdf`
- 📖 **Murphy PML1** §16.1 "K nearest neighbor (KNN) classification" — `Bücher/probabilistic ML.pdf`
- 📖 **Toronto CSC411 notes** §3.4 + §8.4 (K-Nearest Neighbors) — `Bücher/Machine Learning and Data Mining…CSC 411…pdf`
- 📝 Reference: `AML_L02_Ultimate_Reference.md` §3–§4 (algorithm, distances)

## Step 2 — Curse of dimensionality & feature scaling  (~45 min)

Why k-NN breaks in high dimensions; why features must be scaled before any Lp distance.

- 🎥 **CS4780 #4 — Curse of Dimensionality** — https://www.youtube.com/watch?v=BbYV8UfMJSA  *(the video you shared)*
- 📖 **Murphy PML1** §16.1.2 "The curse of dimensionality"
- 📝 Reference §4.6 (sensitivity to features) + §6 (feature scaling)

## Step 3 — Bias–variance & over/underfitting  (~1 h)

Small k = high variance (overfit), large k = high bias (underfit); the U-shaped test error.

- 🎥 **CS4780 — Bias/Variance Tradeoff** (playlist; [notes](http://www.cs.cornell.edu/courses/cs4780/2018fa/lectures/lecturenote12.html))
- 📖 **ISLP** §2.2.2 "The Bias-Variance Trade-Off"
- 📖 **ESL** (free PDF) §2.9 "Model Selection and the Bias–Variance Tradeoff" — optional depth
- 📖 **Murphy PML1** — the "Bias-variance tradeoff" section (Ch 4, ERM/generalization) — optional
- 🔗 StatQuest bias-variance single (embedded in the reference docs); Brandon Rohrer's regularization/bias-variance posts
- 🔗 **Scott Fortmann-Roe — "Understanding the Bias-Variance Tradeoff"** ⭐ — [link](https://scott.fortmann-roe.com/docs/BiasVariance.html) — the canonical essay, and it works the decomposition **through k-NN** (exactly §8 here).
- 🔗 **Pedro Domingos — "A Few Useful Things to Know About Machine Learning"** ⭐ (CACM 2012) — [pdf](https://homes.cs.washington.edu/~pedrod/papers/cacm12.pdf) — the famous overview: overfitting, bias–variance, the curse of dimensionality, "more data beats a cleverer algorithm." Read once across L02–L04.
- 📖 **CS229 Lecture Notes §8.1 "Bias-variance tradeoff"** — `…/Bücher/CS229 Lecture Notes.pdf` (p.105) — frames it through the **linear-vs-degree-5-polynomial** example and defines **bias = the test error you'd still have even with infinite training data**; §8.1.1 has the `Bias²+Var+σ²` decomposition. (No k-NN, but the concept is identical.)
- 📝 Reference §8 — incl. §8.1.1 (decoding the slide wording) and **§8.1.2 (flexibility → variance → overfitting; variance = how much predictions move when you retrain on different samples)**

## Step 4 — Cross-validation & choosing k  (~1 h)

How to pick k *from the training data* without touching the test set: validation-set → LOOCV → k-fold.

- 🎥 **CS4780 — ML Debugging / Over-&Underfitting** ([notes](http://www.cs.cornell.edu/courses/cs4780/2018fa/lectures/lecturenote11.html), covers k-fold CV)
- 📖 **ISLP** Ch 5 §5.1 "Cross-Validation" (p.202) + §5.1.2 LOOCV (p.204)
- 📖 **ESL** §7.10 "Cross-Validation" — optional depth
- 🔗 Brandon Rohrer "Splitting the data" (Ch 4)
- 🔗 **Stanford CS231n — "Image Classification: k-NN + Validation sets / Cross-validation"** ⭐ — [notes](https://cs231n.github.io/classification/) — course-quality walk-through of choosing k via a validation set then k-fold CV; mirrors **Übungsblatt 1 Tasks 9–10** almost exactly.
- 📝 Reference §9 (incl. the new §9.2.1 on why it's "training" for a lazy learner) + §10 (hyperparameter tuning)

## Step 5 — Evaluation metrics  (~30 min)

Confusion matrix, precision/recall/F1, micro vs macro — this is **SaD L11 material** (ISLP/Murphy underweight it). For L02 itself you only need **accuracy / test-error** for the k-NN error analysis; reach for precision/recall/F under **class imbalance**.

- 📒 **SaD L11 reference (the home for this)** — `…/SaD/notes/lect11 instance-based/SaD_L11_Reference.md` **§8** — the full evaluation toolkit, the worked SPAM example, micro vs macro (and a flagged slide typo: SPAM F = 0.50, not 0.37).
- 📖 SaD L11 slides — `…/SaD/SaD-2025/11_instance-based.pdf` (the 126-slide *instance-based* lecture; evaluation is slides 93–124). ⚠️ *Not* `Lecture-slides/13_similarity_based.pdf` — that's a different 32-page deck.
- 📝 AML L02 Reference §7.1 (train/test error) + the §7.2 pointer into SaD L11 §8.

## Step 6 — Practice & self-test  (→ exercise bank)

Do these closed-book, then self-grade. Full details + links in **`AML_L02_Exercise_Bank.md`**:

1. **Bonusblatt 1** (k-NN) → check vs `AML_BonusSheet01_Solution.md`
2. **ISLP 2.7** (k-NN by hand) + 2.1 / 2.3 / 2.6 (bias-variance, parametric vs non-parametric)
3. **`AML_L02_Mock_Exam.md`** (75 min, timed)
4. **MIT 6.034 Quiz 3** Problem 1A (question-only)

---

### Suggested schedule (~6 h total)

| Session | Steps | Output |
|---------|-------|--------|
| 1 | Steps 1–2 | k-NN mechanics + distances solid |
| 2 | Steps 3–4 | bias-variance + CV; can choose k |
| 3 | Step 5 + Bonusblatt 1 + ISLP 2.7 | first practice, self-graded |
| 4 | Mock exam (timed) → review misses | gaps closed via cited reference § |

Pull a supplement only where the lecture slide feels thin — don't read everything linearly.
