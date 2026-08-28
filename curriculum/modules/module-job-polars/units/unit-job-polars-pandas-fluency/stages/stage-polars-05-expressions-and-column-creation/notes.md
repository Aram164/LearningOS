# Stage Working Notes

## Mental Models

### Pandas baseline

vectorized Series arithmetic, assign, eval, rename, broadcasting, callable assignments, and the sequential dependencies possible inside a chain.

### Polars mirror

Expr trees, pl.col/pl.lit, alias, select versus with_columns, named expressions, expression expansion, and the fact that expressions in one context are evaluated in parallel rather than seeing siblings created in that same call.

## Read-only Anchor

Optional cross-reference — the Stratum track owns this material, and no session is blocked on it. Read it only to see the idea already in production. Read-only: stratum/optimizer/ir/_column_expr.py, stratum/optimizer/ir/_map_ops.py, stratum/optimizer/physical/_map_execs.py, and the AssignOp section of stratum/optimizer/physical/_projection_execs.py. Explain why folded AssignMapOp uses one pandas assign or one Polars with_columns call, and when opaque AssignOp is needed.

## Component

- stratum/optimizer/ir/_column_expr.py
- stratum/optimizer/ir/_map_ops.py
- stratum/optimizer/physical/_map_execs.py
- stratum/optimizer/physical/_projection_execs.py

## Verified Against



## External Code Boundary

Any Stratum paths above refer to the sibling `semestercontext/Stratum/` worktree. They are optional read-only learning anchors: LearningOS does not index, validate, manage, or write that codebase.
