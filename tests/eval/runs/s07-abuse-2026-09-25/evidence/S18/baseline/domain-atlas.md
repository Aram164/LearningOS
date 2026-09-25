# Domain atlas — the cross-domain map

> ⚠️ GENERATED file — a disposable VIEW over the canonical records, not part of the canonical architecture. Never edit; edit canonical inputs instead. Rebuilt by `python tools/generate.py` (learning_os v3.2.0) from: knowledge/, sources/, curriculum/, records/, work/.
> Generated: 2026-09-18T09:51:00+02:00 (last commit)

## At a glance

- **mathematics** — 22 notes · no shelves yet
- **machine-learning** — 25 notes · no shelves yet
- **systems** — 21 notes · no shelves yet
- **data-systems** — 23 notes · no shelves yet
- **algorithms** — 0 notes · no shelves yet
- **programming** — 17 notes · no shelves yet
- **cross-domain** — 8 notes · no shelves yet
- **Outside this map (deliberate):** Foundations archive (unregistered; names in `materials/FILES.txt`) · external code repositories such as `Stratum/` (not LearningOS data) — details in the last section.

*Per-domain shelves and wiring hubs below · per-concept joins → `concept-index.md` · full source detail → `source-index.md` · wiring debt → `reports/health.md`.*

## mathematics

Notes: 22 — derivation 5 · implementation 1 · synthesis 16

Notes by role:

- **synthesis** (16)
  - [Bias and variance, rewritten from Murphy](../knowledge/notes/mathematics/note-bias-variance-from-book.md) — `note-bias-variance-from-book` · rough
  - [Conditional probability and Bayes' rule](../knowledge/notes/mathematics/note-conditional-probability-basics.md) — `note-conditional-probability-basics` · evolving
  - [Convex functions and why they matter for optimization](../knowledge/notes/mathematics/note-convexity-basics.md) — `note-convexity-basics` · evolving
  - [Eigenvectors — the directions a matrix only stretches](../knowledge/notes/mathematics/note-eigenvectors-intuition.md) — `note-eigenvectors-intuition` · evolving
  - [Independence is not the same as conditional independence](../knowledge/notes/mathematics/note-independence-vs-conditional-independence.md) — `note-independence-vs-conditional-independence` · evolving
  - [Kernel density estimation](../knowledge/notes/mathematics/note-kernel-density-estimation.md) — `note-kernel-density-estimation` · rough
  - [Little's law](../knowledge/notes/mathematics/note-queueing-littles-law.md) — `note-queueing-littles-law` · evolving
  - [Low-rank approximation (unfinished)](../knowledge/notes/mathematics/note-low-rank-approximation.md) — `note-low-rank-approximation` · rough
  - [Markov chains and stationary distributions](../knowledge/notes/mathematics/note-markov-chains-stationary.md) — `note-markov-chains-stationary` · evolving
  - [Multivariable chain rule as Jacobian products](../knowledge/notes/mathematics/note-chain-rule-multivariable.md) — `note-chain-rule-multivariable` · evolving
  - [SVD as rotate–stretch–rotate](../knowledge/notes/mathematics/note-svd-geometric.md) — `note-svd-geometric` · evolving
  - [Standardizing and z-scores](../knowledge/notes/mathematics/note-normal-distribution-standardizing.md) — `note-normal-distribution-standardizing` · evolving
  - [The covariance matrix and its ellipse](../knowledge/notes/mathematics/note-covariance-matrix.md) — `note-covariance-matrix` · evolving
  - [Unbiased versus consistent estimators](../knowledge/notes/mathematics/note-consistent-estimators.md) — `note-consistent-estimators` · evolving
  - [What a p-value actually is](../knowledge/notes/mathematics/note-p-values-corrected.md) — `note-p-values-corrected` · evolving
  - [p-values (first take)](../knowledge/notes/mathematics/note-p-values-first-take.md) — `note-p-values-first-take` · deprecated
- **derivation** (5)
  - [Bias–variance decomposition (lecture version)](../knowledge/notes/mathematics/note-bias-variance-decomposition-lecture.md) — `note-bias-variance-decomposition-lecture` · evolving
  - [How often a Bloom filter lies](../knowledge/notes/mathematics/note-bloom-filter-false-positive-math.md) — `note-bloom-filter-false-positive-math` · evolving
  - [MAP estimation — a prior turns into an extra term](../knowledge/notes/mathematics/note-map-estimation-priors.md) — `note-map-estimation-priors` · evolving
  - [Maximum likelihood for a coin](../knowledge/notes/mathematics/note-mle-coin-flips.md) — `note-mle-coin-flips` · evolving
  - [Why least squares falls out of Gaussian noise](../knowledge/notes/mathematics/note-gaussian-noise-least-squares.md) — `note-gaussian-noise-least-squares` · evolving
- **implementation** (1)
  - [CLT by simulation](../knowledge/notes/mathematics/note-central-limit-theorem-simulation.md) — `note-central-limit-theorem-simulation` · evolving

Shelves: none yet — sources for this domain surface only through concept links and note references.

## machine-learning

Notes: 25 — derivation 3 · implementation 4 · mock-exam 1 · reference 1 · synthesis 16

Notes by role:

- **reference** (1)
  - [Regression metrics](../knowledge/notes/machine-learning/note-regression-metrics.md) — `note-regression-metrics` · evolving
- **synthesis** (16)
  - [Adam is just better](../knowledge/notes/machine-learning/note-adam-always-better.md) — `note-adam-always-better` · deprecated
  - [Adam versus SGD, revisited](../knowledge/notes/machine-learning/note-adam-vs-sgd-revisited.md) — `note-adam-vs-sgd-revisited` · evolving
  - [Backpropagation is careful bookkeeping](../knowledge/notes/machine-learning/note-backprop-as-bookkeeping.md) — `note-backprop-as-bookkeeping` · rough
  - [Batch normalization](../knowledge/notes/machine-learning/note-batchnorm-internal-covariate-shift.md) — `note-batchnorm-internal-covariate-shift` · evolving
  - [Convolutions in CNNs](../knowledge/notes/machine-learning/note-cnn-convolution-kernels.md) — `note-cnn-convolution-kernels` · rough
  - [Decision trees and information gain](../knowledge/notes/machine-learning/note-decision-trees-entropy.md) — `note-decision-trees-entropy` · evolving
  - [Generative versus discriminative classifiers](../knowledge/notes/machine-learning/note-generative-vs-discriminative.md) — `note-generative-vs-discriminative` · rough
  - [HMMs and the Viterbi algorithm](../knowledge/notes/machine-learning/note-hmm-viterbi.md) — `note-hmm-viterbi` · evolving
  - [Matrix factorization for recommendations](../knowledge/notes/machine-learning/note-matrix-factorization-recommenders.md) — `note-matrix-factorization-recommenders` · rough
  - [Naive Bayes for the spam exercise](../knowledge/notes/machine-learning/note-naive-bayes-spam-filter.md) — `note-naive-bayes-spam-filter` · evolving
  - [SVMs and the kernel trick](../knowledge/notes/machine-learning/note-svm-kernel-trick.md) — `note-svm-kernel-trick` · rough
  - [Softmax and temperature](../knowledge/notes/machine-learning/note-softmax-temperature.md) — `note-softmax-temperature` · rough
  - [The scaler leak](../knowledge/notes/machine-learning/note-data-leakage-scaler.md) — `note-data-leakage-scaler` · evolving
  - [Why batch norm works is contested](../knowledge/notes/machine-learning/note-batchnorm-why-it-works-contested.md) — `note-batchnorm-why-it-works-contested` · rough
  - [Why the lasso sets weights exactly to zero](../knowledge/notes/machine-learning/note-lasso-sparsity-geometry.md) — `note-lasso-sparsity-geometry` · evolving
  - [k-fold cross-validation](../knowledge/notes/machine-learning/note-cross-validation-kfold.md) — `note-cross-validation-kfold` · evolving
- **mock-exam** (1)
  - [Statistical Learning — mock exam 1](../knowledge/notes/machine-learning/note-statlearn-mock-exam-september.md) — `note-statlearn-mock-exam-september` · rough
- **derivation** (3)
  - [Linear regression — the normal equation](../knowledge/notes/machine-learning/note-linear-regression-normal-equation.md) — `note-linear-regression-normal-equation` · evolving
  - [Logistic regression and where cross-entropy comes from](../knowledge/notes/machine-learning/note-logistic-regression-cross-entropy.md) — `note-logistic-regression-cross-entropy` · evolving
  - [Ridge regression](../knowledge/notes/machine-learning/note-ridge-regression-penalty.md) — `note-ridge-regression-penalty` · evolving
- **implementation** (4)
  - [Gradient descent from scratch (housing exercise)](../knowledge/notes/machine-learning/note-gradient-descent-from-scratch.md) — `note-gradient-descent-from-scratch` · evolving
  - [Overfitting — polynomial degree experiment](../knowledge/notes/machine-learning/note-overfitting-polynomial-degree.md) — `note-overfitting-polynomial-degree` · evolving
  - [PCA by hand on a 2-D toy dataset](../knowledge/notes/machine-learning/note-pca-by-hand.md) — `note-pca-by-hand` · evolving
  - [Training a small MLP — minibatches and momentum](../knowledge/notes/machine-learning/note-sgd-momentum-nn-training.md) — `note-sgd-momentum-nn-training` · rough

Shelves: none yet — sources for this domain surface only through concept links and note references.

## systems

Notes: 21 — derivation 1 · exercise-bank 1 · reference 2 · synthesis 17

Notes by role:

- **reference** (2)
  - [CPU scheduling — FCFS, SJF, round robin](../knowledge/notes/systems/note-cpu-scheduling-round-robin.md) — `note-cpu-scheduling-round-robin` · evolving
  - [Dominant Resource Fairness](../knowledge/notes/systems/note-dominant-resource-fairness-paper.md) — `note-dominant-resource-fairness-paper` · evolving
- **synthesis** (17)
  - [Amdahl's law](../knowledge/notes/systems/note-amdahls-law.md) — `note-amdahls-law` · evolving
  - [Caches and locality](../knowledge/notes/systems/note-cpu-cache-locality.md) — `note-cpu-cache-locality` · evolving
  - [Data-parallel training did not scale as expected](../knowledge/notes/systems/note-data-parallel-training-scaling.md) — `note-data-parallel-training-scaling` · rough
  - [Deadlock — the four conditions](../knowledge/notes/systems/note-deadlock-four-conditions.md) — `note-deadlock-four-conditions` · evolving
  - [Dynamic batching in model serving](../knowledge/notes/systems/note-dynamic-batching-inference.md) — `note-dynamic-batching-inference` · rough
  - [Instruction pipelining](../knowledge/notes/systems/note-cpu-instruction-pipeline.md) — `note-cpu-instruction-pipeline` · rough
  - [Journaling file systems](../knowledge/notes/systems/note-journaling-filesystems.md) — `note-journaling-filesystems` · evolving
  - [Kernel mode, user mode and system calls](../knowledge/notes/systems/note-os-kernel-user-mode.md) — `note-os-kernel-user-mode` · evolving
  - [Mixed-precision training](../knowledge/notes/systems/note-mixed-precision-training.md) — `note-mixed-precision-training` · rough
  - [Page replacement — FIFO, LRU, clock](../knowledge/notes/systems/note-page-replacement-lru-clock.md) — `note-page-replacement-lru-clock` · evolving
  - [Priority inversion](../knowledge/notes/systems/note-priority-inversion.md) — `note-priority-inversion` · evolving
  - [Proportional share and Linux CFS](../knowledge/notes/systems/note-cfs-fair-share.md) — `note-cfs-fair-share` · evolving
  - [Sharing one inference cluster between teams](../knowledge/notes/systems/note-multi-tenant-gpu-sharing.md) — `note-multi-tenant-gpu-sharing` · rough
  - [The KV cache in transformer inference](../knowledge/notes/systems/note-kv-cache-transformer-serving.md) — `note-kv-cache-transformer-serving` · rough
  - [Virtual memory](../knowledge/notes/systems/note-virtual-memory-is-swap.md) — `note-virtual-memory-is-swap` · deprecated
  - [Virtual memory is address translation](../knowledge/notes/systems/note-virtual-memory-address-translation.md) — `note-virtual-memory-address-translation` · evolving
  - [What a context switch costs](../knowledge/notes/systems/note-context-switch-cost.md) — `note-context-switch-cost` · rough
- **exercise-bank** (1)
  - [OS scheduling — exercise bank](../knowledge/notes/systems/note-os-scheduling-exercise-bank.md) — `note-os-scheduling-exercise-bank` · rough
- **derivation** (1)
  - [Semaphores and the bounded buffer](../knowledge/notes/systems/note-semaphores-producer-consumer.md) — `note-semaphores-producer-consumer` · evolving

Shelves: none yet — sources for this domain surface only through concept links and note references.

## data-systems

Notes: 23 — derivation 1 · reference 4 · synthesis 18

Notes by role:

- **reference** (4)
  - [Database Systems — exam cheat sheet](../knowledge/notes/data-systems/note-db-exam-cheatsheet.md) — `note-db-exam-cheatsheet` · rough
  - [Normal forms (up to BCNF)](../knowledge/notes/data-systems/note-db-normalization-3nf.md) — `note-db-normalization-3nf` · evolving
  - [Relational algebra operators](../knowledge/notes/data-systems/note-relational-algebra-operators.md) — `note-relational-algebra-operators` · evolving
  - [Why- and where-provenance](../knowledge/notes/data-systems/note-why-provenance-paper.md) — `note-why-provenance-paper` · rough
- **synthesis** (18)
  - [16 workers, 1.6× faster](../knowledge/notes/data-systems/note-parallel-workers-no-speedup.md) — `note-parallel-workers-no-speedup` · rough
  - [ACID — and what the C means](../knowledge/notes/data-systems/note-acid-consistency.md) — `note-acid-consistency` · evolving
  - [Algebraic equivalences and pushing selections down](../knowledge/notes/data-systems/note-algebraic-equivalences-pushdown.md) — `note-algebraic-equivalences-pushdown` · evolving
  - [B+ tree indexes](../knowledge/notes/data-systems/note-b-plus-tree-indexes.md) — `note-b-plus-tree-indexes` · evolving
  - [Buffer pool management](../knowledge/notes/data-systems/note-buffer-pool-replacement.md) — `note-buffer-pool-replacement` · evolving
  - [Columnar storage and compression](../knowledge/notes/data-systems/note-columnar-storage-compression.md) — `note-columnar-storage-compression` · evolving
  - [Consumer lag and backpressure](../knowledge/notes/data-systems/note-kafka-consumer-lag-backpressure.md) — `note-kafka-consumer-lag-backpressure` · rough
  - [Cost models and selectivity](../knowledge/notes/data-systems/note-query-optimizer-cost-model.md) — `note-query-optimizer-cost-model` · evolving
  - [Debugging a wrong dashboard number](../knowledge/notes/data-systems/note-data-lineage-debugging.md) — `note-data-lineage-debugging` · rough
  - [Hash join versus sort-merge join](../knowledge/notes/data-systems/note-hash-join-vs-sort-merge.md) — `note-hash-join-vs-sort-merge` · evolving
  - [Idempotent pipeline steps](../knowledge/notes/data-systems/note-idempotent-pipelines-backfills.md) — `note-idempotent-pipelines-backfills` · evolving
  - [LSM trees](../knowledge/notes/data-systems/note-lsm-trees.md) — `note-lsm-trees` · evolving
  - [Lazy frames build a plan first](../knowledge/notes/data-systems/note-lazy-evaluation-query-plans.md) — `note-lazy-evaluation-query-plans` · evolving
  - [Pipelines as DAGs of tasks](../knowledge/notes/data-systems/note-data-pipeline-orchestration-dag.md) — `note-data-pipeline-orchestration-dag` · rough
  - [System R join ordering](../knowledge/notes/data-systems/note-selinger-join-ordering.md) — `note-selinger-join-ordering` · evolving
  - [The C in CAP is not the C in ACID](../knowledge/notes/data-systems/note-cap-consistency-linearizability.md) — `note-cap-consistency-linearizability` · evolving
  - [Two-phase locking and deadlocks](../knowledge/notes/data-systems/note-two-phase-locking-deadlocks.md) — `note-two-phase-locking-deadlocks` · evolving
  - [Write-ahead logging and ARIES recovery](../knowledge/notes/data-systems/note-write-ahead-logging-aries.md) — `note-write-ahead-logging-aries` · evolving
- **derivation** (1)
  - [External merge sort](../knowledge/notes/data-systems/note-external-merge-sort.md) — `note-external-merge-sort` · evolving

Shelves: none yet — sources for this domain surface only through concept links and note references.

## algorithms

Notes: none yet

Shelves: none yet — sources for this domain surface only through concept links and note references.

## programming

Notes: 17 — implementation 3 · reference 1 · synthesis 13

Notes by role:

- **reference** (1)
  - [The phases of a compiler](../knowledge/notes/programming/note-compiler-pipeline-overview.md) — `note-compiler-pipeline-overview` · evolving
- **synthesis** (13)
  - [Build systems — DAGs and incrementality](../knowledge/notes/programming/note-build-systems-dag-incremental.md) — `note-build-systems-dag-incremental` · rough
  - [Constant folding and common subexpression elimination](../knowledge/notes/programming/note-constant-folding-cse.md) — `note-constant-folding-cse` · evolving
  - [Dynamic programming and memoization](../knowledge/notes/programming/note-dynamic-programming-memoization.md) — `note-dynamic-programming-memoization` · evolving
  - [Errors as values](../knowledge/notes/programming/note-error-handling-result-types.md) — `note-error-handling-result-types` · rough
  - [Event sourcing](../knowledge/notes/programming/note-event-sourcing-append-only.md) — `note-event-sourcing-append-only` · evolving
  - [Generational garbage collection](../knowledge/notes/programming/note-garbage-collection-generational.md) — `note-garbage-collection-generational` · rough
  - [Git's object model](../knowledge/notes/programming/note-git-internals-content-addressing.md) — `note-git-internals-content-addressing` · evolving
  - [Idempotency keys](../knowledge/notes/programming/note-idempotency-keys-api.md) — `note-idempotency-keys-api` · evolving
  - [Property-based testing](../knowledge/notes/programming/note-property-based-testing.md) — `note-property-based-testing` · rough
  - [Regression tests and snapshot files](../knowledge/notes/programming/note-regression-testing-snapshots.md) — `note-regression-testing-snapshots` · rough
  - [Rust ownership and borrowing](../knowledge/notes/programming/note-rust-ownership-borrowing.md) — `note-rust-ownership-borrowing` · rough
  - [Static single assignment](../knowledge/notes/programming/note-ssa-form.md) — `note-ssa-form` · rough
  - [Type inference by unification](../knowledge/notes/programming/note-type-inference-unification.md) — `note-type-inference-unification` · rough
- **implementation** (3)
  - [Forward-mode autodiff with dual numbers](../knowledge/notes/programming/note-forward-mode-autodiff-dual-numbers.md) — `note-forward-mode-autodiff-dual-numbers` · rough
  - [Rewriting plan trees with a visitor](../knowledge/notes/programming/note-tagless-visitor-pattern-ast.md) — `note-tagless-visitor-pattern-ast` · evolving
  - [Simulated annealing](../knowledge/notes/programming/note-simulated-annealing.md) — `note-simulated-annealing` · rough

Shelves: none yet — sources for this domain surface only through concept links and note references.

## cross-domain

Notes: 8 — synthesis 8

Notes by role:

- **synthesis** (8)
  - [End-of-semester review (July)](../knowledge/notes/cross-domain/note-semester-review-july.md) — `note-semester-review-july` · rough
  - [How I take notes](../knowledge/notes/cross-domain/note-how-i-take-notes.md) — `note-how-i-take-notes` · evolving
  - [How the review scheduler decides](../knowledge/notes/cross-domain/note-spaced-repetition-scheduler.md) — `note-spaced-repetition-scheduler` · evolving
  - [Pomodoro and the cost of switching subjects](../knowledge/notes/cross-domain/note-pomodoro-and-context-switching.md) — `note-pomodoro-and-context-switching` · rough
  - [Preparing for an oral exam](../knowledge/notes/cross-domain/note-oral-exam-prep-strategy.md) — `note-oral-exam-prep-strategy` · rough
  - [Retake plan — splitting time fairly between two exams](../knowledge/notes/cross-domain/note-study-plan-retake-strategy.md) — `note-study-plan-retake-strategy` · evolving
  - [The same cache idea in three courses](../knowledge/notes/cross-domain/note-caching-everywhere.md) — `note-caching-everywhere` · rough
  - [Weekly review log (summer)](../knowledge/notes/cross-domain/note-weekly-review-log.md) — `note-weekly-review-log` · evolving

Shelves: none yet — sources for this domain surface only through concept links and note references.

## Not in this map — deliberately excluded strata

- **External code repositories** — sibling worktrees such as `Stratum/` are never indexed or validated as LearningOS data; an agent may inspect them only when the current task explicitly needs code context.

