---
id: note-algo2-fibonacci-heaps-viva-drill
type: note
title: "Algo 2 T04 — Viva Drill: Fibonacci-Heaps"
created: "2026-08-16"
role: mock-exam
state: evolving
authorship: operator-drafted
concepts: [concept-fibonacci-heaps, concept-adt-priority-queue, concept-amortized-analysis]
sources: [source-algo2-hu-materials]
contexts: [workspace-algo2-exam-prep]
---

> **Build note (2026-08-16).** Operator-drafted from `ad2_fibonacciheap.pdf`.
> `role: mock-exam` is the schema's nearest value; **this is an oral drill.**
> Unverified by Aram.

# Algo 2 · Topic 4 — Viva Drill

> 🔑 **Three lecture sessions, the longest topic in the course.** Expect the
> examiner to go deep here if they go deep anywhere.

---

## A. The five-minute summary

*"Was sind Fibonacci-Heaps und wozu?"*

1. Start from the **table**: binomial heaps are `O(log n)` everywhere; the
   expensive operation in practice is `decreasekey`, which Dijkstra and Prim call
   constantly.
2. The goal: `decreasekey` in amortized `O(1)`.
3. Why bubbling fails, and the answer: **cut into the root list**.
4. The cost of cutting: trees proliferate and shapes degrade — repaired by
   **marking** (cut on the *second* child loss) and by **lazy consolidation**
   during `extractmin`.
5. The potential `Φ = t + 2m`, with what each term pays for.
6. The bounds — amortized, **and say the worst case is `O(n)`**.
7. The degree bound `D(n) = O(log n)`, which is where the name comes from.

---

## B. Follow-up trees

**B1. "Warum Fibonacci-Heaps?"**
- → "Welche Operation wollen Sie verbessern?" → `decreasekey`
- → "Wer ruft die oft auf?" → Dijkstra, Prim
- → "Was kostet sie im Binomial-Heap?" → `O(log n)`
- → "Und was ist der Preis für die Verbesserung?" ⚠️ → the bounds become
  **amortized**; individual operations can be `O(n)`

**B2. "Wie erreichen Sie `decreasekey` in `O(1)`?"**
- → "Warum nicht nach oben tauschen?" → `Ω(m log n)` over `m` calls
- → "Was machen Sie stattdessen?" → cut `x` with its subtree into the root list
- → "Was ist dann kaputt?" → tree shapes degrade; degree bound at risk
- → "Wie reparieren Sie das?" → marking + cascading cuts
- → "Wann genau wird ein Knoten markiert?" ⚠️ → on losing its **first** child
- → "Und wann wird er selbst abgeschnitten?" → on losing a **second**

**B3. "Nennen Sie die Potentialfunktion."**
- → `Φ(H) = t(H) + 2m(H)`
- → "Wofür steht `t`?" → trees in the root list; pays for future consolidation
- → "Wofür die 2 bei `m`?" ⚠️ *the question* → one unit for the cut this mark
  promises, one for the mark that cut will place on its parent
- → "Rechnen Sie `decreasekey` vor." → actual `≤ βd + O(1)`, `ΔΦ ≤ −d + O(1)`,
  the `d` cancels → `O(1)`
- → "Was passiert mit Faktor 1 statt 2?" → the cancellation fails

**B4. "Erklären Sie extractmin."**
- → "Was passiert mit den Kindern des Minimums?" → into the root list
- → "Was ist Konsolidieren?" → combine equal degrees via `A[0..D(n)]`
- → "Wer wird Kind von wem?" → the larger key
- → "Wie viele Bäume bleiben?" → `O(log n)`
- → "Warum ist das amortisiert `O(log n)`?" → potential drops by ~`t(H)`

**B5. "Warum heißt das Fibonacci-Heap?"**
- → "Zeigen Sie die Gradschranke." → `grad[yᵢ] ≥ i−2` → `size(x) ≥ F_{k+2} ≥ φ^k`
- → "Warum `i−2` und nicht `i−1`?" ⚠️ → at linking time it was `i−1`; it may have
  lost **one** child since — a second loss would have removed it from `x`
- → "Und daraus folgt?" → `n ≥ φ^k`, so `k ≤ log_φ n`, `D(n) = O(log n)`
- → "Wo haben Sie diese Schranke vorher schon benutzt?" → in `extractmin`'s cost;
  §6 discharges an assumption made in §5

**B6. "Wie löschen Sie ein beliebiges Element?"**
- → `decreasekey(H,x,−∞)` then `extractmin` → `O(log n)` amortized
- → "Welche Annahme brauchen Sie?" → no other key equals `−∞`

---

## C. Board work

| # | Draw / write while talking | Target |
|---|---|---|
| C1 | The sl. 6 bound table, all four rows | 60 s |
| C2 | A root list with 4 trees, marks shown | 45 s |
| C3 | `Φ = t + 2m` and the two intuitions | 30 s |
| C4 | A cascading cut, before and after | 60 s |
| C5 | The `decreasekey` cost cancellation | 60 s |
| C6 | The chain `grad[yᵢ] ≥ i−2` → `size ≥ F_{k+2}` → `D(n) = O(log n)` | 90 s |

---

## D. Traps

**D1.** *"Fibonacci-Heaps sind also `O(1)` für decreasekey?"* — **Amortized**
`O(1)`. Worst case `O(n)`. Say both halves, every time; the deck's own table has
that row for a reason.

**D2.** *"Die Bäume sind Binomialbäume?"* — No: *unordered*, min-heap-ordered
trees. The looser structure is the entire design.

**D3.** *"Ein markierter Knoten wird sofort abgeschnitten?"* — No. Marked on the
**first** child loss; cut on the **second**.

**D4.** *"Wurzeln können markiert sein?"* — Never. Nodes are unmarked when they
enter the root list.

**D5.** *"Wenn Sie den Faktor 2 auf 1 senken — geht der Beweis noch?"* — No. The
mark must fund two things. Being able to say *why* the constant is 2 separates
understanding from recall.

**D6.** *"Fibonacci-Zahlen — weil die Bäume so aussehen?"* — No. They appear in
the **minimum subtree size** for a given degree, which is what bounds `D(n)`.

---

## E. Two-minute version

> "Binomial-Heaps schaffen alle Operationen in `O(log n)`. Teuer ist in der Praxis
> `decreasekey`, das Dijkstra und Prim ständig aufrufen. Fibonacci-Heaps senken
> das auf amortisiert `O(1)` — wichtig: amortisiert, im Worstcase kann eine
> einzelne Operation `O(n)` kosten. Die Idee: statt den Knoten nach oben zu
> tauschen, schneidet man ihn mit seinem Teilbaum ab und hängt ihn in die
> Wurzelliste. Damit die Baumstruktur nicht beliebig degeneriert, markiert man
> einen Knoten, wenn er sein erstes Kind verliert, und schneidet ihn selbst ab,
> wenn er ein zweites verliert — kaskadierende Schnitte. Aufgeräumt wird faul,
> erst beim `extractmin`, durch Konsolidieren gleicher Grade. Die Analyse läuft
> über das Potential `Φ = t + 2m`: `t` zahlt fürs spätere Konsolidieren, die 2 bei
> `m` für den späteren Schnitt und die Markierung beim Vater. Damit heben sich
> beim `decreasekey` die Kosten der Kaskade genau weg. Der Name kommt von der
> Gradschranke: ein Knoten vom Grad `k` hat mindestens `F_{k+2} ≥ φ^k` Knoten im
> Teilbaum, also ist der Maximalgrad `O(log n)`."

**~90 seconds** — longer than the other topics, and justified.
