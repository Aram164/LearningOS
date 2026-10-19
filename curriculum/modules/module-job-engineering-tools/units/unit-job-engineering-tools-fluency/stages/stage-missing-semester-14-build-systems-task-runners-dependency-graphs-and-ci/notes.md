# Stage Working Notes

## Mental Models

### Tool model

a build system evaluates a dependency graph from inputs to outputs, using timestamps or content hashes to skip valid work; task runners give stable human-facing names to commands; CI replays quality and build tasks in a clean remote environment.

### Working practice

declare dependencies accurately, make targets deterministic and idempotent, expose one local command per CI job, cache only with correct keys, and fail fast with useful artifacts.

### Job relevance

tests, generated code, native extensions, benchmarks, and releases must run in the correct order without tribal command sequences.

### Failure mode

phony targets masquerading as incremental builds, hidden environment inputs, duplicated local/CI logic, or caches that preserve stale output.

## Read-only Anchor

Read-only in Stratum: map project commands and CI workflows into a dependency graph—environment, format/lint/type/test/build/benchmark—and identify which tasks are authoritative. Do not trigger workflows or write build output.

## Component


## Verified Against



## External Code Boundary

Any Stratum paths above refer to the sibling `semestercontext/Stratum/` worktree. They are optional read-only learning anchors: LearningOS does not index, validate, manage, or write that codebase.
