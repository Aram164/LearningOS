# Stage Working Notes

## Mental Models

### Core model

git worktree lets multiple working trees share one object database and most refs while each has its own HEAD and index; a branch normally cannot be checked out twice. Submodules and shallow/partial clones solve different repository-distribution problems and add coordination costs.

### Working practice

use named worktrees for genuinely parallel tasks, prune deliberately, and adopt submodules only when ownership and update policy are explicit.

### Job relevance

parallel review fixes and ticket work can stay isolated without repeated stashing or duplicate full clones.

### Failure mode

deleting worktree directories manually, confusing worktree state, or choosing submodules as a casual folder-linking mechanism.

## Read-only Anchor

Read-only in Stratum: inspect git worktree list and repository common-dir metadata only. Do not add, move, lock, prune, or remove worktrees, and do not initialize or update submodules.

## Component


## Verified Against



## External Code Boundary

Any Stratum paths above refer to the sibling `semestercontext/Stratum/` worktree. They are optional read-only learning anchors: LearningOS does not index, validate, manage, or write that codebase.
