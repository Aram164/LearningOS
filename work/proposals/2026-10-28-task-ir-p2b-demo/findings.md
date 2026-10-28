# Task IR P2b demonstration findings (Gates 1–3) — 2026-10-28

Three live demonstration sessions ran under the staged authorization. The
108-session campaign has not run and remains unauthorized. P1 was not
modified. All work happened on disposable synthetic fixtures.

## Gate 1 — frozen inputs

Model (Muse Code 1.4.14, default model route, muse-wonder-1.0 as
recorded by every session), scenario P2-07, prompts, fixtures, reviewer
criteria, and per-session limits (40 model steps, 900 s wall kill, web tools
disabled) were frozen before execution in `frozen/FREEZE.md`. All three
fixture fingerprints were identical (`cd4e16ec…f104`). The reviewer applies
identical semantic criteria in all arms; check-record bytes are never
compared. Prompts differ only in the interface section; their SHA-256
hashes are recorded in `frozen/demo-trials.json`.

## Gate 2 — demonstration results (n = 1 per arm; illustrative, not evidence)

Every arm completed the task correctly. The independent state oracle
confirms, in all three fixture copies: only `angle` changed (to the exact
task value), the stable route id was materialized, every other route field
is identical to a pristine fixture, and exactly one receipt exists.

| Measure | A — manual | B — runner | C — Task IR |
|---|---|---|---|
| Model calls | 13 | 5 | 8 |
| Input tokens (incl. cached) | 477,861 | 149,782 | 290,211 |
| Cached input (subset) | 405,372 | 89,308 | 217,144 |
| Non-cached input | 72,489 | 60,474 | 73,067 |
| Output tokens | 2,882 | 1,826 | 1,619 |
| Tool calls | 12 | 4 | 7 |
| Interface invocations | 11 | 3 | 4 |
| Tool-batch errors | 0 | 0 | 0 |
| Wall time | 49.9 s | 29.2 s | 47.1 s |
| Review before apply | yes | yes | yes |
| Final state | committed | committed | committed |

Token accounting verified end to end: sums over `model_completed` events in
each session's own log match the runner's `run.usage` summary exactly for
all three arms. Cache tokens are a subset of input in every record.

Behaviour worth noting, without over-reading a single trial: Arm A's agent
probed `--help` twice and repeated `plan-edit-context --route-id …` three
times while finding its way (11 interface invocations against the scripted
operator's 3). Arm C's agent spent two exploratory shell calls orienting
before preview/apply. Arm B's agent executed its three interface calls
without exploration. This is the class of friction P2b exists to measure;
one trial per arm cannot rank the arms.

Harness failure recorded honestly: one Arm C invocation was a bare
`agent_run.py` probe (no plan), which the tool-batch error counter did not
classify as an error. Retry accounting in the full campaign must count
nonzero interface exits from the recorded commands, not tool-batch error
flags.

## Gate 3 — cost of the full campaign

Projected at the demonstrated per-arm rates (36 sessions per arm):

- Input tokens: 36 × (477,861 + 149,782 + 290,211) ≈ **33.0M**
- Output tokens: ≈ **0.23M**

Conservative ceiling, from the enforced caps rather than the averages:
every session is capped at 40 model steps; the largest observed single-call
input in the demonstrations was 44,471 tokens. A session that hit the step
cap at that per-call size would consume ≈ 1.78M input tokens, so
108 sessions are bounded at ≈ **192M input tokens**. A prudent campaign
budget cap is therefore **200M input tokens**, with the existing 40-step
and 900-second per-session limits kept as the enforcement mechanism.

Monetary conversion is **not verified**: no per-token price for
muse-wonder-1.0 is available in this environment, and inventing one would
corrupt the gate. The only credit signal observed is the runner's allowance
report, which moved from 22% to 25% of its window and 80% to 81% of its
weekly allowance across the three demonstrations — a coarse, shared meter
that also covers other work in the same window. If a dollar ceiling is
required, it is `tokens × price` once Aram supplies the price for his plan;
the token ceiling above is enforceable today.

## What did not happen

No 108-session run, no P1 change, no P3 design, no merge. PR #71 remains
frozen at `e895758`; the P2 branch's tools tree is byte-identical to it.

## Recommendation

Approve or adjust the 200M-input-token campaign ceiling (and a dollar
ceiling if a price is supplied). On approval, Gate 4 runs the frozen
benchmark unchanged: 108 sessions, paired analysis across the seven
headline scenarios, preregistered thresholds, findings reported either way.
