# Stage Working Notes

## Mental Models

### Pandas baseline

merge/join, inner/left/right/outer/cross, one-to-one/many-to-one/many-to-many cardinality, duplicate-key multiplication, validate, indicator, index joins, suffixes, and row-order behavior.

### Polars mirror

join with inner/left/right/full/semi/anti/cross, validate, nulls_equal, coalesce, maintain_order, expression keys, and no dataframe index.

## Read-only Anchor

Optional cross-reference — the Stratum track owns this material, and no session is blocked on it. Read it only to see the idea already in production. Read-only: start with stratum/optimizer/ir/_join_ops.py. Trace how make_join_op normalizes pandas merge(on=...), merge(left_on/right_on), DataFrame.join defaults, positional arguments, suffix defaults, sort refusal, and chained index joins into JoinOp fields.

## Component

- stratum/optimizer/ir/_join_ops.py

## Verified Against



## External Code Boundary

Any Stratum paths above refer to the sibling `semestercontext/Stratum/` worktree. They are optional read-only learning anchors: LearningOS does not index, validate, manage, or write that codebase.
