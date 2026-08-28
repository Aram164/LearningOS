# Stage Working Notes

## Mental Models

### Tool model

a terminal is an interface to a shell process; the shell parses command text, locates executables through PATH, starts processes, and gives each process a current working directory. Paths name filesystem objects, permissions gate operations, and root authority changes the consequence of mistakes.

### Working practice

inspect location and targets before acting, quote paths, prefer explicit narrow paths, and read --help/man before copying commands.

### Job relevance

repository setup, test execution, and diagnosing ‘command not found’ all depend on this model.

### Safety rule

never run recursive or destructive commands against an unresolved variable, glob, home directory, or repository root.

### Failure mode

treating the prompt as magic and memorizing commands without understanding parsing or targets.

## Read-only Anchor

Read-only in Stratum: identify the repository root, current directory, absolute and relative paths for one optimizer file, file type, permissions, and the executable selected for python, pytest, and git. Do not chmod, install, or execute project mutations.

## Component


## Verified Against



## External Code Boundary

Any Stratum paths above refer to the sibling `semestercontext/Stratum/` worktree. They are optional read-only learning anchors: LearningOS does not index, validate, manage, or write that codebase.
