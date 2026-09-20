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
