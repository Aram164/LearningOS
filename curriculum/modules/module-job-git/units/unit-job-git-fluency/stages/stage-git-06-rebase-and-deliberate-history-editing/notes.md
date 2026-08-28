# Stage Working Notes

## Mental Models

### Core model

rebase copies commits onto a new base, producing new object IDs; interactive rebase is a program for reorder, edit, squash, fixup, drop, and exec.

### Working practice

rewrite only private history, preserve authorship and intent, and verify the complete range before updating a remote.

### Job relevance

a clean feature series reduces reviewer load and separates preparatory refactors from behavior changes.

### Safety rule

shared commits are coordination points, so rewriting them forces everyone else to reconcile different histories.

### Failure mode

using rebase as cosmetic magic or force-pushing without lease and without inspecting divergence.

## Read-only Anchor

Read-only in Stratum: compare the first-parent graph with the full graph and identify any rebased-looking linear feature series only as an inference. Do not rebase or alter refs.

## Component


## Verified Against



## External Code Boundary

Any Stratum paths above refer to the sibling `semestercontext/Stratum/` worktree. They are optional read-only learning anchors: LearningOS does not index, validate, manage, or write that codebase.
