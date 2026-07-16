---
id: note-aml-l02-knn-bias-variance
type: note
title: "AML Lecture 02 — Ultimate Reference: k-NN, Bias-Variance, and Model Evaluation"
created: "2026-07-11"
role: reference
state: evolving
authorship: mixed
concepts: [concept-k-nearest-neighbors, concept-bias-variance-tradeoff, concept-cross-validation, concept-classification-metrics, concept-curse-of-dimensionality]
sources: [source-aml-ss26-lectures, source-islp, source-esl]
contexts: [workspace-aml-exam-prep]
---

> **Migration note (2026-07-17, Stage 2):** body preserved verbatim from
> `Plans/ML/foundations/AML/my notes/lect02 KNN-classifier/AML_L02_Ultimate_Reference.md` (legacy tree).

# AML Lecture 02 — Ultimate Reference: k-NN, Bias-Variance, and Model Evaluation

*Synthesized from: AML L02 (Schäfer, HU SoSe 2025) + ISLP §2.2.2 / Ch 5.1 (James et al.). The **SaD L11** (Akbik, 2025) material this draws on — vectorization, the ML-families taxonomy, similarity measures, the full evaluation toolkit — now lives in its own sheet: `…/SaD/notes/lect11 instance-based/SaD_L11_Reference.md` (scope split in §11).*
*Created: KW 22 (May 2026) — deep reference for Block D of the Foundations plan*

---
    
## Table of Contents

1. [From Statistics to Machine Learning](#1-from-statistics-to-machine-learning)
2. [The Supervised Learning Setup](#2-the-supervised-learning-setup)
3. [The Nearest Neighbor Classifier](#3-the-nearest-neighbor-classifier)
4. [Distance Functions](#4-distance-functions)
5. [Feature Engineering and Vectorization](#5-feature-engineering-and-vectorization)
6. [Feature Scaling](#6-feature-scaling)
7. [Evaluation Metrics](#7-evaluation-metrics)
8. [Bias, Variance, and Generalization](#8-bias-variance-and-generalization)
9. [Cross-Validation](#9-cross-validation)
10. [Hyperparameter Tuning](#10-hyperparameter-tuning)
11. [Summary and Cross-Wire Moments](#11-summary-and-cross-wire-moments)

---

## 1. From Statistics to Machine Learning

**[Source: SaD L11, slides 6–18]**

Statistics and machine learning share the same mathematical foundations but differ in focus:

- **Statistics** focuses on aggregate properties of populations: What is the probability of rain in Berlin in June? What fraction of employees earn above 80k?
- **Machine learning** focuses on predictions for individual data points: Given today's weather data, will it rain tomorrow? How much will *I* earn?

Both start from the same place — a **population** (Grundgesamtheit) that cannot be fully observed, and a **sample** (Stichprobe) drawn randomly from it. The statistical goal is to estimate population parameters (mean, variance, distribution shape). The ML goal is to learn a function that predicts well on new, unseen individuals.

**Arthur Samuel (1959):** "Machine learning is the field of study that gives computers the ability to learn without being explicitly programmed."

**Tom Mitchell (1998):** "A computer program is said to learn from experience E with respect to some task T and some performance measure P, if its performance on T, as measured by P, improves with experience E."

### Three Types of Machine Learning

| Type | Goal | Example |
|------|------|---------|
| **Classification** | Predict a discrete label | Spam detection, digit recognition, dog breed identification |
| **Regression** | Predict a continuous value | Tomorrow's temperature, house price, steering angle |
| **Clustering** | Discover structure (unsupervised) | Customer segments, topic discovery |

### Where k-NN sits among ML approaches

SaD L11 groups ML into **four families** — similarity-based (k-NN), information-based (trees), probability-based (Naive Bayes), and error-based (linear/logistic regression, neural nets). The full taxonomy is **SaD L11 §2** (`…/SaD/notes/lect11 instance-based/SaD_L11_Reference.md`).

The takeaway for L02: **k-NN is the *similarity-based* family** — the simplest possible classifier, where *no model is learned and no parameters are fit; the training data **is** the model* (a **lazy learner**). Most of the rest of AML lives in the **error-based** family (regression, logistic regression, neural nets — all "minimize a loss").

---

## 2. The Supervised Learning Setup

**[Source: AML L02, slides 4–14; SaD L11, slides 22–24]**

### Notation

Both AML and SaD use the same formal setup, with minor notational differences:

| Symbol | Meaning |
|--------|---------|
| X | The data matrix, m × n |
| m | Number of samples (observations) |
| n | Number of features (dimensions) |
| x⁽ⁱ⁾ | The i-th sample (a vector in ℝⁿ) |
| xⱼ⁽ⁱ⁾ | The j-th feature of sample i |
| Y | The labels (a vector of length m) |
| y⁽ⁱ⁾ | The label of sample i |
| h: X → Y | The learned hypothesis (model) |

**Data as vectors and matrices.** Every data point is represented as a feature vector x = (x₁, x₂, ..., xₙ) ∈ ℝⁿ. A dataset of m samples forms an m × n matrix X. In MNIST, each image is 28 × 28 = 784 pixels, so x ∈ ℝ⁷⁸⁴ and Y = {0, 1, ..., 9}.

**Supervised learning** requires labeled data D = {(x⁽ⁱ⁾, y⁽ⁱ⁾) | i ∈ [1...m]}. The goal is to learn a function f(x) → ŷ that accurately recovers the input-output pattern and **generalizes** to unseen data.

---

## 3. The Nearest Neighbor Classifier

**[Source: AML L02, slides 15–32; SaD L11, slides 29–35, 87–91]**

### 3.1 Core Intuition

The fundamental assumption: **nearby data points should have the same label.** If you want to classify a new data point, find the most similar point in your training data and copy its label.

This is also called:
- Similarity-based learning (Ähnlichkeitsbasiertes Lernen)
- Instance-based learning
- Memory-based learning
- Lazy learning (because no training phase exists — the algorithm just stores the data)

**Cognitive science parallel (SaD L11):** Case-based reasoning in medicine (doctors use past cases), law (precedent-based argumentation), and creative design (reusing similar prior solutions).

### 3.2 The 1-NN Algorithm

Given a training dataset D_train = {(x⁽ⁱ⁾, y⁽ⁱ⁾) | i ∈ [1...m]} and a new query point x:

```
i_nn = argmin_i dist(x⁽ⁱ⁾, x)
return y⁽ⁱ_nn⁾
```

That's it. Find the training point closest to x, return its label.

**Properties of 1-NN:**
- **No training phase** (lazy learner): just store D_train
- **Classification time**: O(nm) for a single query — must compute distance to all m training points, each requiring O(n) operations
- **Memory**: O(nm) — must store entire training dataset
- **Train error**: Always 0% (every point is its own nearest neighbor)
- **Test error on MNIST**: 3.09% (309 out of 10,000 misclassified)

### 3.3 The k-NN Algorithm

**[Source: SaD L11, slide 33; AML L02, slides 37–39]**

1-NN is sensitive to label noise — a single mislabeled point corrupts predictions. The fix: consult k neighbors and take a majority vote.

**Algorithm (SaD L11 pseudocode):**

```
Input:  Training data (x₁,y₁),...,(xₘ,yₘ)
        New query point x_new
        Number of neighbors k
        Distance function d(x, x')

1. For each training example (xᵢ, yᵢ):
      Compute distance d(x_new, xᵢ)
2. Sort training examples by ascending distance
3. Select the k nearest neighbors
4. Determine the most frequent class among these k neighbors
      → Majority vote
5. Return this class as prediction for x_new
```

**Complexity:**
- Naive approach: O(km + nm) — compute all distances O(nm), then find k smallest O(km)
- Heap-based: O(m + k log m + nm) — use a max-heap of size k

**MNIST results (AML L02):**

| k | 1 | 3 | 5 | 7 | 9 | 11 |
|---|---|---|---|---|---|---|
| Test error (%) | 3.09 | 2.94 | 3.13 | 3.10 | 3.43 | 3.34 |

The best k here is 3 — but how do we find the best k in general? This is a **hyperparameter selection** problem (see Section 9).

### 3.4 Aggregation Functions for k-NN

**[Source: SaD L11, slide 91]**

Given k neighbor labels sorted by distance:

- **Nominal classes:** Majority voting (use odd k to avoid ties: k = 3, 5, 7, ...)
- **Ordinal classes:** Median of labels
- **Regression:** Average of the k neighbors' values (k-NN regression)

**Distance-weighted voting:** Closer neighbors should have more influence:

$$\text{class}(z) = \arg\min_{c \in C} \sum_{i=1}^{k} \mathbb{I}(y_i = c) \cdot \frac{1}{\text{dist}(z, x_i)}$$

This reduces the influence of distant neighbors that happened to be among the k closest.

### 3.5 k-NN for Regression

**[Source: AML L02, slide 71]**

The classification algorithm uses majority vote (the mode). For regression, change mode to **average**: return the mean of the k nearest neighbors' response values.

$$\hat{f}(x) = \frac{1}{k} \sum_{i \in N_k(x)} y_i$$

where N_k(x) is the set of k nearest training points to x.

---

## 4. Distance Functions

**[Source: AML L02, slides 18–20, 59–82; SaD L11, slides 59–85]**

The choice of distance function profoundly affects k-NN performance. This section covers all distance measures from both lectures.

### 4.1 Euclidean Distance (L₂)

The most common choice. For two n-dimensional vectors x, z ∈ ℝⁿ:

$$\text{dist}(x, z) = \|x - z\|_2 = \sqrt{\sum_{i=1}^{n} (x_i - z_i)^2}$$

Derived from the Pythagorean theorem. In 2D: dist((1,2), (3,5)) = √(2² + 3²) = √13.

**Squared Euclidean distance** (used in practice for performance — avoids the square root):

$$\text{dist}^2(x, z) = \|x - z\|_2^2 = \sum_{i=1}^{n} (x_i - z_i)^2$$

Since the square root is monotonic, the ranking of nearest neighbors is identical whether you use dist or dist².

### 4.2 The General Lp Distance (Minkowski Distance)

**[Source: AML L02, slides 75–82; SaD L11, slides 61–62]**

The Lp distance generalizes Euclidean distance:

$$\|x - z\|_p = \left(\sum_{i=1}^{n} |x_i - z_i|^p\right)^{1/p}$$

| p | Name | Formula | Geometric shape of "unit ball" in 2D |
|---|------|---------|------|
| 1 | **Manhattan** (L₁) | Σ\|xᵢ − zᵢ\| | Diamond |
| 2 | **Euclidean** (L₂) | √(Σ(xᵢ − zᵢ)²) | Circle |
| ∞ | **Chebyshev** (L∞) | max_i \|xᵢ − zᵢ\| | Square |

**Manhattan distance (L₁):** The "city block" distance — the length you'd walk on a grid. Named after the grid layout of Manhattan streets.

**Chebyshev distance (L∞):** Only the single largest coordinate difference matters.

**Example (AML L02):** For the all-ones vector x = (1, 1, ..., 1) in ℝⁿ:
- ‖x‖₁ = n (sum of all absolute values)
- ‖x‖₂ = √n (square root of sum of squares)
- ‖x‖∞ = 1 (maximum single entry)

**Why different p values matter for k-NN:** The shape of the "neighborhood" changes. L₁ creates diamond-shaped neighborhoods, L₂ creates circles, L∞ creates squares. Different data distributions favor different shapes. In the AML exercise, you optimize over p ∈ {1, 2, 3} via grid search.

### 4.3 Cosine Similarity

**[Source: SaD L11, slides 80–84]**

Measures the angle between two vectors, ignoring their magnitude:

$$\text{cos\_sim}(x, z) = \frac{x \cdot z}{\|x\| \cdot \|z\|} = \frac{\sum_{i=1}^{n} x_i z_i}{\sqrt{\sum x_i^2} \cdot \sqrt{\sum z_i^2}}$$

- Range: [-1, 1] (or [0, 1] for non-negative features like bag-of-words)
- +1: Identical direction (most similar)
- 0: Orthogonal (no similarity)
- -1: Opposite direction

**Cosine distance** = 1 − cos_sim(x, z), converting similarity to a distance measure.

**When to use:** Particularly useful for text data (bag-of-words vectors) where document length varies — cosine similarity normalizes for this automatically. Two documents with the same word distribution but different lengths will have cosine similarity = 1.

### 4.4 Mahalanobis Distance

**[Source: SaD L11, slides 77–78]**

All previous distance measures ignore the distribution of the data. The Mahalanobis distance accounts for **correlations between features** by scaling with the covariance matrix:

$$d_M(x, \mu) = \sqrt{(x - \mu)^T \Sigma^{-1} (x - \mu)}$$

where Σ is the covariance matrix and μ is the mean vector.

**Key insight:** If two features are highly correlated, the Mahalanobis distance down-weights differences along that correlated direction. This makes it more robust than Euclidean distance when features are not independent.

**Practical limitation:** Requires estimating the covariance matrix Σ, which needs sufficient data and is expensive for high-dimensional data.

### 4.5 Distance Function Properties

**[Source: SaD L11, slide 60]**

A function dist: I × I → ℝ is a **distance measure** if for all i, j ∈ I:
1. **Symmetry:** dist(i, j) = dist(j, i)
2. **Non-negativity + Identity:** dist(i, j) ≥ 0, and dist(i, j) = 0 ⟺ i = j

The pairwise distances for all points can be arranged in a symmetric N × N **distance matrix**.

### 4.6 Sensitivity to Features

**[Source: AML L02, slides 59–66]**

**Problem 1: Pixel shifts.** The Euclidean distance between two identical MNIST digits can be very high if one is shifted by a few pixels. Row i of image x becomes row i of image z with an offset — the pixel-level comparison sees maximum mismatch.

**Problem 2: Noisy features.** Adding a single irrelevant feature can destroy k-NN performance. AML L02 gives the ski/snowboard example: adding a random "height" feature to width-based classification wrecks the distance computation.

**Solutions:**
- **Feature selection:** Remove irrelevant features
- **Normalization:** Scale features to comparable ranges (Section 6)
- **Better distance functions:** Use tangent distance (invariant to small translations/rotations) or shape context
- **Learned embeddings:** Use representations like CLIP embeddings (as in the AML exercise) that are semantically meaningful

**MNIST test error rates with different distances (AML L02):**

| Distance | L₂ (Euclidean) | L₃ | Tangent distance | Shape context |
|----------|---|---|---|---|
| Test error (%) | 3.09 | 2.83 | 1.1 | 0.63 |

---

## 5. Feature Engineering and Vectorization

> **Scope note (moved to SaD L11).** The full treatment of vectorization — scale types (*Skalenniveaus*), one-hot / multi-hot, ordinal encoding, **Bag-of-Words** text vectors, and image-as-pixel-vector — is **SaD L11 material**. It now lives in **`…/SaD/notes/lect11 instance-based/SaD_L11_Reference.md` §4**. It answers "*what is the vector we compute distances on?*", but AML L02 doesn't teach it.

**What AML L02 actually relies on:** the k-NN exercise skips hand-built vectorization and works on **pre-computed CLIP embeddings** (512-dim dense vectors for the dog images) — the modern learned-embedding alternative to Bag-of-Words. So for L02 you only need: *every data point is already a numeric feature vector* (here, a CLIP embedding). For how those vectors are built from raw nominal/ordinal/text/image data, see **SaD L11 §4**.

---

## 6. Feature Scaling

**[Source: SaD L11, slides 66–76]**

Distance measures are sensitive to the scale of features. A feature measured in kilometers will dominate one measured in meters. Feature scaling ensures all features contribute proportionally.

### 6.1 Min-Max Normalization (Rescaling)

Transforms each feature to the range [0, 1]:

$$x_{\text{scaled}} = \frac{x - x_{\min}}{x_{\max} - x_{\min}}$$

- After scaling: minimum value maps to 0, maximum to 1
- Preserves the shape of the original distribution
- Sensitive to outliers (a single extreme value compresses the rest)

### 6.2 Z-Score Normalization (Standardization)

Centers each feature to mean 0 and standard deviation 1:

$$x_{\text{scaled}} = \frac{x - \mu}{\sigma}$$

where μ is the feature mean and σ is the feature standard deviation.

- After scaling: the feature has mean ≈ 0 and std ≈ 1
- More robust to outliers than min-max
- The resulting values are unbounded (not restricted to [0, 1])

**Connection to SaD 02:** You learned sample mean x̄ and sample standard deviation s in Block A. Z-score normalization is literally applying those formulas per feature column.

### 6.3 When to Use Which

| Method | Use when | Limitation |
|--------|----------|------------|
| **Min-Max** | You need values in [0, 1], or the distribution is roughly uniform | Sensitive to outliers |
| **Z-Score** | Features have different scales, approximately normal distribution | Assumes meaningful mean/std |
| **No scaling** | Features are already on the same scale or you use cosine similarity | Rare in practice |

**Critical for k-NN:** Without scaling, a feature with range [0, 100000] will completely dominate a feature with range [0, 1] in any Lp distance computation.

---

## 7. Evaluation Metrics

**[Source: SaD L11, slides 93–122; AML L02, slides 25–31]**

### 7.1 Train vs Test Error

**[Source: AML L02, slides 25–30]**

- **Error** = fraction of samples incorrectly classified
- **Accuracy** = fraction of samples correctly classified = 1 − error

**Train error of 1-NN:** Always 0%. Every sample is its own nearest neighbor, so every training point is classified correctly. This makes train error useless as a performance metric for 1-NN.

**Train error of k-NN (k > 1):** Can be > 0%. With k = 3, the query point is one of its own 3 neighbors, but the other 2 might be from a different class and outvote it. This explains why the train error is non-zero in the AML Exercise 1 (Task 8).

**Test error:** Uses a separate, held-out dataset that the classifier has never seen. This estimates how well the model generalizes to new data.

**Key principle (AML L02):** "Error on training data is an overly optimistic predictor of future performance."

### 7.2 Beyond accuracy → the SaD L11 evaluation toolkit

> **Scope note (moved to SaD L11).** The confusion matrix (*Wahrheitsmatrix*), **precision / recall / F-score**, **micro vs macro** averaging, and the worked SPAM example are **SaD L11 material** — now in **`…/SaD/notes/lect11 instance-based/SaD_L11_Reference.md` §8**. (That sheet also flags a lecture typo: the SPAM F-score is **0.50**, not the deck's printed 0.37 — the harmonic mean of P = 1.0, R = 0.33.)

**What AML L02 needs from it:** for the k-NN error analysis (Exercise 1, Tasks 5–8) you report **test error / accuracy** and reason about *which* cases the classifier gets wrong. Accuracy is the right single number when each point has one label and classes are balanced; under **class imbalance** (e.g. 99% non-spam) accuracy misleads, and you reach for **precision / recall / F** — all defined and worked out in **SaD L11 §8**.

---

## 8. Bias, Variance, and Generalization

**[Source: AML L02, slides 37–58; SaD L11, slides 86–91]**

### 8.1 The Core Tradeoff

This is arguably the most important concept in machine learning.

**Underfitting (High Bias):**
- The model is too simple to capture the true pattern
- High error on both training AND test data
- In k-NN: k is too large (e.g., k = m), so the prediction is just the overall majority class

**Overfitting (High Variance):**
- The model memorizes the training data, including noise
- Low training error but high test error
- In k-NN: k = 1 is susceptible — a single noisy point corrupts predictions
- SaD L11: "Ausreißer werden als wichtige Muster erkannt" (outliers are mistaken for important patterns)

**Generalization (Sweet Spot):**
- The model captures true patterns without memorizing noise
- Training error close to test error
- The gap between them is the **generalization gap**

### 8.1.1 Decoding "Fails to Learn Intrinsic Patterns" (Both Failure Modes)

The slides describe both failures with the same closing phrase, which is confusing because they are opposites:

> - **High Variance:** Low train but high test error. The model perfectly adapts to train data but fails to learn intrinsic patterns.
> - **High Bias:** High train AND high test error. The model fails to adapt to train data and fails to learn intrinsic patterns.

The key is what **"intrinsic pattern"** means: the *true underlying signal* that generalizes to new data — as opposed to the random **noise** in your particular training sample. Both modes fail to generalize, but for opposite reasons:

- **High variance (overfitting):** the model is so flexible it bends to fit every training point *including the noise*. It nails the training data (low train error), but it mistook sample-specific quirks for real structure. Those quirks don't recur in the test set → high test error. It fails to learn the intrinsic pattern by learning **too much** — memorizing noise instead of signal.
- **High bias (underfitting):** the model is too simple/rigid to capture the signal at all. It can't even fit the data it was given (high train error), so it's hopeless on new data too (high test error). It fails to learn the intrinsic pattern by being **incapable** of representing it.

**The tell is the train error.** Overfitting fits the training data *too* well (low train error); underfitting fits it *poorly* (high train error). Test error is high either way — so train error is what distinguishes the two.

**Exam analogy** (studying from practice questions):

- *Overfitting (high variance):* you memorize the exact practice questions and answers word-for-word, even the typos. You ace the practice test but bomb the real exam — you learned specific answers, not concepts.
- *Underfitting (high bias):* you barely study and use one crude rule ("the answer's always C"). You do badly on both the practice and the real exam — you never grasped the material.

This maps directly onto k-NN (see §8.3): **k = 1** gives 0% train error but a jagged, noise-hugging boundary → high test error (**high variance**); **k = m** always predicts the majority class, so it is wrong even on training data → high train *and* test error (**high bias**). The sweet-spot k is where train and test error are both low and close together.

### 8.1.2 Flexibility → Variance → Overfitting (the retraining intuition)

**[Builds on AML L02 slides 37–58; formal decomposition: ISLP §2.2.1–2.2.2, ESL §2.9 / §7.3]**

This subsection makes precise *why* a more flexible model overfits. The chain is: **more flexibility → higher variance → overfitting.** The key is what "variance" actually measures.

**What "flexibility" means.** A model's *flexibility* (or capacity) is the range of different functions it is free to represent. A flexible model can bend into wiggly, complicated shapes; a rigid one is stuck near a simple shape. Every model has a knob that sets this:

- **k-NN:** flexibility rises as **k falls**. `k = 1` is maximally flexible (the boundary can hug every point); `k = m` is maximally rigid (one constant prediction).
- **Polynomial regression (L04):** flexibility rises with **degree**. Degree 1 is a rigid line; degree 15 can thread through almost any set of points.

**Variance is not about one training set — it is about *how the model would change across different training sets*.** This is the intuition to hold onto:

> Imagine you could draw many different training samples `D₁, D₂, …, D_B`, each of size *m*, all from the **same** underlying distribution. Train the *same* model (same k, same degree) separately on each one, giving fitted predictors `f̂(·; D₁), …, f̂(·; D_B)`. Now fix a single test point **x** and look at the *B* predictions `f̂(x; D₁), …, f̂(x; D_B)`. They will differ, because each model saw a different sample. **Variance at x = the average amount those predictions swing around their own mean.** High variance = the prediction at x jumps around a lot depending on *which* sample you happened to train on; low variance = the prediction is stable no matter the sample.

So variance measures the **instability / sample-sensitivity of the model's predictions**, averaged over the training samples you might have gotten. (Precisely it is the average *squared* deviation from the mean prediction — the statistical variance of `f̂(x; D)` over D — but the working intuition is "how much do the predictions move when I retrain on a fresh sample.")

**The formal version (one line).** Let `f̄(x) = E_D[f̂(x; D)]` be the *average* prediction over all possible training sets. Then for squared-error regression with `y = f(x) + ε`, `Var(ε) = σ²`:

```
 E_D[(y − f̂(x;D))²]  =  (f̄(x) − f(x))²   +   E_D[(f̂(x;D) − f̄(x))²]   +   σ²
 expected test error  =     Bias(x)²       +        Variance(x)          +  irreducible
```

The expectation `E_D[ · ]` *is* the "average over different training samples" — that operator is literally the retraining thought experiment written down. **Bias** = how far the *average* prediction sits from the truth (systematic error); **Variance** = how much individual predictions scatter around that average (sample-to-sample wobble).

**Why more flexibility raises variance.** Each training sample carries the true signal *plus its own particular noise*. A flexible model has enough degrees of freedom to **bend itself to fit that noise** — and since the noise is different in every sample, the fitted function comes out different every time → the predictions wobble a lot → **high variance**. A rigid model can't chase the noise (it can only render a simple shape), so it lands in nearly the same place regardless of the sample → **low variance** — but that same rigidity may make it systematically miss the signal → **high bias**. This is the tradeoff: the flexibility that buys you low bias is exactly what costs you high variance.

**Why high variance *is* overfitting.** Overfitting means the model learned the noise of its particular training set instead of the generalizable signal. The retraining experiment exposes this directly: an overfit model produces wildly different predictions across resamples, and none of them track the truth — they track each sample's accidents. That is why you can't see overfitting from a single training set's low train error; you see it as **instability across resamples**, which is also precisely why **cross-validation** (§9), by repeatedly refitting on different folds, is able to detect it.

**k-NN made concrete.** Fix a test point x and resample the training data:

- **`k = 1`:** the prediction is whatever the single nearest point happens to be. Swap a few training points for a fresh sample and the nearest neighbour — hence the prediction — can flip entirely. Predictions swing hard across samples → **high variance** → overfitting.
- **`k = m`:** the prediction is the global majority class, which barely changes if you resample. Predictions are rock-stable across samples → **low variance** → (but high bias).

This is the same fact as "moving one training point changes the k=1 boundary dramatically" (§8.3), now stated as the quantity it really is: **variance = sensitivity of the prediction to the particular training sample.**

**The chain, in one sentence.** Raising flexibility (↓ k, ↑ degree) lets the model fit the sample-specific noise, so its fitted function — and therefore its prediction at any fixed x — changes a lot from one training sample to the next; that sample-to-sample swing **is** the variance, and high variance **is** overfitting (low train error, high test error). *(Polynomial mirror in `../lect04 non-linear regression/AML_L04_Ultimate_Reference.md` §9–§10: a degree-15 fit is a different wild curve on every resample; a line is nearly the same line every time.)*

### 8.2 The Dart-Throwing Analogy

**[Source: AML L02, slide 55]**

Think of a dart thrower:
- **High bias:** Consistently misses the bullseye (systematic error), but the darts are clustered together
- **High variance:** Darts are scattered all over the board, even if their average position is the center
- **Goal:** Low bias AND low variance — consistently hitting the bullseye

### 8.3 Bias-Variance in k-NN

| k | Bias | Variance | Effect |
|---|------|----------|--------|
| k = 1 | Low (flexible boundary) | High (sensitive to noise) | Overfitting |
| k = m | High (predicts majority class) | Low (same prediction always) | Underfitting |
| Sweet spot | Moderate | Moderate | Best generalization |

**Why k = 1 has high variance:** The decision boundary is jagged — it hugs every single training point. Moving one training point changes the boundary dramatically.

**Why large k has high bias:** The boundary is overly smooth — it ignores local structure. It's like asking the entire population to vote on every prediction.

### 8.4 The Three Error Curves

**[Source: AML L02, slides 49–52]**

When you plot error as a function of k:

1. **Training error** (blue): Monotonically increases with k. At k=1, it's 0% (every point is its own neighbor). As k grows, the model becomes more constrained.

2. **Validation/CV error** (black): U-shaped. Decreases as k increases from 1 (reducing variance), hits a minimum at the sweet spot, then increases again (increasing bias).

3. **Test error** (brown): Similar shape to validation but not identical. The minimum of the validation curve may not exactly match the minimum of the test curve.

**Key insight:** The value of k that minimizes validation error is our best estimate of the optimal k, but it may not be the true optimum for unseen data. This is why we keep the test set completely separate.

### 8.5 Generalization Performance

**[Source: AML L02, slide 42]**

Generalization is the ability of a model to make accurate predictions on new, unseen data. AML L02 uses the Tesla self-driving example: the car must not make mistakes in traffic situations unknown at training time.

The goal of all model selection (choosing k, choosing features, choosing the distance function) is to **maximize generalization performance**.

---

## 9. Cross-Validation

**[Source: AML L02, slides 40–58; ISLP Chapter 5.1; SaD L11, slides 93–97]**

### 9.1 The Fundamental Problem

We want to find the best hyperparameters (e.g., k in k-NN), but:

- **Never optimize on the test data.** Once you use test data for decisions, it's no longer an unbiased estimate of generalization performance.
- AML L02, slide 44 (quoting *Elements of Statistical Learning*): "Ideally, the test set should be kept in a 'vault' and be brought out only at the end of the data analysis."

**The Cardinal Rule of Machine Learning (AML L02, slide 45):** Never use the test data to choose hyperparameters. The test data is your final, one-time measurement of generalization.

### 9.2 Three-Way Partition

**[Source: AML L02, slide 46; SaD L11, slides 95–97]**

Split labeled data D into three disjoint sets:

| Split | Purpose | Typical size |
|-------|---------|------|
| **Training** | Learn the model (in k-NN: store these points) | 60-80% |
| **Validation** (Dev) | Choose hyperparameters (find best k) | 10-20% |
| **Test** | Final evaluation of generalization | 10-20% |

**SaD L11 example:** 1000 labeled emails → 800 train, 100 validation, 100 test.

**Drawback:** We lose data for training. With small datasets, this significantly hurts model quality.

### 9.2.1 Why We Say "Training" vs "Validation" When k-NN Doesn't Train

**[Connects to §3.1 (lazy learning) and §7.1 (train error). Resolves an apparent contradiction in this document.]**

Earlier we said k-NN has **no training phase** and that "the training data *is* the model" (§3.1). So why do we still split off a **training** set and call it that? Because in ML, **"training" names the *role* a data partition plays in the workflow — not the amount of computation performed.** "Training" = *whatever the algorithm does to prepare to predict*, however trivial. The split names are deliberately algorithm-agnostic so the same cross-validation machinery works for every model.

**What "training" means for k-NN specifically:** the fit step is real but trivial — `fit()` just **stores the labeled points** (a lazy learner) plus any preprocessing derived from them (e.g., feature-scaling min/max or mean/std, see §6). The training set is therefore **the pool of points the algorithm is allowed to consult as neighbors.** So for k-NN the train/validation boundary is not "data I learned weights from" vs "data I didn't" — it is:

- **Training points** = eligible to be neighbors (the lookup pool)
- **Validation points** = the points being predicted and scored (never their own neighbors)

**Why the split is essential *precisely because* k-NN doesn't fit anything:** recall from §7.1 that 1-NN has **0% training error by construction** — every point is its own nearest neighbor. If validation points sat in the same pool they were scored against, every query would find itself and report trivially perfect accuracy. Holding the validation set out is the *only* thing that makes the error estimate honest. Same justification as a parametric model, reached from the opposite direction.

**What is actually "learned" during k-NN cross-validation:** not parameters (there are none — see §10.1), but the **hyperparameter k** (and p, the distance metric). The CV loop is a search: for each candidate k, use the training folds as the neighbor pool, score on the held-out fold, average. Selecting the k with lowest validation error *is* learning from data — just at the hyperparameter level rather than the parameter level.

**Practical consequence — k-NN can still leak.** Even with no weights, feature-scaling statistics must be computed from the **training fold only**. Scaling the whole dataset before splitting bleeds validation information into "training," exactly the failure the partition exists to prevent. So the train/validation boundary is operationally meaningful for k-NN, not just inherited terminology.

### 9.3 The Validation Set Approach

**[Source: ISLP 5.1.1]**

The simplest resampling method: randomly split data into a training set and a validation set (typically 50/50 or 80/20). Fit the model on the training set, evaluate on the validation set.

ISLP demonstrates this on the Auto dataset, fitting polynomial regressions of degrees 1-10 and measuring validation MSE. The quadratic fit clearly outperforms linear, but cubic adds no improvement.

**Two drawbacks (ISLP):**
1. **High variability:** The validation MSE estimate depends heavily on which observations land in which split. Different random splits give substantially different estimates.
2. **Data waste:** Only the training portion is used to fit the model. With fewer training observations, statistical methods tend to perform worse, so the validation error may overestimate the true test error.

### 9.4 Leave-One-Out Cross-Validation (LOOCV)

**[Source: ISLP 5.1.2; AML L02, slide 58]**

Instead of one large split, use each observation once as the sole validation point:

**Procedure:**
1. For i = 1 to n: remove observation i, train on the remaining n-1, predict for observation i
2. Compute the test error estimate:

$$CV_{(n)} = \frac{1}{n} \sum_{i=1}^{n} MSE_i$$

**Advantages over validation set approach:**
- **Far less bias:** Training on n-1 observations (nearly all data)
- **No randomness:** The same split always gives the same result
- Every observation is used for both training and validation

**Computational shortcut for linear regression (ISLP formula 5.2):**

$$CV_{(n)} = \frac{1}{n} \sum_{i=1}^{n} \left(\frac{y_i - \hat{y}_i}{1 - h_i}\right)^2$$

where ŷᵢ is the fitted value from the full model and hᵢ is the leverage (how much observation i influences its own fit). This makes LOOCV cost the same as fitting the model once — a remarkable result.

**Disadvantage:** For non-linear models without this shortcut, LOOCV requires fitting the model n times, which can be very slow for large n.

### 9.5 k-Fold Cross-Validation

**[Source: ISLP 5.1.3; AML L02, slides 47–48]**

The practical workhorse. Divide D_train into k (often written r in AML) equally-sized folds.

**Algorithm (AML L02, slide 48):**
```
Split D_train into r equally-sized folds {f₁, ..., fᵣ}

for each hyperparameter k ∈ {1, 3, 5, ...}:
    for each fold f ∈ {f₁, ..., fᵣ}:
        train model on remaining (r-1) folds: {f₁,...,fᵣ} \ {f}
        validate model on fold f
    compute average error over all r folds
choose k with smallest average validation error
```

**The ISLP formula:**

$$CV_{(k)} = \frac{1}{k} \sum_{i=1}^{k} MSE_i$$

Note: LOOCV is the special case where k = n.

**Practical choice of k (AML L02, slide 58):**
- **Rule of thumb:** Use k = 3, 5, or 10
- k small → faster training, higher bias, lower variance
- k large → slower training, lower bias, higher variance

### 9.6 Bias-Variance Tradeoff in Cross-Validation

**[Source: AML L02, slides 53–58; ISLP 5.1.4]**

The number of folds r creates its own bias-variance tradeoff:

**Extreme Case A: r = 2 (AML L02, slide 57)**
Each fold has only half the data. The training set is small → model underfits → error estimate has **high bias** (overestimates true error). The error might be 100% in some cases.

**Extreme Case B: r = m (LOOCV) (AML L02, slide 57)**
Each training set has m-1 points (nearly all data) → low bias. But the m training sets are nearly identical (they differ by only one point) → the m error estimates are highly correlated → their average has **high variance**. The error estimate can fluctuate dramatically.

**Sweet spot: k = 5 or k = 10**
- Enough data in each training fold to fit well (moderate bias)
- Enough independence between folds for stable estimates (moderate variance)
- ISLP states this is empirically validated across many studies

### 9.7 CV for k-NN Classification

**[Source: AML L02, slides 49–52; ISLP Figure 5.8]**

ISLP Figure 5.8 shows a powerful illustration: for a 2D classification problem, the 10-fold CV error curve closely tracks the true test error curve when applied to k-NN with different values of K. The CV curve correctly identifies the optimal K despite never seeing the test data.

The training error curve always decreases as the model becomes more flexible (smaller K), confirming that training error alone cannot guide model selection.

---

## 10. Hyperparameter Tuning

**[Source: AML L02, slides 40–45, 69; SaD L11, slide 92]**

### 10.1 Model Parameters vs Hyperparameters

**[Source: AML L02, slide 69]**

| | Model Parameters | Hyperparameters |
|--|-----------------|-----------------|
| **What** | Learned from training data | Set before training begins |
| **How** | By the learning algorithm | By the practitioner (via CV) |
| **k-NN example** | None (lazy learner) | k (number of neighbors), p (Lp norm) |
| **Linear regression example** | Weights β | Regularization λ |

### 10.2 Grid Search

To optimize multiple hyperparameters simultaneously, evaluate all combinations:

For k-NN with hyperparameters k ∈ {1,...,9} and p ∈ {1, 2, 3}:
- This gives 9 × 3 = 27 combinations
- For each combination, run k-fold CV
- Select the combination with lowest average CV error

**In sklearn:**
```python
from sklearn.model_selection import GridSearchCV

parameters = {
    'n_neighbors': np.arange(1, 10),
    'p': np.arange(1, 4)
}
grid = GridSearchCV(KNeighborsClassifier(), parameters, cv=3)
grid.fit(X_train, y_train)

print(grid.best_params_)       # {'n_neighbors': 5, 'p': 1}
print(grid.best_score_)        # Cross-validation accuracy
print(grid.score(X_test, y_test))  # Test accuracy (evaluate ONCE)
```

### 10.3 The Complete ML Workflow

**[Source: SaD L11, slides 93–101, 123]**

1. **Split data** into train / dev / test
2. **Vectorize** features (one-hot, scaling, etc.)
3. **For each hyperparameter combination:**
   - Train model on training split
   - Evaluate on dev split (or use k-fold CV on training data)
4. **Select** the hyperparameters with best dev/CV performance
5. **Retrain** final model on full training data with best hyperparameters
6. **Evaluate once** on test split → this is your reported generalization performance
7. **Check statistical significance** (t-test, etc.) when comparing models

---

## 11. Summary and Cross-Wire Moments

### 11.1 Key Takeaways

**k-NN (AML L02 + SaD L11):**
- Simple, powerful, no training phase
- Expensive at test time: O(nm) per query
- Very sensitive to feature scale and irrelevant features
- Hyperparameter k controls the bias-variance tradeoff

**Evaluation (SaD L11):**
- Never evaluate on training data alone (1-NN train error = 0% = meaningless)
- Use precision/recall/F1 when classes are imbalanced
- Confusion matrices provide per-class diagnostics

**Cross-Validation (ISLP 5.1 + AML L02):**
- The Cardinal Rule: never use test data for model selection
- k-fold CV (k=5 or 10) is the practical standard
- LOOCV is low-bias but high-variance and slow (unless the shortcut formula applies)
- The CV error curve approximates the true test error curve

### 11.2 Cross-Wire Moments (Connections Between Sources)

> The SaD-side depth for every wire below now lives in **`…/SaD/notes/lect11 instance-based/SaD_L11_Reference.md`** (vectorization §4, similarity measures §5, the evaluation toolkit §8). This section is the *index* of how the two lectures connect — see the full scope-split table in **SaD L11 §10**.

1. **SaD L11 ↔ AML L02 (k-NN):** SaD L11 gives the algorithm pseudocode and the similarity/distance theory. AML L02 adds the bias-variance theory, the Lp generalization, and the connection to model complexity. Together they provide both the *what* and the *why*.

2. **SaD L11 ↔ AML L02 (evaluation):** SaD L11's confusion matrix + precision/recall framework is used directly in AML L02's error analysis. When AML says "test error = 3.09%", that's the accuracy metric from SaD. When you analyze failure cases (AML slide 31), you're doing what SaD calls qualitative evaluation.

3. **ISLP 5.1 ↔ AML L02 (cross-validation):** AML L02 introduces CV as "the way to choose k." ISLP 5.1 provides the mathematical depth: the formal CV formulas, the LOOCV shortcut, and the bias-variance analysis of why k=5 or k=10 works well. ISLP also proves that the CV error curve approximates the true test error curve.

4. **SaD L11 vectorization ↔ AML exercise:** The AML exercise uses CLIP embeddings (512D vectors) to represent dog images. This is the modern version of what SaD L11 teaches as "Vektorisierung" — converting real-world data to numerical vectors. The exercise skips raw pixel vectorization (which SaD L11 shows) and uses learned embeddings instead.

5. **SaD feature scaling ↔ AML distance sensitivity:** AML L02 shows that pixel shifts destroy Euclidean distance on raw images. SaD L11's feature scaling section explains the general principle: features must be on comparable scales for distance-based methods to work. This is why the AML exercise works well — CLIP embeddings are already normalized.

### 11.3 What's Next

After mastering this material, the plan continues to:
- **Block E (Regression):** Linear regression uses the same loss minimization principle as k-NN's MSE
- **Block H (Regularization):** Ridge/Lasso add λ-controlled penalties — hyperparameter selection via CV is the same
- **Block I (Classification):** Logistic regression provides a parametric alternative to k-NN for classification

---

*Document version 1.0 — KW 22 (May 2026)*
*Plan step IDs covered: F.B2, F.D1, F.D2, F.D3, F.D3b, F.D4, F.D5 (partial)*
