# AN — node plan 7: Taylor approximation

**Node** `knowledge-an-taylor` · **Stage** `stage-m2-analysis-anf`
(210 min, `exam_critical: true`)
**Builds on** `knowledge-an-differentiation`
**Feeds** `knowledge-an-exam-transfer`

> **Scope is unusually precise here — respect it exactly.** §6.8 is in;
> **§6.9 is excluded**; **§6.10 is Ausflug depth only** (overview, exam-light
> application context). This is the node where scope discipline saves the most
> time, because Taylor material expands indefinitely if you let it.

## Scope

Taylor polynomials, **the remainder and error bound**, and approximation as a
usable tool. Script §6.8 · §6.9 excluded · §6.10 overview only.

## Sources — which, at which angle

| When | Source | Angle | Locator |
|---|---|---|---|
| **Spine** | `source-analysis-skript` | The authority, and the scope fence. §6.8 in full; §6.10 skim only | §6.8 (+ §6.10 overview) |
| **Practice, first** | `source-analysis-skript` | HU tasks before any external bank | `ana_inf_serie05–09`, topic-matched |
| **When the *shape* of the approximation is unclear** | `source-3b1b-essence-of-calculus` | **Geometric intuition, not technique** — one of its two named windows is Taylor. Shows why the polynomial is the shape it is. Watch, then return to the script | Taylor episode only |
| **Applied framing** | `source-strang-calculus` | **Applied-first:** Taylor introduced through what it computes. Complements 3B1B — Strang gives worked mechanics where 3B1B gives the picture. Pairs well here specifically | Ch. 5, 7, 10 selections |
| **Structural second reading** | `source-lebl-basic-analysis` | Text-twin; **§4.3 → Taylor** | §4.3 |
| **Solved drill** | `source-forster-wessoly` | Klausur vocabulary | topic-matched |
| **German second voice** | `source-grieser-analysis1` | Hinweise + Lösungen | topic-matched |
| **Reps on remainder estimation** | `source-analysis-drill-blaetter-extern` | Volume, after the HU series | as diagnosed |

**Note the pairing:** this is the one node where 3B1B and Strang are explicitly
complementary rather than redundant — picture *then* mechanics. Elsewhere,
picking two explanation sources is avoidance; here the routes say otherwise.

## What to produce

1. **The Taylor polynomial + remainder card.** `Tₙ(x)` around a point, the
   remainder term in the form the script uses (Lagrange, most likely — **use the
   script's form, not the one you remember**), and the **error bound derived from
   it**. One page.
2. **Three standard expansions** worked from the definition, not recalled:
   `eˣ`, `sin x`, and one the script uses. Deriving them once beats memorizing
   them badly.
3. **Two error-bound problems.** *"Approximate X to within ε — how many terms?"*
   This is the question form that actually appears, and it is the one that uses
   the remainder rather than just the polynomial.

## How to self-test

Closed-book, at the end:

- [ ] Write `Tₙ` and the remainder term from memory, in the script's form.
- [ ] Expand a function you haven't expanded today, to order 3, from the
      definition.
- [ ] Answer a "how many terms for accuracy ε" question and **justify the bound**.
- [ ] State what §6.9 and §6.10 are, and that they are out of / at overview scope
      — scope awareness is itself a checkable item here.
- [ ] One HU-series subproblem, cold and timed.

**Done when** the remainder is as automatic as the polynomial. Students who lose
marks here almost always know `Tₙ` and not `Rₙ`.

## Traps

- **Studying the polynomial and skipping the remainder.** The remainder is where
  the marks and the difficulty live. Approximation without an error bound isn't
  approximation.
- **Drifting into §6.9.** It is *excluded*, explicitly. Not de-prioritized —
  excluded.
- **Treating §6.10 as content.** Ausflug = exam-light application context.
  Overview depth, once.
- **Memorizing expansions.** Derive them; the exam can ask for one you didn't
  memorize.
- **Using a remainder form from another textbook.** Several exist. The script's
  form is the one the marker expects.
