# Stage Working Notes

## Mental Models

### Pandas baseline

NumPy-backed versus PyArrow-backed columns, to_numpy, Arrow conversion, Copy-on-Write, and object dtype.

### Polars mirror

Arrow columnar memory, chunks/ChunkedArray, to_arrow/from_arrow, Arrow PyCapsule interface, to_pandas/from_pandas, zero-copy conditions, categorical/string/nested types, and when conversion copies or changes representation.

## Read-only Anchor

Optional cross-reference — the Stratum track owns this material, and no session is blocked on it. Read it only to see the idea already in production. Read-only: stratum/optimizer/physical/_source_execs.py, stratum/optimizer/physical/_projection_execs.py conversion fallbacks, stratum/runtime/_object_serialization.py, and _rust/. Map where a frame can change representation and mark each boundary as potentially zero-copy, conditional, or copying.

## Component

- _rust/
- stratum/optimizer/physical/_projection_execs.py
- stratum/optimizer/physical/_source_execs.py
- stratum/runtime/_object_serialization.py

## Verified Against



## External Code Boundary

Any Stratum paths above refer to the sibling `semestercontext/Stratum/` worktree. They are optional read-only learning anchors: LearningOS does not index, validate, manage, or write that codebase.
