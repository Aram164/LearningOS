# Stage Working Notes

## Mental Models

### Pandas baseline

dtype inference at construction, silent upcast on missing values, object as the universal fallback, the NumPy-backed versus nullable-extension split, and astype/convert_dtypes as after-the-fact repairs.

### Polars mirror

a declared schema that survives operations, supertype resolution across branches, strict versus non-strict cast, overflow behaviour, and an error where pandas would have widened.

### Why this is its own stage

Type promotion is the divergence most likely to pass every value check and still be wrong. Two frames can hold identical numbers under different dtypes, and the difference only surfaces three operations later.

## Read-only Anchor



## Component


## Verified Against



## External Code Boundary

Any Stratum paths above refer to the sibling `semestercontext/Stratum/` worktree. They are optional read-only learning anchors: LearningOS does not index, validate, manage, or write that codebase.
