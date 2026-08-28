# Stage Working Notes

## Mental Models

### Pandas baseline

None, NaN, NaT, pd.NA, nullable integer/Boolean/string dtypes, isna/notna, fillna/dropna, astype, and coercion.

### Polars mirror

null versus floating NaN, is_null/is_nan, fill_null/fill_nan/drop_nulls, strict and non-strict cast, schema stability, Categorical, and Enum. Treat equality, aggregation, and join behavior separately.

## Read-only Anchor

Optional cross-reference — the Stratum track owns this material, and no session is blocked on it. Read it only to see the idea already in production. Read-only: stratum/optimizer/ir/_column_expr.py (MissingMaskExpr) and stratum/optimizer/physical/_selection_execs.py. Locate the frame-wide pl.all().is_null() path and the pandas isna/notna path. Note that current join tests normalize pandas NaN versus Polars None rather than pretending they are identical objects.

## Component

- stratum/optimizer/ir/_column_expr.py
- stratum/optimizer/physical/_selection_execs.py

## Verified Against



## External Code Boundary

Any Stratum paths above refer to the sibling `semestercontext/Stratum/` worktree. They are optional read-only learning anchors: LearningOS does not index, validate, manage, or write that codebase.
