# Task IR research closure — final decision record (2026-10-28)

Status: closed. This record is the single decision summary for the Task IR
research campaign. It introduces no code, no abstraction, and no trials.

## Decision

Retire Task IR P1 as a production candidate. Do not merge PR #71, do not
integrate `plan.compose`, the P3 selector, or any new query engine. The
existing bounded plan runner remains the supported agent execution
interface. Declarative programming for LearningOS is not rejected in
principle; on the evidence gathered, the proposed architecture does not
offer enough additional value over the runner that already exists.

Future work returns to real LearningOS usage. Further engineering in this
direction is justified only by recorded operational evidence from that
usage — recurring agent selection or ID-carrying errors, unnecessary
context transfers, or repeated operator interventions — not by further
architectural experimentation on speculation.

## Stage conclusions

| Stage | Conclusion |
|---|---|
| P1 — typed orchestration | Correctness and recovery demonstrated; efficiency not established |
| P2a — mechanical A/B/C comparison | Minimal advantage over the existing runner; Task IR returned the most bytes |
| P2b — live agent screening | No convincing efficiency advantage at screening scale |
| P3 — declarative resolution feasibility | Technically feasible; production investment unjustified |
| Production direction | Existing runner, with selective simplification only |

## What the evidence showed

- P1's four typed operations compile into existing machinery and recover
  correctly (73 Task IR tests; hosted exact-pair gates succeeded at the
  frozen pair). Correctness was never the open question after P1.
- Scripted P2a (36 trials, all oracle-clean): Task IR saved one invocation
  in one scenario and returned 32,735 bytes against the plan runner's
  25,663. Mechanical efficiency is not its advantage.
- Live demonstrations and one normalized B/C screening pair (all committed
  correctly, token accounting verified against session logs): no credible
  token or error advantage for Task IR once prompts were normalized.
  Arm B's two runs of the same scenario under different prompt versions
  (149,782 vs 209,829 input tokens) also showed that prompt scaffolding
  swings cost more than the arm choice at this scale; that pair of runs is
  not a clean variance estimate, and no strong statistical claim rests on it.
- P3 offline: compact projection alone cut agent-visible bytes on the
  unique-patch scenario from 5,601 (runner) to 375, below declarative
  resolution's 474. P3's distinct remainder — one fewer invocation, 184
  fewer authored bytes, system-enforced selection — is real but narrow
  and unproven against real LLM error rates.

## Preserved references

| Artifact | Reference |
|---|---|
| P1 implementation | branch `codex/task-ir-p1-experiment`, head `e895758126e332f8a8a9d7b34d4f1916337cee45`, draft PR #71 (stacked on PR #64), unmerged |
| Paired UI | `3c9a5f664c147790c490fae0a256e7764b4b9157` |
| P2 protocol, pilot, demo, screening reports | branch `codex/task-ir-p2-benchmark-20261028`, head `e719ba474c27118673d5c9a32c74f1b606843213`; `work/proposals/2026-10-28-task-ir-p2*` |
| P3 feasibility report | branch `codex/task-ir-p3-feasibility-20261028`, commit `53b9e575c8e77f5702f3623210b1aeba4e30b872`; `work/proposals/2026-10-28-task-ir-p3-feasibility-findings.md` |
| Scripted pilot traces | workbench `task-ir-p2-benchmark/results/pilot.json`, sha256 `ebbecfb63bf8f5b6ab75f131535df645865d1b5229478d823b502dcac79a78e3` |
| P3 comparison traces | workbench `task-ir-p3-feasibility/results/comparison.json`, sha256 `0b11f17b6a95aec560806e0a94979935c3faa953c50f6996e990f6c3ef7c7143` |

## Limitations kept on record

- P1's acceptance rests on its own reports and hosted CI; no merge or
  production exposure followed.
- Live P2b evidence is three demonstrations plus one screening pair —
  screening-grade only, by design and by budget decision.
- P2a/P3 harnesses, POC code, and raw traces remain in the local workbench;
  the reported deterministic runs are documented there, not independently
  reproduced or reviewed.
- The claim that productionizing P3 would cost on P1's scale is an
  engineering judgment from the 131-line POC's dependencies, not a measured
  implementation cost, and the POC has had no independent review.
- No dollar cost figure is used anywhere: no verified per-token price was
  available, and earlier unverified pricing estimates are withdrawn.

## Candidate runner improvements (recorded, not commissioned)

Only these survived the campaign as potentially worthwhile, each to be
taken up — if at all — as ordinary runner work driven by observed need:

1. Compact write-path result projection for the plan runner (the B+ shape),
   without changing safety or recovery evidence.
2. A deterministic unique-route helper at the runner layer, only when real
   operating evidence shows route-selection friction.

## Architectural lesson

Moving orchestration from the LLM into deterministic software helps only
in proportion to the responsibility the new layer actually removes.
LearningOS already had a capable runner, typed contracts, guarded writes,
and recovery; Task IR duplicated part of that interface instead of
replacing missing functionality. A compact runner response delivered most
of the measurable communication improvement without another language.
That is a useful negative result, recorded at the cost of one offline
experiment rather than a production subsystem.
