# Stage Working Notes

## Mental Models

### Ownership model

Every value has one owner; moving transfers that responsibility and Drop ends it.

### Cost model

clone is an explicit cost and should follow a deliberate API decision, not a borrow-checker workaround.

## Read-only Anchor

Read-only: ownership of Vec fields in _rust/src/csr.rs and owned versus borrowed parameters in _rust/src/tokenize.rs and _rust/src/lib.rs.

## Component

- _rust/src/csr.rs
- _rust/src/lib.rs
- _rust/src/tokenize.rs

## Verified Against



## External Code Boundary

Any Stratum paths above refer to the sibling `semestercontext/Stratum/` worktree. They are optional read-only learning anchors: LearningOS does not index, validate, manage, or write that codebase.
