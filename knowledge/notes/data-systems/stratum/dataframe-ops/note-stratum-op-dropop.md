---
id: note-stratum-op-dropop
type: note
title: "DropOp — df.drop(...)"
created: "2026-07-27"
role: reference
state: evolving
authorship: user
concepts: [concept-logical-ir, concept-dataframe-ops, concept-projection-family]
sources: []
---

# DropOp

> `df.drop(...)` — drop labels/columns. Family `"Projection"`.

**Created by** — MethodCallOp `drop` branch of
[`extract_dataframe_op`](../note-stratum-extract-dataframe-op.md). Built inline,
then `op.replace_output_of_inputs(new_op)`.

## Node shape
- `DropOp(ProjectionOp)`, `logical_family = "Projection"`.
- `fields = ["args", "kwargs", "columns"]` (redefined — narrower than the
  `ProjectionOp` field list, which also carries `func`/`method`).
- `output_type = FRAME` (ProjectionOp default).

## How it's built
```python
DropOp(args=op.args, kwargs=op.kwargs, inputs=op.inputs, outputs=op.outputs)
```

## Gotchas
- `columns` is `None` until schema resolution (a TODO across the projection ops).
- Execution lives in `physical/_projection_execs.py`; the logical op is config only.


## Legacy Job provenance

### component

stratum/optimizer/ir/_projection_ops.py

### verified_against

f63b93c (2026-07-27)

### status

current
