---
id: note-algo2-bipartite-matching
type: note
title: "Algo 2 T09 — Reference: Bipartites Matching"
created: "2026-08-16"
role: reference
state: evolving
authorship: operator-drafted
concepts: [concept-bipartite-matching, concept-max-flow, concept-graph-basics]
sources: [source-algo2-hu-materials, source-ottmann-widmayer]
contexts: [workspace-algo2-exam-prep]
---

> **Build note (2026-08-16).** Operator-drafted from `ad2_bipartitematching.pdf`
> (58 sl.). Companions: `-exercise-bank`, `-viva-drill`. Not yet worked by Aram.

# Algo 2 · Topic 9 — Bipartites Matching

*Lectures: 10. Juni `[1-12]`, 15. Juni `[13-37]`, 17. Juni `[38-end]`.*
***Literatur:** Ottmann/Widmayer Abschnitt 9.8, supplementing the slides.
**Leseempfehlung:** Vazirani [2020], *"A Proof of the MV Matching Algorithm"* —
still the fastest for general graphs (from 1980); read the beginning for an
overview.*

**Agenda (sl. 2):** what (bipartite) matchings are and what they're for ·
augmenting paths · **Hopcroft-Karp** · **Übung: bipartite matchings via maximum
flow** · Ausblick: maximum matching in general graphs.

> 🔗 **Requires T08.** The deck's own exercise is the flow reduction, and the
> augmenting-path idea is explicitly presented as the matching analogue of
> augmenting along residual paths.

---

## 1. Motivating problems (sl. 4–8)

**Example 1 (sl. 4–5) — dorm placement.** Two-person apartments; students state
whom they would share with. Model: `G = (V,E)` with `V` the students and an edge
when two are willing to share. **This is a general graph**, not bipartite.

**Example 2 (sl. 6–8) — study places.** Applicants state which universities they
would attend; each university `u` has a capacity `f(u)`. Model: a **bipartite**
graph `G = (U ∪̇ V, E)`. **Alternative modelling (sl. 8):** instead of a capacity
function, **duplicate each `u` into `f(u)` copies** — which reduces the capacitated
problem to plain matching.

---

## 2. Basic notions (sl. 10–12)

> **Definition (sl. 10).** `M ⊆ E` is a **matching** if its edges do not overlap —
> no two share an endpoint.

**Maximal vs maximum (sl. 11) — the distinction that matters.** A **maximal**
matching cannot be extended by adding an edge; a **maximum** matching has the
greatest possible cardinality. The deck's figure shows one that is maximal but not
maximum.

> **Erkenntnis (sl. 11):** the naive greedy that adds edges until stuck produces a
> **maximal** matching, which need not be maximum.

**Covered and free (sl. 12):** `v` is **covered** by `M` if some `e ∈ M` is
incident to it; otherwise `v` is **M-frei** (exposed).

---

## 3. Augmenting paths and Berge's theorem (sl. 14–23)

**Intuition (sl. 14):** analogous to finding a maximum flow via residual paths,
a non-maximum matching always admits an improvement.

> **Definitions (sl. 15–16).** An **`M`-alternating path** has length ≥ 1 and its
> edges alternate between `M` and `E \ M`. An **`M`-augmenting path** is an
> alternating path whose **both endpoints are `M`-free**.
>
> Augmenting: `M′ = M △ E(P)` (symmetric difference) is a matching with
> `|M′| = |M| + 1`.

> **Satz von Berge (sl. 18–22).** Let `M` and `M′` be matchings in `G` with
> `|M| < |M′|`. Then the subgraph `G′ = (V, M △ M′)` contains at least
> `|M′| − |M|` **vertex-disjoint `M`-augmenting paths**.
>
> **Proof idea:** in `M △ M′` every vertex has degree ≤ 2 (at most one edge from
> each matching), so the components are paths and even cycles, alternating by
> construction. Cycles contribute equally to both matchings; the surplus
> `|M′| − |M|` must therefore sit in paths that start and end with `M′`-edges —
> and those are exactly `M`-augmenting.

> **Characterization (sl. 22).** `M` is **maximum ⟺ there is no `M`-augmenting
> path.**

**Algorithmic use (sl. 23):** start from any matching (`M = ∅`, or a greedy
maximal one), repeatedly find an augmenting path and augment. Each augmentation
adds exactly one edge, so at most `n/2` rounds.

---

## 4. Hopcroft-Karp (sl. 25–48)

**Context (sl. 25):** for decades the fastest algorithm for bipartite matching.
*(Chen et al. [2022] now solve it in `O(m^{1+o(1)})` via a reduction to maximum
flow — the paper is held locally.)*

**The idea: augment along many shortest paths at once, in phases.**

> **Lemma (sl. 26–28).** Let `M` be a matching and `P` a **shortest**
> `M`-augmenting path. Then for every shortest `(M △ E(P))`-augmenting path `P′`,
> `|P′| ≥ |P|` — and if they share a vertex, `|P′| > |P|`. **Shortest augmenting
> path lengths grow monotonically.**

> **SAP-Packing (sl. 29).** A set `S` of **vertex-disjoint shortest**
> `M`-augmenting paths. *(SAP = shortest augmenting paths.)*

> **Lemma (sl. 30–34).** If `S = {P₁,…,P_ℓ}` is a **maximal** SAP-packing and
> `M′ = M △ E(P₁) △ … △ E(P_ℓ)`, then every shortest `M′`-augmenting path is
> **strictly longer** than the paths in `S`.

That is the phase structure: each phase augments along a maximal packing of
shortest paths, and the shortest-path length strictly increases afterwards.

```
Hopcroft-Karp(G = (V,E)):
1  M ← ∅
2  repeat
3      find a maximal SAP-packing S for M in G
4      augment M along all paths in S
5  until no augmenting path exists
```

> **Theorem (sl. 36–37).** Hopcroft-Karp needs at most **`O(√n)` phases**.
>
> **Proof idea:** the shortest augmenting-path length strictly increases each
> phase, so after `⌈√n⌉` phases every remaining augmenting path has length
> `> √n`, hence uses `> √n` vertices. Augmenting paths for the current `M` can be
> chosen vertex-disjoint (Berge), so at most `n/√n = √n` of them fit. Since each
> subsequent phase adds at least one matching edge, at most `√n` further phases
> remain. Total `O(√n)`.

**⚠️ Sl. 38 flags the gap:** the phase count alone is not the runtime. A phase must
be implemented efficiently.

> **Theorem (sl. 39–47).** For connected bipartite graphs with `m` edges, **one
> phase runs in `O(m)`**.

**How a phase works (sl. 40–46).** For bipartite `G = (A ∪̇ B, E)`:

1. **Level graph by BFS (sl. 43).** Start BFS from the set `F` of `M`-free
   vertices in `A`, alternating: unmatched edges from `A` to `B`, matched edges
   back from `B` to `A`. Stop at the first level containing `M`-free vertices in
   `B` — call that set `R`. Every shortest augmenting path runs from `F` to `R`
   inside this layered graph `G′`.
2. **Backward DFS (sl. 44).** Essentially a greedy selection of vertex-disjoint
   `R→F` paths in `G′`, deleting used vertices as you go.
3. **Properties (sl. 45).** Every `P ∈ S` is a shortest `M`-augmenting path, and
   `S` is maximal because DFS exhausted the layered graph.
4. **Augment (sl. 46).** The paths are vertex-disjoint, so all `|S|` augmentations
   can be applied at once.

Both traversals are `O(m)`.

> **Total runtime (sl. 47): `O(m√n)`.**

**Summary (sl. 48):** Berge gives existence of augmenting paths and the maximum
characterization; monotone growth of shortest lengths gives the phase structure;
`O(√n)` phases at `O(m)` each.

---

## 5. Ausblick: general graphs (sl. 50–55)

**What stays the same (sl. 51):** Berge's theorem, and the monotone growth of
shortest augmenting-path lengths.

**What breaks (sl. 52):** in a non-bipartite graph you cannot orient the edges as
in the bipartite case, so the level-graph search can go wrong.

> **Blossoms (sl. 53–54).** A **blossom** consists of an alternating path plus an
> **odd cycle**. Augmenting paths entering a blossom must leave it again to reach
> an `M`-free vertex — the odd cycle lets the search enter a vertex "on the wrong
> parity" and mis-conclude.

**Edmonds' algorithm (sl. 55):** systematic search with alternating paths from
free vertices, **contracting blossoms** when found, then expanding them back.

---

## 6. Überblick and Ausblick (sl. 57–58)

**Überblick.** Matchings; alternating and augmenting paths; Berge's theorem and
the characterization of maximum matchings; the connection between bipartite
matching and flows; Hopcroft-Karp.

**Ausblick (sl. 58).** Alongside graph colouring, the structure of maximum
matchings is a much-studied topic — e.g. the **Gallai-Edmonds decomposition**.

---

## 7. Exam-critical minimum

| Must be automatic | Where |
|---|---|
| Matching; **maximal vs maximum**, with the greedy caveat | sl. 10–11 |
| `M`-free, alternating path, **augmenting path** | sl. 12, 15 |
| `M △ E(P)` grows the matching by one | sl. 16 |
| **Satz von Berge**, and the degree-≤2 component argument | sl. 18–21 |
| `M` maximum ⟺ no augmenting path | sl. 22 |
| Monotone growth of shortest augmenting-path lengths | sl. 26 |
| SAP-packing, and the maximal-packing lemma | sl. 29–30 |
| **`O(√n)` phases**, and the counting argument | sl. 36–37 |
| One phase in `O(m)`: BFS level graph + backward DFS | sl. 39–46 |
| **`O(m√n)` total** | sl. 47 |
| Matching via max flow — the deck's own Übung | sl. 2 |
| Blossoms and Edmonds for general graphs | sl. 53–55 |

**Traps:** conflating maximal with maximum; stating Berge as "there is an
augmenting path" without the disjointness count; giving `O(√n)` as the *runtime*
rather than the phase count (sl. 38 warns about exactly this); claiming
Hopcroft-Karp works unchanged on general graphs — blossoms are precisely why it
does not.
