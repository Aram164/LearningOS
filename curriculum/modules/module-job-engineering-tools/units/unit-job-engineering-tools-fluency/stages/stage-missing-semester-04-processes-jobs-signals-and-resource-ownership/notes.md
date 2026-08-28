# Stage Working Notes

## Mental Models

### Tool model

commands run as processes with identifiers, parents, process groups, environment, open file descriptors, and lifecycle state; the terminal and shell coordinate foreground jobs and deliver control signals. Signals request behavior and may be handled, ignored, or uncatchable depending on the signal.

### Working practice

observe before killing, send the least severe signal, understand parent/child ownership, and wait/reap background work.

### Job relevance

hanging tests, orphaned workers, ports in use, and interrupted benchmarks are process-model problems.

### Failure mode

using kill -9 first, confusing a job number with a PID, or closing a terminal and assuming remote work will survive.

## Read-only Anchor

Job application without repository mutation: observe process trees for your own shell and a harmless lab command using ps/pgrep; map parent, group, terminal, and open port ownership. Never signal unrelated or production processes.

## Component


## Verified Against



## External Code Boundary

Any Stratum paths above refer to the sibling `semestercontext/Stratum/` worktree. They are optional read-only learning anchors: LearningOS does not index, validate, manage, or write that codebase.
