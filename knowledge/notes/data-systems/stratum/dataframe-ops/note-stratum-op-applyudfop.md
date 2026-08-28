---
id: note-stratum-op-applyudfop
type: note
title: "ApplyUDFOp — df.apply(fn) / col.apply(fn)"
created: "2026-07-27"
role: reference
state: evolving
authorship: user
concepts: [concept-logical-ir, concept-dataframe-ops, concept-projection-family]
sources: []
---

# ApplyUDFOp

> A user function applied via `df.apply(fn)` / `col.apply(fn)`. Family `"Projection"`.

**Created by** — MethodCallOp `apply` branch of
[`extract_dataframe_op`](../note-stratum-extract-dataframe-op.md). Built inline,
then `op.replace_output_of_inputs(new_op)`.

## Node shape
- `ApplyUDFOp(ProjectionOp)`, `logical_family = "Projection"`.
- `fields = ["args", "kwargs", "columns"]` (redefined).
- `output_type = op.inputs[0].output_type` — set **explicitly**, overriding the
  ProjectionOp FRAME default: apply on a column → column (SERIES), on a frame → frame.

## How it's built
```python
new_op = ApplyUDFOp(args=op.args, kwargs=op.kwargs, inputs=op.inputs, outputs=op.outputs)
new_op.output_type = op.inputs[0].output_type
op.replace_output_of_inputs(new_op)
```

## Gotchas
- Runtime detail: `MethodCallOp.process` special-cases `apply` on a polars `Series`
  by dispatching to `map_elements`.
- Opaque UDF — no folding into the lazy map grammar; it keeps the input's kind.


## Legacy Job provenance

### component

stratum/optimizer/ir/_projection_ops.py

### verified_against

f63b93c (2026-07-27)

### status

current
