---
id: note-sad-l11-instance-based
type: note
title: "SaD Lecture 11 — Ultimate Reference: Similarity-Based / Instance-Based Machine Learning"
created: "2026-07-11"
role: reference
state: evolving
authorship: mixed
concepts: [concept-k-nearest-neighbors, concept-feature-scaling, concept-classification-metrics]
sources: [source-sad-ss26-lectures, source-kelleher-fmlpda]
contexts: [workspace-m2-exam-prep]
---

> **Migration note (2026-07-17, Stage 2):** body preserved verbatim from
> `Plans/Math/sad/SaD/notes/lect11 instance-based/SaD_L11_Reference.md` (legacy tree).

# SaD Lecture 11 — Ultimate Reference: Similarity-Based / Instance-Based Machine Learning

*Source: **SaD-2025 Lecture 11 "Ähnlichkeitsbasiertes Maschinelles Lernen"** (Prof. Dr. Alan Akbik, HU SoSe 2025) — `…/SaD/SaD-2025/11_instance-based.pdf`, 126 slides. The lecture is delivered in German; this reference keeps the German terms with English glosses.*

> **What this sheet is.** The standalone home for the full SaD L11 lecture. The **AML L02** reference (k-NN) borrows only the overlapping bits (k-NN intuition, distances, scaling, train/test split) and **links here** for everything that is SaD-scope: the four ML families, the full *Vektorisierung* treatment, cosine similarity, and the complete evaluation toolkit. The what-lives-where map is **§10**.

## Table of Contents

1. [From Statistics to Machine Learning](#1)
2. [The Four Families of ML Approaches](#2)
3. [Similarity-Based Classification: Intuition & Algorithm](#3)
4. [Vectorization of Features (Vektorisierung)](#4)
5. [Measuring Similarity: Distance & Similarity Measures](#5)
6. [Feature Scaling](#6)
7. [Overfitting / Underfitting & the Choice of k](#7)
8. [Training & Evaluation](#8)
9. [Self-Test](#9)
10. [Cross-Reference Map to AML L02](#10)

---

## 1. From Statistics to Machine Learning <a name="1"></a>

**[Source: SaD L11, slides 5–26]**

**The central problem of statistics:** a **population** (*Grundgesamtheit*) `U` cannot be measured in full; we draw a random **sample** (*Stichprobe*) `X₁,…,Xₙ` (i.i.d.) and **estimate** a property `θ` of `U` (mean, median, variance, …) from it.

**The shift to ML:** statistics focuses on **aggregates** (population-level relationships); ML focuses on **predictions for individual data points / instances**. The lecture's contrast table:

| Aggregate (statistics) | Individual data point (ML) |
|---|---|
| Probability it rains < 5× in Berlin in June | Given today's weather: will it rain tomorrow? |
| Probability a data scientist at firm X earns > 80k | How much will *I* earn? |
| Probability that drug A causes side effects | Will *I* get side effects? |

**Data types** (*Datentypen*): **structured** (tables — rows = instances, columns = features; first normal form; from DBs, CSVs, sensors, surveys), **unstructured** (text, images, graphs), **sequence** (time series, DNA, language). Real datasets are often distributed, large, fast-changing (→ stream/incremental learning), heterogeneous, noisy, and multivariate (thousands of features).

**Features & targets:** four feature types — nominal, ordinal, interval, ratio; `x = (x₁,…,xₙ)`; target `y` discrete or continuous. *(Arthur Samuel, 1959: "Machine Learning: field of study that gives computers the ability to learn without being explicitly programmed.")*

**Three kinds of ML:** **Classification** (predict a discrete variable — fraud, categorization), **Regression** (predict a continuous variable — tomorrow's temperature, steering angle), **Clustering** (discover structure — customer segments). **Supervised learning** = learn a function `f(x) → ŷ` from labeled data `D` of `m` input–output pairs `(x⁽ⁱ⁾, y⁽ⁱ⁾)` — *the analogue of estimating a distribution's parameters from a sample.*

---

## 2. The Four Families of ML Approaches <a name="2"></a>

**[Source: SaD L11, slide 27]** *(This taxonomy is SaD-specific — AML L02 does not give it.)*

| Family | Idea | Examples |
|--------|------|----------|
| **Ähnlichkeitsbasiert** (similarity-based) | Decisions based on **similarity to known data** | **k-NN** (this lecture) |
| **Informationsbasiert** (information-based) | Information-theoretic splits | Decision Trees, Random Forests |
| **Wahrscheinlichkeitsbasiert** (probability-based) | Probability theory | Naive Bayes |
| **Fehlerbasiert** (error-based) | Minimize a **loss function** | Linear Regression, Neural Networks (ANNs) |

> This places k-NN among its siblings: it's the **similarity-based** family. The AML track lives mostly in the **error-based** family (regression, logistic regression, NNs — all "minimize a loss"), which is why AML and SaD feel like different angles on the same menu.

---

## 3. Similarity-Based Classification: Intuition & Algorithm <a name="3"></a>

**[Source: SaD L11, slides 29–35]**

**Core idea:** *similar data points probably belong to the same class.* For a new point, find the most similar training instances and derive the class from them → the **nearest-neighbor classifier**; the standard variant considers the **k nearest neighbors (k-NN)**.

**Lazy learner:** **no model is trained** — the training data is merely *indexed*. (Also called **instance-based** or **memory-based** learning.) Cognitive-science parallel — **case-based reasoning**: medical diagnosis (doctors recall past cases), legal argument (precedent), creative design (reusing similar prior solutions).

**The algorithm (lecture pseudocode):**

```
Input: training data (x₁,y₁),…,(xₙ,yₙ); new input x_neu; k; distance d(x,x′)
1. For each training example (xᵢ,yᵢ): compute d(x_neu, xᵢ)
2. Sort the training examples by ascending distance
3. Take the k nearest neighbors
4. Determine the most frequent class among them  (majority of labels)
5. Return that class as the prediction for x_neu
```

**Probabilistic reading:** `P(x belongs to class c) =` the **fraction of the k nearest neighbors that belong to c**. Two open questions drive the rest of the lecture: *how do we define the similarity of two points?* and *what k do we choose?*

---

## 4. Vectorization of Features (Vektorisierung) <a name="4"></a>

**[Source: SaD L11, slides 36–57]** — *Before any distance can be computed, every data point must become a numeric feature vector. This is the most SaD-specific section and is **the** reason AML L02 links here.*

**Scale types** (*Skalenniveaus* — slide 37):

| Scale | Description | Examples | Operations |
|-------|-------------|----------|-----------|
| **Nominal** | categories, **no** order | ja/nein; rot/grün/blau | `=`, `≠` |
| **Ordinal** | **ordered** categories | wenig / mittel / sehr | `>`, `<` |
| **Intervall** | metric, **no** true zero | 2019, 2020 (years) | `+`, `−` |
| **Verhältnis** (ratio) | metric, **true** zero | 10 min, 20 min | `×`, `÷` |

**How each type becomes vector dimensions:**
- **Metric** (interval/ratio): each feature → **1 dimension**, value used directly.
- **Nominal → One-Hot Encoding** (the standard): one dimension per category, all `0` except the chosen category `= 1`. E.g. gender {m, f, d} → `m = (1,0,0)`, `f = (0,1,0)`, `d = (0,0,1)`.
- **Enumerations / multi-valued** (*Aufzählungen*) → **multi-hot**: a binary variable per category. E.g. languages {R, Python, Java, Matlab}; an entry "Python, Java" → `(0,1,1,0)`.
- **Ordinal**: *Option 1* one-hot (but one-hot vectors are **orthogonal** → the order is lost); *Option 2* a single ordered value, e.g. {wenig, mittel, viel} → `[1]/[2]/[3]`. Trade-off: one-hot keeps categories distinct but drops order; single value keeps order but imposes equal spacing.

**Special case — text** (slides 50–51): **Count Vectorization / Bag-of-Words** — each dimension = a vocabulary word, value = its count in the text. *"Kaufen jetzt kaufen!"* → *kaufen*: 2, *jetzt*: 1, rest 0. **Disadvantages:** word **order is lost** (as in Naive Bayes); **unknown/new words** aren't captured.

**Special case — images** (slides 52–56): an image as a **vector of colour/pixel values** (*Bild als Vektor von Farbwerten*) — flatten the pixel grid into one long vector.

**Summary:** every data point can be written as a feature vector, and that vector representation is the basis of **almost every** ML method.

---

## 5. Measuring Similarity: Distance & Similarity Measures <a name="5"></a>

**[Source: SaD L11, slides 58–85]**

**Distance measure** (*Distanzmaß*) — axioms: a function `dist : I×I → ℝ` is a distance measure if for all `i,j`: **symmetry** `dist(i,j)=dist(j,i)`, and **non-negativity / identity** `dist(i,j) ≥ 0` with `= 0 ⟺ i = j`. There is no maximum; the minimum is 0; higher = more dissimilar. The values form a symmetric `N×N` **distance matrix**.

**Lₚ distances** (slides 61–62): the generic `Lₚ` distance between `x⁽ⁱ⁾, x⁽ʲ⁾`; the two used here:
- **L1 — Manhattan distance**: sum of absolute coordinate differences (city-block).
- **L2 — Euclidean distance**: the straight-line (ruler) length. **Disadvantage:** squaring the differences means **features with large values dominate** → motivates scaling (§6).

**Mahalanobis distance** (slides 77–78): all the above ignore the **distribution** of the data. When features are strongly **correlated** (high covariance), Mahalanobis **scales each dimension's difference by the covariance**, so correlated dimensions get **less weight**. Needs the **covariance matrix Σ** and the **mean vector μ**.

**Similarity measure** (*Ähnlichkeitsmaß*) — axioms: `sim : I×I → ℝ`, **symmetric**, and `sim(i,i) ≥ sim(i,j)` (*a point is most similar to itself*); usually in `[0,1]` or `[−1,1]`; higher = more similar. → a symmetric **similarity matrix**.

**Cosine similarity** (slides 80–84): the **angle** between two feature vectors; range `[−1,1]`; **normalizes for vector length**. Computed as the **dot product ÷ (product of the two lengths)**. Interpretation: **positive** = similar, **≈ 0** = orthogonal (no similarity), **negative** = opposite. **For text** (one-hot/count vectors, all entries ≥ 0): cosine lies in `[0,1]` — `0` = no shared words, `1` = identical words; the **cosine distance** is then `1 − cosine similarity` (a distance with max 1).

**Summary (slide 85):** the similarity of two points depends on the **features chosen**, their **scaling**, and the **distance measure**.

---

## 6. Feature Scaling <a name="6"></a>

**[Source: SaD L11, slides 66–76]** *(In the lecture this sits inside "Messen von Ähnlichkeiten" — distance depends on how features are scaled.)*

Because Euclidean distance lets large-valued features dominate, features are put on a comparable scale. Two methods:

**Min-Max Normalization (Rescaling)** — map each feature to `[0,1]`:
```
x' = (x − min) / (max − min)
```
*Example (German states by GDP):* Bayern 70 549 → **1.000**, Bremen 419 → **0.000**, the rest in between.

**Z-Score Normalization (Standardization)** — subtract the feature mean, divide by the feature standard deviation → mean 0, std 1:
```
z = (x − μ) / σ
```
*Example:* with `μ = 22 350`, `σ = 18 699`, Bayern 70 549 → `z = (70 549 − 22 350)/18 699 ≈ 2.58`.

Rescaling fixes the range; standardization fixes the spread and is less sensitive to the exact min/max (outliers).

---

## 7. Overfitting / Underfitting & the Choice of k <a name="7"></a>

**[Source: SaD L11, slides 86–92]**

The choice of **k strongly affects the result** (too small? too large?):
- **Overfitting** — **k too small**: the model abstracts too little over the training data → **outliers are mistaken for important patterns** (*"Ausreißer werden als wichtige Muster erkannt"*); the data needs "smoothing" (*Weichzeichnen*).
- **Underfitting** — **k too large**: important patterns are no longer recognized.

**Aggregation functions for k-NN** (given the k labels, sorted by distance):
- **Nominal** classes → **majority voting** (beware ties; use k = 3, 5, …).
- **Ordinal** classes → **median** of the labels.
- **Advanced** → **distance weighting**: nearer neighbors count more, e.g. `class(z) = argmax_c Σᵢ (1/dist(z,dᵢ))·I(i,dᵢ)`.

How do we *find* the best k and aggregation? A **simulation-based setup** — the next section.

---

## 8. Training & Evaluation <a name="8"></a>

**[Source: SaD L11, slides 93–124]**

**The three splits.** Labeled data `D` is divided into disjoint sets:

| Split | Role |
|-------|------|
| **D_train** | determines the model (for k-NN: the indexed points the prediction reads from) |
| **D_validation / Dev** | "hold-out" used to **select hyperparameters** (best k, early stopping) |
| **D_test** | "hold-out" used **once** for the final estimate of model quality |

*Example:* 1000 labeled emails → **80%** train, **10%** dev, **10%** test. **Procedure:** (1) train on D_train; (2) predict on the held-out set; (3) compare predictions against the gold labels.

**Accuracy** = fraction of correct predictions — the standard measure **when each point gets exactly one label**. **Problem — class imbalance** (*Class Imbalance*): if 99% of mails are non-spam, a "predict non-spam always" model scores 99% accuracy while catching zero spam → accuracy alone is misleading; we need **Precision, Recall, F-Score**.

**Confusion matrix** (*Wahrheitsmatrix*) for a class X:

| | Predicted **X** | Predicted **other** |
|---|---|---|
| **Gold X** | True Positive (TP) | False Negative (FN) |
| **Gold other** | False Positive (FP) | True Negative (TN) |

```
Precision = TP / (TP + FP)   — of those predicted positive, how many are right
Recall    = TP / (TP + FN)   — of the actual positives, how many we caught
F-Score   = harmonic mean(Precision, Recall) = 2·P·R / (P + R)
```

One confusion matrix is built **per label** (spam classification → a SPAM matrix and a KEIN_SPAM matrix).

**Worked example (the lecture's SPAM / KEIN_SPAM data, computer-verified):**

| Class | TP | FP | FN | Precision | Recall | F-Score |
|-------|----|----|----|-----------|--------|---------|
| **SPAM** | 1 | 0 | 2 | 1.0 | 1/3 ≈ 0.33 | **0.50** |
| **KEIN_SPAM** | 7 | 2 | 0 | 7/9 ≈ 0.78 | 1.0 | 0.88 |

> ⚠️ **Slide typo:** the lecture's summary table prints the **SPAM F-Score as 0.37**. The harmonic mean of P = 1.0 and R = 0.33 is **0.50**, and the deck's own **Macro-F = 0.69** only reconciles with 0.50 (since (0.50 + 0.88)/2 = 0.69, whereas (0.37 + 0.88)/2 = 0.63). So read **SPAM F = 0.50**. *(verified with exact fractions.)*

**Accuracy** here = (TP+TN)/all = **8/10**.

**Micro vs Macro averaging** (combining the per-class numbers into one):
- **Micro-Average** — pool the counts across classes, *then* compute: `precision = (TP_SPAM + TP_KEIN) / (TP_SPAM + TP_KEIN + FP_SPAM + FP_KEIN) = (1+7)/(1+7+0+2) = 0.8`. (Micro P = R = F = **0.8**.)
- **Macro-Average** — the **arithmetic mean** of the per-class values: macro-P = (1.0 + 0.78)/2 = **0.89**, macro-R = (0.33 + 1.0)/2 = **0.67**, macro-F = (0.50 + 0.88)/2 = **0.69**.
- **Macro < Micro ⇒ the rare class (SPAM) is recognized less well** — macro averaging weights every class equally, so it exposes poor minority-class performance that micro (count-weighted) hides.

**Evaluation in one number** (for comparison tables): **Accuracy** when every point has exactly one label and there's no imbalance; **Micro-F** when points may have no label; **Macro-F** for **class imbalance** (the fair choice — "leider selten" / sadly rarely used).

**ML workflow:** you spend most of your time on the **train + dev** splits, tuning hyperparameters to do best on dev; mind **statistical significance** (t-test) when comparing — and keep the **test split sealed** until the end.

---

## 9. Self-Test <a name="9"></a>

1. Name the **four ML families** and give one example algorithm of each. Which family is k-NN? Which family is most of AML?
2. Why is k-NN called a **lazy learner**? What is actually "stored" at training time?
3. Vectorize one survey row with: years-experience = 3 (metric), gender = f (nominal), languages = {Python, Java} (enumeration), open-source = "viel" (ordinal, ordered encoding). Write the full vector.
4. Why are **one-hot** vectors a problem for **ordinal** data? Give the two encoding options and their trade-off.
5. State the **distance-measure axioms** and the **similarity-measure axioms**. How do you turn cosine similarity into a distance?
6. When is **cosine similarity** preferred over Euclidean distance? What is its range for text (count) vectors, and why?
7. Min-max vs z-score normalization: write both formulas; which is less sensitive to outliers and why?
8. For the SPAM example, recompute Precision, Recall and F for SPAM and verify the **0.50** F-Score. Then compute micro- and macro-averaged F.
9. You have 99% non-spam. Why is accuracy a bad single number here, and which one should you report instead?
10. What are the **roles** of the train / dev / test splits? Why must the test split be touched only once?

---

## 10. Cross-Reference Map to AML L02 <a name="10"></a>

This sheet and `…/AML/my notes/lect02 KNN-classifier/AML_L02_Ultimate_Reference.md` deliberately split the material:

| Topic | Lives in | Notes |
|-------|----------|-------|
| Four ML families taxonomy | **SaD L11 §2** | SaD-only; AML L02 links here |
| Vectorization (scale types, one-hot, multi-hot, ordinal, text, images) | **SaD L11 §4** | SaD-only; the AML exercise uses pre-made CLIP embeddings instead |
| Cosine similarity / similarity measures | **SaD L11 §5** | SaD-only |
| Full evaluation toolkit (confusion matrix, P/R/F, micro/macro) | **SaD L11 §8** | SaD-only; AML L02 keeps only train/test-error + accuracy for error analysis |
| k-NN algorithm & aggregation | **both** | AML L02 §3 is the home; SaD §3 gives the lazy-learner framing + pseudocode |
| Distance functions (Lp, Manhattan, Euclidean, Mahalanobis) | **both** | AML L02 §4 is the home; SaD §5 adds the axioms + cosine |
| Feature scaling (min-max, z-score) | **both** | AML L02 §6 is the home; SaD §6 has the worked German-states example |
| Train / validation / test split | **both** | AML L02 §9 (as part of cross-validation); SaD §8 has the roles + spam example |
| **Bias–variance, cross-validation depth, hyperparameter tuning** | **AML L02 only** | the AML lecture's own scope — *not* in SaD L11 |

*Whenever AML L02 needs the SaD-side depth, it points to the section here rather than carrying it inline.*

