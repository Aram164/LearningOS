# Stage Working Notes

## Mental Models

### Async model

An async function creates a Future; progress occurs only when an executor polls it.

### Boundary model

CPU-bound dataframe kernels usually need threads or native parallelism, while async primarily coordinates waiting.

## Read-only Anchor

Read-only orientation: compare the absence or presence of async in _rust and the scheduler responsibilities in stratum/runtime/_scheduler.py.

## Component

- stratum/runtime/_scheduler.py

## Verified Against



## External Code Boundary

Any Stratum paths above refer to the sibling `semestercontext/Stratum/` worktree. They are optional read-only learning anchors: LearningOS does not index, validate, manage, or write that codebase.
