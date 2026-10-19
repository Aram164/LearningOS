# Stage Working Notes

## Mental Models

### Pandas baseline

sort_values with an unstable default kind and na_position='last', sort_index, the groupby sort argument, nlargest/nsmallest, and a merge whose row order is documented loosely enough that callers depend on an accident.

### Polars mirror

sort with explicit descending and nulls_last, maintain_order on group_by and unique and join, top_k, and a general willingness to reorder rows for parallelism unless told otherwise.

### Why order is a first-class axis

Preserving pandas behaviour means preserving what callers actually rely on, and row order is the thing they rely on without knowing it. Ordering is also where a parity harness most easily lies in both directions — passing because order was normalized away, or failing on a difference that was never promised.

## Read-only Anchor



## Component


## Verified Against



## External Code Boundary

Any Stratum paths above refer to the sibling `semestercontext/Stratum/` worktree. They are optional read-only learning anchors: LearningOS does not index, validate, manage, or write that codebase.
