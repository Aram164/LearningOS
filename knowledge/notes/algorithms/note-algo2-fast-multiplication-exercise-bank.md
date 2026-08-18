---
id: note-algo2-fast-multiplication-exercise-bank
type: note
title: "Algo 2 T01 — Exercise Bank: Schnellere Multiplikation"
created: "2026-08-16"
role: exercise-bank
state: evolving
authorship: operator-drafted
concepts: [concept-fast-multiplication, concept-recurrences-master-theorem,
  concept-asymptotic-analysis]
sources: [source-algo2-hu-materials, source-dms-grundwerkzeuge, source-clrs]
contexts: [workspace-algo2-exam-prep]
---

> **Build note (2026-08-16).** Operator-drafted from `ad2_fastmultiplication.pdf`.
> Solutions operator-computed, **unverified by Aram**. Where a solution disagrees
> with the deck, the deck wins.

# Algo 2 · Topic 1 — Exercise Bank

**Scope:** number representation and addition cost, the school method and its
`3n²` bound, the recursive split, Karatsuba's identity and its multiplication
count, both recurrences, the master theorem, `O(n^{log₂ 3})`, Toom-k.

> 🚨 **No HU Übungsblatt exists for this topic** — none exists for any topic
> except stable matching. The course's own practice instruction is the
> **Leseaufgabe**: read DMS Kap. 1 completely, including material not lectured.
> Do that; it is the closest thing to an assigned exercise set.

## 1. Local material

| File | What | Where |
|---|---|---|
| `note-algo2-fast-multiplication` | Reference (§ refs below) | this vault |
| `note-algo2-fast-multiplication-viva-drill` | Oral drill | this vault |
| `note-algo2-phase0-prerequisites` | Phase 0.2 = master theorem | this vault |
| DMS Kap. 1 | **The assigned reading** | `material://source-dms-grundwerkzeuge/dms.pdf` |
| CLRS Kap. 4 | Recurrences, if Phase 0.2 failed | `material://source-clrs/clrs-de.pdf` |

## 2. Drills

### A. Counting

**A1.** Show the school method uses fewer than `3n²` elementary operations.

<details><summary>Solution</summary>

Each of the `n` partial products `q_j = a·b_j` costs about `2n` (one op per digit
for `a_i·b_j`, then `n` more to combine the `c`/`d` rows). Accumulating the `n`
shifted partial products costs a further `≈ n` each. Summing over `j = 0..n−1`
gives `< 3n²`. *(Ref §2, sl. 9–14.)*
</details>

**A2.** Why does it matter that the `3n²` bound is *tight*?

<details><summary>Solution</summary>

Because if the school method could be `o(n²)` with better bookkeeping, Karatsuba
would be an implementation detail rather than a different algorithm. Tightness is
what makes `O(n^{log₂ 3})` a real asymptotic improvement. *(Ref §2, sl. 14.)*
</details>

**A3. [open]** Multiply two 4-digit numbers in base 10 by the school method and
count your actual elementary operations. Compare to `3n² = 48`. *(Ref §2.)*

### B. The split and Karatsuba's identity

**B1.** Write the recursive-school-method expansion and count its multiplications.

<details><summary>Solution</summary>

`a = a₁B^k + a₀`, `b = b₁B^k + b₀`, `k = ⌊n/2⌋`, so
`a·b = a₁b₁B^{2k} + (a₁b₀ + a₀b₁)B^k + a₀b₀` — **four** half-length
multiplications. *(Ref §3, sl. 17.)*
</details>

**B2.** Write Karatsuba's identity from memory and count the multiplications.

<details><summary>Solution</summary>

`a·b = a₁b₁B^{2k} + ((a₁+a₀)(b₁+b₀) − (a₁b₁ + a₀b₀))B^k + a₀b₀`.
Apparently five, actually **three**: `a₁b₁` and `a₀b₀` each occur twice and are
computed once. Six additions. *(Ref §4, sl. 21–22.)*
</details>

**B3.** Verify Karatsuba's identity algebraically — show the middle term really
is `a₁b₀ + a₀b₁`.

<details><summary>Solution</summary>

`(a₁+a₀)(b₁+b₀) = a₁b₁ + a₁b₀ + a₀b₁ + a₀b₀`. Subtracting `a₁b₁ + a₀b₀` leaves
`a₁b₀ + a₀b₁`. ∎ *(Ref §4.)*
</details>

**B4. [open]** Run Karatsuba by hand on `a = 1234`, `b = 5678` in base 10 with
`k = 2`. Track all three sub-multiplications and check the result. *(Ref §4.)*

**B5. [open]** Why is it fine that the additions went from `4n` to `8n`?
*(Ref §4, sl. 22.)*

### C. Recurrences

**C1.** State both recurrences exactly as the deck gives them.

<details><summary>Solution</summary>

Recursive school method: `T(n) ≤ 1` for `n = 1`; `4T(⌈n/2⌉) + 4n` for `n ≥ 2`.
Karatsuba: `T(n) ≤ 3n²` for `n ≤ 3`; `3T(⌈n/2⌉ + 1) + 8n` for `n ≥ 4`.
*(Ref §3–4, sl. 23.)*
</details>

**C2.** Solve `T(n) = 4T(n/2) + n` and `T(n) = 3T(n/2) + n` by the master theorem.

<details><summary>Solution</summary>

Both have `b = 2` and `f(n) = n`.
First: `a = 4`, `d = log₂4 = 2`; `f(n) = n` polynomially smaller than `n²` →
`Θ(n²)` — no gain over the school method.
Second: `a = 3`, `d = log₂3 ≈ 1.585`; again `f` polynomially smaller →
`Θ(n^{log₂3})`. **The only thing that changed was `a`.** *(Ref §5, sl. 28.)*
</details>

**C3. [open]** State the master theorem's three cases with their conditions, then
say which case both C2 recurrences fall into. *(Ref §5; Phase 0.2.)*

**C4. [open]** The Karatsuba recurrence has `⌈n/2⌉ + 1`, not `n/2`. Why can the
master theorem still be applied? *(Ref §5, sl. 28 — the deck addresses this.)*

### D. Bounds and the bigger picture

**D1.** State the final theorem, with its constant.

<details><summary>Solution</summary>

`T(n) ≤ 153·n^{log₂3} = O(n^{log₂3})` for all `n` (sl. 24). *(Ref §4.)*
</details>

**D2. [open]** For roughly what `n` does `153·n^{log₂3}` actually beat `3n²`?
Solve approximately and comment on what that means practically. *(Ref §4.)*

**D3. [open]** Toom-3 gives `O(n^{1.46})`. Reconstruct why: how many
multiplications of `n/3`-length numbers, and what is `log₃` of that? *(Ref §6,
sl. 31.)*

**D4. [open]** Explain why increasing `k` in Toom-k has diminishing returns.
*(Ref §6.)*

### E. Cross-wires

**E1. [open]** Topic 12 (FFT) also multiplies integers. State both bounds and say
which wins and when. *(Use `note-algo2-fft` once built.)*

**E2. [open]** Karatsuba is divide-and-conquer; so is merge sort. Write both
recurrences side by side and say why one is `n log n` and the other isn't.
*(Ref §5.)*

## 3. External practice — scope filter

| Source | Take | Avoid |
|---|---|---|
| DMS Kap. 1 | **The assigned Leseaufgabe**, in full | — |
| CLRS Kap. 4 | Recurrence-solving technique, substitution and recursion trees | the Akra-Bazzi material — beyond scope |
| `source-algo2-frankfurt-klausuren` | Any Karatsuba/master-theorem items, as explain-aloud drill | it is a written format from another university |

**Filter:** this deck stops at Toom-k as an *Ausblick*. Schönhage–Strassen,
Fürer, and Harvey–van der Hoeven are **not** in scope — know that faster methods
exist, do not study them.
