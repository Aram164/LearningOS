# Stage Working Notes

## Mental Models

### Pandas baseline

groupby.transform, rank, shift, cumulative operations, rolling/expanding, and index-aligned return shapes.

### Polars mirror

expression.over, mapping strategies, window expressions, shift/rank/cum_* and rolling expressions. Separate reduction (fewer rows) from windowing (same row cardinality).

## Read-only Anchor

Optional cross-reference — the Stratum track owns this material, and no session is blocked on it. Read it only to see the idea already in production. Read-only gap analysis: search the Stratum IR and physical registries for window/transform support, then record what is present, absent, or represented generically. Do not infer support from a matching pandas method name.

## Component


## Verified Against



## External Code Boundary

Any Stratum paths above refer to the sibling `semestercontext/Stratum/` worktree. They are optional read-only learning anchors: LearningOS does not index, validate, manage, or write that codebase.
