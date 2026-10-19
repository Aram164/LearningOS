# LearningOS architecture hardening plan

17 October 2026 — proposed implementation contract, not implementation or permission to install, publish or change learner data.

18 October integration note: [MIGRATION-PLAN.md](MIGRATION-PLAN.md) now governs
sequencing with the two claim plans and the shared acceptance schedule. Its
explicit amendments apply before S0; this document remains the detailed
hardening specification. Completed planning checks and their limits are in
[VERIFICATION-2026-10-18.md](VERIFICATION-2026-10-18.md).

## 1. Understanding

LearningOS needs the demonstrated transaction, recovery, durability and stale-read defects repaired while its application interfaces become easier to understand and maintain. The work must preserve learner-visible behavior, authored data, approval boundaries, provenance, receipts and the existing recovery guarantees, with modest measured performance losses acceptable. We will retain the current modular monolith and transaction owner, replace narrow interfaces incrementally, and accept each change using independent effects evidence as well as the existing suite.

### Verified starting point

| Item | Inspected state |
|---|---|
| Core | `/Users/aramaljanadi/Desktop/semestercontext/LearningOS/repository`, `074f4717e14527798752de84b3c9c4e88348b658` |
| UI | `/Users/aramaljanadi/Desktop/semestercontext/LearningOS/obsidian-ui`, `a88b1188ad54439b4df32813904de182c06a105c` |
| Working trees | Both clean when this plan was prepared |
| Binding direction | Core AGENTS → OPERATOR → normative corpus; ADR-018 governs the existing operation-boundary architecture |
| Existing behavior evidence | [Correctness review](/Users/aramaljanadi/.codex/visualizations/2026/10/17/01a14ba3-c560-7e83-946e-639b5bcc05d6/learningos-architecture-review/review.md), [source review](/Users/aramaljanadi/.codex/visualizations/2026/10/17/01a14ba3-c560-7e83-946e-639b5bcc05d6/learningos-architecture-review/code-quality-review.md), and their linked probe outputs |

Existing observations in this plan were checked in those revisions; proposed files and interfaces are marked **NEW**. **ASSUMPTION:** this is the implementation baseline; reconcile tips, dirty work, active writers and governing contracts again before starting. No live installation, physical power-loss test or performance acceptance run was performed for this planning task.

### Decisions and reasons

1. **Keep the modular monolith and TransactionService.** The problems are specific boundaries and missing safeguards; replacing storage, adding a server or introducing a general framework expands the risk without resolving them more directly.
2. **Use existing request schemas as the single operation definition.** Remove the parser round-trip by normalizing schema-described requests independently of argparse. Do not maintain a parallel catalogue.
3. **Keep one final application Outcome.** Replace the commit tuple and ambient refusal channel with a narrow internal result; map it into the existing Outcome once. Preserve exceptions that express genuinely exceptional or post-commit conditions until their separate migration is justified.
4. **Choose finite commit policies.** Ordinary, goal and AI-delivery proposals account for the inspected hook exceptions. Preserve typed domain preconditions and transaction-bound effects; do not expose mandatory engine phases as arbitrary handler callbacks.
5. **Repair correctness before broad extraction.** Durability and the reproduced lost-edit interval are isolated first; recovery's irreversible storage-compatibility transition comes after the shared boundary is explicit.
6. **Preserve plain-text ownership honestly.** Detect and retain conflicts from external editors, but do not claim atomic exclusion against arbitrary noncooperating writers. Complete exclusion would require a separate product decision about writer cooperation.
7. **Make unresolved-write resolution explicit.** A durable retirement fence prevents future execution; it is not evidence that an uncertain request never executed. Preserve the original envelope, draft and historical uncertainty. Use ledger storage v2 and recovery-journal storage v3 as explicit compatibility changes; protecting an old active journal must happen before resolution effects, because automatic recovery precedes ordinary ledger admission.
8. **Preserve existing generated manifest shape.** A separate bounded Core freshness query verifies the exact manifest bytes the UI loaded. Schema validity remains a distinct check.
9. **Spend modest time on stronger guarantees.** Add necessary synchronization and freshness checks, avoid new persistent caches, and measure overhead against predefined budgets rather than weakening correctness to meet a timing target.

Research and primary sources supporting these decisions are in [RESEARCH.md](/Users/aramaljanadi/Desktop/semestercontext/LearningOS/workbench/architecture-hardening-2026-10-17/RESEARCH.md).

### Finding-to-solution traceability

| Reviewed concern | Implementation / acceptance |
|---|---|
| Completed foreign edit overwritten | S2 uncached preimage checks and ownership-preserving rollback; original interleaving plus guard-disabled control. |
| Unfinished stale request blocks all writes | S9 reviewed resolution, saved draft/envelopes and late-request fence; restart/race/old-reader witnesses. |
| Missing persistence barriers | S1 namespace/file durability owner and settlement certificates; barrier fault model and platform evidence. |
| Old valid manifest presented as current | S8 exact-byte Core verification, bounded invalidation and retained stale view; real-validator/Core scenarios. |
| Gateway depends on CLI parser | S3 schema-derived normalization and adapter input port; gateway works with parser construction unavailable. |
| Commit failure facts split across channels | S4 explicit commit alternatives into the existing Outcome; no ambient refusal dependency. |
| Broad feature/session responsibilities | S5 session ownership service and S6 concrete material/source/import/reference separations; behavior/effect identity. |
| Proposal callback state space too broad | S5 capability-bound closed policies, retained explicit domain effects and extended A18 enforcement. |
| Strong wire schemas weakened internally | S6 typed boundary/views and S7 generated collection types; runtime validation plus negative type cases. |

## 2. Files affected

The following are concrete file targets, not permission to edit every file preemptively. A slice must touch only the targets its final design needs. Paths below are absolute so this plan can be handed to a fresh implementer.

| Existing file or group | Reason |
|---|---|
| `/Users/aramaljanadi/Desktop/semestercontext/LearningOS/repository/tools/learning_os/store/transactions.py` | Keep protocol ownership; add durable filesystem calls, guarded mutation/rollback, explicit journal settlement and merged recovery-ledger effects. |
| `/Users/aramaljanadi/Desktop/semestercontext/LearningOS/repository/tools/learning_os/domain/transaction.py`, `/Users/aramaljanadi/Desktop/semestercontext/LearningOS/repository/tools/learning_os/domain/failures.py`, `/Users/aramaljanadi/Desktop/semestercontext/LearningOS/repository/system/schema/transaction-receipt.schema.json` | Type engine-owned resolution/settlement effects and failures, and validate receipt-bound transition metadata without changing ReceiptV2 identity. |
| `/Users/aramaljanadi/Desktop/semestercontext/LearningOS/repository/tools/learning_os/store/evidence.py` and `tools/learning_os/store/diagnostics/resolver.py` under the same Core root | Read and verify committed/retired idempotency evidence consistently, including historical proof across the storage-version transition. |
| `/Users/aramaljanadi/Desktop/semestercontext/LearningOS/repository/tools/learning_os/app/lock.py` | Permit narrowly scoped, exclusive recovery inspection without normal automatic reconciliation; ordinary operations retain normal locking. |
| `/Users/aramaljanadi/Desktop/semestercontext/LearningOS/repository/tools/learning_os/app/gateway.py`, `app/pipeline.py`, `app/commit.py`, `app/outcomes.py`, `app/proposal.py` under `tools/learning_os/` | Remove parser-mediated admission and ambient commit refusal, simplify policies, enforce retirement before execution and retain one outer classification. |
| `/Users/aramaljanadi/Desktop/semestercontext/LearningOS/repository/tools/learning_os/store/contracts/requests.py`, `store/contracts/payloads.py`; `/Users/aramaljanadi/Desktop/semestercontext/LearningOS/repository/tools/learning_os/adapters/cli.py`, `adapters/cli_parser.py`, `adapters/capability.py` | Own bounded normalization and preserve CLI generation/transport translation; delete proven unreachable compatibility routes. |
| `/Users/aramaljanadi/Desktop/semestercontext/LearningOS/repository/tools/learning_os/app/session.py` | Own receipt-based session-ownership reconstruction currently embedded in the pipeline. |
| `/Users/aramaljanadi/Desktop/semestercontext/LearningOS/repository/tools/learning_os/app/context.py`, `/Users/aramaljanadi/Desktop/semestercontext/LearningOS/repository/tools/learning_os/app/handlers/capture.py`, `/Users/aramaljanadi/Desktop/semestercontext/LearningOS/repository/tools/learning_os/app/handlers/learner.py` | Replace direct stdin access with a deferred typed input port, preserving each operation's existing validation order. |
| `/Users/aramaljanadi/Desktop/semestercontext/LearningOS/repository/tools/learning_os/app/handlers/materials.py`, `app/handlers/goals.py`, `app/ai_actions/service.py` under `tools/learning_os/` | Thin the material handler and migrate the two exceptional proposal families without changing their ownership or effects. |
| `/Users/aramaljanadi/Desktop/semestercontext/LearningOS/repository/tools/learning_os/domain/snapshot.py` | Add narrow typed validated views where migrated code needs them; retain raw authored records and faithful serialization. |
| `/Users/aramaljanadi/Desktop/semestercontext/LearningOS/repository/tools/learning_os/app/handlers/sources.py`, `/Users/aramaljanadi/Desktop/semestercontext/LearningOS/repository/tools/learning_os/app/handlers/plan.py`, `/Users/aramaljanadi/Desktop/semestercontext/LearningOS/repository/tools/learning_os/derive/validation/references.py` | Separate dossier-impact planning, prepared-import construction and entity-family reference checks at the specific seams described in S6. |
| `/Users/aramaljanadi/Desktop/semestercontext/LearningOS/repository/tools/learning_os/domain/plan_import.py`, `/Users/aramaljanadi/Desktop/semestercontext/LearningOS/repository/tools/learning_os/app/_plan_gate.py` | Reuse their existing pure rules and staged gates during import extraction; do not create competing versions. |
| `/Users/aramaljanadi/Desktop/semestercontext/LearningOS/repository/tools/learning_os/app/projection.py` and `tools/learning_os/store/manifest_identity.py` | Share the current identity predicate and report freshness bound to the exact raw manifest hash. |
| `/Users/aramaljanadi/Desktop/semestercontext/LearningOS/obsidian-ui/src/manifest-store.ts`, `/Users/aramaljanadi/Desktop/semestercontext/LearningOS/obsidian-ui/src/contracts/manifest.ts`, `/Users/aramaljanadi/Desktop/semestercontext/LearningOS/obsidian-ui/src/features/unit/model.ts` | Preserve generated collection types and atomic index publication while keeping generic heterogeneous search. |
| `/Users/aramaljanadi/Desktop/semestercontext/LearningOS/obsidian-ui/src/gateway-client.ts`, `/Users/aramaljanadi/Desktop/semestercontext/LearningOS/obsidian-ui/src/main.ts`, `/Users/aramaljanadi/Desktop/semestercontext/LearningOS/obsidian-ui/src/views/review-view.ts` | Persist reviewed recovery transitions and connect bounded freshness verification to startup, focus, refresh and completed mutations. |
| `/Users/aramaljanadi/Desktop/semestercontext/LearningOS/repository/system/contracts/capabilities.yaml`, `/Users/aramaljanadi/Desktop/semestercontext/LearningOS/repository/system/schema/ui-responses.schema.json`, `/Users/aramaljanadi/Desktop/semestercontext/LearningOS/repository/system/schema/capability-envelope.schema.json` | Explicit additive operation/response/error contracts; update generated UI response artifacts through their generator. |
| `/Users/aramaljanadi/Desktop/semestercontext/LearningOS/repository/tests/group_map.py`, `/Users/aramaljanadi/Desktop/semestercontext/LearningOS/repository/tests/architecture/surface-approvals.yaml`, `/Users/aramaljanadi/Desktop/semestercontext/LearningOS/repository/tests/architecture/ratchets.yaml` | Register coverage and record only deliberately accepted surface changes; shrink callback/dependency allowances instead of resetting baselines. |
| `/Users/aramaljanadi/Desktop/semestercontext/LearningOS/repository/tests/test_arch_callbacks.py` | Extend A18 enforcement to policy variants and retained transaction-bound functions so moving a callback cannot hide it from the ratchet. |
| `/Users/aramaljanadi/Desktop/semestercontext/LearningOS/repository/system/ARCHITECTURE.md`, `/Users/aramaljanadi/Desktop/semestercontext/LearningOS/repository/system/procedures/back-up-and-restore.md`, `/Users/aramaljanadi/Desktop/semestercontext/LearningOS/repository/system/contracts/normative-corpus.yaml` | Document changed ownership, recovery storage compatibility and executable procedures; classify any new binding document. |

**NEW proposed Core files**, all under `/Users/aramaljanadi/Desktop/semestercontext/LearningOS/repository/`:

- `tools/learning_os/store/durable_fs.py`: filesystem persistence primitives with a small injectable syscall port for fault tests.
- `tools/learning_os/app/commit_result.py`: explicit narrow commit return alternatives.
- `tools/learning_os/app/commit_policy.py`: three closed policy variants, selected and interpreted by application-owned commit code.
- `tools/learning_os/app/material_context.py` and `tools/learning_os/derive/material_context.py`: file observation/orchestration and pure retrieval computation respectively.
- `tools/learning_os/app/source_revision.py` and `tools/learning_os/app/plan_import.py`: observed source/dossier impact planning and typed prepared-import construction; existing domain rules remain authoritative.
- `tools/learning_os/app/recovery.py` and `tools/learning_os/store/recovery_resolution.py`: reviewed recovery coordination and persistence of resolution evidence.
- `system/schema/requests/projection.status.schema.json`, `recovery.inspect.schema.json`, `recovery.resolve.schema.json` in that same requests directory; `system/schema/capabilities/recovery.resolve.schema.json`: explicit new operations.
- `system/procedures/review-an-unfinished-write.md`: executable recovery procedure.
- `tests/test_durable_fs.py`, `tests/test_request_normalization.py`, `tests/test_projection_status.py`, `tests/test_recovery_resolution.py`, `tests/test_architecture_hardening_adversarial.py`: focused new proof obligations, integrated with existing tests.
- `tools/benchmark_hardening.py`: non-CI measurement runner over disposable worlds, with machine-readable baseline/candidate results.

**NEW proposed UI files**, under `/Users/aramaljanadi/Desktop/semestercontext/LearningOS/obsidian-ui/`:

- `src/application/projection-freshness.ts`: bounded freshness state/coalescing, separate from rendering.
- `tests/test-projection-freshness.js` and `tests/test-recovery-resolution.js`: real-validator integration and persistence transition coverage; register them in `package.json` checks.

Existing test families to extend are identified with each slice below. New module names are design choices; avoid creating a wrapper that merely relocates the same responsibility without narrowing its interface.

## 3. Independently checkable implementation steps

### S0 — Pin behavior and build an independent acceptance baseline

1. Reconcile both source tips and dirty files; retain unrelated work. Create isolated paired candidate checkouts with the sibling layout expected by the paired gate. Use captured or synthetic data, with outputs outside the live repositories.
2. Capture only from an isolated, quiescent source with no active writers, and record that precondition. The existing capture tool copies sequentially; hashes of the result do not prove the source was consistent during copying. Pin that world using the existing capture/compare tools. Separately freeze an independently reviewed inventory of authored roots, operational evidence and UI settings/drafts. The new effects oracle uses OS traversal and byte hashes, not production request normalization, outcome classification or mutable production root constants. Existing audit attribution remains supplementary evidence.
3. Record public output, stderr, exit, request/intent identity, canonical bytes, receipt/revision/idempotency effects, session ownership and projection semantics. Fixed clocks/IDs make comparison useful; only documented nondeterministic fields may be normalized.
4. Establish the change allowlist: detected foreign-edit refusal, repaired durability, explicit stale/unavailable UI state, new reviewed recovery operations and retirement storage format. Everything else must remain equivalent.
5. Record fresh-process read, check/apply/replay and UI performance before implementation. Inventory the current request/default behavior, proposal hooks and all ledger readers, writers, verifiers and backup consumers. Prepare a deliberate architecture-contract amendment for the persistence/resolution protocol and its storage versions; ADR-018's earlier behavior-neutral transaction move cannot serve as blanket authority for these new behaviors. Surface/contract approval records must describe the actual new design and must not claim approval before it is given.

**Exit evidence:** pinned source pair/world, machine-readable effects and timing baselines, a finite compatibility matrix, and the four original probes still demonstrating the old failures. Baseline characterization is evidence about existing behavior, not an assertion that all existing behavior is correct.

### S1 — Give durable filesystem effects one owner

1. Add durable primitives for parent creation, atomic replacement/publication, rename and unlink. Synchronize every newly created ancestor entry in the required order, not only the final file's immediate parent.
2. Route transaction forward changes, rollback/recovery changes, journals, receipts, ledger publication, projection invalidation and cleanup through those primitives. Maintain the existing journal-before-data and receipt/commit ordering; do not distribute persistence decisions into handlers.
3. Run a small macOS/Linux capability experiment in disposable storage. On macOS verify the actual filesystem and `F_FULLFSYNC` behavior; select strong barriers for proof-critical persistent data. Surface synchronization failures and retain recoverable evidence. Never silently acknowledge an unsupported stronger guarantee.
4. After a transaction is proven settled, persist a settlement certificate binding its transaction ID, exact journal digest, disposition (`verified-commit`, `verified-rollback` or later `accepted-by-resolution`) and supporting commit/resolution receipt where applicable. Then durably rename the journal into a new sibling `operations/transactions/.settled/` namespace, synchronizing both source and destination parents plus new ancestors, before garbage collection. The certificate records the established rollback disposition; restart must not attempt to re-prove it by comparing against current files after later valid writes. A crash before rename leaves an intact classified journal; afterward the certificate classifies the settled evidence. Unknown/corrupt certificates stop cleanup and require inspection. Do not recursively delete an active journal as the first settlement step.

**Exit evidence:** an independent event trace proves file and directory barriers at each namespace change; injected failures at every barrier preserve a complete recoverable state and never produce premature success. Cover deletion, multiple new ancestors, recovery deletion, receipt publication and interrupted settled-journal cleanup. Extend transaction/recovery tests and the new durable-filesystem suite. A crash model may drop/reorder unsynchronized operations; label this simulated evidence separately from actual hardware power-loss proof.

### S2 — Close the demonstrated external-edit interval and preserve conflicts

1. Once the journal is durable, revalidate the complete captured prestate using direct uncached observations. Immediately before each apply/delete, check its expected preimage again. Cover absent targets, no-op targets and delayed operational-ledger writes as well as normal replacements.
2. If a preimage diverges, stop. For any rollback, restore only bytes the engine can prove it still owns; do not overwrite a foreign edit with either the proposal or the original preimage. Retain the journal and report recovery-required when ownership cannot be established.
3. Keep cooperative writer exclusion under the operator lock. Document that a noncooperating write between the final comparison and replacement remains outside that exclusion guarantee; do not market these checks as an atomic content CAS.

**Exit evidence:** deterministic barriers reproduce the original edit-after-journal schedule and verify that the learner text survives. Add variants before later writes, delete/no-op/absent targets, ledger publication and rollback. The independent byte oracle checks both intended and foreign bytes. A control with the new guard disabled must reproduce the old overwrite; sleeps alone are insufficient scheduling evidence.

### S3 — Remove argparse from application admission

1. Extend the existing request-contract module with a pure schema-derived normalizer. Validate raw payloads first, then apply the characterized bounded defaults and transport translations. Do not use JSON Schema `default` as implicit runtime behavior or revalidate enriched internal requests with the wire-only schema.
2. CLI parsing stays in adapters and continues to derive from the same request metadata. Replace direct stdin access in capture and stage/path/unit note handlers with a deferred typed text-input port: the CLI adapter owns the stream read, and the handler requests materialization at the existing point after its existing guards. A gateway implementation never reads a process stream; missing content produces an explicit typed refusal. Record the additive OpContext surface change. Inline structured JSON is not accidentally parsed a second time.
3. **Preserve revision representation in this slice.** Existing expected-revision strings are accepted request notation and parsed by a shared non-argparse function in the transaction module. Keep these values and each handler's current parsing/refusal site, including combined-invalid-input precedence. Removing parser construction does not require rewriting the revision consumers across fourteen handler files; that independent migration is deliberately excluded rather than hidden inside S3. Typed boundary views may wrap the existing notation without changing when it is validated.
4. Migrate gateway preparation and registered computation together, deleting the parser→Namespace→dictionary round-trip. Keep omission/null/false/list behavior, error ordering and content-bound file observations unchanged.
5. Verify registry coverage before removing dispatch fallbacks. The inspected inventory has 91 request schemas, 90 registered handlers, a direct `cli.capability` binding, and all 47 public command capabilities registered; the internal `goal.decision.record` exclusion is deliberate. Remove the unreachable legacy non-V2 gateway route and registry-miss/stdout-capture fallback only after independent coverage witnesses establish the remaining entry paths.

**Exit evidence:** parity for every current request action/default/choice and every public command capability; direct gateway invocation succeeds with parser construction deliberately unavailable. Invalid-target stage/path commands with missing text must refuse without reading stdin; gateway capture/note requests must never read stdin. Combined malformed revision/target/snapshot inputs retain their characterized refusal order. Extend gateway choice, CLI parity, request-schema, capability dispatch and operation-pipeline tests. No persistent normalization cache or new runtime dependency.

### S4 — Make commit decisions explicit

1. Introduce internal success/refusal alternatives carrying the exit-independent facts currently split between the return triple and `_GATEWAY_REFUSAL`. Include classification, issues, confirmation and trustworthy commit facts where applicable.
2. Migrate callers, then remove the tuple compatibility adapter and refusal ContextVar in the same slice. Do not remove unrelated authority/lock context merely because it also uses ContextVar.
3. Keep the existing outer Outcome and centralized public mapping. Preserve distinctions among no effects, committed, and uncertain; preserve post-commit receipt provenance. Snapshot, projection and rollback exceptions retain their meaning and are normalized once at the outer boundary.

**Exit evidence:** no error code depends on stale ambient state or message matching; sequential operations cannot leak classifications. Failure and interruption fixtures match existing outputs/effects outside the approved fixes. Extend operation-commit, typed-refusal and architecture-outcome tests. Do not change GatewayEnvelopeV2/ReceiptV2 to disguise an internal cleanup.

### S5 — Reduce commit policy states and return session logic to its owner

1. Replace `STANDARD | None | callable` phase choices with the three closed policies. Selection is capability-bound in application-owned code: a handler cannot substitute AI/goal policy for an ordinary capability, instantiate an arbitrary policy, or select which mandatory phases run. Handler parameters describe reviewed domain preconditions/effects. TransactionService retains mandatory validation, authority, journal, persistence, receipt and recovery ordering.
2. Preserve route/plan `validate_extra` behavior as typed domain preconditions, including warning and reviewed-revision gates. Preserve AI transaction-dependent writes as explicit transaction-bound effects. Prove AI validation/publication equivalence before sharing their implementation; completion and touched-path ownership remain distinct.
3. Preserve goal operations' intentional no-publication and session-path semantics. Keep inbox cleanup and AI completion after durable commit; failure there cannot imply rollback of an already committed transaction or authorize a second write.
4. Move receipt-based session-ownership repair from pipeline into existing `app/session.py`. Derive all receipt-authored states, validate all channel/session/shared-ledger ownership, then persist once. Never adopt merely observed current bytes as session-owned, reopen released sessions, or partially persist before all validations finish.

**Exit evidence:** the hook matrix becomes smaller and invalid combinations are unrepresentable. AI, goal, inbox, replay and session-transition effects remain equivalent. Extend A18's scanner to policy variants and transaction-bound effects before shrinking allowances: moving a callable into a new constructor is not removing it. Negative controls must detect arbitrary callbacks, custom policy instances and ordinary-capability/AI-policy substitution. Extend AI actions, goal proposals, session ledger, session scenario and architecture callback/write tests.

### S6 — Separate material retrieval decisions and strengthen internal models

1. Keep request checks, exact note/file reads, material observations and before/after snapshot guards in the application service. Pass explicit observed inputs to pure direct/related selection, matching, ranking and page shaping in derivation.
2. Preserve observation digests, including normalized filters, exact bytes and absence; direct/related membership, stable tie order, anchor/page ranges and continuation semantics must remain unchanged. Compute notes/assessments once per request; do not introduce a persistent cache.
3. Type normalized requests/results at the migrated boundaries and add narrow validated Unit/StudyMap/Route access where actually needed. Keep raw malformed/authored documents available to validation and lossless serialization. Correct inaccurate boundary annotations as consumers move; avoid a repository-wide object-model conversion.
4. Apply three specific additional separations, as individual subchanges rather than one mixed patch. In `sources.py::_plan_source_record_revise`, keep source-patch/material verification and registry serialization separate from approved-dossier impact/replacement/rebase planning in the new source-revision service; return typed planned dossier effects and guards, and retain one atomic source+dossier proposal. In `plan.py::_execute_plan_import`, extract a typed prepared-import/write-set value and preparation service; keep staged-basis/check-report/apply branches explicit and reuse existing `domain/plan_import.py` and `app/_plan_gate.py`. In `derive/validation/references.py::check_references`, build the shared route index once and call named entity-family methods in the same module in the original order, preserving diagnostic order and malformed-input handling. Do not create a generic validator framework or duplicate rules merely to shorten these functions.

**Exit evidence:** material results and observation tokens match on direct/related pools, ties, filters, pagination, missing notes and changed notes. Pure derivation can execute without filesystem access. Source/dossier changes remain one atomic proposal; import check/apply prepare the same write set and guards; ordered reference issues remain equivalent. Strict typing covers new modules and touched boundaries without broad `Any`, casts or ignores concealing errors. Extend material-context/boundary, source-record revision, compact-module revision, module warning-gate, curriculum and validation tests plus captured-world identity.

### S7 — Preserve generated UI types through the store

1. Use indexed generated manifest types for collection-specific accessors. Migrate unit/stage consumers first; keep the generic heterogeneous search path where its flexibility is required. Avoid an unconstrained `get<T>` that lets callers invent a return type.
2. Preserve first-match behavior, archive filtering, ordered stage authority, note/synthesis lookup and atomic replacement of manifest, identity map and indexes. Late results must not create mixed-generation views.
3. Keep runtime validation at ingress and contextual bindings in consumers. Reduce redundant decoding only after generated types and runtime requirements both cover it.

**Exit evidence:** type-negative cases reject wrong fields without assertions; real manifest fixtures retain current navigation and ordering. Existing index tests stub validation, so add real-validator coverage rather than treating those stubs as wire proof. Run UI type/contract/index checks and paired real-Core fixtures.

### S8 — Verify that displayed projection bytes are current

1. Factor a shared freshness predicate from existing identity/reuse checks. Add read-only `projection.status` returning `current | stale | unavailable`, exact raw manifest SHA-256, relevant snapshot, check time and bounded reason. Reuse canonical, producer/runtime, operations, material and date dependencies already checked by Core; do not create a competing UI freshness algorithm.
2. UI loads and validates a candidate off to the side, then compares the hash of its exact bytes with Core's verified hash. Snapshot equality alone is insufficient. A result for one manifest must never authorize another candidate. Replace the current failed-load behavior that clears the store: a corrupt/missing refresh retains the last validated data/indexes/identity map, marked stale/unverified, and only a complete candidate can replace them atomically.
3. While checking, retain readable cached content visibly awaiting verification. Stale/unavailable state preserves navigation and drafts but disables ordinary learner mutations/currentness claims. Keep a finite maintenance/recovery lane for projection generation/verification and `recovery.inspect`/`recovery.resolve`, even when the projection or pending-write gate blocks ordinary writes. These operations retain their own evidence, lock and approval requirements; this is not a generic bypass flag. On confirmed stale state, generate through the existing projection operation once, reload and verify once. `fresh_manifest_and_repo` may rebuild only in memory, so calling it alone does not repair the published file.
4. Coalesce startup/focus/explicit refresh/settled-mutation invalidations. Subscribe to available canonical/operations/material file events and invalidate at midnight; events mark suspect, while Core establishes proof. Scope subscriptions to the actual manifest-input inventory, excluding diagnostic traces and generated/cache/temporary output churn; a status query must not invalidate itself by writing a diagnostic trace. Add a proposed 60-second maximum active verification age to cover missed events while the app remains focused, using one coalesced active check rather than one per render. Use generation tokens to ignore late older responses. Set a proposed five-second foreground verification deadline, then show unavailable/retry while retaining cached content; an older result cannot authorize a newer generation. No extra Core call per component render or local navigation, no retry loop, and no blanking the last useful view when freshness checking fails. Gate ordinary writes centrally by operation kind/policy, not blanket `plugin.mutate()`, which also wraps generation and read-only review.

**Exit evidence:** the old-valid-manifest probe is reported stale. Test same canonical snapshot with changed operations, producer identity, material state or date; a good load followed by corrupt/missing refresh; external edits while continuously focused; midnight; dropped watcher events; Core unavailable; slow response arriving after a newer load; and rebuild failure. Verify repair/recovery remains accessible while ordinary writes are gated. Use actual Core and the production validator. Record time-to-verified separately from initial cached rendering, plus idle verification IO/CPU cost.

### S9 — Add reviewed recovery with a durable late-request fence

1. Add `recovery.inspect` and approval-gated `recovery.resolve`. Normal operator-lock acquisition currently reconciles inflight journals before yielding; a conflict can therefore block inspection. Provide a narrow recovery coordinator path that acquires the same exclusive mutex but performs bounded read-only inspection before automatic reconciliation. Track this as a distinct recovery context, not ordinary exclusive authority: reentrant/nested ordinary dispatch must refuse until the coordinator has established the required recovery state. This is a finite operation policy, not a public skip-recovery switch available to ordinary handlers. Refuse resolution if unrelated armed journals remain unreconciled and outside the reviewed evidence inventory.
2. Inspection binds the exact saved envelope/intent, request/key/channel, approval identity, journal/receipt hashes, affected path hashes, current snapshot and proposed resolution into a plan hash. Build the resolution approval from that fresh inspection's snapshot/evidence, not the stale UI manifest; the maintenance lane still binds approval to current Core facts. Changed evidence invalidates that plan. Inspect contradictions, malformed records and partial evidence explicitly; absence of a row or journal does not prove historical non-execution.
3. If valid evidence proves commitment, settle that existing transaction. If a journal proves safe rollback, use guarded engine recovery. If the original outcome remains uncertain, allow an explicit reviewed acceptance of the reconciled current state plus retirement of future execution. Any content merge/reapplication is a separate visible, scoped approval; never silently re-sign the old action.
4. Store retirement in **idempotency ledger storage v2** with discriminated committed/retired entries. Read v1 losslessly; upgrade only when first needed. Preserve existing receipt bindings. Add receipt-bound semantic transition metadata containing storage versions before/after, whole-ledger hashes before/after, and the original key's absent→retired row effect/hash, alongside the normal resolution-key binding. Historical proof reverses both logical effects, then uses the recorded historical serializer at the v2→v1 boundary, checking every reconstructed hash and rejecting unexplained rows. Verify retirement through its resolution receipt and transition; a bare retired status is not authority. Update every ledger consumer, diagnostics and historical-evolution proof. A sidecar ignored by older Core is insufficient.
5. Add an explicit **engine-owned accepted-journal settlement effect** binding original journal identity/digest, selected current-state hashes, resolution identity and its committed receipt. The current engine supports file writes/deletes; do not assume a directory rename is already a journaled effect. Before any resolution ledger/canonical effect, durably wrap every referenced original active journal in a self-contained **journal storage v3** intent preserving its exact legacy intent bytes/hash and backups; use v3 for the resolution's own journal too. The inspected old reader rejects unknown journal versions before restoration, preventing it from undoing accepted originals even before it encounters ledger v2. Publish wrapper changes atomically with S1 barriers.
6. New recovery classifies the resolution/original dependency before generic undo: without a valid resolution receipt, first recover tentative resolution effects, then apply ordinary guarded original recovery using the retained legacy intent; with a verified resolution receipt, honor its settlement decision and never undo the accepted original state. Contradictory evidence blocks with all journals retained. Produce the S1 settlement certificate and move journals to `.settled` only as recoverable post-receipt cleanup. Test the actual old source revision at every interruption boundary. No resolution effects may begin until **all** referenced wrappers are durable; after that barrier old Core must refuse without canonical mutation, including between receipt and cleanup. Before that barrier, ordinary guarded original recovery is permitted and invalidates the reviewed plan; this includes interruption between multiple wrapper conversions. Old recovery may invalidate a disposable projection, which is distinct from canonical mutation.
7. Merge the retirement semantic ledger change with the resolution command's own idempotency binding in the same journaled transaction. Require a distinct resolution request ID/key; reject using the original key, so the resolution binding cannot replace its own retirement fence. Do not have a handler independently rewrite `idempotency.yaml`, or submit two competing raw writes to that file. The resolution obtains its own ordinary ReceiptV2; it does not fabricate a receipt for the uncertain original action.
8. Under the same exclusive lock, check a retired key before any original handler execution or replay miss can proceed. Bind the tombstone to the original identity/intent, preserve normal key-collision refusals, and persist it indefinitely. Operational metadata is outside the canonical fingerprint, so the explicit fence is required even if an old approval's canonical snapshot still matches. Add a typed terminal refusal through the central mapping and deliberately approve the additive public contract change.
9. Version the UI pending-record format with lossless v1 migration. Show “Review unfinished write,” the inspected evidence and the exact resolution. **Before sending resolution**, persist and await a `resolving` state containing both the untouched original record/draft and the exact sealed resolution envelope/plan identity. A failed preparatory save sends nothing. On restart replay that exact resolution or re-inspect its terminal evidence; never resume the original action from a resolving record. After Core confirms resolution, archive the original pending record with its receipt and clear the active slot in one awaited settings save, preserving the draft. A failed final save/restart must converge by replaying the persisted resolution. Migration and failed-save cases must retain both envelopes without a second active learner write.
10. Malformed saved records retain their raw bytes. Missing identity cannot be handled by blind discard: expose a bounded diagnostic/export path and require a Core plan tied to verified identity before any retirement. Unknown identity may remain blocked while the user can recover/export the draft; do not invent an all-clear.

**Exit evidence:** the original unsent-capture/stale-snapshot case becomes reviewably resolvable. Cover already committed, rolled back, genuinely unknown, contradictory and malformed cases; a delayed original racing before/during/after resolution; key aliasing and same key/different intent; failed UI save; crash during v3 wrapping, before/after resolution receipt and during settlement; retained draft; and duplicate resolution replay. Attempt ordinary nested dispatch inside recovery context and require refusal. Verify exactly one terminal decision, no duplicate original effects, no undo of accepted state and no fabricated history. Actual old Core must refuse protected v3 journals before canonical mutation and v2 ledger writes afterward. Exercise old/new backup/restore, later valid writes and receipt-history inversion across both storage transitions.

### S10 — Prove the whole pair and prepare controlled rollout

1. Run the complete paired gate on the exact final source pair, independent adversarial suite, captured-world comparisons and performance comparison. Investigate all unexplained deltas; do not refresh golden files merely to make them match.
2. Independently review actual production code and dataflow: one normalization owner, one final classification, closed policies, exclusive retirement fence, no second writer and no hidden retry loop. The reviewer must trace code and effects, not infer architecture from passing tests.
3. Exercise actual Obsidian workflows in a disposable vault: startup, external source change, refresh, navigate unit/stage, read note/material, reviewed edit, interrupted write, reviewed resolution and restart. Verify source, built bytes, loaded runtime and interaction separately.
4. Keep release installation/publication as a later explicitly authorized step. Before any approved live transition, capture a restorable backup, record the source pair and verify the installed and running pair. Do not navigate/replay a production pending write as part of an automated smoke check.

**Exit evidence:** exact-pair receipts, effects comparison, independent review, timing distribution, disposable-vault interaction record and restore receipt. Report unavailable proof separately. No acceptance from a build alone.

## 4. Risks, compatibility and rollback

| Risk | How it would show | Containment / rollback |
|---|---|---|
| Defaults or adapter conversion change | Omitted/false/empty inputs differ, approval intent or errors drift | Exhaustive current-schema parity before removing old normalizer; rollback source slice before storage v2. |
| More types merely hide behavior behind casts | Compiler green while runtime shapes differ | Runtime validation retained; negative type cases; reject broad casts/ignores at new boundaries. |
| Extra disk synchronization is slow or fails | Higher write latency, ENOSPC/EIO or unsupported barrier | Measure actual platform; preserve recoverable state on failure; never skip required barriers to pass a budget. |
| Conflict detection misses a hostile final instant | Arbitrary editor writes between check and replacement | State cooperative-lock limit explicitly; preserve detected conflicts. Full arbitrary-writer exclusion is not claimed. |
| Extraction changes material/session meaning | Ranking, continuation digests or session-owned paths drift | Exact effect/digest comparisons, shared-ledger and released-session adversarial cases; small independently reversible slices. |
| UI freshness introduces stalls or stale races | Waiting forever, mixed generations, blank views or late authorization | One bounded check/rebuild cycle, timeout/unavailable state, readable cached data, generation tokens. |
| Recovery bypass weakens ordinary safety | Normal handlers run with unresolved journals | Finite recovery-only lock policy, explicit architecture witness, negative test ordinary operation cannot select it. |
| New retirement/settlement ignored by an older Core | Retired original executes, or old recovery undoes accepted state | Journal v3 protects active originals before effects; ledger v2 protects later admission; actual old-reader compatibility checked at every crash boundary. |
| Ledger v2 invalidates old receipt proofs | Older exact replay or history verification refuses | Version-aware historical reconstruction and old-receipt replay fixtures; no live upgrade before these pass. |
| Crash during UI/archive or journal cleanup | Slot lost, draft lost, partial journal treated active | Atomic settings save; replayable Core resolution; durable settlement rename; fault injection at transitions. |

Before S9, rollback can restore a prior coherent source pair while preserving learner data and operational evidence. The S9 rollback boundary begins at the **first durable active-journal v3 wrapper**, which can precede ledger v2: code-only downgrade is no longer valid then. Keep a compatible reader/fence, or remain safely blocked. Restoring an old data backup alone can also resurrect a retired request, so restore procedures must retain/reconcile later retirement evidence before reopening writes. If that evidence is unavailable, remain blocked rather than infer safety from an old backup or the absence of an old process. Never delete tombstones or strip journal wrappers to make an older version run. Backup and restore compatibility is a required acceptance test, not a documentation afterthought.

All public additions, error variants and intentional fixed behaviors must appear in an explicit surface-delta packet. Do not silently regenerate the approved surface, warning baseline or ratchets. The current planning request does not grant installation/publication authority.

## 5. Verification and performance acceptance

### Verification strategy

Use three different forms of evidence: production-source review; independent filesystem/wire/ledger observations; and the existing tests. The independent observer freezes its own effect inventory and must not decide success through production error classification. Include child-process and pre-opened-descriptor witnesses. Controls that disable the guard, omit a directory flush, accept a stale manifest or bypass the retirement fence must make the corresponding harness fail. Keep controls in disposable worlds only.

Schedule races with process barriers at named boundaries, not timing guesses. Inject exceptions, ENOSPC/EIO and process termination before and after journal, apply, receipt, ledger, post-commit completion and UI-save boundaries. For power-loss modeling, record the assumed persistence/reordering model and enumerate its admissible recoveries. Preserve uncertainty rather than asserting physical hardware proof from a killed process.

### Commands

Run commands from the **isolated candidate Core checkout** with its sibling candidate UI. The following existing commands were verified in the inspected source; they do not imply permission to run generation/stress against the live repository.

```sh
.venv/bin/python tools/capture_world.py --root . --out /private/tmp/los-hardening-world
.venv/bin/python tools/compare_world.py --world /private/tmp/los-hardening-world --baseline 074f4717e14527798752de84b3c9c4e88348b658 --candidate WORKTREE
.venv/bin/python -m pytest -q tests/test_transactions.py tests/test_recovery_conflicts.py tests/test_gateway_v2.py tests/test_evidence_parity.py tests/test_ui_gateway_recovery.py
.venv/bin/python -m pytest -q tests/test_ops_pipeline.py tests/test_ops_commit.py tests/test_gateway_typed_refusals.py tests/test_gateway_choice_parity.py tests/test_arch_cli_parity.py tests/test_capability_dispatch.py tests/test_arch_request_schemas.py tests/test_arch_outcomes.py tests/test_arch_callbacks.py tests/test_arch_writes.py
.venv/bin/python -m pytest -q tests/test_material_context.py tests/test_material_context_boundaries.py tests/test_manifest_reuse.py tests/test_session_ledger.py tests/test_scenarios_session.py tests/test_ai_actions.py tests/test_goal_proposals.py
.venv/bin/python -m pytest -q tests/test_source_record_revise.py tests/test_compact_module_plan_revision.py tests/test_module_plan_warning_gate.py tests/test_curriculum_v2.py tests/test_validation.py
.venv/bin/lint-imports --no-cache
make code-check
npm --prefix ../obsidian-ui run typecheck
npm --prefix ../obsidian-ui run contract:check
npm --prefix ../obsidian-ui run test:manifest-store-indexes
.venv/bin/python tests/benchmark_runtime.py --samples 5
.venv/bin/python tests/benchmark_agent_reads.py --samples 5
make system-check
```

Use only relevant focused families during each slice; run the full paired gate for accepted milestones and final source pair, and rerun when subsequent shared changes invalidate its receipt. Register all new Python tests in `tests/group_map.py` and new UI tests in package checks; do not let a new test become invisible to release verification. New modules must pass strict mypy under the existing ADR policy. Do not widen strictness to the entire legacy tree during this work.

The existing world comparison proves projection identity, not all write/recovery/UI behavior; the independent scenarios supply those missing dimensions. Its production-root imports likewise do not replace the independent effect inventory. `make system-check` builds the sibling UI and writes a verified-pair stamp. The stress tool republishes generated outputs and belongs only in disposable candidate state.

**NEW runner interface to implement in S0/S10:**

```sh
.venv/bin/python tools/benchmark_hardening.py --world /private/tmp/los-hardening-world --baseline 074f4717e14527798752de84b3c9c4e88348b658 --candidate WORKTREE --warm-samples 50 --cold-samples 20 --out /private/tmp/los-hardening-performance.json
.venv/bin/python -m pytest -q tests/test_durable_fs.py tests/test_request_normalization.py tests/test_projection_status.py tests/test_recovery_resolution.py tests/test_architecture_hardening_adversarial.py
```

The new runner executes writes only in disposable copies. “Cold” means a fresh process with the application cache state controlled and reported; do not pretend it means a flushed OS/device cache. Alternate baseline/candidate runs on the same machine and pinned world, report p50/p95, peak RSS, input/output volume and variance, and rerun unstable comparisons. Record hardware, filesystem, Python/Node versions and observation clock. Existing runtime/read benchmarks are useful reference measurements but do not cover fresh brief startup, writes/replay or UI verification.

### Proposed performance budgets

These are technical acceptance decisions, not measured claims about the candidate. **ASSUMPTION:** the current world and machine are representative; add a bounded larger synthetic world to expose repeated work and scaling failures.

| Path | Acceptance budget relative to same-world baseline |
|---|---|
| Existing interactive Core reads, warm and fresh-process | p95 increase ≤ max(15%, 100 ms); unchanged result size outside approved deltas. |
| Check/apply/replay including stronger persistence | p95 increase ≤ max(25%, 300 ms); attribute extra synchronization separately. |
| UI local navigation/render | No new Core round-trip; p95 increase ≤ max(10%, one 16 ms frame). |
| New warm freshness verification | Proposed p95 ≤ 1 second on the user's measured machine; cached content remains usable while checking. A stale rebuild is measured against existing generation separately. |
| Peak memory for existing workloads | Increase ≤ max(10%, 16 MiB); no full-repository duplicate model per interaction. |
| Active background freshness checks | At most one coalesced check per 60-second expiry, excluding input-triggered invalidation; proposed average CPU overhead ≤ 2% of one core, with IO reported and no repeated generation for a current manifest. |

If a budget fails, locate repeated IO, extra loading or duplicated computation first. Optimize inside the current dependency/derived-state model only with independent warm/cold identity proof. If a necessary durability barrier exceeds the budget, report the actual cost and a concrete design tradeoff; do not weaken persistence, global validation, approval or conflict handling. An unexplained user-visible regression blocks acceptance even if the aggregate budget passes.

### Observable definition of done

The original completed external-edit schedule preserves foreign text and refuses or recovers explicitly. A never-sent stale request can be reviewed, retired and replaced with a newly approved request without losing its draft or allowing the original to execute late. Persistent namespace changes have ordered barriers and a tested recovery model. An old valid projection is visibly stale until its exact bytes are verified. Gateway admission no longer constructs a CLI parser, commit classification no longer requires ambient refusal state, proposal policies are closed, and material/session responsibilities have explicit owners. Unchanged workflows, provenance, receipts, session scopes and public output are independently equivalent, with measured performance inside the stated budgets or an explicitly reviewed exception.

## 6. Out of scope

- Implementation during this planning task; production installation, source commits/pushes, publication and live learner-write experiments.
- Canonical learning-content changes, semantic rewrites, identity changes, mastery judgments, quarantine changes, legacy edits or Stratum traversal.
- Replacing file storage with SQLite, adding a server, a new runtime framework/dependency, a policy plugin system or a repository-wide object-model rewrite.
- Perfect isolation from arbitrary noncooperating editor writes, or universal hardware power-loss guarantees without platform/device evidence.
- Automatic dismissal of uncertain requests, automatic reapproval/reapplication, deletion of recovery evidence or weakening global validation.
- New persistent caches, unrelated performance tuning, weakening existing gates, deleting useful tests or a line-count cleanup campaign.
- Agent-role assignment, historical campaign takeover and closure of unrelated critique points.
