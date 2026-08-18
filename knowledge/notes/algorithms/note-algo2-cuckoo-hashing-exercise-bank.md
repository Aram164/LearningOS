---
id: note-algo2-cuckoo-hashing-exercise-bank
type: note
title: "Algo 2 T06 — Exercise Bank: Cuckoo Hashing"
created: "2026-08-16"
role: exercise-bank
state: evolving
authorship: operator-drafted
concepts: [concept-cuckoo-hashing, concept-hashing-chaining, concept-expected-value]
sources: [source-algo2-hu-materials, source-dms-grundwerkzeuge, source-algo2-frankfurt-klausuren]
contexts: [workspace-algo2-exam-prep]
---

> **Build note (2026-08-16).** Operator-drafted from `ad2_hashing.pdf`. Solutions
> operator-computed, **unverified by Aram**. Deck wins on disagreement.

# Algo 2 · Topic 6 — Exercise Bank

**Scope:** hashing and collisions, chaining and its expected bucket size, the
two-function idea, the eviction loop, worst-case lookup, the cuckoo graph and
path lemma, rehashing and its cost, the dynamic variant.

> 🔗 **Cross-module:** the probability half (linearity of expectation, indicator
> variables) is shared with M2/SaD. If both modules are live, do this alongside
> the SaD probability lectures.

## 1. Local material

| File | What | Where |
|---|---|---|
| `note-algo2-cuckoo-hashing` | Reference (§ refs below) | this vault |
| `note-algo2-cuckoo-hashing-viva-drill` | Oral drill | this vault |
| `note-algo2-phase0-prerequisites` | Phase 0.5 = chaining + expectation | this vault |
| DMS Kap. 4 | **Assigned reading** | `material://source-dms-grundwerkzeuge/dms.pdf` |
| Pagh 2006 | **Assigned**; sl. 19's example is on pp. 4–5 | `material://source-algo2-hu-materials` |

## 2. Drills

### A. Hashing basics

**A1.** Why does hashing yield only expected running times?

<details><summary>Solution</summary>

Storage locations are chosen by randomization (the hash function), so runtimes
are random variables and we can only bound their expectations. *(Ref §1, sl. 7.)*
</details>

**A2.** Show `P[h(x) = h(y)] = 1/r` for `x ≠ y`, and show the expected bucket size
under chaining is constant.

<details><summary>Solution</summary>

Under idealized randomness the `r` values are equally likely for `h(x)`, so for
fixed `h(y)` the probability of a match is `1/r`. Expected bucket size: define
`I_y = 1` iff `h(y) = h(x)`; by linearity, `E[Σ_y I_y] = |S|/r`, constant when
`r = Θ(|S|)`. *(Ref §2, sl. 11–12.)*
</details>

**A3.** What two weaknesses of chaining/linear probing motivate cuckoo hashing?

<details><summary>Solution</summary>

Neither can **guarantee** constant access time; and linear probing **degrades
under deletion**. *(Ref §3, sl. 15.)*
</details>

### B. The structure

**B1.** State the core idea in one sentence, and say what it buys.

<details><summary>Solution</summary>

Two hash functions `h₁, h₂`; every key may be stored **only** at `h₁(x)` or
`h₂(x)`. Consequence: lookup checks two cells, so `search` is **`O(1)` worst
case**. *(Ref §3, sl. 16; §4, sl. 21.)*
</details>

**B2.** Write the insert loop.

<details><summary>Solution</summary>

If `x` is already at either position, return. Set `pos ← h₁(x)`. Repeat up to `n`
times: if `T[pos]` is free, store and return; otherwise **swap** `x` with
`T[pos]`, and move `pos` to the *other* position of the newly displaced key. If
the loop exhausts, **rehash**. *(Ref §3, sl. 18.)*
</details>

**B3. [open]** Work Pagh's page-4 example by hand, drawing the table after each
eviction. *(The deck does this at the board — sl. 19.)*

**B4. [open]** Construct a small instance where inserting one key causes at least
four evictions. Then construct one that forces a rehash.

### C. The analysis

**C1.** Give search and delete costs, precisely.

<details><summary>Solution</summary>

Both **`O(1)` worst case** — two cell probes. *(Ref §4, sl. 21.)*
</details>

**C2.** Define the cuckoo graph.

<details><summary>Solution</summary>

Vertices = the `r` table cells; each key `x` contributes an edge `{h₁(x), h₂(x)}`.
An eviction chain is a walk in this graph, so insert cost is a path-length
question. *(Ref §4.)*
</details>

**C3.** State the path lemma.

<details><summary>Solution</summary>

For any `i, j`, with `r ≥ 2cn` (`c > 1`) and `ℓ ≥ 1`, the probability that the
undirected cuckoo graph has an `i,j`-path of length `ℓ` is at most `c^{−ℓ}/r`.
Summing the geometric series bounds the expected chain length by a constant.
*(Ref §4, sl. 23.)*
</details>

**C4.** State the rehashing result and why insert stays `O(1)`.

<details><summary>Solution</summary>

For `c ≥ 3` (i.e. `r′ ≥ 2c|S|`) the cycle probability is at most `1/2`; without a
cycle the rehash succeeds, so expected attempts ≤ 2. A rehash costs `O(n)`
expected but occurs at a given insert with probability only `O(1/r)`, contributing
`O(n/r) = O(1)` since `r ≥ 2cn`. *(Ref §4, sl. 31–33.)*
</details>

**C5. [open]** Where exactly is `r ≥ 2cn` used? What happens to each bound if the
table is only `r = n`?

**C6. [open]** Why does a **cycle** in the cuckoo graph make the rehash fail?
Reason about how many keys map into a cyclic component versus how many cells it
has.

**C7. [open]** Sum the geometric series in C3 explicitly to get the constant.

### D. The dynamic variant

**D1.** Give the three costs for dynamic cuckoo hashing.

<details><summary>Solution</summary>

`search`: **`O(1)` worst case**, and independent of the randomness — the table
size never needs to change for a lookup. `insert`, `delete`: **amortized expected
`O(1)`** — amortized over resizes, expected over hash functions. *(Ref §5,
sl. 36.)*
</details>

**D2. [open]** Explain "amortized expected" — which word handles which source of
uncertainty? *(Ref §5.)*

### E. Boundaries

**E1.** Contrast this topic's guarantees with T02's.

<details><summary>Solution</summary>

T02 (amortized): **deterministic**, worst case over a *sequence*, no probability.
Here: **probabilistic**, expectation over the random hash functions, for a single
operation. Cuckoo's `search` is neither — it is plain worst case. Three distinct
kinds of guarantee, all in one course. *(Ref §4.)*
</details>

**E2. [open]** What does the Ausblick name as the open question, and why does it
matter for the analysis above? *(Ref §6, sl. 39 — the analysis assumed idealized
randomness.)*

**E3. [open]** Compare cuckoo hashing with B-trees (T03) and splay trees (T05) as
dictionary implementations: which operations does each guarantee, and at what cost?

## 3. External practice — scope filter

| Source | Take | Avoid |
|---|---|---|
| Pagh 2006 | **Assigned**; short, and the source of the worked example | — |
| DMS Kap. 4 | **Assigned**; hashing re-entry, universal hashing | — |
| Frankfurt Klausuren | Hashing items as explain-aloud drill | written framing |

**Filter:** in scope are chaining recall, the two-function scheme, the eviction
loop, the graph lemma, rehashing, and the dynamic variant. **Out:** `d`-ary cuckoo
hashing, blocked cuckoo, cuckoo filters, and the detailed construction of
universal/tabulation hash families — good hash function design is named as an
*Ausblick*.
