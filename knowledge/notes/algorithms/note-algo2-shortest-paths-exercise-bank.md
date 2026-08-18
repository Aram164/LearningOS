---
id: note-algo2-shortest-paths-exercise-bank
type: note
title: "Algo 2 T07 — Exercise Bank: Kürzeste Wege"
created: "2026-08-16"
role: exercise-bank
state: evolving
authorship: operator-drafted
concepts: [concept-shortest-paths, concept-graph-basics]
sources: [source-algo2-hu-materials, source-clrs, source-algo2-frankfurt-klausuren]
contexts: [workspace-algo2-exam-prep]
---

> **Build note (2026-08-16).** Operator-drafted from `ad2_shortestpaths.pdf`.
> Solutions operator-computed, **unverified by Aram**. Deck wins on disagreement.

# Algo 2 · Topic 7 — Exercise Bank

**Scope:** graph vocabulary, distance with `±∞`, relaxation and optimal
substructure, Bellman-Ford with correctness and negative-cycle detection,
reweighting, Johnson.

## 1. Local material

| File | What | Where |
|---|---|---|
| `note-algo2-shortest-paths` | Reference (§ refs below) | this vault |
| `note-algo2-shortest-paths-viva-drill` | Oral drill | this vault |
| `note-algo2-phase0-prerequisites` | Phase 0.6 = graphs + Dijkstra | this vault |
| CLRS Kap. 24–25 | **Assigned reading** | `material://source-clrs/clrs-de.pdf` |
| Thorup 1999 | Leseempfehlung | `material://source-algo2-hu-materials` |

## 2. Drills

### A. Vocabulary and distances

**A1.** Distinguish Weg, Pfad, geschlossener Weg, Kreis — and give the English.

<details><summary>Solution</summary>

Weg = walk (vertices may repeat) · Pfad = path (no repeats) · geschlossener Weg =
closed walk (`v₁ = v_r`) · Kreis = cycle (closed, interior vertices distinct).
English also has *trail* (no repeated **edges**) and *circuit*. *(Ref §1,
sl. 6–8.)*
</details>

**A2.** Define `δ(u,v)` including both infinite cases.

<details><summary>Solution</summary>

`∞` if no `u,v`-walk exists; `−∞` if arbitrarily short walks exist (a negative
cycle lies on some `u,v`-walk); otherwise the minimum walk length. *(Ref §2,
sl. 15.)*
</details>

**A3.** Show that if a shortest `s,t`-walk exists, a shortest `s,t`-path exists.

<details><summary>Solution</summary>

If a shortest walk repeats a vertex it contains a cycle `K`; deleting `K` gives a
walk of length `w(W) − w(K)`. Since `W` is shortest, `w(K) ≥ 0`, so deleting does
not increase the length. Repeat until no vertex repeats. *(Ref §2, sl. 11–13.)*
</details>

### B. Relaxation and Bellman-Ford

**B1.** Write the relaxation step and state the invariant lemma.

<details><summary>Solution</summary>

`if d[u] + w(u,v) < d[v] then d[v] ← d[u] + w(u,v); π[v] ← u`. Lemma (sl. 25/31):
starting from `d[s]=0`, `d[v]=∞`, after **any** relaxation sequence `d[v] ≥
δ(s,v)`, and once `d[v] = δ(s,v)` it never changes. *(Ref §3.)*
</details>

**B2.** Write Bellman-Ford and give its runtime.

<details><summary>Solution</summary>

See reference §4. `|V|−1` passes over all edges, then one detection pass.
**`Θ(nm)`**. *(Ref §4, sl. 28–29.)*
</details>

**B3.** Why do `n−1` iterations suffice?

<details><summary>Solution</summary>

A shortest path has at most `n−1` edges. By the path lemma (sl. 33), if the edges
of a walk are relaxed **in order**, `d` at its end is at most the walk's length.
Each iteration relaxes every edge, so after `i` iterations all shortest paths with
`≤ i` edges are accounted for. *(Ref §4, sl. 33, 36.)*
</details>

**B4.** Prove the negative-cycle detection is correct.

<details><summary>Solution</summary>

Suppose a reachable negative cycle `(v₀,…,v_k = v₀)` exists but the algorithm
returned `true`. Then no edge relaxes further, so `d[vᵢ₊₁] ≤ d[vᵢ] + w(vᵢ,vᵢ₊₁)`
for each `i`. Summing around the cycle, the `d`-terms cancel telescopically,
giving `0 ≤ Σᵢ w(vᵢ,vᵢ₊₁) < 0` — contradiction. *(Ref §4, sl. 39–40.)*
</details>

**B5. [open]** Run Bellman-Ford by hand on a 5-vertex graph with two negative
edges but no negative cycle. Record `d` after each pass.

**B6. [open]** Modify the graph in B5 to create a negative cycle and show which
edge triggers detection.

**B7. [open]** Why does Dijkstra fail on negative edges? Give a concrete
4-vertex counterexample where it returns a wrong distance. *(Ref §3 — this is the
motivation for the entire lecture.)*

### C. Johnson and reweighting

**C1.** State the reweighting lemma and both of its claims.

<details><summary>Solution</summary>

For any `h : V → ℝ`, `ŵ(u,v) := w(u,v) + h(u) − h(v)`. Then (1) `W` is a shortest
`s,t`-walk w.r.t. `w` iff w.r.t. `ŵ`; (2) every **cycle** has the same length
under both. *(Ref §5, sl. 45–46.)*
</details>

**C2.** Prove claim (1) by telescoping.

<details><summary>Solution</summary>

For `W = (v₀,…,v_k)`, `ŵ(W) = Σ(w(vᵢ,vᵢ₊₁) + h(vᵢ) − h(vᵢ₊₁)) = w(W) + h(v₀) −
h(v_k)`. The offset depends only on the endpoints, so the ordering of `s,t`-walks
by length is unchanged. For a cycle `v₀ = v_k`, the offset is 0. *(Ref §5.)*
</details>

**C3.** How is `h` chosen, and why does it make `ŵ` non-negative?

<details><summary>Solution</summary>

Add a new vertex `s` with 0-weight edges to all vertices; run Bellman-Ford; set
`h(v) := δ(s,v)`. Then the triangle-type inequality `δ(s,v) ≤ δ(s,u) + w(u,v)`
holds for every edge, i.e. `h(v) ≤ h(u) + w(u,v)`, i.e.
`ŵ(u,v) = w(u,v) + h(u) − h(v) ≥ 0`. *(Ref §5, sl. 48–49.)*
</details>

**C4.** Give Johnson's total runtime.

<details><summary>Solution</summary>

Bellman-Ford once: `Θ(nm)`. Then `n` Dijkstra runs. With a Fibonacci heap each is
`O(m + n log n)`, giving `O(nm + n² log n)`. *(Ref §5, sl. 50 — and note the
**cross-wire to T04**: this is where Fibonacci heaps pay off.)*
</details>

**C5. [open]** Answer the deck's Übung (sl. 51): does it matter that all new edges
`(s,v)` have weight 0? Could an existing vertex serve as `s` instead?

**C6. [open]** Why can reweighting **not** be used to make Bellman-Ford
unnecessary — i.e. why can't we just reweight away a negative cycle? *(Ref §5,
claim (2).)*

### D. Cross-wires

**D1. [open]** Compare Johnson with running Bellman-Ford `n` times. When is
Johnson better, and by how much?

**D2. [open]** Where would a Fibonacci heap (T04) change Johnson's bound? State
both versions. *(Ref §5.)*

**D3. [open]** Max flow (T08) also uses BFS on a graph that changes each round.
Compare the role of BFS there with its role in Dijkstra here.

## 3. External practice — scope filter

| Source | Take | Avoid |
|---|---|---|
| CLRS Kap. 24–25 | **Assigned**; Bellman-Ford, Johnson | Floyd-Warshall unless you want it for contrast — the deck teaches Johnson |
| Thorup 1999 | Leseempfehlung, for the Ausblick only | its full analysis |
| Frankfurt Klausuren | Shortest-path items as explain-aloud drill | written framing |

**Filter:** in scope are relaxation, Bellman-Ford with correctness, negative-cycle
detection, reweighting and Johnson. Dijkstra and BFS are **assumed** (Phase 0.6),
not examined as new material — but you must be able to state Dijkstra and its
weight assumption on demand. A*, bidirectional search and contraction hierarchies
are outside the course.
