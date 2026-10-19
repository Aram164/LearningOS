# Independent repairs and publication — 19 October 2026

Aram cancelled the test-suite exploration and instructed Codex to finish the confirmed fixes, test them and publish them. The original interrupted C1 handoff is retained locally at `receipts/R-takeover-20261019/CONTINUE-before-takeover.md`; it no longer describes current implementation state. The frozen migration contract remains unchanged.

## Implemented repairs

- R1: retry the receipt-parent durability barrier before retiring a committed journal; a failed retry preserves recovery evidence.
- R2: synchronize the journal namespace through the repository root before effects on every attempt, including retries after a failed barrier left directories visible.
- R3: bind asynchronous recovery transitions and failed-save rollback to the request and state they observed; obsolete results cannot replace or retire newer recovery state or drafts.
- R4: reject fresh writes from retained stale data even when the caller supplies an explicit snapshot. Exact recovery and projection rebuilding remain available.
- R5: visibly label retained stale views, redraw after refresh failure, and coalesce relevant manifest events/window focus through the existing lifecycle-owned queue.
- R6: recheck plugin ownership after awaited startup reads and before registrations/layout work; obsolete manifest loads cannot publish partial or late state.

Existing migration changes are preserved: parser-free gateway admission, typed commit results, capability-selected commit families, session reconstruction in its existing owner, compact multi-unit revision evidence, and the previous transaction/claim hardening. No test-suite redesign or thinning was performed.

## Verification and publication rule

Focused settled-source evidence: 308 Core/architecture/engine checks passed; the complete UI check passed (including 12,750 differential response cases); all procedure checks passed (15 passed, two expected historical mismatches); the independent Core/UI/plugin reproductions passed. The new UI regressions also fail against the retained old source. macOS file/directory sync and stronger flush probes passed; interruption tests are not physical power-loss evidence.

The first final dirty-tree run, `R-paired-final`, was deliberately stopped by Codex after 1,147 passes so the complete final gate could run once against clean publication commits. It has exit 2, unchanged source, and is not acceptance evidence. The prior Muse `C3-paired-final-2` has no completion receipt and is also not accepted.

Publication uses matching `codex/architecture-hardening-repairs-20261019` branches in both repositories, isolated from the retained candidate worktrees. Exact source equality is recorded in the local execution `publication/source-equivalence.json`. The complete paired gate must succeed on these clean commits before either remote publication; normal Git hooks remain enabled. Its authoritative result and exact commit identities belong in the paired pull-request descriptions and local publication receipt.

## Boundaries and continuation

C1/S0 and C2 have their historical accepted-source receipts. These repairs and a green source gate do not alone certify all C3 obligations: disposable real-Obsidian workflows and independent restoration of raw vault settings/drafts require their own evidence. The original vault, authored/operational state and unrelated dirty work remain outside this publication. No main merge, live installation, release or S9b extension is included. Test-suite exploration is cancelled.

Local execution root: `/Users/aramaljanadi/Desktop/semestercontext/LearningOS/workbench/architecture-hardening-2026-10-17/execution`. Before continuing, reconcile `LEDGER.md`, `continuation-state.json`, the publication receipt and actual GitHub pair; preserve existing receipts and never infer completion from partial output.
