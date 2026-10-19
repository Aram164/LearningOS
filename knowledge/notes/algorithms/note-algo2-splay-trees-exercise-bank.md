---
id: note-algo2-splay-trees-exercise-bank
type: note
title: "Algo 2 T05 — Exercise Bank: Splay-Bäume"
created: "2026-08-16"
role: exercise-bank
state: evolving
authorship: operator-drafted
concepts: [concept-splay-trees, concept-binary-search-trees, concept-amortized-analysis]
sources: [source-algo2-hu-materials, source-ottmann-widmayer, source-algo2-frankfurt-klausuren]
contexts: [workspace-algo2-exam-prep]
---

> **Build note (2026-08-16).** Operator-drafted from `ad2_splaytrees.pdf`.
> Solutions operator-computed, **unverified by Aram**. Deck wins on disagreement.

# Algo 2 · Topic 5 — Exercise Bank

**Scope:** self-adjusting structures, the splay operation and its three steps,
implementing search/insert/delete via splay, ranks and the potential, the splay
lemma and its proof, the `O(log n)` theorem, trade-offs, dynamic optimality.

> ✍️ **Draw the rotations.** zig-zig vs zig-zag is a *picture* difference; people
> who learn it verbally reliably get the grandparent order wrong under pressure.

## 1. Local material

| File | What | Where |
|---|---|---|
| `note-algo2-splay-trees` | Reference (§ refs below) | this vault |
| `note-algo2-splay-trees-viva-drill` | Oral drill | this vault |
| `note-algo2-amortized-analysis` | The method applied here | this vault |
| Ottmann/Widmayer 5.4 | **Assigned reading** | `material://source-ottmann-widmayer/ow.pdf` |
| Ottmann/Widmayer 3.3 | **Leseaufgabe** — self-adjusting lists | same |
| Sleator & Tarjan 1985 | Leseempfehlung, first six pages | `material://source-algo2-hu-materials` |

## 2. Drills

### A. The operation

**A1.** Name the three splay steps and their triggers.

<details><summary>Solution</summary>

**zig**: parent is the root — single rotation, terminating case. **zig-zig**: `p`
and `φp` are both left children or both right — rotate the **grandparent first**,
then the parent. **zig-zag**: `p` is a left child and `φp` a right child (or vice
versa) — two rotations at `p`. *(Ref §2, sl. 14–16.)*
</details>

**A2.** What is `p` when the search for `k` fails?

<details><summary>Solution</summary>

The **inner node reached at the end of the unsuccessful search** — splaying still
happens, which is what makes membership testing a by-product. *(Ref §2, sl. 13.)*
</details>

**A3.** How does splay differ from move-to-root, and why does it matter?

<details><summary>Solution</summary>

Both put `p` at the root. But move-to-root rotates `p` upward twice in the
zig-zig case, whereas splay rotates the **grandparent first**. Only splay also
roughly halves the depths of the other nodes on the search path, and only splay
has a good amortized bound. *(Ref §2, sl. 15, 17.)*
</details>

**A4. [open]** Build a path-shaped tree with keys `1..8` (each node the right
child of the previous) and splay `1` to the root. Draw every step, label each as
zig/zig-zig/zig-zag, and compare the resulting height to the start.

**A5. [open]** Do A4 again with move-to-root. Compare the final shapes — this is
the fastest way to *see* why zig-zig is defined as it is.

### B. Operations via splay

**B1.** Describe `delete(t,k)` via splay.

<details><summary>Solution</summary>

`splay(t,k)`; if the root holds `k`, remove it, leaving `t_ℓ` and `t_r`. Splay the
**largest** key of `t_ℓ` to its root — it then has no right child — and attach
`t_r` there. *(Ref §3, sl. 21.)*
</details>

**B2. [open]** Describe `insert(t,k)` via splay, including what happens when the
root ends up holding a neighbouring key `k′ > k`. *(Ref §3, sl. 19–20.)*

**B3. [open]** Sl. 22 observes that every operation "almost always" uses splay.
Which one is the exception, and why?

### C. The analysis

**C1.** Define rank and the potential.

<details><summary>Solution</summary>

`w` assigns each key a positive weight (`w ≡ 1` suffices); the size of a subtree
is the total weight in it; `r(x) = log(size(x))`; the potential is the **sum of
the ranks of all nodes**. *(Ref §4, sl. 25.)*
</details>

**C2.** State the splay lemma.

<details><summary>Solution</summary>

Amortized cost of `splay(t,k)` is at most `3(r(t) − r(p)) + 1`, with `p` the node
with key `k` or the last inner node of a failed search. *(Ref §4, sl. 27.)*
</details>

**C3.** Derive the `O(log n)` bound from the lemma.

<details><summary>Solution</summary>

With `w ≡ 1`, the whole tree has size `n`, so `r(t) = log n`; and `r(p) ≥ 0` since
subtree sizes are ≥ 1. Hence amortized cost `≤ 3 log n + 1 = O(log n)`.
*(Ref §4, sl. 38–39.)*
</details>

**C4.** State the auxiliary lemma and prove it.

<details><summary>Solution</summary>

If `a, b > 0` with `a + b ≤ c`, then `log a + log b ≤ 2 log c − 2`. Proof: from
`(a−b)² ≥ 0` we get `4ab ≤ (a+b)² ≤ c²`, so `ab ≤ c²/4`; taking logs,
`log a + log b ≤ 2 log c − 2`. *(Ref §4, sl. 31.)*
</details>

**C5.** Which of the three cases was tight, and what follows?

<details><summary>Solution</summary>

Only **zig-zig** (sl. 37). That is why the constant is 3 — the other two cases had
slack. The tightness is a structural fact about the operation, not an artefact of
the proof. *(Ref §4.)*
</details>

**C6. [open]** Sl. 41 asks what remains to prove for insert/delete/search once the
splay lemma is available. Answer it. *(Ref §4 — the key set changes, so the
potential changes in ways the lemma doesn't cover.)*

**C7. [open]** Work the zig-zag bound from `am ≤ 2 + r′(q) + r′(r) − 2r(p)` to
`3(r′(p) − r(p))` using the auxiliary lemma. *(Ref §4, sl. 32–33.)*

**C8. [open]** Explain the telescoping in one sentence, and say where the `+1`
comes from. *(Ref §4, sl. 36.)*

### D. Trade-offs and boundaries

**D1.** Give two advantages and two disadvantages.

<details><summary>Solution</summary>

**Pro:** no balance-information overhead, simple structure; the shape adapts to
the access pattern; `O(log n)` amortized. **Con:** no per-operation worst-case
guarantee (a single splay can be `Ω(n)`); the tree is restructured even on
**reads**, which is bad for concurrency and caching. *(Ref §5, sl. 49.)*
</details>

**D2.** What is the dynamic optimality conjecture, and is it settled?

<details><summary>Solution</summary>

Sleator and Tarjan conjectured splay trees are within a constant factor of *any*
BST strategy, including one knowing the access sequence in advance. **Still
open.** *(Ref §5, sl. 52.)*
</details>

**D3. [open]** Compare splay trees with B-trees (T03) as dictionary
implementations: what does each optimize, and when would you choose which?

**D4. [open]** Both splay trees and Fibonacci heaps (T04) have amortized bounds
via a potential. Compare the two potentials — what state quantity does each
measure, and why is each the natural choice?

## 3. External practice — scope filter

| Source | Take | Avoid |
|---|---|---|
| O/W 5.4 | **Assigned**; the deck follows its presentation and notation | — |
| O/W 3.3 | **Leseaufgabe** — self-adjusting lists; possibly never covered in AlgoDat I | — |
| Sleator & Tarjan 1985 | **First six pages only**, as the deck specifies | the rest of the paper |
| Frankfurt Klausuren | Splay items as explain-aloud drill | written framing |

**Filter:** in scope are the splay operation, the three cases, the reductions, the
rank potential, the lemma and its proof, and the stated trade-offs. **Out:** link-cut
trees, tango trees, and the wider dynamic-optimality literature — the conjecture is
named as an *Ausblick* only.
