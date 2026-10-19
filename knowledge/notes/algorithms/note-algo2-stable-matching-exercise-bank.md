---
id: note-algo2-stable-matching-exercise-bank
type: note
title: "Algo 2 T10 — Exercise Bank: Stable Matching"
created: "2026-08-16"
role: exercise-bank
state: evolving
authorship: operator-drafted
concepts: [concept-stable-matching, concept-bipartite-matching]
sources: [source-algo2-hu-materials, source-kleinberg-tardos, source-algo2-frankfurt-klausuren]
contexts: [workspace-algo2-exam-prep]
---

> **Build note (2026-08-16).** Operator-drafted from `ad2_stablematching.pdf`.
> Solutions operator-computed, **unverified by Aram**. Deck wins on disagreement.

# Algo 2 · Topic 10 — Exercise Bank

**Scope:** the stable matching problem and instability, Gale-Shapley, termination,
perfectness, stability, men-optimality and women-pessimality, capacity extension.

> 🎁 **The one topic with a local exercise sheet.** `stable matching aufgaben.pdf`
> sits in `material://source-algo2-hu-materials` — the *only* exercise file in the
> whole Algo 2 archive. Use it before anything external.

## 1. Local material

| File | What | Where |
|---|---|---|
| `note-algo2-stable-matching` | Reference (§ refs below) | this vault |
| `note-algo2-stable-matching-viva-drill` | Oral drill | this vault |
| **`stable matching aufgaben.pdf`** | **The only local exercise sheet in Algo 2** | `material://source-algo2-hu-materials` |
| Kleinberg & Tardos 1.1 | **Assigned reading** | `material://source-kleinberg-tardos` |

## 2. Drills

### A. The problem

**A1.** State the problem and define instability precisely.

<details><summary>Solution</summary>

Input: `F` and `M` of size `n` each, with **complete** preference orders over the
other set. Output: a perfect matching `S`. `S` is **unstable** if there are
`(f,m), (f′,m′) ∈ S` with `f` preferring `m′` over `m` **and** `m′` preferring `f`
over `f′` — a *mutual* incentive to deviate. Stable = no such pair. *(Ref §2,
sl. 11.)*
</details>

**A2. [open]** Construct a 2×2 instance with two distinct stable matchings, and a
2×2 instance with exactly one. What structural feature distinguishes them?
*(Ref §2, sl. 12–13.)*

**A3. [open]** Why is "`f` would rather have `m′`" alone not an instability? Give
an instance where every person is unhappy with their partner yet the matching is
stable.

### B. The algorithm

**B1.** Write Gale-Shapley.

<details><summary>Solution</summary>

See reference §3. While some free man has not proposed to everyone: he proposes to
his highest-ranked not-yet-proposed woman; she accepts if free, or switches if she
prefers him to her current partner, freeing the latter. *(Ref §3, sl. 19.)*
</details>

**B2.** Prove termination in ≤ `n²` iterations.

<details><summary>Solution</summary>

Every iteration issues a proposal that has never been made before; with `n` men
and `n` women there are at most `n²` possible proposals. *(Ref §4, sl. 25.)*
</details>

**B3.** Prove the output is a perfect matching.

<details><summary>Solution</summary>

It is a matching (each person holds ≤ 1 partner). Suppose on termination some man
`m` were free. By sl. 26 he would still have an unproposed woman, so the loop
would continue — contradiction. Hence all `n` men are engaged, and engagements are
to distinct women, so all `n` women are too. *(Ref §4, sl. 26–27.)*
</details>

**B4.** Prove the output is stable.

<details><summary>Solution</summary>

Suppose `(f,m), (f′,m′) ∈ S`, `f` prefers `m′` over `m`, and `m′` prefers `f` over
`f′`. Since `m′` proposes in decreasing preference order and ended with `f′`, he
proposed to `f` **earlier**. At that point `f` either accepted him or was already
engaged to someone she preferred. Since a woman's partner only ever improves, her
final partner `m` is at least as good as `m′` — contradicting that she prefers
`m′`. ∎ *(Ref §4, sl. 28–29.)*
</details>

**B5. [open]** Run Gale-Shapley on a 3×3 instance you construct, twice, using
different orders for choosing the free man in line 3. Confirm the outputs are
identical. *(This makes sl. 34's theorem tangible.)*

### C. Fairness

**C1.** State the men-optimality theorem.

<details><summary>Solution</summary>

With `best(m)` the best partner `m` has in **any** stable matching and
`S* = {(best(m), m) : m ∈ M}`: **every execution** of Gale-Shapley returns `S*`.
The output does not depend on the order free men are processed. *(Ref §5,
sl. 34–35.)*
</details>

**C2.** State and justify the corollary for the women.

<details><summary>Solution</summary>

In `S*` every woman is paired with her **worst** possible stable partner. Suppose
`(f,m) ∈ S*` and some stable `S′` gives `f` a partner she likes less; combining
with men-optimality of `S*` produces an instability in `S′`. *(Ref §5, sl. 38–39.)*
</details>

**C3. [open]** Sl. 33 observes that if the `n` men have distinct top choices they
all get them. Construct such an instance for `n = 3` and note how bad it is for the
women.

**C4. [open]** Run Gale-Shapley on your 3×3 instance with the **women** proposing.
Compare with the men-proposing result. What does this say about who should
propose?

**C5. [open]** Is Gale-Shapley strategy-proof for the proposing side? For the
receiving side? *(Beyond the deck — flag what you'd need to verify rather than
asserting.)*

### D. Boundaries and extensions

**D1.** How does stable matching differ from bipartite matching (T09)?

<details><summary>Solution</summary>

T09 maximizes **cardinality** and has no preferences; here preferences are central,
the matching is always **perfect** (complete preference lists), and the objective
is **stability**, not size. Different problems, taught back to back. *(Ref §2.)*
</details>

**D2. [open]** Sl. 42 extends to university places with capacities. Sketch the
modification: what replaces "engaged", and what does a university do when it holds
`f(u)` offers and receives another? *(Cross-ref: T09 sl. 8 handles capacities by
duplication — does the same trick work here?)*

**D3. [open]** Answer the deck's own *Frage/Übung* on sl. 30.

## 3. External practice — scope filter

| Source | Take | Avoid |
|---|---|---|
| **`stable matching aufgaben.pdf`** | **First** — the only local sheet | — |
| Kleinberg & Tardos 1.1 | **Assigned**; the canonical presentation | later K&T chapters |
| Cseh 2017 | Leseempfehlung, popular matchings | its technical results |
| Frankfurt Klausuren | Any GS items as explain-aloud drill | written framing |

**Filter:** in scope are the problem, the algorithm, the three results
(termination, perfectness, stability), and the optimality/pessimality pair.
**Out:** strategy-proofness proofs, the hospital-residents algorithm in detail,
stable roommates (the non-bipartite variant, which can have *no* stable matching),
and popular matchings — named as Leseempfehlung only.
