# Stage Working Notes

## Mental Models

### Pandas baseline

eager execution, explicit usecols/filter ordering, intermediates, and manual performance choices.

### Polars mirror

LazyFrame, scan_*, collect, collect_schema, explain, optimized versus unoptimized plans, predicate/projection/slice pushdown, common subplan elimination, expression simplification, type coercion, cardinality estimation, join ordering, and streaming execution.

## Read-only Anchor

Optional cross-reference — the Stratum track owns this material, and no session is blocked on it. Read it only to see the idea already in production. Read-only: stratum/optimizer/_optimize.py, stratum/optimizer/_explain.py, stratum/optimizer/physical/_plan_context.py, stratum/optimizer/physical/_lowering.py, and stratum/optimizer/physical/_impl_selection.py. Contrast two optimizer layers: Stratum rewrites/binds a pipeline IR; Polars optimizes the dataframe query executed inside a chosen physical op.

## Component

- stratum/optimizer/_explain.py
- stratum/optimizer/_optimize.py
- stratum/optimizer/physical/_impl_selection.py
- stratum/optimizer/physical/_lowering.py
- stratum/optimizer/physical/_plan_context.py

## Verified Against



## External Code Boundary

Any Stratum paths above refer to the sibling `semestercontext/Stratum/` worktree. They are optional read-only learning anchors: LearningOS does not index, validate, manage, or write that codebase.
