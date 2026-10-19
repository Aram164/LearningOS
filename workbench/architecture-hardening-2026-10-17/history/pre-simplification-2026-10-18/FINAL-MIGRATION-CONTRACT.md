# Final LearningOS reliability and architecture migration

## 1. Understanding

Make this the final planned structural migration for LearningOS’s current requirements, leaving a coherent implementation with enforced boundaries and proven recovery behavior. Preserve learner work, provenance, existing capabilities and efficient agent workflows while completing the claim-admission, scan and hardening changes. Completion requires working code, independent effects evidence and runtime verification, with no unresolved major correctness or architecture findings.

The final review found necessary amendments. It also reproduced a concrete transaction defect in a temporary world: failure after receipt publication left a committed receipt while rolling the data back.

This contract supersedes conflicting execution details in the saved [migration plan](/Users/aramaljanadi/Desktop/semestercontext/LearningOS/workbench/architecture-hardening-2026-10-17/MIGRATION-PLAN.md). The three referenced source plans remain the detailed specifications and file inventories. This pass made no file changes; persisting these amendments is the first execution step.

## 2. End-state design and files affected

Retain the modular monolith and existing transaction service. Each migrated responsibility must have one production owner, typed inputs and outputs, and an executable boundary check.

| Responsibility | Required end state |
|---|---|
| Request admission | Request schemas remain authoritative; adapters own CLI parsing and deferred stdin access. Application admission does not construct a parser. |
| Application orchestration | Handlers coordinate explicit check/apply paths and return typed plans/results. They do not own persistence or carry arbitrary commit callbacks. |
| Material and claim decisions | Shared claim admission; material derivation consumes observed values and performs no filesystem, network or process access. |
| Persistence | TransactionService owns protocol decisions; mechanical filesystem helpers report publication/durability phases without acquiring independent write authority. |
| Results and policies | Closed success/refusal/uncertain alternatives and capability-bound ordinary, goal and AI policies replace ambient classification and open-ended hook combinations. |
| UI | Generated collection types survive through the store. Freshness and recovery reuse the existing plugin lifecycle lease and preserve the last validated view. |

The existing inventories still apply. These additional concrete changes are required:

- `tools/learning_os/app/handlers/sources.py`: include source revision in lineage guard preparation. There are **five existing lineage writers**; evidence-bearing route-patch becomes the sixth.
- `tests/architecture/operational-owners.yaml`, `tests/arch_audit_hook.py` and the existing write/protected-import checks: enforce bounded filesystem-helper delegation, correct lineage ownership and declare settlement storage.
- `pyproject.toml` and `Makefile`: maintain strict-mypy coverage for every new production module and migrated typed boundary; invoke it permanently from `system-check`.
- `system/contracts/backup-roots.yaml` and `tools/learning_os/app/backup_manifest.py`: include the goal ledger and verify the additional vault recovery-state safety bundle.
- Existing claim, source-revision, transaction, recovery, backup and UI lifecycle test families: extend their coverage rather than build a parallel test framework.

Temporary adapters and superseded implementations must be removed in their migration slice. Moving a large function unchanged into another file does not satisfy the architecture exit.

## 3. Ordered execution

### 0. Freeze the baseline and acceptance inventory

Reconcile the source pair, dirty work, active writers, toolchain, disk and governing contracts. Capture one quiescent world, including independently inventoried authored data, operational evidence and installed-vault settings.

Create one compact execution ledger linking each requirement to its implementation, decisive tests, negative control and acceptance receipt. Correct the earlier four-writer claim explicitly.

**Exit:** reproducible inputs, preserved unrelated work, confirmed ownership and a finite list of acceptance obligations.

### 1. Establish enforcement before introducing new structures

Add the permanent strict-type gate and extend the ownership checks before moving filesystem effects.

Protect the new filesystem helper from direct handler/derivation imports. Attribute mechanical helper calls to their authorized semantic owner while retaining independent before/after byte checks. Do not exempt `store/**` or infer authority merely because an engine frame appears somewhere on the stack.

Extend backup coverage to handler-owned durable operational files, including `operations/goal-ledger.yaml`; loader-observed inputs alone are insufficient.

Start the finite transaction-state model here. Extend it for S9 later, rather than postponing protocol modeling until recovery implementation.

**Exit:** deliberate impure derivation, unauthorized helper writes, hidden callback writes and incorrect typed alternatives all make their respective checks fail.

### 2. Implement the combined claim slice

Implement the matcher and reader, then shared admission, writer guards, audit lifecycle and read annotations.

**Admission and guards**

- Apply one admission rule to material/coverage changes and permitted unchanged stale/disputed re-judgments.
- Prepare identical prospective paths and revision guards for check, envelope, apply and receipt.
- Every lineage writer—including source revision—guards the shared lineage artifact.
- Evidence-only repairs change lineage and its file revision without inventing unit/module changes.
- Narrowly update receipt verification for ledger-only writes; retain ordinary-write checks.

**Material verification**

- Classify known-local-but-unresolved material separately and refuse admission. Removing a file binding or creating an ambiguous locator must not turn a local claim into an existence-only remote claim.
- Determine classification from before/after identities and declared material authority.
- Hash and extract from the same immutable per-request byte snapshot; reuse it per unique file and re-admit at apply.
- Require an explicit place for unreadable-PDF fallback. Parser, dependency, encryption or extraction errors refuse; they do not silently become “no text.”
- Preserve explicit remote/unanchored and unsupported-format outcomes.
- Retain duplicate-locator rejection as a declared authoring constraint, with the historical broadcast controls proving its intended scope.

**Goal and audit identity**

- Bind stale-goal occurrence identity to the stable judgment plus relevant current stale facts. Exclude unrelated snapshots, clocks and read ordering.
- Persist full digests; abbreviate only for display.
- Different relevant dependency drift creates a new occurrence. Identical facts intentionally reuse the prior decision.
- Store audit authorization and result separately from mutable attention state.
- Authorize one frozen pool/sample once; identical replay succeeds, redraw or conflicting closure refuses.
- Reject/defer must preserve the seed, sample, report and defects.
- Match certification and defects to exact claim/basis pairs.

Include evidence-bearing route-patch in the complete target, with its explicit write grant. If that amendment remains unapproved, the migration remains incomplete.

Batch schema, surface, parity and transcript regeneration after the slice stabilizes. Obtain required approval against the actual candidate diff.

**C1:** complete paired gate, claim acceptance scenarios, real-material checks and read/admission performance evidence.

### 3. Capture the hardening baseline, then repair durability and conflicts

Record hardening S0 against the accepted claim candidate. Reuse the captured inputs and independent observer.

Implement S1–S2 with an explicit receipt-publication state:

- Before receipt publication, guarded rollback remains possible.
- If this transaction’s receipt may have been published but durability is unconfirmed, preserve forward effects and the journal; return uncertain/recovery-required.
- Never roll data back behind that transaction’s valid visible receipt.
- Recovery verifies the surviving evidence and establishes durability before settlement.
- Preserve the existing distinction between this receipt and unrelated foreign evidence.

Cover file and directory barriers, new ancestors, deletion, settlement, ownership-preserving rollback and external edits.

**C2:** complete paired gate plus fault/interleaving evidence. The reproduced receipt-barrier failure must be a permanent regression, with a disabled-protection control.

### 4. Complete the application and UI structure in small slices

Execute the existing hardening order:

1. Schema-derived request normalization and deferred input.
2. Explicit commit results.
3. Closed capability-bound policies and session ownership.
4. Material derivation, source/dossier planning, prepared imports and reference checking.
5. Typed UI collection access.
6. Exact-byte projection freshness.

Each slice retains its focused behavior/effects tests and removes its old implementation before acceptance.

Prepared imports carry explicit writes, guards, report data and planned lineage effects. They must not conceal orchestration inside untyped dictionaries or callback factories.

Freshness/recovery must reuse the existing plugin lifecycle lease. Unload/re-enable during a query, rebuild or resolution must dispose timers/watchers and prevent an old instance from authorizing, overwriting settings, archiving pending work or initiating duplicate effects.

**Exit:** all architecture obligations are mechanically enforced, with no temporary compatibility layer left behind.

### 5. Implement reviewed recovery with explicit terminal branches

Extend the state model and connect its transitions to production interruption tests.

Choose these branches explicitly:

- **Proven committed:** preserve the original committed ledger row and receipt; settle its journal without repeating original effects.
- **Absent original row, safely rolled back or uncertain:** perform the reviewed receipt-bound retirement transition.
- **Contradictory or malformed evidence:** retain evidence and block mutation.

A resolution uses a distinct identity and its own receipt referencing the original evidence. Preserve exact original and resolution envelopes before dispatch.

Fence both the retired key and the original request ID against aliasing under another key. Preserve normal key/intent collision refusals. This does not claim to revoke every separately authorized request with identical content.

Retain the wrapper-before-effects barrier, old-reader refusal, receipt-history inversion, settlement certificates and failed-settings-save behavior. The first durable v3 wrapper remains the downgrade boundary.

**Exit:** the model, actual old-reader tests, restart/replay tests and restore tests agree.

### 6. Prove the final source pair

Perform C3 after all source changes:

- Complete paired gate and permanent type/architecture checks.
- Independent review of actual production ownership and dataflow.
- Captured-world effects comparisons and performance measurements.
- Real Core/production-validator integration.
- Disposable-Obsidian workflows and restore drill.

Resolve confirmed major findings and recheck their affected seams. Avoid restarting unchanged broad investigations.

**Exit:** no unresolved major correctness or architecture finding; every acceptance obligation has evidence. Passing a build or a large test count alone is insufficient.

### 7. Rehearse content migration, then perform controlled rollout

Prepare the 21 claim repairs from pinned materials and rehearse governed application in disposable state. Reuse semantic review only while its exact source and material bindings remain valid.

The live sequence is:

1. Quiesce writers and preserve pending drafts/envelopes.
2. Capture and verify the complete pre-change backup and safety bundle.
3. Deploy the accepted compatible Core/UI pair.
4. Verify installed bytes, loaded runtime and read-only operation.
5. Apply authorized claim repairs sequentially, verifying each receipt immediately.
6. Freeze the actual audit pool and perform its single authorized sample.
7. Verify projection freshness, runtime behavior and safe re-entry.

A defective audit produces repair work; it is never redrawn to obtain a clean result.

Publication requires the applicable exact-pair CI receipts. Installation and content application retain their explicit authorization boundaries.

## 4. Recovery and rollout risks

- **Backup incompleteness:** preserve the installed plugin’s raw `data.json`, including malformed records, pending/resolving/archived envelopes and drafts. Store it outside live roots in a versioned safety bundle bound to the ordinary backup, source pair and retirement evidence.
- **Old backups resurrecting requests:** restore readiness requires reconciliation with later retirement evidence. Missing or contradictory evidence leaves writes blocked.
- **False certainty from citations or audits:** verified quotation presence is distinct from semantic support; sampled certification covers only its frozen population.
- **Uncontrolled external writers:** preserve detected conflicts and state the cooperative-lock boundary. Do not claim atomic exclusion of arbitrary editors or physical power-loss proof from process termination.

Extend the existing backup interface with `backup-manifest --vault-state-file PATH` and `backup-verify --safety-bundle FILE`. Keep the ordinary backup manifest compatible by storing the additional vault evidence in an adjacent versioned bundle. Migration-readiness verification requires that bundle; historical checksum verification remains available.

## 5. Verification and completion criteria

| Area | Mandatory decisive scenarios |
|---|---|
| Claim admission | Historical broadcast; missing/wrong-file/wrong-page quotes; local-to-unresolved downgrade; partial multi-file resolution; unreadable fallback; material replacement during extraction and between check/apply. |
| Shared lineage | Interposed writes from all six writers; source attach with dossier replacement/rebase; ledger-only repair; exact replay; ordinary-write verification negative controls. |
| Goals and audits | Rejected drift A → fresh → different B; identical recurrence; restamp stability; immutable authorization/result; re-decisions; failed audit → repair → new basis; historical closure; pools below threshold. |
| Transaction durability | Exceptions, EIO/ENOSPC and interruption before/after each persistence barrier; receipt visible but durability unconfirmed; settlement interruption; foreign receipt and foreign-edit preservation. |
| Recovery | Committed/rolled-back/unknown/contradictory originals; delayed requests; identity aliases; multiple journal wrappers; old-reader attempts; inverse receipt history; duplicate resolution. |
| Backup/restore | Goal decisions/sample unchanged; raw vault state preserved; omitted/tampered bundle; older backup with later retirements; unavailable frontier. |
| Architecture | Strict typing and negative fixtures; denied-I/O derivation; protected helpers; callback/policy substitution controls; no superseded implementation or hidden persistent cache. |
| UI and existing workflows | Startup, navigation, notes/materials, Atlas, reviewed edits, corrupt refresh, midnight/missed events, unload/re-enable, failed saves, resolution and restart against real Core. |
| Performance | Existing warm/fresh reads, admission, writes/replay, UI navigation, freshness IO/CPU and memory against the specified budgets. |

Retain three full local milestone gates:

```sh
PYTEST_ADDOPTS='-m "not live_install"' make system-check
```

The gate must include the new maintained type checks and registered tests. Use focused checks between milestones. Reuse receipts only for the source pair, toolchain and relevant inputs they prove; enumerate every skipped test and supply its required platform or disposable-runtime evidence.

Final acceptance requires:

- Zero validation errors and no new warning signature.
- No unexplained behavior/effects regression.
- One enforced owner per migrated responsibility.
- No arbitrary callback escape hatch or untyped new service.
- Proven preservation of authored bytes, drafts, receipts and recovery evidence.
- Verified source, build, installed runtime and interactions.
- No unresolved major structural finding.

## 6. Assumptions, defaults and boundaries

**ASSUMPTION:** the currently verified clean pair remains the execution baseline; recheck before starting. Use the current macOS host for platform durability evidence and Linux CI for portable engine behavior.

“Final migration” means closure of the known structural work under current requirements. Later features require their own demonstrated need; they are not preemptively added here.

The 786 unrecorded routes, remote semantic verification, unsupported readers and three study-map obligations remain explicit content/product boundaries. They must be represented honestly and tested, but do not justify another architecture expansion.

No database replacement, new runtime framework, telemetry/model-routing project, broad UI redesign, unrelated dirty-work changes, legacy edits or Stratum work. This pass remains planning only.
