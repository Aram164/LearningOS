# Stage Working Notes

## Mental Models

### Python model

local, enclosing, global, and built-in resolution is determined per code object; closures retain cells, not frozen values, and nonlocal changes an enclosing binding.

### Stratum relevance

generated match functions close over operation classes and configuration, and rewrite runners rebind a root as transformations replace it.

### Failure mode

late binding, accidental UnboundLocalError, confusing mutation with nonlocal rebinding, or assuming a closure copied its value.

### Engineering ownership

AI may critique only after your own model and first attempt exist. You remain responsible for the specification, trade-offs, every accepted line, tests, failure behavior, and maintenance cost.

## Read-only Anchor

Read-only: stratum/optimizer/_op_utils.py::rewrite_pass and its rebinding of root; closures returned by stratum/optimizer/_numeric_rewrites.py match factories; in-method imports in stratum/optimizer/ir/_column_expr.py as a scope/import bridge.

## Component

- stratum/optimizer/_numeric_rewrites.py
- stratum/optimizer/_op_utils.py
- stratum/optimizer/ir/_column_expr.py

## Verified Against



## External Code Boundary

Any Stratum paths above refer to the sibling `semestercontext/Stratum/` worktree. They are optional read-only learning anchors: LearningOS does not index, validate, manage, or write that codebase.
