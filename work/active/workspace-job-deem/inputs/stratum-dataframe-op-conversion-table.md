# Stratum DataFrame IR — Operation Conversion Table

> Companion to `map of dataframe op processing structure .txt`. Condenses the whole
> extraction structure into tables **grouped by the strict operator taxonomy** the
> codebase is migrating toward (§1): for each supported operation, the **generic node
> it starts as**, the **specialized node it becomes**, the **factory/mechanism** that
> does the conversion, the **file** that owns it, the resulting **OutputType**, the
> **guard**, the **graph side-effects**, and an **example**.
>
> Verified against `stratum/optimizer/ir/*` on 2026-07-13, **after** the
> `[FrameOperator] Map operator (#141)` change that introduced `_map_ops.py`.

---

## Target taxonomy — the end goal

The strict grouping we are building classifies every essential pandas op by **what
part of the frame it touches**, so each group has a clean algebraic meaning:

| Group | Definition (strict) | Touches |
|---|---|---|
| **Source** | Introduce data into the graph (the leaves). | — (creates a frame) |
| **Projection** | Eliminate columns or alter their **order/labels**, with **no effect on rows and no change of dtypes/values**. | columns (structure only) |
| **Selection** | Like projection, but over **rows**: restrict which rows survive; columns unchanged. | rows |
| **Map** | **Add or remove columns, or change the dtype/values** of columns, **without changing the row structure**. | columns (values/dtypes) |
| **Aggregate** | Partition rows into groups and compute per-group values. | rows → groups |

Two families sit **outside** the strict five because they are not single-frame
column/row transforms: **combiners** (Join, Concat — two or more frames in) and
**workflow/typing** nodes (Split for ML X/y, and the type-only Estimator/Choice
branches). They are kept as Group 6.

### Migration status — built step by step

The code is **mid-transition**: modules are still partly implementation-oriented, so a
node's *strict group* and its *current file* do not yet match 1:1. The split is being
done incrementally.

- **Done (step 1, commit #141):** the Map family started moving out of
  `_projection_ops.py` into a dedicated `_map_ops.py`. `AssignMapOp` (from a foldable
  `df.assign(...)`) is the **first** Map operator; the dispatcher gained a `map_op`
  flag and now tries `make_assign_map_op` before the opaque `AssignOp` fallback.
- **Pending:** the other Map-semantics nodes (`DatetimeConversionOp`, `StringMethodOp`,
  `ApplyUDFOp`, the `.dt`/`.str` accessor chains, `BinOp`/`UnaryOp` computed columns)
  still live in `_projection_ops.py` / `_ops.py` and are strictly **Map**, not
  Projection. They are candidates for the same treatment (fold into `MapOp` where the
  grammar allows).
- The **File** column below shows each node's *current* home; the **group header**
  shows its *strict* group. Where they differ, that node is a pending migration.

---

## How to read the tables

`extract_dataframe_op(op, root, selection_op=True, map_op=True)` is the one dispatcher.
It looks at a **generic** IR node (built by `_ops.py` while tracing pandas/polars calls)
and either (a) **replaces** it with a specialized node via a `make_*` factory or direct
construction, or (b) leaves it in place and only **sets its `output_type`** (a
"type-only" branch). Two flags gate replacements: `selection_op` (fold `df[mask]` into
`SelectionOp(MASK)`) and the new `map_op` (fold `df.assign(...)` into `AssignMapOp`).

- **Factory** — a `make_*` function builds the specialized node (may also rewire/detach neighbours).
- **Direct** — the node is constructed inline in the dispatcher (no `make_*`).
- **Type-only** — no replacement; the dispatcher just assigns `output_type`.

Columns: **Guard** = exact branch condition; **Side-effects** = in-place swap vs.
rewire/detach; each class is annotated with its **base class** (e.g.
`DropOp(ProjectionOp)`, `AssignMapOp(MapOp)`); **Example** = concrete snippet. Row `#`
numbers are stable across revisions so §1b/§1c/§2 cross-references line up.

**Group index**

| Strict group | Rows | Paper (§4.3) relationship |
|---|---|---|
| 1. Source | 1–4 | none (Stratum-only: data entry) |
| 2. Projection | 21, 20, 23, 9, 10 | PROJECTION + RENAME (pure column ops) |
| 3. Selection | 19, 14, 15, 16, 17, 18 | SELECTION + DROP DUPLICATES |
| 4. Map | 12, 12b, 22, 5, 11, 6, 20-dt | MAP + computed PROJECTION |
| 5. Aggregate | 8, 7 | GROUPBY |
| 6. Combiners & workflow | 13, C1, S1, S2, 24, 25 | JOIN, UNION, (none) |

---

### Group 1 — Source operations (`_source_ops.py`)

Introduce data into the graph (the leaves). **Paper:** no equivalent — the algebra
assumes a frame already exists; an executable optimizer also needs to say where data
comes from and whether it yields FRAME or MATRIX. **Migration:** already isolated in its
own module; matches the strict group.

| # | Operation (pandas surface) | From (generic node → base) | → To (specialized node → base) | Mechanism | File | OutputType | Guard (recognition predicate) | Graph side-effects | Example |
|---|---|---|---|---|---|---|---|---|---|
| 1 | In-memory DataFrame literal | `ValueOp(Op)` | `DataSourceOp(Op)` | Direct | `_source_ops.py` | FRAME | `len(inputs)==0` and `isinstance(op, ValueOp)` and value is pandas/polars `DataFrame` | New node **inherits `op.outputs`**; standard `replace_input_of_outputs`. No upstream (leaf source). | `pd.DataFrame({"age":[25,30]})` |
| 2 | Read CSV | `CallOp(Op)` (`pd.read_csv`) | `DataSourceOp(Op)` `format="csv"` | `make_read_op` | `_source_ops.py` | FRAME | `not is_frame_like(inputs[0])` and `op.func is pd.read_csv` | Constant args inlined into the node; variable args kept as `OperandRef` graph inputs. Node swapped in place. | `pd.read_csv("people.csv")` |
| 3 | Read Parquet | `CallOp(Op)` (`pd.read_parquet`) | `DataSourceOp(Op)` `format="parquet"` | `make_read_op` | `_source_ops.py` | FRAME | `op.func is pd.read_parquet` | Same as CSV. | `pd.read_parquet("people.parquet")` |
| 4 | Load NPY | `CallOp(Op)` (`np.load`) | `DataSourceOp(Op)` `format="npy"` | `make_read_op` | `_source_ops.py` | MATRIX | `op.func is np.load` | Same as CSV; declares MATRIX output. | `np.load("features.npy")` |

---

### Group 2 — Projection (pure column ops) (`_projection_ops.py`)

Eliminate columns or alter their **order/labels** — **no row change, no dtype/value
change**. **Paper:** PROJECTION + RENAME. **Migration:** these are the nodes that
genuinely stay in Projection under the strict scheme; the Map-semantics nodes that used
to sit here (assign/datetime/string/apply) move to Group 4.

| # | Operation (pandas surface) | From (generic node → base) | → To (specialized node → base) | Mechanism | File | OutputType | Guard (recognition predicate) | Graph side-effects | Example |
|---|---|---|---|---|---|---|---|---|---|
| 21 | Column / sub-frame select | `GetItemOp(Op)` (not a mask) | *(stays `GetItemOp(Op)`)* | Type-only (`_getitem_output_type`) | `_dataframe_ops.py` | SERIES or FRAME\* | `isinstance(op, GetItemOp)` and **not** `is_mask_selection` (or `selection_op=False`) | None — only sets `output_type` (SERIES/FRAME per key shape). | `df["age"]` / `df[["age","city"]]` |
| 20 | Attribute / column access | `GetAttrOp(Op)` | `GetAttrProjectionOp(Op)` `[...]` | `make_frame_get_attr` | `_projection_ops.py` | = input | `isinstance(op, GetAttrOp)` | Chained case fuses onto an existing `GetAttrProjectionOp` and **removes the old attr op** from its input's outputs; single case swaps in place. | `df.age` (pure column access) |
| 23 | skrub column selector | `TransformerOp(BaseEstimatorOp)` (`SelectCols`) | `ColumnSelectorOp(Op)` | `make_column_selector_op` | `_projection_ops.py` | FRAME | `isinstance(op, TransformerOp)` and `estimator` is `SelectCols`, no `param_refs`, `y` not an `OperandRef` | `op.replace_output_of_inputs(new_op)` — in-place swap; resolves column names at fit. | `skb.select(["age","city"])` |
| 9 | Rename | `MethodCallOp(Op)` (`rename`) | `MetadataOp(Op)` | Direct | `_projection_ops.py` | FRAME | `op.method_name in ["rename"]` | `op.replace_output_of_inputs(new_op)` — in-place swap, inputs' output pointers rewired. | `df.rename(columns={"age":"years"})` |
| 10 | Drop columns | `MethodCallOp(Op)` (`drop`) | `DropOp(ProjectionOp)` | Direct | `_projection_ops.py` | FRAME | `op.method_name == "drop"` | `op.replace_output_of_inputs(new_op)` — in-place swap. | `df.drop(columns=["city"])` |

\* Row 21: `df["col"]` → SERIES; `df[["a","b"]]` → FRAME (`_getitem_output_type`).

**Strict-taxonomy caveats (straddlers):**

- **Row 21 slice** `df[0:5]` selects *rows* → strictly **Selection**, not Projection. It rides the same `GetItemOp` type-only branch (also FRAME) but belongs to Group 3 semantically.
- **Row 20 `.dt`/`.str` chains** (`df["ts"].dt.year`, `df["name"].str...`) extract/transform *values/dtypes* → strictly **Map** (Group 4). Only the bare column access (`df.age`) is pure Projection.
- **Row 10 `drop(index=)`** removes *rows* → strictly **Selection**. Stratum keeps both `drop` forms under `DropOp` here because they share the pandas method and execution shape (an implementation grouping).

---

### Group 3 — Selection (row restriction) (`_selection_ops.py`)

Restrict **which rows survive** while keeping the column structure. **Paper:** SELECTION
(mask) + DROP DUPLICATES; Stratum also folds null-removal, positional prefix/suffix, and
sampling into the same group. **Migration:** already isolated; matches the strict group.

| # | Operation (pandas surface) | From (generic node → base) | → To (specialized node → base) | Mechanism | File | OutputType | Guard (recognition predicate) | Graph side-effects | Example |
|---|---|---|---|---|---|---|---|---|---|
| 19 | Boolean-mask filter | `GetItemOp(Op)` where `is_mask_selection` | `SelectionOp(Op)` `MASK, predicate` | `make_mask_selection_op` (+ `fold_column_expr`) | `_selection_ops.py` | FRAME | `is_mask_selection`: `op.key` is `OperandRef`, container `output_type==FRAME`, key op `output_type==SERIES` (⚠ boolean dtype **not** checked) | **Folds the mask subgraph into a `ColumnExpr` predicate**: nodes used *only* by the mask are absorbed & detached (removed from their inputs' outputs, own outputs cleared); external leaf ops kept as `OperandLeaf` inputs; source + kept leaves rewired to feed the selection; caller rewires downstream via `replace_input_of_outputs`. | `df[df["age"] > 18]` |
| 14 | Drop NA rows | `MethodCallOp(Op)` (`dropna`) | `SelectionOp(Op)` `DROPNA` | `make_selection_op` | `_selection_ops.py` | = input[0] | `op.method_name in _SELECTION_METHODS` | `op.replace_output_of_inputs(new_op)` — in-place swap. | `df.dropna()` |
| 15 | Drop duplicates | `MethodCallOp(Op)` (`drop_duplicates`) | `SelectionOp(Op)` `DROP_DUPLICATES` | `make_selection_op` | `_selection_ops.py` | = input[0] | `method_name in _SELECTION_METHODS` | In-place swap. | `df.drop_duplicates(subset=["city"])` |
| 16 | Head | `MethodCallOp(Op)` (`head`) | `SelectionOp(Op)` `HEAD` | `make_selection_op` | `_selection_ops.py` | = input[0] | `method_name in _SELECTION_METHODS` | In-place swap. | `df.head(5)` |
| 17 | Tail | `MethodCallOp(Op)` (`tail`) | `SelectionOp(Op)` `TAIL` | `make_selection_op` | `_selection_ops.py` | = input[0] | `method_name in _SELECTION_METHODS` | In-place swap. | `df.tail(5)` |
| 18 | Sample | `MethodCallOp(Op)` (`sample`) | `SelectionOp(Op)` `SAMPLE` | `make_selection_op` | `_selection_ops.py` | = input[0] | `method_name in _SELECTION_METHODS` | In-place swap. | `df.sample(n=10, random_state=0)` |

`SelectionOp` also declares a `QUERY` kind (no factory wires it yet) and, on pandas with
`FLAGS.pandas_query`, can emit `df.query(<predicate.to_pandas_query()>)` when the mask
predicate is query-expressible (falls back to boolean masking otherwise). Mask predicates
are `ColumnExpr` trees (see §1d). **Also strictly here** (currently handled elsewhere):
`drop(index=)` and `df[slice]`.

---

### Group 4 — Map (add/remove columns, change dtype/values) (`_map_ops.py` — new; rest pending in `_projection_ops.py`)

Add or remove columns, or change the **dtype/values** of columns, **without changing the
row population**. **Paper:** MAP (+ computed PROJECTION). **Migration:** this is the
group actively being built. `_map_ops.py` (`MapOp` base) is new; `AssignMapOp` is the
first member. Every other row below is **strictly Map but still physically in
`_projection_ops.py`/`_ops.py`** (pending extraction) — the File column shows the gap.

| # | Operation (pandas surface) | From (generic node → base) | → To (specialized node → base) | Mechanism | File | OutputType | Guard (recognition predicate) | Graph side-effects | Example |
|---|---|---|---|---|---|---|---|---|---|
| 12 | Assign (foldable) | `MethodCallOp(Op)` (`assign`) | `AssignMapOp(MapOp)` | `make_assign_map_op` | `_map_ops.py` **(migrated)** | FRAME | `map_op` flag on; **no positional args**; kwargs present; every kwarg is an `OperandRef` or a **scalar** constant (`_is_scalar_constant`) | **Folds all kwargs into `ColumnExpr` `entries` via one shared `_Folder`**: absorbed nodes detached & cleared, kept producers (`[src, *leaf_ops]`) rewired to the new op (`_detach_absorbed_and_rewire`). | `df.assign(is_adult=df["age"]>=18)` |
| 12b | Assign (unfoldable fallback) | `MethodCallOp(Op)` (`assign`) | `AssignOp(ProjectionOp)` | Direct (fallback when `make_assign_map_op` → `None`) | `_projection_ops.py` *(pending)* | FRAME | `make_assign_map_op` returns `None`: positional args, no kwargs, or a **sequence-valued** constant kwarg (list/array/Series) | `op.replace_output_of_inputs(new_op)` — opaque in-place swap (no folding). Polars: `with_columns(**kwargs)`. | `df.assign(c=[1,2,3])` (list ⇒ not foldable) |
| 22 | Elementwise binary / unary | `BinOp(Op)` / `UnaryOp(Op)` | *(stays)* | Type-only (`= input[0]`) | `_dataframe_ops.py` *(pending)* | = input[0] | `isinstance(op, (BinOp, UnaryOp))` | None — only sets `output_type = inputs[0].output_type`. Foldable into a `MapOp`/mask `ColumnExpr` when it feeds one. | `df["age"] > 7` / `df + 1` / `~mask` |
| 5 | Datetime parse | `CallOp(Op)` (`pd.to_datetime`) | `DatetimeConversionOp(ProjectionOp)` | `make_datetime_conversion_op` | `_projection_ops.py` *(pending)* | = input[0] | input **is** frame-like and `op.func is pd.to_datetime` | `op.replace_output_of_inputs(new_op)` — in-place swap. Foldable into a `DatetimeExpr` when polars-expressible (`polars_datetime_kwargs`). | `pd.to_datetime(df["ts"])` |
| 11 | Apply (UDF) | `MethodCallOp(Op)` (`apply`) | `ApplyUDFOp(ProjectionOp)` | Direct | `_projection_ops.py` *(pending)* | = input[0] | `op.method_name == "apply"` | `output_type` copied from `inputs[0]`; in-place swap. (Polars: `map_elements`/`map_rows`, with `sin`/`cos` fast paths.) | `df["age"].apply(lambda x: x+1)` |
| 6 | String method | `MethodCallOp(Op)` on `GetAttrProjectionOp(Op)` `["str"]` | `StringMethodOp(ProjectionOp)` | `make_string_method_op` | `_projection_ops.py` *(pending)* | SERIES | `isinstance(inputs[0], GetAttrProjectionOp)` and `inputs[0].attr_name == ["str"]` | **Detaches the `.str` accessor** — removes the method from the accessor's `outputs`, and if last consumer, unlinks it from the column too. New node feeds off the original column. Foldable into a `StrExpr`. | `df["name"].str.lower()` |
| 20-dt | Datetime/str attr chain | `GetAttrOp(Op)` → `GetAttrProjectionOp(Op)` `["dt", …]` | `GetAttrProjectionOp(Op)` (chain) | `make_frame_get_attr` | `_projection_ops.py` *(pending)* | = input | chained `GetAttrOp` (e.g. `.dt.year`) — same branch as row 20 | Chained fuse; **removes old attr op**. Foldable into a `DtExpr` (`.dt.<attr>`). | `df["ts"].dt.year` |

Supported map-fold grammar (what `_Folder._is_foldable` will absorb into a single lazy
kernel): `BinOp` in `BINARY_SYMBOLS`, `UnaryOp` in `UNARY_SYMBOLS`, `df["col"]` →
`Col`, `StringMethodOp` (literal args) → `StrExpr`, `DatetimeConversionOp`
(polars-expressible) → `DatetimeExpr`, `GetAttrProjectionOp(["dt", attr])` → `DtExpr`.
Anything outside the grammar stays a graph node and feeds the map as an `OperandLeaf`.

---

### Group 5 — Aggregate (`_aggregation_ops.py`)

Partition rows into groups and compute per-group values. **Paper:** GROUPBY. Stratum
**fuses** `groupby + agg → AggregateOp`; a bare groupby is only typed FRAME so the agg
can find it. **Migration:** already isolated; matches the strict group.

| # | Operation (pandas surface) | From (generic node → base) | → To (specialized node → base) | Mechanism | File | OutputType | Guard (recognition predicate) | Graph side-effects | Example |
|---|---|---|---|---|---|---|---|---|---|
| 8 | Groupby (bare) | `MethodCallOp(Op)` | *(stays `MethodCallOp(Op)`)* | Type-only (`FRAME`) | `_dataframe_ops.py` | FRAME | `op.method_name == "groupby"` | None — only sets `output_type=FRAME` so the following agg can find/fuse it. | `df.groupby("city")` |
| 7 | Grouped aggregation | `MethodCallOp(Op)` (agg) over `MethodCallOp(Op)` (`groupby`) | `AggregateOp(Op)` | `make_aggregate_op` | `_aggregation_ops.py` | FRAME | `_is_aggregation`: `inputs[0]` is a `groupby` **with exactly one consumer**, grouping key extractable, method in `_AGG_METHODS` or `agg/aggregate` with positional spec | **Bypasses the `groupby`**: `groupby_op.replace_output_of_inputs(new_op)` then removes the agg from the groupby's outputs, cutting the intermediate node out. | `df.groupby("city").mean()` |

Supported aggregations: `sum, mean, count, min, max, median, std, var, first, last,
prod, size, nunique, sem`, plus `agg(spec)`/`aggregate(spec)` (positional spec only).
`GroupedDataframeOp` is an experimental sibling (`process()` raises
`NotImplementedError`). **Limitation:** `AggregateOp`'s Polars backend is not implemented.

---

### Group 6 — Combiners & workflow (outside the strict five)

Not single-frame column/row transforms: **combiners** take ≥2 frames (Join, Concat);
**workflow/typing** nodes serve the ML DAG (Split) or just propagate a type
(Estimator/Choice). **Paper:** JOIN, ordered UNION, and (none) respectively.

| # | Operation (surface) | From (generic node → base) | → To (specialized node → base) | Mechanism | File | OutputType | Guard (recognition predicate) | Graph side-effects | Example |
|---|---|---|---|---|---|---|---|---|---|
| 13 | Join / Merge | `MethodCallOp(Op)` (`join`/`merge`) | `JoinOp(Op)` (chained → last of chain) | `make_join_op` | `_join_ops.py` | FRAME | `op.method_name in ["join","merge"]` | Single join: `op.replace_output_of_inputs`. **Chained** `df1.join([df2,df3])`: unrolled into a chain of binary `JoinOp`s (`_make_chained_join_op`), each right frame rewired, links wired parent→child; returns the final join. Normalizes `on`→`left_on`/`right_on`, index joins, suffixes; pandas→Polars `.merge`/`.join`. | `customers.merge(orders, on="id")` |
| C1 | Concatenate frames | `CallOp(Op)` (`pd.concat`) | `ConcatOp(Op)` | Direct build during **tracing** (**not** the dispatcher) | class in `_dataframe_ops.py`; built in `_ops.py` (~L980) | FRAME | `pd.concat` seen while tracing in `_ops.py` | Builds node from `first`/`others`/`axis` (constants or `OperandRef`s); no dispatcher rewrite. Polars: `axis=0`→`concat(how="diagonal_relaxed")`, `axis=1`→`concat(how="horizontal")`. | `pd.concat([df1, df2], axis=0)` |
| S1 | Joint X/y row selection | `X` (`input[0]`), `y` (`input[1]`) | `SplitOp(Op)` | `add_splitting_op` (graph pass) | `_split_ops.py` | FRAME (declared; runtime is a `(X[idx], y[idx])` tuple) | `op.is_X==True` and a matching `op.is_y==True` found in the graph | Inserts `SplitOp` fed by X and y, plus two `SplitOutput` consumers. Supports pandas / Polars / NumPy. | (implicit) aligned split of `X`, `y` |
| S2 | Extract one split component | `SplitOp` result (`input[0]`) | `SplitOutput(Op)` | `add_splitting_op` (graph pass) | `_split_ops.py` | FRAME (declared) | created alongside `SplitOp` | `is_x=True` → `inputs[0][0]` (X); `is_x=False` → `inputs[0][1]` (y). | `SplitOutput(is_x=True)` → X branch |
| 24 | Estimator / transformer | `BaseEstimatorOp(Op)` | *(stays)* | Type-only (`FRAME`) | `_dataframe_ops.py` | FRAME | `isinstance(op, BaseEstimatorOp)` (and not the SelectCols sub-case) | None — only sets `output_type=FRAME`. | `StandardScaler().fit_transform(X)` |
| 25 | Choice (grid alt.) | `ChoiceOp(Op)` | *(stays)* | Type-only (shared type / FRAME) | `_dataframe_ops.py` | SERIES/FRAME | `isinstance(op, ChoiceOp)` and all outcomes frame-like | None — sets `output_type` to shared outcome type, else FRAME. | `skb.choose_from({"a":sc_a,"b":sc_b})` |

---

## 1b. Class inheritance hierarchy

Every IR node derives from `Op`. Intermediate bases: `ProjectionOp` (projection family),
`MapOp` (**new** map family), `BaseEstimatorOp` (estimator family).

```
Op
├── ValueOp                 (row 1)
├── CallOp                  (rows 2–5, generic reads/to_datetime)
├── MethodCallOp            (rows 6–18, generic method calls)
├── GetAttrOp               (row 20 input)
├── GetItemOp               (rows 19, 21 input)
├── BinOp / UnaryOp         (row 22)
├── ChoiceOp                (row 25)
├── ImplOp                  (skrub impl wrapper — not a df op)
├── VariableOp              (external variable — not a df op)
├── SearchEvalOp            (grid-search eval — not a df op)
├── DataSourceOp            (rows 1–4 output)                 [Source]
├── MetadataOp              (row 9 output)                    [Projection]
├── ColumnSelectorOp        (row 23 output)                   [Projection]
├── GetAttrProjectionOp     (row 20 / 20-dt output)           [Projection / Map]
├── SelectionOp             (rows 14–19 output)               [Selection]
├── AggregateOp             (row 7 output)                    [Aggregate]
├── GroupedDataframeOp      (experimental; NotImplementedError)
├── JoinOp                  (row 13 output)                   [Combiner]
├── ConcatOp                (C1; built in _ops.py)            [Combiner]
├── SplitOp / SplitOutput   (S1/S2; add_splitting_op)         [Workflow]
├── ProjectionOp                     (base for the projection family)
│   ├── DropOp               (row 10 output)                  [Projection: cols / Selection: index]
│   ├── ApplyUDFOp           (row 11 output)                  [Map — pending move]
│   ├── AssignOp             (row 12b output, fallback)       [Map — pending move]
│   ├── DatetimeConversionOp (row 5 output)                   [Map — pending move]
│   └── StringMethodOp       (row 6 output)                   [Map — pending move]
├── MapOp                             (NEW base for the map family, _map_ops.py)
│   └── AssignMapOp          (row 12 output)                  [Map — migrated]
└── BaseEstimatorOp                  (base for the estimator family)
    ├── EstimatorOp          (predictor)
    └── TransformerOp        (transformer; SelectCols case → row 23)
```

Two asymmetries worth remembering: (1) several "projection-like" nodes (`MetadataOp`,
`ColumnSelectorOp`, `GetAttrProjectionOp`) inherit **directly from `Op`**, not from
`ProjectionOp`; (2) the `ProjectionOp` subtree currently **still holds Map-semantics
nodes** (`ApplyUDFOp`, `AssignOp`, `DatetimeConversionOp`, `StringMethodOp`) — these are
the pending migrations into the `MapOp` family alongside `AssignMapOp`.

**Reading the side-effects.** Patterns recur: (a) *in-place swap* —
`replace_output_of_inputs`/`replace_input_of_outputs` re-point neighbours (rows 5, 9–12b,
14–18, 23); (b) *detach an intermediate* — the `.str` accessor (6), the `groupby` (7),
the old attr op (20/20-dt); (c) *absorb a subgraph* — mask folding (19) and **assign-map
folding (12)** pull a whole tree into `ColumnExpr`s and detach everything used only by
them. Type-only rows (8, 21, 22, 24, 25) touch nothing but `output_type`.

---

## 1c. Paper ↔ Stratum operator mapping (§4.3 inspiration)

The paper classifies by **mathematical effect**; Stratum's *target* taxonomy classifies
by **which part of the frame is touched** (Source/Projection/Selection/Map/Aggregate),
which pulls MAP out of PROJECTION into its own group. Strongest correspondences:

```
Projection  <->  PROJECTION + RENAME          (pure column structure)
Selection   <->  SELECTION + DROP DUPLICATES
Map         <->  MAP + computed PROJECTION     (values/dtypes; new group)
Aggregate   <->  GROUPBY
Combiners   <->  JOIN, ordered UNION
```

| Paper operator (§4.3) | Stratum group / node(s) | Rows |
|---|---|---|
| SELECTION | `SelectionOp(MASK)` | 19 |
| PROJECTION (pure) | `GetItemOp` / `GetAttrProjectionOp` (col) / `ColumnSelectorOp` | 21, 20, 23 |
| RENAME | `MetadataOp` | 9 |
| Column removal | `DropOp` (impl. grouping; `drop(index=)` is really SELECTION) | 10 |
| MAP — assign | `AssignMapOp` (folded) / `AssignOp` (fallback) | 12, 12b |
| MAP — computed | `BinOp` / `UnaryOp` | 22 |
| MAP — values/dtypes | `ApplyUDFOp`, `StringMethodOp`, `DatetimeConversionOp`, `.dt`/`.str` chains | 11, 6, 5, 20-dt |
| DROP DUPLICATES | `SelectionOp(DROP_DUPLICATES)` | 15 |
| GROUPBY | `AggregateOp` after groupby+aggregate fusion | 7, 8 |
| CROSS PRODUCT / JOIN | `JoinOp` | 13 |
| UNION | `ConcatOp(axis=0)`, approximately | C1 |
| DIFFERENCE / SORT / WINDOW / TRANSPOSE / TOLABELS / FROMLABELS | *no dedicated node* | — |
| — (Stratum-only) | `DataSourceOp` — data entry | 1–4 |
| — (Stratum-only) | `SplitOp` / `SplitOutput` — ML X/y | S1, S2 |
| — (Stratum-only) | `ColumnExpr` classes — predicate/map representation | (in 19, 12) |

**Borderline cases:**

- `drop` — `drop(columns=)` = PROJECTION, `drop(index=)` = SELECTION; both under `DropOp`.
- `apply` — `axis=1` ≈ row-wise MAP, `axis=0` ≈ column-oriented, Series `apply` element-wise; all → `ApplyUDFOp` (Map).
- `assign` — MAP (adds computed columns): folds to `AssignMapOp`, else opaque `AssignOp`.
- `StringMethodOp` / `DatetimeConversionOp` / `.dt` chains — MAP over values/dtypes; foldable into `StrExpr`/`DatetimeExpr`/`DtExpr`.
- `drop_duplicates` — separate operator in the paper; SELECTION in Stratum (removes rows).
- `groupby` — independent operator in the paper; intermediate node in Stratum, fused with the aggregation.
- `concat(axis=0)` — ≈ ordered UNION; Stratum treats it as ordered concatenation (keeps duplicates, aligns schemas).

---

## 1d. The Map operator (new — `_map_ops.py`)

The Map group's machinery, added by `[FrameOperator] Map operator (#141)`. It expresses
column computations as **backend-agnostic `ColumnExpr` trees** so a whole `assign` folds
into a single lazy kernel on Polars (`with_columns`) or `assign` on pandas.

**`MapOp(Op)`** — base for folded column-map operators. `output_type = FRAME`.
`make_context(mode, inputs)` builds an `EvalContext(frame=inputs[0], inputs=inputs,
mode=mode)` that the `ColumnExpr` tree evaluates against.

**`AssignMapOp(MapOp)`** — the only map kind so far, from `df.assign(...)`. Field
`entries: dict[str, ColumnExpr]` maps each new column name to its folded expression;
input columns pass through.

    process(mode, inputs):
        polars:  frame.with_columns(**{name: expr.to_polars(ctx) for …})
        pandas:  frame.assign(**{name: expr.to_pandas(ctx) for …})

(with guards: an `OperandLeaf` yielding a pandas object is converted via
`pl.from_pandas`; a python list is wrapped as `pl.Series`.)

**`make_assign_map_op(op: MethodCallOp) -> AssignMapOp | None`** — the factory the
dispatcher calls for `assign` when `map_op` is on.

    returns None (→ keep opaque AssignOp) when:
        - op has positional args, or
        - no kwargs, or
        - any kwarg is a sequence-valued constant (list/array/Series)   [_is_scalar_constant]
    otherwise:
        - OperandRef kwargs  -> folded via one shared _Folder.fold_many(roots)
        - scalar constants   -> Const(value) entries
        - entries keep kwargs' assignment order (later cols may overwrite earlier)
        - inputs = [src, *folder.leaf_ops]; _detach_absorbed_and_rewire(op, new_op, folder)

**Shared folding engine (`_column_expr.py`, extended for #141).** `_Folder` now folds
**several roots at once** (`fold_many`) against one shared cone + memo, so a producer
feeding two assigned columns is absorbed once and both trees share the sub-expression.
Three passes: `_discover` (collect the foldable subgraph), `_absorbable` (keep nodes
with no external consumers), `_build` (materialise the tree; an `OperandLeaf` for the
rest).

Foldable grammar (`_is_foldable`) and the `ColumnExpr` node it yields:

| Graph node | Condition | ColumnExpr |
|---|---|---|
| `BinOp` | `op in BINARY_SYMBOLS` | `BinOpExpr` |
| `UnaryOp` | `op in UNARY_SYMBOLS` | `UnaryOpExpr` |
| `GetItemOp` `df["col"]` | string key, input is the src frame | `Col` |
| `StringMethodOp` | literal args only (`_has_literal_call_args`) | `StrExpr` |
| `DatetimeConversionOp` | literal args and `polars_datetime_kwargs(...) is not None` | `DatetimeExpr` |
| `GetAttrProjectionOp` | `len(attr_name)==2` and `attr_name[0]=="dt"` (`.dt.<attr>`) | `DtExpr` |
| anything else | — | `OperandLeaf` (stays a graph input) |

`ColumnExpr` gained `to_pandas(ctx)`, `to_polars(ctx)`, `to_pandas_query(params)` (for
the `SelectionOp` query fast path), plus `iter_operand_refs()` / `remap_operand_refs()`
for operand-index bookkeeping during rewrites. `DtExpr` and `DatetimeExpr` are the two
new expression nodes (added alongside `Col`, `Const`, `OperandLeaf`, `BinOpExpr`,
`UnaryOpExpr`, `StrExpr`).

**Why this matters for the taxonomy:** the same `ColumnExpr` language now backs both
**Selection** predicates (`df[mask]`) and **Map** computations (`df.assign`). That shared
substrate is what makes the strict Map group buildable step by step — each remaining
Map-semantics node (datetime, string, apply, `.dt`) already has, or can get, a
`ColumnExpr` form and be folded into a `MapOp` rather than kept as an opaque
`ProjectionOp`.

---

## 2. What each strict group changes

- **Source (1–4):** where a frame/matrix *enters* the graph; NPY is the only MATRIX source.
- **Projection (21, 20-col, 23, 9, 10-cols):** change *which columns exist / their order/labels*; rows and dtypes untouched.
- **Selection (14–19):** restrict *rows*, keep columns. Method kinds are 1:1 with a frame method; `MASK` carries a folded `ColumnExpr` predicate.
- **Map (12/12b, 22, 5, 11, 6, 20-dt):** add/remove columns or change *values/dtypes*; row population unchanged. `AssignMapOp` folds to one lazy kernel; the rest are still opaque `ProjectionOp`s pending the fold.
- **Aggregate (7, 8):** fuse `groupby` + agg into one node; the bare `groupby` is only typed so the agg can find it.
- **Combiners & workflow (13, C1, S1, S2, 24, 25):** ≥2-frame joins/concats, ML X/y split, and type-only estimator/choice branches.

---

## 3. Coverage gap analysis — remaining pandas methods (by strict group)

Common pandas methods **not** yet recognized, and the strict group each belongs to.

### → Selection (`_selection_ops.py`)
- `query(expr)` → `SelectionKind.QUERY` **exists as an enum but no factory creates it**; the predicate plumbing (`to_pandas_query`) is already there, so wiring it is the highest-value gap.
- `nlargest(n, col)` / `nsmallest(n, col)` → new ordered-restriction kinds (like HEAD/TAIL but predicate-ordered).
- `isin(...)` → a boolean mask; folds into a MASK `ColumnExpr`, not its own node.

### → Projection (`_projection_ops.py`)
- `df.filter(items=/like=/regex=)` — selects *columns* despite the name → pure Projection.
- `set_index(...)` / `reset_index(...)` — index/label reshaping; metadata-like → extend `MetadataOp`.

### → Map (`_map_ops.py` target; today `_projection_ops.py`)
- `astype(...)` / `convert_dtypes()` — dtype cast → a `CastOp`/`MapOp` kind (sibling of `DatetimeConversionOp`); foldable.
- `fillna(...)` / `replace(...)` — value substitution (no row drop) → Map.
- `clip(...)`, `round(...)`, `rank(...)`, `cumsum()/cumprod()/cummax()` — elementwise column transforms → Map (numeric ones can route through `_numeric_ops.py`).
- **Migration note:** `AssignOp`, `DatetimeConversionOp`, `StringMethodOp`, `ApplyUDFOp` already exist but strictly belong in the Map group — folding them into `MapOp` (as `assign` now is) is the natural next step.

### → Aggregate (`_aggregation_ops.py`)
- **Non-grouped reductions:** `df.mean()`, `df.sum()`, `df.describe()` — only groupby-fused aggregations are captured; a bare reduction needs an `AggregateOp` variant with no grouping key (SCALAR/SERIES output).
- `pivot_table(...)` / `crosstab(...)` — grouped reshapes (heavier, but semantically aggregation).
- `agg`/`aggregate` with **dict/kwargs spec** — only the positional-spec form is supported today.
- `transform(...)` — groupby-broadcast (same shape); own kind, lives with aggregation.

### → Combiners (`_join_ops.py`) / reshapes
- `combine_first(...)`, `update(...)`, `merge_asof`/`merge_ordered` — `JoinOp` cousins/flags.
- `pd.concat` — modelled by `ConcatOp` but built in `_ops.py`, not the dispatcher; consider routing through `extract_dataframe_op`.
- **Reshapes** `melt/pivot/stack/unstack/explode/transpose` — change row/column *structure*; fit none of the five → candidate new `_reshape_ops.py` (the biggest structural gap).

### Numeric / matrix — `_numeric_ops.py`
Handles the MATRIX/NumPy path (`NumericOp`, `make_unary_numeric_op`,
`make_binary_numeric_op`; `np.log/exp/sqrt/abs/square/log1p/expm1` and `+ - * /`).
Elementwise math on a MATRIX belongs here, not in the frame modules. (Still absent from
the text map — worth adding.)

---

## 4. Table columns / further data

Included columns: operation, from-node (+base), to-node (+base), mechanism, owning file,
OutputType(+rule), **guard**, **graph side-effects**, example. Additional data that would
help as the migration proceeds:

1. **Strict group vs. current file** — *now shown* via the group header vs. the File column; the mismatch is the migration to-do list.
2. **Polars divergence** — several nodes differ (`assign`→`with_columns`, `dropna`→`drop_nulls`, `drop_duplicates`→`unique`, `AggregateOp` polars *not implemented*, `StringMethodOp` renamed methods). A dedicated column would make backend gaps explicit.
3. **Foldable? (Map/Selection)** — whether a node can be absorbed into a `ColumnExpr` (per §1d grammar) vs. stays an opaque graph node. Directly tracks how far the Map build has progressed.
4. **Status / maturity** — experimental/not-wired branches (`GroupedDataframeOp` → `NotImplementedError`; `QUERY` kind unwired; `AggregateOp` no polars path).
