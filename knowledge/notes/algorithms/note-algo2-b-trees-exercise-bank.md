---
id: note-algo2-b-trees-exercise-bank
type: note
title: "Algo 2 T03 — Exercise Bank: B-Bäume"
created: "2026-08-16"
role: exercise-bank
state: evolving
authorship: operator-drafted
concepts: [concept-b-trees, concept-adt-dictionary, concept-binary-search-trees]
sources: [source-algo2-hu-materials, source-clrs, source-algo2-frankfurt-klausuren]
contexts: [workspace-algo2-exam-prep]
---

> **Build note (2026-08-16).** Operator-drafted from `ad2_btrees.pdf`. Solutions
> operator-computed, **unverified by Aram**. Deck wins on disagreement.

# Algo 2 · Topic 3 — Exercise Bank

**Scope:** disk-access cost model, the definition with minimal degree `t`, the
height theorem, search/create/split/insert, deletion cases, B⁺ and B*.

> ✍️ **This topic is best learned by drawing.** Every operation is a picture.
> Working the CLRS figures is the deck's own Leseaufgabe (sl. 2) — do it with a
> pen, not by reading.

## 1. Local material

| File | What | Where |
|---|---|---|
| `note-algo2-b-trees` | Reference (§ refs below) | this vault |
| `note-algo2-b-trees-viva-drill` | Oral drill | this vault |
| CLRS Kap. 18 | **Assigned reading + figures** | `material://source-clrs/clrs-de.pdf` |
| Bayer & McCreight 1970 | Leseempfehlung, the original | `material://source-algo2-hu-materials` |
| Frankfurt Klausuren | Solved B-tree items | `material://source-algo2-frankfurt-klausuren` |

## 2. Drills

### A. Definition and height

**A1.** State the B-tree definition with minimal degree `t`.

<details><summary>Solution</summary>

Rooted directed tree; each node `x` has `x.n` sorted keys, a leaf flag, and
`x.n+1` children if internal; keys separate the subtrees; every non-root node has
between `t−1` and `2t−1` keys (so `t` to `2t` children); the root has ≥ 1 key if
non-empty; **all leaves at the same depth**. Full = `2t−1` keys. *(Ref §3.)*
</details>

**A2.** State and prove the height theorem.

<details><summary>Solution</summary>

`h ≤ log_t((n+1)/2)`. Proof: the root forces ≥ 1 key and ≥ 2 children; every
node below has ≥ `t` children, so level `i ≥ 1` has ≥ `2t^{i−1}` nodes, each with
≥ `t−1` keys. Summing, `n ≥ 1 + (t−1)Σ_{i=1}^{h} 2t^{i−1} = 2t^h − 1`. Rearranging
gives the bound. *(Ref §4, sl. 16–17.)*
</details>

**A3. [open]** For `t = 100` and `n = 10⁹`, bound `h`. How many disk accesses does
a search cost? Compare with a balanced BST on the same data. *(Ref §4 — this
computation is the entire economic argument for B-trees.)*

**A4. [open]** Why must all leaves be at the same depth? What breaks otherwise?

**A5. [open]** Why is the minimal degree `t ≥ 2` and not `t ≥ 1`?

### B. Operations

**B1.** Give the disk-access and CPU cost of `B-Tree-Search`.

<details><summary>Solution</summary>

Visited nodes form a downward path, so **≤ `h` disk accesses** = `O(log_t n)`.
Within each node the deck uses **linear** search over ≤ `2t−1` keys, so CPU
`O(t·h) = O(t log_t n)`. *(Ref §5, sl. 22.)*
</details>

**B2.** Describe `B-Tree-Split-Child(x, i)` precisely.

<details><summary>Solution</summary>

Precondition: `x` not full, `y = x.cᵢ` full, both in memory. Allocate `z`; move
`y`'s **upper `t−1` keys** into `z` (`z.n = t−1`), and children too if `y` is
internal; set `y.n = t−1`; the **median key `y.key_t` moves up into `x`**; `z`
becomes a child of `x`. *(Ref §5, sl. 26.)*
</details>

**B3.** Why does insertion split full nodes on the way *down*?

<details><summary>Solution</summary>

So that whenever a node must be split, its parent is guaranteed non-full and can
absorb the median key. This makes insertion a **single downward pass** with no
upward propagation. *(Ref §5, sl. 28.)*
</details>

**B4.** How does a B-tree grow in height?

<details><summary>Solution</summary>

Only at the **root**: when the root is full, a new empty root `s` is created whose
sole child is the old root, which is then split. Height increases by one, and all
leaves stay at equal depth — which is exactly why growth must happen at the top.
*(Ref §5, sl. 29.)*
</details>

**B5. [open]** Insert `1..20` one at a time into an initially empty B-tree with
`t = 2`. Draw every split. State the final height. *(Ref §5.)*

**B6. [open]** The deck asks (sl. 32) whether array storage inside a node could be
improved, given the shifting cost. Answer it: what would you use, and what would
it cost you?

### C. Deletion

**C1.** State the invariant deletion maintains and say why.

<details><summary>Solution</summary>

Every node entered by a recursive call has **at least `t` keys** — one above the
minimum `t−1`. This guarantees a key can be removed from it without violating the
lower bound, which is why the descent repairs a child *before* entering it.
*(Ref §6, sl. 35, 37.)*
</details>

**C2.** Enumerate the deletion cases.

<details><summary>Solution</summary>

**1** leaf containing `k` → delete directly. **2** internal node containing `k`:
**2a** preceding child has ≥ `t` keys → replace with predecessor, recurse;
**2b** symmetric with successor; **2c** both children minimal → merge `y`, `k`, `z`
and recurse. **3** internal node not containing `k` → repair the child (borrow
from a sibling, or merge) then descend. *(Ref §6, sl. 37–40.)*
</details>

**C3. [open]** Take your `t = 2` tree from B5 and delete `9`, `13`, `1` in that
order. Name which case fires each time. *(Ref §6.)*

**C4. [open]** Construct a deletion that triggers case 2c and reduces the tree's
height. Which case is the only one that can shrink the height?

### D. Boundaries and variants

**D1.** B⁺ vs B* trees?

<details><summary>Solution</summary>

**B⁺:** all data in the leaves, internal nodes act purely as an index (and leaves
are usually linked for range scans). **B*:** higher minimum fill factor per node.
*(Ref §7, sl. 44.)*
</details>

**D2. [open]** Why are B-trees called "hardware-oriented"? What does the deck say
this costs? *(Ref §7, sl. 44.)*

**D3. [open]** Contrast with splay trees (T05): both are dictionaries, but one
optimizes disk accesses and the other amortized comparisons. When would you pick
each?

## 3. External practice — scope filter

| Source | Take | Avoid |
|---|---|---|
| CLRS Kap. 18 | **Assigned**; work the figures | — |
| Bayer & McCreight 1970 | Leseempfehlung, historical framing | its implementation minutiae |
| Ottmann/Widmayer | German alternative vocabulary | its broader index-structure survey |
| Frankfurt Klausuren | B-tree items as explain-aloud drill | written-format framing |

**Filter:** in scope are the definition, height, search, split, one-pass insert,
the deletion cases, and B⁺/B* **by name**. Out: concurrency and locking, LSM-trees,
fractal trees, and cache-oblivious structures — External Memory Algorithms is
named as an *Ausblick*, not taught.
