# Stage Working Notes

## Mental Models

### Tool model

debugging is iterative hypothesis elimination using observations at the narrowest useful layer—structured logs, assertions, debugger state, system calls, network/file activity, or a minimized reproducer. A debugger controls execution; tracing observes interactions; logging records selected state over time.

### Working practice

reproduce first, preserve the failing input, change one variable, separate fact from inference, and add a regression test after the cause is known.

### Job relevance

backend differences and optimizer invariants demand evidence about where behavior first diverges.

### Failure mode

random edits, excessive print noise, changing several variables, or fixing the symptom without a stable reproduction.

## Read-only Anchor

Read-only in Stratum: choose an already understood test or historical failure and map observation points from API call to logical node to physical implementation; do not run mutating fixers or edit the checkout. Use a synthetic reproduction outside Stratum for debugger practice.

## Component


## Verified Against



## External Code Boundary

Any Stratum paths above refer to the sibling `semestercontext/Stratum/` worktree. They are optional read-only learning anchors: LearningOS does not index, validate, manage, or write that codebase.
