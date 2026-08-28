# Stage Working Notes

## Mental Models

### Dispatch model

Generics and impl Trait use static dispatch; dyn Trait trades concrete type knowledge for runtime polymorphism.

### Interface model

A useful trait states behavior and laws, not merely a list of methods shared by current classes.

## Read-only Anchor

Read-only: generic helpers and crate traits used in _rust/src/fd.rs, _rust/src/truncated_svd.rs, and _rust/src/tokenize.rs.

## Component

- _rust/src/fd.rs
- _rust/src/tokenize.rs
- _rust/src/truncated_svd.rs

## Verified Against



## External Code Boundary

Any Stratum paths above refer to the sibling `semestercontext/Stratum/` worktree. They are optional read-only learning anchors: LearningOS does not index, validate, manage, or write that codebase.
