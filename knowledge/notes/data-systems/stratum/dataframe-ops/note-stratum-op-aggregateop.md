---
id: note-stratum-op-aggregateop
type: note
title: "AggregateOp — fused groupby(...).agg(...)"
created: "2026-07-27"
role: reference
state: evolving
authorship: user
concepts: [concept-logical-ir, concept-dataframe-ops, concept-aggregation-family]
sources: []
---

# AggregateOp

> A `groupby(by).agg(...)` (or `.sum()`/`.mean()`/…) pair fused into one op.
> Family `"Aggregation"`.

**Created by** — MethodCallOp aggregation branch of
[`extract_dataframe_op`](../note-stratum-extract-dataframe-op.md) when
`_is_aggregation(op)` holds, via `make_aggregate_op`. The preceding `groupby`
call is only tagged `FRAME` by its own branch and then **bypassed** here.

## Node shape
- `AggregateOp(Op)`, `logical_family = "Aggregation"`.
- `fields = ["grouping_attributes", "aggregations", "groupby_kwargs"]`.
- `output_type = FRAME`; `name` renders `by=<keys>, agg=<spec>`.
- `inputs = [df] + groupby_op.inputs[1:] + op.inputs[1:]` (frame, then grouping-key
  placeholder operands, then aggregation-spec placeholder operands).

## How it's built (`make_aggregate_op`)
- `grouping_attributes = _extract_grouping(groupby_op)` — `args[0]` or `kwargs["by"]`.
- `aggregations = _extract_aggregations(op)` — for `.agg`/`.aggregate` the positional
  `args[0]`; for a direct method (`.mean()`) its own name string.
- An `OperandRef` in `aggregations` is shifted by `offset = len(groupby_op.inputs) - 1`
  to stay valid after the grouping operands are spliced in front.
- `groupby_kwargs` = the groupby's kwargs minus `by`.
- Bypasses the now-orphaned groupby (rewires the frame + key producers, moves the
  agg's extra producers, removes `op` from the groupby's outputs).

## `_is_aggregation` guard
All must hold: `inputs[0]` is a `groupby` MethodCallOp; that groupby has **exactly
one** consumer; its grouping key is extractable; and either
`method_name ∈ _AGG_METHODS` (`sum, mean, count, min, max, median, std, var,
first, last, prod, size, nunique, sem`) **or** `method_name ∈ {agg, aggregate}`
with positional args.

## Gotchas
- Won't fuse if anything (e.g. a `GetItem`) sits between the groupby and the agg,
  or if the groupby has multiple consumers.
- Only the positional-spec form of `.agg(spec)` is supported.
- `GroupedDataframeOp` lives in the same module but is **experimental and not
  integrated** — it is not produced by this dispatcher.


## Legacy Job provenance

### component

stratum/optimizer/ir/_aggregation_ops.py

### verified_against

f63b93c (2026-07-27)

### status

current
