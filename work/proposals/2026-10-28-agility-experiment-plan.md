# LearningOS agility experiment — execution plan

Date: 2026-10-28. Authority: Aram requested a plan followed by implementation on a new experimental branch, selected the broader roadmap in stages, and decided to replace the separate Projects section with ordinary Modules. This authorizes experimental implementation; it does not authorize a production merge, installation, paid-model campaign, or mutation of the existing working vault.

## 1. Understanding

LearningOS should require proportionate effort for ordinary learning-plan changes while preserving its existing review, concurrency, receipt, recovery, and learner-state guarantees. The bachelor thesis will become an ordinary visible Module and the separate Projects product surface will be retired, with its meaningful information and historical references preserved. Execute the broader improvement roadmap in independently checkable stages on isolated experimental Core/UI branches, beginning with the documented contract defect and a small reproducible baseline.

## 2. Verified starting state and decisions

- The primary Core checkout is on `review/f1-f2-prompt-recipe-2026-10-28` at `f6c4232`, with unrelated ICOP, transaction-ledger, material-manifest and hook changes. Do not stash, reset, incorporate, or edit those changes.
- Core `origin/main` is locally pinned at `d3d3b3510349f84cee2d7aca1b8601330409539d`; paired UI `origin/main` is locally pinned at `5a6bbeebc0b8a4dbfa1977bb8d4c223541023348`. These are inspected refs, not evidence of the installed vault or remote freshness.
- **Decision:** create `codex/agility-experiment-20261028` in isolated sibling `repository/` and `obsidian-ui/` worktrees under this workbench directory. Reason: preserve the dirty working vault and the relative paths used by paired checks.
- **Decision:** Core starts at `17ce3dba1fd05607e3c68634a20acc079124ecf4`, the head of open PR #61, which is two commits above the inspected main and contains the required effect-classification/uncertain-write repair. UI starts at the inspected `5a6bbee` baseline. Reason: exercise new work with the necessary runner repair without importing the much larger PR #64 campaign or Task IR. This is an experimental dependency, not approval or a merge of #61.
- **Decision:** carry the existing F1/F2 recipe commit `f6c4232dcd1cd865b84d3a162094abb79e6910f6` onto the experiment. Reason: reuse the already-written narrow task-entry/review-display improvement without another instruction mechanism.
- The SOP currently mandates contract v2 globally; single-unit revisions enforce v1. **Decision:** document the two package versions at their owning paths and make refusal messages identify the correct path. Do not change validation versions to disguise the contradiction.
- Compact module revisions already support `resources_append`, full stage-resource replacement, and deterministic carry-forward of unchanged records. **Decision:** benchmark and extend this machinery rather than introduce another mutation language.
- The thesis Module already exists with two milestone Units, but is `compatibility_only`; its Project is active. **Decision:** reactivate the existing Module ID under `program-bachelors`, preserving Unit IDs, maps and study state; retire the old Project identity through a backward redirect.
- **Decision:** use existing `related_module_ids` for linked modules and the associated workspace for research workstreams, decisions, files, Topic Pack relationships and access-boundary text. Preserve original field values and stable sub-identities in the migration evidence. Do not add Project-shaped fields to Module just to reproduce the retired domain.
- **Decision:** compatibility readers may remain temporarily for frozen historical formats and old links, but the target product has no Projects navigation or active Project writer. Record the compatibility boundary explicitly rather than maintaining two active owners.
- **Decision:** run focused checks locally and the full gate in hosted CI against exact Core/UI commits. Reason: Aram's full-gate preference and a paired consumer contract.
- **ASSUMPTION:** three representative scenarios will reveal enough friction to select the first editing increment; if they do not, expand the baseline with an explicitly recorded reason.

## 3. Files affected

Paths below are relative to the experiment's Core `repository/` unless prefixed `obsidian-ui/`; new files are labelled.

- `system/PLAN-CREATION-SOP.md`: make package-version requirements specific to full/compact-module imports, single-unit revisions, standalone maps and route patches.
- `tools/learning_os/domain/plan_import.py`: own the existing compact package behavior and its contract diagnostics; extend only for selected structural operations.
- `tools/learning_os/app/handlers/plan.py`: repair the actual single-unit contract-version diagnostic; its owner was verified during initial implementation.
- `tools/learning_os/app/_plan_gate.py`: preserve semantic acknowledgments, synthesis reuse, exact review and learner-state checks when assembling changes.
- `tests/test_unit_plan_revision.py`, `tests/test_compact_module_plan_revision.py`: exercise correct and wrong contract versions and the selected editing behavior.
- `work/proposals/2026-10-28-agility-experiment-plan.md` (new): retain this plan on the branch, with stage outcomes and deviations by reference.
- `workbench/agility-experiment/baseline.py` and `workbench/agility-experiment/README.md` (new): a disposable-fixture benchmark driver and its measured scope; no new production abstraction.
- `tools/migrations/projects_to_modules_v62.py` (new): a dry-run-first, current-generation-bounded migration with before-images, exact review and shared transaction/receipt handling.
- `curriculum/modules/module-project-bachelor-thesis/module.yaml`: restore the ordinary Module and its Bachelor's ownership while retaining related-module joins.
- `work/active/workspace-thesis-mle-medical/CONTEXT.md` and a new `outputs/thesis-operational-context.md`: correct workspace joins and preserve the Project's operational content without rewriting existing prose.
- `projects/registry/project-bachelor-thesis.yaml`, `projects/relations/project-relations.yaml`, `projects/aliases.yaml`: retire active Project ownership and reverse compatibility resolution after the migration succeeds; preserve original bytes in migration evidence.
- `system/schema/project-aliases.schema.json`, `tools/learning_os/derive/validation/projects.py`, `tools/learning_os/derive/projection/projection/records_projects.py`: support the bounded old-Project-to-Module redirect without alias cycles or shadowing active IDs.
- `system/contracts/data-contract.yaml`, `tests/test_format_fixtures.py` and a new frozen format fixture: record any stored-format evolution and prove historical formats remain readable; never edit frozen fixtures.
- `tests/test_projects.py`, `tests/test_migration_lifecycle.py`: replace current-vault expectations with Module/alias preservation and migration lifecycle/refusal checks while retaining historical coverage.
- `tools/README.md`, `tools/code_reachability.py`, `tests/group_map.py`, `.github/shard-manifest.json`: register new executable/test ownership if new files are necessary.
- `obsidian-ui/src/app/navigator.ts`, `src/app/router.ts`, `src/constants.ts`, `src/main.ts`: remove Projects entry routes and resolve legacy destinations to the ordinary Module surface.
- `obsidian-ui/src/manifest-store.ts`: replace the academic-only Modules filter with the ordinary learning-Module selection needed by the agreed product; verified `openAcademicModules()` currently excludes `kind: project`, so reactivating the thesis record alone would leave it hidden.
- `obsidian-ui/src/views/project-view.ts`, `src/features/project/`, project style files and their view registrations: retire the separate renderer once its useful content is reachable through Module/workspace navigation.
- `obsidian-ui/src/features/module/`, `src/features/unit/`, `src/gateway-client.ts`: expose the selected structural edit and its exact Core review through ordinary learner controls.
- `obsidian-ui/tests/dashboard/study-surfaces.js` and owning navigation/runtime tests: prove Module visibility, compatibility redirects, editing review, stale refusal and preserved study state.
- `system/ARCHITECTURE.md`, relevant capability/request contracts and UI `README.md`: describe the resulting ownership and supported operations; regenerate derived contract artifacts only with their owning tools.
- `system/contracts/manifest-contract.yaml` and paired UI contract mirrors: change only if a published shape changes; preserve exact paired versioning.

**ASSUMPTION:** final renderer retirement can reveal additional imports or pinned fixtures beyond the named owners. Record any extra path and its reason before editing it; do not use this as permission for unrelated cleanup.

## 4. Execution stages

1. **Isolate and secure the experiment.** Create the two branches/worktrees at the pinned revisions, carry F1/F2, retain this plan, and record the exact pair. Confirm the primary dirty checkout is unchanged. Deliverable: cleanly bounded branch ancestry and preserved original state.
2. **Resolve the contract contradiction (#58).** Make each package version explicit, link the single-unit refusal to its exact procedure, and verify passing examples plus wrong-version refusal without canonical writes. Deliverable: a focused, reviewable fix; no changes to the accepted versions.
3. **Measure the first three ordinary changes.** Use disposable fixtures to append one existing resource, move one existing stage, and extend one module with a Unit. Exercise the shortest supported preflight/apply paths, record authored bytes, repeated unchanged content, affected files, validation count/time and receipts, and prove the intended effect and preserved state. Separate scripted mechanical measurements from unavailable live-agent/user measurements. Deliverable: baseline JSON/report and a justified choice of the first editing increment.
4. **Consolidate Projects into Modules.** Inventory all active Project references and map every field/sub-ID to its target; implement and test dry-run, stale-review refusal, atomic apply, idempotent rerun and rollback evidence; apply only in the experimental tree. Make the thesis visible under Bachelor's Modules, remove Projects navigation/rendering, keep old links resolvable, and retire active Project authoring. Deliverable: one active Module owner and preserved meaningful content, with no live-vault change.
5. **Deliver proportional structural editing through Core and UI.** Select the smallest two operations from measured need (initial candidates: stage move and resource insertion/move); use stable IDs and relative placement, derive unchanged state under existing guards, preserve IDs/progress and review the exact result. Add the Obsidian controls in the same increment. Add Unit extension/order only after these pass. Deliverable: representative learner operations completed without replacement YAML or manual guards.
6. **Define temporary-session adjustment precisely.** Specify lifetime, allowed reordering/omission, prerequisite constraints and expiry against a snapshot before writing an override. Keep the durable plan unchanged. **ASSUMPTION:** an in-memory/snapshot-bound override suffices; if required behavior exceeds it, retain a concrete unresolved product question rather than invent a persistent Session entity.
7. **Optimize only measured remaining costs.** Profile current validation cold/warm paths and inspect the existing evidence-reuse boundary; remove demonstrated repeated work with equivalence checks. Extend benchmark scenarios only where the prior stages or real operation logs justify them. Do not infer actual token/cost savings from scripted call counts.
8. **Verify and present the experiment.** Run owning local checks, zero-error validation and unchanged-warning checks, publish experimental commits/paired draft PRs when ready, run the complete exact-pair CI gate and inspect its result. Leave merge, installation and production migration for Aram's review of the concrete result. Report each completed stage and every uncompleted stage explicitly.

Each stage gets a distinct commit or small commit set and an outcome note. Do not represent starting this campaign as completion of all eight stages.

## 5. Risks and verification

- **Lost learner state or changed identity:** compare Unit/map/stage/resource IDs, notes, attachments, feedback, resume pointer and progress before/after migration and edits; only intended order/numbering/ownership may change.
- **Lost Project content:** retain original bytes and an exhaustive field/sub-ID mapping; verify every decision, workstream node, file reference, relationship reason/contribution and boundary value at its destination.
- **Alias loops or duplicate ownership:** test old Project ID → active Module, ordinary Module ID → itself, missing targets, self/cyclic aliases and active-ID shadowing; active projections/counts must contain one thesis owner.
- **Stale approved work:** mutate the guarded fixture after preflight and prove refusal without any partial mutation or replacement approval.
- **Partial writes/recovery:** failure injection must preserve existing transaction uncertainty and receipt guarantees; no private writer, approval system or journal.
- **Legacy-format breakage:** run `tests/test_format_fixtures.py` and migration lifecycle tests against current schemas; preserve frozen input bytes.
- **UI contract mismatch:** run `npm run check` against the sibling experimental Core and pair changed manifests using the existing contract tools.
- **Unrelated content damage:** compare the original checkout's status and relevant file digests against the starting record; no migration follows external working-code paths.

Focused commands for the initial increment:

```sh
.venv/bin/python -m pytest -q tests/test_unit_plan_revision.py tests/test_compact_module_plan_revision.py tests/test_agent_run.py
.venv/bin/python tools/validate.py --compact
.venv/bin/python tools/warning_baseline.py --check
.venv/bin/python tools/system_map.py --check
git diff --check
```

Subsequent owning checks include `tests/test_projects.py`, `tests/test_migration_lifecycle.py`, `tests/test_format_fixtures.py`, architecture ownership/reachability gates, the benchmark's preservation oracle, and UI `npm run check`. The complete gate runs in CI for the recorded exact Core/UI pair; local focused results are not a full acceptance claim.

## 6. Out of scope

Production merge, installation, rewriting the running vault, changes to unrelated ICOP work, edits to `LearningOS/legacy/`, traversing external code repositories, deleting working-code directories, Task IR/P3/P4 revival, a generic mutation/query language, a new transaction/review system, inferred academic facts or source judgments, mastery claims, paid-model trials, and speculative validation replacement.

PR #64 / UI PR #9 remain a separate unmerged campaign. This experiment must eventually reconcile with their accepted outcome, but importing or merging them is not an initial-stage prerequisite.

## Execution record — initial increment

- Stages 1–2 implemented on the isolated branches. Core starts at the exact PR #61 head; F1/F2 is carried as `498dce5`. The documentation now distinguishes package versions and both refusal messages name the owning mutation path. Four regression cases cover both accepted versions and both crossed-version refusals, with an unchanged canonical fingerprint throughout preflight. Four affected characterization recordings were regenerated through their harness; the fifth selected refusal remained unchanged.
- Stage 3's three scenarios completed, with the stage-move case expanded to 2/10/50 stages to measure proportionality. Five runs passed preservation, zero-write preflight and one-receipt checks. See [the baseline report](../../workbench/agility-experiment/README.md) and its raw JSON; no live-agent or user-cost claims are made.
- Initial checks: 186 owning revision/runner tests, 57 document/layer tests, and five selected refusal scenarios passed. Ruff, system-map consistency and diff whitespace checks passed. Repository validation has zero errors and no new warning signature. Hosted full-pair verification remains a separate pending check until its exact run completes.
- No Project migration or UI change has been applied in this initial increment. Stage 4 is next; the verified academic-only UI filter is included in its affected paths before implementation.
