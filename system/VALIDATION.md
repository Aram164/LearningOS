# Learning OS v3 — Validation Rules (Consolidated v3.1)

Structure is validated by `system/schema/*.schema.json` (canonical structural contracts). This file defines the **cross-file semantic rules** that JSON Schema cannot express. `tools/validate.py` enforces both. Severity: **E** = error (blocks acceptance), **W** = warning.

## Identity

- **E** IDs unique within each family (note, concept, source, workspace, module).
- **E** IDs match `^(note|concept|source|workspace|module)-[a-z0-9]+(?:-[a-z0-9]+)*$`.
- **E** An ID never changes when its file moves or is renamed.
- **W** Numeric suffix present without a collision counterpart (gratuitous suffix).

## References

- **E** Every note `concepts` entry resolves in the concept registry.
- **E** Every note `sources` entry resolves in the source registry.
- **E** Every relation `from`/`to` resolves; endpoints are distinct.
- **E** Every `supersedes` / `replaced_by` target resolves.
- **E** Workspace IDs cited in COORDINATION.md dependencies resolve to active workspaces.
- **E** Evidence refs use a valid URI scheme (`note://`, `source://`, `concept://`, `workspace://`, `material://`, `project://`, `github://`, or https URL).
- **W** `material://` or `project://` URI does not resolve on disk (reported, not fatal — media may be offline).

## Registries

- **E** No duplicate relation edges (same from/type/to).
- **E** Relation `type` is one of the eight supported types (no `related-to`).
- **W** Alias collision: one alias maps to multiple concepts.
- **W** Two source records share title+author or identical URL/identifier (duplicate candidates).
- **E** Concept records contain no body/explanation fields beyond short description.
- **E** Every `sources/collections/*.yaml` file validates against `collections.schema.json`; filename is kebab-case; every entry's `source` resolves to a registered source.
- **W** A source is listed more than once within the same collection.

## Ownership boundaries

- **E** No canonical file references anything under `generated/` as an input.
- **E** No file under `generated/` is tracked by Git.
- **E** COORDINATION.md contains no ISO date equal to any `modules.yaml` attempt date (exam-date duplication), and no `status:` restatements of workspace state.
- **W** A `role: crosswalk` note contains Markdown tables whose headers match evaluation vocabulary (strengths/weaknesses/level/best-for) — judgments belong in source records.
- **E** Module attempt dates are chronologically ordered per module; `grade` only on `passed` attempts or completed modules; `result: registered` only on the latest attempt.

## Operating contract

- **W** `CLAUDE.md` and `system/CLAUDE.md` differ before the `## 13.` heading (the copies are identical by construction except §13 — divergence is drift; code `CLAUDE-SYNC`).

## Files

- **E** A note's filename equals `<id>.md`; a mismatch between filename and frontmatter ID is an error.
- **E** Every `attachments` entry resolves to a file under `knowledge/attachments/<note-id>/`.
- **W** A folder under `knowledge/attachments/` has no owning note referencing it (orphaned attachments).
- **W** Binary files under `knowledge/` outside `attachments/` (books/slides belong in materials).
- **W** Items in `work/inbox/` older than 14 days (unrouted capture — the inbox should trend toward empty).

## Workspaces

- **E** Required body sections present (Objective, Current Scope, Open Questions, Next Action).
- **E** Archived workspaces are excluded from generated concept/source indexes.
- **W** More than 7 non-standing active workspaces.
- **W** Active non-standing workspace untouched (per Git) for 21+ days (neglect signal — surfaced in the coordination view).

## Links

- **E** Internal Markdown links (relative paths, `note://` etc.) resolve.
- Online-only (`--online` flag): **W** external URL unreachable. External link rot never blocks offline validation.

## Generated outputs

- **E** `generated/` contains only the defined deterministic outputs; agent-computed artifacts (plans, source menus, summaries, recommendations) live in workspaces, never in `generated/`.
- **E** Regeneration after deleting `generated/` reproduces byte-identical outputs except timestamp fields.
- **E** Every generated file carries a generated-file warning header.
- **E** Manifest covers every canonical record; index entries resolve; backlinks equal the inverse of canonical forward references.
