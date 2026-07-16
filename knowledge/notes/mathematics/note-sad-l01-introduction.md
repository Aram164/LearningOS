---
id: note-sad-l01-introduction
type: note
title: "SaD Lecture 01 — Ultimate Reference: Describing Data, the Confusion Matrix & Bayes"
created: "2026-07-11"
role: reference
state: evolving
authorship: mixed
concepts: [concept-descriptive-statistics, concept-classification-metrics]
sources: [source-sad-ss26-lectures, source-teschl-mathe-informatiker, source-kroese-dsml]
contexts: [workspace-m2-exam-prep]
---

> **Migration note (2026-07-17, Stage 2):** body preserved verbatim from
> `Plans/Math/sad/SaD/notes/lect01 introduction/SaD_L01_Ultimate_Reference.md` (legacy tree).

# SaD Lecture 01 — Ultimate Reference: Describing Data, the Confusion Matrix & Bayes

*Synthesized from: SaD L01 (Leser, HU SoSe 2026) `Lecture-slides/01_introduction.pdf` (42 slides) + Fahrmeir Ch 2 (descriptive) + Blitzstein Ch 2 / OpenIntro Ch 3 (conditioning & Bayes) + Kroese §7.2 (metrics). Cross-wired to the AML L02 / SaD L11 evaluation toolkit and SaD L04 (probability).*
*Created: KW 28 (Jul 2026) — first of the per-lecture SaD units (built on request; extends the "no-unit for 01–02" default in `SaD-Module-Overview.md`).*

> **⚠️ Source correction (from the slide deck itself).** L01 slide 40 names the **primary statistics text as Teschl & Teschl, *Mathematik für Informatiker* (Springer, 2007)** and the ML text as **Kelleher, Mac Namee & D'Arcy, *ML for Predictive Data Analytics* (2015)** — *not* Fahrmeir, which the crosswalk had assumed as "the course book." Fahrmeir is still an excellent notation-matched German reference and stays useful; but the officially-cited stats book is Teschl & Teschl. Flagged in the crosswalk. Verify against the Moodle literature list (Moodle key on slide 40: `Recall26`).

---

## Table of Contents

1. [What This Lecture Is](#1-what-this-lecture-is)
2. [Describing a Data Set: Mean, Median, Mode](#2-describing-a-data-set-mean-median-mode)
3. [Robustness and Outliers](#3-robustness-and-outliers)
4. [From Samples to Distributions](#4-from-samples-to-distributions)
5. [Be Careful With Intuition: The Medical Test](#5-be-careful-with-intuition-the-medical-test)
6. [The Confusion Matrix: TP / FP / FN / TN](#6-the-confusion-matrix-tp--fp--fn--tn)
7. [Precision and Recall (and the whole naming zoo)](#7-precision-and-recall-and-the-whole-naming-zoo)
8. [The Bayes Approach — Deriving Slide 24](#8-the-bayes-approach--deriving-slide-24)
9. [Why This Matters: The Oncology Case Study](#9-why-this-matters-the-oncology-case-study)
10. [Course Logistics & Exam](#10-course-logistics--exam)
11. [Summary and Cross-Wire Moments](#11-summary-and-cross-wire-moments)

---

## 1. What This Lecture Is

**[Source: SaD L01, slides 1–2, 35–38]**

L01 is a *motivational* lecture, not a technical one. It has two jobs:

1. **Show that "describing data" is already full of judgment calls.** Even the simplest question — "how long do students take for a Bachelor?" — has several defensible answers (mean, median, mode), and each tells a different story to a different audience (slides 3–8).
2. **Show that raw intuition about probability is unreliable**, using the classic medical-test example, and introduce the two tools that fix it: the **confusion matrix** (counting) and **Bayes' theorem** (probability) (slides 11–24).

Everything technical here is revisited rigorously later: descriptive measures in **L02** (Basic Concepts), probability and Bayes in **L04**, evaluation metrics in **L11** (Data Science Intro). So treat L01 as the map, not the territory — but the two worked examples (20 students; the medical test) are exactly the kind of thing that shows up on the Klausur descriptive/probability clusters (**Block N1 / N2**).

**The course's own roadmap (slide 37–38)** — useful as your mental table of contents for the whole module:

> sample/mean/variance → correlation & regression (MLR) → probability & Naïve Bayes → combinatorics → random variables, Chebyshev, LLN → discrete distributions → continuous/Normal/CLT → point & interval estimation → hypothesis testing → data-science/ML lifecycle → trees & random forests → k-NN → Naïve Bayes revisited → (deep) neural networks.

---

## 2. Describing a Data Set: Mean, Median, Mode

**[Source: SaD L01, slides 3–6]**

The running example: 20 students' Bachelor durations (semesters). *Mock-up data.*

```
11  6  8  5 17 11  9  9 12  7 10  8  7  8  9 16  8  7  7  7
```

**Sorted** (do this first, always — median and mode fall out of it):

```
5  6  7  7  7  7  7  8  8  8  8  9  9  9 10 11 11 12 16 17
```

### 2.1 The three "centers"

| Measure | German | Definition | Value here | Answers the question |
|---|---|---|---|---|
| **Mean** (Mittelwert) | arithmetisches Mittel | x̄ = (1/n) Σ xᵢ | **9.1** | "What's the total/average load?" |
| **Median** | Median | middle value of the sorted list (avg of the two middle values if n even) | **8** | "What's the typical middle case?" |
| **Mode** (Modus / Modalwert) | Modalwert | the most frequent value | **7** | "What's the single most likely value?" |

**Arithmetic (verified):** sum = 182, n = 20 → mean = 182/20 = **9.1**. With n = 20 (even), the median is the average of the 10th and 11th sorted values = (8 + 8)/2 = **8**. The value 7 occurs 5 times (more than any other) → mode = **7**.

### 2.2 Why three different answers, and who each is "for" (slides 4–6)

- **Mean = 9.1.** Good for *aggregate* reasoning: total tutoring volume = 9.1 × 20 = 182 student-semesters ("maybe we need more professors?"). But *"will you study 9.1 semesters?"* — no one studies 9.1 semesters; the mean need not be an attainable value.
- **Median = 8.** "If you're an average student, your length is in the *middle* of all lengths." Robust, interpretable as a typical case.
- **Mode = 7.** "Most students finish in 7 semesters" — the value with the **highest a-priori probability** (think of a 20-sided die weighted by the histogram). Best single bet for *one* new student.

**The takeaway L01 is selling:** "the average" is ambiguous. Always ask *which* average and *for what purpose.* This recurs as the lecture's closing warning (slide 41): most bad statistics is not fraud but **biased analysis and overconfident interpretation**.

### 2.3 The histogram (slide 6)

Counting frequencies gives the histogram (this *is* the empirical distribution):

| value | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 16 | 17 |
|---|---|---|---|---|---|---|---|---|---|---|
| count | 1 | 1 | **5** | 4 | 3 | 1 | 2 | 1 | 1 | 1 |

(Counts sum to 20.) The mode is just the tallest bar. The histogram is the bridge from "a list of numbers" to "a distribution" (§4), and to the *a-priori probability* idea that becomes L04.

---

## 3. Robustness and Outliers

**[Source: SaD L01, slide 7]**

"Why should I resemble *exactly* these 20 students? I'm not a genius (forget 5 semesters) and I'll work hard (forget 16–17)." → motivation for **outlier removal**.

**Top/bottom-k trimming with k = 1:** drop the single smallest (5) and single largest (17):

```
6  7  7  7  7  7  8  8  8  8  9  9  9 10 11 11 12 16   (n = 18)
```

Recompute (verified): **mean = 8.9** (160/18 = 8.889), **median = 8**, **mode = 7**.

**The key lesson — robustness:**

> The **mean is *not* robust** to outliers (one extreme value drags it). The **median and mode *are* robust** (they barely move).

Here trimming moved the mean 9.1 → 8.9 but left median and mode unchanged. This is *the* reason to report the median for skewed data (incomes, durations, response times). Revisited formally in L02 (quantiles, boxplots — the boxplot is a robustness-first summary).

---

## 4. From Samples to Distributions

**[Source: SaD L01, slides 8–10]**

Slides 8–10 pose the deeper question that powers the rest of the course:

- Different samples of 20 students give different mean/median/mode (Bachelor vs. a mislabeled Master sample). **Which 20 students? Why these and not others?**
- "Can we *automatically test* whether two samples come from the same underlying program/distribution?" → this is the seed of **inferential statistics** (L09 estimation, L10 hypothesis testing).
- "How many students must I observe before I can answer?" → **sample size / law of large numbers** (L06) and the **CLT** (L08).
- "The x- and y-axis ranges differ — can I make the data *comparable*?" → **standardization / normalization** (z-scores in L08; feature scaling in the ML half / AML L02).

So L01 quietly names the four pillars of the module: **describe → model with probability → estimate → test.**

---

## 5. Be Careful With Intuition: The Medical Test

**[Source: SaD L01, slides 11–18]**

Setup (slide 12). A test for disease X, with the manufacturer's claims:

- If you **are ill**, P(test positive) = **99%**  → this is the test's **sensitivity / recall**.
- If you are **not ill**, P(test positive) = **10%**  → the **false-positive rate** (so specificity = 90%).
- Base rate: **2%** of the population is ill (from cohort studies).

You test **positive**. What's the probability you're ill? The slide's tempting-but-wrong options: 99%, 90%, 2%, "no idea." The correct answer is **≈ 17%**, and the point of the lecture is that *none* of the intuitive guesses is right — the low base rate dominates.

### The counting solution (slides 13–17) — imagine 100,000 people

Build the table by filling the **margins first, then the interior**:

1. **2% ill** → 2,000 ill, 98,000 healthy (column totals). *(slide 14)*
2. **99% of the ill test positive** → 1,980 TP, 20 FN (the "ill" column). *(slide 15)*
3. **10% of the healthy test positive** → 9,800 FP, 88,200 TN (the "not ill" column). *(slide 16)*
4. **Sum the rows** to get the "positive test" total = 1,980 + 9,800 = 11,780. *(slide 17)*

|  | Ill | Not ill | **Sum** |
|---|---|---|---|
| **Positive test** | 1,980 | 9,800 | **11,780** |
| **Negative test** | 20 | 88,200 | **88,220** |
| **Sum** | 2,000 | 98,000 | **100,000** |

**Read off the answer (slide 18):** of the 11,780 who test positive, only 1,980 are truly ill:

$$P(\text{ill}\mid\text{pos}) = \frac{1{,}980}{11{,}780} \approx 0.168 \approx 17\%$$

**Medical consequence (slide 18):** for a *rare* disease you need an *extremely* good test to trust a single positive result — otherwise the false positives (drawn from the huge healthy majority) swamp the true positives. Fixes: better tests, repeat testing, or independent test procedures.

> **This is base-rate neglect.** The gut says "99% accurate test + positive result ⇒ ~99% ill." Wrong, because the 10% false-positive rate acts on 98,000 healthy people (→ 9,800 false alarms) while the 99% hit rate acts on only 2,000 ill people (→ 1,980 hits). The prior (2%) is doing most of the work. Hold the base rate in view and the "paradox" disappears.

---

## 6. The Confusion Matrix: TP / FP / FN / TN

**[Source: SaD L01, slides 19–20]**

The four cells get names. Rows = what the **test says**; columns = the **truth**.

|  | Ill (truth +) | Not ill (truth −) |
|---|---|---|
| **Positive test (predict +)** | **True Positive (TP)** | **False Positive (FP)** |
| **Negative test (predict −)** | **False Negative (FN)** | **True Negative (TN)** |

- **False negative** = ill but the test missed it (the dangerous miss).
- **False positive** = healthy but flagged (the false alarm).

For our example: TP = 1,980, FP = 9,800, FN = 20, TN = 88,200.

**Why not just report these four numbers? (slide 20)**

1. They depend on **n = 100,000**, which was arbitrary → not comparable across studies.
2. Four numbers is a lot to carry around.
3. For good tests on rare classes, **TN is huge and uninteresting** (here 88,200) — it inflates any accuracy-style number and hides the real behavior.

→ so we aggregate into two scale-free ratios: **precision** and **recall**.

---

## 7. Precision and Recall (and the whole naming zoo)

**[Source: SaD L01, slides 20–22]** · depth: `…/lect11 instance-based/SaD_L11_Reference.md` §8, AML L02 §7.2

### 7.1 The two measures

$$\text{precision} = \frac{TP}{TP+FP} = \frac{1{,}980}{1{,}980+9{,}800} \approx 0.17
\qquad
\text{recall} = \frac{TP}{TP+FN} = \frac{1{,}980}{1{,}980+20} = 0.99$$

- **Precision** — "of everything I *flagged* positive, what fraction is *truly* positive?" Column-free; punishes **false positives**. *(slide 21: "If your test is positive, how likely are you ill?")*
- **Recall** (a.k.a. **sensitivity**, **true-positive rate**) — "of everything that is *truly* positive, what fraction did I *catch*?" Punishes **false negatives**. *(slide 21: "How many of all ill people will this test find?")*

> **⚠️ Slide-wording decode (slide 20) — do NOT carry this to the exam literally.** Leser labels precision as *"Type-1 error – what is wrong from what we see?"* and recall as *"Type-2 error – what did we not see?"*. This is a **loose mnemonic, not the standard definition.** Formally, **Type I error = a false positive** (α, rejecting a true H₀) and **Type II error = a false negative** (β, failing to reject a false H₀) — those are error *probabilities* from hypothesis testing (L10), **not** precision/recall. The *useful* half of the mnemonic: precision is the measure that reacts to **FP** ("what's wrong among what we flagged"), recall is the measure that reacts to **FN** ("what we failed to see"). Keep the intuition, drop the "Type-1/2" labels when you write definitions.

### 7.2 The precision ↔ Bayes bridge (the point of the whole lecture)

Notice precision = 1,980 / 11,780 = **0.17** = exactly the $P(\text{ill}\mid\text{pos})$ from §5. **Precision *is* the posterior** $P(\text{truth}=+ \mid \text{predict}=+)$. And recall = 0.99 = $P(\text{pos}\mid\text{ill})$ = the sensitivity you were *given*. So the confusion-matrix half and the Bayes half of this lecture are computing **the same two numbers from two directions** — this is the unifying idea to lock in.

### 7.3 The naming zoo (slide 22)

Other fields rename the same cell-ratios — and *definitions of identical terms sometimes conflict*, so always check the formula, not the word:

| Measure | Formula | Also called | Value here |
|---|---|---|---|
| Recall | TP/(TP+FN) | sensitivity, true-positive rate, hit rate | 0.99 |
| Specificity | TN/(TN+FP) | true-negative rate | 0.90 |
| Precision | TP/(TP+FP) | positive predictive value (PPV) | 0.17 |
| Fall-out | FP/(FP+TN) | false-positive rate = 1 − specificity | 0.10 |

**Precision and recall are not independent (slide 22):** changing the test/threshold usually improves one and worsens the other (the precision–recall trade-off). The combined single number is the **F-score** (harmonic mean) — defined in **L11 / SaD L11 Reference §8**, not here.

**Where it's used (slide 22):** recommender quality, policy screening (*Rasterfahndung*), population medical screens (*Bevölkerungsscreening*) — anywhere you flag a rare class in a big pool.

---

## 8. The Bayes Approach — Deriving Slide 24

**[Source: SaD L01, slides 23–24]** · depth: Blitzstein Ch 2, OpenIntro Ch 3, SaD L04

The same answer without inventing 100,000 people. Given:

$$p(\text{ill})=0.02,\quad p(\text{healthy})=0.98,\quad p(\text{pos}\mid\text{ill})=0.99,\quad p(\text{pos}\mid\text{healthy})=0.10;\qquad \textbf{seek } p(\text{ill}\mid\text{pos}).$$

### 8.1 Everything comes from one definition

Conditional probability: $p(A\mid B) = \dfrac{p(A\cap B)}{p(B)}$ — "restrict the world to B, ask what fraction also has A." Applied to the same joint event two ways:

$$p(\text{ill}\mid\text{pos})=\frac{p(\text{ill}\cap\text{pos})}{p(\text{pos})},\qquad p(\text{pos}\mid\text{ill})=\frac{p(\text{ill}\cap\text{pos})}{p(\text{ill})}\Rightarrow p(\text{ill}\cap\text{pos})=p(\text{pos}\mid\text{ill})\,p(\text{ill}).$$

Substitute → the **numerator** of Bayes:

$$\boxed{\,p(\text{ill}\mid\text{pos})=\frac{p(\text{pos}\mid\text{ill})\,p(\text{ill})}{p(\text{pos})}\,}$$

### 8.2 The denominator = law of total probability

Every positive test is positive-and-ill *or* positive-and-healthy (the two cells of the "positive" row), so:

$$p(\text{pos})=\underbrace{p(\text{pos}\mid\text{ill})\,p(\text{ill})}_{\text{TP}/N}+\underbrace{p(\text{pos}\mid\text{healthy})\,p(\text{healthy})}_{\text{FP}/N}$$

### 8.3 Plug in (verified)

$$p(\text{ill}\mid\text{pos})=\frac{0.99\cdot 0.02}{0.99\cdot 0.02+0.10\cdot 0.98}=\frac{0.0198}{0.0198+0.098}=\frac{0.0198}{0.1178}\approx 0.17.$$

**Term-by-term, this *is* the table divided by N = 100,000** — and the N cancels top and bottom:

| Bayes term | value | ↔ table cell |
|---|---|---|
| $p(\text{pos}\mid\text{ill})\,p(\text{ill}) = 0.99\cdot0.02$ | 0.0198 | 1,980 TP |
| $p(\text{pos}\mid\text{healthy})\,p(\text{healthy}) = 0.10\cdot0.98$ | 0.098 | 9,800 FP |
| denominator | 0.1178 | 11,780 positives |
| ratio | 0.17 | 1,980 / 11,780 |

**Recognition trigger (carry this forward):** reach for Bayes whenever you can state the *forward* direction $p(\text{evidence}\mid\text{cause})$ (how the world generates data — a test's hit rate) but you've *observed the evidence* and want the *backward* $p(\text{cause}\mid\text{evidence})$. Diagnosis, spam filtering, and the Naïve Bayes classifier (L04, L14) are all this same "flip the conditional" move. When symbols confuse you, fall back to the counting table — it's the same computation with N already cancelled.

---

## 9. Why This Matters: The Oncology Case Study

**[Source: SaD L01, slides 25–34]** — *motivational, not examinable; skim once.*

Leser's own research thread, shown to prove the course's methods are used in real science:

- **Problem (slides 26–27):** classify/grade pancreatic neuroendocrine neoplasms (PanNEN) — rare (5% of pancreatic tumors), subtypes with wildly different prognosis (NEC < 1 yr vs NEN > 10 yr), hard to grade from histology.
- **Data (slide 28):** transcriptomes — each sample → a ~20,000-dimensional gene-expression vector (RNA-Seq). This is your first glimpse of **high-dimensional feature vectors** (the ML half's bread and butter).
- **Idea (slides 29–31):** infer the **cell-type-of-origin** from the mixed bulk signal via **deconvolution** (matrix factorization) — separating a mixture into component fractions + error (`bulk ≈ signature × proportions + ε`).
- **Results (slides 32–34):** **PCA** on cell-type proportions separates tumor classes; a **Random Forest** with **10-fold cross-validation** classifies grading/type (sensitivity ~84–91%, specificity ~90–91%) — *note the precision/recall/sensitivity/specificity and CV vocabulary from §6–7 reappearing*; **Cox regression** relates cell-type fractions to survival. Closing hook: *"but how reliable is 'highly correlated'?"* → correlation, regression, inference (L03, L09–L10).

**The point for you:** every method named here (PCA, Random Forest, cross-validation, regression, the sensitivity/specificity metrics) is a later lecture. The case study is a table of contents in disguise.

---

## 10. Course Logistics & Exam

**[Source: SaD L01, slides 36–40]** — cross-check against `SEMESTER-STATUS.md` (authoritative for dates).

- **Format:** 3 SWS, lectures Tue & Thu 11–13, room 0'115. Slides English, lecture in German; one exercise group German, one English. Exercises (Binger Chen & Filipe Laitenberger) start the following week; **presence + commitment required**, groups, 8 slots. Passing the exercises = **admission** to the exam.
- **Exam (as stated on slide 39, later finalized):** dates "probably 27.7.26 and 6.10.26" — ✅ **confirmed in the semester brain: the combined M2 (SaD + Analysis) Klausur is Mo 27.07.26, 12:00–15:00**; 2. Termin Fr 09.10. Three variants exist: full **Analysis + SDS = 150 min**; **"SDS für Wechsler"** (Analysis already passed) = 75 min SDS only; **"Analysis für Wechsler"** = 75 min Analysis only.
- **Books (slide 40):** primary = **Teschl & Teschl, *Mathematik für Informatiker*** (stats) + **Kelleher et al.** (ML); further = Sachs & Hedderich *Angewandte Statistik*, Goodfellow et al. *Deep Learning*, Bishop *PRML*. Moodle key: **`Recall26`**.
- ⚠️ **Action (from Open Loop #1):** confirm you're registered for M2 (1.-PZ Anmeldung closed 02.07); AML-Rücktritt by 15.07 if taking AML at 2. Termin.

---

## 11. Summary and Cross-Wire Moments

### 11.1 Key takeaways

- **"The average" is ambiguous.** Mean (not robust), median (robust), mode (most likely) answer different questions. Report the median for skewed data.
- **The confusion matrix** names the four outcomes; **precision = TP/(TP+FP)**, **recall = TP/(TP+FN)**. Accuracy hides behavior when a class is rare (TN dominates).
- **Base-rate neglect** is the L01 headline: a 99%-sensitive test on a 2%-prevalence disease still gives only **17%** post-positive probability.
- **Precision = the Bayes posterior** $p(\text{ill}\mid\text{pos})$; **recall = sensitivity** $p(\text{pos}\mid\text{ill})$ — the two halves of the lecture are the same numbers from opposite directions.
- **Bayes = the counting table with N cancelled.** When confused, imagine a population and count.

### 11.2 Cross-wires

1. **L01 descriptive → L02 Basic Concepts:** mean/median/mode/histogram here become x̄, s², quantiles, boxplots (the formal, robustness-aware versions). Same **Block N1** exam cluster.
2. **L01 Bayes → L04 Probability & Naïve Bayes:** slide 24 is the informal version of L04's axioms → conditional probability → Bayes → the **Naïve Bayes classifier**; extended again in **L14** (Laplace smoothing, Gaussian NB).
3. **L01 confusion matrix / precision-recall → L11 Data Science Intro & the eval toolkit:** F-score, micro vs macro averaging, ROC live in **`…/lect11 instance-based/SaD_L11_Reference.md` §8** and **AML L02 §7**. L01 is where the vocabulary is born.
4. **L01 "same distribution?" (slides 8–10) → L09/L10:** the seed of estimation and hypothesis testing; "how many samples?" → LLN (L06) and CLT (L08).
5. **L01 case study → L03, L11, L12:** PCA, Random Forest + 10-fold CV, Cox/linear regression, correlation — a preview of the ML half and the regression bridge.

### 11.3 What's next

- **L02 (Basic Concepts):** population vs sample, x̄, s², quantiles, boxplots — the formal descriptive layer. (Next unit to build.)
- **L04 (Probability):** the rigorous home of §5/§8; do the Bayes intuition materials in the Mini Plan first.

---

*Document version 1.0 — KW 28 (Jul 2026). All worked numerics (mean 9.1, trimmed 8.9, median 8, mode 7; TP/FP/FN/TN 1,980/9,800/20/88,200; precision 0.168, recall 0.99, specificity 0.90; Bayes 0.168) verified programmatically.*
*Plan step: supports Block N1 (descriptive) + N2 (probability/Bayes). SaD steps remain F.* in Chat1.*
