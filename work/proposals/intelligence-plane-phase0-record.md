# Intelligence Plane — Phase 0 record (approved, in progress)

Parent proposal: `intelligence-plane-plan.md`. This record registers the
Phase 0 intent decisions and what the phase lands. Coordination state itself
is unchanged — no exam, priority, or deferral fact moves.

## Decided paths

| Need | Decision | Why |
|---|---|---|
| Semantic-contract doc | `system/SEMANTIC-CONTRACT.md` (binding reference) + evaluator `tools/learning_os/semantics/` | Proposal §Key Decisions 1; indexed in `normative-corpus.yaml` so the corpus cannot grow silently |
| VOQ fixtures | `tests/fixtures/verified_operator_questions/` (15 examples / 5 held-out split) | Fixtures, not runtime (proposal §2); a `README.md` holds the path until Phase 1 adds triples |
| Proposal queue | `work/proposals/` (this directory) | Default from the plan's Open Questions; no workspace-convention conflict found (`work/active/` holds workspaces, `work/proposals/` holds proposals) |
| Telemetry log | `operations/` from Phase 4 (no path created now) | Beside `transactions/` and `ai-actions/`; append-only rows land with the Task IR, not before |
| Dossier cache keys | content-addressed `context://<unit\|route>/semantic-dossier` under the rebuilt views (Phase 5) | Rebuilt views are never hand-edited; the validator ensures no hand-edit path |

## What Phase 0 lands

- This record (intent registration).
- `system/SEMANTIC-CONTRACT.md` stub + corpus entry (one predicate documented).
- `tools/learning_os/semantics/` — `CONTRACT_VERSION = 1`, `NeedsStudyMap`
  predicate, `PREDICATES` registry, `evaluate()` entry point.
- Producer delegation: `records_curriculum._needs_study_map` calls the
  evaluator (same signature, same truth table; `tests/test_study_map_obligation.py`
  untouched and green).
- `tests/test_semantic_contract.py` — contract version, registry shape,
  evaluator truth table, producer/evaluator agreement sweep.
- VOQ fixture path held by a `README.md`; no triples until Phase 1.

## Explicit non-changes

- No new JSON schema: no new canonical shape and no new gateway payload
  exists yet (proposal/Task-IR/telemetry schemas arrive with Phases 3–4).
- No canonical migration, no gateway change, no hand-edit of rebuilt views.
- No critique-point action taken.

## Phase 0 exit (all green before Phase 1)

`make lint` (incl. code reachability: `records_curriculum` → `semantics`
edge keeps the new package classified), `make test-fast` (1049 passed),
full `make test` phase files, and `tests/test_study_map_obligation.py`
incl. its `full_repo` agreement test — all green (2026-09-07 session).

`make check` zero-errors is **blocked by pre-existing issues outside this
phase's scope**, none referencing Phase 0 files: two `PERIMETER-UNDECLARED`
errors for umbrella-root files outside the workspace (`.museignore`,
`muse_architecture_prompt.md`), and one `GEN-INPUT` for this proposal's
parent (`intelligence-plane-plan.md` mentions the rebuilt views — approved
wording, not rewritten to dodge the rule). Four full-repo tests assert a
zero-error repository and fail on exactly those three. The warning-baseline
gate cannot be evaluated until errors clear. `work/proposals/` was declared
in `tree-contract.yaml` and the ARCHITECTURE block regenerated through the
sanctioned projector, so Phase 0 itself adds no new error or warning.
