---
id: note-11-datascience-intro-pp033-038
type: note
role: reference
title: 'L11 pp. 33–38 — Evaluation: confusion matrix, precision/recall/F, ROC/AUC'
created: '2026-09-21'
state: rough
authorship: operator-drafted
semantic_review: unreviewed
material_analysis:
  resolution: resolved
  material: mathematics/probability-statistics/sad-ss26-lectures/lecture-slides/11_datascience_intro.pdf
  recorded_source_digest: b7decfedf4ce4eb66c0a564027f94ac668dbcf396e04461989773eb45d987302
  inspected_range:
    start: 33
    end: 38
  frozen_input_sha256: 8c64cb9e3b8c0c8a9cbaaf1d1a6041988446bfa8b88d8a6cb3aad8f34b803a4d
  frozen_input_bytes: 1228
  source_id: source-sad-ss26-lectures
  live_source_digest: b7decfedf4ce4eb66c0a564027f94ac668dbcf396e04461989773eb45d987302
  model: muse-spark 2026-09
  built: '2026-09-20'
---

<!-- GENERATED file - do not edit; promoted by tools/material_summarize.py --promote -->

# L11 pp. 33–38 — Evaluation: confusion matrix, precision/recall/F, ROC/AUC

Metric split (p. 33): MSE is natural for regression (hard to
interpret); cross-entropy punishes far-but-correct decisions, so
classification evaluation counts correctness only — starting with
accuracy, fraction correct. Confusion matrix (pp. 33–34): TP/FN/FP/TN
over model × gold standard; accuracy = (TP+TN)/all. Class imbalance
(p. 34): rare positives make huge TN irrelevant — precision =
TP/(TP+FP), recall = TP/(TP+FN), F-score = harmonic mean, F1 =
2PR/(P+R), general Fβ weights recall by β. Illustration (p. 35):
figure-only retrieved/relevant Venn panels. Why F (p. 36): trivial
models reach P=1 or R=1 alone, and plain averaging floors at 0.5
without using [0,1]; β=1 equal weight, higher β favors recall.
ROC/AUC (pp. 37–38): scored classifiers trade P/R via threshold t
(assumes score tracks class); worked score table shows P=5/8,R=5/6
vs P=3/4,R=3/6 at two thresholds; ROC traces P/R over t, AUC is area
under curve — higher F1 wins at one threshold t (itself learned),
higher AUC is generally better but not at every threshold.
