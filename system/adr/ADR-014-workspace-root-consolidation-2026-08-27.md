# ADR-014 — Consolidate the semestercontext root

**Date:** 2026-08-27 · **Status:** accepted (Aram)

## Context

After the LearningOS v3 cutover and the ADR-013 Job-learning migration, the
`semestercontext/` root still exposed transitional directories, compatibility
files, audit work, and retired release helpers beside the two active roots.
This obscured the actual ownership boundary.

## Decision

`semestercontext/` has exactly two visible top-level directories:

```text
semestercontext/
├── LearningOS/
└── Stratum/
```

`LearningOS/` is the umbrella for all LearningOS system components. The Core,
UI, materials, and project repositories retain their existing independent Git
boundaries. The disposable root workbench becomes `LearningOS/workbench/`.
The frozen pre-v3 tree becomes `LearningOS/legacy/`, and the former Job source
retained after its completed governed migration becomes
`LearningOS/legacy/Job/`. The compatibility `Plans` symlink moves with the tree
and continues to resolve to `legacy/Plans`.

Historical root release scripts, their commit message, the retired root README,
and the empty root operations directory are shelved under
`LearningOS/archive/retired-semester-root/`. Strategy and audit documents move
to their corresponding `LearningOS/workbench/` areas. The local `.env` moves to
`LearningOS/.env` with its permissions preserved so the bounded review client
continues to resolve it.

`Stratum/` remains an independent sibling Git repository and keeps its existing
capitalization, remotes, branch, and worktree.

Hidden root support metadata (`.git`, `.gitignore`, `.idea`, `.obsidian`, and
OS metadata) is not part of the visible information architecture and remains
in place to preserve the retired wrapper repository and local application
state.

## Migration properties

- Directory relocations are same-filesystem atomic renames; contents are not
  rewritten.
- Existing dirty and untracked work is preserved; nothing is stashed, reset,
  cleaned, committed, or pushed.
- Historical provenance labels such as `Job/...` and `Plans/...` remain valid
  descriptions of source identity. Active filesystem defaults point to the new
  shelves.
- No canonical learning record, generated artifact, material URI, project
  checkout, or Stratum file is changed by this consolidation.

## Verification

The move is accepted when the visible root contains only `LearningOS` and
`Stratum`, the nested LearningOS repositories and independent Stratum
repository still resolve, `LearningOS/Plans` and the `CLAUDE.md` links resolve,
the former Job and legacy directory inodes are preserved, active path-default
tests pass, and the focused LearningOS checks introduce no new failures.
