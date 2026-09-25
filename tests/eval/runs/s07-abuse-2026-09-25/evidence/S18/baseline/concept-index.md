# Concept index

> ⚠️ GENERATED file — a disposable VIEW over the canonical records, not part of the canonical architecture. Never edit; edit canonical inputs instead. Rebuilt by `python tools/generate.py` (learning_os v3.2.0) from: knowledge/, sources/, curriculum/, records/, work/.
> Generated: 2026-09-18T09:51:00+02:00 (last commit)

## Contents

**A:** [Adaptive optimizers](#adaptive-optimizers) · [Amdahl's law](#amdahls-law) · [Automatic differentiation](#automatic-differentiation)

**B:** [B+ trees](#b-trees) · [Backpropagation](#backpropagation) · [Batch normalization](#batch-normalization) · [Bayes' theorem](#bayes-theorem) · [Bias–variance trade-off](#biasvariance-trade-off) · [Bloom filters](#bloom-filters) · [Buffer management](#buffer-management) · [Build systems](#build-systems)

**C:** [CAP theorem](#cap-theorem) · [Cardinality estimation](#cardinality-estimation) · [Central limit theorem](#central-limit-theorem) · [Chain rule](#chain-rule) · [Columnar storage](#columnar-storage) · [Compiler optimization](#compiler-optimization) · [Compiler structure](#compiler-structure) · [Conditional independence](#conditional-independence) · [Conditional probability](#conditional-probability) · [Content addressing](#content-addressing) · [Context switch](#context-switch) · [Convexity](#convexity) · [Convolutional neural networks](#convolutional-neural-networks) · [Covariance matrix](#covariance-matrix) · [CPU caches](#cpu-caches) · [CPU scheduling](#cpu-scheduling) · [Cross-entropy](#cross-entropy) · [Cross-validation](#cross-validation)

**D:** [Data leakage](#data-leakage) · [Data provenance](#data-provenance) · [Data-parallel training](#data-parallel-training) · [Database normalization](#database-normalization) · [Deadlock](#deadlock) · [Decision trees](#decision-trees) · [Dominant resource fairness](#dominant-resource-fairness) · [Dynamic programming](#dynamic-programming)

**E:** [Eigendecomposition](#eigendecomposition) · [Event sourcing](#event-sourcing) · [External sorting](#external-sorting)

**G:** [Garbage collection](#garbage-collection) · [Generative vs discriminative models](#generative-vs-discriminative-models) · [Gradient descent](#gradient-descent)

**H:** [Hidden Markov models](#hidden-markov-models) · [Hypothesis testing](#hypothesis-testing)

**I:** [Idempotency](#idempotency) · [Instruction pipelining](#instruction-pipelining)

**J:** [Join algorithms](#join-algorithms) · [Journaling file systems](#journaling-file-systems)

**K:** [Kernel density estimation](#kernel-density-estimation) · [KV cache](#kv-cache)

**L:** [Lazy evaluation](#lazy-evaluation) · [Linear regression](#linear-regression) · [Logistic regression](#logistic-regression) · [Low-rank approximation](#low-rank-approximation) · [LSM trees](#lsm-trees)

**M:** [MAP estimation](#map-estimation) · [Markov chains](#markov-chains) · [Matrix factorization](#matrix-factorization) · [Maximum likelihood estimation](#maximum-likelihood-estimation) · [Mean squared error](#mean-squared-error) · [Mixed-precision training](#mixed-precision-training) · [Model serving](#model-serving)

**N:** [Naive Bayes](#naive-bayes) · [Normal distribution](#normal-distribution) · [Normal equation](#normal-equation)

**O:** [Operating-system kernel](#operating-system-kernel) · [Overfitting](#overfitting)

**P:** [Page replacement](#page-replacement) · [Principal component analysis](#principal-component-analysis) · [Priority inversion](#priority-inversion) · [Probability](#probability) · [Property-based testing](#property-based-testing) · [Proportional-share scheduling](#proportional-share-scheduling)

**Q:** [Query optimization](#query-optimization) · [Queueing theory](#queueing-theory)

**R:** [Regression metrics](#regression-metrics) · [Regression testing](#regression-testing) · [Regularization](#regularization) · [Relational algebra](#relational-algebra) · [Rust ownership](#rust-ownership)

**S:** [Simulated annealing](#simulated-annealing) · [Singular value decomposition](#singular-value-decomposition) · [Softmax](#softmax) · [Spaced repetition](#spaced-repetition) · [Static single assignment](#static-single-assignment) · [Statistical estimation](#statistical-estimation) · [Stochastic gradient descent](#stochastic-gradient-descent) · [Stream processing](#stream-processing) · [Study planning](#study-planning) · [Support vector machines](#support-vector-machines) · [Synchronization](#synchronization)

**T:** [Transactions and ACID](#transactions-and-acid) · [Two-phase locking](#two-phase-locking) · [Type inference](#type-inference)

**V:** [Virtual memory](#virtual-memory) · [Visitor pattern](#visitor-pattern)

**W:** [Workflow orchestration](#workflow-orchestration) · [Write-ahead logging](#write-ahead-logging)

## Adaptive optimizers

`concept-adaptive-optimizers`

Aliases: AdaGrad · Adam · RMSprop

**Notes:**

- `note-adam-always-better` — Adam is just better *(role: synthesis)*
- `note-adam-vs-sgd-revisited` — Adam versus SGD, revisited *(role: synthesis)*

**Contextual sources:**

- **Wilson et al. — The Marginal Value of Adaptive Gradient Methods (2017)** (`source-wilson-adaptive-2017`) — roles: review — level: advanced — generalization comparison that tempers the "Adam everywhere" habit

## Amdahl's law

`concept-amdahls-law`

Aliases: parallel speedup

**Notes:**

- `note-amdahls-law` — Amdahl's law *(role: synthesis)*

## Automatic differentiation

`concept-automatic-differentiation`

Aliases: autodiff · dual numbers · forward mode

**Notes:**

- `note-forward-mode-autodiff-dual-numbers` — Forward-mode autodiff with dual numbers *(role: implementation)*

## B+ trees

`concept-b-plus-trees`

Aliases: B+-Baum · index

**Notes:**

- `note-b-plus-tree-indexes` — B+ tree indexes *(role: synthesis)*

## Backpropagation

`concept-backpropagation`

Aliases: Fehlerrückführung · backprop

**Notes:**

- `note-backprop-as-bookkeeping` — Backpropagation is careful bookkeeping *(role: synthesis)*

**Related concepts:**

- requires → `concept-chain-rule`

**Contextual sources:**

- **Goodfellow, Bengio, Courville — Deep Learning** (`source-goodfellow-dl`) — roles: first-learning, reference — level: intermediate — chapter 6 computational graphs; chapter 8 optimization

## Batch normalization

`concept-batch-normalization`

Aliases: BatchNorm

**Notes:**

- `note-batchnorm-internal-covariate-shift` — Batch normalization *(role: synthesis)*
- `note-batchnorm-why-it-works-contested` — Why batch norm works is contested *(role: synthesis)*

**Contextual sources:**

- **Goodfellow, Bengio, Courville — Deep Learning** (`source-goodfellow-dl`) — roles: first-learning, reference — level: intermediate — chapter 6 computational graphs; chapter 8 optimization
- **Ioffe & Szegedy — Batch Normalization (2015)** (`source-ioffe-batchnorm-2015`) — roles: first-learning — level: intermediate — original algorithm and the internal-covariate-shift motivation
- **Santurkar et al. — How Does Batch Normalization Help Optimization? (2018)** (`source-santurkar-batchnorm-2018`) — roles: review — level: advanced — experiments that separate covariate shift from smoothing

## Bayes' theorem

`concept-bayes-theorem`

Aliases: Bayes rule · Satz von Bayes · posterior

**Notes:**

- `note-conditional-probability-basics` — Conditional probability and Bayes' rule *(role: synthesis)*
- `note-map-estimation-priors` — MAP estimation — a prior turns into an extra term *(role: derivation)*

**Related concepts:**

- builds-on → `concept-conditional-probability`
- ← requires from `concept-naive-bayes`

## Bias–variance trade-off

`concept-bias-variance-tradeoff`

Aliases: Bias-Varianz-Zerlegung · bias-variance decomposition

**Notes:**

- `note-bias-variance-decomposition-lecture` — Bias–variance decomposition (lecture version) *(role: derivation)*
- `note-bias-variance-from-book` — Bias and variance, rewritten from Murphy *(role: synthesis)*
- `note-overfitting-polynomial-degree` — Overfitting — polynomial degree experiment *(role: implementation)*
- `note-statlearn-mock-exam-september` — Statistical Learning — mock exam 1 *(role: mock-exam)*

**Contextual sources:**

- **Hastie, Tibshirani, Friedman — The Elements of Statistical Learning** (`source-esl`) — roles: reference — level: advanced — lasso geometry figure; honest about cross-validation pitfalls
- **Kevin Murphy — Probabilistic Machine Learning: An Introduction** (`source-murphy-pml1`) — roles: derivation, review — level: intermediate — probabilistic view throughout; ridge as MAP made explicit

## Bloom filters

`concept-bloom-filters`

Aliases: Bloom filter

**Notes:**

- `note-bloom-filter-false-positive-math` — How often a Bloom filter lies *(role: derivation)*

**Related concepts:**

- ← requires from `concept-lsm-trees`

## Buffer management

`concept-buffer-management`

Aliases: Puffer · buffer pool

**Notes:**

- `note-buffer-pool-replacement` — Buffer pool management *(role: synthesis)*
- `note-caching-everywhere` — The same cache idea in three courses *(role: synthesis)*

**Contextual sources:**

- **Garcia-Molina, Ullman, Widom — Database Systems: The Complete Book** (`source-garcia-molina-db`) — roles: first-learning, reference — level: intermediate — recovery chapter is the clearest treatment of undo/redo logging

## Build systems

`concept-build-systems`

Aliases: Bazel · incremental build · make

**Notes:**

- `note-build-systems-dag-incremental` — Build systems — DAGs and incrementality *(role: synthesis)*

## CAP theorem

`concept-cap-theorem`

Aliases: linearizability

**Notes:**

- `note-cap-consistency-linearizability` — The C in CAP is not the C in ACID *(role: synthesis)*

**Contextual sources:**

- **Martin Kleppmann — Designing Data-Intensive Applications** (`source-kleppmann-ddia`) — roles: first-learning, review — level: intermediate — separates the many meanings of consistency

## Cardinality estimation

`concept-cardinality-estimation`

Aliases: histograms · selectivity estimation

**Notes:**

- `note-query-optimizer-cost-model` — Cost models and selectivity *(role: synthesis)*

**Related concepts:**

- applies-in → `concept-query-optimization`

**Contextual sources:**

- **Selinger et al. — Access Path Selection in a Relational Database Management System (1979)** (`source-selinger-1979`) — roles: derivation — level: advanced — the original cost-based join-order search

## Central limit theorem

`concept-central-limit-theorem`

Aliases: CLT · Zentraler Grenzwertsatz

**Notes:**

- `note-central-limit-theorem-simulation` — CLT by simulation *(role: implementation)*

## Chain rule

`concept-chain-rule`

Aliases: Jacobian · Kettenregel · multivariable chain rule

**Notes:**

- `note-backprop-as-bookkeeping` — Backpropagation is careful bookkeeping *(role: synthesis)*
- `note-chain-rule-multivariable` — Multivariable chain rule as Jacobian products *(role: synthesis)*

**Related concepts:**

- ← requires from `concept-backpropagation`

## Columnar storage

`concept-columnar-storage`

Aliases: Parquet · column store · run-length encoding

**Notes:**

- `note-columnar-storage-compression` — Columnar storage and compression *(role: synthesis)*

## Compiler optimization

`concept-compiler-optimization`

Aliases: common subexpression elimination · constant folding · dead code elimination

**Notes:**

- `note-constant-folding-cse` — Constant folding and common subexpression elimination *(role: synthesis)*
- `note-ssa-form` — Static single assignment *(role: synthesis)*

**Related concepts:**

- builds-on → `concept-compiler-structure`
- ← applies-in from `concept-ssa`

**Contextual sources:**

- **Aho, Lam, Sethi, Ullman — Compilers: Principles, Techniques, and Tools** (`source-dragon-book`) — roles: reference — level: advanced — dataflow analysis chapter

## Compiler structure

`concept-compiler-structure`

Aliases: AST · intermediate representation · lexer · parser

**Notes:**

- `note-compiler-pipeline-overview` — The phases of a compiler *(role: reference)*

**Related concepts:**

- ← builds-on from `concept-compiler-optimization`

**Contextual sources:**

- **Robert Nystrom — Crafting Interpreters** (`source-crafting-interpreters`) — roles: first-learning, implementation — level: introductory — visitor-based tree walking explained with working code

## Conditional independence

`concept-conditional-independence`

Aliases: bedingte Unabhängigkeit

**Notes:**

- `note-independence-vs-conditional-independence` — Independence is not the same as conditional independence *(role: synthesis)*

## Conditional probability

`concept-conditional-probability`

Aliases: bedingte Wahrscheinlichkeit

**Notes:**

- `note-conditional-probability-basics` — Conditional probability and Bayes' rule *(role: synthesis)*
- `note-independence-vs-conditional-independence` — Independence is not the same as conditional independence *(role: synthesis)*

**Related concepts:**

- ← builds-on from `concept-bayes-theorem`
- ← requires from `concept-logistic-regression`

## Content addressing

`concept-content-addressing`

Aliases: Merkle DAG · git object model

**Notes:**

- `note-git-internals-content-addressing` — Git's object model *(role: synthesis)*

## Context switch

`concept-context-switch`

Aliases: Kontextwechsel

**Notes:**

- `note-context-switch-cost` — What a context switch costs *(role: synthesis)*
- `note-os-scheduling-exercise-bank` — OS scheduling — exercise bank *(role: exercise-bank)*

**Related concepts:**

- applies-in → `concept-cpu-scheduling`

## Convexity

`concept-convexity`

Aliases: Konvexität · convex function

**Notes:**

- `note-convexity-basics` — Convex functions and why they matter for optimization *(role: synthesis)*

## Convolutional neural networks

`concept-convolutional-networks`

Aliases: CNN · convolution · feature map

**Notes:**

- `note-cnn-convolution-kernels` — Convolutions in CNNs *(role: synthesis)*

**Contextual sources:**

- **Goodfellow, Bengio, Courville — Deep Learning** (`source-goodfellow-dl`) — roles: first-learning, reference — level: intermediate — chapter 6 computational graphs; chapter 8 optimization

## Covariance matrix

`concept-covariance-matrix`

Aliases: Kovarianzmatrix · covariance

**Notes:**

- `note-covariance-matrix` — The covariance matrix and its ellipse *(role: synthesis)*
- `note-pca-by-hand` — PCA by hand on a 2-D toy dataset *(role: implementation)*

**Related concepts:**

- ← requires from `concept-pca`

## CPU caches

`concept-cpu-caches`

Aliases: cache line · locality of reference

**Notes:**

- `note-caching-everywhere` — The same cache idea in three courses *(role: synthesis)*
- `note-cpu-cache-locality` — Caches and locality *(role: synthesis)*

## CPU scheduling

`concept-cpu-scheduling`

Aliases: FCFS · Prozessscheduling · round robin · time quantum

**Notes:**

- `note-cfs-fair-share` — Proportional share and Linux CFS *(role: synthesis)*
- `note-cpu-scheduling-round-robin` — CPU scheduling — FCFS, SJF, round robin *(role: reference)*
- `note-os-scheduling-exercise-bank` — OS scheduling — exercise bank *(role: exercise-bank)*

**Related concepts:**

- ← applies-in from `concept-context-switch`
- ← builds-on from `concept-proportional-share`

**Contextual sources:**

- **Arpaci-Dusseau — Operating Systems: Three Easy Pieces** (`source-ostep`) — roles: first-learning, review — level: introductory — lottery and stride scheduling chapter; crash-consistency chapter
- **Silberschatz, Galvin, Gagne — Operating System Concepts** (`source-silberschatz-os`) — roles: reference — level: intermediate — exhaustive; banker's algorithm worked examples
- **TU Havelberg — Operating Systems lecture slides (SoSe 2026)** (`source-tuh-os-slides`) — roles: first-learning — level: introductory — clear diagrams of scheduling timelines

## Cross-entropy

`concept-cross-entropy`

Aliases: Kreuzentropie · binary cross-entropy · log loss

**Notes:**

- `note-logistic-regression-cross-entropy` — Logistic regression and where cross-entropy comes from *(role: derivation)*

## Cross-validation

`concept-cross-validation`

Aliases: Kreuzvalidierung · k-fold

**Notes:**

- `note-cross-validation-kfold` — k-fold cross-validation *(role: synthesis)*
- `note-data-leakage-scaler` — The scaler leak *(role: synthesis)*

**Contextual sources:**

- **Hastie, Tibshirani, Friedman — The Elements of Statistical Learning** (`source-esl`) — roles: reference — level: advanced — lasso geometry figure; honest about cross-validation pitfalls

## Data leakage

`concept-data-leakage`

Aliases: target leakage · train-test contamination

**Notes:**

- `note-data-leakage-scaler` — The scaler leak *(role: synthesis)*

**Contextual sources:**

- **Chip Huyen — Designing Machine Learning Systems** (`source-huyen-dmls`) — roles: first-learning — level: introductory — practical serving trade-offs; leakage chapter

## Data-parallel training

`concept-data-parallel-training`

Aliases: all-reduce · distributed training

**Notes:**

- `note-data-parallel-training-scaling` — Data-parallel training did not scale as expected *(role: synthesis)*

## Data provenance

`concept-data-provenance`

Aliases: lineage · why-provenance

**Notes:**

- `note-why-provenance-paper` — Why- and where-provenance *(role: reference)*

**Contextual sources:**

- **Buneman, Khanna, Tan — Why and Where: A Characterization of Data Provenance (2001)** (`source-buneman-provenance-2001`) — roles: first-learning — level: advanced — witness sets make "why is this row here" precise

## Database normalization

`concept-db-normalization`

Aliases: 3NF · BCNF · Normalform · functional dependency

**Notes:**

- `note-db-exam-cheatsheet` — Database Systems — exam cheat sheet *(role: reference)*
- `note-db-normalization-3nf` — Normal forms (up to BCNF) *(role: reference)*

**Contextual sources:**

- **Garcia-Molina, Ullman, Widom — Database Systems: The Complete Book** (`source-garcia-molina-db`) — roles: first-learning, reference — level: intermediate — recovery chapter is the clearest treatment of undo/redo logging

## Deadlock

`concept-deadlock`

Aliases: Coffman conditions · Verklemmung

**Notes:**

- `note-deadlock-four-conditions` — Deadlock — the four conditions *(role: synthesis)*

**Related concepts:**

- requires → `concept-synchronization`

**Contextual sources:**

- **Arpaci-Dusseau — Operating Systems: Three Easy Pieces** (`source-ostep`) — roles: first-learning, review — level: introductory — lottery and stride scheduling chapter; crash-consistency chapter
- **Silberschatz, Galvin, Gagne — Operating System Concepts** (`source-silberschatz-os`) — roles: reference — level: intermediate — exhaustive; banker's algorithm worked examples
- **TU Havelberg — Operating Systems lecture slides (SoSe 2026)** (`source-tuh-os-slides`) — roles: first-learning — level: introductory — clear diagrams of scheduling timelines

## Decision trees

`concept-decision-trees`

Aliases: Entscheidungsbaum · information gain

**Notes:**

- `note-decision-trees-entropy` — Decision trees and information gain *(role: synthesis)*

## Dominant resource fairness

`concept-dominant-resource-fairness`

Aliases: DRF

**Notes:**

- `note-dominant-resource-fairness-paper` — Dominant Resource Fairness *(role: reference)*
- `note-multi-tenant-gpu-sharing` — Sharing one inference cluster between teams *(role: synthesis)*

**Contextual sources:**

- **Ghodsi et al. — Dominant Resource Fairness (2011)** (`source-ghodsi-drf-2011`) — roles: first-learning — level: advanced — multi-resource fairness with strategy-proofness arguments

## Dynamic programming

`concept-dynamic-programming`

Aliases: Dynamische Programmierung · memoization

**Notes:**

- `note-caching-everywhere` — The same cache idea in three courses *(role: synthesis)*
- `note-dynamic-programming-memoization` — Dynamic programming and memoization *(role: synthesis)*

## Eigendecomposition

`concept-eigendecomposition`

Aliases: Eigenvektor · Eigenwert · eigenvalue · eigenvector

**Notes:**

- `note-covariance-matrix` — The covariance matrix and its ellipse *(role: synthesis)*
- `note-eigenvectors-intuition` — Eigenvectors — the directions a matrix only stretches *(role: synthesis)*
- `note-markov-chains-stationary` — Markov chains and stationary distributions *(role: synthesis)*
- `note-pca-by-hand` — PCA by hand on a 2-D toy dataset *(role: implementation)*
- `note-svd-geometric` — SVD as rotate–stretch–rotate *(role: synthesis)*

**Related concepts:**

- ← generalizes from `concept-svd`
- ← requires from `concept-pca`

**Contextual sources:**

- **3Blue1Brown — Essence of Linear Algebra** (`source-3b1b-linalg`) — roles: intuition — level: introductory — best picture of what an eigenvector is
- **Gilbert Strang — Introduction to Linear Algebra (5th ed.)** (`source-strang-linalg`) — roles: first-learning, derivation — level: introductory — geometric intuition first

## Event sourcing

`concept-event-sourcing`

Aliases: append-only log · event log

**Notes:**

- `note-event-sourcing-append-only` — Event sourcing *(role: synthesis)*

**Contextual sources:**

- **Martin Kleppmann — Designing Data-Intensive Applications** (`source-kleppmann-ddia`) — roles: first-learning, review — level: intermediate — separates the many meanings of consistency

## External sorting

`concept-external-sorting`

Aliases: external merge sort

**Notes:**

- `note-external-merge-sort` — External merge sort *(role: derivation)*

**Contextual sources:**

- **Garcia-Molina, Ullman, Widom — Database Systems: The Complete Book** (`source-garcia-molina-db`) — roles: first-learning, reference — level: intermediate — recovery chapter is the clearest treatment of undo/redo logging

## Garbage collection

`concept-garbage-collection`

Aliases: generational GC

**Notes:**

- `note-garbage-collection-generational` — Generational garbage collection *(role: synthesis)*

## Generative vs discriminative models

`concept-generative-vs-discriminative`

Aliases: generative classifier

**Notes:**

- `note-generative-vs-discriminative` — Generative versus discriminative classifiers *(role: synthesis)*

## Gradient descent

`concept-gradient-descent`

Aliases: Gradientenverfahren · learning rate

**Notes:**

- `note-gradient-descent-from-scratch` — Gradient descent from scratch (housing exercise) *(role: implementation)*

**Related concepts:**

- applies-in → `concept-linear-regression`
- ← builds-on from `concept-stochastic-gradient-descent`
- ← contrasts-with from `concept-normal-equation`

## Hidden Markov models

`concept-hidden-markov-models`

Aliases: HMM · Viterbi · trellis

**Notes:**

- `note-hmm-viterbi` — HMMs and the Viterbi algorithm *(role: synthesis)*

**Related concepts:**

- requires → `concept-markov-chains`

**Contextual sources:**

- **Christopher Bishop — Pattern Recognition and Machine Learning** (`source-bishop-prml`) — roles: derivation — level: advanced — complete derivations

## Hypothesis testing

`concept-hypothesis-testing`

Aliases: Hypothesentest · p-Wert · p-value · significance level

**Notes:**

- `note-p-values-corrected` — What a p-value actually is *(role: synthesis)*
- `note-p-values-first-take` — p-values (first take) *(role: synthesis)*

**Contextual sources:**

- **Wasserstein & Lazar — The ASA Statement on p-Values (2016)** (`source-wasserstein-asa-2016`) — roles: review — level: intermediate — lists the six principles; corrects the common misreading

## Idempotency

`concept-idempotency`

Aliases: idempotency key · idempotent

**Notes:**

- `note-idempotency-keys-api` — Idempotency keys *(role: synthesis)*
- `note-idempotent-pipelines-backfills` — Idempotent pipeline steps *(role: synthesis)*

## Instruction pipelining

`concept-instruction-pipelining`

Aliases: pipeline hazard · stall

**Notes:**

- `note-cpu-instruction-pipeline` — Instruction pipelining *(role: synthesis)*

## Join algorithms

`concept-join-algorithms`

Aliases: hash join · nested loop join · sort-merge join

**Notes:**

- `note-hash-join-vs-sort-merge` — Hash join versus sort-merge join *(role: synthesis)*
- `note-selinger-join-ordering` — System R join ordering *(role: synthesis)*

**Related concepts:**

- applies-in → `concept-query-optimization`

**Contextual sources:**

- **Garcia-Molina, Ullman, Widom — Database Systems: The Complete Book** (`source-garcia-molina-db`) — roles: first-learning, reference — level: intermediate — recovery chapter is the clearest treatment of undo/redo logging

## Journaling file systems

`concept-journaling-file-systems`

Aliases: crash consistency · journaling

**Notes:**

- `note-journaling-filesystems` — Journaling file systems *(role: synthesis)*

**Contextual sources:**

- **Arpaci-Dusseau — Operating Systems: Three Easy Pieces** (`source-ostep`) — roles: first-learning, review — level: introductory — lottery and stride scheduling chapter; crash-consistency chapter

## Kernel density estimation

`concept-kernel-density-estimation`

Aliases: KDE · Parzen window

**Notes:**

- `note-kernel-density-estimation` — Kernel density estimation *(role: synthesis)*

## KV cache

`concept-kv-cache`

Aliases: key-value cache

**Notes:**

- `note-kv-cache-transformer-serving` — The KV cache in transformer inference *(role: synthesis)*

**Related concepts:**

- applies-in → `concept-model-serving`

**Contextual sources:**

- **Kwon et al. — Efficient Memory Management for LLM Serving with PagedAttention (2023)** (`source-kwon-pagedattention-2023`) — roles: first-learning — level: advanced — block-based KV memory

## Lazy evaluation

`concept-lazy-evaluation`

Aliases: deferred execution · lazy frame

**Notes:**

- `note-lazy-evaluation-query-plans` — Lazy frames build a plan first *(role: synthesis)*

**Contextual sources:**

- **Polars user guide — Lazy API** (`source-polars-guide`) — roles: first-learning — level: introductory — explain() output walkthrough

## Linear regression

`concept-linear-regression`

Aliases: least squares · lineare Regression

**Notes:**

- `note-gaussian-noise-least-squares` — Why least squares falls out of Gaussian noise *(role: derivation)*
- `note-gradient-descent-from-scratch` — Gradient descent from scratch (housing exercise) *(role: implementation)*
- `note-linear-regression-normal-equation` — Linear regression — the normal equation *(role: derivation)*
- `note-ridge-regression-penalty` — Ridge regression *(role: derivation)*

**Related concepts:**

- ← applies-in from `concept-gradient-descent`

## Logistic regression

`concept-logistic-regression`

Aliases: logistische Regression · sigmoid

**Notes:**

- `note-generative-vs-discriminative` — Generative versus discriminative classifiers *(role: synthesis)*
- `note-logistic-regression-cross-entropy` — Logistic regression and where cross-entropy comes from *(role: derivation)*

**Related concepts:**

- requires → `concept-conditional-probability`

**Contextual sources:**

- **Christopher Bishop — Pattern Recognition and Machine Learning** (`source-bishop-prml`) — roles: derivation — level: advanced — complete derivations

## Low-rank approximation

`concept-low-rank-approximation`

Aliases: Eckart–Young · truncated SVD

**Notes:**

- `note-low-rank-approximation` — Low-rank approximation (unfinished) *(role: synthesis)*

**Related concepts:**

- builds-on → `concept-svd`

**Contextual sources:**

- **Gilbert Strang — Introduction to Linear Algebra (5th ed.)** (`source-strang-linalg`) — roles: first-learning, derivation — level: introductory — geometric intuition first

## LSM trees

`concept-lsm-trees`

Aliases: SSTable · compaction · log-structured merge tree

**Notes:**

- `note-lsm-trees` — LSM trees *(role: synthesis)*

**Related concepts:**

- requires → `concept-bloom-filters`

**Contextual sources:**

- **Martin Kleppmann — Designing Data-Intensive Applications** (`source-kleppmann-ddia`) — roles: first-learning, review — level: intermediate — separates the many meanings of consistency

## MAP estimation

`concept-map-estimation`

Aliases: maximum a posteriori · prior

**Notes:**

- `note-map-estimation-priors` — MAP estimation — a prior turns into an extra term *(role: derivation)*

**Related concepts:**

- builds-on → `concept-maximum-likelihood`

**Contextual sources:**

- **Kevin Murphy — Probabilistic Machine Learning: An Introduction** (`source-murphy-pml1`) — roles: derivation, review — level: intermediate — probabilistic view throughout; ridge as MAP made explicit

## Markov chains

`concept-markov-chains`

Aliases: Markov-Kette · stationary distribution

**Notes:**

- `note-markov-chains-stationary` — Markov chains and stationary distributions *(role: synthesis)*

**Related concepts:**

- ← requires from `concept-hidden-markov-models`

## Matrix factorization

`concept-matrix-factorization`

Aliases: collaborative filtering · recommender systems

**Notes:**

- `note-matrix-factorization-recommenders` — Matrix factorization for recommendations *(role: synthesis)*

## Maximum likelihood estimation

`concept-maximum-likelihood`

Aliases: MLE · Maximum-Likelihood-Schätzung · likelihood

**Notes:**

- `note-gaussian-noise-least-squares` — Why least squares falls out of Gaussian noise *(role: derivation)*
- `note-mle-coin-flips` — Maximum likelihood for a coin *(role: derivation)*
- `note-statlearn-mock-exam-september` — Statistical Learning — mock exam 1 *(role: mock-exam)*

**Related concepts:**

- derives → `concept-mean-squared-error`
- ← builds-on from `concept-map-estimation`

**Contextual sources:**

- **Kevin Murphy — Probabilistic Machine Learning: An Introduction** (`source-murphy-pml1`) — roles: derivation, review — level: intermediate — probabilistic view throughout; ridge as MAP made explicit
- **TU Havelberg — Statistical Learning lecture slides (SoSe 2026)** (`source-tuh-statlearn-slides`) — roles: first-learning — level: intermediate — defines the exam scope; notation matches the exam

## Mean squared error

`concept-mean-squared-error`

Aliases: MSE · squared loss

**Related concepts:**

- ← derives from `concept-maximum-likelihood`

## Mixed-precision training

`concept-mixed-precision`

Aliases: bf16 · fp16 · loss scaling

**Notes:**

- `note-mixed-precision-training` — Mixed-precision training *(role: synthesis)*

## Model serving

`concept-model-serving`

Aliases: dynamic batching · inference serving

**Notes:**

- `note-dynamic-batching-inference` — Dynamic batching in model serving *(role: synthesis)*
- `note-kv-cache-transformer-serving` — The KV cache in transformer inference *(role: synthesis)*
- `note-multi-tenant-gpu-sharing` — Sharing one inference cluster between teams *(role: synthesis)*

**Related concepts:**

- ← applies-in from `concept-kv-cache`

**Contextual sources:**

- **Chip Huyen — Designing Machine Learning Systems** (`source-huyen-dmls`) — roles: first-learning — level: introductory — practical serving trade-offs; leakage chapter

## Naive Bayes

`concept-naive-bayes`

Aliases: naiver Bayes-Klassifikator

**Notes:**

- `note-generative-vs-discriminative` — Generative versus discriminative classifiers *(role: synthesis)*
- `note-naive-bayes-spam-filter` — Naive Bayes for the spam exercise *(role: synthesis)*
- `note-statlearn-mock-exam-september` — Statistical Learning — mock exam 1 *(role: mock-exam)*

**Related concepts:**

- requires → `concept-bayes-theorem`

**Contextual sources:**

- **Kevin Murphy — Probabilistic Machine Learning: An Introduction** (`source-murphy-pml1`) — roles: derivation, review — level: intermediate — probabilistic view throughout; ridge as MAP made explicit
- **TU Havelberg — Statistical Learning lecture slides (SoSe 2026)** (`source-tuh-statlearn-slides`) — roles: first-learning — level: intermediate — defines the exam scope; notation matches the exam

## Normal distribution

`concept-normal-distribution`

Aliases: Gaussian · Normalverteilung · standardization · z-score

**Notes:**

- `note-normal-distribution-standardizing` — Standardizing and z-scores *(role: synthesis)*

## Normal equation

`concept-normal-equation`

Aliases: Normalgleichung · closed-form least squares

**Notes:**

- `note-linear-regression-normal-equation` — Linear regression — the normal equation *(role: derivation)*

**Related concepts:**

- contrasts-with → `concept-gradient-descent`

## Operating-system kernel

`concept-os-kernel`

Aliases: Betriebssystemkern · kernel mode · system call

**Notes:**

- `note-os-kernel-user-mode` — Kernel mode, user mode and system calls *(role: synthesis)*

## Overfitting

`concept-overfitting`

Aliases: generalization gap · Überanpassung

**Notes:**

- `note-overfitting-polynomial-degree` — Overfitting — polynomial degree experiment *(role: implementation)*

**Related concepts:**

- motivates → `concept-regularization`

## Page replacement

`concept-page-replacement`

Aliases: LRU · Seitenersetzung · clock algorithm

**Notes:**

- `note-page-replacement-lru-clock` — Page replacement — FIFO, LRU, clock *(role: synthesis)*

**Related concepts:**

- builds-on → `concept-virtual-memory`

**Contextual sources:**

- **Arpaci-Dusseau — Operating Systems: Three Easy Pieces** (`source-ostep`) — roles: first-learning, review — level: introductory — lottery and stride scheduling chapter; crash-consistency chapter

## Principal component analysis

`concept-pca`

Aliases: Hauptkomponentenanalyse · PCA

**Notes:**

- `note-pca-by-hand` — PCA by hand on a 2-D toy dataset *(role: implementation)*
- `note-statlearn-mock-exam-september` — Statistical Learning — mock exam 1 *(role: mock-exam)*

**Related concepts:**

- requires → `concept-covariance-matrix`
- requires → `concept-eigendecomposition`

**Contextual sources:**

- **Christopher Bishop — Pattern Recognition and Machine Learning** (`source-bishop-prml`) — roles: derivation — level: advanced — complete derivations
- **TU Havelberg — Statistical Learning lecture slides (SoSe 2026)** (`source-tuh-statlearn-slides`) — roles: first-learning — level: intermediate — defines the exam scope; notation matches the exam

## Priority inversion

`concept-priority-inversion`

Aliases: priority inheritance

**Notes:**

- `note-priority-inversion` — Priority inversion *(role: synthesis)*

## Probability

`concept-probability`

Aliases: Wahrscheinlichkeit · probability axioms

**Notes:**

- `note-bloom-filter-false-positive-math` — How often a Bloom filter lies *(role: derivation)*

## Property-based testing

`concept-property-based-testing`

Aliases: QuickCheck · shrinking

**Notes:**

- `note-property-based-testing` — Property-based testing *(role: synthesis)*

## Proportional-share scheduling

`concept-proportional-share`

Aliases: CFS · fair-share scheduling · lottery scheduling · vruntime

**Notes:**

- `note-cfs-fair-share` — Proportional share and Linux CFS *(role: synthesis)*
- `note-os-scheduling-exercise-bank` — OS scheduling — exercise bank *(role: exercise-bank)*

**Related concepts:**

- builds-on → `concept-cpu-scheduling`

**Contextual sources:**

- **Arpaci-Dusseau — Operating Systems: Three Easy Pieces** (`source-ostep`) — roles: first-learning, review — level: introductory — lottery and stride scheduling chapter; crash-consistency chapter
- **Waldspurger & Weihl — Stride Scheduling (1995)** (`source-waldspurger-stride-1995`) — roles: derivation — level: advanced — deterministic proportional share with pass values

## Query optimization

`concept-query-optimization`

Aliases: Anfrageoptimierung · predicate pushdown · query plan

**Notes:**

- `note-algebraic-equivalences-pushdown` — Algebraic equivalences and pushing selections down *(role: synthesis)*
- `note-db-exam-cheatsheet` — Database Systems — exam cheat sheet *(role: reference)*
- `note-lazy-evaluation-query-plans` — Lazy frames build a plan first *(role: synthesis)*
- `note-query-optimizer-cost-model` — Cost models and selectivity *(role: synthesis)*
- `note-selinger-join-ordering` — System R join ordering *(role: synthesis)*

**Related concepts:**

- requires → `concept-relational-algebra`
- ← applies-in from `concept-cardinality-estimation`
- ← applies-in from `concept-join-algorithms`

**Contextual sources:**

- **Garcia-Molina, Ullman, Widom — Database Systems: The Complete Book** (`source-garcia-molina-db`) — roles: first-learning, reference — level: intermediate — recovery chapter is the clearest treatment of undo/redo logging
- **Polars user guide — Lazy API** (`source-polars-guide`) — roles: first-learning — level: introductory — explain() output walkthrough
- **Selinger et al. — Access Path Selection in a Relational Database Management System (1979)** (`source-selinger-1979`) — roles: derivation — level: advanced — the original cost-based join-order search
- **TU Havelberg — Database Systems lecture slides (SoSe 2026)** (`source-tuh-dbsys-slides`) — roles: first-learning — level: intermediate — exam-aligned; good worked plan-rewrite examples

## Queueing theory

`concept-queueing-theory`

Aliases: Little's law · arrival rate

**Notes:**

- `note-queueing-littles-law` — Little's law *(role: synthesis)*

## Regression metrics

`concept-regression-metrics`

Aliases: MAE · RMSE · R²

**Notes:**

- `note-regression-metrics` — Regression metrics *(role: reference)*

## Regression testing

`concept-regression-testing`

Aliases: golden file · snapshot test

**Notes:**

- `note-regression-testing-snapshots` — Regression tests and snapshot files *(role: synthesis)*

## Regularization

`concept-regularization`

Aliases: L1 penalty · L2 penalty · Regularisierung · lasso · ridge · weight decay

**Notes:**

- `note-lasso-sparsity-geometry` — Why the lasso sets weights exactly to zero *(role: synthesis)*
- `note-ridge-regression-penalty` — Ridge regression *(role: derivation)*
- `note-statlearn-mock-exam-september` — Statistical Learning — mock exam 1 *(role: mock-exam)*

**Related concepts:**

- ← motivates from `concept-overfitting`

**Contextual sources:**

- **Hastie, Tibshirani, Friedman — The Elements of Statistical Learning** (`source-esl`) — roles: reference — level: advanced — lasso geometry figure; honest about cross-validation pitfalls
- **Kevin Murphy — Probabilistic Machine Learning: An Introduction** (`source-murphy-pml1`) — roles: derivation, review — level: intermediate — probabilistic view throughout; ridge as MAP made explicit
- **TU Havelberg — Statistical Learning lecture slides (SoSe 2026)** (`source-tuh-statlearn-slides`) — roles: first-learning — level: intermediate — defines the exam scope; notation matches the exam

## Relational algebra

`concept-relational-algebra`

Aliases: join · projection · relationale Algebra · selection

**Notes:**

- `note-algebraic-equivalences-pushdown` — Algebraic equivalences and pushing selections down *(role: synthesis)*
- `note-db-exam-cheatsheet` — Database Systems — exam cheat sheet *(role: reference)*
- `note-relational-algebra-operators` — Relational algebra operators *(role: reference)*

**Related concepts:**

- ← requires from `concept-query-optimization`

**Contextual sources:**

- **Garcia-Molina, Ullman, Widom — Database Systems: The Complete Book** (`source-garcia-molina-db`) — roles: first-learning, reference — level: intermediate — recovery chapter is the clearest treatment of undo/redo logging
- **TU Havelberg — Database Systems lecture slides (SoSe 2026)** (`source-tuh-dbsys-slides`) — roles: first-learning — level: intermediate — exam-aligned; good worked plan-rewrite examples

## Rust ownership

`concept-rust-ownership`

Aliases: borrow checker · lifetimes

**Notes:**

- `note-error-handling-result-types` — Errors as values *(role: synthesis)*
- `note-rust-ownership-borrowing` — Rust ownership and borrowing *(role: synthesis)*
- `note-tagless-visitor-pattern-ast` — Rewriting plan trees with a visitor *(role: implementation)*

**Contextual sources:**

- **The Rust Programming Language** (`source-rust-book`) — roles: first-learning — level: introductory — ownership chapter

## Simulated annealing

`concept-simulated-annealing`

Aliases: annealing schedule

**Notes:**

- `note-simulated-annealing` — Simulated annealing *(role: implementation)*

## Softmax

`concept-softmax`

Aliases: logits · temperature scaling

**Notes:**

- `note-softmax-temperature` — Softmax and temperature *(role: synthesis)*

## Spaced repetition

`concept-spaced-repetition`

Aliases: Anki · SM-2 · review scheduler

**Notes:**

- `note-spaced-repetition-scheduler` — How the review scheduler decides *(role: synthesis)*

**Contextual sources:**

- **Anki manual — scheduling** (`source-anki-manual`) — roles: reference — level: introductory — explains interval growth and lapses

## Static single assignment

`concept-ssa`

Aliases: SSA · phi node

**Notes:**

- `note-ssa-form` — Static single assignment *(role: synthesis)*

**Related concepts:**

- applies-in → `concept-compiler-optimization`

**Contextual sources:**

- **Aho, Lam, Sethi, Ullman — Compilers: Principles, Techniques, and Tools** (`source-dragon-book`) — roles: reference — level: advanced — dataflow analysis chapter

## Statistical estimation

`concept-statistical-estimation`

Aliases: consistent estimator · estimator · point estimation · unbiased estimator

**Notes:**

- `note-bias-variance-from-book` — Bias and variance, rewritten from Murphy *(role: synthesis)*
- `note-consistent-estimators` — Unbiased versus consistent estimators *(role: synthesis)*

## Stochastic gradient descent

`concept-stochastic-gradient-descent`

Aliases: SGD · minibatch · momentum

**Notes:**

- `note-adam-vs-sgd-revisited` — Adam versus SGD, revisited *(role: synthesis)*
- `note-batchnorm-why-it-works-contested` — Why batch norm works is contested *(role: synthesis)*
- `note-sgd-momentum-nn-training` — Training a small MLP — minibatches and momentum *(role: implementation)*

**Related concepts:**

- builds-on → `concept-gradient-descent`

**Contextual sources:**

- **Goodfellow, Bengio, Courville — Deep Learning** (`source-goodfellow-dl`) — roles: first-learning, reference — level: intermediate — chapter 6 computational graphs; chapter 8 optimization
- **Wilson et al. — The Marginal Value of Adaptive Gradient Methods (2017)** (`source-wilson-adaptive-2017`) — roles: review — level: advanced — generalization comparison that tempers the "Adam everywhere" habit

## Stream processing

`concept-stream-processing`

Aliases: Kafka · backpressure · consumer lag

**Notes:**

- `note-kafka-consumer-lag-backpressure` — Consumer lag and backpressure *(role: synthesis)*

**Contextual sources:**

- **Martin Kleppmann — Designing Data-Intensive Applications** (`source-kleppmann-ddia`) — roles: first-learning, review — level: intermediate — separates the many meanings of consistency

## Study planning

`concept-study-planning`

Aliases: Lernplan · retake strategy

**Notes:**

- `note-oral-exam-prep-strategy` — Preparing for an oral exam *(role: synthesis)*
- `note-pomodoro-and-context-switching` — Pomodoro and the cost of switching subjects *(role: synthesis)*
- `note-semester-review-july` — End-of-semester review (July) *(role: synthesis)*
- `note-study-plan-retake-strategy` — Retake plan — splitting time fairly between two exams *(role: synthesis)*
- `note-weekly-review-log` — Weekly review log (summer) *(role: synthesis)*

## Singular value decomposition

`concept-svd`

Aliases: SVD · Singulärwertzerlegung

**Notes:**

- `note-low-rank-approximation` — Low-rank approximation (unfinished) *(role: synthesis)*
- `note-svd-geometric` — SVD as rotate–stretch–rotate *(role: synthesis)*

**Related concepts:**

- generalizes → `concept-eigendecomposition`
- ← builds-on from `concept-low-rank-approximation`

**Contextual sources:**

- **Gilbert Strang — Introduction to Linear Algebra (5th ed.)** (`source-strang-linalg`) — roles: first-learning, derivation — level: introductory — geometric intuition first

## Support vector machines

`concept-svm`

Aliases: RBF · SVM · kernel trick

**Notes:**

- `note-svm-kernel-trick` — SVMs and the kernel trick *(role: synthesis)*

## Synchronization

`concept-synchronization`

Aliases: Synchronisation · mutex · producer-consumer · semaphore

**Notes:**

- `note-deadlock-four-conditions` — Deadlock — the four conditions *(role: synthesis)*
- `note-priority-inversion` — Priority inversion *(role: synthesis)*
- `note-semaphores-producer-consumer` — Semaphores and the bounded buffer *(role: derivation)*

**Related concepts:**

- ← requires from `concept-deadlock`

**Contextual sources:**

- **Silberschatz, Galvin, Gagne — Operating System Concepts** (`source-silberschatz-os`) — roles: reference — level: intermediate — exhaustive; banker's algorithm worked examples

## Transactions and ACID

`concept-transactions-acid`

Aliases: ACID · Transaktion

**Notes:**

- `note-acid-consistency` — ACID — and what the C means *(role: synthesis)*
- `note-cap-consistency-linearizability` — The C in CAP is not the C in ACID *(role: synthesis)*
- `note-two-phase-locking-deadlocks` — Two-phase locking and deadlocks *(role: synthesis)*
- `note-write-ahead-logging-aries` — Write-ahead logging and ARIES recovery *(role: synthesis)*

**Related concepts:**

- ← applies-in from `concept-write-ahead-logging`
- ← requires from `concept-two-phase-locking`

**Contextual sources:**

- **Martin Kleppmann — Designing Data-Intensive Applications** (`source-kleppmann-ddia`) — roles: first-learning, review — level: intermediate — separates the many meanings of consistency
- **TU Havelberg — Database Systems lecture slides (SoSe 2026)** (`source-tuh-dbsys-slides`) — roles: first-learning — level: intermediate — exam-aligned; good worked plan-rewrite examples

## Two-phase locking

`concept-two-phase-locking`

Aliases: 2PL · Zwei-Phasen-Sperrprotokoll

**Notes:**

- `note-db-exam-cheatsheet` — Database Systems — exam cheat sheet *(role: reference)*
- `note-two-phase-locking-deadlocks` — Two-phase locking and deadlocks *(role: synthesis)*

**Related concepts:**

- requires → `concept-transactions-acid`

**Contextual sources:**

- **Garcia-Molina, Ullman, Widom — Database Systems: The Complete Book** (`source-garcia-molina-db`) — roles: first-learning, reference — level: intermediate — recovery chapter is the clearest treatment of undo/redo logging

## Type inference

`concept-type-inference`

Aliases: Hindley–Milner · unification

**Notes:**

- `note-type-inference-unification` — Type inference by unification *(role: synthesis)*

**Contextual sources:**

- **Aho, Lam, Sethi, Ullman — Compilers: Principles, Techniques, and Tools** (`source-dragon-book`) — roles: reference — level: advanced — dataflow analysis chapter

## Virtual memory

`concept-virtual-memory`

Aliases: TLB · page table · paging · virtueller Speicher

**Notes:**

- `note-virtual-memory-address-translation` — Virtual memory is address translation *(role: synthesis)*
- `note-virtual-memory-is-swap` — Virtual memory *(role: synthesis)*

**Related concepts:**

- ← builds-on from `concept-page-replacement`

**Contextual sources:**

- **Arpaci-Dusseau — Operating Systems: Three Easy Pieces** (`source-ostep`) — roles: first-learning, review — level: introductory — lottery and stride scheduling chapter; crash-consistency chapter
- **TU Havelberg — Operating Systems lecture slides (SoSe 2026)** (`source-tuh-os-slides`) — roles: first-learning — level: introductory — clear diagrams of scheduling timelines

## Visitor pattern

`concept-visitor-pattern`

Aliases: AST traversal · tree rewriting

**Notes:**

- `note-tagless-visitor-pattern-ast` — Rewriting plan trees with a visitor *(role: implementation)*

**Contextual sources:**

- **Robert Nystrom — Crafting Interpreters** (`source-crafting-interpreters`) — roles: first-learning, implementation — level: introductory — visitor-based tree walking explained with working code

## Workflow orchestration

`concept-workflow-orchestration`

Aliases: Airflow · task DAG

**Notes:**

- `note-data-pipeline-orchestration-dag` — Pipelines as DAGs of tasks *(role: synthesis)*
- `note-idempotent-pipelines-backfills` — Idempotent pipeline steps *(role: synthesis)*

## Write-ahead logging

`concept-write-ahead-logging`

Aliases: ARIES · WAL · redo log

**Notes:**

- `note-db-exam-cheatsheet` — Database Systems — exam cheat sheet *(role: reference)*
- `note-write-ahead-logging-aries` — Write-ahead logging and ARIES recovery *(role: synthesis)*

**Related concepts:**

- applies-in → `concept-transactions-acid`

**Contextual sources:**

- **Garcia-Molina, Ullman, Widom — Database Systems: The Complete Book** (`source-garcia-molina-db`) — roles: first-learning, reference — level: intermediate — recovery chapter is the clearest treatment of undo/redo logging
- **Mohan et al. — ARIES (1992)** (`source-mohan-aries-1992`) — roles: reference — level: advanced — authoritative; far beyond exam depth

