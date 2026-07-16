---
id: note-aml-l02-exercise-bank
type: note
title: "AML Lecture 02 — Exercise Bank (k-Nearest Neighbors)"
created: "2026-07-11"
role: exercise-bank
state: evolving
authorship: mixed
concepts: [concept-k-nearest-neighbors, concept-bias-variance-tradeoff, concept-cross-validation]
sources: [source-aml-ss26-lectures, source-mit-6034-quizzes]
contexts: [workspace-aml-exam-prep]
---

> **Migration note (2026-07-17, Stage 2):** body preserved verbatim from
> `Plans/ML/foundations/AML/my notes/lect02 KNN-classifier/AML_L02_Exercise_Bank.md` (legacy tree).

# AML Lecture 02 — Exercise Bank (k-Nearest Neighbors)

All practice material for L02, in one place. Covers k-NN (classification + regression), distance metrics, feature scaling, evaluation metrics, bias–variance, and cross-validation. External links **verified live 21 Jun 2026**.

How to use: work the **local** sheets first (they match the HU exam style and notation exactly), then use the **external** sets for extra volume and self-checking. Everything here has solutions to grade yourself against.

---

## 1. Local material (already in this folder / your repo)

| File | What it is | Status |
|------|-----------|--------|
| `AML_L02_Ultimate_Reference.md` | Full topic reference — read/recall source | — |
| `AML_L02_Mock_Exam.md` | 100-pt mock exam, all sections, verified answer key | self-grade |
| `AML_BonusSheet01_Solution.md` | Worked + verified solution to Bonusblatt 1 (Vektorisierung + k-NN regression) | done |

**Source sheets to actually solve (in the repo, not yet self-graded):**

- **Bonusblatt 1** — `Plans/ML/foundations/AML/SoSe 2026/Bonus-exercises/zusatz-blatt01.pdf` — the official k-NN/vectorization Klausur-prep sheet (solution key above).
- **k-NN tutorial slides** — `Plans/ML/foundations/AML/SoSe 2026/Exercise slides/Übung 02 .pdf` — walks through the graded notebook below + a NumPy primer.

### Übungsblatt 1 — the graded notebook, task-by-task (from `Übung 02 .pdf`)

**Setup.** *k-NN search with vector embeddings.* **Dataset:** Stanford Dogs (120 classes, 20,580 images) → each image turned into a **512-dim CLIP embedding** (you're handed the image embeddings; you build the classifier on top). Run on the CMS **JupyterHub** (Data-Science-Environment); the full notebook executes in ~1–2 min — much longer means a bug. **1 point per task; you need ≥ 50 % of the points across all sheets to pass.**

| # | Task | What it drills |
|---|------|----------------|
| 1 | Count the **images per class** | dataset exploration (`np.unique`, counts) |
| 2 | Implement **Euclidean (L2) distance** | the distance metric — §3/§4 of the reference |
| 3 | Implement **1-NN search** | argmin over distances |
| 4 | Implement **1-NN classification** | take the label of the nearest point |
| 5 | **Suggest improvements** to lower the error | error analysis (scaling, k, better metric) |
| 6 | Report the **test error** | evaluation |
| 7 | Report the **train error** | evaluation |
| 8 | **Explain** the train error | ⭐ conceptual — see note below |
| 9 | Optimize **k via cross-validation** | model selection — §9 of the reference |
| 10 | Optimize hyper-parameters via **grid-search** | `GridSearchCV` |

> **Task 8 is the exam-classic:** the **1-NN train error is exactly 0** — every training point is its own nearest neighbour (distance 0), so it's always classified as itself. This says nothing about generalization (test error is what matters) and is the textbook "why 1-NN overfits" point. Tie it to §8 (bias–variance: 1-NN = max variance).

> **NumPy primer (second half of the deck):** vectors/matrices, indexing, the dot product, **broadcasting**, and the **vectorization benchmark** — computing `Σ wⱼxⱼ` as a Python for-loop took **0.1235 s** vs the vectorized dot product **0.00052 s** (~**240× faster**). Same lesson as Bonusblatt 1 Aufgabe 1.

---

## 2. External practice — solution-checked, matched to L02

### ⭐ ISLP — the closest fit (conceptual + by-hand + applied)

- **Chapter 2 exercises** with full Python solutions → **[botlnec.github.io/islp — Chapter 2](https://botlnec.github.io/islp/sols/chapter2/exercise1/)** (2.1–2.10).
  - **Exercise 2.7 is the key one** — a k-NN-by-hand problem: a small table of points, compute Euclidean distances to a query, predict with K=1 and K=3. This is *exactly* the HU exam archetype. Do it closed-book, then check.
  - 2.1–2.4 drill the **flexibility / bias–variance** conceptual reasoning (when is a flexible method better?).
- **Chapter 5 exercises** (cross-validation) → **[Chapter 5](https://botlnec.github.io/islp/sols/chapter5/exercise1/)** — LOOCV vs k-fold, the validation-set approach. Matches §9 of your reference.
- Applied-code alternatives if you want to run them: [a-martyn/ISL-python](https://github.com/a-martyn/ISL-python), [KarimABOUSSELHAM/ISLP-applied-solutions](https://github.com/KarimABOUSSELHAM/ISLP-applied-solutions).

*Note: solutions are for the R-edition ISLR numbering; the book itself is in your `Bücher/` folder. Cross-check derivations against the text — community quality varies.*

### MIT 6.034 Artificial Intelligence — exam-format k-NN problems

I opened the PDFs and pinned down which quizzes carry the k-NN problem (it's always **Quiz 3** in the years that taught it):

- **Quiz 3, Fall 2010** — [PDF](https://ocw.mit.edu/courses/6-034-artificial-intelligence-fall-2010/4a2ea7a8b0ab11a40e0f1a0093a78865_MIT6_034F10_quiz3_2010.pdf) — do **only Problem 1, Part A "Nearest Neighbors" (25 pts)**: draw the k=1 Euclidean decision boundaries, classify two query points X and Y, **name the problem with k=1** (→ overfitting), redo with k=3, and **explain why k=21 is bad** (→ over-smoothing/underfitting). *Skip Part B (ID-trees) and Problem 2 (neural nets) — not L02.* This part maps perfectly onto §3 + §8 of your reference.
- **Quiz 3, Fall 2007** — [PDF](https://ocw.mit.edu/courses/6-034-artificial-intelligence-fall-2010/5c0e73c065cc8ae4c2a1899e4d4417f7_MIT6_034F10_quiz3_2007.pdf) — tagged "nearest neighbors"; a second k-NN drill.

⚠️ **No written answer key on OCW** — these quiz PDFs are blank exams (question-only; I verified). The methods are walked through in the course's **Mega-Recitation videos** and **Tutorials**, and the k-NN parts are simple enough to self-check against §3 (k-NN) and §8 (bias–variance) of your reference. Ask me and I'll produce a verified worked key for either.

*(Other years' Quiz 3/4 cover different topics — 2009 Q3 "zombie infection" leans ID-trees, 2008 Q3 neural nets, the Q4s are SVM/Bayes — so they're not L02.)*

### Cornell CS4780 — notes + self-checks (supplementary)

- **[Course materials page](https://www.cs.cornell.edu/courses/cs4780/2018fa/page18/index.html)** (Weinberger). Directly relevant lecture notes:
  - [k-NN](http://www.cs.cornell.edu/courses/cs4780/2018fa/lectures/lecturenote02_kNN.html) (+ Curse of Dimensionality)
  - [ML Debugging / Over- & Underfitting — k-fold CV](http://www.cs.cornell.edu/courses/cs4780/2018fa/lectures/lecturenote11.html)
  - [Bias / Variance Tradeoff](http://www.cs.cornell.edu/courses/cs4780/2018fa/lectures/lecturenote12.html)
- Use as a second explanation + the embedded reasoning checks.
- ✓ **Local solved homeworks** — `Plans/ML/foundations/AML/CS4780-homeworks/`. For L02: **2018Fall HW1** (train/test split, k-NN decision boundary + regression, curse of dimensionality) and **2018Fall HW6 Problem 2** (bias–variance decomposition of k-NN regression) — both with full solution PDFs. See the folder `README.md` for the topic map.

### Famous essays + CS231n (conceptual self-check)

- ⭐ **Stanford CS231n — [Image Classification (k-NN + cross-validation)](https://cs231n.github.io/classification/)** — read the notes, then do the linked **k-NN assignment** (validation-set + 5-fold CV for choosing k) — basically Übungsblatt 1 Tasks 9–10 done from scratch.
- ⭐ **Scott Fortmann-Roe — [Understanding the Bias-Variance Tradeoff](https://scott.fortmann-roe.com/docs/BiasVariance.html)** — after the mock exam, use it to sanity-check your bias-variance answers (it's worked through k-NN).
- ⭐ **Pedro Domingos — [A Few Useful Things to Know About Machine Learning](https://homes.cs.washington.edu/~pedrod/papers/cacm12.pdf)** (CACM 2012) — the famous overview essay; one read covers L02–L04 (overfitting, bias-variance, curse of dimensionality).

---

## 3. Suggested sequence

1. **Bonusblatt 1** (closed-book) → check against `AML_BonusSheet01_Solution.md`.
2. **ISLP 2.7** (k-NN by hand) + **2.1–2.4** (bias–variance reasoning) → check on botlnec.
3. **`AML_L02_Mock_Exam.md`** (timed, 75 min) → self-grade with its key.
4. **MIT 6.034** — one quiz's nearest-neighbor problem as a fresh timed drill.
5. Thin spots only: **ISLP Ch 5** (CV) + the Cornell bias–variance note.

Anything you miss → reread the cited § in `AML_L02_Ultimate_Reference.md`.

---

## 4. ISLP Chapter 2 — question prompts + solution links

The prompts below are transcribed from your ISLP book (§2.4 Exercises) so you have question + answer in one place. ⭐ = most L02-relevant. Solve from here, then click the link to check.

### Conceptual

**ISLP 2.1 ⭐ — flexible vs. inflexible** · [solution](https://botlnec.github.io/islp/sols/chapter2/exercise1/)
For each part, say whether a flexible statistical-learning method generally performs **better or worse** than an inflexible one, and justify:
(a) n extremely large, p small. (b) p extremely large, n small. (c) relationship highly non-linear. (d) variance of the error terms σ² = Var(ε) extremely high.

**ISLP 2.2 — classification vs. regression; inference vs. prediction** · [solution](https://botlnec.github.io/islp/sols/chapter2/exercise2/)
For each scenario, state whether it's classification or regression, whether we care about inference or prediction, and give n and p:
(a) Top-500 US firms; record profit, #employees, industry, CEO salary; interested in what affects CEO salary. (b) Launch new product, success/failure; data on 20 similar products with price, marketing budget, competitor price, +10 vars. (c) Predict weekly % change in USD/Euro from weekly % changes in US/British/German markets, 2012 weekly data.

**ISLP 2.3 ⭐ — bias–variance decomposition** · [solution](https://botlnec.github.io/islp/sols/chapter2/exercise3/)
(a) On one plot, sketch the typical **(squared) bias, variance, training error, test error, and Bayes/irreducible error** curves as flexibility increases (x = flexibility, y = value); five labeled curves. (b) Explain why each curve has the shape you drew. *(This is §8.4 of your reference, generalized.)*

**ISLP 2.4 — real-life applications** · [solution](https://botlnec.github.io/islp/sols/chapter2/exercise4/)
Describe three real-life applications each for (a) classification, (b) regression, (c) cluster analysis; for (a)/(b) name the response + predictors and say whether the goal is inference or prediction.

**ISLP 2.5 — pros/cons of a very flexible approach** · [solution](https://botlnec.github.io/islp/sols/chapter2/exercise5/)
Advantages and disadvantages of a very flexible vs. a less flexible approach for regression/classification. When is more flexible preferred? When is less flexible preferred?

**ISLP 2.6 ⭐ — parametric vs. non-parametric** · [solution](https://botlnec.github.io/islp/sols/chapter2/exercise6/)
Describe the difference between a parametric and a non-parametric approach. What are the advantages/disadvantages of the parametric approach? *(k-NN is the non-parametric example — tie this to §3.1.)*

**ISLP 2.7 ⭐⭐ — k-NN by hand** · [solution](https://botlnec.github.io/islp/sols/chapter2/exercise7/)
Training set (six observations, three predictors, qualitative response):

| Obs. | X₁ | X₂ | X₃ | Y |
|------|----|----|----|------|
| 1 | 0 | 3 | 0 | Red |
| 2 | 2 | 0 | 0 | Red |
| 3 | 0 | 1 | 3 | Red |
| 4 | 0 | 1 | 2 | Green |
| 5 | −1 | 0 | 1 | Green |
| 6 | 1 | 1 | 1 | Red |

Predict Y at the test point X₁ = X₂ = X₃ = 0 using k-NN:
(a) Compute the Euclidean distance from each observation to the test point. (b) Prediction with K = 1? Why? (c) Prediction with K = 3? Why? (d) If the Bayes decision boundary is highly non-linear, would the best K be large or small? Why?

> This is the single best by-hand drill for L02 — same archetype as the HU exam. (Quick check: nearest is Obs 5 at √2; K=1 → Green; K=3 nearest are Obs 5 (√2, Green), 6 (√3, Red), 2 (2, Red) → 2 Red vs 1 Green → **Red**; (d) small K.)

### Applied (dataset/coding — lower exam priority)

- **2.8** College.csv · [solution](https://botlnec.github.io/islp/sols/chapter2/exercise8/) — data loading, summaries, scatter/box plots, binning an "Elite" variable.
- **2.9** Auto · [solution](https://botlnec.github.io/islp/sols/chapter2/exercise9/) — quantitative vs. qualitative predictors, ranges, mean/std, graphical exploration.
- **2.10** Boston · [solution](https://botlnec.github.io/islp/sols/chapter2/exercise10/) — load, explore, crime-rate associations, summary stats.

*(Numbering matches your ISLP book for Chapter 2. botlnec follows the same numbers here; double-check applied-exercise datasets against your PDF, as they shift between editions.)*

---

*Reminder: no HU AML Altklausuren are public (Moodle/Fachschaft only — see `LEARNING-RESOURCES.md` §6 for the channels). The above is matched external material, not HU past papers.*
