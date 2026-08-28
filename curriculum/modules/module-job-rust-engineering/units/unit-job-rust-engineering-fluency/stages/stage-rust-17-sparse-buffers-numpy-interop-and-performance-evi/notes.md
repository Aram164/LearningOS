# Stage Working Notes

## Mental Models

### Layout model

Logical arrays have dtype, shape, stride, index, and ownership contracts that cross-language code must preserve.

### Benchmark model

Conversion, allocation, scheduling, and kernel work must be timed separately before attributing a speedup to Rust.

## Read-only Anchor

Read-only: _rust/src/csr.rs, _rust/src/one_hot_encoder.rs, _rust/src/fd.rs, _rust/src/truncated_svd.rs, and the corresponding wrappers exported from _rust/src/lib.rs.

## Component

- _rust/src/csr.rs
- _rust/src/fd.rs
- _rust/src/lib.rs
- _rust/src/one_hot_encoder.rs
- _rust/src/truncated_svd.rs

## Verified Against



## External Code Boundary

Any Stratum paths above refer to the sibling `semestercontext/Stratum/` worktree. They are optional read-only learning anchors: LearningOS does not index, validate, manage, or write that codebase.
