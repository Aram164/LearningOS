# Connection worksheet (judge)

Grade each returned relevant target: explanation 0 (wrong/absent) · 1 (partly) · 2 (correct), provenance 0/1. Oracle mentions are guidance, not wording.

## C01 — note-naive-bayes-spam-filter

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | note-independence-vs-conditional-independence | MUST_CONNECT | The naive assumption is conditional independence of words given the class; this note defines exactly that and warns that every such factorisation is an independence claim that could be false. | the naive assumption is conditional independence of the words/features given the class; it is what lets p(x/y) factor into a product | 2 |  |
| 2 | stage:stage-l05-01-derive-naive-bayes | MUST_CONNECT | Her own stage derivation of the same classifier (argmax of log prior + Σ log likelihoods, Laplace estimates) — the worked version of this note. | the stage derivation of the same classifier |  |  |
| 3 | note-generative-vs-discriminative | MUST_CONNECT | Places Naive Bayes as the generative classifier against logistic regression, with the little-data claim she is testing now. | NB is the generative model compared with logistic regression |  |  |
| 4 | stage:stage-l05-02-generative-vs-discriminative | UNJUDGED | Active stage running NB vs logistic regression on the same bag-of-words features; half-finished learning curves. |  |  |  |
| 5 | garden:independence-assumptions-that-still-work.md | USEFUL_CONNECT | Garden seed asking exactly this note's puzzle: why a plainly false assumption still classifies well. | the garden seed asks why NB works despite a false assumption |  |  |
| 6 | note-statlearn-mock-exam-september | USEFUL_CONNECT | Mock exam Q2 is a Naive Bayes spam-filter question asking for the assumption and why it is violated. |  |  | 1 |
| 7 | note-mle-coin-flips | UNJUDGED | The zero-count problem Laplace smoothing fixes (the 'Havelberg' word) is the same overconfidence of the MLE at k = 0 that this note flags. |  |  |  |
| 8 | note-query-optimizer-cost-model | USEFUL_CONNECT | Same 'multiply the per-attribute probabilities as if independent' shortcut, but in selectivity estimation it goes badly wrong — a useful contrast to 'it still works because only the ranking matters'. | both multiply per-feature/per-predicate probabilities as if independent; both break when features/columns are correlated | 2 | 1 |
| 9 | note-conditional-probability-basics | USEFUL_CONNECT | Bayes' rule, prior/likelihood/posterior and evidence — the first line of the derivation. | Bayes' rule is the starting point of the NB posterior |  |  |
| 10 | note-map-estimation-priors | UNJUDGED | Add-one smoothing can be read as a prior on the word probabilities; this note shows how a prior enters as an extra term. |  |  |  |

## C02 — note-map-estimation-priors

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | note-ridge-regression-penalty | MUST_CONNECT | Ridge is MAP with a Gaussian prior; the ridge note's open question 'where does λ come from?' is answered here (λ ∝ σ²/τ²). | a Gaussian prior on the weights gives a squared (L2) penalty; ridge = MAP with Gaussian prior; lambda corresponds to sigma²/tau² (prior strength) | 2 |  |
| 2 | note-lasso-sparsity-geometry | USEFUL_CONNECT | The Laplace-prior line of this note gives Σ/θ_j/ — the lasso penalty; read together they give the probabilistic and the geometric view of L1. | a Laplace prior gives the L1 (lasso) penalty |  |  |
| 3 | note-mle-coin-flips | USEFUL_CONNECT | MAP = MLE + log-prior; the coin note ends on the MLE's overconfidence 'fixed later with priors' — this is that fix. | MAP adds a log-prior to the MLE objective; fixes the k=0 overconfidence the coin note complains about | 2 |  |
| 4 | note-gaussian-noise-least-squares | USEFUL_CONNECT | Supplies the likelihood term this note plugs in (Gaussian noise → squared residuals). | the likelihood term is the squared error from the Gaussian-noise model |  |  |
| 5 | stage:stage-l07-01-ridge-lasso-geometry | USEFUL_CONNECT | Active L07 stage on ridge vs lasso; MAP explains both penalties and where the exact zeros come from. |  |  |  |
| 6 | note-bias-variance-from-book | USEFUL_CONNECT | Shrinking towards zero adds bias but can lower MSE — the estimator-side reason a prior helps. | shrinkage adds bias but can reduce variance |  |  |
| 7 | note-conditional-probability-basics | USEFUL_CONNECT | Prior, likelihood, posterior, evidence — the vocabulary MAP is built on. |  |  |  |
| 8 | note-statlearn-mock-exam-september | UNJUDGED | Mock exam asks when the MLE is poor (Q1) and to derive ridge (Q3) — both answered through MAP. |  |  |  |
| 9 | note-generative-vs-discriminative | UNJUDGED | Her guess that the generative model's extra assumptions 'act like a prior'. |  |  |  |
| 10 | note-naive-bayes-spam-filter | UNJUDGED | Laplace smoothing is a pseudo-count prior on word probabilities — a concrete MAP example from her own exercise. |  |  |  |

## C03 — note-parallel-workers-no-speedup

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | note-amdahls-law | MUST_CONNECT | The serial CSV parse (half the job) caps the speedup exactly as Amdahl's law predicts: p ≈ 0.5 → at most 2×. | the single-process CSV parse is the sequential fraction; speedup is bounded by 1/(1−p); with half the job sequential, at most 2× | 2 |  |
| 2 | note-data-parallel-training-scaling | USEFUL_CONNECT | Same pattern in GPU training: the part that does not shrink with more workers dominates. | the non-shrinking part (all-reduce, data loading) limits speedup the same way | 2 |  |
| 3 | note-columnar-storage-compression | USEFUL_CONNECT | Her fix was switching the export to Parquet files; this note explains what Parquet/columnar storage buys. |  |  |  |
| 4 | note-lazy-evaluation-query-plans | UNJUDGED | Same CSV-pipeline setting; reading only needed columns and pushing filters into the reader attacks the parse cost. |  |  |  |
| 5 | note-kafka-consumer-lag-backpressure | UNJUDGED | Parallelism capped by how the input is partitioned — analogous to one big CSV that cannot be split. |  |  |  |
| 6 | workspace-dataframe-skill | USEFUL_CONNECT | The workspace this pipeline work belongs to (lazy dataframe engines, debugging pipelines). |  |  |  |
| 7 | note-data-pipeline-orchestration-dag | USEFUL_CONNECT | Pipeline structure: independent branches run in parallel, serial dependencies do not. |  |  |  |

## C04 — note-cfs-fair-share

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | stage:stage-os-l02-02-proportional-share | MUST_CONNECT | Her active stage on exactly this topic; the stride example stopped at step 4 and vruntime still has to be explained aloud. | the half-finished stride example |  |  |
| 2 | note-os-scheduling-exercise-bank | MUST_CONNECT | Exercises on lottery (Q3), stride (Q4) and CFS nice values (Q5). |  |  |  |
| 3 | note-cpu-scheduling-round-robin | MUST_CONNECT | The turnaround/response-oriented policies (incl. MLFQ) that this note explicitly contrasts proportional share with. |  |  |  |
| 4 | note-multi-tenant-gpu-sharing | USEFUL_CONNECT | Weighted shares of GPU time with lending — CFS-style weighted fairness applied to an inference cluster ('weights fixed it'). | weighted shares per team is proportional-share scheduling; unused share is lent out and reclaimed; strict priority starved batch jobs | 1 |  |
| 5 | note-dominant-resource-fairness-paper | USEFUL_CONNECT | Generalises fair share from one resource (CPU) to several (CPU + memory). | DRF generalizes fair share to several resources |  |  |
| 6 | garden:fairness-for-my-study-time.md | AMBIGUOUS | Her seed idea of scheduling study time like CFS with a 'virtual study time'. |  |  |  |
| 7 | note-study-plan-retake-strategy | MUST_NOT_CONNECT | Her retake plan is a proportional-share policy (fixed 2/3 : 1/3 shares with catch-up). |  | 1 |  |
| 8 | inbox:20260915-os-oral-questions.md | USEFUL_CONNECT | Collected oral question that this note answers. |  |  |  |
| 9 | workspace-os-oral-prep | UNJUDGED | The oral-prep workspace whose next action is this stage. |  |  |  |
| 10 | note-context-switch-cost | USEFUL_CONNECT | Why CFS keeps a minimum granularity: too-short slices pay the switching cost. |  |  |  |

## C05 — note-write-ahead-logging-aries

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | note-journaling-filesystems | MUST_CONNECT | The same write-ahead rule in file systems: the journal record must be durable before the in-place write; replay committed transactions after a crash. | the journal/log record must be durable before the in-place write; after a crash, committed records are replayed/redone and uncommitted ignored |  |  |
| 2 | note-acid-consistency | USEFUL_CONNECT | WAL/ARIES is the machinery behind Atomicity and Durability in ACID. | WAL provides atomicity and durability |  |  |
| 3 | note-db-exam-cheatsheet | USEFUL_CONNECT | Her exam summary of ARIES — and her note that the recovery question was harder than expected. |  |  |  |
| 4 | garden:logs-are-the-real-database.md | MUST_CONNECT | Her seed that the log is the truth and a recovery log, event sourcing and git share one shape. |  |  |  |
| 5 | note-event-sourcing-append-only | USEFUL_CONNECT | Log as source of truth; state rebuilt by replaying — ARIES redo 'repeats history' the same way. | an append-only log from which state is rebuilt by replay |  |  |
| 6 | note-lsm-trees | USEFUL_CONNECT | LSM trees also write a log for durability before the in-memory structure is persisted. |  |  | 1 |
| 7 | note-buffer-pool-replacement | UNJUDGED | Evicting a dirty page is exactly when the WAL rule bites (steal policy). |  |  |  |
| 8 | note-two-phase-locking-deadlocks | USEFUL_CONNECT | The isolation half of transaction processing, next to this recovery half. |  |  | 1 |
| 9 | garden:ledgerline-receipt-idea.md | USEFUL_CONNECT | Append-only change records replayed to reconstruct past state — the same idea for her notes tool. |  |  |  |

## C06 — note-selinger-join-ordering

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | note-query-optimizer-cost-model | MUST_CONNECT | The cost and selectivity estimates System R's dynamic programme compares plans with. | the cost model/cardinality estimates rank the candidate plans |  |  |
| 2 | garden:why-did-swapping-from-order-matter.md | MUST_CONNECT | Her open question 'does the database reorder joins itself? based on what?' — this note is the answer. | the April question 'does the database reorder joins?' is answered by cost-based join ordering |  |  |
| 3 | note-dynamic-programming-memoization | MUST_CONNECT | Selinger's search is dynamic programming: optimal substructure over table subsets, keep the best plan per subset. | System R join enumeration is dynamic programming; best plan per subset = optimal substructure; subsets reused = overlapping subproblems | 2 | 1 |
| 4 | note-hash-join-vs-sort-merge | USEFUL_CONNECT | Join algorithms whose costs and output orders ('interesting orders' for merge join) the enumeration weighs. | interesting orders serve merge joins |  |  |
| 5 | note-algebraic-equivalences-pushdown | USEFUL_CONNECT | Commutativity/associativity of joins is what makes reordering legal; the lecture heuristic defers join order to this step. |  |  |  |
| 6 | project-tessera | USEFUL_CONNECT | Tessera's planned milestone is cost-based join ordering. |  |  |  |
| 7 | note-hmm-viterbi | USEFUL_CONNECT | Same principle of optimality: the best path into a state extends a best path into a predecessor — like the best plan per subset. | both keep only the best partial solution per state/subset | 2 |  |
| 8 | note-db-exam-cheatsheet | UNJUDGED | Her compact DB exam summary (optimizer rules) to review alongside. |  |  |  |
| 9 | note-relational-algebra-operators | UNJUDGED | Operator trees with base tables at the leaves — the left-deep trees System R restricts to. |  |  |  |

## C07 — note-query-optimizer-cost-model

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | note-selinger-join-ordering | MUST_CONNECT | The plan search that consumes these cardinality estimates. |  |  |  |
| 2 | note-independence-vs-conditional-independence | USEFUL_CONNECT | The conjunction rule assumes attribute independence; this note explains what independence claims and how they fail. | P(A,B)=P(A)P(B) only under independence; correlated columns violate it | 1 |  |
| 3 | note-db-normalization-3nf | UNJUDGED | zip → city is a functional dependency — the textbook notion that explains why the two predicates are not independent. |  |  |  |
| 4 | note-naive-bayes-spam-filter | USEFUL_CONNECT | Same product-of-marginals shortcut; there it survives because only the ranking matters — here the absolute number matters, so it fails. | the product-of-selectivities rule is the same independence assumption Naive Bayes makes | 2 |  |
| 5 | garden:independence-assumptions-that-still-work.md | USEFUL_CONNECT | Her seed asking where else a false independence simplification is built in; the cost model is a case where it does not 'still work'. |  |  |  |
| 6 | note-algebraic-equivalences-pushdown | USEFUL_CONNECT | Pushdown is justified by the same row-count reasoning (filter before join shrinks inputs). |  |  |  |
| 7 | note-hash-join-vs-sort-merge | UNJUDGED | Operator choice (build side, memory) depends on the estimated input sizes. |  |  |  |
| 8 | garden:why-did-swapping-from-order-matter.md | UNJUDGED | Her question of what the optimizer bases its decisions on. |  |  |  |
| 9 | note-lazy-evaluation-query-plans | UNJUDGED | A second optimizer she uses (Polars), rule-based rather than cost-based. |  |  |  |
| 10 | note-db-exam-cheatsheet | UNJUDGED | Her DB exam summary (optimizer section). |  |  |  |

## C08 — note-low-rank-approximation

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | note-matrix-factorization-recommenders | MUST_CONNECT | Answers this note's open question: fit the low-rank factors only on the observed ratings, so the missing entries are never needed. | answers the open question about recommenders; fit P Qᵀ only on observed ratings, so missing entries are never needed |  |  |
| 2 | note-svd-geometric | MUST_CONNECT | The SVD itself — singular values and vectors that the rank-k truncation keeps. |  |  |  |
| 3 | stage:stage-linalg-svd-02-low-rank | MUST_CONNECT | The paused stage holding this experiment: rank 5 done, ranks 20 and 50 still open. | rank 5 done, 20/50 not |  |  |
| 4 | stage:stage-l09-02-svd-connection | USEFUL_CONNECT | PCA↔SVD stage stopped at why singular values relate to explained variance — the same Σσ² that gives the Eckart–Young error. |  |  |  |
| 5 | workspace-linalg-refresh | USEFUL_CONNECT | Workspace whose next action is finishing this image-compression experiment. |  |  |  |
| 6 | note-pca-by-hand | USEFUL_CONNECT | PCA keeps the top components — a low-rank projection keeping 93% of the variance. | PCA keeps the top components — a truncated SVD |  |  |
| 7 | note-eigenvectors-intuition | USEFUL_CONNECT | Eigen-decomposition background the SVD note builds on. |  |  |  |
| 8 | note-covariance-matrix | USEFUL_CONNECT | Spectral picture of the covariance matrix used by PCA. |  |  |  |

## C09 — note-data-lineage-debugging

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | note-why-provenance-paper | MUST_CONNECT | Formalises 'which input rows justify this output row' (why-provenance); a join witness has one tuple from each side — exactly her duplicated device rows. | 'which input rows produced this output row' is why-provenance; a join output's witness has one tuple per side — fan-out duplicates |  |  |
| 2 | stage:stage-df-lineage-01-trace | UNJUDGED | Pending stage whose objective is this very exercise. |  |  |  |
| 3 | workspace-dataframe-skill | USEFUL_CONNECT | Workspace objective includes debugging wrong results in multi-step pipelines; lists this note. |  |  |  |
| 4 | note-idempotent-pipelines-backfills | AMBIGUOUS | Another silently doubled aggregate in a pipeline (retry + INSERT) — same failure family, different cause. |  |  |  |
| 5 | note-relational-algebra-operators | UNJUDGED | Set vs bag semantics: SQL keeps duplicates unless DISTINCT — why COUNT(*) double-counted after the join. |  |  |  |
| 6 | note-data-pipeline-orchestration-dag | USEFUL_CONNECT | The pipeline as a DAG of steps she walked backwards through. |  |  | 1 |
| 7 | note-event-sourcing-append-only | AMBIGUOUS | Keeping history so you can answer 'how did we get here?' — a lineage-friendly design. |  |  |  |

## C10 — note-kv-cache-transformer-serving

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | garden:attention-as-soft-lookup.md | MUST_CONNECT | Her seed asking whether the KV cache is literally a cache of attention's key→value dictionary. |  |  |  |
| 2 | note-dynamic-batching-inference | MUST_CONNECT | KV memory per sequence limits how many requests fit in a batch — the batching side of the same serving problem. | KV memory limits how many requests fit in a batch |  |  |
| 3 | note-virtual-memory-address-translation | USEFUL_CONNECT | The fragmentation problem (unknown final length, gaps between sequences) is what paging solves: non-contiguous frames behind a page table. | the reserve-vs-grow fragmentation problem is what paging solves in an OS |  |  |
| 4 | note-multi-tenant-gpu-sharing | USEFUL_CONNECT | GPU memory as the binding resource in serving. |  |  |  |
| 5 | note-softmax-temperature | UNJUDGED | Attention weights are a softmax; the same note covers sampling from language models. |  |  |  |
| 6 | note-caching-everywhere | AMBIGUOUS | Her 'same cache idea in three courses' note — the KV cache is a fourth instance. |  |  |  |
| 7 | note-buffer-pool-replacement | UNJUDGED | Frames plus a page table managing a fixed memory pool — the design pattern paged KV memory borrows. |  |  |  |
| 8 | note-mixed-precision-training | USEFUL_CONNECT | Bytes per value (fp16/bf16) set the KV-cache size formula. |  |  | 1 |

## C11 — note-os-kernel-user-mode

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | note-virtual-memory-address-translation | USEFUL_CONNECT | Page tables are changed only in kernel mode, and a page fault is a trap into the kernel. | page tables are changed only in kernel mode; page faults trap into the kernel |  |  |
| 2 | note-context-switch-cost | MUST_CONNECT | Quantifies the mode/process switch and cache/TLB pollution this note blames for system-call cost. | mode switches and cache/TLB pollution make kernel entry expensive |  |  |
| 3 | inbox:20260915-os-oral-questions.md | USEFUL_CONNECT | Oral questions (page fault, TLB on context switch, process vs thread) that build on kernel/user mode. |  |  |  |
| 4 | garden:kernel-is-an-overloaded-word.md | USEFUL_CONNECT | Disambiguates 'kernel': the OS kernel is unrelated to the SVM, convolution and KDE kernels that keyword search returns. | as a disambiguation, not an equivalence |  |  |
| 5 | workspace-os-oral-prep | UNJUDGED | The OS oral-prep workspace this topic feeds. |  |  |  |
| 6 | stage:stage-os-l05-01-translation | UNJUDGED | Pending stage walking an address through page tables and the TLB — kernel-managed structures. |  |  |  |
| 7 | note-cpu-cache-locality | UNJUDGED | Cache behaviour behind the 'cache and TLB pollution' cost of a system call. |  |  |  |

## C12 — note-db-normalization-3nf

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | note-db-exam-cheatsheet | MUST_CONNECT | Her exam sheet's BCNF test. |  |  |  |
| 2 | note-relational-algebra-operators | USEFUL_CONNECT | Natural join/projection — the operators behind lossless-join decomposition. | decomposition uses projection; lossless-join uses natural join |  |  |
| 3 | note-query-optimizer-cost-model | UNJUDGED | zip → city is a functional dependency; it is why the optimizer's independence assumption fails. |  |  |  |
| 4 | note-acid-consistency | USEFUL_CONNECT | Declared keys and constraints are what the database enforces for C. |  |  |  |
| 5 | note-data-lineage-debugging | UNJUDGED | A one-to-many device table duplicated rows after a join — the kind of redundancy normalization reasons about. |  |  |  |

## C13 — note-acid-consistency

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | note-cap-consistency-linearizability | MUST_CONNECT | Explicitly contrasts CAP consistency (linearizability) with this ACID C. | CAP consistency (linearizability) is a different property from ACID consistency (invariants) |  |  |
| 2 | note-two-phase-locking-deadlocks | USEFUL_CONNECT | The I in ACID: how serializability is actually enforced. |  |  |  |
| 3 | note-write-ahead-logging-aries | USEFUL_CONNECT | The A and D in ACID: logging and recovery. |  |  |  |
| 4 | note-db-exam-cheatsheet | UNJUDGED | Her DB exam summary covering 2PL and ARIES. |  |  |  |
| 5 | note-db-normalization-3nf | USEFUL_CONNECT | Keys and dependencies — the integrity constraints C is defined over. |  |  |  |
| 6 | note-journaling-filesystems | AMBIGUOUS | Crash consistency in file systems: keeping on-disk structures consistent across a crash. |  |  |  |

## C14 — note-spaced-repetition-scheduler

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | note-study-plan-retake-strategy | USEFUL_CONNECT | Her other study-scheduling rules (shares, catch-up first) next to the review scheduler's. |  |  |  |
| 2 | note-pomodoro-and-context-switching | USEFUL_CONNECT | Her own evidence on how study sessions should be sized and switched. |  |  |  |
| 3 | inbox:20260916-sleep-podcast.md | USEFUL_CONNECT | Memory-consolidation capture relevant to when to review. |  |  |  |
| 4 | note-how-i-take-notes | USEFUL_CONNECT | Her note-taking rules — pairs with 'write cards myself'. |  |  |  |
| 5 | garden:fairness-for-my-study-time.md | UNJUDGED | Seed idea for a scheduler over subjects (CFS-style) — the same 'let an algorithm pick what to study' move. |  |  |  |
| 6 | note-oral-exam-prep-strategy | UNJUDGED | Retrieval practice for the oral (practise out loud, listen back). |  |  |  |
| 7 | note-queueing-littles-law | UNJUDGED | 'The backlog grows faster than you think' is a queue whose arrivals outpace service; Little's law relates queue length to delay. |  |  |  |
| 8 | note-kafka-consumer-lag-backpressure | UNJUDGED | Same arithmetic as a review backlog: if cards arrive faster than you review, lag grows without bound. |  |  |  |
| 9 | note-weekly-review-log | UNJUDGED | Her weekly log of what actually got studied. |  |  | 1 |

## C15 — note-buffer-pool-replacement

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | note-page-replacement-lru-clock | MUST_CONNECT | The OS version of the same eviction problem; LRU's worst case (looping over a set one page too large) is sequential flooding. | the same eviction problem in the OS; LRU fails when a scan/loop is larger than memory (sequential flooding) |  |  |
| 2 | note-caching-everywhere | MUST_CONNECT | Her cross-course note naming the buffer pool as one of three instances of the same cache idea. |  |  |  |
| 3 | stage:stage-os-l05-02-replacement | UNJUDGED | Pending stage simulating LRU and clock on a reference string. |  |  |  |
| 4 | note-cpu-cache-locality | USEFUL_CONNECT | Temporal/spatial locality — the assumption LRU relies on and scans violate. |  |  |  |
| 5 | note-write-ahead-logging-aries | UNJUDGED | Writing back a dirty victim before commit (steal) is what forces WAL and undo. |  |  |  |
| 6 | note-virtual-memory-address-translation | USEFUL_CONNECT | Page tables mapping pages to frames — the OS mechanism the DB bypasses with its own pool. |  |  |  |
| 7 | note-external-merge-sort | USEFUL_CONNECT | Sorting with B buffer pages — a buffer-pool consumer with a sequential access pattern. |  |  |  |
| 8 | note-b-plus-tree-indexes | USEFUL_CONNECT | Why index lookups are cheap: the top levels stay cached in the pool. |  |  |  |

## C16 — note-p-values-corrected

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | note-p-values-first-take | MUST_CONNECT | Her April version with the exact misconception this note corrects. | the April note is the wrong earlier belief that this note corrects | 2 |  |
| 2 | inbox:20260903-pvalue-reminder.md | MUST_CONNECT | She made the same mistake again in the mock — unrouted reminder that belongs next to this note. | the misconception recurred in September | 2 |  |
| 3 | note-conditional-probability-basics | USEFUL_CONNECT | Same swapped-conditional error as the disease-test trap: P(H0 / data) vs P(data / H0). | confusing P(data/H0) with P(H0/data) is the swapped-conditional trap |  |  |
| 4 | note-normal-distribution-standardizing | UNJUDGED | z-scores and normal tail probabilities used to compute p-values. |  |  |  |
| 5 | note-central-limit-theorem-simulation | USEFUL_CONNECT | Why test statistics of means are approximately normal. |  |  |  |
| 6 | note-map-estimation-priors | UNJUDGED | Getting P(H0 / data) needs a prior — the Bayesian side this note says a frequentist test never uses. |  |  |  |

## C17 — note-gradient-descent-from-scratch

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | note-normal-distribution-standardizing | USEFUL_CONNECT | The fix she found (standardize every feature) is this z-score move, with the same m² vs rooms example. | standardizing features fixed the divergence |  |  |
| 2 | note-sgd-momentum-nn-training | MUST_CONNECT | Same update rule on minibatches; momentum cancels the zig-zag across a narrow valley. | same update rule with a minibatch gradient and momentum |  |  |
| 3 | note-linear-regression-normal-equation | MUST_CONNECT | The closed-form solution of the same least-squares problem; explains when the iterative version is needed. | closed form vs iterative |  |  |
| 4 | note-convexity-basics | USEFUL_CONNECT | Squared error of a linear model is convex, so gradient descent reaches the global minimum. | squared error is convex, so descent finds the global minimum |  |  |
| 5 | note-regression-metrics | USEFUL_CONNECT | Metrics from the same housing regression. |  |  | 1 |
| 6 | note-adam-vs-sgd-revisited | USEFUL_CONNECT | Learning-rate sensitivity and adaptive per-parameter steps (Adam) versus SGD. |  |  |  |
| 7 | note-data-leakage-scaler | UNJUDGED | Caveat for the standardization fix: fit the scaler inside each training fold. |  |  |  |
| 8 | note-batchnorm-why-it-works-contested | UNJUDGED | Normalization smoothing the loss landscape so larger steps are safe — the same scaling story inside networks. |  |  |  |

## C18 — note-dynamic-batching-inference

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | note-kv-cache-transformer-serving | USEFUL_CONNECT | KV-cache memory limits how many requests fit in a batch. |  |  |  |
| 2 | note-multi-tenant-gpu-sharing | MUST_CONNECT | Interactive vs batch traffic on shared serving GPUs — the latency side of the trade-off. |  |  |  |
| 3 | note-queueing-littles-law | USEFUL_CONNECT | Requests waiting in the batching queue: Little's law ties queue length, arrival rate and waiting time. | requests waiting in the queue relate arrival rate and waiting time (L = λW) |  |  |
| 4 | note-cpu-scheduling-round-robin | UNJUDGED | The same responsiveness-vs-overhead trade-off as choosing a round-robin quantum. |  |  |  |
| 5 | note-kafka-consumer-lag-backpressure | USEFUL_CONNECT | Throughput vs arrival rate and bounded buffers pushing back. |  |  |  |
| 6 | note-semaphores-producer-consumer | UNJUDGED | Bounded buffer between producers and consumers — the queue in front of the batcher. |  |  |  |
| 7 | note-data-parallel-training-scaling | UNJUDGED | Bigger batches help throughput until something else (accuracy) suffers. |  |  |  |
| 8 | note-context-switch-cost | UNJUDGED | Amortising a fixed per-step cost over more work. |  |  |  |

## C19 — note-softmax-temperature

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | garden:temperature-everywhere.md | MUST_CONNECT | Her seed noticing softmax temperature and annealing temperature are both exp(·/T). |  |  | 1 |
| 2 | note-simulated-annealing | USEFUL_CONNECT | The other temperature: accept worse moves with exp(−ΔE/T); high T accepts almost anything, low T is greedy — same flatten/sharpen behaviour. | both are exp(−E/T) Boltzmann forms; T→0 becomes greedy/argmax | 2 |  |
| 3 | note-logistic-regression-cross-entropy | USEFUL_CONNECT | The sigmoid/cross-entropy pair is the two-class softmax. |  |  |  |
| 4 | garden:attention-as-soft-lookup.md | UNJUDGED | Attention turns scores into weights with a softmax. |  |  |  |
| 5 | note-kernel-density-estimation | UNJUDGED | Bandwidth h plays the same smoothing role as T (small → spiky, large → one blob). |  |  |  |
| 6 | note-kv-cache-transformer-serving | UNJUDGED | Language-model generation, where temperature sampling happens. |  |  |  |

## C20 — note-constant-folding-cse

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | note-tagless-visitor-pattern-ast | MUST_CONNECT | Tessera's optimizer does the same rewrites on plans: fold `1 = 1` to true, drop Filter(true), iterate to a fixed point with a pass cap. | Tessera's rules fold constants and iterate to a fixed point with a pass cap |  |  |
| 2 | note-algebraic-equivalences-pushdown | USEFUL_CONNECT | Meaning-preserving rewrite rules for query plans — the relational analogue. | both rewrite a tree with meaning-preserving equivalences |  |  |
| 3 | note-lazy-evaluation-query-plans | USEFUL_CONNECT | Polars' optimizer lists common subplan elimination and expression simplification — CSE and folding on query plans. | common subplan elimination / expression simplification |  |  |
| 4 | note-ssa-form | MUST_CONNECT | SSA makes CSE and constant propagation simple passes. |  |  |  |
| 5 | inbox:20260910-tessera-todo.md | USEFUL_CONNECT | Her Tessera todo: constant folding done; worry that rules fight and never reach a fixed point. | rules fighting each other / termination |  |  |
| 6 | note-property-based-testing | USEFUL_CONNECT | Testing the rewrite contract directly: execute(optimize(q)) == execute(q). | execute(optimize(q)) == execute(q) checks meaning preservation |  |  |
| 7 | note-compiler-pipeline-overview | MUST_CONNECT | Where optimization passes sit in the compiler pipeline. |  |  | 1 |
| 8 | workspace-tessera-engine | USEFUL_CONNECT | Workspace building a rule-based optimizer for Tessera's plans. |  |  |  |
| 9 | note-regression-testing-snapshots | UNJUDGED | Snapshotting the printed optimized plans guards the rewrites. |  |  |  |
| 10 | project-tessera | UNJUDGED | The project whose rule-based optimizer milestone this feeds. |  |  |  |

## A01 — arrival:A01

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | note-naive-bayes-spam-filter | MUST_CONNECT | The 'single class node with arrows to every feature node' she half-recognises is Naive Bayes: the graph encodes exactly the per-word factorisation in this note. | the class node with arrows to every feature is Naive Bayes; answers the '??? recognize this' line | 2 |  |
| 2 | note-independence-vs-conditional-independence | MUST_CONNECT | Conditional independence and 'explaining away' — the two ideas the page leans on — are already worked out here. | a node is independent of its non-descendants given its parents; explaining away appears in both | 1 |  |
| 3 | stage:stage-l05-01-derive-naive-bayes | UNJUDGED | Her derivation of the same factorisation p(x / y) = Π_j p(x_j / y), i.e. the class-node network. |  |  |  |
| 4 | note-generative-vs-discriminative | USEFUL_CONNECT | A Bayesian network over class and features is a generative model p(x / y) p(y). |  |  |  |
| 5 | garden:independence-assumptions-that-still-work.md | USEFUL_CONNECT | Seed about the false-but-useful independence assumption that the graph makes explicit. |  |  |  |
| 6 | note-hmm-viterbi | USEFUL_CONNECT | An HMM is another directed graphical model (a chain of hidden states with emissions). | an HMM is a Bayesian network over a chain | 2 |  |
| 7 | note-conditional-probability-basics | USEFUL_CONNECT | Bayes' rule and the law of total probability used to read the factorised joint. |  |  |  |
| 8 | note-statlearn-mock-exam-september | UNJUDGED | Mock Q2 asks for the Naive Bayes assumption — now expressible as the graph structure. |  |  |  |
| 9 | garden:everything-is-a-dag.md | AMBIGUOUS | Another DAG for her 'everything is a DAG' collection. |  |  |  |

## A02 — arrival:A02

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | stage:stage-l07-01-ridge-lasso-geometry | MUST_CONNECT | Written in this stage; answers its open question about a 1-D lasso solvable by hand. | the stage asked for a 1-D version by hand |  |  |
| 2 | note-ridge-regression-penalty | MUST_CONNECT | Answers the ridge note's open question why ridge has a closed form and the lasso needs special solvers. | answers why ridge has a closed form and lasso does not (piecewise/soft-thresholding) |  |  |
| 3 | note-lasso-sparsity-geometry | MUST_CONNECT | The geometric explanation of the same exact zeros; soft thresholding is the algebraic one. | algebraic (soft-thresholding) counterpart of the diamond-corner picture | 2 |  |
| 4 | note-map-estimation-priors | USEFUL_CONNECT | The λ/w/ term is a Laplace prior; this note shows where it comes from. | Laplace prior |  |  |
| 5 | workspace-statlearn-retake | USEFUL_CONNECT | Retake workspace; its next action is the L07 ridge/lasso stage. |  |  |  |
| 6 | note-statlearn-mock-exam-september | UNJUDGED | Mock Q3 (ridge estimator) — the 1-D comparison with ridge is exam material. |  |  |  |
| 7 | note-convexity-basics | USEFUL_CONNECT | The lasso objective is convex but not differentiable at 0 — why the minimum can sit at the kink. |  |  |  |

## A03 — arrival:A03

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | inbox:20260910-tessera-todo.md | MUST_CONNECT | Ticks off three of her open Tessera todos: filter-below-join, projection pruning, and the property test. | two todo items are now done | 1 | 1 |
| 2 | workspace-tessera-engine | MUST_CONNECT | The workspace whose next action is exactly this rule plus result-comparison tests. | it was the recorded next action |  |  |
| 3 | note-algebraic-equivalences-pushdown | MUST_CONNECT | The relational-algebra law the rule implements. | the implemented rule is σ_p(R ⋈ S) = σ_p(R) ⋈ S when p only uses R's attributes |  |  |
| 4 | note-property-based-testing | MUST_CONNECT | The property she has now implemented, and which immediately found a bug. |  |  |  |
| 5 | note-tagless-visitor-pattern-ast | MUST_CONNECT | Tessera's rule framework the new rule plugs into. |  |  |  |
| 6 | project-tessera | MUST_CONNECT | The active optimizer milestone of the project. |  |  |  |
| 7 | note-lazy-evaluation-query-plans | MUST_CONNECT | Polars does the same predicate and projection pushdown. | predicate pushdown in the lazy engine |  |  |
| 8 | note-regression-testing-snapshots | USEFUL_CONNECT | Her snapshot tests of optimized plans will change with the new rule (7 → 5 operators). |  |  |  |
| 9 | stage:stage-df-lazy-02-read-explain | USEFUL_CONNECT | She observed the same filter move in Polars' explain() output. |  |  |  |

## A04 — arrival:A04

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | note-kv-cache-transformer-serving | MUST_CONNECT | The fragmentation problem PagedAttention solves (unknown length, more than half of KV memory wasted). | PagedAttention solves the reserve-vs-fragment waste that note describes |  |  |
| 2 | note-virtual-memory-address-translation | MUST_CONNECT | The answer to 'where have I seen block tables before?': page tables mapping virtual pages to non-contiguous frames, plus copy-on-write sharing. | the block table is a page table; non-contiguous fixed-size blocks, on-demand allocation, copy-on-write sharing |  |  |
| 3 | garden:attention-as-soft-lookup.md | USEFUL_CONNECT | Her seed wondering what exactly the KV cache caches. |  |  |  |
| 4 | stage:stage-os-l05-01-translation | UNJUDGED | The pending VM stage on page-table walks — the OS side of the same mechanism. |  |  |  |
| 5 | note-buffer-pool-replacement | UNJUDGED | Another fixed pool of frames with a page table mapping ids to frames. |  |  |  |
| 6 | note-dynamic-batching-inference | USEFUL_CONNECT | Less KV waste means bigger batches — the serving payoff. |  |  |  |
| 7 | arrival:A30 | UNJUDGED | Another new capture asking what the server keeps in memory between steps — same topic, file together. |  |  |  |
| 8 | arrival:A20 | UNJUDGED | New stage draft on page-table walks and TLBs — the block-table analogue. |  |  |  |

## A05 — arrival:A05

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | note-data-lineage-debugging | MUST_CONNECT | The first join fan-out ('second time ... bitten me'): same walk-back with row counts, same duplicated rows. | same join fan-out bug and same step-by-step row-count method | 2 |  |
| 2 | stage:stage-df-lineage-01-trace | UNJUDGED | Pending stage whose objective this page already carries out. |  |  |  |
| 3 | note-why-provenance-paper | USEFUL_CONNECT | Why-provenance: which input tuples justify an output tuple — the two matching 'N' rows. |  |  |  |
| 4 | workspace-dataframe-skill | USEFUL_CONNECT | Workspace on debugging wrong results in multi-step pipelines. |  |  |  |
| 5 | note-relational-algebra-operators | UNJUDGED | Bag semantics: joins keep duplicates unless removed. |  |  |  |
| 6 | note-db-normalization-3nf | AMBIGUOUS | The fix (uniqueness on the dimension key) is a key constraint; the duplicate region row is an update anomaly. |  |  |  |
| 7 | note-idempotent-pipelines-backfills | AMBIGUOUS | Another silently doubled aggregate in a pipeline. |  |  |  |

## A06 — arrival:A06

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | workspace-ledgerline | MUST_CONNECT | This is the deliverable of the Ledgerline workspace (receipt format before code) — but the workspace is blocked until after the exams. | answers 'full text or diff?' | 1 |  |
| 2 | garden:ledgerline-receipt-idea.md | MUST_CONNECT | The seed idea this v0 format makes concrete. |  |  |  |
| 3 | project-ledgerline | MUST_CONNECT | Project record, including her decision to pause Ledgerline until after the October exams. | the project is paused by a recorded decision |  |  |
| 4 | note-event-sourcing-append-only | MUST_CONNECT | Current text = replay of receipts, with periodic snapshots — event sourcing. | append-only receipts with state rebuilt by replay is event sourcing |  |  |
| 5 | note-git-internals-content-addressing | USEFUL_CONNECT | Hash-chained history and 'recompute the hash' integrity checking. | hash chain with parent pointers, integrity by recomputing hashes |  |  |
| 6 | garden:logs-are-the-real-database.md | USEFUL_CONNECT | Log-is-the-truth seed tagged #ledgerline. |  |  |  |
| 7 | note-write-ahead-logging-aries | USEFUL_CONNECT | Log records with sequence numbers and replay — the database version of receipts. |  |  |  |
| 8 | arrival:A23 | UNJUDGED | The other new Ledgerline design note (duplicate receipts on retry). |  |  |  |

## A07 — arrival:A07

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | stage:stage-os-l02-02-proportional-share | MUST_CONNECT | Read for this stage; the stride example there stopped at step 4. | the stride example stopped at step 4 |  |  |
| 2 | note-cfs-fair-share | MUST_CONNECT | Her note already names stride as the deterministic lottery; this excerpt gives the error bound that makes that precise. |  |  |  |
| 3 | note-os-scheduling-exercise-bank | MUST_CONNECT | Exercises Q3 (lottery short-run unfairness) and Q4 (stride decisions). |  |  |  |
| 4 | workspace-os-oral-prep | UNJUDGED | Oral-prep workspace whose next action is a stride example by hand. |  |  |  |
| 5 | inbox:20260915-os-oral-questions.md | UNJUDGED | [REDACTED by S10 judge: reason text matches an oracle sentence covered by the H5 adjudication for connections.jsonl only; see leak-adjudications.json — worksheet must not repeat it] |  |  |  |
| 6 | note-cpu-scheduling-round-robin | USEFUL_CONNECT | The other policy family for comparison. |  |  |  |

## A08 — arrival:A08

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | note-dynamic-batching-inference | MUST_CONNECT | Her batching trade-off note; this experiment measures it (throughput up, p99 up). | max_batch/max_wait trade throughput for latency |  |  |
| 2 | note-multi-tenant-gpu-sharing | MUST_CONNECT | Same starvation story at cluster scale: one heavy client starves another; weights/fair shares fix it. | the small client starves behind the big one; per-client queues/weights fix it | 2 |  |
| 3 | note-cpu-scheduling-round-robin | USEFUL_CONNECT | B stuck behind A's full batches is the convoy effect; per-client queues served in turn is round robin. |  |  |  |
| 4 | note-cfs-fair-share | USEFUL_CONNECT | Per-client fairness as a proportional-share scheduling problem. | serving per-client queues in turn is fair-share/round-robin scheduling | 2 |  |
| 5 | note-dominant-resource-fairness-paper | USEFUL_CONNECT | Fair allocation between users of a shared cluster. |  |  |  |
| 6 | note-queueing-littles-law | USEFUL_CONNECT | Queueing view of the latency numbers. |  |  |  |
| 7 | note-kv-cache-transformer-serving | UNJUDGED | Other serving constraint on batch size (for generative models). |  |  |  |

## A09 — arrival:A09

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | note-two-phase-locking-deadlocks | MUST_CONNECT | The same database deadlock: T1 locks A then B, T2 B then A; the DB detects the waits-for cycle and aborts a victim. | waits-for cycle; the DB aborts a victim |  |  |
| 2 | note-deadlock-four-conditions | MUST_CONNECT | 'Always touch tables in the same order' is breaking circular wait with a global lock order. | a fixed lock order breaks circular wait |  |  |
| 3 | inbox:20260915-os-oral-questions.md | USEFUL_CONNECT | 'That's literally the exam question' — it is in her collected oral questions. |  |  |  |
| 4 | stage:stage-os-l07-01-deadlock | UNJUDGED | Pending deadlock stage (conditions and cycle detection). |  |  |  |
| 5 | workspace-os-oral-prep | UNJUDGED | Oral-prep workspace covering deadlock. |  |  |  |
| 6 | note-semaphores-producer-consumer | USEFUL_CONNECT | Her own lock-ordering deadlock (mutex before empty). |  |  |  |
| 7 | note-db-exam-cheatsheet | UNJUDGED | DB exam summary of 2PL. |  |  |  |

## A10 — arrival:A10

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | note-query-optimizer-cost-model | MUST_CONNECT | Same lesson with her own example (city/zip): multiplying selectivities as if independent underestimates; same remedies (multi-column stats, sampling). |  |  |  |
| 2 | note-independence-vs-conditional-independence | USEFUL_CONNECT | What the independence assumption claims, and why correlated columns violate it. |  |  |  |
| 3 | note-selinger-join-ordering | USEFUL_CONNECT | The plan search these bad estimates mislead. |  |  |  |
| 4 | note-naive-bayes-spam-filter | USEFUL_CONNECT | The same product-of-marginals shortcut, which survives in Naive Bayes because only the ranking matters. | the same independence factorization | 2 |  |
| 5 | garden:independence-assumptions-that-still-work.md | USEFUL_CONNECT | Seed asking where else a false independence simplification is used — here it does not 'still work'. |  |  |  |
| 6 | note-db-normalization-3nf | UNJUDGED | model → make is a functional dependency, the formal reason the columns are not independent. |  |  |  |
| 7 | garden:why-did-swapping-from-order-matter.md | UNJUDGED | Her question about what the optimizer bases its decisions on. |  |  |  |

## A11 — arrival:A11

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | note-p-values-corrected | MUST_CONNECT | The card restates this note's corrected definition almost word for word. | already recorded; no new durable note needed | 1 |  |
| 2 | inbox:20260903-pvalue-reminder.md | MUST_CONNECT | Earlier capture of the same correction after repeating the mistake in the mock. |  |  |  |
| 3 | note-p-values-first-take | USEFUL_CONNECT | The superseded misconception the card is written to prevent. | flagged as the wrong earlier belief | 2 |  |
| 4 | note-spaced-repetition-scheduler | USEFUL_CONNECT | The card lives in her flashcard system; its review rules apply. |  |  |  |
| 5 | note-conditional-probability-basics | USEFUL_CONNECT | Same swapped-conditional trap (P(A / B) vs P(B / A)). |  |  |  |

## A12 — arrival:A12

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | note-hmm-viterbi | MUST_CONNECT | The algorithm this exercise applies (δ recursion with backpointers). |  |  |  |
| 2 | note-markov-chains-stationary | USEFUL_CONNECT | The hidden weather chain; her weather toy Markov chain. |  |  |  |
| 3 | note-dynamic-programming-memoization | USEFUL_CONNECT | Viterbi is dynamic programming (table fill + path back). | the δ table is a DP table |  |  |
| 4 | workspace-statlearn-retake | USEFUL_CONNECT | Statistical Learning retake workspace (bonus exercise). |  |  |  |

## A13 — arrival:A13

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | note-amdahls-law | MUST_CONNECT | Her Amdahl note already includes Gustafson's counterpoint; the excerpt adds the scaled-speedup formula. | Amdahl (sequential fraction) and Gustafson (scaled problem size) | 2 |  |
| 2 | note-parallel-workers-no-speedup | MUST_CONNECT | Her own 16-worker job capped by a serial parse — the sequential fraction s in practice. | the CSV parse is the sequential fraction |  |  |
| 3 | note-data-parallel-training-scaling | MUST_CONNECT | Scaling the per-GPU batch is Gustafson-style scaling of the problem with the machine. | all-reduce/data loading don't shrink; bigger per-GPU batches is Gustafson-style scaling |  |  |

## A14 — arrival:A14

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | stage:stage-df-lazy-02-read-explain | MUST_CONNECT | Written in this stage; completes its 'Plans 2 and 3 still to do'. | plans 2 and 3 complete the stage |  |  |
| 2 | workspace-dataframe-skill | UNJUDGED | Workspace next action: annotate three explain() plans. |  |  |  |
| 3 | note-lazy-evaluation-query-plans | MUST_CONNECT | Names the optimizations seen here: predicate/projection pushdown and common subplan elimination (the CACHE node). |  |  |  |
| 4 | inbox:20260812-lazy-plan-explain-paste.md | MUST_CONNECT | Plan 1's pasted explain() output with her question about the vanished filter — answered by the rule she now states. | answers 'why did the filter disappear from the top' |  |  |
| 5 | note-algebraic-equivalences-pushdown | MUST_CONNECT | The algebraic rule behind 'a filter can move below an operator only if it depends on nothing that operator creates'. | a selection can move below an operator only when it uses nothing that operator produces |  |  |
| 6 | note-constant-folding-cse | USEFUL_CONNECT | The CACHE node is common subexpression elimination on plans. | CACHE = common subexpression elimination |  |  |
| 7 | inbox:20260910-tessera-todo.md | UNJUDGED | Tessera needs the same filter-below-join and projection-pruning rules. |  |  |  |
| 8 | arrival:A03 | UNJUDGED | New Tessera log implementing the same pushdown rule. |  |  |  |

## A15 — arrival:A15

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | garden:temperature-everywhere.md | MUST_CONNECT | Answers her seed's question: yes, softmax and annealing share the Boltzmann exp(−E/T) form. | answers the seed's 'coincidence or same physics?' |  |  |
| 2 | note-softmax-temperature | MUST_CONNECT | Her softmax-temperature note (flattening/sharpening, T → 0 argmax). |  |  |  |
| 3 | note-simulated-annealing | MUST_CONNECT | The Metropolis acceptance rule exp(−ΔE/T) the capture refers to. | exp(−ΔE/T) acceptance has the same Boltzmann form | 2 |  |
| 4 | note-markov-chains-stationary | AMBIGUOUS | Metropolis is a Markov chain whose stationary distribution is the Boltzmann distribution. |  |  |  |

## A16 — arrival:A16

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | note-batchnorm-internal-covariate-shift | MUST_CONNECT | Her batch-norm note says to use running averages at test time — the step she forgot. | use running averages at test time |  |  |
| 2 | note-normal-distribution-standardizing | USEFUL_CONNECT | The z-score with fixed parameters she compares eval-mode batch norm to. | standardizing with fixed population parameters, like a z-score |  |  |
| 3 | note-data-leakage-scaler | USEFUL_CONNECT | Same principle: normalisation statistics are fitted parameters of the model, not recomputed on evaluation data. | which data's statistics the normalizer uses |  |  |
| 4 | note-batchnorm-why-it-works-contested | USEFUL_CONNECT | The other batch-norm note (mechanics vs contested explanation). |  |  |  |
| 5 | stage:stage-l11-02-optimizers-and-normalization | UNJUDGED | Pending L11 stage covering batch normalization. |  |  |  |
| 6 | inbox:20260914-batchnorm-forum-question.md | USEFUL_CONNECT | Open batch-norm question to check before the exam. |  |  |  |
| 7 | note-cnn-convolution-kernels | USEFUL_CONNECT | Her CNN note (the model being debugged). |  |  |  |

## A17 — arrival:A17

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | note-cap-consistency-linearizability | MUST_CONNECT | Answers the question directly: CAP consistency is linearizability, not the ACID C. | no: linearizability vs invariants |  |  |
| 2 | note-acid-consistency | MUST_CONNECT | What the ACID C actually means (invariants, mostly the application's job). |  |  |  |
| 3 | note-two-phase-locking-deadlocks | UNJUDGED | Serializability (the I in ACID) — often confused with linearizability; useful contrast. |  |  |  |

## A18 — arrival:A18

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | garden:everything-is-a-dag.md | MUST_CONNECT | The same thought already planted in the Garden (git, make/Bazel, Airflow, query plans, NN graphs; topological sort). | the same idea already sits in the Garden |  |  |
| 2 | note-build-systems-dag-incremental | USEFUL_CONNECT | Build DAGs, topological scheduling, and cycles as errors. |  |  |  |
| 3 | note-data-pipeline-orchestration-dag | USEFUL_CONNECT | Airflow DAGs: topological order, refusing cycles at load time. |  |  |  |
| 4 | note-git-internals-content-addressing | USEFUL_CONNECT | Git history as a Merkle DAG. |  |  |  |
| 5 | note-backprop-as-bookkeeping | USEFUL_CONNECT | Autograd: walking the computation graph in reverse. |  |  |  |
| 6 | note-deadlock-four-conditions | USEFUL_CONNECT | Cycle detection on a resource-allocation graph. | cycle detection |  |  |
| 7 | note-two-phase-locking-deadlocks | USEFUL_CONNECT | Cycle detection on the waits-for graph. |  |  |  |
| 8 | note-lazy-evaluation-query-plans | USEFUL_CONNECT | Query plans as a logical plan graph. |  |  |  |
| 9 | note-ssa-form | USEFUL_CONNECT | Programs as dataflow graphs. |  |  |  |

## A19 — arrival:A19

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | note-bloom-filter-false-positive-math | MUST_CONNECT | Her derivation predicts exactly this: ~10 bits per key gives ≈1% false positives, and no false negatives. | 10 bits/key ≈ 1% false positives matches the formula | 2 |  |
| 2 | note-lsm-trees | MUST_CONNECT | The per-SSTable 'definitely not here / maybe here' filter in her LSM note is this Bloom filter. | the note's 'small in-memory filter' per SSTable is a Bloom filter |  |  |
| 3 | note-columnar-storage-compression | USEFUL_CONNECT | Parquet min/max statistics skip reads the same way: cheap metadata answers 'cannot match'. |  |  |  |

## A20 — arrival:A20

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | stage:stage-os-l05-01-translation | UNJUDGED | Written in this stage (two-level page-table walk and TLB). |  |  |  |
| 2 | note-virtual-memory-address-translation | MUST_CONNECT | Her VM note: multi-level page tables and the TLB. |  |  |  |
| 3 | inbox:20260915-os-oral-questions.md | USEFUL_CONNECT | Answers two collected oral questions (why a TLB; what a context switch does to it). | answers 'why is a TLB needed / what happens on a context switch' |  |  |
| 4 | note-context-switch-cost | USEFUL_CONNECT | Cold TLB after a context switch as the indirect cost. | TLB pollution after a switch; ASID/PCID | 1 |  |
| 5 | workspace-os-oral-prep | UNJUDGED | Oral-prep workspace (virtual memory unit). |  |  |  |
| 6 | note-cpu-cache-locality | USEFUL_CONNECT | Huge pages and TLB reach are the same locality story as cache lines. |  |  |  |
| 7 | note-os-kernel-user-mode | UNJUDGED | TLB pollution on mode switches; page tables changed only in kernel mode. |  |  |  |
| 8 | arrival:A04 | UNJUDGED | New capture on PagedAttention's block tables — the same mapping idea in GPU memory. |  |  |  |

## A21 — arrival:A21

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | stage:stage-l09-02-svd-connection | MUST_CONNECT | Answers the exact point the paused stage stopped at: variance along direction i is s_i²/(n−1). | answers the stage's open question: variance along direction i is s_i²/(n−1) |  |  |
| 2 | note-pca-by-hand | MUST_CONNECT | Her PCA-by-covariance computation; the slide gives the SVD route to the same directions. |  |  |  |
| 3 | note-svd-geometric | MUST_CONNECT | AᵀA = V Σ² Vᵀ is the identity the slide uses. |  |  |  |
| 4 | note-covariance-matrix | USEFUL_CONNECT | Her covariance note uses 1/n where the slide uses 1/(n−1). |  |  |  |
| 5 | note-low-rank-approximation | USEFUL_CONNECT | Truncated SVD — PCA's top components are a low-rank approximation. |  |  |  |
| 6 | note-statlearn-mock-exam-september | UNJUDGED | Mock Q5 (first principal component and explained variance). |  |  |  |
| 7 | note-consistent-estimators | UNJUDGED | Explains the 1/n versus 1/(n−1) difference between her note and the slide. |  |  |  |
| 8 | workspace-statlearn-retake | USEFUL_CONNECT | Retake workspace (L09 is in scope). | open question whether the SVD proof is asked | 1 |  |
| 9 | note-weekly-review-log | UNJUDGED | Her log recording that PCA stalled at the SVD step. |  |  |  |

## A22 — arrival:A22

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | note-chain-rule-multivariable | MUST_CONNECT | The Jacobian-product order argument: multiplying from the output side is cheap for a scalar loss — the reason reverse mode wins. | the order of the Jacobian product is the forward/reverse choice; answers 'remember this when we get to neural networks' | 2 |  |
| 2 | note-forward-mode-autodiff-dual-numbers | MUST_CONNECT | Her forward-mode implementation, which already notes reverse mode is the right direction for one output. | forward mode: one pass per input; reverse: one per output |  |  |
| 3 | note-backprop-as-bookkeeping | MUST_CONNECT | Backprop as a reverse sweep over the graph; one backward pass for all parameters. |  |  |  |
| 4 | stage:stage-l11-01-backprop | UNJUDGED | Pending stage: backprop by hand. |  |  |  |

## A23 — arrival:A23

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | note-idempotency-keys-api | MUST_CONNECT | Her idempotency-key note is exactly this fix (client key per logical operation, server returns stored result). | save_id is an idempotency key; same key returns stored result |  |  |
| 2 | note-idempotent-pipelines-backfills | USEFUL_CONNECT | Same retry-duplicates bug in pipelines; upsert on a natural key. |  |  |  |
| 3 | workspace-ledgerline | MUST_CONNECT | Ledgerline workspace (blocked until after the exams). | answers 'how to make retried saves not produce duplicate receipts' | 1 |  |
| 4 | project-ledgerline | MUST_CONNECT | Project record with the pause decision. |  |  |  |
| 5 | garden:ledgerline-receipt-idea.md | USEFUL_CONNECT | The receipt idea being designed. |  |  |  |
| 6 | note-event-sourcing-append-only | USEFUL_CONNECT | Append-only log of facts; duplicates must be prevented at write time. |  |  |  |
| 7 | arrival:A06 | UNJUDGED | New receipt-format draft this fix applies to. |  |  |  |

## A24 — arrival:A24

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|

## A25 — arrival:A25

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | note-logistic-regression-cross-entropy | MUST_CONNECT | Answers the question: cross-entropy is the Bernoulli negative log-likelihood, and squared error with a sigmoid is non-convex with vanishing gradients. | cross-entropy is the negative Bernoulli log-likelihood; squared error with a sigmoid is non-convex and has vanishing gradients |  |  |
| 2 | note-mle-coin-flips | USEFUL_CONNECT | The Bernoulli log-likelihood written out — it is the cross-entropy. | Bernoulli log-likelihood has the CE form |  |  |
| 3 | note-gaussian-noise-least-squares | MUST_CONNECT | The other half of the answer: squared error is the Gaussian-noise likelihood, so it is not a convention either. | MSE is the Gaussian-noise likelihood; CE is the Bernoulli one — same MLE recipe |  |  |
| 4 | note-convexity-basics | UNJUDGED | Why convexity of the loss matters for optimisation. |  |  |  |
| 5 | note-generative-vs-discriminative | UNJUDGED | Logistic regression as the discriminative model. |  |  |  |

## A26 — arrival:A26

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | note-gradient-descent-from-scratch | MUST_CONNECT | 'The housing thing in April': η too large made the loss explode; the real culprit was feature scaling. | the April divergence at η=0.1; resolved there by standardizing features | 2 |  |
| 2 | note-sgd-momentum-nn-training | MUST_CONNECT | Her earlier MLP training note (same update rule, minibatches). |  |  |  |
| 3 | note-normal-distribution-standardizing | USEFUL_CONNECT | Standardising inputs — the housing fix. |  |  |  |
| 4 | note-adam-vs-sgd-revisited | UNJUDGED | Learning-rate sensitivity of SGD vs Adam. |  |  |  |
| 5 | note-batchnorm-internal-covariate-shift | UNJUDGED | Normalisation inside the network allows larger learning rates. |  |  |  |
| 6 | note-mixed-precision-training | AMBIGUOUS | Another source of inf/NaN in training. |  |  |  |

## A27 — arrival:A27

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | stage:stage-df-joins-01-strategies | UNJUDGED | Written in this stage; it is the stage's measurement. |  |  |  |
| 2 | note-hash-join-vs-sort-merge | MUST_CONNECT | Her exam summary 'hash join is always O(n + m)' — this measurement shows when it is not (one key larger than memory). | corrects the claim that hash join is always O(n+m); skewed keys overflow one partition and spill | 2 |  |
| 3 | note-external-merge-sort | USEFUL_CONNECT | Spilling and multi-pass processing when data exceeds the memory budget. |  |  |  |
| 4 | workspace-dataframe-skill | USEFUL_CONNECT | Workspace for the joins-at-scale unit. |  |  |  |
| 5 | note-kafka-consumer-lag-backpressure | UNJUDGED | Parallelism capped by partitioning — a hot key cannot be split across partitions either. |  |  |  |
| 6 | note-parallel-workers-no-speedup | USEFUL_CONNECT | One unsplittable piece of work dominating the runtime. | one partition dominates like a sequential bottleneck | 2 |  |

## A28 — arrival:A28

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | note-kafka-consumer-lag-backpressure | MUST_CONNECT | Answers it: lag is unbounded growth of the log, whereas a bounded buffer blocks the producer (backpressure). | lag grows instead of blocking; push-based bounded buffers push back |  |  |
| 2 | note-semaphores-producer-consumer | MUST_CONNECT | The OS bounded buffer, where a full buffer blocks producers. | a bounded buffer blocks the producer; Kafka's log does not |  |  |
| 3 | note-queueing-littles-law | USEFUL_CONNECT | Queue length, arrival rate and delay — how lag translates into time behind. | lag / consume rate ≈ delay is L = λW |  |  |

## A29 — arrival:A29

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | inbox:20260816-drf-paper-link.md | MUST_CONNECT | The same 'read later' link captured on 2026-08-16 — this is a duplicate capture. | exact duplicate capture |  |  |
| 2 | note-dominant-resource-fairness-paper | MUST_CONNECT | She has already read the paper and written it up, so the 'read later' is done. | already read and noted on 2026-08-17 |  |  |
| 3 | note-multi-tenant-gpu-sharing | USEFUL_CONNECT | Her note from the internship-fair talk that mentioned the paper. |  |  |  |

## A30 — arrival:A30

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | note-kv-cache-transformer-serving | MUST_CONNECT | Answers the question: the server keeps every past token's keys and values (the KV cache), and it grows linearly with context. | the server keeps past keys and values; size grows linearly with context |  |  |
| 2 | garden:attention-as-soft-lookup.md | MUST_CONNECT | Her seed describing attention as a soft dictionary lookup and asking about the KV cache. |  |  |  |
| 3 | note-softmax-temperature | USEFUL_CONNECT | The softmax in the attention formula. |  |  |  |
| 4 | arrival:A04 | UNJUDGED | New capture on PagedAttention — how that memory is managed. |  |  |  |


## Judge grading notes (S10)

- expl: 0 wrong/absent, 1 partly right, 2 correct. All keyword-heuristic misses
  were human-graded; heuristic-covered rows were accepted after a 12-row
  spot-check per run found no false covers. MUST_NOT rows graded on whether
  the stated reason is factually correct (several are knowing contrasts).
- prov: 1 cited material refs resolve and support the claim; 0 no usable
  citation (no evidence, or only a discovery-method note such as a `los ...`
  command or `surfaced by:` line). Sampled rows only; see FAILURE_ANALYSIS.md.
