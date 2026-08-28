# Stage Working Notes

## Mental Models

### Error model

Library callers need structured variants; application edges need context and a humane presentation.

### Dependency model

A crate saves code but adds an API, release, feature, and security relationship you must own.

## Read-only Anchor

Read-only: error conversion and dependencies in _rust/Cargo.toml, _rust/src/fd.rs, _rust/src/truncated_svd.rs, _rust/src/one_hot_encoder.rs, and _rust/src/lib.rs.

## Component

- _rust/Cargo.toml
- _rust/src/fd.rs
- _rust/src/lib.rs
- _rust/src/one_hot_encoder.rs
- _rust/src/truncated_svd.rs

## Verified Against



## External Code Boundary

Any Stratum paths above refer to the sibling `semestercontext/Stratum/` worktree. They are optional read-only learning anchors: LearningOS does not index, validate, manage, or write that codebase.
