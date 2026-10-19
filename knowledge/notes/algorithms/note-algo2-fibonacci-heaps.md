---
id: note-algo2-fibonacci-heaps
type: note
title: "Algo 2 T04 — Reference: Fibonacci-Heaps"
created: "2026-08-16"
role: reference
state: evolving
authorship: operator-drafted
concepts: [concept-fibonacci-heaps, concept-adt-priority-queue, concept-amortized-analysis]
sources: [source-algo2-hu-materials, source-clrs]
contexts: [workspace-algo2-exam-prep]
---

> **Build note (2026-08-16).** Operator-drafted from `ad2_fibonacciheap.pdf`
> (57 sl.). Companions: `-exercise-bank`, `-viva-drill`. Not yet worked by Aram.

# Algo 2 · Topic 4 — Fibonacci-Heaps

*Lectures: 22. April `[1-13]`, 27. April `[14-44]`, 29. April `[45-end]` — three
sessions, the third being the degree bound alone.*
***Literatur:** CLRS Kap. 19. **Leseaufgabe:** reread Kap. 19 afterwards and work
the figures.*

**Agenda (sl. 2):** Erinnerung ADT Priority Queue + heaps · core design ideas ·
structure and representation · the operations · **amortized analysis via the
potential method** · an upper bound on the maximum degree.

> ⚠️ **Requires T02 (amortized analysis) completely.** The headline bounds are
> amortized, and the whole lecture is an extended application of the potential
> method. Do not start this before T02 is solid.

---

## 1. Prerequisite recalled (sl. 4–6) — Phase 0.4

**ADT Priority Queue:** dynamic set of items with ordered keys; operations
`insert`, `min`, `extractmin`, `decreasekey`, `delete`, `union`.

**Heap idea (sl. 5):** maintain one or more trees in which children have keys at
least as large as their parent — **min-heap-ordered**.

> **The table that motivates everything (sl. 6):**
>
> | | insert | min | extr-min | decr-key | delete | union |
> |---|---|---|---|---|---|---|
> | **Binär** | O(log n) | O(1) | O(log n) | O(log n) | O(log n) | **O(n)** |
> | **Binomial** | O(log n) | O(log n) | O(log n) | O(log n) | O(log n) | O(log n) |
> | **Fibo. (worst)** | O(1) | O(1) | O(n) | O(n) | O(n) | O(1) |
> | **Fibo. (amort.)** | **O(1)** | **O(1)** | O(log n) | **O(1)** | O(log n) | **O(1)** |
>
> **Note the worst-case row.** Individual Fibonacci operations can be `O(n)`.
> The improvement is *amortized only* — stating this unprompted is the single
> best signal you understand the topic.

**Payoff:** clear advantages for algorithms that call `decreasekey` often — hence
often a component of Dijkstra and Prim.

---

## 2. Core design ideas (sl. 8–10)

**Question (sl. 8):** every operation that does not remove an element runs in
amortized `O(1)`. How?

- Like binomial heaps, but with a **less restrictive structure** — work is
  deferred ("lazy") and cleaned up only during `extractmin`.
- The root list is an unsorted collection of trees; nothing is consolidated until
  it must be.

**The `decreasekey` problem (sl. 9–10).** `decreasekey(S,x,k)` lowers `x`'s key
and must restore min-heap order if `x`'s parent now has a larger key. In binomial
trees you would bubble `x` upward — but then `m` calls cost
`Ω(m·h) = Ω(m log n)`.

> **The answer: don't bubble — cut.** Separate `x` (with its subtree) from its
> parent and move it into the root list. That is `O(1)`, but it damages the
> tree-shape guarantee — which is what the **marking** scheme repairs.

---

## 3. Structure and representation (sl. 12–17)

**Informally (sl. 12):** a Fibonacci heap is a **set of directed, unordered,
min-heap-ordered trees**, one key per node.

**Root list (sl. 13):** the roots of all trees in a **doubly linked list**;
`min[H]` points to the root with the smallest key. Children of a node are
likewise in a doubly linked list. Each node stores `key`, `data`, `p` (parent),
`kind` (a child), `grad` (number of children), `marke`.

**Marking (sl. 14) — the mechanism that makes the analysis work:**

- nodes in the root list are **always unmarked**;
- newly created nodes are unmarked and go into the root list;
- a node is marked **when it loses its first child** (since becoming a child
  itself);
- if a marked node loses a **second** child, it is itself cut and moved to the
  root list — a **cascading cut** — and unmarked there.

**Maximum degree (sl. 15):** `D(n)` denotes the maximum node degree; the deck
assumes `D(n) = O(log n)` for now and proves it in §6.

> **Potential function (sl. 16):**
> $$\Phi(H) = t(H) + 2\,m(H)$$
> where `t(H)` = number of trees in the root list, `m(H)` = number of marked nodes.

**Intuition (sl. 17).** `t(H)`: adding trees to the root list increases the later
cost of consolidating it, so pay for that now. `m(H)`: each mark is a warning that
a future cut is owed — and the factor **2** covers both the cut of the marked node
*and* the mark it will place on its own parent.

---

## 4. The cheap operations (sl. 19–25)

**insert (sl. 20–21).** Set `p[x] = nil`, `kind[x] = nil`, `grad[x] = 0`,
`marke[x] = false`; splice into the root list; update `min[H]` if smaller.
Actual `O(1)`; `t` grows by 1, `m` unchanged, so `ΔΦ = +1`; **amortized `O(1)`**.

**min (sl. 22).** `min[H]` always points at the smallest root: **`O(1)`**, no
potential change.

**union (sl. 23–24).** Concatenate the two root lists; `min[H]` is the smaller of
the two minima. Actual `O(1)`. Since `t(H) = t(H₁) + t(H₂)` and the marked count
adds too, `ΔΦ = 0` — **amortized `O(1)`**.

> **Summary (sl. 25):** `insert`, `min`, `union` all have *actual* cost `O(1)`;
> only `insert` raises the potential (by 1). **No consolidation happens here** —
> that laziness is the design.

---

## 5. extractmin, consolidate, decreasekey, delete (sl. 27–42)

### extractmin (sl. 27–33)

Remove `x = min[H]` and output it; its **children are not removed** — they are
spliced into the root list. Then **consolidate**.

**Consolidation (sl. 28–31).** Goal: combine trees so that only `O(log n)` remain
— which both lowers the potential and keeps future work bounded. Use an array
`A[0..D(n)]` where `A[d]` points to a root of degree `d`:

```
1  for i ∈ {0,…,D(n[H])} do A[i] ← nil
2  for each node w in the root list do
3      x ← w;  d ← grad[x]
4      while A[d] ≠ nil do
5          combine x with A[d]  (larger key becomes the child)
6          A[d] ← nil;  d ← d + 1
7      A[d] ← x
```

Two roots of equal degree are linked: the one with the **larger key becomes a
child** of the other, raising the winner's degree by one.

**Costs (sl. 32–33).** Actual: `O(D(n))` to move the children out, plus
`O(t(H) + D(n))` to consolidate → `O(t(H) + log n)`. Potential change:
`D(n) + 1 − t(H)`. Sum → **amortized `O(log n)`**.

### decreasekey (sl. 35–41) — *the star of the lecture*

If `k < key[x]`, set `key[x] ← k`. **Done** if `x` is a root, or if the parent's
key is still ≤ `key[x]`.

Otherwise: **cut** `x` from its parent `y`, move `x` with its subtree into the
root list, set `marke[x] ← false`. Then examine `y`:

- if `y` is a root, stop;
- if `y` is unmarked, mark it and stop;
- if `y` is already marked, **cut `y` too and repeat upward** — the cascading cut.

**Costs (sl. 38–40).** Actual: `O(1)` for `x`, plus the cost of `d` further cut
nodes → at most `β·d + O(1)`. Potential change: each cut adds a tree (`+1`) but
removes a mark (`−2`), giving at most `−d + O(1)`. Summing:
**amortized `O(1)`** — the `d` terms cancel exactly.

> 🎯 **This cancellation is the most elegant argument in the course.** The
> potential was designed with the factor 2 precisely so the cascade pays for
> itself. If you can narrate that, you have the topic.

### delete (sl. 42)

`delete(H,x)` = `decreasekey(H,x,−∞)` then `extractmin(H)`, assuming no other key
is `−∞`. Amortized `O(log n)`.

---

## 6. Bounding the maximum degree (sl. 44–54)

**The plan (sl. 45):** (1) show a node of high degree has children of high
degree; (2) recall Fibonacci numbers and their exponential growth; (3) conclude.

> **Lemma (sl. 46).** Let `x` have `grad[x] = k`, with children `y₁,…,y_k` in the
> order they were linked to `x` (`y₁` first). Then `grad[y₁] ≥ 0` and
> `grad[yᵢ] ≥ i − 2` for `i ≥ 2`.

**Why (sl. 47–48).** When `yᵢ` was linked, `x` already had ≥ `i−1` children, so
`yᵢ` had degree ≥ `i−1` at that moment (equal degrees are linked). Since then
`yᵢ` can have lost **at most one** child — a second loss would have cut it away
from `x` entirely. Hence `grad[yᵢ] ≥ i−2`.

**Fibonacci numbers (sl. 49–51).** `F₀ = 0`, `F₁ = 1`, `F_k = F_{k−1} + F_{k−2}`.
Closed form `F_k = Θ(φ^k)` with `φ = (1+√5)/2`. The needed facts:
`F_{k+2} ≥ φ^k`, and

> **Lemma (sl. 51).** `F_{k+2} = 1 + Σ_{i=0}^{k} Fᵢ`. *(Übung: prove by
> induction.)*

> **Lemma (sl. 52–53).** With `size(x)` the number of nodes in `x`'s subtree and
> `k = grad[x]`:
> $$\text{size}(x) \ge F_{k+2} \ge \varphi^k$$
> Proved by induction on the minimal subtree size `s_k` for degree `k`.

> **Folgerung (sl. 54).** The maximum node degree in a Fibonacci heap with `n`
> nodes is **`D(n) = O(log n)`** — because `n ≥ size(x) ≥ φ^k` gives
> `k ≤ log_φ n`.

**This closes the loop:** §5 assumed `D(n) = O(log n)` to get `extractmin` at
`O(log n)`, and §6 earns it.

---

## 7. Überblick and Ausblick (sl. 56–57)

**Überblick.** Related to binomial heaps but less restrictive. Amortized:
`insert`, `min`, `union`, `decreasekey` in `O(1)`; `extractmin` and `delete` in
`O(log n)`.

**Ausblick.** Many other priority-queue realizations exist — e.g. **Pairing
Heaps**, a simplification of Fibonacci heaps with similar amortized bounds but
easier to implement.

---

## 8. Exam-critical minimum

| Must be automatic | Where |
|---|---|
| The sl. 6 table, **including the worst-case row** | sl. 6 |
| Why bubbling up fails for `decreasekey` | sl. 10 |
| Structure: unordered min-heap-ordered trees, root list | sl. 12–13 |
| The four marking rules | sl. 14 |
| **`Φ(H) = t(H) + 2m(H)`** and the intuition for each term | sl. 16–17 |
| `insert`/`min`/`union` amortized `O(1)` with `ΔΦ` | sl. 21–25 |
| Consolidation via `A[0..D(n)]` | sl. 29–30 |
| `extractmin` amortized `O(log n)` | sl. 32–33 |
| Cut + cascading cut, and the `−d` cancellation | sl. 37–40 |
| `delete` = `decreasekey(−∞)` + `extractmin` | sl. 42 |
| `grad[yᵢ] ≥ i−2` | sl. 46 |
| `size(x) ≥ F_{k+2} ≥ φ^k` ⟹ `D(n) = O(log n)` | sl. 53–54 |

**Traps:** calling the bounds worst-case; forgetting the factor **2** on `m(H)`
(then `decreasekey` does not come out `O(1)`); saying roots can be marked (they
cannot); forgetting that the *second* child loss triggers the cut, not the first;
being unable to say where the name "Fibonacci" comes from — it is the degree
bound of §6, not the structure.
