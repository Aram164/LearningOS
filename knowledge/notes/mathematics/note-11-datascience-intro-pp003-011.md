---
id: note-11-datascience-intro-pp003-011
type: note
role: reference
title: L11 pp. 3–11 — What data science is, pipeline, data types
created: '2026-09-21'
state: rough
authorship: operator-drafted
semantic_review: unreviewed
material_analysis:
  resolution: resolved
  material: mathematics/probability-statistics/sad-ss26-lectures/lecture-slides/11_datascience_intro.pdf
  recorded_source_digest: b7decfedf4ce4eb66c0a564027f94ac668dbcf396e04461989773eb45d987302
  inspected_range:
    start: 3
    end: 11
  frozen_input_sha256: 86c010f0fc2e873f872e9a8ecef01b5efc576135996539637460744637f22a23
  frozen_input_bytes: 1652
  source_id: source-sad-ss26-lectures
  live_source_digest: b7decfedf4ce4eb66c0a564027f94ac668dbcf396e04461989773eb45d987302
  model: muse-spark 2026-09
  built: '2026-09-20'
---

<!-- GENERATED file - do not edit; promoted by tools/material_summarize.py --promote -->

# L11 pp. 3–11 — What data science is, pipeline, data types

Positioning (p. 3): statistics is mathematical with applications; data
science is the practical discipline (term public since ~2010, "fourth
paradigm", "data is the new oil/soil"). Practitioners spend ~90% of time
on data wrangling; this lecture covers only the ML aspect. Roots map
(p. 4): statistics, ML, deep learning, big data, data mining, search,
semantic web, data integration/engineering feed into data science.
Course map (p. 5): three blocks — DS/ML/AI concepts, supervised ML,
trade-offs.

Definition (pp. 6–7): NYU gloss — automated methods to analyze massive
data and extract knowledge; needs programming/repeatability, databases
(scalability), ML (needle in haystack), and domain context. Pipeline
(p. 8, del Valle): acquisition (DBs, APIs, scraping, Kaggle, flat
files) → cleaning/normalization/imputation/outliers/featurization →
descriptive stats, exploration, hypotheses, ML, validation →
insights, storytelling, visualization, action. Effort split (p. 9):
figure-only Crowdflower 2016 time-use chart.

Data types (p. 10): structured tables (rows = samples, columns =
features, first normal form, numerical-or-numericable), unstructured
(text/images/graphs → vectorize first), sequential
(time series/text/logs/DNA); representation learning converges them.
Real datasets (p. 11): distributed (federation), big (scalability),
fast/changing (streaming, incremental), heterogeneous (integration),
dirty (cleaning), multivariate — though many scores stay univariate.
