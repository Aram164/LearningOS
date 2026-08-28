# Stage Working Notes

## Mental Models

### Python model

syntax delegates to data-model protocols; repr, equality, hashing, iteration, containment, context management, and attribute access each carry contracts. Slots change instance storage but not semantics, and equal hashable objects must share a hash.

### Stratum relevance

expression values use structural keys while Op nodes deliberately preserve identity; repr must remain safe during optimizer failures.

### Failure mode

implementing too many dunders, structural equality on identity nodes, hash changes after insertion, or repr that raises while debugging the original error.

### Engineering ownership

AI may critique only after your own model and first attempt exist. You remain responsible for the specification, trade-offs, every accepted line, tests, failure behavior, and maintenance cost.

## Read-only Anchor

Read-only: Op.__repr__, Op.__str__, and update_name in stratum/optimizer/ir/_ops.py; _key, __repr__, and __slots__ across stratum/optimizer/ir/_column_expr.py; deliberate absence of structural Op equality.

## Component

- stratum/optimizer/ir/_column_expr.py
- stratum/optimizer/ir/_ops.py

## Verified Against



## External Code Boundary

Any Stratum paths above refer to the sibling `semestercontext/Stratum/` worktree. They are optional read-only learning anchors: LearningOS does not index, validate, manage, or write that codebase.
