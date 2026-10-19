---
id: note-algo2-splay-trees
type: note
title: "Algo 2 T05 — Reference: Splay-Bäume"
created: "2026-08-16"
role: reference
state: evolving
authorship: operator-drafted
concepts: [concept-splay-trees, concept-binary-search-trees, concept-amortized-analysis,
  concept-adt-dictionary]
sources: [source-algo2-hu-materials, source-ottmann-widmayer]
contexts: [workspace-algo2-exam-prep]
---

> **Build note (2026-08-16).** Operator-drafted from `ad2_splaytrees.pdf` (52 sl.).
> Companions: `-exercise-bank`, `-viva-drill`. Not yet worked by Aram.

# Algo 2 · Topic 5 — Splay-Bäume

*Lectures: 29. April `[1-18]`, 4. Mai `[19-39]`, 6. Mai `[40-end]` — three
sessions; the middle one is the amortized analysis, which is the hardest proof in
the course.*
***Literatur:** Ottmann/Widmayer Abschnitt 5.4 (6. Aufl. D.). **Leseaufgabe:** O/W
3.3 "Selbstanordnende lineare Listen" — *"Wird manchmal in AlgoDat I behandelt"*,
i.e. **possibly never seen**. **Leseempfehlung:** the first six pages of Sleator &
Tarjan [1985], held locally.*

**Agenda (sl. 2):** Erinnerung ADT Dictionary + BSTs · self-adjusting lists and
trees · how splay trees work · amortized analysis.

> ⚠️ **Requires T02.** And note the book convention (sl. 7): **only inner nodes
> carry keys**; leaves are empty sentinels. Every statement below follows that.

---

## 1. Setup (sl. 4–9)

**ADT Dictionary, simplified (sl. 5):** a dynamic set of ordered, unique **keys**
with `search`, `insert`, `delete`.

**Representation (sl. 7):** following the book — only inner nodes hold keys; each
node has pointers to parent, left and right child.

**Self-adjusting idea (sl. 8–9).** The goal for a BST is fast access. One strategy
is strict balancing (AVL, red-black) with extra balance information. The
alternative: **let the structure adapt to the access pattern.** The book views
trees as a generalization of lists, so the ideas from **self-adjusting lists**
(move-to-front) carry over — instead of moving within a list, you rotate within a
tree.

---

## 2. The splay operation (sl. 11–17)

> **Splay trees** are binary search trees **without any balance information**. The
> central operation is `splay` — *"verbreitern/ausbreiten"*. The searched key `k`
> is moved to the root by rotations, and the depth of every key on the path to
> `k` is roughly **halved**.

`search`, `insert` and `delete` all reduce to `splay`. **Amortized cost of each
operation is `O(log n)`.**

**Rotations (sl. 12):** the usual BST rotations, applied only to inner nodes whose
relevant child is also an inner node.

**`splay(t, k)` (sl. 13).** First search for `k`. Let `p` be the node with key `k`
if present; **otherwise `p` is the inner node reached at the end of the
unsuccessful search.** Then move `p` to the root by repeating one of three steps.
Notation: `φp` is `p`'s parent, `φφp` the grandparent.

| Step | When | What |
|---|---|---|
| **zig** (sl. 14) | `q = φp` is the root | a single left/right rotation — the terminating case |
| **zig-zig** (sl. 15) | `p` and `φp` are **both** left children, or both right | rotate the **grandparent first**, then the parent |
| **zig-zag** (sl. 16) | `p` is a left child and `φp` a right child, or vice versa | two rotations at `p` |

> 🎯 **zig-zig is the whole trick.** Rotating grandparent-first (rather than
> `p` twice, which is move-to-root) is what produces the depth halving. **The
> comparison on sl. 17 makes this explicit:** under both `splay` and
> move-to-root, `p` becomes the new root — but only `splay` also improves the
> depths of the other nodes on the path. Move-to-root has no good amortized bound.

---

## 3. The operations via splay (sl. 18–22)

**search(t, k)** (sl. 18): if the tree is empty, answer no. Otherwise `splay(t,k)`;
if `k` is now at the root, yes, else no.

**insert(t, k)** (sl. 19–20): empty tree → new root. Otherwise `splay(t,k)`; if the
root now holds `k`, nothing to do. Otherwise the root holds the neighbouring key
`k′` and the tree is **split** at the root, with `k` becoming the new root and the
two halves attached as its subtrees.

**delete(t, k)** (sl. 21): `splay(t,k)`; if the root holds `k`, remove it, leaving
subtrees `t_ℓ` and `t_r`. Splay the largest key of `t_ℓ` to its root — it then has
no right child — and hang `t_r` there.

**Observation (sl. 22):** every operation uses `splay(t,k)` (almost always), which
conveniently also *decides membership* as a by-product.

---

## 4. Amortized analysis (sl. 24–47) — *the hard part*

**Why amortized (sl. 24):** splay trees are **not balanced in general**, so a
single `splay` can cost `Ω(n)` in the worst case — e.g. on a path-shaped tree.

**Weights and ranks (sl. 25).** Let `w` assign each key a positive weight; for our
purposes `w(k) = 1` suffices, though the book proves more with general weights.
For a subtree, its **size** is the total weight it contains, and its **rank**
`r(x) = log(size(x))`. The potential is the **sum of the ranks of all nodes**.

**Amortized cost (sl. 26):** `d(q) = c(q) + Φ(D″) − Φ(D′)` — the T02 definition,
unchanged.

> **Lemma (sl. 27–28).** The amortized cost of `splay(t,k)` is at most
> $$3\,(r(t) - r(p)) + 1$$
> where `p` is the node with key `k`, or the inner node at the end of the
> unsuccessful search, and `r(t)` is the rank of the whole tree.

**Proof structure (sl. 29–36).** Show per-step bounds and telescope:

> **Behauptung (sl. 29).** Amortized cost per **zig** at `p` is at most
> `3(r′(p) − r(p)) + 1`; per **zig-zig** and **zig-zag**, at most
> `3(r′(p) − r(p))`.

- **zig (sl. 30):** `q = φp` is the root; direct estimate.
- **A useful auxiliary lemma (sl. 31)** for handling logarithms:
  > If `a, b > 0` and `a + b ≤ c`, then `log a + log b ≤ 2 log c − 2`.
  > *(Proof from `(a−b)² ≥ 0`.)*
- **zig-zag (sl. 32–33):** reach `am_{zig-zag} ≤ 2 + r′(q) + r′(r) − 2r(p)`, then
  apply the auxiliary lemma.
- **zig-zig (sl. 34–35):** reach `am_{zig-zig} ≤ 2 + r′(p) + r′(r) − 2r(p)`, then
  the same technique on the subtree sizes.
- **Wrap-up (sl. 36):** the per-step bounds **telescope** — the `+1` survives only
  from the single terminating zig, giving `3(r(t) − r(p)) + 1`.

**Comment (sl. 37):** only in the **zig-zig** case was the estimate tight — i.e.
zig-zig is what forces the constant 3. That is the structural reason the operation
is defined the way it is.

**What the lemma means (sl. 38–39):** with `w ≡ 1`, `r(t) = log n` and
`r(p) ≥ 0`, so the amortized cost of a splay is `O(log n)`.

> **Theorem (sl. 40, 47).** The amortized costs of `insert`, `delete` and `search`
> are **`O(log n)`** when the tree holds at most `n` keys. Every sequence of `m`
> operations therefore costs `O(m log n)`.

**Sl. 41 asks the right question:** these operations only add constant work around
one or two splays — so what is left to prove? **Answer:** insert and delete
*change the key set*, and therefore change the potential in ways the splay lemma
does not cover. Sl. 42–46 discharge each case separately.

**Further results (sl. 48).** With other weight choices `w ≠ 1`, the same analysis
yields the **static optimality** theorem and related bounds.

---

## 5. Trade-offs, Überblick, Ausblick (sl. 49–52)

**Advantages (sl. 49):** simple structure with **no balance-information
overhead**; the tree shape adapts to the access pattern; amortized `O(log n)`.
**Disadvantages:** no worst-case guarantee per operation; the restructuring
happens even on *reads*, which is awkward for concurrency and for caching.

**Ausblick (sl. 52).** Sleator and Tarjan conjectured splay trees are not only
statically but **dynamically optimal** — within a constant factor of *any* binary
search tree strategy, including one that knows the access sequence in advance.
**Still open.**

---

## 6. Exam-critical minimum

| Must be automatic | Where |
|---|---|
| Splay trees carry **no** balance information | sl. 11 |
| The three steps: zig, zig-zig, zig-zag, and their triggers | sl. 14–16 |
| **zig-zig rotates the grandparent first** | sl. 15 |
| splay vs move-to-root — why MtR is worse | sl. 17 |
| `p` on an *unsuccessful* search is the last inner node | sl. 13 |
| search/insert/delete all reduce to splay | sl. 18–21 |
| A single operation can cost `Ω(n)` | sl. 24 |
| rank `r(x) = log(size(x))`, potential = sum of ranks | sl. 25 |
| The lemma `3(r(t) − r(p)) + 1` | sl. 27 |
| The auxiliary lemma `log a + log b ≤ 2 log c − 2` | sl. 31 |
| Only **zig-zig** is tight — hence the 3 | sl. 37 |
| The theorem `O(log n)` amortized, `O(m log n)` per sequence | sl. 40, 47 |
| Dynamic optimality is **open** | sl. 52 |

**Traps:** calling the bound worst-case; describing zig-zig as "rotate `p` twice"
(that is move-to-root, and it does *not* give the bound); forgetting that splaying
happens on searches too, which is the concurrency drawback; claiming the dynamic
optimality conjecture has been settled.
