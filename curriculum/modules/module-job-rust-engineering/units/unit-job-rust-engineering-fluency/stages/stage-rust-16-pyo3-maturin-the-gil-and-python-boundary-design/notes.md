# Stage Working Notes

## Mental Models

### FFI model

The boundary is a contract between two runtimes; types, lifetime, copies, exceptions, and thread assumptions must be explicit.

### Testing model

A pure-Python oracle isolates semantic correctness from native packaging and performance.

## Read-only Anchor

Read-only: pyproject.toml, _rust/Cargo.toml, _rust/src/lib.rs, and stratum/_rust_backend.py. Do not build the Stratum extension.

## Component

- _rust/Cargo.toml
- _rust/src/lib.rs
- pyproject.toml
- stratum/_rust_backend.py

## Verified Against



## External Code Boundary

Any Stratum paths above refer to the sibling `semestercontext/Stratum/` worktree. They are optional read-only learning anchors: LearningOS does not index, validate, manage, or write that codebase.
