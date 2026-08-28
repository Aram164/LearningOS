# Stage Working Notes

## Mental Models

### Error model

Errors are part of the API: classify expected conditions, preserve causes, and avoid catching exceptions you cannot resolve or contextualize.

### Observability model

Emit facts at meaningful boundaries so behavior can be reconstructed without exposing secrets or flooding logs.

### Debugging model

Form a hypothesis, gather discriminating evidence, reduce the reproducer, and preserve the fix as a regression test.

### Engineering ownership

AI may critique only after your own model and first attempt exist. You remain responsible for the specification, trade-offs, every accepted line, tests, failure behavior, and maintenance cost.

## Read-only Anchor

Read-only: timing and configuration in stratum/utils/_utils.py and stratum/_rust_backend.py, plus failure paths in stratum/runtime/_scheduler.py, stratum/runtime/_buffer_pool.py, and one physical implementation.

## Component

- stratum/_rust_backend.py
- stratum/runtime/_buffer_pool.py
- stratum/runtime/_scheduler.py
- stratum/utils/_utils.py

## Verified Against



## External Code Boundary

Any Stratum paths above refer to the sibling `semestercontext/Stratum/` worktree. They are optional read-only learning anchors: LearningOS does not index, validate, manage, or write that codebase.
