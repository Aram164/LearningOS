# Stage Working Notes

## Mental Models

### Tool model

efficient editing is navigation and transformation over structured text; Vim composes operators, motions, counts, and text objects, while a language server supplies semantic facts independently of the editor UI. Formatters, linters, type checkers, debuggers, tests, and version control are separate tools integrated by the IDE.

### Working practice

master one editor, remain functional in a terminal editor, configure the correct project environment, and distinguish syntax coloring from semantic analysis.

### Job relevance

fast definition/reference navigation across Stratum's IR, lowering, physical selection, and tests reduces cognitive load.

### Failure mode

installing extensions until features conflict or blaming the editor when the language server points at the wrong environment.

## Read-only Anchor

Read-only in Stratum: use jump-to-definition, find references, symbol search, call hierarchy, test discovery, and Git blame to trace one operation end to end. Confirm the selected Python environment without changing project configuration.

## Component


## Verified Against



## External Code Boundary

Any Stratum paths above refer to the sibling `semestercontext/Stratum/` worktree. They are optional read-only learning anchors: LearningOS does not index, validate, manage, or write that codebase.
