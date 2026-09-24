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
them. Repair sessions build worlds with `--source-rev WORKTREE` so the same
data exercises the patched product; session 13 starts again from the
unmodified scenarios.

Suggested budget split: world construction ~10%, blind consumers (2–4) ~20%,
connections (5–6) ~20%, abuse (7) ~15%, scale and friction (8–9) ~10%,
adjudication and repair (10–12) ~15%, verification and clean room (13–14) ~10%.

## Kickoff prompts

Start each consumer session on a branch of this repository that contains
`tests/eval/`. Paste the campaign's consumer prompt ("Prompt 2 — blind
first-time consumer"), then add:

> Your run plan is **<PLAN>**, run id **<run-id>**. The harness is described
> in `tests/eval/public/CONSUMER-PROTOCOL.md`; read that file and nothing else
> under `tests/eval/` except what it points to. Build your own world, run the
> plan's scenarios, record everything under `tests/eval/runs/<run-id>/`, and
> commit only that directory.

For session 0 (baseline cartographer), use plan **B** with the same text.
For sessions 7 and 8, the scenarios are probes rather than learner requests;
the same protocol applies.

For session 10 (judge), paste "Prompt 3 — white-box judge and repairer", give
it `LOS_EVAL_ORACLE_KEY` as an environment variable or in the message, and
add:

> Open the oracle with `tests/eval/tools/oracle_vault.py open --out
> ~/los-eval/oracle`, read its README and AUTHOR-NOTES first, then score every
> run under `tests/eval/runs/` with the scorers in `tests/eval/metrics/`.
> Grade the worksheets. Write FAILURE_ANALYSIS.md before changing any code.

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
