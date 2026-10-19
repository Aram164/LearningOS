# Stage Working Notes

## Mental Models

### Pandas baseline

concat along axis 0/1, join inner/outer, ignore_index, keys/MultiIndex, dtype reconciliation, melt, pivot, pivot_table, stack/unstack.

### Polars mirror

concat vertical/vertical_relaxed/horizontal/diagonal, rechunk, align_frames when appropriate, unpivot, eager pivot, and lazy-schema limitations for pivot.

## Read-only Anchor

Optional cross-reference — the Stratum track owns this material, and no session is blocked on it. Read it only to see the idea already in production. Read-only: stratum/optimizer/physical/_concat_execs.py and stratum/optimizer/physical/_source_execs.py::rechunk_pl_frame. Compare the backend calls and identify which pandas concat axes/options cannot be mirrored by the current Polars implementation.

## Component

- stratum/optimizer/physical/_concat_execs.py
- stratum/optimizer/physical/_source_execs.py

## Verified Against



## External Code Boundary

Any Stratum paths above refer to the sibling `semestercontext/Stratum/` worktree. They are optional read-only learning anchors: LearningOS does not index, validate, manage, or write that codebase.
