# Stage Working Notes

## Mental Models

### Python model

iterators are stateful one-pass objects, generator bodies run on demand, yield from delegates a protocol, and recursive traversal needs explicit leaf and container rules.

### Stratum relevance

operand discovery and graph traversal are lazy, while rewrite actions may replace the structure being walked.

### Failure mode

consuming an iterator twice, mutating a traversal frontier, forgetting a heterogeneous container branch, or assuming generator creation executed its body.

### Engineering ownership

AI may critique only after your own model and first attempt exist. You remain responsible for the specification, trade-offs, every accepted line, tests, failure behavior, and maintenance cost.

## Read-only Anchor

Read-only: iter_operand_refs in stratum/optimizer/ir/_column_expr.py; _iter_operand_refs, topological_iterator, BFS/DFS walkers, and validate_dag in stratum/optimizer/_op_utils.py.

## Component

- stratum/optimizer/_op_utils.py
- stratum/optimizer/ir/_column_expr.py

## Verified Against



## External Code Boundary

Any Stratum paths above refer to the sibling `semestercontext/Stratum/` worktree. They are optional read-only learning anchors: LearningOS does not index, validate, manage, or write that codebase.
