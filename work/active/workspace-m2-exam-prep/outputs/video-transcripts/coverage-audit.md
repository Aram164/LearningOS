# SaD video coverage audit

Source: route-records.yaml (65 video routes post-recheck, 13 units + 1 reassigned L02 claim). Claims come from transcript evidence;
confidence is post-recheck (35 downgraded to low, 6 removed, 9 duplicate covers deduped, 1 operator-confirmed medium). Gaps are reported plainly.

Plan-contract basis for the six completeness checks: local inventory = 65/65 transcripts present; linked inventory =
65/65 URLs verified live 2026-09-15 (VERIFIED-URLS.txt); materials checked via word-verified captions (682/685 words,
zero foreign words) plus adversarial line-level recheck, videos themselves not watched by design; prior scope reconciled
against 7 already-routed videos (6 repaired in place, YG15 held out); duplicates checked (covers deduped, route ids
uniqueness-checked); exclusions recorded here and below (YG15m2VwSjA + XLCWeSVzHUU excluded with reasons; 3oZrS3ZWVcA
reassigned L01→L02 by operator direct read as a reviewed first-cross-unit exception).

## Local

Local evidence is 65 fetched caption transcripts under BASE/transcripts/, one per video, word-verified against
independently held copies (682 of 685 distinct words, zero words present that were not in the source). No video
bytes were downloaded and nothing was added to the materials registry; the transcripts are verification inputs,
not owned material. Per-video proposals (BASE/proposals/), line-level recheck verdicts (BASE/recheck/) and angle
sidecars (BASE/angles/) are the recorded audit trail from evidence to claim.

## Linked

All 65 URLs verified live on YouTube on 2026-09-15 (VERIFIED-URLS.txt). Channel-to-source mapping: StatQuest (30),
Kurzes Tutorium Statistik (12), jbstatistics (10), zedstatistics (3) and Karpathy micrograd (1) route under existing
registry sources; 3Blue1Brown videos route under the matching playlist source except the CLT video, which needs the
new draft source-3b1b-central-limit-theorem; the Iain Gaussian video needs the new draft
source-iain-gaussian-distribution (both staged uncommitted in sources/registry/mathematics.yaml). Seven videos were
already routed: six SaD routes are repaired in place under their existing ids, and YG15m2VwSjA (already routed on
Analysis ch06) is excluded with its record retained.

## Completeness

Boundaries of this package: 63 routes (57 new inserts, 6 in-place repairs across 13 units). Excluded: YG15m2VwSjA
(teaches nothing claimable; Analysis ch06 route stands) and XLCWeSVzHUU (no worked segments anywhere; motivation
only). 3oZrS3ZWVcA ships reassigned L01→L02 as a reviewed exception. Uncovered and all-low-confidence nodes are
listed per unit below and are genuine gaps, not omissions: L05 is thinnest (5 of 7 nodes uncovered), and the L08
German CLT gap is confirmed (zero German-channel L08 routes) and recorded unfilled. No stage placements are added
or changed; one L06 placement inherits its locator from a repaired route and will resolve to verified timestamps
after import.

## unit-m2-sad-l01 (6 videos)

- knowledge-sad-l01-data-questions — 
  - NO VIDEO COVERAGE
- knowledge-sad-l01-location — 
  - [high] HsDeAoBOyS4 (Boxplots ... und auch Median und Quartile ;o), Kurzes Tutorium Statistik)
  - [high] ybyunHdinXo (Arithmetisches Mittel & Median einfach erklärt: Anwendung und Unterschied mit Beispiel, Kurzes Tutorium Statistik)
- knowledge-sad-l01-distributions — 
  - [low] HsDeAoBOyS4 (Boxplots ... und auch Median und Quartile ;o), Kurzes Tutorium Statistik)
- knowledge-sad-l01-sampling-context — 
  - [low] HZGCoVF3YvM (Bayes theorem, the geometry of changing beliefs, 3Blue1Brown)
- knowledge-sad-l01-classification — 
  - [high] Kdsp6soqA7o (Machine Learning Fundamentals: The Confusion Matrix, StatQuest with Josh Starmer)
  - [high] lG4VkPoG3ko (The medical test paradox, and redesigning Bayes' rule, 3Blue1Brown)
  - [high] vP06aMoz4v8 (Machine Learning Fundamentals: Sensitivity and Specificity, StatQuest with Josh Starmer)
- knowledge-sad-l01-base-rates — 
  - [high] HZGCoVF3YvM (Bayes theorem, the geometry of changing beliefs, 3Blue1Brown)
  - [high] lG4VkPoG3ko (The medical test paradox, and redesigning Bayes' rule, 3Blue1Brown)
- knowledge-sad-l01-course-map — 
  - NO VIDEO COVERAGE

Uncovered nodes: knowledge-sad-l01-data-questions, knowledge-sad-l01-course-map
All-low-confidence nodes: knowledge-sad-l01-distributions, knowledge-sad-l01-sampling-context

## unit-m2-sad-l02 (4 videos)

- knowledge-sad-l02-vocabulary — 
  - [medium] FZ4pEQxkVhU (Skalenniveaus einfach erklärt: Nominal-, Ordinal-, Intervall- und Verhältnisskala mit Beispiel, Kurzes Tutorium Statistik)
  - [high] aJDXIG1P738 (Statistik Grundlagen: Grundbegriffe einfach erklärt (Grundgesamtheit, Merkmal, Merkmalsträger), Kurzes Tutorium Statistik)
- knowledge-sad-l02-scales — 
  - [high] FZ4pEQxkVhU (Skalenniveaus einfach erklärt: Nominal-, Ordinal-, Intervall- und Verhältnisskala mit Beispiel, Kurzes Tutorium Statistik)
- knowledge-sad-l02-frequencies — 
  - NO VIDEO COVERAGE
- knowledge-sad-l02-location — 
  - [medium] qcTcsEdMgBo (Range | Interquartile Range (IQR) | Box and whisker plot, zedstatistics)
- knowledge-sad-l02-dispersion — 
  - [medium] 3oZrS3ZWVcA (Streumaße - Varianz, Standardabweichung, Variationskoeffizient und mehr!, Kurzes Tutorium Statistik)
  - [low] qcTcsEdMgBo (Range | Interquartile Range (IQR) | Box and whisker plot, zedstatistics)
- knowledge-sad-l02-simpson — 
  - NO VIDEO COVERAGE
- knowledge-sad-l02-sampling — 
  - NO VIDEO COVERAGE

Uncovered nodes: knowledge-sad-l02-frequencies, knowledge-sad-l02-simpson, knowledge-sad-l02-sampling
All-low-confidence nodes: none

## unit-m2-sad-l03 (5 videos)

- knowledge-sad-l03-paired-data — 
  - [high] 3I-aLUc6ylQ (Streudiagramm & Korrelationskoeffizient einfach erklärt – anschaulich mit Alwins Restaurant, Kurzes Tutorium Statistik)
  - [high] xZ_z8KWkhXE (Pearson's Correlation, Clearly Explained!!!, StatQuest with Josh Starmer)
- knowledge-sad-l03-covariance — 
  - [high] 3I-aLUc6ylQ (Streudiagramm & Korrelationskoeffizient einfach erklärt – anschaulich mit Alwins Restaurant, Kurzes Tutorium Statistik)
  - [high] xZ_z8KWkhXE (Pearson's Correlation, Clearly Explained!!!, StatQuest with Josh Starmer)
- knowledge-sad-l03-interpretation — 
  - [medium] xZ_z8KWkhXE (Pearson's Correlation, Clearly Explained!!!, StatQuest with Josh Starmer)
- knowledge-sad-l03-simple-regression — 
  - [high] Ekbw28n6IX0 (Regression - Methode der kleinsten Fehlerquadrate, Kurzes Tutorium Statistik)
  - [high] PaFPbb66DxQ (The Main Ideas of Fitting a Line to Data (The Main Ideas of Least Squares and Linear Regression.), StatQuest with Josh Starmer)
- knowledge-sad-l03-multivariate — 
  - NO VIDEO COVERAGE
- knowledge-sad-l03-gradient-descent — 
  - [high] sDv4f4s2SB8 (Gradient Descent, Step-by-Step, StatQuest with Josh Starmer)
- knowledge-sad-l03-scaling-weights — 
  - NO VIDEO COVERAGE

Uncovered nodes: knowledge-sad-l03-multivariate, knowledge-sad-l03-scaling-weights
All-low-confidence nodes: none

## unit-m2-sad-l04 (2 videos)

- knowledge-sad-l04-framing — 
  - NO VIDEO COVERAGE
- knowledge-sad-l04-events — 
  - NO VIDEO COVERAGE
- knowledge-sad-l04-axioms — 
  - NO VIDEO COVERAGE
- knowledge-sad-l04-conditional — 
  - [high] ZlBog_1EyAM (Bedingte Wahrscheinlichkeit, Satz von Bayes und stochastische Unabhängigkeit, Kurzes Tutorium Statistik)
- knowledge-sad-l04-bayes — 
  - [low] O2L2Uv9pdDA (Naive Bayes, Clearly Explained!!!, StatQuest with Josh Starmer)
  - [high] ZlBog_1EyAM (Bedingte Wahrscheinlichkeit, Satz von Bayes und stochastische Unabhängigkeit, Kurzes Tutorium Statistik)
- knowledge-sad-l04-independence — 
  - [medium] ZlBog_1EyAM (Bedingte Wahrscheinlichkeit, Satz von Bayes und stochastische Unabhängigkeit, Kurzes Tutorium Statistik)
- knowledge-sad-l04-naive-bayes — 
  - [high] O2L2Uv9pdDA (Naive Bayes, Clearly Explained!!!, StatQuest with Josh Starmer)

Uncovered nodes: knowledge-sad-l04-framing, knowledge-sad-l04-events, knowledge-sad-l04-axioms
All-low-confidence nodes: none

## unit-m2-sad-l05 (2 videos)

- knowledge-sad-l05-decision-grid — 
  - [medium] L2KMttDm3aY (An Introduction to the Hypergeometric Distribution, jbstatistics)
- knowledge-sad-l05-permutations — 
  - NO VIDEO COVERAGE
- knowledge-sad-l05-variations — 
  - NO VIDEO COVERAGE
- knowledge-sad-l05-combinations — 
  - NO VIDEO COVERAGE
- knowledge-sad-l05-repetition — 
  - NO VIDEO COVERAGE
- knowledge-sad-l05-counting-probability — 
  - [high] L2KMttDm3aY (An Introduction to the Hypergeometric Distribution, jbstatistics)
  - [low] udyAvvaMjfM (Fisher's Exact Test and the Hypergeometric Distribution, StatQuest with Josh Starmer)
- knowledge-sad-l05-identities — 
  - NO VIDEO COVERAGE

Uncovered nodes: knowledge-sad-l05-permutations, knowledge-sad-l05-variations, knowledge-sad-l05-combinations, knowledge-sad-l05-repetition, knowledge-sad-l05-identities
All-low-confidence nodes: none

## unit-m2-sad-l06 (3 videos)

- knowledge-sad-l06-random-variable — 
  - [high] DoHTsDrzAQk (Zufallsvariable, Massenfunktion, Dichtefunktion und Verteilungsfunktion, Kurzes Tutorium Statistik)
  - [medium] Vyk8HQOckIE (The Expected Value and Variance of Discrete Random Variables, jbstatistics)
- knowledge-sad-l06-distribution-functions — 
  - [high] DoHTsDrzAQk (Zufallsvariable, Massenfunktion, Dichtefunktion und Verteilungsfunktion, Kurzes Tutorium Statistik)
- knowledge-sad-l06-transformations — 
  - NO VIDEO COVERAGE
- knowledge-sad-l06-expectation — 
  - [high] KLs_7b7SKi4 (Expected Values, Main Ideas!!!, StatQuest with Josh Starmer)
  - [high] Vyk8HQOckIE (The Expected Value and Variance of Discrete Random Variables, jbstatistics)
- knowledge-sad-l06-variance-covariance — 
  - [high] Vyk8HQOckIE (The Expected Value and Variance of Discrete Random Variables, jbstatistics)
- knowledge-sad-l06-sample-mean — 
  - NO VIDEO COVERAGE
- knowledge-sad-l06-concentration — 
  - [low] Vyk8HQOckIE (The Expected Value and Variance of Discrete Random Variables, jbstatistics)

Uncovered nodes: knowledge-sad-l06-transformations, knowledge-sad-l06-sample-mean
All-low-confidence nodes: knowledge-sad-l06-concentration

## unit-m2-sad-l07 (4 videos)

- knowledge-sad-l07-model-selection — 
  - [low] UrOXRvG9oYE (Overview of Some Discrete Probability Distributions (Binomial,Geometric,Hypergeometric,Poisson,NegB), jbstatistics)
- knowledge-sad-l07-bernoulli-binomial — 
  - [high] J8jNoF-K8E8 (The Binomial Distribution and Test, Clearly Explained!!!, StatQuest with Josh Starmer)
  - [low] UrOXRvG9oYE (Overview of Some Discrete Probability Distributions (Binomial,Geometric,Hypergeometric,Poisson,NegB), jbstatistics)
- knowledge-sad-l07-hypergeometric — 
  - [low] UrOXRvG9oYE (Overview of Some Discrete Probability Distributions (Binomial,Geometric,Hypergeometric,Poisson,NegB), jbstatistics)
- knowledge-sad-l07-geometric — 
  - [high] 2v-4NrbVVr0 (Zufall ohne Gedächtnis: Geometrische & Exponentialverteilung endlich verstehen (mit Alwin ☕), Kurzes Tutorium Statistik)
  - [low] UrOXRvG9oYE (Overview of Some Discrete Probability Distributions (Binomial,Geometric,Hypergeometric,Poisson,NegB), jbstatistics)
- knowledge-sad-l07-poisson — 
  - [low] UrOXRvG9oYE (Overview of Some Discrete Probability Distributions (Binomial,Geometric,Hypergeometric,Poisson,NegB), jbstatistics)
- knowledge-sad-l07-relationships — 
  - [low] 2v-4NrbVVr0 (Zufall ohne Gedächtnis: Geometrische & Exponentialverteilung endlich verstehen (mit Alwin ☕), Kurzes Tutorium Statistik)
  - [low] UrOXRvG9oYE (Overview of Some Discrete Probability Distributions (Binomial,Geometric,Hypergeometric,Poisson,NegB), jbstatistics)

Uncovered nodes: none
All-low-confidence nodes: knowledge-sad-l07-model-selection, knowledge-sad-l07-hypergeometric, knowledge-sad-l07-poisson, knowledge-sad-l07-relationships

## unit-m2-sad-l08 (7 videos)

- knowledge-sad-l08-normal — 
  - [low] RNmDyzYw7aQ (What is a Gaussian Distribution?, Iain Explains Signals, Systems, and Digital Comms)
  - [low] XepXtl9YKwc (Maximum Likelihood, clearly explained!!!, StatQuest with Josh Starmer)
  - [high] iYiOVISWXS4 (An Introduction to the Normal Distribution, jbstatistics)
  - [high] zeJD6dqJ5lo (But what is the Central Limit Theorem?, 3Blue1Brown)
- knowledge-sad-l08-standardization — 
  - [low] iYiOVISWXS4 (An Introduction to the Normal Distribution, jbstatistics)
  - [medium] zeJD6dqJ5lo (But what is the Central Limit Theorem?, 3Blue1Brown)
- knowledge-sad-l08-transform-sum — 
  - [medium] zeJD6dqJ5lo (But what is the Central Limit Theorem?, 3Blue1Brown)
- knowledge-sad-l08-clt — 
  - [high] Pujol1yC1_A (Introduction to the Central Limit Theorem, jbstatistics)
  - [high] YAlJCEDH2uY (The Central Limit Theorem, Clearly Explained!!!, StatQuest with Josh Starmer)
  - [high] zeJD6dqJ5lo (But what is the Central Limit Theorem?, 3Blue1Brown)
- knowledge-sad-l08-approximation — 
  - NO VIDEO COVERAGE
- knowledge-sad-l08-likelihood — 
  - [high] XepXtl9YKwc (Maximum Likelihood, clearly explained!!!, StatQuest with Josh Starmer)
  - [high] pYxNSUDSFH4 (In Statistics, Probability is not Likelihood., StatQuest with Josh Starmer)
- knowledge-sad-l08-mle — 
  - [high] XepXtl9YKwc (Maximum Likelihood, clearly explained!!!, StatQuest with Josh Starmer)

Uncovered nodes: knowledge-sad-l08-approximation
All-low-confidence nodes: none

## unit-m2-sad-l09 (8 videos)

- knowledge-sad-l09-estimator — 
  - [high] DdwTa28W4Os (Intervallschätzungen - Konfidenzintervalle, Kurzes Tutorium Statistik)
  - [high] EJe3jiZNwUU (What are confidence intervals? Actually., zedstatistics)
  - [low] XNgt7F6FqDU (The standard error, Clearly Explained!!!, StatQuest with Josh Starmer)
- knowledge-sad-l09-properties — 
  - NO VIDEO COVERAGE
- knowledge-sad-l09-standard-error — 
  - [high] A82brFpdr9g (Standard Deviation vs Standard Error, Clearly Explained!!!, StatQuest with Josh Starmer)
  - [high] DdwTa28W4Os (Intervallschätzungen - Konfidenzintervalle, Kurzes Tutorium Statistik)
  - [high] EJe3jiZNwUU (What are confidence intervals? Actually., zedstatistics)
  - [low] Uv6nGIgZMVw (Introduction to the t Distribution (non-technical), jbstatistics)
  - [high] XNgt7F6FqDU (The standard error, Clearly Explained!!!, StatQuest with Josh Starmer)
  - [low] Xz0x-8-cgaQ (Bootstrapping Main Ideas!!!, StatQuest with Josh Starmer)
- knowledge-sad-l09-z-interval — 
  - [high] DdwTa28W4Os (Intervallschätzungen - Konfidenzintervalle, Kurzes Tutorium Statistik)
  - [high] EJe3jiZNwUU (What are confidence intervals? Actually., zedstatistics)
  - [medium] Uv6nGIgZMVw (Introduction to the t Distribution (non-technical), jbstatistics)
- knowledge-sad-l09-t-interval — 
  - [low] CF4Vdqiwhaw (Jimmy and Mr. S discuss the interpretation of a confidence interval, jbstatistics)
  - [high] EJe3jiZNwUU (What are confidence intervals? Actually., zedstatistics)
  - [low] Uv6nGIgZMVw (Introduction to the t Distribution (non-technical), jbstatistics)
- knowledge-sad-l09-bootstrap — 
  - [high] TqOeMYtOc1w (Confidence Intervals, Clearly Explained!!!, StatQuest with Josh Starmer)
  - [medium] XNgt7F6FqDU (The standard error, Clearly Explained!!!, StatQuest with Josh Starmer)
  - [high] Xz0x-8-cgaQ (Bootstrapping Main Ideas!!!, StatQuest with Josh Starmer)
- knowledge-sad-l09-data-bias — 
  - [high] CF4Vdqiwhaw (Jimmy and Mr. S discuss the interpretation of a confidence interval, jbstatistics)

Uncovered nodes: knowledge-sad-l09-properties
All-low-confidence nodes: none

## unit-m2-sad-l10 (9 videos)

- knowledge-sad-l10-test-model — 
  - [low] 0oc49DyA3hU (Hypothesis Testing and The Null Hypothesis, Clearly Explained!!!, StatQuest with Josh Starmer)
  - [low] 7mE-K_w1v90 (Type I Errors, Type II Errors, and the Power of the Test, jbstatistics)
  - [high] 8JIe_cz6qGA (Hypothesis testing (ALL YOU NEED TO KNOW!), zedstatistics)
  - [high] JQc3yx0-Q9E (How to calculate p-values, StatQuest with Josh Starmer)
  - [medium] UsU-O2Z1rAs (What is a p-value?  (Updated and extended version), jbstatistics)
  - [high] rbYg5IsOYaM (Einstichproben-t-Test einfach erklärt | Beispiel, Voraussetzungen, Interpretation, Kurzes Tutorium Statistik)
  - [high] tTeMYuS87oU (An Introduction to Hypothesis Testing, jbstatistics)
- knowledge-sad-l10-tails-pvalue — 
  - [high] 8JIe_cz6qGA (Hypothesis testing (ALL YOU NEED TO KNOW!), zedstatistics)
  - [high] JQc3yx0-Q9E (How to calculate p-values, StatQuest with Josh Starmer)
  - [high] UsU-O2Z1rAs (What is a p-value?  (Updated and extended version), jbstatistics)
  - [high] bsZGt-caXO4 (StatQuest:  One or Two Tailed P-Values, StatQuest with Josh Starmer)
  - [low] tTeMYuS87oU (An Introduction to Hypothesis Testing, jbstatistics)
  - [low] vemZtEM63GY (p-values: What they are and how to interpret them, StatQuest with Josh Starmer)
- knowledge-sad-l10-errors-power — 
  - [high] 7mE-K_w1v90 (Type I Errors, Type II Errors, and the Power of the Test, jbstatistics)
  - [high] 8JIe_cz6qGA (Hypothesis testing (ALL YOU NEED TO KNOW!), zedstatistics)
  - [low] UsU-O2Z1rAs (What is a p-value?  (Updated and extended version), jbstatistics)
  - [low] bsZGt-caXO4 (StatQuest:  One or Two Tailed P-Values, StatQuest with Josh Starmer)
  - [low] vemZtEM63GY (p-values: What they are and how to interpret them, StatQuest with Josh Starmer)
- knowledge-sad-l10-z-t — 
  - [high] rbYg5IsOYaM (Einstichproben-t-Test einfach erklärt | Beispiel, Voraussetzungen, Interpretation, Kurzes Tutorium Statistik)
- knowledge-sad-l10-ci-duality — 
  - [medium] 8JIe_cz6qGA (Hypothesis testing (ALL YOU NEED TO KNOW!), zedstatistics)
- knowledge-sad-l10-chi-square — 
  - NO VIDEO COVERAGE
- knowledge-sad-l10-nonparametric — 
  - NO VIDEO COVERAGE
- knowledge-sad-l10-multiple — 
  - NO VIDEO COVERAGE

Uncovered nodes: knowledge-sad-l10-chi-square, knowledge-sad-l10-nonparametric, knowledge-sad-l10-multiple
All-low-confidence nodes: none

## unit-m2-sad-l12 (5 videos)

- knowledge-sad-l12-tree-model — 
  - [low] LsK-xG1cLYA (AdaBoost, Clearly Explained, StatQuest with Josh Starmer)
  - [high] _L39rN6gz7Y (Decision and Classification Trees, Clearly Explained!!!, StatQuest with Josh Starmer)
  - [high] g9c66TUylZ4 (Regression Trees, Clearly Explained!!!, StatQuest with Josh Starmer)
- knowledge-sad-l12-entropy-id3 — 
  - NO VIDEO COVERAGE
- knowledge-sad-l12-regression — 
  - [low] D0efHEJsfHo (How to Prune Regression Trees, Clearly Explained!!!, StatQuest with Josh Starmer)
  - [high] g9c66TUylZ4 (Regression Trees, Clearly Explained!!!, StatQuest with Josh Starmer)
- knowledge-sad-l12-pruning — 
  - [high] D0efHEJsfHo (How to Prune Regression Trees, Clearly Explained!!!, StatQuest with Josh Starmer)
  - [medium] g9c66TUylZ4 (Regression Trees, Clearly Explained!!!, StatQuest with Josh Starmer)
- knowledge-sad-l12-bagging-forest — 
  - [high] J4Wdy0Wc_xQ (StatQuest: Random Forests Part 1 - Building, Using and Evaluating, StatQuest with Josh Starmer)
- knowledge-sad-l12-boosting — 
  - [high] LsK-xG1cLYA (AdaBoost, Clearly Explained, StatQuest with Josh Starmer)
- knowledge-sad-l12-stacking — 
  - NO VIDEO COVERAGE

Uncovered nodes: knowledge-sad-l12-entropy-id3, knowledge-sad-l12-stacking
All-low-confidence nodes: none

## unit-m2-sad-l14 (1 videos)

- knowledge-sad-l14-nb-recap — 
  - [high] H3EjCKtlVog (Gaussian Naive Bayes, Clearly Explained!!!, StatQuest with Josh Starmer)
- knowledge-sad-l14-smoothing — 
  - NO VIDEO COVERAGE
- knowledge-sad-l14-numeric — 
  - [high] H3EjCKtlVog (Gaussian Naive Bayes, Clearly Explained!!!, StatQuest with Josh Starmer)
- knowledge-sad-l14-gaussian — 
  - [high] H3EjCKtlVog (Gaussian Naive Bayes, Clearly Explained!!!, StatQuest with Josh Starmer)
- knowledge-sad-l14-multinomial — 
  - NO VIDEO COVERAGE
- knowledge-sad-l14-bayes-net — 
  - NO VIDEO COVERAGE
- knowledge-sad-l14-markov — 
  - NO VIDEO COVERAGE

Uncovered nodes: knowledge-sad-l14-smoothing, knowledge-sad-l14-multinomial, knowledge-sad-l14-bayes-net, knowledge-sad-l14-markov
All-low-confidence nodes: none

## unit-m2-sad-l15 (9 videos)

- knowledge-sad-l15-neuron — 
  - [high] CqOfi41LfDw (The Essential Main Ideas of Neural Networks, StatQuest with Josh Starmer)
  - [high] VMj-3S1tku0 (The spelled-out intro to neural networks and backpropagation: building micrograd, Andrej Karpathy)
  - [high] aircAruvnKk (But what is a neural network? | Deep learning chapter 1, 3Blue1Brown)
- knowledge-sad-l15-activation — 
  - [high] CqOfi41LfDw (The Essential Main Ideas of Neural Networks, StatQuest with Josh Starmer)
  - [medium] VMj-3S1tku0 (The spelled-out intro to neural networks and backpropagation: building micrograd, Andrej Karpathy)
  - [medium] aircAruvnKk (But what is a neural network? | Deep learning chapter 1, 3Blue1Brown)
- knowledge-sad-l15-output — 
  - NO VIDEO COVERAGE
- knowledge-sad-l15-forward — 
  - [high] CqOfi41LfDw (The Essential Main Ideas of Neural Networks, StatQuest with Josh Starmer)
  - [low] IHZwWFHWa-w (Gradient descent, how neural networks learn | Deep Learning Chapter 2, 3Blue1Brown)
  - [medium] IN2XmBhILt4 (Neural Networks Pt. 2: Backpropagation Main Ideas, StatQuest with Josh Starmer)
  - [low] Ilg3gGewQ5U (Backpropagation, intuitively | Deep Learning Chapter 3, 3Blue1Brown)
  - [medium] VMj-3S1tku0 (The spelled-out intro to neural networks and backpropagation: building micrograd, Andrej Karpathy)
  - [high] aircAruvnKk (But what is a neural network? | Deep learning chapter 1, 3Blue1Brown)
  - [low] tIeHLnjs5U8 (Backpropagation calculus | Deep Learning Chapter 4, 3Blue1Brown)
- knowledge-sad-l15-backprop — 
  - [high] IN2XmBhILt4 (Neural Networks Pt. 2: Backpropagation Main Ideas, StatQuest with Josh Starmer)
  - [low] Ilg3gGewQ5U (Backpropagation, intuitively | Deep Learning Chapter 3, 3Blue1Brown)
  - [high] VMj-3S1tku0 (The spelled-out intro to neural networks and backpropagation: building micrograd, Andrej Karpathy)
  - [high] tIeHLnjs5U8 (Backpropagation calculus | Deep Learning Chapter 4, 3Blue1Brown)
- knowledge-sad-l15-training — 
  - [low] IHZwWFHWa-w (Gradient descent, how neural networks learn | Deep Learning Chapter 2, 3Blue1Brown)
  - [medium] IN2XmBhILt4 (Neural Networks Pt. 2: Backpropagation Main Ideas, StatQuest with Josh Starmer)
  - [low] Ilg3gGewQ5U (Backpropagation, intuitively | Deep Learning Chapter 3, 3Blue1Brown)
  - [medium] VMj-3S1tku0 (The spelled-out intro to neural networks and backpropagation: building micrograd, Andrej Karpathy)
  - [high] vMh0zPT0tLI (Stochastic Gradient Descent, Clearly Explained!!!, StatQuest with Josh Starmer)
- knowledge-sad-l15-universality — 
  - NO VIDEO COVERAGE
- knowledge-sad-l15-outlook — 
  - NO VIDEO COVERAGE

Uncovered nodes: knowledge-sad-l15-output, knowledge-sad-l15-universality, knowledge-sad-l15-outlook
All-low-confidence nodes: none

## Known gap (confirmed, not filled)

No German-channel video covers the central limit theorem (Zentraler Grenzwertsatz): L08 has 0 German video route(s). L08 has no German option for knowledge-sad-l08-clt.
Excluded from import: YG15m2VwSjA (teaches nothing claimable; Analysis ch06 route stands) and XLCWeSVzHUU (no worked segments anywhere; motivation only). Proposals retained for later review.
