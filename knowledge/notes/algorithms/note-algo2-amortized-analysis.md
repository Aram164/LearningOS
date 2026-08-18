---
id: note-algo2-amortized-analysis
type: note
title: "Algo 2 T02 — Reference: Amortisierte Analyse"
created: "2026-08-16"
role: reference
state: evolving
authorship: operator-drafted
concepts: [concept-amortized-analysis, concept-asymptotic-analysis]
sources: [source-algo2-hu-materials, source-clrs]
contexts: [workspace-algo2-exam-prep]
---

> **Build note (2026-08-16).** Operator-drafted from `ad2_amortizedanalysis.pdf`
> (40 sl.), page-anchored. Companions: `note-algo2-amortized-analysis-exercise-bank`,
> `note-algo2-amortized-analysis-viva-drill`. Not yet worked by Aram.

# Algo 2 · Topic 2 — Amortisierte Analyse

*Lectures: 20. April `[1-19]`, 22. April `[20-end]`. **Literatur:** CLRS Kap. 17,
speziell 17.1–17.3. **Leseaufgabe:** 17.4 "Dynamische Tabellen".*

**Agenda (sl. 2):** what amortized analysis is for · when it pays · the three
standard methods (Aggregat-Analyse, Account-Methode, Potentialmethode) · what
amortized costs mean.

> 🔑 **The load-bearing topic of the course.** Fibonacci heaps (T04) and splay
> trees (T05) both list amortized analysis on *their* slide 2 as assumed. Their
> headline bounds are amortized, not worst-case. **Do this one properly or the
> next two collapse.**

---

## 1. Why analyse data structures this way (sl. 3–5)

For an algorithm we want a good upper bound on running time. That usually depends
on the data structure, and the cost that matters is the **total cost `c(Q)` of a
sequence** `Q = ⟨q₁, …, q_m⟩` of operations.

**Goal (sl. 4):** a good upper bound on `c(Q)` for *arbitrary* sequences,
depending only on `m` and the number `n` of distinct elements.

**Observation:** summing per-operation worst cases gives *a* bound — but often a
badly pessimistic one, because the expensive operations cannot all happen.

> **Amortized analysis (sl. 5)** gives an upper bound on whole sequences that can
> be *substantially* lower than the sum of individual worst cases, and yields
> **amortized costs per operation type** — which is what lets you compare data
> structures.

---

## 2. The three methods (sl. 6)

| Method | What you do | Character |
|---|---|---|
| **Aggregat-Analyse** | Prove a bound `T(m)` for `m` operations directly; amortized cost ≤ `T(m)/m` | Elegant when it works; too hard for complex structures |
| **Account-Methode** | Assign *fictitious* costs; the account (difference) must never go negative | More powerful; needs a good choice of fictitious costs |
| **Potentialmethode** | Define a potential function on states; amortized cost = actual + potential change | Most powerful; the one Fibonacci heaps and splay trees use |

**Two running examples are used throughout, for all three methods** — the
multipop stack and the `k`-bit binary counter. Learning the same two examples
three ways is the deck's design, and it is also the fastest route to fluency.

---

## 3. Aggregate analysis (sl. 8–13)

Prove a global bound directly, without amortized costs or potentials.

### Example I — stack with multipop (sl. 9–10)

Operations `push(S,x)`, `pop(S)`, and `multipop(S,k)`: remove the top `k`
objects, or empty the stack if it holds fewer.

Worst case for a single `multipop` is `Θ(n)` — so the naive bound over `m`
operations is `O(m²)`.

**Aggregate argument:** `push` and `pop` cost `Θ(1)`. `multipop(S,k)` costs
`Θ(1)` plus some number `ℓ ≤ k` of pops on a non-empty stack. **Every such pop
must be preceded by a push of that element.** There are at most `m` pushes, hence
at most `m` such pops in total.

> **Total: `O(m)`. Amortized `O(1)` per operation.**

### Example II — `k`-bit binary counter (sl. 11–12)

A `k`-bit counter `A` starting at 0 is incremented `m` times. Per operation
`O(k)` because of carries, worst case `Θ(k)` — naive bound `O(mk)`.

**Aggregate argument:** `A[0]` flips on every call; `A[1]` on every second; in
general `A[i]` flips on every `2^i`-th call, and bits `A[i]` with `i ≥ k` do not
exist. Total flips:

$$\sum_{i=0}^{k-1}\left\lfloor \frac{m}{2^i}\right\rfloor < m\sum_{i=0}^{\infty}\frac{1}{2^i} = 2m$$

> **Total `O(m)`, amortized `O(1)` per increment** — independent of `k`.

**Summary (sl. 13).** Direct, no potential function or fictitious costs; short and
elegant when it works, e.g. for a known fixed sequence of simple operations; also
good when the cost of expensive operations is easy to predict.

---

## 4. The accounting method (sl. 15–23)

Assign **fictitious costs** `d(qᵢ)` that may lie above or below the actual costs
`c(qᵢ)`. The difference is paid into or out of an **account which must never go
negative**.

**What to do:** define the fictitious costs, then prove `d(Q) ≥ c(Q)` for all
sequences `Q`.

**How to prove it (sl. 17).** A direct proof for arbitrary `Q` is often hard —
and if it were easy you would have used aggregate analysis. So: **induction over
`m`.**

### Example I — the stack (sl. 18–21)

| Operation | actual `c` | fictitious `d` |
|---|---|---|
| `push(S,x)` | 1 | **2** |
| `pop(S)` | 1 | 1 |
| `multipop(S,k)` | `min{k, |S|+1}` | 1 |

> ⚠️ **"Achtung: Hier weichen wir vom Buch ab"** (sl. 18) — the deck's fictitious
> costs differ from CLRS. **Use the deck's.** If you quote CLRS's numbers to this
> examiner you are answering a different question.

**Sl. 19 is a `Fehlversuch`** — a deliberately failed induction. The naive
hypothesis `d(Q) ≥ c(Q)` does not carry through.

**The fix (sl. 20):** strengthen the hypothesis to

$$d(Q) \ge c(Q) + |S|$$

for every sequence `Q` of length `m`. Base case `m = 0`, `Q = ⟨⟩`, trivially
holds. The extra `|S|` is exactly the credit sitting on the stack.

> 🎯 **The failed attempt is pedagogically the most valuable slide in the deck.**
> An examiner who asks "und warum reicht die naive Induktionshypothese nicht?"
> is asking about sl. 19. Know it as a *result*, not an accident.

### Example II — the counter (sl. 22)

`c(increment) = j`, the number of bits flipped; `d(increment) = 2`. A sequence of
`m` increments has fictitious cost `O(m)`.

**Intuition:** pay 2 when setting a bit to 1 — one for the flip, one saved to pay
for flipping it back to 0 later. Each bit is cleared at most once per set.

**Summary (sl. 23).** Decisive is that the account `d(Q) − c(Q) ≥ 0`. Much more
powerful than aggregate analysis; easy to compute sequence costs once the
fictitious costs are fixed.

---

## 5. The potential method (sl. 25–36)

Define a **potential function** assigning a value to the current *state* of the
data structure. The amortized cost of an operation is its actual cost **plus the
change in potential**.

**Setup (sl. 26).** `D` is the structure; `D₀` is empty; `Dᵢ` is the state after
operation `i`.

> **Amortized cost (sl. 27).** If `q` takes the structure from `D′` to `D″` with
> actual cost `c(q)`:
> $$d(q) := c(q) + \Phi(D'') - \Phi(D')$$

**Why this makes sense (sl. 28).** Potential can *fall*, so amortized cost can be
**lower** than actual cost — which is the entire purpose. Expensive operations
are paid for by potential built up earlier.

> **Theorem (sl. 29).** For any potential `Φ` with `Φ(D₀) = 0` and `Φ(Dᵢ) ≥ 0`
> for all `i`:
> $$d(Q) \ge c(Q) \quad \text{for all sequences } Q.$$
> The sum of amortized costs is an upper bound on the actual costs.

**What it buys:** you only need **one** function, and then every bound follows
automatically.

### The two examples again (sl. 30–34)

**Stack:** `Φ(S)` = number of elements. `Φ(S₀) = 0`, `Φ ≥ 0`. Then

- `d(push) = 1 + 1 = 2`
- `d(pop) ≤ 1 − 1 = 0`, bounded by 1
- `d(multipop) ≤ 1` — the `ℓ` pops cost `ℓ` but drop the potential by `ℓ`

**Counter:** `Φ(A)` = number of ones in `A`. `Φ(A₀) = 0`. An increment flipping
`j` bits clears `j−1` ones and sets one → potential change `−(j−1) + 1 = 2 − j`,
so `d(increment) = j + 2 − j = 2`.

### The requirement, examined (sl. 36)

Since `d(Q) = Φ(D_m) − Φ(D₀) + c(Q)`, we get `d(Q) ≥ c(Q)` **exactly when
`Φ(D_m) ≥ Φ(D₀)`**. The usual conditions `Φ(D₀) = 0` and `Φ(Dᵢ) ≥ 0` are the
convenient *sufficient* version, because they work for **all** sequences at once.

> 🎯 This distinction — necessary vs. sufficient condition on `Φ` — is the
> deepest point in the lecture and a natural "and why exactly?" follow-up.

---

## 6. Überblick and Ausblick (sl. 38–40)

**Überblick.** Amortized analysis serves primarily to analyse data structures;
often yields better bounds for operation sequences than the sum of worst cases;
three methods, increasing in power and in setup cost.

**Ausblick (sl. 39).** Best-known applications: **Fibonacci heaps** (T04),
**Union-Find** (disjoint sets — *not* a lecture topic here), **splay trees**
(T05).

**Aufgabe (sl. 40).** Aggregate analysis for **dynamic arrays**: simulate a
growing array in a static one; when full, allocate double the size and copy
everything. This is the `Leseaufgabe` CLRS 17.4 and it is the classic exam
question — **do it.**

---

## 7. Exam-critical minimum

| Must be automatic | Where |
|---|---|
| Why sum-of-worst-cases is too pessimistic | sl. 4 |
| All three methods, named, with their trade-off | sl. 6, 13, 23, 35 |
| Stack multipop: aggregate argument in one sentence | sl. 10 |
| Counter: the `Σ m/2^i < 2m` computation | sl. 12 |
| The deck's fictitious costs 2/1/1 — **not CLRS's** | sl. 18 |
| The strengthened induction hypothesis `d(Q) ≥ c(Q) + |S|` | sl. 20 |
| `d(q) = c(q) + Φ(D″) − Φ(D′)` | sl. 27 |
| The theorem and its two conditions on `Φ` | sl. 29 |
| Both potential functions (stack size; number of ones) | sl. 30, 33 |
| `Φ(D_m) ≥ Φ(D₀)` is the *real* condition | sl. 36 |
| Dynamic arrays | sl. 40 |

**Traps:** calling splay-tree/Fibonacci bounds worst-case (they are amortized);
quoting CLRS's stack costs instead of the deck's; stating the `Φ` conditions
without knowing they are sufficient rather than necessary; forgetting that
amortized analysis is **deterministic** — it is not average-case over random
inputs, and confusing the two is the single most common error in this material.
