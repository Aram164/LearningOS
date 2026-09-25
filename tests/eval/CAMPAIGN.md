# Evaluation campaign — session plan

Each session is a **separate, fresh** cloud session. Blindness between them is
the point: consumer sessions never see the oracle, and repair sessions never
see the consumers' conversations, only their recorded runs.

Spend more on trying to break LearningOS than on changing it. No patch
without an observed failure, a measured bottleneck, or a clearly violated
invariant.

## Sessions

| # | Role | Plan | Key needed | Output |
|---|---|---|---|---|
| 0 | Baseline cartographer | B | no | `runs/s00-baseline-<date>/` |
| 1 | Test-world author (this package) | — | writes it | `tests/eval/` |
| 2 | Blind consumer — novice | N | no | `runs/s02-novice-<date>/` |
| 3 | Blind consumer — serious learner | L | no | `runs/s03-learner-<date>/` |
| 4 | Blind consumer — resuming another user's work | R | no | `runs/s04-resume-<date>/` |
| 5 | Connection experiment A | C | no | `runs/s05-connections-a-<date>/` |
| 6 | Connection experiment B (independent repeat) | C | no | `runs/s06-connections-b-<date>/` |
| 7 | Abuse / failure investigator | X | no | `runs/s07-abuse-<date>/` |
| 8 | Scale investigator | P | no | `runs/s08-scale-<date>/` |
| 9 | Agent-friction investigator | F | no | `runs/s09-friction-<date>/` |
| 10 | White-box adjudicator | — | **yes** | `runs/s10-judge-<date>/FAILURE_ANALYSIS.md`, metrics |
| 11–12 | Repair sessions | — | yes | commits + `PATCH_LEDGER.md` |
| 13 | Hostile verifier | reruns | yes | `runs/s13-verify-<date>/` |
| 14 | Clean-room consumer on the final revision | N + C | no | `runs/s14-cleanroom-<date>/` |

Sessions 2–9 are independent and can run in parallel. Session 10 needs all of
them. Session 9 was omitted by owner decision (see run ledger); adjudication and repair proceed on Sessions 0–8. Repair sessions build worlds with `--source-rev WORKTREE` so the same
data exercises the patched product; session 13 starts again from the
unmodified scenarios.

Suggested budget split: world construction ~10%, blind consumers (2–4) ~20%,
connections (5–6) ~20%, abuse (7) ~15%, scale and friction (8–9) ~10%,
adjudication and repair (10–12) ~15%, verification and clean room (13–14) ~10%.

## Kickoff prompts

From session 5 on, a consumer chat needs only a short kickoff; the standing
instructions are in [`public/SESSION-BRIEF.md`](public/SESSION-BRIEF.md) and
the mechanics in [`public/CONSUMER-PROTOCOL.md`](public/CONSUMER-PROTOCOL.md).
Two authorizations stay in the kickoff because they must come from the
campaign owner in person: computing the approval value for learner-approved
writes, and pushing the session branch past the pre-push hook that cannot run
in cloud containers.

    Blinded LearningOS evaluation, session <N>.
    git fetch origin claude/learningos-eval-benchmark-swapck and base your working
    branch on it. Read tests/eval/public/SESSION-BRIEF.md, then follow it.
    Run plan: <PLAN>. Run id: <run-id>. Role: <role>.
    I authorize you to compute any approval value LearningOS requires for a write
    the scripted learner approved — that records her approval, it does not bypass it.
    If the repository's pre-push hook blocks your push because the paired
    obsidian-ui checkout is missing, push your session branch with --no-verify.

Sessions 0–4 used the longer inline prompt (the same content as the brief).

For session 10 (judge), paste "Prompt 3 — white-box judge and repairer", give
it `LOS_EVAL_ORACLE_KEY`, and add:

> Open the oracle with `tests/eval/tools/oracle_vault.py open --out
> ~/los-eval/oracle`, read its README and AUTHOR-NOTES first, merge every run
> branch listed in the run ledger below, score every run with the scorers in
> `tests/eval/metrics/`, grade the worksheets, and write FAILURE_ANALYSIS.md
> before changing any code.

## What gets measured, and how honestly

| Dimension | Instrument | Nature |
|---|---|---|
| Connection quality: Recall@5/10, P@5, judged P@5, must-not rate, MRR, by category and lexical overlap | `score_connections.py` on `connections.jsonl` | MEASURED against the oracle |
| Explanation correctness | worksheet, graded by the judge; keyword coverage as a HEURISTIC aid | OBSERVED (judged) |
| Provenance correctness | cited refs resolve in the world (MEASURED); citation supports the claim (judged) | mixed |
| Retrieval success | `score_retrieval.py`: evidence hit, answer points (HEURISTIC), forbidden-claim flags; judge grade 0–2 | MEASURED + judged |
| Agent friction: tool calls, commands, retries, docs, implementation files, questions to the learner, minutes | `friction.py` over scenario results | MEASURED as self-reported by the session |
| Corrective prompts | `questions_asked_to_learner` + scripted replies used | MEASURED (self-reported) |
| Internal behaviour: receipts, request ids, journals, derived changes, writes without receipts | `observe.py` snapshots and diffs | MEASURED |
| Atomicity under SIGKILL | `interrupt_probe.py` outcome classes | MEASURED |
| Derived-state rebuild and determinism | `determinism.py` | MEASURED |
| Scale and incrementality | `scale_bench.py` medians with spread; derived bytes | MEASURED (noisy) |
| Wall-clock time per operation | `scale_bench.py` | MEASURED only when spread < median |
| Consumer token cost | not visible from inside a session | NOT TESTED |
| Obsidian UI: discoverability, pane layout, click paths, latency | none in this environment | NOT TESTED — use the live Obsidian battery |

## What cannot be tested automatically

- Whether an explanation is *right* (the judge reads the worksheet).
- Whether a consumer "understood" something beyond what it did and recorded.
- Anything visual or interactive in Obsidian.
- Real multi-month use: the world's history is synthetic and its notes are
  cleaner than a real learner's.
- Timing stability in shared containers; treat single timings as anecdotes.

## Guardrails that apply to every session

- Never edit the learner's real data. Worlds live outside the repository.
- Consumer sessions never patch LearningOS, never bypass approval or safety
  mechanisms, never force-push, never push to `main`.
- Repair sessions: failing reproduction first, smallest general fix, no
  special-casing of synthetic content, no weakened tests, full checks before
  every push, before/after metrics in `PATCH_LEDGER.md`.

## Run ledger

Consumer sessions must not open other runs' branches before finishing their
own. The judge merges every run branch before scoring.

| Session | Plan | Run id | Branch | World HEAD | Notes |
|---|---|---|---|---|---|
| 0 | B | `s00-baseline-2026-09-24` | `claude/optimistic-mayer-065kyv` | `9a85f012…` | built before harness change H1 |
| 2 | N | `s02-novice-2026-09-25` | `claude/relaxed-maxwell-63p0mh` | `13ad2fca…` | after H1, before H2 (eval `3a53589`); owner authorized approval values mid-run |
| 3 | L | `s03-learner-2026-09-25` | `claude/zealous-einstein-7h57rx` | `13ad2fca…` | after H1, before H2 (eval `3a53589`); owner authorized approval values mid-run |
| 4 | R | `s04-resume-2026-09-25` | `claude/adoring-thompson-fa2n41` | `13ad2fca…` | before H2: agent environment refused the approval hash; no write completed (S10, S16 apply, S26 goal 2) |
| 4b | O (S10, S16, S26) | `s04b-writes-2026-09-25` | `claude/eval-s04b-writes-2026-09-25` | `13ad2fca…` | after H3 (eval `658db28`); local run (H4), opened an earlier memory note before starting |
| 5 | C | `s05-connections-a-2026-09-25` | `claude/eval-s05-connections-a-2026-09-25` | `13ad2fca…` | after H3 (eval `658db28`); local run (H4), opened an earlier memory note before starting; one leak-scan match adjudicated (H5) |
| 6 | C | `s06-connections-b-2026-09-25` | `claude/eval-s06-connections-b-2026-09-25` | `13ad2fca…` | after H3 (eval `658db28`); local run (H4), memory index in context only |
| 7 | X | `s07-abuse-2026-09-25` | `claude/eval-s07-abuse-2026-09-25` | `13ad2fca…` | after H3 (eval `658db28`); local run (H4), memory index in context; started before the H4 brief |
| 8 | P | `s08-scale-2026-09-25` | `muse/eval-s08-scale-2026-09-25` | `13ad2fca…` | after H4 brief; local run, blind, check_run clean; 4 scale worlds (scale-0 head shown, all heads in run environment.worlds); --no-verify commit (hook env) + push (authorized); S23 PERFORMANCE_FAILURE, judge to confirm; timings non-comparable (H4) |
| 9 | F | — | — | — | OMITTED by owner decision 2026-09-25; partial run discarded uncommitted and excluded from adjudication |

## Harness changes

Every change to the world, protocol or scorers after a run started is listed
here, so the judge can tell a product finding from an artefact of the harness.

- **H1 (2026-09-25).** The world builder wrote a study map's earlier
  progress state *after* its final state when both carried the same date, so
  `study-map-os-l02` and `study-map-statlearn-l05` were built one stage behind
  the corpus (stage 01 current instead of stage 02), disagreeing with the
  resume pointer. Fixed: history is written first and must be strictly
  earlier; the self-test now compares every built study map with the corpus.
  World HEAD at the pinned product revision moved from `9a85f012…` to
  `13ad2fca…`. Runs on `9a85f012…` (session 0) saw the inconsistent maps; a
  "resume pointer vs study map" observation from those runs is a harness
  artefact, though whether the product should flag such a disagreement
  remains a fair question.
- **H2 (2026-09-25).** Session 4's agent environment refused to compute the
  value LearningOS requires an operator to attach to an approved write,
  reading it as self-approval, so none of that run's writes happened.
  `public/CONSUMER-PROTOCOL.md` now states that a scripted learner approval is
  a real approval and that recording it in the product's required form is the
  operator's job. Runs after H2 received this sentence; their friction on
  discovering the approval mechanism is therefore not comparable with runs 0,
  2, 3 and 4, which measured it without the hint.
- **H3 (2026-09-25).** The self-test's leak scan used the oracle's expected
  mentions (the short phrases a correct connection explanation should contain,
  which `score_connections.py` rewards) as leak markers everywhere, including
  consumer output. Run 3's `connections.jsonl` tripped it twice. Both times the
  consumer had condensed a sentence from the learner's own notes into the same
  words the oracle author used. No judgment reason, judge note or scenario
  expectation appeared in any run. Fixed in `selftest.py`: `runs/` is scanned
  for the oracle's own sentences only; expected mentions remain leak markers
  in public files, the corpus, built worlds and every other committed path. A
  toy self-test covers the split. No run's content or score changes; the
  judge's worksheets show the two matches as ordinary mention coverage.
- **H4 (2026-09-25).** From session 4b on, consumer chats run locally, on the
  owner's machine, not in separate cloud containers. They share its
  filesystem, its other agent sessions and the assistant's persistent memory.
  That memory includes notes from the owner's earlier development work on
  LearningOS internals. Runs 4b, 5, 6 and 7 started with that memory index in
  context, and 4b and 5 opened one such note. One chat's shell slip deleted an
  untracked owner file outside its world; it was restored from earlier
  transcripts. `public/SESSION-BRIEF.md` now has a "shared machine" section:
  work only in your own world, no memory or transcript reads, explicit git
  paths, quoted heredocs, and a load record for timing runs. Runs 8 and 9
  received it. The judge should treat the implementation-knowledge friction of
  runs 4b, 5, 6 and 7 as possibly understated, and should not compare their
  timings with container runs.
- **H5 (2026-09-25).** One of the oracle's own one-line judgment reasons
  (44 characters, summarising a single inbox item) appeared verbatim in run
  5's `connections.jsonl`, as its reason for a different probe. Run 5's local
  transcript shows the phrase only in the session's own writes; no tool
  result ever showed it oracle text. The same transcript check on runs 4b, 6
  and 7 found no oracle text read either. Rather than loosening the scan
  again, `selftest.py` now honours `leak-adjudications.json`: each entry names
  one run file and the SHA-256 of one oracle sentence, so the list reveals no
  oracle text, and every other match still fails. A toy self-test covers it.
  No run's content or score changes.

