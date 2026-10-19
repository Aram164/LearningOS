---
id: note-stratum-op-stringmethodop
type: note
title: "StringMethodOp — fused col.str.<method>(...)"
created: "2026-07-27"
role: reference
state: evolving
authorship: user
concepts: [concept-logical-ir, concept-dataframe-ops, concept-projection-family]
sources: []
---

# StringMethodOp

> A `col.str.<method>(...)` accessor+method call fused into one projection.
> Family `"Projection"`.

**Created by** — MethodCallOp branch of
[`extract_dataframe_op`](../note-stratum-extract-dataframe-op.md) when
`inputs[0]` is a [`GetAttrProjectionOp`](note-stratum-op-getattrprojectionop.md)
with `attr_name == ["str"]`, via `make_string_method_op`.

## Node shape
- `StringMethodOp(ProjectionOp)`, `logical_family = "Projection"`.
- `fields = ["method", "args", "kwargs", "columns"]`; `method = op.method_name`.
- `output_type = accessor.output_type` — a string column stays SERIES.
- `inputs = [column, *op.inputs[1:]]` — the column replaces the `.str` accessor as
  the primary operand; the method's other operands are unchanged (indices stay valid).

## How it's built (`make_string_method_op`)
- `column = accessor.inputs[0]` (the accessor's source) becomes `OperandRef(0)`.
- Rewires each non-accessor operand to the new op; the column now feeds it directly.
- Detaches the `.str` accessor **only when this was its last consumer** (a shared
  accessor stays until its final call is fused).

## Gotchas
- Making the `.str` call first-class lets selection folding lift it straight into a
  `StrExpr` predicate instead of re-discovering the accessor+call shape.
- polars renames some methods: `STR_POLARS_METHODS` (e.g. `count→count_matches`,
  `lower→to_lowercase`, `startswith→starts_with`, `len→len_chars`). Methods that
  match across backends need no entry.


## Legacy Job provenance

### component

stratum/optimizer/ir/_projection_ops.py

### verified_against

f63b93c (2026-07-27)

### status

current
