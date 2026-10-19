# Stage Working Notes

## Mental Models

### Core model

ignore rules affect only untracked discovery; attributes control path-specific Git behavior; configuration is layered by system/global/local/worktree; hooks are local automation unless a project distributes and installs them.

### Working practice

track reproducible configuration, keep generated and secret material out before the first commit, normalize text deliberately, and make quality gates runnable outside hooks.

### Job relevance

clean diffs and deterministic setup keep backend changes reviewable across macOS, Linux, and CI.

### Safety rule

deleting a secret from the latest commit does not remove it from history or revoke it.

### Failure mode

adding .gitignore after tracking a file, committing machine-specific config, or relying on an undistributed hook.

## Read-only Anchor

Read-only in Stratum: inspect .gitignore, .gitattributes, relevant local config origins, and any hook tooling declared in project files. Never edit config or hooks; never print credential values.

## Component


## Verified Against



## External Code Boundary

Any Stratum paths above refer to the sibling `semestercontext/Stratum/` worktree. They are optional read-only learning anchors: LearningOS does not index, validate, manage, or write that codebase.
