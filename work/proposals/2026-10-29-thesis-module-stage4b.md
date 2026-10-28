# Stage 4B — executable thesis migration in disposable fixtures

The [Stage 4A specification](2026-10-28-thesis-module-stage4a.md) remains the migration contract. This increment implements its Core migration and compatibility contract, without applying the migration to this checkout's thesis records or retiring the Projects interface.

## Implementation decisions

1. `tools/migrations/projects_to_modules_v62.py` is a dry-run frontend. Its JSON output contains the complete proposed file bodies, original-byte backups, source/absence hashes, snapshot, separate artifact revisions, redirects and exhaustive field map. Apply requires that reviewed file and its SHA-256; the controller recomputes the draft under the shared operator lock and rejects any difference.
2. `tools/learning_os/app/project_migration.py` owns execution through `TransactionService`. It lives in the application controller layer because taking the lock and loading validation state would violate the ordinary handler plumbing contract. This refines the provisional `app/handlers/` location in 4A without adding a handler exception. Ordinary `commit_proposal` admission is unchanged.
3. The declared `migration.projects-to-modules-v62` authority enumerates the five canonical input destinations and each exact evidence destination. A destination outside those scopes fails in the transaction engine. The migration retires after data-contract v62; it is a one-shot bridge, not another standing operation.
4. The transaction writes the completion marker with the allocated transaction ID. Replay checks its committed receipt and evidence hashes, then returns that same transaction without rewriting evolved Module/workspace state. An uncertain receipt uses the existing journal and reconciliation; a failure before publication rolls the bounded write set back.
5. The existing alias mechanism admits direct canonical Module, Unit and workspace owners. Validation refuses missing targets, chains, self-aliases and shadowing of canonical owners or still-live Project nodes. Historical compatibility-only Module-to-Project aliases still load. Projection derives the actual target type.
6. The schema changes deliberately introduce stored-record v62 and manifest v16. The old manifest schema and older frozen formats stay unchanged. The paired UI mirrors v16 and regenerates its validator/types; its navigation and Projects screens are unchanged in this increment. The separate unmerged #64/UI #9 contract version still needs reconciliation before integration.
7. Migration before-inputs are frozen in `tests/fixtures/migrations/projects-to-modules-v62/`, independent of later canonical retirement. `tests/fixtures/formats/v62/` covers the readable transitional alias format alongside the established record families.

## Evidence

- The migration suite proves exhaustive preservation of 71 Project and 22 relationship scalar values, original workspace body, Unit/maps/notes/deliverables, present or absent resume state, supplied academic facts, unknown academic facts, thematic groups and historical receipt identities.
- Failure tests cover altered drafts, source/snapshot/revision/absence conflicts, unknown fields, forbidden authority destinations, symlink boundaries, future-generation refusal, rollback, uncertain publication, receipt/evidence corruption, idempotent replay and later workspace evolution.
- Ordinary `inspect` and `related` reads resolve old IDs to the same canonical owner as direct lookup. Manifest v15's Project-only alias definition demonstrably rejects the new alias shape; v16 and the generated UI validator admit the three new owner families.
- Focused migration/format/workflow/operational-owner acceptance: 103 passed, one audit-population test skipped outside its scenario run. Controller/plumbing/callback/ratchet/layer/document checks: 187 passed before the final frozen-input and corruption-test additions. Other owning write/private-name/prose/vocabulary checks passed in the earlier focused run.
- UI contract regeneration/mirror checks, typecheck, build and ManifestStore index tests passed. Core code reachability and system-map checks passed. Ruff and whitespace checks passed.
- Read-only dry run against the experimental checkout succeeded. Validation: zero errors; 964 baseline-managed warnings across the same 32 signatures, with no new/grown signature. The seven protected primary-checkout digests and frozen experimental thesis inputs remain unchanged.

Hosted verification on the exact resulting Core/UI commits is pending when this record is committed. It must pass before Stage 4C application/retirement is accepted. Full gates run in CI; no installation, merge or production-vault application is claimed.

## Next increment

Stage 4C aligns ordinary Module visibility in Core/UI, adds the workspace-context open action, retires Projects navigation/rendering/authoring, and tests old-ID/title navigation and access to every preserved research section. Only then apply the reviewed migration to the experimental thesis records and test the resulting product. The live learner checkout and installed plugin remain outside this experiment.
