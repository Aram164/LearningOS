# Stage Working Notes

## Mental Models

### Tool model

formatters normalize syntax; linters flag suspicious patterns; type checkers prove a limited static model; tests execute examples/properties/integrations; coverage records execution rather than correctness; pre-commit hooks provide fast local feedback; CI is the enforceable shared gate.

### Working practice

give each tool a non-overlapping role, version and centralize configuration, convert bugs to regression tests, and keep the complete gate runnable with one command.

### Job relevance

optimizer and backend changes need semantic tests plus cheap static checks before review.

### Failure mode

chasing coverage percentage, duplicating conflicting rules, suppressing diagnostics without rationale, or trusting a green type check as runtime proof.

## Read-only Anchor

Read-only in Stratum: inventory formatter, linter, type checker, tests, coverage, hooks, and CI configuration; select one historical bug/test and classify which quality layer could catch it. Do not run auto-fix or write caches into Stratum.

## Component


## Verified Against



## External Code Boundary

Any Stratum paths above refer to the sibling `semestercontext/Stratum/` worktree. They are optional read-only learning anchors: LearningOS does not index, validate, manage, or write that codebase.
