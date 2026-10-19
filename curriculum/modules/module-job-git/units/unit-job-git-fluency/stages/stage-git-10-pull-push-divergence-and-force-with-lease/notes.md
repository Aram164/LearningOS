# Stage Working Notes

## Mental Models

### Core model

pull is fetch followed by a configured integration strategy; push asks a remote to update refs if safety rules allow. A non-fast-forward rejection protects commits the sender may not possess.

### Working practice

inspect ahead/behind, choose an explicit pull strategy, and use force-with-lease only for intentionally rewritten private branches after fetching.

### Job relevance

predictable synchronization avoids merge-noise commits and accidental overwrites in collaborative work.

### Safety rule

force is a ref overwrite request; a lease adds a concurrency precondition but does not make shared-history rewriting harmless.

### Failure mode

repeatedly pulling until errors disappear or using --force to bypass a rejection.

## Read-only Anchor

Read-only in Stratum: inspect the configured branch.*.remote, branch.*.merge, pull.rebase, and push.default values with git config --get-regexp where present. Do not pull, push, or change config.

## Component


## Verified Against



## External Code Boundary

Any Stratum paths above refer to the sibling `semestercontext/Stratum/` worktree. They are optional read-only learning anchors: LearningOS does not index, validate, manage, or write that codebase.
