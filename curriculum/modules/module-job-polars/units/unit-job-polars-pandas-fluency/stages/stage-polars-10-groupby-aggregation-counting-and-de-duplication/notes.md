# Stage Working Notes

## Mental Models

### Pandas baseline

split-apply-combine, groupby object versus aggregation, as_index, sort, dropna, observed, single/multiple keys, named aggregation, dict/list specs, size/count/nunique, and result shape.

### Polars mirror

group_by().agg(expression list), named expressions, maintain_order, key columns retained as columns, len/count/n_unique, strict expression outputs, and order guarantees.

## Read-only Anchor

Optional cross-reference — the Stratum track owns this material, and no session is blocked on it. Read it only to see the idea already in production. Read-only: stratum/optimizer/ir/_aggregation_ops.py, stratum/optimizer/ir/_dataframe_ops.py, stratum/optimizer/physical/_aggregation_execs.py, and stratum/tests/logical_optimizer/test_dataframe_ops.py. Relate this to the open Job task that separates Groupby from Aggregate logic. Observe the working tree as evidence only; do not edit, run formatters, or execute tests in Stratum.

## Component

- stratum/optimizer/ir/_aggregation_ops.py
- stratum/optimizer/ir/_dataframe_ops.py
- stratum/optimizer/physical/_aggregation_execs.py
- stratum/tests/logical_optimizer/test_dataframe_ops.py

## Verified Against



## External Code Boundary

Any Stratum paths above refer to the sibling `semestercontext/Stratum/` worktree. They are optional read-only learning anchors: LearningOS does not index, validate, manage, or write that codebase.
