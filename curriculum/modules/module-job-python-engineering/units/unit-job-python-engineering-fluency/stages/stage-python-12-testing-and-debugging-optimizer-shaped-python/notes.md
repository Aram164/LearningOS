# Stage Working Notes

## Mental Models

### Python model

tests specify behavior and failure contracts; parametrization separates cases from mechanics, fixtures isolate graphs, property tests explore invariants, and debugging combines traceback, introspection, breakpoint, and minimized reproduction.

### Stratum relevance

backend and rewrite code needs edge-case matrices that fail for semantic bugs rather than merely exercise lines.

### Failure mode

over-normalized assertions, shared mutable fixtures, patching the wrong binding, tests that cannot detect their own implementation being broken, or stepping before reducing the case.

### Engineering ownership

AI may critique only after your own model and first attempt exist. You remain responsible for the specification, trade-offs, every accepted line, tests, failure behavior, and maintenance cost.

## Read-only Anchor

Read-only: tests for optimizer IR, dataframe operations, joins, and physical selection under stratum/tests or tests/ as present in the checkout. Observe parametrization, fixtures, backend-specific assertions, unsupported cases, and gaps; do not execute or edit Stratum tests.

## Component

- stratum/tests

## Verified Against



## External Code Boundary

Any Stratum paths above refer to the sibling `semestercontext/Stratum/` worktree. They are optional read-only learning anchors: LearningOS does not index, validate, manage, or write that codebase.
