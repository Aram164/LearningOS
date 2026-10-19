---
id: note-algo2-fast-multiplication
type: note
title: "Algo 2 T01 — Reference: Schnellere Multiplikation (Karatsuba)"
created: "2026-08-16"
role: reference
state: evolving
authorship: operator-drafted
concepts: [concept-fast-multiplication, concept-recurrences-master-theorem,
  concept-asymptotic-analysis]
sources: [source-algo2-hu-materials, source-dms-grundwerkzeuge]
contexts: [workspace-algo2-exam-prep]
---

> **Build note (2026-08-16).** Operator-drafted from `ad2_fastmultiplication.pdf`
> (31 sl.), page-anchored. Companions: `note-algo2-fast-multiplication-exercise-bank`,
> `note-algo2-fast-multiplication-viva-drill`. Not yet worked by Aram.

# Algo 2 · Topic 1 — Schnellere Multiplikation

*Lecture: 13. April, whole deck `[*]`. **Literatur:** DMS Kap. 1 — Leseaufgabe:
read the chapter **completely, including material not discussed.** The authors
call it the "Vorspeise" of their book.*

**Agenda (sl. 2):** Zahlendarstellung und Addition · Die Schulmethode · eine
rekursive Version der Schulmethode · Karatsuba-Multiplikation · Erinnerung:
Mastertheorem.

> 🎯 **Why this is lecture 1.** It is the whole course in miniature: take a
> problem you think is solved, count operations honestly, find a recurrence,
> improve the *branching factor*, re-solve. Every later topic is a variation on
> that move.

---

## 1. Number representation and addition (sl. 3–10)

Numbers to base `B`: `a = (a_{n−1} … a_0)`, digits `a_i ∈ {0,…,B−1}`.

**Addition of two `n`-digit numbers costs `n` elementary operations.** This is
the baseline everything is measured against, and it is why the addition count in
Karatsuba turns out not to matter.

**Multiplication by a single digit (sl. 9–10).** Multiplying `a` by one digit
`b_j`: for each `i`, one elementary operation gives `a_i · b_j = c_i·B + d_i`;
adding the `c` and `d` rows costs a further `n`. So roughly `2n` per digit.

---

## 2. The school method (sl. 12–14)

Form partial products `q_j = a · b_j`, shift by `B^j`, sum:

```
Input : a = (a_{n−1}…a_0), b = (b_{n−1}…b_0)
Output: p = a · b
1  p ← 0
2  for j = 0 to n−1 do
3      p ← p + a · b_j · B^j
```

> **Satz (sl. 14).** The school method computes the product of two `n`-digit
> naturals with **fewer than `3n²` elementary operations.**

And — the half people forget — it also does **not** use essentially fewer than
`3n²`. The bound is tight, so beating it requires a different algorithm, not a
better implementation.

---

## 3. A recursive version of the school method (sl. 16–18)

Divide and conquer. With `k = ⌊n/2⌋`, split both numbers:

$$a = a_1 B^k + a_0, \qquad b = b_1 B^k + b_0$$

where `a_0, a_1, b_0, b_1` are `⌈n/2⌉`-**digit numbers** (not single digits —
the deck flags this explicitly). Then directly:

$$a \cdot b = a_1b_1 B^{2k} + (a_1b_0 + a_0b_1)B^{k} + a_0b_0$$

**Four** multiplications of half-length numbers, plus additions and shifts.

> **Recurrence (sl. 23).**
> $$T(n) \le \begin{cases} 1 & n = 1 \\ 4\,T(\lceil n/2\rceil) + 4n & n \ge 2\end{cases}$$

This is *"im Wesentlichen genauso schnell/langsam"* as the school method (sl. 16)
— `Θ(n²)` again. The recursion bought nothing **yet**. That is the setup.

---

## 4. Karatsuba (sl. 20–24)

**Observation:** a simple modification lets you use only **three** multiplications
of half-length numbers.

$$a \cdot b = a_1b_1 B^{2k} + \Big((a_1{+}a_0)(b_1{+}b_0) - (a_1b_1 + a_0b_0)\Big)B^k + a_0b_0$$

**Counting (sl. 21–22).** At first glance five multiplications — but `a_0b_0` and
`a_1b_1` each appear **twice** and are computed once. So:

> **Three multiplications and six additions.**

**The additions make no asymptotic difference** (sl. 22): they are applied
directly and cost `O(n)`.

> **Recurrence (sl. 23).**
> $$T(n) \le \begin{cases} 3n^2 & n \le 3 \\ 3\,T(\lceil n/2\rceil + 1) + 8n & n \ge 4\end{cases}$$
>
> **"Entscheidend ist 3 vs. 4 als Faktor."** The linear term went *up* (4n → 8n)
> and the bound still improved. **This one sentence is the lecture.**

> **Satz (sl. 24).** For the Karatsuba algorithm on `n`-digit naturals,
> $$T(n) \le 153\, n^{\log_2 3} = O(n^{\log_2 3}) \quad \text{for all } n.$$

`log₂ 3 ≈ 1.585`. The constant `153` is large and honest — asymptotics win only
eventually.

---

## 5. Erinnerung: the master theorem (sl. 26–28)

Useful for the asymptotic analysis of divide-and-conquer algorithms; the deck
notes it is *"oft bereits in Pflichtvorlesungen … enthalten"* — hence
**Erinnerung**, and hence Phase 0.2.

> **Mastertheorem (sl. 27).** Let `a ≥ 1`, `b > 1`, and `d = log_b a`. Let `f(n)`
> be a function and `T(n)` defined over the non-negative integers by
> $$T(n) = a\,T(n/b) + f(n)$$
> where `n/b` means `⌊n/b⌋` or `⌈n/b⌉`. Then the three standard cases apply,
> comparing `f(n)` against `n^d`.

**Applied to Karatsuba (sl. 28).** One shows `T(n) = 3T(n/2) + n` has the same
asymptotic worst-case bound (and the `n ≤ 3` value is irrelevant). Then
`a = 3`, `b = 2`, so `d = log₂ 3`, and `f(n) = n` is polynomially smaller than
`n^{log₂ 3}` — giving `T(n) = Θ(n^{log₂ 3})`.

---

## 6. Überblick and Ausblick (sl. 30–31)

**Überblick.** Base-`B` representation · addition of `n`-digit numbers costs `n`
elementary operations · naive multiplication ≈ `3n²` · the naive method can also
be written recursively · Karatsuba reaches `O(n^{log₂ 3})`.

**Ausblick (sl. 31).** Split into `k ≥ 3` parts → **Toom-Cook / Toom-k**
multiplication [1963]. For `k = 3`: `O(n^{1.46})`. As `k` grows the asymptotic
bound improves, but the constants and the number of additions grow with it.

> 🔗 **The course returns here.** Topic 12 (FFT) closes on *"Schnelle
> Multiplikation von Polynomen und ganzen Zahlen"* — the same problem, attacked
> through polynomial evaluation, with a better bound. **Lecture 1 and lecture 12
> are bookends**, which is a gift for an oral: it lets you answer "what did this
> course do?" with one thread.

---

## 7. Exam-critical minimum

| Must be automatic | Where |
|---|---|
| School method `< 3n²`, and tight | sl. 14 |
| The split `a = a₁B^k + a₀` | sl. 17 |
| Karatsuba's identity, written from memory | sl. 21 |
| **3 vs 4 is the whole point** | sl. 23 |
| `O(n^{log₂ 3})`, and where `log₂ 3` comes from | sl. 24, 28 |
| Master theorem statement + Karatsuba application | sl. 27–28 |
| Toom-k as the generalization | sl. 31 |

**Traps:** claiming five multiplications (missing the reuse); saying the extra
additions cost something asymptotically; quoting `n^{1.585}` without being able
to produce `log₂ 3`; forgetting that the school-method bound is *tight*, which is
what makes the improvement meaningful.
