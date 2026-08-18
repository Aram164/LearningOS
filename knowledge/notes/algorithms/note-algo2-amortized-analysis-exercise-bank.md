---
id: note-algo2-amortized-analysis-exercise-bank
type: note
title: "Algo 2 T02 — Exercise Bank: Amortisierte Analyse"
created: "2026-08-16"
role: exercise-bank
state: evolving
authorship: operator-drafted
concepts: [concept-amortized-analysis, concept-asymptotic-analysis]
sources: [source-algo2-hu-materials, source-clrs, source-algo2-frankfurt-klausuren]
contexts: [workspace-algo2-exam-prep]
---

> **Build note (2026-08-16).** Operator-drafted from `ad2_amortizedanalysis.pdf`.
> Solutions operator-computed, **unverified by Aram**. Deck wins on disagreement.

# Algo 2 · Topic 2 — Exercise Bank

**Scope:** why amortized analysis; aggregate, accounting and potential methods;
the multipop stack and `k`-bit counter under all three; the potential theorem and
its conditions; dynamic arrays.

> 🎯 **Highest-yield bank in the course.** The Frankfurt Klausuren list amortized
> analysis among their recurring topics, and two later lectures depend on it.
> **Leseaufgabe: CLRS 17.4, dynamic tables** — the deck sets it as sl. 40.

## 1. Local material

| File | What | Where |
|---|---|---|
| `note-algo2-amortized-analysis` | Reference (§ refs below) | this vault |
| `note-algo2-amortized-analysis-viva-drill` | Oral drill | this vault |
| CLRS Kap. 17.1–17.4 | Assigned reading + Leseaufgabe | `material://source-clrs/clrs-de.pdf` |
| Frankfurt Klausuren | Solved items on amortized analysis | `material://source-algo2-frankfurt-klausuren` |

## 2. Drills

### A. The three methods, three ways

**A1.** Give the aggregate argument for the multipop stack.

<details><summary>Solution</summary>

`push`/`pop` are `Θ(1)`. A `multipop(S,k)` costs `Θ(1)` plus `ℓ ≤ k` pops on a
non-empty stack. **Each such pop requires an earlier push of that element**, and
there are at most `m` pushes in total. So all pops across the whole sequence
number at most `m` → total `O(m)`, amortized `O(1)`. *(Ref §3, sl. 10.)*
</details>

**A2.** Give the aggregate argument for the `k`-bit counter, with the sum.

<details><summary>Solution</summary>

`A[i]` flips on every `2^i`-th increment; bits `i ≥ k` don't exist. Total flips
`= Σ_{i=0}^{k−1} ⌊m/2^i⌋ < m·Σ_{i≥0} 2^{−i} = 2m`. Total `O(m)`, amortized `O(1)`
per increment — **independent of `k`**. *(Ref §3, sl. 12.)*
</details>

**A3.** State the deck's fictitious costs for the stack.

<details><summary>Solution</summary>

`d(push) = 2`, `d(pop) = 1`, `d(multipop) = 1`, against actual `1`, `1`,
`min{k,|S|+1}`. **The deck explicitly deviates from CLRS here (sl. 18)** — use
these. *(Ref §4.)*
</details>

**A4.** Why does the naive induction hypothesis fail, and what replaces it?

<details><summary>Solution</summary>

`d(Q) ≥ c(Q)` alone does not carry through the induction step — sl. 19 is a
deliberate `Fehlversuch`. Strengthen to `d(Q) ≥ c(Q) + |S|`: the extra `|S|` is
the accumulated credit, one unit per stacked element, which is exactly what a
later `multipop` will spend. Base case `m = 0`. *(Ref §4, sl. 19–20.)*
</details>

**A5.** Define the potential method and state the theorem with both conditions.

<details><summary>Solution</summary>

`d(q) := c(q) + Φ(D″) − Φ(D′)`. **Theorem (sl. 29):** for any `Φ` with
`Φ(D₀) = 0` and `Φ(Dᵢ) ≥ 0` for all `i`, `d(Q) ≥ c(Q)` for all sequences.
*(Ref §5.)*
</details>

**A6.** Give both potential functions and derive one amortized cost from each.

<details><summary>Solution</summary>

**Stack:** `Φ(S) = |S|`. `d(push) = 1 + 1 = 2`.
**Counter:** `Φ(A)` = number of ones. An increment flipping `j` bits clears `j−1`
ones and sets one, so `ΔΦ = 2 − j` and `d = j + (2 − j) = 2`. *(Ref §5,
sl. 30–34.)*
</details>

**A7.** What is the *actual* condition on `Φ` for `d(Q) ≥ c(Q)`?

<details><summary>Solution</summary>

Since `d(Q) = Φ(D_m) − Φ(D₀) + c(Q)`, the bound holds **iff `Φ(D_m) ≥ Φ(D₀)`**.
`Φ(D₀) = 0` with `Φ ≥ 0` is the usual *sufficient* condition, chosen because it
works for **every** sequence at once. *(Ref §5, sl. 36.)*
</details>

**A8. [open]** Redo the counter under the accounting method, and say in one
sentence what the "2" buys. *(Ref §4, sl. 22.)*

### B. Dynamic arrays — the Leseaufgabe

**B1. [open]** A dynamic array doubles when full, copying everything. Give the
aggregate analysis for `m` insertions from empty. *(Ref §6, sl. 40; CLRS 17.4.)*

**B2. [open]** Now do it with a potential function. Find a `Φ` that makes each
insert `O(1)` amortized. *(Hint: it should be 0 right after a resize and maximal
right before the next.)*

**B3. [open]** Add deletion. If you halve when the array drops to half-full,
construct a sequence with bad amortized behaviour. What halving threshold fixes
it, and why? *(This is CLRS 17.4's real content and a classic exam question.)*

### C. Choosing a method

**C1. [open]** For each, say which method you'd reach for first and why:
(a) a fixed known sequence of simple operations; (b) a structure where one
operation occasionally does `Θ(n)` work; (c) a structure whose state has a
natural "messiness" measure. *(Ref §2, sl. 13/23/35.)*

**C2. [open]** Aggregate analysis is described as "too hard for complex data
structures." Why does the potential method scale better? *(Ref §5, sl. 29.)*

### D. Concept boundaries — where marks are lost

**D1.** Is amortized analysis average-case analysis?

<details><summary>Solution</summary>

**No.** It is a deterministic worst-case bound over a *sequence* of operations.
No probability, no distribution over inputs, no randomization. The guarantee
holds for **every** sequence. Contrast with cuckoo hashing (T06), whose bounds
*are* probabilistic — the course teaches both, and conflating them is the
standard error. *(Ref §1.)*
</details>

**D2. [open]** A splay tree operation can cost `Θ(n)`. Is "splay trees are
`O(log n)`" therefore false? Answer precisely. *(Ref §1; forward to T05.)*

**D3. [open]** Can amortized cost exceed actual cost for a given operation? Can
it be lower? Give an example of each from the stack. *(Ref §5, sl. 28, 32.)*

### E. Cross-wires

**E1. [open]** Fibonacci heaps use the potential method (T04). Before reading
that deck, predict what their potential function must measure. *(Ref §6, sl. 39.)*

**E2. [open]** Same for splay trees (T05). What state quantity would you choose?

**E3. [open]** Union-Find appears in the Ausblick but is **not** a lecture topic.
Note that boundary and move on — it is the deck's own scope statement.

## 3. External practice — scope filter

| Source | Take | Avoid |
|---|---|---|
| CLRS 17.1–17.3 | The assigned reading; same three methods | its stack fictitious costs — **the deck deviates** |
| CLRS 17.4 | **The set Leseaufgabe**, dynamic tables | — |
| Frankfurt Klausuren | Amortized-analysis items, as explain-aloud drill | written-format framing; other university's notation |

**Filter:** three methods, two running examples, dynamic arrays. Union-Find,
competitive analysis of online algorithms, and amortization in functional data
structures are **out** — the Ausblick names Union-Find but does not teach it.
