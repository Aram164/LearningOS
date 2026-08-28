# Stage Working Notes

## Mental Models

### Python model

functions are runtime objects that can be stored, passed, returned, inspected, and partially applied; a callable value is not the result of calling it.

### Stratum relevance

match factories return predicates, rewrite_pass consumes match and action callables, and registry records store supports/cost functions.

### Failure mode

calling during configuration, losing captured configuration, or designing a class where one function value is the clearer interface.

### Engineering ownership

AI may critique only after your own model and first attempt exist. You remain responsible for the specification, trade-offs, every accepted line, tests, failure behavior, and maintenance cost.

## Read-only Anchor

Read-only: stratum/optimizer/_numeric_rewrites.py::match_two_op_chain and match_identity_operation; stratum/optimizer/_op_utils.py::rewrite_pass; physical implementation supports and cost callables in stratum/optimizer/physical/_registry.py.

## Component

- stratum/optimizer/_numeric_rewrites.py
- stratum/optimizer/_op_utils.py
- stratum/optimizer/physical/_registry.py

## Verified Against



## External Code Boundary

Any Stratum paths above refer to the sibling `semestercontext/Stratum/` worktree. They are optional read-only learning anchors: LearningOS does not index, validate, manage, or write that codebase.
