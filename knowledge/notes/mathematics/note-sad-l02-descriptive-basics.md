---
id: note-sad-l02-descriptive-basics
type: note
title: "SaD L02 — Ultimate Reference: Basic Concepts (Populations, Scales, Location & Dispersion)"
created: "2026-07-11"
role: reference
state: evolving
authorship: mixed
concepts: [concept-descriptive-statistics, concept-variance]
sources: [source-sad-ss26-lectures, source-teschl-mathe-informatiker,
  source-fahrmeir-statistik, source-openintro-statistics]
contexts: [workspace-m2-exam-prep]
---

> **Migration note (2026-07-17, Stage-1 pilot):** body preserved verbatim from
> `Plans/Math/sad/SaD/notes/lect02 basics/SaD_L02_Ultimate_Reference.md` (legacy tree). Companion: `note-sad-l02-exercise-bank`; the Mini Plan is operational and lives in `work/active/workspace-m2-exam-prep/`.

# SaD Lecture 02 — Ultimate Reference: Basic Concepts (Populations, Scales, Location & Dispersion)

*Synthesized from: SaD L02 (Leser, HU SoSe 2026) `Lecture-slides/02_basics.pdf` (39 slides) + Teschl & Teschl (descriptive) / Fahrmeir Ch 2 (notation-matched) + OpenIntro Ch 2 (gentle). Cross-wired to L01 (the informal preview), L06 (RVs/variance rules), L08 (z-scores), L09 (why n−1).*
*Created: KW 28 (Jul 2026) — second per-lecture SaD unit (3-file variant, no Mock Exam).*

---

## Table of Contents

1. [What Statistics Is (and the three kinds)](#1-what-statistics-is-and-the-three-kinds)
2. [Population, Sample, Instance, Feature](#2-population-sample-instance-feature)
3. [Scale Types (the exam's favourite classify-this task)](#3-scale-types)
4. [Frequencies and Histograms](#4-frequencies-and-histograms)
5. [Simpson's Paradox](#5-simpsons-paradox)
6. [Measures of Location: Mean, Median, Mode](#6-measures-of-location)
7. [Quantiles and Boxplots](#7-quantiles-and-boxplots)
8. [Measures of Dispersion: Range, MAD, Variance, SD](#8-measures-of-dispersion)
9. [The n vs n−1 Question (a real slide inconsistency)](#9-the-n-vs-n1-question)
10. [Mind the Sample: Sampling Bias](#10-mind-the-sample-sampling-bias)
11. [Summary and Cross-Wire Moments](#11-summary-and-cross-wire-moments)

---

## 1. What Statistics Is (and the three kinds)

**[Source: SaD L02, slides 3–11]**

Working definition (Leser): **learn characteristics of a potentially infinite set of "objects," and use those characteristics to *analyze* or to *predict*.** "Objects" = inhabitants, measurements over time, sales, students…; we study **features** of them (age, income, temperature, …). "Characteristics" = a few summarizing numbers (mean, median, mode, variance, histogram) that let us make statements about all values. "Learn" = compute those from a **sample**, subject to sampling requirements (ideally random) and a confidence question.

**Three branches (slide 11) — know the distinction:**

| Branch | Question | Scope | Includes |
|---|---|---|---|
| **Descriptive** (deskriptiv) | Summarize *this* sample concisely | the sample only | measures, error-finding, comparing samples |
| **Inductive / inferential** (induktiv) | Infer properties of the *population* | the whole universe | probability theory, hypothesis testing, supervised ML |
| **Exploratory** (explorativ) | Find "interesting" structure | sets, open-ended | hypothesis generation, data mining, unsupervised learning |

**L02 is almost entirely *descriptive*.** Inference starts at L09. Leser's provocation (slide 3): *"Is machine learning a subfield of statistics?"* — left open; the ML half (L11–L15) is the course's answer.

---

## 2. Population, Sample, Instance, Feature

**[Source: SaD L02, slides 10–12]**

The formal vocabulary (memorize — it underpins every later definition):

- **Population** U (*Grundgesamtheit*) — the set of all objects we want to study.
- **Instance** u ∈ U — one object.
- **Sample** U′ ⊆ U (*Stichprobe*) — a subset we actually observe. n = |U′|.
- **Feature** (*Merkmal / Variable*) — the attribute of an object we study, written **u.f** (value of feature f on object u).

**Two remarks that matter for the exam:**

1. |U| may be **infinite**, or just too large to be practical (83M Germans, all future measurements). We work with U′ because U is too large / expensive / private (slide 10).
2. **The precise definition of U fixes the scope of every inference.** "All students" vs "all male Monobachelor Informatik students at HU in the 6th semester with ≥100 ECTS" are different universes → different conclusions (slide 12).

---

## 3. Scale Types

**[Source: SaD L02, slides 13–15]** — *this is a classic Klausur "classify each feature" task.*

A univariate sample is one feature (1-D); multivariate is a vector of features. Each feature has a **scale type (Skalenniveau):**

| Scale | Ordered? | Values | Example | Aggregations that make sense |
|---|---|---|---|---|
| **Nominal** | no (only =/≠) | discrete, finite, unordered | flower colour, student name | counts, mode |
| **Ordinal** | yes (ranking) | discrete, finite, totally ordered | semester, exam grade, "sehr/mittel/wenig" | + median, quantiles |
| **Discrete** | yes | finite or countable (1:1 to ℤ) | number of children | + everything quantitative |
| **Continuous** | yes | infinite, totally ordered | price, height, time | + mean, variance, ratios |

**The two super-categories (slide 15):**

- **Quantitative** = discrete + continuous. "Natural"/measured values; **sums, means, ratios make sense.**
- **Qualitative** = nominal + ordinal. Human-assigned/"artificial"; **aggregation is meaningless** ("mean of two colours"?). Ordinal can be *compared* (1.0 < 2.0); nominal only for *equality* (green vs blue has no order).

**Discretization (slide 15):** mapping continuous → discrete (grades 1.0–1.3 → "very good"; **rounding is discretization**). This is the reverse direction of "binning" a histogram (§4) and reappears as feature engineering in the ML half.

> **Worked slide-14 example.** "Passed? (ja/nein)" = **nominal**; "Interest? (sehr/mittel/wenig)" = **ordinal**; "Year? (2019/2020)" = **discrete** (Leser tags it discrete — countable/ordered but not a measured continuum); "Time? (125/150/180 min)" = **continuous**. The reflex: *unordered → nominal; ordered categories → ordinal; counts → discrete; measured on a continuum → continuous.*

---

## 4. Frequencies and Histograms

**[Source: SaD L02, slides 16–18]**

For a univariate sample U′ with n = |U′| and V = set of unique values:

- **Absolute frequency** of value v: h(v) = |{u ∈ U′ : u.f = v}| — how many times v occurs.
- **Relative frequency**: f(v) = h(v)/n — the fraction. (Σ f(v) = 1.)

**Problem:** V is often huge with tiny frequencies → summarize by **classifying (binning)** values into k classes. A **classification** is a function c: V → {1,…,k} assigning each value to a bin by cut-points k₀ < k₁ < … The **histogram** is the distribution of class frequencies.

**Choosing bin borders (slide 17):**

- **Equi-width** — all intervals the same length (popular default).
- **Equi-depth** — borders chosen so each bin holds (almost) equal frequency (popular in databases).

The choice of k and border strategy changes the histogram's shape — a first taste of "the summary depends on your choices" (the L01 theme).

---

## 5. Simpson's Paradox

**[Source: SaD L02, slides 19–20]** — *a favourite "explain this" exam question.*

**The phenomenon:** an aggregate ratio can *reverse* the per-group ratios. Leser's exam-pass example:

| | Female — Pass | Fail | % fail | Male — Pass | Fail | % fail |
|---|---|---|---|---|---|---|
| **Day 1** | 1 | 0 | **0%** | 7 | 1 | **12.5%** |
| **Day 2** | 2 | 1 | **33%** | 1 | 1 | **50%** |
| **All** | 3 | 1 | **25%** | 8 | 2 | **20%** |

**On each day, males fail more often** (12.5% > 0%, 50% > 33%). **But overall, females fail more** (25% > 20%).

**Why (slide 20):** the group sizes ("the n's") differ wildly, so relative frequencies **cannot be aggregated by adding**. Males have a large *easy* Day-1 sample (8 people, mostly passing) that dominates their overall rate, while females are spread thin across both days. The lesson: **never aggregate rates without weighting by counts** — a confounder (here, the day) can flip the story. Connects to §10 (confounders in sampling) and the L01 base-rate lesson.

---

## 6. Measures of Location

**[Source: SaD L02, slides 22–23, 26–27]**

Let U′ = {x₁,…,xₙ}, quantitative feature; U″ = the values sorted ascending.

**Mean (arithmetic):**
$$\bar{x} = \frac{1}{n}\sum_{i=1}^{n} x_i$$

**Median** (0.5-quantile):
$$\tilde{x} = \begin{cases} U''[\tfrac{n+1}{2}] & n \text{ odd}\\[4pt] \tfrac{1}{2}\big(U''[\tfrac{n}{2}] + U''[\tfrac{n}{2}+1]\big) & n \text{ even}\end{cases}$$

**Mode** (*Modalwert*): the value with the highest (relative) frequency, mode(U′) = argmaxₖ f(k). A distribution is **unimodal** if its histogram has one peak, else **multimodal**.

**Properties to state on the exam (slide 23):**

- The mean of a discrete feature can be an **impossible value** (average grade 2.66).
- **Mean and median say nothing about spread** — `mean(20,20,20,20,20,30,40,20+…)` can equal a very different-looking set's mean (§8 exists precisely to fix this).
- **Mean is outlier-sensitive; median is robust.** *Verified example:* mean(20,21,19,20,18,22,20,21,**19**) = 20 but mean(…,**135**) = 32.9, while **both medians = 20**.
- **Exactly 50%** of values lie below the median (not true of the mean).
- **Median works for ordinal features; the mean does not** (you can't average "sehr/mittel/wenig"). Mode works even for **nominal**.
- Mode/median are **robust to outliers**; report the three most frequent values for a nominal summary.

---

## 7. Quantiles and Boxplots

**[Source: SaD L02, slides 25–26]**

**p-quantile** (0 ≤ p ≤ 1): the value x̃ₚ such that a fraction p of the sample is smaller. So the 0.3-quantile has 30% of values below it.

- median = **0.5-quantile**; min = 0-quantile; max = 1-quantile.
- The **quartiles** are the 0.25- and 0.75-quantiles; the **IQR** (interquartile range) = Q₀.₇₅ − Q₀.₂₅.

**Boxplot (box-and-whisker):** the five-number summary — box from Q₀.₂₅ to Q₀.₇₅ with the median line inside; whiskers to min/max (or to a whisker limit, with points beyond drawn as **outliers**). It's a **robustness-first visual**: built from quantiles, so outliers don't distort the box. **Violin plot (slide 26):** a boxplot fused with an estimated probability density — shows *shape* (e.g. bimodality) a boxplot hides.

---

## 8. Measures of Dispersion

**[Source: SaD L02, slides 29–31]**

Location alone is blind to spread (slide 29 shows two 20-value samples with similar centre but ranges [5,17] vs [5,23] and very different density). The spread measures (*Streumaße*):

**Range:** range(v) = |max − min|. Simple, but maximally outlier-sensitive.

**Mean absolute deviation (MAD):** average absolute distance to the mean:
$$\text{mad}(v) = \frac{1}{n-1}\sum_{i=1}^{n} |x_i - \bar{x}|$$

**Variance and standard deviation** (the ones to *memorize* — MAD you don't):
$$s^2 = \frac{1}{n-1}\sum_{i=1}^{n}(x_i-\bar{x})^2, \qquad s = \sqrt{s^2}$$

**Variance coefficient** (scale-free spread): v(v) = s / x̄ — lets you compare dispersion across features on different scales (connects to standardization, L08).

**Intuition & properties (slide 31):**

- Variance/SD ≈ the "average distance of a value from the mean." SD is in the *same units* as the data; variance is in squared units.
- **Variance punishes large deviations more** (squares them); MAD scales punishment linearly. → variance is far more outlier-sensitive.
- Useful for **unimodal** distributions, much less meaningful for multimodal ones.
- "Sample variance" is properly the **empirical variance** (likewise empirical mean) — the sample estimate, to distinguish it from the population's true variance (§9).

> **Worked slide-31 numbers (verified).** The two slide-29 samples give (using ÷n, see §9): Data set 1 → variance **8.99**, SD **3.00**; Data set 2 → variance **30.86**, SD **5.56**. Same ballpark centre, very different spread — exactly the point that location measures miss.

---

## 9. The n vs n−1 Question

**[Source: SaD L02, slide 30 (formula) vs slide 31 (numbers); resolved in L09]** — ⚠️ *a genuine inconsistency in the deck; know both.*

Slide 30 **defines** the sample variance with the **1/(n−1)** divisor (with the note "*For a sample, we divide by (n−1) → Slides set 09*"). But the **slide-31 example numbers are computed with 1/n** (the population formula): with ÷(n−1) they would be 9.46 and 32.48, not the printed 8.99 and 30.86.

**What to do on the exam:** use the divisor the task gives you. The default *empirical/sample* variance in this course is **÷(n−1)** (slide 30's definition). The reason — **Bessel's correction**: dividing by n−1 makes s² an **unbiased estimator** of the population variance σ² (dividing by n underestimates it, because the deviations are taken from the sample mean, which is itself fitted to the sample). The full justification is **L09 (estimation: unbiasedness)**. Just don't be thrown that the two slides disagree — flag which divisor you're using.

| divisor | name | use |
|---|---|---|
| **1/n** | population / uncorrected variance | when you have the whole population, or are told to |
| **1/(n−1)** | empirical / sample variance (Bessel) | default for a *sample* — unbiased estimate of σ² |

---

## 10. Mind the Sample: Sampling Bias

**[Source: SaD L02, slides 33–38]**

We extrapolate sample measures to the population — so a **non-representative sample poisons every inference.** Random sampling is the simple ideal, but "good" sampling is hard.

- **Stratified sampling (slide 33):** fix known **confounders** and preserve their ratios (e.g. male/female, smoker/non-smoker). The *Nationale Kohorte (NaKo)*: 200,000 randomly selected Germans. Web surveys are "Infotainment" (Schnell 2023) — self-selected, not representative.
- **Case 1 — male/female mammal size (Tombak et al. 2024, slide 34–36):** the Darwinian "males are larger" narrative came from a **species bias** — researchers studied "interesting" species (primates, ungulates, raptors), but the most numerous mammal groups are rodents and bats. **Bias-corrected sampling (male/female *within the same species*, weighted by how many species) → no significant difference.** Confounder = species.
- **Case 2 — "no birds in northern St. Louis" (Carlen et al. 2024, slide 37–38):** citizen-science observations showed animals almost only in the south. North and south are equally dense with equal parks — but the reporting *populations* differ (demographic differences in willingness/means to participate). The "signal" was **sampling bias**, not biology.

**Takeaway:** before trusting any measure, ask *how was the sample drawn, and what confounder could it encode?* This is the descriptive-side version of the inference caution that dominates L09–L10.

**Last words — "models" (slide 39):** a set of derived measures is a **model** of the data — an encoded assumption about its structure, ranging from "a single mean" to a million-parameter autoencoder. More complex models should reconstruct the data more tightly. ("Model" is data-science vocabulary; classical statistics says it less.) This is the on-ramp to L11's ML lifecycle.

---

## 11. Summary and Cross-Wire Moments

### 11.1 Key takeaways

- **Vocabulary:** population U ⊇ sample U′, instance u, feature u.f — and U's definition scopes every inference.
- **Scale type** decides which measures are legal: nominal → mode only; ordinal → + median/quantiles; quantitative → + mean/variance.
- **Location:** mean (sensitive), median (robust, = 0.5-quantile), mode (works for nominal). Report median for skewed data.
- **Dispersion:** range, MAD, and the two to memorize — **variance s² and SD s** (÷(n−1) by default; variance punishes outliers via squaring).
- **Two traps:** **Simpson's paradox** (never add rates without weighting) and **sampling bias** (confounders make a sample lie).

### 11.2 Cross-wires

1. **L01 → L02:** L01's mean/median/mode/histogram/robustness were the informal preview; L02 gives the **formal definitions, scale types, and the variance machinery**. Same **Block N1** exam cluster.
2. **L02 variance → L06 (Random Variables):** the empirical mean/variance here become **E[X] and Var(X)**; the ÷(n−1) story is completed by **L09 (unbiased estimators)**.
3. **L02 variance coefficient → L08 (Normal / z-scores):** standardization z = (x − x̄)/s is exactly "centre and scale by SD"; feature scaling in the ML half (AML L02 §6) is the same operation per column.
4. **L02 scale types → L11–L15 (ML):** nominal/ordinal/continuous drive **encoding** (one-hot, ordinal) and which distance/algorithm applies (k-NN, trees) — see SaD L11 Reference §4.
5. **L02 Simpson / sampling bias → L10 (testing) & L03 (correlation):** confounders are why "correlation ≠ causation" and why controlled/stratified designs matter.

### 11.3 What's next

- **L03 (Correlation & Regression):** covariance, Pearson r, the regression line, MLR — see the **Regression Bridge** (`Plans/ML/foundations/reference/Regression_SaD-AML-ISLP_Bridge.md`), which is the authoritative doc for L03.

---

*Document version 1.0 — KW 28 (Jul 2026). Numerics verified programmatically: dataset variances 8.99/30.86 (÷n) vs 9.46/32.48 (÷(n−1)); outlier example means 20 vs 32.9, medians 20/20; Simpson counts (F 25% vs M 20% overall; M worse each day).*
*Supports Block N1. SaD steps remain F.* in Chat1.*
