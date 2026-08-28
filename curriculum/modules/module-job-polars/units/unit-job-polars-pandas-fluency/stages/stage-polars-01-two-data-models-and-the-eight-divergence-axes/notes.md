# Stage Working Notes

## Mental Models

### Pandas baseline

eager DataFrame/Series operations, index-bearing row identity, implicit alignment, and Copy-on-Write.

### Polars mirror

index-free DataFrame/Series, strict schema, immutable-style transformations, expression-oriented execution, and Arrow-backed columns.

### The working method

parity means preserving an explicit operation contract, not copying method names. When a new method arrives, you do not recall a memorised table — you ask the eight questions below and the contract falls out.

### Axis 1 — Row identity

pandas gives every row a label through the index, and that label drives alignment, join-on-index, and assignment. Polars rows have position only. Ask: does this operation consult row labels, and what happens to them in the result?

### Axis 2 — Null model

pandas spreads missingness across None, NaN, NaT and pd.NA with dtype-dependent behaviour; Polars separates a null from a floating NaN. Ask: which of the two does this produce, and does it propagate, get skipped, or form a group key?

### Axis 3 — Type promotion and strictness

pandas widens silently — int to float on a missing value, to object on mixed input; Polars computes a supertype or raises. Ask: what dtype comes out, and was anyone told it changed?

### Axis 4 — Ordering and determinism

pandas sort_values defaults to an unstable quicksort with na_position='last'; Polars sort takes nulls_last and maintain_order explicitly, and several Polars operations promise no order at all. Ask: is this row order guaranteed, incidental, or undefined?

### Axis 5 — Cardinality and shape

reduce is fewer rows, map is the same rows, window is the same rows scoped by group, explode is more rows. pandas puts the choice in the method (agg versus transform); Polars puts it in the context (agg versus over). Ask: how many rows come out, and where did the keys land?

### Axis 6 — Evaluation context

pandas assign evaluates sequentially, so a new column can see the one defined before it; Polars with_columns evaluates the whole list against the input frame, so siblings are invisible. Ask: which frame is this expression resolved against, and when?

### Axis 7 — Key cardinality and duplicates

duplicate join keys multiply rows in both libraries, but pandas additionally permits duplicate index labels and duplicate column names. Ask: what does this operation do when the key is not unique?

### Axis 8 — Failure contract

pandas mostly coerces, warns, or returns something; Polars mostly raises. Ask: on bad input does this raise, coerce silently, or return a wrong-but-plausible answer?

## Read-only Anchor

Optional cross-reference — the Stratum track owns this material, and no session is blocked on it. Read it only to see the idea already in production. Read-only trace: stratum/optimizer/ir/_join_ops.py defines one backend-neutral JoinOp; stratum/optimizer/physical/_join_execs.py registers PandasJoinOp and PolarsJoinOp; stratum/optimizer/physical/_plan_context.py and stratum/optimizer/physical/_impl_selection.py decide the physical class before execution. Write a one-page trace from a pandas merge call to the selected physical implementation.

## Component

- stratum/optimizer/ir/_join_ops.py
- stratum/optimizer/physical/_impl_selection.py
- stratum/optimizer/physical/_join_execs.py
- stratum/optimizer/physical/_plan_context.py

## Verified Against



## External Code Boundary

Any Stratum paths above refer to the sibling `semestercontext/Stratum/` worktree. They are optional read-only learning anchors: LearningOS does not index, validate, manage, or write that codebase.
