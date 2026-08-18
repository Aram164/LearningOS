---
id: note-algo2-maximum-flow
type: note
title: "Algo 2 T08 — Reference: Maximaler Fluss"
created: "2026-08-16"
role: reference
state: evolving
authorship: operator-drafted
concepts: [concept-max-flow, concept-graph-basics]
sources: [source-algo2-hu-materials, source-clrs]
contexts: [workspace-algo2-exam-prep]
---

> **Build note (2026-08-16).** Operator-drafted from `ad2_maximumflow.pdf`
> (67 sl.). Companions: `-exercise-bank`, `-viva-drill`. Not yet worked by Aram.

# Algo 2 · Topic 8 — Maximaler Fluss

*Lectures: 20. Mai `[1-13]`, 27. Mai `[14-34]`, 8. Juni `[35-56]`, 10. Juni
`[57-end]` — **four sessions, the most of any topic**, split by the two
`Keine Vorlesung` days on 1. and 3. Juni.*
***Literatur:** CLRS Kap. 26, sections 26.1–26.2. The deck warns that **notation
differs slightly and the ordering is different** — read the book, but answer in
the deck's notation.*

**Agenda (sl. 2):** flow networks and flows · a simple greedy algorithm ·
**Ford-Fulkerson** · **Edmonds-Karp** · the **max-flow min-cut theorem**.

---

## 1. Flow networks and flows (sl. 4–8)

> **Definition (sl. 4).** A **flow network** is a tuple `N = (G, c, s, t)` with a
> directed graph `G = (V,A)`, a capacity function `c : A → ℝ⁺`, and two
> distinguished vertices: the **source** `s` and the **sink** `t`.

**Notation (sl. 5):** `δ⁻(v)` = edges entering `v`; `δ⁺(v)` = edges leaving `v`.

> **Definition (sl. 6).** A **flow** is `f : A → ℝ≥0` satisfying
> 1. **capacity constraint:** `f(a) ≤ c(a)` for all `a ∈ A`;
> 2. **flow conservation:** for all `v ∈ V \ {s,t}`,
>    `Σ_{a ∈ δ⁻(v)} f(a) = Σ_{a ∈ δ⁺(v)} f(a)`.

> **Value (sl. 7).** `|f| = Σ_{a ∈ δ⁺(s)} f(a) − Σ_{a ∈ δ⁻(s)} f(a)` — net
> outflow from the source.

**Problem (sl. 8):** find a flow maximizing `|f|`. Remarkably, **intelligent
greedy algorithms solve it optimally**; the best known algorithm is not greedy.

---

## 2. A greedy attempt, and why it fails (sl. 9–13)

**Idea (sl. 9):** iteratively augment `f` along `s,t`-paths using only edges with
positive **residual capacity** `c(a) − f(a)`.

**Übung (sl. 10):** augmenting along a path by the smallest residual capacity
`x > 0` always yields a valid flow again.

```
GreedyFlow(G, c, s, t):
1  foreach a ∈ A do f(a) ← 0
2  while there is an s,t-path P with positive residual capacity do
3      augment f along P
```

**Why this is not enough (sl. 12–13):** augmenting along *arbitrary* paths can
reach a state where no augmenting path remains but `f` is **not** maximum. The
fix must allow **undoing** earlier decisions — which is exactly what the residual
network provides.

---

## 3. Ford-Fulkerson (sl. 15–22)

> **Residual network (sl. 15).** For a flow `f` in `N`, `N_f = (G_f, c_f, s, t)`
> has, for each `a = (u,v) ∈ A`:
> - a **forward edge** `(u,v)` with `c_f = c(a) − f(a)`, if positive;
> - a **backward edge** `(v,u)` with `c_f = f(a)`, if positive.
>
> Backward edges are what let the algorithm retract flow it previously sent.

**Augmenting (sl. 17–19).** For an `s,t`-path `P` in `N_f`, set
`x = min_{a ∈ P} c_f(a)` and update

$$f'(a) = \begin{cases} f(a) + x & \text{if } \overrightarrow{a} \text{ is an edge of } P \\ f(a) - x & \text{if } \overleftarrow{a} \text{ is an edge of } P \\ f(a) & \text{otherwise}\end{cases}$$

Sl. 18–19 verify that `f′` still satisfies the capacity constraint and flow
conservation.

```
Ford-Fulkerson(N):
1  foreach a ∈ A do f(a) ← 0
2  build the residual network N_f
3  while there is an s,t-path P in N_f do
4      augment f along P;  rebuild N_f
5  return f
```

> **Lemma (sl. 21).** With **integer** capacities, Ford-Fulkerson terminates —
> each augmentation raises `|f|` by at least 1.

**Runtime (sl. 22):** at most `F` iterations where `F` is the maximum flow value,
each costing `O(m)` → **`O(F·m)`**. This is **not polynomial in the input size**,
since `F` can be exponential in the number of bits. With irrational capacities it
need not terminate at all.

---

## 4. Optimality: cuts (sl. 24–35)

> **Definition (sl. 25).** A **cut** of `N` is a pair `(S,T)` with `S ∪̇ T = V`,
> `s ∈ S`, `t ∈ T`. Its capacity is `c(S,T) = Σ_{a ∈ δ⁺(S)} c(a)`.

> **Lemma (sl. 26–28).** For **every** flow `f` and **every** cut `(S,T)`:
> `|f| ≤ c(S,T)`.
>
> **Proof (sl. 27):** rewrite `|f|` by adding the (zero) conservation terms for
> every `v ∈ S \ {s}`; everything internal to `S` cancels, leaving the net flow
> across the cut, which is bounded by its capacity.

**This is weak duality** — every cut certifies an upper bound on every flow.

> **The key lemma (sl. 29–34).** For any flow `f`, the following are
> **equivalent**:
> 1. `f` is a maximum flow;
> 2. there is **no `s,t`-path in the residual network `N_f`**;
> 3. there exists a cut `(S,T)` with `|f| = c(S,T)`.

**Proof structure.** (1)⇒(2): an augmenting path would improve `f`. (2)⇒(3): let
`S` be the set of vertices reachable from `s` in `G_f`; then `t ∉ S`, and for every
`a ∈ δ⁺(S)` we must have `f(a) = c(a)` (else a forward residual edge would leave
`S`) and for every `a ∈ δ⁻(S)`, `f(a) = 0` (else a backward residual edge would).
Hence `|f| = c(S,T)`. (3)⇒(1): by the weak-duality lemma, no flow can exceed
`c(S,T)`, so `f` is maximum.

**Summary (sl. 35):** Ford-Fulkerson does not always terminate, but is guaranteed
`O(F·m)` with integer capacities — **and is correct whenever it terminates**, by
(2)⇒(1).

---

## 5. Edmonds-Karp (sl. 37–45)

> **The improvement (sl. 37):** always augment along a **shortest** `s,t`-path in
> the residual network — i.e. choose it by BFS.

> **Lemma (sl. 38–40).** Under Edmonds-Karp, the residual distances `δ_f(s,v)`
> **increase monotonically** over the run, for every `v`.

> **Theorem (sl. 41–44).** The total number of iterations is `O(|V|·|A|)`.
>
> **Proof idea:** call an edge **critical** on an augmentation if it is the
> bottleneck. When `(u,v)` is critical it lies on a shortest augmenting path, so
> `δ_f(s,v) = δ_f(s,u) + 1`. Before it can become critical again, the flow on it
> must be reduced, which requires `(v,u)` on a later augmenting path — and by
> monotonicity the distance to `u` has grown by at least 2 in between. Since
> distances are bounded by `|V|`, **each edge is critical at most `|V|/2` times**.

**Runtime (sl. 45):** `O(|V|·|A|²)` — and crucially, **polynomial and independent
of the capacities.**

---

## 6. Max-flow min-cut (sl. 47–49)

> **Theorem (sl. 47).** For a flow network `N`, the **maximum value of a flow
> equals the minimum capacity of a cut**.

Immediate from the key lemma: (1)⇒(3) gives a cut matching the max flow, and the
weak-duality lemma says no cut can be smaller.

**Finding a minimum cut (sl. 49):** compute a maximum flow `f` (Edmonds-Karp),
build `N_f`, and let `S` = the vertices reachable from `s` in `G_f`. Then
`(S, V\S)` is a minimum cut. **The algorithm for max flow is also the algorithm
for min cut.**

---

## 7. Efficiently solvable variants (sl. 51–64)

**Non-overlapping `s,t`-paths (sl. 52–54).** Given `G` and `s,t`, find a maximum
set of **edge-disjoint** `s,t`-paths. Set all capacities to 1 and compute a max
flow; read off `k = |f|` paths by tracing unit flow from `s`. They share no edges
because each has capacity 1.

**Undirected graphs (sl. 55–56).** Replace each undirected edge `{u,v}` by the two
directed edges `(u,v)` and `(v,u)`, each with the original capacity.

**Vertex capacities (sl. 57–60).** Replace each `v ∈ V \ {s,t}` by `v⁺` and `v⁻`
joined by an edge of capacity `c(v)`; incoming edges land on `v⁻`, outgoing leave
`v⁺`. Proved equal by mapping solutions both ways.

> **Sl. 61:** **all four combinations** — vertex or edge capacities × directed or
> undirected — reduce to the basic problem and are efficiently solvable.

> **Menger's theorem (sl. 62–63).** For non-adjacent `s,t` in an undirected graph,
> the maximum number of **vertex-disjoint** `s,t`-paths equals the minimum size of
> an `s,t`-**separator**. There is an edge-disjoint variant too (where `s,t` may be
> adjacent), matching minimum edge cuts.

**Sl. 64:** min cuts and separators are computed via max-flow min-cut.

---

## 8. Überblick and Ausblick (sl. 66–67)

**Überblick.** Flow networks and flows; a simple non-optimal greedy; the residual
network; Ford-Fulkerson; Edmonds-Karp; max-flow min-cut; efficiently solvable
variants.

**Ausblick (sl. 67).** A long list of successive improvements — **Dinic's
algorithm** at `O(n²m)`, and others. *(Cf. `Chen et al. 2022`, held locally:
almost-linear time, and the paper that superseded Hopcroft-Karp for bipartite
matching in T09.)*

---

## 9. Exam-critical minimum

| Must be automatic | Where |
|---|---|
| Flow network, flow, the two constraints, `|f|` | sl. 4–7 |
| Why plain greedy fails — no way to undo | sl. 12–13 |
| The residual network, **with backward edges** | sl. 15 |
| The augmentation update `f′` | sl. 18 |
| Ford-Fulkerson terminates with integer capacities; `O(F·m)` **not polynomial** | sl. 21–22 |
| Cut definition and `|f| ≤ c(S,T)` | sl. 25–26 |
| **The three equivalent statements** | sl. 29 |
| The `S` = reachable-from-`s` construction in (2)⇒(3) | sl. 32–33 |
| Edmonds-Karp = BFS; monotone distances; `O(|V|·|A|²)` | sl. 37–45 |
| Each edge critical ≤ `|V|/2` times | sl. 43 |
| Max-flow min-cut, and how to *extract* the min cut | sl. 47, 49 |
| The variant reductions, all four combinations | sl. 52–61 |
| Menger's theorem, both variants | sl. 62–63 |

**Traps:** forgetting backward residual edges (then the algorithm is just the
broken greedy); calling `O(F·m)` polynomial; stating max-flow min-cut without
being able to produce the cut; confusing edge-disjoint with vertex-disjoint in
Menger.
