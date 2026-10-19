# Stage Working Notes

## Mental Models

### Review model

Review starts with intended behavior and system context, then checks correctness, tests, interfaces, operability, and long-term cost—not stylistic preference.

### Maintenance model

Existing users, data, errors, and extension points are constraints. A small compatible change is often better engineering than a clean rewrite.

### Contribution model

A useful contribution follows local conventions, makes one claim, includes evidence, and is easy for a maintainer to understand and reverse.

### Engineering ownership

AI may critique only after your own model and first attempt exist. You remain responsible for the specification, trade-offs, every accepted line, tests, failure behavior, and maintenance cost.

## Read-only Anchor

Read-only: choose one small historical or current Stratum change already present locally and reconstruct intent from tests, call sites, and diff/history if available. Do not modify, commit, or contact anyone.

## Component


## Verified Against



## External Code Boundary

Any Stratum paths above refer to the sibling `semestercontext/Stratum/` worktree. They are optional read-only learning anchors: LearningOS does not index, validate, manage, or write that codebase.
