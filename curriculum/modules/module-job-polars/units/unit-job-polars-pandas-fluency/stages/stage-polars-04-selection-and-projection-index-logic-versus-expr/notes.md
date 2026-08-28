# Stage Working Notes

## Mental Models

### Pandas baseline

df[col], df[[cols]], loc, iloc, boolean masks, query, label alignment, and Series-versus-DataFrame return shapes.

### Polars mirror

select, filter, row slicing, pl.col, selectors, expression expansion, and the deliberate absence of loc/iloc/index alignment. Separate column projection from row selection.

## Read-only Anchor

Optional cross-reference — the Stratum track owns this material, and no session is blocked on it. Read it only to see the idea already in production. Read-only: stratum/optimizer/ir/_dataframe_ops.py, stratum/optimizer/physical/_getitem_execs.py, stratum/optimizer/physical/_selection_execs.py, and stratum/optimizer/physical/_projection_execs.py. Identify when df[key] becomes ColumnProjectionOp, SelectionOp, or fallback GetItemOp; compare pandas boolean indexing/query with Polars filter.

## Component

- stratum/optimizer/ir/_dataframe_ops.py
- stratum/optimizer/physical/_getitem_execs.py
- stratum/optimizer/physical/_projection_execs.py
- stratum/optimizer/physical/_selection_execs.py

## Verified Against



## External Code Boundary

Any Stratum paths above refer to the sibling `semestercontext/Stratum/` worktree. They are optional read-only learning anchors: LearningOS does not index, validate, manage, or write that codebase.
