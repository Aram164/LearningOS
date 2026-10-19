# Analysis — per-node study plans (index)

*Written 2026-08-15 to `workspace-m2-exam-prep/inputs/`. **Operational, not
canon** — this expires with the workspace (WORKFLOWS §23). The durable material
is the unit's knowledge map and the module source-map's 23 routes; these plans
only say how to walk them.*

## What these are

One plan per node of `unit-m2-analysis-exam-prep`'s **10-node knowledge map**.
Each answers three questions and nothing else:

1. **Which source, at which angle** — chosen from the 23 routes in
   `curriculum/modules/module-hu-m2-statistik-analysis/source-map.yaml`, not invented.
2. **What to produce** — the artifact that survives the session.
3. **How to self-test** — the cold check that decides whether the node is done.

> ⚠️ **These are routes, not prescriptions.** `source_selections` in `unit.yaml`
> is **deliberately empty** — it is your selection space, and the 2026-08-15
> overhaul emptied it on purpose. Nothing here should be copied into it. Record a
> selection only after you have actually used a source and it worked.

## The order

The map is a dependency chain, not a list. `AN.0` unlocks everything; sequences
unlock series **and** function limits; limits unlock continuity, differentiation
and integration; Taylor needs differentiation. **Only two things float:**
proof-presentation (a skill, run it alongside) and exam-transfer (the
convergence point).

| # | Node | Plan | Stage | Est. | Script |
|---|---|---|---|---|---|
| 0 | Proof reading & presentation | [`AN_00_proof_presentation.md`](AN_00_proof_presentation.md) | `calibrate` | 60 min | contract + `kleine_beweise` |
| 1 | Foundations & the real numbers | [`AN_01_foundations.md`](AN_01_foundations.md) | `an0` | 210 min | Ch 1–2 |
| 2 | Sequences & convergence | [`AN_02_sequences.md`](AN_02_sequences.md) | `ana` | 360 min | Ch 3 |
| 3 | Series & convergence criteria | [`AN_03_series.md`](AN_03_series.md) | `anb` | 270 min | Ch 4 |
| 4 | Function limits & continuity | [`AN_04_limits_continuity.md`](AN_04_limits_continuity.md) | `anc` | 300 min | §5.1–5.5 |
| 5 | Exp/log & uniform convergence | [`AN_05_exp_log_uniform.md`](AN_05_exp_log_uniform.md) | `and` | 150 min | §5.6–5.7 |
| 6 | Differentiation & mean-value theorems | [`AN_06_differentiation.md`](AN_06_differentiation.md) | `ane` | 330 min | Ch 6 |
| 7 | Taylor approximation | [`AN_07_taylor.md`](AN_07_taylor.md) | `anf` | 210 min | §6.8 |
| 8 | Riemann integration | [`AN_08_integration.md`](AN_08_integration.md) | `ang` | 330 min | §7.1–7.3 |
| 9 | Retrieval, mixed practice, combined mocks | [`AN_09_exam_transfer.md`](AN_09_exam_transfer.md) | `anx` | 540 min | all |

**Exam-critical total: 2,760 minutes = 46 hours.** (`stage-m2-analysis-exkurse`,
90 min, is explicitly *not* exam-critical and is excluded — Chapter 8 and the
Exkurs sections are outside scope.)

## The 46-hour problem, stated plainly

46 hours of Analysis remain, and **none of it has started** — the Analysis half
of a combined one-grade Klausur currently holds one note, a source crosswalk.
Meanwhile AML's build finished on 2026-08-15, so AML from here is *working*
existing artifacts rather than producing new ones.

The M2 sitting is nine days after the AML sitting, and COORDINATION.md is
explicit that Phase C "is a finish, not a start." **46 hours does not fit in nine
days alongside the SaD half.** Two consequences, and they are the whole reason
these plans exist:

- **AN.0 → AN.A start now, in parallel with AML**, not after it.
- **AN.X (540 min, the largest single block) cannot be the thing that gets
  compressed.** It is where the blocks become exam performance. Protect it by
  finishing AN.0–AN.G before the AML sitting, not by shortening it.

## The loop, once (from `stage-m2-analysis-calibrate`)

Every node runs the same loop. It is stated here so the ten plans don't repeat it:

1. **10-minute cold diagnostic** — attempt before studying. This produces the
   error, and the error chooses the source.
2. **≤ 20 minutes of intuition support, only if blocked** — a detour, not a
   parallel course.
3. **Active pass through `unser skript`** — definitions, theorem conditions,
   results.
4. **Solve the current HU tasks** (`ana_inf_serie05–09`, `serieWV`) **before any
   external drill.** External sheets are other examiners asking differently.
5. **Repair only the proofs that explain a failed application.** The script's own
   contract (pp. iv–vii) says proofs need not be memorized.
6. **Closed-book retrieval test** to finish.

**The error ledger runs across all ten nodes**, classifying every miss as
*definition · theorem-condition · method-choice · algebra · time*. It is created
in the calibrate stage and never restarted. By AN.X it is the single most
valuable object in the track — it tells you what your mocks should contain.

## Source-selection rules that apply everywhere

| Rule | Why |
|---|---|
| **HU series before any external bank** | Only tasks calibrated to this script and this examiner, in HU notation |
| **Ulm/Leipzig Klausuren stay unsolved** | Reserved for fresh timed sittings in AN.X — seeing solutions first destroys the test |
| **Marburg/Regensburg are solved** | Use these for diagnosed gaps, not for timed practice |
| **One book per stuck proof** | From Abbott's source record; reading three explanations of the same thing is avoidance, not study |
| **Wiederholung required · Ausflug exam-light · Exkurs + Ch 8 out** | The script's own triage; do not relitigate it per node |
| **7 sources carry no evaluation** | `labs-schreyer`, `mfnf`, `ohlbach-eisinger`, `velleman`, `ross`, `thomas`, `stewart` — routed but unassessed. **Visibility debt: repay on use** (WORKFLOWS §6a) by adding a minimal evaluation stub the first time you actually open one. Never in bulk. |
