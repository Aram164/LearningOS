# Stage Working Notes

## Mental Models

### Core model

cherry-pick copies a commit's patch and metadata intent onto a different parent; tags are stable names for objects, with annotated tags carrying their own metadata.

### Working practice

propagate only changes whose dependencies are understood, resolve context differences explicitly, and tag immutable release commits.

### Job relevance

isolated fixes may need backporting while experimental optimizer work must not cross release boundaries accidentally.

### Failure mode

treating cherry-pick as copying a hash unchanged or moving an existing release tag after publication.

## Read-only Anchor

Read-only in Stratum: inspect git tag --list and git show on one tag if tags exist; find one self-contained historical fix and list the dependencies that would make a backport safe or unsafe. Do not create tags or cherry-pick.

## Component


## Verified Against



## External Code Boundary

Any Stratum paths above refer to the sibling `semestercontext/Stratum/` worktree. They are optional read-only learning anchors: LearningOS does not index, validate, manage, or write that codebase.
