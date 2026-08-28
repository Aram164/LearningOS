# Stage Working Notes

## Mental Models

### Specification model

Code cannot rescue an unclear problem. Examples, non-goals, invariants, failures, and acceptance criteria turn intent into something testable.

### Decomposition model

A thin vertical slice crosses real boundaries and reduces uncertainty; a pile of generated modules can hide it.

### Decision model

Engineering judgment is visible in trade-offs, rejected options, and reversal cost—not in confident prose.

### Engineering ownership

AI may critique only after your own model and first attempt exist. You remain responsible for the specification, trade-offs, every accepted line, tests, failure behavior, and maintenance cost.

## Read-only Anchor

Read-only: choose one bounded Stratum operation family and reconstruct its apparent contract from public call sites, tests, and error paths. Do not use implementation details to write the no-AI slice.

## Component


## Verified Against



## External Code Boundary

Any Stratum paths above refer to the sibling `semestercontext/Stratum/` worktree. They are optional read-only learning anchors: LearningOS does not index, validate, manage, or write that codebase.
