# AN — node plan 5: Exponential, logarithm and uniform convergence

**Node** `knowledge-an-exp-log-uniform` · **Stage** `stage-m2-analysis-and`
(150 min, `exam_critical: true`) — **the smallest exam-critical block**
**Builds on** `knowledge-an-limits-continuity` **and** `knowledge-an-series`
(the only node with two prerequisites from different branches)
**Feeds** `knowledge-an-exam-transfer`

> **Two unlike halves in one stage.** Exp/log is computational and cheap; uniform
> convergence is conceptual and is the one genuinely subtle idea in the node. The
> map is explicit that exp/log stays **"kept computational"** and uniform
> convergence is held **"at script depth"** — neither half should expand.

## Scope

Exponential and logarithm laws (computational), and the **pointwise vs uniform
convergence** distinction at script depth. Script §5.6–5.7.

## Sources — which, at which angle

| When | Source | Angle | Locator |
|---|---|---|---|
| **Spine** | `source-analysis-skript` | The authority, and the depth limit for the uniform-convergence half. §5.6–5.7 | §5.6–5.7 |
| **Practice, first** | `source-analysis-skript` | HU tasks before any external bank | `ana_inf_serie05–09`, topic-matched |
| **Uniform convergence, when the quantifier order won't sit still** | `source-lebl-basic-analysis` | Text-twin of the script; **§6.1–6.2 → uniform convergence** — the closest structural match available | §6.1–6.2 |
| **Same, motivated** | `source-abbott-understanding-analysis` | **Ch. 6 → uniform convergence.** Motivates why the definition needs `N` independent of `x`. One book per stuck proof — pick Lebl **or** Abbott, not both | Ch. 6 |
| **Exp/log computation, if rusty** | `source-strang-calculus` | **Applied-first:** introduced through what they compute rather than how they are constructed. Exactly right for the "kept computational" half | Ch. 5, 7, 10 selections |
| **Solved drill** | `source-forster-wessoly` | Klausur vocabulary | topic-matched |
| **German second voice** | `source-grieser-analysis1` | Hinweise + Lösungen | topic-matched |
| **Reps on log/exp manipulation** | `source-analysis-drill-blaetter-extern` | Volume, after the HU series | as diagnosed |

## What to produce

1. **The quantifier-order card.** Pointwise: `∀x ∀ε ∃N(x,ε)`. Uniform:
   `∀ε ∃N(ε) ∀x`. Write both, and write the one-sentence statement of what
   changes: **`N` may not depend on `x`.** Then the standard example where the
   two differ (`fₙ(x) = xⁿ` on `[0,1]` is the usual one — check the script's
   choice and use *that*).
2. **A short exp/log laws sheet** — the laws you actually manipulate, not a
   derivation. This is a cheat-sheet fragment, and it is one of the few Analysis
   items that transfers directly onto the M2 sheet.
3. **One worked "does uniform convergence hold?" problem**, with the reasoning
   for the answer, not just the answer.

## How to self-test

Closed-book, at the end:

- [ ] Write both definitions with quantifiers **in the right order**, and say in
      one sentence what uniform convergence buys you.
- [ ] Give a sequence of functions converging pointwise but not uniformly, and
      justify.
- [ ] Manipulate a compound exp/log expression without hesitation.
- [ ] One HU-series subproblem, cold and timed.

**Done when** the quantifier order is automatic — that is the entire conceptual
content of the node.

## Traps

- **Letting uniform convergence expand.** It is genuinely interesting and it is
  a rabbit hole; the script's depth is the ceiling. If you find yourself reading
  about Weierstrass M-tests and equicontinuity, you have left the syllabus.
- **Deriving exp and log from scratch.** The map says *kept computational.* The
  construction is not what's examined here.
- **Reading Lebl §6.1–6.2 *and* Abbott Ch. 6.** One book per stuck proof. Two
  explanations of the same subtlety is avoidance.
- **Treating 150 minutes as a light session and merging it into another node.**
  It's small because it's narrow, not because it's easy — the quantifier order is
  a classic exam discriminator.
