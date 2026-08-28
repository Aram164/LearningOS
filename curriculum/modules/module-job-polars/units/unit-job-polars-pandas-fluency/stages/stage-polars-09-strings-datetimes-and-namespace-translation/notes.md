# Stage Working Notes

## Mental Models

### Pandas baseline

Series.str, Series.dt, to_datetime, errors/format/dayfirst, timezone-aware values, date offsets, and accessor properties.

### Polars mirror

Expr/Series str and dt namespaces, str.to_datetime/str.strptime, explicit format and strictness, method-versus-property differences, weekday numbering, duration expressions, and timezone conversion.

## Read-only Anchor

Optional cross-reference — the Stratum track owns this material, and no session is blocked on it. Read it only to see the idea already in production. Read-only: stratum/optimizer/ir/_column_expr.py and stratum/optimizer/physical/_projection_execs.py. Trace STR_POLARS_METHODS, polars_datetime_kwargs, DatetimeConversionOp fallback through pandas, and GetAttrProjectionOp mappings such as dayofweek and is_month_end.

## Component

- stratum/optimizer/ir/_column_expr.py
- stratum/optimizer/physical/_projection_execs.py

## Verified Against



## External Code Boundary

Any Stratum paths above refer to the sibling `semestercontext/Stratum/` worktree. They are optional read-only learning anchors: LearningOS does not index, validate, manage, or write that codebase.
