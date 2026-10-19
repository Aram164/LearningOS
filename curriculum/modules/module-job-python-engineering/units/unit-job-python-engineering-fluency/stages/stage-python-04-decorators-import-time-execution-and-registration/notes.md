# Stage Working Notes

## Mental Models

### Python model

@decorator(expression) is nested function application executed while a module body defines the decorated object; wrappers must preserve metadata and registration decorators may intentionally create import-time side effects.

### Stratum relevance

physical_impl collects implementations before the selector can use them.

### Failure mode

registering the wrapper instead of the class, forgetting to import a registration module, evaluating configuration at call time, or hiding metadata without functools.wraps.

### Engineering ownership

AI may critique only after your own model and first attempt exist. You remain responsible for the specification, trade-offs, every accepted line, tests, failure behavior, and maintenance cost.

## Read-only Anchor

Read-only: stratum/optimizer/physical/_registry.py::physical_impl, _DECORATED_IMPLS, and build_default_physical_registry; consumer path in stratum/optimizer/physical/_impl_selection.py.

## Component

- stratum/optimizer/physical/_impl_selection.py
- stratum/optimizer/physical/_registry.py

## Verified Against



## External Code Boundary

Any Stratum paths above refer to the sibling `semestercontext/Stratum/` worktree. They are optional read-only learning anchors: LearningOS does not index, validate, manage, or write that codebase.
