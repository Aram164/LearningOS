---
id: note-algo2-bipartite-matching-exercise-bank
type: note
title: "Algo 2 T09 — Exercise Bank: Bipartites Matching"
created: "2026-08-16"
role: exercise-bank
state: evolving
authorship: operator-drafted
concepts: [concept-bipartite-matching, concept-max-flow, concept-graph-basics]
sources: [source-algo2-hu-materials, source-ottmann-widmayer, source-algo2-frankfurt-klausuren]
contexts: [workspace-algo2-exam-prep]
---

> **Build note (2026-08-16).** Operator-drafted from `ad2_bipartitematching.pdf`.
> Solutions operator-computed, **unverified by Aram**. Deck wins on disagreement.

# Algo 2 · Topic 9 — Exercise Bank

**Scope:** matchings and the maximal/maximum distinction, alternating and
augmenting paths, Berge's theorem, SAP-packings, Hopcroft-Karp with its phase
bound and phase implementation, the flow reduction, blossoms.

## 1. Local material

| File | What | Where |
|---|---|---|
| `note-algo2-bipartite-matching` | Reference (§ refs below) | this vault |
| `note-algo2-bipartite-matching-viva-drill` | Oral drill | this vault |
| `note-algo2-maximum-flow` | The reduction target | this vault |
| Ottmann/Widmayer 9.8 | **Assigned supplement** | `material://source-ottmann-widmayer/ow.pdf` |
| Vazirani 2020 | Leseempfehlung — read the beginning | `material://source-algo2-hu-materials` |

## 2. Drills

### A. Basics

**A1.** Distinguish maximal from maximum, and say what the greedy gives.

<details><summary>Solution</summary>

**Maximal:** no edge can be added. **Maximum:** greatest cardinality. The naive
greedy that adds edges until stuck yields a **maximal** matching, which may be
strictly smaller than maximum. *(Ref §2, sl. 11.)*
</details>

**A2.** Define alternating and augmenting paths, and state the effect of
augmenting.

<details><summary>Solution</summary>

**Alternating:** length ≥ 1, edges alternate between `M` and `E \ M`.
**Augmenting:** alternating **and both endpoints `M`-free**. Then
`M △ E(P)` is a matching with one more edge. *(Ref §3, sl. 15–16.)*
</details>

**A3. [open]** Draw a path on 6 vertices with a maximal matching of size 2 and
show the augmenting path that improves it to 3.

**A4. [open]** Sl. 8 offers two models for university capacities `f(u)`: a
capacity function, or `f(u)` copies of `u`. Show the two are equivalent, and say
which you'd prefer for an implementation.

### B. Berge

**B1.** State Berge's theorem.

<details><summary>Solution</summary>

If `|M| < |M′|`, then `G′ = (V, M △ M′)` contains at least `|M′| − |M|`
**vertex-disjoint `M`-augmenting paths**. *(Ref §3, sl. 18.)*
</details>

**B2.** Prove it.

<details><summary>Solution</summary>

In `M △ M′` each vertex is incident to at most one edge of `M` and one of `M′`, so
degrees are ≤ 2 and the components are paths and cycles, alternating between the
two matchings. Cycles are even and contribute equally to both. The surplus
`|M′| − |M|` must therefore lie in components that are paths with more `M′`-edges
than `M`-edges — i.e. paths beginning and ending with `M′`-edges, whose endpoints
are `M`-free. Those are `M`-augmenting, and being distinct components they are
vertex-disjoint. *(Ref §3, sl. 20–21.)*
</details>

**B3.** State the maximum characterization and derive it from B1.

<details><summary>Solution</summary>

`M` is maximum ⟺ no `M`-augmenting path exists. (⇐) If one existed, augmenting
would give a larger matching. (⇒) If `M` were not maximum, take `M′` larger;
Berge gives ≥ 1 augmenting path. *(Ref §3, sl. 22.)*
</details>

**B4. [open]** Why can Berge's theorem be used to bound the number of
augmentations needed by any augmenting-path algorithm?

### C. Hopcroft-Karp

**C1.** State the monotonicity lemma and the SAP-packing lemma.

<details><summary>Solution</summary>

**Sl. 26:** if `P` is a shortest `M`-augmenting path, every shortest
`(M △ E(P))`-augmenting path `P′` has `|P′| ≥ |P|`, strictly longer if they share a
vertex. **Sl. 30:** if `S` is a **maximal** SAP-packing and `M′` is `M` augmented
along all of `S`, then every shortest `M′`-augmenting path is strictly longer than
those in `S`. *(Ref §4.)*
</details>

**C2.** Prove the `O(√n)` phase bound.

<details><summary>Solution</summary>

Shortest augmenting-path length strictly increases per phase, so after `⌈√n⌉`
phases every remaining augmenting path has length `> √n` and so uses `> √n`
vertices. By Berge the remaining augmenting paths can be taken vertex-disjoint, so
at most `n/√n = √n` of them exist — bounding the number of further augmentations,
hence further phases, by `√n`. Total `O(√n)`. *(Ref §4, sl. 36–37.)*
</details>

**C3.** Describe one phase and give its cost.

<details><summary>Solution</summary>

**BFS** from the `M`-free vertices of `A`, alternating unmatched edges `A→B` and
matched edges `B→A`, stopping at the first level containing `M`-free vertices of
`B` — this builds the level graph `G′`. **Backward DFS** greedily selects
vertex-disjoint paths from `R` back to `F`, deleting used vertices. The result is
a maximal SAP-packing; all augmentations apply at once since the paths are
vertex-disjoint. Both traversals `O(m)`, so **`O(m)` per phase**. *(Ref §4,
sl. 40–46.)*
</details>

**C4.** Total runtime, and the warning on sl. 38?

<details><summary>Solution</summary>

**`O(m√n)`**. Sl. 38's warning: the `O(√n)` phase count is **not** the runtime —
the per-phase implementation must also be bounded, which is the separate theorem
of sl. 39. *(Ref §4, sl. 38, 47.)*
</details>

**C5. [open]** Run one phase by hand on a small bipartite graph: draw the level
graph, pick the packing, augment.

**C6. [open]** Why must the paths in a packing be **vertex**-disjoint rather than
merely edge-disjoint?

### D. The flow reduction — the deck's own Übung

**D1. [open]** Build the flow network that solves bipartite matching: add `s` and
`t`, orient the edges, choose capacities. Prove max flow value = maximum matching
size. *(Ref §5 of `note-algo2-maximum-flow`; the deck sets this as its Übung,
sl. 2.)*

**D2. [open]** With that reduction and Edmonds-Karp, what bound do you get?
Compare with `O(m√n)` and say when each is better.

**D3. [open]** Chen et al. [2022] solve matching in `O(m^{1+o(1)})` **via max
flow**. What does that say about the relationship between the two problems?

### E. General graphs

**E1.** What is a blossom and why does it break the bipartite approach?

<details><summary>Solution</summary>

A blossom is an alternating path plus an **odd cycle**. In a bipartite graph no
odd cycles exist, so the level graph is well defined. In general graphs the odd
cycle lets a search reach a vertex on the "wrong parity", so an augmenting path
appears to exist where it does not. Edmonds' algorithm **contracts** blossoms and
later expands them. *(Ref §5, sl. 52–55.)*
</details>

**E2. [open]** Which results survive into general graphs unchanged? *(Ref §5,
sl. 51.)*

## 3. External practice — scope filter

| Source | Take | Avoid |
|---|---|---|
| O/W 9.8 | **Assigned supplement** | its wider graph-algorithm survey |
| Vazirani 2020 | **The beginning only**, for the overview | the full MV proof |
| Frankfurt Klausuren | Matching items as explain-aloud drill | written framing |

**Filter:** in scope are matchings, Berge, Hopcroft-Karp with both theorems, and
the flow reduction. **Edmonds' algorithm and blossoms are Ausblick** (sl. 49–55)
— understand *why* the bipartite method fails and what the fix is called; do not
learn the algorithm in detail. Gallai-Edmonds decomposition and weighted matching
(Hungarian algorithm) are outside the course.
