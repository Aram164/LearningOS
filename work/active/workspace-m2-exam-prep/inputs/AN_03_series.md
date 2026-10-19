# AN — node plan 3: Series and convergence criteria

**Node** `knowledge-an-series` · **Stage** `stage-m2-analysis-anb`
(270 min, `exam_critical: true`)
**Builds on** `knowledge-an-sequences`
**Feeds** `knowledge-an-exp-log-uniform` and `knowledge-an-exam-transfer`

> **The map's own words:** *"Chapter 4, best held as a decision process."* That
> phrasing is the whole plan. This node is not a list of criteria to know — it is
> a **flowchart to execute under time pressure.** Study it as one.

## Scope

Necessary conditions, geometric and telescoping series, **comparison, ratio, root
and Leibniz criteria**, absolute convergence. Script Chapter 4.

## Sources — which, at which angle

| When | Source | Angle | Locator |
|---|---|---|---|
| **Spine** | `source-analysis-skript` | The authority; Ch. 4, active pass | Ch. 4 |
| **Practice, first** | `source-analysis-skript` | HU tasks before any external bank | `ana_inf_serie05–09`, topic-matched |
| **Volume — and this node needs volume** | `source-analysis-drill-blaetter-extern` | *"For when one technique needs ten more repetitions rather than a new explanation."* Series is precisely that case: criterion selection is a reflex built by reps | as diagnosed, **after** the HU series |
| **Solved drill, first choice** | `source-forster-wessoly` | Terse but complete solutions; *"the exam points live here"* | topic-matched |
| **Fresh problems when Forster is spent** | `source-deitmar-uebungsbuch` | **Kap. 3.2 → series** | Kap. 3.2 |
| **Structural second reading** | `source-lebl-basic-analysis` | Text-twin; **§2.5–2.6 → series** | §2.5–2.6 |
| **When a criterion's *proof* is the blocker** | `source-abbott-understanding-analysis` | Motivates why each criterion takes its form. **Ch. 2 covers sequences *and* series.** One book per stuck proof | Ch. 2 |
| **German second voice** | `source-grieser-analysis1` | Exercises with Hinweise + Lösungen, Klausur vocabulary | topic-matched |
| **Correct write-up in German** | `source-fritzsche-trainingsbuch` | Solution *reasoning* written out — use after an HU task you got wrong | Kap. 1–4, topic-matched |

## What to produce

**The decision process, as an actual artifact — this is the node's deliverable
and everything else is support:**

1. **A one-page criterion flowchart.** Entry test (does `aₙ → 0`? if not, done),
   then the branch conditions for comparison / ratio / root / Leibniz /
   absolute convergence, each with **the trigger that selects it** and **the
   condition that must be checked before applying it**.
2. **A 20-item classification drill.** Twenty series, and for each: *which
   criterion, and why that one* — **without computing the answer.** Selection
   speed is the skill; the arithmetic is not.
3. **A counterexample pair** for the criteria that are inconclusive at the
   boundary (ratio/root = 1). Knowing *when a criterion says nothing* is worth
   more marks than knowing ten criteria.

## How to self-test

Closed-book, at the end:

- [ ] Reproduce the flowchart from memory.
- [ ] Given eight unseen series, name the criterion for each in under 60 seconds
      total. Then compute only the two you were least sure about.
- [ ] State the necessary condition for convergence and **give a series that
      satisfies it but diverges** (the harmonic series is the answer; be able to
      say why it matters).
- [ ] State what absolute convergence buys you that plain convergence doesn't.
- [ ] One HU-series subproblem, cold and timed.

**Done when** criterion selection happens before you've finished reading the
series.

## Traps

- **Learning criteria as facts rather than as a process.** The exam question is
  never "state the ratio test"; it's "does this converge," under time.
- **Applying a criterion without checking its condition.** This is the
  `theorem-condition` ledger class, and series is where it hurts most —
  Leibniz needs monotone decreasing *and* null, not just alternating.
- **Reaching for external drill before the HU series.** Same rule as every node.
- **Treating the inconclusive cases as edge cases.** Examiners choose them
  deliberately, because they separate process from recall.
- **Over-investing here at AN.A's expense.** 270 min vs sequences' 360 — the
  ratio is intentional. Series is narrower and more mechanical; sequences is the
  spine.
