# Stage Working Notes

## Mental Models

### Tool model

after shell expansion and quoting, a program receives an argument vector plus inherited environment and three conventional streams; pipelines connect stdout to stdin while stderr remains separate unless redirected. Exit status is machine-readable control flow, and pipe failure semantics require deliberate handling.

### Working practice

predict argv before execution, quote expansions, keep data and diagnostics on separate streams, and check the status of the operation that matters.

### Job relevance

test, benchmark, and data commands must be composable and must fail visibly in automation.

### Failure mode

parsing human-readable output accidentally, losing whitespace through unquoted expansion, or reporting success because only the last pipeline command succeeded.

## Read-only Anchor

Read-only in Stratum: inspect one documented test or benchmark command and write its exact argv, environment dependencies, stdout/stderr behavior, and success condition. If running read-only discovery, avoid redirection into the repository.

## Component


## Verified Against



## External Code Boundary

Any Stratum paths above refer to the sibling `semestercontext/Stratum/` worktree. They are optional read-only learning anchors: LearningOS does not index, validate, manage, or write that codebase.
