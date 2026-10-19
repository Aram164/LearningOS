# Stage Working Notes

## Mental Models

### Compiler model

The compiler is a reasoning partner: first predict the error, then use the diagnostic to correct your model.

### Engineering model

A crate is more than source code; its manifest, tests, documentation, and build outputs form one reproducible unit.

## Read-only Anchor

Read-only: _rust/Cargo.toml, pyproject.toml build-system/tool.maturin tables, and _rust/src/lib.rs module declarations. Do not build or modify Stratum.

## Component

- _rust/Cargo.toml
- _rust/src/lib.rs
- pyproject.toml

## Verified Against



## External Code Boundary

Any Stratum paths above refer to the sibling `semestercontext/Stratum/` worktree. They are optional read-only learning anchors: LearningOS does not index, validate, manage, or write that codebase.
