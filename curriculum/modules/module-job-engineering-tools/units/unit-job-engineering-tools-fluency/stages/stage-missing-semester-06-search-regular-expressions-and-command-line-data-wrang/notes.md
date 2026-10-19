# Stage Working Notes

## Mental Models

### Tool model

search tools select files, lines, or syntax; regex describes text patterns; pipelines progressively filter, transform, aggregate, and format streams. Structured formats should be handled by structure-aware tools rather than brittle text splitting.

### Working practice

narrow early, preserve raw input, validate record counts at each step, and choose rg/find/sed/awk/sort/uniq/jq according to data shape.

### Job relevance

locating optimizer paths, extracting test failures, and comparing benchmark or plan output are daily data-wrangling tasks.

### Failure mode

parsing JSON with regex, relying on locale-dependent sort, or producing a plausible aggregate without validating dropped/malformed records.

## Read-only Anchor

Read-only in Stratum: use rg and file listing to answer a concrete architecture question such as where a logical op is declared, lowered, selected, executed, and tested. Export notes outside the Stratum checkout if needed.

## Component


## Verified Against



## External Code Boundary

Any Stratum paths above refer to the sibling `semestercontext/Stratum/` worktree. They are optional read-only learning anchors: LearningOS does not index, validate, manage, or write that codebase.
