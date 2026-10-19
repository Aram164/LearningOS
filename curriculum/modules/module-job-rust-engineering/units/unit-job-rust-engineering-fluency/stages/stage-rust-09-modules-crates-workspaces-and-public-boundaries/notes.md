# Stage Working Notes

## Mental Models

### Boundary model

A module is a namespace and privacy boundary; a crate is a compilation and distribution unit.

### API model

Make the smallest stable surface public and keep construction invariants behind it.

## Read-only Anchor

Read-only: _rust/Cargo.toml and _rust/src/lib.rs module declarations and exported PyO3 function registrations.

## Component

- _rust/Cargo.toml
- _rust/src/lib.rs

## Verified Against



## External Code Boundary

Any Stratum paths above refer to the sibling `semestercontext/Stratum/` worktree. They are optional read-only learning anchors: LearningOS does not index, validate, manage, or write that codebase.
