---
id: note-algo2-b-trees
type: note
title: "Algo 2 T03 — Reference: B-Bäume"
created: "2026-08-16"
role: reference
state: evolving
authorship: operator-drafted
concepts: [concept-b-trees, concept-adt-dictionary, concept-binary-search-trees]
sources: [source-algo2-hu-materials, source-clrs]
contexts: [workspace-algo2-exam-prep]
---

> **Build note (2026-08-16).** Operator-drafted from `ad2_btrees.pdf` (44 sl.).
> Companions: `-exercise-bank`, `-viva-drill`. Not yet worked by Aram.

# Algo 2 · Topic 3 — B-Bäume

*Lectures: 15. April `[1-32]`, 20. April `[33-end]` — **the split falls exactly
at the deletion section**, which is the deck's own hardest part.*
***Literatur:** CLRS Kap. 18 (4. Aufl. D.) — Leseaufgabe: read the chapter
independently and work through the figures. **Leseempfehlung:** Bayer &
McCreight [1970], held locally.*

**Agenda (sl. 2):** Erinnerung ADT Dictionary + BSTs · primary vs secondary
storage · definition · operations · what are B⁺/B*-trees.

---

## 1. Prerequisites recalled (sl. 4–5) — Phase 0.3

**ADT Dictionary:** manage a dynamic set `S` of items (key + data); keys come
from an ordered set. **BST:** one key per node, ≤ 2 children, search-tree
property (left subtree smaller, right larger), search in `O(h)` with `h` the
height.

---

## 2. Primary vs secondary storage (sl. 7–10) — *the motivation*

With large data (databases), the structure lives mostly on **secondary storage**
(SSD/HDD). **Accesses to secondary storage are orders of magnitude more expensive
than to main memory.**

A BST on disk: most operations traverse a root-to-leaf path of height
`h ≈ c log n`, and **each step is a disk access**.

> **The B-tree answer:** store as many keys as possible in one node, so that one
> disk access retrieves a whole page. Fewer, fatter nodes ⟹ smaller height ⟹
> fewer disk accesses.

**Pseudocode convention (sl. 10):** `disk-read(x)` and `disk-write(x)` are
written explicitly; if `x` is already in main memory they are free. Counting these
calls *is* the cost model.

---

## 3. Definition (sl. 13–15)

> **Definition.** A B-tree `T` with **minimal degree `t ≥ 2`** is a rooted
> directed tree where:
>
> 1. every node `x` has attributes `x.n` (number of keys), the keys
>    `x.key₁ ≤ … ≤ x.key_{x.n}` in ascending order, `x.blatt` (leaf flag), and —
>    if internal — `x.n + 1` child pointers `x.c₁ … x.c_{x.n+1}`;
> 2. the keys separate the subtrees: all keys in the subtree at `x.cᵢ` lie
>    between `x.key_{i−1}` and `x.keyᵢ`;
> 3. **degree bounds:** every node other than the root holds at least `t − 1` and
>    at most `2t − 1` keys (so between `t` and `2t` children); the root holds at
>    least one key if the tree is non-empty;
> 4. **all leaves have the same depth `h`.**

A node with `2t − 1` keys is **full**.

**Simplification (sl. 12):** the deck works with sets of *keys*, not items; data
(or pointers to it) moves implicitly with the keys.

**Note (sl. 15):** requiring the root to hold ≥ 1 key when non-empty rules out a
degenerate root with no key but children.

---

## 4. Height (sl. 16–17) — *the theorem to know cold*

> **Theorem.** For every B-tree `T` with `n ≥ 1` keys, height `h`, and minimal
> degree `t ≥ 2`:
> $$h \le \log_t \frac{n+1}{2}$$

**Proof sketch (sl. 17).** For `h = 0` it is immediate. Otherwise the root has
≥ 1 key and ≥ 2 children; every node at depth 1 has ≥ `t` children, at depth 2 at
least `t²`, and so on. Counting the minimum number of keys forced at each level
gives `n ≥ 2t^h − 1`, and rearranging yields the bound.

> 🎯 **Why this is the point of the whole lecture.** The height directly bounds
> the number of disk accesses. The base is `t`, not 2 — that is the entire gain,
> and `t` is chosen to match the page size.

---

## 5. Search, create, insert (sl. 19–32)

**B-Tree-Search(x, k)** (sl. 21) — like BST search, but the key must be compared
against up to `x.n` keys within a node (the deck uses **linear** search):

```
1  i = 1
2  while i ≤ x.n and k > x.keyᵢ do i = i + 1
3  if i ≤ x.n and k == x.keyᵢ then return (x, i)
4  else if x.blatt then return nil
5  else disk-read(x.cᵢ); return B-Tree-Search(x.cᵢ, k)
```

**Cost (sl. 22):** the visited nodes form a downward path, so **at most `h` disk
accesses**, i.e. `O(log_t n)`; CPU cost `O(t·h) = O(t log_t n)`.

**B-Tree-Create** (sl. 23): allocate a node, `blatt = true`, `n = 0`,
`disk-write`, make it the root.

**B-Tree-Split-Child(x, i)** (sl. 25–27). Input: a **non-full** node `x` and an
index `i` such that `x.cᵢ` is **full**; both are in main memory.

- `y = x.cᵢ`; allocate `z` as the **right half** of `y`, with `z.n = t − 1`;
- move keys `y.key_{j+t}` for `j = 1..t−1` into `z` (and children if `y` is not a
  leaf);
- `y.n = t − 1`;
- the **median key `y.key_t` moves up into `x`**, and `z` becomes a new child of
  `x`.

**B-Tree-Insert (sl. 28–31) — one downward pass.** The key idea: **split every
full node encountered on the way down**, so you are always in the situation that
the parent of the node you descend into is not full. Consequence: no upward pass
is ever needed.

Special case (sl. 29): if the **root** is full, allocate a new root `s` with no
keys whose only child is the old root, then split. **This is the only way a
B-tree grows in height** — from the top.

`B-Tree-Insert-Nonfull(x, k)` (sl. 30): in a leaf, shift keys and insert; else
find the correct child, split it if full, and recurse.

**Frage (sl. 32, possibly Übung):** keys are stored as arrays, so insertion and
deletion inside a node cost shifting. Could that be done better?

---

## 6. Deletion (sl. 34–41) — *the complicated one*

> **"Die komplizierteste der Operationen."** Unlike insertion, deletion can
> target *any* node, giving many situations.

**Invariant maintained throughout:** on every recursive call, the current node
`x` has **at least `t` keys** — one more than the minimum. This is what
guarantees a key can be removed without immediately violating the lower bound,
and it is why the descent must fix nodes *before* entering them.

**Root special case (sl. 36):** if the root is the only node (a leaf), delete
directly.

**The cases:**

- **Fall 1 (sl. 37) — leaf reached.** `x` is a non-root leaf containing `k`:
  delete it. Simplest case.
- **Fall 2 (sl. 38–39) — internal node `x` containing `k`:**
  - **2a.** the child `y` preceding `k` has ≥ `t` keys → replace `k` by its
    **predecessor** from `y`, recurse to delete that;
  - **2b.** symmetric with the following child `z` and the **successor**;
  - **2c.** both `y` and `z` have exactly `t − 1` keys → **merge** `y`, `k` and
    `z` into one node and recurse into it.
- **Fall 3 (sl. 40) — internal node `x` not containing `k`.** Determine
  `y = x.cᵢ`, the root of the subtree that must contain `k`. If `y` has only
  `t − 1` keys, first **borrow** a key from a sibling (rotating through the
  parent) or **merge** with a sibling — restoring the invariant — then descend.

**Comments (sl. 41):** most keys live in leaves, so in practice the easiest case
dominates, and a single downward pass suffices.

---

## 7. Überblick and Ausblick (sl. 43–44)

**Überblick.** B-trees generalize balanced BSTs by allowing more than one key per
node; this exploits large storage pages in secondary memory and gives low height
`log_t`.

**Ausblick.** B-trees exemplify methods oriented toward **real hardware** (at the
cost of complexity). The field is **External Memory Algorithms**. **B⁺-trees**
keep all data in the leaves with internal nodes as an index; **B*-trees** raise
the minimum fill factor.

---

## 8. Exam-critical minimum

| Must be automatic | Where |
|---|---|
| Why disk accesses, not comparisons, are the cost | sl. 7–8 |
| Definition with `t`, `t−1 … 2t−1` keys, equal leaf depth | sl. 13–14 |
| `h ≤ log_t((n+1)/2)` **and its proof sketch** | sl. 16–17 |
| Search = ≤ `h` disk accesses | sl. 22 |
| Split: median moves up, `z` is the right half, `z.n = t−1` | sl. 26 |
| Insert splits **on the way down**, one pass | sl. 28 |
| The tree grows **at the root** | sl. 29 |
| Delete: the ≥ `t` keys invariant, and cases 1 / 2a-b-c / 3 | sl. 35–40 |
| B⁺ vs B* | sl. 44 |

**Traps:** giving the height bound with base 2; saying insertion splits on the way
*up* (that is the naive version the one-pass design avoids); forgetting the
invariant is `t`, not `t−1`, and therefore missing why case 3 fixes the child
*before* descending; claiming B-trees are binary.
