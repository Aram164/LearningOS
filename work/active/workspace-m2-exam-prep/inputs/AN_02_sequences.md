# AN — node plan 2: Sequences and convergence

**Node** `knowledge-an-sequences` · **Stage** `stage-m2-analysis-ana`
(360 min, `exam_critical: true`) — **the largest single topic block in the track**
**Builds on** `knowledge-an-foundations`
**Unlocks** series *and* function limits — the only node that forks the chain

> **The map's own words:** *"Chapter 3 is the spine."* Two later nodes depend on
> this one directly, and a third (integration) depends on it through limits. If
> the 46 hours have to compress, **this is the last block to cut**, not the first.

## Scope

Sequence definitions, **epsilon-N arguments**, accumulation points, subsequences,
**Cauchy sequences**, monotone convergence, divergence criteria. Script Chapter 3.

## Sources — which, at which angle

| When | Source | Angle | Locator |
|---|---|---|---|
| **Spine** | `source-analysis-skript` | The authority; Ch. 3 in full, active pass | Ch. 3 |
| **Practice, first** | `source-analysis-skript` | HU tasks before any external bank | `ana_inf_serie05–09`, topic-matched |
| **When an epsilon-N argument won't come out** | `source-mit-18100a` | **One of its only two permitted windows: L7–L9 is sequences.** Full rigour, deliberately more than this exam needs — for repair when a definition genuinely does not make sense | Lectures 7–9 **only** |
| **Structural second reading** | `source-lebl-basic-analysis` | Text-twin of the script; **Ch. 2 → sequences** (§2.5–2.6 is series, i.e. the next node) | Ch. 2 |
| **Motivation for the definition's shape** | `source-abbott-understanding-analysis` | Most readable English rigour; motivates *why* the epsilon-N definition takes the form it does. **Ch. 2 → sequences/series.** Rule from its record: **one book per stuck proof** | Ch. 2 |
| **German second voice** | `source-grieser-analysis1` | Same role as Abbott without the language switch; exercises carry Hinweise + Lösungen | topic-matched |
| **Solved drill, first** | `source-forster-wessoly` | Terse but complete solutions in Klausur vocabulary | topic-matched |
| **Fresh problems once Forster is spent** | `source-deitmar-uebungsbuch` | **Kap. 3.1 → convergence** | Kap. 3.1 |
| **When one technique needs ten more reps** | `source-analysis-drill-blaetter-extern` | Volume with solutions attached — repetition, not a new explanation. **Always after the HU series** | as diagnosed |
| **Pace problem, capped** | `source-professor-leonard` | Slow blackboard teaching that does in full what the script compresses. **≤ 20 min per gap**, only after a cold diagnostic shows a block | topic-matched |

## What to produce

1. **An epsilon-N template**, written once, in the script's notation: given
   `ε > 0`, choose `N`, show `n ≥ N ⟹ |aₙ − a| < ε`. Then **five instances**
   filled in, at increasing difficulty. This is a *writing* artifact — it exists
   so the proof-presentation node has something to correct.
2. **A convergence-criterion decision list** — monotone+bounded, Cauchy,
   subsequence, direct epsilon-N — with the trigger for each. One line per entry.
3. **A worked Cauchy example** where Cauchy is genuinely easier than exhibiting
   the limit. If you can't find one, you haven't understood why Cauchy exists.

## How to self-test

Closed-book, at the end:

- [ ] Write the definition of convergence *and* of a Cauchy sequence, then state
      the relationship between them **and which direction needs completeness**.
- [ ] Produce a full epsilon-N proof for a sequence you haven't seen today.
- [ ] Given a sequence, choose the criterion and **justify the choice in one
      sentence** — method-choice is a ledger class for a reason.
- [ ] One HU-series subproblem, cold and timed.

**Done when** the criterion choice is automatic and the epsilon-N write-up needs
no template in front of you.

## Traps

- **Collecting criteria without a trigger for each.** The exam failure mode is
  not "didn't know the ratio test exists," it's method-choice — reaching for the
  wrong tool under time.
- **Letting MIT 18.100A become a second course.** Its route says *two windows,
  never linear*. L7–L9 for sequences, then close it.
- **Doing external drill before the HU series.** External sheets are other
  examiners asking differently; the HU series is the only thing calibrated to
  this examiner's notation.
- **Skipping accumulation points and subsequences** because convergence feels
  like the "real" topic. Bolzano–Weierstrass-shaped questions live there.
- **Budget honesty:** 360 minutes is six hours. That is two or three sessions,
  not one. Plan it as such rather than discovering it at hour four.
