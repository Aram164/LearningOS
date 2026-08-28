# Stage Working Notes

## Mental Models

### Pandas baseline

Series.map, DataFrame.apply, axis semantics, raw/result_type, vectorized NumPy/pandas alternatives, and Python-call overhead.

### Polars mirror

native expressions first, map_elements/map_batches/map_rows only when necessary, explicit return_dtype, skip_nulls, warnings, threading limits, and plugins for native execution. Treat a pandas fallback as a correctness tool with a conversion cost, not as fluent Polars.

## Read-only Anchor

Optional cross-reference — the Stratum track owns this material, and no session is blocked on it. Read it only to see the idea already in production. Read-only: stratum/optimizer/physical/_projection_execs.py::PandasApplyUDFOp, PolarsApplyUDFOp, and _to_datetime_via_pandas. Note native sin/cos rewrites, Series map_elements, DataFrame map_rows, and conversion fallback. Search tests for the exact expected paths.

## Component

- stratum/optimizer/physical/_projection_execs.py

## Verified Against



## External Code Boundary

Any Stratum paths above refer to the sibling `semestercontext/Stratum/` worktree. They are optional read-only learning anchors: LearningOS does not index, validate, manage, or write that codebase.
