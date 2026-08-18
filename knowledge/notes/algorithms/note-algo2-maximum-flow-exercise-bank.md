---
id: note-algo2-maximum-flow-exercise-bank
type: note
title: "Algo 2 T08 — Exercise Bank: Maximaler Fluss"
created: "2026-08-16"
role: exercise-bank
state: evolving
authorship: operator-drafted
concepts: [concept-max-flow, concept-graph-basics]
sources: [source-algo2-hu-materials, source-clrs, source-algo2-frankfurt-klausuren]
contexts: [workspace-algo2-exam-prep]
---

> **Build note (2026-08-16).** Operator-drafted from `ad2_maximumflow.pdf`.
> Solutions operator-computed, **unverified by Aram**. Deck wins on disagreement.

# Algo 2 · Topic 8 — Exercise Bank

**Scope:** flow networks, residual networks, Ford-Fulkerson, Edmonds-Karp, cuts
and the three equivalences, max-flow min-cut, the variant reductions, Menger.

> 🔗 **Feeds T09.** Bipartite matching's own Übung is "find matchings via maximum
> flow." Do this topic first.

## 1. Local material

| File | What | Where |
|---|---|---|
| `note-algo2-maximum-flow` | Reference (§ refs below) | this vault |
| `note-algo2-maximum-flow-viva-drill` | Oral drill | this vault |
| CLRS 26.1–26.2 | **Assigned** — notation differs slightly from the deck | `material://source-clrs/clrs-de.pdf` |
| Chen et al. 2022 | Ausblick — almost-linear max flow | `material://source-algo2-hu-materials` |

## 2. Drills

### A. Definitions

**A1.** Define flow network, flow, and `|f|`.

<details><summary>Solution</summary>

`N = (G,c,s,t)` with `c : A → ℝ⁺`. A flow `f : A → ℝ≥0` satisfies the **capacity
constraint** `f(a) ≤ c(a)` and **flow conservation** at every `v ∉ {s,t}`.
`|f| = Σ_{δ⁺(s)} f(a) − Σ_{δ⁻(s)} f(a)`. *(Ref §1.)*
</details>

**A2.** Define the residual network and say what the backward edges are *for*.

<details><summary>Solution</summary>

For `a = (u,v)`: a forward edge `(u,v)` with capacity `c(a) − f(a)` if positive,
and a **backward** edge `(v,u)` with capacity `f(a)` if positive. Backward edges
let the algorithm **retract** flow sent earlier — which is exactly what the naive
greedy could not do. *(Ref §3, sl. 15; §2, sl. 12–13.)*
</details>

**A3. [open]** Build a 4-vertex network where naive greedy on arbitrary paths gets
stuck below the maximum, and show how a backward edge fixes it. *(The canonical
example — have it memorized for the viva.)*

### B. The algorithms

**B1.** Write the augmentation update `f′`.

<details><summary>Solution</summary>

With `x = min_{a ∈ P} c_f(a)`: `f′(a) = f(a) + x` if the forward copy of `a` is on
`P`; `f(a) − x` if the backward copy is; `f(a)` otherwise. *(Ref §3, sl. 18.)*
</details>

**B2.** Give Ford-Fulkerson's termination and runtime, with the caveat.

<details><summary>Solution</summary>

With **integer** capacities each augmentation raises `|f|` by ≥ 1, so it
terminates in ≤ `F` iterations → `O(F·m)`. **Not polynomial in the input size**
(`F` can be exponential in the bit length), and with irrational capacities it need
not terminate. *(Ref §3, sl. 21–22.)*
</details>

**B3.** What does Edmonds-Karp change, and what does that buy?

<details><summary>Solution</summary>

Always augment along a **shortest** residual `s,t`-path (BFS). Then residual
distances increase monotonically, the number of iterations is `O(|V|·|A|)`, and
the total runtime is **`O(|V|·|A|²)` — polynomial and independent of the
capacities.** *(Ref §5.)*
</details>

**B4.** Why is each edge critical at most `|V|/2` times?

<details><summary>Solution</summary>

When `(u,v)` is critical it lies on a shortest augmenting path, so
`δ_f(s,v) = δ_f(s,u) + 1`. To become critical again, flow on it must first be
reduced, requiring `(v,u)` on a later augmenting path, at which point
`δ(s,u) = δ(s,v) + 1`. By monotonicity `δ(s,u)` has increased by ≥ 2. Distances
are bounded by `|V|`, hence ≤ `|V|/2` occurrences. *(Ref §5, sl. 43.)*
</details>

**B5. [open]** Run Edmonds-Karp on a 6-vertex network by hand; record the residual
network after each augmentation.

**B6. [open]** Construct an instance where Ford-Fulkerson with badly chosen paths
takes `Θ(F)` iterations while Edmonds-Karp takes a handful. *(The classic
"two big edges and one unit middle edge" family.)*

### C. Cuts and duality

**C1.** Prove `|f| ≤ c(S,T)` for every flow and cut.

<details><summary>Solution</summary>

Add the conservation terms (each zero) for every `v ∈ S \ {s}` to the definition
of `|f|`. All edges internal to `S` appear once positively and once negatively and
cancel, leaving the net flow across `δ⁺(S)` minus `δ⁻(S)`, which is at most
`Σ_{δ⁺(S)} c(a) = c(S,T)`. *(Ref §4, sl. 26–27.)*
</details>

**C2.** State the three equivalent conditions and prove (2)⇒(3).

<details><summary>Solution</summary>

(1) `f` maximum ⟺ (2) no `s,t`-path in `N_f` ⟺ (3) some cut has `|f| = c(S,T)`.
For (2)⇒(3): let `S` = vertices reachable from `s` in `G_f`. Since there is no
`s,t`-path, `t ∉ S`. For `a ∈ δ⁺(S)` we must have `f(a) = c(a)` — otherwise a
forward residual edge would leave `S`. For `a ∈ δ⁻(S)` we must have `f(a) = 0` —
otherwise a backward residual edge would. Hence `|f| = c(S,T)`. *(Ref §4,
sl. 29–33.)*
</details>

**C3.** State max-flow min-cut and give the algorithm for a minimum cut.

<details><summary>Solution</summary>

Max flow value = min cut capacity. Algorithm: compute a max flow with
Edmonds-Karp, build `N_f`, take `S` = vertices reachable from `s` in `G_f`; then
`(S, V\S)` is a minimum cut. *(Ref §6, sl. 47, 49.)*
</details>

**C4. [open]** Why is max-flow min-cut an instance of *duality*? Identify which
direction is easy (weak) and which is the real content (strong).

### D. Variants

**D1.** How do you find a maximum set of edge-disjoint `s,t`-paths?

<details><summary>Solution</summary>

Set all capacities to 1, compute a max flow, and trace `k = |f|` unit paths from
`s`. They are edge-disjoint because each edge carries at most one unit.
*(Ref §7, sl. 52–54.)*
</details>

**D2.** Give both reductions: undirected graphs, and vertex capacities.

<details><summary>Solution</summary>

**Undirected:** replace `{u,v}` by `(u,v)` and `(v,u)`, each with the original
capacity. **Vertex capacities:** split each `v ∉ {s,t}` into `v⁻ → v⁺` with an
edge of capacity `c(v)`; incoming edges arrive at `v⁻`, outgoing leave `v⁺`.
*(Ref §7, sl. 55–60.)*
</details>

**D3.** State both forms of Menger's theorem.

<details><summary>Solution</summary>

**Vertex version:** for non-adjacent `s,t`, the maximum number of vertex-disjoint
`s,t`-paths equals the minimum size of an `s,t`-separator. **Edge version:** for
any `s,t` (possibly adjacent), the maximum number of edge-disjoint `s,t`-paths
equals the minimum edge cut. *(Ref §7, sl. 62–63.)*
</details>

**D4. [open]** Sl. 61 claims all four combinations (vertex/edge capacities ×
directed/undirected) reduce to the base problem. Compose the two reductions to
handle **undirected graphs with vertex capacities** and check the composition is
valid.

### E. Cross-wires

**E1. [open]** How is bipartite matching solved via max flow? Build the network.
*(Ref T09's own Übung.)*

**E2. [open]** Compare the role of BFS in Edmonds-Karp with its role in Dijkstra
(T07). Why does Edmonds-Karp need *shortest* paths at all?

## 3. External practice — scope filter

| Source | Take | Avoid |
|---|---|---|
| CLRS 26.1–26.2 | **Assigned**; note the notation and ordering differ | 26.3+ (matching there) unless doing T09 |
| Frankfurt Klausuren | Flow items as explain-aloud drill | written framing |

**Filter:** in scope are flows, residual networks, FF, EK, cuts, max-flow min-cut,
the four variant reductions, and Menger. **Dinic and the almost-linear algorithms
are Ausblick only** (sl. 67) — know that they exist and roughly their bounds; do
not study push-relabel, blocking flows, or min-cost flow.
