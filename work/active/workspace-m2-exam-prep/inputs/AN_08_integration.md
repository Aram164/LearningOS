# AN — node plan 8: Riemann integration and the fundamental theorem

**Node** `knowledge-an-integration` · **Stage** `stage-m2-analysis-ang`
(330 min, `exam_critical: true`) — tied for second-largest block
**Builds on** `knowledge-an-limits-continuity` **and** `knowledge-an-differentiation`
**Feeds** `knowledge-an-exam-transfer`

> **The map calls Taylor and integration *"the two payoffs."*** This is the last
> topic node — everything before it exists partly to make this one possible. It
> also has two prerequisites, so it cannot be pulled earlier if the schedule
> slips: it is genuinely last.

## Scope

Riemann sums, **integrability**, the **fundamental theorem**, substitution,
integration by parts, **improper integrals**. Script §7.1–7.3.

## Sources — which, at which angle

| When | Source | Angle | Locator |
|---|---|---|---|
| **Spine** | `source-analysis-skript` | The authority; §7.1–7.3, active pass | §7.1–7.3 |
| **Practice, first** | `source-analysis-skript` | HU tasks before any external bank | `ana_inf_serie05–09`, topic-matched |
| **Structural second reading** | `source-lebl-basic-analysis` | Text-twin; **Ch. 5 → integral** | Ch. 5 |
| **Why integrability is defined this way** | `source-abbott-understanding-analysis` | **Ch. 7 → integral.** Motivates upper/lower sums. One book per stuck proof | Ch. 7 |
| **Full rigour repair — its second permitted window** | `source-mit-18100a` | **L23–L24 is the node's one allowed window** (the other is sequences). For when the definition of the integral genuinely does not make sense. Never linear | Lectures 23–24 **only** |
| **Technique volume** | `source-strang-calculus` | **Applied-first**, integration introduced through what it computes. The right register for substitution and by-parts mechanics | Ch. 5, 7, 10 selections |
| **Solved drill, first** | `source-forster-wessoly` | Exam points live here | topic-matched |
| **German second voice** | `source-grieser-analysis1` | Hinweise + Lösungen | topic-matched |
| **Reps on substitution / by parts** | `source-analysis-drill-blaetter-extern` | Volume with solutions, after the HU series. This node's technique half needs reps | as diagnosed |
| **Correct write-up in German** | `source-fritzsche-trainingsbuch` | Solution reasoning written out, after a failed HU task | Kap. 1–4 |

## What to produce

1. **The FTC card — both parts, kept distinct.** Part 1 (`F(x) = ∫ₐˣ f` is an
   antiderivative of continuous `f`) and Part 2 (`∫ₐᵇ f = F(b) − F(a)`), each
   with **exact hypotheses**. Conflating them is the standard error, and the
   hypotheses differ.
2. **An integrability page.** Upper and lower sums, the criterion the script
   uses, and **one function that is not Riemann integrable** with the reason.
   Knowing the boundary of the definition is what distinguishes this from
   school calculus.
3. **A technique set, timed:** ten substitutions, ten by-parts, five requiring
   both. The mechanics must be free.
4. **Four improper integrals** — two convergent, two divergent, each with the
   limit argument written out. Improper integrals are where integration reconnects
   to AN.A/AN.B, and mixed questions exploit that.

## How to self-test

Closed-book, at the end:

- [ ] State both parts of the FTC with exact hypotheses and say how they differ.
- [ ] Define Riemann integrability via upper/lower sums, and give a
      non-integrable example.
- [ ] Compute a substitution and a by-parts integral without hesitation.
- [ ] Decide convergence of an improper integral **and write the limit argument**.
- [ ] One HU-series subproblem, cold and timed.

**Done when** the FTC's two parts are separate objects in your head and improper
integrals are handled as limits rather than as formulas.

## Traps

- **Doing school calculus and calling it Analysis.** The examinable content is
  integrability and the FTC's hypotheses; substitution and by-parts are the
  enabling mechanics, not the subject.
- **Blurring FTC parts 1 and 2.** Different statements, different hypotheses,
  frequently a two-part exam question.
- **Handling improper integrals without limits.** They are *defined* as limits;
  writing the limit is where the marks are.
- **Opening MIT 18.100A outside L23–L24.** Two windows, that's the rule.
- **Arriving here with no time left.** This node has two prerequisites and cannot
  be reordered. If the schedule is slipping by AN.E, the thing to compress is
  external drill in AN.B/AN.E — **not** this node and **not** AN.X.
