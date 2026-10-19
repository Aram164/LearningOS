# Stage Working Notes

## Mental Models

### Pandas baseline

merge uses how='outer', two suffix values, inferred or explicit keys, optional index joins, and may leave output row order unspecified.

### Polars mirror

join uses how='full', one right-side suffix plus explicit left renaming, explicit key coalescing, and a deliberately narrower contract for unsupported index joins.

### Parity engineering around one real operation

pandas outer versus Polars full; pandas suffixes=(left,right) versus Polars suffix for right plus explicit left rename; identical versus distinct key names; key coalescing; common non-key columns; inferred common keys; multi-key joins; unsupported index joins and strategies; deterministic comparison when row order is unspecified.

## Read-only Anchor

Optional cross-reference — the Stratum track owns this material, and no session is blocked on it. Read it only to see the idea already in production. Read-only deep dive: stratum/optimizer/physical/_join_execs.py and stratum/tests/logical_optimizer/test_join_ops.py. Explain every translation in PolarsJoinOp: common_columns, outer→full, left_on/right_on inference, suffixes[1], coalesce=(left_on == right_on), key_cols, left-side rename, and explicit refusals. Compare those choices with PandasJoinOp’s direct merge call.

## Component

- stratum/optimizer/physical/_join_execs.py
- stratum/tests/logical_optimizer/test_join_ops.py

## Verified Against



## External Code Boundary

Any Stratum paths above refer to the sibling `semestercontext/Stratum/` worktree. They are optional read-only learning anchors: LearningOS does not index, validate, manage, or write that codebase.
