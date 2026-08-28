# Stage Working Notes

## Mental Models

### Lifetime model

Annotations describe relationships already present; they do not extend an object's life.

### Design model

A difficult lifetime can reveal confused ownership and may call for an owned boundary instead of more annotations.

## Read-only Anchor

Read-only: borrowed array and iterator parameters at the PyO3 boundary in _rust/src/lib.rs and _rust/src/one_hot_encoder.rs.

## Component

- _rust/src/lib.rs
- _rust/src/one_hot_encoder.rs

## Verified Against



## External Code Boundary

Any Stratum paths above refer to the sibling `semestercontext/Stratum/` worktree. They are optional read-only learning anchors: LearningOS does not index, validate, manage, or write that codebase.
