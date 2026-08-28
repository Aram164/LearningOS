# Stage Working Notes

## Mental Models

### Python model

graph code combines identity-based nodes, adjacency invariants, queues, generators, cloning, and careful mutation; topological order is a partial-order contract, not an incidental list.

### Stratum relevance

optimizer correctness depends on indegree bookkeeping, traversal order, clone boundaries, root replacement, and bidirectional edges.

### Failure mode

O(N squared) rescans, duplicate edges, stale reverse links, mutation during traversal, or accepting a cycle as an odd ordering.

### Engineering ownership

AI may critique only after your own model and first attempt exist. You remain responsible for the specification, trade-offs, every accepted line, tests, failure behavior, and maintenance cost.

## Read-only Anchor

Read-only: clone_sub_dag, compute_graph_node_indegree, topological_iterator_bfs/dfs, validate_dag, and rewrite_pass in stratum/optimizer/_op_utils.py; replace_input/output helpers in stratum/optimizer/ir/_base.py.

## Component

- stratum/optimizer/_op_utils.py
- stratum/optimizer/ir/_base.py

## Verified Against



## External Code Boundary

Any Stratum paths above refer to the sibling `semestercontext/Stratum/` worktree. They are optional read-only learning anchors: LearningOS does not index, validate, manage, or write that codebase.
