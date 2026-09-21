---
id: note-11-datascience-intro-pp012-020
type: note
role: reference
title: 'L11 pp. 12–20 — Machine learning: definition, classes, AI separation'
created: '2026-09-21'
state: rough
authorship: operator-drafted
semantic_review: unreviewed
material_analysis:
  resolution: resolved
  material: mathematics/probability-statistics/sad-ss26-lectures/lecture-slides/11_datascience_intro.pdf
  recorded_source_digest: b7decfedf4ce4eb66c0a564027f94ac668dbcf396e04461989773eb45d987302
  inspected_range:
    start: 12
    end: 20
  frozen_input_sha256: 0f62c6bbff198d3fd207dd8d944748da5ea6f8b8c20540544395ae974d54f407
  frozen_input_bytes: 1623
  source_id: source-sad-ss26-lectures
  live_source_digest: b7decfedf4ce4eb66c0a564027f94ac668dbcf396e04461989773eb45d987302
  model: muse-spark 2026-09
  built: '2026-09-20'
---

<!-- GENERATED file - do not edit; promoted by tools/material_summarize.py --promote -->

# L11 pp. 12–20 — Machine learning: definition, classes, AI separation

Definition (p. 12, Samuel 1959): learning without explicit
programming = algorithmically fitting parameters of f (usually by
optimization) so f works on training instances and, hopefully, unseen
ones; examples spam/ham over mail features, OCR over pixels. Recall
(p. 13): multivariate regression (numerical features → number, e.g.
rents) and Naïve Bayes (binary features → event probability) already
covered earlier in the course.

Classes (p. 14): supervised = raw instances plus annotation (ground
truth / gold standard, supervision signal), extrapolate to unseen;
unsupervised = raw data only, output is a partitioning (clustering)
where classes result from, rather than enter, learning. Worked
motivation (pp. 15–16): T-shirt sizes from customer heights/weights —
how many sizes, which cutoffs. Supervised split (p. 17):
classification (finite discrete labels: yes/no, cancer types, news
categories) vs regression (numbers: prices, volumes, times); rent
table example. Variations (p. 18): multi-label, semi-supervised,
graph-based, sequential, reinforcement, active, transfer (no IID),
autoregressive (LLMs). interplay (p. 19): clustering defines classes
for later classification and probes classifiability — no clusters,
no classifier. AI vs ML (p. 20): AI spans logic/reasoning, heuristic
search, uncertainty calculi, knowledge representation, robotics,
planning, data mining; ML (regression/classification/prediction) is
one branch of it.
