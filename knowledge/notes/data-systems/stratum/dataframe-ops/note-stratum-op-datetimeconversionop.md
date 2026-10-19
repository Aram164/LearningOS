---
id: note-stratum-op-datetimeconversionop
type: note
title: "DatetimeConversionOp — pd.to_datetime parse"
created: "2026-07-27"
role: reference
state: evolving
authorship: user
concepts: [concept-logical-ir, concept-dataframe-ops, concept-projection-family]
sources: []
---

# DatetimeConversionOp

> A `pd.to_datetime(col_or_df, ...)` string→datetime parse. Family `"Projection"`.

**Created by** — CallOp `pd.to_datetime` branch of
[`extract_dataframe_op`](../note-stratum-extract-dataframe-op.md), via
`make_datetime_conversion_op`. **Not** gated by `map_op`.

## Node shape
- `DatetimeConversionOp(ProjectionOp)`, `logical_family = "Projection"`.
- `fields` inherited from `ProjectionOp` = `["func", "method", "args", "kwargs", "columns"]`.
- `output_type = inputs[0].output_type` — a column parse → SERIES, a frame parse → FRAME.

## How it's built (`make_datetime_conversion_op`)
- The frame/series is positional arg 0 of the original call, so it's dropped:
  `args = op.args[1:]` when `len(op.args) > 1`, else `()`. `kwargs` kept (copied).
- `op.replace_output_of_inputs(new_op)` wires the upstream side.

## Gotchas
- polars has a fast path only for a restricted kwargs set — `format`, `errors`,
  `exact`, `cache`, with `errors ∈ {raise, coerce}` and no positional options
  (see `polars_datetime_kwargs` / `_POLARS_DATETIME_KWARGS`). Anything else takes
  the pandas compatibility path. Positional options are kept on the pandas path
  because their ordering differs from `Expr.str.to_datetime`.


## Legacy Job provenance

### component

stratum/optimizer/ir/_projection_ops.py

### verified_against

f63b93c (2026-07-27)

### status

current
