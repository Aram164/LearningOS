# AML source-rigor implementation checkpoint — 2026-08-30

## Purpose and pause boundary

This is the restart document for the authorized AML learning-plan completion and paired
LearningOS release. Work is intentionally paused **before P4** at Aram's request.

- P1, P2 and P2b were applied canonically through GatewayEnvelopeV2 and have Receipt V2
  evidence.
- P3 is authored and passes `module-plan-import --check`, but **has not been applied**.
- P4 has **not** been authored.
- The paired full gates, two repository commits, exact-pair receipt, vault installation,
  install-status check and live Obsidian verification have **not** been run for this release.
- Nothing was committed or pushed in this run. Do not push unless Aram separately asks.

Work only in:

- `/Users/aramaljanadi/Desktop/semestercontext/LearningOS/repository`
- `/Users/aramaljanadi/Desktop/semestercontext/LearningOS/obsidian-ui`
- the declared live vault only for the final install/live verification

Do not inspect or touch sibling repositories. Preserve the dirty trees and include their
reviewed contents in the eventual authorized all-tree commits; do not reset, clean, rebase,
discard or overwrite them.

## Governing files to re-read

1. `/Users/aramaljanadi/Desktop/semestercontext/AGENTS.md`
2. `/Users/aramaljanadi/Desktop/semestercontext/LearningOS/repository/AGENTS.md`
3. `/Users/aramaljanadi/Desktop/semestercontext/LearningOS/repository/system/OPERATOR.md`
4. `/Users/aramaljanadi/Desktop/semestercontext/LearningOS/repository/system/PLAN-CREATION-SOP.md`
5. `work/active/workspace-aml-exam-prep/outputs/AML-source-rigor-HANDOFF-2026-08-30.md`
6. `work/active/workspace-aml-exam-prep/outputs/AML-SOURCE-RIGOR-PLAN-2026-08-30.md`
7. this checkpoint

Use `/Users/aramaljanadi/Desktop/semestercontext/LearningOS/repository/.venv/bin/python`.
Canonical plan changes must continue through `module.plan.import`; never hand-edit the
canonical AML source map, units, study maps or generated projections.

## Current canonical state

The last canonical write was P2b. The current revision ledger records:

- `module-hu-aml`: 7
- `unit-aml-exam-prep`: 5
- `unit-aml-l01` through `unit-aml-l09`: 2 each, including `unit-aml-l07`: 2
- `unit-aml-l10`: 4
- `unit-aml-l11`: 4
- `study-map-aml-l01` through `study-map-aml-l09`: 2 each
- `study-map-aml-l10`: 3
- `study-map-aml-l11`: 2

`los status --json` at the pause boundary reported 0 validation errors and 362 warnings.
The last full post-P2 gate was stronger: `make check` reported 0 errors/361 warnings,
`make views` completed, a second `make check` reported 0 errors/361 warnings,
`tests/test_curriculum_v2.py` passed 58 tests, and the warning baseline had no new or grown
signature. The one-warning difference in the later status appeared after the unapplied P3
work package existed; do not represent it as a canonical regression without reproducing and
classifying it.

## Applied packages and immutable evidence

| Package | SHA-256 | Receipt | Revision effect |
|---|---|---|---|
| P1 | `3bc84da409a1c479d2449b10d4b92ec965e22c8c7b43534709da534f55a4fe1c` | `operations/transactions/transaction-20260830-132122-001.yaml` | AML module 4→5; exam-prep 4→5 |
| P2 | `ec09c3ff09211d39b331616a78c03a39d94a8da91b8878d2b738567f61c395c5` | `operations/transactions/transaction-20260830-180925-001.yaml` | AML module 5→6; L10 3→4 |
| P2b | `9b31ceb69c55eabceccde426b965ff65e7fb1ece241182dada6a662d0fdf2ca7` | `operations/transactions/transaction-20260830-181112-001.yaml` | AML module 6→7 |

The exact persisted envelopes are under `operations/gateway-requests/`. The first P1 stale
attempt is deliberately preserved as `AML-source-rigor-P1-stale-envelope.json`; do not replay
it. P1 repaired wrong Murphy pages and the exact local Zacharski filename. P2 replaced every
local vague locator, split aggregate ESL/ISLP routes, removed the false CS229/CSC411 CNN
claims, and rebuilt L10 atomically. P2b only rephrased two exact CS229 locators so the
validator would not misread the heading word “selection” as an unbounded locator.

## P3: ready for governed import, not yet applied

Artifacts:

- builder: `work/active/workspace-aml-exam-prep/outputs/aml-source-rigor-build/p3.py`
- reviewed package: `work/active/workspace-aml-exam-prep/outputs/AML-source-rigor-plan-P3.yaml`
- exact SHA-256: `07733200923615577344c1c4121ae86c6a7b1d9a49c2369245d0fe1170b8d00e`
- package projection: 48 sources, 268 routes, 2 unit records
- unit records shipped: `unit-aml-l07` rebuilt study map and
  `unit-aml-exam-prep` selection-locator synchronization

The successful preflight was:

```bash
cd /Users/aramaljanadi/Desktop/semestercontext/LearningOS/repository
.venv/bin/python tools/los.py module-plan-import module-hu-aml \
  --file work/active/workspace-aml-exam-prep/outputs/AML-source-rigor-plan-P3.yaml \
  --check
```

Expected result:

```json
{"ok": true, "mode": "check", "module_id": "module-hu-aml", "units_checked": ["unit-aml-exam-prep", "unit-aml-l07"], "files_checked": 5, "canonical_files_written": 0}
```

Re-run the hash and preflight before import. Do **not** regenerate P3 by applying P1/P2/P2b
again: `run.py p3 ...` is intentionally based on the current post-P2b canonical map.

### P3 probe decisions that must not be lost

- Selected and routed: Berkeley CS189 official solved-exam bank; reachable official CS229
  practice-midterm solutions; Belkin et al. double-descent paper; 3Blue1Brown calculus;
  Setosa OLS; Bendersky normal equation; Distill momentum; local Marsland; Fortmann-Roe;
  Müller et al. kernel tutorial; Jurafsky Ch 3; Nielsen; Prince; MIT 18.S096; targeted MIT
  18.06 sessions; Patrick Loeber's CIFAR-10 CNN.
- Marsland was opened locally. Exact usable ranges are §2.2/§2.5 PDF pp. 40-51 and 56-57,
  §3.3 pp. 64-76, §8.2 pp. 196-200, and §3.1-§3.2 plus §4.1 pp. 60-64 and 94-97. It has no
  CNN chapter, so the proposed L10 route was rejected.
- The current Ng Machine Learning Specialization no longer contains the old “Kernels I/II”
  lessons named by the existing L07 route. P3 removes that false route and replaces its
  coverage with reachable kernel sources; this is why L07 is rebuilt atomically.
- `source-islp-community-solutions` currently resolves to a 2017 first-edition ISLR solution
  site, not the routed 2023 ISLP exercises. It was excluded rather than mislabelled.
- Current CS229 course assignments are Stanford-login restricted and the archived PSet PDF
  links are dead/restricted. P3 routes only the reachable official 2010 practice-midterm
  solution and explicitly says the other problem sets are not routed.
- Berkeley's official resources page exposes current and historical midterms/finals with
  official solutions. P3 uses exact 2024/2026 question locators rather than a generic exam-bank
  label on lecture routes.
- Jurafsky Ch 3 and Ch 8 direct PDFs were live-opened as the August 19, 2026 drafts. P3 uses
  Ch 3 §3.1-§3.2 PDF pp. 1-8 and Ch 8 PDF pp. 1-17.
- `source-sutton-barto-rl` remains visible, reference-only and unrouted because RL is absent
  from the current AML decks.
- Graduate-depth texts, a fourth video rail, and interpretability/augmentation tooling retain
  the explicit deferred/out-of-scope dispositions already recorded in the audit.

Primary pages used for the live probe include:

- `https://eecs189.org/fa26/resources/`
- `https://cs229.stanford.edu/materials.html-OLD`
- `https://cs229.stanford.edu/oldSol-randomstringfdsafsa/practice-midterm-solutions.pdf`
- `https://mml-book.github.io/`
- `https://cs231n.github.io/classification/`
- `https://cs231n.github.io/optimization-1/`
- `https://cs231n.github.io/convolutional-networks/`
- `https://distill.pub/2017/momentum/`
- `https://scott.fortmann-roe.com/docs/BiasVariance.html`
- `https://web.stanford.edu/~jurafsky/slp3/3.pdf`
- `https://web.stanford.edu/~jurafsky/slp3/8.pdf`
- `https://ocw.mit.edu/courses/18-s096-matrix-calculus-for-machine-learning-and-beyond-january-iap-2023/`
- `https://ocw.mit.edu/courses/18-06-linear-algebra-spring-2010/resources/lecture-videos/`
- `https://ocw.mit.edu/courses/6-034-artificial-intelligence-fall-2010/pages/exams/`
- `https://docs.pytorch.org/tutorials/beginner/blitz/autograd_tutorial.html`
- `https://docs.pytorch.org/tutorials/beginner/blitz/cifar10_tutorial.html`

### Exact P3 import restart sequence

1. Confirm the P3 hash and repeat the successful `--check` above.
2. Recompute the current canonical fingerprint **after every work artifact has been written**:

   ```bash
   .venv/bin/python -c 'from pathlib import Path; from tools.learning_os.fingerprint import canonical_fingerprint; print("sha256:" + canonical_fingerprint(Path.cwd()))'
   ```

3. Create a new persisted `operations/gateway-requests/AML-source-rigor-P3-envelope.json`
   using the P2b envelope as the shape, with new request/idempotency identities, the current
   fingerprint, the package hash above, and these expected revisions:

   ```json
   {
     "module-hu-aml": 7,
     "unit-aml-l07": 2,
     "unit-aml-exam-prep": 5
   }
   ```

4. Compute the approval subject from the exact envelope intent using
   `tools.learning_os.contracts.gateway.intent_sha256`, write it to
   `approval.subject_sha256`, persist the final bytes, then call:

   ```bash
   .venv/bin/python tools/los.py capability module.plan.import \
     --payload-file operations/gateway-requests/AML-source-rigor-P3-envelope.json
   ```

5. Require a successful Receipt V2, then verify the receipt's package hash, paths, revisions
   and `snapshot_after`. Expected revision effect is module 7→8, L07 2→3, exam-prep 5→6.
6. Run `make views`, `make check`, the focused curriculum tests and warning-baseline gate
   before starting P4. Stop on new errors or a new/grown warning signature.

Never reuse a stale envelope with a changed fingerprint, and never generate a fresh request
after an ambiguous result until the exact persisted envelope has been replayed and projection
reconciliation has observed `snapshot_after`.

## P4 remaining work

The current post-P2b canonical map has 228 routes and 219 missing `angle_detail` values.
The preflighted P3 candidate has 268 routes and **218** missing `angle_detail` values: P3's
40 net additions all already have route-specific detail, and the one removed obsolete Ng
kernel route lacked detail. P4 therefore has exactly 218 existing routes to finish.

P4 requirements:

1. Author `aml-source-rigor-build/p4.py` against the **post-P3 canonical map**. Do not emit a
   generic copied template. Each detail must state what the reader gets, prerequisites/depth,
   how it differs from neighboring routes, and where it departs from the current deck.
2. Set `REBUILD_UNITS` to all twelve AML unit IDs so the final package atomically carries
   every lecture and exam-prep study map.
3. Generate only P4 into `AML-source-rigor-plan-P4.yaml`; expect 48 sources, 268 routes,
   0 missing details, and all 12 unit records.
4. Update the coverage audit truthfully: replace the historical “not applied” claims with P1-
   P4 receipt evidence, record all selected/deferred/rejected sweep outcomes above, and record
   measured final route/warning counts rather than the old forecast table.
5. Run `module-plan-import --check`. The P4 envelope must use the current post-P3 snapshot and
   exact then-current revisions. If no intervening writes occurred, the expected revisions
   should begin with module 8; L07 3; exam-prep 6; L01-L06/L08-L09 2; L10 4; L11 4. Re-read
   `operations/transactions/revisions.yaml` rather than trusting this forecast.
6. Apply once through GatewayEnvelopeV2 and require Receipt V2 plus projection reconciliation.
7. Run final AML acceptance checks: 0 locator warnings for routed AML material unless a truly
   unresolved item is explicitly accepted; 0 missing `angle_detail`; all 12 study maps valid;
   no invented pages, concepts, times or source claims.

## Release tail still required after P4

Do not claim release completion from focused tests alone. The original request still requires:

1. Core and UI focused tests for every changed safety/recovery/install surface.
2. Core `make check`, `make views`, second `make check`, curriculum tests and warning baseline.
3. Paired `make system-check`; then `make stress` if its online URL probes are available.
4. Review the real complete diffs in both dirty repositories. Preserve and include all current
   requested changes, but stop on unexplained unrelated failures.
5. Commit all reviewed changes in each nested repository, without pushing.
6. Generate and validate the exact Core/UI release-pair receipt from the two committed tree
   identities. A dirty or mismatched pair is not release proof.
7. Install the exact committed UI build into the declared live vault, run `npm run install:status`,
   reload as required, and use the live-app verification path. If real Obsidian verification is
   impossible, report that as missing release evidence rather than “done.”

## Dirty-tree and branch baseline to preserve

- Core branch: `engineering-review-tier1`; starting HEAD for this request was
  `1af2031f85c895b11148b647faa32542a55c235c` with upstream +0/-0.
- UI branch: `engineering-review-tier1`; starting HEAD was
  `bb1074bfc612035b7e864ce149fd2d7b8f82301a` with upstream +0/-0.
- Both repositories already contained substantial authorized changes before the AML work.
  The current `git status --short` is long; inspect it fresh and never treat untracked files as
  disposable.

## Resume success condition

Resume at **P3 governed import**, not at discovery and not by rerunning P1/P2. The task is
complete only after P3 and P4 receipts, exhaustive AML gates, paired system gates, reviewed
all-tree commits, an exact-pair receipt, exact committed UI installation, install-status proof,
and live verification (or an explicit evidence gap) are all recorded.
