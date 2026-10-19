# AN — node plan 4: Function limits and continuity

**Node** `knowledge-an-limits-continuity` · **Stage** `stage-m2-analysis-anc`
(300 min, `exam_critical: true`)
**Builds on** `knowledge-an-sequences`
**Unlocks** exp/log & uniform convergence, differentiation, **and** integration —
three downstream nodes, more than any other

> **The hinge of the chain.** Sequences forked into two branches; this node is
> where the function-side branch becomes load-bearing. Three of the remaining
> five nodes list it as a prerequisite.

## Scope

**Sequence criteria for limits**, one-sided and improper limits, continuity, the
**intermediate value theorem**, inverse functions, extrema and the
**compact-interval theorems**. Script §5.1–5.5.

## Sources — which, at which angle

| When | Source | Angle | Locator |
|---|---|---|---|
| **Spine** | `source-analysis-skript` | The authority; §5.1–5.5, active pass | §5.1–5.5 |
| **Practice, first** | `source-analysis-skript` | HU tasks before any external bank | `ana_inf_serie05–09`, topic-matched |
| **When the limit definition feels arbitrary** | `source-3b1b-essence-of-calculus` | **Geometric intuition, not technique.** Shows *why* the limit is the shape it is. Explicitly *"useless for producing an epsilon-N argument"* — watch, then return to the script. **Limits/continuity episodes only** | limits/continuity episodes |
| **Structural second reading** | `source-lebl-basic-analysis` | Text-twin; **Ch. 3 → continuity** | Ch. 3 |
| **Why the definitions take this form** | `source-abbott-understanding-analysis` | **Ch. 4 → continuity.** One book per stuck proof | Ch. 4 |
| **German second voice** | `source-grieser-analysis1` | Klausur vocabulary, Hinweise + Lösungen | topic-matched |
| **Solved drill, first** | `source-forster-wessoly` | Exam points live here | topic-matched |
| **Pace problem on a specific computation** | `source-professor-leonard` | Does in full what the script compresses. **≤ 20 min per gap**, after a cold diagnostic | topic-matched |
| **Repetitions on one technique** | `source-analysis-drill-blaetter-extern` | After the HU series | as diagnosed |

## What to produce

1. **The sequence-criterion bridge, written out.** `lim_{x→a} f(x) = L` iff for
   every sequence `xₙ → a` (with `xₙ ≠ a`), `f(xₙ) → L`. This is the single most
   useful object in the node: it converts every function-limit question into a
   sequences question, and you already own sequences. **Include the standard use:
   proving a limit does *not* exist by exhibiting two sequences with different
   images.**
2. **A theorem-condition card for the compact-interval results.** IVT, extreme
   value theorem, and the continuity of inverse functions — for each: exact
   hypotheses, exact conclusion, and **one counterexample showing what breaks
   when a hypothesis is dropped** (drop closedness, drop boundedness, drop
   continuity).
3. **Six worked limits** spanning: two-sided, one-sided, improper, and one
   non-existent.

## How to self-test

Closed-book, at the end:

- [ ] State the sequence criterion, then use it to prove some limit does **not**
      exist.
- [ ] State IVT and EVT with **exact** hypotheses, and break each with a
      counterexample.
- [ ] Distinguish continuity at a point from continuity on an interval, and say
      where the difference bites.
- [ ] One HU-series subproblem, cold and timed.

**Done when** you reach for the sequence criterion automatically instead of
constructing epsilon-delta arguments from scratch.

## Traps

- **Learning epsilon-delta as a separate skill from epsilon-N.** The sequence
  criterion exists precisely so you don't have to. Build the bridge first.
- **Stating the compact-interval theorems without their hypotheses.** This is the
  `theorem-condition` ledger class and this node is where it is most punished —
  "continuous on `[a,b]`" is doing enormous work in every one of them.
- **Watching more 3B1B than 20 minutes.** Its route is explicit that it gives the
  picture and *not* the technique. It cannot produce a single mark on its own.
- **Treating one-sided and improper limits as minor.** They are cheap marks and
  they are commonly the setup for an l'Hospital question in AN.E.
