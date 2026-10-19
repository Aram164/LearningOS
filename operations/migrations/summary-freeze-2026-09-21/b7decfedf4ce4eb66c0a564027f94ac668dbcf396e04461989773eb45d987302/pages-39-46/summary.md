<!-- GENERATED file - do not edit; promoted by tools/material_summarize.py --promote -->

# L11 pp. 39–46 — Trade-offs: inductive bias, overfitting, CV, bootstrap

Block map (p. 39) then inductive bias (pp. 40–41): induction from
examples needs assumptions — restriction bias (which function set)
plus preference bias (which of equally good functions); MLR =
linear + L2, trees = sequential splits + shallower; no learning
without it, it sets generalization ability (p. 41 figure-only).
Over/underfitting (p. 42): good-on-D1 need not hold on D2/S;
underfit = bad on both (wrong function class/features, too few
parameters, too little data — try other algorithms, features, more
data, clustering check); overfit = much worse on D2 than D1 (too
many parameters, noisy features, D1/D2 bias — select features, more
data, simpler model, regularization). Bias–variance (p. 43):
complexity (parameter count) cuts training error but hurts
unseen-data generalization via noise-fitting sensitivity.

Cross-validation (pp. 44–45): k folds, train k−1, evaluate k'th,
report mean/variance; high variance signals overfitting; final
check on held-out test; with hyperparameters use k−2/k−1/k'th
(training/tuning/eval) then retrain on all. Larger k = more train
data, lower variance, slower and hungrier (leave-one-out extreme);
typical k = 3, 5, 10. Bootstrap (p. 46): resample n' of n with
replacement, evaluate on the rest, repeat ~10,000× for a normal
score distribution (LLN) with robust confidence intervals;
compute-heavy.
