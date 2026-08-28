# Stage Working Notes

## Mental Models

### Core model

a three-way merge combines two tips relative to their merge base; a fast-forward only moves a ref, while a true merge creates a two-parent commit. Conflicts are index entries and working-tree markers requiring a semantic decision, not a text-cleanup ritual.

### Working practice

inspect ours, theirs, base, and tests; resolve the intended behavior; stage the resolution; continue or abort.

### Job relevance

concurrent backend and optimizer changes often overlap in contracts even when textual conflicts are small.

### Failure mode

choosing one whole side, deleting markers, and declaring success without testing the combined behavior.

## Read-only Anchor

Read-only in Stratum: find a historical merge commit if present and inspect both parents plus --cc output; otherwise draw a hypothetical merge around two recent neighboring commits. Never merge in the checkout.

## Component


## Verified Against



## External Code Boundary

Any Stratum paths above refer to the sibling `semestercontext/Stratum/` worktree. They are optional read-only learning anchors: LearningOS does not index, validate, manage, or write that codebase.
