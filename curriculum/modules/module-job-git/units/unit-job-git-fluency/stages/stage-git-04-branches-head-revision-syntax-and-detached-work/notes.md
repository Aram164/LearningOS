# Stage Working Notes

## Mental Models

### Core model

a branch is a movable commit pointer; switching changes HEAD and materializes a target tree, while detached HEAD points directly to a commit. Revision expressions such as ~ and ^ navigate first-parent and parent-number relationships.

### Working practice

inspect the graph before switching and immediately create a branch when detached work must survive.

### Job relevance

feature isolation and accurate revision selection underpin safe ticket work and review.

### Failure mode

imagining branches as copied folders or losing detached commits by moving away without naming them.

## Read-only Anchor

Read-only in Stratum: inspect git branch --all --verbose, git symbolic-ref --short HEAD, and several rev-parse expressions. Sketch local and remote-tracking refs without switching branches.

## Component


## Verified Against



## External Code Boundary

Any Stratum paths above refer to the sibling `semestercontext/Stratum/` worktree. They are optional read-only learning anchors: LearningOS does not index, validate, manage, or write that codebase.
