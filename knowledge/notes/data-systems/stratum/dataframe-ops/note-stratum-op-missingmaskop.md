---
id: note-stratum-op-missingmaskop
type: note
title: "MissingMaskOp — folded is-null / not-null predicate"
created: "2026-07-27"
role: reference
state: evolving
authorship: user
concepts: [concept-logical-ir, concept-dataframe-ops, concept-map-family]
sources: []
---

# MissingMaskOp

> A pandas missing-value predicate (`isna`/`isnull`/`notna`/`notnull`) on a frame
> or series, folded into one `MapOp`. Family `"Map"`.

**Captures** — a boolean missing-value mask. On polars it compiles into a lazy
`with_columns` kernel (the MapOp grammar).

**Created by** — two branches of
[`extract_dataframe_op`](../note-stratum-extract-dataframe-op.md), both gated by
`map_op` and both routed through `make_missing_mask_op`:
- CallOp branch — `pd.isna/isnull/notna/notnull(obj)` (`func in MISSING_FUNCTIONS`).
- MethodCallOp branch — `obj.isna()/isnull()/notna()/notnull()` (`method in MISSING_METHODS`).

## Node shape
- `MissingMaskOp(MapOp)`, `logical_family = "Map"`.
- `fields = ["positive"]` — `positive = True` for `isna`/`isnull` (is-null),
  `False` for `notna`/`notnull` (not-null). `name` renders `"isnull"`/`"notnull"`.
- `output_type` = `FRAME` from the `MapOp` base, then overridden to
  `inputs[0].output_type` when inputs are present (mask of a series → SERIES).
- `inputs = [operand]` — the single frame/series being tested.

## How it's built (`make_missing_mask_op`)
- Dispatches on the source op type:
  - `MethodCallOp` → `_make_method_missing_mask_op`: requires **no args/kwargs** and
    **exactly one input**; `inputs = [op.inputs[0]]`.
  - `CallOp` → `_make_call_missing_mask_op`: only the single-operand forms
    `func(obj)` or `func(obj=obj)`, and `obj` must be an `OperandRef`;
    `inputs = [op.inputs[operand_ref.k]]`.
- `positive` set from `POSITIVE_MISSING_METHODS` / `POSITIVE_MISSING_FUNCTIONS`.
- Wires the upstream side via `op.replace_output_of_inputs(new_op)`.
- **Returns `None`** (branch no-ops) if the call shape doesn't match — e.g.
  `pd.isna(a, b)`, extra kwargs, or a non-`OperandRef` operand.

## Gotchas
- One node, **two entry points** (CallOp + MethodCallOp) — keep both in mind when
  grepping for producers.
- MapOp grammar is deliberately narrow (natively-lazy ops only); anything outside
  it stays in the graph and feeds the map as an `OperandLeaf`.
- See sibling [AssignMapOp](note-stratum-op-assignmapop.md) — the other MapOp kind.


## Legacy Job provenance

### component

stratum/optimizer/ir/_map_ops.py

### verified_against

f63b93c (2026-07-27)

### status

current
