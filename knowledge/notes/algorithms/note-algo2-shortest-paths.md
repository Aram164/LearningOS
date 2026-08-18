---
id: note-algo2-shortest-paths
type: note
title: "Algo 2 T07 — Reference: Kürzeste Wege in Graphen"
created: "2026-08-16"
role: reference
state: evolving
authorship: operator-drafted
concepts: [concept-shortest-paths, concept-graph-basics]
sources: [source-algo2-hu-materials, source-clrs]
contexts: [workspace-algo2-exam-prep]
---

> **Build note (2026-08-16).** Operator-drafted from `ad2_shortestpaths.pdf`
> (54 sl.). Companions: `-exercise-bank`, `-viva-drill`. Not yet worked by Aram.

# Algo 2 · Topic 7 — Kürzeste Wege in Graphen

*Lectures: 11. Mai `[1-10]`, 18. Mai `[11-45]`, 20. Mai `[46-end]`.*
***Literatur:** CLRS Kap. 24 and 25. **Note the deck's own scope line:** *"Alles
Weitere wurde bereits in AlgoDat 1 behandelt"* — **Dijkstra and BFS are assumed,
not taught.** **Leseempfehlung:** Thorup [1999], held locally.*

**Agenda (sl. 2):** (Erinnerung) graphs and shortest paths · shortest paths via
bounds and **relaxation** · handling negative cycles · **Bellman-Ford** ·
**Johnson**.

> 🎯 **What is actually new here** is narrow: negative weights. Dijkstra already
> solved the non-negative case in AlgoDat I. Both new algorithms exist because of
> negative edges, and Johnson exists to *remove* them.

---

## 1. Graph vocabulary (sl. 5–8) — Phase 0.6

**Directed graph** `G = (V, A)` with `A ⊆ {(u,v) | u,v ∈ V, u ≠ v}`.
**Weg (walk):** a sequence `W = (v₁,…,v_r)` with `(vᵢ,vᵢ₊₁) ∈ A`.
**Pfad (path):** a walk with no repeated vertices.
**Geschlossener Weg:** a walk with `v₁ = v_r`. **Kreis (cycle):** a closed walk
whose `v₁,…,v_{r−1}` are pairwise distinct.

> **The English glossary (sl. 8) — memorize it, the terms cross-translate badly:**
> Walk = Weg · Trail = Weg ohne wiederholte Kanten · **Path = Pfad** ·
> Closed walk = geschlossener Weg · Circuit / closed trail = geschlossener Weg
> ohne wiederholte Kanten · **Cycle = Kreis**.

---

## 2. Lengths, cycles, distances (sl. 10–16)

**Length** of a walk under weights `w : A → ℝ` is the sum of its edge weights.

**Shortest walks and cycles (sl. 11–13).** If a shortest `v₀,v_ℓ`-walk repeats a
vertex, it contains a cycle `K`; removing `K` cannot increase the length, so `K`
has length ≥ 0 — and if some cycle had negative length no shortest walk would
exist at all.

> **Consequence (sl. 13):** if a shortest `s,t`-walk exists, then a shortest
> `s,t`-**path** exists. Paths suffice.

> **Distance (sl. 15).** `δ(u,v) ∈ ℝ ∪ {∞, −∞}`:
> `∞` if no `u,v`-walk exists; `−∞` if arbitrarily short walks exist (a reachable
> negative cycle on the way); otherwise the minimum length.

**Problems (sl. 16).** **Single-source:** given `s`, compute `δ(s,v)` for all `v`.
**All-pairs:** compute `δ(u,v)` for all pairs.

**Assumed known (sl. 17):** **BFS** computes distances from `s` in *unweighted*
graphs.

---

## 3. Bounds and relaxation (sl. 20–25)

Most single-source algorithms share the same machinery.

**Optimal substructure (sl. 21).** Every subwalk of a shortest walk is itself a
shortest walk between its endpoints.

**Implicit representation (sl. 22).** Store a predecessor `π[v]` for each vertex;
the `π`-pointers encode a shortest-path tree.

> **Relaxation of an edge `(u,v)` (sl. 23).** Test whether the upper bound `d[v]`
> for `δ(s,v)` improves by going via `u`:
> ```
> if d[u] + w(u,v) < d[v] then
>     d[v] ← d[u] + w(u,v);  π[v] ← u
> ```

**Dijkstra, in brief (sl. 24).** Finds distances from `s` when **no weight is
negative**; maintains a set `S` of finished vertices and repeatedly relaxes out of
the closest unfinished one. *(AlgoDat I — recalled, not derived.)*

> **Lemma (sl. 25).** Starting from `d[s] = 0` and `d[v] = ∞` otherwise, after
> **any** sequence of edge relaxations: `d[v] ≥ δ(s,v)` always, and once
> `d[v] = δ(s,v)` it never changes again.

---

## 4. Bellman-Ford (sl. 27–41)

Solves single-source shortest paths **when weights may be negative**.

```
Bellman-Ford(G, w, s):
1  foreach v ∈ V do π[v] ← nil; d[v] ← ∞
2  d[s] ← 0
3  for i ← 1 to |V| − 1 do
4      foreach (u,v) ∈ A do relax(u,v)
5  foreach (u,v) ∈ A do
6      if d[u] + w(u,v) < d[v] then return false     // negative cycle
7  return true
```

**Runtime (sl. 29): `Θ(nm)`** — `|V|−1` passes over all `|A|` edges.

**Correctness plan (sl. 30):** (a) with no reachable negative cycle, `d[v] = δ(s,v)`
after `n−1` iterations; (b) with one, the algorithm returns `false`.

**The supporting lemmas:**

> **Sl. 31.** After any sequence of relaxations, `d[v] ≥ δ(s,v)` for all `v`.
>
> **Sl. 33 — the key one.** Let `W = (v₀,…,v_k)` with `s = v₀` be any walk. If the
> edges of `W` have been relaxed **in order** `(v₀,v₁), …, (v_{k−1},v_k)` (possibly
> with other relaxations interleaved), then `d[v_k] ≤ w(W)`.

**Why `n−1` iterations suffice (sl. 36).** A shortest path has at most `n−1`
edges; iteration `i` relaxes every edge, so after `i` iterations every shortest
path with `≤ i` edges has been "traced" in order. Unreachable vertices keep
`d[v] = ∞` (sl. 37).

> **Theorem (sl. 39–40).** If a negative-length cycle is reachable from `s`, the
> algorithm returns `false`.
>
> **Proof idea:** suppose it returned `true`. Then `d[vᵢ₊₁] ≤ d[vᵢ] + w(vᵢ,vᵢ₊₁)`
> around the cycle. Summing over the cycle, the `d`-terms cancel telescopically,
> leaving `0 ≤ Σ w(vᵢ,vᵢ₊₁) < 0` — contradiction.

**Summary (sl. 41):** computes shortest-path lengths from `s` when no reachable
negative cycle exists, and otherwise reports one.

---

## 5. All pairs: Johnson's algorithm (sl. 43–51)

**The idea (sl. 44):** if weights were non-negative, we could just run Dijkstra
`n` times, which is fast. **So make them non-negative** — without changing which
paths are shortest.

> **Reweighting lemma (sl. 45–46).** For any `h : V → ℝ`, define
> $$\hat w(u,v) := w(u,v) + h(u) - h(v)$$
> Then: (1) a walk `W` is a shortest `s,t`-walk w.r.t. `w` **iff** it is one
> w.r.t. `ŵ`; (2) the length of every **cycle** is unchanged.

**Why it works:** along a walk the `h`-terms telescope, so `ŵ(W) = w(W) + h(s) −
h(t)` — a constant offset depending only on the endpoints. Around a cycle the
offset is zero, which is why negative cycles cannot be hidden by reweighting.

**Choosing `h` (sl. 48–49).** Build `G′` by adding a new vertex `s` with a
**0-weight** edge to every vertex. Run Bellman-Ford from `s`. If there is no
negative cycle, set `h(v) := d[v] = δ(s,v)`. Then for every edge,
`δ(s,v) ≤ δ(s,u) + w(u,v)`, i.e. `ŵ(u,v) = w(u,v) + h(u) − h(v) ≥ 0`. ∎

> **Johnson's algorithm (sl. 50).** Bellman-Ford on `G′` in `Θ(nm)` to get `h`
> (or report a negative cycle); reweight; run Dijkstra from each of the `n`
> vertices; convert the distances back.

**Übung (sl. 51):** does it matter that all new edges `(s,v)` have weight 0?
Could an existing vertex be used instead of a new one?

---

## 6. Überblick and Ausblick (sl. 53–54)

**Überblick.** Walks, paths, closed walks and cycles in directed graphs;
algorithms based on bounds and relaxation; handling negative weights and negative
cycles; Bellman-Ford; all-pairs via Johnson.

**Ausblick (sl. 54).** Reachability and distances are fundamental with many
further research directions — including substantially faster methods under
restrictions (cf. **Thorup 1999**, linear time for undirected graphs with positive
integer weights, held locally as the Leseempfehlung).

---

## 7. Exam-critical minimum

| Must be automatic | Where |
|---|---|
| Weg vs Pfad vs Kreis, and the English glossary | sl. 6–8 |
| `δ(u,v)` with its `∞` and `−∞` cases | sl. 15 |
| Shortest walk ⟹ a shortest path exists | sl. 13 |
| Optimal substructure, `π[v]`, and the relaxation step | sl. 21–23 |
| Dijkstra needs **non-negative** weights | sl. 24 |
| Bellman-Ford's `n−1` passes and `Θ(nm)` | sl. 28–29 |
| Why `n−1` suffices (path-length argument) | sl. 33, 36 |
| The negative-cycle detection and its telescoping proof | sl. 39–40 |
| The reweighting lemma **and why cycles are unchanged** | sl. 45–46 |
| `h(v) := δ(s,v)` from a new 0-edge source | sl. 48–49 |
| Johnson = BF `Θ(nm)` + `n ×` Dijkstra | sl. 50 |

**Traps:** claiming Dijkstra works with negative edges "if you re-add vertices";
saying Bellman-Ford runs `n` iterations (it is `n−1`, plus one detection pass);
forgetting that reweighting preserves cycle lengths — that is precisely why it
cannot mask a negative cycle; being unable to say *where* the `h`-terms telescope.
