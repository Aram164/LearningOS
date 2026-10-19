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
