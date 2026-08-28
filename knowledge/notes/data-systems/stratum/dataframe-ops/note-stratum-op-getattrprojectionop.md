---
id: note-stratum-op-getattrprojectionop
type: note
title: "GetAttrProjectionOp — tabular attribute access"
created: "2026-07-27"
role: reference
state: evolving
authorship: user
concepts: [concept-logical-ir, concept-dataframe-ops, concept-projection-family]
sources: []
---

# GetAttrProjectionOp

> Attribute access on tabular data (`df.dt`, `col.str`, `df.values`, chained
> `.dt.year`), preserving the tabular kind. Family `"Projection"`.

**Created by** — the `GetAttrOp` branch of
[`extract_dataframe_op`](../note-stratum-extract-dataframe-op.md), via
`make_frame_get_attr`. Also appears as the `.str` accessor that
[StringMethodOp](note-stratum-op-stringmethodop.md) fuses away.

## Node shape
- `GetAttrProjectionOp(Op)`, `logical_family = "Projection"`.
- `fields = ["attr_name"]` — **always a list** (a single `str` is wrapped to
  `[str]`); `name` renders the dotted path.
- `output_type =` the source's `output_type` (attribute access keeps FRAME/SERIES).

## How it's built (`make_frame_get_attr`)
- If `inputs[0]` is itself a `GetAttrProjectionOp` → **fuse**: concatenate
  `attr_name`s into one node re-pointed at the original source. If the inner node
  had other consumers it's kept; otherwise it's replaced.
- Else → wrap the single `GetAttrOp`'s attr into a new node over `op.inputs`.

## Gotchas
- Backend attribute-name differences: `POLARS_ATTR_NAME_MAP`
  (`dayofweek→weekday`, `dayofyear→ordinal_day`). **Watch `dayofweek`**: pandas is
  Monday=0, polars `weekday()` is Monday=1.
- The dispatcher calls `make_frame_get_attr(None, op)` — the first `new_op`
  argument is always `None` here (vestigial; the factory builds its own).


## Legacy Job provenance

### component

stratum/optimizer/ir/_projection_ops.py

### verified_against

f63b93c (2026-07-27)

### status

current
