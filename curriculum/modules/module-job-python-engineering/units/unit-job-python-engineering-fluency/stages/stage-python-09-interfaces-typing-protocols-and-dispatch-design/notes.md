# Stage Working Notes

## Mental Models

### Python model

duck typing is behavior, Protocol makes a consumer's structural requirement explicit, ABCs provide runtime nominal contracts, and dispatch may live in subclasses, functions, registries, or data.

### Stratum relevance

ColumnExpr exposes an implicit backend interface and physical implementation selection combines type lookup with supports and cost predicates.

### Failure mode

selecting a mechanism by habit, creating import cycles through interface placement, widening a base contract for one backend, or type hints that document nothing testable.

### Engineering ownership

AI may critique only after your own model and first attempt exist. You remain responsible for the specification, trade-offs, every accepted line, tests, failure behavior, and maintenance cost.

## Read-only Anchor

Read-only: NumericOp.process in stratum/optimizer/ir/_numeric_ops.py; to_pandas/to_polars in stratum/optimizer/ir/_column_expr.py; PhysicalRegistry in stratum/optimizer/physical/_registry.py; selection in stratum/optimizer/physical/_impl_selection.py.

## Component

- stratum/optimizer/ir/_column_expr.py
- stratum/optimizer/ir/_numeric_ops.py
- stratum/optimizer/physical/_impl_selection.py
- stratum/optimizer/physical/_registry.py

## Verified Against



## External Code Boundary

Any Stratum paths above refer to the sibling `semestercontext/Stratum/` worktree. They are optional read-only learning anchors: LearningOS does not index, validate, manage, or write that codebase.
