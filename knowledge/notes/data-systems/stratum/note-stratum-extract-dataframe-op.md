---
id: note-stratum-extract-dataframe-op
type: note
title: "extract_dataframe_op (frame-like branch) — dispatch map"
created: "2026-07-27"
role: reference
state: evolving
authorship: user
concepts: [concept-logical-ir, concept-dataframe-ops, concept-op-rewriting, concept-dispatch]
sources: []
# --- living-note header (see ../README.md) ---
---

# extract_dataframe_op — frame-like branch (dispatch map)

> `extract_dataframe_op(op, root, selection_op=True, map_op=True, column_projection=True)`
> rewrites one logical `Op` into a more specific dataframe op (or just tags its
> `output_type`). This note is the **dispatch map** for the third top-level case —
> the `else` branch where the input is frame-world data. Each produced node has its
> own note under [`dataframe-ops/`](dataframe-ops/); this file only records *what
> original node + which conditions* build each one.

## Scope: which case this is about

The method's outer shape is a 3-way split on the *input*:

1. `len(op.inputs) == 0` → a directly-passed DataFrame (`ValueOp` → `DataSourceOp`).
2. `not is_frame_like(op.inputs[0])` → a read from a raw value (`read_csv` /
   `read_parquet` / `np.load` → `DataSourceOp`).
3. **else — `op.inputs[0]` is frame-like → a real dataframe op.**  ← this note.

`is_frame_like(x)` ⇔ `x.output_type ∈ {FRAME, SERIES}` (`_base.py`). Inside case 3
the dispatch is on `type(op)`, in the order below.

## Conventions

- `inputs[0]` = the **implicit primary operand** (object the method is called on /
  attribute is read from / container being indexed). Later inputs are the
  de-duplicated operands referenced by `OperandRef(k)` in the node's fields.
- `output_type ∈ {FRAME, SERIES, SCALAR, MATRIX}` (`OutputType`, `_base.py`).
- Graph surgery uses two helpers:
  - `op.replace_output_of_inputs(new_op)` — **upstream** side; called inside the
    `make_*` factories / next to each inline constructor.
  - `op.replace_input_of_outputs(new_op)` — **downstream** side; run once in the
    dispatcher tail whenever a `new_op` was produced.
- **Two outcomes per branch:** **REPLACE** (builds a `new_op`, tail returns
  `(root, True)`) or **IN-PLACE** (only sets `output_type`/`is_filter`; `new_op`
  stays `None`, tail returns `(root, False)`).
- Flags (default `True`): `map_op` (missing masks + assign fold), `selection_op`
  (mask selection), `column_projection` (literal column selects). A `False` flag
  skips its branch.

## Dispatch by original node type

Each row: the condition that fires, and the produced node (→ its note). "in-place"
rows produce no node — they only tag the existing op.

### CallOp — `fields = [func, args, kwargs]` (frame flows in as an operand)

| Condition | Produces |
|---|---|
| `map_op and func ∈ MISSING_FUNCTIONS` (`pd.isna/isnull/notna/notnull`) | [MissingMaskOp](dataframe-ops/note-stratum-op-missingmaskop.md) |
| `func is pd.to_datetime` | [DatetimeConversionOp](dataframe-ops/note-stratum-op-datetimeconversionop.md) |

### MethodCallOp — `fields = [method_name, args, kwargs]` (object = `inputs[0]`)

Matched **in order**; first match wins.

| Condition | Produces |
|---|---|
| `map_op and method ∈ MISSING_METHODS` (`isna/isnull/notna/notnull`) | [MissingMaskOp](dataframe-ops/note-stratum-op-missingmaskop.md) |
| `inputs[0]` is a `GetAttrProjectionOp` with `attr_name == ["str"]` | [StringMethodOp](dataframe-ops/note-stratum-op-stringmethodop.md) |
| `method == "groupby"` | *in-place* → `output_type = FRAME` (marks it so the following agg fuses) |
| `_is_aggregation(op)` | [AggregateOp](dataframe-ops/note-stratum-op-aggregateop.md) |
| `method == "rename"` | [MetadataOp](dataframe-ops/note-stratum-op-metadataop.md) |
| `method == "drop"` | [DropOp](dataframe-ops/note-stratum-op-dropop.md) |
| `method == "apply"` | [ApplyUDFOp](dataframe-ops/note-stratum-op-applyudfop.md) |
| `method == "assign"` | [AssignMapOp](dataframe-ops/note-stratum-op-assignmapop.md) if foldable, else [AssignOp](dataframe-ops/note-stratum-op-assignop.md) |
| `method ∈ {join, merge}` | [JoinOp](dataframe-ops/note-stratum-op-joinop.md) (chained → a chain of them) |
| `method ∈ _SELECTION_METHODS` (`dropna/drop_duplicates/head/tail/sample`) | [SelectionOp](dataframe-ops/note-stratum-op-selectionop.md) (method kind) |

### GetAttrOp — `fields = [attr_name]`

| Condition | Produces |
|---|---|
| any (via `make_frame_get_attr`, fuses chained accessors) | [GetAttrProjectionOp](dataframe-ops/note-stratum-op-getattrprojectionop.md) |

### BinOp / UnaryOp — `[op, left, right]` / `[op, operand]`

| Condition | Produces |
|---|---|
| any | *in-place* → `output_type = inputs[0].output_type` (SERIES operand → SERIES; FRAME → FRAME) |

### GetItemOp — `fields = [key, is_filter]` (container = `inputs[0]`)

Checked in order:

| Condition | Produces |
|---|---|
| `is_mask_selection(op)` (`df[bool_series]`) — sets `is_filter=True`; if `selection_op` | [SelectionOp](dataframe-ops/note-stratum-op-selectionop.md) (`MASK` kind) |
| `column_projection and _is_column_projection(op)` (literal `str`/`list[str]` on a FRAME) | [ColumnProjectionOp](dataframe-ops/note-stratum-op-columnprojectionop.md) |
| else | *in-place* → `output_type = _getitem_output_type(op)`; plain `GetItemOp` survives |

### BaseEstimatorOp — `[estimator, y, cols, how, allow_reject, unsupervised, kwargs, param_refs]`

Always sets `output_type = FRAME` first, then:

| Condition | Produces |
|---|---|
| `TransformerOp` wrapping skrub `SelectCols`, no `param_refs`, `y` not `OperandRef` | [ColumnSelectorOp](dataframe-ops/note-stratum-op-columnselectorop.md) |
| else | *in-place* → stays `BaseEstimatorOp`, `output_type = FRAME` |

### ChoiceOp — `fields = [outcome_names]`

| Condition | Produces |
|---|---|
| all outcomes frame-like | *in-place* → `output_type` = shared type if all agree, else FRAME |

## The shared tail

```python
if new_op is None:
    return root, False              # every in-place branch lands here
op.replace_input_of_outputs(new_op) # downstream side of the rewire
if root is op:
    root = new_op
return root, True                   # every replace branch lands here
```

A REPLACE branch wires the **upstream** side itself (inside the `make_*` / next to
the constructor); the **downstream** side is wired here, once, uniformly.

## Notes vs. the handwritten pages

- **`rename` → MetadataOp** was missing from the handwritten code page; it sits
  between aggregation and drop. Reinstating it re-aligns the numbering (drop/apply/
  assign/join/selection each shift down one).
- The two left for last are here: **BaseEstimatorOp** (→ ColumnSelectorOp / in-place)
  and **ChoiceOp** (in-place).
- **MissingMaskOp has two entry points** (CallOp + MethodCallOp). Flags to remember:
  `map_op` gates the two missing-mask rows + the assign fold; `selection_op` gates
  the mask row; `column_projection` gates the literal-column row.

## Open questions

- `make_frame_get_attr(None, op)` is always passed `new_op = None` — vestigial arg?
- `is_mask_selection` misfires on a non-boolean series key (TODO: gate on boolean
  dtype once the type lattice tracks it).


## Legacy Job provenance

### component

stratum/optimizer/ir/_dataframe_ops.py

### verified_against

f63b93c (2026-07-27)

### status

current
