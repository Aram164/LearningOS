# Task IR P2b entry findings — 2026-10-28

The P2b entry requirements from `P2-PROTOCOL.md` are closed, except the one
that is Aram's decision: approval of the live-trial budget. No live agent
trial has run. P1 remains frozen; `plan.compose` remains unstarted.

## Assessment of the two-hypothesis restructure

Adopted. The suggestion's separation is sound and is now recorded in the
protocol's analysis: P2b tests Hypothesis A (typed orchestration helps real
agents), and a negative P2b result would not settle Hypothesis B
(declarative execution with internal resolution and projected output), which
gets its own narrow P3 slice only after the P1 decision.

Three cautions carried into the record:

1. The early P1 figures (6 → 2 round trips, −90% bytes) came from a scripted
   comparison with no plan-runner arm. Against Arm B they do not survive, as
   P2a showed. They are retired as evidence, not reconciled.
2. The preregistered 30% round-trip target is kept unchanged, with the
   expectation stated in advance: many scenarios sit at an irreducible one
   or two calls, so the target can only be met through avoided LLM errors
   and retries. A miss will be reported with its cause class, not treated
   as a blanket verdict on the research direction.
3. The P3 example (`where: {unit_id, stage_id, source_id}`) is not
   automatically unique: one source can hold several stage placements with
   different angles. Any P3 slice must enforce uniqueness and refuse
   ambiguity, with ambiguity scenarios in its corpus from the start.

## Entry requirement 1 — multi-route fixture (P2-04): closed

The harness now builds a multi-route variant (second source and route in
the synthetic source map). Unit-level discovery returns two routes in all
arms. Scripted outcome: Arms A and B count two routes and refuse to choose;
Arm C's typed binding refuses and nothing is written. Oracle passes.

## Entry requirement 2 — authored-runtime scenario (P2-05): closed

The authored variant sets the same `runtime_target` the P1 suite uses. All
three arms now settle `proposed` with a `runtime-session-v1` packet present
and zero canonical change. The unauthored refusal shape left the corpus by
recorded amendment; P1's suite and P2-06 cover refusals.

## Entry requirement 3 — token capture: verified, with one trap found

Live trials can run as separate headless `muse exec` sessions rooted at a
disposable fixture workspace. Each session's `session.jsonl` carries one
usage record per `model_completed` event with `input_tokens`,
`output_tokens`, `cached_tokens`, `cache_read_tokens`, `cache_write_tokens`,
and `reasoning_tokens`. Aggregation over a real session log was verified on
2026-10-28. Two traps, both recorded in the protocol amendment: usage-shaped
nodes appear in more than one record shape, so aggregation must key on
`model_completed` events and deduplicate by event identity; and per-call
`input_tokens` already includes the cached share, so cache tokens are a
reported subset, never an added term.

One live demonstration trial per arm has deliberately not been run: it is
the first live spend, and the protocol places budget approval before it.

## Completed-corpus pilot (supersedes the 11-scenario totals)

All 12 scenarios × 3 arms = 36 scripted trials pass; the oracle
discrimination self-check still passes.

| Arm | Invocations | Returned bytes | Oracle |
|---|---|---|---|
| A — manual | 16 | 28,407 | 12/12 |
| B — plan runner | 16 | 25,663 | 12/12 |
| C — Task IR | 15 | 32,735 | 12/12 |

The P2a conclusion is unchanged at full corpus strength: Task IR saves one
invocation in one scenario and returns the most bytes. Mechanical
efficiency is not where its case can be made.

- Harness: `harness/p2_pilot.py`, sha256 `7659b2d381be15165c898c2e984e821a30948595dc9a83a72494874c85b1c6ae`
- Raw traces: `results/pilot.json`, sha256 `ebbecfb63bf8f5b6ab75f131535df645865d1b5229478d823b502dcac79a78e3`
- Protocol (amended): sha256 `915c75cddd3a04d1e69dd663d3484127b452dbd8557481b4f4dc5f5c170eda0c`

## What remains before any live trial

1. Aram approves the live budget: 12 scenarios × 3 arms × 3 repetitions =
   108 headless sessions, plus one demonstration trial per arm first.
   Analysis stays paired by the 7 headline scenarios; the other 5 are
   boundary and safety evidence.
2. Trial prompts per arm are frozen as files, identical except for the arm's
   interface instructions, with construction inside the trial clock and the
   same scripted reviewer condition for writes.
3. Only then: run, analyse per scenario class, and make the P1 decision
   (retain, simplify to a scenario class, or reject) before any P3 design.
