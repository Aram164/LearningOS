# Stage Working Notes

## Mental Models

### Tool model

shell is a programming language optimized for starting programs and wiring streams; functions, variables, conditionals, loops, traps, and exit codes carry shell-specific parsing rules. A humane CLI presents stable arguments, useful help, actionable errors, quiet machine-readable output, and predictable status codes.

### Working practice

keep shell automation small, quote variables, validate inputs, use shellcheck, clean temporary files with traps, and move complex data logic to Python.

### Job relevance

repeatable setup, lint, test, benchmark, and release commands remove manual omissions.

### Safety rule

strict modes help but do not replace understanding of expected failures and cleanup.

### Failure mode

growing an untested 200-line shell script or assuming set -e makes all failures safe and obvious.

## Read-only Anchor

Read-only in Stratum: locate existing command runners, CI commands, or shell scripts and assess quoting, error propagation, cleanup, and idempotence. Do not execute setup/release scripts or edit them.

## Component


## Verified Against



## External Code Boundary

Any Stratum paths above refer to the sibling `semestercontext/Stratum/` worktree. They are optional read-only learning anchors: LearningOS does not index, validate, manage, or write that codebase.
