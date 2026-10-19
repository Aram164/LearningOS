---
id: note-stratum-op-columnprojectionop
type: note
title: "ColumnProjectionOp — literal df[col] / df[[cols]]"
created: "2026-07-27"
role: reference
state: evolving
authorship: user
concepts: [concept-logical-ir, concept-dataframe-ops, concept-projection-family]
sources: []
---

# ColumnProjectionOp

> Column selection by **literal** name(s): `df["a"]` (→ SERIES) or
> `df[["a", "b"]]` (→ sub-FRAME). Family `"Projection"`.

**Created by** — the `GetItemOp` branch of
[`extract_dataframe_op`](../note-stratum-extract-dataframe-op.md) when
`_is_column_projection(op)` holds and the `column_projection` flag is on, via
`make_column_projection_op`.

## Node shape
- `ColumnProjectionOp(Op)`, `logical_family = "Projection"`.
- `fields = ["key"]` — the literal column label(s); `name` renders `cols[<key>]`.
- `output_type = SERIES` if `key` is a `str` (single column), else `FRAME`
  (list of labels → sub-frame).

## How it's built (`make_column_projection_op`)
```python
new_op = ColumnProjectionOp(key=op.key, inputs=op.inputs, outputs=op.outputs)
op.replace_output_of_inputs(new_op)
```
`_is_column_projection`: container is a `FRAME` **and** `key` is a `str` or a
`list[str]`.

## Gotchas
- Only literal keys on a frame route here. Boolean masks, graph-fed keys, slices
  and positional keys stay a plain `GetItemOp` (the dispatcher's GetItem fallback).
- Distinct from [ColumnSelectorOp](note-stratum-op-columnselectorop.md): the
  columns are given **verbatim**, so there's no fit-time schema resolution.


## Legacy Job provenance

### component

stratum/optimizer/ir/_projection_ops.py

### verified_against

f63b93c (2026-07-27)

### status

current
