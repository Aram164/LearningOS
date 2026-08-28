# Stage Working Notes

## Mental Models

### Tool model

wall time, CPU time, allocation/memory growth, I/O wait, and algorithmic work are different resources; profilers sample or instrument where resources are spent. A benchmark is an experiment requiring controlled inputs, warm-up, repetition, variance, and a meaningful baseline.

### Working practice

measure before optimizing, identify the dominant resource and hotspot, change one mechanism, remeasure correctness and performance, and report uncertainty.

### Job relevance

Polars/Pandas backend choices and optimizer rewrites need query-plan and runtime evidence rather than intuition.

### Failure mode

timing one noisy run, optimizing a non-hot path, changing semantics, or presenting percentage improvement without absolute scale.

## Read-only Anchor

Read-only in Stratum: inspect existing benchmark definitions and one physical-plan or explain path. Do not run a benchmark that writes artifacts into Stratum; reproduce a small equivalent in Job scratch or another disposable lab.

## Component


## Verified Against



## External Code Boundary

Any Stratum paths above refer to the sibling `semestercontext/Stratum/` worktree. They are optional read-only learning anchors: LearningOS does not index, validate, manage, or write that codebase.
