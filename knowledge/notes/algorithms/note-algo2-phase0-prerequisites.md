---
id: note-algo2-phase0-prerequisites
type: note
title: "Algo 2 — Phase 0: prerequisites the decks assume"
created: "2026-08-16"
role: reference
state: evolving
authorship: operator-drafted
concepts: [concept-asymptotic-analysis, concept-recurrences-master-theorem,
  concept-adt-dictionary, concept-binary-search-trees, concept-adt-priority-queue,
  concept-hashing-chaining, concept-graph-basics, concept-complex-roots-of-unity,
  concept-determinant-orientation, concept-expected-value, concept-proof-technique]
sources: [source-algo2-hu-materials, source-clrs, source-dms-grundwerkzeuge,
  source-ottmann-widmayer]
contexts: [workspace-algo2-exam-prep]
---

> **Build note (2026-08-16).** Drafted by the operator from the twelve `ad2_*.pdf`
> decks' own *Erinnerung* / *Wiederholung* / *Themen des Abschnitts* slides.
> **Nothing here is inferred from "what an algorithms course usually assumes"** —
> every phase below is named by a deck, with the slide cited. `authorship:
> operator-drafted` — not yet worked by Aram.

# Algo 2 — Phase 0: prerequisites

**Why this exists.** Algo 2 is a **second** course. Its decks do not re-teach
AlgoDat I; they open with a recall slide and move on within two minutes. The
`ad2_hashing` deck states it flatly: *"Sicher bekannt aus AlgoDat I"* (sl. 10).
If a prerequisite is soft, the failure does not appear as "I don't know the
prerequisite" — it appears as being unable to follow the *actual* topic, four
slides in.

**Phase 0 is triage, not a course.** Every phase below is a **diagnostic first**.
Pass it, and you skip the phase entirely. That is the intended outcome for most
of them — this is a checklist for finding the two or three that are actually
soft, not a syllabus to work through.

> ⚠️ **The oral changes the standard.** In a 30-minute viva you cannot quietly
> route around a shaky prerequisite the way you can on paper. If the examiner
> asks *"and why is a binary heap's decrease-key O(log n)?"* mid-way through
> Fibonacci heaps, the prerequisite **is** the question. Phase 0 items are
> examinable in exactly this indirect way.

---

## How to run a phase

1. **Diagnostic (10 min, cold).** Attempt the check without review.
2. **Pass → skip the phase.** Record it and move on. Do not "revise anyway."
3. **Fail → repair only the failed item**, from the route given, capped at the
   stated budget.
4. **Re-check cold**, next session, not the same one.

Everything lands in the same **error ledger** the other tracks use —
`definition · theorem-condition · method-choice · algebra · time`.

---

## Phase 0.1 — Asymptotic analysis and elementary operations

**Named by:** the whole course; `ad2_fastmultiplication` counts
*Elementaroperationen* explicitly (sl. 9–10).
**Budget if failed:** 45 min.

**Diagnostic**

- [ ] Define `O`, `Ω`, `Θ` precisely — with the quantifiers.
- [ ] Count the elementary operations of schoolbook multiplication of two
      `n`-digit numbers, and get `Θ(n²)` **by counting**, not by recall.
- [ ] Say what "elementary operation" means when the numbers don't fit in a word.

**Route on failure:** `source-dms-grundwerkzeuge` Kap. 1 — it is the course's
chosen source for topic 1 anyway, so this repair is not a detour. Then CLRS
Kap. 3.

**Done when** you can justify a bound by counting rather than by pattern-matching
the shape of the loop.

---

## Phase 0.2 — Recurrences and the master theorem

**Named by:** `ad2_fastmultiplication` sl. 2, whose agenda literally ends
*"Erinnerung: Mastertheorem"*.
**Budget if failed:** 60 min. **Highest-value phase on this list.**

**Diagnostic**

- [ ] State the master theorem's three cases **with their conditions**.
- [ ] Solve `T(n) = 4T(n/2) + Θ(n)` and `T(n) = 3T(n/2) + Θ(n)` and say which one
      is Karatsuba.
- [ ] Explain *why* dropping one of the four subproblems changes the exponent —
      i.e. why `3` vs `4` matters more than the linear term.

**Route on failure:** CLRS Kap. 4. Then redo the two recurrences cold.

**Done when** you can go from a divide-and-conquer description straight to its
recurrence and then to its bound, in one pass, out loud.

> 🎯 **Oral relevance: very high.** "Warum ist Karatsuba schneller?" is the
> obvious opening question of the entire course, and the answer *is* a recurrence
> solve. This is the single prerequisite most likely to be examined directly.

---

## Phase 0.3 — ADT Dictionary and binary search trees

**Named by:** `ad2_btrees` sl. 2 and `ad2_splaytrees` sl. 2 — both open
*"Erinnerung an ADT Dictionary und binäre Suchbäume"*. `ad2_btrees` sl. 5
restates the search-tree property and the `O(h)` bound.
**Budget if failed:** 60 min.

**Diagnostic**

- [ ] State the ADT Dictionary operations, and the search-tree property.
- [ ] Explain why search is `O(h)` and what makes `h` grow to `n`.
- [ ] Perform a rotation on paper and say what it preserves.
- [ ] Name what a balanced BST buys and what it costs.

**Route on failure:** CLRS Kap. 12 (BSTs) and 13 (red-black, for the balancing
idea only — Algo 2 does not examine red-black trees). Ottmann/Widmayer Kap. 5 is
the German alternative and shares vocabulary with the splay-tree deck.

**Done when** rotations are mechanical and you can state what balancing is *for*
without naming a specific balanced tree.

> 🔗 Feeds **two** topics: B-trees and splay trees. Splay trees are defined as
> *"binäre Suchbäume ohne zusätzliche Balance-Werte"* (sl. 11) — that sentence is
> only meaningful if you already know what the balance values normally do.

---

## Phase 0.4 — ADT Priority Queue and heaps

**Named by:** `ad2_fibonacciheap` sl. 2 (*"Erinnerung an ADT Priority Queue und
Umsetzung mittels Heap"*) and sl. 6, which tabulates binary / binomial /
Fibonacci bounds side by side.
**Budget if failed:** 60 min.

**Diagnostic**

Reproduce the operative half of the deck's own sl. 6 table, from memory:

| | insert | min | extract-min | decrease-key | delete | union |
|---|---|---|---|---|---|---|
| **Binary** | O(log n) | O(1) | O(log n) | O(log n) | O(log n) | O(n) |
| **Binomial** | O(log n) | O(log n) | O(log n) | O(log n) | O(log n) | O(log n) |

- [ ] Fill both rows and **justify three of the entries**.
- [ ] Explain why binary-heap `union` is `O(n)` while binomial is `O(log n)`.
- [ ] Say which operation Dijkstra calls most often.

**Route on failure:** CLRS Kap. 6 (binary heaps); the binomial-heap material sits
in CLRS's Fibonacci chapter neighbourhood and in Ottmann/Widmayer.

**Done when** you can motivate Fibonacci heaps *before* seeing them — i.e. state
which column of that table needs improving and why.

> 🎯 **Oral relevance: very high.** The Fibonacci lecture's entire premise is the
> last row of that table. An examiner who asks "warum Fibonacci-Heaps?" is asking
> a Phase 0.4 question.

---

## Phase 0.5 — Hashing with chaining, and expected-value probability

**Named by:** `ad2_hashing` sl. 2 (*"Wiederholung: Hashing with Chaining"*),
sl. 10 (*"Sicher bekannt aus AlgoDat I"*), sl. 7 (randomization ⟹ *"nur
Erwartungswerte für Laufzeit"*).
**Budget if failed:** 75 min — this phase has two halves.

**Diagnostic — hashing half**

- [ ] Describe hashing with chaining: hash function `h : U → {1,…,r}`, table
      `T[1..r]`, collision handling.
- [ ] State the expected chain length under uniform hashing and **derive it**.
- [ ] Say what a *universal* family of hash functions guarantees.

**Diagnostic — probability half**

- [ ] Compute an expected value by linearity over indicator variables.
- [ ] State Markov's inequality and use it once.
- [ ] Explain what "with high probability" means as a bound.

**Route on failure:** `source-dms-grundwerkzeuge` Kap. 4 — the deck's own named
Literatur, so again not a detour. For the probability half, your own SaD
material (`concept-expected-value`, `concept-probability`) is closer to hand than
any algorithms text, and this is a **genuine M2 ↔ Algo 2 cross-wire**.

**Done when** you can carry out an expected-value argument over indicators
without looking up linearity of expectation.

> 🔗 **Cross-wire worth exploiting:** the probability half is shared with M2/SaD.
> If Algo 2 is reinstated, this phase gets substantially cheaper by being done
> alongside the SaD probability lectures rather than separately.

---

## Phase 0.6 — Graphs: representation, traversal, and Dijkstra

**Named by:** `ad2_shortestpaths` sl. 2 (*"(Erinnerung) Graphen und kürzeste
Wege"*) and its Literatur note: *"Alles Weitere wurde bereits in AlgoDat 1
behandelt."* Also assumed wholesale by `ad2_maximumflow` and
`ad2_bipartitematching`.
**Budget if failed:** 75 min.

**Diagnostic**

- [ ] Define directed graph, closed walk (*geschlossener Weg*) and cycle
      (*Kreis*) — sl. 7 flags these as the deck's **only** repeated definitions,
      which means everything else is assumed.
- [ ] Compare adjacency list vs matrix on space and neighbour-iteration cost.
- [ ] Run BFS and DFS on a small graph and state what each computes.
- [ ] State Dijkstra, its **assumption on edge weights**, and where the priority
      queue enters.

**Route on failure:** CLRS Kap. 22 (elementary graph algorithms) and 24.3
(Dijkstra).

**Done when** you can state precisely why Dijkstra fails on negative edges —
because that failure is the motivation for Bellman-Ford, which is the topic.

> 🔗 Feeds **three** topics: shortest paths, max flow, bipartite matching. This
> is the widest-reaching prerequisite after amortized analysis (which is itself
> a course topic, not a Phase 0 item — see below).

---

## Phase 0.7 — Complex numbers, roots of unity, polynomials

**Named by:** `ad2_fastfouriertransform` sl. 2 (*"Alternative zu komplexen
Einheitswurzeln"* as an agenda item) and sl. 4–7, which build polynomial
representation from scratch.
**Budget if failed:** 90 min — **the most likely phase to actually be soft.**

**Diagnostic**

- [ ] Write the `n`-th roots of unity and show `ω_n^n = 1`; draw them on the unit
      circle.
- [ ] State the halving and squaring properties that make the FFT recursion work.
- [ ] Give the two representations of a polynomial (coefficient vs point-value)
      and the cost of multiplication in each.
- [ ] Explain what "choosing Stützstellen" is for.

**Route on failure:** the deck itself (sl. 4–7 are genuinely self-contained), then
`source-ottmann-widmayer` Abschnitt 1.2, the named Literatur.

**Done when** the FFT's divide step looks inevitable rather than clever — the
halving property does the work.

> ⚠️ **Honest flag:** this is the one Phase 0 item that is *not* AlgoDat I recall.
> It is mathematics the course assumes from elsewhere. If it's soft, budget for
> it properly rather than hoping the deck carries you.

---

## Phase 0.8 — Determinants and orientation tests

**Named by:** `ad2_computationalgeometry` sl. 7 — *"Aus der Schulmathematik
sollten Methoden dafür bekannt sein"* — and sl. 9, which gives the test as
`det[x₁ x₂; y₁ y₂] = x₁y₂ − x₂y₁`.
**Budget if failed:** 30 min. **The cheapest phase here.**

**Diagnostic**

- [ ] Compute a 2×2 determinant and read off the orientation of two points about
      the origin from its **sign**.
- [ ] Say why the course prefers this to angles: it **avoids division and
      trigonometric functions**, which are expensive and numerically awkward
      (sl. 7).

**Route on failure:** the deck's sl. 7–9 are self-contained; 20 minutes there is
enough.

**Done when** the sign convention is automatic: positive ⟹ `p₁` lies clockwise
*after* `p₂`; negative ⟹ *before*.

---

## Phase 0.9 — Proof presentation, out loud

**Named by:** not by a deck — by the **exam format**. 30 minutes, oral, by Zoom.
**Budget:** ongoing, not a block.

There is no written script to hide behind and no time to reconstruct an argument
silently. The skill is stating a definition precisely, then walking a proof at
speaking pace while someone interrupts.

**Diagnostic:** pick any theorem from a deck you already understand. Explain it
aloud, timed, in **three minutes**, without notes, to an empty room. Record it.
Play it back.

Most people fail this on the first attempt while knowing the material perfectly
well. That gap is what this phase closes, and it does not close by reading.

**Route:** the per-topic **viva drills** in this suite
(`note-algo2-*-viva-drill`) are built for exactly this. Cross-reference
`source-algo2-frankfurt-klausuren` — its worked solutions double as
explain-aloud scripts even though the format is written.

**Done when** you can deliver any topic's five-minute summary cold.

---

## What is *not* a Phase 0 item

**Amortized analysis is a course topic, not a prerequisite** — it is the second
lecture (`ad2_amortizedanalysis`, 40 sl., CLRS 17.1–17.3). But **Fibonacci heaps
and splay trees both require it**, and both decks say so on their slide 2. So it
functions as an internal prerequisite:

> **Study order constraint:** amortized analysis must be complete before either
> Fibonacci heaps or splay trees is started. The lecture schedule respects this
> (20.–22. April, before Fibonacci on 22. April) but a self-directed order might
> not.

Likewise **max flow before bipartite matching** — the matching deck's own Übung
is *"Bipartite Matchings durch maximalen Fluss finden"* (sl. 2).

---

## Phase 0 budget summary

| Phase | Topic | If failed | Feeds |
|---|---|---|---|
| 0.1 | Asymptotics, elementary operations | 45 min | all |
| 0.2 | Recurrences, master theorem | 60 min | fast multiplication, FFT |
| 0.3 | ADT Dictionary, BSTs | 60 min | B-trees, splay trees |
| 0.4 | ADT Priority Queue, heaps | 60 min | Fibonacci heaps |
| 0.5 | Hashing with chaining + expected value | 75 min | cuckoo hashing |
| 0.6 | Graphs, traversal, Dijkstra | 75 min | shortest paths, max flow, matching |
| 0.7 | Complex roots of unity, polynomials | 90 min | FFT |
| 0.8 | Determinants, orientation | 30 min | computational geometry |
| 0.9 | Proof presentation, out loud | ongoing | the exam itself |

**Worst case — every phase fails: 8 hours.** Realistic case, if AlgoDat I is
reasonably intact: **2–3 hours**, concentrated in 0.7 (roots of unity) and 0.9
(speaking), with the rest passing their diagnostics.

**That spread is the point.** Run the diagnostics *first*, before committing to
the module, because the difference between 2 hours and 8 hours of Phase 0
materially changes what reinstating Algo 2 costs — and that decision has to be
made by the registration deadline of **10 September**.
