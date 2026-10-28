# Task IR P2a pilot findings — 2026-10-28

Phase P2a of the preregistered protocol (`P2-PROTOCOL.md`) is complete. The
live phase P2b has not started. Nothing here is an LLM token measurement.

## What was run

Scripted reference operators executed 11 of the 12 corpus scenarios in all
three arms (33 trials) on disposable fixtures built by the frozen Core's own
builders (`build_mini_repo` + `material_fixture`, synthetic data only). Every
operator subprocess was recorded with exit code, returned bytes, and wall
time. State oracles read canonical YAML directly. Frozen pair: Core
`e895758126e332f8a8a9d7b34d4f1916337cee45`, UI
`3c9a5f664c147790c490fae0a256e7764b4b9157`, re-verified clean before the run.

- Harness: `harness/p2_pilot.py`, sha256 `e6be9b3cf377ed2a1bdb2b4446dbb971f7e1b901a06bb12efe01860c033194f7`
- Raw traces: `results/pilot.json`, sha256 `1296ebecf88a1b1667308fc00037d2559cf6b727f821953a1ba62f02ae2d5181`
- Retained in `LearningOS/workbench/task-ir-p2-benchmark/` (local workbench;
  the protocol and this report are also committed on
  `codex/task-ir-p2-benchmark-20261028` under `work/proposals/`).

## Result: correctness parity, no mechanical efficiency win

All 33 trials passed their oracles, and every arm settled the same outcome in
every scenario (ok / found-unique / committed / unchanged / blocked /
refused). The oracle discrimination self-check passes: the patch oracle
accepts a correct commit and rejects a tampered route.

| Scenario | A calls/bytes | B calls/bytes | C calls/bytes | Outcome (all arms) |
|---|---|---|---|---|
| P2-01 inspect unit | 1 / 1165 | 1 / 2004 | 1 / 1938 | ok |
| P2-02 inspect stage | 1 / 4486 | 1 / 3075 | 1 / 3006 | ok |
| P2-03 find unique route | 1 / 4428 | 1 / 3019 | 1 / 4416 | found-unique |
| P2-05 propose session | 1 / 61 | 1 / 969 | 1 / 996 | refused (no runtime target in fixture) |
| P2-06 propose unknown stage | 1 / 61 | 1 / 969 | 1 / 996 | refused |
| P2-07 patch via discovery | 3 / 6827 | 3 / 5418 | 2 / 10247 | committed |
| P2-08 patch literal route | 2 / 2399 | 2 / 2399 | 2 / 1811 | committed |
| P2-09 patch unchanged | 1 / 704 | 1 / 704 | 1 / 743 | unchanged, zero receipts |
| P2-10 stale after preview | 2 / 1087 | 2 / 1087 | 2 / 2164 | blocked, external change preserved |
| P2-11 patch unknown unit | 1 / 97 | 1 / 97 | 1 / 419 | refused, never read as unchanged |
| P2-12 malformed input | 1 / 106 | 1 / 158 | 1 / 113 | refused before dispatch |
| **Total** | **15 / 21421** | **15 / 19899** | **14 / 26849** | — |

## Findings

1. **For an ideal operator, Task IR saves almost no invocations.** It saves
   exactly one call in one scenario (P2-07, discovery-to-patch: 2 vs 3).
   Everywhere else the arms are at parity, because the plan runner already
   collapses reads and the seal flow is already two calls.
2. **Task IR returns more bytes, not fewer.** Arm C returns the most bytes
   overall, driven by P2-07 (10,247 vs B's 5,418). Bounded-but-complete
   results cost context. Any claim that Task IR obviously shrinks operator
   context is disproved at the interface level; the live token target (20%
   reduction) is therefore genuinely at risk, not a formality.
3. **Wall time favours the simpler arms on synthetic fixtures** (Arm C calls
   run roughly 1.4–1.9× Arm A's). Python and subprocess startup dominate at
   this scale; per protocol, wall time is reported and never decides alone.
4. **Safety behaviour is at parity for correct operators.** Stale, unknown,
   unchanged, and malformed cases settle identically in all arms. P1's safety
   value is therefore not "the old paths are unsafe" — it is that the safe
   behaviour is carried by the system instead of by operator discipline.
   That difference only appears with a fallible operator, i.e. in P2b.
5. **P2-05 confirms the protocol assumption.** The synthetic fixture has no
   authored runtime target, so all arms refuse the session proposal. The
   authored shape remains covered only by P1's own suite.
6. **P2-04 (ambiguous unit-level discovery) was not exercised.** The fixture
   has a single unit route; a multi-route fixture extension is required
   before the live phase. This is a corpus gap, recorded rather than hidden.

## Interpretation

The pilot validates the corpus, the oracles, and trace capture. It also
sharpens the hypothesis P2b must test: Task IR's benefit, if any, is not
fewer mechanical steps for a perfect operator. It would have to come from
LLM behaviour — fewer mis-copied IDs, fewer malformed envelopes, fewer
retries and recoveries — weighed against Arm C's larger returned context.
A benchmark comparing only Arm A would miss this entirely; Arm B is close
to Arm C on every mechanical measure here.

## Decision

Proceed to P2b exactly as preregistered. No operation expansion, no
`plan.compose`, no schema change. PR #71 stays frozen and unchanged.

P2b entry criteria, in order:

1. Multi-route fixture extension so P2-04 runs in all arms.
2. Token capture demonstrated from the agent harness's session records on
   one trial per arm. Self-reported token counts are not accepted.
3. Scripted reviewer condition identical across arms; construction of the
   task spec / plan / command chain inside the trial clock.
4. Trial budget approved by Aram (12 scenarios × 3 arms × 3 repetitions,
   analysed paired by scenario).

If P2b cannot meet the preregistered targets (≥20% median token reduction
and ≥30% fewer round trips against the strongest comparator, no success
loss, zero safety violations), the standing recommendation in the protocol
applies: simplify P1 to the scenario class that pays, or reject it and keep
the runner.
