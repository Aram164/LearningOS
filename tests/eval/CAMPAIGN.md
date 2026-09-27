# Campaign: authoring, failure recovery and native UI

Baseline product: Core `e17d52c7c694ce574619ca362aeb59d8c4722518`, UI
`a2d031d1f00e586b6310ebb5e5a5a5ed88103936`. Record the exact candidate
SHAs for every run; the baseline names a comparison point, not an assertion
that a later branch is unchanged. All worlds and run logs live outside the
real checkout and vault.

The prior campaign tested the study/capture loop. In the real receipt record
from 2026-08-27, 178 of 237 writes were module plans, unit maps/revisions,
route patches or analysis saves. This campaign gives those paths ordinary
operator goals as well as hostile failure probes.

## Sessions

| # | Role | Plan / output |
|---|---|---|
| 00 | Harness author | Build and self-test the world, scenarios, sealed oracle and scorers; freeze their digest |
| 01 | Independent design reviewer | Audit realism, oracle, leakage, safety and omitted failure modes; text review before results |
| 02 | Blind baseline operator | B: S00–S01 |
| 03 | Blind plan author | A: S01–S07, then S08 in a fresh context on the same world with the apply response withheld |
| 04 | Blind analysis operator | E: S09–S14 |
| 05 | Independent context operator | E on a fresh world, so source discovery can be compared |
| 06 | Guard investigator | X: S15–S17 |
| 07 | Fault and recovery investigator | X: S18–S22 |
| 08 | Native Obsidian operator | U: S23–S25, using a disposable synthetic vault |
| 09 | Scale investigator | P: S26, same host and seed across sizes |
| 10 | Judge | Open oracle, score every run, inspect code and write FAILURE_ANALYSIS.md before repairs |
| 11–12 | Repair sessions | Failing reproduction first; bounded fixes and PATCH_LEDGER.md |
| 13 | Hostile verifier | V: attack every repaired failure and its adjacent invariants on frozen candidate |
| 14 | Clean-room consumer | C: S02, S04, S05, S07, S09, S10, S15, S23–S25, fresh sessions |
| 15 | Exact-pair assessment | R: S27 on frozen Core/UI commits |

For S22 the investigator first prepares a synthetic Core/UI pair. For S27,
build the world from the exact frozen Core commit and clone the exact UI
commit; record the candidate Core SHA separately from the synthetic world
HEAD. The live check takes the synthetic HEAD because it observes Noor's Git
history, while paired CI is checked against the candidate product commits.

Sessions 02–09 can run independently except that A, E and U each have their
own within-run continuations. Session 10 sees all results and the oracle;
sessions 02–09 never do. The same agent session must not author an expected
answer and later count itself as a blind consumer. For local runs, use fresh
agent sessions without shared task history or memory. The independent reviewer
may inspect the oracle, but must not brief blind consumers from it.
The S08 restart receives only its world path, S07 preflight, submitted
envelope and idempotency key. The conductor keeps the actual S07 apply response
in judge evidence and combines the two segments in one A-plan run. A restarted
operator must discover whether S07 committed from the system state.

## Hard acceptance

For every successful write: an actual learner approval when required, exact
reviewed input bytes, the expected snapshot and artifact revisions, one
committed receipt, no unexplained authored change, and a fresh projected read.
For every refusal: named reason and file when applicable, zero unintended
canonical change, no committed receipt, no abandoned journal, and no later
read poisoned by the refusal. Existing learner notes, attachments, feedback,
progress and unrelated unit order survive plan revisions. Source analysis
remains bound to observed bytes and cannot claim review or mastery merely by
being saved. Native UI state must agree with Core and Diagnostics must identify
the actual running pair.

The judge assigns each scenario PASS, PASS_WITH_FRICTION, FUNCTIONAL_FAILURE,
ROBUSTNESS_FAILURE, USABILITY_FAILURE, PERFORMANCE_FAILURE, AMBIGUOUS or
NOT_RUN. A confirmed hard-invariant violation fails its capability even when
the operator eventually reaches the requested result. Give task correctness
0/1/2 (wrong or missing / partial / complete with supporting evidence).
Report task completion separately from CLI exit status and test-suite results.

Measure commands, context bytes, documentation reads, implementation-file
reads, retries, learner questions and time to a correct result. Count a
candidate surfaced by a public product read separately from one found by
opening files manually. Treat wording or keyword scores as heuristic; a judge
checks whether the citation actually supports the claim. S26 reports raw
times, medians, spread and host load. The 10,000-note cold result is tracked
performance debt for this campaign, not a release blocker by itself.

## Failure and repair discipline

Consumers never patch the product. They record a minimal failing command,
stderr, observer snapshots and one reasonable retry. The judge checks the
failure against the code at the evaluated SHA and labels it confirmed,
pre-existing, harness artefact, ambiguous or deferred. Each repair has a
base-vs-candidate reproduction on the same world and a ledger row naming
changed files, before/after result, neighboring cases and remaining risk.
Verifier session 13 starts from a frozen candidate and may not patch it. A
verifier finding causes a new candidate and a new verification pass; it is
not silently absorbed into a green report.

## Gates and release claim

During development run the affected focused journey. Before a fix batch is
merged, run the full synthetic CLI set, the relevant native UI cases, the
hostile verifier and `make system-check`. Inspect Core and UI CI on the exact
pair. `install:status` proves installed identity; a running-app claim needs
Diagnostics-backed `check:live` after the disposable vault is loaded. The
final report separates source tests, synthetic journeys, CI, installation
and actual Obsidian evidence. It lists every NOT_RUN case.

S17 records the existing ledger-loss residual. S26 measures cold search.
Neither authorizes an unreviewed ledger redesign or scale optimization. Any
new warning signature, validator error or crash on the final pair remains a
failure even when earlier runs passed.

## Harness changes

Each entry is dated and names what changed and why. Runs made before an entry
are not comparable with runs after it for the affected scenarios.

### 2026-09-27 H1 — design-review fixes before any blind run (conductor)

Session 01 (`DESIGN_REVIEW.md`, public-safe) found four blockers and 24
should-fix items against the freeze at `ebaaa90`. No blind run had started.
The corrected operator harness is built from the new freeze recorded in the
conductor handoff. It uses a private Python environment with no `los` entry
point (S1, S2), a real `node_modules` copy for the harness UI (S5), excludes
real learner data from the checkout (L3), and has an extended workspace fence
(S8). Plaintext oracle, key and oracle-bound review artifacts are in the
judge-only home directory, outside `/private/tmp` (L1, L2). Repository changes:

- `build_world.py`: refuse `--out` inside any existing Git working tree, so a
  harness copy cannot write into the real tree (S3); record
  `product_tree_sha256` for every build and, for `WORKTREE`, the source HEAD
  and a status digest (R6).
- `prepare_native.py`: the same Git-tree fence for the world (S3).
- `interrupt_probe.py`: restore a full pristine copy before each trial instead
  of `git reset`/`git clean`, so untracked prerequisites survive; exit 2 when
  the uninterrupted run changes nothing; accept only a world's
  `LearningOS/repository` (S4).
- `observe.py` (observer v2): receipts are `transaction-*.yaml` only, ledgers
  reported separately (R3); "authored change" excludes
  `operations/transactions/`, so both receipt/change flags can fire (R4); the
  external materials tree, a sibling UI checkout and the plugin's `data.json`
  are observed (R5).
- `check_run.py`, schemas: plan letters X1 (S15–S17) and X2 (S18–S22) for
  the two sessions that share X, O documented (R1); per-case records for
  multi-world scenarios (R2); `envelope_files`/`review_reports`, and a
  receipted result must name its envelope or say why none exists (R9); a
  `WORKTREE` product revision must carry a product digest (R6); optional
  metric fields for context bytes, product-surfaced versus file-read targets
  and time to a correct result (R7); `worlds` and `ui_revision` in `run.json`
  (R8).
- `score_workflows.py`: flags from every case, receipts compared by
  transaction file.
- Public text: build from the exact product commit the kickoff names, with
  validation; run the product as `python tools/los.py` from the world root,
  never a bare `los`; do not read `corpus/`, cite world paths, read
  `eval-drop/` only when named (L4, H6); save envelopes and review outputs;
  NATIVE-UI names the operator harness and requires a `basePath` assertion
  before CLI-driven UI actions because the synthetic vault shares the real
  vault's folder name (S6, S7).
- Scenario and oracle repairs: S04 asks for a useful locator refinement rather
  than correction of a nonexistent defect; S06 names the exact route move;
  S07 accepts the approved operator path and forbids a forged UI channel;
  S08 genuinely restarts without the apply response; S13 checks a false
  Tessera premise; S14 supplies the sketch; S21 leaves normalization to the
  judge; S27 separates world-compatible and real-product full-suite gates.
- Decision recorded (L5): `CAMPAIGN.md` stays in the operator harness. Blind
  operators are not directed to it and not forbidden from it.
- Recorded for the judge (H1, H9): `full_repo` and `live_install` tests assert
  the real learner's installation and fail in every synthetic world; the
  product at `ebaaa90` is the baseline Core `e17d52c` plus two test files.
