# Stage Working Notes

## Mental Models

### Core model

a remote is a named collection of URLs and refspecs; origin/main is a local remote-tracking ref updated by fetch, not the live branch on a server. Fetch transfers objects and updates configured tracking refs without integrating them into the current branch.

### Working practice

fetch, inspect divergence, then choose merge, rebase, fast-forward, or no action.

### Job relevance

clear origin/upstream semantics are essential for fork-based contribution and for knowing exactly whose branch a ticket follows.

### Failure mode

believing fetch changes files, confusing main with origin/main, or using pull before observing what arrived.

## Read-only Anchor

Read-only in Stratum: inspect git remote -v, git remote show, git branch -vv, and ahead/behind counts. Do not fetch because the checkout is required to remain externally unchanged.

## Component


## Verified Against



## External Code Boundary

Any Stratum paths above refer to the sibling `semestercontext/Stratum/` worktree. They are optional read-only learning anchors: LearningOS does not index, validate, manage, or write that codebase.
