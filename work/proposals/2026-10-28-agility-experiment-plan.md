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
- The thesis Module already exists with two milestone Units, but is `compatibility_only`; its Project is active. **Decision:** retain the existing Module ID under `program-bachelors`, preserving Unit IDs, maps and study state, with an old-Project-to-Module redirect. Stage 4A must explicitly settle Module kind and academic-fact handling before reactivation: membership in the Bachelor's area alone does not establish enrollment or degree credit. Reason: `module_lifecycle` derives enrollment from an active academic Module, while the current thesis records state that registration facts are not yet known.
- **Decision:** use existing `related_module_ids` for linked modules and the associated workspace for operational research content, retaining stable sub-identities and exact values. This is a proposed ownership mapping to validate in 4A; settled coordination decisions remain with their existing owner in `work/COORDINATION.md`. Every workstream, open question, relationship reason/contribution, file and access boundary must remain reachable through ordinary Module/workspace navigation and search in 4C. Historical backups alone do not satisfy preservation. Do not add Project-shaped fields to Module just to reproduce the retired domain.
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
- `workbench/agility-experiment/baseline-clean-d32d2cf8.json` and `baseline-clean-d32d2cf8-provenance.json` (new): retain a clean-commit reproduction of the first increment without overwriting its original measured evidence.
- `work/proposals/2026-10-28-agility-first-increment-review-response.md` (new): record accepted review changes and the independently checked CI correction, with source pointers.
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
- `tools/learning_os/derive/semesters.py` and its owning listing tests: keep the Core-owned listing explanation aligned with any UI selection change; the current `is_listed` rule also selects only academic Modules. This does not authorize changing academic credit or enrollment semantics for visibility.
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
4. **Consolidate Projects into Modules through three separately accepted increments.** The product decision is settled; each acceptance boundary below prevents proceeding on an unverified preservation or academic-identity assumption.

   **4A — Inventory and dry-run specification.** Inventory every Project field, nested node, decision, relationship, file, workspace join, alias, generated identity and historical reference; name its single destination and the normal operation that retrieves it. Specify exact before/after expectations, affected paths and the reverse alias direction. Settle Module kind and academic semantics from evidence: preserve Bachelor's affiliation, existing examination/credit facts if any, and explicit unknowns; do not infer institution, semester, registration, credits, grade or degree completion. Check schema, lifecycle, listings, Module logistics and any actual degree-accounting consumers before selecting metadata. **Acceptance:** exhaustive ownership/ID map, explicit academic decision and preservation oracle, and a no-write dry-run specification; no canonical Project removal or reactivation. Any consumer not inspected is marked ASSUMPTION and blocks the corresponding acceptance claim.

   **4B — Core migration in disposable fixtures.** Implement the bounded migration with original-byte retention and shared transaction/receipt handling. Prove atomic application, unchanged Unit/map/stage IDs and learner state, idempotent rerun, stale-state refusal, recovery/rollback evidence and compatibility of Project IDs, nested IDs, workspace joins and historical receipts. Exercise fixtures with known academic facts and with absent facts: known values must survive exactly; absent credits remain unknown rather than zero, and research progress must not become awarded credit. **Acceptance:** all 4A expectations and refusal/preservation checks pass in fixtures; no live-vault application or interface retirement.

   **4C — UI consolidation and domain retirement.** Make the thesis visible through ordinary Bachelor's Modules and expose the migrated operational content through Module/workspace navigation and search. Test old Project links, nested destinations, workspace navigation, generated IDs and historical evidence. Module visibility tests must cover intended ordinary Modules, closed Modules, compatibility-only records, and quarantined/boundary records, so removing the academic-only filter does not expose unrelated records. Remove Projects navigation/rendering and active writers only after these access and compatibility tests pass, then apply the reviewed migration only to the experimental tree. **Acceptance:** one active thesis owner, ordinary access to every preserved useful field, tested historical resolution, preserved academic semantics and no separate Projects product surface; no production installation.
5. **Deliver proportional structural editing through Core and UI.** Select the smallest two operations from measured need (initial candidates: stage move and resource insertion/move); use stable IDs and relative placement, derive unchanged state under existing guards, preserve IDs/progress and review the exact result. Add the Obsidian controls in the same increment. Add Unit extension/order only after these pass. Deliverable: representative learner operations completed without replacement YAML or manual guards.
6. **Define temporary-session adjustment precisely.** Specify lifetime, allowed reordering/omission, prerequisite constraints and expiry against a snapshot before writing an override. Keep the durable plan unchanged. **ASSUMPTION:** an in-memory/snapshot-bound override suffices; if required behavior exceeds it, retain a concrete unresolved product question rather than invent a persistent Session entity.
7. **Optimize only measured remaining costs.** Profile current validation cold/warm paths and inspect the existing evidence-reuse boundary; remove demonstrated repeated work with equivalence checks. Extend benchmark scenarios only where the prior stages or real operation logs justify them. Do not infer actual token/cost savings from scripted call counts.
8. **Verify and present the experiment.** Run owning local checks, zero-error validation and unchanged-warning checks, publish experimental commits/paired draft PRs when ready, run the complete exact-pair CI gate and inspect its result. Leave merge, installation and production migration for Aram's review of the concrete result. Report each completed stage and every uncompleted stage explicitly.

Each stage gets a distinct commit or small commit set and an outcome note. Do not represent starting this campaign as completion of all eight stages.

## 5. Risks and verification

- **Lost learner state or changed identity:** compare Unit/map/stage/resource IDs, notes, attachments, feedback, resume pointer and progress before/after migration and edits; only intended order/numbering/ownership may change.
- **Lost Project content:** retain original bytes and an exhaustive field/sub-ID mapping; verify every decision, workstream node, file reference, relationship reason/contribution and boundary value at its operational destination. A backup or migration report is historical evidence, not proof that the information remains usable.
- **Changed academic meaning:** area membership must not silently infer enrollment or awarded credits. Stage 4A must choose kind/metadata using the owning schema and consumers; 4B/4C must preserve known academic facts exactly, keep absent facts unknown and distinguish research progress from degree completion.
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

For a manual exact-pair workflow, record the workflow-definition ref separately from the tested checkout commits. Its API `head_sha` is not sufficient to identify those checkouts: verify the dispatch inputs, checkout/log evidence and clean-commit assertions, then the completed gate and independently verified pair receipt. A push run's exact `head_sha` is useful additional evidence but does not replace the paired UI identity or receipt. Pending runs establish no completed hosted acceptance.

## 6. Out of scope

Production merge, installation, rewriting the running vault, changes to unrelated ICOP work, edits to `LearningOS/legacy/`, traversing external code repositories, deleting working-code directories, Task IR/P3/P4 revival, a generic mutation/query language, a new transaction/review system, inferred academic facts or source judgments, mastery claims, paid-model trials, and speculative validation replacement.

PR #64 / UI PR #9 remain a separate unmerged campaign. This experiment must eventually reconcile with their accepted outcome, but importing or merging them is not an initial-stage prerequisite.

## Execution record — initial increment

- Stages 1–2 implemented on the isolated branches. Core starts at the exact PR #61 head; F1/F2 is carried as `498dce5`. The documentation now distinguishes package versions and both refusal messages name the owning mutation path. Four regression cases cover both accepted versions and both crossed-version refusals, with an unchanged canonical fingerprint throughout preflight. Four affected characterization recordings were regenerated through their harness; the fifth selected refusal remained unchanged.
- Stage 3's three scenarios completed, with the stage-move case expanded to 2/10/50 stages to measure proportionality. Five runs passed preservation, zero-write preflight and one-receipt checks. See [the baseline report](../../workbench/agility-experiment/README.md) and its raw JSON; no live-agent or user-cost claims are made.
- Initial checks: 186 owning revision/runner tests, 57 document/layer tests, and five selected refusal scenarios passed. Ruff, system-map consistency and diff whitespace checks passed. Repository validation has zero errors and no new warning signature. Hosted full-pair verification remains a separate pending check until its exact run completes.
- No Project migration or UI change has been applied in this initial increment. Stage 4 is next; the verified academic-only UI filter is included in its affected paths before implementation.

## First-increment review incorporated

The migration is now split into 4A/4B/4C, with academic identity and normal operational access as explicit acceptance gates. The baseline was rerun from clean commit `d32d2cf8c25d3115740939962cbd1e0c7b3e152b` before these review edits; all five structural results and draft hashes match the original run, and the measured source hashes were verified. See the [review response](2026-10-28-agility-first-increment-review-response.md) for the CI finding's correction and retained reproduction evidence. No canonical thesis record or UI implementation is changed by this review incorporation; 4A is the next implementation increment.

## CI completion and Stage 4A

The one-shot Bash watcher waited for branch run `40779280991` (Core `873a77613dc237cd638b25d345f9f01ffcd44748`) and exact-pair run `40777259003` (Core `d32d2cf8c25d3115740939962cbd1e0c7b3e152b` / UI `5a6bbeebc0b8a4dbfa1977bb8d4c223541023348`). Both completed successfully. The pair artifact's ZIP digest matched GitHub's artifact digest, and the published receipt independently verified against its downloaded assets; this is CI evidence, not an installation claim.

Stage 4A's [specification and decisions](2026-10-28-thesis-module-stage4a.md) and [read-only inventory](../../workbench/agility-experiment/stage4a-inventory.json) are now retained. The inventory maps 71 Project scalar values and 22 relationship scalar values, checks referenced files and separately guards absent resume state. Current Module kind is deliberately preserved during consolidation to avoid inferred enrollment. The workspace becomes the active operational owner; the earlier proposal for an extra operational-context output file is withdrawn. The missing Open workspace context action is included in 4C's concrete files and access tests. The corresponding Core/UI inspection, alias validation and stored-format changes remain 4B/4C work; no canonical Project removal is performed by 4A.

The 4B architecture inspection also confirmed two required boundaries: current write scopes cannot authorize the migration implicitly, and manifest v15 restricts alias target IDs/types to Projects. The 4A specification now records the one-shot scoped authority/application-controller requirement and the necessary paired manifest bump before fixture migration can be accepted. This is a design requirement for 4B, not permission to disable admission or edit historical schemas.

## Stage 4B implementation

The bounded migration, direct owner aliases, frozen inputs and failure/preservation tests are implemented; see the [Stage 4B execution record](2026-10-29-thesis-module-stage4b.md). Stored-record v62 and paired manifest v16 are deliberate contract changes. The migration controller lives in `app/project_migration.py` so its lock and validation orchestration respect the ordinary handler plumbing boundary. Canonical thesis inputs and the original learner checkout remain unchanged. Hosted verification of this increment is the next gate before Stage 4C.

## Stage 4C verification and completion

The received Stage 4C implementation was reviewed and repaired against the 4A contract. The experimental thesis migration is receipt-bound, the Module is visible under Bachelor's, ordinary workspace access is tested, the separate Project renderer/navigation and active writers are retired, and direct aliases preserve historical IDs. The [4C review record](2026-10-29-thesis-module-stage4c.md) records the defects found, preservation evidence and owning checks, including repair of historical engine fixture isolation without rebasing its accepted oracle. The original learner checkout remains unchanged. Final hosted exact-pair acceptance and downloaded artifact verification gate continuation into Stages 5–8 in the user-requested new session; those results belong to the external continuation handoff so a documentation-only evidence commit does not supersede the verified implementation pair.

## Stage 5 implementation decisions (2026-10-29 continuation)

Stage 4C acceptance is retained in the external `STAGE4C-ACCEPTANCE.json`; it is the starting pair, not work to repeat. Both experimental worktrees are clean at that pair.

1. **Decision:** accept a narrow `structural_edit` file through the existing `unit.map.import` capability, with `unit_id`, one `stage_move`, `resource_move`, or `resource_insert`, a nonblank reason and exactly one `before_id`/`after_id`. Reason: the owning `handlers/maps.py` already owns exact UI review, stable map identity, learner-state carry-forward and guarded transactions; `module.plan.import` is deliberately unavailable to UI gestures. No new write capability or approval protocol is needed.
2. **Decision:** expand against `authored_data`, never reconstruct existing records in the caller. Keep stage/resource IDs, map/current-stage state and resource fields verbatim; renumber stages only for stage movement. Resource movement stays within its stage. Refuse ambiguous/missing IDs, self placement, collisions, empty/no-op edits and extra fields. Reason: this bounds authority and preserves shared material references and resource-owned evidence.
3. **Decision:** run the existing staged proposal checker for structural preflight and retain the original snapshot/revision/file digest in the review. UI creates only a temporary intent file, displays Core's exact diff, and applies through the existing recovery-aware gateway. Editing any control invalidates the displayed review. Reason: preflight must prove the resulting record and apply must never refresh an approval silently.
4. **Decision:** implement and verify these operations first; then add compact module Unit additions with only new Unit/map/route records and relative Unit movement. The existing module import keeps its operator review and plan-contract/audit requirements. Keep these Unit-level academic-scope changes on the existing operator-reviewed file path; the Obsidian controls in this milestone cover stage/resource adjustments. Do not relabel a UI gesture as operator approval or widen module-import gesture admission. Reason: Unit extension includes authored academic scope, unlike choosing an existing stage position.

Concrete affected files: `tools/learning_os/domain/plan_import.py` (pure stable-ID editing); `tools/learning_os/app/handlers/maps.py` (expand/preflight under existing import); `tests/test_material_editing.py` (verified owning existing tests: preservation, malformed, stale and transaction refusals); `tools/learning_os/domain/plan_import.py` and `tests/test_compact_module_plan_revision.py` (later Unit delta assembly); sibling UI `src/gateway-client.ts`, `src/features/unit/map-import.ts`, `src/features/unit/shell.ts` (controls and exact review); existing dashboard fixture tests (visible review and invalidation). Any additional owning path will be recorded before it is changed.

Checkable sequence: implement pure edits; run owning map tests; implement UI controls and run UI checks; add Unit deltas and their refusal/preservation checks; rerun the disposable proportionality benchmark; retain Stage 5 outcome and commit/push its pair. Risks are state loss, authored-reference expansion, ambiguous placement, stale reviews and partial transactions; the above refusal/oracle tests expose each. Full combined hosted acceptance remains Stage 8. Real learner Units and today's plan, new entities, generic patch languages, admission widening and production installation are out of scope.

UI additional owning path verified: `src/types/runtime.d.ts` declares the supported Node surface; add only temporary-file APIs used by the structural review. No stored-record or manifest shape changes are needed. Aram narrowed this continuation to finishing the current Stage 5 milestone; Stages 6–8 remain deferred after its outcome.

Stage 5 initial-operation owning checks pass (30 material-editing cases, 123 direct UI module cases and the dashboard controls). Unit extension now proceeds: compact `unit_additions` carries only each new Unit, its new map and added source routes; relative placement defaults to append. `unit_move` derives module ordering and affected numeric Unit order fields from stable IDs, supplies the existing intentional-reorder declaration from its reason and preserves all maps/state. The full existing module plan contract, audit, claim evidence, semantic review and transaction gate remain mandatory. File-backed operator preflight/apply avoids handwritten guards; no module-import UI admission is added. This is a deliberate scope boundary: Unit authoring stays operator-reviewed; stage/resource controls are available directly in Obsidian.

Refusal witness verification found that `rich_world` deliberately carries a legacy map without current template numbering, so it cannot reach the new shadow preflight. Add a bounded `rich_world_structural` variant in `tests/scenario_harness.py` using the existing valid current-template replacement fixture; only the new structural-preflight case uses it. Retain exact recordings for the two new refusal sites and update the existing compact-empty-input diagnostic recording. This preserves historical fixtures rather than weakening current-template admission to reach a test branch.

## Stage 5 implementation outcome

Stage 5 implementation and focused preservation/refusal/UI verification are complete; see [the outcome record](2026-10-29-agility-stage5-outcome.md) for the exact scope, Unit-authoring boundary and measured comparison. The original learner checkout remains unchanged. Aram's latest instruction limits this continuation to this milestone, so do not start Stages 6–8. Keep milestone branch CI distinct from Stage 8's final combined exact-pair/artifact acceptance.
