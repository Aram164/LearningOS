---
id: note-algo2-cuckoo-hashing
type: note
title: "Algo 2 T06 — Reference: Cuckoo Hashing"
created: "2026-08-16"
role: reference
state: evolving
authorship: operator-drafted
concepts: [concept-cuckoo-hashing, concept-hashing-chaining, concept-adt-dictionary,
  concept-expected-value, concept-probability]
sources: [source-algo2-hu-materials, source-dms-grundwerkzeuge]
contexts: [workspace-algo2-exam-prep]
---

> **Build note (2026-08-16).** Operator-drafted from `ad2_hashing.pdf` (39 sl.).
> Companions: `-exercise-bank`, `-viva-drill`. Not yet worked by Aram.

# Algo 2 · Topic 6 — Cuckoo Hashing

*Lectures: 6. Mai `[1-19]`, 11. Mai `[20-end]`.*
***Literatur:** DMS Kap. 4 for the (re-)entry into hashing, **and** Rasmus Pagh
[2006] *"Cuckoo Hashing for Undergraduates"* — **both held locally**.
**Leseaufgabe:** read both independently, including what was not discussed.*

**Agenda (sl. 2):** Erinnerung ADT Dictionary + hashing · Wiederholung hashing
with chaining · core idea of cuckoo hashing · analysis (especially insert and
rehashing) · dynamic cuckoo hashing.

> ⚠️ **The one probabilistic topic in the course.** Everything else here is
> deterministic worst-case or amortized. These bounds are **expected values over
> the random choice of hash functions**. Keeping that distinction crisp — against
> T02's amortized bounds — is the most likely thing to be probed.

---

## 1. Setup (sl. 4–8) — Phase 0.5

**ADT Dictionary with unique keys**; **associative arrays** (sl. 5) are used
synonymously: an array with a potentially huge index set but very sparse actual
usage.

**When space is free (sl. 6):** if `S` is large relative to the universe `U`, or
memory is abundant, direct addressing works trivially. Hashing exists for when it
does not.

**Hashing (sl. 7).** Giving up the extra operations a search tree offers
(min/max, ordered traversal), hash tables are the most efficient realization of
the ADT. Key points, stated by the deck:

- we use **randomization** to choose storage locations;
- consequently we obtain only **expected values** for running times;
- **hash functions** `h` are essential.

**Collisions (sl. 8):** handling `x ≠ y` with `h(x) = h(y)` is as essential as the
hash function itself; several schemes exist.

---

## 2. Wiederholung: hashing with chaining (sl. 10–13)

*Sl. 10: "Sicher bekannt aus AlgoDat I."*

A hash function `h : U → {1,…,r}` and a table `T[1..r]`; all keys with the same
`h(x) = k` are stored in a **singly linked list** at `T[k]` — the **bucket**.
Space-efficient, and the analysis shows buckets are short on average.

> **Observation (sl. 11).** For two distinct keys `x ≠ y`,
> `P[h(x) = h(y)] = 1/r`, because the values `{1,…,r}` are equally likely for
> `h(x)`.

**Analysis (sl. 12).** It suffices to show the **expected bucket size of `x` is
constant**. Assume `x ∉ S` and add 1 to compensate. By linearity of expectation
over indicator variables, the expected number of keys colliding with `x` is
`|S|/r`, which is constant when `r = Θ(|S|)`.

**Summary (sl. 13):** collisions force potentially many elements into one bucket,
realized as linked lists.

---

## 3. The core idea (sl. 15–19)

**Weaknesses of what we know (sl. 15):**

- chaining and linear probing **cannot guarantee constant access time**;
- linear probing **degrades under deletion**.

> **Idea (sl. 16).** Use **two** hash functions `h₁, h₂ : U → {1,…,r}`. Every key
> has exactly **two possible positions and may be stored only there.**

That single restriction is what buys a **worst-case** guarantee for lookups: to
find `x` you check two cells and stop.

**Collisions — the cuckoo move (sl. 17).** *"Wir machen es wie der Kuckuck!"* To
insert `x`, place it at `h₁(x)`. If that cell is occupied, **evict the occupant**
and re-place *it* at its own alternative position, which may evict another, and so
on.

**insert(x) (sl. 18):**

```
1  if T[h₁(x)] = x or T[h₂(x)] = x then return          // already present
2  pos ← h₁(x)
3  for n times do
4      if T[pos] = nil then T[pos] ← x; return
5      x ↔ T[pos]                                       // evict: swap in
6      if pos = h₁(x) then pos ← h₂(x) else pos ← h₁(x) // go to the other slot
7  rehash and reinsert
```

The loop is bounded; if it runs out, the structure **rehashes**.

**Example (sl. 19):** the deck works Pagh's page-4 example at the board — read
pages 4–5 of `Pagh06_CuckooHashingForUndergraduates.pdf`.

---

## 4. Analysis (sl. 21–33)

### search and delete (sl. 21) — *the headline result*

> **`search(x)`:** check `T[h₁(x)] = x` and `T[h₂(x)] = x`. **`O(1)` worst case.**
> **`delete(x)`:** likewise, then set to `nil`. **`O(1)` worst case.**

**Not expected — worst case.** This is the whole point of the two-position
restriction, and it is what chaining cannot offer.

### insert (sl. 22–27)

Goal: **`O(1)` expected**. Shown first for the case where no rehashing is needed.
The approach mirrors chaining: show the relevant "bucket" — here, the set of cells
reachable by the eviction chain — has constant expected size.

**The cuckoo graph.** Vertices are the `r` table cells; each key `x` contributes an
edge between `h₁(x)` and `h₂(x)`. An eviction chain is a walk in this graph, so
insert cost is governed by path lengths.

> **Lemma (sl. 23–26).** For any `i, j ∈ {1,…,r}`, with `r ≥ 2cn` for some `c > 1`
> and `ℓ ≥ 1`: the probability that the undirected cuckoo graph contains an
> `i,j`-path of length `ℓ` is **at most `c^{−ℓ}/r`**.

Summing the geometric series over `ℓ` gives a constant expected chain length —
hence **`insert` in expected `O(1)`** when no rehash occurs.

**Interim status (sl. 27):** `search` `O(1)` worst case · `delete` `O(1)` worst
case · `insert` expected `O(1)` **absent rehashing**. What about rehashing?

### Rehashing (sl. 29–33)

**What happens (sl. 29):** choose `r′ ≥ 2c·|S|` and an empty table `T′[1..r′]`
(for an insert, `r′ = r`); choose **new random hash functions**; reinsert
everything.

**How many attempts (sl. 30–31)?** The same lemma applies.

> **Result (sl. 31).** For `c ≥ 3`, i.e. `r′ ≥ 2c|S|`, the probability that the
> cuckoo graph contains a **cycle** is at most `1/2`. **If there is no cycle, the
> rehash succeeds.** So the expected number of attempts is at most 2.

**And the cost at insert time (sl. 32–33)?** The natural objection: rehashing is
`O(n)`, so how can insert stay `O(1)`?

> **Answer.** Rehashing costs `O(n)` expected **when it happens**, but at a given
> `insert` it happens with probability only `O(1/r)`. The contribution is
> `O(1/r)·O(n) = O(n/r) = O(1)`, because `r ≥ 2cn`.

**The table's slack is what pays for the rehash.** That is the design.

---

## 5. Dynamic cuckoo hashing (sl. 35–36)

Analogous to dynamic arrays: the table size adapts repeatedly to `|S|`, growing
and shrinking with rebuilds.

**Costs (sl. 36):**

- **`search`:** the table size never has to change for it, so no overhead — and it
  is **independent of the randomness**. `O(1)` worst case.
- **`insert`/`delete`:** **amortized expected `O(1)`** — amortized over the
  resizes, expected over the hash functions.

> 🎯 **"Amortized expected"** is a compound guarantee combining T02's method with
> this topic's probability. Being able to say which word covers which source of
> uncertainty is exactly the level of precision an oral rewards.

---

## 6. Überblick and Ausblick (sl. 38–39)

**Überblick.** Hashing is the essential technique for the ADT Dictionary /
associative arrays; we recalled hashing in general and chaining in particular;
cuckoo hashing is the new variant, with worst-case constant lookup.

**Ausblick (sl. 39).** Hashing is heavily researched both theoretically and
practically. The open thread the deck names: **what should good hash functions
look like**, and how are they constructed — the analysis above assumed idealized
randomness.

---

## 7. Exam-critical minimum

| Must be automatic | Where |
|---|---|
| Randomization ⟹ only **expected** runtimes | sl. 7 |
| `P[h(x) = h(y)] = 1/r` | sl. 11 |
| Chaining's expected bucket size is constant | sl. 12 |
| Chaining/probing **cannot guarantee** constant access | sl. 15 |
| Two hash functions, **two allowed positions only** | sl. 16 |
| The eviction loop, and that it is bounded | sl. 18 |
| **`search` and `delete` are `O(1)` worst case** | sl. 21 |
| The cuckoo graph and the path lemma | sl. 23 |
| `insert` expected `O(1)` | sl. 26 |
| Cycle probability ≤ `1/2` for `c ≥ 3` | sl. 31 |
| Why rehashing doesn't break `O(1)`: `O(1/r)·O(n) = O(1)` | sl. 32–33 |
| Dynamic version: search `O(1)` worst case, insert/delete **amortized expected** `O(1)` | sl. 36 |

**Traps:** saying lookup is "expected `O(1)`" — it is worst case, and that is the
selling point; confusing this topic's *expected* bounds with T02's *amortized*
ones; forgetting the load condition `r ≥ 2cn`; claiming insert is worst-case
`O(1)`; being unable to explain why an `O(n)` rehash doesn't spoil the bound.
