---
id: note-aml-l02-mock-exam
type: note
title: "AML Lecture 02 — Mock Exam"
created: "2026-07-11"
role: mock-exam
state: evolving
authorship: mixed
concepts: [concept-k-nearest-neighbors, concept-bias-variance-tradeoff, concept-cross-validation]
sources: [source-aml-ss26-lectures]
contexts: [workspace-aml-exam-prep]
---

> **Migration note (2026-07-17, Stage 2):** body preserved verbatim from
> `Plans/ML/foundations/AML/my notes/lect02 KNN-classifier/AML_L02_Mock_Exam.md` (legacy tree).

# AML Lecture 02 — Mock Exam

**Topic:** k-NN, distances, feature engineering & scaling, evaluation metrics, bias–variance, cross-validation, hyperparameter tuning
**Source of truth:** `AML_L02_Ultimate_Reference.md` (section refs given in the answer key)
**Suggested time:** 75 minutes, closed-book
**How to use:** Answer everything on blank paper *before* opening the answer key. Then self-grade and revisit any section you missed.

> Scoring guide: Part A = 20 pts (2 each), Part B = 40 pts, Part C = 15 pts (3 each), Part D = 25 pts. Total 100.

---

## Part A — Conceptual Short Answer (2 pts each)

**A1.** k-NN is called a *lazy learner*. What happens during its "training" phase, and in what sense is the training data itself the model?

**A2.** Explain why the training error of **1-NN is always 0%**, and why this makes train error useless as a quality metric for 1-NN.

**A3.** Distinguish **model parameters** from **hyperparameters**. Give k-NN's examples of each.

**A4.** Using train and test error, define **high bias** and **high variance**. State which k-regime (small or large k) produces each in k-NN.

**A5.** Why must feature-scaling statistics (e.g. min/max or mean/std) be computed on the **training fold only** during cross-validation? Name the failure that occurs if you scale the whole dataset first.

**A6.** Why can **accuracy** be misleading under class imbalance? Name the metric you'd prefer and why.

**A7.** One-hot encoding makes every pair of distinct categories **equidistant**. For an *ordinal* feature (low/medium/high), why is that a problem, and what's the alternative?

**A8.** When is **cosine similarity** preferable to Euclidean distance? Give the data type where this matters most and the reason.

**A9.** State the "vault" principle for the **test set** and the one rule you must never break with it.

**A10.** A colleague says "adding one more feature can only help k-NN, since it just adds a dimension." Refute this in one or two sentences.

---

## Part B — Numerical Problems (show your work)

### B1. k-NN classification (15 pts)

Training set (2-D points with labels):

| Point | Coordinates | Label |
|-------|-------------|-------|
| A | (1, 2) | + |
| B | (2, 3) | + |
| C | (3, 3) | − |
| D | (5, 4) | − |
| E | (2, 0) | + |
| F | (4, 2) | − |

Query point **q = (3, 2)**, using **Euclidean (L₂)** distance.

(a) Compute the L₂ distance from q to all six points.
(b) Give the predicted label for **k = 1, k = 3, k = 5**.
(c) The prediction changes as k grows. Explain what this says about bias/variance as k increases.

### B2. Distance metrics (8 pts)

(a) For x = (2, 3) and z = (5, 7), compute the **L₁ (Manhattan)**, **L₂ (Euclidean)**, and **L∞ (Chebyshev)** distances.
(b) For the all-ones vector **x = (1,1,…,1) ∈ ℝ⁹**, give ‖x‖₁, ‖x‖₂, ‖x‖∞.
(c) True or false: replacing L₂ with **squared** L₂ changes which points are the k nearest neighbors. Justify.

### B3. Confusion matrix & metrics (10 pts)

A binary classifier for the class **"Disease"** produces, on 200 test cases:

TP = 40, FN = 10, FP = 20, TN = 130.

Compute, for the Disease class: (a) accuracy, (b) precision, (c) recall, (d) F₁.
(e) In one sentence, interpret the precision vs recall gap.

### B4. Normalization & cross-validation counting (7 pts)

(a) Feature column **[10, 20, 30, 40, 50]**. Compute the **min–max** normalized values.
(b) For the same column, compute the **z-score** of the value **40** (use the *population* standard deviation, i.e. divide by n).
(c) You run **5-fold CV** over the hyperparameter grid k ∈ {1, 3, 5, 7, 9} on **100** points. How many model fits in total? How many points train vs. validate in each fit?
(d) If you instead used **LOOCV**, how many fits per hyperparameter value?

---

## Part C — True / False + One-Line Justification (3 pts each)

**C1.** Increasing k in k-NN always lowers test error.

**C2.** LOOCV has lower bias but can have higher variance than 10-fold CV.

**C3.** k-NN learns weight parameters during training.

**C4.** Min–max normalization is more robust to outliers than z-score standardization.

**C5.** In multi-class evaluation, macro-averaging gives more influence to rare classes than micro-averaging.

---

## Part D — Synthesis & Short Derivation (25 pts)

**D1. (9 pts) The three error curves.** For k-NN, sketch (or describe) how **training error**, **cross-validation error**, and **test error** behave as k goes from 1 to m. Mark where overfitting and underfitting live, and explain why the training-error curve alone cannot be used to select k.

**D2. (8 pts) One-hot geometry.** Show that two one-hot vectors for *distinct* categories are orthogonal, and compute the L₂ distance between any two distinct one-hot vectors. Explain what this implies for how k-NN treats categorical features.

**D3. (8 pts) Fold count trade-off.** Explain the bias–variance trade-off controlled by the number of folds r. Contrast the extremes r = 2 and r = m (LOOCV), and state the commonly recommended value with the reason.

---
---

# ANSWER KEY

> Section references (§) point to `AML_L02_Ultimate_Reference.md`.

## Part A

**A1.** (§3.1, §9.2.1) "Training" just means *storing* the labeled dataset — there is no parameter fitting. At prediction time the algorithm searches those stored points for the nearest neighbors, so the dataset *is* the model (no compressed representation is learned). k-NN is "lazy" because all work is deferred to query time.

**A2.** (§7.1) Every training point is its own nearest neighbor at distance 0, so 1-NN labels each training point with its own (correct) label → 0% error by construction. Because it's automatic and independent of how good the model is, it tells you nothing about generalization.

**A3.** (§10.1) **Parameters** are learned from data by the algorithm; **hyperparameters** are set before training by the practitioner (tuned via CV). k-NN: parameters = *none* (lazy learner); hyperparameters = **k** (number of neighbors) and **p** (the Lp norm).

**A4.** (§8.1, §8.1.1, §8.3) **High bias / underfitting** = high train AND high test error (model too rigid to capture the signal) → **large k** (e.g. k = m predicts the majority class). **High variance / overfitting** = low train but high test error (model fits the noise) → **small k** (k = 1).

**A5.** (§9.2.1, §6) Computing scaling stats on the whole dataset lets information from the validation/test points leak into "training," inflating the score — **data leakage**. Stats must come from the training fold only.

**A6.** (§7.3) With heavy imbalance, a trivial classifier that always predicts the majority class scores high accuracy while completely missing the rare class (0% recall). Prefer **macro-averaged F₁** (or per-class precision/recall), which gives equal weight to the rare class.

**A7.** (§5.3, §5.4) One-hot makes low–high the same distance as low–medium, discarding the natural order. Alternative: **integer/ordinal encoding** (low=1, medium=2, high=3), which preserves order (at the cost of assuming equal spacing).

**A8.** (§4.3) Prefer cosine when **magnitude shouldn't matter, only direction** — classically **text / bag-of-words**, where document length varies. Two docs with the same word *distribution* but different lengths get cosine similarity 1.

**A9.** (§9.1) Keep the test set "in a vault," brought out **only once at the very end**. Never use it to choose hyperparameters or make any modeling decision — otherwise it stops being an unbiased estimate of generalization.

**A10.** (§4.6) False — a single **irrelevant/noisy feature** can dominate or corrupt the distance computation and wreck k-NN (the ski/snowboard "height" example). Extra dimensions can hurt, not just help.

## Part B

**B1.**
(a) L₂ distances from q = (3, 2):

| Point | Distance | Label |
|-------|----------|-------|
| C (3,3) | √(0+1) = **1.000** | − |
| F (4,2) | √(1+0) = **1.000** | − |
| B (2,3) | √(1+1) = **1.414** | + |
| A (1,2) | √(4+0) = **2.000** | + |
| E (2,0) | √(1+4) = **2.236** | + |
| D (5,4) | √(4+4) = **2.828** | − |

(b) **k = 1:** nearest are C and F (tie at 1.000), both **−** → predict **−**. **k = 3:** {C−, F−, B+} → 2 vs 1 → **−**. **k = 5:** {C−, F−, B+, A+, E+} → 2 vs 3 → **+**.
(c) Small k (=1) hugs the closest couple of points → **high variance** (jagged, noise-sensitive). As k grows, the vote averages over more neighbors, smoothing the boundary → **lower variance, higher bias**. The flip from − to + shows the prediction becoming dominated by the broader + region. (§8.3)

**B2.**
(a) |x − z| = (3, 4): **L₁ = 3 + 4 = 7**, **L₂ = √(9+16) = √25 = 5**, **L∞ = max(3, 4) = 4**. (§4.2)
(b) ‖x‖₁ = **9**, ‖x‖₂ = **√9 = 3**, ‖x‖∞ = **1**. (§4.2)
(c) **False.** Squaring is monotonic for non-negative distances, so it preserves the ordering of neighbors — the same k points are selected. (§4.1)

**B3.** (§7.3)
(a) Accuracy = (40+130)/200 = **0.85**
(b) Precision = 40/(40+20) = 40/60 = **0.667**
(c) Recall = 40/(40+10) = 40/50 = **0.80**
(d) F₁ = 2·(0.667·0.80)/(0.667+0.80) = **8/11 ≈ 0.727**
(e) Precision (0.667) < recall (0.80): the model **catches most real Disease cases but raises a fair number of false alarms** (20 healthy flagged as Disease).

**B4.**
(a) (x − 10)/(50 − 10) = (x − 10)/40 → **[0, 0.25, 0.5, 0.75, 1.0]**. (§6.1)
(b) mean = 30; population σ = √200 ≈ 14.142; z(40) = (40 − 30)/14.142 = **0.707**. (§6.2) *(With sample std, ddof=1: σ ≈ 15.811 → z ≈ 0.632.)*
(c) **5 × 5 = 25 fits**; each fit trains on **80** points, validates on **20**. (§9.5, §10.2)
(d) LOOCV ⇒ **100 fits** per hyperparameter value (one per left-out point). (§9.4)

## Part C

**C1.** **False.** CV/test error is U-shaped in k — too-large k underfits (rising error). (§8.4)

**C2.** **True.** LOOCV trains on n−1 points (low bias) but its n training sets are nearly identical → correlated, high-variance estimate. (§9.6)

**C3.** **False.** k-NN has no learned parameters; k and p are hyperparameters. (§10.1)

**C4.** **False.** It's the reverse — min–max is *more* sensitive to outliers (one extreme value compresses the rest); z-score is more robust. (§6.1–6.3)

**C5.** **True.** Macro-averaging computes the metric per class then averages, weighting each class equally and so amplifying rare classes; micro pools all counts, favoring frequent classes. (§7.4)

## Part D

**D1.** (§8.4) **Training error** (blue): monotonically **increases** with k — 0% at k = 1, more constrained as k grows. **CV error** (black): **U-shaped** — falls as k rises from 1 (variance down), reaches a minimum at the sweet spot, then rises (bias up). **Test error** (brown): similar U-shape, minimum not necessarily at the same k. **Overfitting** lives at small k (left), **underfitting** at large k (right). Training error can't select k because it just keeps dropping toward k = 1 (0%), which is the *worst*, most overfit model — it has no minimum to point at the sweet spot. You need held-out (CV) error for that.

**D2.** (§5.3) A one-hot vector has a single 1 and the rest 0, with the 1 in a different position for each category. For distinct categories the dot product is 0 (no overlapping nonzero entry) → **orthogonal**. The L₂ distance between two distinct one-hot vectors is √(1² + 1²) = **√2** (one coordinate goes 1→0, another 0→1). Implication: k-NN treats **all distinct categories as equally far apart** — fine for nominal data, but it erases any ordering, which is why ordinal features may need integer encoding instead.

**D3.** (§9.6) Few folds (r = 2): each training set is small → models underfit → estimate has **high bias** (overestimates error). Many folds (r = m = LOOCV): each training set has nearly all data → **low bias**, but the m training sets differ by one point → highly correlated error estimates → **high variance**. Recommended **r = 5 or 10**: enough data per fold to fit well (moderate bias) and enough fold independence for a stable estimate (moderate variance) — empirically validated in ISLP.

---

*Self-grade, then for any miss, reread the cited section in `AML_L02_Ultimate_Reference.md`. Once this feels easy, move on to bonus sheets `zusatz-blatt02–04` and the real `Übung 02`.*
