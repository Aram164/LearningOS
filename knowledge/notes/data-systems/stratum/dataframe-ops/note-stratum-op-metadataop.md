---
id: note-stratum-op-metadataop
type: note
title: "MetadataOp — schema-only rewrite (rename)"
created: "2026-07-27"
role: reference
state: evolving
authorship: user
concepts: [concept-logical-ir, concept-dataframe-ops]
sources: []
---

# MetadataOp

> A schema-only rewrite with no data movement. Today only `df.rename(...)` routes
> here.

**Created by** — MethodCallOp `rename` branch of
[`extract_dataframe_op`](../note-stratum-extract-dataframe-op.md). Built
**inline** (no `make_*` factory), then `op.replace_output_of_inputs(new_op)`.

## Node shape
- `MetadataOp(Op)` — a **direct `Op`**, not a `ProjectionOp`.
- `fields = ["func", "args", "kwargs"]` — `func` is the method name string
  (e.g. `"rename"`); `name` renders it upper-cased.
- `output_type = FRAME`.

## How it's built
```python
MetadataOp(func=op.method_name, args=op.args, kwargs=op.kwargs,
           inputs=op.inputs, outputs=op.outputs)
op.replace_output_of_inputs(new_op)
```

## Gotchas
- The guard is `op.method_name in ["rename"]` — a list, so extending to other
  metadata-only methods is a one-line change.
- ⚠️ This is the branch that was missing from the handwritten code page; its
  omission shifted the rest of the MethodCallOp numbering by one.


## Legacy Job provenance

### component

stratum/optimizer/ir/_projection_ops.py

### verified_against

f63b93c (2026-07-27)

### status

current
