# Stage Working Notes

## Mental Models

### Borrow model

Many readers or one writer is an aliasing contract, not just compiler syntax.

### API model

Prefer borrowed views for inputs and return ownership only when the result must outlive its source.

## Read-only Anchor

Read-only: slice and Vec boundaries in _rust/src/csr.rs, _rust/src/tokenize.rs, _rust/src/one_hot_encoder.rs, and _rust/src/lib.rs.

## Component

- _rust/src/csr.rs
- _rust/src/lib.rs
- _rust/src/one_hot_encoder.rs
- _rust/src/tokenize.rs

## Verified Against



## External Code Boundary

Any Stratum paths above refer to the sibling `semestercontext/Stratum/` worktree. They are optional read-only learning anchors: LearningOS does not index, validate, manage, or write that codebase.
