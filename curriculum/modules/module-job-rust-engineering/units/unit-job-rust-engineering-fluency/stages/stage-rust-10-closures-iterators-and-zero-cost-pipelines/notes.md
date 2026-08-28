# Stage Working Notes

## Mental Models

### Closure model

The required call trait follows how captured state is borrowed or consumed.

### Iterator model

Adaptors are lazy state machines; ownership changes at iter, iter_mut, and into_iter.

## Read-only Anchor

Read-only: iterator pipelines and closure use in _rust/src/tokenize.rs, _rust/src/hashing.rs, and _rust/src/tfidf.rs.

## Component

- _rust/src/hashing.rs
- _rust/src/tfidf.rs
- _rust/src/tokenize.rs

## Verified Against



## External Code Boundary

Any Stratum paths above refer to the sibling `semestercontext/Stratum/` worktree. They are optional read-only learning anchors: LearningOS does not index, validate, manage, or write that codebase.
