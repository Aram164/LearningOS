**Latest state: the resumed checkpoint at the end of this file supersedes the earlier handoff below, especially its runtime description and remaining-work list.**

# LearningOS migration continuation — 18 October 2026

Aram requested implementation, then instructed: at 5% remaining usage, document the current state, continuation and percentage of work left. The account tool reached 95% used in its five-hour window (5% remaining); weekly usage was 30%. Stop here for handoff after collecting the already-running check. No reset was redeemed. This is an unfinished source candidate, not an accepted release.

Estimated **80% of the full migration remains** (reasonable range 75–85%). This is engineering judgment about implementation plus mandatory verification, not a count of files/tests. Baseline/enforcement and substantial material/claim foundations are done; most later architecture, durability, recovery, UI and runtime acceptance work remains.

## Exact authority and paths

- Workspace: `/Users/aramaljanadi/Desktop/semestercontext`.
- Contract: `/Users/aramaljanadi/Desktop/semestercontext/LearningOS/workbench/architecture-hardening-2026-10-17/FINAL-MIGRATION-CONTRACT.md`, SHA256 `ffcca27a2d0c516d12e8394ae4247b94a0491345885aadbf74e6e2892468ebaf`.
- Execution directory: `/Users/aramaljanadi/Desktop/semestercontext/LearningOS/workbench/architecture-hardening-2026-10-17/execution`.
- **Continue Core edits in** `execution/candidate/repository` and UI edits in sibling `execution/candidate/obsidian-ui`. Both are manual git worktrees on `codex/final-reliability-20261018`.
- Core HEAD: `074f4717e14527798752de84b3c9c4e88348b658`.
- UI HEAD: `a88b1188ad54439b4df32813904de182c06a105c`.
- Changes are uncommitted. No commits, push, PR, publication, installation or live learner-data edits occurred. Original `LearningOS/repository` and `LearningOS/obsidian-ui` are clean.
- Read workspace AGENTS.md, candidate Core AGENTS.md and system/OPERATOR.md, normative corpus and applicable architecture contracts before further changes. Do not traverse Stratum or edit legacy.
- No subagents were used or authorized. No independent reviewer was assigned. Same-session review cannot satisfy final independent acceptance.
- Required dated A11 approval must be obtained against the actual candidate surface diff. None has been written or fabricated. Source drafting is authorized; acceptance of the changed surface and live rollout retain their gates.

Read `LEDGER.md` for decisions and obligations. Detailed specifications are the parent `MIGRATION-PLAN.md`, hardening `PLAN.md`, and sibling `workbench/verbatim-anchor-admission-2026-10-18/PLAN.md` and `workbench/scan-in-workflow-2026-10-18/PLAN.md`. The final contract supersedes their conflicts. Reference these files rather than copying their specs into new plans.

## Preserved world and environment

`baseline-receipt.json`, `independent-inputs.json`, `outer-dirty-inputs.json`, `vault-settings-baseline.json`, private raw `vault-safety-baseline/data.json` and `world/` preserve the initial world. Inventory has 2188 authored/operational/vault entries. Raw settings SHA256 is `a8981ca36ef1d059b1425af81c0666936e824671c0ee9c5730818300fd4516f4`.

`continuation-state.json` records exact hashes of every candidate source file, original/candidate statuses, retained command receipts and independent preservation comparisons. `candidate-core.patch` retains the tracked diff; `candidate-new-files.tar` retains new nonignored source files. The worktrees remain the authoritative editable candidate. Preserve all existing unrelated outer dirty/untracked work; never reset or clean the tree.

Python 3.14.4, mypy 2.4.0, Node v26.6.0, npm 11.18.0. Core `.venv` is a real ignored directory with bin/lib/include links to the original runtime and a copied pyvenv.cfg. UI `node_modules` is an untracked dependency symlink to the original runtime; do not stage it. Candidate sibling `materials` links to live LearningOS/materials; do not mutate it. Relevant material digests are required for evidence reuse. There were 207 GiB free at handoff preparation.

Do not rerun capture_baseline.py into existing baseline paths. `capture_continuation.py` is safe to rerun: it reads the originals and writes the current preservation/source snapshot outside the candidate.

## Implemented candidate changes

1. Permanent strict type gate in pyproject/Makefile, covering all five new/maintained boundaries; frozen 213-module legacy inventory catches uncovered new production modules. `follow_imports=silent`, never skip. Architecture controls protect future durable_fs imports and attribute mechanical helper effects only to the immediate authorized production caller, while retaining the raw writer. Callback negative controls are included.
2. Backup declarations include goal-ledger.yaml. Backup inspection now derives durable operational writes from commands, internal_commands and domain_capabilities before first write. Versioned raw-vault safety bundle CLI is **not implemented**.
3. Initial finite persistence model separates receipt visibility/durability and demonstrates the rollback counterexample with protection disabled. It is a logical model only. **The serious production receipt-publication/rollback defect has not yet been fixed.**
4. New pure quotation matcher, shared immutable PDF byte reader and request-local exact-file anchor reader. Explicit quote length/normalization, PDF place, transcript grid/window/video identity, manifest digest, parser refusal, unreadable fallback and changed-material checks. Shared reader used by both initial and continuation material slices and material_toc verification. No persistent cache or stored excerpts.
5. Shared typed app/claim_admission.py replaced the old Phase B implementation in plan.py. Admission covers identity/coverage changes and unchanged stale/contested rejudgments; exact audit-defect eligibility is pending. Digest-only planned lineage, unit-scoped evidence and ephemeral anchor reports. Shared lineage file guard added to plan check/apply, source revision with dossiers and synthesis publication; restamp already used it. Narrow ledger-only receipt verification retains ordinary-write checks.
6. Locator duplicate/file-contradiction validator and tests; real captured world still validates with zero errors and the same three exempt advisories. Historical Sept12 broadcast replay/disabled-rule controls remain pending.
7. Candidate route.patch evidence schema/CLI/catalogue/write-grant, same shared admission and atomic lineage, prospective check/envelope guards and replay tests. Generated capability schemas were updated once; full combined surface/parity/transcript/UI regeneration is pending. No approval baseline changed.
8. Last integration found legacy id-less routes were absent from the former source-map helper; an ordinary descriptive edit falsely looked like a new claim. Shared admission now uses the existing route_with_identity owner for both before/after maps. A material-edit fixture now supplies a real PDF, exact manifest and quote instead of invalid text masquerading as a PDF. The interposed guard test includes all six capability grants, but this engine-driven test alone is **not** actual handler interleaving proof.

## Evidence and limits

Retained raw logs and source-before/after identities are under `receipts/`. `run_receipt.py` refuses name reuse. Earlier failed runs are intentionally preserved.

- E1-enforcement: 128 passed, 1 skipped. Skip is A19 population-wide witness verification and must run with the complete scenario population at C1.
- E1-types and current manual `make typecheck`: passed; strict coverage is five source modules.
- E1-validation-clean and CLAIM-V4-validation: zero errors, three existing operational advisories. Earlier E1 validation failures were the task-created mypy cache and incorrectly symlinked .venv, corrected without changing authored content.
- V2-real-inventory.json: 894 active routes = 538 local, 70 local-unresolved, 286 remote-unanchored. All 382 transcripts parsed with zero failures. Classification deliberately uses declared source authority and differs from raw existence buckets.
- Earlier corrected matcher/slices/type/layer check: 99 passed. Ledger-only/receipt/acceptance focused run: 16 passed. New route.patch check/apply/refusal tests: 3 passed.
- CLAIM-integration-before-scan: 318 passed, 2 failed. Those failures exposed the legacy identity compatibility bug and an obsolete evidence-free fixture; preserve the receipt as a failure.
- CLAIM-legacy-route-regressions: 8 passed, 1 failed. Identity bug fixed; remaining fixture lacked the source registry's book.pdf once a manifest activated integrity validation. Corrected fixture with real book.pdf and complete size/hash rows.
- CLAIM-corrected-integration: see final appended handoff checkpoint and its receipt for the authoritative result; never assume an unfinished process passed.
- Latest ruff on admission/material-edit/unit-revision files passed. Reachability earlier classified 271/271 modules with 11 historical allowances and no new allowance. Broad architecture/surface gates after all changes remain pending.

**No C1, C2 or C3 acceptance has been claimed.** There has been no full paired system-check for the final candidate, independent acceptance review, disposable Obsidian runtime proof, installation or publication.

## Next implementation work

1. Read the final handoff checkpoint and reconcile active sessions/processes, current worktree statuses/hashes and receipt completion. If the last integration failed, fix the actual failure first and rerun its affected seam. Do not reset the candidate or recapture the world.
2. Close remaining material/source authority seams before claim acceptance: proposed source_patches are currently not overlaid into AnchorReader's source registry. Verify before/after source.material authority and removal/downgrade behavior, implement the appropriate observed overlay and add real tests. Check malformed ledger/manifest/revision failures become named preflight refusals rather than unhandled errors. Do not silently accept evidence using the old binding.
3. Complete scan/goals/audit lifecycle from its source plan and final amendments. No implementation started here. Build one shared claim-status owner with bounded reads; stale occurrence = stable judgment plus relevant current drift, full digests, no clocks/snapshot ordering. Immutable audit authorization/result must be separate from mutable attention decisions, exact claim/basis certification/defects, no redraw, historical closure, failed-audit repair/new-basis behavior. Extend IDs, schemas, decisions and tests; reject needs note and authorized means intent, not completion. Implement brief-only false-positive suppression under specified Wilson rule without hiding full JSON.
4. Integrate status into focused route plan-edit-context, bounded brief, full unit claims map and live dossier summary outside the cached bundle; no stage-wide claim reads. Add nonblocking preflight impact; extend unchanged rejudgment eligibility to exact audit-defective pairs. Remove duplicate staleness logic rather than introducing a cycle through scan.
5. Complete historical broadcast controls, actual all-six-writer handler interpositions (including source attach/dossier replacement/rebase), material replacement between check/apply, production owner/effects evidence and performance measurements. Finish docs and batch schema/surface/parity/transcript/UI generation after the combined slice stabilizes. Obtain actual-diff A11 approval. Complete **C1**.
6. Only then capture hardening S0. Implement S1/S2 durability/conflicts and prove the visible-receipt barrier regression with disabled protection; **C2**.
7. S3–S8 request normalization, closed results/policies, explicit prepared imports/material derivation, typed UI collections and exact-byte freshness; remove old implementations in each slice.
8. S9 reviewed recovery, model/production connection, real old-reader refusal, downgrade/fences/settlement/receipt inversions, raw-vault safety bundle and restore readiness.
9. **C3** full paired gate, independent review, captured effects/performance, real production Core/validator, disposable Obsidian workflows/lifecycle and restore drill. Rehearse 21 governed claim repairs, then separately authorized live backup/install/content/audit/publication.

Required full local milestone command, from isolated candidate Core with sibling candidate UI:

```sh
PYTEST_ADDOPTS='-m "not live_install"' make system-check
```

Focused evidence command pattern (use a fresh receipt name):

```sh
.venv/bin/python ../../run_receipt.py NAME -- .venv/bin/python -m pytest -q TEST_FILES
make typecheck
```

Do not replace the ordered milestones with focused green tests. Reuse receipts only while source pair, toolchain and relevant inputs still match; enumerate skipped tests and supply their runtime/platform evidence.

## Paste-ready instruction for the next chat

Continue the already authorized LearningOS final reliability migration. First read `/Users/aramaljanadi/Desktop/semestercontext/LearningOS/workbench/architecture-hardening-2026-10-17/execution/CONTINUE.md`, its final checkpoint, LEDGER.md, continuation-state.json and FINAL-MIGRATION-CONTRACT.md in the parent directory. Reconcile candidate files, active processes and completed receipts before changing anything. Work only in the existing isolated candidate Core/UI worktrees on codex/final-reliability-20261018; preserve all original and unrelated dirty bytes. Finish any current integration failure, then remaining material-authority seams and the combined scan/goals/audit/read-status slice. Follow C1 → S0/S1/S2 → C2 → structural/UI/recovery → C3 order. No commits, push, installation, live learner-data changes, invented surface approval or unassigned independent acceptance. No subagent delegation without Aram's instruction. The current candidate is unfinished; the production visible-receipt rollback defect remains unfixed. Do not restart from narrative or treat the test counts as release acceptance.


## Final handoff checkpoint

- Snapshot time: 2026-10-18T03:03:10.412122+00:00.
- CLAIM-corrected-integration completed: **321 passed**, exit 0, 72.37 seconds, candidate source unchanged during the run. Includes the corrected legacy-route compatibility case, evidence-bearing material edit and six-grant guard interpositions. Raw receipt: `receipts/CLAIM-corrected-integration/receipt.json`.
- All migration command sessions completed (92151, 76331 and 59068). No migration command is intentionally left running. Filtered process inventory found no Obsidian/Muse process; the sole long-running Python PID 1514 was VSCode's isort language server, not a migration writer.
- Original Core/UI git statuses empty; original independent authored/operational/vault inventory unchanged; original unrelated outer dirty bytes unchanged. No difference keys.
- Candidate Core source-files digest: `f81578edb9284b5d6cfc5be2ef32c8eb315e2120c92d84275439f9c91f288999`.
- Candidate UI source-files digest: `4092ea79920358b1aaa0fd6cdb1188abcb68bcc6376cd64cdc0127d2fc2d0d1d`. Its only status item is the runtime node_modules symlink, which is not authored UI code.
- Tracked diff SHA256: `09b596e40a18fe12f64950536661f7d4960c3d9c82a7c68a7ee918dad82b976f`. New-file archive SHA256: `7e5f733decd5c18830b95c063cad6e2f3d3893580c6a69f298b7b9cc5a5b12c7`.
- The 5% threshold triggered the stop. Estimated migration work remaining: **80%**, uncertainty range 75–85%. No further implementation started after the threshold; only check completion and preservation/documentation followed.
- First next work: inspect the known proposed-source/material authority seam, then implement the combined scan/goals/audit/read-status slice. The 321 passing tests do not resolve those missing requirements or the production receipt-barrier defect.


## Resumed checkpoint — 18 October 2026, 12:00 UTC

Stopped new implementation when the account reached **95% used / 5% remaining** (weekly 45%), honoring the prior instruction. No reset was redeemed. All commands started in this resumed run have completed or were explicitly stopped as described below. Estimated full migration work remaining: **about 75% (70–80%)**; this is engineering judgment, not a file/test count. The combined claim source slice is substantially implemented but C1 is still unaccepted; durability, structural/UI, recovery and final runtime acceptance remain.

### Exact preserved state

- Keep using these existing candidate Core/UI worktrees; HEADs remain Core `074f4717e14527798752de84b3c9c4e88348b658`, UI `a88b1188ad54439b4df32813904de182c06a105c`, branch `codex/final-reliability-20261018`. No commits/push/install/publication/live learner writes or delegation.
- Snapshot `2026-10-18T12:00:04.602048+00:00`: Core source digest `bbc25eecd96e4e3eba20f1b5f6b8be7bbe470ca757312ec3791217982a6f7fd2`; UI `4092ea79920358b1aaa0fd6cdb1188abcb68bcc6376cd64cdc0127d2fc2d0d1d`. Exact files/statuses/receipts are in `continuation-state.json`; summary `resumed-checkpoint.json`.
- New retained tracked patch: `candidate-core-20261018-resume.patch`, SHA256 `6ac48e2c8e0c3ef58d8f5e2c6fd2bf21da8a4e02face0c1921c55ac3ff35bbde`. New-source archive: `candidate-new-files-20261018-resume.tar`, SHA256 `b2bd7c368df60adc5ecc70f912bec4c08d684f3094377bb84228a43daa3b3666`. Earlier patch/archive were preserved. Worktrees remain authoritative.
- Original Core/UI statuses empty. Original authored/operational/vault inventory and unrelated outer dirty bytes unchanged; both independent comparisons have no difference keys. Disk: 206 GiB free.
- Runtime correction: candidate `.venv` now has a **proper private interpreter prefix**, own `bin/` and a `.pth` pointing first at candidate `tools/`, then at the original installed dependency directory as a plain path. The original editable-install hooks are not executed. No downloads or original-runtime changes. `runtime-private-prefix.json` proves prefix/executable/package path; prior runtime is retained at `runtime-before-private-prefix/`. Do not restore the old symlinked `bin/` layout: it caused fixture launchers to re-exec forever. Python remains 3.14.4. UI node_modules and sibling materials remain shared read-only links.

### Implemented and verified in this resumed run

- Proposed source registry overlay and before/after downgrade checks, with source-material digest pins; malformed lineage/manifest/revision/audit inputs give named refusals.
- One shared bounded claim-status owner; scan duplicate staleness detectors removed; stable judgment basis and full drift occurrence identity; exact-basis audit-defect rejudgment eligibility. Focused/batch/brief/full plan context and live dossier metadata use the owner; stage-focused reads do not. Nonblocking preflight claim impact is included.
- Immutable audit authorization/result separate from mutable decisions, frozen full pool/seed/sample, exact historical closure, no redraw, exact-basis defects, replay bound to both reviewed hash and semantic intent (including note/session), note-required rejection, authorization as intent and Wilson-based brief/resume quieting.
- Seven actual-handler interposition witnesses cover all six writers, including source replacement and source rebase. Each actual handler advances the shared file revision; a suspended whole-ledger replacement refuses and preserves its bytes. Disabled-protection controls demonstrate the overwrite.
- Historical broadcast rows are pinned from actual Git revisions; missing/wrong-file/wrong-text/staged-duplicate controls and real disabled-guard validator runs pass. Real analysis PDF p.26 quotation passes; wrong-file and missing evidence refuse; candidate canonical bytes unchanged. Twenty quotes sharing a file/page took 0.132 seconds total.
- Docs, request/capability schemas, five-key surface snapshot, affected CLI parity and selected scenarios updated. Historical corpus pins remain 1,786 and 265. No A11 approval was invented. Candidate generated views were refreshed after source work.

### Authoritative receipts and remaining evidence limits

- `CLAIM-corrected-owner-integration`: 312 passed, source unchanged.
- `CLAIM-final-focused-source`: 196 passed, source unchanged.
- `CLAIM-broadcast-production-controls`: 78 passed, source unchanged.
- `CLAIM-cli-parity-corrected`: 70 passed; fixed corpus sizes retained.
- `CLAIM-actual-handler-interpositions`: 7 passed, source unchanged.
- `CLAIM-private-runtime-provenance-corrected`: 9 passed; foreign-package startup negative control, actual candidate import/layer/type checks.
- `CLAIM-scenarios-candidate-comparison`: **233 passed / 874 deselected**, 141.39 seconds, source unchanged. This is comparison mode under the corrected runtime, not recording-mode acceptance. The complete scenario population and A19 witness gate still need C1.
- `CLAIM-source-controls`: types, lint, layers, reachability, validation, warning baseline and UI contract all exit 0, source unchanged. Reachability 273/273, 11 historical allowances. Validation 0 errors; its fourth advisory was stale generated views, subsequently regenerated.
- `CLAIM-read-performance`: 20 alternating baseline/candidate runs each for brief, recorded-claim route and dossier, all budgets met. Candidate p95: 1.575s / 0.874s / 1.043s. Brief 10,669 bytes, focused route 3,929 bytes. Raw paired observations under `performance/claim-reads/results.json`.
- `CLAIM-real-material-checked`: actual PDF digest/place and quote digest, genuine/wrong-file/missing evidence preflights; all expected outcomes and canonical/source preservation. Excerpts remain in external execution receipts, not Core.
- `CLAIM-procedures-private-prefix`: **36 transcripts attempted, 7 passed, 29 failed Scrut comparisons (exit 50)**; source unchanged. Exact per-transcript results/stdout/stderr/audits are under `receipts/claim-procedure-private-prefix-details/`. The inspected capture-routing/bootstrap failures show stale snapshot expectations; do not assume every failure is hash-only. Classify every diff before refreshing expectations. No transcript source was rewritten here.

Important provenance correction: audit startup previously imported the original package before the candidate script. `tests/arch_site/sitecustomize.py` now moves its own `tools/` to the front even if already on sys.path; the poisoned-foreign-package regression proves this. Earlier audited-child observations before this correction do **not** prove candidate behavior. Ordinary parent/CLI focused checks are distinct. The first procedure attempt (`CLAIM-procedures-observed`) was explicitly stopped with exit -15 because the old candidate interpreter prefix caused a relaunch loop; only its own PIDs 13705–13708 were stopped. That environment defect is repaired. Its large audit log is diagnostic, not acceptance.

Selected recording deltas were retained and reviewed in `receipts/CLAIM-recording-review.json` and `CLAIM-recording-disposition.md`: 67 prior cases changed, four added. Authored-effect maps are unchanged after fixing a nested publication's missing shared guard. One specified refusal change remains: local locator-only evidence in module.plan.import/lineage-admission-direct now fails quotation admission (exit 1), instead of the old direct-CLI refusal. Its fixture snapshot was refreshed to reach that actual seam, and its declared site is lineage-preflight-failed.

### Next actions — do not restart or cross C1

1. Reconcile this checkpoint, current processes, source/runtime paths and retained receipts. No migration job is intentionally left running. Preserve current candidate and original bytes.
2. Classify all 29 procedure diffs from retained logs. Refresh only intended snapshot/claim/surface expectations, repair any actual regression, preserve commands/refusals/oracles, and rerun with actual candidate provenance. The existing helper scripts retain raw evidence; `verify_claim_procedures.py` accepts a fresh detail-directory name. Do not overwrite earlier runs.
3. Run/refresh the full scenario population and architecture/prose/A9/A19 coverage with correct runtime; selected 233 cases are insufficient. Additional crypto-bound recordings may need justified refresh after schema/transcript changes. Do not blindly bless changed exits or authored effects. Reuse captured-world/material/timing evidence only for matching relevant inputs.
4. **Aram approved the exact five-key [C1 surface packet](C1-SURFACE-PACKET.md) on 18 October 2026**, explicitly replying “Approve this exact C1 surface packet”. The dated receipt is [C1-SURFACE-APPROVAL.json](C1-SURFACE-APPROVAL.json), binding packet SHA256 `8e7781d6d10071e25eb0bc51cc0d068bbecffd51340946f1d82a7c107c31d2cf`. On authorized resumption, verify the current exact diff matches that immutable packet, then add dated candidate A11 approval rows and run its gate. No candidate row has yet been applied; the implementation pause remains. This approval grants neither C1 acceptance nor installation/publication/live writes.
5. Complete the required C1 paired `PYTEST_ADDOPTS='-m "not live_install"' make system-check` after source/fixtures and actual approval are ready. Only accepted C1 permits hardening S0 then S1/S2/C2. The production receipt-visible rollback defect is **still unfixed**. Preserve C1 → S0/S1/S2 → C2 → S3–S9 → C3 order.
6. Independent final review remains unassigned; no subagents without Aram's instruction. No commits, push, publication, installation or live content/audit application.
