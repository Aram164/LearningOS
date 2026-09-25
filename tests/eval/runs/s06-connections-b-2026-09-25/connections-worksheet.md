# Connection worksheet (judge)

Grade each returned relevant target: explanation 0 (wrong/absent) · 1 (partly) · 2 (correct), provenance 0/1. Oracle mentions are guidance, not wording.

## C01 — note-naive-bayes-spam-filter

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | stage:stage-l05-01-derive-naive-bayes | MUST_CONNECT | Her own no-slides derivation of the same classifier, including the Laplace estimate (count+1)/(N+2); the formal version of this note. | the stage derivation of the same classifier |  |  |
| 2 | note-generative-vs-discriminative | MUST_CONNECT | Places Naive Bayes as the generative model against logistic regression (Ng & Jordan); explains why NB wins with little data. | NB is the generative model compared with logistic regression |  |  |
| 3 | garden:independence-assumptions-that-still-work.md | USEFUL_CONNECT | Garden seed asking exactly this note's puzzle: NB assumes something plainly false and still classifies well. | the garden seed asks why NB works despite a false assumption |  |  |
| 4 | note-independence-vs-conditional-independence | MUST_CONNECT | The NB assumption is conditional independence of words given the class; this note separates it from plain independence. | the naive assumption is conditional independence of the words/features given the class; it is what lets p(x/y) factor into a product | 2 |  |
| 5 | stage:stage-l05-02-generative-vs-discriminative | UNJUDGED | Active stage running NB vs logistic regression on the same bag-of-words features (NB ahead at n=50, 200). |  |  |  |
| 6 | note-mle-coin-flips | UNJUDGED | The k=0 overconfidence problem of the MLE is the same zero-count problem Laplace smoothing fixes ("Havelberg" always ham). |  |  |  |
| 7 | note-query-optimizer-cost-model | USEFUL_CONNECT | The same "treat features as unrelated" assumption in selectivity estimation, where it fails badly because errors compound; the counterpart to "only the ranking matters". | both multiply per-feature/per-predicate probabilities as if independent; both break when features/columns are correlated | 2 | 1 |
| 8 | note-statlearn-mock-exam-september | USEFUL_CONNECT | Mock exam Q2 is an NB spam classification that asks for the assumption and why it is violated. |  |  | 0 |
| 9 | note-map-estimation-priors | UNJUDGED | Add-one smoothing can be read as a prior on the word probabilities (MAP view); the MAP note shows how a prior becomes an extra term. |  |  |  |
| 10 | note-conditional-probability-basics | USEFUL_CONNECT | Bayes rule and prior/likelihood/posterior vocabulary the NB derivation starts from. | Bayes' rule is the starting point of the NB posterior |  |  |

## C02 — note-map-estimation-priors

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | note-ridge-regression-penalty | MUST_CONNECT | A Gaussian prior on the weights turns MAP into ridge; answers the ridge note's open question of where λ comes from (λ = σ²/τ²). | a Gaussian prior on the weights gives a squared (L2) penalty; ridge = MAP with Gaussian prior; lambda corresponds to sigma²/tau² (prior strength) | 2 |  |
| 2 | note-gaussian-noise-least-squares | USEFUL_CONNECT | Supplies the likelihood term the MAP note plugs in (Gaussian noise → squared error). | the likelihood term is the squared error from the Gaussian-noise model |  |  |
| 3 | note-mle-coin-flips | USEFUL_CONNECT | MAP = MLE + log-prior; the coin note flags the k=0 overconfidence that "the lecture fixes later with priors". | MAP adds a log-prior to the MLE objective; fixes the k=0 overconfidence the coin note complains about | 2 |  |
| 4 | note-lasso-sparsity-geometry | USEFUL_CONNECT | The Laplace prior at the end of the MAP note gives the L1 penalty, i.e. the lasso. | a Laplace prior gives the L1 (lasso) penalty |  |  |
| 5 | stage:stage-l07-01-ridge-lasso-geometry | USEFUL_CONNECT | Active ridge/lasso stage; the MAP view is the missing "where does the penalty come from" angle. |  |  |  |
| 6 | note-conditional-probability-basics | USEFUL_CONNECT | Prior, likelihood, posterior and evidence defined; the evidence dropping out is the first step of MAP. |  |  |  |
| 7 | note-bias-variance-from-book | USEFUL_CONNECT | Shrinking an estimate towards zero trades bias for variance, which is what a prior centred at zero does. | shrinkage adds bias but can reduce variance |  |  |
| 8 | note-generative-vs-discriminative | UNJUDGED | Guesses that the generative model's extra assumptions "act like a prior". |  |  |  |
| 9 | note-naive-bayes-spam-filter | UNJUDGED | Laplace (add-one) smoothing as a prior on counts. |  |  |  |
| 10 | note-p-values-corrected | UNJUDGED | Frequentist counterpoint: a p-value never uses a prior on H0. |  |  |  |

## C03 — note-parallel-workers-no-speedup

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | note-amdahls-law | MUST_CONNECT | Exactly this situation: half the job is serial CSV parsing, so the speed-up is capped at about 2×. | the single-process CSV parse is the sequential fraction; speedup is bounded by 1/(1−p); with half the job sequential, at most 2× | 2 |  |
| 2 | note-data-parallel-training-scaling | USEFUL_CONNECT | Same pattern in GPU training: the part that does not shrink (all-reduce, a shared disk) dominates at 8 GPUs. | the non-shrinking part (all-reduce, data loading) limits speedup the same way | 2 |  |
| 3 | workspace-dataframe-skill | USEFUL_CONNECT | The workspace this experiment belongs to. |  |  |  |
| 4 | note-columnar-storage-compression | USEFUL_CONNECT | The fix was switching to 32 Parquet files; this note explains what Parquet/columnar storage buys. |  |  |  |
| 5 | note-kafka-consumer-lag-backpressure | UNJUDGED | Parallelism capped by the partition count, the same shape as "one CSV cannot be split". |  |  |  |
| 6 | note-lazy-evaluation-query-plans | UNJUDGED | Same workspace; the lazy CSV benchmark shows where scan time goes. |  |  |  |

## C04 — note-cfs-fair-share

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | stage:stage-os-l02-02-proportional-share | MUST_CONNECT | The active stage for this topic; the stride example stopped at step 4 and is the next action. | the half-finished stride example |  |  |
| 2 | note-os-scheduling-exercise-bank | MUST_CONNECT | Exercises 3–5 drill lottery, stride and CFS nice values. |  |  |  |
| 3 | note-cpu-scheduling-round-robin | MUST_CONNECT | The MLFQ/round-robin baseline this note contrasts itself with. |  |  |  |
| 4 | note-dominant-resource-fairness-paper | USEFUL_CONNECT | Fair share generalised to several resources (dominant share). | DRF generalizes fair share to several resources |  |  |
| 5 | note-multi-tenant-gpu-sharing | USEFUL_CONNECT | Weighted shares on a GPU cluster: "strict priorities starved the batch jobs; weights fixed it". | weighted shares per team is proportional-share scheduling; unused share is lent out and reclaimed; strict priority starved batch jobs | 1 |  |
| 6 | garden:fairness-for-my-study-time.md | AMBIGUOUS | Seed applying CFS/virtual runtime to her own study time. |  |  |  |
| 7 | note-study-plan-retake-strategy | MUST_NOT_CONNECT | A fixed weekly share with catch-up, i.e. proportional share applied to the two exams. |  | 1 |  |
| 8 | workspace-os-oral-prep | UNJUDGED | Oral-exam workspace; its next action is this stage. |  |  |  |
| 9 | inbox:20260915-os-oral-questions.md | USEFUL_CONNECT | Oral question "explain how the scheduler on your laptop decides what runs next" is answered by CFS. |  |  |  |
| 10 | note-context-switch-cost | USEFUL_CONNECT | Why CFS has a minimum granularity: switching has a cost. |  |  |  |

## C05 — note-write-ahead-logging-aries

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | note-journaling-filesystems | MUST_CONNECT | The same write-ahead idea in file systems: journal, commit block, replay after a crash. | the journal/log record must be durable before the in-place write; after a crash, committed records are replayed/redone and uncommitted ignored | 2 |  |
| 2 | note-db-exam-cheatsheet | USEFUL_CONNECT | ARIES in one line (analysis → redo → undo with CLRs); records that the recovery question was hard. |  |  |  |
| 3 | note-buffer-pool-replacement | UNJUDGED | Steal/no-force are buffer-pool policies: evicting a dirty page before commit is why undo is needed. |  |  |  |
| 4 | note-acid-consistency | USEFUL_CONNECT | WAL is the machinery behind A and D. | WAL provides atomicity and durability | 2 |  |
| 5 | garden:logs-are-the-real-database.md | MUST_CONNECT | Seed saying a recovery log, event sourcing and git share one shape. |  |  |  |
| 6 | note-event-sourcing-append-only | USEFUL_CONNECT | The log treated as the source of truth, with state as a fold over it. | an append-only log from which state is rebuilt by replay | 2 |  |
| 7 | note-two-phase-locking-deadlocks | USEFUL_CONNECT | The isolation half of transaction machinery, next to the recovery half. |  |  | 0 |
| 8 | note-lsm-trees | USEFUL_CONNECT | LSM trees also write a log for durability before the memtable. |  |  | 1 |
| 9 | workspace-dbsys-exam | AMBIGUOUS | Archived DB exam workspace that lists this note. |  |  |  |

## C06 — note-selinger-join-ordering

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | note-query-optimizer-cost-model | MUST_CONNECT | The cost/selectivity model that the Selinger search depends on; the same 1979 source. | the cost model/cardinality estimates rank the candidate plans | 2 |  |
| 2 | garden:why-did-swapping-from-order-matter.md | MUST_CONNECT | Her open question "does the database reorder joins itself? based on what?" is answered by this note. | the April question 'does the database reorder joins?' is answered by cost-based join ordering |  |  |
| 3 | note-dynamic-programming-memoization | MUST_CONNECT | Selinger is dynamic programming over table subsets: optimal substructure, keep the best plan per subset. | System R join enumeration is dynamic programming; best plan per subset = optimal substructure; subsets reused = overlapping subproblems | 2 | 0 |
| 4 | note-hash-join-vs-sort-merge | USEFUL_CONNECT | Join algorithms being costed; sort-merge output order is why "interesting orders" exist. | interesting orders serve merge joins |  |  |
| 5 | note-algebraic-equivalences-pushdown | USEFUL_CONNECT | Commutativity/associativity of joins make reordering legal; the lecture heuristic is "then worry about join order". |  |  |  |
| 6 | project-tessera | USEFUL_CONNECT | Her engine plans cost-based join ordering after the rule-based rewrites (decision-tessera-rules-before-cost). |  |  |  |
| 7 | note-db-exam-cheatsheet | UNJUDGED | Exam summary for the optimizer topics. |  |  |  |
| 8 | note-hmm-viterbi | USEFUL_CONNECT | Same principle as Viterbi: the best path to a state consists of best sub-paths. | both keep only the best partial solution per state/subset | 2 |  |
| 9 | note-lazy-evaluation-query-plans | USEFUL_CONNECT | A production optimizer she is studying in the dataframe skill. |  |  |  |

## C07 — note-query-optimizer-cost-model

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | note-selinger-join-ordering | MUST_CONNECT | The search that consumes these cardinality estimates; errors compound across the joins it enumerates. |  |  |  |
| 2 | note-independence-vs-conditional-independence | USEFUL_CONNECT | The product rule sel(p1∧p2)=sel(p1)·sel(p2) is an independence assumption; this note is about when independence holds. | P(A,B)=P(A)P(B) only under independence; correlated columns violate it | 1 |  |
| 3 | note-naive-bayes-spam-filter | USEFUL_CONNECT | The same false independence assumption, harmless there (only the ranking matters) and catastrophic here (magnitudes compound). | the product-of-selectivities rule is the same independence assumption Naive Bayes makes | 2 |  |
| 4 | garden:independence-assumptions-that-still-work.md | USEFUL_CONNECT | Seed asking what else rests on a false-but-useful simplification; this note is a case where it stops working. |  |  |  |
| 5 | note-algebraic-equivalences-pushdown | USEFUL_CONNECT | The rewrite side of the optimizer, next to the costing side. |  |  |  |
| 6 | note-db-normalization-3nf | UNJUDGED | zip → city is a functional dependency; FDs are exactly what makes column predicates correlated. |  |  |  |
| 7 | garden:why-did-swapping-from-order-matter.md | UNJUDGED | Plan choice depends on these estimates, which is why her MySQL timings differed by 4x. |  |  |  |
| 8 | note-db-exam-cheatsheet | UNJUDGED | Exam summary for optimizer topics. |  |  |  |
| 9 | note-columnar-storage-compression | UNJUDGED | Parquet per-chunk min/max statistics are a lightweight form of column statistics. |  |  |  |

## C08 — note-low-rank-approximation

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | note-matrix-factorization-recommenders | MUST_CONNECT | Answers the note's open question: fit P·Qᵀ only over observed ratings, so the missing entries are never needed. | answers the open question about recommenders; fit P Qᵀ only on observed ratings, so missing entries are never needed |  |  |
| 2 | note-svd-geometric | MUST_CONNECT | The SVD this note truncates. |  |  |  |
| 3 | stage:stage-linalg-svd-02-low-rank | MUST_CONNECT | Paused stage with the rank-5 result (relative error 0.31); ranks 20 and 50 still to do. | rank 5 done, 20/50 not | 2 |  |
| 4 | workspace-linalg-refresh | USEFUL_CONNECT | Workspace whose next action is this experiment. |  |  |  |
| 5 | stage:stage-l09-02-svd-connection | USEFUL_CONNECT | PCA ↔ SVD stage, paused on σ_i² and explained variance, which is the same Σσ² bookkeeping as Eckart–Young. |  |  |  |
| 6 | note-pca-by-hand | USEFUL_CONNECT | PCA keeps the top directions, i.e. a low-rank projection of the data. | PCA keeps the top components — a truncated SVD | 2 |  |
| 7 | note-eigenvectors-intuition | USEFUL_CONNECT | Eigendecomposition, which the SVD generalises. |  |  |  |
| 8 | note-covariance-matrix | USEFUL_CONNECT | Same Strang source; eigenvectors of the covariance matrix, which links to PCA. |  |  |  |

## C09 — note-data-lineage-debugging

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | note-why-provenance-paper | MUST_CONNECT | Why-provenance is exactly "which input rows produced this output row", the tool the note wishes it had. | 'which input rows produced this output row' is why-provenance; a join output's witness has one tuple per side — fan-out duplicates | 1 |  |
| 2 | stage:stage-df-lineage-01-trace | UNJUDGED | Pending stage "Trace a wrong number" in the lineage unit, the same exercise. |  |  |  |
| 3 | workspace-dataframe-skill | USEFUL_CONNECT | The workspace this debugging belongs to. |  |  |  |
| 4 | note-relational-algebra-operators | UNJUDGED | Set vs bag semantics: SQL keeps duplicates unless DISTINCT, the root of the double count. |  |  |  |
| 5 | note-idempotent-pipelines-backfills | AMBIGUOUS | Another way a pipeline silently doubles a number (append on retry). |  |  |  |
| 6 | note-data-pipeline-orchestration-dag | USEFUL_CONNECT | Pipelines as DAGs; walking upstream step by step is walking this DAG backwards. |  |  | 1 |
| 7 | note-lazy-evaluation-query-plans | UNJUDGED | Same workspace; plan inspection as another debugging lens. |  |  |  |
| 8 | note-event-sourcing-append-only | AMBIGUOUS | Keeping history to answer "how did we get here?". |  |  |  |

## C10 — note-kv-cache-transformer-serving

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | garden:attention-as-soft-lookup.md | MUST_CONNECT | Seed asking whether the KV cache is literally a cache of attention's key/value dictionary. |  |  |  |
| 2 | note-dynamic-batching-inference | MUST_CONNECT | KV memory limits how many requests fit in a batch; the batching trade-off. | KV memory limits how many requests fit in a batch |  |  |
| 3 | note-virtual-memory-address-translation | USEFUL_CONNECT | The fragmentation problem (reserve max vs gaps) is the one paging solves for process memory. | the reserve-vs-grow fragmentation problem is what paging solves in an OS |  |  |
| 4 | note-multi-tenant-gpu-sharing | USEFUL_CONNECT | GPU memory as a shared resource between serving teams. |  |  |  |
| 5 | note-mixed-precision-training | USEFUL_CONNECT | fp16/bf16 bytes per value, a factor in the KV size formula. |  |  | 1 |
| 6 | note-caching-everywhere | AMBIGUOUS | Her cross-course "keep a fast copy of something expensive" pattern. |  |  |  |
| 7 | note-softmax-temperature | UNJUDGED | Softmax inside attention and temperature in LLM sampling. |  |  |  |

## C11 — note-os-kernel-user-mode

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | note-context-switch-cost | MUST_CONNECT | Mode and address-space switches, cache and TLB pollution: the costs this note names. | mode switches and cache/TLB pollution make kernel entry expensive |  |  |
| 2 | note-virtual-memory-address-translation | USEFUL_CONNECT | Page tables are what only kernel mode may change; the TLB and page faults (traps). | page tables are changed only in kernel mode; page faults trap into the kernel |  |  |
| 3 | inbox:20260915-os-oral-questions.md | USEFUL_CONNECT | Oral questions on page faults, the TLB and context switches build on the kernel/user boundary. |  |  |  |
| 4 | garden:kernel-is-an-overloaded-word.md | USEFUL_CONNECT | Seed separating the OS kernel from the SVM, CNN and KDE kernels. | as a disambiguation, not an equivalence | 2 |  |
| 5 | workspace-os-oral-prep | UNJUDGED | OS oral prep; the chair follows up on "why is read() expensive"-type questions. |  |  |  |
| 6 | note-cpu-cache-locality | UNJUDGED | Cache pollution after a system call. |  |  |  |
| 7 | note-oral-exam-prep-strategy | UNJUDGED | "Only mention things you can explain one level deeper." |  |  |  |

## C12 — note-db-normalization-3nf

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | note-db-exam-cheatsheet | MUST_CONNECT | Has the BCNF test in exam form. |  |  |  |
| 2 | note-relational-algebra-operators | USEFUL_CONNECT | Decomposition and natural join, which lossless-join is defined in terms of. | decomposition uses projection; lossless-join uses natural join |  |  |
| 3 | note-query-optimizer-cost-model | UNJUDGED | zip → city is an FD; FDs make predicates correlated and break the independence estimate. |  |  |  |
| 4 | note-acid-consistency | USEFUL_CONNECT | Integrity constraints: the database enforces the declared ones (keys), which normalization relies on. |  |  |  |
| 5 | workspace-dbsys-exam | UNJUDGED | Archived DB exam workspace. |  |  |  |
| 6 | note-data-lineage-debugging | UNJUDGED | One user → many devices joined in and duplicated rows: a redundancy/anomaly example from practice. |  |  |  |

## C13 — note-acid-consistency

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | note-cap-consistency-linearizability | MUST_CONNECT | "The C in CAP is not the C in ACID"; the direct companion. | CAP consistency (linearizability) is a different property from ACID consistency (invariants) | 2 |  |
| 2 | note-write-ahead-logging-aries | USEFUL_CONNECT | The machinery behind A and D. |  |  |  |
| 3 | note-two-phase-locking-deadlocks | USEFUL_CONNECT | The machinery behind I (serializability). |  |  |  |
| 4 | note-journaling-filesystems | AMBIGUOUS | Atomic, durable multi-structure updates outside databases. |  |  |  |
| 5 | note-db-normalization-3nf | USEFUL_CONNECT | Declared constraints (keys, FDs) are what the database can enforce for C. |  |  |  |
| 6 | note-idempotency-keys-api | AMBIGUOUS | "Store the key in the same transaction as the effect": atomicity used in an API. |  |  |  |
| 7 | note-consistent-estimators | MUST_NOT_CONNECT | The same word in statistics with an unrelated meaning. |  | 2 |  |

## C14 — note-spaced-repetition-scheduler

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | inbox:20260916-sleep-podcast.md | USEFUL_CONNECT | Sleep and memory consolidation, the same retention question. |  |  |  |
| 2 | note-study-plan-retake-strategy | USEFUL_CONNECT | Scheduling study time across two exams. |  |  |  |
| 3 | note-pomodoro-and-context-switching | USEFUL_CONNECT | Another self-experiment on study technique. |  |  |  |
| 4 | note-how-i-take-notes | USEFUL_CONNECT | Her rules for writing in her own words, parallel to "write cards myself". |  |  |  |
| 5 | note-semester-review-july | UNJUDGED | "Exercise sheets every week, not in exam week", the same don't-let-the-backlog-grow lesson. |  |  |  |
| 6 | garden:fairness-for-my-study-time.md | UNJUDGED | Another scheduler applied to studying. |  |  |  |
| 7 | note-oral-exam-prep-strategy | UNJUDGED | Active recall by practising out loud. |  |  |  |

## C15 — note-buffer-pool-replacement

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | note-page-replacement-lru-clock | MUST_CONNECT | The OS version of the same eviction problem (LRU, clock, Belady). | the same eviction problem in the OS; LRU fails when a scan/loop is larger than memory (sequential flooding) | 1 |  |
| 2 | note-caching-everywhere | MUST_CONNECT | Her cross-course note naming the buffer pool, CPU caches and memoization as one idea. |  |  |  |
| 3 | note-write-ahead-logging-aries | UNJUDGED | Dirty-page write-back and the steal/no-force policies tie the buffer pool to recovery. |  |  |  |
| 4 | note-cpu-cache-locality | USEFUL_CONNECT | Hardware caching and locality, the third member of the caching note. |  |  |  |
| 5 | note-virtual-memory-address-translation | USEFUL_CONNECT | Pages and frames in the OS, and why databases bypass the OS page cache. |  |  |  |
| 6 | note-external-merge-sort | USEFUL_CONNECT | Uses B buffer pages; sequential access patterns. |  |  |  |
| 7 | note-b-plus-tree-indexes | USEFUL_CONNECT | "The top two levels are almost always cached." |  |  |  |

## C16 — note-p-values-corrected

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | note-p-values-first-take | MUST_CONNECT | Her April wrong version that this note corrects. | the April note is the wrong earlier belief that this note corrects |  |  |
| 2 | inbox:20260903-pvalue-reminder.md | MUST_CONNECT | She made the same mistake again in a mock on 2026-09-03; unresolved capture. | the misconception recurred in September | 2 |  |
| 3 | note-conditional-probability-basics | USEFUL_CONNECT | P(H0 / data) would need Bayes' rule; the disease-test trap is the same swap of conditionals. | confusing P(data/H0) with P(H0/data) is the swapped-conditional trap |  |  |
| 4 | workspace-statlearn-retake | UNJUDGED | The retake this matters for (exam 2026-10-06). |  |  |  |
| 5 | note-map-estimation-priors | UNJUDGED | The Bayesian counterpart that does use a prior. |  |  |  |
| 6 | note-central-limit-theorem-simulation | USEFUL_CONNECT | Sampling distributions behind test statistics. |  |  |  |

## C17 — note-gradient-descent-from-scratch

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | note-normal-distribution-standardizing | USEFUL_CONNECT | Standardization, the fix this note arrives at. | standardizing features fixed the divergence | 2 |  |
| 2 | note-linear-regression-normal-equation | MUST_CONNECT | The closed-form alternative for the same problem (normal-equation contrasts-with gradient-descent). | closed form vs iterative |  |  |
| 3 | note-sgd-momentum-nn-training | MUST_CONNECT | "The same update rule from the housing exercise", plus minibatches and momentum. | same update rule with a minibatch gradient and momentum |  |  |
| 4 | note-data-leakage-scaler | UNJUDGED | How to fit the scaler without leaking validation data. |  |  |  |
| 5 | note-convexity-basics | USEFUL_CONNECT | MSE is convex, so GD finds the global minimum; the thin valley is poor conditioning. | squared error is convex, so descent finds the global minimum |  |  |
| 6 | note-regression-metrics | USEFUL_CONNECT | Metrics for the same housing regression. |  |  | 1 |
| 7 | note-adam-vs-sgd-revisited | USEFUL_CONNECT | Learning-rate sensitivity and optimizer choice. |  |  |  |
| 8 | note-ridge-regression-penalty | UNJUDGED | Same linear-regression family with a penalty. |  |  |  |
| 9 | note-gaussian-noise-least-squares | UNJUDGED | Why the loss is MSE. |  |  |  |
| 10 | note-batchnorm-internal-covariate-shift | UNJUDGED | Normalising inputs inside a network, same motivation as feature scaling. |  |  |  |

## C18 — note-dynamic-batching-inference

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | note-kv-cache-transformer-serving | USEFUL_CONNECT | KV memory decides how many requests fit in a batch. |  |  |  |
| 2 | note-multi-tenant-gpu-sharing | MUST_CONNECT | Interactive vs batch traffic on shared GPUs. |  |  |  |
| 3 | note-queueing-littles-law | USEFUL_CONNECT | Queue length, waiting time and throughput: L = λW. | requests waiting in the queue relate arrival rate and waiting time (L = λW) |  |  |
| 4 | note-cpu-scheduling-round-robin | UNJUDGED | The same throughput vs response-time trade-off (quantum size). |  |  |  |
| 5 | note-kafka-consumer-lag-backpressure | USEFUL_CONNECT | What happens when arrivals outpace service. |  |  |  |
| 6 | note-data-parallel-training-scaling | UNJUDGED | Bigger batches help throughput until something else degrades. |  |  |  |
| 7 | note-semaphores-producer-consumer | UNJUDGED | Bounded buffer between a producer and a consumer. |  |  |  |

## C19 — note-softmax-temperature

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | garden:temperature-everywhere.md | MUST_CONNECT | Seed asking whether softmax temperature and annealing temperature are the same idea. |  |  | 1 |
| 2 | note-simulated-annealing | USEFUL_CONNECT | exp(−Δ/T) acceptance with a cooling schedule. | both are exp(−E/T) Boltzmann forms; T→0 becomes greedy/argmax | 1 |  |
| 3 | garden:attention-as-soft-lookup.md | UNJUDGED | Softmax turning attention scores into weights. |  |  |  |
| 4 | note-logistic-regression-cross-entropy | USEFUL_CONNECT | The sigmoid is the two-class softmax; cross-entropy is its loss. |  |  |  |
| 5 | note-kv-cache-transformer-serving | UNJUDGED | LLM inference, where temperature sampling happens. |  |  |  |
| 6 | note-naive-bayes-spam-filter | UNJUDGED | The same numerical trick: work in log space and avoid under/overflow. |  |  |  |

## C20 — note-constant-folding-cse

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | note-tagless-visitor-pattern-ast | MUST_CONNECT | Tessera's rules include constant folding (1 = 1 → true) and are applied to a fixed point with a 50-pass cap. | Tessera's rules fold constants and iterate to a fixed point with a pass cap |  |  |
| 2 | note-algebraic-equivalences-pushdown | USEFUL_CONNECT | Rewrite rules that keep the result identical but change the cost: the same contract for query plans. | both rewrite a tree with meaning-preserving equivalences | 2 |  |
| 3 | note-ssa-form | MUST_CONNECT | SSA makes constant propagation and CSE simple graph passes. |  |  |  |
| 4 | inbox:20260910-tessera-todo.md | USEFUL_CONNECT | "rules fighting each other → optimizer never terminates?" is the fixed-point question; constant folding is ticked. | rules fighting each other / termination |  |  |
| 5 | note-property-based-testing | USEFUL_CONNECT | execute(optimize(q)) == execute(q) checks the preserve-meaning contract. | execute(optimize(q)) == execute(q) checks meaning preservation |  |  |
| 6 | note-lazy-evaluation-query-plans | USEFUL_CONNECT | A dataframe optimizer doing common-subplan elimination and expression simplification. | common subplan elimination / expression simplification |  |  |
| 7 | note-compiler-pipeline-overview | MUST_CONNECT | Where the IR and the optimisation passes sit. |  |  | 0 |
| 8 | workspace-tessera-engine | USEFUL_CONNECT | The workspace implementing these rewrites. |  |  |  |
| 9 | note-regression-testing-snapshots | UNJUDGED | Snapshots of the optimized plan for 20 queries. |  |  |  |

## A01 — arrival:A01

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | note-naive-bayes-spam-filter | MUST_CONNECT | The "single class node with arrows to every feature" she half-recognises is Naive Bayes; her spam note is that network. | the class node with arrows to every feature is Naive Bayes; answers the '??? recognize this' line | 2 |  |
| 2 | note-independence-vs-conditional-independence | MUST_CONNECT | d-separation and explaining away are this note's two cases (dependent-but-independent-given-C; the XOR collider). | a node is independent of its non-descendants given its parents; explaining away appears in both | 1 |  |
| 3 | stage:stage-l05-01-derive-naive-bayes | UNJUDGED | Her derivation writes p(x/y) = Π p(x_j/y), which is the BN factorisation for that graph. |  |  |  |
| 4 | garden:independence-assumptions-that-still-work.md | USEFUL_CONNECT | A BN makes the independence assumptions explicit, which is the question this seed asks. |  |  |  |
| 5 | note-generative-vs-discriminative | USEFUL_CONNECT | BNs are generative models; NB and GDA are the examples there. |  |  |  |
| 6 | note-hmm-viterbi | USEFUL_CONNECT | An HMM is a chain-structured Bayesian network. | an HMM is a Bayesian network over a chain |  |  |
| 7 | note-conditional-probability-basics | USEFUL_CONNECT | Chain rule and Bayes rule behind the factorisation. |  |  |  |
| 8 | garden:everything-is-a-dag.md | AMBIGUOUS | One more DAG for her "everything is a DAG" collection. |  |  |  |
| 9 | workspace-statlearn-retake | UNJUDGED | She is reading this ahead of the retake. |  |  |  |

## A02 — arrival:A02

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | stage:stage-l07-01-ridge-lasso-geometry | MUST_CONNECT | Continues this stage and answers its open question ("is there a one-dimensional version I can solve by hand?"). | the stage asked for a 1-D version by hand |  |  |
| 2 | note-lasso-sparsity-geometry | MUST_CONNECT | The geometric (diamond-corner) explanation; this adds the algebraic one, soft thresholding. | algebraic (soft-thresholding) counterpart of the diamond-corner picture | 2 |  |
| 3 | note-ridge-regression-penalty | MUST_CONNECT | Answers its open question: why ridge has a closed form and the lasso needs special solvers. | answers why ridge has a closed form and lasso does not (piecewise/soft-thresholding) |  |  |
| 4 | note-map-estimation-priors | USEFUL_CONNECT | L1 = Laplace prior under MAP, the probabilistic reading of the same penalty. | Laplace prior |  |  |
| 5 | stage:stage-l07-02-choose-lambda | UNJUDGED | The next stage, choosing λ, the threshold in soft thresholding. |  |  |  |
| 6 | workspace-statlearn-retake | USEFUL_CONNECT | Retake workspace; L07 ridge/lasso is its next action. |  |  |  |
| 7 | note-statlearn-mock-exam-september | UNJUDGED | Mock Q3 derives the ridge estimator; this is the lasso counterpart. |  |  |  |
| 8 | note-convexity-basics | USEFUL_CONNECT | Convex but non-differentiable at 0, which is why the minimum sits at the kink. |  |  |  |

## A03 — arrival:A03

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | note-tagless-visitor-pattern-ast | MUST_CONNECT | The rule framework (transform_up, fixed point) this rule plugs into. |  |  |  |
| 2 | inbox:20260910-tessera-todo.md | MUST_CONNECT | This log ticks off two of those todos: filter-below-join and the property test. | two todo items are now done | 2 | 1 |
| 3 | note-algebraic-equivalences-pushdown | MUST_CONNECT | Rule 2 there, σ_p(R⋈S) = σ_p(R)⋈S when p mentions only R, is exactly this rule. | the implemented rule is σ_p(R ⋈ S) = σ_p(R) ⋈ S when p only uses R's attributes | 2 |  |
| 4 | note-property-based-testing | MUST_CONNECT | The execute(optimize(q)) == execute(q) property she just ran. |  |  |  |
| 5 | workspace-tessera-engine | MUST_CONNECT | Its next action was precisely this rule plus before/after tests. | it was the recorded next action |  | 0 |
| 6 | project-tessera | MUST_CONNECT | The project; the optimizer milestone is active. |  |  |  |
| 7 | note-lazy-evaluation-query-plans | MUST_CONNECT | Predicate pushdown as a production engine does it. | predicate pushdown in the lazy engine |  |  |
| 8 | stage:stage-df-lazy-02-read-explain | USEFUL_CONNECT | The explain() annotations show the same filter moving into the scan. |  |  |  |
| 9 | arrival:A14 | UNJUDGED | Same rule stated from the dataframe side ("a filter can move below an operator only if it depends on nothing that operator creates"). |  |  |  |
| 10 | note-regression-testing-snapshots | USEFUL_CONNECT | Her 20 plan snapshots will change with this rule. |  |  |  |

## A04 — arrival:A04

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | note-kv-cache-transformer-serving | MUST_CONNECT | The problem PagedAttention solves: more than half of KV memory wasted by reservation and gaps. | PagedAttention solves the reserve-vs-fragment waste that note describes |  |  |
| 2 | note-virtual-memory-address-translation | MUST_CONNECT | "Where have I seen block tables before": page tables mapping virtual pages to physical frames. | the block table is a page table; non-contiguous fixed-size blocks, on-demand allocation, copy-on-write sharing | 1 |  |
| 3 | arrival:A30 | UNJUDGED | Her question about what the server keeps in memory and why it grows. |  |  |  |
| 4 | note-dynamic-batching-inference | USEFUL_CONNECT | Less KV waste means more requests fit per batch. |  |  |  |
| 5 | garden:attention-as-soft-lookup.md | USEFUL_CONNECT | Seed asking what the KV cache really caches. |  |  |  |
| 6 | note-buffer-pool-replacement | UNJUDGED | Another page-id → frame table. |  |  |  |
| 7 | stage:stage-os-l05-01-translation | UNJUDGED | Upcoming address-translation stage, the same mechanism. |  |  |  |

## A05 — arrival:A05

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | note-data-lineage-debugging | MUST_CONNECT | "Second time a join fan-out has bitten me": this was the first (device table, +38%). | same join fan-out bug and same step-by-step row-count method | 1 |  |
| 2 | note-why-provenance-paper | USEFUL_CONNECT | Why-provenance would point straight from an inflated row to its two region rows. |  |  |  |
| 3 | stage:stage-df-lineage-01-trace | UNJUDGED | The pending "Trace a wrong number" stage, the same exercise. |  |  |  |
| 4 | workspace-dataframe-skill | USEFUL_CONNECT | Debugging multi-step pipelines is one of its objectives. |  |  |  |
| 5 | note-relational-algebra-operators | UNJUDGED | Bag vs set semantics; SQL keeps the duplicates. |  |  |  |
| 6 | note-db-normalization-3nf | AMBIGUOUS | A dimension key that is not unique is the key/FD violation her uniqueness check guards against. |  |  |  |
| 7 | note-idempotent-pipelines-backfills | AMBIGUOUS | Another way pipeline totals double silently (append on retry). |  |  |  |

## A06 — arrival:A06

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | garden:ledgerline-receipt-idea.md | MUST_CONNECT | The seed this format grows out of (hash before/after, why, replay to April). |  |  |  |
| 2 | workspace-ledgerline | MUST_CONNECT | Its objective is "design the receipt format"; it is blocked until after 2026-10-12. | answers 'full text or diff?' | 1 |  |
| 3 | project-ledgerline | MUST_CONNECT | The project; note the decision to pause it until after the October exams. | the project is paused by a recorded decision |  |  |
| 4 | note-event-sourcing-append-only | MUST_CONNECT | Current text = fold over receipts; snapshots every 50 match event-sourcing snapshots. | append-only receipts with state rebuilt by replay is event sourcing | 2 |  |
| 5 | note-git-internals-content-addressing | USEFUL_CONNECT | A hash chain where changing the past changes every later id; integrity by recomputing the hash. | hash chain with parent pointers, integrity by recomputing hashes |  |  |
| 6 | arrival:A23 | UNJUDGED | The retry/duplicate-receipt problem in this very format. |  |  |  |
| 7 | garden:logs-are-the-real-database.md | USEFUL_CONNECT | The log as truth, tables as cache. |  |  |  |
| 8 | note-idempotency-keys-api | AMBIGUOUS | Needed once clients retry saves. |  |  |  |
| 9 | note-write-ahead-logging-aries | USEFUL_CONNECT | Append-only log with per-record ids (LSNs) and replay. |  |  |  |

## A07 — arrival:A07

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | stage:stage-os-l02-02-proportional-share | MUST_CONNECT | Read for this stage; her stride example (strides 100, 200, 40) stopped at step 4. | the stride example stopped at step 4 |  |  |
| 2 | note-cfs-fair-share | MUST_CONNECT | "Stride scheduling is the deterministic version of lottery — still need to work an example by hand." |  |  |  |
| 3 | note-os-scheduling-exercise-bank | MUST_CONNECT | Exercise 3 (lottery) and exercise 4 (stride, first eight decisions). |  |  |  |
| 4 | workspace-os-oral-prep | UNJUDGED | Oral prep whose next action is the stride example. |  |  |  |
| 5 | note-dominant-resource-fairness-paper | USEFUL_CONNECT | Proportional share extended to several resources. |  |  |  |
| 6 | note-multi-tenant-gpu-sharing | USEFUL_CONNECT | Weighted shares applied to GPUs. |  |  |  |

## A08 — arrival:A08

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | note-dynamic-batching-inference | MUST_CONNECT | The max_batch/max_wait trade-off she measured, including worse p99. | max_batch/max_wait trade throughput for latency |  |  |
| 2 | note-multi-tenant-gpu-sharing | MUST_CONNECT | One heavy client starving a light one, fixed with per-client weights: the same story. | the small client starves behind the big one; per-client queues/weights fix it |  |  |
| 3 | note-cfs-fair-share | USEFUL_CONNECT | Per-client queues served in turn is fair-share scheduling. | serving per-client queues in turn is fair-share/round-robin scheduling |  |  |
| 4 | note-queueing-littles-law | USEFUL_CONNECT | Throughput, queue length and waiting time. |  |  |  |
| 5 | note-cpu-scheduling-round-robin | USEFUL_CONNECT | Round robin across clients trades throughput for response time. |  |  |  |
| 6 | note-kv-cache-transformer-serving | UNJUDGED | Same serving context; memory bounds batch size. |  |  |  |
| 7 | note-dominant-resource-fairness-paper | USEFUL_CONNECT | Fairness across tenants. |  |  |  |

## A09 — arrival:A09

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | note-two-phase-locking-deadlocks | MUST_CONNECT | Database deadlock: waits-for graph, cycle, abort a victim, which is what Postgres did. | waits-for cycle; the DB aborts a victim |  |  |
| 2 | note-deadlock-four-conditions | MUST_CONNECT | "Impose a global lock order so a cycle cannot form", the fix they used. | a fixed lock order breaks circular wait | 2 |  |
| 3 | inbox:20260915-os-oral-questions.md | USEFUL_CONNECT | "How can deadlock be prevented? Which condition would you break in practice?", the exam question she means. |  |  |  |
| 4 | stage:stage-os-l07-01-deadlock | UNJUDGED | The pending deadlock stage. |  |  |  |
| 5 | workspace-os-oral-prep | UNJUDGED | Deadlock is one of the three oral topics. |  |  |  |
| 6 | note-db-exam-cheatsheet | UNJUDGED | 2PL summary. |  |  |  |
| 7 | note-semaphores-producer-consumer | USEFUL_CONNECT | Her own acquisition-order deadlock (mutex before empty). |  |  |  |

## A10 — arrival:A10

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | note-query-optimizer-cost-model | MUST_CONNECT | The same lesson (zip/city there, make/model here), with the same remedies. |  |  |  |
| 2 | note-independence-vs-conditional-independence | USEFUL_CONNECT | Factorising joint selectivity assumes independence; make and model are dependent. |  |  |  |
| 3 | note-naive-bayes-spam-filter | USEFUL_CONNECT | The same factorisation assumption, harmless for classification ranking, harmful for cardinalities. | the same independence factorization |  |  |
| 4 | garden:independence-assumptions-that-still-work.md | USEFUL_CONNECT | A case where the false-but-useful simplification stops being useful. |  |  |  |
| 5 | note-selinger-join-ordering | USEFUL_CONNECT | Bad estimates mislead the join-order search. |  |  |  |
| 6 | note-db-normalization-3nf | UNJUDGED | model → make is a functional dependency. |  |  |  |
| 7 | note-columnar-storage-compression | UNJUDGED | Parquet column statistics. |  |  |  |

## A11 — arrival:A11

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | note-p-values-corrected | MUST_CONNECT | Same definition and the same "large p does not prove H0"; the card is a condensed copy. | already recorded; no new durable note needed | 1 |  |
| 2 | inbox:20260903-pvalue-reminder.md | MUST_CONNECT | Earlier capture of the same correction after a mock mistake. |  |  |  |
| 3 | note-p-values-first-take | USEFUL_CONNECT | The wrong April version the card guards against. | flagged as the wrong earlier belief | 2 |  |
| 4 | note-spaced-repetition-scheduler | USEFUL_CONNECT | It is an Anki card; her card-writing rules. |  |  |  |
| 5 | note-conditional-probability-basics | USEFUL_CONNECT | P(H0 / data) would need Bayes' rule. |  |  |  |

## A12 — arrival:A12

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | note-hmm-viterbi | MUST_CONNECT | The algorithm she executed by hand (δ table and backpointers). |  |  |  |
| 2 | note-markov-chains-stationary | USEFUL_CONNECT | Weather Markov chain; the hidden-state chain's stationary behaviour. |  |  |  |
| 3 | note-dynamic-programming-memoization | USEFUL_CONNECT | Viterbi is a DP table over (t, state). | the δ table is a DP table |  |  |
| 4 | workspace-statlearn-retake | USEFUL_CONNECT | Statistical Learning bonus exercise. |  |  |  |
| 5 | note-selinger-join-ordering | USEFUL_CONNECT | Same keep-the-best-sub-solution principle. |  |  |  |

## A13 — arrival:A13

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | note-amdahls-law | MUST_CONNECT | Her note already states Amdahl and Gustafson's counterpoint; the excerpt is the textbook version. | Amdahl (sequential fraction) and Gustafson (scaled problem size) | 2 |  |
| 2 | note-parallel-workers-no-speedup | MUST_CONNECT | Her 16-worker job with a serial CSV parse, a worked Amdahl case. | the CSV parse is the sequential fraction | 2 |  |
| 3 | note-data-parallel-training-scaling | MUST_CONNECT | Non-shrinking all-reduce and data loading cap GPU speed-up. | all-reduce/data loading don't shrink; bigger per-GPU batches is Gustafson-style scaling | 1 |  |
| 4 | workspace-dataframe-skill | UNJUDGED | Where the parallel-workers experiment lives. |  |  |  |

## A14 — arrival:A14

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | stage:stage-df-lazy-02-read-explain | MUST_CONNECT | Written for this stage: plans 2 and 3 were still to do. | plans 2 and 3 complete the stage |  |  |
| 2 | note-lazy-evaluation-query-plans | MUST_CONNECT | Predicate/projection pushdown and common subplan elimination (the CACHE node). |  |  |  |
| 3 | inbox:20260812-lazy-plan-explain-paste.md | MUST_CONNECT | Plan 1 paste with "why did the filter disappear from the top??", answered by her rule here. | answers 'why did the filter disappear from the top' |  |  |
| 4 | note-algebraic-equivalences-pushdown | MUST_CONNECT | The algebra behind "a filter moves below only if it depends on nothing that operator creates". | a selection can move below an operator only when it uses nothing that operator produces |  |  |
| 5 | workspace-dataframe-skill | UNJUDGED | Next action: annotate three explain() plans. |  |  |  |
| 6 | arrival:A03 | UNJUDGED | Tessera's filter-below-join rule, the same condition. |  |  |  |
| 7 | note-constant-folding-cse | USEFUL_CONNECT | Common subexpression elimination, the compiler twin of the CACHE node. | CACHE = common subexpression elimination |  |  |
| 8 | note-tagless-visitor-pattern-ast | UNJUDGED | Her own rule engine applying such rewrites. |  |  |  |

## A15 — arrival:A15

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | garden:temperature-everywhere.md | MUST_CONNECT | Answers the seed's question: softmax temperature and annealing are both exp(−E/T) (Boltzmann). | answers the seed's 'coincidence or same physics?' |  |  |
| 2 | note-softmax-temperature | MUST_CONNECT | Temperature limits T→0 and T→∞. |  |  |  |
| 3 | note-simulated-annealing | MUST_CONNECT | Metropolis acceptance exp(−Δ/T). | exp(−ΔE/T) acceptance has the same Boltzmann form | 2 |  |
| 4 | note-logistic-regression-cross-entropy | USEFUL_CONNECT | Sigmoid as two-class softmax. |  |  |  |
| 5 | garden:attention-as-soft-lookup.md | UNJUDGED | Softmax as soft argmax in attention. |  |  |  |

## A16 — arrival:A16

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | note-batchnorm-internal-covariate-shift | MUST_CONNECT | "At test time use running averages … not the statistics of the test batch", the rule she broke. | use running averages at test time |  |  |
| 2 | note-normal-distribution-standardizing | USEFUL_CONNECT | Her z-score analogy. | standardizing with fixed population parameters, like a z-score | 1 |  |
| 3 | note-batchnorm-why-it-works-contested | USEFUL_CONNECT | The other batch-norm note. |  |  |  |
| 4 | inbox:20260914-batchnorm-forum-question.md | USEFUL_CONNECT | Open batch-norm capture to settle before the exam. |  |  |  |
| 5 | stage:stage-l11-02-optimizers-and-normalization | UNJUDGED | Pending stage covering batch normalization. |  |  |  |
| 6 | note-data-leakage-scaler | USEFUL_CONNECT | Same principle: statistics are fit on training data and reused, never recomputed on test data. | which data's statistics the normalizer uses |  |  |
| 7 | note-cnn-convolution-kernels | USEFUL_CONNECT | The CNN context. |  |  |  |

## A17 — arrival:A17

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | note-cap-consistency-linearizability | MUST_CONNECT | Answers the question: "The C in CAP is not the C in ACID". | no: linearizability vs invariants | 2 |  |
| 2 | note-acid-consistency | MUST_CONNECT | What ACID consistency means (application invariants). |  |  |  |
| 3 | note-two-phase-locking-deadlocks | UNJUDGED | Isolation/serializability, the ACID property people confuse with strong consistency. |  |  |  |
| 4 | workspace-dbsys-exam | UNJUDGED | DB exam context. |  |  |  |
| 5 | note-consistent-estimators | MUST_NOT_CONNECT | A third, statistical meaning of "consistent". |  | 2 |  |

## A18 — arrival:A18

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | garden:everything-is-a-dag.md | MUST_CONNECT | The same idea is already a garden seed (git, make/Bazel, Airflow, query plans, NN graphs; topological sort). | the same idea already sits in the Garden |  |  |
| 2 | note-build-systems-dag-incremental | USEFUL_CONNECT | Build DAGs, topological scheduling and cycle errors. |  |  |  |
| 3 | note-data-pipeline-orchestration-dag | USEFUL_CONNECT | Airflow DAGs; cycles refused at load time. |  |  |  |
| 4 | note-git-internals-content-addressing | USEFUL_CONNECT | Git history as a Merkle DAG. |  |  |  |
| 5 | note-backprop-as-bookkeeping | USEFUL_CONNECT | Autograd walks the computation DAG in reverse. |  |  |  |
| 6 | note-deadlock-four-conditions | USEFUL_CONNECT | Cycle detection in the resource-allocation graph. | cycle detection |  |  |
| 7 | note-two-phase-locking-deadlocks | USEFUL_CONNECT | Cycle detection in the waits-for graph. |  |  |  |
| 8 | note-relational-algebra-operators | UNJUDGED | Queries as operator trees. |  |  |  |

## A19 — arrival:A19

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | note-bloom-filter-false-positive-math | MUST_CONNECT | 10 bits per key → about 1% false positives, the numbers in the excerpt. | 10 bits/key ≈ 1% false positives matches the formula | 2 |  |
| 2 | note-lsm-trees | MUST_CONNECT | "Each SSTable has a small in-memory filter", which is where RocksDB uses Bloom filters. | the note's 'small in-memory filter' per SSTable is a Bloom filter |  |  |
| 3 | note-b-plus-tree-indexes | USEFUL_CONNECT | The other storage-engine design, for contrast. |  |  |  |

## A20 — arrival:A20

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | stage:stage-os-l05-01-translation | UNJUDGED | Written in this stage (first VM session). |  |  |  |
| 2 | note-virtual-memory-address-translation | MUST_CONNECT | Multi-level page tables and the TLB. |  |  |  |
| 3 | note-context-switch-cost | USEFUL_CONNECT | TLB contents useless after a switch; ASID/PCID is the fix. | TLB pollution after a switch; ASID/PCID |  |  |
| 4 | inbox:20260915-os-oral-questions.md | USEFUL_CONNECT | "Why is a TLB needed? What happens on a context switch to the TLB?" | answers 'why is a TLB needed / what happens on a context switch' |  |  |
| 5 | workspace-os-oral-prep | UNJUDGED | Virtual memory is an oral topic. |  |  |  |
| 6 | note-os-kernel-user-mode | UNJUDGED | Only the kernel may change page tables. |  |  |  |
| 7 | note-virtual-memory-is-swap | AMBIGUOUS | Her April misconception; the translation note corrects it. |  |  |  |
| 8 | arrival:A04 | UNJUDGED | Block tables for the KV cache are the same idea. |  |  |  |

## A21 — arrival:A21

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | stage:stage-l09-02-svd-connection | MUST_CONNECT | Answers the stage's stalled question: variance along direction i is s_i²/(n−1). | answers the stage's open question: variance along direction i is s_i²/(n−1) |  |  |
| 2 | note-pca-by-hand | MUST_CONNECT | PCA from the covariance eigenvectors, which the slide redoes via the SVD. |  |  |  |
| 3 | note-svd-geometric | MUST_CONNECT | AᵀA = VΣ²Vᵀ, the step the slide uses. |  |  |  |
| 4 | note-covariance-matrix | USEFUL_CONNECT | The covariance matrix and its eigenvectors. |  |  |  |
| 5 | note-low-rank-approximation | USEFUL_CONNECT | Truncated SVD = keeping the top principal directions. |  |  |  |
| 6 | note-statlearn-mock-exam-september | UNJUDGED | Mock Q5 on the first principal component. |  |  |  |
| 7 | workspace-statlearn-retake | USEFUL_CONNECT | L09 is part of the retake. | open question whether the SVD proof is asked | 1 |  |
| 8 | note-eigenvectors-intuition | USEFUL_CONNECT | Spectral theorem for symmetric matrices. |  |  |  |

## A22 — arrival:A22

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | note-forward-mode-autodiff-dual-numbers | MUST_CONNECT | The forward-mode half; it already says reverse mode is what you want for one output. | forward mode: one pass per input; reverse: one per output |  |  |
| 2 | note-backprop-as-bookkeeping | MUST_CONNECT | Backprop as a reverse walk; the speaker's claim restated. |  |  |  |
| 3 | note-chain-rule-multivariable | MUST_CONNECT | Jacobian products; multiplication order decides cost, the "why" the lecturer left out. | the order of the Jacobian product is the forward/reverse choice; answers 'remember this when we get to neural networks' | 2 |  |
| 4 | stage:stage-l11-01-backprop | UNJUDGED | Pending backprop-by-hand stage. |  |  |  |
| 5 | garden:everything-is-a-dag.md | UNJUDGED | Autograd graphs in her DAG list. |  |  |  |

## A23 — arrival:A23

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | note-idempotency-keys-api | MUST_CONNECT | The same pattern (client key per logical operation, server returns stored result). | save_id is an idempotency key; same key returns stored result |  |  |
| 2 | arrival:A06 | UNJUDGED | The receipt format this fix applies to. |  |  |  |
| 3 | project-ledgerline | MUST_CONNECT | Ledgerline; paused until after the October exams. |  |  |  |
| 4 | workspace-ledgerline | MUST_CONNECT | Receipt-format workspace (blocked until 2026-10-12). | answers 'how to make retried saves not produce duplicate receipts' | 1 |  |
| 5 | note-idempotent-pipelines-backfills | USEFUL_CONNECT | Idempotency against retries in pipelines. |  |  |  |
| 6 | garden:ledgerline-receipt-idea.md | USEFUL_CONNECT | Original receipt idea. |  |  |  |
| 7 | note-event-sourcing-append-only | USEFUL_CONNECT | Append-only events; duplicates corrupt the fold. |  |  |  |

## A24 — arrival:A24

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|

## A25 — arrival:A25

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | note-logistic-regression-cross-entropy | MUST_CONNECT | Answers it: squared error with a sigmoid is non-convex and its gradient vanishes when confidently wrong; cross-entropy is the Bernoulli likelihood. | cross-entropy is the negative Bernoulli log-likelihood; squared error with a sigmoid is non-convex and has vanishing gradients |  |  |
| 2 | note-mle-coin-flips | USEFUL_CONNECT | Bernoulli likelihood → log-likelihood, which gives cross-entropy. | Bernoulli log-likelihood has the CE form |  |  |
| 3 | note-gaussian-noise-least-squares | MUST_CONNECT | The parallel: squared error is the Gaussian likelihood, so neither loss is a convention. | MSE is the Gaussian-noise likelihood; CE is the Bernoulli one — same MLE recipe |  |  |
| 4 | note-convexity-basics | UNJUDGED | Convexity of the loss. |  |  |  |
| 5 | note-generative-vs-discriminative | UNJUDGED | Logistic regression as the discriminative model. |  |  |  |

## A26 — arrival:A26

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | note-gradient-descent-from-scratch | MUST_CONNECT | "The housing thing in April": η = 0.1 exploded to inf, solved by feature scaling. | the April divergence at η=0.1; resolved there by standardizing features | 2 |  |
| 2 | note-sgd-momentum-nn-training | MUST_CONNECT | The MLP training setup. |  |  |  |
| 3 | note-adam-vs-sgd-revisited | UNJUDGED | Learning-rate sensitivity. |  |  |  |
| 4 | note-normal-distribution-standardizing | USEFUL_CONNECT | Feature standardization, the fix last time. |  |  |  |
| 5 | note-mixed-precision-training | AMBIGUOUS | Where inf/NaN come from numerically. |  |  |  |
| 6 | note-batchnorm-internal-covariate-shift | UNJUDGED | Batch norm allows larger learning rates. |  |  |  |

## A27 — arrival:A27

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | note-hash-join-vs-sort-merge | MUST_CONNECT | Her exam summary "hash join is always O(n+m)"; this measurement shows skew breaks it. | corrects the claim that hash join is always O(n+m); skewed keys overflow one partition and spill | 2 |  |
| 2 | stage:stage-df-joins-01-strategies | UNJUDGED | Written for this stage ("Join strategies and skew"). |  |  |  |
| 3 | workspace-dataframe-skill | USEFUL_CONNECT | Joins-at-scale unit of the dataframe skill. |  |  |  |
| 4 | note-parallel-workers-no-speedup | USEFUL_CONNECT | Another case where one indivisible piece (a single CSV, a single key) caps the speed-up. | one partition dominates like a sequential bottleneck | 2 |  |
| 5 | note-kafka-consumer-lag-backpressure | UNJUDGED | Parallelism capped by partitions; a hot partition is the same skew. |  |  |  |
| 6 | note-external-merge-sort | USEFUL_CONNECT | Spilling and passes when data exceeds memory. |  |  |  |

## A28 — arrival:A28

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | note-kafka-consumer-lag-backpressure | MUST_CONNECT | Answers it: Kafka does not push back, the log just grows; bounded buffers do push back. | lag grows instead of blocking; push-based bounded buffers push back |  |  |
| 2 | note-semaphores-producer-consumer | MUST_CONNECT | The bounded buffer where a full buffer blocks the producer. | a bounded buffer blocks the producer; Kafka's log does not |  |  |
| 3 | note-queueing-littles-law | USEFUL_CONNECT | Lag / consume rate ≈ time behind; L = λW. | lag / consume rate ≈ delay is L = λW |  |  |

## A29 — arrival:A29

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | inbox:20260816-drf-paper-link.md | MUST_CONNECT | Identical capture already in the inbox. | exact duplicate capture | 2 |  |
| 2 | note-dominant-resource-fairness-paper | MUST_CONNECT | She has already read the paper and written it up, so the "read later" is done. | already read and noted on 2026-08-17 |  |  |
| 3 | note-multi-tenant-gpu-sharing | USEFUL_CONNECT | The internship-fair talk that mentioned it. |  |  |  |
| 4 | note-cfs-fair-share | UNJUDGED | Single-resource fair share. |  |  |  |

## A30 — arrival:A30

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | note-kv-cache-transformer-serving | MUST_CONNECT | Answers the question: keys and values of all previous tokens, 0.5 MB per token for 7B fp16. | the server keeps past keys and values; size grows linearly with context | 2 |  |
| 2 | garden:attention-as-soft-lookup.md | MUST_CONNECT | Her attention-as-lookup seed. |  |  |  |
| 3 | arrival:A04 | UNJUDGED | PagedAttention: how that growing memory is managed. |  |  |  |
| 4 | note-softmax-temperature | USEFUL_CONNECT | The softmax inside attention. |  |  |  |
| 5 | note-dynamic-batching-inference | USEFUL_CONNECT | Why KV memory matters for serving. |  |  |  |
| 6 | note-backprop-as-bookkeeping | UNJUDGED | Same store-versus-recompute trade-off for intermediate values. |  |  |  |


## Judge grading notes (S10)

- expl: 0 wrong/absent, 1 partly right, 2 correct. All keyword-heuristic misses
  were human-graded; heuristic-covered rows were accepted after a 12-row
  spot-check per run found no false covers. MUST_NOT rows graded on whether
  the stated reason is factually correct (several are knowing contrasts).
- prov: 1 cited material refs resolve and support the claim; 0 no usable
  citation (no evidence, or only a discovery-method note such as a `los ...`
  command or `surfaced by:` line). Sampled rows only; see FAILURE_ANALYSIS.md.
