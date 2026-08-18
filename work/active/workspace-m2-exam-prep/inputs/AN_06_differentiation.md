# AN — node plan 6: Differentiation and the mean-value theorems

**Node** `knowledge-an-differentiation` · **Stage** `stage-m2-analysis-ane`
(330 min, `exam_critical: true`) — second-largest topic block
**Builds on** `knowledge-an-limits-continuity`
**Unlocks** Taylor, and (with limits) integration

> **The map's own words:** *"the derivative definition and theorem chain."*
> **Chain** is the operative word. Rolle → MVT → monotonicity → extrema →
> l'Hospital is a single dependency line, and questions routinely walk two or
> three links of it. Learn it as a chain, not as five theorems.

## Scope

The derivative definition; calculating derivatives; justifying extrema and
monotonicity; **Rolle and the mean-value theorem**; **l'Hospital**. Script Ch. 6
(§6.8 Taylor is the next node).

## Sources — which, at which angle

| When | Source | Angle | Locator |
|---|---|---|---|
| **Spine** | `source-analysis-skript` | The authority; Ch. 6 up to Taylor, active pass | Ch. 6 (excl. §6.8) |
| **Practice, first** | `source-analysis-skript` | HU tasks before any external bank | `ana_inf_serie05–09`, topic-matched |
| **Structural second reading** | `source-lebl-basic-analysis` | Text-twin; **Ch. 4 → differentiation** (§4.3 is Taylor, next node) | Ch. 4 |
| **Why the theorems take this form** | `source-abbott-understanding-analysis` | **Ch. 5 → differentiation.** One book per stuck proof | Ch. 5 |
| **German second voice** | `source-grieser-analysis1` | Klausur vocabulary, Hinweise + Lösungen | topic-matched |
| **Computation pace** | `source-professor-leonard` | Does the computation in full where the script compresses to a result. **≤ 20 min per gap**, only after a cold diagnostic. This node's mechanical half is where it earns its place | topic-matched |
| **Solved drill, first** | `source-forster-wessoly` | Exam points live here | topic-matched |
| **Fresh problems** | `source-deitmar-uebungsbuch` | Once Forster is spent. **Verify chapter mapping on first use** — only Kap. 1–2 and 3.1–3.2 are mapped | verify on use |
| **Reps on derivative computation** | `source-analysis-drill-blaetter-extern` | Volume, after the HU series | as diagnosed |
| **Applied framing** | `source-strang-calculus` | Introduced through what it computes. Useful if the *point* of MVT is unclear | Ch. 5, 7, 10 selections |

## What to produce

1. **The theorem chain, on one page.** Rolle → MVT → (monotonicity criterion,
   extremum criteria) → l'Hospital. For each link: **hypotheses, conclusion, and
   what the previous link supplied.** The chain structure is the memory device —
   you should be able to derive MVT's statement from Rolle's shape.
2. **A hypothesis-breaking set.** For Rolle and MVT: drop differentiability at
   one interior point, drop continuity at an endpoint, drop `f(a) = f(b)` — one
   counterexample each. `theorem-condition` is a ledger class and this is its
   home node.
3. **An l'Hospital checklist.** The indeterminate forms it applies to, the forms
   it does *not*, and the requirement to **verify the form before applying** —
   plus one example where applying it blindly gives a wrong answer.
4. **Twenty derivative computations**, timed. The mechanical half must be free so
   the theorem half gets the thinking time.

## How to self-test

Closed-book, at the end:

- [ ] Write the derivative definition, then Rolle and MVT with exact hypotheses.
- [ ] Derive the monotonicity criterion **from** MVT rather than recalling it.
- [ ] Given a function on an interval, locate and **justify** extrema — the
      justification is the marks.
- [ ] Apply l'Hospital correctly, and produce one case where it doesn't apply.
- [ ] One HU-series subproblem, cold and timed.

**Done when** you can move along the chain in both directions and every extremum
claim comes with its justification attached.

## Traps

- **Computing derivatives well and justifying badly.** The exam asks *why this is
  a maximum*, not *what the derivative is*. Mechanical fluency is the enabler,
  not the deliverable.
- **l'Hospital without checking the form.** The single most common self-inflicted
  error in this material.
- **Memorizing MVT's proof.** The contract says proofs need not be memorized —
  but its *hypotheses* absolutely must be exact. Know the statement cold, the
  proof only if it explains a failed application.
- **Letting Professor Leonard run past 20 minutes.** His route caps it. This node
  has the most mechanical content and therefore the most temptation.
- **Starting Taylor here** because §6.8 is in the same chapter. It's a separate
  stage with its own 210 minutes.
