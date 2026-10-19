# Stage Working Notes

## Mental Models

### Pandas baseline

Specify the familiar pandas-facing values, schema, ordering, failure, index, and dtype behavior before implementing the eager executor.

### Polars mirror

Implement the same declared contract idiomatically with Polars expressions or lazy plans, then state and test every intentional divergence.

### Integrate the full workflow

define a backend-neutral logical contract; normalize pandas-facing arguments; implement independent pandas and Polars executors; declare unsupported cases; test values, schema, order, and failures; inspect a Polars lazy plan; benchmark without counting setup/conversion accidentally; and explain how the standalone design would map onto Stratum’s logical/physical registry without changing the read-only repository.

## Read-only Anchor

Optional cross-reference — the Stratum track owns this material, and no session is blocked on it. Read it only to see the idea already in production. Choose Join as the default capstone because it exercises the real Stratum parity layer; choose GroupBy+Aggregate or Selection only if the current ticket makes it more useful. Work entirely in Job/workspace-job-deem/scratch or another non-Stratum lab directory. The Stratum checkout supplies observations, not a place to practice edits.

## Component


## Verified Against



## External Code Boundary

Any Stratum paths above refer to the sibling `semestercontext/Stratum/` worktree. They are optional read-only learning anchors: LearningOS does not index, validate, manage, or write that codebase.
