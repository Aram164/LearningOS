---
id: note-stratum-op-assignop
type: note
title: "AssignOp — opaque df.assign(...) fallback"
created: "2026-07-27"
role: reference
state: evolving
authorship: user
concepts: [concept-logical-ir, concept-dataframe-ops, concept-projection-family]
sources: []
---

# AssignOp

> The opaque fallback for a `df.assign(...)` that could not fold into an
> [AssignMapOp](note-stratum-op-assignmapop.md). Family `"Projection"`.

**Created by** — MethodCallOp `assign` branch of
[`extract_dataframe_op`](../note-stratum-extract-dataframe-op.md), taken when
`make_assign_map_op` returns `None` (or `map_op` is off). Built inline, then
`op.replace_output_of_inputs(new_op)`.

## Node shape
- `AssignOp(ProjectionOp)`, `logical_family = "Projection"`.
- `fields` inherited from `ProjectionOp` = `["func", "method", "args", "kwargs", "columns"]`.
- `output_type = FRAME`.

## How it's built
```python
new_op = AssignOp(args=op.args, kwargs=op.kwargs, inputs=op.inputs, outputs=op.outputs)
op.replace_output_of_inputs(new_op)
```

## Gotchas
- Reached for positional-arg assigns or sequence-valued constant kwargs — exactly
  the cases `make_assign_map_op` rejects. Prefer the foldable
  [AssignMapOp](note-stratum-op-assignmapop.md) path when possible.


## Legacy Job provenance

### component

stratum/optimizer/ir/_projection_ops.py

### verified_against

f63b93c (2026-07-27)

### status

current
