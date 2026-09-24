Garden seeds in knowledge/garden/. Key = file name. Plain Markdown with
optional inline #tags; no schema.

=== why-did-swapping-from-order-matter.md
date: 2026-04-21
---
# why did the query get faster when I swapped the tables?

DB tutorial: `SELECT … FROM big, small WHERE …` vs `FROM small, big` — the
tutor said the database should not care about the order in FROM, but my
timings on the old MySQL VM differed by 4×. Does the database reorder joins
itself? Based on what? #databases #question

=== independence-assumptions-that-still-work.md
date: 2026-05-08
---
Naive Bayes assumes something that is plainly false and still classifies well.
What else is built on a false-but-useful simplification? #ml #epistemology

=== kernel-is-an-overloaded-word.md
date: 2026-07-14
---
"kernel" so far this semester:
- OS kernel (the privileged core of the operating system)
- SVM kernel (inner product in a feature space)
- convolution kernel (the small weight matrix in a CNN)
- KDE kernel (the bump you put on each data point)
- the Jupyter kernel, lol

Are any two of these secretly the same idea? KDE and SVM maybe? #words #ml

=== fairness-for-my-study-time.md
date: 2026-07-26
---
What if I scheduled study like CFS — every subject has a "virtual study time"
that grows while I work on it, and I always pick the subject with the smallest
one, weighted by exam importance? Probably over-engineering a calendar.
#planning #os

=== ledgerline-receipt-idea.md
date: 2026-07-28
---
Notes app idea: never overwrite a note. Every save appends a small record —
what changed, the hash before and after, why. Then "what did I believe in
April?" is just replaying records up to April. Would be the opposite of every
notes app I have used. #ledgerline #idea

=== logs-are-the-real-database.md
date: 2026-08-01
---
Kleppmann line that stuck: the log is the truth and the tables are just a cache
of the latest values in it. If that's right, then a database's recovery log, an
event-sourced app, and git are all the same shape. #databases #ledgerline

=== everything-is-a-dag.md
date: 2026-08-07
---
git history, make/Bazel builds, Airflow pipelines, query plans, neural-network
computation graphs … all DAGs. Is there one algorithm I keep relearning?
(topological sort, at least) #cs #pattern

=== temperature-everywhere.md
date: 2026-08-12
---
softmax temperature: exp(z/T). annealing acceptance: exp(−Δ/T). both called
temperature, both exponentials divided by T. coincidence or the same physics?
#ml #physics

=== attention-as-soft-lookup.md
date: 2026-08-23
---
Attention: compare a query against all keys, turn the scores into weights with
a softmax, return the weighted sum of the values. A dictionary lookup where
every key matches a little. Is a KV cache then literally a cache of this
dictionary? #ml #databases
