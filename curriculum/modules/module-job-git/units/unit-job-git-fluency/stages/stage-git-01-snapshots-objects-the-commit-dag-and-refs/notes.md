# Stage Working Notes

## Mental Models

### Core model

Git stores content-addressed blobs and trees; commits point to a root tree, parent commit(s), and metadata; history is a directed acyclic graph. Branches and tags are refs that name commits, while HEAD names the checked-out branch or a commit.

### Working practice

translate every command into object creation, ref movement, or tree materialization before using it.

### Job relevance

Stratum history becomes understandable as a graph of immutable snapshots rather than a mysterious list of diffs.

### Failure mode

memorizing porcelain commands without being able to predict which object or ref changes.

## Read-only Anchor

Read-only in Stratum: run or inspect the outputs of git rev-parse HEAD, git log --graph --decorate --oneline --all, git cat-file -p HEAD, and git ls-tree HEAD. Draw the current branch ref, HEAD, the latest three commits, and one tree/blob path. Do not change repository state.

## Component


## Verified Against



## External Code Boundary

Any Stratum paths above refer to the sibling `semestercontext/Stratum/` worktree. They are optional read-only learning anchors: LearningOS does not index, validate, manage, or write that codebase.
