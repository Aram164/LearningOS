# Stage Working Notes

## Mental Models

### Python model

pyproject declares build metadata, an isolated build backend produces importable artifacts, editable installs alter discovery, extension modules obey Python import rules, and FFI crosses ownership, typing, error, and copying boundaries.

### Stratum relevance

maturin and PyO3 bind the Rust runtime into a Python optimizer package.

### Failure mode

confusing environment selection with package metadata, assuming editable means rebuilt native code, hiding copies at the boundary, or changing the Stratum environment to learn the mechanism.

### Engineering ownership

AI may critique only after your own model and first attempt exist. You remain responsible for the specification, trade-offs, every accepted line, tests, failure behavior, and maintenance cost.

## Read-only Anchor

Read-only: README.md build section, pyproject.toml build-system and tool.maturin tables, _rust/Cargo.toml PyO3 declaration, and the Python module boundary under stratum/_rust or its current equivalent. Do not install, build, or modify the Stratum checkout.

## Component

- _rust/Cargo.toml
- pyproject.toml

## Verified Against



## External Code Boundary

Any Stratum paths above refer to the sibling `semestercontext/Stratum/` worktree. They are optional read-only learning anchors: LearningOS does not index, validate, manage, or write that codebase.
