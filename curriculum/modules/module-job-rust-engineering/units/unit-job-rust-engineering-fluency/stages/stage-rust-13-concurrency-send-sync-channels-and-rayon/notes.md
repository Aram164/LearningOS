# Stage Working Notes

## Mental Models

### Concurrency model

Ownership and Send/Sync constrain which state may cross threads; they do not prove higher-level algorithm correctness.

### Performance model

Parallelism is an optimization with overhead and determinism costs, not a default architecture.

## Read-only Anchor

Read-only: _rust/src/threads.rs, Rayon use across _rust/src, and Python configuration in stratum/_rust_backend.py.

## Component

- _rust/src
- _rust/src/threads.rs
- stratum/_rust_backend.py

## Verified Against



## External Code Boundary

Any Stratum paths above refer to the sibling `semestercontext/Stratum/` worktree. They are optional read-only learning anchors: LearningOS does not index, validate, manage, or write that codebase.
