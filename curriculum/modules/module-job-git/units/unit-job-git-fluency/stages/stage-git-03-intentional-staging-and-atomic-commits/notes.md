# Stage Working Notes

## Mental Models

### Core model

the index is an editable draft snapshot, so one working session can be decomposed into several commits without rewriting files.

### Working practice

stage by path or hunk, review the exact staged diff, test that snapshot, and write a message that records why.

### Job relevance

small semantic commits make optimizer behavior easier to review, bisect, revert, and backport.

### Failure mode

git add . followed by a vague message that mixes refactoring, behavior, tests, and formatting.

## Read-only Anchor

Read-only in Stratum: select one multi-file historical commit with git show --stat and git show. Decide whether it represents one purpose, whether tests travel with behavior, and whether the message preserves the forcing reason. Do not rewrite it.

## Component


## Verified Against



## External Code Boundary

Any Stratum paths above refer to the sibling `semestercontext/Stratum/` worktree. They are optional read-only learning anchors: LearningOS does not index, validate, manage, or write that codebase.
