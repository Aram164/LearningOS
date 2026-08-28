---
id: note-stratum-op-selectionop
type: note
title: "SelectionOp — relational row selection"
created: "2026-07-27"
role: reference
state: evolving
authorship: user
concepts: [concept-logical-ir, concept-dataframe-ops, concept-selection-family]
sources: []
---

# SelectionOp

> A relational selection: **restricts rows, keeps columns**. Family `"Selection"`.

**Created by** — **two** branches of
[`extract_dataframe_op`](../note-stratum-extract-dataframe-op.md):
- MethodCallOp `method ∈ _SELECTION_METHODS` → `make_selection_op` (method kinds).
- GetItemOp `df[bool_series]` (`is_mask_selection`, gated by `selection_op`) →
  `make_mask_selection_op` (the `MASK` kind).

## Node shape
- `SelectionOp(Op)`, `logical_family = "Selection"`.
- `fields = ["kind", "args", "kwargs", "predicate"]`.
- `kind`: `SelectionKind` ∈ `{MASK, QUERY, DROPNA, DROP_DUPLICATES, HEAD, TAIL, SAMPLE}`.
- `output_type = FRAME` by default; the method path overrides it to
  `inputs[0].output_type`; the mask path keeps `FRAME`.

## How it's built
- **Method path** (`make_selection_op`): `kind = _SELECTION_METHODS[method]`
  (`dropna, drop_duplicates, head, tail, sample`); carries `args`/`kwargs`;
  `predicate = None`; `inputs = op.inputs`; `replace_output_of_inputs`.
- **Mask path** (`make_mask_selection_op`): `kind = MASK`; `predicate` = the folded
  `ColumnExpr` (`fold_column_expr`); `inputs = [src, *leaf_ops]`; absorbs mask-only
  nodes and detaches them from the graph.

## Gotchas
- `QUERY` is defined in the enum but **not produced** by this dispatcher.
- Method kinds map 1:1 to a per-backend frame method (`_SELECTION_PANDAS_METHOD` /
  `_SELECTION_POLARS_METHOD`, e.g. `dropna→drop_nulls`, `drop_duplicates→unique`).
- `is_mask_selection` has a known TODO: it misfires on a **non-boolean** series key
  (positional/label indexing) because boolean-ness isn't tracked in the type lattice.


## Legacy Job provenance

### component

stratum/optimizer/ir/_selection_ops.py

### verified_against

f63b93c (2026-07-27)

### status

current
