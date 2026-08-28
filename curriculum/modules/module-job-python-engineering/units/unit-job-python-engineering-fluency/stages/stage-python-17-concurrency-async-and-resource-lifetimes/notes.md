# Stage Working Notes

## Mental Models

### Concurrency model

Concurrency is about overlapping work and coordinating ownership; parallel speedup is a separate claim requiring measurement.

### Cancellation model

Cancellation is a normal control path that must preserve invariants and release resources, not an exceptional afterthought.

### Selection model

Sequential code is often the best design until latency, throughput, blocking, or isolation requirements justify another model.

### Engineering ownership

AI may critique only after your own model and first attempt exist. You remain responsible for the specification, trade-offs, every accepted line, tests, failure behavior, and maintenance cost.

## Read-only Anchor

Read-only: stratum/runtime/_scheduler.py, optimizer execution orchestration, _rust/src/threads.rs, and stratum/_rust_backend.py configuration. Observe responsibilities only.

## Component

- _rust/src/threads.rs
- stratum/_rust_backend.py
- stratum/runtime/_scheduler.py

## Verified Against



## External Code Boundary

Any Stratum paths above refer to the sibling `semestercontext/Stratum/` worktree. They are optional read-only learning anchors: LearningOS does not index, validate, manage, or write that codebase.
