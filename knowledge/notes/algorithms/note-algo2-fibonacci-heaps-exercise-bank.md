---
id: note-algo2-fibonacci-heaps-exercise-bank
type: note
title: "Algo 2 T04 — Exercise Bank: Fibonacci-Heaps"
created: "2026-08-16"
role: exercise-bank
state: evolving
authorship: operator-drafted
concepts: [concept-fibonacci-heaps, concept-adt-priority-queue, concept-amortized-analysis]
sources: [source-algo2-hu-materials, source-clrs, source-algo2-frankfurt-klausuren]
contexts: [workspace-algo2-exam-prep]
---

> **Build note (2026-08-16).** Operator-drafted from `ad2_fibonacciheap.pdf`.
> Solutions operator-computed, **unverified by Aram**. Deck wins on disagreement.

# Algo 2 · Topic 4 — Exercise Bank

**Scope:** the PQ bound table, why bubbling fails, structure and marking, the
potential `Φ = t + 2m`, all six operations with their amortized costs,
consolidation, cascading cuts, and the `D(n) = O(log n)` proof chain.

> 🔗 **Prerequisite:** T02 amortized analysis, complete. Every cost here is a
> potential-method computation.

## 1. Local material

| File | What | Where |
|---|---|---|
| `note-algo2-fibonacci-heaps` | Reference (§ refs below) | this vault |
| `note-algo2-fibonacci-heaps-viva-drill` | Oral drill | this vault |
| `note-algo2-amortized-analysis` | The method this topic applies | this vault |
| CLRS Kap. 19 | **Assigned reading + figures** | `material://source-clrs/clrs-de.pdf` |
| Frankfurt Klausuren | Solved Fibonacci-heap items | `material://source-algo2-frankfurt-klausuren` |

## 2. Drills

### A. Motivation and structure

**A1.** Reproduce the sl. 6 table for binary, binomial and Fibonacci heaps.

<details><summary>Solution</summary>

See reference §1. **Key rows:** binary `union` is `O(n)`; binomial is `O(log n)`
across the board; Fibonacci amortized gives `O(1)` for `insert`, `min`,
`decreasekey`, `union` and `O(log n)` for `extractmin`, `delete` — with a
**worst-case row of `O(n)`** for the removing operations. *(Ref §1.)*
</details>

**A2.** Why can't `decreasekey` bubble the node upward?

<details><summary>Solution</summary>

Bubbling costs `O(h)`, so `m` calls cost `Ω(m·h) = Ω(m log n)` — no better than a
binomial heap. Instead the node is **cut** from its parent into the root list,
which is `O(1)`; marking then limits the structural damage. *(Ref §2, sl. 9–10.)*
</details>

**A3.** State the four marking rules.

<details><summary>Solution</summary>

Roots are always unmarked · new nodes are unmarked and enter the root list · a
node is marked when it loses its **first** child since becoming a child · a marked
node that loses a **second** child is itself cut into the root list and unmarked.
*(Ref §3, sl. 14.)*
</details>

**A4. [open]** Why must roots be unmarked? What would break if a root carried a
mark? *(Think about `Φ` and about what a mark is a promise of.)*

### B. The potential function

**B1.** State `Φ` and explain each term.

<details><summary>Solution</summary>

`Φ(H) = t(H) + 2m(H)`; `t` = trees in the root list, `m` = marked nodes. `t` pays
for future consolidation; `2m` pays for a future cut **and** the mark that cut
will place on the node's own parent. *(Ref §3, sl. 16–17.)*
</details>

**B2.** Derive the amortized cost of `insert`.

<details><summary>Solution</summary>

Actual `O(1)`. `t` increases by 1, `m` unchanged → `ΔΦ = +1`. Amortized
`O(1) + 1 = O(1)`. *(Ref §4, sl. 21.)*
</details>

**B3.** Derive the amortized cost of `union`.

<details><summary>Solution</summary>

Actual `O(1)` (concatenate root lists). `t(H) = t(H₁)+t(H₂)` and marks add, so
`ΔΦ = 0`. Amortized `O(1)`. *(Ref §4, sl. 24.)*
</details>

**B4.** Derive the amortized cost of `decreasekey` — the important one.

<details><summary>Solution</summary>

Let `d` be the number of cascading cuts. Actual `≤ β·d + O(1)`. Potential: each
cut adds one tree (`+1`) but clears one mark (`−2`), net `−1` per cut, so
`ΔΦ ≤ −d + O(1)`. Sum: `β·d − d + O(1) = O(1)` for suitable constants — **the `d`
terms cancel**, which is exactly why the factor 2 is in `Φ`. *(Ref §5,
sl. 38–40.)*
</details>

**B5. [open]** Redo B4 with `Φ = t + m` (factor 1). Where does the argument fail?
*(This is the cleanest way to see why the 2 is there.)*

**B6. [open]** Derive `extractmin`'s amortized cost from actual `O(t(H) + log n)`
and `ΔΦ = D(n) + 1 − t(H)`. *(Ref §5, sl. 32–33.)*

### C. Consolidation

**C1.** Describe consolidation and its data structure.

<details><summary>Solution</summary>

Array `A[0..D(n)]` where `A[d]` holds a root of degree `d`. Walk the root list;
for each root `x` of degree `d`, while `A[d] ≠ nil`, link `x` with `A[d]` (larger
key becomes the child), clear `A[d]`, increment `d`; finally store `x` in `A[d]`.
Result: at most one tree per degree, so `O(log n)` trees. *(Ref §5, sl. 29–30.)*
</details>

**C2. [open]** Run consolidation by hand on a root list with degrees
`0,0,1,1,1,2`. Show the array after each step and give the final degrees.

**C3. [open]** Why does the root list have at most `D(n)+1` trees afterwards?

### D. The degree bound

**D1.** State the child-degree lemma and justify it.

<details><summary>Solution</summary>

For `x` with `grad[x] = k` and children `y₁,…,y_k` in linking order:
`grad[y₁] ≥ 0` and `grad[yᵢ] ≥ i−2` for `i ≥ 2`. When `yᵢ` was linked, `x` had
≥ `i−1` children and links join **equal degrees**, so `grad[yᵢ] ≥ i−1` then;
since it has lost **at most one** child (a second loss would have cut it away),
`grad[yᵢ] ≥ i−2`. *(Ref §6, sl. 46–48.)*
</details>

**D2.** State the size lemma and the conclusion.

<details><summary>Solution</summary>

`size(x) ≥ F_{k+2} ≥ φ^k` with `k = grad[x]`, `φ = (1+√5)/2`. Since
`n ≥ size(x) ≥ φ^k`, we get `k ≤ log_φ n`, i.e. **`D(n) = O(log n)`**.
*(Ref §6, sl. 53–54.)*
</details>

**D3. [open]** Prove `F_{k+2} = 1 + Σ_{i=0}^{k} Fᵢ` by induction. *(The deck sets
this as an Übung, sl. 51.)*

**D4. [open]** The deck notes `F_k ≥ 2^{k/2} ≥ 1.414^k` would also have sufficed
(sl. 50). Redo the conclusion with that weaker bound — does `D(n) = O(log n)` still
follow? What changes?

**D5. [open]** Sl. 44 asks: for each `k`, find the Fibonacci heap with a
degree-`k` node and as few nodes as possible. Construct it for `k = 1,2,3,4` and
count. What sequence appears?

### E. Boundaries

**E1. [open]** "Fibonacci heaps are `O(1)` for decreasekey" — restate precisely
enough to be correct. *(Ref §1 — amortized, not worst-case.)*

**E2. [open]** Dijkstra with a binary heap vs a Fibonacci heap: write both total
bounds in terms of `|V|` and `|E|`, and say when the Fibonacci version wins.
*(Ref §1; connects to T07.)*

**E3. [open]** Where does the name "Fibonacci" come from? *(Not the structure —
the degree bound.)*

## 3. External practice — scope filter

| Source | Take | Avoid |
|---|---|---|
| CLRS Kap. 19 | **Assigned**; work the figures | — |
| `note-algo2-amortized-analysis` | The potential method itself | — |
| Frankfurt Klausuren | Fibonacci items as explain-aloud drill | written framing |

**Filter:** in scope are structure, marking, `Φ = t + 2m`, all six operations,
consolidation, the degree bound. **Pairing heaps are an Ausblick only** (sl. 57)
— know the name, do not study them. Strict Fibonacci heaps, rank-pairing heaps
and Brodal queues are outside the course entirely.
