# Stage Working Notes

## Mental Models

### Core model

a pull request is a hosted review and integration proposal between branch tips; Git stores commits, while GitHub adds discussion, checks, permissions, and merge policies.

### Working practice

branch from the correct upstream base, keep scope narrow, explain problem and evidence, respond to review with intentional commits, then choose merge/squash/rebase according to project policy.

### Job relevance

Stratum work is judged through the clarity and verifiability of its contribution, not merely whether local code runs.

### Failure mode

mixing unrelated changes, pushing generated noise, hiding trade-offs, or rewriting a reviewed branch without communicating.

## Read-only Anchor

Read-only in Stratum: inspect one merged contribution's commit series and available PR metadata if already local/accessible; identify base, head, review units, tests, and final integration shape. Do not create branches or contact remotes.

## Component


## Verified Against



## External Code Boundary

Any Stratum paths above refer to the sibling `semestercontext/Stratum/` worktree. They are optional read-only learning anchors: LearningOS does not index, validate, manage, or write that codebase.
