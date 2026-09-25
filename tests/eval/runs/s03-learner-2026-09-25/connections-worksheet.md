# Connection worksheet (judge)

Grade each returned relevant target: explanation 0 (wrong/absent) · 1 (partly) · 2 (correct), provenance 0/1. Oracle mentions are guidance, not wording.

## C01 — note-naive-bayes-spam-filter

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | stage:stage-l05-01-derive-naive-bayes | MUST_CONNECT | The completed derivation of this same classifier without slides; states exactly where the naive assumption enters and the Laplace estimate. | the stage derivation of the same classifier |  |  |
| 2 | note-independence-vs-conditional-independence | MUST_CONNECT | The naive assumption is conditional independence of words given the class; this note explains why that is different from plain independence (and 'explaining away'). | the naive assumption is conditional independence of the words/features given the class; it is what lets p(x/y) factor into a product | 2 |  |
| 3 | note-generative-vs-discriminative | MUST_CONNECT | Places Naive Bayes as the generative classifier against logistic regression; the current L05 stage builds on it. | NB is the generative model compared with logistic regression |  |  |
| 4 | stage:stage-l05-02-generative-vs-discriminative | UNJUDGED | Active stage running NB vs logistic regression on the same bag-of-words features (NB ahead at n=50/200). |  |  |  |
| 5 | note-mle-coin-flips | UNJUDGED | Each P(w_i / spam) is a Bernoulli MLE (a count); the k = 0 overconfidence problem there is exactly what Laplace smoothing fixes here ('Havelberg'). |  |  |  |
| 6 | note-conditional-probability-basics | USEFUL_CONNECT | Bayes' rule, prior/likelihood/posterior/evidence — the first line of the spam note. | Bayes' rule is the starting point of the NB posterior |  |  |
| 7 | garden:independence-assumptions-that-still-work.md | USEFUL_CONNECT | The Garden seed this note provoked: false-but-useful simplifications. | the garden seed asks why NB works despite a false assumption | 2 |  |
| 8 | note-query-optimizer-cost-model | USEFUL_CONNECT | Cross-course: the optimizer's sel(p₁∧p₂)=sel(p₁)·sel(p₂) is the same 'columns have nothing to do with each other' assumption, but there magnitude errors compound instead of only the ranking mattering. | both multiply per-feature/per-predicate probabilities as if independent; both break when features/columns are correlated | 2 | 1 |
| 9 | note-map-estimation-priors | UNJUDGED | Add-one (Laplace) smoothing is a prior on the word probabilities — the MAP view of the same estimates. |  |  |  |
| 10 | note-statlearn-mock-exam-september | USEFUL_CONNECT | Mock exam Q2 is a Naive Bayes spam classification asking for the assumption and why it is violated. |  |  | 1 |

## C02 — note-map-estimation-priors

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | note-ridge-regression-penalty | MUST_CONNECT | MAP with a Gaussian prior on the weights is ridge regression with λ = σ²/τ²; this answers the ridge note's open question 'where does λ come from'. | a Gaussian prior on the weights gives a squared (L2) penalty; ridge = MAP with Gaussian prior; lambda corresponds to sigma²/tau² (prior strength) | 2 |  |
| 2 | note-gaussian-noise-least-squares | USEFUL_CONNECT | Supplies the likelihood term: Gaussian noise turns −log p(D/θ) into squared error. | the likelihood term is the squared error from the Gaussian-noise model |  |  |
| 3 | note-mle-coin-flips | USEFUL_CONNECT | The MLE side of MAP (concept relation MAP builds-on MLE); ends by saying priors fix MLE's overconfidence. | MAP adds a log-prior to the MLE objective; fixes the k=0 overconfidence the coin note complains about | 2 |  |
| 4 | note-lasso-sparsity-geometry | USEFUL_CONNECT | The Laplace-prior line of this note gives Σ/θ_j/ — the lasso; geometric explanation of the resulting zeros. | a Laplace prior gives the L1 (lasso) penalty |  |  |
| 5 | stage:stage-l07-01-ridge-lasso-geometry | USEFUL_CONNECT | Active stage where the learner is stuck on why lasso gives zeros; the prior view is one route in. |  |  |  |
| 6 | note-conditional-probability-basics | USEFUL_CONNECT | Bayes' rule and the prior/likelihood/posterior/evidence vocabulary used in the MAP derivation. |  |  |  |
| 7 | note-bias-variance-from-book | USEFUL_CONNECT | Shrinking an estimate towards zero adds bias but can lower MSE — why a prior can help. | shrinkage adds bias but can reduce variance |  |  |
| 8 | note-naive-bayes-spam-filter | UNJUDGED | Laplace smoothing there is a prior on the word counts — a concrete MAP instance. |  |  |  |
| 9 | note-generative-vs-discriminative | UNJUDGED | Its 'half-understood' guess is that extra modelling assumptions act like a prior. |  |  |  |
| 10 | note-convexity-basics | AMBIGUOUS | Loss + λ‖w‖² is strictly convex — why the Gaussian-prior MAP problem has a unique solution. |  |  |  |

## C03 — note-parallel-workers-no-speedup

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | note-amdahls-law | MUST_CONNECT | The explanation: the single-process CSV parse is the serial fraction, so speedup is capped near 1/(1−p). | the single-process CSV parse is the sequential fraction; speedup is bounded by 1/(1−p); with half the job sequential, at most 2× | 2 |  |
| 2 | note-data-parallel-training-scaling | USEFUL_CONNECT | Same pattern with GPUs: all-reduce and shared-disk loading do not shrink, so 8 GPUs give 4.2×. | the non-shrinking part (all-reduce, data loading) limits speedup the same way | 2 |  |
| 3 | note-columnar-storage-compression | USEFUL_CONNECT | The fix was switching the export to Parquet files; this note explains why columnar files are cheaper to read. |  |  |  |
| 4 | note-kafka-consumer-lag-backpressure | UNJUDGED | 'Parallelism is capped by the partition count' — the same reason one CSV file capped the parse. |  |  |  |
| 5 | stage:stage-df-lazy-01-lazy-vs-eager | UNJUDGED | Measured on a 2 GB CSV pipeline: most of the gain came from reading only 4 of 31 columns — reading cost dominates here too. |  |  |  |
| 6 | note-lazy-evaluation-query-plans | UNJUDGED | Same workspace; projection/predicate pushdown into the file reader attacks the same reading bottleneck. |  |  |  |
| 7 | workspace-dataframe-skill | USEFUL_CONNECT | The workspace this note belongs to. |  |  |  |
| 8 | note-data-pipeline-orchestration-dag | USEFUL_CONNECT | Nightly pipeline as a DAG with independent branches run in parallel. |  |  |  |
| 9 | note-data-lineage-debugging | UNJUDGED | Same practice pipeline/workspace (dashboard job). |  |  |  |

## C04 — note-cfs-fair-share

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | stage:stage-os-l02-02-proportional-share | MUST_CONNECT | The active working note on the same topic: lottery short-run unfairness and the stride example in progress. | the half-finished stride example |  |  |
| 2 | note-os-scheduling-exercise-bank | MUST_CONNECT | Exercises 3–5 practise lottery, stride and CFS nice weights. |  |  |  |
| 3 | note-cpu-scheduling-round-robin | MUST_CONNECT | The classic policies and MLFQ that proportional share is contrasted with. |  |  |  |
| 4 | note-context-switch-cost | USEFUL_CONNECT | Why sched_latency has a minimum granularity: tiny slices are dominated by switch cost. |  |  |  |
| 5 | note-dominant-resource-fairness-paper | USEFUL_CONNECT | Generalizes 'fair share' from one resource (CPU) to several (CPU + memory). | DRF generalizes fair share to several resources |  |  |
| 6 | note-multi-tenant-gpu-sharing | USEFUL_CONNECT | Weighted shares with lending of unused share — CFS-style weights applied to GPU time between teams. | weighted shares per team is proportional-share scheduling; unused share is lent out and reclaimed; strict priority starved batch jobs | 1 |  |
| 7 | workspace-os-oral-prep | UNJUDGED | Its open question is how deep the chair goes on CFS internals. |  |  |  |
| 8 | inbox:20260915-os-oral-questions.md | USEFUL_CONNECT | First collected oral question: 'Explain how the scheduler on your laptop decides what runs next.' |  |  |  |
| 9 | garden:fairness-for-my-study-time.md | AMBIGUOUS | The learner's idea of scheduling study time like CFS with a 'virtual study time'. |  |  |  |
| 10 | note-study-plan-retake-strategy | MUST_NOT_CONNECT | A fixed weekly share with catch-up is proportional-share scheduling of study time. |  | 1 |  |

## C05 — note-write-ahead-logging-aries

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | note-journaling-filesystems | MUST_CONNECT | The same 'write the log record durably before the in-place change' rule in the OS course (ext3/ext4 journal + commit block). | the journal/log record must be durable before the in-place write; after a crash, committed records are replayed/redone and uncommitted ignored | 1 |  |
| 2 | note-acid-consistency | USEFUL_CONNECT | WAL is the machinery behind A and D. | WAL provides atomicity and durability | 2 |  |
| 3 | note-event-sourcing-append-only | USEFUL_CONNECT | The log-as-truth view: state is a fold over an append-only log; 'compensating' events echo ARIES CLRs. | an append-only log from which state is rebuilt by replay |  |  |
| 4 | garden:logs-are-the-real-database.md | MUST_CONNECT | The learner's own seed: a recovery log, event sourcing and git are the same shape. |  |  |  |
| 5 | note-buffer-pool-replacement | UNJUDGED | Steal/no-force is about when dirty buffer-pool pages may be written; the pool's write-back is what WAL orders. |  |  |  |
| 6 | note-lsm-trees | USEFUL_CONNECT | Writes go to a log for durability before the memtable is flushed. |  |  | 1 |
| 7 | note-db-exam-cheatsheet | USEFUL_CONNECT | One-line ARIES summary compiled for the exam; notes the recovery question was harder than expected. |  |  |  |
| 8 | note-two-phase-locking-deadlocks | USEFUL_CONNECT | Same unit (transactions and recovery); aborting a deadlock victim is an undo. |  |  | 0 |
| 9 | garden:ledgerline-receipt-idea.md | USEFUL_CONNECT | Append a record per change and replay to reconstruct any past state — WAL's idea applied to notes. |  |  |  |

## C06 — note-selinger-join-ordering

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | note-query-optimizer-cost-model | MUST_CONNECT | Selinger's DP needs a cost per sub-plan; this note is where the row-count estimates come from (and why they go wrong). | the cost model/cardinality estimates rank the candidate plans | 2 |  |
| 2 | garden:why-did-swapping-from-order-matter.md | MUST_CONNECT | The April question this note answers: does the database reorder joins itself, and based on what? | the April question 'does the database reorder joins?' is answered by cost-based join ordering |  |  |
| 3 | note-dynamic-programming-memoization | MUST_CONNECT | System R join ordering is dynamic programming over table subsets (optimal substructure, keep the best per subset). | System R join enumeration is dynamic programming; best plan per subset = optimal substructure; subsets reused = overlapping subproblems |  | 1 |
| 4 | note-hash-join-vs-sort-merge | USEFUL_CONNECT | 'Interesting orders' exist because a sorted result can feed a merge join. | interesting orders serve merge joins |  |  |
| 5 | note-algebraic-equivalences-pushdown | USEFUL_CONNECT | Join commutativity/associativity make reordering legal; the lecture heuristic says push selections first, then worry about join order. |  |  |  |
| 6 | note-hmm-viterbi | USEFUL_CONNECT | Same principle: the best path into a state only extends best sub-paths. | both keep only the best partial solution per state/subset | 2 |  |
| 7 | project-tessera | USEFUL_CONNECT | Cost-based join ordering is Tessera's planned milestone, deliberately after rule-based rewrites (decision 2026-08-04). |  |  |  |
| 8 | workspace-dataframe-skill | UNJUDGED | Open question: which dataframe optimizations are rule-based and which use statistics. |  |  |  |
| 9 | note-lazy-evaluation-query-plans | USEFUL_CONNECT | The dataframe engine's optimizer from the learner's current skill module. |  |  |  |
| 10 | note-relational-algebra-operators | UNJUDGED | Operator trees with base tables at the leaves — the plans being enumerated. |  |  |  |

## C07 — note-query-optimizer-cost-model

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | note-selinger-join-ordering | MUST_CONNECT | The search procedure that consumes these cost estimates. |  |  |  |
| 2 | note-naive-bayes-spam-filter | USEFUL_CONNECT | Cross-course: the same 'treat features as unrelated' assumption, which NB survives because only the ranking matters. | the product-of-selectivities rule is the same independence assumption Naive Bayes makes | 2 |  |
| 3 | note-independence-vs-conditional-independence | USEFUL_CONNECT | Correlated columns (city/zip) are dependent; the product rule assumes independence. | P(A,B)=P(A)P(B) only under independence; correlated columns violate it |  |  |
| 4 | note-db-normalization-3nf | UNJUDGED | zip → city is a functional dependency; the FD is exactly the correlation that breaks the independence estimate. |  |  |  |
| 5 | garden:independence-assumptions-that-still-work.md | USEFUL_CONNECT | Selectivity estimation is another 'false-but-useful simplification' (one that often hurts). |  |  |  |
| 6 | garden:why-did-swapping-from-order-matter.md | UNJUDGED | Cost-based plan choice explains why FROM order can matter on an old engine and not on a cost-based one. |  |  |  |
| 7 | note-algebraic-equivalences-pushdown | USEFUL_CONNECT | The rule-based half of optimization that the cost model complements. |  |  |  |
| 8 | note-data-lineage-debugging | UNJUDGED | A join that produced 1.38× more rows than expected — a real cardinality surprise at join time. |  |  |  |
| 9 | workspace-dataframe-skill | UNJUDGED | Open question on rule-based vs statistics-based optimizations. |  |  |  |
| 10 | project-tessera | UNJUDGED | Cost model deliberately postponed until the executor is stable. |  |  |  |

## C08 — note-low-rank-approximation

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | note-matrix-factorization-recommenders | MUST_CONNECT | Answers this note's open question: fit the low-rank factors on observed ratings only (ALS/SGD), no SVD of the full matrix needed. | answers the open question about recommenders; fit P Qᵀ only on observed ratings, so missing entries are never needed |  |  |
| 2 | note-svd-geometric | MUST_CONNECT | The SVD this approximation truncates. |  |  |  |
| 3 | stage:stage-linalg-svd-02-low-rank | MUST_CONNECT | The paused stage for this note: rank-5 done, ranks 20/50 open. | rank 5 done, 20/50 not |  |  |
| 4 | stage:stage-l09-02-svd-connection | USEFUL_CONNECT | PCA ↔ SVD for the retake: explained variance = the σ_i² that Eckart–Young drops. |  |  |  |
| 5 | note-pca-by-hand | USEFUL_CONNECT | PCA keeps the top components — the same truncation seen from the covariance side. | PCA keeps the top components — a truncated SVD |  |  |
| 6 | workspace-linalg-refresh | USEFUL_CONNECT | The paused workspace holding the open question. |  |  |  |
| 7 | note-covariance-matrix | USEFUL_CONNECT | Eigen-decomposition of XᵀX links singular values to variances. |  |  |  |
| 8 | note-eigenvectors-intuition | USEFUL_CONNECT | Prerequisite: eigenvectors/spectral theorem. |  |  |  |

## C09 — note-data-lineage-debugging

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | note-why-provenance-paper | MUST_CONNECT | Why-provenance witnesses are exactly 'which input rows produced this output row' — what the note wishes it had. | 'which input rows produced this output row' is why-provenance; a join output's witness has one tuple per side — fan-out duplicates | 1 |  |
| 2 | stage:stage-df-lineage-01-trace | UNJUDGED | The not-yet-started stage 'Trace a wrong number' — this note is effectively its worked case. |  |  |  |
| 3 | note-idempotent-pipelines-backfills | AMBIGUOUS | Another wrong total from the same kind of pipeline (a retry doubled a day's totals). |  |  |  |
| 4 | note-relational-algebra-operators | UNJUDGED | Bag vs set semantics: SQL keeps duplicates unless DISTINCT — the root of COUNT(*) double counting. |  |  |  |
| 5 | note-query-optimizer-cost-model | UNJUDGED | Join output cardinality is where the 1.38× surprise happened. |  |  |  |
| 6 | workspace-dataframe-skill | USEFUL_CONNECT | The workspace this note belongs to. |  |  |  |
| 7 | note-parallel-workers-no-speedup | UNJUDGED | Same practice pipeline; step-by-step timing is the same walk-back method. |  |  |  |
| 8 | note-event-sourcing-append-only | AMBIGUOUS | Keeping full history answers 'how did we get here?'. |  |  |  |
| 9 | note-data-pipeline-orchestration-dag | USEFUL_CONNECT | The pipeline structure the walk-back traverses. |  |  | 0 |

## C10 — note-kv-cache-transformer-serving

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | garden:attention-as-soft-lookup.md | MUST_CONNECT | The learner's own question: is a KV cache literally a cache of the attention 'dictionary'? |  |  |  |
| 2 | note-dynamic-batching-inference | MUST_CONNECT | KV memory limits how many requests fit in a batch. | KV memory limits how many requests fit in a batch |  |  |
| 3 | note-multi-tenant-gpu-sharing | USEFUL_CONNECT | GPU memory, not compute, is often the shared bottleneck. |  |  |  |
| 4 | note-virtual-memory-address-translation | USEFUL_CONNECT | The fragmentation problem (reserve max vs grow as you go) is what paging solves; paged allocation is the obvious fix. | the reserve-vs-grow fragmentation problem is what paging solves in an OS |  |  |
| 5 | note-caching-everywhere | AMBIGUOUS | Another instance of 'keep a small fast copy of something expensive'. |  |  |  |
| 6 | note-dynamic-programming-memoization | AMBIGUOUS | The KV cache avoids recomputation exactly like memoization. |  |  |  |
| 7 | note-mixed-precision-training | USEFUL_CONNECT | Bytes per value (fp16/bf16) set the per-token KV size. |  |  | 0 |
| 8 | note-backprop-as-bookkeeping | UNJUDGED | Also a memory wall from keeping intermediates. |  |  |  |
| 9 | note-softmax-temperature | UNJUDGED | Attention's softmax and sampling temperature in the generation loop. |  |  |  |

## C11 — note-os-kernel-user-mode

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | note-context-switch-cost | MUST_CONNECT | Mode and address-space switches plus cache/TLB pollution are the concrete cost of crossing into the kernel. | mode switches and cache/TLB pollution make kernel entry expensive |  |  |
| 2 | note-virtual-memory-address-translation | USEFUL_CONNECT | Page tables are privileged state; a page fault traps into the kernel. | page tables are changed only in kernel mode; page faults trap into the kernel |  |  |
| 3 | inbox:20260915-os-oral-questions.md | USEFUL_CONNECT | Oral questions on page faults, context switches and the TLB all rest on the kernel/user boundary. |  |  |  |
| 4 | note-cpu-scheduling-round-robin | USEFUL_CONNECT | The scheduler is kernel code; same OS course. |  |  |  |
| 5 | workspace-os-oral-prep | UNJUDGED | The oral prep this topic feeds. |  |  |  |
| 6 | garden:kernel-is-an-overloaded-word.md | USEFUL_CONNECT | The learner's list of the different 'kernels' — this note is the OS one. | as a disambiguation, not an equivalence | 2 |  |
| 7 | note-cfs-fair-share | UNJUDGED | Scheduling policy implemented in the kernel. |  |  |  |
| 8 | note-priority-inversion | USEFUL_CONNECT | Another OS-lecture topic from the same slides (an oral question). |  |  |  |
| 9 | note-svm-kernel-trick | MUST_NOT_CONNECT | Same word, unrelated meaning — contrast only. |  | 2 |  |
| 10 | note-cnn-convolution-kernels | MUST_NOT_CONNECT | Same word, unrelated meaning — contrast only. |  | 2 |  |

## C12 — note-db-normalization-3nf

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | note-db-exam-cheatsheet | MUST_CONNECT | BCNF test line compiled for the exam. |  |  |  |
| 2 | note-relational-algebra-operators | USEFUL_CONNECT | Decompositions are rejoined with natural joins (lossless join). | decomposition uses projection; lossless-join uses natural join |  |  |
| 3 | note-query-optimizer-cost-model | UNJUDGED | The zip → city example is a functional dependency that breaks independent-selectivity estimates. |  |  |  |
| 4 | note-acid-consistency | USEFUL_CONNECT | Keys and declared constraints are what the DB enforces for C. |  |  |  |
| 5 | note-data-lineage-debugging | UNJUDGED | A 1:n join on a non-key duplicated rows — redundancy showing up at query time. |  |  |  |
| 6 | workspace-dbsys-exam | UNJUDGED | The archived exam workspace for this course. |  |  |  |

## C13 — note-acid-consistency

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | note-cap-consistency-linearizability | MUST_CONNECT | Explicitly contrasts CAP consistency with this note's ACID consistency ('see the June note'). | CAP consistency (linearizability) is a different property from ACID consistency (invariants) | 2 |  |
| 2 | note-write-ahead-logging-aries | USEFUL_CONNECT | The A and D machinery. |  |  |  |
| 3 | note-two-phase-locking-deadlocks | USEFUL_CONNECT | The I machinery. |  |  |  |
| 4 | note-db-normalization-3nf | USEFUL_CONNECT | Keys/FDs are the declared constraints the DB can enforce. |  |  |  |
| 5 | note-consistent-estimators | MUST_NOT_CONNECT | Yet another 'consistent' — statistical consistency; contrast only. |  | 2 |  |
| 6 | note-journaling-filesystems | AMBIGUOUS | Crash consistency of file-system structures (the OS analogue of atomicity + durability). |  |  |  |
| 7 | note-idempotency-keys-api | AMBIGUOUS | Stores the key in the same transaction as the effect — atomicity in an API design. |  |  |  |
| 8 | note-db-exam-cheatsheet | UNJUDGED | Exam summary of the course. |  |  |  |

## C14 — note-spaced-repetition-scheduler

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | note-study-plan-retake-strategy | USEFUL_CONNECT | Scheduling study time between two exams — the planning counterpart of review scheduling. |  |  |  |
| 2 | note-pomodoro-and-context-switching | USEFUL_CONNECT | How the learner actually structures study blocks (switching cost). |  |  |  |
| 3 | inbox:20260916-sleep-podcast.md | USEFUL_CONNECT | Memory consolidation after learning — the same retention question from another angle. |  |  |  |
| 4 | note-queueing-littles-law | UNJUDGED | The review backlog is a queue: 'never skip a day' is L = λW. |  |  |  |
| 5 | garden:fairness-for-my-study-time.md | UNJUDGED | A scheduler idea for study time. |  |  |  |
| 6 | note-cfs-fair-share | MUST_NOT_CONNECT | The OS scheduler analogy the Garden seed borrows. |  | 1 |  |
| 7 | note-oral-exam-prep-strategy | UNJUDGED | Retrieval practice aloud for the oral. |  |  |  |
| 8 | note-weekly-review-log | UNJUDGED | The learner's own review cadence. |  |  | 0 |
| 9 | note-semester-review-july | UNJUDGED | Lesson: exercise sheets every week, not in exam week (spacing). |  |  |  |
| 10 | note-how-i-take-notes | USEFUL_CONNECT | The learner's own note-taking rules (write in own words). |  |  |  |

## C15 — note-buffer-pool-replacement

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | note-page-replacement-lru-clock | MUST_CONNECT | The OS version of the same eviction problem; sequential flooding is the 'working set one page larger than memory' worst case. | the same eviction problem in the OS; LRU fails when a scan/loop is larger than memory (sequential flooding) |  |  |
| 2 | note-caching-everywhere | MUST_CONNECT | Explicitly lists the buffer pool as one of three instances of the same cache idea. |  |  |  |
| 3 | note-cpu-cache-locality | USEFUL_CONNECT | Hardware caching and locality. |  |  |  |
| 4 | note-write-ahead-logging-aries | UNJUDGED | Dirty-page write-back (steal/no-force) is constrained by WAL. |  |  |  |
| 5 | note-virtual-memory-address-translation | USEFUL_CONNECT | The OS page cache/paging that databases often bypass. |  |  |  |
| 6 | note-b-plus-tree-indexes | USEFUL_CONNECT | Top index levels stay cached in the pool — why a lookup costs one disk read. |  |  |  |
| 7 | note-external-merge-sort | USEFUL_CONNECT | Uses B buffer pages from the pool. |  |  |  |
| 8 | note-dynamic-programming-memoization | UNJUDGED | Memoization is a cache that never evicts (the contrast in the caching note). |  |  |  |
| 9 | note-kv-cache-transformer-serving | AMBIGUOUS | Another memory-managed cache with fragmentation problems. |  |  |  |

## C16 — note-p-values-corrected

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | note-p-values-first-take | MUST_CONNECT | The April note this one corrects; kept, marked deprecated, but not linked. | the April note is the wrong earlier belief that this note corrects | 2 |  |
| 2 | inbox:20260903-pvalue-reminder.md | MUST_CONNECT | The same mistake recurred in the September mock — the correction has not stuck yet. | the misconception recurred in September |  |  |
| 3 | note-conditional-probability-basics | USEFUL_CONNECT | The underlying error is swapping P(data/H0) with P(H0/data) — the same swapped-conditional trap as the disease test. | confusing P(data/H0) with P(H0/data) is the swapped-conditional trap |  |  |
| 4 | note-map-estimation-priors | UNJUDGED | Getting P(H0 / data) would need Bayes' rule and a prior — the Bayesian side mentioned in this note. |  |  |  |
| 5 | note-statlearn-mock-exam-september | UNJUDGED | The mock where the error recurred; retake practice. |  |  |  |
| 6 | note-normal-distribution-standardizing | UNJUDGED | Tail probabilities of a standardized statistic (P(Z > 2) ≈ 0.023) are what a p-value computes. |  |  |  |
| 7 | note-central-limit-theorem-simulation | USEFUL_CONNECT | Why test statistics are approximately normal. |  |  |  |
| 8 | workspace-statlearn-retake | UNJUDGED | Exam context for the retake. |  |  |  |

## C17 — note-gradient-descent-from-scratch

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | note-normal-distribution-standardizing | USEFUL_CONNECT | The fix (standardize features) and it even mentions square metres vs rooms. | standardizing features fixed the divergence |  |  |
| 2 | note-sgd-momentum-nn-training | MUST_CONNECT | 'The update rule is the same one from the housing exercise'; momentum cancels the zig-zag across narrow directions — the long thin valley. | same update rule with a minibatch gradient and momentum |  |  |
| 3 | note-linear-regression-normal-equation | MUST_CONNECT | The closed-form alternative (concept relation: normal equation contrasts-with gradient descent). | closed form vs iterative |  |  |
| 4 | note-convexity-basics | USEFUL_CONNECT | Squared error of a linear model is convex, so GD finds the global minimum. | squared error is convex, so descent finds the global minimum |  |  |
| 5 | note-data-leakage-scaler | UNJUDGED | How to standardize without leaking validation data. |  |  |  |
| 6 | note-adam-vs-sgd-revisited | USEFUL_CONNECT | Per-parameter step sizes (Adam) are another answer to badly scaled directions. |  |  |  |
| 7 | note-regression-metrics | USEFUL_CONNECT | Metrics of the same housing regression (MAE/RMSE/R²). |  |  | 0 |
| 8 | note-gaussian-noise-least-squares | UNJUDGED | Why the loss is mean squared error. |  |  |  |
| 9 | note-ridge-regression-penalty | UNJUDGED | Same linear-regression loss plus a penalty. |  |  |  |
| 10 | note-covariance-matrix | UNJUDGED | The elongated ellipse picture behind the 'long thin valley'. |  |  |  |

## C18 — note-dynamic-batching-inference

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | note-kv-cache-transformer-serving | USEFUL_CONNECT | KV-cache memory decides how many requests fit into a batch. |  |  |  |
| 2 | note-multi-tenant-gpu-sharing | MUST_CONNECT | Interactive vs batch traffic on shared GPUs. |  |  |  |
| 3 | note-queueing-littles-law | USEFUL_CONNECT | Waiting requests, arrival rate and delay: L = λW. | requests waiting in the queue relate arrival rate and waiting time (L = λW) |  |  |
| 4 | note-kafka-consumer-lag-backpressure | USEFUL_CONNECT | Throughput vs queue growth and backpressure. |  |  |  |
| 5 | note-cpu-scheduling-round-robin | UNJUDGED | Quantum trade-off: responsiveness vs overhead — same shape as max_wait vs throughput. |  |  |  |
| 6 | note-context-switch-cost | UNJUDGED | Amortizing a fixed per-dispatch cost. |  |  |  |
| 7 | note-data-parallel-training-scaling | UNJUDGED | Bigger per-GPU batches helped until accuracy dropped. |  |  |  |
| 8 | note-semaphores-producer-consumer | UNJUDGED | Bounded queue between producers and a consumer. |  |  |  |

## C19 — note-softmax-temperature

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | garden:temperature-everywhere.md | MUST_CONNECT | The learner's own question: is softmax temperature the same physics as annealing temperature? |  |  | 1 |
| 2 | note-simulated-annealing | USEFUL_CONNECT | exp(−Δ/T) acceptance and the cooling schedule. | both are exp(−E/T) Boltzmann forms; T→0 becomes greedy/argmax | 1 |  |
| 3 | note-logistic-regression-cross-entropy | USEFUL_CONNECT | The two-class softmax (sigmoid) and cross-entropy. |  |  |  |
| 4 | garden:attention-as-soft-lookup.md | UNJUDGED | Attention turns scores into weights with a softmax. |  |  |  |
| 5 | note-kv-cache-transformer-serving | UNJUDGED | Language-model generation, where sampling temperature is used. |  |  |  |

## C20 — note-constant-folding-cse

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | note-tagless-visitor-pattern-ast | MUST_CONNECT | Tessera's optimizer already folds '1 = 1' and applies rules until a pass changes nothing (cap 50) — this note's fixed-point idea in the learner's own code. | Tessera's rules fold constants and iterate to a fixed point with a pass cap |  |  |
| 2 | note-algebraic-equivalences-pushdown | USEFUL_CONNECT | Meaning-preserving rewrite rules for query plans — the DB counterpart of compiler passes. | both rewrite a tree with meaning-preserving equivalences |  |  |
| 3 | note-ssa-form | MUST_CONNECT | SSA makes constant propagation and CSE simple passes. |  |  |  |
| 4 | inbox:20260910-tessera-todo.md | USEFUL_CONNECT | Constant folding is done; open item: rules fighting each other (non-termination). | rules fighting each other / termination |  |  |
| 5 | workspace-tessera-engine | USEFUL_CONNECT | Open question on termination when two rules undo each other. |  |  |  |
| 6 | note-property-based-testing | USEFUL_CONNECT | execute(optimize(q)) == execute(q) is the test of 'every rewrite must preserve meaning'. | execute(optimize(q)) == execute(q) checks meaning preservation |  |  |
| 7 | note-lazy-evaluation-query-plans | USEFUL_CONNECT | Dataframe optimizers list common subplan elimination and expression simplification. | common subplan elimination / expression simplification |  |  |
| 8 | note-compiler-pipeline-overview | MUST_CONNECT | Where optimization passes sit in a compiler (concept relation builds-on). |  |  | 0 |
| 9 | note-regression-testing-snapshots | UNJUDGED | Tessera snapshots the printed optimized plan for twenty queries. |  |  |  |

## A01 — arrival:A01

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | note-naive-bayes-spam-filter | MUST_CONNECT | '??? recognize this from somewhere': a single class node with arrows to every feature node is exactly the Naive Bayes model — its factorization is the BN joint for that graph. | the class node with arrows to every feature is Naive Bayes; answers the '??? recognize this' line | 2 |  |
| 2 | note-independence-vs-conditional-independence | MUST_CONNECT | Where the page was filed: a BN is a joint that factorizes by conditional-independence claims; 'explaining away' is already in this note. | a node is independent of its non-descendants given its parents; explaining away appears in both | 1 |  |
| 3 | note-generative-vs-discriminative | USEFUL_CONNECT | Naive Bayes as the generative classifier — the BN view of p(x/y)p(y). |  |  |  |
| 4 | stage:stage-l05-01-derive-naive-bayes | UNJUDGED | The learner's own derivation of the NB factorization Π_j p(x_j/y). |  |  |  |
| 5 | note-hmm-viterbi | USEFUL_CONNECT | An HMM is a chain-structured Bayesian network over hidden states and emissions. | an HMM is a Bayesian network over a chain |  |  |
| 6 | note-query-optimizer-cost-model | AMBIGUOUS | Same move in databases: factorizing a joint as if columns were independent. |  |  |  |
| 7 | garden:independence-assumptions-that-still-work.md | USEFUL_CONNECT | False-but-useful independence assumptions — BNs make them explicit per edge. |  |  |  |
| 8 | garden:everything-is-a-dag.md | AMBIGUOUS | One more DAG for the learner's list. |  |  |  |
| 9 | note-markov-chains-stationary | USEFUL_CONNECT | Markov chain = the simplest chain-shaped graphical model. |  |  |  |
| 10 | note-conditional-probability-basics | USEFUL_CONNECT | Bayes' rule underlying inference in the network. |  |  |  |

## A02 — arrival:A02

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | stage:stage-l07-01-ridge-lasso-geometry | MUST_CONNECT | Filed here; it answers the stage's own 'question for later: is there a one-dimensional version I can solve by hand?'. | the stage asked for a 1-D version by hand |  |  |
| 2 | note-ridge-regression-penalty | MUST_CONNECT | Answers its open question 'Why is there a neat closed form here while the lasso needs special solvers?' — the lasso solution is piecewise. | answers why ridge has a closed form and lasso does not (piecewise/soft-thresholding) |  |  |
| 3 | note-lasso-sparsity-geometry | MUST_CONNECT | The geometric (diamond-corner) explanation of the same zeros; A02 is the algebraic one (soft thresholding). | algebraic (soft-thresholding) counterpart of the diamond-corner picture | 2 |  |
| 4 | note-map-estimation-priors | USEFUL_CONNECT | L1 penalty = Laplace prior; soft thresholding is the MAP estimate under it. | Laplace prior |  |  |
| 5 | note-convexity-basics | USEFUL_CONNECT | /w/ is convex but not differentiable at 0 — why the minimum can sit at the kink. |  |  |  |
| 6 | stage:stage-l07-02-choose-lambda | UNJUDGED | Next stage: choosing λ, which sets the threshold. |  |  |  |
| 7 | note-statlearn-mock-exam-september | UNJUDGED | Mock Q3 (ridge estimator) — the contrast with lasso is exam material. |  |  |  |
| 8 | workspace-statlearn-retake | USEFUL_CONNECT | 'L07 regularization is the biggest gap.' |  |  |  |

## A03 — arrival:A03

_not answered_

## A04 — arrival:A04

_not answered_

## A05 — arrival:A05

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | note-data-lineage-debugging | MUST_CONNECT | The first fan-out bug ('Second time a join fan-out has bitten me'): same walk-back with row counts, same duplicate-key cause. | same join fan-out bug and same step-by-step row-count method | 2 |  |
| 2 | stage:stage-df-lineage-01-trace | UNJUDGED | Filed here: the stage asks for exactly this — a written trace with row counts per step. |  |  |  |
| 3 | note-db-normalization-3nf | AMBIGUOUS | The fix (uniqueness check on the dimension key) is enforcing a key constraint. |  |  |  |
| 4 | note-why-provenance-paper | USEFUL_CONNECT | Why-provenance would point from the doubled North revenue straight to the two 'N' region rows. |  |  |  |
| 5 | note-relational-algebra-operators | UNJUDGED | Bag semantics: joins keep duplicates unless DISTINCT. |  |  |  |
| 6 | note-idempotent-pipelines-backfills | AMBIGUOUS | Another doubled number from the same practice pipelines (retry doubled a day's totals). |  |  | 0 |
| 7 | note-query-optimizer-cost-model | UNJUDGED | Join output cardinality, estimated vs actual. |  |  |  |
| 8 | workspace-dataframe-skill | USEFUL_CONNECT | Workspace owning the lineage unit. |  |  |  |

## A06 — arrival:A06

_not answered_

## A07 — arrival:A07

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | stage:stage-os-l02-02-proportional-share | MUST_CONNECT | Filed here: the stage's reading (stride paper §2) and its stride example in progress. | the stride example stopped at step 4 |  |  |
| 2 | note-cfs-fair-share | MUST_CONNECT | Lottery vs stride: the paper's error bound (constant vs √n) is the precise version of 'fair only on average'. |  |  |  |
| 3 | note-os-scheduling-exercise-bank | MUST_CONNECT | Exercises 3–4 (lottery probability, stride decisions). |  |  |  |
| 4 | workspace-os-oral-prep | UNJUDGED | Oral prep for which this stage is exam-critical. |  |  |  |
| 5 | note-cpu-scheduling-round-robin | USEFUL_CONNECT | The baseline policies proportional share is contrasted with. |  |  |  |
| 6 | note-dominant-resource-fairness-paper | USEFUL_CONNECT | Proportional share generalized to several resources. |  |  |  |
| 7 | note-multi-tenant-gpu-sharing | USEFUL_CONNECT | Weighted shares in practice. |  |  |  |
| 8 | garden:fairness-for-my-study-time.md | AMBIGUOUS | Pass/stride as a study scheduler. |  |  |  |

## A08 — arrival:A08

_not answered_

## A09 — arrival:A09

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | note-deadlock-four-conditions | MUST_CONNECT | The friend's fix ('always touch tables in the same order') is exactly the practical prevention in this note: a global lock order breaks circular wait. | a fixed lock order breaks circular wait |  |  |
| 2 | note-two-phase-locking-deadlocks | MUST_CONNECT | The database side: 2PL does not prevent deadlocks; the DB keeps a waits-for graph and aborts a victim — Postgres's 'deadlock detected'. | waits-for cycle; the DB aborts a victim |  |  |
| 3 | inbox:20260915-os-oral-questions.md | USEFUL_CONNECT | 'That's literally the exam question': the collected oral question asks how deadlock can be prevented and which condition to break in practice. |  |  |  |
| 4 | stage:stage-os-l07-01-deadlock | UNJUDGED | Where the capture was filed: the pending OS L07 stage on deadlock conditions and detection. |  |  |  |
| 5 | workspace-os-oral-prep | UNJUDGED | The oral prep workspace whose scope includes concurrency/deadlock (L07). |  |  |  |
| 6 | note-semaphores-producer-consumer | USEFUL_CONNECT | Another ordering-caused deadlock the learner made herself (mutex before empty). |  |  |  |
| 7 | note-db-exam-cheatsheet | UNJUDGED | 2PL summary line from the (past) DB exam. |  |  |  |
| 8 | note-priority-inversion | AMBIGUOUS | The other lock pathology in the collected oral questions. |  |  |  |

## A10 — arrival:A10

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | note-query-optimizer-cost-model | MUST_CONNECT | Filed into: the same failure (independent-selectivity product) with city/zip; A10 adds make/model and extended statistics. |  |  |  |
| 2 | note-naive-bayes-spam-filter | USEFUL_CONNECT | Same independence factorization, in ML. | the same independence factorization |  |  |
| 3 | note-independence-vs-conditional-independence | USEFUL_CONNECT | Correlated columns are dependent; factorizing their joint is an independence claim. |  |  |  |
| 4 | note-db-normalization-3nf | UNJUDGED | model → make is a functional dependency — the correlation extended statistics capture. |  |  |  |
| 5 | note-selinger-join-ordering | USEFUL_CONNECT | The plan search that is misled by bad estimates. |  |  |  |
| 6 | garden:independence-assumptions-that-still-work.md | USEFUL_CONNECT | An independence assumption that does not 'still work'. |  |  |  |
| 7 | workspace-dataframe-skill | UNJUDGED | Open question: which optimizations use statistics. |  |  |  |
| 8 | project-tessera | UNJUDGED | Cost-based join ordering milestone (planned). |  |  |  |
| 9 | arrival:A01 | UNJUDGED | The BN page's joint factorization is the same move made deliberately. |  |  |  |

## A11 — arrival:A11

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | note-p-values-corrected | MUST_CONNECT | The flashcard's three statements are this note's definition and consequences, nearly word for word. | already recorded; no new durable note needed | 1 |  |
| 2 | inbox:20260903-pvalue-reminder.md | MUST_CONNECT | The same correction written after repeating the mistake in the mock. |  |  |  |
| 3 | note-p-values-first-take | USEFUL_CONNECT | The belief the card guards against. | flagged as the wrong earlier belief | 2 |  |
| 4 | note-spaced-repetition-scheduler | USEFUL_CONNECT | The card lives in the learner's review scheduler. |  |  |  |
| 5 | note-conditional-probability-basics | USEFUL_CONNECT | Swapped conditionals — the root of the error. |  |  |  |

## A12 — arrival:A12

_not answered_

## A13 — arrival:A13

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | note-amdahls-law | MUST_CONNECT | Filed into: the note already has Amdahl's formula and Gustafson's counterpoint; the excerpt adds the scaled-speedup formula. | Amdahl (sequential fraction) and Gustafson (scaled problem size) | 2 |  |
| 2 | note-parallel-workers-no-speedup | MUST_CONNECT | A measured Amdahl case: the serial CSV parse capped 16 workers at 1.6×. | the CSV parse is the sequential fraction | 2 |  |
| 3 | note-data-parallel-training-scaling | MUST_CONNECT | Non-shrinking all-reduce; bigger per-GPU batches are Gustafson-style scaling. | all-reduce/data loading don't shrink; bigger per-GPU batches is Gustafson-style scaling |  |  |
| 4 | note-data-pipeline-orchestration-dag | UNJUDGED | Parallel branches of a pipeline. |  |  |  |

## A14 — arrival:A14

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | stage:stage-df-lazy-02-read-explain | MUST_CONNECT | Filed here: plans 2 and 3 complete the stage's three annotated plans. | plans 2 and 3 complete the stage |  |  |
| 2 | note-algebraic-equivalences-pushdown | MUST_CONNECT | A14's rule ('a filter can move below an operator only if it depends on nothing that operator creates') is rule 2 generalized. | a selection can move below an operator only when it uses nothing that operator produces |  |  |
| 3 | inbox:20260910-tessera-todo.md | UNJUDGED | Tessera's filter-below-join rule 'only when predicate columns come from one side' — the same condition. |  |  |  |
| 4 | workspace-tessera-engine | USEFUL_CONNECT | Next action is exactly the filter-below-join rule; open question on pruning order. | open question: pruning before or after pushdown |  |  |
| 5 | note-lazy-evaluation-query-plans | MUST_CONNECT | Lists predicate/projection pushdown and common subplan elimination (the CACHE node). |  |  |  |
| 6 | note-constant-folding-cse | USEFUL_CONNECT | Common subexpression elimination in compilers = the CACHE of a shared subplan. | CACHE = common subexpression elimination |  |  |
| 7 | inbox:20260812-lazy-plan-explain-paste.md | MUST_CONNECT | The plan-1 paste that started this stage. | answers 'why did the filter disappear from the top' | 1 |  |
| 8 | workspace-dataframe-skill | UNJUDGED | Next action 'annotate three explain() plans' is now done in substance. |  |  |  |
| 9 | note-tagless-visitor-pattern-ast | UNJUDGED | How Tessera expresses such rules. |  |  |  |

## A15 — arrival:A15

_not answered_

## A16 — arrival:A16

_not answered_

## A17 — arrival:A17

_not answered_

## A18 — arrival:A18

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | garden:everything-is-a-dag.md | MUST_CONNECT | The same idea, captured 2026-08-07 (git, make/Bazel, Airflow, query plans, NN graphs; topological sort). | the same idea already sits in the Garden | 2 |  |
| 2 | note-build-systems-dag-incremental | USEFUL_CONNECT | Build DAGs; cycles are an error ('Circular dependency dropped'). |  |  |  |
| 3 | note-data-pipeline-orchestration-dag | USEFUL_CONNECT | Topological order; the orchestrator refuses a cyclic DAG at load time. |  |  |  |
| 4 | note-git-internals-content-addressing | USEFUL_CONNECT | Git history as a Merkle DAG. |  |  |  |
| 5 | note-backprop-as-bookkeeping | USEFUL_CONNECT | Autograd walks the computation graph in reverse topological order. |  |  |  |
| 6 | note-ssa-form | USEFUL_CONNECT | A program as a dataflow graph. |  |  |  |
| 7 | note-deadlock-four-conditions | USEFUL_CONNECT | Cycle detection in a resource-allocation graph. | cycle detection |  |  |
| 8 | note-two-phase-locking-deadlocks | USEFUL_CONNECT | Cycle detection in the waits-for graph. |  |  |  |
| 9 | arrival:A01 | UNJUDGED | Bayesian networks are DAGs too. |  |  |  |

## A19 — arrival:A19

_not answered_

## A20 — arrival:A20

_not answered_

## A21 — arrival:A21

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | stage:stage-l09-02-svd-connection | MUST_CONNECT | Filed here: the slide answers the stage's open point — variance along direction i is s_i²/(n−1), not σ_i²/n. | answers the stage's open question: variance along direction i is s_i²/(n−1) |  |  |
| 2 | note-pca-by-hand | MUST_CONNECT | The covariance-eigenvector route; the slide gives the SVD route to the same directions. |  |  |  |
| 3 | note-svd-geometric | MUST_CONNECT | AᵀA = VΣᵀΣVᵀ: right singular vectors are eigenvectors of XᵀX. |  |  |  |
| 4 | note-consistent-estimators | UNJUDGED | The 1/(n−1) vs 1/n denominators — unbiased vs biased covariance. |  |  |  |
| 5 | note-covariance-matrix | USEFUL_CONNECT | Uses Σ = (1/n)XᵀX; the slide uses n−1. |  |  |  |
| 6 | note-low-rank-approximation | USEFUL_CONNECT | Dropping small singular values = dropping low-variance directions. |  |  |  |
| 7 | workspace-statlearn-retake | USEFUL_CONNECT | Open question: is the SVD proof asked or only the PCA computation? | open question whether the SVD proof is asked |  |  |
| 8 | note-statlearn-mock-exam-september | UNJUDGED | Mock Q5: first principal component and explained variance. |  |  |  |
| 9 | stage:stage-linalg-svd-02-low-rank | UNJUDGED | Coordination: resume the SVD stage only as far as L09 needs — this slide may be most of it. |  |  |  |

## A22 — arrival:A22

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | note-forward-mode-autodiff-dual-numbers | MUST_CONNECT | Ends with exactly this: reverse mode for one output and many inputs. | forward mode: one pass per input; reverse: one per output |  |  |
| 2 | note-backprop-as-bookkeeping | MUST_CONNECT | Backprop's cost argument (one backward pass for all parameters). |  |  |  |
| 3 | note-chain-rule-multivariable | MUST_CONNECT | Multiplying the Jacobian chain from the output side is cheap when k = 1. | the order of the Jacobian product is the forward/reverse choice; answers 'remember this when we get to neural networks' | 2 |  |
| 4 | stage:stage-l11-01-backprop | UNJUDGED | Filed here (pending stage: backprop by hand). |  |  |  |

## A23 — arrival:A23

_not answered_

## A24 — arrival:A24

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|

## A25 — arrival:A25

_not answered_

## A26 — arrival:A26

_not answered_

## A27 — arrival:A27

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | note-hash-join-vs-sort-merge | MUST_CONNECT | The note whose exam summary ('hash join is always O(n + m)') this measurement refutes; correction appended there. | corrects the claim that hash join is always O(n+m); skewed keys overflow one partition and spill | 1 |  |
| 2 | stage:stage-df-joins-01-strategies | UNJUDGED | Filed here: the stage asks to measure a skewed join and explain the slowdown. |  |  |  |
| 3 | note-parallel-workers-no-speedup | USEFUL_CONNECT | Same shape: one part that cannot be split (one giant key / one CSV parse) dominates the runtime. | one partition dominates like a sequential bottleneck | 2 |  |
| 4 | note-amdahls-law | UNJUDGED | The unsplittable key is the 'serial fraction' of the join. |  |  |  |
| 5 | note-external-merge-sort | USEFUL_CONNECT | Spilling and multi-pass processing when data exceeds memory — the sort-merge alternative. |  |  |  |
| 6 | note-buffer-pool-replacement | UNJUDGED | Memory budget and spilling. |  |  |  |
| 7 | note-query-optimizer-cost-model | USEFUL_CONNECT | Skew is what uniform cardinality estimates miss. |  |  |  |
| 8 | workspace-dataframe-skill | USEFUL_CONNECT | Workspace owning the joins-at-scale unit. |  |  |  |

## A28 — arrival:A28

_not answered_

## A29 — arrival:A29

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | inbox:20260816-drf-paper-link.md | MUST_CONNECT | The identical first capture, still unprocessed in the inbox. | exact duplicate capture | 2 |  |
| 2 | note-dominant-resource-fairness-paper | MUST_CONNECT | The link was already read and written up (2026-08-17). | already read and noted on 2026-08-17 |  |  |
| 3 | note-multi-tenant-gpu-sharing | USEFUL_CONNECT | The internship-fair talk that mentioned DRF. |  |  |  |
| 4 | note-cfs-fair-share | UNJUDGED | Single-resource proportional share. |  |  |  |

## A30 — arrival:A30

_not answered_


## Judge grading notes (S10)

- expl: 0 wrong/absent, 1 partly right, 2 correct. All keyword-heuristic misses
  were human-graded; heuristic-covered rows were accepted after a 12-row
  spot-check per run found no false covers. MUST_NOT rows graded on whether
  the stated reason is factually correct (several are knowing contrasts).
- prov: 1 cited material refs resolve and support the claim; 0 no usable
  citation (no evidence, or only a discovery-method note such as a `los ...`
  command or `surfaced by:` line). Sampled rows only; see FAILURE_ANALYSIS.md.
