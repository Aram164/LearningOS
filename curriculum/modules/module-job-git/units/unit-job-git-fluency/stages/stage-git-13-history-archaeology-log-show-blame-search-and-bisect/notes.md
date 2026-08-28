# Stage Working Notes

## Mental Models

### Core model

repository history is a queryable causal record; path filters, pickaxe search, line history, blame, and binary search answer different questions.

### Working practice

start from a reproducible observation, narrow the search space, inspect whole commits and messages, and verify the candidate rather than blaming an author.

### Job relevance

unfamiliar optimizer behavior is often faster to understand through when-and-why history than through current code alone.

### Failure mode

reading blame as ownership, using visual chronology as causality, or bisecting with a flaky predicate.

## Read-only Anchor

Read-only in Stratum: choose one behavior in join or aggregation logic and trace it with log -- path, log -S/-G, blame -L, and show. Record evidence and uncertainty; do not infer intent from author names alone.

## Component


## Verified Against



## External Code Boundary

Any Stratum paths above refer to the sibling `semestercontext/Stratum/` worktree. They are optional read-only learning anchors: LearningOS does not index, validate, manage, or write that codebase.
