---
id: note-11-datascience-intro-pp021-032
type: note
role: reference
title: 'L11 pp. 21–32 — Supervised setup: splits, features, functions, loss, learning'
created: '2026-09-21'
state: rough
authorship: operator-drafted
semantic_review: unreviewed
material_analysis:
  resolution: resolved
  material: mathematics/probability-statistics/sad-ss26-lectures/lecture-slides/11_datascience_intro.pdf
  recorded_source_digest: b7decfedf4ce4eb66c0a564027f94ac668dbcf396e04461989773eb45d987302
  inspected_range:
    start: 21
    end: 32
  frozen_input_sha256: a40cf7d4d3a0a9e1bbe205cb372ffba4f5e70e7ef99fe3fb4b9cd6a07c5e8e67
  frozen_input_bytes: 2389
  source_id: source-sad-ss26-lectures
  live_source_digest: b7decfedf4ce4eb66c0a564027f94ac668dbcf396e04461989773eb45d987302
  model: muse-spark 2026-09
  built: '2026-09-20'
---

<!-- GENERATED file - do not edit; promoted by tools/material_summarize.py --promote -->

# L11 pp. 21–32 — Supervised setup: splits, features, functions, loss, learning

Block map (p. 21) then formal setup (p. 22): datasets
D1 = {(xi, yi)} (train, n samples), D2 (test, m samples),
k-dimensional features xi, target yi, loss L; learn f's parameters
on D1 alone to minimize total loss on D2. D1/D2 are the gold
standard; yi in {1..k} = classification, yi real = regression.
Open questions (p. 23, Kelleher): datasets, features, function
classes, losses, learning rule.

Splits (pp. 24–26): S = all real instances (unknown); D1/D2 must be
representative or bias follows; D1 trains, D2 stands in for S\D1.
Practice: split one labeled set (record splits for reproducibility),
never touch D2 during training (leakage → overfitting); deep learning
adds a validation split (train/validation/test). ML is ill-posed
(p. 26): S unknown, so no optimal solution exists — heuristic by
nature, many equally good models on D1/D2, generalization undecided;
evaluation is the only window onto S, under explicit sampling
assumptions.

Features (p. 27): quality decides performance; filter/transform given
features (normalize, combine, impute, embed, select; representation
learning); expect numerical totally ordered inputs (ordinal → ints,
nominal → binary); correlated features are redundant — trees cope,
Naïve Bayes does not. Functions (p. 28): regression = linear combos,
symbolic = polynomials/logs/exponentials, Naïve Bayes = log-linear,
trees = piecewise linear (split points), nets = universal (zillions
of weights); hyperparameters (depth, width, tree count) are not
learned by training — tune on validation (grid/random/Bayesian);
model = function class + parameters + hyperparameters + loss. Loss
(p. 29): regression MSE; classification cross-entropy over
thresholded class probabilities, binary and multi-class forms;
link farm (p. 30). Learning (p. 31): minimize loss over D1 (train
loss, since D2 is off-limits); under IID + large D1 this hopefully
transfers to D2/S — no guarantees, so evaluate without
retraining; training algorithms usually gradient descent. Course
approaches (p. 32): information-based (trees, forests, boosting),
similarity-based (k-NN), probability-based (Bayes family), error-based
(logistic/multinomial regression, ANNs); one formulation each.
