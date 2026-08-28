# Statistics and Data Science — extensive learning plan (2026-08-27)

This is the learner-facing overview of the complete SaD lecture sequence. The fifteen 2026 lecture decks remain the scope authority. Every other item is an explained option: current exercises are required practice; books, videos, other university courses, implementations, prior-year decks and solved exams are selected by the angle they provide. Availability is never confused with learner selection.

## Plan architecture

- **15 lecture units**, each with one ordered stage per authored knowledge node.
- **66 source families** and **306 lecture-specific source routes** in the complete menu.
- **1082 concept-stage resource appearances**, up from 827; the increase is the material that existed in the source map but was absent from the lecture maps.
- Every route below includes an exact locator, a one-line angle, and the longer judgment: what it gives, what it assumes, and where it stops.
- `required-now` means current course scope/practice. `helpful-now` is a selectable second angle. `reference-only` is prior-year or advanced material that should be opened only for a recorded gap.

## Sequence at a glance

| Lecture | Topic | Knowledge stages | Source routes | Stage resource rows |
|---|---|---:|---:|---:|
| `L01` | SaD Lecture 01 — Introduction | 7 | 11 | 30 |
| `L02` | SaD Lecture 02 — Basic Concepts | 7 | 12 | 49 |
| `L03` | SaD Lecture 03 — Correlation & Regression | 7 | 25 | 70 |
| `L04` | SaD Lecture 04 — Probability & Naïve Bayes | 7 | 25 | 92 |
| `L05` | SaD Lecture 05 — Combinatorics | 7 | 19 | 64 |
| `L06` | SaD Lecture 06 — Random Variables, Expectation & Variance | 7 | 25 | 99 |
| `L07` | SaD Lecture 07 — Discrete Distributions | 6 | 23 | 102 |
| `L08` | SaD Lecture 08 — Normal Distribution, CLT & Likelihood | 7 | 24 | 85 |
| `L09` | SaD Lecture 09 — Point & Interval Estimation | 7 | 18 | 70 |
| `L10` | SaD Lecture 10 — Statistical Hypothesis Testing | 8 | 21 | 85 |
| `L11` | SaD Lecture 11 — Data Science & Machine Learning Workflow | 7 | 22 | 58 |
| `L12` | SaD Lecture 12 — Tree-Based Learning & Ensembles | 7 | 16 | 62 |
| `L13` | SaD Lecture 13 — Similarity-Based Learning | 7 | 13 | 47 |
| `L14` | SaD Lecture 14 — Probability-Based Learning | 7 | 20 | 54 |
| `L15` | SaD Lecture 15 — Neural Networks | 8 | 32 | 115 |

## How to use a lecture map

1. Read the current deck for the stage and reproduce the stage objective without notes.
2. Attempt the exact current sheet item before reading the matching UE solution.
3. Choose one second explanation whose angle matches the actual problem: intuition, derivation, implementation, extra drill, or deeper reference.
4. Use solved external exams late and timed. A prior-year deck can clarify a terse slide but never expands current scope.
5. Record misses against the stage; do not run every optional book or full university course end to end.

## L01 — SaD Lecture 01 — Introduction

**Lecture purpose.** The lecture begins with one data question and shows why every numerical answer depends on the population, sample, representation, loss, and decision being asked for.

**Concept progression.**

1. **One dataset, several legitimate questions** — A statistic is useful only relative to a question; totals, typical cases, likely cases, and decisions can require different summaries of the same observations.
2. **Mean, median, mode, and robustness** — Central-tendency summaries answer different questions, while outliers move the mean much more strongly than the median or mode. Builds on: One dataset, several legitimate questions.
3. **Frequencies, histograms, and empirical distributions** — Counts become relative frequencies and distributions, making samples of different sizes and ranges comparable without pretending that the sample is the population. Builds on: Mean, median, mode, and robustness.
4. **Samples, populations, and context** — A result changes with the sampled group; the same-looking numbers can describe different populations, and comparison requires attention to selection and context. Builds on: Frequencies, histograms, and empirical distributions.
5. **Confusion matrices and classification metrics** — True/false positives and negatives support accuracy, precision, recall, sensitivity, and specificity; the useful metric depends on the error costs and class prevalence. Builds on: One dataset, several legitimate questions.
6. **Base rates and Bayes by counting** — Medical-test and classification examples expose why a high sensitivity need not imply a high posterior probability when the positive class is rare. Builds on: Confusion matrices and classification metrics.
7. **From description to inference and prediction** — Descriptive statistics summarize observed data; probability models uncertainty; inference reasons about populations; data science and machine learning use the resulting structure to predict. Builds on: Samples, populations, and context, Base rates and Bayes by counting.

**Complete source menu.**

### 1. Current scope and current practice

- **SaD — Statistik und Datenanalyse, lecture slides (SoSe 2026) — Current L01 introduction deck**
  - Use: `course-material` · depth `course-aligned` · scope `current`
  - Exact locator: `lecture-slides/01_introduction.pdf, 42 slides`
  - Covers: One dataset, several legitimate questions, Mean, median, mode, and robustness, Frequencies, histograms, and empirical distributions, Samples, populations, and context, Confusion matrices and classification metrics, Base rates and Bayes by counting, From description to inference and prediction
  - Angle: The scope authority for L01 and the only place the course's own framing of the module appears.
  - Why this angle matters: Everything in L01 is demonstrated on a single study-duration dataset, which is the deck's pedagogical device and also its limitation: each idea appears once, in one context, and is not revisited. Treat it as the definition of what is in scope and the source of the notation, and use the supporting routes on this stage for the second and third encounters the deck does not provide. The classification-metrics and base-rate slides at the end preview L04 and L11 rather than belonging to L01's own material.
- **SaD exercise sheets UE1–UE7 (SoSe 2026) — Blatt 1, Aufgabe 1 — data summaries in the opening dataset**
  - Use: `exercise` · depth `practice` · scope `current`
  - Exact locator: `exercise-slides/Blatt1.pdf, pp. 1-2, Aufgabe 1`
  - Covers: One dataset, several legitimate questions, Mean, median, mode, and robustness, Samples, populations, and context
  - Angle: Turns the introductory dataset into an unaided frequency, location and interpretation task.
  - Why this angle matters: This is a current assessed sheet: attempt it before opening the tutorial solution. It is scope evidence because it shows the chair's own wording, data size and expected amount of working; it is not a replacement for the lecture derivation.
  - Local target: `material://source-sad-ss26-lectures/exercise-slides/Blatt1.pdf`
- **SaD exercise sheets UE1–UE7 (SoSe 2026) — UE2, slides 5-18 — feature and data-type walkthrough**
  - Use: `exercise` · depth `practice` · scope `current`
  - Exact locator: `exercise-slides/UE2.pdf, slides 5-18`
  - Covers: One dataset, several legitimate questions, Samples, populations, and context
  - Angle: Shows how the course translates a raw table into features before any model is chosen.
  - Why this angle matters: This is the current worked tutorial for the named task. Use it after an unaided attempt: its value is the course's calculation order and notation, while reading it first would turn an exam-relevant retrieval task into passive recognition.
  - Local target: `material://source-sad-ss26-lectures/exercise-slides/UE2.pdf`

### 2. Books and independent derivations

- **Statistik: Der Weg zur Datenanalyse (9. Aufl.) — Fahrmeir Chapter 2 — descriptive-statistics reference**
  - Use: `book` · depth `derivation` · scope `complementary`
  - Exact locator: `Ch 2 §2.1 Verteilungen und ihre Darstellungen, pdf pp. 47-66; §2.2 Beschreibung von Verteilungen, pdf pp. 67-90`
  - Covers: Mean, median, mode, and robustness, Frequencies, histograms, and empirical distributions, Samples, populations, and context
  - Angle: The German textbook vocabulary for exactly the descriptive tools L01 demonstrates, so the exam words and the lecture words match.
  - Why this angle matters: L01 shows mean/median/mode and a histogram on one study-duration dataset and moves on; Fahrmeir gives the same objects their examinable German names and definitions — Häufigkeitsverteilung, Lagemaße, Streuungsmaße, Quantil, Boxplot — with a worked example per definition. Read it for naming and notation, not for new ideas: everything here is L01 content stated more slowly and in the language the Klausur is written in. It assumes no probability at all, so it is safe this early.
  - Local target: `material://source-fahrmeir-statistik/statistik.pdf`
- **OpenIntro Statistics (4th ed.) — OpenIntro Chapters 1–2 — accessible data summaries**
  - Use: `book` · depth `orientation` · scope `complementary`
  - Exact locator: `Ch 1 introduction to data, pdf pp. 7-38 (case study: stents to prevent strokes p. 9); Ch 2 §2.1 examining numerical data, pdf pp. 40-59; §2.3 case study: malaria vaccine, pdf pp. 70-78`
  - Covers: One dataset, several legitimate questions, Mean, median, mode, and robustness, Frequencies, histograms, and empirical distributions, Samples, populations, and context
  - Angle: Opens with a real study whose result reverses on closer reading — the argument for why descriptive statistics is not decoration.
  - Why this angle matters: The stent case study runs through the whole first chapter: a treatment that looks beneficial at 30 days and harmful at 365, with the data shown both ways. It is the most persuasive answer available to 'why does L01 spend a lecture on summaries', and it costs twenty minutes. The writing is aimed at first-year undergraduates with no calculus, so this is the gentlest route on the shelf; that is a feature at L01 and a limitation later. Free, open licence, and the same book carries L02-L10, so the notation stays constant across the whole statistics half of the course.
  - Local target: `material://source-openintro-statistics/openintro.pdf`

### 3. Visual, implementation and additional practice

- **Arbeitsbuch Statistik (Fahrmeir et al.) — Arbeitsbuch Chapter 2 — descriptive warm-ups**
  - Use: `exercise` · depth `practice` · scope `complementary`
  - Exact locator: `Ch 2 Aufgaben pdf pp. 12-30, Lösungen pdf pp. 31-56 (start with the Häufigkeits- and Lagemaß items)`
  - Covers: Mean, median, mode, and robustness, Frequencies, histograms, and empirical distributions
  - Angle: Solved German drill for the descriptive measures L01 introduces, with every step written out rather than a final answer.
  - Why this angle matters: The Arbeitsbuch is the companion to the Fahrmeir textbook and shares its numbering exactly, so an exercise here always has a chapter of theory behind it at the same number. Its solutions are full derivations, which makes it the right place to check calculation habits — divisor choice, rounding, how a median is reported for even n — rather than to test yourself. For untimed self-testing prefer the SaD Übungen; for timed self-testing use the Klausur bank.
  - Local target: `material://source-fahrmeir-arbeitsbuch/arbeitsbuch.pdf`
- **A Modern Introduction to Probability and Statistics — Dekking — descriptive review and answer-backed exercises**
  - Use: `exercise` · depth `practice` · scope `complementary`
  - Exact locator: `Ch 16 Exploratory data analysis: numerical summaries, pdf pp. 238-250 (centre p. 238; variability p. 240; empirical quantiles and IQR p. 241; boxplot p. 243; exercises p. 247); Ch 15 histograms pdf pp. 216-218; full solutions App D pdf pp. 443-471`
  - Covers: Mean, median, mode, and robustness, Frequencies, histograms, and empirical distributions, Samples, populations, and context
  - Angle: Descriptive statistics presented after probability, so mean and variance arrive as estimates of distribution features rather than as summary formulas.
  - Why this angle matters: Dekking deliberately places EDA in Ch 15-16, two thirds of the way through the book, and the consequence is a different reading of the same formulas L01 shows on slide one: the sample mean is introduced as an estimator of E[X], the sample variance as an estimator of Var(X). Coming back to this after L09 is one of the most useful re-reads in the module, because it retroactively explains why L01's descriptive tools were worth defining. On a first pass through L01, use it only for the exercises — the framing will not land yet.
  - Local target: `material://source-dekking-mips/dekking.pdf`
- **StatQuest with Josh Starmer (YouTube) — StatQuest — confusion matrix, sensitivity, and specificity**
  - Use: `video` · depth `orientation` · scope `complementary`
  - Exact locator: `'The Confusion Matrix, Clearly Explained' and 'Sensitivity and Specificity, Clearly Explained' (≈10 min each)`
  - Covers: Confusion matrices and classification metrics
  - Angle: Twenty minutes that fix the confusion matrix orientation problem — which axis is truth, which is prediction — for good.
  - Why this angle matters: Nearly every mistake with precision, recall, sensitivity and specificity is a transposition error made under time pressure, not a conceptual failure. StatQuest's fix is a colour-coded table built up cell by cell, repeated until the layout is memorable. That is worth more for L01 than any written treatment, because the written ones assume you will not transpose it. Stop after these two; the channel's ROC video belongs to L11.
- **Kurzes Tutorium Statistik (Bärtl, YouTube) — Kurzes Tutorium Statistik — Lagemaße und Streuung**
  - Use: `video` · depth `orientation` · scope `complementary`
  - Exact locator: `Die Videos 'Lagemaße' und 'Streuungsmaße' (je ≈10 Min)`
  - Covers: Mean, median, mode, and robustness
  - Angle: German-language vocabulary for L01's descriptive measures — the words the Klausur will actually use.
  - Why this angle matters: The lecture is delivered in English but examined in a German programme, and the exam vocabulary (Lagemaß, Streuungsmaß, Merkmalsausprägung, Häufigkeit) is not always introduced on the slides. These videos are short and use the terms consistently, which is the cheapest way to close that gap. Content is at Abitur/first-semester level — use it for language, not for depth.
- **3Blue1Brown — videos on Bayes' theorem (playlist) — 3Blue1Brown — Bayes' theorem and the medical-test paradox**
  - Use: `video` · depth `intuition` · scope `complementary`
  - Exact locator: `'Bayes theorem, the geometry of changing beliefs' (≈15 min); 'The medical test paradox, and redesigning Bayes' rule' (≈21 min)`
  - Covers: Confusion matrices and classification metrics, Base rates and Bayes by counting
  - Angle: Turns the base-rate problem into an area picture, so the answer is seen before it is computed.
  - Why this angle matters: L01 introduces base rates through a medical-test example and asserts the counterintuitive answer. The first video builds a rectangle whose areas are the four cells of the joint distribution, and the posterior becomes a visible ratio of two areas — at which point the answer stops being surprising. The second video is the medical-test case itself and argues for thinking in odds and Bayes factors, which is a genuinely different representation from the lecture's. Watch before the algebra in L04, not after.
  - Web target: https://www.youtube.com/playlist?list=PLk4N6AFvLWe3xCHuOs0siWp0q2F43Cslh

### 4. University courses, prior-year, exam and advanced reference

- **FAU Erlangen Statistik-Klausur WS14/15 (mit Lösungen) — FAU pp. 4 and 22 — origin/base-rate table with solution**
  - Use: `exercise` · depth `practice` · scope `complementary`
  - Exact locator: `FAU-Erlangen_Statistik-Klausur_WS14-15_mit-Loesungen.pdf, p. 4 Aufgabe 1(3)-(4), solution p. 22`
  - Covers: Confusion matrices and classification metrics, Base rates and Bayes by counting
  - Angle: An authentic German base-rate item showing the amount of working that receives marks.
  - Why this angle matters: The orange-origin table asks for posterior/origin reasoning in the form that makes sensitivity-versus-posterior mistakes visible. It is a calibration item after L01, not a new explanation of Bayes.
  - Local target: `material://source-fau-klausur-ws1415/FAU-Erlangen_Statistik-Klausur_WS14-15_mit-Loesungen.pdf`

## L02 — SaD Lecture 02 — Basic Concepts

**Lecture purpose.** The lecture establishes the descriptive-statistics language and the measurement constraints that determine which summaries and comparisons are mathematically meaningful.

**Concept progression.**

1. **Population, sample, object, feature, and realization** — Statistics observes feature values on sampled objects to learn about a larger population; each term identifies a different part of that inference problem.
2. **Feature types and measurement scales** — Nominal, ordinal, interval, and ratio scales determine which ordering, distance, averaging, and arithmetic operations are legitimate. Builds on: Population, sample, object, feature, and realization.
3. **Frequency distributions and histograms** — Absolute, relative, and cumulative frequencies organize raw observations; bin choices and scale can change the visual claim a histogram appears to make. Builds on: Population, sample, object, feature, and realization.
4. **Location, quantiles, and boxplots** — Mean, median, mode, quantiles, and five-number summaries describe where data lie and support a compact comparison of skew and outliers. Builds on: Feature types and measurement scales, Frequency distributions and histograms.
5. **Range, variance, standard deviation, and divisors** — Dispersion measures complement location; population variance divides by n, while the familiar sample estimator uses n-1 for a later inferential reason. Builds on: Location, quantiles, and boxplots.
6. **Aggregation and Simpson's paradox** — A trend can reverse after groups are combined because group sizes and hidden variables alter the weighting; stratification is part of interpretation, not cosmetic reporting. Builds on: Frequency distributions and histograms.
7. **Representative samples and sampling bias** — Randomness, coverage, nonresponse, survivorship, and convenience sampling decide whether a descriptive result can support a population claim. Builds on: Population, sample, object, feature, and realization, Aggregation and Simpson's paradox.

**Complete source menu.**

### 1. Current scope and current practice

- **SaD — Statistik und Datenanalyse, lecture slides (SoSe 2026) — Current L02 basic-concepts deck**
  - Use: `course-material` · depth `course-aligned` · scope `current`
  - Exact locator: `lecture-slides/02_basics.pdf, 39 slides`
  - Covers: Population, sample, object, feature, and realization, Feature types and measurement scales, Frequency distributions and histograms, Location, quantiles, and boxplots, Range, variance, standard deviation, and divisors, Aggregation and Simpson's paradox, Representative samples and sampling bias
  - Angle: Fixes the exact vocabulary and calculation conventions the rest of the course and the exam use.
  - Why this angle matters: This is the deck to check whenever a definition is in dispute — including the variance divisor, which differs between textbooks and is settled here for this course. The Simpson's-paradox and sampling-bias slides at the end are conceptually the most demanding part and get the least time; OpenIntro §1.3 and §2.2 are the elaboration. Nothing in L02 requires probability, so it can be revised independently of everything after L03.
- **SaD exercise sheets UE1–UE7 (SoSe 2026) — Blatt 1, Aufgabe 1 — frequencies, median, mean and spread**
  - Use: `exercise` · depth `practice` · scope `current`
  - Exact locator: `exercise-slides/Blatt1.pdf, pp. 1-2, Aufgabe 1`
  - Covers: Feature types and measurement scales, Frequency distributions and histograms, Location, quantiles, and boxplots, Range, variance, standard deviation, and divisors
  - Angle: A compact by-hand check that the descriptive vocabulary can be turned into numbers.
  - Why this angle matters: This is a current assessed sheet: attempt it before opening the tutorial solution. It is scope evidence because it shows the chair's own wording, data size and expected amount of working; it is not a replacement for the lecture derivation.
  - Local target: `material://source-sad-ss26-lectures/exercise-slides/Blatt1.pdf`
- **SaD exercise sheets UE1–UE7 (SoSe 2026) — UE2, slides 5-18 — feature types and descriptive conventions**
  - Use: `exercise` · depth `practice` · scope `current`
  - Exact locator: `exercise-slides/UE2.pdf, slides 5-18`
  - Covers: Population, sample, object, feature, and realization, Feature types and measurement scales, Frequency distributions and histograms, Representative samples and sampling bias
  - Angle: Supplies the lecturer's worked distinctions between feature types and the summaries allowed for each scale.
  - Why this angle matters: This is the current worked tutorial for the named task. Use it after an unaided attempt: its value is the course's calculation order and notation, while reading it first would turn an exam-relevant retrieval task into passive recognition.
  - Local target: `material://source-sad-ss26-lectures/exercise-slides/UE2.pdf`

### 2. Books and independent derivations

- **Statistik: Der Weg zur Datenanalyse (9. Aufl.) — Fahrmeir Chapter 2 — univariate descriptive statistics**
  - Use: `book` · depth `derivation` · scope `complementary`
  - Exact locator: `Ch 2 complete, pdf pp. 46-125 (§2.1 Darstellungen p. 47; §2.2 Lage und Streuung p. 67; §2.3 Konzentrationsmaße p. 91; §2.4 Dichtekurven und Normalverteilung p. 101; Aufgaben p. 123)`
  - Covers: Feature types and measurement scales, Frequency distributions and histograms, Location, quantiles, and boxplots, Range, variance, standard deviation, and divisors
  - Angle: The definitional authority for L02: every scale, frequency, location and dispersion measure defined once, in German, with the divisor conventions spelled out.
  - Why this angle matters: This is the chapter L02 is compressing. It settles the two things the deck leaves implicit: which measures are admissible on which Skalenniveau (nominal/ordinal/metrisch, §2.1-2.2), and the n versus n-1 divisor question for the variance, which Fahrmeir states as a definition rather than leaving it to inference. §2.3 (Lorenzkurve, Gini) is beyond SaD scope — skip it unless a concentration measure appears in an exercise. §2.4 previews the Normal density as a smoothed histogram, which is the picture L08 later assumes you already have.
  - Local target: `material://source-fahrmeir-statistik/statistik.pdf`
- **OpenIntro Statistics (4th ed.) — OpenIntro Chapters 1–2 — descriptive foundations**
  - Use: `book` · depth `orientation` · scope `complementary`
  - Exact locator: `Ch 1 §1.2 data basics, pdf pp. 14-21; §1.3 sampling principles and strategies, pdf pp. 21-30; Ch 2 §2.1 examining numerical data, pdf pp. 40-59; §2.2 considering categorical data, pdf pp. 60-69`
  - Covers: Population, sample, object, feature, and realization, Feature types and measurement scales, Frequency distributions and histograms, Location, quantiles, and boxplots, Range, variance, standard deviation, and divisors, Representative samples and sampling bias
  - Angle: Spends ten pages on sampling design and bias, which L02 compresses into two slides and the exam still asks about.
  - Why this angle matters: §1.3 names and distinguishes the sampling schemes — simple random, stratified, cluster, convenience — and works through what each does to representativeness, plus non-response and voluntary-response bias. L02's sampling node is one slide; the exam question 'why is this sample not representative' expects the vocabulary from this section. §2.2 is also the only treatment here that takes categorical data seriously as its own case with contingency tables, which is where Simpson's paradox lives.
  - Local target: `material://source-openintro-statistics/openintro.pdf`

### 3. Visual, implementation and additional practice

- **Arbeitsbuch Statistik (Fahrmeir et al.) — Arbeitsbuch Chapter 2 — descriptive-statistics drills**
  - Use: `exercise` · depth `practice` · scope `complementary`
  - Exact locator: `Ch 2 Aufgaben pdf pp. 12-30, Lösungen pdf pp. 31-56`
  - Covers: Frequency distributions and histograms, Location, quantiles, and boxplots, Range, variance, standard deviation, and divisors
  - Angle: The largest solved bank on the shelf for scales, frequencies, location and dispersion — roughly 45 worked items.
  - Why this angle matters: L02 is the lecture where the exam risk is arithmetic and convention rather than understanding: which measure is defined on which scale, how a class-grouped mean is computed, whether the variance divides by n or n-1 in this course. Volume is what fixes those, and this chapter has more solved items on exactly that material than anything else available. Work them with the solutions covered; the value is in the many small conventions, not in any single problem.
  - Local target: `material://source-fahrmeir-arbeitsbuch/arbeitsbuch.pdf`
- **A Modern Introduction to Probability and Statistics — Dekking — descriptive-statistics exercise bank**
  - Use: `exercise` · depth `practice` · scope `complementary`
  - Exact locator: `Ch 15 §§15.2-15.5 histograms, kernel density, empirical distribution function, scatterplot, pdf pp. 216-231; Ch 16 §§16.1-16.4, pdf pp. 238-244; exercises pdf pp. 233-237 and pp. 247-250`
  - Covers: Frequency distributions and histograms, Location, quantiles, and boxplots, Range, variance, standard deviation, and divisors, Representative samples and sampling bias
  - Angle: Adds the empirical distribution function, which is the object that makes 'the histogram approximates the distribution' precise.
  - Why this angle matters: L02 draws histograms and moves on. §15.4 introduces the empirical distribution function Fn and states that it converges to the true F — the formal content of the intuition that a bigger sample gives a better picture. That single idea is what later makes the bootstrap in L09 comprehensible rather than magical, so reading it now pays twice. §15.3 on kernel density estimates is outside SaD scope; skim it as context for why smoothed histograms exist.
  - Local target: `material://source-dekking-mips/dekking.pdf`
- **zedstatistics (Justin Zeltzer, YouTube channel) — zedstatistics — descriptive statistics and data types**
  - Use: `video` · depth `intuition` · scope `complementary`
  - Exact locator: `The descriptive-statistics videos (measures of centre, measures of spread, types of data), ≈10-15 min each`
  - Covers: Feature types and measurement scales, Location, quantiles, and boxplots, Range, variance, standard deviation, and divisors
  - Angle: Explains what each summary measure hides, not only what it reports — the reason a lecture needs more than one of them.
  - Why this angle matters: Zeltzer's recurring move is to show two visibly different datasets with the same mean, or the same standard deviation, and ask what the summary failed to capture. That framing answers the question L02 provokes but does not address: why so many measures for one dataset. Useful before the Fahrmeir drill, because it gives the definitions a purpose.
- **jbstatistics (YouTube) — jbstatistics — data types, histograms, center, and spread**
  - Use: `video` · depth `orientation` · scope `complementary`
  - Exact locator: `'Types of Data'; 'Frequency Distributions and Histograms'; 'Mean, Median and Mode'; 'Variance and Standard Deviation' (≈8 min each)`
  - Covers: Feature types and measurement scales, Frequency distributions and histograms, Location, quantiles, and boxplots, Range, variance, standard deviation, and divisors
  - Angle: Chalk-talk pace with every calculation written out — closest in style to a German Vorlesung of the same material.
  - Why this angle matters: Where StatQuest is animated and mnemonic, jbstatistics is a lecturer working through definitions and examples at writing speed. For L02, where the content is definitional and the risk is convention rather than intuition, that register is the better fit: the divisor question and the grouped-data mean are both worked explicitly. Playlists are ordered to be watched in sequence.
- **Kurzes Tutorium Statistik (Bärtl, YouTube) — Kurzes Tutorium Statistik — Grundbegriffe and Skalenniveaus**
  - Use: `video` · depth `orientation` · scope `complementary`
  - Exact locator: `'Statistische Grundbegriffe'; 'Skalenniveaus'; 'Lagemaße' und 'Streuungsmaße'`
  - Covers: Population, sample, object, feature, and realization, Feature types and measurement scales, Location, quantiles, and boxplots, Range, variance, standard deviation, and divisors
  - Angle: The Skalenniveau hierarchy in German, with the admissible-operations rule stated for each level.
  - Why this angle matters: Which statistics are permissible on nominal, ordinal, intervall- and verhältnisskalierte data is a standard German exam question and is a vocabulary question as much as a conceptual one. These videos give the hierarchy and the rule in the exact terms used, in under half an hour total.

### 4. University courses, prior-year, exam and advanced reference

- **FAU Erlangen Statistik-Klausur WS14/15 (mit Lösungen) — FAU pp. 3 and 22 — descriptive-statistics block with solution**
  - Use: `exercise` · depth `practice` · scope `complementary`
  - Exact locator: `FAU-Erlangen_Statistik-Klausur_WS14-15_mit-Loesungen.pdf, p. 3 Aufgabe 1(1), solution p. 22`
  - Covers: Frequency distributions and histograms, Location, quantiles, and boxplots, Range, variance, standard deviation, and divisors
  - Angle: Shows exactly how briefly median, quartiles, range, mean and skewness are reported in a real German solution.
  - Why this angle matters: This is useful for timing and answer economy rather than conceptual depth. Work the orange table cold, then compare only the form and amount of the published answer.
  - Local target: `material://source-fau-klausur-ws1415/FAU-Erlangen_Statistik-Klausur_WS14-15_mit-Loesungen.pdf`
- **SaD external German Klausur bank (local) — HS Harz pp. 2-5 — descriptive statistics under exam timing**
  - Use: `exercise` · depth `practice` · scope `complementary`
  - Exact locator: `HS-Harz_Statistik-I_Probeklausur_mit-Loesungen.pdf, pp. 2-5, Aufgabenteile I-III`
  - Covers: Frequency distributions and histograms, Location, quantiles, and boxplots, Range, variance, standard deviation, and divisors
  - Angle: A short German paper with boxplot, mean, median and dispersion computations plus worked answers.
  - Why this angle matters: The four-page descriptive block is mechanically close to L02 and small enough to time. Its value is answer economy and German exam phrasing; it does not cover sampling design or Simpson's paradox.
  - Local target: `material://source-sad-klausuren-extern/HS-Harz_Statistik-I_Probeklausur_mit-Loesungen.pdf`

## L03 — SaD Lecture 03 — Correlation & Regression

**Lecture purpose.** The lecture moves from describing paired variation to fitting a predictive linear relationship, while separating computational association from causal explanation.

**Concept progression.**

1. **Paired data and scatterplots** — Correlation is defined on corresponding measurements; scatterplots reveal direction, form, outliers, and nonlinearity before any coefficient is calculated.
2. **Covariance and Pearson correlation** — Covariance measures joint signed deviation, while Pearson normalization produces a scale-free coefficient in [-1,1] for linear association. Builds on: Paired data and scatterplots.
3. **Correlation is not causation** — A numerical association can reflect confounding, reverse causality, selection, coincidence, or a real mechanism; computation alone cannot choose among these explanations. Builds on: Covariance and Pearson correlation.
4. **Simple linear regression and least squares** — A line predicts one variable from another; residuals measure errors, and minimizing squared error determines slope and intercept. Builds on: Covariance and Pearson correlation.
5. **Multivariate linear regression and the design matrix** — Several predictors become columns of a matrix, one parameter vector produces predictions, and the normal equation expresses the closed-form least-squares solution. Builds on: Simple linear regression and least squares.
6. **Gradient descent as an alternative optimizer** — Iterative updates follow the negative loss gradient; learning rate, initialization, scaling, and convergence determine whether the fitted parameters are reached reliably. Builds on: Simple linear regression and least squares.
7. **Scaling, coefficient interpretation, and model limits** — Feature units change coefficient magnitudes and optimization geometry; weights require context, and linear fit quality does not by itself establish generalization or causality. Builds on: Multivariate linear regression and the design matrix, Gradient descent as an alternative optimizer.

**Complete source menu.**

### 1. Current scope and current practice

- **SaD — Statistik und Datenanalyse, lecture slides (SoSe 2026) — Current L03 correlation and regression deck**
  - Use: `course-material` · depth `course-aligned` · scope `current`
  - Exact locator: `lecture-slides/03_correlation_regression.pdf, 48 slides`
  - Covers: Paired data and scatterplots, Covariance and Pearson correlation, Correlation is not causation, Simple linear regression and least squares, Multivariate linear regression and the design matrix, Gradient descent as an alternative optimizer, Scaling, coefficient interpretation, and model limits
  - Angle: The course's own path from a scatterplot to the normal equation and gradient descent, in one sitting.
  - Why this angle matters: The deck covers an unusual amount of ground for one lecture: descriptive correlation, simple least squares, the multivariate design matrix, the closed-form normal equation and an iterative optimiser. The compression is real, and the two places it shows are the matrix notation (assumed) and gradient descent (stated, not run). Géron Ch 4 and 3Blue1Brown's linear-algebra episodes are the routes that repair those two specifically. Everything here is examinable.
- **SaD exercise sheets UE1–UE7 (SoSe 2026) — Blatt 1, Aufgabe 2 — correlation and simple regression**
  - Use: `exercise` · depth `practice` · scope `current`
  - Exact locator: `exercise-slides/Blatt1.pdf, p. 3, Aufgabe 2`
  - Covers: Paired data and scatterplots, Covariance and Pearson correlation, Correlation is not causation, Simple linear regression and least squares
  - Angle: Asks for both the coefficient and its interpretation on a real price pair, the closest current exam-style L03 task.
  - Why this angle matters: This is a current assessed sheet: attempt it before opening the tutorial solution. It is scope evidence because it shows the chair's own wording, data size and expected amount of working; it is not a replacement for the lecture derivation.
  - Local target: `material://source-sad-ss26-lectures/exercise-slides/Blatt1.pdf`
- **SaD exercise sheets UE1–UE7 (SoSe 2026) — Blatt 1, Aufgabe 3 — multivariate regression**
  - Use: `exercise` · depth `practice` · scope `current`
  - Exact locator: `exercise-slides/Blatt1.pdf, p. 4, Aufgabe 3`
  - Covers: Multivariate linear regression and the design matrix, Scaling, coefficient interpretation, and model limits
  - Angle: Moves from the scalar line to a real feature matrix and prediction problem.
  - Why this angle matters: This is a current assessed sheet: attempt it before opening the tutorial solution. It is scope evidence because it shows the chair's own wording, data size and expected amount of working; it is not a replacement for the lecture derivation.
  - Local target: `material://source-sad-ss26-lectures/exercise-slides/Blatt1.pdf`
- **SaD exercise sheets UE1–UE7 (SoSe 2026) — UE2, slides 20-28 — covariance and Pearson correlation**
  - Use: `exercise` · depth `practice` · scope `current`
  - Exact locator: `exercise-slides/UE2.pdf, slides 20-28`
  - Covers: Paired data and scatterplots, Covariance and Pearson correlation, Correlation is not causation
  - Angle: Works the covariance-to-correlation normalization one line at a time in course notation.
  - Why this angle matters: This is the current worked tutorial for the named task. Use it after an unaided attempt: its value is the course's calculation order and notation, while reading it first would turn an exam-relevant retrieval task into passive recognition.
  - Local target: `material://source-sad-ss26-lectures/exercise-slides/UE2.pdf`
- **SaD exercise sheets UE1–UE7 (SoSe 2026) — UE2, slides 30-35 — regression prediction and RMSE**
  - Use: `exercise` · depth `practice` · scope `current`
  - Exact locator: `exercise-slides/UE2.pdf, slides 30-35`
  - Covers: Simple linear regression and least squares, Multivariate linear regression and the design matrix, Scaling, coefficient interpretation, and model limits
  - Angle: Connects fitted coefficients to predictions and an explicit residual error measure.
  - Why this angle matters: This is the current worked tutorial for the named task. Use it after an unaided attempt: its value is the course's calculation order and notation, while reading it first would turn an exam-relevant retrieval task into passive recognition.
  - Local target: `material://source-sad-ss26-lectures/exercise-slides/UE2.pdf`
- **SaD exercise sheets UE1–UE7 (SoSe 2026) — UE3, slides 5-14 — Blatt 1 regression solutions**
  - Use: `exercise` · depth `practice` · scope `current`
  - Exact locator: `exercise-slides/UE3.pdf, slides 5-14`
  - Covers: Covariance and Pearson correlation, Correlation is not causation, Simple linear regression and least squares, Multivariate linear regression and the design matrix
  - Angle: Provides the official solution path for the two regression questions after the independent attempt.
  - Why this angle matters: This is the current worked tutorial for the named task. Use it after an unaided attempt: its value is the course's calculation order and notation, while reading it first would turn an exam-relevant retrieval task into passive recognition.
  - Local target: `material://source-sad-ss26-lectures/exercise-slides/UE3.pdf`
- **SaD exercise sheets UE1–UE7 (SoSe 2026) — Blatt 2, Aufgabe 3 — gradient descent and loss curve**
  - Use: `exercise` · depth `practice` · scope `current`
  - Exact locator: `exercise-slides/blatt-02.pdf, p. 3, Aufgabe 3(a)-(b)`
  - Covers: Gradient descent as an alternative optimizer, Scaling, coefficient interpretation, and model limits
  - Angle: The only current assignment that makes the optimizer and normalization executable rather than symbolic.
  - Why this angle matters: This is a current assessed sheet: attempt it before opening the tutorial solution. It is scope evidence because it shows the chair's own wording, data size and expected amount of working; it is not a replacement for the lecture derivation.
  - Local target: `material://source-sad-ss26-lectures/exercise-slides/blatt-02.pdf`
- **SaD exercise sheets UE1–UE7 (SoSe 2026) — UE3, slides 40-45 — gradient descent and normalization walkthrough**
  - Use: `exercise` · depth `practice` · scope `current`
  - Exact locator: `exercise-slides/UE3.pdf, slides 40-45`
  - Covers: Gradient descent as an alternative optimizer, Scaling, coefficient interpretation, and model limits
  - Angle: Explains why scaling changes the descent geometry and how the MSE curve diagnoses the update.
  - Why this angle matters: This is the current worked tutorial for the named task. Use it after an unaided attempt: its value is the course's calculation order and notation, while reading it first would turn an exam-relevant retrieval task into passive recognition.
  - Local target: `material://source-sad-ss26-lectures/exercise-slides/UE3.pdf`

### 2. Books and independent derivations

- **Statistik: Der Weg zur Datenanalyse (9. Aufl.) — Fahrmeir Chapter 3 — multivariate description and regression**
  - Use: `book` · depth `derivation` · scope `complementary`
  - Exact locator: `Ch 3 §3.4 Zusammenhangsmaße bei metrischen Merkmalen, pdf pp. 151-163; §3.5 Korrelation und Kausalität, pdf pp. 164-167; §3.6 Regression, pdf pp. 168-182; Aufgaben pdf pp. 189-192`
  - Covers: Paired data and scatterplots, Covariance and Pearson correlation, Correlation is not causation, Simple linear regression and least squares
  - Angle: Correlation and least squares derived from the descriptive side only — no random variables, no inference, which is exactly L03's standpoint.
  - Why this angle matters: Most books introduce regression after probability and immediately talk about errors as random variables. Fahrmeir Ch 3 is still in the descriptive half of the book, so the Kleinste-Quadrate line is derived as a purely geometric fit to a scatterplot — the same standpoint as L03, which also has no probability yet. §3.5 is the short, sharp treatment of Scheinkorrelation and confounding that the lecture states in one slide. It does NOT cover multivariate regression in matrix form or gradient descent; for those parts of L03 use ISLP §3.2 and Géron Ch 4.
  - Local target: `material://source-fahrmeir-statistik/statistik.pdf`
- **Fundamentals of Machine Learning for Predictive Data Analytics — Kelleher Chapter 7 — error surfaces and gradient descent**
  - Use: `book` · depth `intuition` · scope `complementary`
  - Exact locator: `Ch 7 Error-based Learning, pdf pp. 351-424 (the error surface and gradient-descent sections)`
  - Covers: Gradient descent as an alternative optimizer, Scaling, coefficient interpretation, and model limits
  - Angle: Draws the error surface as a landscape and walks gradient descent across it, which is the picture L03's optimiser slides assume.
  - Why this angle matters: Kelleher's treatment of least squares is unusual in starting from the shape of the error function over the parameter space — a bowl, with the fitted line at its bottom — before any update rule. Once that surface is in view, gradient descent is obviously a descent and the learning rate is obviously a step size, which is the intuition L03 states in words. The chapter also covers multivariable weights consistently with the deck's notation.
  - Local target: `material://source-kelleher-fmlpda/kelleher.pdf`
- **Eli Bendersky — Derivation of the Normal Equation for Linear Regression — Bendersky — derivation of the normal equation**
  - Use: `website` · depth `derivation` · scope `complementary`
  - Exact locator: `The complete article 'Derivation of the Normal Equation for linear regression' (eli.thegreenplace.net), both the calculus and the linear-algebra derivations`
  - Covers: Multivariate linear regression and the design matrix, Simple linear regression and least squares
  - Angle: Derives the same closed-form solution twice — once by calculus, once by projection — which is the connection L03 leaves implicit.
  - Why this angle matters: L03 states the normal equation and moves to gradient descent. This article shows where it comes from: set the gradient of the squared-error objective to zero and solve, then separately, project the target vector onto the column space of the design matrix and get the identical result. Seeing both is what turns the formula from something to memorise into something with two independent justifications. Assumes matrix notation, so read 3Blue1Brown's episodes 1-4 and 9 first if that is shaky.
- **Mathematics for Machine Learning — MML Ch 9 — linear regression from the mathematical side**
  - Use: `book` · depth `derivation` · scope `complementary`
  - Exact locator: `Ch 9 Linear Regression §9.1 problem formulation, §9.2 parameter estimation (maximum likelihood and MAP); read with Ch 5 Vector Calculus §§5.1-5.3 for the gradient notation`
  - Covers: Multivariate linear regression and the design matrix, Gradient descent as an alternative optimizer, Simple linear regression and least squares
  - Angle: Derives least squares as maximum likelihood under Gaussian noise from the start, so L03 and L08 are one derivation rather than two lectures.
  - Why this angle matters: §9.2 does not present squared error as a design choice; it starts from a Gaussian noise model and derives the squared-error objective as the negative log-likelihood. That is the same bridge L08's Gaussian-error slides build, arrived at from the regression side. Reading it after L08 makes the whole regression thread cohere. Ch 5 supplies the vector-calculus notation the derivation uses; free PDF from mml-book.github.io.
- **OpenIntro Statistics (4th ed.) — OpenIntro — correlation and linear regression**
  - Use: `book` · depth `orientation` · scope `complementary`
  - Exact locator: `Ch 8 introduction to linear regression, pdf pp. 303-340 (§8.1 fitting a line, residuals, and correlation p. 305; §8.2 least squares regression p. 317; §8.3 types of outliers p. 328; §8.4 inference for linear regression p. 331)`
  - Covers: Paired data and scatterplots, Covariance and Pearson correlation, Correlation is not causation, Simple linear regression and least squares
  - Angle: Makes residual plots a first-class diagnostic, so a fitted line is something you check rather than something you report.
  - Why this angle matters: §8.1 introduces residuals before it introduces the least-squares criterion, and §8.3 catalogues the ways a single point can dominate a fit — leverage, influence, outliers — with pictures. L03 derives the line and stops; the model-limits node at the end of the lecture is exactly this material, unelaborated. Reading §8.3 is the cheapest protection against the exam question that shows a scatterplot and asks whether the reported r is trustworthy. §8.4's inference is L10 material — leave it until then.
  - Local target: `material://source-openintro-statistics/openintro.pdf`
- **Ng — Machine Learning (Coursera) — Ng — linear regression and gradient descent lectures**
  - Use: `course` · depth `intuition` · scope `complementary`
  - Exact locator: `Week 1-2: the linear regression with one variable and multiple variables lectures (cost function, gradient descent, learning rate, feature scaling)`
  - Covers: Gradient descent as an alternative optimizer, Scaling, coefficient interpretation, and model limits, Simple linear regression and least squares
  - Angle: Spends a whole lecture on the learning rate alone — too large, too small, and how to tell which you have.
  - Why this angle matters: L03 introduces gradient descent with the update rule and a remark that the step size matters. Ng devotes separate segments to diagnosing a bad learning rate from the cost curve, and to why feature scaling changes how many steps are needed. Those are the two practical facts that make gradient descent usable rather than merely definable, and they are the content of L03's scaling-weights node.

### 3. Visual, implementation and additional practice

- **3Blue1Brown — Essence of Calculus — 3Blue1Brown — what a derivative is, before gradient descent uses one**
  - Use: `video` · depth `intuition` · scope `prerequisite`
  - Exact locator: `Essence of Calculus episodes 2 ('The paradox of the derivative') and 3 ('Derivative formulas through geometry')`
  - Covers: Gradient descent as an alternative optimizer
  - Angle: Restores the derivative as a slope you can see, which gradient descent's update rule silently assumes you still hold.
  - Why this angle matters: L03's optimiser takes a step proportional to the negative derivative, and that rule is only obvious if the derivative is still a slope in your mind rather than a differentiation rule you once memorised. Two episodes restore the picture. Routed as a prerequisite rather than a supplement: if the derivative is solid, skip it entirely.
- **Arbeitsbuch Statistik (Fahrmeir et al.) — Arbeitsbuch Chapter 3 — correlation and regression drills**
  - Use: `exercise` · depth `practice` · scope `complementary`
  - Exact locator: `Ch 3 Aufgaben pdf pp. 57-66, Lösungen pdf pp. 67-82`
  - Covers: Covariance and Pearson correlation, Simple linear regression and least squares
  - Angle: Correlation and regression by hand, including the contingency-table measures the lecture mentions but never drills.
  - Why this angle matters: Computing r and a least-squares line from a small table by hand is a distinct skill from understanding them, and it is the one the Klausur can test under time pressure. These items are sized for that. The chapter also drills the Kontingenztafel association measures from Fahrmeir §3.2, which L03 does not cover but the exam's descriptive half occasionally reaches — treat those as optional unless a past paper shows otherwise.
  - Local target: `material://source-fahrmeir-arbeitsbuch/arbeitsbuch.pdf`
- **Setosa — Ordinary Least Squares Regression (visual explainer) — Setosa — ordinary least squares, interactive**
  - Use: `website` · depth `intuition` · scope `complementary`
  - Exact locator: `The single interactive page 'Ordinary Least Squares Regression: explained visually' (setosa.io) — the residual-square and leverage widgets`
  - Covers: Simple linear regression and least squares, Paired data and scatterplots, Correlation is not causation
  - Angle: Lets you move a point and watch the fitted line respond, which shows leverage and influence in seconds rather than in prose.
  - Why this angle matters: The page draws the squared residuals as actual squares and totals their area, so 'least squares' becomes a visible minimisation rather than a name. Dragging an outlier then shows the line swinging — the leverage effect that OpenIntro §8.3 describes in text and that L03's model-limits node states abstractly. Ten minutes, no installation, and it makes the criterion memorable in a way no derivation does.
- **A Modern Introduction to Probability and Statistics — Dekking — correlation and regression exercises**
  - Use: `exercise` · depth `practice` · scope `complementary`
  - Exact locator: `Ch 10 covariance and correlation, pdf pp. 144-159 (covariance p. 147; correlation coefficient p. 150; exercises p. 153); Ch 22 the method of least squares, pdf pp. 332-343 (§22.3 relation with maximum likelihood p. 338; exercises p. 340); Ch 17 §17.4 the linear regression model, pdf pp. 262-264`
  - Covers: Covariance and Pearson correlation, Correlation is not causation, Simple linear regression and least squares
  - Angle: Contains the derivation L03 does not do: least squares is exactly maximum likelihood when the errors are Normal.
  - Why this angle matters: §22.3 is a two-page proof that minimising the sum of squared residuals and maximising the likelihood under Normal errors are the same optimisation. L03 presents least squares as a reasonable choice and L08 presents MLE separately; this is the join between them, and it answers the question the lecture invites but never asks — why squares and not absolute deviations. Requires L08's likelihood material to read, so this is a return visit, not a first pass. Ch 10 is the probabilistic covariance to set beside L03's descriptive one.
  - Local target: `material://source-dekking-mips/dekking.pdf`
- **StatQuest with Josh Starmer (YouTube) — StatQuest — Pearson correlation, least squares, and gradient descent**
  - Use: `video` · depth `orientation` · scope `complementary`
  - Exact locator: `'Pearson's Correlation, Clearly Explained'; 'Linear Regression, Clearly Explained' (least squares); 'Gradient Descent, Step-by-Step' (≈20 min)`
  - Covers: Covariance and Pearson correlation, Simple linear regression and least squares, Gradient descent as an alternative optimizer
  - Angle: Steps a gradient-descent run through by hand, one iteration at a time, with the numbers on screen.
  - Why this angle matters: L03 introduces gradient descent as an alternative optimiser and shows the update rule. The step-by-step video actually performs the iterations on a two-parameter regression, so the abstract rule becomes a visible sequence of numbers converging. It also shows what a learning rate that is too large does, which is the intuition behind every later discussion of step size. The correlation video is the one to watch if the difference between covariance and correlation is what is unclear.
- **Géron — Hands-On Machine Learning (local) — Geron Ch 4 - the normal equation and gradient descent side by side**
  - Use: `book` · depth `implementation` · scope `complementary`
  - Exact locator: `Chapter 4, pp. 139-180 (closed-form solution p. 139; gradient descent p. 140; normal equation p. 142; learning rate p. 146; feature scaling p. 148)`
  - Covers: Multivariate linear regression and the design matrix, Gradient descent as an alternative optimizer
  - Angle: L03 presents the closed-form normal equation and gradient descent as two routes to the same fit; this chapter runs both on the same data, shows what the learning rate does to convergence and why unscaled features distort the descent path - the two claims the deck makes without demonstration.
  - Why this angle matters: Ch 4 is where L03's two optimisation routes stop being abstract. The closed-form normal equation and gradient descent are implemented on the same data, and the chapter then shows what actually differs between them in practice: the normal equation's cubic cost in the number of features against gradient descent's sensitivity to feature scaling and learning rate. The scaling demonstration on p. 148 is the concrete version of L03's scaling-weights node — two elongated and two circular contour plots, with the descent paths drawn on them.
  - Local target: `material://source-geron-handson/geron.pdf`
- **3Blue1Brown — Essence of Linear Algebra (playlist) — 3Blue1Brown — vectors, dot products, and matrix transformations**
  - Use: `video` · depth `orientation` · scope `complementary`
  - Exact locator: `Essence of Linear Algebra, episodes 1-4 (vectors, linear combinations, linear transformations, matrix multiplication) and episode 9 (dot products)`
  - Covers: Multivariate linear regression and the design matrix, Gradient descent as an alternative optimizer
  - Angle: Makes the design matrix a transformation rather than a table, which is what L03's multivariate notation assumes.
  - Why this angle matters: L03 moves from a single predictor to a design matrix and a normal equation in a few slides, and that jump silently assumes matrix-vector multiplication is a familiar operation with a geometric meaning. These episodes supply exactly that meaning — a matrix as a transformation, multiplication as composition, the dot product as projection. The projection reading of the dot product in episode 9 is what later makes least squares recognisable as an orthogonal projection.

### 4. University courses, prior-year, exam and advanced reference

- **An Introduction to Statistical Learning (Python edition) — ISLP Chapter 3 — statistical regression bridge**
  - Use: `book` · depth `derivation` · scope `complementary`
  - Exact locator: `Ch 3 Linear Regression, pdf pp. 78-143 (§3.1 simple linear regression p. 79; §3.2 multiple linear regression p. 87; §3.3 other considerations p. 98); read alongside the repository's Regression Bridge note §§2, 4 and 7`
  - Covers: Simple linear regression and least squares, Multivariate linear regression and the design matrix, Scaling, coefficient interpretation, and model limits
  - Angle: Adds the inferential layer L03 omits: standard errors, t-statistics and confidence intervals for the fitted coefficients.
  - Why this angle matters: L03 fits a line and stops; ISLP fits the same line and then asks whether the slope is distinguishable from zero. That question is not examinable in L03 — it belongs to L10 — but knowing it exists changes how you read a regression output, and it is the bridge between the module's two halves. §3.3 covers the practical issues (collinearity, non-linearity, outliers) that L03's model-limits node names without elaborating. The Regression Bridge note in this repository already maps which ISLP sections correspond to which SaD slides.
  - Local target: `material://source-islp/islp.pdf`
- **FAU Erlangen Statistik-Klausur WS14/15 (mit Lösungen) — FAU pp. 35 and 48 — covariance/correlation formula completion**
  - Use: `exercise` · depth `practice` · scope `complementary`
  - Exact locator: `FAU-Erlangen_Statistik-Klausur_WS14-15_mit-Loesungen.pdf, p. 35 Aufgabe 2(8), solution p. 48`
  - Covers: Covariance and Pearson correlation
  - Angle: A very short R-formula completion that checks whether covariance is normalized by both variances correctly.
  - Why this angle matters: The former route incorrectly promised a solved compute-and-interpret correlation item. The actual task is narrower: complete Kor=function(Kova,v1,v2). It is retained honestly as formula recall; it does not practise scatterplot interpretation or a regression fit.
  - Local target: `material://source-fau-klausur-ws1415/FAU-Erlangen_Statistik-Klausur_WS14-15_mit-Loesungen.pdf`
- **SaD external German Klausur bank (local) — HS Harz pp. 6-7 — Kendall association and linear regression**
  - Use: `exercise` · depth `practice` · scope `complementary`
  - Exact locator: `HS-Harz_Statistik-I_Probeklausur_mit-Loesungen.pdf, pp. 6-7, Aufgabenteile IV-V`
  - Covers: Paired data and scatterplots, Correlation is not causation, Simple linear regression and least squares
  - Angle: Pairs an association measure with a fitted line and R² interpretation on one dataset.
  - Why this angle matters: This is the strongest external L03 item because the prompt, computation and interpretation are visible together and the solution is printed immediately below. Kendall's tau itself is outside the current lecture; use that part only as an association contrast, then work the linear-regression section in full.
  - Local target: `material://source-sad-klausuren-extern/HS-Harz_Statistik-I_Probeklausur_mit-Loesungen.pdf`
- **SaD external German Klausur bank (local) — University of Cologne pp. 7-8 — multivariate regression interpretation**
  - Use: `solutions` · depth `advanced-reference` · scope `complementary`
  - Exact locator: `Koeln_Statistik-Klausur_Musterloesung.pdf, pp. 7-8, Aufgabe 5(c)-(d)`
  - Covers: Multivariate linear regression and the design matrix, Scaling, coefficient interpretation, and model limits
  - Angle: Shows coefficient interpretation, prediction and an interaction extension in a real multivariate model.
  - Why this angle matters: Parts (c)-(d) are useful L03 transfer: substitute a feature vector, compare a dummy coefficient and propose an interaction term. Parts (a)-(b) use t tests and confidence intervals, which require L10; they are deliberately excluded from the L03 task.
  - Local target: `material://source-sad-klausuren-extern/Koeln_Statistik-Klausur_Musterloesung.pdf`

## L04 — SaD Lecture 04 — Probability & Naïve Bayes

**Lecture purpose.** The lecture formalizes uncertain events and then turns Bayes' law into a classifier, exposing both the strength and the assumptions of probability-based learning.

**Concept progression.**

1. **Human probability judgments and framing** — Equivalent outcomes can trigger different decisions when expressed as gains or losses, motivating a formal calculus instead of unaided intuition.
2. **Random experiments, outcomes, and event spaces** — A sample space contains possible outcomes; events are subsets, and set operations encode the logical structure of compound probability questions.
3. **Probability axioms and derived rules** — Non-negativity, normalization, and additivity generate complement, union, inclusion-exclusion, monotonicity, and bounds. Builds on: Random experiments, outcomes, and event spaces.
4. **Conditional probability and total probability** — Conditioning restricts the reference population; partitions decompose an event into mutually exclusive cases whose weighted probabilities sum to the whole. Builds on: Probability axioms and derived rules.
5. **Bayes' law and posterior reasoning** — Bayes reverses a conditional using likelihoods and prior/base rates, explaining medical-test and classification paradoxes that raw accuracy obscures. Builds on: Conditional probability and total probability.
6. **Independence and conditional independence** — Independent events factorize jointly; conditional independence is a different claim that can hold or fail after a third variable is known. Builds on: Conditional probability and total probability.
7. **Categorical Naive Bayes classifier** — Class priors and per-feature likelihoods produce a posterior score under a conditional-independence assumption; missing combinations and zero counts preview the smoothing problem in L14. Builds on: Bayes' law and posterior reasoning, Independence and conditional independence.

**Complete source menu.**

### 1. Current scope and current practice

- **SaD — Statistik und Datenanalyse, lecture slides (SoSe 2026) — Current L04 probability and Naive Bayes deck**
  - Use: `course-material` · depth `course-aligned` · scope `current`
  - Exact locator: `lecture-slides/04_probability.pdf, 59 slides`
  - Covers: Human probability judgments and framing, Random experiments, outcomes, and event spaces, Probability axioms and derived rules, Conditional probability and total probability, Bayes' law and posterior reasoning, Independence and conditional independence, Categorical Naive Bayes classifier
  - Angle: Controls the probability notation for the whole module, and builds the categorical Naive Bayes classifier that L14 later extends.
  - Why this angle matters: The largest deck in the statistics half and the one with the widest span: framing puzzles, axioms, conditioning, Bayes, independence, then a full classifier. Its one known gap is slide 46, which states Bayes with the total-probability expansion already substituted into the denominator, so the partition step is invisible — Fahrmeir §4.6 supplies it and a repository note records the proof. The Naive Bayes construction at the end has no exact equivalent in any book here; the deck is authoritative for it.
- **SaD exercise sheets UE1–UE7 (SoSe 2026) — Blatt 2, Aufgaben 1-2 — probability, Bayes and Naive Bayes**
  - Use: `exercise` · depth `practice` · scope `current`
  - Exact locator: `exercise-slides/blatt-02.pdf, pp. 1-2, Aufgaben 1-2`
  - Covers: Random experiments, outcomes, and event spaces, Probability axioms and derived rules, Conditional probability and total probability, Bayes' law and posterior reasoning, Independence and conditional independence, Categorical Naive Bayes classifier
  - Angle: Combines finite probability, dependence, Bayes inversion and a small classifier in the current assignment format.
  - Why this angle matters: This is a current assessed sheet: attempt it before opening the tutorial solution. It is scope evidence because it shows the chair's own wording, data size and expected amount of working; it is not a replacement for the lecture derivation.
  - Local target: `material://source-sad-ss26-lectures/exercise-slides/blatt-02.pdf`
- **SaD exercise sheets UE1–UE7 (SoSe 2026) — UE3, slides 15-38 — events, axioms and conditional probability**
  - Use: `exercise` · depth `practice` · scope `current`
  - Exact locator: `exercise-slides/UE3.pdf, slides 15-38`
  - Covers: Random experiments, outcomes, and event spaces, Probability axioms and derived rules, Conditional probability and total probability, Bayes' law and posterior reasoning, Independence and conditional independence
  - Angle: Builds the event algebra and then works the medical-test style base-rate inversion visually.
  - Why this angle matters: This is the current worked tutorial for the named task. Use it after an unaided attempt: its value is the course's calculation order and notation, while reading it first would turn an exam-relevant retrieval task into passive recognition.
  - Local target: `material://source-sad-ss26-lectures/exercise-slides/UE3.pdf`
- **SaD exercise sheets UE1–UE7 (SoSe 2026) — UE4, slides 9-12 — Bayes and Naive Bayes solutions**
  - Use: `exercise` · depth `practice` · scope `current`
  - Exact locator: `exercise-slides/UE4.pdf, slides 9-12`
  - Covers: Conditional probability and total probability, Bayes' law and posterior reasoning, Categorical Naive Bayes classifier
  - Angle: Shows exactly where the conditional-independence assumption enters the two-feature classifier.
  - Why this angle matters: This is the current worked tutorial for the named task. Use it after an unaided attempt: its value is the course's calculation order and notation, while reading it first would turn an exam-relevant retrieval task into passive recognition.
  - Local target: `material://source-sad-ss26-lectures/exercise-slides/UE4.pdf`

### 2. Books and independent derivations

- **Statistik: Der Weg zur Datenanalyse (9. Aufl.) — Fahrmeir Chapter 4 — probability foundations**
  - Use: `book` · depth `derivation` · scope `complementary`
  - Exact locator: `Ch 4 §§4.1-4.2 Wahrscheinlichkeitsbegriff, pdf pp. 194-213; §4.4 Bedingte Wahrscheinlichkeiten, pdf pp. 221-223; §4.5 Unabhängigkeit, pdf pp. 224-227; §4.6 Totale Wahrscheinlichkeit, pdf pp. 228-229; §4.7 Satz von Bayes, pdf pp. 230-234; Aufgaben pdf pp. 239-241`
  - Covers: Random experiments, outcomes, and event spaces, Probability axioms and derived rules, Conditional probability and total probability, Bayes' law and posterior reasoning, Independence and conditional independence
  - Angle: Splits total probability and Bayes into two separately numbered sections, which is the derivation order L04's slide 46 skips.
  - Why this angle matters: The 2026 deck states Bayes with the total-probability expansion already substituted into the denominator, so the step where the partition enters is invisible. Fahrmeir gives §4.6 (Satz von der totalen Wahrscheinlichkeit) its own statement and proof, then derives §4.7 (Bayes) from it, which is the missing half. It also gives the German phrasing of Unabhängigkeit as a product rule rather than as a conditional statement — worth reading because the Klausur can ask for either. Stops before Naive Bayes: the classifier construction is L04's own, and no book on this shelf matches it exactly.
  - Local target: `material://source-fahrmeir-statistik/statistik.pdf`
- **Grinstead & Snell — Introduction to Probability (AMS, open access) — Grinstead & Snell Ch 4 — conditional probability**
  - Use: `book` · depth `course-aligned` · scope `complementary`
  - Exact locator: `Ch 4 Conditional Probability §§4.1-4.3 (discrete conditional probability, continuous conditional probability, paradoxes), with the chapter exercises`
  - Covers: Conditional probability and total probability, Bayes' law and posterior reasoning, Independence and conditional independence
  - Angle: Open-access and legally free to keep, with a paradoxes section that attacks the intuition failures L04 opens on.
  - Why this angle matters: The AMS releases this under a licence that lets you keep and print it, which matters for a text you will return to across three lectures. §4.3 collects the classic conditional-probability paradoxes — Monty Hall, the two-child problem, the prisoner's dilemma — and resolves each by making the conditioning event explicit. That is the same diagnosis L04's framing slides make, worked out at length rather than asserted. The exercises are plentiful and answers to odd-numbered ones are published.
- **Introduction to Probability (2nd ed.) — Blitzstein Chapter 2 — conditioning and Bayes**
  - Use: `book` · depth `intuition` · scope `complementary`
  - Exact locator: `Ch 2 pdf pp. 62-119 (§2.2 definition and intuition p. 63; §2.3 Bayes' rule and the law of total probability p. 69; §2.5 independence of events p. 80; §2.7 conditioning as a problem-solving tool p. 85; §2.8 pitfalls and paradoxes p. 91; exercises §2.11 p. 100)`
  - Covers: Conditional probability and total probability, Bayes' law and posterior reasoning, Independence and conditional independence
  - Angle: Treats conditioning as the primary object — 'conditioning is the soul of statistics' — so Bayes arrives as a way of thinking rather than a formula to memorise.
  - Why this angle matters: The one book here that opens the chapter by arguing conditional probability is the fundamental notion and unconditional probability the special case. That reframing is why §2.7 exists: a section on conditioning as a deliberate problem-solving move, which no other source on this shelf has. §2.8 catalogues the confusion of the inverse and the prosecutor's fallacy — the same base-rate error L04's framing slides open with, but named and dissected. Notation is measure-free and the register is conversational; it is slower than Fahrmeir but far more likely to make the idea stick. 60 exercises, many with published solutions on the book's site.
  - Local target: `material://source-blitzstein-hwang/blitzstein.pdf`
- **Jurafsky & Martin — Speech and Language Processing (3rd ed. draft) — Jurafsky & Martin Ch 4 — naive Bayes for text classification**
  - Use: `book` · depth `course-aligned` · scope `complementary`
  - Exact locator: `Ch 4 'Naive Bayes, Text Classification, and Sentiment' §§4.1-4.3 (the naive Bayes classifier, training, and a worked example)`
  - Covers: Categorical Naive Bayes classifier, Independence and conditional independence
  - Angle: The clearest published account of the exact classifier L04 builds — bag of words, conditional independence, product of counted likelihoods.
  - Why this angle matters: L04's spam classifier has no equivalent in the probability books on this shelf, because they stop at Bayes' rule. This chapter is precisely that construction, written as a textbook chapter with the assumptions named — the bag-of-words assumption and the naive conditional-independence assumption stated separately, which the deck merges. §4.3 works a complete numeric example on a handful of documents. Free draft PDF from Stanford.
- **OpenIntro Statistics (4th ed.) — OpenIntro — probability foundations**
  - Use: `book` · depth `orientation` · scope `complementary`
  - Exact locator: `Ch 3 §3.1 defining probability, pdf pp. 81-94; §3.2 conditional probability, pdf pp. 95-111 (tree diagrams and Bayes' theorem); §3.3 sampling from a small population, pdf pp. 112-114`
  - Covers: Random experiments, outcomes, and event spaces, Conditional probability and total probability, Bayes' law and posterior reasoning, Independence and conditional independence
  - Angle: Runs conditional probability entirely through tree diagrams and contingency tables, so Bayes is arithmetic on a table before it is an equation.
  - Why this angle matters: §3.2 develops the whole of conditioning pictorially: a two-way table, then a tree with branch probabilities, then Bayes as a ratio read off the tree. Only at the end does the algebraic form appear. For a first pass this is the lowest-friction route available, and it matches how German exams pose the question (Vierfeldertafel). It does not cover Naive Bayes and does not do conditional independence carefully — for those parts of L04 use the deck and Kelleher Ch 6.
  - Local target: `material://source-openintro-statistics/openintro.pdf`
- **CS229 Lecture Notes (Stanford) — CS229 §4.2 — Naive Bayes event models**
  - Use: `course-material` · depth `advanced-reference` · scope `complementary`
  - Exact locator: `Main notes §4 Generative Learning algorithms — §4.2 Naive Bayes and §4.2.1 Laplace smoothing`
  - Covers: Categorical Naive Bayes classifier
  - Angle: The compact mathematical statement of the classifier L04 builds informally, in about four pages.
  - Why this angle matters: Where the deck constructs the spam classifier by counting, CS229 writes the generative model, states the conditional-independence assumption formally, and derives the maximum-likelihood parameter estimates. Reading both gives the construction and its justification. The notes are terse and assume comfort with likelihood notation, so this is better after L08 than before it.
  - Local target: `material://source-cs229-notes/cs229-notes.pdf`

### 3. Visual, implementation and additional practice

- **Arbeitsbuch Statistik (Fahrmeir et al.) — Arbeitsbuch Chapter 4 — conditional probability and Bayes**
  - Use: `exercise` · depth `practice` · scope `complementary`
  - Exact locator: `Ch 4 Aufgaben pdf pp. 83-88, Lösungen pdf pp. 89-95`
  - Covers: Probability axioms and derived rules, Conditional probability and total probability, Bayes' law and posterior reasoning, Independence and conditional independence
  - Angle: Bayes and total probability in Vierfeldertafel form — the exact presentation German exams use.
  - Why this angle matters: German statistics exams overwhelmingly pose conditional-probability questions as a four-field table or a tree, not as an algebraic identity, and grading follows the table. These solutions show the table being filled and read, which is the mechanical skill worth having automatic before the Klausur. Six pages of problems, seven of solutions — small enough to finish in one sitting.
  - Local target: `material://source-fahrmeir-arbeitsbuch/arbeitsbuch.pdf`
- **A Modern Introduction to Probability and Statistics — Dekking — probability exercise bank**
  - Use: `exercise` · depth `practice` · scope `complementary`
  - Exact locator: `Ch 2 outcomes, events, and probability, pdf pp. 24-35; Ch 3 conditional probability and independence, pdf pp. 36-51 (§3.3 law of total probability and Bayes' rule p. 41; §3.4 independence p. 43; exercises p. 48); answers App C pdf pp. 434-442`
  - Covers: Probability axioms and derived rules, Conditional probability and total probability, Bayes' law and posterior reasoning, Independence and conditional independence
  - Angle: Quick exercises embedded mid-section with solutions at the chapter end — a self-check every few pages rather than only at the end.
  - Why this angle matters: The structural feature that distinguishes this book: each section plants short 'quick exercises' in the flow and answers them at §x.5 before the real exercise set. For probability rules, where the failure mode is silent misunderstanding rather than difficulty, that rhythm catches errors within a page instead of after a chapter. The treatment itself is compact and modern; Ch 2 is twelve pages for material Fahrmeir spends twenty on. Ch 1's Monty Hall opening (p. 16) is the same framing puzzle L04 uses.
  - Local target: `material://source-dekking-mips/dekking.pdf`
- **MIT 18.05 Introduction to Probability and Statistics (OCW) — MIT 18.05 — probability notes and solved problems**
  - Use: `course` · depth `practice` · scope `complementary`
  - Exact locator: `Classes: Reading and In-class Materials: 'Conditional Probability, Independence and Bayes' Theorem' reading and slides; Problem Set 2 with its published solutions`
  - Covers: Random experiments, outcomes, and event spaces, Conditional probability and total probability, Bayes' law and posterior reasoning, Independence and conditional independence
  - Angle: Reading, in-class problems and solved problem set for the same topic, published together — a complete study loop rather than one artifact.
  - Why this angle matters: 18.05 publishes, per class, a reading, the slides used on it, the in-class problems and the solutions, plus a problem set with worked answers. That means one topic can be learned, practised and checked without leaving the page — the thing a lecture deck alone cannot give you. Its treatment of the base-rate fallacy is unusually direct and matches L04's opening framing slides. Written for students who have had multivariable calculus, so the register sits above OpenIntro and below Ross.
- **Schaum's Outline of Probability — Schaum — probability and Bayes worked problems**
  - Use: `exercise` · depth `practice` · scope `complementary`
  - Exact locator: `Ch 3 Introduction to Probability, pdf pp. 40-55; Ch 4 Conditional Probability and Independence, pdf pp. 56-75 (every problem carries a full worked solution)`
  - Covers: Probability axioms and derived rules, Conditional probability and total probability, Bayes' law and posterior reasoning, Independence and conditional independence
  - Angle: Pure volume: dozens of short solved problems per chapter, sorted by difficulty, with no exposition to read around them.
  - Why this angle matters: Schaum's is a problem book with the theory compressed into a two-page summary at each chapter head. That makes it the wrong first exposure and the right thing to open when the concept is understood and the calculation is not yet automatic — the state most students are in a week before the Klausur. The problems are short enough to do in batches of ten, and every one is solved in full. This is a scanned older edition, so notation occasionally differs from the lecture's; treat the deck as authoritative where they disagree.
  - Local target: `material://source-schaums-probability/schaums-probability.pdf`
- **StatQuest with Josh Starmer (YouTube) — StatQuest — Naive Bayes**
  - Use: `video` · depth `orientation` · scope `complementary`
  - Exact locator: `'Naive Bayes, Clearly Explained' (≈15 min)`
  - Covers: Categorical Naive Bayes classifier
  - Angle: Builds the spam classifier from counted word frequencies before writing any probability notation.
  - Why this angle matters: The video's order is the reverse of the lecture's: it counts words in example messages, forms the products, and only then names what it has been doing as Naive Bayes with a conditional independence assumption. For a construction that looks arbitrary on slides, seeing the counting first makes the independence assumption's role obvious — it is what lets the counts be multiplied. Pairs with the deck rather than replacing it; the deck's notation is what the exam uses.
- **Kurzes Tutorium Statistik (Bärtl, YouTube) — Kurzes Tutorium Statistik — Zufallsexperiment and Bayes basics**
  - Use: `video` · depth `orientation` · scope `complementary`
  - Exact locator: `'Zufallsexperiment und Ereignisse'; 'Bedingte Wahrscheinlichkeit'; 'Satz von Bayes'`
  - Covers: Random experiments, outcomes, and event spaces, Probability axioms and derived rules, Conditional probability and total probability, Bayes' law and posterior reasoning
  - Angle: Works Bayes through the Vierfeldertafel, in German, which is the presentation German exams use.
  - Why this angle matters: The four-field table is the standard German exam apparatus for conditional probability, and these videos build and read one directly. Combined with the Fahrmeir Arbeitsbuch solutions this covers the format completely. Do not use them for the Naive Bayes construction — that is the lecture's own and has no German-language equivalent here.
- **3Blue1Brown — videos on Bayes' theorem (playlist) — 3Blue1Brown — the geometry behind conditional probability and Bayes**
  - Use: `video` · depth `intuition` · scope `complementary`
  - Exact locator: `'Bayes theorem, the geometry of changing beliefs' (≈15 min); 'The quick proof of Bayes' theorem' (≈3 min); optionally 'The medical test paradox'`
  - Covers: Conditional probability and total probability, Bayes' law and posterior reasoning
  - Angle: The three-minute proof recovers the formula from the same picture — read it after the geometry, never instead of it.
  - Why this angle matters: The pairing is the point: the long video makes the result obvious geometrically and the short one shows that the algebraic identity is just that picture written down. Doing them in that order means L04's formula arrives as a summary of something already understood. Reversing the order wastes both. Neither video covers total probability as a separate result — for that, Fahrmeir §4.6.
  - Web target: https://www.youtube.com/playlist?list=PLk4N6AFvLWe3xCHuOs0siWp0q2F43Cslh

### 4. University courses, prior-year, exam and advanced reference

- **SaD 2025 lecture recordings (WiSe 2025 run) — 2025 probability deck with notes**
  - Use: `course-material` · depth `advanced-reference` · scope `prior-year`
  - Exact locator: `04_probability_with_notes (1).pdf`
  - Covers: Random experiments, outcomes, and event spaces, Probability axioms and derived rules, Conditional probability and total probability, Bayes' law and posterior reasoning, Independence and conditional independence
  - Angle: The 2025 deck for the same topic, annotated with the lecturer's spoken notes.
  - Why this angle matters: Prior-year material is never scope evidence — the 2026 deck decides what is examinable — but the annotated version records explanations that exist only in speech, which is exactly what a PDF of the current deck cannot give you. Use it when a current slide is terse and you want to know what was said around it. Check every claim against the 2026 deck before relying on it.
- **MIT 6.041SC — Probabilistic Systems Analysis and Applied Probability (Tsitsiklis, OCW) — MIT 6.041SC — conditional probability, Bayes and independence lectures**
  - Use: `course` · depth `course-aligned` · scope `complementary`
  - Exact locator: `Lectures 2-3 (conditioning and Bayes' rule; independence) with their recitations and solved tutorials`
  - Covers: Conditional probability and total probability, Bayes' law and posterior reasoning, Independence and conditional independence, Probability axioms and derived rules
  - Angle: Every lecture is paired with a recitation and a tutorial whose problems are solved on video — three passes over one topic.
  - Why this angle matters: Tsitsiklis's course structure is the differentiator: the lecture states the theory, the recitation works standard problems, and the tutorial works harder ones, all recorded. For a topic where the gap between following an explanation and solving a problem is wide — which is exactly conditional probability — that three-pass structure is worth more than a better single explanation. Free on OCW with all materials.
- **FAU Erlangen Statistik-Klausur WS14/15 (mit Lösungen) — FAU pp. 4 and 22 — total probability, Bayes and independence**
  - Use: `exercise` · depth `practice` · scope `complementary`
  - Exact locator: `FAU-Erlangen_Statistik-Klausur_WS14-15_mit-Loesungen.pdf, p. 4 Aufgabe 1(3)-(4), solution p. 22`
  - Covers: Conditional probability and total probability, Bayes' law and posterior reasoning, Independence and conditional independence
  - Angle: Tests conditional probability as a table calculation rather than a definition recital.
  - Why this angle matters: The same orange-origin item is routed here for its formal Bayes and independence steps. It confirms the German notation and the compact published answer after the course sheet has established the method.
  - Local target: `material://source-fau-klausur-ws1415/FAU-Erlangen_Statistik-Klausur_WS14-15_mit-Loesungen.pdf`
- **Pitman — Probability — Pitman — conditional probability selections**
  - Use: `book` · depth `advanced-reference` · scope `complementary`
  - Exact locator: `Ch 1 §1.4 Conditional Probability and Independence, pdf pp. 44-57; §1.5 Bayes' Rule, pdf pp. 58-66; §1.6 Sequences of Events, pdf pp. 67-89`
  - Covers: Probability axioms and derived rules, Conditional probability and total probability, Bayes' law and posterior reasoning, Independence and conditional independence
  - Angle: Everything through tree diagrams and partitions drawn on the page — the most visual derivation of Bayes on the shelf.
  - Why this angle matters: Pitman's method is to draw the partition and the tree, label every branch, and read the answer off the picture before writing any algebra; §1.5 derives Bayes' rule as a relabelling of a tree you have already drawn. That makes the role of the partition — the thing L04's slide 46 leaves implicit when it states Bayes with the denominator pre-expanded — impossible to miss. §1.6 then does sequences of events and the multiplication rule, which is the machinery behind the chain of conditional independence assumptions Naive Bayes rests on. Hundreds of worked examples; the exercises are harder than SaD needs, so pick rather than sweep.
  - Local target: `material://source-pitman-probability/pitman.pdf`
- **Tijms — Understanding Probability (2e) — Tijms — simulation-first probability intuition**
  - Use: `book` · depth `advanced-reference` · scope `complementary`
  - Exact locator: `Ch 6 Chance trees and Bayes' rule, pdf pp. 218-234; Ch 8 Conditional probability and Bayes, pdf pp. 255-274`
  - Covers: Conditional probability and total probability, Bayes' law and posterior reasoning
  - Angle: Two passes over Bayes, deliberately separated: an informal chance-tree chapter in Part One, a formal one in Part Two.
  - Why this angle matters: The book is split into 'Probability in action' and 'Essentials of probability', and Bayes appears in both. Ch 6 argues entirely with chance trees and real cases — medical screening, the notorious court cases — with no formal apparatus; Ch 8 restates the same results with the definitions in place. If L04's formal treatment did not land, reading Ch 6 alone and returning to the deck often fixes it, which is a cheaper repair than a full probability chapter. Tijms is also the best source here on why intuition fails on these problems, which is what L04's framing node is about.
  - Local target: `material://source-tijms-understanding-probability/tijms.pdf`
- **Ross — A First Course in Probability — Ross — formal probability foundations**
  - Use: `book` · depth `advanced-reference` · scope `complementary`
  - Exact locator: `Ch 2 Axioms of Probability, pdf pp. 46-99 (§2.3 axioms; §2.5 sample spaces having equally likely outcomes); Ch 3 Conditional Probability and Independence, pdf pp. 100-197 (§3.3 Bayes's Formula; §3.4 Independent Events; §3.5 P(·\|F) is a Probability)`
  - Covers: Probability axioms and derived rules, Conditional probability and total probability, Bayes' law and posterior reasoning, Independence and conditional independence
  - Angle: The reference treatment: axioms stated formally, every derived rule proved from them, and independence given a full section with counterexamples.
  - Why this angle matters: Ross is the standard rigorous first course, and its value here is completeness rather than gentleness. Two things it has that the softer sources do not: §3.4 works through why pairwise independence does not imply mutual independence, with an explicit counterexample — the distinction L04's independence node states and the exam can probe; and §3.5 proves that conditioning on a fixed event yields a genuine probability measure, which is the formal fact behind every 'just condition and continue' move. Use it to settle a question, not to learn the topic from cold.
  - Local target: `material://source-ross-first-course/ross.pdf`
- **Harvard Stat 110 — Probability (Blitzstein) — Harvard Stat 110 — conditioning and Bayes lectures**
  - Use: `course` · depth `advanced-reference` · scope `complementary`
  - Exact locator: `Lectures 2-4 (conditional probability, Bayes' rule, independence) with the matching sections of the Stat 110 strategic-practice sheets and their solutions`
  - Covers: Conditional probability and total probability, Bayes' law and posterior reasoning, Independence and conditional independence
  - Angle: Blitzstein lecturing his own book — the same argument delivered twice, in print and on video.
  - Why this angle matters: This is the video companion to Blitzstein & Hwang, so choosing between them is a format decision rather than a content decision: the definitions, notation and examples line up section by section. The lectures add the thing the book cannot — hearing which step he considers the difficult one, and watching him refuse to write the algebra until the story is clear. The strategic-practice sheets are graded from routine to hard with full solutions.
- **SaD external German Klausur bank (local) — Leuphana-Merz pp. 5-10 — probability and conditional-probability drills**
  - Use: `exercise` · depth `practice` · scope `complementary`
  - Exact locator: `Leuphana-Merz_Statistik-2_Uebungsbuch-mit-Klausur.pdf, pp. 5-10, Aufgabenblatt 1`
  - Covers: Random experiments, outcomes, and event spaces, Probability axioms and derived rules, Conditional probability and total probability, Bayes' law and posterior reasoning, Independence and conditional independence
  - Angle: A dense German exercise block for finite probability, conditioning and Bayes before the later inference chapters.
  - Why this angle matters: The block supplies more authentic German stems than the course sheet while remaining at the same foundational level. Select only the event/conditioning items; later pages in this 109-page book belong to estimation and testing and are routed separately.
  - Local target: `material://source-sad-klausuren-extern/Leuphana-Merz_Statistik-2_Uebungsbuch-mit-Klausur.pdf`

## L05 — SaD Lecture 05 — Combinatorics

**Lecture purpose.** The lecture turns verbal counting problems into a small decision system based on order, replacement, and selection size, then uses those counts as probability denominators and numerators.

**Concept progression.**

1. **The combinatorics decision grid** — First decide whether order matters, whether replacement/repetition is allowed, and whether all n objects or only k are used; the formula follows from those choices.
2. **Permutations and indistinguishable objects** — Ordering all objects gives n!; repeated or indistinguishable groups divide away permutations that do not create a new arrangement. Builds on: The combinatorics decision grid.
3. **Ordered selections (variations)** — Choosing k positions with order yields falling-factorial counts without replacement and n^k sequences with replacement. Builds on: The combinatorics decision grid.
4. **Unordered selections and binomial coefficients** — Choosing k objects without order gives n choose k, whose symmetry and recursive identities recur throughout probability and algorithms. Builds on: The combinatorics decision grid.
5. **Combinations with repetition and stars and bars** — Multisets and allocations become separator problems; the model must distinguish selecting types repeatedly from ordering individual draws. Builds on: Unordered selections and binomial coefficients.
6. **Laplace probability, complements, and hypergeometric counting** — In equally likely finite spaces, probability is favorable counts over total counts; complements simplify at-least-one events, and without-replacement samples produce hypergeometric terms. Builds on: Permutations and indistinguishable objects, Ordered selections (variations), Unordered selections and binomial coefficients.
7. **Binomial identities and Stirling approximation** — Algebraic identities reorganize repeated counting arguments, while Stirling estimates factorial growth when exact evaluation is impractical. Builds on: Unordered selections and binomial coefficients.

**Complete source menu.**

### 1. Current scope and current practice

- **SaD — Statistik und Datenanalyse, lecture slides (SoSe 2026) — Current L05 combinatorics deck**
  - Use: `course-material` · depth `course-aligned` · scope `current`
  - Exact locator: `lecture-slides/05_combinatorics.pdf, 34 slides`
  - Covers: The combinatorics decision grid, Permutations and indistinguishable objects, Ordered selections (variations), Unordered selections and binomial coefficients, Combinations with repetition and stars and bars, Laplace probability, complements, and hypergeometric counting, Binomial identities and Stirling approximation
  - Angle: The decision grid — order × replacement × selection size — which is the organising device the exam expects you to apply.
  - Why this angle matters: The deck's contribution is the grid itself rather than the individual formulas, which are standard. Read it as a classification procedure: identify the cell, then apply the formula that cell names. The identities and Stirling slides at the end are stated without justification; Blitzstein §1.5's story proofs are where they become memorable rather than memorised.
- **SaD exercise sheets UE1–UE7 (SoSe 2026) — Blatt 2, Aufgabe 1 — counting inside finite probability**
  - Use: `exercise` · depth `practice` · scope `current`
  - Exact locator: `exercise-slides/blatt-02.pdf, p. 1, Aufgabe 1(a)-(e)`
  - Covers: The combinatorics decision grid, Ordered selections (variations), Unordered selections and binomial coefficients, Laplace probability, complements, and hypergeometric counting
  - Angle: Hides the counting case inside cards, repeated dice and dependent portfolio events, which tests identification rather than formula recall.
  - Why this angle matters: This is a current assessed sheet: attempt it before opening the tutorial solution. It is scope evidence because it shows the chair's own wording, data size and expected amount of working; it is not a replacement for the lecture derivation.
  - Local target: `material://source-sad-ss26-lectures/exercise-slides/blatt-02.pdf`
- **SaD exercise sheets UE1–UE7 (SoSe 2026) — UE4, slides 4-8 — worked finite-counting solutions**
  - Use: `exercise` · depth `practice` · scope `current`
  - Exact locator: `exercise-slides/UE4.pdf, slides 4-8`
  - Covers: The combinatorics decision grid, Ordered selections (variations), Unordered selections and binomial coefficients, Laplace probability, complements, and hypergeometric counting
  - Angle: Makes the numerator/denominator counting decisions explicit for the current sheet's disguised cases.
  - Why this angle matters: This is the current worked tutorial for the named task. Use it after an unaided attempt: its value is the course's calculation order and notation, while reading it first would turn an exam-relevant retrieval task into passive recognition.
  - Local target: `material://source-sad-ss26-lectures/exercise-slides/UE4.pdf`

### 2. Books and independent derivations

- **Statistik: Der Weg zur Datenanalyse (9. Aufl.) — Fahrmeir Chapter 4 — combinatorics and finite probability**
  - Use: `book` · depth `derivation` · scope `complementary`
  - Exact locator: `Ch 4 §4.3 Zufallsstichproben und Kombinatorik, pdf pp. 214-220; Aufgaben pdf pp. 239-241`
  - Covers: The combinatorics decision grid, Unordered selections and binomial coefficients, Laplace probability, complements, and hypergeometric counting
  - Angle: Six pages that put counting where SaD puts it — inside sampling — instead of treating combinatorics as its own subject.
  - Why this angle matters: This is deliberately the shortest combinatorics treatment on the shelf, and that is its value: Fahrmeir introduces the counting cases only as the sizes of sample spaces for Ziehen mit/ohne Zurücklegen and mit/ohne Berücksichtigung der Reihenfolge, which is precisely how L05's decision grid is organised. If the grid is what will not stick, read this rather than a full combinatorics chapter, because it never leaves the sampling frame. For volume of drill and the harder identity questions go to Blitzstein Ch 1 or Schaum's Ch 2 instead.
  - Local target: `material://source-fahrmeir-statistik/statistik.pdf`
- **Grinstead & Snell — Introduction to Probability (AMS, open access) — Grinstead & Snell Ch 3 — combinatorics**
  - Use: `book` · depth `course-aligned` · scope `complementary`
  - Exact locator: `Ch 3 Combinatorics §3.1 permutations, §3.2 combinations, §3.3 card shuffling, with the chapter exercises`
  - Covers: Permutations and indistinguishable objects, Ordered selections (variations), Unordered selections and binomial coefficients, Binomial identities and Stirling approximation, Laplace probability, complements, and hypergeometric counting
  - Angle: Proves the binomial identities L05 lists, and uses card shuffling as a running example that makes the counting concrete.
  - Why this angle matters: §3.2 does not merely state Pascal's identity and the binomial theorem — it proves them and then uses them, which is what L05's identities node needs and does not supply. The card-shuffling section is unusual and useful: it applies the counting machinery to a physical process, so the abstractions acquire a referent. Free and open-access, with a large exercise set.
- **Introduction to Probability (2nd ed.) — Blitzstein Chapter 1 — strategic counting**
  - Use: `book` · depth `intuition` · scope `complementary`
  - Exact locator: `Ch 1 pdf pp. 18-61 (§1.3 naive definition of probability p. 23; §1.4 how to count p. 25; §1.5 story proofs p. 37; §1.6 non-naive definition p. 38; exercises §1.9 p. 50)`
  - Covers: The combinatorics decision grid, Permutations and indistinguishable objects, Ordered selections (variations), Unordered selections and binomial coefficients, Combinations with repetition and stars and bars, Laplace probability, complements, and hypergeometric counting
  - Angle: Story proofs: counting identities argued by describing two ways to count the same set, with no algebra at all.
  - Why this angle matters: §1.5 is the reason to come here for L05 rather than to any German text. A story proof establishes an identity — the symmetry of binomial coefficients, Vandermonde, the hockey stick — by naming a set and counting it twice, and once seen the identities stop being things to memorise. That directly serves L05's identities node, which the deck states without justification. §1.4 also makes the sampling table (ordered/unordered × with/without replacement) explicit, which is the same four-way grid the lecture draws. The strongest exercise set on the shelf for this material.
  - Local target: `material://source-blitzstein-hwang/blitzstein.pdf`
- **OpenIntro Statistics (4th ed.) — OpenIntro — finite counting inside probability**
  - Use: `book` · depth `orientation` · scope `complementary`
  - Exact locator: `Ch 3 §3.3 sampling from a small population, pdf pp. 112-114; Ch 4 §4.3 binomial distribution, pdf pp. 149-157`
  - Covers: Laplace probability, complements, and hypergeometric counting
  - Angle: Almost no combinatorics on purpose: it shows which L05 results survive when counting is replaced by simulation and tables.
  - Why this angle matters: OpenIntro reaches the binomial coefficient in a single paragraph inside §4.3 and never builds a counting apparatus. Routed here as an honest boundary marker rather than as study material: it tells you which of L05's machinery an applied statistics course considers optional. If the aim is to pass L05's counting questions, this is the wrong source — use Blitzstein Ch 1 or Schaum's Ch 2. Kept on the menu so the absence is visible rather than an accidental gap.
  - Local target: `material://source-openintro-statistics/openintro.pdf`

### 3. Visual, implementation and additional practice

- **Arbeitsbuch Statistik (Fahrmeir et al.) — Arbeitsbuch Chapter 4 — combinatorics applications**
  - Use: `exercise` · depth `practice` · scope `complementary`
  - Exact locator: `Ch 4 Aufgaben pdf pp. 83-88, Lösungen pdf pp. 89-95 (the Ziehen mit/ohne Zurücklegen items)`
  - Covers: The combinatorics decision grid, Unordered selections and binomial coefficients, Laplace probability, complements, and hypergeometric counting
  - Angle: Counting embedded in probability questions rather than as pure counting exercises — which is how L05 is examined.
  - Why this angle matters: The exam rarely asks 'how many arrangements' on its own; it asks for a probability whose computation happens to require a count. These items are all of that second kind, so they train the step students actually lose marks on: deciding whether order and replacement matter before reaching for a formula. Thin on pure identities and Stirling — Blitzstein §1.4 covers those.
  - Local target: `material://source-fahrmeir-arbeitsbuch/arbeitsbuch.pdf`
- **A Modern Introduction to Probability and Statistics — Dekking — counting and finite-probability exercises**
  - Use: `exercise` · depth `practice` · scope `complementary`
  - Exact locator: `Ch 4 §4.3 the Bernoulli and binomial distributions, pdf pp. 56-58; Ch 2 §2.4 products of sample spaces, pdf pp. 29-30; exercises pdf pp. 62-66`
  - Covers: The combinatorics decision grid, Unordered selections and binomial coefficients, Laplace probability, complements, and hypergeometric counting
  - Angle: Deliberately thin on counting — read it to see how far you can get with product sample spaces instead of combinatorial formulas.
  - Why this angle matters: This book barely has a combinatorics section, and knowing that is useful: it builds the binomial coefficient where it is needed, out of the product sample space in §2.4, rather than teaching counting as a prerequisite subject. If L05's grid feels like arbitrary memorisation, seeing a serious book do without most of it reframes the grid as a shortcut rather than as the content. For actual counting practice go to Blitzstein §1.4 or Schaum's Ch 2 — this route is orientation.
  - Local target: `material://source-dekking-mips/dekking.pdf`
- **MIT 18.05 Introduction to Probability and Statistics (OCW) — MIT 18.05 — counting and finite probability**
  - Use: `course` · depth `practice` · scope `complementary`
  - Exact locator: `Classes: Reading and In-class Materials, Class 1 'Counting and Sets' reading and slides; Problem Set 1 with solutions`
  - Covers: The combinatorics decision grid, Unordered selections and binomial coefficients, Laplace probability, complements, and hypergeometric counting
  - Angle: Treats counting as one week of prerequisite technique, which is a useful calibration of how much of L05 is genuinely hard.
  - Why this angle matters: 18.05 spends a single class on counting before moving to probability, and its problem set is correspondingly compact. Reading it tells you which parts of L05's grid a strong applied course considers routine and which it considers worth practising — helpful when deciding how much time this lecture deserves. Not a substitute for Blitzstein Ch 1 if the grid itself is the problem.
- **Schaum's Outline of Probability — Schaum — combinatorics drills**
  - Use: `exercise` · depth `practice` · scope `complementary`
  - Exact locator: `Ch 2 Techniques of Counting, pdf pp. 18-39`
  - Covers: The combinatorics decision grid, Permutations and indistinguishable objects, Ordered selections (variations), Unordered selections and binomial coefficients, Laplace probability, complements, and hypergeometric counting
  - Angle: Twenty-two pages that are almost entirely solved counting problems — the highest drill density for L05 on the shelf.
  - Why this angle matters: L05 is the lecture where practice volume beats explanation, because the difficulty is pattern recognition across many superficially different word problems. This chapter supplies that volume and nothing else. Work them in mixed order and force yourself to name the grid cell (ordered/unordered, with/without replacement) before computing — the chapter is organised by technique, which otherwise gives the answer away.
  - Local target: `material://source-schaums-probability/schaums-probability.pdf`
- **StatQuest with Josh Starmer (YouTube) — StatQuest — Hypergeometric distribution**
  - Use: `video` · depth `orientation` · scope `complementary`
  - Exact locator: `'The Hypergeometric Distribution, Clearly Explained' (≈12 min)`
  - Covers: Laplace probability, complements, and hypergeometric counting
  - Angle: The one video here that treats the counting problem behind sampling without replacement rather than the formula.
  - Why this angle matters: Hypergeometric counting is where L05's grid meets L07's distributions, and it is the cell students most often get wrong because the numerator and denominator involve different populations. The video draws the urn, marks the two groups, and builds the ratio of combinations from the picture. Short, and worth watching before attempting the L05 counting exercises that involve defective items or committee selection.
- **jbstatistics (YouTube) — jbstatistics — permutations and combinations**
  - Use: `video` · depth `orientation` · scope `complementary`
  - Exact locator: `The 'Permutations and Combinations' video series (3 videos, ≈10 min each)`
  - Covers: The combinatorics decision grid, Permutations and indistinguishable objects, Ordered selections (variations), Unordered selections and binomial coefficients
  - Angle: Derives the combination formula from the permutation formula on screen, rather than presenting both as given.
  - Why this angle matters: nCr = nPr / r! is the relationship that makes the two halves of L05's grid one idea rather than two formulas, and seeing the division performed — dividing out the orderings you decided not to distinguish — is what makes it stick. Short series, appropriate as a first exposure before the Schaum's drill.

### 4. University courses, prior-year, exam and advanced reference

- **SaD 2025 lecture recordings (WiSe 2025 run) — 2025 probability deck — counting context**
  - Use: `course-material` · depth `advanced-reference` · scope `prior-year`
  - Exact locator: `05_random_variables.pdf`
  - Covers: Laplace probability, complements, and hypergeometric counting
  - Angle: Prior-year treatment of the same material at a different pace; note that the 2025 numbering does not match 2026.
  - Why this angle matters: The 2025 sequence numbers this deck as random variables where 2026 has combinatorics, so the file names cannot be used to align lectures. Compare by topic, never by number. Useful as a second explanation, dangerous as a scope guide.
- **Pitman — Probability — Pitman — counting foundations**
  - Use: `book` · depth `advanced-reference` · scope `complementary`
  - Exact locator: `Ch 1 §1.1 Equally Likely Outcomes, pdf pp. 14-32; Ch 2 §2.1 The Binomial Distribution, pdf pp. 90-102`
  - Covers: Unordered selections and binomial coefficients, Laplace probability, complements, and hypergeometric counting
  - Angle: Counting introduced only as the way to compute equally-likely probabilities, never as an independent topic.
  - Why this angle matters: §1.1 sets up the Laplace model first — probability as a ratio of counts — so every counting technique that follows arrives as an answer to 'how do I get that numerator'. That is the same motivation L05 uses when it moves from the decision grid to Laplace probability, and it is a better frame than treating combinatorics as prerequisite algebra. Thin on stars-and-bars and repetition cases; Blitzstein §1.4 covers those properly.
  - Local target: `material://source-pitman-probability/pitman.pdf`
- **Tijms — Understanding Probability (2e) — Tijms — counting through probability models**
  - Use: `book` · depth `advanced-reference` · scope `complementary`
  - Exact locator: `Ch 7 Foundations of probability theory, pdf pp. 235-254 (finite sample spaces and the Laplace model)`
  - Covers: The combinatorics decision grid, Laplace probability, complements, and hypergeometric counting
  - Angle: Counting kept subordinate to the sample-space model, with birthday- and lottery-style problems as the worked cases.
  - Why this angle matters: Tijms treats combinatorial questions as questions about the size of a well-chosen sample space, and his worked cases — coincidences, lotteries, matching problems — are the ones whose answers are counterintuitive enough to be memorable. Useful as a second pass after the mechanics are in place from L05's grid, less useful as a first exposure because he does not tabulate the cases.
  - Local target: `material://source-tijms-understanding-probability/tijms.pdf`
- **Ross — A First Course in Probability — Ross — combinatorial analysis**
  - Use: `book` · depth `advanced-reference` · scope `complementary`
  - Exact locator: `Ch 1 Combinatorial Analysis, pdf pp. 14-45 (§1.2 the basic principle of counting; §1.3 permutations; §1.4 combinations; §1.5 multinomial coefficients; §1.6 the number of integer solutions of equations)`
  - Covers: Permutations and indistinguishable objects, Ordered selections (variations), Unordered selections and binomial coefficients, Laplace probability, complements, and hypergeometric counting
  - Angle: The multinomial coefficient and the integer-solutions problem, both of which L05's grid implies but does not develop.
  - Why this angle matters: §1.5 generalises the binomial coefficient to partitions into more than two groups — the case that appears when a question asks for arrangements of a word with repeated letters, which L05's 'permutations with indistinguishable objects' node is exactly about. §1.6 is the stars-and-bars argument stated as counting integer solutions, which is the honest form of the 'combinations with repetition' cell in the grid. Together these two sections cover the two grid cells that most often go wrong, in about fifteen pages.
  - Local target: `material://source-ross-first-course/ross.pdf`
- **Harvard Stat 110 — Probability (Blitzstein) — Harvard Stat 110 — strategic counting**
  - Use: `course` · depth `advanced-reference` · scope `complementary`
  - Exact locator: `Lecture 1 (sample spaces, naive definition, counting) and Lecture 2 (story proofs, non-naive definition); Strategic Practice 1 with solutions`
  - Covers: The combinatorics decision grid, Unordered selections and binomial coefficients, Laplace probability, complements, and hypergeometric counting
  - Angle: Contains the story-proof demonstrations performed live, which is where that technique is easiest to pick up.
  - Why this angle matters: A story proof is a way of arguing, and watching one being constructed is more instructive than reading a finished one — the moment where he chooses what set to count twice is the whole method. Two lectures cover all of L05's counting content at a level above the lecture's own, with the identities node handled properly.
- **SaD external German Klausur bank (local) — Leuphana-Merz pp. 5-10 — combinatorial probability items**
  - Use: `exercise` · depth `practice` · scope `complementary`
  - Exact locator: `Leuphana-Merz_Statistik-2_Uebungsbuch-mit-Klausur.pdf, pp. 5-10, Aufgabenblatt 1 counting items`
  - Covers: The combinatorics decision grid, Unordered selections and binomial coefficients, Laplace probability, complements, and hypergeometric counting
  - Angle: Uses counting as the hidden first step of a probability problem rather than naming the formula.
  - Why this angle matters: This is identification practice: decide the finite sample space and the relevant count before computing a probability. It does not replace the lecture's complete order/replacement decision grid, so use it only after that grid can be reproduced.
  - Local target: `material://source-sad-klausuren-extern/Leuphana-Merz_Statistik-2_Uebungsbuch-mit-Klausur.pdf`

## L06 — SaD Lecture 06 — Random Variables, Expectation & Variance

**Lecture purpose.** The lecture converts uncertain outcomes into numerical variables and develops the moment and concentration language used by every later distribution and inference result.

**Concept progression.**

1. **Random variables and realizations** — A random variable maps outcomes to numbers; the variable, a realized value, and the underlying random experiment are distinct objects.
2. **PMF, density, and CDF** — Discrete mass and continuous density assign probability differently, while the cumulative distribution function uniformly represents P(X less than or equal to x). Builds on: Random variables and realizations.
3. **Functions and transformations of random variables** — A transformation g(X) changes the possible values and distribution; probabilities and moments must be recomputed from the mapping rather than by treating X as a fixed number. Builds on: PMF, density, and CDF.
4. **Expected value and linearity** — Expectation is a probability-weighted long-run average; linearity holds without independence and extends from X to functions and sums of random variables. Builds on: PMF, density, and CDF.
5. **Variance, standard deviation, and covariance** — Variance measures squared deviation from expectation, affine scaling squares the multiplier, and covariance records joint variation needed for sums and sample means. Builds on: Expected value and linearity.
6. **IID samples and the random sample mean** — The sample mean is itself random; under IID sampling its expectation is the population mean and its variance shrinks as sigma squared divided by n. Builds on: Variance, standard deviation, and covariance.
7. **Chebyshev bounds and the law of large numbers** — Chebyshev gives a distribution-free tail bound, and the law of large numbers explains why sample averages stabilize as data accumulate. Builds on: IID samples and the random sample mean.

**Complete source menu.**

### 1. Current scope and current practice

- **SaD — Statistik und Datenanalyse, lecture slides (SoSe 2026) — Current L06 random-variables deck**
  - Use: `course-material` · depth `course-aligned` · scope `current`
  - Exact locator: `lecture-slides/06_random_variables.pdf, 60 slides`
  - Covers: Random variables and realizations, PMF, density, and CDF, Functions and transformations of random variables, Expected value and linearity, Variance, standard deviation, and covariance, IID samples and the random sample mean, Chebyshev bounds and the law of large numbers
  - Angle: The scope authority for random-variable language, and the deck that introduces PMF, density and CDF in a single pass.
  - Why this angle matters: Sixty slides covering random variables, all three distribution functions, transformations, expectation, variance, covariance, the sample mean, Chebyshev and the law of large numbers. The single-pass treatment of PMF versus density is where most confusion starts — Fahrmeir separates them by chapter and is the standard repair. Chebyshev and the LLN at the end are the bridge into L08 and are examinable in their own right.
- **SaD exercise sheets UE1–UE7 (SoSe 2026) — Übungsblatt 3, Aufgabe 1 — PMF, transformation, expectation and variance**
  - Use: `exercise` · depth `practice` · scope `current`
  - Exact locator: `exercise-slides/Übung-3.pdf, p. 1, Aufgabe 1(a)-(c)`
  - Covers: PMF, density, and CDF, Functions and transformations of random variables, Expected value and linearity, Variance, standard deviation, and covariance
  - Angle: Compresses the four core random-variable operations into one exact current assignment.
  - Why this angle matters: This is a current assessed sheet: attempt it before opening the tutorial solution. It is scope evidence because it shows the chair's own wording, data size and expected amount of working; it is not a replacement for the lecture derivation.
  - Local target: `material://source-sad-ss26-lectures/exercise-slides/Übung-3.pdf`
- **SaD exercise sheets UE1–UE7 (SoSe 2026) — Übungsblatt 3, Aufgabe 3 — mixture moments and the LLN**
  - Use: `exercise` · depth `practice` · scope `current`
  - Exact locator: `exercise-slides/Übung-3.pdf, p. 3, Aufgabe 3(a)-(d)`
  - Covers: Expected value and linearity, Variance, standard deviation, and covariance, IID samples and the random sample mean, Chebyshev bounds and the law of large numbers
  - Angle: Turns expectation and the law of large numbers into a cumulative-mean simulation with a distribution change.
  - Why this angle matters: This is a current assessed sheet: attempt it before opening the tutorial solution. It is scope evidence because it shows the chair's own wording, data size and expected amount of working; it is not a replacement for the lecture derivation. It assumes basic Python/pandas and is therefore a worked application, not the first explanation.
  - Local target: `material://source-sad-ss26-lectures/exercise-slides/Übung-3.pdf`
- **SaD exercise sheets UE1–UE7 (SoSe 2026) — UE4, slides 18-34 — random variables, moments and LLN**
  - Use: `exercise` · depth `practice` · scope `current`
  - Exact locator: `exercise-slides/UE4.pdf, slides 18-34`
  - Covers: Random variables and realizations, PMF, density, and CDF, Functions and transformations of random variables, Expected value and linearity, Variance, standard deviation, and covariance, IID samples and the random sample mean, Chebyshev bounds and the law of large numbers
  - Angle: Uses one discrete and one mixed random variable to connect the definitions to empirical convergence.
  - Why this angle matters: This is the current worked tutorial for the named task. Use it after an unaided attempt: its value is the course's calculation order and notation, while reading it first would turn an exam-relevant retrieval task into passive recognition.
  - Local target: `material://source-sad-ss26-lectures/exercise-slides/UE4.pdf`
- **SaD exercise sheets UE1–UE7 (SoSe 2026) — UE5, slides 4-17 — official Blatt 3 solutions**
  - Use: `exercise` · depth `practice` · scope `current`
  - Exact locator: `exercise-slides/UE5.pdf, slides 4-17`
  - Covers: PMF, density, and CDF, Functions and transformations of random variables, Expected value and linearity, Variance, standard deviation, and covariance, Chebyshev bounds and the law of large numbers
  - Angle: Provides the complete official solution and implementation trace for Blatt 3 after it has been attempted.
  - Why this angle matters: This is the current worked tutorial for the named task. Use it after an unaided attempt: its value is the course's calculation order and notation, while reading it first would turn an exam-relevant retrieval task into passive recognition.
  - Local target: `material://source-sad-ss26-lectures/exercise-slides/UE5.pdf`

### 2. Books and independent derivations

- **Statistik: Der Weg zur Datenanalyse (9. Aufl.) — Fahrmeir Chapters 5–7 — random variables and moments**
  - Use: `book` · depth `derivation` · scope `complementary`
  - Exact locator: `Ch 5 §5.1 Zufallsvariablen, pdf pp. 243-246; §5.2 Verteilungen und Parameter diskreter ZV, pdf pp. 247-269; Ch 6 §6.1 Definition und Verteilung, pdf pp. 289-300; §6.2 Lageparameter, Quantile, Varianz, pdf pp. 301-309; Ch 7 §7.1 Gesetz der großen Zahlen, pdf pp. 330-336; Ch 8 §8.5 Kovarianz und Korrelation, pdf pp. 368-374`
  - Covers: Random variables and realizations, PMF, density, and CDF, Expected value and linearity, Variance, standard deviation, and covariance, Chebyshev bounds and the law of large numbers
  - Angle: Keeps discrete and continuous random variables in separate chapters, so PMF and density are never conflated the way a single merged treatment can.
  - Why this angle matters: L06 introduces PMF, density and CDF together in one pass. Fahrmeir separates them by chapter, which is slower but makes the one exam-relevant distinction unmissable: P(X=x) is a probability in Ch 5 and is identically zero in Ch 6, where only intervals have probability. §8.5 supplies the covariance definition L06 needs and connects it back to the descriptive covariance of Ch 3, so the same symbol is not learned twice. §7.1 is the German statement of Tschebyscheff and the Gesetz der großen Zahlen; read it here rather than in an English text if the exam wording matters.
  - Local target: `material://source-fahrmeir-statistik/statistik.pdf`
- **Grinstead & Snell — Introduction to Probability (AMS, open access) — Grinstead & Snell Ch 6 — expected value and variance**
  - Use: `book` · depth `course-aligned` · scope `complementary`
  - Exact locator: `Ch 6 Expected Value and Variance §6.1 expected value of discrete random variables, §6.2 variance of discrete random variables, §6.3 continuous random variables`
  - Covers: Expected value and linearity, Variance, standard deviation, and covariance, Functions and transformations of random variables
  - Angle: Separates the discrete and continuous cases into their own sections while keeping one chapter, so the parallel between sum and integral stays visible.
  - Why this angle matters: Splitting by chapter (as Fahrmeir does) makes the PMF/PDF distinction unmissable but hides the analogy; merging them (as L06 does) shows the analogy but blurs the distinction. This chapter's three-section structure gets both — the definitions are stated separately and then compared directly. Good middle route if Fahrmeir felt slow and the deck felt fast.
- **Introduction to Probability (2nd ed.) — Blitzstein Chapters 3–4 and 10 — RVs and expectation**
  - Use: `book` · depth `intuition` · scope `complementary`
  - Exact locator: `Ch 3 pdf pp. 120-165 (§3.2 distributions and PMFs p. 123; §3.6 CDFs p. 137; §3.7 functions of random variables p. 140; §3.8 independence of r.v.s p. 146); Ch 4 pdf pp. 166-229 (§4.1 definition of expectation p. 166; §4.2 linearity p. 169; §4.5 LOTUS p. 187; §4.6 variance p. 188); Ch 7 §7.3 covariance and correlation, pdf pp. 343-348`
  - Covers: Random variables and realizations, Functions and transformations of random variables, Expected value and linearity, Variance, standard deviation, and covariance
  - Angle: Insists on the distinction between a random variable and its distribution, and proves linearity of expectation without independence.
  - Why this angle matters: Two things here are worth the reading time. First, §3.1-3.2 hammer that a random variable is a function on the sample space while its distribution is a separate object — the confusion behind most wrong answers about transformations, and something L06 states once. Second, §4.2 proves that E[X+Y] = E[X] + E[Y] holds whether or not X and Y are independent, and shows why that is surprising; the lecture asserts linearity, and knowing it needs no independence is what makes it a tool. §4.5 (LOTUS) is the rule for E[g(X)] that the transformations node depends on. Skip the MGF sections in Ch 6 — out of scope.
  - Local target: `material://source-blitzstein-hwang/blitzstein.pdf`
- **OpenIntro Statistics (4th ed.) — OpenIntro Chapter 4 — distribution bridge**
  - Use: `book` · depth `orientation` · scope `complementary`
  - Exact locator: `Ch 3 §3.4 random variables, pdf pp. 115-124; §3.5 continuous distributions, pdf pp. 125-130`
  - Covers: Random variables and realizations, Expected value and linearity, Variance, standard deviation, and covariance, IID samples and the random sample mean
  - Angle: Ten pages on random variables with expectation and variance introduced through an expected-profit calculation rather than through a definition.
  - Why this angle matters: §3.4 defines E[X] by working out the expected revenue of a lottery-like setup and then naming the computation, which makes the linearity property feel like an accounting fact. That is a lighter entry than Blitzstein's Ch 4 and enough for L06's expectation node, but it stops well short: no LOTUS, no covariance, no Chebyshev. Use it to get started and switch to Blitzstein or Dekking for the transformation and concentration nodes.
  - Local target: `material://source-openintro-statistics/openintro.pdf`

### 3. Visual, implementation and additional practice

- **Arbeitsbuch Statistik (Fahrmeir et al.) — Arbeitsbuch Chapters 5–7 — RV and moment drills**
  - Use: `exercise` · depth `practice` · scope `complementary`
  - Exact locator: `Ch 5 Aufgaben pdf pp. 96-104, Lösungen pdf pp. 105-123; Ch 6 Aufgaben pdf pp. 124-133, Lösungen pdf pp. 134-157; Ch 7 Aufgaben pdf pp. 158-160, Lösungen pdf pp. 161-164`
  - Covers: PMF, density, and CDF, Expected value and linearity, Variance, standard deviation, and covariance, Chebyshev bounds and the law of large numbers
  - Angle: Expectation and variance computed from a given distribution, over and over, in both the discrete and continuous chapters.
  - Why this angle matters: Three chapters of solved items whose common shape is: here is a PMF or density, produce E[X], Var(X), and a transformed variable's moments. That repetition is the point — L06's linearity and transformation rules are only usable once applying them is automatic. Ch 7's items are the Tschebyscheff and LLN calculations, which are short and worth doing because they are the easiest marks in this part of the exam.
  - Local target: `material://source-fahrmeir-arbeitsbuch/arbeitsbuch.pdf`
- **A Modern Introduction to Probability and Statistics — Dekking — random-variable exercises**
  - Use: `exercise` · depth `practice` · scope `complementary`
  - Exact locator: `Ch 4 discrete random variables, pdf pp. 52-66; Ch 5 continuous random variables, pdf pp. 67-80; Ch 7 expectation and variance, pdf pp. 98-111 (change-of-variable formula p. 103; variance p. 105; exercises p. 108); Ch 9 joint distributions, pdf pp. 124-143; Ch 13 §13.2 Chebyshev's inequality, pdf pp. 191-192`
  - Covers: PMF, density, and CDF, Functions and transformations of random variables, Expected value and linearity, Variance, standard deviation, and covariance
  - Angle: States the change-of-variable formula as its own numbered result, which is the rule L06's transformation node needs and states only in passing.
  - Why this angle matters: §7.3 gives E[g(X)] = Σ g(x)p(x) the status of a named theorem with a proof sketch, and every later expectation computation in the book cites it. L06 uses the same rule when it computes moments of transformed variables but never isolates it, so it is easy to treat each computation as a new trick. Ch 13's Chebyshev section is three pages and directly serves the concentration node, with the LLN following immediately in §13.3 so the connection is visible.
  - Local target: `material://source-dekking-mips/dekking.pdf`
- **MIT 18.05 Introduction to Probability and Statistics (OCW) — MIT 18.05 — random variables, expectation, and variance**
  - Use: `course` · depth `practice` · scope `complementary`
  - Exact locator: `Classes: Reading and In-class Materials: the 'Discrete Random Variables; Expectation and Variance' and 'Continuous Random Variables' readings; Problem Sets 2-3 with solutions`
  - Covers: PMF, density, and CDF, Functions and transformations of random variables, Expected value and linearity, Variance, standard deviation, and covariance
  - Angle: Uses R simulations alongside the algebra, so every claimed identity is also demonstrated numerically.
  - Why this angle matters: The course's design principle is that a probabilistic claim should be checked by simulation before it is trusted, and the R code is published. For L06's rules — linearity, variance under scaling, the behaviour of a sample mean — running the simulation is a fast way to find out whether you have remembered the rule correctly, and it takes minutes. Also introduces quantiles carefully, which the lecture uses without defining.
- **Schaum's Outline of Probability — Schaum — random-variable and moment drills**
  - Use: `exercise` · depth `practice` · scope `complementary`
  - Exact locator: `Ch 5 Random Variables, pdf pp. 76-106`
  - Covers: PMF, density, and CDF, Functions and transformations of random variables, Expected value and linearity, Variance, standard deviation, and covariance
  - Angle: Expectation, variance and standard deviation computed from tabulated distributions, dozens of times, with every arithmetic step shown.
  - Why this angle matters: Thirty pages of the same operation on different tables. That is exactly right for L06, where the concepts are few and the exam risk is a slip in the arithmetic or in reading the distribution table. Also covers joint distributions and independence of random variables at the end of the chapter, which supports L06's covariance node.
  - Local target: `material://source-schaums-probability/schaums-probability.pdf`
- **StatQuest with Josh Starmer (YouTube) — StatQuest — expected values and probability distributions**
  - Use: `video` · depth `orientation` · scope `complementary`
  - Exact locator: `'Expected Values, Main Ideas'; 'Expected Values for Continuous Variables'; 'The Main Ideas behind Probability Distributions' (≈10-15 min each)`
  - Covers: PMF, density, and CDF, Expected value and linearity
  - Angle: Handles the discrete-to-continuous transition visually — the histogram narrowing into a density — which is where L06's PMF/PDF distinction is usually lost.
  - Why this angle matters: The two expected-value videos are deliberately a pair: the same quantity computed as a weighted sum, then as an integral, with the bars of the histogram shrinking on screen between them. That animation is the single most useful thing here, because it makes the sum-to-integral move a continuous change rather than two unrelated formulas. Watch them in order.
- **jbstatistics (YouTube) — jbstatistics — expected value and variance calculations**
  - Use: `video` · depth `orientation` · scope `complementary`
  - Exact locator: `'Expected Value and Variance of a Discrete Random Variable' and the companion variance video (≈10 min each)`
  - Covers: Expected value and linearity, Variance, standard deviation, and covariance
  - Angle: Computes E[X] and Var(X) from a probability table step by step, in the layout an exam answer uses.
  - Why this angle matters: The videos build the working column by column — x, P(x), x·P(x), x²·P(x) — which is exactly the table you should be drawing under exam conditions. Copying that layout is a small procedural habit that reliably prevents arithmetic slips, and no book on the shelf shows it as clearly.
- **Kurzes Tutorium Statistik (Bärtl, YouTube) — Kurzes Tutorium Statistik — Zufallsvariablen and Erwartungswert**
  - Use: `video` · depth `orientation` · scope `complementary`
  - Exact locator: `'Zufallsvariablen'; 'Erwartungswert'; 'Varianz'`
  - Covers: Random variables and realizations, Expected value and linearity, Variance, standard deviation, and covariance
  - Angle: The German names and notation for L06's objects, with the symbols the Klausur prints.
  - Why this angle matters: E(X) versus μ, Var(X) versus σ², and the German phrasing of the linearity rules. Short and purely terminological — the concepts should come from Blitzstein or Dekking, but the words should come from here if the exam wording has ever cost you time.

### 4. University courses, prior-year, exam and advanced reference

- **SaD 2025 lecture recordings (WiSe 2025 run) — 2025 random-variables and expected-values pair**
  - Use: `course-material` · depth `advanced-reference` · scope `prior-year`
  - Exact locator: `06_expected_values.pptx-1.pdf`
  - Covers: Random variables and realizations, PMF, density, and CDF, Expected value and linearity, Variance, standard deviation, and covariance
  - Angle: A prior-year deck devoted specifically to expected values, in more detail than the 2026 pass.
  - Why this angle matters: Because 2025 split this material differently, expectation gets a whole deck rather than a section, which makes it a slower and more worked-through treatment of L06's central node. One of the more useful prior-year files for that reason.
- **MIT 6.041SC — Probabilistic Systems Analysis and Applied Probability (Tsitsiklis, OCW) — MIT 6.041SC — random variables, expectation and variance lectures**
  - Use: `course` · depth `course-aligned` · scope `complementary`
  - Exact locator: `Lectures 5-7 (discrete random variables, expectation, multiple random variables) with recitations and tutorials`
  - Covers: Random variables and realizations, Expected value and linearity, Variance, standard deviation, and covariance, PMF, density, and CDF
  - Angle: Insists on the distinction between a random variable and a numerical value throughout, with notation discipline the deck does not enforce.
  - Why this angle matters: The course is unusually strict about writing X for the variable and x for a value, and about what it means to condition a random variable on an event. That discipline is what makes later manipulations safe, and it is the habit most often missing when students find transformations confusing. Recorded lectures make it easy to see the distinction being applied rather than merely stated.
- **Pitman — Probability — Pitman — random variables and expectation**
  - Use: `book` · depth `advanced-reference` · scope `complementary`
  - Exact locator: `Ch 3 Random Variables, pdf pp. 148-268 (§3.2 Expectation p. 171; §3.3 Standard Deviation and Normal Approximation p. 194; §3.6 Symmetry p. 246)`
  - Covers: PMF, density, and CDF, Functions and transformations of random variables, Expected value and linearity, Variance, standard deviation, and covariance
  - Angle: Introduces expectation as the long-run average of repeated draws, with the frequency picture kept alongside the formula throughout.
  - Why this angle matters: Pitman consistently draws the distribution as a bar chart and marks the mean as a balance point and the standard deviation as a width, then computes. Keeping the picture attached to the symbol is why this is a good route when E[X] and Var(X) feel like formulas to memorise rather than properties of a shape. §3.3 also introduces the Normal approximation right after standard deviation, so the reason anyone cares about sigma is visible immediately. Long chapter — for L06 read §3.2 and §3.3 and stop.
  - Local target: `material://source-pitman-probability/pitman.pdf`
- **Tijms — Understanding Probability (2e) — Tijms — random variables by experiment and simulation**
  - Use: `book` · depth `advanced-reference` · scope `complementary`
  - Exact locator: `Ch 9 Basic rules for discrete random variables, pdf pp. 275-295; Ch 10 §§10.1-10.3 Continuous random variables, pdf pp. 296-324; Ch 11 §11.4 Covariance and correlation coefficient, pdf pp. 325-342`
  - Covers: PMF, density, and CDF, Expected value and linearity, Variance, standard deviation, and covariance, Chebyshev bounds and the law of large numbers
  - Angle: States each rule for expectation and variance as a numbered 'basic rule' and then immediately tests it against a simulation.
  - Why this angle matters: The chapter title is literal: the rules are enumerated and each is checked by a simulation whose code and output are shown. For a lecture whose content is a small set of algebraic identities (linearity, variance of a scaled variable, variance of a sum under independence), seeing each one confirmed numerically is a strong antidote to misremembering which of them needs independence. §11.4 gives covariance with the correlation coefficient bounded in [-1,1] and proved.
  - Local target: `material://source-tijms-understanding-probability/tijms.pdf`
- **Ross — A First Course in Probability — Ross — random-variable theory**
  - Use: `book` · depth `advanced-reference` · scope `complementary`
  - Exact locator: `Ch 4 Random Variables, pdf pp. 198-305 (§4.3 expected value; §4.4 expectation of a function of a random variable; §4.5 variance; §4.10 properties of the cumulative distribution function); Ch 7 §7.2 expectation of sums, pdf pp. 478-500`
  - Covers: Random variables and realizations, PMF, density, and CDF, Expected value and linearity, Variance, standard deviation, and covariance
  - Angle: Proves the variance identity Var(X) = E[X²] − (E[X])², which is the computational form every exercise actually uses.
  - Why this angle matters: The definition of variance is an expected squared deviation; almost every calculation uses the shortcut identity instead. Ross derives the identity from the definition rather than presenting it as an alternative formula, which is worth seeing once so that the shortcut is a theorem you can reconstruct rather than a rule you hope you remember. §4.4 is the general expectation-of-a-function rule that L06's transformations node needs; §4.10 gives the CDF its own properties list.
  - Local target: `material://source-ross-first-course/ross.pdf`
- **Harvard Stat 110 — Probability (Blitzstein) — Harvard Stat 110 Units 3–4 — RVs and expectation**
  - Use: `course` · depth `advanced-reference` · scope `complementary`
  - Exact locator: `Lectures 5-9 (random variables and their distributions, expectation, indicator random variables, LOTUS, variance)`
  - Covers: Random variables and realizations, Functions and transformations of random variables, Expected value and linearity, Variance, standard deviation, and covariance
  - Angle: Builds expectation around indicator variables, a technique that makes several otherwise hard computations trivial.
  - Why this angle matters: The 'fundamental bridge' — that the expectation of an indicator is the probability of its event — plus linearity without independence lets you compute means of complicated counts by decomposition. L06 never mentions it, but once seen it is the fastest route through a large class of exercises, and it makes linearity feel like a tool rather than an identity. Lectures run 45-50 minutes each; this is a five-lecture commitment, so choose it only if L06 is a topic you intend to be strong on.
- **SaD external German Klausur bank (local) — Leuphana-Merz pp. 5-10 — random-variable and moment items**
  - Use: `exercise` · depth `practice` · scope `complementary`
  - Exact locator: `Leuphana-Merz_Statistik-2_Uebungsbuch-mit-Klausur.pdf, pp. 5-10, Aufgabenblatt 1 random-variable items`
  - Covers: PMF, density, and CDF, Expected value and linearity, Variance, standard deviation, and covariance
  - Angle: Adds short expectation and variance calculations in German exam notation.
  - Why this angle matters: Use these for speed only after PMF/CDF and moment definitions are stable. The book's theoretical framing is broader than L06, so the locator intentionally limits the route to the first exercise block.
  - Local target: `material://source-sad-klausuren-extern/Leuphana-Merz_Statistik-2_Uebungsbuch-mit-Klausur.pdf`
- **SaD external German Klausur bank (local) — Regensburg-Löh pp. 2-5 — rigorous probability-space reference**
  - Use: `exam` · depth `advanced-reference` · scope `optional`
  - Exact locator: `Regensburg-Loeh_WTheorie-Statistik_Klausur_mit-Loesungen.pdf, pp. 2-5, Aufgaben 1-2`
  - Covers: Random variables and realizations, PMF, density, and CDF, Chebyshev bounds and the law of large numbers
  - Angle: Shows the measure-theoretic formulation behind random variables and convergence, far beyond the course's computational level.
  - Why this angle matters: This is not normal L06 practice: sigma-algebras and proof questions assume a rigorous probability course. It is retained so the owned file is visible and can answer a formal-definition question, but it should never displace Fahrmeir, Blitzstein or the current exercises.
  - Local target: `material://source-sad-klausuren-extern/Regensburg-Loeh_WTheorie-Statistik_Klausur_mit-Loesungen.pdf`
- **The Principles of Probability — From Formal Logic to Measure Theory (Springer LNM 2384) — Swanson — the measure-theoretic definition behind the random-variable language**
  - Use: `book` · depth `advanced-reference` · scope `out-of-scope`
  - Exact locator: `The Principles of Probability (LNM 2384), the chapters defining sigma-algebras, measurable functions and the abstract expectation integral`
  - Covers: Random variables and realizations, Expected value and linearity, PMF, density, and CDF
  - Angle: Says what a random variable formally is — a measurable function — which every course-level source deliberately avoids.
  - Why this angle matters: Routed here as a deliberate boundary marker, not as study material. L06 defines a random variable as 'a variable whose value depends on chance', which is a description rather than a definition, and some readers find that unsatisfying enough to be distracting. This is where the actual definition lives, along with the reason discrete and continuous cases can be treated by one integral. Reading it will cost days and will not help the exam. Open it to see that the answer exists, then close it.
  - Local target: `material://source-swanson-principles-probability/Swanson_Principles-of-Probability_LNM2384.pdf`

## L07 — SaD Lecture 07 — Discrete Distributions

**Lecture purpose.** The lecture replaces formula matching with experiment matching: each named distribution is the probability model of a particular data-generating story.

**Concept progression.**

1. **Distribution choice from assumptions** — Number of trials, independence, replacement, changing versus fixed success probability, stopping rule, and count interval determine which discrete model is valid.
2. **Bernoulli trials and the Binomial distribution** — A Bernoulli variable records one success/failure, while Binomial(n,p) counts successes in n independent trials with constant p; combinatorics explains its PMF. Builds on: Distribution choice from assumptions.
3. **Hypergeometric sampling without replacement** — Drawing from a finite population without replacement makes trials dependent and adds the finite population correction absent from the Binomial model. Builds on: Distribution choice from assumptions.
4. **Geometric waiting times** — The Geometric model counts trials until the first success, introducing a stopping-time story and the memoryless property rather than a fixed number of trials. Builds on: Bernoulli trials and the Binomial distribution.
5. **Poisson event counts** — Poisson(lambda) models independent events occurring at a stable rate in an interval, with equal expectation and variance. Builds on: Distribution choice from assumptions.
6. **Limits, approximations, and moment signatures** — Rare-event Binomials approach Poisson; distribution moments provide fast checks, but approximation conditions must be stated rather than assumed. Builds on: Bernoulli trials and the Binomial distribution, Poisson event counts.

**Complete source menu.**

### 1. Current scope and current practice

- **SaD — Statistik und Datenanalyse, lecture slides (SoSe 2026) — Current L07 discrete-distributions deck**
  - Use: `course-material` · depth `course-aligned` · scope `current`
  - Exact locator: `lecture-slides/07_discrete_distributions.pdf, 33 slides`
  - Covers: Distribution choice from assumptions, Bernoulli trials and the Binomial distribution, Hypergeometric sampling without replacement, Geometric waiting times, Poisson event counts, Limits, approximations, and moment signatures
  - Angle: Defines the identification conditions for the four discrete families, which is what the exam tests rather than the formulas.
  - Why this angle matters: Short deck, high exam density. Each distribution gets its conditions, PMF, moments and a worked example, and the final slides state the limit relationships between them. The relationships are asserted; Blitzstein §3.9 and §4.8 prove them. If time is short before the exam, the conditions slides are the ones to know cold — the formulas are recoverable, the identification is not.
- **SaD exercise sheets UE1–UE7 (SoSe 2026) — Übungsblatt 3, Aufgabe 2 — identify four discrete distributions**
  - Use: `exercise` · depth `practice` · scope `current`
  - Exact locator: `exercise-slides/Übung-3.pdf, p. 2, Aufgabe 2(a)-(d)`
  - Covers: Distribution choice from assumptions, Bernoulli trials and the Binomial distribution, Hypergeometric sampling without replacement, Geometric waiting times, Poisson event counts
  - Angle: Forces model selection from prose before any formula can be substituted.
  - Why this angle matters: This is a current assessed sheet: attempt it before opening the tutorial solution. It is scope evidence because it shows the chair's own wording, data size and expected amount of working; it is not a replacement for the lecture derivation.
  - Local target: `material://source-sad-ss26-lectures/exercise-slides/Übung-3.pdf`
- **SaD exercise sheets UE1–UE7 (SoSe 2026) — UE4, slides 36-49 — distribution conditions and worked cases**
  - Use: `exercise` · depth `practice` · scope `current`
  - Exact locator: `exercise-slides/UE4.pdf, slides 36-49`
  - Covers: Distribution choice from assumptions, Bernoulli trials and the Binomial distribution, Hypergeometric sampling without replacement, Geometric waiting times, Poisson event counts, Limits, approximations, and moment signatures
  - Angle: Puts the identifying conditions for Binomial, Hypergeometric, Geometric and Poisson side by side.
  - Why this angle matters: This is the current worked tutorial for the named task. Use it after an unaided attempt: its value is the course's calculation order and notation, while reading it first would turn an exam-relevant retrieval task into passive recognition.
  - Local target: `material://source-sad-ss26-lectures/exercise-slides/UE4.pdf`
- **SaD exercise sheets UE1–UE7 (SoSe 2026) — UE5, slides 8-11 — official discrete-distribution solutions**
  - Use: `exercise` · depth `practice` · scope `current`
  - Exact locator: `exercise-slides/UE5.pdf, slides 8-11`
  - Covers: Distribution choice from assumptions, Bernoulli trials and the Binomial distribution, Hypergeometric sampling without replacement, Poisson event counts, Limits, approximations, and moment signatures
  - Angle: Checks the model-choice reasoning against the current sheet's official solution.
  - Why this angle matters: This is the current worked tutorial for the named task. Use it after an unaided attempt: its value is the course's calculation order and notation, while reading it first would turn an exam-relevant retrieval task into passive recognition.
  - Local target: `material://source-sad-ss26-lectures/exercise-slides/UE5.pdf`

### 2. Books and independent derivations

- **Statistik: Der Weg zur Datenanalyse (9. Aufl.) — Fahrmeir Chapter 5 — discrete distributions**
  - Use: `book` · depth `derivation` · scope `complementary`
  - Exact locator: `Ch 5 §5.3 Spezielle diskrete Verteilungsmodelle, pdf pp. 270-282; Zusammenfassung pdf pp. 283-284; Aufgaben pdf pp. 286-287`
  - Covers: Distribution choice from assumptions, Bernoulli trials and the Binomial distribution, Hypergeometric sampling without replacement, Geometric waiting times, Poisson event counts
  - Angle: Presents each discrete model as a modelling decision — what generating situation forces this distribution — rather than as a formula sheet.
  - Why this angle matters: Thirteen pages covering Binomial, Hypergeometrisch, Geometrisch and Poisson, each opened with the Situation that produces it (fixed n and independence; drawing without replacement from a finite urn; waiting for the first success; rare events in continuous time). That is exactly the skill L07's model-selection node is testing, and it is the part a formula sheet cannot give you. The moments are stated without derivation — if you want the E[X] and Var(X) proofs, use Blitzstein §§3.3-3.4 and §4.7 instead. The Zusammenfassung on pp. 283-284 is the single best one-page revision table for this lecture on the shelf.
  - Local target: `material://source-fahrmeir-statistik/statistik.pdf`
- **Grinstead & Snell — Introduction to Probability (AMS, open access) — Grinstead & Snell Ch 5 — important distributions**
  - Use: `book` · depth `course-aligned` · scope `complementary`
  - Exact locator: `Ch 5 Distributions and Densities §5.1 important distributions (discrete), §5.2 important densities, with the chapter exercises`
  - Covers: Bernoulli trials and the Binomial distribution, Hypergeometric sampling without replacement, Geometric waiting times, Poisson event counts, Distribution choice from assumptions
  - Angle: Catalogues the discrete families with a simulation for each, so the shape of every distribution is seen before its formula is used.
  - Why this angle matters: The book's approach throughout is to simulate first and derive second, and for L07 that means each distribution appears as a histogram from a generating process before its PMF is written. Seeing the geometric's decay and the Poisson's shape as outputs of a described experiment is a good defence against choosing the wrong model, which is the actual exam risk here.
- **Introduction to Probability (2nd ed.) — Blitzstein Chapters 3–4 — distribution-generating stories**
  - Use: `book` · depth `intuition` · scope `complementary`
  - Exact locator: `Ch 3 §3.3 Bernoulli and Binomial, pdf pp. 129-131; §3.4 Hypergeometric, pdf pp. 132-134; §3.9 connections between Binomial and Hypergeometric, pdf pp. 150-152; Ch 4 §4.3 Geometric and Negative Binomial, pdf pp. 174-180; §4.7 Poisson, pdf pp. 191-197; §4.8 connections between Poisson and Binomial, pdf pp. 198-200`
  - Covers: Distribution choice from assumptions, Bernoulli trials and the Binomial distribution, Hypergeometric sampling without replacement, Geometric waiting times, Poisson event counts
  - Angle: Gives each distribution a story first, then derives its moments — and devotes whole sections to the relationships between them.
  - Why this angle matters: L07's relationships node — Binomial to Poisson in the rare-event limit, Hypergeometric to Binomial as the population grows — is stated on a slide as a fact. §3.9 and §4.8 are entire sections that prove those limits and say when the approximation is safe, which is the difference between reciting the relationship and being able to justify an approximation in an exam. The story-first presentation ('a Binomial counts successes in n independent trials with the same p') is also the most reliable way to get the model-selection node right under time pressure.
  - Local target: `material://source-blitzstein-hwang/blitzstein.pdf`
- **OpenIntro Statistics (4th ed.) — OpenIntro Chapter 4 — common distributions**
  - Use: `book` · depth `orientation` · scope `complementary`
  - Exact locator: `Ch 4 §4.2 geometric distribution, pdf pp. 144-148; §4.3 binomial distribution, pdf pp. 149-157; §4.4 negative binomial, pdf pp. 158-162; §4.5 Poisson distribution, pdf pp. 163-167`
  - Covers: Distribution choice from assumptions, Bernoulli trials and the Binomial distribution, Poisson event counts
  - Angle: Each distribution gets a stated checklist of conditions before its formula, which is the exact form of L07's model-selection question.
  - Why this angle matters: §4.3 opens with four numbered conditions a situation must satisfy for a binomial model to apply, and the later sections follow the same pattern. L07's model-selection node is asking precisely for that checklist, and having it in list form is more usable under exam pressure than a prose description. Hypergeometric is thin here (it lives in §3.3 as 'sampling from a small population') — Fahrmeir §5.3 or Blitzstein §3.4 covers it properly.
  - Local target: `material://source-openintro-statistics/openintro.pdf`

### 3. Visual, implementation and additional practice

- **Arbeitsbuch Statistik (Fahrmeir et al.) — Arbeitsbuch Chapter 5 — distribution drills**
  - Use: `exercise` · depth `practice` · scope `complementary`
  - Exact locator: `Ch 5 Aufgaben pdf pp. 96-104, Lösungen pdf pp. 105-123 (the Verteilungsmodell items)`
  - Covers: Distribution choice from assumptions, Bernoulli trials and the Binomial distribution, Hypergeometric sampling without replacement, Poisson event counts
  - Angle: Model-identification drill: each item describes a situation and leaves you to name the distribution before computing anything.
  - Why this angle matters: The examinable difficulty in L07 is choosing between Binomial, Hypergeometrisch, Geometrisch and Poisson from a word problem — once chosen, the arithmetic is a formula lookup. These items are written so that the choice is the work, and the solutions justify the choice rather than jumping to the formula. Do them mixed rather than in blocks; solving ten Binomial questions in a row trains nothing about identification.
  - Local target: `material://source-fahrmeir-arbeitsbuch/arbeitsbuch.pdf`
- **A Modern Introduction to Probability and Statistics — Dekking — discrete-distribution exercises**
  - Use: `exercise` · depth `practice` · scope `complementary`
  - Exact locator: `Ch 4 §4.3 Bernoulli and binomial, pdf pp. 56-58; §4.4 the geometric distribution, pdf pp. 59-61; Ch 12 the Poisson process, pdf pp. 176-188 (taking a closer look at random arrivals p. 177; the one-dimensional Poisson process p. 180)`
  - Covers: Distribution choice from assumptions, Bernoulli trials and the Binomial distribution, Hypergeometric sampling without replacement, Poisson event counts
  - Angle: Derives the Poisson distribution from the arrival process rather than defining it by its PMF.
  - Why this angle matters: Everywhere else on this shelf the Poisson distribution is defined by its formula and then motivated. Ch 12 starts from random points on a line, asks what the count in an interval must look like if arrivals are memoryless and non-simultaneous, and the PMF falls out. That is the answer to 'why is this the right model for rare events', which L07's model-selection node assumes. Longer than the alternatives and beyond exam scope in its later sections — read §12.2 and §12.3 and stop.
  - Local target: `material://source-dekking-mips/dekking.pdf`
- **MIT 18.05 Introduction to Probability and Statistics (OCW) — MIT 18.05 — discrete-distribution problems**
  - Use: `course` · depth `practice` · scope `complementary`
  - Exact locator: `Classes: Reading and In-class Materials, the 'Discrete Random Variables' readings covering Bernoulli, binomial, geometric and Poisson; Problem Set 2 with solutions`
  - Covers: Distribution choice from assumptions, Bernoulli trials and the Binomial distribution, Hypergeometric sampling without replacement, Geometric waiting times, Poisson event counts
  - Angle: Introduces each discrete family with an explicit R function name beside its formula, tying the mathematics to a computation you can run.
  - Why this angle matters: Every distribution arrives with its dbinom/pbinom-style counterpart, so a hand computation can be checked immediately. That is a small thing that removes a large class of silent errors when practising, and it also means the model-selection question can be tested empirically: simulate the described situation, compare the histogram with the candidate PMF.
- **Schaum's Outline of Probability — Schaum — discrete-distribution drills**
  - Use: `exercise` · depth `practice` · scope `complementary`
  - Exact locator: `Ch 6 Binomial, Normal and Poisson Distributions, pdf pp. 107-127`
  - Covers: Distribution choice from assumptions, Bernoulli trials and the Binomial distribution, Hypergeometric sampling without replacement, Geometric waiting times, Poisson event counts
  - Angle: Puts the three named distributions in one chapter with mixed problems, so identification is forced rather than given away by the section heading.
  - Why this angle matters: Because the binomial, Normal and Poisson share a chapter here, the end-of-chapter problems are mixed, and mixed problems are the only ones that actually train L07's model-selection node — a block of ten binomial questions trains substitution, not choice. Includes the binomial-to-Normal and binomial-to-Poisson approximation problems that L08 also needs.
  - Local target: `material://source-schaums-probability/schaums-probability.pdf`
- **StatQuest with Josh Starmer (YouTube) — StatQuest — Binomial distribution and sampling**
  - Use: `video` · depth `orientation` · scope `complementary`
  - Exact locator: `'The Binomial Distribution in 30 Seconds'; 'Sampling from a Distribution, Clearly Explained'`
  - Covers: Bernoulli trials and the Binomial distribution, Distribution choice from assumptions
  - Angle: Very short — use as a recall check between practice sets rather than as a first explanation.
  - Why this angle matters: The 30-second binomial video is exactly what it says and is best used as a spaced-repetition prompt: watch it cold and see whether you could have said the same thing. The sampling video is more substantial and explains what 'drawing from a distribution' means operationally, which matters for L11's resampling material later.
- **jbstatistics (YouTube) — jbstatistics — discrete distributions**
  - Use: `video` · depth `orientation` · scope `complementary`
  - Exact locator: `The discrete-distribution playlist: 'The Binomial Distribution', 'The Geometric Distribution', 'The Hypergeometric Distribution', 'The Poisson Distribution'`
  - Covers: Distribution choice from assumptions, Bernoulli trials and the Binomial distribution, Hypergeometric sampling without replacement, Geometric waiting times, Poisson event counts
  - Angle: One video per distribution, each opening with the conditions that must hold before the formula appears.
  - Why this angle matters: The consistent structure across the series — conditions, then PMF, then a worked example, then the moments — makes the four distributions directly comparable, which is what L07's model-selection node requires. Watching them back to back is more useful than watching any one of them, because the differences between the condition lists are the actual content.
- **Kurzes Tutorium Statistik (Bärtl, YouTube) — Kurzes Tutorium Statistik — discrete distributions**
  - Use: `video` · depth `orientation` · scope `complementary`
  - Exact locator: `'Binomialverteilung'; 'Hypergeometrische Verteilung'; 'Poissonverteilung'`
  - Covers: Distribution choice from assumptions, Bernoulli trials and the Binomial distribution, Hypergeometric sampling without replacement, Poisson event counts
  - Angle: Names the German distribution vocabulary and the Ziehen-mit/ohne-Zurücklegen phrasing that identifies each model in an exam question.
  - Why this angle matters: German exam questions signal the intended distribution through fixed phrases — 'mit Zurücklegen', 'ohne Zurücklegen', 'in einem festen Zeitintervall'. These videos use exactly those phrases while deriving each model, which turns the phrase into a reliable trigger. That mapping is not available in any of the English sources.
- **Brandon Foltz — Statistics 101 (YouTube channel) — Brandon Foltz — Poisson distribution walkthrough**
  - Use: `video` · depth `orientation` · scope `complementary`
  - Exact locator: `'Introduction to the Poisson Distribution' (≈25 min)`
  - Covers: Poisson event counts
  - Angle: A slow, single-topic walkthrough for when the shorter explanations have not worked.
  - Why this angle matters: Foltz's videos are two to three times longer than StatQuest's on the same topic, and that is their purpose: he restates each step several ways and works a full example without skipping arithmetic. Routed here as the fallback route for L07's hardest single distribution — if the short explanations have already landed, skip it, because the length is real.

### 4. University courses, prior-year, exam and advanced reference

- **SaD 2025 lecture recordings (WiSe 2025 run) — 2025 discrete-distributions deck**
  - Use: `course-material` · depth `advanced-reference` · scope `prior-year`
  - Exact locator: `07_discrete_distributions.pptx (1).pdf`
  - Covers: Distribution choice from assumptions, Bernoulli trials and the Binomial distribution, Hypergeometric sampling without replacement, Poisson event counts
  - Angle: Same-topic prior-year deck with a different set of worked examples.
  - Why this angle matters: The examples differ from 2026's even where the content matches, which makes this a source of extra worked cases at exactly the right level — closer to the course than any textbook. Verify the formulas against the current deck; notation drifts year to year.
- **FAU Erlangen Statistik-Klausur WS14/15 (mit Lösungen) — FAU pp. 5 and 22 — Binomial model and quantile**
  - Use: `exercise` · depth `practice` · scope `complementary`
  - Exact locator: `FAU-Erlangen_Statistik-Klausur_WS14-15_mit-Loesungen.pdf, p. 5 Aufgabe 1(5), solution p. 22`
  - Covers: Distribution choice from assumptions, Bernoulli trials and the Binomial distribution, Limits, approximations, and moment signatures
  - Angle: Requires both a point probability and a cumulative/quantile decision for a named Binomial variable.
  - Why this angle matters: The distribution is named, so this is calculation and quantile practice rather than model identification. It is best used after mixed-distribution tasks, as a speed check.
  - Local target: `material://source-fau-klausur-ws1415/FAU-Erlangen_Statistik-Klausur_WS14-15_mit-Loesungen.pdf`
- **Pitman — Probability — Pitman Chapters 2–3 — discrete distributions**
  - Use: `book` · depth `advanced-reference` · scope `complementary`
  - Exact locator: `Ch 2 §2.1 The Binomial Distribution, pdf pp. 90-102; §2.4 Poisson Approximation, pdf pp. 127-147; Ch 3 §3.4 Discrete Distributions, pdf pp. 217-230; §3.5 The Poisson Distribution, pdf pp. 231-245`
  - Covers: Bernoulli trials and the Binomial distribution, Hypergeometric sampling without replacement, Geometric waiting times, Poisson event counts
  - Angle: Reaches the Poisson twice — once as a limit of the Binomial, once as a distribution in its own right — several chapters apart.
  - Why this angle matters: §2.4 derives the Poisson as what the Binomial becomes when n grows and p shrinks with np fixed, with the error of the approximation discussed; §3.5, much later, treats the Poisson as a first-class distribution with its own moments. Meeting it in both roles is the clearest way to hold L07's relationships node, which asserts the limit on one slide. §3.4 collects the discrete families with a comparison of their shapes.
  - Local target: `material://source-pitman-probability/pitman.pdf`
- **Tijms — Understanding Probability (2e) — Tijms — discrete-distribution modeling examples**
  - Use: `book` · depth `advanced-reference` · scope `complementary`
  - Exact locator: `Ch 9 Basic rules for discrete random variables, pdf pp. 275-295; Ch 4 Rare events and lotteries, pdf pp. 115-152`
  - Covers: Distribution choice from assumptions, Bernoulli trials and the Binomial distribution, Hypergeometric sampling without replacement, Geometric waiting times, Poisson event counts
  - Angle: Ch 4 is an entire chapter of rare-event modelling — the Poisson's natural habitat — before the distribution is ever defined formally.
  - Why this angle matters: Lottery coincidences, near-misses and clusters, worked out with counts and simulations. It is the most convincing answer available to why the Poisson deserves its own model rather than being a Binomial special case, which is what L07's model-selection node needs you to have internalised. Read it for the modelling judgment, not for formulas — the formal statements are in Ch 9.
  - Local target: `material://source-tijms-understanding-probability/tijms.pdf`
- **Ross — A First Course in Probability — Ross — named discrete distributions**
  - Use: `book` · depth `advanced-reference` · scope `complementary`
  - Exact locator: `Ch 4 Random Variables, pdf pp. 198-305 (§4.6 the Bernoulli and binomial random variables; §4.7 the Poisson random variable; §4.8.1 geometric; §4.8.3 hypergeometric)`
  - Covers: Bernoulli trials and the Binomial distribution, Hypergeometric sampling without replacement, Geometric waiting times, Poisson event counts, Limits, approximations, and moment signatures
  - Angle: Derives every moment rather than tabulating it, so E[X] and Var(X) for each family can be reconstructed instead of recalled.
  - Why this angle matters: Where Fahrmeir tabulates the moments and OpenIntro states them, Ross computes each one from the PMF, usually with a slick algebraic step worth learning on its own (the index shift in the binomial mean, the derivative trick for the geometric). If the exam permits no formula sheet, being able to rebuild one moment from its PMF is a genuine safety net. §4.7.1 also covers computing the distribution function without overflow, which is a numerical aside but explains the recursive forms that appear in software.
  - Local target: `material://source-ross-first-course/ross.pdf`
- **Harvard Stat 110 — Probability (Blitzstein) — Harvard Stat 110 Units 3–4 — discrete distributions**
  - Use: `course` · depth `advanced-reference` · scope `complementary`
  - Exact locator: `Lectures 6-8 (Bernoulli, binomial, hypergeometric, geometric, Poisson) plus the published 'Table of Distributions' handout`
  - Covers: Distribution choice from assumptions, Bernoulli trials and the Binomial distribution, Hypergeometric sampling without replacement, Geometric waiting times, Poisson event counts
  - Angle: Each distribution is given a one-sentence 'story' that determines when it applies — the compressed form of the model-selection skill.
  - Why this angle matters: Blitzstein's stories ('a hypergeometric counts the successes when you sample without replacement from a finite population containing a known number of successes') are short enough to memorise and complete enough to decide a modelling question. Learning the five stories is a far better use of an hour than learning the five PMFs, because the PMF follows from the story and the identification does not. The published distribution-summary sheet tabulates all of them with moments.
- **SaD external German Klausur bank (local) — Leuphana-Merz pp. 11-16 — discrete distribution selection**
  - Use: `exercise` · depth `practice` · scope `complementary`
  - Exact locator: `Leuphana-Merz_Statistik-2_Uebungsbuch-mit-Klausur.pdf, pp. 11-16, Aufgabenblatt 2`
  - Covers: Distribution choice from assumptions, Bernoulli trials and the Binomial distribution, Hypergeometric sampling without replacement, Geometric waiting times, Poisson event counts, Limits, approximations, and moment signatures
  - Angle: A mixed block where Binomial, Hypergeometric and Poisson models must be identified from context.
  - Why this angle matters: Unlike a chapter-end single-distribution drill, this block mixes families and therefore tests the L07 decision step. Check each parameterization against the 2026 deck because notation varies across German courses.
  - Local target: `material://source-sad-klausuren-extern/Leuphana-Merz_Statistik-2_Uebungsbuch-mit-Klausur.pdf`

## L08 — SaD Lecture 08 — Normal Distribution, CLT & Likelihood

**Lecture purpose.** The lecture explains why Normal models dominate sampling-based inference and connects probabilistic data models to the optimization objectives used in regression and machine learning.

**Concept progression.**

1. **The Normal family and its parameters** — Mean locates the bell curve and variance controls spread; symmetry, density, and the 68-95-99.7 rule support qualitative checks before calculation.
2. **Standardization, CDFs, and quantiles** — Z=(X-mu)/sigma maps any Normal variable to N(0,1), enabling probability and inverse-probability calculations through Phi and its quantiles. Builds on: The Normal family and its parameters.
3. **Linear transforms and sums of independent Normals** — Affine transformations change mean and variance predictably, and independent Normal sums remain Normal with variances adding. Builds on: The Normal family and its parameters.
4. **Law of large numbers versus central limit theorem** — The LLN concerns convergence of an average to its expectation; the CLT concerns the approximately Normal shape and scale of its sampling fluctuations.
5. **Normal approximation and continuity correction** — Sums and counts may be approximated by a Normal law when conditions are adequate; discrete boundaries require a continuity correction and approximation error remains explicit. Builds on: Standardization, CDFs, and quantiles, Law of large numbers versus central limit theorem.
6. **Probability versus likelihood** — A probability distribution varies data with parameters fixed; a likelihood treats observed data as fixed and compares parameter values by how well they explain it. Builds on: The Normal family and its parameters.
7. **Maximum likelihood and the MSE bridge** — Maximizing a product of densities becomes maximizing a log-likelihood; Gaussian error assumptions turn this into minimizing squared residuals. Builds on: Probability versus likelihood.

**Complete source menu.**

### 1. Current scope and current practice

- **SaD — Statistik und Datenanalyse, lecture slides (SoSe 2026) — Current L08 Normal, CLT, and likelihood deck**
  - Use: `course-material` · depth `course-aligned` · scope `current`
  - Exact locator: `lecture-slides/08_normal_distribution.pdf, 38 slides`
  - Covers: The Normal family and its parameters, Standardization, CDFs, and quantiles, Linear transforms and sums of independent Normals, Law of large numbers versus central limit theorem, Normal approximation and continuity correction, Probability versus likelihood, Maximum likelihood and the MSE bridge
  - Angle: Two lectures in one deck: Normal calculations and the CLT, then likelihood and the derivation that turns maximum likelihood into least squares.
  - Why this angle matters: The Gaussian-error derivation at the end is the intellectual centre of the statistics half — it is where L03's least-squares choice is finally justified — and it arrives after the CLT material when attention is lowest. Budget a separate session for the likelihood slides. The LLN-versus-CLT slides are the other high-risk part; they are correct but terse. Dekking Ch 13-14 and Ch 21 cover both halves in the same notation.
- **SaD exercise sheets UE1–UE7 (SoSe 2026) — Blatt 4, Aufgaben 1 and 3 — Normal calculations and CLT simulation**
  - Use: `exercise` · depth `practice` · scope `current`
  - Exact locator: `exercise-slides/Statistics_And_Data_Science.pdf, pp. 1 and 3, Aufgaben 1 and 3`
  - Covers: The Normal family and its parameters, Standardization, CDFs, and quantiles, Linear transforms and sums of independent Normals, Law of large numbers versus central limit theorem, Normal approximation and continuity correction
  - Angle: Pairs table-based Normal calculations with a simulation that reveals when the CLT approximation works.
  - Why this angle matters: This is a current assessed sheet: attempt it before opening the tutorial solution. It is scope evidence because it shows the chair's own wording, data size and expected amount of working; it is not a replacement for the lecture derivation. The file's printed sheet number is absent; content identifies it as the current Blatt 4, and that naming uncertainty remains recorded.
  - Local target: `material://source-sad-ss26-lectures/exercise-slides/Statistics_And_Data_Science.pdf`
- **SaD exercise sheets UE1–UE7 (SoSe 2026) — UE5, slides 20-38 — Normal, standardization and CLT walkthrough**
  - Use: `exercise` · depth `practice` · scope `current`
  - Exact locator: `exercise-slides/UE5.pdf, slides 20-38`
  - Covers: The Normal family and its parameters, Standardization, CDFs, and quantiles, Linear transforms and sums of independent Normals, Law of large numbers versus central limit theorem, Normal approximation and continuity correction
  - Angle: Gives a visual, calculation-first bridge from z-scores to sample-mean normality.
  - Why this angle matters: This is the current worked tutorial for the named task. Use it after an unaided attempt: its value is the course's calculation order and notation, while reading it first would turn an exam-relevant retrieval task into passive recognition.
  - Local target: `material://source-sad-ss26-lectures/exercise-slides/UE5.pdf`
- **SaD exercise sheets UE1–UE7 (SoSe 2026) — UE6, slides 5-20 — official Blatt 4 Normal/CLT solutions**
  - Use: `exercise` · depth `practice` · scope `current`
  - Exact locator: `exercise-slides/UE6.pdf, slides 5-20`
  - Covers: The Normal family and its parameters, Standardization, CDFs, and quantiles, Law of large numbers versus central limit theorem, Normal approximation and continuity correction
  - Angle: Supplies the current official numerical solutions and the code shape for the CLT experiment.
  - Why this angle matters: This is the current worked tutorial for the named task. Use it after an unaided attempt: its value is the course's calculation order and notation, while reading it first would turn an exam-relevant retrieval task into passive recognition.
  - Local target: `material://source-sad-ss26-lectures/exercise-slides/UE6.pdf`

### 2. Books and independent derivations

- **Statistik: Der Weg zur Datenanalyse (9. Aufl.) — Fahrmeir Chapters 6–7 — Normal distribution and limit theorems**
  - Use: `book` · depth `derivation` · scope `complementary`
  - Exact locator: `Ch 6 §6.3 Spezielle stetige Verteilungsmodelle, pdf pp. 310-322 (Normalverteilung); Ch 7 §7.1 Grenzwertsätze, pdf pp. 330-336; §7.2 Approximation von Verteilungen, pdf pp. 337-338; Tabelle A Standardnormalverteilung, pdf p. 631`
  - Covers: The Normal family and its parameters, Standardization, CDFs, and quantiles, Linear transforms and sums of independent Normals, Law of large numbers versus central limit theorem, Normal approximation and continuity correction
  - Angle: The only route here that also hands you the z-table you will actually use, in the layout the Klausur uses.
  - Why this angle matters: §6.3 defines the Normal family and standardisation in German notation; §7.1 separates the Gesetz der großen Zahlen from the Zentraler Grenzwertsatz, which is the single most confused pair in this lecture; §7.2 states the approximation rules with the Stetigkeitskorrektur that English texts often omit. Then p. 631 is the Standardnormalverteilung table itself — practising lookups against the table you will be given matters more than it sounds, because reading Φ backwards for a quantile is a distinct skill from reading it forwards. Contains no likelihood or MLE: for the L08 likelihood half use Dekking Ch 21.
  - Local target: `material://source-fahrmeir-statistik/statistik.pdf`
- **Grinstead & Snell — Introduction to Probability (AMS, open access) — Grinstead & Snell Ch 8-9 — law of large numbers and the central limit theorem**
  - Use: `book` · depth `derivation` · scope `complementary`
  - Exact locator: `Ch 8 Law of Large Numbers §§8.1-8.2 and Ch 9 Central Limit Theorem §§9.1-9.3, with the chapter exercises`
  - Covers: Law of large numbers versus central limit theorem, Normal approximation and continuity correction, The Normal family and its parameters
  - Angle: Gives the LLN and the CLT a chapter each, so the two limit theorems can never be read as one.
  - Why this angle matters: Conflating the law of large numbers with the central limit theorem is the standard L08 error, and a chapter boundary is the strongest structural defence against it. Ch 8 proves the weak law from Chebyshev; Ch 9 states the CLT for the Bernoulli case first, where it can be checked numerically, then generalises. Ch 9's discrete-case treatment includes the continuity correction with its justification, which most texts state as a rule.
- **Introduction to Probability (2nd ed.) — Blitzstein Chapters 5 and 10 — continuous variables and CLT**
  - Use: `book` · depth `intuition` · scope `complementary`
  - Exact locator: `Ch 5 §5.1 probability density functions, pdf pp. 230-236; §5.4 Normal, pdf pp. 248-254; Ch 10 §10.1 inequalities, pdf pp. 475-483; §10.2 law of large numbers, pdf pp. 484-487; §10.3 central limit theorem, pdf pp. 488-493; exercises §10.7 pdf pp. 503-513`
  - Covers: The Normal family and its parameters, Linear transforms and sums of independent Normals, Law of large numbers versus central limit theorem
  - Angle: Puts the LLN and the CLT in one chapter with the inequalities that bound them, so the two limit theorems are compared rather than met separately.
  - Why this angle matters: The single most common L08 misconception is that the CLT is a stronger version of the LLN. Ch 10 makes them adjacent sections making visibly different claims — the LLN about where the sample mean goes, the CLT about the shape of its fluctuation around that point — and the proximity does the teaching. §10.1 supplies Markov, Chebyshev and Jensen with proofs, which is where L06's concentration node also points. §5.4 derives the standardisation identity rather than asserting it. No likelihood content: for L08's MLE half use Dekking Ch 21.
  - Local target: `material://source-blitzstein-hwang/blitzstein.pdf`
- **OpenIntro Statistics (4th ed.) — OpenIntro Chapter 4 — Normal and sampling distributions**
  - Use: `book` · depth `orientation` · scope `complementary`
  - Exact locator: `Ch 4 §4.1 normal distribution, pdf pp. 133-143 (Z-scores, percentiles, 68-95-99.7 rule); Ch 5 §5.1 point estimates and sampling variability, pdf pp. 170-180 (the sampling distribution of the mean and the CLT statement)`
  - Covers: The Normal family and its parameters, Standardization, CDFs, and quantiles, Law of large numbers versus central limit theorem, Normal approximation and continuity correction
  - Angle: Builds the CLT out of a simulation the reader can picture — repeated samples, one histogram of their means — before any statement of the theorem.
  - Why this angle matters: §5.1 shows the sampling distribution being constructed by repetition, so 'the distribution of the sample mean' becomes a concrete object rather than a phrase. That picture is what makes the standard error formula in L09 obviously about a distribution of means rather than of data. §4.1 drills z-score conversion in both directions with a table, which is the mechanical L08 skill. No likelihood content and no proof of the CLT — deliberately, since the course does not need one.
  - Local target: `material://source-openintro-statistics/openintro.pdf`

### 3. Visual, implementation and additional practice

- **Arbeitsbuch Statistik (Fahrmeir et al.) — Arbeitsbuch Chapters 6–7 — Normal and CLT drills**
  - Use: `exercise` · depth `practice` · scope `complementary`
  - Exact locator: `Ch 6 Aufgaben pdf pp. 124-133, Lösungen pdf pp. 134-157; Ch 7 Aufgaben pdf pp. 158-160, Lösungen pdf pp. 161-164`
  - Covers: Standardization, CDFs, and quantiles, Law of large numbers versus central limit theorem, Normal approximation and continuity correction
  - Angle: Normal-table lookups and CLT approximations worked to the digit, including the continuity correction.
  - Why this angle matters: Two mechanical skills decide the L08 questions: reading Φ in both directions, and knowing when a Binomial may be replaced by a Normal and what the ±0.5 correction does to the answer. Both are drilled here with full arithmetic, so a wrong answer can be traced to the exact step. Ch 7's approximation items are the ones to prioritise if time is short.
  - Local target: `material://source-fahrmeir-arbeitsbuch/arbeitsbuch.pdf`
- **A Modern Introduction to Probability and Statistics — Dekking — Normal and CLT exercises**
  - Use: `exercise` · depth `practice` · scope `complementary`
  - Exact locator: `Ch 5 §5.5 the normal distribution, pdf pp. 74-75; Ch 13 the law of large numbers, pdf pp. 189-202 (Chebyshev p. 191; LLN p. 193; consequences p. 196; exercises p. 199); Ch 14 the central limit theorem, pdf pp. 203-213 (standardizing averages p. 203; applications p. 207; exercises p. 211); Ch 21 maximum likelihood, pdf pp. 317-331 (likelihood and loglikelihood p. 320; properties p. 325; exercises p. 327)`
  - Covers: Standardization, CDFs, and quantiles, Linear transforms and sums of independent Normals, Law of large numbers versus central limit theorem, Normal approximation and continuity correction
  - Angle: The one route that covers both halves of L08 — the limit theorems and maximum likelihood — in the same book and notation.
  - Why this angle matters: L08 is really two lectures: Normal/CLT, and likelihood/MLE. Almost every other source covers one or the other. Dekking has consecutive chapters for the first (13 and 14, deliberately separated so the LLN and CLT are never conflated) and a dedicated chapter for the second, using one notation throughout. Ch 21 also does what the deck skips — works the loglikelihood transformation explicitly and explains why maximising the log is legitimate, which is the step where students lose the thread when they meet the Gaussian-error derivation.
  - Local target: `material://source-dekking-mips/dekking.pdf`
- **MIT 18.05 Introduction to Probability and Statistics (OCW) — MIT 18.05 — Normal and CLT notes/exams**
  - Use: `course` · depth `practice` · scope `complementary`
  - Exact locator: `Classes: Reading and In-class Materials: the 'Central Limit Theorem and the Law of Large Numbers' reading and the 'Maximum Likelihood Estimates' reading; the published exam questions and solutions on the Exams page`
  - Covers: The Normal family and its parameters, Standardization, CDFs, and quantiles, Law of large numbers versus central limit theorem, Normal approximation and continuity correction
  - Angle: The only route here whose likelihood reading is written specifically to separate likelihood from probability, in one page.
  - Why this angle matters: L08's likelihood node turns on one distinction — the same expression read as a function of the data versus as a function of the parameter — and 18.05's MLE reading opens with exactly that before any optimisation. Combined with the CLT/LLN reading, this covers both halves of L08 with the same notation. The Exams page then supplies solved questions of both kinds under timed conditions, which is the closest thing on the shelf to an English-language SaD mock.
- **Schaum's Outline of Probability — Schaum — Normal and CLT drills**
  - Use: `exercise` · depth `practice` · scope `complementary`
  - Exact locator: `Ch 6 Binomial, Normal and Poisson Distributions, pdf pp. 107-127 (the Normal approximation problems)`
  - Covers: Standardization, CDFs, and quantiles, Linear transforms and sums of independent Normals, Law of large numbers versus central limit theorem, Normal approximation and continuity correction
  - Angle: Normal-table drill with the approximation conditions and the continuity correction applied problem by problem.
  - Why this angle matters: The mechanical half of L08 — convert to z, read the table, apply the ±0.5 correction, check that np and n(1−p) are large enough — is trained here at volume and nowhere else on the shelf as cheaply. No CLT theory and no likelihood; this route is calculation practice only, and should be paired with Dekking Ch 13-14 for the reasoning.
  - Local target: `material://source-schaums-probability/schaums-probability.pdf`
- **StatQuest with Josh Starmer (YouTube) — StatQuest — CLT, likelihood, and maximum likelihood**
  - Use: `video` · depth `orientation` · scope `complementary`
  - Exact locator: `'The Central Limit Theorem, Clearly Explained'; 'Probability is not Likelihood'; 'Maximum Likelihood, Clearly Explained' (≈12 min each)`
  - Covers: Law of large numbers versus central limit theorem, Probability versus likelihood, Maximum likelihood and the MSE bridge
  - Angle: 'Probability is not Likelihood' isolates L08's hardest distinction into a single dedicated video.
  - Why this angle matters: The likelihood-versus-probability confusion is the reason L08's second half is hard, and it is a distinction about which quantity is held fixed, not about any formula. This video does nothing else for eight minutes: same curve, same expression, read twice. Watch it before reading Dekking Ch 21 and the chapter becomes straightforward. The CLT video uses the same repeated-sampling animation OpenIntro describes in text.
- **jbstatistics (YouTube) — jbstatistics — Normal, z-scores, and CLT**
  - Use: `video` · depth `orientation` · scope `complementary`
  - Exact locator: `'The Normal Distribution', 'Standardizing Normally Distributed Random Variables', 'Introduction to the Central Limit Theorem'`
  - Covers: Standardization, CDFs, and quantiles, Law of large numbers versus central limit theorem, Normal approximation and continuity correction
  - Angle: Drills the standard-normal table in both directions, including finding a value from a given probability.
  - Why this angle matters: Reading the table backwards — given a tail probability, find z — is a distinct skill and the one L09's confidence intervals will immediately depend on. The videos work several of each direction, which is more repetition than any text here provides in that specific operation.
- **Kurzes Tutorium Statistik (Bärtl, YouTube) — Kurzes Tutorium Statistik — Normalverteilung and ZGS**
  - Use: `video` · depth `orientation` · scope `complementary`
  - Exact locator: `'Normalverteilung'; 'Standardnormalverteilung'; 'Zentraler Grenzwertsatz'`
  - Covers: The Normal family and its parameters, Standardization, CDFs, and quantiles, Law of large numbers versus central limit theorem
  - Angle: Reads the German z-table layout, which is arranged differently from the tables in the English texts.
  - Why this angle matters: The Standardnormalverteilung table you will be given is the German layout, and practising lookups against an American table is a small but real mismatch. These videos use the German one and read it in both directions. Fahrmeir p. 631 is the same table in print.

### 4. University courses, prior-year, exam and advanced reference

- **SaD 2025 lecture recordings (WiSe 2025 run) — 2025 Normal-distribution deck**
  - Use: `course-material` · depth `advanced-reference` · scope `prior-year`
  - Exact locator: `08_normal_distribution_no_notes.pdf`
  - Covers: The Normal family and its parameters, Standardization, CDFs, and quantiles, Law of large numbers versus central limit theorem
  - Angle: Prior-year Normal/CLT deck, without the annotation layer.
  - Why this angle matters: No spoken notes in this file, so its value is limited to the alternative worked examples and the different ordering. Lower priority than the annotated 2025 files.
- **MIT 6.041SC — Probabilistic Systems Analysis and Applied Probability (Tsitsiklis, OCW) — MIT 6.041SC — limit theorems lectures**
  - Use: `course` · depth `course-aligned` · scope `complementary`
  - Exact locator: `The limit-theorems lectures (weak law of large numbers; central limit theorem) with their recitations`
  - Covers: Law of large numbers versus central limit theorem, Normal approximation and continuity correction
  - Angle: States precisely what each limit theorem does and does not claim, with counterexamples to the usual misreadings.
  - Why this angle matters: Tsitsiklis spends time on what the CLT does not say — that it is a statement about the distribution of the standardised sum, not about the sum itself, and that it says nothing about the tails at any finite n. Those clarifications prevent the two most common wrong applications. Comes with recitations that apply the theorems to concrete approximation problems.
- **Pitman — Probability — Pitman — Normal and limit-theorem selections**
  - Use: `book` · depth `advanced-reference` · scope `complementary`
  - Exact locator: `Ch 2 §2.2 Normal Approximation: Method, pdf pp. 103-118; §2.3 Normal Approximation: Derivation (optional), pdf pp. 119-126; Ch 4 Continuous Distributions, pdf pp. 269-330`
  - Covers: The Normal family and its parameters, Standardization, CDFs, and quantiles, Law of large numbers versus central limit theorem
  - Angle: Splits the Normal approximation into a 'method' section and an optional 'derivation' section, so the mechanics and the proof are cleanly separable.
  - Why this angle matters: §2.2 gives the recipe with the continuity correction and worked lookups — exactly what the exam needs — and §2.3 then derives it, marked optional by the author. That division lets you take only the first half now and come back for the second if the CLT's origin nags. Pitman also introduces the Normal before continuous random variables in general, which is unusual and works well here: the shape is motivated by the approximation problem instead of appearing as one density among many.
  - Local target: `material://source-pitman-probability/pitman.pdf`
- **Tijms — Understanding Probability (2e) — Tijms — LLN and CLT intuition**
  - Use: `book` · depth `advanced-reference` · scope `complementary`
  - Exact locator: `Ch 5 Probability and statistics, pdf pp. 153-217 (§5.8 the central limit theorem and random walks); Ch 10 §10.2 Important probability densities, pdf pp. 296-324`
  - Covers: Law of large numbers versus central limit theorem, Normal approximation and continuity correction
  - Angle: Demonstrates the CLT by simulation across several different starting distributions, so the universality claim is seen rather than asserted.
  - Why this angle matters: The striking part of the CLT is that the starting distribution does not matter, and that is exactly the part a formula cannot convey. Tijms runs the same averaging experiment on visibly different distributions and shows the same Normal shape emerging each time. §5.9 on Benford's law and §5.10 are outside SaD scope but are short and make the point that a limit theorem is a claim about the world. No likelihood content.
  - Local target: `material://source-tijms-understanding-probability/tijms.pdf`
- **Ross — A First Course in Probability — Ross — Normal distribution and limit theorems**
  - Use: `book` · depth `advanced-reference` · scope `complementary`
  - Exact locator: `Ch 5 Continuous Random Variables, pdf pp. 306-378 (§5.4 normal random variables; §5.7 the distribution of a function of a random variable); Ch 8 Limit Theorems, pdf pp. 617-660 (§8.2 Chebyshev's inequality and the weak law; §8.3 the central limit theorem)`
  - Covers: The Normal family and its parameters, Linear transforms and sums of independent Normals, Law of large numbers versus central limit theorem
  - Angle: Proves the CLT, and states Chebyshev, the weak law and the CLT as a single graded sequence of limit theorems.
  - Why this angle matters: Ch 8 is the only route here that gives a proof of the central limit theorem, and more usefully it arranges the results as an escalation: Chebyshev bounds the deviation crudely, the weak law turns that bound into convergence in probability, and the CLT then describes the exact limiting shape. That ordering is the answer to 'why do we need the CLT when we already have Chebyshev', which the lecture does not address. Above SaD's required level — read it if the LLN/CLT distinction is still unstable after Dekking Ch 13-14.
  - Local target: `material://source-ross-first-course/ross.pdf`
- **Harvard Stat 110 — Probability (Blitzstein) — Harvard Stat 110 Units 5–6 — Normal and CLT**
  - Use: `course` · depth `advanced-reference` · scope `complementary`
  - Exact locator: `Lectures 14-16 (continuous distributions and the Normal) and Lectures 19-20 (law of large numbers, central limit theorem)`
  - Covers: The Normal family and its parameters, Linear transforms and sums of independent Normals, Law of large numbers versus central limit theorem
  - Angle: Derives the Normal's normalising constant and standardisation rather than asserting them.
  - Why this angle matters: The Gaussian integral trick and the change of variables that turns any Normal into a standard Normal are both done on the board. Neither is examinable in SaD, but the second one is the reason the z-table works for every Normal, and knowing that removes the temptation to memorise separate procedures. The LLN/CLT lectures compare the two theorems explicitly, in the same framing the book uses in Ch 10.
- **MIT 18.650 — Statistics for Applications (Rigollet, OCW) — MIT 18.650 Lectures 4–5 — maximum likelihood**
  - Use: `course` · depth `advanced-reference` · scope `complementary`
  - Exact locator: `Lectures 4-5 (maximum likelihood estimation, the method of moments); graduate-level treatment, use for a diagnosed gap only`
  - Covers: Probability versus likelihood, Maximum likelihood and the MSE bridge
  - Angle: The formal estimation-theory framing of likelihood: identifiability, the Fisher information, asymptotic normality of the MLE.
  - Why this angle matters: This is a mathematical-statistics course and sits well above SaD. It is routed here for one situation only: the L08 slides derive the MLE for a specific model and you want to know what the general theory guarantees — that the estimator is consistent and asymptotically Normal, and under what conditions. Reading it will not help with the exam, and it will cost hours. Reference-only by design.
- **SaD external German Klausur bank (local) — Leuphana-Merz pp. 11-16 — Normal and sampling-distribution items**
  - Use: `exercise` · depth `practice` · scope `complementary`
  - Exact locator: `Leuphana-Merz_Statistik-2_Uebungsbuch-mit-Klausur.pdf, pp. 11-16, Aufgabenblatt 2 Normal/CLT items`
  - Covers: The Normal family and its parameters, Standardization, CDFs, and quantiles, Linear transforms and sums of independent Normals, Law of large numbers versus central limit theorem, Normal approximation and continuity correction
  - Angle: Connects standardized Normal calculations to sums and sample statistics in a compact solved block.
  - Why this angle matters: The benefit is transfer between distribution recognition and calculation. It is not the source for L08 likelihood or MLE; those nodes remain with the deck, MIT 18.650 and the dedicated derivation sources.
  - Local target: `material://source-sad-klausuren-extern/Leuphana-Merz_Statistik-2_Uebungsbuch-mit-Klausur.pdf`
- **SaD external German Klausur bank (local) — Regensburg-Löh pp. 6-8 — LLN/CLT proof reference**
  - Use: `exam` · depth `advanced-reference` · scope `optional`
  - Exact locator: `Regensburg-Loeh_WTheorie-Statistik_Klausur_mit-Loesungen.pdf, pp. 6-8, convergence tasks`
  - Covers: Law of large numbers versus central limit theorem, Normal approximation and continuity correction
  - Angle: Provides a rigorous statement-and-proof view of convergence laws that the course uses computationally.
  - Why this angle matters: This route is deliberately reference-only. It can clarify assumptions and modes of convergence, but its proof burden is outside the SaD exam and would be harmful as ordinary preparation.
  - Local target: `material://source-sad-klausuren-extern/Regensburg-Loeh_WTheorie-Statistik_Klausur_mit-Loesungen.pdf`

## L09 — SaD Lecture 09 — Point & Interval Estimation

**Lecture purpose.** The lecture formalizes the jump from a finite sample to an unknown population parameter and makes uncertainty part of the estimate rather than an afterthought.

**Concept progression.**

1. **Statistics, estimators, and estimates** — An estimator is a rule applied to random samples and is therefore random; an estimate is its realized numerical value for one observed sample.
2. **Bias, consistency, efficiency, and mean squared error** — Good estimators trade systematic error and variability; MSE decomposes into variance plus squared bias, while consistency describes large-sample convergence. Builds on: Statistics, estimators, and estimates.
3. **Sampling distributions and standard errors** — The standard error is the standard deviation of an estimator's sampling distribution and usually shrinks with sample size; it is not the spread of the raw data. Builds on: Statistics, estimators, and estimates.
4. **z confidence intervals** — With known population variance or an adequate Normal approximation, estimate plus/minus a z quantile times standard error gives a repeated-sampling coverage procedure. Builds on: Sampling distributions and standard errors.
5. **t confidence intervals** — Estimating variance from small samples introduces extra uncertainty captured by Student's t and its degrees of freedom. Builds on: z confidence intervals.
6. **Bootstrap estimation** — Resampling observations with replacement approximates an estimator's sampling distribution when a convenient analytic standard error is unavailable. Builds on: Sampling distributions and standard errors.
7. **Statistical uncertainty versus data bias** — Narrow intervals cannot repair selection bias, measurement error, dependence, or population drift; the inferential model is only as credible as its sampling assumptions. Builds on: Bias, consistency, efficiency, and mean squared error.

**Complete source menu.**

### 1. Current scope and current practice

- **SaD — Statistik und Datenanalyse, lecture slides (SoSe 2026) — Current L09 estimation deck**
  - Use: `course-material` · depth `course-aligned` · scope `current`
  - Exact locator: `lecture-slides/09_estimating.pdf, 45 slides`
  - Covers: Statistics, estimators, and estimates, Bias, consistency, efficiency, and mean squared error, Sampling distributions and standard errors, z confidence intervals, t confidence intervals, Bootstrap estimation, Statistical uncertainty versus data bias
  - Angle: The exam-notation authority for estimator properties and the z/t/bootstrap interval formulas.
  - Why this angle matters: The deck presents properties and intervals together, so the interval formulas can be learned without the sampling-distribution reasoning that justifies them — which works until a question varies the setup. Fahrmeir §9.2 separates the two deliberately. The final slides on statistical uncertainty versus biased data are conceptual, not computational, and are the kind of point that appears as a short written question.
- **SaD exercise sheets UE1–UE7 (SoSe 2026) — Blatt 4, Aufgabe 2 — point estimate, bootstrap and interval**
  - Use: `exercise` · depth `practice` · scope `current`
  - Exact locator: `exercise-slides/Statistics_And_Data_Science.pdf, p. 2, Aufgabe 2`
  - Covers: Statistics, estimators, and estimates, Bias, consistency, efficiency, and mean squared error, Sampling distributions and standard errors, z confidence intervals, Bootstrap estimation
  - Angle: Makes the estimator/standard-error/interval chain concrete in one data-analysis task.
  - Why this angle matters: This is a current assessed sheet: attempt it before opening the tutorial solution. It is scope evidence because it shows the chair's own wording, data size and expected amount of working; it is not a replacement for the lecture derivation. The generic filename is retained because the PDF itself has no recoverable sheet number.
  - Local target: `material://source-sad-ss26-lectures/exercise-slides/Statistics_And_Data_Science.pdf`
- **SaD exercise sheets UE1–UE7 (SoSe 2026) — UE5, slides 40-77 — estimation, standard error and bootstrap intervals**
  - Use: `exercise` · depth `practice` · scope `current`
  - Exact locator: `exercise-slides/UE5.pdf, slides 40-77`
  - Covers: Statistics, estimators, and estimates, Bias, consistency, efficiency, and mean squared error, Sampling distributions and standard errors, z confidence intervals, t confidence intervals, Bootstrap estimation
  - Angle: Shows the whole inferential chain with one repeated dataset, including what the bootstrap is estimating.
  - Why this angle matters: This is the current worked tutorial for the named task. Use it after an unaided attempt: its value is the course's calculation order and notation, while reading it first would turn an exam-relevant retrieval task into passive recognition.
  - Local target: `material://source-sad-ss26-lectures/exercise-slides/UE5.pdf`
- **SaD exercise sheets UE1–UE7 (SoSe 2026) — UE6, slides 10-13 — official bootstrap confidence-interval solution**
  - Use: `exercise` · depth `practice` · scope `current`
  - Exact locator: `exercise-slides/UE6.pdf, slides 10-13`
  - Covers: Sampling distributions and standard errors, z confidence intervals, Bootstrap estimation
  - Angle: Provides the official short-form answer expected for the current interval question.
  - Why this angle matters: This is the current worked tutorial for the named task. Use it after an unaided attempt: its value is the course's calculation order and notation, while reading it first would turn an exam-relevant retrieval task into passive recognition.
  - Local target: `material://source-sad-ss26-lectures/exercise-slides/UE6.pdf`

### 2. Books and independent derivations

- **Statistik: Der Weg zur Datenanalyse (9. Aufl.) — Fahrmeir Chapter 9 — parameter estimation**
  - Use: `book` · depth `derivation` · scope `complementary`
  - Exact locator: `Ch 9 §9.1 Punktschätzung, pdf pp. 383-385; §9.2 Eigenschaften von Schätzstatistiken, pdf pp. 386-393; §9.3 Konstruktion von Schätzfunktionen, pdf pp. 394-402; §9.4 Intervallschätzung, pdf pp. 403-410; Aufgaben pdf pp. 413-415`
  - Covers: Statistics, estimators, and estimates, Bias, consistency, efficiency, and mean squared error, Sampling distributions and standard errors, z confidence intervals, t confidence intervals
  - Angle: Estimator quality before estimator recipes: bias, consistency and efficiency are defined and compared in §9.2 before any interval formula appears.
  - Why this angle matters: L09 introduces estimator properties and confidence intervals in the same pass, which makes it easy to learn the interval formulas as rituals. Fahrmeir spends eight pages on Erwartungstreue, Konsistenz, Effizienz and MSE with worked comparisons of competing estimators BEFORE §9.4 derives an interval, so the interval arrives as a consequence of a sampling distribution rather than as a boxed formula. §9.3 covers the Maximum-Likelihood and Momenten construction methods, which is the bridge back to L08's MLE node. Use the German property names from here — the Klausur asks for 'erwartungstreu', not 'unbiased'.
  - Local target: `material://source-fahrmeir-statistik/statistik.pdf`
- **OpenIntro Statistics (4th ed.) — OpenIntro Chapter 5 — confidence intervals**
  - Use: `book` · depth `orientation` · scope `complementary`
  - Exact locator: `Ch 5 §5.1 point estimates and sampling variability, pdf pp. 170-180; §5.2 confidence intervals for a proportion, pdf pp. 181-188; Ch 7 §7.1 one-sample means with the t-distribution, pdf pp. 251-261`
  - Covers: Sampling distributions and standard errors, z confidence intervals, t confidence intervals
  - Angle: Introduces confidence intervals on a proportion first, where the standard error has no nuisance parameter to estimate.
  - Why this angle matters: By starting with a proportion, §5.2 gets to a complete interval before the reader has to deal with an unknown sigma, so the interpretation of 'confident' can be discussed on its own. Then §7.1 introduces the t-distribution specifically as the correction needed once sigma is estimated — which is exactly the z-versus-t decision L09 asks you to make, presented as a consequence rather than a rule. The repeated-interval simulation picture in §5.2 is also the standard defence against the classic misinterpretation the exam likes to test.
  - Local target: `material://source-openintro-statistics/openintro.pdf`

### 3. Visual, implementation and additional practice

- **Arbeitsbuch Statistik (Fahrmeir et al.) — Arbeitsbuch Chapter 9 — estimation drills**
  - Use: `exercise` · depth `practice` · scope `complementary`
  - Exact locator: `Ch 9 Aufgaben pdf pp. 180-187, Lösungen pdf pp. 188-199`
  - Covers: Bias, consistency, efficiency, and mean squared error, Sampling distributions and standard errors, z confidence intervals, t confidence intervals
  - Angle: Confidence intervals computed under all three regimes — known sigma, unknown sigma, proportions — with the choice justified each time.
  - Why this angle matters: The recurring L09 exam failure is using z where t belongs, or the wrong standard-error formula for a proportion. These solutions state the regime check before every computation, so the habit being trained is the check rather than the substitution. Also includes sample-size determination items, which the lecture treats lightly but which are cheap marks when they appear.
  - Local target: `material://source-fahrmeir-arbeitsbuch/arbeitsbuch.pdf`
- **A Modern Introduction to Probability and Statistics — Dekking — estimation exercises**
  - Use: `exercise` · depth `practice` · scope `complementary`
  - Exact locator: `Ch 19 unbiased estimators, pdf pp. 291-303; Ch 20 efficiency and mean squared error, pdf pp. 304-316 (variance of an estimator p. 307; MSE p. 310; exercises p. 312); Ch 18 the bootstrap, pdf pp. 275-290 (bootstrap principle p. 275; empirical bootstrap p. 278; exercises p. 286); Ch 23 confidence intervals for the mean, pdf pp. 344-363 (normal data p. 348; bootstrap confidence intervals p. 353); Ch 24 §24.1 the probability of success, pdf pp. 364-366`
  - Covers: Bias, consistency, efficiency, and mean squared error, Sampling distributions and standard errors, z confidence intervals, t confidence intervals
  - Angle: The only source here that gives the bootstrap its own chapter with a stated principle, instead of one slide of procedure.
  - Why this angle matters: L09 shows the bootstrap as a resampling recipe. Ch 18 states the bootstrap principle first — replace the unknown true distribution by the empirical one, then do exactly what you would have done — and only then gives the algorithm, which is what makes it transferable to a situation the recipe does not cover. §23.3 then builds a bootstrap confidence interval, closing the loop to the z/t intervals in §23.2 so the three interval methods sit side by side. Chapters 19 and 20 separate unbiasedness from efficiency, which the lecture presents together.
  - Local target: `material://source-dekking-mips/dekking.pdf`
- **zedstatistics (Justin Zeltzer, YouTube channel) — zedstatistics — confidence intervals**
  - Use: `video` · depth `intuition` · scope `complementary`
  - Exact locator: `The confidence-interval videos (interpretation, construction, and the t-distribution), ≈15-20 min each`
  - Covers: Sampling distributions and standard errors, z confidence intervals, t confidence intervals
  - Angle: Opens with the standard misinterpretation stated plainly, then dismantles it — which is more memorable than stating the correct version first.
  - Why this angle matters: Most treatments give the correct interpretation and warn against the wrong one in a footnote. Zeltzer inverts it: he states the tempting reading ('95% chance the parameter is in here'), shows with repeated sampling why it cannot be right, and only then gives the correct one. Since the misinterpretation is the examinable point, attacking it directly is the better route.
- **MIT 18.05 Introduction to Probability and Statistics (OCW) — MIT 18.05 — estimation and confidence intervals**
  - Use: `course` · depth `practice` · scope `complementary`
  - Exact locator: `Classes: Reading and In-class Materials, the 'Bootstrapping' reading and the 'Confidence Intervals' readings I-III; the corresponding problem sets with solutions`
  - Covers: Statistics, estimators, and estimates, Sampling distributions and standard errors, z confidence intervals, t confidence intervals
  - Angle: Teaches bootstrap confidence intervals as a first-class method beside the analytic ones, with runnable code.
  - Why this angle matters: Most courses mention the bootstrap; this one builds intervals with it and compares them against the z and t intervals on the same data. Seeing the three agree — and seeing where they disagree — is what turns L09's bootstrap node from a curiosity into a method with a place. The reading also separates the frequentist confidence interval from the Bayesian probability interval explicitly, which prevents the most common interpretation error.
- **StatQuest with Josh Starmer (YouTube) — StatQuest — standard error, confidence intervals, and bootstrap**
  - Use: `video` · depth `orientation` · scope `complementary`
  - Exact locator: `'Standard Error, Clearly Explained'; 'Confidence Intervals, Clearly Explained'; 'Bootstrapping, Clearly Explained'`
  - Covers: Sampling distributions and standard errors, z confidence intervals, Bootstrap estimation
  - Angle: Distinguishes the standard deviation from the standard error explicitly, which the lecture's notation blurs.
  - Why this angle matters: sigma and sigma/sqrt(n) look similar on a slide and mean entirely different things — the spread of the data versus the spread of an estimate. The video separates them with two visibly different histograms, and once separated the confidence-interval formula stops looking arbitrary. The bootstrapping video then shows the resampling loop being run, which is the procedural half of L09's bootstrap node.
- **jbstatistics (YouTube) — jbstatistics — t distribution and confidence intervals**
  - Use: `video` · depth `orientation` · scope `complementary`
  - Exact locator: `'Introduction to Confidence Intervals' and 'Introduction to the t Distribution', with the interval-construction videos that follow them`
  - Covers: Sampling distributions and standard errors, z confidence intervals, t confidence intervals
  - Angle: Explains why the t-distribution has heavier tails as a consequence of estimating sigma, not as a property to accept.
  - Why this angle matters: The t-distribution is usually introduced as 'use this when sigma is unknown', which gives no reason for its shape. The videos connect the extra uncertainty of estimating sigma to the heavier tails and thus to the wider interval, which makes the z-versus-t decision a reasoned one and much harder to get wrong under pressure.
- **Kurzes Tutorium Statistik (Bärtl, YouTube) — Kurzes Tutorium Statistik — Konfidenzintervalle**
  - Use: `video` · depth `orientation` · scope `complementary`
  - Exact locator: `Die Videos 'Konfidenzintervall' und 'Konfidenzintervall berechnen'`
  - Covers: Sampling distributions and standard errors, z confidence intervals, t confidence intervals
  - Angle: German terminology for interval estimation — Konfidenzniveau, Vertrauensbereich, Schätzfunktion.
  - Why this angle matters: L09's German vocabulary is denser than most: erwartungstreu, konsistent, effizient, Stichprobenumfang, Konfidenzniveau. Having heard the words used in a worked calculation makes the exam phrasing readable at speed. Fahrmeir §9.4 is the print equivalent with more depth.
- **Brandon Foltz — Statistics 101 (YouTube channel) — Brandon Foltz — confidence-interval walkthroughs**
  - Use: `video` · depth `orientation` · scope `complementary`
  - Exact locator: `'Confidence Intervals' parts 1-3 (≈25-30 min each)`
  - Covers: Sampling distributions and standard errors, z confidence intervals, t confidence intervals
  - Angle: Spends most of a video on interpretation — what a 95% interval does and does not claim — before any computation.
  - Why this angle matters: The standard misinterpretation ('there is a 95% probability the parameter is in this interval') is the most commonly examined conceptual point in L09, and it survives most brief treatments. Foltz attacks it directly and at length, with the repeated-sampling picture. Worth the time once.

### 4. University courses, prior-year, exam and advanced reference

- **SaD 2025 lecture recordings (WiSe 2025 run) — 2025 point and interval estimation deck**
  - Use: `course-material` · depth `advanced-reference` · scope `prior-year`
  - Exact locator: `09_point_interval_estimation (1).pdf`
  - Covers: Statistics, estimators, and estimates, Bias, consistency, efficiency, and mean squared error, Sampling distributions and standard errors, z confidence intervals, t confidence intervals
  - Angle: Prior-year estimation deck with additional worked interval examples.
  - Why this angle matters: Estimation is a topic where extra worked examples at course level are genuinely scarce — the textbooks either drill mechanically or theorise. This deck sits at the right level. Confirm the interval formulas and notation against the 2026 deck first.
- **An Introduction to Statistical Learning (Python edition) — ISLP 5.2 - the bootstrap as a resampling estimate of standard error**
  - Use: `book` · depth `practice` · scope `complementary`
  - Exact locator: `Section 5.2 the bootstrap, pp. 220-223; lab section 5.3, pp. 223-231; exercises section 5.4, p. 232`
  - Covers: Bootstrap estimation
  - Angle: L09 introduces the bootstrap as a way to quantify uncertainty without a formula; this section builds the resampled standard error on a concrete estimator and then repeats it in a lab, which is the arithmetic the deck asserts.
  - Why this angle matters: §5.2 (pp. 220-223) states the bootstrap in three pages with the resampling diagram, then the lab (pp. 223-231) runs it in code on a real estimator so the sampling distribution is produced rather than described. L09 presents the bootstrap as a procedure; seeing the resampled estimates accumulate into a histogram is what makes the standard-error claim believable. Exercises at p. 232. Read Dekking Ch 18 first for the principle, then this for the execution.
  - Local target: `material://source-islp/islp.pdf`
- **MIT 18.650 — Statistics for Applications (Rigollet, OCW) — MIT 18.650 Lectures 3–5 — parametric inference**
  - Use: `course` · depth `advanced-reference` · scope `complementary`
  - Exact locator: `Lectures 3-5 (parametric estimation, confidence intervals, the delta method); graduate-level, reference only`
  - Covers: Statistics, estimators, and estimates, Bias, consistency, efficiency, and mean squared error, Sampling distributions and standard errors
  - Angle: Says what 'efficient' means precisely, via the Cramér-Rao bound that SaD's efficiency node alludes to without naming.
  - Why this angle matters: L09 says one estimator can be more efficient than another and leaves efficiency comparative. 18.650 gives the absolute version: there is a variance floor for unbiased estimators, and an estimator attaining it is efficient in a precise sense. That is satisfying and entirely optional — nothing in the M2 exam requires it. Come here only if the comparative statement bothered you.
- **SaD external German Klausur bank (local) — Leuphana-Merz pp. 17-27 — estimation and confidence intervals**
  - Use: `exercise` · depth `practice` · scope `complementary`
  - Exact locator: `Leuphana-Merz_Statistik-2_Uebungsbuch-mit-Klausur.pdf, pp. 17-27, Aufgabenblätter 3-4`
  - Covers: Statistics, estimators, and estimates, Bias, consistency, efficiency, and mean squared error, Sampling distributions and standard errors, z confidence intervals, t confidence intervals
  - Angle: A full progression from sample functions and point estimates to mean, variance and proportion intervals.
  - Why this angle matters: Page 23 begins Aufgabenblatt 4 on interval estimation and visibly distinguishes known-sigma, estimated-sigma and proportion regimes. This is the strongest local external practice for selecting the correct interval, but it does not cover the bootstrap.
  - Local target: `material://source-sad-klausuren-extern/Leuphana-Merz_Statistik-2_Uebungsbuch-mit-Klausur.pdf`

## L10 — SaD Lecture 10 — Statistical Hypothesis Testing

**Lecture purpose.** The lecture converts a scientific claim into a controlled decision under uncertainty, separating evidence against a null model from the probability that a substantive theory is true.

**Concept progression.**

1. **Null model, alternative, statistic, and reference distribution** — A test specifies a falsifiable null, an alternative, a statistic computed from the sample, and the statistic's distribution if the null were true.
2. **Tails, critical regions, and p-values** — The alternative determines one- versus two-sided evidence; a p-value is the null probability of a result at least as extreme, not the probability that the null is true. Builds on: Null model, alternative, statistic, and reference distribution.
3. **Type I error, Type II error, and power** — Alpha controls false rejection under the null, beta describes missed effects under an alternative, and power depends on effect size, noise, sample size, and the decision threshold. Builds on: Tails, critical regions, and p-values.
4. **z and t tests for means** — Standardized mean differences use z when variance assumptions justify it and t when variance is estimated; paired and independent designs require different standard errors. Builds on: Null model, alternative, statistic, and reference distribution.
5. **Confidence intervals and test duality** — A two-sided level-alpha test rejects exactly the parameter values outside the matching 1-alpha confidence interval under the same assumptions. Builds on: z and t tests for means.
6. **Chi-square tests for categorical data** — Observed and expected counts support goodness-of-fit and independence tests, with degrees of freedom and count-size assumptions controlling the reference approximation. Builds on: Null model, alternative, statistic, and reference distribution.
7. **Rank and permutation tests** — Rank tests reduce distributional assumptions, while permutation tests construct a null distribution from exchangeability by reassigning labels. Builds on: Null model, alternative, statistic, and reference distribution.
8. **Multiple testing and false discoveries** — Repeating tests inflates the chance of at least one false positive; family-wise and false-discovery controls answer different error-management questions. Builds on: Type I error, Type II error, and power.

**Complete source menu.**

### 1. Current scope and current practice

- **SaD — Statistik und Datenanalyse, lecture slides (SoSe 2026) — Current L10 hypothesis-testing deck**
  - Use: `course-material` · depth `course-aligned` · scope `current`
  - Exact locator: `lecture-slides/10_testing.pdf, 65 slides`
  - Covers: Null model, alternative, statistic, and reference distribution, Tails, critical regions, and p-values, Type I error, Type II error, and power, z and t tests for means, Confidence intervals and test duality, Chi-square tests for categorical data, Rank and permutation tests, Multiple testing and false discoveries
  - Angle: The largest deck in the module and the complete course logic of testing, from null models to multiple testing.
  - Why this angle matters: Sixty-five slides introducing the entire testing vocabulary at once — null model, statistic, reference distribution, tails, p-value, both error types, power, z/t, chi-square, nonparametric alternatives, confidence-interval duality and multiplicity. The volume is the difficulty. Dekking's two-chapter split (Ch 25 essentials, Ch 26 elaboration) is the standard way to take the same content in two passes. Duality and multiple testing are both exam-favoured and both sit at the end of the deck.
- **SaD exercise sheets UE1–UE7 (SoSe 2026) — Blatt 5, Aufgabe 1 — permutation test and t-test comparison**
  - Use: `exercise` · depth `practice` · scope `current`
  - Exact locator: `exercise-slides/blatt-05.pdf, pp. 1-2, Aufgabe 1(a)-(d)`
  - Covers: Null model, alternative, statistic, and reference distribution, Tails, critical regions, and p-values, Type I error, Type II error, and power, z and t tests for means, Rank and permutation tests
  - Angle: Makes the null/alternative, p-value decision and parametric/nonparametric comparison one coherent task.
  - Why this angle matters: This is a current assessed sheet: attempt it before opening the tutorial solution. It is scope evidence because it shows the chair's own wording, data size and expected amount of working; it is not a replacement for the lecture derivation.
  - Local target: `material://source-sad-ss26-lectures/exercise-slides/blatt-05.pdf`
- **SaD exercise sheets UE1–UE7 (SoSe 2026) — UE6, slides 23-38 — permutation and two-sample t tests**
  - Use: `exercise` · depth `practice` · scope `current`
  - Exact locator: `exercise-slides/UE6.pdf, slides 23-38`
  - Covers: Null model, alternative, statistic, and reference distribution, Tails, critical regions, and p-values, Type I error, Type II error, and power, z and t tests for means, Rank and permutation tests
  - Angle: Presents both procedures on matched questions, exposing which assumptions change and which decision logic does not.
  - Why this angle matters: This is the current worked tutorial for the named task. Use it after an unaided attempt: its value is the course's calculation order and notation, while reading it first would turn an exam-relevant retrieval task into passive recognition.
  - Local target: `material://source-sad-ss26-lectures/exercise-slides/UE6.pdf`
- **SaD exercise sheets UE1–UE7 (SoSe 2026) — UE7, slides 12-16 — official Blatt 5 testing solution**
  - Use: `exercise` · depth `practice` · scope `current`
  - Exact locator: `exercise-slides/UE7.pdf, slides 12-16`
  - Covers: Null model, alternative, statistic, and reference distribution, Tails, critical regions, and p-values, z and t tests for means, Rank and permutation tests
  - Angle: Shows the complete answer structure the current course accepts for a test decision.
  - Why this angle matters: This is the current worked tutorial for the named task. Use it after an unaided attempt: its value is the course's calculation order and notation, while reading it first would turn an exam-relevant retrieval task into passive recognition.
  - Local target: `material://source-sad-ss26-lectures/exercise-slides/UE7.pdf`

### 2. Books and independent derivations

- **Statistik: Der Weg zur Datenanalyse (9. Aufl.) — Fahrmeir Chapters 10–11 — hypothesis tests**
  - Use: `book` · depth `derivation` · scope `complementary`
  - Exact locator: `Ch 10 §10.1 Der Binomial- und der Gauß-Test, pdf pp. 417-429; §10.2 Prinzipien des Testens, pdf pp. 430-444; §10.3 Multiple Testprobleme, pdf pp. 445-446; Ch 11 §11.2 Ein-Stichproben-Fall, pdf pp. 452-469; §11.5 Zusammenhangsanalyse, pdf pp. 482-485`
  - Covers: Null model, alternative, statistic, and reference distribution, Tails, critical regions, and p-values, Type I error, Type II error, and power, z and t tests for means, Chi-square tests for categorical data, Rank and permutation tests
  - Angle: Teaches one concrete test end to end first, then generalises the principle — the reverse of the lecture's order, and the better order when the logic will not click.
  - Why this angle matters: L10 opens with the abstract null-model/statistic/reference-distribution machinery and then instantiates it. Fahrmeir §10.1 does the opposite: it runs the Gauß-Test completely — hypotheses, statistic, critical region, decision — and only then does §10.2 extract Fehler 1./2. Art, Güte and the p-Wert as principles from the worked case. If the abstract version did not land in the lecture, this inversion is the reason to come here rather than to OpenIntro. §11.5 supplies the χ²-Unabhängigkeitstest and the correlation test; §10.3 is two pages on multiple testing, enough for the exam but thinner than ISLP Ch 13.
  - Local target: `material://source-fahrmeir-statistik/statistik.pdf`
- **Introduction to Probability (2nd ed.) — Blitzstein §10.4 — where the t and chi-square distributions come from**
  - Use: `book` · depth `derivation` · scope `complementary`
  - Exact locator: `Ch 10 §10.4 Chi-Square and Student-t, pdf pp. 494-496`
  - Covers: z and t tests for means, Chi-square tests for categorical data
  - Angle: Defines the t and chi-square distributions constructively out of Normals, instead of introducing them as table lookups.
  - Why this angle matters: L10 uses both as reference distributions and never says what they are. Three pages here define chi-square as a sum of squared standard Normals and t as a standard Normal divided by the root of an independent chi-square over its degrees of freedom. That is what makes 'degrees of freedom' a quantity rather than a column heading, and it explains why the t approaches the Normal as n grows. Background, not exam-bearing — read it once.
  - Local target: `material://source-blitzstein-hwang/blitzstein.pdf`
- **OpenIntro Statistics (4th ed.) — OpenIntro Chapters 5–7 — tests by data type**
  - Use: `book` · depth `orientation` · scope `complementary`
  - Exact locator: `Ch 5 §5.3 hypothesis testing for a proportion, pdf pp. 189-205; Ch 6 §6.3 testing for goodness of fit using chi-square, pdf pp. 229-239; §6.4 testing for independence in two-way tables, pdf pp. 240-248; Ch 7 §7.1 one-sample means with the t-distribution, pdf pp. 251-261; §7.4 power calculations, pdf pp. 278-284`
  - Covers: Null model, alternative, statistic, and reference distribution, Tails, critical regions, and p-values, z and t tests for means, Chi-square tests for categorical data
  - Angle: Teaches the p-value through randomisation before any reference distribution appears, and has the only real power section on the shelf.
  - Why this angle matters: §5.3 builds the null distribution by shuffling the data — the malaria-vaccine simulation from Ch 2 — so a p-value is first seen as a proportion of shuffles at least as extreme as the observed result. Once that is concrete, the z and t reference distributions are recognisable as shortcuts for the same quantity. §7.4 then does what almost nothing else here does: computes power and required sample size explicitly, rather than defining power and moving on. §§6.3-6.4 cover both chi-square variants that L10 names.
  - Local target: `material://source-openintro-statistics/openintro.pdf`

### 3. Visual, implementation and additional practice

- **Arbeitsbuch Statistik (Fahrmeir et al.) — Arbeitsbuch Chapters 10–11 — testing drills**
  - Use: `exercise` · depth `practice` · scope `complementary`
  - Exact locator: `Ch 10 Aufgaben pdf pp. 200-205, Lösungen pdf pp. 206-218; Ch 11 Aufgaben pdf pp. 219-226, Lösungen pdf pp. 227-242`
  - Covers: Null model, alternative, statistic, and reference distribution, Tails, critical regions, and p-values, z and t tests for means, Chi-square tests for categorical data, Rank and permutation tests
  - Angle: Complete test write-ups in German exam form: hypotheses, statistic, critical value, decision, sentence.
  - Why this angle matters: A German statistics exam awards marks for the shape of the answer, not only the number — stating H0 and H1 formally, naming the test, giving the critical value, and closing with a sentence that answers the question in context. These solutions are written in exactly that form, which makes them a template as much as an answer key. Ch 11 extends to the two-sample and χ² cases; do Ch 10 first and only reach Ch 11 if the exercises show those tests are in scope.
  - Local target: `material://source-fahrmeir-arbeitsbuch/arbeitsbuch.pdf`
- **A Modern Introduction to Probability and Statistics — Dekking — hypothesis-testing exercises**
  - Use: `exercise` · depth `practice` · scope `complementary`
  - Exact locator: `Ch 25 testing hypotheses: essentials, pdf pp. 375-384 (null hypothesis and test statistic p. 375; tail probabilities p. 378; type I and II errors p. 379; exercises p. 382); Ch 26 testing hypotheses: elaboration, pdf pp. 385-399 (significance level p. 385; critical region p. 388; type II error p. 392; relation with confidence intervals p. 394); Ch 27 the t-test, pdf pp. 400-414`
  - Covers: Null model, alternative, statistic, and reference distribution, Tails, critical regions, and p-values, z and t tests for means, Chi-square tests for categorical data
  - Angle: Splits testing across two chapters — essentials, then elaboration — so the vocabulary is not all introduced at once.
  - Why this angle matters: L10 introduces null model, statistic, tails, p-value, both error types, power, and duality inside one lecture, and the vocabulary load is the real difficulty. Dekking's split means Ch 25 gets you to a decision with only three of those ideas, and Ch 26 revisits the same example to add significance level, critical region, type II error and the confidence-interval duality one at a time. §26.4 on duality is the clearest statement of that equivalence on the shelf, and duality is a recurring exam question. Ch 27 works the t-test in a regression setting as well as the one-sample case.
  - Local target: `material://source-dekking-mips/dekking.pdf`
- **zedstatistics (Justin Zeltzer, YouTube channel) — zedstatistics — hypothesis testing and p-values**
  - Use: `video` · depth `intuition` · scope `complementary`
  - Exact locator: `The hypothesis-testing and p-value videos, ≈15-25 min each`
  - Covers: Null model, alternative, statistic, and reference distribution, Tails, critical regions, and p-values, Type I error, Type II error, and power
  - Angle: Treats the p-value as a conditional probability and keeps naming what it is conditioned on, which is where most confusion lives.
  - Why this angle matters: 'Probability of data this extreme GIVEN the null is true' — the conditioning clause is the whole content, and it is the clause that gets dropped when the definition is recited. The videos repeat it every time the quantity is used, which is a small pedagogical choice with a large effect. Pairs well with OpenIntro §5.3's randomisation construction.
- **MIT 18.05 Introduction to Probability and Statistics (OCW) — MIT 18.05 — hypothesis-testing notes and solved exams**
  - Use: `course` · depth `practice` · scope `complementary`
  - Exact locator: `Classes: Reading and In-class Materials: the 'Null Hypothesis Significance Testing' readings (I, II, III) and the chi-square reading; the Exams page for solved test questions`
  - Covers: Null model, alternative, statistic, and reference distribution, Tails, critical regions, and p-values, Type I error, Type II error, and power, z and t tests for means, Chi-square tests for categorical data
  - Angle: Splits NHST across three consecutive readings, and closes with an explicit critique of p-values that the lecture only gestures at.
  - Why this angle matters: Reading I sets up the machinery, II adds the error types and power, III covers the multiple-test and replication problems including a frank discussion of what a p-value does not tell you. That third part is the intellectual content behind L10's multiple-testing node, and it is what makes the difference between reciting the false-discovery definition and understanding why the topic is in the lecture at all. Solved timed questions on the Exams page.
- **StatQuest with Josh Starmer (YouTube) — StatQuest — hypothesis tests and p-values**
  - Use: `video` · depth `orientation` · scope `complementary`
  - Exact locator: `'Hypothesis Testing and the Null Hypothesis'; 'p-values, Clearly Explained'; 'How to Calculate p-values'; 'One- or Two-Tailed p-values'`
  - Covers: Null model, alternative, statistic, and reference distribution, Tails, critical regions, and p-values
  - Angle: A four-video sequence that separates what a p-value is from how it is computed and from how many tails to use.
  - Why this angle matters: Those three questions get conflated in a single lecture and each is a separate source of lost marks. Splitting them across four short videos means each can be checked independently: do I know what the number means, can I produce it, and did I choose the right tail count for this alternative. The one-or-two-tailed video in particular addresses the decision the exam most often penalises.
- **jbstatistics (YouTube) — jbstatistics — hypothesis-testing calculations**
  - Use: `video` · depth `orientation` · scope `complementary`
  - Exact locator: `'Introduction to Hypothesis Testing', 'What is a p-value?', and the Type I / Type II error videos in the same playlist`
  - Covers: Null model, alternative, statistic, and reference distribution, Tails, critical regions, and p-values, z and t tests for means
  - Angle: Insists on stating H0 and H1 before anything else, every single time, which is the marking-scheme habit.
  - Why this angle matters: The repetition is the pedagogy here: every example in the series begins by writing the hypotheses formally, in symbols, before touching the data. German exam marking awards points for that step independently of the arithmetic, so the habit converts directly into marks.
- **Kurzes Tutorium Statistik (Bärtl, YouTube) — Kurzes Tutorium Statistik — Hypothesentests**
  - Use: `video` · depth `orientation` · scope `complementary`
  - Exact locator: `'Hypothesentest'; 'p-Wert'; 'Fehler 1. und 2. Art'`
  - Covers: Null model, alternative, statistic, and reference distribution, Tails, critical regions, and p-values, z and t tests for means
  - Angle: States the Fehler 1./2. Art distinction in German with the standard table, which is a near-certain exam item.
  - Why this angle matters: Type I and type II errors are asked in almost every German statistics exam and are asked in German. The two-by-two table (Entscheidung × Wahrheit) is the answer format, and these videos build it. Short; watch alongside the Fahrmeir Arbeitsbuch Ch 10 solutions for the written form.
- **Brandon Foltz — Statistics 101 (YouTube channel) — Brandon Foltz — hypothesis-testing walkthroughs**
  - Use: `video` · depth `orientation` · scope `complementary`
  - Exact locator: `'Hypothesis Testing' parts 1-3 and the 'Statistical Power' videos (≈25-30 min each)`
  - Covers: Null model, alternative, statistic, and reference distribution, Tails, critical regions, and p-values, z and t tests for means
  - Angle: Walks a complete test end to end without cuts, including the parts other explanations skip as obvious.
  - Why this angle matters: Useful specifically when a worked solution loses you at a step everyone else treats as trivial — choosing the critical value, deciding the direction, writing the conclusion. Foltz does not skip those. Long; use as a repair route rather than a first pass.

### 4. University courses, prior-year, exam and advanced reference

- **SaD 2025 lecture recordings (WiSe 2025 run) — 2025 statistical-significance deck**
  - Use: `course-material` · depth `advanced-reference` · scope `prior-year`
  - Exact locator: `10_statistical_significance.pdf`
  - Covers: Null model, alternative, statistic, and reference distribution, Tails, critical regions, and p-values, Type I error, Type II error, and power
  - Angle: Prior-year testing deck, titled around significance rather than testing.
  - Why this angle matters: The different title reflects a different emphasis: 2025 organised the lecture around what significance means, 2026 around the testing procedure. Reading both gives two framings of the same material, which is useful for a topic this conceptually slippery.
- **An Introduction to Statistical Learning (Python edition) — ISLP Ch 13 - the multiple-testing slide worked out with labs and exercises**
  - Use: `book` · depth `practice` · scope `complementary`
  - Exact locator: `Chapter 13, pp. 563-602 (false discovery rate p. 564; family-wise error rate p. 571; Bonferroni and Holm p. 573; Benjamini-Hochberg p. 581; lab section 13.6 p. 589; exercises section 13.7 p. 599)`
  - Covers: Multiple testing and false discoveries
  - Angle: L10's closing slides name family-wise error and false discoveries and stop; this chapter separates the two error-management questions, gives Bonferroni and Holm for FWER and Benjamini-Hochberg for FDR, and ends with a lab and exercise set - the only registered practice for the node.
  - Why this angle matters: The most complete multiple-testing treatment on the shelf, and L10's multiplicity node is one slide. The page map matters: family-wise error rate (p. 571) and Bonferroni/Holm (p. 573) are the conservative classical corrections; false discovery rate (p. 564) and Benjamini-Hochberg (p. 581) are the modern alternative that controls a different quantity entirely. Understanding that FWER and FDR are different targets — not competing approximations of one target — is the conceptual point, and it is the kind of distinction a written exam question can turn on. Lab at p. 589, exercises at p. 599.
  - Local target: `material://source-islp/islp.pdf`
- **FAU Erlangen Statistik-Klausur WS14/15 (mit Lösungen) — FAU pp. 20/45 and 25/50 — one-sided correlation test**
  - Use: `exercise` · depth `practice` · scope `complementary`
  - Exact locator: `FAU-Erlangen_Statistik-Klausur_WS14-15_mit-Loesungen.pdf, p. 20 Aufgabe 4(8), repeated p. 45; solutions pp. 25 and 50`
  - Covers: Null model, alternative, statistic, and reference distribution, Tails, critical regions, and p-values, Type I error, Type II error, and power, z and t tests for means
  - Angle: A real test of whether a population correlation exceeds 0.8, including hypotheses, statistic and decision.
  - Why this angle matters: This item was previously misused as L03 support, but bivariate-normal assumptions and a correlation hypothesis test make it L10 work. Use it to practise a complete one-sided decision; the specialized correlation-test formula may be beyond the exact 2026 formula sheet.
  - Local target: `material://source-fau-klausur-ws1415/FAU-Erlangen_Statistik-Klausur_WS14-15_mit-Loesungen.pdf`
- **MIT 18.650 — Statistics for Applications (Rigollet, OCW) — MIT 18.650 Lectures 7–12 — tests and goodness-of-fit**
  - Use: `course` · depth `advanced-reference` · scope `complementary`
  - Exact locator: `Lectures 7-12 (hypothesis testing, the Neyman-Pearson framework, chi-square and goodness-of-fit tests); graduate-level, reference only`
  - Covers: Null model, alternative, statistic, and reference distribution, Type I error, Type II error, and power, z and t tests for means, Chi-square tests for categorical data
  - Angle: Derives why the standard tests take the form they do, via the Neyman-Pearson lemma that no SaD material mentions.
  - Why this angle matters: SaD hands you a catalogue of tests and their statistics. Neyman-Pearson answers the question the catalogue provokes — where did these particular statistics come from, and in what sense are they the best available — by showing that the likelihood ratio is the optimal test statistic for a simple hypothesis pair. Genuinely interesting and genuinely out of scope; six lectures.
- **SaD external German Klausur bank (local) — Leuphana-Merz pp. 28-40 — parametric, two-sample and goodness-of-fit tests**
  - Use: `exercise` · depth `practice` · scope `complementary`
  - Exact locator: `Leuphana-Merz_Statistik-2_Uebungsbuch-mit-Klausur.pdf, pp. 28-40, Aufgabenblätter 5-6`
  - Covers: Null model, alternative, statistic, and reference distribution, Tails, critical regions, and p-values, Type I error, Type II error, and power, z and t tests for means, Confidence intervals and test duality, Chi-square tests for categorical data, Rank and permutation tests
  - Angle: Supplies full German test write-ups across several test families, with solutions.
  - Why this angle matters: This is the widest local testing bank: one- and two-sample tests plus goodness-of-fit/chi-square work. Use the problems to practise test selection and complete written decisions; skip procedures not named in the 2026 L10 deck.
  - Local target: `material://source-sad-klausuren-extern/Leuphana-Merz_Statistik-2_Uebungsbuch-mit-Klausur.pdf`
- **SaD external German Klausur bank (local) — University of Cologne pp. 7-8 — coefficient t-test and confidence interval**
  - Use: `solutions` · depth `practice` · scope `complementary`
  - Exact locator: `Koeln_Statistik-Klausur_Musterloesung.pdf, pp. 7-8, Aufgabe 5(a)-(b)`
  - Covers: Null model, alternative, statistic, and reference distribution, Tails, critical regions, and p-values, z and t tests for means, Confidence intervals and test duality
  - Angle: Shows how inference is written around a fitted multivariate regression coefficient.
  - Why this angle matters: The same model routed to L03 becomes an L10 inference task here: formulate H0, calculate a t statistic and construct a confidence interval. It is a good bridge between regression interpretation and test mechanics, but regression-slope inference is an extension beyond the core L03 scope.
  - Local target: `material://source-sad-klausuren-extern/Koeln_Statistik-Klausur_Musterloesung.pdf`

## L11 — SaD Lecture 11 — Data Science & Machine Learning Workflow

**Lecture purpose.** The lecture situates models inside an end-to-end data-science process and defines the evaluation discipline needed to distinguish a useful system from a model that merely fits available data.

**Concept progression.**

1. **The data-science pipeline** — Data acquisition, cleaning, integration, exploration, feature construction, modeling, validation, communication, and action are coupled steps; modeling is only one part of the work.
2. **Supervised and unsupervised tasks** — Classification predicts categories, regression predicts quantities, and unsupervised methods seek structure without labels; the learning setup must match the target and available supervision. Builds on: The data-science pipeline.
3. **Data types, features, and representation** — Structured, text, image, graph, and temporal data require different preprocessing and representations; domain knowledge determines which transformations preserve useful information. Builds on: The data-science pipeline.
4. **Train, validation, test, cross-validation, and bootstrap** — Separate data roles prevent evaluation leakage; repeated splits, cross-validation, and bootstrap estimate different aspects of out-of-sample uncertainty. Builds on: Supervised and unsupervised tasks.
5. **Loss functions, hypotheses, and inductive bias** — A learner searches a hypothesis space using an objective; architecture, regularization, features, and optimization encode assumptions about which solutions should generalize. Builds on: Supervised and unsupervised tasks.
6. **Evaluation metrics and class imbalance** — Accuracy, precision, recall, F1, macro/micro/weighted aggregation, and regression losses answer different questions; metric choice follows costs, prevalence, and deployment context. Builds on: Train, validation, test, cross-validation, and bootstrap.
7. **Underfitting, overfitting, and bias-variance** — Model complexity trades approximation bias against sensitivity to samples; data volume, regularization, validation, and compute shape the attainable generalization performance. Builds on: Loss functions, hypotheses, and inductive bias, Evaluation metrics and class imbalance.

**Complete source menu.**

### 1. Current scope and current practice

- **SaD — Statistik und Datenanalyse, lecture slides (SoSe 2026) — Current L11 data-science introduction deck**
  - Use: `course-material` · depth `course-aligned` · scope `current`
  - Exact locator: `lecture-slides/11_datascience_intro.pdf, 49 slides`
  - Covers: The data-science pipeline, Supervised and unsupervised tasks, Data types, features, and representation, Train, validation, test, cross-validation, and bootstrap, Loss functions, hypotheses, and inductive bias, Evaluation metrics and class imbalance, Underfitting, overfitting, and bias-variance
  - Angle: Defines the pipeline vocabulary — task, resampling, objective, metric, generalization — that L12 to L15 all assume.
  - Why this angle matters: This deck is the hinge of the module: everything before it is statistics, everything after is learning algorithms, and it supplies the shared frame. Its concepts are individually simple and collectively easy to hold vaguely, which is why the exercise-level routes on this stage (Géron Ch 2-3, ESL §7.10) matter more here than usual. Note that the deck's evaluation metrics extend L01's confusion matrix rather than re-deriving it.
- **SaD exercise sheets UE1–UE7 (SoSe 2026) — Blatt 5, Aufgabe 3 — multiclass evaluation metrics**
  - Use: `exercise` · depth `practice` · scope `current`
  - Exact locator: `exercise-slides/blatt-05.pdf, p. 4, Aufgabe 3(a)-(d)`
  - Covers: Evaluation metrics and class imbalance
  - Angle: Requires per-class confusion matrices plus micro/macro aggregation, the most calculation-heavy part of L11.
  - Why this angle matters: This is a current assessed sheet: attempt it before opening the tutorial solution. It is scope evidence because it shows the chair's own wording, data size and expected amount of working; it is not a replacement for the lecture derivation.
  - Local target: `material://source-sad-ss26-lectures/exercise-slides/blatt-05.pdf`
- **SaD exercise sheets UE1–UE7 (SoSe 2026) — UE6, slides 70-82 — classifier evaluation walkthrough**
  - Use: `exercise` · depth `practice` · scope `current`
  - Exact locator: `exercise-slides/UE6.pdf, slides 70-82`
  - Covers: Evaluation metrics and class imbalance
  - Angle: Builds accuracy, precision, recall and F1 from the confusion matrix rather than presenting isolated formulas.
  - Why this angle matters: This is the current worked tutorial for the named task. Use it after an unaided attempt: its value is the course's calculation order and notation, while reading it first would turn an exam-relevant retrieval task into passive recognition.
  - Local target: `material://source-sad-ss26-lectures/exercise-slides/UE6.pdf`
- **SaD exercise sheets UE1–UE7 (SoSe 2026) — UE7, slides 22-30 — official multiclass-metrics solution**
  - Use: `exercise` · depth `practice` · scope `current`
  - Exact locator: `exercise-slides/UE7.pdf, slides 22-30`
  - Covers: Evaluation metrics and class imbalance
  - Angle: Shows how the current course reports per-class and aggregate metrics when class priorities differ.
  - Why this angle matters: This is the current worked tutorial for the named task. Use it after an unaided attempt: its value is the course's calculation order and notation, while reading it first would turn an exam-relevant retrieval task into passive recognition.
  - Local target: `material://source-sad-ss26-lectures/exercise-slides/UE7.pdf`

### 2. Books and independent derivations

- **Fundamentals of Machine Learning for Predictive Data Analytics — Kelleher — predictive-analytics workflow framing**
  - Use: `book` · depth `orientation` · scope `complementary`
  - Exact locator: `Ch 1 Machine Learning for Predictive Data Analytics, pdf pp. 36-56; Ch 2 Data to Insights to Decisions, pdf pp. 57-91; Ch 8 Evaluation, pdf pp. 425-490`
  - Covers: The data-science pipeline, Supervised and unsupervised tasks, Data types, features, and representation, Loss functions, hypotheses, and inductive bias, Evaluation metrics and class imbalance
  - Angle: Frames the whole pipeline as a business problem being converted into an analytics problem — the step before L11's pipeline starts.
  - Why this angle matters: Ch 2 is about deciding what to predict at all: converting a stated goal into a target feature, choosing the analytics base table, and confronting the fact that the available data may not support the question. L11 begins one step later, with the data already framed. That earlier step is where most real projects fail and it is the part of the pipeline the lecture treats as given. Ch 8 then covers evaluation designs — hold-out, cross-validation, the choice of metric per task — at more length than the deck.
  - Local target: `material://source-kelleher-fmlpda/kelleher.pdf`
- **Google — Machine Learning Crash Course — Google ML Crash Course — framing, generalization and validation modules**
  - Use: `course` · depth `orientation` · scope `complementary`
  - Exact locator: `The 'Framing', 'Generalization', 'Training and Test Sets', 'Validation Set' and 'Classification' modules, each ≈15 min with in-page exercises`
  - Covers: Supervised and unsupervised tasks, Train, validation, test, cross-validation, and bootstrap, Evaluation metrics and class imbalance, Underfitting, overfitting, and bias-variance
  - Angle: Each concept arrives with an immediate in-page check question, so the vocabulary is tested as it is introduced.
  - Why this angle matters: L11 is a vocabulary lecture, and vocabulary decays unless it is used. The crash course's format — a short explanation followed at once by a question you must answer to continue — is well suited to that, and the whole relevant sequence takes about ninety minutes. The validation-set module in particular explains why a third split is needed once you start tuning, which the deck states without motivating. Shallow by design; it is orientation, not depth.
- **Ng — Machine Learning (Coursera) — Ng — bias, variance and the evaluation workflow lectures**
  - Use: `course` · depth `intuition` · scope `complementary`
  - Exact locator: `Week 6: the 'Advice for applying machine learning' lectures (train/validation/test split, learning curves, diagnosing bias vs variance)`
  - Covers: Underfitting, overfitting, and bias-variance, Train, validation, test, cross-validation, and bootstrap, Evaluation metrics and class imbalance
  - Angle: Turns bias and variance into a diagnostic procedure — read the learning curves, then decide what to change.
  - Why this angle matters: L11 defines underfitting, overfitting and the bias-variance trade-off. Ng's week 6 makes them actionable: if training and validation error are both high you have bias and more data will not help; if they diverge you have variance and more data will. That if-then structure is the most retainable form of this material and is exactly what a conceptual exam question about the trade-off is testing.

### 3. Visual, implementation and additional practice

- **Understanding the Bias-Variance Tradeoff — Fortmann-Roe — understanding the bias-variance tradeoff**
  - Use: `website` · depth `intuition` · scope `complementary`
  - Exact locator: `The complete article 'Understanding the Bias-Variance Tradeoff' (scott.fortmann-roe.com), including the bullseye diagram and the derivation appendix`
  - Covers: Underfitting, overfitting, and bias-variance
  - Angle: The bullseye diagram — four targets showing high/low bias against high/low variance — which is the fastest way to fix the distinction.
  - Why this angle matters: Bias and variance are easy to confuse because both are described as 'error'. The four-panel target picture separates them physically: bias is where the cluster of shots sits relative to the centre, variance is how spread the cluster is. Fifteen minutes, and it makes the L11 curves interpretable. The appendix gives the algebraic decomposition for readers who want it after the picture.
- **scikit-learn documentation — user guide & examples — scikit-learn user guide §3.1 — cross-validation**
  - Use: `documentation` · depth `implementation` · scope `complementary`
  - Exact locator: `User guide §3.1 'Cross-validation: evaluating estimator performance' and §3.4 'Metrics and scoring', with the linked examples`
  - Covers: Train, validation, test, cross-validation, and bootstrap, Evaluation metrics and class imbalance
  - Angle: Enumerates the resampling schemes as named, runnable splitters — KFold, StratifiedKFold, GroupKFold — with the situation each exists for.
  - Why this angle matters: L11 names cross-validation as one idea. The user guide shows it is a family, and each member exists because of a specific failure: stratified splits for class imbalance, group splits when observations are not independent, time-series splits when order matters. Knowing that the plain version has failure modes is the conceptual content; the diagrams in §3.1 make the differences immediate.
- **ISLP community exercise solutions (botlnec / a-martyn / applied-only) — ISLP community solutions — Ch 2 and Ch 5 exercises**
  - Use: `solutions` · depth `practice` · scope `complementary`
  - Exact locator: `The Ch 2 (statistical learning) and Ch 5 (resampling methods) solution notebooks in the botlnec / a-martyn / applied-on-ISLP repositories`
  - Covers: Underfitting, overfitting, and bias-variance, Train, validation, test, cross-validation, and bootstrap
  - Angle: Makes the ISLP exercises checkable, which is the difference between reading the chapter and knowing it.
  - Why this angle matters: ISLP publishes no official solutions, so its exercises are unusable for self-testing on their own. These community repositories work them in full, usually with the code and the reasoning. Treat them as an answer key rather than as authority: they are unreviewed, and on a disagreement the book wins. The Ch 5 notebooks are the most useful here — cross-validation and bootstrap worked end to end.
- **Géron — Hands-On Machine Learning (local) — Geron Ch 1 - the ML vocabulary with failure cases attached**
  - Use: `book` · depth `intuition` · scope `complementary`
  - Exact locator: `Chapter 1, pp. 29-61 (supervised/unsupervised pp. 34-41; overfitting p. 54; underfitting p. 56; testing and validating pp. 57-59; exercises p. 60)`
  - Covers: Supervised and unsupervised tasks, Data types, features, and representation, Underfitting, overfitting, and bias-variance
  - Angle: L11 states supervised/unsupervised, over- and underfitting and the train/test split in single bullets; Geron spends thirty pages on that same vocabulary with concrete data-quality and sampling failures, so each term Leser asserts arrives with a worked counterexample.
  - Why this angle matters: The vocabulary chapter, with the failure cases attached to the definitions rather than deferred. Overfitting (p. 54) and underfitting (p. 56) arrive with the diagnosis and the standard remedies, and testing/validating (pp. 57-59) explains why the split exists before L11's resampling node formalises it. Written for practitioners, so every term is introduced with the situation that made it necessary. The chapter exercises on pp. 60-61 are a fast check of whether the vocabulary has actually landed.
  - Local target: `material://source-geron-handson/geron.pdf`
- **Géron — Hands-On Machine Learning (local) — Geron Ch 2 - the pipeline executed end to end**
  - Use: `book` · depth `implementation` · scope `complementary`
  - Exact locator: `Chapter 2, pp. 63-111 (create a test set p. 80; feature scaling p. 98; transformation pipelines p. 99; better evaluation using cross-validation p. 102)`
  - Covers: The data-science pipeline, Data types, features, and representation, Train, validation, test, cross-validation, and bootstrap
  - Angle: Turns the L11 pipeline slide into an executed sequence: building the test set before looking at the data, scaling features, composing transformation pipelines, and scoring with cross-validation - the leakage-avoidance ordering the deck asserts but never demonstrates.
  - Why this angle matters: The whole L11 pipeline executed once, end to end, on real housing data — the only route on this stage where the stages are performed rather than described. The specific pages matter: creating a test set (p. 80) shows the leakage trap L11 warns about, transformation pipelines (p. 99) shows why preprocessing must be fitted on training data only, and cross-validation (p. 102) shows the resampling node in code. Doing this chapter once makes the deck's pipeline diagram concrete in a way no amount of re-reading will.
  - Local target: `material://source-geron-handson/geron.pdf`
- **Géron — Hands-On Machine Learning (local) — Geron Ch 3 - the evaluation metrics of L11 as drills**
  - Use: `book` · depth `practice` · scope `complementary`
  - Exact locator: `Chapter 3, pp. 113-137 (ROC p. 117; confusion matrix p. 118; precision/recall trade-off p. 121; AUC p. 126; multiclass p. 128; multilabel p. 134)`
  - Covers: Evaluation metrics and class imbalance
  - Angle: The deck's ROC/AUC pair (slides 38-39) had no practice source in the module at all; this chapter builds the confusion matrix, the precision/recall trade-off, the ROC curve and AUC, then extends to multiclass and multilabel, each with exercises.
  - Why this angle matters: The evaluation chapter as a drill: confusion matrix (p. 118), precision/recall trade-off (p. 121), ROC and AUC (pp. 117, 126), and then the multiclass and multilabel extensions (pp. 128, 134) that L11 names but does not work through. The precision-recall trade-off curve is the part worth the most attention — it makes the threshold an explicit decision rather than a hidden default, which is the conceptual content behind class-imbalance questions.
  - Local target: `material://source-geron-handson/geron.pdf`
- **Géron — Hands-On Machine Learning (local) — Geron Ch 1 exercises - the L11 vocabulary tested back**
  - Use: `exercise` · depth `practice` · scope `complementary`
  - Exact locator: `Chapter 1 exercises, pp. 60-61`
  - Covers: Supervised and unsupervised tasks, Underfitting, overfitting, and bias-variance
  - Angle: Nineteen short questions on labelled data, supervised versus unsupervised tasks, overfitting, the validation set and why tuning on the test set breaks - the retrieval check for the framing half of L11, which otherwise has no practice asset at all. Note: this copy is an early-release ebook and its solutions cross-reference on p. 61 is unresolved, so answers must be checked against the chapter body.
  - Why this angle matters: Two pages of exercises testing exactly the L11 vocabulary, phrased as questions rather than definitions. Because L11 has almost no computation, self-testing is otherwise hard to arrange, and these are the closest available proxy for the short conceptual questions the exam will use. Answers are in the book's appendix.
  - Local target: `material://source-geron-handson/geron.pdf`
- **Géron — Hands-On Machine Learning (local) — Geron Ch 4 - the loss functions L11 names in one line**
  - Use: `book` · depth `implementation` · scope `complementary`
  - Exact locator: `Chapter 4, pp. 139-180 (cross-entropy cost function, equation 4-22, p. 177)`
  - Covers: Loss functions, hypotheses, and inductive bias
  - Angle: L11 slides 30-31 name MSE and cross-entropy as the popular losses and move on; this chapter derives both and the softmax output they attach to, with the cost function written out at equation 4-22. It supplies the loss half of the node only - inductive bias stays with the Domingos article.
  - Why this angle matters: L11 names loss functions in a single line. Ch 4 gives them their own treatment, and equation 4-22 on p. 177 is the cross-entropy cost written out — the loss that L15's softmax output layer will minimise. Reading it here means that when it reappears in L15 it is a known object rather than a new formula, which is worth the detour given how compressed L15 is.
  - Local target: `material://source-geron-handson/geron.pdf`
- **A Programmer's Guide to Data Mining — Zacharski Ch 5 - evaluating a classifier by hand**
  - Use: `book` · depth `practice` · scope `complementary`
  - Exact locator: `Chapter 5, pp. 184-225 (10-fold cross-validation p. 187; confusion matrix p. 193; Kappa p. 203)`
  - Covers: Train, validation, test, cross-validation, and bootstrap, Evaluation metrics and class imbalance
  - Angle: Walks 10-fold cross-validation, the confusion matrix and the Kappa statistic on a small worked data set, which is the arithmetic L11 asserts on its cross-validation and evaluation slides without ever running it.
  - Why this angle matters: Evaluation carried out with a pen: 10-fold cross-validation (p. 187) explained as a procedure you could run manually, the confusion matrix (p. 193) built by hand, and Kappa (p. 203) — a metric L11 does not cover but which answers the 'is this better than guessing the majority class' question that class imbalance raises. Zacharski writes at the lowest technical level of any book on this stage, which makes it the fastest route when the concept rather than the mathematics is the obstacle.
  - Local target: `material://source-zacharski-data-mining/Zacharski_Programmers-Guide-to-Data-Mining.pdf`

### 4. University courses, prior-year, exam and advanced reference

- **An Introduction to Statistical Learning (Python edition) — ISLP Chapter 2 — statistical-learning workflow**
  - Use: `book` · depth `derivation` · scope `complementary`
  - Exact locator: `Ch 2 Statistical Learning, pdf pp. 25-77 (§2.1 what is statistical learning p. 26; §2.2 assessing model accuracy, with the bias-variance decomposition, p. 37; §2.3 lab p. 48)`
  - Covers: Supervised and unsupervised tasks, Train, validation, test, cross-validation, and bootstrap, Loss functions, hypotheses, and inductive bias, Underfitting, overfitting, and bias-variance
  - Angle: Derives the bias-variance decomposition algebraically, which L11 states as a picture of two curves crossing.
  - Why this angle matters: §2.2 shows the expected test error splitting into three named terms — squared bias, variance and irreducible error — and the derivation is short enough to follow at first reading. That is the content behind L11's U-shaped test-error curve, and having the algebra makes the trade-off a consequence rather than an empirical observation. The chapter also draws the distinction between prediction and inference as two different reasons to fit a model, which reframes what the pipeline is for.
  - Local target: `material://source-islp/islp.pdf`
- **Berkeley CS189/289A — Intro ML (past exams with solutions) — Berkeley CS189 — past exam questions on evaluation and generalization**
  - Use: `exam` · depth `practice` · scope `complementary`
  - Exact locator: `The published midterm and final papers with solutions — the bias-variance, cross-validation and evaluation-metric questions`
  - Covers: Underfitting, overfitting, and bias-variance, Train, validation, test, cross-validation, and bootstrap, Evaluation metrics and class imbalance
  - Angle: Written exam questions on conceptual ML material, which is otherwise almost impossible to practise.
  - Why this angle matters: L11 will be examined in writing, and the shelf is full of coding exercises and textbook problems but nearly empty of written conceptual questions with model answers. These papers fill that gap: short-answer and multiple-choice items about when cross-validation is appropriate, what a learning curve implies, why a metric is inappropriate for imbalanced data. Filter by topic — the course covers much that SaD does not.
- **Caltech Learning From Data (Abu-Mostafa) — homework sets — Caltech LFD — the bias-variance decomposition and generalization lectures**
  - Use: `course` · depth `derivation` · scope `complementary`
  - Exact locator: `Lecture 8 'Bias-Variance Tradeoff' and Lecture 11 'Overfitting', with the corresponding homework sets and solutions`
  - Covers: Underfitting, overfitting, and bias-variance, Loss functions, hypotheses, and inductive bias, Train, validation, test, cross-validation, and bootstrap
  - Angle: Asks whether learning is possible at all before asking how to do it, which is the question L11's inductive-bias node gestures at.
  - Why this angle matters: The course's organising question is whether fitting the training data tells you anything about unseen data, and its answer is that it does only under conditions that can be stated precisely. L11 asserts that inductive bias is necessary; this is where that assertion gets an argument. Lecture 8 derives the bias-variance decomposition on the board with the averaging-over-datasets picture, which is more illuminating than the algebra alone. Homework with solutions; genuinely above SaD level.
- **Data Science and Machine Learning — Kroese — data-science workflow and evaluation**
  - Use: `book` · depth `derivation` · scope `complementary`
  - Exact locator: `Ch 2 Statistical Learning, pdf pp. 37-84 (risk, loss and the training/test split); Ch 1 Importing, Summarizing and Visualizing Data, pdf pp. 19-36`
  - Covers: The data-science pipeline, Train, validation, test, cross-validation, and bootstrap, Evaluation metrics and class imbalance, Underfitting, overfitting, and bias-variance
  - Angle: States the whole supervised problem as risk minimisation first, so loss functions and generalization are one framework rather than two topics.
  - Why this angle matters: Kroese defines the learner's goal as minimising expected loss over an unknown distribution, then derives training error, test error and the need for a held-out set as consequences of not knowing that distribution. L11 introduces objectives and resampling as separate pipeline stages; this route shows they answer the same question. More mathematical than the other L11 options — expect measure-free but real probability notation.
  - Local target: `material://source-kroese-dsml/kroese.pdf`
- **A Few Useful Things to Know About Machine Learning (CACM) — Domingos — A Few Useful Things to Know About Machine Learning**
  - Use: `paper` · depth `intuition` · scope `complementary`
  - Exact locator: `Complete article, 9 pages (CACM 55(10), 2012)`
  - Covers: Data types, features, and representation, Loss functions, hypotheses, and inductive bias, Underfitting, overfitting, and bias-variance
  - Angle: Nine pages of practitioner judgment — that generalization is the goal, that data beats cleverness, that overfitting has many faces.
  - Why this angle matters: This is the single best-value item on the L11 stage: it takes half an hour and it supplies the 'why does this matter' layer for almost every node in the lecture. Its central points — learning is induction and therefore needs assumptions, more data usually beats a better algorithm, feature engineering is where the work is — are exactly what L11's pipeline slides assert without argument. Also the best available preparation for a conceptual exam question, because it is written as argument rather than as definition.
- **The Elements of Statistical Learning — ESL Ch 7 - what cross-validation and the bootstrap actually estimate**
  - Use: `book` · depth `advanced-reference` · scope `optional`
  - Exact locator: `Sections 7.2-7.3, pp. 238-247; section 7.10 cross-validation, p. 260; section 7.11 bootstrap methods, p. 268`
  - Covers: Train, validation, test, cross-validation, and bootstrap, Underfitting, overfitting, and bias-variance
  - Angle: L11 presents cross-validation and bootstrapping as confidence-raising procedures; this chapter separates the bias-variance decomposition from the estimator of test error, which is the distinction the deck's 'which k?' slide leaves open. Open only when a recorded error needs it.
  - Why this angle matters: The reference statement of what resampling actually estimates. §§7.2-7.3 (pp. 238-247) distinguish test error from expected test error and derive the optimism of the training error, which is the precise version of L11's claim that training error is not a fair estimate. §7.10 (p. 260) then explains what cross-validation estimates and why the number of folds is a bias-variance trade-off in its own right. Graduate level; read the specific sections rather than the chapter.
  - Local target: `material://source-esl/esl.pdf`

## L12 — SaD Lecture 12 — Tree-Based Learning & Ensembles

**Lecture purpose.** The lecture constructs interpretable partition models from information criteria and then reduces their instability by combining many trees in deliberately different ways.

**Concept progression.**

1. **Decision trees, rules, and preference bias** — Internal nodes test features, branches partition the instance space, and leaves predict; simpler rules encode a generalization preference rather than merely memorizing IDs.
2. **Entropy, information gain, and ID3** — Entropy measures class impurity, information gain measures the reduction after a split, and ID3 greedily chooses the feature that produces the largest gain. Builds on: Decision trees, rules, and preference bias.
3. **Regression trees and variance reduction** — Numeric targets replace class impurity with within-node squared-error or variance reduction while retaining the same recursive partition structure. Builds on: Decision trees, rules, and preference bias.
4. **Tree growth, stopping, and pruning** — Depth, minimum samples, purity thresholds, and post-pruning control complexity; an unpruned tree can fit noise and generalize poorly. Builds on: Entropy, information gain, and ID3.
5. **Bagging and random forests** — Bootstrap aggregation averages unstable learners, while random forests add feature subsampling to decorrelate trees and reduce ensemble variance. Builds on: Tree growth, stopping, and pruning.
6. **Boosting** — Sequential weak learners focus on residuals or misclassified examples, trading a coordinated bias reduction against sensitivity to noise and tuning. Builds on: Decision trees, rules, and preference bias.
7. **Stacking and ensemble tradeoffs** — A meta-learner combines diverse base predictions; leakage-safe out-of-fold construction, diversity, interpretability, compute, and calibration decide whether an ensemble is worthwhile. Builds on: Bagging and random forests, Boosting.

**Complete source menu.**

### 1. Current scope and current practice

- **SaD — Statistik und Datenanalyse, lecture slides (SoSe 2026) — Current L12 tree-based learning deck**
  - Use: `course-material` · depth `course-aligned` · scope `current`
  - Exact locator: `lecture-slides/12_tree_based.pdf, 36 slides`
  - Covers: Decision trees, rules, and preference bias, Entropy, information gain, and ID3, Regression trees and variance reduction, Tree growth, stopping, and pruning, Bagging and random forests, Boosting, Stacking and ensemble tradeoffs
  - Angle: The only current tree scope: preference bias, entropy/information gain/ID3, regression splitting, pruning, and the four ensemble families.
  - Why this angle matters: Compact but complete — the deck covers what many courses spread over two lectures. ID3's information-gain computation is the examinable calculation; the ensemble section is mostly conceptual comparison. Because bagging, random forests, boosting and stacking all arrive on the last slides, they are easy to blur; Géron Ch 7 treats each as a separate technique with its own reason to exist.

### 2. Books and independent derivations

- **Fundamentals of Machine Learning for Predictive Data Analytics — Kelleher Chapter 4 — information-based learning**
  - Use: `book` · depth `course-aligned` · scope `complementary`
  - Exact locator: `Ch 4 Information-based Learning, pdf pp. 156-214 (§4.2.3 the ID3 algorithm; the entropy and information-gain worked example)`
  - Covers: Decision trees, rules, and preference bias, Entropy, information gain, and ID3, Tree growth, stopping, and pruning, Bagging and random forests, Boosting
  - Angle: Runs one ID3 example completely, computing every entropy and every gain by hand across all splits.
  - Why this angle matters: L12 states the information-gain formula and shows a resulting tree. Kelleher computes the entropy of the target, then the remainder for each candidate feature, then the gain, then recurses — with the arithmetic printed at every node. That is exactly the calculation an exam will ask for on a small table, and doing it once with a fully worked reference is worth more than reading the formula ten times. The chapter also covers the gain-ratio correction for many-valued features, which the deck mentions in passing.
  - Local target: `material://source-kelleher-fmlpda/kelleher.pdf`
- **CS229 Lecture Notes (Stanford) — CS229 — decision-tree and boosting derivations**
  - Use: `course-material` · depth `advanced-reference` · scope `complementary`
  - Exact locator: `The decision-trees and boosting notes (the separate 'Decision Trees' and 'Boosting' note PDFs on the course site)`
  - Covers: Entropy, information gain, and ID3, Boosting
  - Angle: Derives boosting as a greedy stagewise fit to a loss function, which is where AdaBoost's exponential weights come from.
  - Why this angle matters: L12 presents AdaBoost's reweighting rule as a procedure. These notes show it falling out of minimising exponential loss one weak learner at a time, which explains both the specific weight formula and why boosting can overfit. Above exam level and worth reading only if the reweighting rule looked arbitrary.
  - Local target: `material://source-cs229-notes/cs229-notes.pdf`

### 3. Visual, implementation and additional practice

- **scikit-learn documentation — user guide & examples — scikit-learn user guide §1.10 and §1.11 — trees and ensembles**
  - Use: `documentation` · depth `implementation` · scope `complementary`
  - Exact locator: `User guide §1.10 'Decision Trees' (including §1.10.7 mathematical formulation of the impurity criteria) and §1.11 'Ensembles: Gradient boosting, random forests, bagging, voting, stacking'`
  - Covers: Decision trees, rules, and preference bias, Entropy, information gain, and ID3, Tree growth, stopping, and pruning, Bagging and random forests, Boosting, Stacking and ensemble tradeoffs
  - Angle: States the impurity criteria as formulas beside the parameter that selects them, tying L12's theory directly to a knob.
  - Why this angle matters: §1.10.7 writes out the Gini and entropy criteria and the regression variance criterion, and the surrounding text explains what each pruning parameter (max_depth, min_samples_leaf, ccp_alpha) does to the resulting tree. That mapping from concept to parameter is a strong memory aid, and §1.11 does the same for all four ensemble families L12 names — including stacking, which most books skip.
- **StatQuest with Josh Starmer (YouTube) — StatQuest — decision trees and random forests**
  - Use: `video` · depth `orientation` · scope `complementary`
  - Exact locator: `'Decision Trees, Clearly Explained'; 'Regression Trees, Clearly Explained'; 'Random Forests Part 1 — Building, Using and Evaluating'; 'AdaBoost, Clearly Explained' (≈15-20 min each)`
  - Covers: Decision trees, rules, and preference bias, Tree growth, stopping, and pruning, Bagging and random forests
  - Angle: Builds a tree split by split with the impurity numbers on screen, then shows exactly what a forest changes.
  - Why this angle matters: The tree video computes the impurity of each candidate split and picks the winner, on screen, which is the L12 exam calculation. The random-forest video then isolates the two changes from a single tree — bootstrap the rows, restrict the columns at each split — and shows out-of-bag evaluation falling out for free. Separating those two changes is what stops 'random forest' from being a black box. The AdaBoost video handles the reweighting visually.
- **Cornell CS4780 homework sets (local copies) — Cornell CS4780 HW8 — trees and AdaBoost**
  - Use: `exercise` · depth `practice` · scope `complementary`
  - Exact locator: `2018Fall/HW8 and 2018Spring/HW8 (trees, bagging and AdaBoost), with the published solution files`
  - Covers: Decision trees, rules, and preference bias, Entropy, information gain, and ID3, Boosting
  - Angle: Solution-backed problem sets that ask you to trace the algorithms by hand rather than to describe them.
  - Why this angle matters: Cornell's homework problems require executing AdaBoost's reweighting for a few rounds on a tiny dataset, which is the only way to find out whether the rule is actually understood. Solutions are published, so the work is checkable. Harder than the SaD exam will be; use them as a confidence test, not as the baseline.
- **MIT 6.034 Artificial Intelligence quizzes — MIT 6.034 quizzes — ID3/tree tracing**
  - Use: `exercise` · depth `practice` · scope `complementary`
  - Exact locator: `The published 6.034 quizzes and finals — the ID3 / decision-tree tracing questions, with the official solutions`
  - Covers: Entropy, information gain, and ID3, Decision trees, rules, and preference bias
  - Angle: Exam-format tracing questions with solutions: build the tree from a small table under time pressure.
  - Why this angle matters: MIT 6.034's quizzes are unusually procedural — they ask you to execute the algorithm and show the intermediate state, which is precisely the L12 exam form. Because the solutions are official and complete, a wrong answer can be diagnosed to the exact split. The archive spans many years, so there is enough material to practise repeatedly.
- **Géron — Hands-On Machine Learning (local) — Geron Ch 6 - trees you can grow and prune**
  - Use: `book` · depth `implementation` · scope `complementary`
  - Exact locator: `Chapter 6, pp. 203-216`
  - Covers: Decision trees, rules, and preference bias, Entropy, information gain, and ID3, Regression trees and variance reduction, Tree growth, stopping, and pruning
  - Angle: Executes the L12 induction story: impurity-driven splits, the regression criterion, and the regularisation hyperparameters that stand in for the deck's pre-pruning discussion, so the ID3 trace has a machine-checked counterpart.
  - Why this angle matters: Fourteen pages that grow a tree, visualise it, and then prune it by constraining depth and leaf size — the practical form of L12's pruning node, which the deck states as a principle. Because the trees are drawn at each stage, the effect of each constraint on the decision boundary is visible rather than described. Also demonstrates the instability of trees to small data changes, which is the motivation for the ensembles in the next chapter.
  - Local target: `material://source-geron-handson/geron.pdf`
- **Géron — Hands-On Machine Learning (local) — Geron Ch 7 - the three ensemble families side by side**
  - Use: `book` · depth `implementation` · scope `complementary`
  - Exact locator: `Chapter 7, pp. 217-240 (bagging p. 221; out-of-bag p. 223; AdaBoost and gradient boosting p. 228; stacking blender p. 236)`
  - Covers: Bagging and random forests, Boosting, Stacking and ensemble tradeoffs
  - Angle: L12 slide 34 names stacking in one line and no other registered source covers it; this chapter builds bagging, out-of-bag scoring, random forests, AdaBoost, gradient boosting and a stacking blender in one place, which is exactly the comparison the deck asks for.
  - Why this angle matters: The ensemble chapter with each family given its own section and its own reason: bagging (p. 221) and out-of-bag evaluation (p. 223), AdaBoost and gradient boosting (p. 228), stacking with a blender (p. 236). L12 presents all four on its closing slides, where they blur together; here each is built and evaluated separately on the same problem, so the differences are measured. Out-of-bag evaluation in particular is a neat idea the deck mentions in passing.
  - Local target: `material://source-geron-handson/geron.pdf`
- **Marsland — Machine Learning: An Algorithmic Perspective (2nd ed.) — Marsland Ch 12-13 - ID3 and the ensembles as algorithms**
  - Use: `book` · depth `implementation` · scope `complementary`
  - Exact locator: `Chapter 12, pp. 270-287 (ID3 p. 271; entropy, information gain and Gini p. 272; pruning p. 278; classification and regression trees p. 281) and Chapter 13, pp. 288-301 (boosting and AdaBoost p. 289; bagging p. 294; random forests p. 296)`
  - Covers: Entropy, information gain, and ID3, Regression trees and variance reduction, Tree growth, stopping, and pruning, Bagging and random forests, Boosting
  - Angle: Presents ID3 as code with entropy, information gain and Gini side by side, then boosting, bagging and random forests as procedures, which is the algorithmic reading of L12 that the slide pseudocode compresses.
  - Why this angle matters: Marsland's discipline is that every method appears as runnable code, so ID3 (p. 271) is a function you could execute and the entropy/information-gain/Gini comparison (p. 272) is three lines you could swap. For L12's algorithmic nodes that is the most direct possible representation. Ch 13 then does the same for boosting/AdaBoost (p. 289), bagging (p. 294) and random forests (p. 296), so the ensembles are also code rather than description. Pruning at p. 278 and the CART variant at p. 281 complete the deck's tree scope.
  - Local target: `material://source-marsland-ml-algorithmic/Machine Learning_ An Algorithmic Perspective (2nd ed.) [Marsland 2014-10-08].pdf`
- **Brandon Rohrer — End-to-End Machine Learning blog/courses — Brandon Rohrer — friendly decision-tree explanation**
  - Use: `website` · depth `orientation` · scope `complementary`
  - Exact locator: `The 'How decision trees work' article and its companion video on e2eml.school`
  - Covers: Decision trees, rules, and preference bias, Tree growth, stopping, and pruning
  - Angle: A no-notation explanation for unblocking, when the formal treatment has stalled.
  - Why this angle matters: Rohrer writes for readers who want the mechanism without the mathematics, using pictures and plain sentences. Routed here as a repair path rather than a study path: if the entropy computation has become an obstacle to seeing what a tree does, twenty minutes here restores the picture and the formal treatment becomes readable again. Not sufficient for the exam on its own.

### 4. University courses, prior-year, exam and advanced reference

- **An Introduction to Statistical Learning (Python edition) — ISLP §§8.1–8.2 — trees and ensembles**
  - Use: `book` · depth `derivation` · scope `complementary`
  - Exact locator: `Ch 8 Tree-Based Methods, pdf pp. 338-372 (§8.1 the basics of decision trees p. 339; §8.2 bagging, random forests, boosting and BART p. 351; Ch 8 lab p. 361)`
  - Covers: Decision trees, rules, and preference bias, Regression trees and variance reduction, Tree growth, stopping, and pruning, Bagging and random forests, Boosting
  - Angle: Separates the two reasons ensembles help — variance reduction by averaging, bias reduction by sequential fitting — instead of listing methods.
  - Why this angle matters: L12 presents bagging, random forests, boosting and stacking as a family of techniques. ISLP organises the same material around the mechanism: bagging and forests reduce variance by averaging decorrelated trees, boosting reduces bias by fitting each tree to the residual of the last. Once that split is clear, the differences between the methods stop being arbitrary details. §8.2 also explains why random forests decorrelate by restricting the feature subset, which the deck asserts.
  - Local target: `material://source-islp/islp.pdf`
- **Berkeley CS189/289A — Intro ML (past exams with solutions) — Berkeley CS189 — past exam questions on trees and ensembles**
  - Use: `exam` · depth `practice` · scope `complementary`
  - Exact locator: `The published midterm and final papers with solutions — the decision-tree, bagging and boosting questions`
  - Covers: Entropy, information gain, and ID3, Tree growth, stopping, and pruning, Bagging and random forests, Boosting
  - Angle: Exam-form questions that ask why an ensemble helps, not only how to run one.
  - Why this angle matters: The 'compute the information gain' question is well covered by MIT 6.034's quizzes. What these papers add is the other kind: why does bagging reduce variance but not bias, why does a random forest decorrelate trees, when would boosting overfit. Those are the conceptual items L12's summary slides set up, and having model answers calibrates how much to write.
- **Data Science and Machine Learning — Kroese Chapter 8 — tree methods**
  - Use: `book` · depth `derivation` · scope `complementary`
  - Exact locator: `Ch 8 Decision Trees and Ensemble Methods, pdf pp. 305-340`
  - Covers: Decision trees, rules, and preference bias, Regression trees and variance reduction, Bagging and random forests, Boosting
  - Angle: Gives the splitting criteria as impurity functions in a single framework, so entropy and Gini are two choices of one object.
  - Why this angle matters: Presenting information gain and the Gini index as different impurity measures plugged into the same greedy algorithm is more economical than learning them separately, and it makes clear that the algorithm does not depend on which is chosen. The ensemble half is compact and mathematical — it gives the variance-reduction argument for bagging in algebra rather than in words.
  - Local target: `material://source-kroese-dsml/kroese.pdf`
- **Stanford CS229 Machine Learning (Spring 2022 lectures) — Stanford CS229 — tree/ensemble lecture selections**
  - Use: `course` · depth `advanced-reference` · scope `complementary`
  - Exact locator: `The 2022 lecture covering decision trees and ensemble methods (identify by title on the playlist; roughly the mid-course tree lecture)`
  - Covers: Decision trees, rules, and preference bias, Bagging and random forests, Boosting
  - Angle: A research-level lecturer explaining why trees are still used, which is context the deck does not attempt.
  - Why this angle matters: The useful part is the framing: where trees sit relative to everything else in the course, what they are good at (heterogeneous tabular features, interpretability) and what they are bad at. That judgment is hard to get from a textbook and is the kind of thing a conceptual exam question rewards. The technical content is above SaD's level in places; watch for the framing.
- **The Elements of Statistical Learning — ESL - the ensemble chapters behind the L12 summary slide**
  - Use: `book` · depth `advanced-reference` · scope `optional`
  - Exact locator: `Section 9.2 tree-based methods, p. 324; section 8.8 model averaging and stacking, p. 307; Chapter 10 boosting and additive trees, pp. 356-407; Chapter 15 random forests, pp. 606-623`
  - Covers: Decision trees, rules, and preference bias, Bagging and random forests, Boosting, Stacking and ensemble tradeoffs
  - Angle: Supplies the derivations the deck summarises in four bullets: why AdaBoost fits an additive model under exponential loss, what random forests do to variance, and the model-averaging view that stacking belongs to.
  - Why this angle matters: The research-level accounts behind L12's summary slides. §9.2 (p. 324) is CART stated properly; Ch 10 (pp. 356-407) develops boosting as forward stagewise additive modelling, which is where the algorithm actually comes from; Ch 15 (pp. 606-623) is the random-forest analysis including why decorrelation reduces variance. §8.8 (p. 307) covers stacking. Use it to settle a specific question — this is not a first-pass reading and each section assumes the ones before it.
  - Local target: `material://source-esl/esl.pdf`

**Explicit practice gap.** No current SaD sheet directly practises this lecture. The external/other-university problem routes are therefore visible, but none is mislabeled as current course evidence.

## L13 — SaD Lecture 13 — Similarity-Based Learning

**Lecture purpose.** The lecture treats similarity as both a modeling assumption and a systems problem: predictions depend on a representation and metric, while practical use depends on finding neighbors efficiently.

**Concept progression.**

1. **1-NN and k-NN as lazy learners** — Neighbor methods store the training data and defer computation until prediction; k controls the local smoothness and bias-variance tradeoff.
2. **Classification, regression, voting, and weighting** — Nominal labels use majority or weighted voting, numeric targets use local averages, and ties, imbalance, and distance weighting alter the decision. Builds on: 1-NN and k-NN as lazy learners.
3. **Similarities, distances, and metric axioms** — Non-negativity, identity, symmetry, and triangle inequality define a metric; not every useful similarity is a metric, which affects algorithms and indexes. Builds on: 1-NN and k-NN as lazy learners.
4. **Minkowski distances and feature scaling** — Manhattan and Euclidean distance are Lp cases; units and high-dimensional irrelevant features can dominate neighborhoods unless representation and normalization are chosen deliberately. Builds on: Similarities, distances, and metric axioms.
5. **Cosine, Jaccard, and Mahalanobis measures** — Directional, set-valued, and covariance-aware data require different measures; each encodes a distinct invariance and assumption about what “similar” should mean. Builds on: Similarities, distances, and metric axioms.
6. **Exact similarity-search indexes** — kd-trees, k-means-style partitions, and metric trees prune search using geometric or metric structure, but effectiveness degrades with dimension and data geometry. Builds on: Minkowski distances and feature scaling.
7. **Approximate search and locality-sensitive hashing** — LSH trades guaranteed exact neighbors for sublinear candidate retrieval by making collision probability track similarity. Builds on: Cosine, Jaccard, and Mahalanobis measures, Exact similarity-search indexes.

**Complete source menu.**

### 1. Current scope and current practice

- **SaD — Statistik und Datenanalyse, lecture slides (SoSe 2026) — Current L13 similarity-based learning deck**
  - Use: `course-material` · depth `course-aligned` · scope `current`
  - Exact locator: `lecture-slides/13_similarity_based.pdf, 32 slides`
  - Covers: 1-NN and k-NN as lazy learners, Classification, regression, voting, and weighting, Similarities, distances, and metric axioms, Minkowski distances and feature scaling, Cosine, Jaccard, and Mahalanobis measures, Exact similarity-search indexes, Approximate search and locality-sensitive hashing
  - Angle: Scope authority for k-NN and, unusually for an introductory course, for exact and approximate similarity indexes.
  - Why this angle matters: The distance-measure and k-NN half is standard and well covered elsewhere. The indexing half — exact search structures and locality-sensitive hashing — is not: it is a database-systems topic that appears here because the chair teaches it, and almost no ML textbook on this shelf covers LSH at all. For that part the deck is effectively the only source, which makes it unusually important to read closely rather than supplement.
- **SaD exercise sheets UE1–UE7 (SoSe 2026) — UE7, slides 32-75 — similarity, distance and clustering bridge**
  - Use: `exercise` · depth `practice` · scope `current`
  - Exact locator: `exercise-slides/UE7.pdf, slides 32-75`
  - Covers: Similarities, distances, and metric axioms, Minkowski distances and feature scaling, Cosine, Jaccard, and Mahalanobis measures
  - Angle: Uses distance calculations inside k-means, making metric choice operational even though it is not a k-NN sheet.
  - Why this angle matters: This is the current worked tutorial for the named task. Use it after an unaided attempt: its value is the course's calculation order and notation, while reading it first would turn an exam-relevant retrieval task into passive recognition. It does not practise kd-trees, M-trees or LSH, so those remain an explicit L13 gap.
  - Local target: `material://source-sad-ss26-lectures/exercise-slides/UE7.pdf`

### 2. Books and independent derivations

- **Fundamentals of Machine Learning for Predictive Data Analytics — Kelleher Chapter 5 — similarity-based learning**
  - Use: `book` · depth `course-aligned` · scope `complementary`
  - Exact locator: `Ch 5 Similarity-based Learning, pdf pp. 215-281 (§5.2.2 the nearest-neighbour algorithm; the feature-space and normalisation sections)`
  - Covers: 1-NN and k-NN as lazy learners, Classification, regression, voting, and weighting, Similarities, distances, and metric axioms, Minkowski distances and feature scaling, Cosine, Jaccard, and Mahalanobis measures
  - Angle: Shows the decision boundary of a nearest-neighbour classifier as a Voronoi tessellation, which explains k's role geometrically.
  - Why this angle matters: The Voronoi picture makes two L13 facts visible at once: why 1-NN produces jagged boundaries that follow noise, and why increasing k smooths them. Kelleher also treats feature normalisation as part of the algorithm rather than as preprocessing, which matches L13's insistence that distance is meaningless across unscaled features. Does not cover indexing or LSH — for that half of L13 the deck is effectively alone.
  - Local target: `material://source-kelleher-fmlpda/kelleher.pdf`

### 3. Visual, implementation and additional practice

- **scikit-learn documentation — user guide & examples — scikit-learn user guide §1.6 — nearest neighbours and search structures**
  - Use: `documentation` · depth `implementation` · scope `complementary`
  - Exact locator: `User guide §1.6 'Nearest Neighbors', especially §1.6.4 K-D Tree, §1.6.5 Ball Tree and §1.6.6 'Choice of nearest neighbors algorithm'`
  - Covers: 1-NN and k-NN as lazy learners, Classification, regression, voting, and weighting, Similarities, distances, and metric axioms, Exact similarity-search indexes
  - Angle: One of the very few accessible treatments of exact search structures — K-D trees and ball trees — which L13 teaches and almost no ML book covers.
  - Why this angle matters: L13's exact-indexing node is genuinely underserved by this shelf: the ML textbooks treat k-NN as a brute-force scan and move on. §1.6.4-1.6.6 describe how K-D trees and ball trees prune the search, and — more valuably — §1.6.6 states when each stops helping, including the dimensionality at which brute force wins again. That is the practical form of the curse of dimensionality and directly supports the deck's argument for approximate search.
- **Cornell CS4780 homework sets (local copies) — Cornell CS4780 HW1 — k-NN**
  - Use: `exercise` · depth `practice` · scope `complementary`
  - Exact locator: `2017Spring/hw1, 2018Fall/HW1 and 2018Spring/HW1 (k-NN), with the published solutions`
  - Covers: 1-NN and k-NN as lazy learners, Classification, regression, voting, and weighting, Minkowski distances and feature scaling
  - Angle: Asks about k-NN's behaviour in the limit and in high dimensions, not just about computing neighbours.
  - Why this angle matters: Cornell opens its ML course with k-NN and uses it to introduce the curse of dimensionality quantitatively — how far the nearest neighbour actually is when dimensions grow. That is a conceptual result L13 mentions and never quantifies, and these problems make it concrete. Solutions available for all three variants.
- **MIT 6.034 Artificial Intelligence quizzes — MIT 6.034 quizzes — nearest-neighbor tracing**
  - Use: `exercise` · depth `practice` · scope `complementary`
  - Exact locator: `The published 6.034 quizzes and finals — the nearest-neighbour and decision-boundary questions, with solutions`
  - Covers: 1-NN and k-NN as lazy learners, Classification, regression, voting, and weighting, Minkowski distances and feature scaling
  - Angle: Asks you to draw the decision boundary a k-NN classifier induces, which tests the geometry rather than the formula.
  - Why this angle matters: Sketching the boundary for k=1 and k=3 on a small labelled scatter is a compact test of whether the algorithm is understood spatially, and it is a plausible exam item. These quizzes have many such questions with drawn solutions, which is not available anywhere else on the shelf.
- **A Programmer's Guide to Data Mining — Zacharski Ch 2 - the distance measures of L13 computed on real vectors**
  - Use: `book` · depth `implementation` · scope `complementary`
  - Exact locator: `Chapter 2, pp. 20-75 (Manhattan p. 23; Euclidean p. 24; Pearson p. 42; cosine p. 51; k-nearest neighbours p. 62)`
  - Covers: Minkowski distances and feature scaling, Cosine, Jaccard, and Mahalanobis measures
  - Angle: L13 introduces Manhattan, Euclidean and cosine as definitions; this chapter implements each in Python over one recommender data set, so the difference between the measures and the effect of unscaled features becomes something you run rather than something you are told. It does not treat the metric axioms of slide 32.
  - Why this angle matters: Every distance measure L13 names, computed by hand on the same small dataset: Manhattan (p. 23), Euclidean (p. 24), Pearson (p. 42), cosine (p. 51), then k-NN itself (p. 62). Using one running example across all of them is what makes the comparison meaningful — you see the same pair of items being close under one measure and far under another, which is the entire point of L13's metrics node and is invisible when each measure is defined separately.
  - Local target: `material://source-zacharski-data-mining/Zacharski_Programmers-Guide-to-Data-Mining.pdf`
- **A Programmer's Guide to Data Mining — Zacharski Ch 5 - k-NN aggregation and imbalance in practice**
  - Use: `book` · depth `practice` · scope `complementary`
  - Exact locator: `Chapter 5, pp. 184-225`
  - Covers: 1-NN and k-NN as lazy learners, Classification, regression, voting, and weighting
  - Angle: Runs k-NN with different k and different aggregation on a data set where class imbalance actually bites, which is the case L13 slide 14 raises and no current exercise sheet exercises.
  - Why this angle matters: The evaluation chapter revisited for the k-NN case: how to choose k by cross-validation and what class imbalance does to a neighbour vote. L13's aggregation node covers weighting and voting; this shows the failure mode those mechanisms exist to fix, with numbers.
  - Local target: `material://source-zacharski-data-mining/Zacharski_Programmers-Guide-to-Data-Mining.pdf`

### 4. University courses, prior-year, exam and advanced reference

- **SaD 2025 lecture recordings (WiSe 2025 run) — 2025 instance- and similarity-based pair**
  - Use: `course-material` · depth `advanced-reference` · scope `prior-year`
  - Exact locator: `13_similarity_based_part3.pdf`
  - Covers: 1-NN and k-NN as lazy learners, Classification, regression, voting, and weighting, Similarities, distances, and metric axioms, Minkowski distances and feature scaling, Cosine, Jaccard, and Mahalanobis measures, Exact similarity-search indexes
  - Angle: A prior-year similarity-based deck, part 3 — evidence that 2025 spread this topic over more sessions.
  - Why this angle matters: Since almost no book covers L13's indexing material, prior-year decks are a real supplement here rather than a redundancy. Note it is 'part 3' of a longer 2025 treatment; the earlier parts cover the distance-measure material that 2026 compresses.
- **Cornell CS4780 — Machine Learning for Intelligent Systems (Weinberger) — Cornell CS4780 — k-NN and the curse of dimensionality lectures**
  - Use: `course` · depth `course-aligned` · scope `complementary`
  - Exact locator: `Lectures 2-3 (k-nearest neighbours; the curse of dimensionality) with the corresponding lecture notes on the course site`
  - Covers: 1-NN and k-NN as lazy learners, Minkowski distances and feature scaling, Similarities, distances, and metric axioms, Classification, regression, voting, and weighting
  - Angle: Quantifies the curse of dimensionality — how far away the nearest neighbour actually is as dimensions grow — instead of describing it.
  - Why this angle matters: Weinberger computes the expected distance to the nearest of n points in a d-dimensional unit cube and shows it approaching the cube's diameter as d grows, which means 'nearest' stops meaning 'near'. L13 mentions the curse; this is the calculation that makes it alarming, and it is the reason the deck then spends time on approximate search. The lecture notes are written out and free.
- **MIT 6.036 Introduction to Machine Learning (Open Learning Library) — MIT 6.036 — nearest-neighbour and feature-representation units**
  - Use: `course` · depth `course-aligned` · scope `complementary`
  - Exact locator: `The feature-representation and nearest-neighbour units on the Open Learning Library, with their auto-graded exercises`
  - Covers: 1-NN and k-NN as lazy learners, Minkowski distances and feature scaling, Similarities, distances, and metric axioms
  - Angle: Auto-graded exercises give immediate right/wrong feedback, which is rare for this material.
  - Why this angle matters: Most L13 practice on this shelf is either unchecked or comes with a written solution you read after giving up. The Open Learning Library grades your answer instantly, which changes how many attempts you make. Particularly useful for the feature-scaling questions, where the effect on a distance is easy to reason about wrongly and easy to check numerically.
- **AML — Angewandtes Maschinelles Lernen, lecture slides (SoSe 2026) — AML L02 — k-NN deepening**
  - Use: `course-material` · depth `advanced-reference` · scope `optional`
  - Exact locator: `lecture-slides/VL 02-nearest-neighbor.pdf (the AML deck on nearest-neighbour methods)`
  - Covers: 1-NN and k-NN as lazy learners, Classification, regression, voting, and weighting, Minkowski distances and feature scaling
  - Angle: The same k-NN material from the parallel AML module, at greater depth and with the curse of dimensionality treated properly.
  - Why this angle matters: Two modules in the same semester cover k-NN, and AML's version goes further — distance concentration in high dimensions, the effect on neighbourhood meaningfulness, and the consequences for choosing k. Reading it serves both modules at once, which is why it is routed here despite belonging to another course. Note the notation differs slightly; SaD's deck is authoritative for the SaD exam.
- **The Elements of Statistical Learning — ESL Ch 13 - nearest neighbours and the cost of searching them**
  - Use: `book` · depth `advanced-reference` · scope `optional`
  - Exact locator: `Section 13.3 k-nearest-neighbor classifiers, p. 482; section 13.5 computational considerations, p. 499 (editing and condensing)`
  - Covers: 1-NN and k-NN as lazy learners, Exact similarity-search indexes
  - Angle: Section 13.5 is the closest registered treatment of the L13 indexing problem: it states the computational cost of exact nearest-neighbour search and the editing/condensing responses, though it does not cover kd-trees, M-trees or LSH.
  - Why this angle matters: §13.3 (p. 482) is the theoretical treatment of nearest neighbours, including the asymptotic error-rate result that bounds 1-NN's error by twice the Bayes rate — a striking fact L13 does not mention. §13.5 (p. 499) covers editing and condensing the training set to make search cheaper, which is the classical counterpart to the deck's indexing material and the closest any book here comes to it. Reference-only, but the L13 indexing half is otherwise unsupported.
  - Local target: `material://source-esl/esl.pdf`

## L14 — SaD Lecture 14 — Probability-Based Learning

**Lecture purpose.** The lecture extends the elementary categorical Naive Bayes model to sparse, numeric, and count data, then relaxes its global independence assumption with explicit probabilistic graphs.

**Concept progression.**

1. **Naive Bayes decision rule** — Class priors multiply with feature likelihoods under conditional independence, and the largest posterior score determines the class without needing the shared evidence denominator.
2. **Zero counts and Laplace smoothing** — Unseen feature-class pairs zero an entire likelihood product; additive pseudocounts prevent collapse while preserving normalized conditional distributions. Builds on: Naive Bayes decision rule.
3. **Numerical attributes and discretization** — Numeric features can be binned into categorical events or modeled with a class-conditional density; binning changes information and probability estimates. Builds on: Naive Bayes decision rule.
4. **Gaussian Naive Bayes** — Each class-feature pair is modeled by a Normal density with estimated mean and variance, producing continuous likelihoods under the same conditional-independence factorization. Builds on: Numerical attributes and discretization.
5. **Multinomial Naive Bayes and log space** — Count features such as words use multinomial event probabilities; log probabilities turn products into sums and prevent numerical underflow. Builds on: Zero counts and Laplace smoothing.
6. **Bayesian networks and factorization** — A directed acyclic graph encodes local conditional dependencies, factorizing a joint distribution without assuming that all features are independent given the class. Builds on: Naive Bayes decision rule.
7. **Conditional independence and Markov blankets** — Graph structure determines which variables become independent when others are observed; a node's Markov blanket contains the local information needed for its conditional distribution. Builds on: Bayesian networks and factorization.

**Complete source menu.**

### 1. Current scope and current practice

- **SaD — Statistik und Datenanalyse, lecture slides (SoSe 2026) — Current L14 probability-based learning deck**
  - Use: `course-material` · depth `course-aligned` · scope `current`
  - Exact locator: `lecture-slides/14_probability_based.pdf, 29 slides`
  - Covers: Naive Bayes decision rule, Zero counts and Laplace smoothing, Numerical attributes and discretization, Gaussian Naive Bayes, Multinomial Naive Bayes and log space, Bayesian networks and factorization, Conditional independence and Markov blankets
  - Angle: Extends L04's categorical classifier to smoothing, numeric attributes and Gaussian/multinomial variants, then opens Bayesian networks.
  - Why this angle matters: The shortest deck in the second half, and its last third — Bayesian networks, factorization, Markov blankets — is genuinely different material introduced quickly. The Naive Bayes extensions are examinable computations; the network material is more likely to be examined conceptually. Marsland Ch 16 is the only route here that treats the network half at comparable length.
- **SaD exercise sheets UE1–UE7 (SoSe 2026) — UE4, slides 9-12 — categorical Naive Bayes worked example**
  - Use: `exercise` · depth `practice` · scope `current`
  - Exact locator: `exercise-slides/UE4.pdf, slides 9-12`
  - Covers: Naive Bayes decision rule, Zero counts and Laplace smoothing
  - Angle: Rebuilds the two-feature categorical classifier and exposes the conditional-independence assumption before L14 extends it.
  - Why this angle matters: This is the current worked tutorial for the named task. Use it after an unaided attempt: its value is the course's calculation order and notation, while reading it first would turn an exam-relevant retrieval task into passive recognition. It is a recap bridge: it does not cover Gaussian/count likelihoods or Bayesian networks.
  - Local target: `material://source-sad-ss26-lectures/exercise-slides/UE4.pdf`

### 2. Books and independent derivations

- **Fundamentals of Machine Learning for Predictive Data Analytics — Kelleher Chapter 6 — probability-based learning**
  - Use: `book` · depth `course-aligned` · scope `complementary`
  - Exact locator: `Ch 6 Probability-based Learning, pdf pp. 282-350 (§6.4.2 the Naive Bayes model; the smoothing and continuous-feature sections)`
  - Covers: Naive Bayes decision rule, Zero counts and Laplace smoothing, Numerical attributes and discretization, Gaussian Naive Bayes
  - Angle: Covers Naive Bayes and Bayesian networks in one chapter, so the classifier is visibly the simplest network rather than a separate method.
  - Why this angle matters: L14 introduces Naive Bayes and then, separately, Bayesian networks, and the connection between them is asserted late. Kelleher builds the network formalism first and derives Naive Bayes as the network in which every feature depends only on the class — at which point the 'naive' assumption is a graph statement rather than an algebraic convenience. That is the cleanest available account of L14's structure. Smoothing and the continuous-feature handling are worked with numbers.
  - Local target: `material://source-kelleher-fmlpda/kelleher.pdf`
- **Fundamentals of Machine Learning for Predictive Data Analytics — Kelleher Ch 6 exercises - Gaussian Naive Bayes worked on data**
  - Use: `exercise` · depth `practice` · scope `complementary`
  - Exact locator: `Section 6.7 exercises, pp. 344-350 (exercise 3: naive Bayes with normally distributed descriptive features)`
  - Covers: Gaussian Naive Bayes
  - Angle: L14 slides 14-18 introduce continuous features and density estimation but the current UE6 sheet stops at the discrete classifier; exercise 3 asks for a naive Bayes model that uses probability density functions with normally distributed features and then a prediction from it, which is the only registered drill for the Gaussian variant.
  - Why this angle matters: The Gaussian Naive Bayes exercise on pp. 344-350 — exercise 3 in particular — is the worked numeric-attribute case L14 needs and the chapter body only sketches: fit a Normal per class per feature, evaluate the densities at the query point, multiply, compare. Having the full solution means the arithmetic can be checked step by step, which matters because the density values are not probabilities and the intermediate numbers look wrong the first time.
  - Local target: `material://source-kelleher-fmlpda/kelleher.pdf`
- **Jurafsky & Martin — Speech and Language Processing (3rd ed. draft) — Jurafsky & Martin Ch 4 §§4.4-4.7 — smoothing, unknown words and evaluation**
  - Use: `book` · depth `course-aligned` · scope `complementary`
  - Exact locator: `Ch 4 §4.4 optimizing for sentiment analysis, §4.5 naive Bayes as a language model, §4.7 evaluation (precision, recall, F-measure), plus the add-one smoothing treatment in §4.2`
  - Covers: Zero counts and Laplace smoothing, Multinomial Naive Bayes and log space, Naive Bayes decision rule
  - Angle: Derives add-one smoothing as a response to the unknown-word problem, and shows the log-space computation that makes it numerically usable.
  - Why this angle matters: Two L14 details are handled better here than anywhere else on the shelf. First, smoothing arrives because a single unseen word zeroes the entire product — the failure is shown before the fix. Second, §4.2 explains why the computation is done by summing logs rather than multiplying probabilities: with a few hundred words the product underflows to zero in floating point. L14's multinomial node mentions log space; this says why it is not optional.
- **CS229 Lecture Notes (Stanford) — CS229 §4.2 — Naive Bayes derivation**
  - Use: `course-material` · depth `advanced-reference` · scope `complementary`
  - Exact locator: `Main notes §4.2 Naive Bayes, §4.2.1 Laplace smoothing, and §4.2.2 event models for text classification (multinomial vs Bernoulli)`
  - Covers: Naive Bayes decision rule, Zero counts and Laplace smoothing, Multinomial Naive Bayes and log space
  - Angle: Distinguishes the multinomial from the Bernoulli event model explicitly, which L14 blurs.
  - Why this angle matters: These are two genuinely different models — one counts occurrences, one records presence — and they give different answers on the same documents. L14 introduces multinomial Naive Bayes without naming the alternative, which makes it easy to apply the wrong likelihood. §4.2.2 is two pages and settles it. Also gives the maximum-likelihood derivation of the smoothed estimates rather than presenting smoothing as a hack.
  - Local target: `material://source-cs229-notes/cs229-notes.pdf`

### 3. Visual, implementation and additional practice

- **scikit-learn documentation — user guide & examples — scikit-learn user guide §1.9 — naive Bayes variants**
  - Use: `documentation` · depth `implementation` · scope `complementary`
  - Exact locator: `User guide §1.9 'Naive Bayes': §1.9.1 Gaussian, §1.9.2 Multinomial, §1.9.3 Complement, §1.9.4 Bernoulli, §1.9.5 Categorical`
  - Covers: Naive Bayes decision rule, Zero counts and Laplace smoothing, Numerical attributes and discretization, Gaussian Naive Bayes, Multinomial Naive Bayes and log space
  - Angle: Lists all five variants side by side with the data type each assumes — the cleanest statement of what changes between them.
  - Why this angle matters: L14 covers the Gaussian and multinomial variants and mentions that others exist. Seeing all five in one table makes the pattern explicit: the classifier is fixed and only the likelihood term changes with the feature type. Once that is clear, the variants stop being separate algorithms to memorise. The smoothing parameter alpha is documented alongside, with the default and its effect.
- **Stanford CS229 — problem sets & practice midterms — CS229 problem sets — the Naive Bayes and generative-model problems**
  - Use: `exercise` · depth `practice` · scope `complementary`
  - Exact locator: `The problem set containing the Naive Bayes spam-classification problem, plus the generative-model questions on the practice midterms, with their published solutions`
  - Covers: Naive Bayes decision rule, Zero counts and Laplace smoothing, Multinomial Naive Bayes and log space
  - Angle: Asks for the maximum-likelihood estimates to be derived, not just applied — the step L14 states as a result.
  - Why this angle matters: The classic CS229 problem has you write the likelihood of the training corpus under the naive model, differentiate, and obtain the counting formulas the lecture simply hands you. Doing that once explains why the parameter estimates are ratios of counts, and it makes the smoothing correction visible as a modification of the estimator rather than an arbitrary +1. Solutions published.
- **StatQuest with Josh Starmer (YouTube) — StatQuest — Naive Bayes and Gaussian Naive Bayes**
  - Use: `video` · depth `orientation` · scope `complementary`
  - Exact locator: `'Naive Bayes, Clearly Explained'; 'Gaussian Naive Bayes, Clearly Explained' (≈15 min each); 'Logistic Regression' only as a contrast`
  - Covers: Naive Bayes decision rule, Gaussian Naive Bayes
  - Angle: The Gaussian video shows why a density replaces a count for numeric features, which is L14's least intuitive step.
  - Why this angle matters: Moving from multinomial to Gaussian Naive Bayes means the likelihood stops being a proportion and becomes a density evaluation, and the resulting number is no longer a probability. That shift is where L14's numeric-attribute node loses people. The video draws the fitted Normal per class per feature and reads values off it, which makes the substitution concrete. Watch the categorical video first even if you have seen it for L04.
- **Cornell CS4780 homework sets (local copies) — Cornell CS4780 HW4 - solution-backed Naive Bayes problems**
  - Use: `exercise` · depth `practice` · scope `complementary`
  - Exact locator: `2018Fall/HW4 Problem 1 'Intuition for Naive Bayes' (hw4.pdf with hw4_solution.pdf); 2018Spring/HW4 Naive Bayes with smoothing (hw4.pdf, solutions in hw4_solutions.tex)`
  - Covers: Naive Bayes decision rule, Zero counts and Laplace smoothing
  - Angle: One problem set explicitly built to test the intuition behind the independence assumption rather than the arithmetic.
  - Why this angle matters: The problem's title is literal — it asks what goes wrong when the assumption fails and what smoothing is compensating for. Those are exactly the short-answer questions L14 could pose, and they are hard to practise from a textbook. Both terms' versions have published solutions; the Spring set adds the smoothing computation.
- **A Programmer's Guide to Data Mining — Zacharski Ch 6 - Naive Bayes with the zero-frequency failure exposed**
  - Use: `book` · depth `implementation` · scope `complementary`
  - Exact locator: `Chapter 6, pp. 226-296`
  - Covers: Naive Bayes decision rule, Zero counts and Laplace smoothing, Numerical attributes and discretization
  - Angle: Builds the classifier on counts, hits the zero-probability case, and applies smoothing - the same sequence as L14 slides 8-12, but with the intermediate tables visible so the smoothed denominator can be checked.
  - Why this angle matters: Naive Bayes with the zero-frequency problem hit deliberately before smoothing is introduced, so the fix arrives as a response to a failure you have already seen. That ordering is why this is worth reading even though the level is elementary — L14 introduces smoothing as a rule, and the rule is much easier to remember when you have watched a single unseen word drive the whole product to zero.
  - Local target: `material://source-zacharski-data-mining/Zacharski_Programmers-Guide-to-Data-Mining.pdf`
- **A Programmer's Guide to Data Mining — Zacharski Ch 7 - the bag-of-words model behind Multinomial Bayes**
  - Use: `book` · depth `implementation` · scope `complementary`
  - Exact locator: `Chapter 7, pp. 297-333`
  - Covers: Multinomial Naive Bayes and log space
  - Angle: L14 slides 20-23 introduce the multinomial model through documents as bags of words; this chapter is that model implemented on text, including the log-space handling the deck mentions only in passing.
  - Why this angle matters: The bag-of-words representation built explicitly — tokenising documents, counting, and forming the feature vector — which is the model multinomial Naive Bayes operates on. L14 assumes this representation; without it, the multinomial likelihood is hard to interpret. Includes a worked sentiment-classification example end to end.
  - Local target: `material://source-zacharski-data-mining/Zacharski_Programmers-Guide-to-Data-Mining.pdf`
- **Marsland — Machine Learning: An Algorithmic Perspective (2nd ed.) — Marsland Ch 16 - Bayesian networks and the Markov blanket**
  - Use: `book` · depth `implementation` · scope `complementary`
  - Exact locator: `Chapter 16, pp. 342-379 (conditional independence p. 342; Bayesian networks p. 343; Markov blanket p. 349)`
  - Covers: Bayesian networks and factorization, Conditional independence and Markov blankets
  - Angle: L14 slides 25-29 are the only place the module taught Bayesian networks, factorisation and the Markov blanket, and no other registered source covered them; this chapter derives the factorisation from the graph and defines the blanket as the locally sufficient set.
  - Why this angle matters: The only route on this stage that treats L14's last third — Bayesian networks — at real length. Conditional independence (p. 342) is developed as a graph property, networks (p. 343) as factorisations of a joint distribution, and the Markov blanket (p. 349) as the set that renders a node independent of everything else. The deck introduces all three in a handful of slides. Read this if the network material is examined conceptually, which the exercises suggest.
  - Local target: `material://source-marsland-ml-algorithmic/Machine Learning_ An Algorithmic Perspective (2nd ed.) [Marsland 2014-10-08].pdf`

### 4. University courses, prior-year, exam and advanced reference

- **An Introduction to Statistical Learning (Python edition) — ISLP §4.4.4 and lab — Naive Bayes in application**
  - Use: `book` · depth `derivation` · scope `complementary`
  - Exact locator: `Ch 4 Classification, pdf pp. 144-208 — §4.4.4 Naive Bayes and the Ch 4 lab (Naive Bayes on the Smarket data)`
  - Covers: Naive Bayes decision rule, Gaussian Naive Bayes
  - Angle: Places Naive Bayes beside LDA and QDA, so its assumption is visible as one point on a spectrum of covariance assumptions.
  - Why this angle matters: §4.4 develops LDA (shared covariance), QDA (per-class covariance) and then Naive Bayes (diagonal covariance — features conditionally independent) as three points on the same spectrum. That framing answers the question L14 leaves open: what is actually being given up by the naive assumption, and when does giving it up pay. The lab then runs all three on the same data so the trade-off is observed rather than argued.
  - Local target: `material://source-islp/islp.pdf`
- **Bishop — Pattern Recognition and Machine Learning (PRML) — Bishop Ch 8 — graphical models and conditional independence**
  - Use: `book` · depth `advanced-reference` · scope `complementary`
  - Exact locator: `Ch 8 'Graphical Models' §8.1 Bayesian networks, §8.2 conditional independence (including d-separation), §8.3.6 the Markov blanket`
  - Covers: Bayesian networks and factorization, Conditional independence and Markov blankets, Naive Bayes decision rule
  - Angle: Gives the graphical criterion (d-separation) for reading conditional independence off a network, which L14 states only for the naive case.
  - Why this angle matters: L14 introduces Bayesian networks and asserts that the graph encodes conditional independence. §8.2 supplies the actual rule for reading it — which paths block information and which do not — with the three canonical three-node cases worked through. That is the difference between recognising a network and being able to use one. §8.3.6 defines the Markov blanket precisely, which L14's last slides name. Free PDF from Microsoft Research; reference-level and demanding.
- **MIT 18.650 — Statistics for Applications (Rigollet, OCW) — MIT 18.650 Bayesian-statistics lectures — context only**
  - Use: `course` · depth `advanced-reference` · scope `complementary`
  - Exact locator: `Lectures 17-18 (Bayesian inference: priors, posteriors, and the Bayesian-frequentist contrast); reference only`
  - Covers: Naive Bayes decision rule
  - Angle: Places Naive Bayes inside the Bayesian inference framework it borrows its name from.
  - Why this angle matters: L14's classifier applies Bayes' rule to features but is otherwise a frequentist procedure with plug-in estimates. These lectures set out what a genuinely Bayesian treatment would be — a prior over parameters, a posterior, and prediction by integration — which clarifies exactly how much of 'Bayes' the classifier actually uses. Useful for conceptual hygiene, not for the exam.
- **Data Science and Machine Learning — Kroese — probability-based classifier selections**
  - Use: `book` · depth `derivation` · scope `complementary`
  - Exact locator: `Ch 7 Classification, pdf pp. 269-304 (the Bayes classifier and generative classifiers)`
  - Covers: Naive Bayes decision rule, Numerical attributes and discretization, Gaussian Naive Bayes
  - Angle: Derives the Bayes-optimal classifier first, so Naive Bayes is visibly an approximation to a known ideal.
  - Why this angle matters: The Bayes classifier — assign to the class with the highest true posterior — is the best possible classifier and is unavailable because the posterior is unknown. Kroese establishes that baseline before any practical method, which turns Naive Bayes into a specific, understandable approximation of it rather than a standalone algorithm. That framing is missing from L14 and makes the smoothing and independence assumptions easier to reason about.
  - Local target: `material://source-kroese-dsml/kroese.pdf`
- **Stanford CS229 Machine Learning (Spring 2022 lectures) — Stanford CS229 — generative-classifier lecture**
  - Use: `course` · depth `advanced-reference` · scope `complementary`
  - Exact locator: `The 2022 lecture on generative learning algorithms (GDA and Naive Bayes)`
  - Covers: Naive Bayes decision rule, Multinomial Naive Bayes and log space
  - Angle: Sets up the generative-versus-discriminative distinction, which is the category Naive Bayes belongs to and which L14 never names.
  - Why this angle matters: Modelling P(x\|y) and P(y) and inverting with Bayes, versus modelling P(y\|x) directly, is the single most clarifying distinction in classification — it explains why Naive Bayes needs smoothing and logistic regression does not, and why Naive Bayes can be trained on less data. L14 works entirely inside the generative branch without saying so. One lecture, high return.
- **Probabilistic Machine Learning: An Introduction — Murphy §§9.3–9.4 — Gaussian and Multinomial Naive Bayes**
  - Use: `book` · depth `advanced-reference` · scope `complementary`
  - Exact locator: `§9.3 Naive Bayes classifiers and §9.4 generative vs discriminative classifiers (Part II Linear Models, pdf pp. 351-452)`
  - Covers: Gaussian Naive Bayes, Multinomial Naive Bayes and log space
  - Angle: States the conditions under which Naive Bayes beats a discriminative model despite its false assumption.
  - Why this angle matters: §9.4 is the reason to come here: it explains that a wrong but low-variance model can beat a correct high-variance one when data is scarce, which is why a classifier built on an assumption everyone knows is false remains useful. That is the honest answer to the objection L14 invites and does not address. Reference-level writing — precise, compressed, and assuming a probability background beyond SaD's.
  - Local target: `material://source-murphy-pml1/pml1.pdf`
- **Machine Learning and Data Mining — CSC 411 notes (Toronto) — CSC411 notes — compact Naive Bayes reference**
  - Use: `course-material` · depth `advanced-reference` · scope `complementary`
  - Exact locator: `The Naive Bayes lecture notes (Toronto CSC411/2515 course notes, the generative-classifier set)`
  - Covers: Naive Bayes decision rule, Gaussian Naive Bayes, Multinomial Naive Bayes and log space
  - Angle: A two-to-three page summary with the full derivation and no prose — the fastest revision reference for L14.
  - Why this angle matters: University lecture notes written to be revised from rather than learned from: model, assumption, estimates, prediction rule, all on a couple of pages with the algebra intact. Use it the day before the exam to check that you can still reconstruct the derivation, not to meet the topic.
  - Local target: `material://source-csc411-notes/csc411.pdf`

## L15 — SaD Lecture 15 — Neural Networks

**Lecture purpose.** The lecture builds neural networks from the familiar linear model by adding nonlinear activations and layers, then explains how gradients allocate credit through the resulting computation graph.

**Concept progression.**

1. **Artificial neurons and linear-model equivalence** — A neuron computes an affine weighted sum followed by an activation; with the identity activation, a one-layer network is multivariate linear regression.
2. **Nonlinearity, activation functions, and XOR** — Stacking purely linear layers remains linear; nonlinear activations such as sigmoid, tanh, and ReLU let multilayer networks represent boundaries like XOR. Builds on: Artificial neurons and linear-model equivalence.
3. **One-hot targets, output layers, and softmax** — Regression and classification require different output parameterizations; softmax converts class scores into a normalized categorical distribution. Builds on: Artificial neurons and linear-model equivalence.
4. **Multilayer forward passes, shapes, and parameter counts** — Matrix multiplication, biases, activations, and layer dimensions define the forward graph; parameter counting follows directly from adjacent widths and bias vectors. Builds on: Nonlinearity, activation functions, and XOR, One-hot targets, output layers, and softmax.
5. **Loss gradients and backpropagation** — The chain rule propagates output error backward through each operation, producing parameter gradients reused by gradient-based optimizers. Builds on: Multilayer forward passes, shapes, and parameter counts.
6. **Training, generalization, and practical choices** — Initialization, batches, learning rate, stopping, data volume, regularization, and validation interact; lower training loss alone is not evidence of a better model. Builds on: Loss gradients and backpropagation.
7. **Expressiveness and universal approximation** — Sufficiently wide nonlinear networks can approximate broad function classes, but the theorem does not guarantee efficient learning, good generalization, or a practical architecture. Builds on: Nonlinearity, activation functions, and XOR, Training, generalization, and practical choices.
8. **CNN, RNN, and Transformer outlook** — Convolutions encode locality and sharing, recurrent networks encode sequence state, and attention-based Transformers model interactions; these are orientation topics beyond the core MLP calculations. Builds on: Multilayer forward passes, shapes, and parameter counts.

**Complete source menu.**

### 1. Current scope and current practice

- **SaD — Statistik und Datenanalyse, lecture slides (SoSe 2026) — Current L15 neural-networks deck**
  - Use: `course-material` · depth `course-aligned` · scope `current`
  - Exact locator: `lecture-slides/15_neural_networks.pdf, 38 slides`
  - Covers: Artificial neurons and linear-model equivalence, Nonlinearity, activation functions, and XOR, One-hot targets, output layers, and softmax, Multilayer forward passes, shapes, and parameter counts, Loss gradients and backpropagation, Training, generalization, and practical choices, Expressiveness and universal approximation, CNN, RNN, and Transformer outlook
  - Angle: Builds from a single neuron to backpropagation and closes with the CNN/RNN/Transformer outlook that connects SaD to AML.
  - Why this angle matters: The deck's most useful move is starting from the observation that a single neuron with no activation is a linear model — which ties L15 back to L03 rather than presenting neural networks as a new subject. Backpropagation is stated as the chain rule applied layer by layer; the deck does not run a numeric example, which is the gap Karpathy's micrograd and 3Blue1Brown's episode 3 fill. The closing outlook slides are context, not exam material.
- **SaD exercise sheets UE1–UE7 (SoSe 2026) — Blatt 5, Aufgabe 2 — forward pass, softmax and cross-entropy**
  - Use: `exercise` · depth `practice` · scope `current`
  - Exact locator: `exercise-slides/blatt-05.pdf, p. 3, Aufgabe 2(a)-(d)`
  - Covers: Artificial neurons and linear-model equivalence, One-hot targets, output layers, and softmax, Multilayer forward passes, shapes, and parameter counts, Training, generalization, and practical choices
  - Angle: The current by-hand neural-network task: matrix multiply, normalize outputs, calculate loss and interpret the decision rule.
  - Why this angle matters: This is a current assessed sheet: attempt it before opening the tutorial solution. It is scope evidence because it shows the chair's own wording, data size and expected amount of working; it is not a replacement for the lecture derivation.
  - Local target: `material://source-sad-ss26-lectures/exercise-slides/blatt-05.pdf`
- **SaD exercise sheets UE1–UE7 (SoSe 2026) — UE6, slides 39-68 — neurons, forward pass, softmax and loss**
  - Use: `exercise` · depth `practice` · scope `current`
  - Exact locator: `exercise-slides/UE6.pdf, slides 39-68`
  - Covers: Artificial neurons and linear-model equivalence, Nonlinearity, activation functions, and XOR, One-hot targets, output layers, and softmax, Multilayer forward passes, shapes, and parameter counts, Training, generalization, and practical choices
  - Angle: Works the network as explicit matrices before discussing training, preventing the architecture from becoming a black box.
  - Why this angle matters: This is the current worked tutorial for the named task. Use it after an unaided attempt: its value is the course's calculation order and notation, while reading it first would turn an exam-relevant retrieval task into passive recognition.
  - Local target: `material://source-sad-ss26-lectures/exercise-slides/UE6.pdf`
- **SaD exercise sheets UE1–UE7 (SoSe 2026) — UE7, slides 17-21 — official neural-network solution**
  - Use: `exercise` · depth `practice` · scope `current`
  - Exact locator: `exercise-slides/UE7.pdf, slides 17-21`
  - Covers: One-hot targets, output layers, and softmax, Multilayer forward passes, shapes, and parameter counts, Training, generalization, and practical choices
  - Angle: Provides the exact current solution for the forward/softmax/cross-entropy assignment.
  - Why this angle matters: This is the current worked tutorial for the named task. Use it after an unaided attempt: its value is the course's calculation order and notation, while reading it first would turn an exam-relevant retrieval task into passive recognition.
  - Local target: `material://source-sad-ss26-lectures/exercise-slides/UE7.pdf`

### 2. Books and independent derivations

- **Fundamentals of Machine Learning for Predictive Data Analytics — Kelleher Chapter 7 — error-based learning and neural networks**
  - Use: `book` · depth `course-aligned` · scope `complementary`
  - Exact locator: `Ch 7 Error-based Learning, pdf pp. 351-424 (the multi-layer network and backpropagation sections)`
  - Covers: Artificial neurons and linear-model equivalence, Nonlinearity, activation functions, and XOR, Multilayer forward passes, shapes, and parameter counts, Loss gradients and backpropagation, Training, generalization, and practical choices
  - Angle: Arrives at neural networks by extending the linear model of L03 rather than by starting over — the same route L15's first slides take.
  - Why this angle matters: Because Kelleher's Ch 7 is one continuous argument from simple linear regression to multi-layer networks, the continuity L15 asserts on its opening slide (a neuron without an activation is a linear model) is the chapter's actual structure. Reading it in order makes backpropagation feel like the same gradient descent applied through more layers, which is the correct impression and not the one a standalone treatment gives.
  - Local target: `material://source-kelleher-fmlpda/kelleher.pdf`
- **Nielsen — Neural Networks and Deep Learning (free web book) — Nielsen Ch 1-2 — one network, built and then differentiated**
  - Use: `book` · depth `derivation` · scope `complementary`
  - Exact locator: `Ch 1 'Using neural nets to recognize handwritten digits' and Ch 2 'How the backpropagation algorithm works' (the four fundamental equations of backpropagation)`
  - Covers: Artificial neurons and linear-model equivalence, Nonlinearity, activation functions, and XOR, Multilayer forward passes, shapes, and parameter counts, Loss gradients and backpropagation
  - Angle: Reduces backpropagation to four equations, states them, then proves each — the most learnable decomposition of the algorithm available.
  - Why this angle matters: Ch 2's device is to name four equations (the output-layer error, the error recursion backwards through a layer, and the two parameter-gradient formulas) and treat everything else as consequence. That gives you four things to remember instead of a derivation to reproduce, and each is short enough to check. Ch 1 first builds the network on a real digit-recognition task so the abstractions have a referent. Free, and Ch 4's visual proof of universal approximation is the best available treatment of L15's universality node.
- **Nielsen — Neural Networks and Deep Learning (free web book) — Nielsen Ch 4 — the visual proof of universal approximation**
  - Use: `book` · depth `intuition` · scope `complementary`
  - Exact locator: `Ch 4 'A visual proof that neural nets can compute any function' (complete chapter, interactive figures)`
  - Covers: Expressiveness and universal approximation, Nonlinearity, activation functions, and XOR
  - Angle: Constructs the approximation by hand — step functions built from sigmoid pairs, then summed into any shape.
  - Why this angle matters: L15 states the universal approximation theorem. This chapter shows you how to build the approximation: push a sigmoid's weight up until it becomes a step, pair two steps into a bump, then sum bumps to trace any curve. It is a construction rather than an existence proof, so it is genuinely convincing, and the interactive figures let you set the parameters yourself. The best hour available on L15's universality node.
- **Mathematics for Machine Learning — MML Ch 5 — vector calculus and backpropagation**
  - Use: `book` · depth `derivation` · scope `complementary`
  - Exact locator: `Ch 5 Vector Calculus §5.5 gradients of matrices, §5.6 useful identities, §5.7 backpropagation and automatic differentiation`
  - Covers: Loss gradients and backpropagation, Multilayer forward passes, shapes, and parameter counts
  - Angle: Supplies the matrix-derivative identities backpropagation uses, which every other L15 route assumes you already have.
  - Why this angle matters: The obstacle in a backpropagation derivation is rarely the chain rule — it is knowing the derivative of a matrix product with respect to a matrix, and keeping the shapes straight. §5.6 tabulates exactly those identities, and §5.7 then applies them to a network. If the CS229 notes or Murphy's treatment looked like symbol soup, this is the missing prerequisite rather than an alternative explanation.
- **CS229 Lecture Notes (Stanford) — CS229 §7 — compact neural-network derivation**
  - Use: `course-material` · depth `advanced-reference` · scope `complementary`
  - Exact locator: `Main notes §7 Deep Learning (the neural-network and backpropagation sections)`
  - Covers: Multilayer forward passes, shapes, and parameter counts, Loss gradients and backpropagation
  - Angle: Backpropagation written out as matrix derivative bookkeeping, in the most compact correct form available here.
  - Why this angle matters: Six pages that state the forward pass, define the loss, and derive the layer-by-layer gradients with explicit shapes. If you already understand the chain rule and want the algorithm precisely, this is faster than any book on the shelf. If you do not yet have the picture, it will be opaque — start with 3Blue1Brown episodes 3-4 and return here.
  - Local target: `material://source-cs229-notes/cs229-notes.pdf`

### 3. Visual, implementation and additional practice

- **3Blue1Brown — Essence of Calculus — 3Blue1Brown — the chain rule, which is all backpropagation is**
  - Use: `video` · depth `intuition` · scope `prerequisite`
  - Exact locator: `Essence of Calculus episode 4 ('Visualizing the chain rule and product rule')`
  - Covers: Loss gradients and backpropagation
  - Angle: Makes the chain rule a statement about how one small nudge propagates, which is exactly the quantity backpropagation computes.
  - Why this angle matters: Backpropagation is the chain rule applied repeatedly, so if the chain rule is a symbolic manipulation rather than a claim about how a change in one quantity affects another downstream, the derivation cannot mean anything. This episode fixes that in fifteen minutes, and it is the natural companion to the neural-network playlist's episode 4, which assumes it.
- **Karpathy — micrograd (spelled-out backpropagation) — Karpathy — micrograd, backpropagation spelled out**
  - Use: `video` · depth `implementation` · scope `complementary`
  - Exact locator: `'The spelled-out intro to neural networks and backpropagation: building micrograd' (≈2h25m); the derivative and backward-pass segments are the first half`
  - Covers: Loss gradients and backpropagation, Multilayer forward passes, shapes, and parameter counts, Training, generalization, and practical choices
  - Angle: Writes an autograd engine line by line, so the chain rule becomes a local rule attached to each operation.
  - Why this angle matters: The insight the video delivers is that backpropagation is not a formula for a network — it is a small local rule per operation, composed by the graph. Once each node knows how to pass gradient to its inputs, networks of any shape work with no new mathematics. That reframing is what makes L15's derivation feel inevitable rather than intricate. Long, and requires following along in code to get the benefit; treat it as an afternoon, not a lookup.
- **Zhang et al. — Dive into Deep Learning (D2L) — D2L — multilayer perceptrons and forward/backward propagation**
  - Use: `book` · depth `implementation` · scope `complementary`
  - Exact locator: `The 'Multilayer Perceptrons' chapter: the MLP section, the implementation-from-scratch section, and 'Forward Propagation, Backward Propagation, and Computational Graphs'`
  - Covers: Multilayer forward passes, shapes, and parameter counts, Loss gradients and backpropagation, Training, generalization, and practical choices, Nonlinearity, activation functions, and XOR
  - Angle: Implements the same network twice — from scratch and with a framework — so what the framework hides is explicit.
  - Why this angle matters: The from-scratch implementation writes the forward pass and the gradients as ordinary array arithmetic; the concise implementation replaces them with two library calls. Seeing the pair is what makes the framework legible rather than magical, which matters beyond this exam given the thesis workstream. The forward/backward/computational-graph section draws the graph and annotates memory cost, explaining why activations must be stored during the forward pass.
- **StatQuest with Josh Starmer (YouTube) — StatQuest — neural networks and backpropagation**
  - Use: `video` · depth `orientation` · scope `complementary`
  - Exact locator: `'Neural Networks Part 1 — Inside the Black Box'; 'Backpropagation Main Ideas'; 'Stochastic Gradient Descent, Clearly Explained' (≈15-20 min each)`
  - Covers: Artificial neurons and linear-model equivalence, Multilayer forward passes, shapes, and parameter counts, Loss gradients and backpropagation
  - Angle: Shows activation functions being scaled and summed into an arbitrary curve — the mechanical basis of universal approximation.
  - Why this angle matters: Part 1's central demonstration is that two hidden units with a soft activation can be weighted and added to produce a bent curve fitting the data, built up piece by piece on screen. That is L15's universality node made visible without any theorem. The backpropagation video then updates one weight at a time with the numbers shown, and the SGD video explains why the gradient is estimated on a batch rather than the full data — a practical point L15 lists without motivating.
- **Cornell CS4780 homework sets (local copies) — Cornell CS4780 HW9 — neural networks and ReLU**
  - Use: `exercise` · depth `practice` · scope `complementary`
  - Exact locator: `2018Fall/HW9 and 2018Spring/HW9 (neural networks and ReLU), with the published solutions`
  - Covers: Nonlinearity, activation functions, and XOR, Multilayer forward passes, shapes, and parameter counts, Loss gradients and backpropagation
  - Angle: Forward and backward passes computed by hand on small networks, with the answers to check against.
  - Why this angle matters: Hand computation is the only reliable test of whether backpropagation is understood, and these sets provide it at the right scale — networks small enough to finish, large enough to require the bookkeeping. The ReLU problems also make the non-differentiability at zero explicit, which the deck passes over.
- **MIT 6.034 Artificial Intelligence quizzes — MIT 6.034 quizzes — neural-network tracing**
  - Use: `exercise` · depth `practice` · scope `complementary`
  - Exact locator: `The published 6.034 quizzes and finals — the neural-network forward/backward tracing questions, with solutions`
  - Covers: Artificial neurons and linear-model equivalence, Nonlinearity, activation functions, and XOR, Multilayer forward passes, shapes, and parameter counts
  - Angle: Small networks traced numerically under exam conditions, including weight updates.
  - Why this angle matters: The same procedural virtue as the tree questions: execute the computation, show the state. For L15 that means a forward pass with given weights, a loss, and one update step — which is the realistic scope of a neural-network exam question in a combined three-hour paper.
- **3Blue1Brown — Neural Networks playlist (4 videos) — 3Blue1Brown — Neural Networks playlist**
  - Use: `video` · depth `orientation` · scope `complementary`
  - Exact locator: `Episodes 1-4: 'But what is a neural network?', 'Gradient descent, how neural networks learn', 'What is backpropagation really doing?', 'Backpropagation calculus' (≈15-20 min each)`
  - Covers: Artificial neurons and linear-model equivalence, Nonlinearity, activation functions, and XOR, Multilayer forward passes, shapes, and parameter counts, Loss gradients and backpropagation
  - Angle: Episode 3 shows backpropagation as each training example 'voting' on how every weight should change — the intuition before the calculus.
  - Why this angle matters: The four episodes are deliberately staged: what the network computes, what the loss surface looks like, what backpropagation is doing conceptually, and only then the chain-rule algebra in episode 4. Watching 1-3 before reading any derivation is the highest-return hour available for L15, because the derivation is bookkeeping once the picture exists. Episode 4 maps directly onto the deck's gradient slides.
- **Géron — Hands-On Machine Learning (local) — Geron Ch 10 - MLP shapes and outputs made concrete**
  - Use: `book` · depth `implementation` · scope `complementary`
  - Exact locator: `Chapter 10, pp. 303-350`
  - Covers: Artificial neurons and linear-model equivalence, Nonlinearity, activation functions, and XOR, One-hot targets, output layers, and softmax, Multilayer forward passes, shapes, and parameter counts
  - Angle: Gives the L15 forward pass an executable form: layer widths, parameter counts, activation choice and the output/loss pairing for regression, binary and multiclass targets that the deck states as a table.
  - Why this angle matters: Forty-eight pages that make network shapes concrete: how many parameters a given architecture has, what the output layer must look like for binary, multiclass and regression targets, and how the loss must match the output. That is precisely what L15's forward-pass and output nodes cover, and precisely what the SaD Übungen ask you to compute. Working through the shapes here is direct exam preparation.
  - Local target: `material://source-geron-handson/geron.pdf`
- **Géron — Hands-On Machine Learning (local) — Geron Ch 11 - the training choices L15 lists as tricks**
  - Use: `book` · depth `implementation` · scope `complementary`
  - Exact locator: `Chapter 11, pp. 351-392`
  - Covers: Training, generalization, and practical choices
  - Angle: The deck's 'practical tricks' slide (initialisation, learning rate, stopping, regularisation) is one bullet list; this chapter is that list worked out, which is what the stage's generalisation claim needs as evidence.
  - Why this angle matters: L15 closes with a list of practical training choices — initialisation, activation, optimiser, regularization — presented as things practitioners do. Ch 11 explains what each is solving: vanishing gradients, dead units, slow convergence, overfitting. Turning a list of tricks into a list of problems-and-solutions is what makes it retainable and is the difference between recognising the terms and being able to justify a choice.
  - Local target: `material://source-geron-handson/geron.pdf`
- **Marsland — Machine Learning: An Algorithmic Perspective (2nd ed.) — Marsland Ch 3-4 - from the single neuron to backprop and universality**
  - Use: `book` · depth `implementation` · scope `complementary`
  - Exact locator: `Chapter 3, pp. 60-91 and Chapter 4, pp. 92-131 (XOR p. 92; hidden layer p. 94; back-propagation p. 95; universal approximation p. 107)`
  - Covers: Artificial neurons and linear-model equivalence, Nonlinearity, activation functions, and XOR, Multilayer forward passes, shapes, and parameter counts, Loss gradients and backpropagation, Expressiveness and universal approximation
  - Angle: Follows the exact L15 arc - perceptron, the XOR show-stopper, hidden layers, back-propagation - and is the only registered source that states the universal-approximation result the deck asserts on slide 36.
  - Why this angle matters: Chapters 3 and 4 are the classical route into neural networks and they earn their place through the XOR example on p. 92: a problem a single layer provably cannot solve, followed immediately by the hidden layer that solves it (p. 94). That is L15's activation node argued rather than asserted. Backpropagation (p. 95) is then derived and implemented, and universal approximation (p. 107) is stated with its caveats. Together this is the most complete L15 coverage on the shelf at course level.
  - Local target: `material://source-marsland-ml-algorithmic/Machine Learning_ An Algorithmic Perspective (2nd ed.) [Marsland 2014-10-08].pdf`
- **Brandon Rohrer — End-to-End Machine Learning blog/courses — Brandon Rohrer — friendly neural-network explanation**
  - Use: `website` · depth `orientation` · scope `complementary`
  - Exact locator: `The 'How neural networks work' article and companion video on e2eml.school`
  - Covers: Artificial neurons and linear-model equivalence, Multilayer forward passes, shapes, and parameter counts
  - Angle: Builds a tiny network out of explicit arithmetic with no calculus at all.
  - Why this angle matters: Every quantity is a small number and every step is an addition or a multiplication, which removes the notation barrier entirely. Useful as a first contact or as a reset if the gradients have become symbol-pushing. The trade-off is that it stops well before anything examinable — follow it with 3Blue1Brown episode 4 or Marsland Ch 4.

### 4. University courses, prior-year, exam and advanced reference

- **SaD 2025 lecture recordings (WiSe 2025 run) — 2025 neural networks Part 1 — affine models, outputs and SGD**
  - Use: `course-material` · depth `advanced-reference` · scope `prior-year`
  - Exact locator: `14_neural_nets_part1.pdf, slides 8-89`
  - Covers: Artificial neurons and linear-model equivalence, One-hot targets, output layers, and softmax, Multilayer forward passes, shapes, and parameter counts, Training, generalization, and practical choices
  - Angle: Spends a full session on the one-layer network, softmax outputs and gradient-descent setup that 2026 compresses.
  - Why this angle matters: Part 1 is the slower course-level bridge from affine transformations to a trainable classifier. It is especially useful when matrix shapes or the distinction between logits and probabilities is the problem. It predates the current deck, so it elaborates but never defines 2026 scope.
  - Local target: `material://source-sad-2025-recordings/14_neural_nets_part1.pdf`
- **SaD 2025 lecture recordings (WiSe 2025 run) — 2025 neural networks Part 2 — loss landscape, gradients and depth**
  - Use: `course-material` · depth `advanced-reference` · scope `prior-year`
  - Exact locator: `15_neural_nets_part2.pdf, slides 2-223`
  - Covers: Nonlinearity, activation functions, and XOR, One-hot targets, output layers, and softmax, Multilayer forward passes, shapes, and parameter counts, Loss gradients and backpropagation, Training, generalization, and practical choices, Expressiveness and universal approximation, CNN, RNN, and Transformer outlook
  - Angle: Provides the course's most detailed treatment of cross-entropy, gradient computation, nonlinear depth and XOR.
  - Why this angle matters: Part 2 follows one loss landscape through partial derivatives and weight updates before showing why hidden nonlinearities solve problems a one-layer classifier cannot. It is much longer than the current lecture: use only the section matching a recorded gap, and check terminology against the 2026 deck.
  - Local target: `material://source-sad-2025-recordings/15_neural_nets_part2.pdf`
- **An Introduction to Statistical Learning (Python edition) — ISLP §§10.1–10.2 — gentle neural-network introduction**
  - Use: `book` · depth `derivation` · scope `complementary`
  - Exact locator: `Ch 10 Deep Learning, pdf pp. 406-462 (§10.1 single layer neural networks p. 407; §10.2 multilayer neural networks p. 409; Ch 10 lab p. 439)`
  - Covers: Artificial neurons and linear-model equivalence, Nonlinearity, activation functions, and XOR, One-hot targets, output layers, and softmax, Multilayer forward passes, shapes, and parameter counts, Training, generalization, and practical choices
  - Angle: Written for readers who already know linear regression, so every neural-network idea is introduced as a modification of something familiar.
  - Why this angle matters: §10.1 literally begins by writing a single-layer network as a linear model with a nonlinear transformation of derived features, which is L15's own opening claim made precise. For a reader coming from L03 rather than from a deep-learning course, this is the least disorienting introduction on the shelf. It is also the shallowest: no backpropagation derivation, and the training discussion is brief. Pair with Marsland Ch 4 or Nielsen Ch 2 for the gradient work.
  - Local target: `material://source-islp/islp.pdf`
- **MIT 6.036 Introduction to Machine Learning (Open Learning Library) — MIT 6.036 — neural network units**
  - Use: `course` · depth `course-aligned` · scope `complementary`
  - Exact locator: `The neural-network units on the Open Learning Library (forward pass, loss, backpropagation), with their auto-graded exercises`
  - Covers: Artificial neurons and linear-model equivalence, Multilayer forward passes, shapes, and parameter counts, Loss gradients and backpropagation, Nonlinearity, activation functions, and XOR
  - Angle: Small numeric forward and backward passes with instant grading — the fastest way to find out whether the mechanics are right.
  - Why this angle matters: The L15 failure mode is believing you can do a forward pass until you try one and get the shapes wrong. These exercises are sized for that check and grade immediately, so an error is caught in seconds rather than at the end of a written derivation. Pair with the SaD Übungen, which set the same kind of task in the course's own notation.
- **Prince — Understanding Deep Learning — Prince Ch 3-4 — shallow and deep networks, illustrated**
  - Use: `book` · depth `course-aligned` · scope `complementary`
  - Exact locator: `Ch 3 'Shallow neural networks' and Ch 4 'Deep neural networks' (the piecewise-linear region figures), with the chapter problems`
  - Covers: Artificial neurons and linear-model equivalence, Nonlinearity, activation functions, and XOR, Multilayer forward passes, shapes, and parameter counts, Expressiveness and universal approximation
  - Angle: Shows a ReLU network as a function made of linear pieces, and counts how many pieces depth buys — a concrete answer to why depth helps.
  - Why this angle matters: Prince's figures draw the input space partitioned into linear regions and show the count growing with depth far faster than with width. That converts 'deeper networks are more expressive' from a slogan into a countable claim, which is what L15's universality and outlook nodes are reaching for. The illustrations are the best in any book on this shelf, and the PDF is free from the author's site.
- **Goodfellow, Bengio & Courville — Deep Learning (MIT Press, free web book) — Goodfellow Ch 6 — deep feedforward networks**
  - Use: `book` · depth `advanced-reference` · scope `complementary`
  - Exact locator: `Ch 6 'Deep Feedforward Networks' §6.1 the XOR example, §6.2 gradient-based learning and cost functions, §6.3 hidden units, §6.5 back-propagation and other differentiation algorithms`
  - Covers: Nonlinearity, activation functions, and XOR, One-hot targets, output layers, and softmax, Loss gradients and backpropagation, Expressiveness and universal approximation
  - Angle: Explains why the output unit and the loss function must be chosen together, deriving each pairing from maximum likelihood.
  - Why this angle matters: §6.2 is the section worth the visit: sigmoid with cross-entropy, softmax with categorical cross-entropy, and linear with squared error are not conventions but consequences of writing the negative log-likelihood for the corresponding output distribution. L15's output-layer node presents the pairings as facts. This also explains the vanishing-gradient problem that arises when the wrong pairing is used. Reference-level density; read the section, not the chapter.
- **Data Science and Machine Learning — Kroese — neural-network reference**
  - Use: `book` · depth `derivation` · scope `complementary`
  - Exact locator: `Ch 9 Deep Learning, pdf pp. 341-372; App B Multivariate Differentiation and Optimization, pdf pp. 415-438`
  - Covers: Multilayer forward passes, shapes, and parameter counts, Loss gradients and backpropagation, Training, generalization, and practical choices
  - Angle: Keeps the matrix calculus needed for backpropagation in an appendix you can consult while reading the chapter.
  - Why this angle matters: Backpropagation is chain-rule bookkeeping over matrices, and the usual obstacle is not the idea but the notation for derivatives of vector-valued functions. Having App B in the same book, in the same notation, means the gradient steps in Ch 9 can be checked rather than accepted. Denser than the deck requires; useful if the derivation is what you want.
  - Local target: `material://source-kroese-dsml/kroese.pdf`
- **Stanford CS229 Machine Learning (Spring 2022 lectures) — Stanford CS229 — neural-network lecture**
  - Use: `course` · depth `advanced-reference` · scope `complementary`
  - Exact locator: `The 2022 neural-networks lecture (the first of the deep-learning lectures on the playlist)`
  - Covers: Multilayer forward passes, shapes, and parameter counts, Loss gradients and backpropagation, Training, generalization, and practical choices
  - Angle: Motivates depth by showing what a single layer cannot represent, before showing what more layers buy.
  - Why this angle matters: The lecture spends real time on the representational question — what functions are and are not reachable — which is L15's universality node treated as a question rather than a stated theorem. Also useful for hearing how a practitioner describes the training loop, which the deck lists as practical choices.
- **Probabilistic Machine Learning: An Introduction — Murphy §§13.2–13.3 — neural-network depth**
  - Use: `book` · depth `advanced-reference` · scope `complementary`
  - Exact locator: `§§13.2-13.3 multilayer perceptrons and backpropagation (Part III Deep Neural Networks, pdf pp. 453-574)`
  - Covers: Multilayer forward passes, shapes, and parameter counts, Loss gradients and backpropagation, Training, generalization, and practical choices
  - Angle: Presents backpropagation as reverse-mode automatic differentiation on a computation graph, which is what frameworks actually implement.
  - Why this angle matters: L15 derives the gradients by hand for a small network. Murphy names the general algorithm that generalises it and explains why the reverse sweep is the efficient direction when there are many parameters and one scalar loss. That connection between the hand derivation and what PyTorch does is worth having, especially given the thesis workstream. Well beyond exam scope.
  - Local target: `material://source-murphy-pml1/pml1.pdf`
- **Machine Learning and Data Mining — CSC 411 notes (Toronto) — CSC411 notes — compact neural-network reference**
  - Use: `course-material` · depth `advanced-reference` · scope `complementary`
  - Exact locator: `The neural-network and backpropagation lecture notes (Toronto CSC411/2515 course notes)`
  - Covers: Multilayer forward passes, shapes, and parameter counts, Loss gradients and backpropagation
  - Angle: Compact backprop reference with explicit matrix shapes at every step.
  - Why this angle matters: Shape errors are the most common failure when reproducing a forward or backward pass, and these notes annotate every quantity's dimensions. That makes them a good checking reference beside the SaD Übungen's parameter-counting exercises, which are the likeliest L15 exam form.
  - Local target: `material://source-csc411-notes/csc411.pdf`
- **AML — Angewandtes Maschinelles Lernen, lecture slides (SoSe 2026) — AML L08–L09 — feedforward networks and training**
  - Use: `course-material` · depth `advanced-reference` · scope `optional`
  - Exact locator: `lecture-slides/VL 08-feedforward-neural-network.pdf and VL 09-training-neural-networks.pdf`
  - Covers: Nonlinearity, activation functions, and XOR, One-hot targets, output layers, and softmax, Multilayer forward passes, shapes, and parameter counts, Loss gradients and backpropagation, Training, generalization, and practical choices
  - Angle: The AML treatment of the same networks, with a whole deck devoted to training rather than a summary slide.
  - Why this angle matters: SaD compresses initialisation, learning rates, regularization and the practicalities of training into a handful of slides at the end of L15; AML gives them a lecture. Since both exams are in the same period, reading the AML deck covers SaD's training node and AML's own material simultaneously. AML L09 owns the neural-network regularization material and does not cover batch normalization — a distinction already recorded in this repository's wiring notes.
- **UMich EECS 498-007 — Deep Learning for Computer Vision (Johnson) — UMich EECS 498 — fully connected and architecture depth**
  - Use: `course` · depth `advanced-reference` · scope `optional`
  - Exact locator: `Lectures on fully connected networks and backpropagation (roughly lectures 4-6 of the Michigan Deep Learning for Computer Vision playlist)`
  - Covers: Multilayer forward passes, shapes, and parameter counts, Training, generalization, and practical choices, CNN, RNN, and Transformer outlook
  - Angle: Draws the computation graph and propagates gradients through it node by node, on the board.
  - Why this angle matters: The computational-graph presentation is the one that generalises: instead of deriving gradients for a specific architecture, you learn a local rule that composes. Watching it applied to a concrete graph is the step between L15's hand derivation and understanding what a framework does. Beyond SaD scope, and directly useful for AML and the thesis workstream.

## What is deliberately not forced into the sequence

The full menu is available on every matching concept stage, but the plan does not preselect all books or ask for a second full course. Measure-theoretic probability (Swanson and the Regensburg paper), full CS229/18.650 depth, reinforcement learning, general linear-algebra archives, and unrelated mathematics-prep collections remain reference-only or out of direct SaD scope. Their dispositions are recorded in the coverage audit rather than silently omitted.
