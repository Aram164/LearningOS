# S10 failure analysis (white-box judge)

- Date: 2026-09-25. Branch: `muse/eval-s10-judge-2026-09-25`, on base
  `d0c49b5f34fb7526cfa0513f583248fab4301b0e`.
- Product under test: `200a36185fd5c693b4464ce0bdff4be5b89ce584`.
  All code citations below are against that revision, not the branch tip.
- Worlds: `13ad2fca…` for runs 2–8 (`9a85f012…`, pre-H1, for run 0 only).
- Runs merged and scored: 9 (s00, s02, s03, s04, s04b, s05, s06, s07, s08).
  Session 9 was omitted by owner decision; nothing of it is adjudicated.
- Oracle: opened outside the repository, read (README + AUTHOR-NOTES),
  removed after the run. This file paraphrases the oracle throughout and
  quotes none of its sentences: probe/question/scenario ids are the refs.

Method: every run was scored with the package scorers
(`score_connections.py`, `score_retrieval.py`, `friction.py`) against a
reference scale-0 world; every keyword-heuristic miss in the connection
explanations was human-graded (136 rows), every must-not return was read,
provenance was sampled per run (12 rows), all 84 retrieval answers were
graded 0/1/2, every scenario result was graded against its MUST / SHOULD /
MUST_NOT, every failure record was adjudicated, and every load-bearing
claim was checked against the product code at the evaluated revision
(read-only; no product code was changed in this session).

## 1. Run verdicts

blind stands as recorded for all nine runs (see §7). Scores are the
measured record; grades are the judge's.

| Run | Plan | Blind | Scenarios | Headline |
|---|---|---|---|---|
| s00-baseline | B | true | S00, S01, S26 | S00 PWF; S01 ROBUSTNESS (setup recovery, trace leak); S26 USABILITY (capture undocumented) |
| s02-novice | N | true | S00–S02, S04, S06, S10, S14, S15, S26 | Retrieval 12/12 correct; 1 connection probe (A09, from S04), correct; S01 ROBUSTNESS; rest PWF |
| s03-learner | L | true | S02–S08, S13 | Retrieval 36/36 (35×2, 1×1); connections 35/50 probes, recall@10 1.0 answered; all PWF/PASS |
| s04-resume | R | true | S00, S02, S09–S12, S16, S25, S26 | Retrieval 36/36 (35×2, 1×1); S09/S12/S25 PASS; S10/S16/S26 USABILITY (no write completed: docs + H2 env guard) |
| s04b-writes | O | true | S10, S16, S26 | All PWF on retry; S10/S16 MUSTs met; one poisoned world preserved (robustness finding) |
| s05-connections-a | C | true | S03, S27 | 50/50 probes, recall@10 1.0, judged P@5 1.0; PWF |
| s06-connections-b | C | true | S03, S27 | 50/50 probes, recall@10 1.0, judged P@5 0.99; PWF |
| s07-abuse | X | true | S01, S17–S22, S24 | S17 ROBUSTNESS (read exposure); S20 FUNCTIONAL (validate-clean states break reads/writes); S19/S24 PASS; rest PWF |
| s08-scale | P | true | S23 | PERFORMANCE_FAILURE (content search 11.7 s at 2,116 notes, 227.8 s at 10,116; no incremental benefit) |

PWF = PASS_WITH_FRICTION. No run classification filed by a consumer is
overturned; where the judge disagrees on a detail it is noted in §4–§5.

## 2. Connection discovery (measured + judged)

Scorer: `metrics-connections.json` + graded `connections-worksheet.md` in
each of the four run dirs. Macro averages below are over answered probes;
the missing-as-zero average is meaningful only for the plan-C runs, which
are complete by design (s02/s03 answered the probes their scenarios
touched: 1 and 35 of 50).

| Run | Answered | R@5 / R@10 | rel-R@10 | P@5 / judged-P@5 | MRR | Decoy@5 | Outdated |
|---|---|---|---|---|---|---|---|
| s02 | 1 | 1.00 / 1.00 | 0.80 | 0.60 / 1.00 | 0.50 | — | 0 |
| s03 | 35 | 0.98 / 1.00 | 0.95 | 0.73 / 0.99 | 0.97 | 0.08 | 0 |
| s05 | 50 | 0.99 / 1.00 | 0.89 | 0.76 / 1.00 | 0.95 | 0.00 | 0 |
| s06 | 50 | 0.99 / 1.00 | 0.90 | 0.77 / 0.99 | 0.97 | 0.05 | 0 |

Product-only recall (re-ranked on product-sourced targets alone) next to
overall recall, per the AUTHOR-NOTES instruction not to credit the product
with the agent's reading:

| Run | Overall R@10 | Product-only R@10 | MUST found via product |
|---|---|---|---|
| s03 | 1.00 | 0.73 | 47/65 |
| s05 | 1.00 | 0.79 | 79/101 |
| s06 | 1.00 | 0.81 | 80/101 |

Every Garden, inbox, stage and cross-arrival target in s05/s06 came from
agent reading (no product read reaches them — JF-14). Cross-course links
came almost entirely from reading in all runs. The product's connection
surface (`related` one-hop over explicit ids, unranked; lexical `search`)
contributes roughly three quarters of MUST recall; the last quarter is
agent work the product cannot do.

Explanation grades (0 wrong · 1 partly · 2 correct; all heuristic misses
plus all must-not rows human-graded; heuristic-covered rows accepted
after a 12-row spot-check per run found no false covers):

- s05: 36 miss rows → 27×2, 9×1, 0×0; must-not row (C04 study-plan) 1.
- s06: 52 miss rows → 38×2, 14×1, 0×0; must-not rows 1, 2, 2.
- s03: 32 miss rows → 24×2, 8×1, 0×0; must-not rows 1, 2, 2, 2, 1.
- s02: 7 rows → 7×2.
- Total: 136 reviewed rows, 101×2, 35×1, 0×0. No explanation was wrong;
  partials are terse identifications (target named, mechanism unstated) or
  answers that identify a workspace without answering its question (A06,
  A21, A23 in both C runs).

Must-not returns are knowing contrasts, not confusions: every one carries
a reason that states the unrelated meaning (kernel/consistent wording) or
a reasoned analogy (study-plan as proportional shares, returned by all
three runs independently). The oracle's MUST_NOT verdicts stand — a study
timetable is not a scheduling algorithm — but the C04 trio is reasonable
disagreement, recorded as such. A24 (sourdough) correctly returned empty
in all three runs.

Provenance (sampled 12 rows/run; 1 = cited material refs resolve and
support the claim): s05 12/12 (material refs + quotes; `surfaced by:`
lines are discovery records, unresolvable by design, and explain its 0.64
resolvable rate); s06 7/12 (five rows cite only a `los …` command, no
material ref — explains 0.49); s03 5/12 (seven rows cite no evidence at
all, though its cited refs all resolve); s02 7/7. Unjudged returns in
top ranks are consistently plausible (mock exams, exercise banks, filing
locations) — judged precision ≈ 1.0 is the fair precision figure, not
raw P@5.

## 3. Retrieval (judged)

Grades: `retrieval-grades-<run>.json` in this directory (2 correct with
evidence · 1 partly · 0 wrong · null unanswered). Worksheets stay outside
the repository because they embed oracle judge notes.

| Run | Answered | Grade 2 | Grade 1 | Grade 0 | evidence_ok | points (heur.) | provenance |
|---|---|---|---|---|---|---|---|
| s02 | 12 (Q01–Q12, plan scope) | 11 | 1 | 0 | 0.28 | 0.94 | 0.98 |
| s03 | 36 | 35 | 1 | 0 | 0.78 | 0.99 | 0.82 |
| s04 | 36 | 35 | 1 | 0 | 0.83 | 0.97 | 1.00 |

Not a single wrong answer in 84. The three grade-1s are the same question
(Q12): all runs show the partial work correctly but miss the
exercise-bank authorship/solution-status point — a consistent blind spot
for authorship metadata. Later-answer discovery (Q10), cross-domain
synthesis (Q03, Q22, Q32), chronology handling (Q04/Q05/Q18/Q19/Q35) and
the seven-item inbox triage (Q27) are all correct, many with bonuses
(conflict flagging on Q07, relapse bonus on Q04).

All 17 forbidden-claim flags are false positives on reading: old views
quoted as wrong, numbers named as guesses, analogues listed under an
explicit analogy heading, mastery explicitly refused. Keyword
forbidden-claim detection has a 100% false-positive rate on these runs;
it cannot be used without a judge. s03's citations include
single-letter fragment refs on some questions (correct answers, noisy
citation strings) — a minor citation-hygiene note, already visible in
its 0.82 provenance mean.

S02 MUST_NOTs hold in all runs: no mastery declared (Q11/Q23 refuse it
explicitly), no exam fact taken from prose (Q07/Q08 answered from module
records).

## 4. Scenario grades

Outcome classes: PASS, PASS_WITH_FRICTION (PWF), FUNCTIONAL_FAILURE,
ROBUSTNESS_FAILURE, USABILITY_FAILURE, PERFORMANCE_FAILURE. MUST/SHOULD/
MUST_NOT verdicts below paraphrase the oracle; indices follow the
expectation file order.

- S00 (orientation; s00/s02/s04, all PWF — confirmed). Correct
  five-line answers from the task-shaped entry in 6–9 calls, no writes.
  Separation of stopping-point from planned-next shown in all runs;
  registration-window remark not recorded (SHOULD, minor). s00's
  pointer/map disagreement is the H1 harness artefact (JF-22), correctly
  surfaced, not caused, by the consumer.
- S01 (health; s00/s02 ROBUSTNESS_FAILURE, s07 PWF — confirmed).
  Validator/baseline/canonical-clean MUSTs met in all runs. The failures
  are the setup-recovery SHOULD (the documented interpreter override
  cannot repair a half-built venv — JF-01) and the test-suite side
  effects and redness (JF-02/JF-03). s07's PWF stands: its setup worked
  first time and it filed the suite findings separately.
- S02 (retrieval; s02/s03/s04, all PWF — confirmed). §3 is the record.
  Friction (unranked substring search, thin `related`, invisible
  inbox/Garden, stage-note content via cat only) is confirmed product
  behavior (JF-14, JF-24).
- S03 (canon connections; s03/s05/s06, all PWF — confirmed). §2 is the
  record. The source-recording SHOULD is met (all runs log
  product-vs-reading per target).
- S04 (capture routing; s02/s03, PWF — confirmed). Legitimate landing
  via a receipted gateway write into the matching stage note, A09 links
  recorded, exact-change approval obtained. The UI-only-application
  SHOULD is met only in substance (a documented agent path was chosen;
  neither run states the UI-only rule explicitly).
- S05 (arrival filing; s03, PWF — confirmed). A24 correctly unfiled and
  unlinked; nothing silently dropped; connection records kept;
  continuations recognized as stage work. Appends to durable notes went
  through `note.revise` with approval and changed no existing wording
  (MUST_NOT holds), but third-party excerpts now sit in learner notes
  under her authorship — a provenance wrinkle of the missing
  capture-to-note path (JF-25).
- S06 (duplicates; s02/s03, PWF — confirmed). A29/A11/A18 all
  identified; no second p-value note; nothing deleted; the repeated
  capture was reported, not re-filed. Both runs filed A18 as a new
  pointer seed because no capability can append to or retire a seed.
- S07 (later answers; s03, PWF — confirmed). A02 recorded against the
  ridge question and its stage, A21 against the paused SVD stage, A01
  SHOULD met; append-only, no silent edits of old bodies.
- S08 (correction; s03, PWF — confirmed). Wrong note identified in one
  search; original sentence intact (zero removed lines); correction
  appended via receipted revision. The linked-trail SHOULD is unmet —
  no capability can create a successor note — which is also what kept
  the run clear of JF-09.
- S09 (date conflict; s04, PASS — confirmed). Authoritative record
  answered with the conflicting prose named; no record change; conflict
  put to the learner.
- S10 (progress; s02/s04b PWF, s04 USABILITY_FAILURE — confirmed).
  s02/s04b recorded progress through the gateway with receipts, first
  or second attempt, stage left active, no hand edits. Both used
  `stage.note.write` rather than the named progress capabilities: the
  intent (gateway-recorded progress + receipt) is met, but there is no
  progress-with-content capability, and the recorded progress stays
  invisible to `resume` (JF-17). s04's write never happened (JF-05
  docs gap + H2 environment guard, which is not product behavior).
- S11 (project briefing; s04, PWF — confirmed). Workspace, project and
  inbox sources assembled with the coordination constraint; the inbox
  todo and workspace open questions came from direct file reads (JF-14).
- S12 (paused-module advice; s04, PASS — confirmed). Limited-resume
  recommendation with deferral/dependency citations; nothing unpaused.
- S13 (scope triage; s03, PASS — confirmed). Correct required/helpful/
  defer buckets from unit scopes; no deferral recorded without
  agreement; no new plans.
- S14 (tidy-up; s02, PWF — confirmed). Asked first, touched only the
  two approved notes, metadata-only diff via `note.revise` with
  approval, meaning unchanged, nothing merged. Friction: no
  metadata-only capability exists (open authoring uncertainty, §8).
- S15 (semantic revision; s02, PWF — confirmed). All MUSTs met
  (diff + approval, `note.revise` with operator approval and receipt,
  original recoverable verbatim and in Git) plus the SHOULD. Friction:
  no successor-note path (same gap as S08), self-asserted approval, and
  receipts keep only hashes of the old version.
- S16 (AI shelving; s04 USABILITY_FAILURE, s04b PWF — confirmed).
  Prepare/import/validate passed in both; s04b completed end to end
  with receipt, seed unchanged, writes inside grants. The delivery
  format is undocumented (JF-07); s04b's first world was poisoned by a
  custom request id (JF-08). s04's apply never ran (JF-05 + H2).
- S17 (SIGKILL; s07, ROBUSTNESS_FAILURE — confirmed). Atomicity held:
  94 kills, every trial ended pre-state or fully committed, no partial
  state, recovery itself kill-safe, journals auto-reconciled. But
  lock-free reads show content recovery later undoes, and interfaces
  disagree (single `inspect`/`search` vs `bootstrap`/batch reads), while
  validator and status stay green (JF-21).
- S18 (fresh reads; s07, PWF — confirmed). CLI reads reflect edits
  immediately; stale-snapshot writes fail closed naming the actual
  snapshot. Hygiene warning fires, but the views' own stamp cannot show
  staleness (JF-18).
- S19 (rebuild; s07, PASS — confirmed). Byte-identical rebuild after
  deleting derived state (20 files, raw comparison). A genuine
  strength, matching S24.
- S20 (malformed input; s07, FUNCTIONAL_FAILURE — confirmed). Cases
  (a)/(b)/(d) named by the validator; binary capture stored safely.
  Cases (e)/(f) violate the core MUST: schema-valid, validator-clean
  states that break every projection read and all writes (JF-09,
  JF-10), with refusals misreported as retryable internal failures
  leaving orphan journals (JF-11).
- S21 (idempotency; s07, PWF — confirmed). Replay/new-key/conflict
  semantics all correct with intact ledgers; stale guards refuse
  without double-apply (exit 3 on the snapshot path; the revision path
  refuses REVISION_CONFLICT, same code). Diagnostics mislead (JF-19)
  and request ids are not unique; ledger-loss probes yield JF-13.
- S22 (concurrency; s07, PWF — confirmed). 30 racing writes: 10
  committed, 20 clean conflicts, zero lost/duplicated/partial, plus a
  clean read/write race. Friction (global snapshot serializes unrelated
  writes) is the documented design trading off against the MUSTs.
- S23 (scale; s08, PERFORMANCE_FAILURE — confirmed). Both SHOULD
  fail on the numbers, and both matter: content search already misses
  the interactive bar at 2,116 notes (11.7 s; incremental 8.8 s), and
  warm generate ≈ cold generate at every size (one-line edits cost
  full rebuilds). All 44 medians reportable, all exits 0. Full table
  in the run's S23 record; scale-up rows: content search
  0.36 → 1.77 → 11.69 → 227.83 s; metadata search roughly linear
  (0.38 → 0.59 → 1.25 → 4.68 s).
- S24 (determinism; s07, PASS — confirmed). Same HEAD, identical trees,
  byte-identical derived state across directories and timezones.
- S25 (session end; s04, PASS with limitation — confirmed). Correct
  review-stage-commit behavior on an unchanged tree, no push. The
  ledger-vs-canonical staging question is untested (no canonical
  writes happened in the run).
- S26 (errands; s00/s04 USABILITY_FAILURE, s02/s04b PWF — confirmed).
  Deadlines and caching notes take 1–3 calls everywhere. The inbox
  capture takes 13 calls plus an implementation read on first exposure
  in every no-hint run (JF-05); later runs reuse the recipe (2–3
  calls), which is why within-session counts understate the cliff.
  s04's capture never happened (JF-05 + H2).
- S27 (arrival connections; s05/s06, PWF — confirmed). §2 is the
  record; world-unchanged verified by observer diff (zero canonical
  delta, zero receipts); A24 empty in both runs.

## 5. Adjudicated findings

Verdicts: CONFIRMED (product defect/behavior, Minimized and code-checked
unless noted), ARTEFACT (harness/world, not the product), NOT CONFIRMED.
Consumer ids map to one judge finding (JF-nn) each; duplicates are
merged, not multiplied.

JF-01 CONFIRMED — setup cannot recover from its own first failure.
F-s00-baseline-01 + F-s01-setup-stale-venv-03 (2 runs, both minimized,
both retried). After `make setup` fails on a too-old interpreter, the
documented `PYTHON=` override fails identically (the venv target reuses
the half-built tree); only hand-deleting `.venv` recovers, which no
document mentions. First-run trap; high usability severity.

JF-02 CONFIRMED — `make test-fast` is red on a healthy installation.
F-s00-baseline-03 (34), F-s01-test-fast-red-02 (34 → 30 with the ambient
trace unset), F-s07-02 (18, AMBIGUOUS as filed). Decomposition, checked
against the author's own base-commit run: 17 failures couple the suite
to the maintainer's live learner data (missing workspace files and
receipts) — a real portability finding, since any other installation
fails them; 4 come from the inherited TRACEPARENT (JF-04's mechanism);
the remainder (causal resolver, diagnostic store, recovery conflicts,
abilities, format, gateway) fail identically on the base commit without
the eval package, i.e. pre-existing, not eval-caused. Verdict: the
"portable green check" the README promises does not exist; ownership
splits three ways as above.

JF-03 CONFIRMED — the test suite writes phantom operations into the
live installation. F-s00-baseline-02, F-s01-test-trace-leak-01 (with a
TRACEPARENT-unset retest proving independence), F-s07-01 (3 runs + the
author's container). Mechanism verified: the trace store binds to the
root under test and persists spans best-effort, and nothing unbinds it
for tests. ~135 spans per run surface as needs-attention AMBIGUOUS
operations. Gitignored, so status stays clean while the product's own
operations view alarms.

JF-04 CONFIRMED — ambient TRACEPARENT merges unrelated requests into
one misreported operation. F-s04-operations-merge-04, F-s03-diag-01
(both minimized and retried), plus the s00 observation. Mechanism
verified in code: the propagated context is adopted wholesale as the
operation identity, and the attempt span reuses the inherited span id
instead of minting a child, so every process in the session shares one
trace and one span; the operations list then groups by that id and
derives outcome/attention across unrelated requests (committed,
receipted writes shown AMBIGUOUS/needs-attention). The container
triggers it; any agent or CI environment exporting TRACEPARENT hits the
same wrong attention signal. W3C-correct behavior would parent, not
adopt.

JF-05 CONFIRMED — no agent can build a write envelope from the docs.
F-s00-baseline-04, F-s10-intent-hash-01, plus first-exposure friction in
s02 (S04), s03 (S04/S05) and s04b (S10). Verified: the approval hash is
named in WORKFLOWS but its algorithm appears only in
`contracts/gateway.py`; the request-scoped revision guards
(`capture-request:…`, `garden-request:…`) appear in zero documents;
the README's capture command is refused by design (exit 2, correct but
unbridged). Cost: 13 calls + an implementation read for a one-line
capture on first exposure. Audit line, per the conductor: the approval
subject is an operator assertion guarded by snapshot/revision checks,
not proof a human was present — an external safety layer reading it as
forgeable (H2) is a legitimate reading.

JF-06 NOT CONFIRMED — exit 0 on a refused write. F-s10-exit-code-02
(+ s02's matching note). Every UNCONFIRMED path in the evaluated
revision exits 2, and `los.py` propagates the code; no evidence file
captures an exit status. Most likely a piped-command misread. The
refusal envelope itself (ok:false, UNCONFIRMED, empty details) is real
— the empty details belong to JF-05.

JF-07 CONFIRMED — the manual-bundle delivery format is undocumented.
F-s16-delivery-format-03 (+ s04b's three blind attempts). Verified: no
delivery schema exists anywhere; the only specification is the
import validator in code; errors arrive one field at a time and one
names the wrong field (`producer` vs the request's `provider`). The
documented provider path for the documented workflow is unusable from
docs alone.

JF-08 CONFIRMED — a malformed AI-action prepare poisons all reads.
F-s04b-writes-02 (minimized, retried; world preserved). A free-form
`--request-id` option accepts an id the manifest schema rejects, the
bundle is persisted before the rejection, and from then on every
projection read fails while the validator reports clean; the remedy
text prescribes a maintainer contract bump, and no command cancels the
request. Same family as JF-09/JF-10 (validator-blind projection
breakage) with a worse trigger (one optional argument).

JF-09 CONFIRMED — the documented supersede path breaks the product.
F-s07-06 (minimized to one frontmatter line, retried). A schema-valid
`supersedes` entry makes the projection emit record shapes the manifest
contract forbids (verified at the emitter: dict objects into a
string-array slot), failing generate/search/inspect/related/bootstrap
and all writes; the validator stays green. The real repository has zero
such notes, so the path never ran. High severity: following WORKFLOWS
§15 as written takes the installation down.

JF-10 CONFIRMED — schema and manifest disagree on `scope_sources`.
F-s07-07 (minimized to deleting the block, retried). Optional in the
unit schema, required by the manifest contract: validate-clean,
reads-dead, writes failing as internal errors. Same severity and shape
as JF-09.

JF-11 CONFIRMED — write-time defects misreported + orphan journals.
F-s07-08 (minimized, retried). Parse/projection failures during a write
answer INTERNAL_FAILURE retryable:true with "rollback incomplete"
(compare case (b), correctly VALIDATION_FAILED retryable:false, no
journal) and leave orphan crash journals; the recommended exact retry
fails again, then goes STALE_SNAPSHOT once fixed. Inconsistent error
mapping plus litter with no self-cleanup.

JF-12 CONFIRMED behavior, docs gap — one defect blocks all writes.
F-s07-09 (AMBIGUOUS as filed; kept as behavior, not defect). Whole-tree
shadow validation refusing an unrelated capture, and reads refusing
rather than silently omitting, is coherent fail-closed design and the
file is always named. What is missing is any statement that this is
the design — nothing tells the operator an unrelated note's error
disables capture. Fix the docs, not the behavior.

JF-13 CONFIRMED mechanism with world-artefact framing — ledgers are the
sole idempotency memory. F-s07-11. Verified: replay consults only the
ledger row ("no row" means "never happened" — the committed receipt is
invisible without it), nothing rebuilds ledgers from receipts, neither
file is gitignored, and the validator stays silent over duplicate keys.
Downgraded in one respect per the conductor: ledgers start untracked
only because the synthetic history has no gateway writes (in the
author's tree they are tracked). The mechanism — loss or revert of the
ledgers silently re-arms consumed keys — is real either way.

JF-14 CONFIRMED — Garden, inbox and stage-note content have no read
path. F-s05-01, F-s06-01 (both minimized, retried) plus friction in
s02/s03/s04. Verified in code and schema: bootstrap carries counts
only, stage records carry the note path only, no inspectable/searchable
record exists for any of the three, and content search covers durable
notes only. 16+ learner items per world are reachable solely by `cat`,
against OPERATOR's own rule. This is the largest measured contributor
to agent reading (≈45% of connection targets) and the top cross-run
usability finding.

JF-15 CONFIRMED behavior, minor — `related` membership is
one-directional. F-s05-02 (AMBIGUOUS as filed). Verified: reverse
workspace→note visibility exists only via the note's own declarations;
no document defines the direction. Document or symmetrize.

JF-16 ARTEFACT + docs note — missing domain atlas. F-s05-03
(AMBIGUOUS as filed). The world builder removes generated views after
verifying them, so a fresh world starts viewless by harness design —
not a product defect. The fair product residue: entry docs that say
"open the atlas" should say "build views first" on a fresh install
(the hygiene warning already signals it).

JF-17 CONFIRMED — recorded progress invisible to `resume`.
F-s04b-writes-01 + s02's S10 observation (2 runs). `resume` renders
requirement-linked observations; the stage has no authored
requirement, so evidence stays "none recorded" and the workspace aim
still assigns the finished example; no capability advances the
workspace aim, and the observe path needs the missing requirement.
The write succeeds but "move me on" is half-served.

JF-18 CONFIRMED — the Generated stamp cannot show staleness.
F-s07-04. Verified: the stamp is the last-commit time, byte-identical
across rebuilds of different content, so the README's human-fallback
check cannot work after uncommitted edits. The validator's hygiene
warning is the real signal; the view itself carries none.

JF-19 CONFIRMED — `los operations` mislabels settled outcomes.
F-s07-10. Verified: a committed write settles only when the live
published manifest shows its exact snapshot — i.e. after regenerating
views — so every CLI write reads BLOCKED/needs-attention until then,
and all but the latest stay that way permanently; a definitive
idempotency conflict reads AMBIGUOUS; reused request ids (accepted:
ids are not unique) merge explanations. No document describes the
surface at all (zero hits). Medium severity: the only surface that
explains a request.

JF-20 CONFIRMED, low — manifest-as-directory crashes four commands.
F-s07-05 (minimized, retried). Contrived input, raw tracebacks from
generate/status/validate instead of the documented delete-and-rebuild
recovery. Realistic corruptions (truncated/deleted) are handled.

JF-21 CONFIRMED — reads show uncommitted state and disagree with each
other. F-s07-03 (minimized, retried; extends AUTHOR-NOTES 4.3 with the
conductor's no-discovery-credit caveat on the exposure itself).
Verified: reconciliation runs on operator-lock acquisition, which the
query reads (single `inspect`, `search`, `related`) skip while
batch/bootstrap/plan reads take — so after a kill the interfaces
report different states, and validate/status stay green and silent.
Atomicity itself held everywhere (94 kills, zero partials, kill-safe
recovery): this is an isolation/observability defect, not a
durability one. New detail for repair: single-ID and batch `inspect`
take different lock paths and can disagree with each other.

JF-22 ARTEFACT + fair question — s00 pointer/map disagreement. The
observed disagreement is the H1 builder bug (world `9a85f012`), an
evaluation defect for adjudication. The product question it raises —
nothing flags a stale pointer — is fair but unplanted; repair may
treat it as an enhancement, not a regression.

JF-23 CONFIRMED, minor — small read-surface inaccuracies. (a) Stage
`notes_updated` is the last-commit date, not the write date (consumer
report; verified at the projector). (b) The atlas-question payload
schema is an untyped object — effectively undocumented (consumer
report; verified). (c) Deprecated state is absent from search output
(the projections emit no state field — verified). (d) `note.revise`
accepting revision 0 is the legitimate no-recorded-revision baseline
backstopped by the snapshot guard, not a bypass (consumer question;
answered from the guard code).

JF-24 CONFIRMED behavior, not defect — lexical search coarseness.
Multi-word queries conjoin substrings per record (verified), so natural
phrasing often returns nothing, short stems collide (`MAP` vs maps),
and results carry no rank or snippet on the metadata path. Working as
designed; the design is what pushes corpus-wide questions onto full
manual reading (measured in S02/S03 across three runs).

JF-25 CONFIRMED gap — no capture-to-note or successor-note path.
Observed, not filed, across s02/s03 (S05/S08/S15): WORKFLOWS routes
work to successor notes and supersedes trails, OPERATOR makes general
AI read-only, `review.apply` is UI-only, and no agent capability
creates a durable note from a capture or a superseding note — so
consumers revise in place, append third-party text under the learner's
authorship, or skip the trail. This is the structural counterpart of
the open authoring uncertainty; JF-09 is what happens when the trail
is hand-built instead.

Counted verdicts: 22 CONFIRMED (incl. 3 behavior/docs-gap, 2 minor,
1 structural gap), 2 ARTEFACT (JF-16, JF-22, each with a small product
residue), 1 NOT CONFIRMED (JF-06), plus the scale PERFORMANCE_FAILURE
(S23, no failure record filed — the classification is the finding).

## 6. Friction summary

45 scenario results aggregated in `friction.json`. Repeated tags
(2+ runs): doc-contradiction (6 runs), hidden-prerequisite (6),
missing-capability, needs-implementation-knowledge, unhelpful-error,
setup-failure, unclear-safety, unclear-terminology, redundant-calls,
unnecessary-exploration, unstable-output-format,
manual-generated-file-inspection, other. The most-read implementation
file by far is the gateway contract (approval hash + revision guards —
JF-05); the AI-action service (delivery validation — JF-07) is second.
Median tool calls: S00 8, S01 14, S02 42, S03 45. Questions asked to
the learner: 0 nearly everywhere (scripted replies sufficed).
Per the conductor notes, write friction from runs 4b–7 is hinted or
memory-primed and is not pooled with the no-hint runs; the S26
first-exposure cliff (13 calls + implementation read) comes from the
no-hint runs only. S08's counts measure harness operability, not
product discoverability, and are excluded from the same pooling.

## 7. Blindness and leak scan

All nine runs stand blind:true. The two H3 matches in s03 condense the
learner's own note/stage sentences (checked against the cited sources);
the H5 match in s05 is a 44-character arrival summary used for a
different probe, with transcript evidence of independent wording. With
hundreds of oracle patterns, two short-phrase overlaps and one
adjudicated line are consistent with independent writing, not oracle
exposure — the judge concurs with the conductor. No run's content or
score changes. The keyed self-test leak scan over all commits touching
`tests/eval/` (minus the one H5 adjudication) is the check of record
and passes; see `run.json` deviations for the exact command.

## 8. For the repair sessions

No product code was changed here (judge session). Suggested order,
severity-first; each item needs a failing reproduction before the fix
per the campaign rules:

1. Validator-blind projection breakage (JF-08/JF-09/JF-10): validate
   must reject what the manifest cannot publish (or the emitter must
   stop emitting it). Repros are one-liners; worlds/snapshots are in
   s07 (S20 e2/f2) and s04b (S16 poisoned world, owner machine +
   run snapshots).
2. First-run traps (JF-01 setup recovery; JF-05 envelope docs; JF-07
   delivery schema + error naming). Small, high-leverage, doc-heavy.
3. Read-path gaps (JF-14 garden/inbox/stage reads; JF-25
   capture-to-note/successor path — needs Aram's design call first,
   since it touches the read-only boundary and the open authoring
   uncertainty; JF-17 resume-after-progress).
4. Diagnostics honesty (JF-04 trace parenting; JF-03 test binding;
   JF-19 operations labels + request-id uniqueness; JF-21 read
   reconciliation split). Note JF-04 and JF-19 interact: fixing the
   grouping changes what "settled" means.
5. Robustness details (JF-11 error mapping + journal cleanup; JF-13
   ledger rebuild/validation; JF-20 directory-shape crash; JF-18
   stamp content; JF-23 small items; JF-12/JF-15/JF-16/JF-24 doc
   statements).
6. Scale (S23): content-search growth and the missing incremental
   benefit. No threshold is contractual; the judge's call is that
   2k-note interactive latency matters. Confirm the mechanism against
   the implementation before optimizing (the consumer's unindexed-scan
   read of the numbers is not a code finding).
7. Suite health (JF-02): decouple pilot-replay from maintainer data
   (or mark it full-repo), then triage the base-commit failures. The
   campaign cannot use a red suite as a health signal.

Open authoring uncertainties, unchanged by this campaign: the intended
agent path from capture to durable note (measured, still unresolved);
formatting-only edits (S14 worked around it via `note.revise`); the
session-end ledger scope on a write-bearing tree (S25 ran clean —
untested). Do not treat repair as license to resolve these without
Aram; the CRITIQUE-POINTS rule (§17 in OPERATOR.md) applies.

NOT TESTED anywhere in this campaign: the Obsidian UI (all of it),
consumer token cost, real multi-month use, and timing stability across
machines. The clean results worth keeping: byte-identical rebuilds
(S19), deterministic builds (S24), zero lost/duplicated writes under
concurrency (S22) and SIGKILL (S17), and a retrieval surface that
answered 84/84 without a wrong answer.

## 9. Artefacts and grading record

- This directory: `run.json`, `friction.json`,
  `retrieval-grades-{s02,s03,s04}.json`, `FAILURE_ANALYSIS.md`.
- Per-run scorer outputs committed into the nine run dirs:
  `metrics-connections.json` + graded `connections-worksheet.md`
  (s02/s03/s05/s06), `metrics-retrieval.json` (s02/s03/s04).
- Retrieval worksheets and the oracle stayed outside the repository
  (the worksheets embed oracle judge notes, which the leak scan
  forbids in `runs/`); grades for them live in this directory instead.
- Explanation grading: all 120 keyword-heuristic misses + all 9
  must-not rows human-read; heuristic-covered rows accepted after
  clean spot-checks (12 rows/run). Provenance: sampled 12 rows/run
  against the reference world. No grade was filled for a row the judge
  did not read; unfilled worksheet cells are documented in each
  worksheet's grading note.
- Reference world for id resolution: the s08 scale-0 build
  (`13ad2fca…`). s00's world predates H1; its two study-map readings
  were adjudicated as artefacts (JF-22).
- Verification basis: product code read at `200a361…` (exit mapping,
  trace parentage, resolver rules, lock/reconcile split, record
  schema, emitter shapes, ledger replay, stamp source). Greps over
  docs confirm each "undocumented" verdict (zero defining hits).
