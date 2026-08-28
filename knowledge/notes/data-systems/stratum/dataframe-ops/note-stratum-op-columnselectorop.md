---
id: note-stratum-op-columnselectorop
type: note
title: "ColumnSelectorOp — skb.select(cols) deferred selector"
created: "2026-07-27"
role: reference
state: evolving
authorship: user
concepts: [concept-logical-ir, concept-dataframe-ops, concept-projection-family]
sources: []
---

# ColumnSelectorOp

> Column selection by a **deferred skrub selector** (`skb.select(cols)`): keeps
> rows, restricts columns. Family `"Projection"`.

**Created by** — the `BaseEstimatorOp` branch of
[`extract_dataframe_op`](../note-stratum-extract-dataframe-op.md), when the op is
a `TransformerOp` wrapping skrub's `SelectCols` with no `param_refs` and a `y`
that isn't an `OperandRef`, via `make_column_selector_op`. (skrub implements
`skb.select(cols)` as an `Apply` of `SelectCols`.)

## Node shape
- `ColumnSelectorOp(Op)`, `logical_family = "Projection"`.
- `fields = ["selector"]` — `= op.estimator.cols` (the skrub selector).
- `selected_columns = None` initially (populated at fit); `output_type = FRAME`;
  `name` renders `select[<selector>]`.

## How it's built (`make_column_selector_op`)
```python
new_op = ColumnSelectorOp(selector=op.estimator.cols, inputs=op.inputs, outputs=op.outputs)
op.replace_output_of_inputs(new_op)
```

## Gotchas
- Matches `SelectCols` semantics: the (possibly data-dependent, e.g. `numeric()`)
  selector resolves against the schema **at fit time**, and the stored column list
  is reused at predict time.
- Distinct from [ColumnProjectionOp](note-stratum-op-columnprojectionop.md), which
  takes literal column names and needs no resolution.


## Legacy Job provenance

### component

stratum/optimizer/ir/_projection_ops.py

### verified_against

f63b93c (2026-07-27)

### status

current
