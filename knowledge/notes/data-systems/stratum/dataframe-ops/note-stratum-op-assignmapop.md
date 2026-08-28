---
id: note-stratum-op-assignmapop
type: note
title: "AssignMapOp — folded df.assign(...) column map"
created: "2026-07-27"
role: reference
state: evolving
authorship: user
concepts: [concept-logical-ir, concept-dataframe-ops, concept-map-family]
sources: []
---

# AssignMapOp

> `df.assign(**kwargs)` with each assigned column folded to a backend-agnostic
> `ColumnExpr`; input columns pass through unchanged. Family `"Map"`.

**Created by** — MethodCallOp `assign` branch of
[`extract_dataframe_op`](../note-stratum-extract-dataframe-op.md), via
`make_assign_map_op`, only when `map_op` is on **and** the call is foldable.
Non-foldable calls fall back to [AssignOp](note-stratum-op-assignop.md).

## Node shape
- `AssignMapOp(MapOp)`, `logical_family = "Map"`.
- `fields = ["entries"]` — an ordered `{new_column_name: ColumnExpr}` dict.
- `output_type = FRAME`. `name` renders `"assign: <col names>"`.
- `inputs = [src, *folder.leaf_ops]` — the source frame plus any kept producer
  leaves that couldn't be absorbed into the expression.

## How it's built (`make_assign_map_op`)
- **Returns `None`** (→ AssignOp fallback) when: there are positional `args`, there
  are no kwargs, or any kwarg is neither an `OperandRef` nor a *scalar* constant.
- Per kwarg: `OperandRef` values are folded into `ColumnExpr`s through one shared
  `_Folder` (a producer feeding several columns folds once); scalar constants
  become `Const` entries. `_is_scalar_constant`: `str` counts as scalar; anything
  with `__len__` or a pandas/polars `Series`/`DataFrame` does not.
- `entries` preserves the **kwargs order**, so later columns can overwrite earlier.
- Rewires via `_detach_absorbed_and_rewire` (absorbed nodes unlinked; kept
  producers re-pointed at the new op).

## Gotchas
- Sequence-valued constants (lists/arrays/series) are *not* scalar → they force the
  opaque `AssignOp` fallback.
- Only the `**kwargs` form folds; a positional `df.assign(fn)` never does.


## Legacy Job provenance

### component

stratum/optimizer/ir/_map_ops.py

### verified_against

f63b93c (2026-07-27)

### status

current
