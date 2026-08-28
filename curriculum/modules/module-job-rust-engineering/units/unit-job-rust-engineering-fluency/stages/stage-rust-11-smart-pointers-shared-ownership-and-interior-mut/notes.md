# Stage Working Notes

## Mental Models

### Pointer model

Smart pointers encode ownership or synchronization policies; the type should communicate the policy.

### Complexity check

Shared ownership increases coordination cost and should follow a proven requirement.

## Read-only Anchor

Read-only: global and shared state choices in _rust/src/threads.rs, _rust/src/util.rs, and model registries in _rust/src/fd.rs and _rust/src/truncated_svd.rs.

## Component

- _rust/src/fd.rs
- _rust/src/threads.rs
- _rust/src/truncated_svd.rs
- _rust/src/util.rs

## Verified Against



## External Code Boundary

Any Stratum paths above refer to the sibling `semestercontext/Stratum/` worktree. They are optional read-only learning anchors: LearningOS does not index, validate, manage, or write that codebase.
