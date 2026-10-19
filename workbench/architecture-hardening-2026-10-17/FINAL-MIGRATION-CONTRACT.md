# LearningOS — streamline and harden the existing architecture

18 October 2026. Revised execution plan, following Aram's supplied v2 and explicit direction to improve, maximize and streamline the existing architecture without bloat.

**This is the single authoritative migration plan.** It replaces the priorities, scope and completion criteria of the earlier contract, MIGRATION-PLAN.md and PLAN.md. Their exact historical bytes are preserved in [history/pre-simplification-2026-10-18/](history/pre-simplification-2026-10-18/INDEX.json). Earlier anchor/scan plans are design references, not inherited work orders. Existing repository contracts and authorization boundaries still apply. The published branch copy and external execution copy of this document must match.

**Scope frozen after targeted audit amendments.** The source observations were checked against Core `c0365af0f2ca2b8f04e76cc17cb427a0011a8d7d` and UI `a88b1188ad54439b4df32813904de182c06a105c`; this review did not execute the candidate tests. Implement the finite requirements below rather than commission another broad architecture redesign. Reopen a decision only for a demonstrated failure or a changed product requirement.

## 1. Understanding

Improve LearningOS's existing modular monolith so it is reliable, efficient and clear to use and maintain. Preserve completed claim/provenance work, fix demonstrated transaction failures, remove repeated work and unnecessary coupling, and protect learner drafts and state. Finish against the finite acceptance cases below, without promising a final architecture for all future requirements.

### Verified starting point

- Candidate Core: `execution/candidate/repository`, branch `review/architecture-hardening-2026-10-18`, HEAD `300a04a920a31f62734b7e367b618dca3faeb1bf`; tracked working tree clean when inspected. Its WIP commit says `[skip ci]`, which is not acceptance evidence. Local `main` is `074f4717e14527798752de84b3c9c4e88348b658`.
- Candidate UI: `execution/candidate/obsidian-ui`, HEAD `a88b1188ad54439b4df32813904de182c06a105c`; existing untracked `node_modules` is runtime input, not migration content.
- Shared claim admission/status, verbatim matching, immutable PDF/anchor verification, lineage guards and consolidated detectors already exist. Preserve them; do not re-extract their responsibilities.
- One scan currently reopens the goal ledger through `collect_observations`, `observe_claims`, `read_goal_ledger` and `intelligence_scan`. Basic claim observation unconditionally parses audits. These are verified cleanup targets.
- `TransactionService::_write_receipt` sets `commit_reached` only after `atomic_write_bytes` returns. The retained receipt-parent failure probe demonstrated visible committed evidence with rolled-back data; the production repair remains required.
- `manifest-store.ts::load` publishes a complete validated snapshot on success but clears its valid data/indexes on failure. Retain the successful publication design and repair the failure branch.
- `tests/test_compact_module_plan_revision.py` already exercises compact multi-unit `unit_revisions` through module-plan-import. Improve this path before creating an editing API.
- Historical receipts report 233 selected scenario comparisons passing, and 7 of 36 procedure comparisons passing. Classify all 29 remaining differences; none is assumed harmless. Exact receipts, runtime corrections and evidence limitations are in the archived [continuation](history/pre-simplification-2026-10-18/execution/CONTINUE.md). C1/C2/C3 remain unaccepted.

**ASSUMPTION:** these inputs remain available and no competing writer owns the candidate when implementation resumes. Reconcile actual tips, dirty files, processes and imported production paths before mutation. Do not reset the candidate or recapture the original baseline.

### Decisions and reasons

1. **Improve the existing owner first and delete superseded paths in the same slice.** Fewer layers, duplicate rules and behavioral combinations are the objective. Function size or an old planned filename does not justify extraction.
2. **Reuse existing abstractions.** Keep TransactionService, compare-and-undo, GatewayEnvelopeV2, idempotency, schema validation, Outcome, the session owner and plugin lifecycle lease. No parallel transaction, workflow, filesystem or recovery framework.
3. **Share one request-local ledger observation and separate basic status from optional audit enrichment.** This removes redundant IO and failure coupling without a persistent cache. Audit-dependent decisions still require trustworthy audit evidence.
4. **Do bounded claim cleanup before C1, then prioritize S1/S2.** Establish the baseline once; audit feature work and cosmetic restructuring must not hold up safety repairs. Existing tests still have to pass.
5. **Freeze audit scope and defer advanced recovery.** Keep valid existing audit behavior and evidence. Do not expand Wilson quieting, certification or sampling; require a reproduced unmet requirement before new irreversible recovery formats.
6. **Use focused checks between three full gates.** Reuse evidence that still applies and existing harnesses. Do not build another verification platform or repeatedly rerun unchanged broad investigations.
7. **Keep future changes independently reviewable without rewriting the WIP history.** A small behavior/effects slice is useful; cosmetic history reconstruction is not.

A new production abstraction is justified only when the existing owner cannot express a required behavior clearly and the addition reduces duplicated logic or a concrete dependency problem. Prefer a function or closed value to a registry, hierarchy, plugin hook or configurable callback system. Record the reason with the change. No new production module is prescribed merely to satisfy this plan. The audit amendments strengthen evidence and existing recovery guards; they do not introduce another engine or protocol.

## 2. Files affected

Core/UI paths below are relative to the existing isolated roots named above, under this plan's external execution directory. Edit only the files a step actually needs.

| Existing path | Why it may change |
|---|---|
| Core `tools/learning_os/derive/semantics/{scan,claim_status,claim_audits,goals}.py` | Share observations and isolate optional audit enrichment while retaining one status/detector owner. |
| Core `tools/learning_os/app/claim_admission.py` and `app/handlers/{goals,plan,routes,sources,synthesis}.py` | Adapt consumers without weakening eligibility, evidence admission or shared lineage guards. |
| Core `tools/learning_os/store/{transactions,evidence}.py` and `domain/{transaction,failures}.py` | Repair publication, pre-apply checks, ownership-preserving rollback, settlement and restart in the existing implementation. |
| Core `tools/learning_os/app/{gateway,pipeline,commit,outcomes,proposal}.py`, `store/contracts/requests.py`, `adapters/cli_parser.py` | Remove parser round-trips and ambient refusal state using existing normalization/result ownership. |
| Core `tools/learning_os/app/session.py`, `app/handlers/materials.py`, `app/handlers/plan.py`, `app/handlers/sources.py`, `derive/validation/references.py` | Target only independently demonstrated remaining ownership or duplication problems; skip unnecessary extractions. |
| Core `system/schema/requests/`, `system/contracts/capabilities.yaml`, `system/templates/unit-plan-revise.template.yaml`, `system/SEMANTIC-CONTRACT.md`, `system/WORKFLOWS.md` | Align actual payloads, compact editing and audit availability; do not design speculative capabilities. |
| UI `src/manifest-store.ts`, `src/contracts/manifest.ts`, `src/features/unit/model.ts`, `src/main.ts`, `src/gateway-client.ts`, `src/contracts/gateway-v2.ts`, `src/application/gateway-recovery.ts` | Preserve collection types, last validated views, drafts, exact pending envelopes and lifecycle ownership. |
| Core `Makefile`, `pyproject.toml`, `tests/group_map.py`, `tests/architecture/surface-approvals.yaml`; UI `package.json` | Maintain existing gates and register real scenarios; do not weaken ratchets or reset baselines. |
| Existing test families in §5 | Extend the harnesses already exercising these owners. |

**NEW bounded test file:** Core `tests/test_transaction_faults.py`, registered in the existing groups, to exercise real TransactionService commit/rollback/restart schedules. It must not implement a second transaction engine. Prefer extending existing tests for other changes.

## 3. Steps

### 0. Preserve and reconcile

Reuse the captured world, immutable material inventory, runtime-provenance correction, raw receipts and vault safety bundle. Record current tips, dirty files, active jobs and actual imported code before resuming; preserve unrelated work and failed evidence. Old percentage estimates concern a larger superseded scope and are no longer scheduling commitments.

Aram approved the exact five-key C1 packet on 18 October 2026. Preserve [its approval receipt](execution/C1-SURFACE-APPROVAL.json) and immutable JSON. The historical contract hash remains verifiable in the archived original; never rewrite either hash. Apply dated A11 entries only after matching the actual diff. Additional surface changes retain their own applicable approval requirement.

**Exit:** the preserved candidate, imported production paths and applicable evidence are identified, without restarting or recapturing the baseline.

### 1. Remove repeated reads and audit coupling; complete C1

Load the goal-ledger bytes once per scan and share that immutable, request-local observation across decisions, metrics and optional audit enrichment. Basic evidence/lineage freshness must not reopen the ledger simply to calculate status. Its authority ends with that protected operation: an independently authorized write must capture/revalidate its own relevant current state under existing transaction guards. No persistent cache or scan snapshot reused as later write authority. Test an intervening ledger change between the read and independent check/apply.

Malformed isolated audit content must leave ordinary route/stage/plan inspection and basic evidence freshness usable, with enrichment explicitly unavailable. It must never count as certification or proof of no defects. Audit authorization, closure and audit-dependent rejudgment refuse when required evidence is invalid. Preserve global canonical validation on writes; read isolation does not bypass a genuine validation error. Malformed decisions must not silently suppress goals.

Keep existing valid authorization/result immutability and exact claim/basis membership. Add no audit features or statistical tuning. Retain claim admission and all-six-writer controls. Classify all 29 retained procedure diffs, fix actual regressions and change only justified expectations; never bless a failed positive scenario or remove an oracle to get green.

**C1 exit:** one ledger-byte read per scan is measured; basic reads survive isolated malformed audit enrichment while dependent actions refuse; complete scenario population/A19 and procedure comparisons pass with correct candidate provenance; actual surface approval is applied; the full paired gate passes. Reuse material/timing receipts only for matching relevant inputs. Then record the accepted claim baseline (S0). Optional audit enhancements are not C1 obligations.

**Bounded scheduling exception:** if procedure analysis remains prolonged after a focused classification pass, an S1 failure investigation may use a frozen candidate in isolated disposable state. Reproduce the defect and trial a narrowly scoped fix without modifying the active claim candidate, its baseline or shared operational data. No automatic agent delegation is authorized. Integrate and revalidate only after reconciling C1; do not claim C2 acceptance from the isolated investigation.

### 2. Fix transaction correctness and filesystem durability — S1/S2, then C2

Add the production regression for receipt-parent failure first. Extend the existing transaction run with `NOT_PUBLISHED`, `PUBLICATION_UNCERTAIN` and `DURABLE`. Mark uncertainty before entering an operation that may expose the receipt before its final barrier returns. Distinguish matching transaction evidence from foreign or contradictory files.

Before publication, ownership-guarded rollback is allowed. After possible receipt exposure, preserve forward state and journal on uncertainty; never undo data behind a matching receipt or report definitive refusal. Success requires confirmed durability. Fresh-process recovery verifies evidence, establishes necessary barriers and settles without repeating effects; contradictions preserve evidence and block writes.

Before retiring recovery information, join the receipt to the exact journal/transaction and its intended effects, using available request, capability, hash and idempotency evidence. Schema validity, committed status and a matching transaction ID alone are insufficient. A valid-looking receipt with mismatched effects must preserve the journal and block settlement. Verify historical evidence against the recorded transaction, not by requiring current mutable files or the whole current idempotency ledger to equal an old postimage: later legitimate transactions must remain valid. Test wrong-effect/wrong-hash receipts and a genuine commit followed by a legitimate later write. Missing required proof stays explicit; do not fabricate certainty or default to rollback behind a possibly committed receipt.

**End-to-end uncertainty is part of C2, before the S4 refactor.** Every uncertain engine outcome must survive existing commit/error classification and the serialized Gateway response as ambiguous. Exercise the real Core → Gateway → UI path, including the definitive-no-commit code list. Assert that the original envelope and draft remain, the UI stays unresolved, and later exact replay/reconciliation produces no duplicate effect. Never reuse a definitive-refusal code for an uncertain outcome.

Compare captured bytes/existence immediately before each mutation, including deletion and operational targets. Rollback/restart undo only state proven to belong to this transaction, preserving foreign edits. State the cooperative-writer boundary: a pre-apply check cannot atomically exclude an arbitrary editor writing after it.

Complete existing file/parent-directory persistence ordering for new ancestors, replace, unlink, journal/receipt publication and settlement. Reuse atomic-write primitives and centralize only genuinely repeated mechanics. Keep the journal format unless a production failure demonstrates a necessary minimal change. Durable settlement is required; certificates and a general compatibility protocol are not presumed necessary.

Inject exceptions, EIO/ENOSPC and child-process interruption at actual persistence boundaries, including the receipt visibility interval and cleanup. Retain prior abstract-model evidence as support, but connect decisive transitions to production execution and restart. Use independent byte/receipt oracles and disabled-protection controls.

Record the actual macOS volume and file/directory synchronization capabilities, including availability and use of stronger flush operations such as `F_FULLFSYNC` where the required guarantee calls for them. Exercise supported barriers/failures in the existing fault harness and document unsupported guarantees. Linux CI supplies portable evidence, not a substitute for the macOS host check. Process-interruption tests are not physical power-loss proof; this is a focused capability/evidence check, not a filesystem framework.

**C2 exit:** receipt–journal–effect consistency is proven before settlement, including later legitimate writes; visible-but-unconfirmed receipts never trigger backward rollback; serialized uncertainty preserves UI recovery evidence/drafts and exact replay; foreign edits survive apply/failure/restart; namespace barriers and interrupted settlement pass real fault schedules; macOS capabilities/limits are recorded. The second full paired gate passes.

### 3. Simplify application boundaries — S3/S4/S5; targeted S6 only

Remove gateway CLI-parser construction through the existing schema/request-normalization owner; keep parsing/deferred input in adapters and preserve omitted/null/false/empty semantics and validation order. Replace commit tuples and ambient refusal state with narrow typed alternatives mapped once into existing Outcome; preserve uncertain/post-commit facts.

Express only actual ordinary, goal and AI commit cases, selected by the owning capability. Prefer closed branches to a policy hierarchy; mandatory phases stay inside TransactionService. Move misplaced session reconstruction into existing `app/session.py` only where still needed and remove the former implementation.

Inspect remaining material-ranking, source/dossier, prepared-import and reference-index seams. Extract only a demonstrated independent responsibility or duplicate computation. Skip proposed extractions where ownership is already clear. Do not re-extract claim logic, add callback factories or convert the entire repository into service objects.

**Exit:** admission works with CLI-parser construction unavailable; sequential refusals cannot leak classifications; invalid policy substitutions refuse; migrated pure calculations have no IO; existing effects/scopes remain equivalent outside approved deltas; obsolete implementations are gone.

### 4. Improve existing compact editing

Use existing `unit_revisions`/`unit.plan.revise`. Reproduce the source-plus-multi-unit scenario in Core `archive/inbox/2026/complaints/2026-09-28-sad-plan-import-friction.md` in disposable state. Extend only missing parts of that concrete revision; do not add a generic patch language or another planner. If the existing path already satisfies it, improve only relevant help/templates/tests.

Submit intended changes and necessary review/evidence without copying untouched module records; assemble from guarded current state. Preserve snapshot/revision guards, reviewed input hashes, claim evidence, source completeness, learner state, atomic effects and exact replay.

**Exit:** the September 28 scenario completes with one compact revision input, one normal check/apply review cycle, no copied unchanged unit records and no avoidable assembly-repair cycle. Record input bytes, affected files, agent/user steps and elapsed time against the original workflow. Historical timings are not assumed comparable: if unavailable, use a controlled disposable reconstruction and label that comparison. Stale input/scope and missing evidence refuse without writes; notes, progress and unrelated units remain byte-identical. If the existing path meets this criterion, add no editing architecture.

### 5. Improve UI typing and non-destructive freshness — S7/S8

Carry generated collection-specific types into real unit/stage consumers; keep heterogeneous search where needed. Avoid arbitrary `get<T>` casts and a second UI model.

A failed/missing/malformed/incompatible refresh retains the last validated manifest/indexes and visibly marks them stale. With no valid initial snapshot, show unavailable. Preserve drafts, and never use a stale view as fresh write approval. Bind freshness to the exact loaded manifest bytes through existing projection/snapshot identity logic.

Refresh on successful mutations, relevant vault events and focus/re-entry; coalesce work and reuse the existing plugin lease. Unloaded-instance callbacks cannot publish state, save settings or send writes. Add no periodic polling unless a reproduced missed-event case remains; any necessary fallback must be bounded and lifecycle-owned.

**Exit:** typing holds in consumers; corrupt refresh retains a visibly stale view; successful refresh publishes one complete snapshot; drafts/pending envelopes survive failure and unload/re-enable; local navigation adds no Core round-trip.

### 6. Provide simple safe recovery — S9a

Improve existing inspection of the exact original envelope, committed/refused/unknown evidence and draft. Proven commits reconcile the existing receipt/projection without repeating effects; supported retries replay the identical approved envelope. Unknown/contradictory cases stay visibly blocked with an explicit next action and preserved evidence. A failed settings save cannot count as completed resolution.

Never replace ambiguity with a newly identified write, infer non-execution from a missing process, or discard a recovery record merely to unblock the UI.

Every transition, including `markRecovering`, `markConfirmed`, `markBlocked`, refusal cleanup, confirmation settlement and failed-save rollback, may affect only the request identity and state it observed. Use existing request identity, expected state and lifecycle mechanisms; recheck ownership before applying an asynchronous result or restoring saved state. Test a late result after the slot advances, clears or contains another request; an old failed save; and unload/re-enable. None may resurrect a retired record, overwrite a newer record or clear its draft. No new recovery database/state-machine framework.

**Practical recovery is mandatory.** Fix a representative interruption set before implementation: lost response after commit, process interruption before/during effects, stale prepared request never dispatched, projection refresh failure and settings-save failure. Demonstrate an understandable safe path back to normal operation for these ordinary workflows; record learner steps/time and classify any residual blocked cases by cause. A common workflow left indefinitely blocked fails C3. Genuinely contradictory or malformed evidence must remain safely blocked with a concrete manual next action and its limitation reported.

**S9b is deferred:** journal v3, ledger v2, retirement/frontier protocols, settlement certificates, downgrade-history machinery and automatic replacement are not default deliverables. If a required workflow cannot be made safe with existing evidence/formats, retain its blocked case, reproduce it and propose the smallest extension for a separate architecture review. Do not implement half a retirement fence. Deferring the full S9b design must not excuse a common interruption case failing S9a usability: if one needs a fence, reproduce it and review only the smallest safe mechanism, without importing the whole former design. Speculative extensions remain outside the scope and do not delay unrelated safety repairs.

**Exit:** committed/refused/replayable/unknown/malformed cases behave as specified after restart; the representative common interruptions return to normal operation; stale asynchronous results cannot change newer recovery state; original evidence/drafts survive; no ambiguous request receives a new identity automatically. Report the measured blocked-case inventory and manual-resolution limitations rather than treating permanent common-workflow blocking as completion.

### 7. Accept the finite result — C3

Complete the fixed inventory in §5 and final paired gate. Recheck evidence invalidated by later changes, not every historical investigation. Review actual ownership and the specified failure cases; Aram assigns review roles, with no automatic delegation.

Rehearse startup/navigation, one note write, compact plan revision, interrupted-write recovery and stale refresh against real Core in disposable Obsidian. Restore authored/operational state and raw vault settings/drafts from the retained backup and verify independently, using the existing backup interface/safety bundle.

**Exit:** the inventory passes for the final pair, approved deltas and deferred limitations are explicit, and unrelated work is preserved. New suggestions outside this inventory become separate work; they do not expand this migration's finish line. Acceptance alone authorizes no live rollout.

## 4. Risks

| Risk | Observable failure and decisive check |
|---|---|
| Audit isolation trusts missing evidence | Malformed audit becomes certification or authorizes disputed rejudgment; require unavailable enrichment and dependent-operation refusal. |
| Publication or commit evidence is misclassified | Matching receipt survives while data are undone, contradictory effects settle, or Gateway/UI drops uncertain evidence; inject faults and wrong-effect receipts through real recovery and wire/UI paths. |
| External-edit protection overclaims exclusion | Noncooperating writer wins after a check; state the boundary and prove detected edits survive recovery. |
| Simplification drops mandatory phases | Ordinary/goal/AI writes lose authority, validation, ownership or replay safety; exercise each real family and policy substitution. |
| Preserved stale data looks current | Refresh failure retains data without a stale indication or permits stale approval; check display and gateway behavior. |
| Recovery shortcut or late result corrupts state | A new key duplicates effects, a common workflow stays blocked, or an old response/save rollback replaces newer evidence; verify usability plus identity/state/lifecycle interleavings. |
| Old plans reintroduce scope | A later implementer follows archived extraction/S9 requirements; current entry points must point here. |

## 5. Verification and finite acceptance

Use the existing ledger and harnesses. Missing scenarios, failed negative controls or unexplained effect differences fail their item; aggregate test counts do not substitute for evidence.

**Fast inner loop:** after a change, run targeted units, affected contracts/types and the focused fault/interleaving schedules. **Milestones:** C1/C2/C3 retain complete paired verification, independent state comparisons, required architecture checks and raw evidence. After a broad failure, first identify its component and pass the focused reproduction/fix before another full rerun. Reuse a successful receipt only while its relevant code, inputs, environment and verification oracle remain applicable. Never reduce coverage to save runtime.

| Gate | Required evidence |
|---|---|
| C1 observations | One immutable request-local ledger observation; bounded evidence resolution; scalar/batch agreement; isolated invalid audits preserve basic reads and refuse dependent actions; an intervening change cannot authorize a later write from the old observation. |
| C1 claim safety | Historical broadcast; missing/wrong-file/wrong-place evidence; local-to-unresolved refusal; apply-time material replacement; ledger-only repair; all-six-writer interpositions; exact replay and existing controls. |
| C1 regression boundary | All 29 procedure diffs classified; full scenarios/A19 and procedure comparisons with candidate imports; exact surface approval; first complete paired gate. |
| C2 publication/persistence | Real faults at file/parent barriers, new ancestors, unlink, journal/receipt publication and settlement; exact receipt–journal–effect/idempotency consistency before settlement; wrong-effect receipts refuse; later legitimate writes recover; macOS synchronization capabilities/limits recorded. |
| C2 serialized uncertainty | Actual Core/Gateway response and UI classification preserve ambiguous publication, envelope and draft; no definitive no-commit classification; subsequent exact replay/reconciliation has one effect. Required before S4. |
| C2 ownership | Foreign edits before apply/during failure/before restart survive; foreign receipts do not prove this transaction committed; replay has one effect; protection-disabled controls fail; second paired gate. |
| C3 boundaries | Parser unavailable at gateway admission; no ambient refusal leakage; closed capability-bound cases; no superseded paths; maintained strict typing/layers and effects checks. |
| C3 usability | September 28 scenario: one compact input, one check/apply cycle, no copied unchanged unit records or avoidable repair cycle; input bytes/files/steps/time compared; stale scope/evidence refuses; learner state/untouched bytes and replay preserved. |
| C3 UI/recovery | Refresh failures/success and lifecycle restarts preserve stale labeling, drafts and identities; representative common interruptions return to normal operation with measured steps/time and blocked-case inventory; late responses/save rollbacks cannot recreate retired or overwrite newer recovery state. |
| C3 runtime/restore | Disposable real-Core/Obsidian normal workflows and recovery; independently verified restore of authored/operational bytes and raw vault drafts/settings/recovery evidence. |
| C3 final pair | Zero validation errors, no new/grown warning signature, final full paired gate, no unexplained effect regression, unrelated-work preservation. Record all skips and required platform/runtime substitutes. |

Run only relevant focused families between milestones, extending their existing fixtures. The production fault file is **NEW**, to be implemented/registered in step 2 before its scenarios are claimed as covered.

```sh
# From execution/candidate/repository:
.venv/bin/python -m pytest -q tests/test_intelligence_scan.py tests/test_claim_status_audits.py tests/test_verbatim_anchor_admission.py tests/test_lineage_writer_interpositions.py
.venv/bin/python -m pytest -q tests/test_transactions.py tests/test_recovery_conflicts.py tests/test_gateway_v2.py tests/test_ui_gateway_recovery.py
.venv/bin/python -m pytest -q tests/test_ops_commit.py tests/test_ops_pipeline.py tests/test_gateway_typed_refusals.py tests/test_arch_outcomes.py tests/test_arch_callbacks.py
.venv/bin/python -m pytest -q tests/test_unit_plan_revision.py tests/test_compact_module_plan_revision.py tests/test_module_plan_warning_gate.py
.venv/bin/python -m pytest -q tests/test_arch_layers.py tests/test_arch_ratchets.py tests/test_arch_surface.py tests/test_arch_writes.py
make typecheck
npm --prefix ../obsidian-ui run typecheck
npm --prefix ../obsidian-ui run contract:check
npm --prefix ../obsidian-ui run test:manifest-store-indexes

# Once at each stable C1, C2 and C3 milestone:
PYTEST_ADDOPTS='-m "not live_install"' make system-check
```

Retain the earlier [performance budgets](history/pre-simplification-2026-10-18/PLAN.md#proposed-performance-budgets) for existing reads, writes/replay, local navigation, memory and any implemented freshness query. The blanket background-check obligation is removed. Reuse paired read/material receipts while relevant code/inputs match; measure changed transaction and refresh costs with existing tools. Record alternating same-world p50/p95 and IO. Do not remove required durability to meet a budget; report an exceeded budget and concrete tradeoff, without introducing a caching or benchmark platform.

This revision is planning/publication work; no production acceptance gate was rerun for it.

## 6. Out of scope

- Restarting completed work, re-extracting consolidated claim logic, cosmetic moves or creating every file an old plan proposed.
- Audit expansion, Wilson tuning, automatic semantic certification, telemetry or mandatory live audit workflows.
- Default S9b protocols without a demonstrated required failure and separate architecture review; dropping evidence is never an alternative.
- New databases, runtime/service frameworks, plugin registries, configurable commit callbacks, generic patch engines, persistent read caches or broad UI redesign.
- Repository-wide type/model conversion or arbitrary code-size targets.
- Live learner/content repairs, the historical 21-claim campaign, installation, release publication, legacy/Stratum changes or unrelated dirty work; these need their own authorized scope.

Aram authorized a plan-document commit/push to the existing migration review branch. That does not authorize production-code changes in this turn, history rewriting, merging, release or deployment. The existing implementation pause at the 5% usage boundary remains recorded; this planning request does not silently reset it.
