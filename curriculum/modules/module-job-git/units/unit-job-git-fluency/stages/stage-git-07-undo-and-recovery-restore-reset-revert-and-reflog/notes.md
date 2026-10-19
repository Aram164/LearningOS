# Stage Working Notes

## Mental Models

### Core model

undo may change a working file, the index, a branch ref, or history by adding an inverse commit; those are different operations. Reflog records local ref movements and can recover reachable-by-log-lost objects until expiration.

### Working practice

identify what is wrong, whether it was shared, which state must be preserved, and the smallest layer to change.

### Job relevance

safe recovery prevents a bad local command or shared regression from becoming a fresh clone and lost context.

### Safety rule

hard reset and clean are last-resort practice-only tools; shared history is normally undone with revert.

### Failure mode

reaching reflexively for reset --hard or copying a rescue recipe without modeling its target state.

## Read-only Anchor

Read-only in Stratum: inspect git reflog without acting on it. Build a decision table for hypothetical accidental edits, staging, private commits, public commits, and moved refs; never execute the recovery commands there.

## Component


## Verified Against



## External Code Boundary

Any Stratum paths above refer to the sibling `semestercontext/Stratum/` worktree. They are optional read-only learning anchors: LearningOS does not index, validate, manage, or write that codebase.
