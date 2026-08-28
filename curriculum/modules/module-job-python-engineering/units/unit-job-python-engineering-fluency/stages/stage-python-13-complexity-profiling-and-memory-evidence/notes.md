# Stage Working Notes

## Mental Models

### Python model

algorithmic complexity is reasoned about before measurement; cProfile locates cumulative cost, timeit measures a controlled micro-operation, tracemalloc attributes allocations, and benchmarks separate setup from the work under test.

### Stratum relevance

a pass over large DAGs and BufferPool behavior can be dominated by traversal shape, allocation, conversion, or per-node dispatch.

### Failure mode

optimizing intuition, measuring construction with execution, comparing debug and release paths, or treating one noisy timing as evidence.

### Engineering ownership

AI may critique only after your own model and first attempt exist. You remain responsible for the specification, trade-offs, every accepted line, tests, failure behavior, and maintenance cost.

## Read-only Anchor

Read-only: optimizer pass orchestration in stratum/optimizer/_optimize.py; start_time/log_time in stratum/utils/_utils.py; object lifecycle and stats in stratum/runtime/_buffer_pool.py; slotted IR node definitions.

## Component

- stratum/optimizer/_optimize.py
- stratum/runtime/_buffer_pool.py
- stratum/utils/_utils.py

## Verified Against



## External Code Boundary

Any Stratum paths above refer to the sibling `semestercontext/Stratum/` worktree. They are optional read-only learning anchors: LearningOS does not index, validate, manage, or write that codebase.
