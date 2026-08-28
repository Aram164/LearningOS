# Stage Working Notes

## Mental Models

### Python model

fluency means composing identity, callables, closures, decorators, classes, imports, protocols, and iterators without retrieving a neighboring implementation.

### Stratum relevance

one optimizer pass crosses all of these mechanisms before it reaches execution.

### Failure mode

isolated quiz success that collapses when the mechanisms interact or when the source is closed.

### Engineering ownership

AI may critique only after your own model and first attempt exist. You remain responsible for the specification, trade-offs, every accepted line, tests, failure behavior, and maintenance cost.

## Read-only Anchor

Read-only synthesis: stratum/optimizer/_op_utils.py, stratum/optimizer/physical/_registry.py, stratum/optimizer/physical/_impl_selection.py, stratum/optimizer/ir/_base.py, and stratum/optimizer/ir/_column_expr.py. Read only after the closed-book attempt.

## Component

- stratum/optimizer/_op_utils.py
- stratum/optimizer/ir/_base.py
- stratum/optimizer/ir/_column_expr.py
- stratum/optimizer/physical/_impl_selection.py
- stratum/optimizer/physical/_registry.py

## Verified Against



## External Code Boundary

Any Stratum paths above refer to the sibling `semestercontext/Stratum/` worktree. They are optional read-only learning anchors: LearningOS does not index, validate, manage, or write that codebase.
