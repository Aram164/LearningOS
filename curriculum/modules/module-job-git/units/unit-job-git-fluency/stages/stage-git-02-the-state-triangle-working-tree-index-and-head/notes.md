# Stage Working Notes

## Mental Models

### Core model

one path may have three simultaneously different versions—HEAD, index, and working tree—and untracked files are outside the committed snapshot graph.

### Working practice

use status, diff, and diff --cached as a diagnostic triangle before add, restore, or commit.

### Job relevance

precise staging lets a mixed Stratum edit become coherent, independently reviewable commits.

### Safety rule

restore and clean can destroy data that Git has never stored.

### Failure mode

treating git add as file registration once rather than copying the current content into the index.

## Read-only Anchor

Read-only in Stratum: inspect git status --short, git diff, and git diff --cached; for one changed path, state exactly which comparisons are empty or non-empty. Never stage, restore, or clean anything in Stratum.

## Component


## Verified Against



## External Code Boundary

Any Stratum paths above refer to the sibling `semestercontext/Stratum/` worktree. They are optional read-only learning anchors: LearningOS does not index, validate, manage, or write that codebase.
