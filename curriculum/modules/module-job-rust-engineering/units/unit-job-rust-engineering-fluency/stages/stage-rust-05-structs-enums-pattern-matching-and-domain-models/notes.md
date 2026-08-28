# Stage Working Notes

## Mental Models

### Domain model

Enums encode alternatives with their data; exhaustive matching turns domain change into a visible engineering event.

### Invariant model

Constructors and private fields keep invalid states out of the rest of the program.

## Read-only Anchor

Read-only: small state carriers and result shapes in _rust/src/csr.rs, _rust/src/fd.rs, and _rust/src/truncated_svd.rs.

## Component

- _rust/src/csr.rs
- _rust/src/fd.rs
- _rust/src/truncated_svd.rs

## Verified Against



## External Code Boundary

Any Stratum paths above refer to the sibling `semestercontext/Stratum/` worktree. They are optional read-only learning anchors: LearningOS does not index, validate, manage, or write that codebase.
