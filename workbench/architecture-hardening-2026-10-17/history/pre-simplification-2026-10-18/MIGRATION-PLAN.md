# Integrated reliability migration plan

18 October 2026. **Proposed execution contract; planning only.**

## 1. Understanding

Finish the interrupted verification, integrate the claim-admission and scan
changes, then harden the transaction/read/recovery boundaries without losing
learner work or provenance. Establish the hardening behavior baseline only
after the intentional claim changes have passed their gate. Minimize elapsed
time and agent context by reusing evidence, sharing implementation and running
full verification at three meaningful milestones; correctness and existing
acceptance requirements remain unconditional.

### Evidence and authority

The seven pending planning checks are closed in
[VERIFICATION-2026-10-18.md](VERIFICATION-2026-10-18.md), with runnable probes
and machine-readable results beside it. They revealed required implementation
changes, not seven automatic confirmations.

Current inspected pair: Core `074f4717e14527798752de84b3c9c4e88348b658`, UI
`a88b1188ad54439b4df32813904de182c06a105c`; both clean. The enclosing
semestercontext tree has unrelated dirty/untracked work, which is excluded.
No implementation start or hardening behavior capture is recorded in these
plan directories. **ASSUMPTION:** no other session is implementing elsewhere;
check ownership/active writers before execution. Process enumeration was
unavailable in this sandbox, so this pass does not establish quiescence.

Detailed slice specifications remain authoritative by reference:

- [Anchor admission](../verbatim-anchor-admission-2026-10-18/PLAN.md), V1–V8.
- [Scan in workflow](../scan-in-workflow-2026-10-18/PLAN.md), D1–D13 and steps 0–7.
- [Architecture hardening](PLAN.md), S0–S10, as amended by [its review](PLAN-REVIEW.md).

This document decides their order, shared seams and acceptance schedule.
Its explicit amendments below govern conflicts between those specifications;
unchanged details are referenced, never copied. Existing OPERATOR, architecture,
workflow, A11/A17, A19 and warning-baseline contracts continue to bind.

### Migration decisions and reasons

**M1 — Finish both claim source changes before hardening S0.** Land the anchor
rules and scan behavior in one coherent candidate before recording hardening's
equivalence baseline. Reason: they intentionally change imports, reports,
goals and the very handler S6 later extracts. If another implementation already
owns S0, coordinate its baseline explicitly before editing shared files; do not
silently compare against the obsolete baseline.

**M2 — Share admission and prepare the ledger guards before reporting.**
Propose **NEW** `tools/learning_os/app/claim_admission.py` as the common
application owner for per-claim evidence admission and planned lineage effects;
move existing Phase B behavior into it without retaining duplicate rules.
Use the anchor plan's domain matcher/store reader for their respective jobs.

The admission set is the union of coverage/material-identity changes and
explicit evidence for unchanged claims currently stale or disputed. Run quote/
manifest/remote classification on every admitted nonempty claim, including an
evidence-only re-judgment; withdrawals keep their separate absence semantics.
Fresh unchanged and unrecorded unchanged claims retain the backfill refusal.
Enforce unit scope before selecting unchanged re-judgments from an assembled
module map. Reason: this satisfies both plans without creating a repair bypass.

Prepare the prospective touched-path set at check time, including lineage,
without requiring a fabricated admission identity or pre-writing the ledger.
Derive one artifact set for check/envelope/apply/receipt: normal logical owners
plus `file:operations/transactions/lineage.yaml` whenever lineage is written.
Use that explicit shared file artifact for **all four current lineage writers**
and for route-patch if enabled. Keep generic `transaction_artifacts` fallback
semantics unchanged. Reason: an intervening synthesis/import from another unit
must invalidate a reviewed whole-ledger replacement too.

The evidence-only case changes the ledger and its file revision, not unit or
module bytes/revisions. Do not treat it as a no-op. Update
`tools/verify_plan_receipt.py` to accept empty ordinary-write hashes only when
the correctly bound receipt/report writes lineage alone; preserve all ordinary
hash, artifact, receipt and replay checks. Exercise evidence-only check/apply,
intervening writes from every writer, exact replay and verification end to end.

**M3 — Include V7 in the complete target, with an explicit authority amendment.**
Prepare evidence-bearing route-patch using M2, add its lineage write grant and
A19 ownership entry, and bind the ledger in the same transaction. Its preflight
must validate evidence as well as the staged structural rules. Reason: leaving
the common light edit path open retains a demonstrated admission gap. If the
surface amendment is not approved, finish the independent V1–V6 work, but label
route-patch anchoring **deferred**, not fully migrated. No approval is implied
by this planning request.

**M4 — Keep status, anchoring and sampled review distinct.** Show unrecorded
claims as unrecorded and remote existence-only claims as unanchored. Existing
claims are not retroactively anchored; do not bump a lineage contract version
merely to force all 128 through the new check. The 786 unrecorded routes remain
outside the audit population. Reason: a smaller queue cannot manufacture
evidence or mean all curriculum coverage has been verified.

**M5 — Freeze and seed an audit before reviewing it.** Amend scan D9: when an
audit is explicitly authorized, verify and store the complete current pool,
its basis pairs and digest; then draw a fresh system-random seed and store it
with the resulting 30-claim sample in that same reviewed ledger decision.
Use a seeded shuffle of the canonically sorted pool; record the sampling
algorithm/version so replay reproduces it. Bind that pool/seed/sample into
the decision's existing reviewed hash before apply; do not redraw on replay.
Prepare the pool/seed/sample authorization file outside Core, then use
`--authorize --audit-file FILE --check` and its reviewed hash for apply; the
handler validates the still-complete pool and reuses the supplied seed.
The read-only detector emits a pool ID; it does not draw on every scan.
Close through `--audit-file` only against that authorized audit, with exact
sample, report digest, reviewer and defects. Changes after authorization do
not certify new bases; retain the historical basis pairs. Reason: this closes
both arbitrary-subset certification and the unstated random-sampling assumption.
No extra CLI flag or separate audit service is needed. Reviewer independence
is an attestation and workflow requirement, not a property the seed proves.

**M6 — Measure decisions honestly.** Quieting uses the latest explicit decision
per goal occurrence, with stable ordering for equal dates; repeated authorizing
then closing does not add two observations. `authorized` means accepted intent,
not proof of completed work. Retain scan D10's minimum sample, Wilson lower
bound, reset rule and full-output visibility. Reason: the ledger replaces the
decision for an ID, and silent fixes supply no measured outcome.

**M7 — One surface packet per acceptance boundary.** Prepare exact candidate
diffs, then obtain any required dated approval; never invent Aram's line.
The scan packet changes `cli.goal` and
`request_schemas.goal.decide.schema.json`. V7 additionally changes the route-
patch CLI/request/catalog keys measured in the verification report. Hardening's
operation, error, storage and OpContext changes need their own concrete packet
at their milestone. Generate capability schemas before capturing surface and
scenario baselines. Reason: approvals are single-use against actual deltas;
early guessed approvals or repeated regeneration waste review and can hide drift.

**M8 — Three full gates, focused tests between them.** Use C1 after combined
claim source changes, C2 after hardening S1–S2, and C3 at S10 after S3–S9.
Retain every slice's negative controls, targeted checks and independent effects
evidence; any unexplained shared-boundary failure justifies an earlier full
gate. Reason: the full pair is expensive, while three coherent boundaries cover
new behavior, engine correctness and final integration. This does not waive a
required gate or reuse a receipt after relevant source/input drift.

**M9 — Model recovery before crossing its format boundary.** Add a bounded
executable state model to S9's adversarial tests, covering original-journal
protection, tentative/committed resolution, ledger version, settlement and UI
pending/resolving/archive states. Enumerate interruptions and delayed-original
delivery; assert the hardening plan's invariants, then connect counterexample
traces to production fault tests. Use the existing Python test runtime, with no
new modeling dependency. Reason: this is the finite protocol where exhaustive
state exploration earns its cost; it supplements actual old-reader tests.

**M10 — Separate source acceptance, content migration and live rollout.**
Repair the 21 claims and run the sampled audit only after the final source pair
is accepted and content application is authorized. Prepare each unit's evidence
once from pinned material; review and apply sequentially, refreshing guards
after each receipt. Reason: speculative live repairs would change the world
being hardened and require repeated content judgment. Gate source behavior on
captured/synthetic worlds first, including both stale and repaired states.
Installation/publication and uncertain-write resolution remain separate explicit
actions; a source gate does not authorize them.

## 2. Files affected

`Core` below is `/Users/aramaljanadi/Desktop/semestercontext/LearningOS/repository`;
`UI` is `/Users/aramaljanadi/Desktop/semestercontext/LearningOS/obsidian-ui`.
The three source plans' file inventories remain the full concrete inventories;
the following are the integration additions/amendments to those inventories.

| Path relative to Core unless stated | Why |
|---|---|
| `tools/learning_os/app/claim_admission.py` (**NEW**) | Own shared claim admission/planned lineage effects before later import extraction. |
| `tools/learning_os/app/handlers/plan.py`, `tools/learning_os/app/handlers/routes.py` | Use that owner and prepare identical check/apply path and guard sets. |
| `tools/learning_os/app/handlers/synthesis.py` | Include the shared lineage artifact in publication as well as restamp guard derivation. |
| `tools/learning_os/domain/plan_import.py`, `tools/learning_os/app/_plan_gate.py` | Preserve logical-owner semantics while reports include prospective ledger effects. |
| `tools/verify_plan_receipt.py`, `tests/test_unit_plan_revision.py`, `tests/test_phaseB_prospective_lineage.py`, `tests/test_vnext_boundaries.py` | Prove ledger-only receipts and interposed shared-writer changes without weakening ordinary-write verification. |
| `system/contracts/capabilities.yaml`, `tests/architecture/operational-owners.yaml` | Deliberately grant and audit route-patch's additional ledger write. |
| `tools/learning_os/derive/semantics/goals.py`, `tools/learning_os/app/handlers/goals.py`, `system/schema/goal-ledger.schema.json` | Bind authorized audit pool/seed/sample and count decisions once. |
| `tests/test_arch_idroundtrip.py`, `tests/test_arch_cli_parity.py`, `tests/test_cli.py` | Cover both emitter helpers and changed flag behavior while preserving historical corpus pins. |
| `tests/architecture/cli-parity-baseline.json`, `tests/architecture/cli-parity-corpus.json`, `tests/architecture/surface.json`, `tests/architecture/surface-approvals.yaml` | Update only approved changed command rows, observations and actual surface keys. |
| `tests/test_architecture_hardening_adversarial.py` (**NEW in hardening**) | Add the bounded recovery model and production witnesses for its transitions. |
| `UI/scripts/generate-responses.mjs`, `UI/src/contracts/generated/*` | Use the existing generator only when a real UI-response schema closure changes; V7 alone does not establish a request-type regeneration task. |
| `operations/transactions/lineage.yaml`, `operations/goal-ledger.yaml` | Governed post-acceptance content/audit effects only; never direct document edits. |

Publication, lineage persistence and replay coverage is in
`tests/test_vnext_boundaries.py`; extend it rather than creating a duplicate
publication test family.

## 3. Steps and independently checkable exits

1. **E0 — Reconcile and capture once.** Check exact tips, dirty files, active
   writers/ownership, disk and governing contracts. Create one isolated sibling
   Core/UI candidate pair and one quiescent captured world. Record source/data/
   material digests and interpreter versions. Save a compact evidence index
   naming each slice's changed paths, receipt and next step. Exit: reproducible
   baseline and no overlap with another writer; no live mutation.
2. **E1 — Build the shared claim slice.** Apply M2 and anchor V1–V6, scan
   steps 1–5, M5/M6 and V7/M3 as one coherent patch series. Retain anchor V5's
   broadcast replay and disabled-guard controls; add evidence-only repair and
   all-writer interleavings. Batch schemas/docs before one surface/parity/
   transcript update. Exit: focused families, two-field report compatibility,
   complete emitter coverage, no persisted excerpts, approved exact surface
   packet, real-material checks and read/anchor timing.
3. **C1 — Accept claim source behavior.** Run one full paired gate plus the
   combined independent scenarios. On the pinned baseline the predicted queue
   is 25 goals/5 groups after code, 4 after valid repairs, then 3 after a clean
   audit. Those are conditional fixture/captured-world expectations, not live
   results or permission to make a clean audit. Defects remain visible and are
   repaired, not reclassified to hit a number. Exit: reviewed candidate pair,
   actual effects and timing receipts; V7's residual status explicit.
4. **E2 — Capture hardening S0, then S1–S2.** Baseline the accepted C1 pair,
   adding its intentional claim deltas to S0's allowlist. Reuse E0's observer
   and captured inputs; create new measurements only for changed behavior.
   Implement durability and foreign-edit protection in the prescribed order.
   Exit: original defects reproduced on baseline and prevented on candidate,
   negative controls fail as intended, barriers/conflicts preserve evidence.
5. **C2 — Accept the engine corrections.** Run the full paired gate and S1–S2
   adversarial/effects checks. Exit: coherent durability/conflict candidate with
   measured overhead; no recovery-format cutover yet.
6. **E3 — Execute S3–S8 with focused gates.** Preserve each specified boundary
   and refusal order. S6 extracts prepared import using M2's settled claim owner;
   no second Phase B implementation. S7/S8 use actual Core/validator fixtures.
   Exit: per-slice code/effects/type receipts and measured reads/UI freshness,
   with approved OpContext/operation changes where applicable.
7. **E4 — Execute S9 only after its protocol gate.** Review the finite model,
   production interruption traces, actual baseline-reader behavior, old/new
   backup/restore and inverse receipt-history proofs. Preserve exact original
   and resolution envelopes before dispatch. Exit: all S9 witnesses pass in
   disposable worlds; the first durable v3 wrapper remains the explicit
   downgrade boundary. No code-only rollback across it.
8. **C3 — Final source acceptance (S10).** Run the final exact-pair gate,
   independent implementation review, effects comparison, performance comparison
   and disposable-Obsidian interactions. The reviewer must inspect production
   dataflow, not only results; Aram assigns any separate reviewer role. Exit:
   final source/build/runtime/interaction evidence, restore receipt and remaining
   unavailable proof named. A same-session review cannot satisfy independent
   review or audit attestation.
9. **E5 — Authorized content migration.** In the accepted pair, prepare the
   21 current claims across the 10 units listed in the scan plan, with actual
   source judgments and M2 admission. Apply each reviewed unit sequentially,
   verify its receipt immediately, retain supersedes history and learner state,
   then authorize/freeze the 128-claim audit pool and review the 30 sampled claims.
   If state changed, derive the real pool/count rather than forcing 128. Exit:
   no stale claims among those repaired; a clean audit closes only its frozen
   pool, while defects trigger governed repair. Never sample repeatedly to
   discard an unfavorable result.
10. **E6 — Authorized rollout.** Use a restorable backup and the approved exact
    pair; verify installed bytes, loaded runtime, safe interactions and restore
    compatibility. For an authorized publication, obtain the required branch,
    main and release-pair CI receipts on the exact SHAs; a local pair stamp is
    not a remote CI receipt. Preserve live pending drafts/envelopes; do not replay them
    for a smoke test. Exit: distinct source, content, install and runtime
    receipts, or an explicit incomplete/deferred status for the missing stage.

## 4. Risks

| Failure | Observable symptom | Containment |
|---|---|---|
| Independent writers invalidate a whole-ledger replacement | Interposed publication survives a supposedly fresh check | Shared file revision on every lineage writer; exact check/apply/replay witnesses. |
| Reports look sound but ledger-only apply/verifier refuses | Empty guards/hash map or false no-op | M2 end-to-end receipt test; retain ordinary-write negative controls. |
| New admission can be bypassed during repair | Stale claim becomes supported on locator-only evidence for a local PDF | One admission set and matcher for edits and unchanged re-judgments. |
| Audit overstates statistical or semantic evidence | Deterministic/arbitrary subset presented as population proof | Authorized full pool, post-freeze seed, bound sample and honest reviewer attestation. |
| Snapshot/fixture regeneration hides unrelated drift | Diffs outside decided responses or guards | Batch once, classify every diff and retain old counterexamples. |
| Candidate source cannot read its old recovery evidence | Historical replay/restore fails or old Core undoes accepted state | Actual old-reader witnesses and S9 format gate before live cutover. |
| Efficiency shortcuts erase required evidence | Green suite without byte/receipt/runtime proof | M8 reuse by exact inputs only; independent effects and interactions remain mandatory. |

## 5. Verification and efficiency contract

Run from the isolated candidate Core with its sibling UI. During slices use
the named focused commands in the three specifications; do not repeat their
overlapping test lists simply because two documents name them. C1/C2/C3 each
run the complete required pair check once:

```sh
PYTEST_ADDOPTS='-m "not live_install"' make system-check
```

Also run the current slice's tests/negative controls, zero-error validation and
warning-baseline check; strict mypy on new modules and UI type/contract checks
remain required as specified. Register new tests in the existing Python/UI gate
maps. A planning pass is not a reason to run the whole implementation suite.

Use hardening §5's timing budgets; its runner is **NEW to implement**, not an
available tool today. Reuse the same captured world and alternate baseline/
candidate measurements. For read annotations, start with 20 paired runs from
the scan plan, increasing only for noisy or borderline results. Measure quoted
admission by unique file/page/window and memoize within one request; no new
persistent cache. Record input/output bytes alongside latency so token cost is
visible. A necessary correctness barrier is not removed to meet a budget.

Keep one compact execution ledger/evidence index in this workbench, with exact
pair/input digests and links to raw receipts. Read only the next slice and
affected contracts after a handoff; do not reload all three plans or re-run
unchanged historical probes. Run independent read-only checks concurrently when
safe; keep mutations, schema generation, recording and acceptance sequential.
No agent delegation is assumed or authorized by the historical roles.

**Acceptance condition:** no unexplained regression, lost authored bytes,
weakened gate, fabricated approval/audit, or unprotected format downgrade.
Re-use a receipt only for the exact source pair and relevant inputs it proves.
If a budget fails, diagnose repeated work once; report the measured tradeoff
instead of beginning an open-ended optimization or review campaign.

## 6. Out of scope

- Implementation, commits, pushes, installation, publication or live content
  application during this planning request.
- Bulk lineage backfill/anchoring of the 786 unrecorded routes; remote fetching,
  OCR, new document readers, model ranking or learned routing.
- Fixing the three study-map obligations, rewriting learner notes or closing
  critique points.
- New databases/frameworks/persistent caches, broad UI redesign, perfect
  exclusion of arbitrary external editors, or hardware power-loss claims from
  process-crash tests.
- Changes to unrelated dirty work, `LearningOS/legacy/`, or `Stratum/`.
