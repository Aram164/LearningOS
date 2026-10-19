# Stage Working Notes

## Mental Models

### Tool model

a process inherits an environment snapshot; PATH search, shell startup files, aliases/functions, and tool-specific dotfiles layer configuration at different times. Package managers install versioned artifacts and their transitive dependencies into scoped locations.

### Working practice

keep portable dotfiles versioned, make installation idempotent, prefer functions over complex aliases, document secrets as required variable names rather than values, and separate global tools from project dependencies.

### Job relevance

reproducible commands eliminate ‘works in my terminal’ discrepancies.

### Safety rule

never print or commit secret environment values, and test dotfile changes in an isolated shell before replacing live configuration.

### Failure mode

editing multiple startup files blindly, shadowing executables unexpectedly, or installing project packages globally.

## Read-only Anchor

Read-only in Stratum: inspect project-declared environment names, tool versions, pyproject/lock files, and documented setup without printing values or installing anything. Record which inputs are machine, user, project, or secret scope.

## Component


## Verified Against



## External Code Boundary

Any Stratum paths above refer to the sibling `semestercontext/Stratum/` worktree. They are optional read-only learning anchors: LearningOS does not index, validate, manage, or write that codebase.
