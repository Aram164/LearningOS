# Stage Working Notes

## Mental Models

### Core model

stash stores commit-like snapshots referenced under refs/stash; the working tree, index, untracked files, and ignored files are included only according to options.

### Working practice

prefer a small WIP commit on a private branch when history is useful; use named stashes for genuinely temporary context switches and inspect before applying.

### Job relevance

urgent ticket switches should preserve experimental state without contaminating the current feature.

### Failure mode

treating stash as a magical drawer, accumulating anonymous entries, or popping before understanding conflicts.

## Read-only Anchor

Read-only in Stratum: if git stash list is non-empty, inspect names only and do not show, apply, pop, drop, or clear. Compare stash versus WIP-commit trade-offs for a hypothetical interrupted optimizer change.

## Component


## Verified Against



## External Code Boundary

Any Stratum paths above refer to the sibling `semestercontext/Stratum/` worktree. They are optional read-only learning anchors: LearningOS does not index, validate, manage, or write that codebase.
