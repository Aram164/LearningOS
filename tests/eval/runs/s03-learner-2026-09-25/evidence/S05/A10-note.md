---
id: note-query-optimizer-cost-model
type: note
title: Cost models and selectivity
created: 2026-05-23
role: synthesis
state: evolving
authorship: user
concepts:
- concept-cardinality-estimation
- concept-query-optimization
sources:
- source-tuh-dbsys-slides
- source-selinger-1979
---

The optimizer needs the number of rows each operator produces to cost a plan.

Selectivity of a predicate = fraction of rows that pass it. With a histogram
on column a, sel(a = v) ≈ (rows in v's bucket / bucket width) / total rows.

For a conjunction the textbook rule is

    sel(p₁ ∧ p₂) = sel(p₁) · sel(p₂)

i.e. the optimizer behaves as if the two columns had nothing to do with each
other. For city = 'Havelberg' AND zip = '14712' this is badly wrong: the zip
code already determines the city, so the true selectivity is sel(zip), and the
product underestimates it by a factor of 1/sel(city).

Underestimates compound through joins; a plan that looks cheap for "10 rows"
is catastrophic for 100,000. Lecture: "estimation errors grow exponentially
with the number of joins".

Fixes mentioned: multi-column statistics, sampling, adaptive re-optimization.

## Guest lecture on database internals (friend's notes, 2026-09-23)

*Transcribed from a photo of a friend's lecture notes; filed here by the
operator, wording unchanged.*

Cardinality estimation — guest lecture

Estimated rows for WHERE make = 'Honda' AND model = 'Civic':
    sel(make) = 0.08, sel(model) = 0.01 → est. 0.08 · 0.01 · 10⁶ = 800 rows
    actual: 10,000 rows (every Civic is a Honda)

"The optimizer factorizes the joint selectivity as if the columns were
unrelated. It is the most common source of bad plans." Remedy: extended
statistics on (make, model), or sampling.
