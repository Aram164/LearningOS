# Task IR P2 — controlled agent-operator benchmark protocol

Preregistered 2026-10-28, before any P2 measurement. Changes after first
results must be recorded as amendments with reasons, never silently folded in.

## Understanding

P1 proved Task IR can run four typed operations safely through existing
LearningOS machinery. It did not prove an agent operator finishes real tasks
with less effort. P2 measures that, and only that. No feature work is part of
P2: if the numbers do not justify the abstraction, the finding is to simplify
or reject it, not to expand it.

## Frozen reference

| Item | Value |
|---|---|
| Core | `e895758126e332f8a8a9d7b34d4f1916337cee45` (`codex/task-ir-p1-experiment`) |
| UI | `3c9a5f664c147790c490fae0a256e7764b4b9157` (matches `repository/.github/ui-revision.txt`) |
| Draft PR | #71, stacked on #64; preserved unchanged by P2 |
| Fixture | Synthetic only: `tests/conftest.py:build_mini_repo` + `tests/repo_builders.py:material_fixture` |

P2 runs in disposable copies. The primary learner checkout is never a subject.

## Arms

All arms receive the same task wording, the same known IDs, the same starting
snapshot, and the same review condition: a scripted reviewer approves the
identical check record in every arm that reaches a write. No arm may skip the
review step in its count.

| Arm | Workflow |
|---|---|
| A — manual | Individual `tools/los.py` reads; writes via `tools/seal_envelope.py` (`--guards auto --check-out`, then `--guards-from … --submit`) |
| B — plan runner | Reads as one `tools/agent_run.py` plan (schema v2); writes via the same seal flow as A |
| C — Task IR P1 | One typed spec via `tools/agent_run.py --task … --task-phase preview`, then `--task-phase apply` when a write is approved |

Decision: Arm B is the comparator that matters. A Task IR win only over Arm A
would credit Task IR for the existing runner's value.

## Eligibility

P1 requires known unit/stage IDs and authored runtime targets. The headline
corpus therefore supplies known IDs in all arms, and any efficiency claim is
scoped to tasks of that shape. Discovery-heavy work is measured separately
(P2-04, P2-12) as boundary evidence and excluded from the headline claim.

## Corpus (12 scenarios)

| ID | Scenario | Headline |
|---|---|---|
| P2-01 | Inspect one unit (`context.inspect` shape) | yes |
| P2-02 | Inspect one stage | yes |
| P2-03 | Find the unique route of one stage | yes |
| P2-04 | Find routes of a whole unit; write requested via discovery — ambiguous, must not write | no (boundary) |
| P2-05 | Propose a runtime session for unit+stage | yes |
| P2-06 | Propose a session for an unknown stage — must refuse | no (boundary) |
| P2-07 | Patch a route discovered uniquely in P2-03's shape (preview, review, apply) | yes |
| P2-08 | Patch a route named literally | yes |
| P2-09 | Patch a route to its current value — must settle `unchanged`, zero receipts | yes |
| P2-10 | External change between preview and apply — must not commit the stale intent | no (safety) |
| P2-11 | Patch on an unknown unit — must refuse; error text must never read as `unchanged` | no (safety) |
| P2-12 | Malformed input (undeclared field; `$…` expression) — must refuse before dispatch | no (boundary) |

Interruption and lost-response recovery stay deterministic safety exercises.
P1's suite already covers them; they are not timed and not part of the
efficiency claim.

## Oracles

Each scenario has a state oracle independent of the arm's code path. It reads
canonical YAML directly and checks, as applicable: canonical fingerprint
unchanged or changed only in the intended route field; every other route and
stage field preserved; receipt count delta; settled status classification.
The pilot must show each oracle passes a correct run and fails a deliberately
mutated result. An oracle that cannot fail proves nothing.

## Metrics

Per trial, captured by the harness, never by agent self-report:

- invocations: every operator-issued subprocess, with argv, exit code, and
  stdout/stderr byte counts (one invocation = one round trip);
- input/output/reasoning/cache tokens, in the live phase only, from the agent
  harness's own session records; a category the harness cannot expose is
  recorded as missing, never estimated;
- wall-clock milliseconds per invocation and per trial;
- oracle pass/fail per check; manual interventions; safety violations
  (unauthorized write, falsely verified commit, approval misrepresentation).

Task-spec and plan construction is part of the trial. In the live phase the
clock and token count start at task handoff, not at first tool call.

## Phases

**P2a — instrumentation pilot (this increment).** Scripted reference operators
execute every corpus scenario in every arm on disposable fixtures. This
validates the corpus, the oracles, and trace capture, and yields deterministic
interface quantities (invocations, returned bytes, wall time). These are
interface mechanics, not LLM token savings, and must never be reported as such.

**P2b — live phase (next gate, not started).** A real agent harness runs the
same corpus, same model and instructions, arm order varied per scenario,
3 repetitions per scenario per arm. Entry criteria: token capture from harness
session records demonstrated on one trial per arm; reviewer condition scripted
identically; trial budget approved by Aram.

## Analysis and decision rules (live phase, preregistered)

Paired by scenario. Repetitions estimate within-scenario variance; the
scenario is the unit of comparison (n = headline scenarios), reported as
per-scenario distributions and a median paired difference, not a pooled mean
over trials.

Retain P1 as a candidate only if, against the strongest existing comparator
per scenario (the better of A and B):

- median token reduction is at least 20% (target carried from the P1 repair
  report's predeclared P2 targets), and
- median round trips fall by at least 30%, and
- correct completion does not fall, and
- safety violations are zero.

If benefit concentrates in one scenario class, the recommendation is to
simplify P1 to that class. If neither target is met, the recommendation is to
reject the abstraction and keep the runner. Thresholds are decision heuristics
chosen in advance, not significance claims.

## Risks

- Python startup dominates wall time on synthetic fixtures; wall time is
  reported but never decides alone.
- Summary truncation can hide the very IDs an arm needs; a fallback expansion
  counts as an invocation like any other.
- A blocked session proposal can be the truthful result; oracles classify the
  outcome identically across arms instead of demanding a session exist.
  ASSUMPTION: the synthetic fixture has no authored runtime target, so P2-05
  exercises the blocked/refused shape; the authored shape stays covered by
  P1's suite.
- Scripted operators are ideal operators. P2a numbers bound interface
  mechanics; they do not predict live agent behaviour.

## Out of scope

`plan.compose`, new operations, new approval or transaction machinery, UI
changes, learner data, merging or closing PR #71/#64, and any production
readiness claim.

## Amendments

Recorded before any live (P2b) data existed, per the amendment rule above.

- 2026-10-28, corpus completion: P2-04 is implemented with a multi-route
  fixture extension (a second source and route in the synthetic source map;
  unit-level discovery then returns two routes). P2-05 now uses an authored
  `runtime_target` on the fixture stage, so it exercises a successful
  `runtime-session-v1` proposal as a headline scenario. The earlier
  unauthored-refusal shape leaves the corpus: P1's suite already covers it
  (`test_session_propose_without_runtime_target_refuses_cleanly`) and P2-06
  covers the refusal class. No threshold, arm, or decision rule changed.
- 2026-10-28, token capture mechanism: live trials run as separate headless
  `muse exec` sessions, one per trial, rooted at a disposable fixture
  workspace. Token totals are summed from that session's own
  `session.jsonl`: one usage record per `model_completed` event
  (`input_tokens`, `output_tokens`, `cached_tokens`, `cache_read_tokens`,
  `cache_write_tokens`, `reasoning_tokens`), deduplicated by event identity.
  Verified against a live session log on 2026-10-28; a naive sum over every
  usage-shaped node double-counts, and per-call `input_tokens` includes the
  cached share, which is therefore reported separately, never added twice.
