---
id: note-algo2-cuckoo-hashing-viva-drill
type: note
title: "Algo 2 T06 — Viva Drill: Cuckoo Hashing"
created: "2026-08-16"
role: mock-exam
state: evolving
authorship: operator-drafted
concepts: [concept-cuckoo-hashing, concept-hashing-chaining, concept-expected-value]
sources: [source-algo2-hu-materials]
contexts: [workspace-algo2-exam-prep]
---

> **Build note (2026-08-16).** Operator-drafted from `ad2_hashing.pdf`.
> `role: mock-exam` is the schema's nearest value; **this is an oral drill.**
> Unverified by Aram.

# Algo 2 · Topic 6 — Viva Drill

> 🔑 **The precision topic.** Three different kinds of guarantee appear in this
> one lecture — worst case, expected, and amortized expected. An examiner
> probing whether you know the difference is probing here.

---

## A. The five-minute summary

1. Hash tables are the efficient dictionary if you give up ordered operations;
   randomization means **expected** runtimes.
2. Chaining works and has constant expected bucket size — but **cannot guarantee**
   constant access, and probing degrades under deletion.
3. The idea: **two hash functions, two permitted positions**.
4. Consequence: **`search` and `delete` are `O(1) worst case`.** Lead with this.
5. Insert evicts like a cuckoo; the chain is a walk in the **cuckoo graph**; the
   path lemma gives expected `O(1)`.
6. Rehashing: cycle probability `≤ 1/2` for `c ≥ 3`; costs `O(n)` but happens with
   probability `O(1/r)`, so contributes `O(1)`.
7. Dynamic version: **amortized expected** `O(1)` for insert/delete.

---

## B. Follow-up trees

**B1. "Was ist die Idee beim Cuckoo Hashing?"**
- → "Warum genau zwei Positionen?"
- → "Was gewinnen Sie dadurch?" ⚠️ → **worst-case** `O(1)` lookup
- → "Was verlieren Sie?" → insert becomes complicated and only expected `O(1)`
- → "Warum reicht Chaining nicht?" → no guarantee; probing degrades on delete

**B2. "Wie fügt man ein?"**
- → "Und wenn beide Positionen belegt sind?" → evict, the occupant moves to *its*
  other position
- → "Wann bricht die Schleife ab?" → after a bounded number of steps → rehash
- → "Warum ist die Schleife überhaupt beschränkt?" → to detect the cyclic case

**B3. "Wie analysieren Sie insert?"**
- → "Was ist der Cuckoo-Graph?" → cells are vertices, each key an edge between its
  two positions
- → "Was entspricht einer Verdrängungskette?" → a walk in that graph
- → "Nennen Sie das Lemma." → `P[i,j`-path of length `ℓ] ≤ c^{−ℓ}/r` for `r ≥ 2cn`
- → "Und wie folgt daraus `O(1)`?" → geometric series over `ℓ`
- → "Wo brauchen Sie `r ≥ 2cn`?" ⚠️ *the load condition is load-bearing*

**B4. "Und wenn ein Rehashing nötig wird? Das kostet doch `O(n)`."**
- *This is the deck's own posed objection (sl. 32) — expect it.*
- → "Wie wahrscheinlich ist es?" → `O(1/r)` at a given insert
- → "Also?" → `O(1/r) · O(n) = O(n/r) = O(1)` since `r ≥ 2cn`
- → "Wann scheitert ein Rehashing?" → when the cuckoo graph has a cycle
- → "Wie wahrscheinlich ist das?" → `≤ 1/2` for `c ≥ 3` → expected ≤ 2 attempts

**B5. "Welche Garantien haben Sie jetzt genau?"** ⚠️ *the precision question*
- → `search`: worst case `O(1)`
- → `delete`: worst case `O(1)`
- → `insert`: **expected** `O(1)`
- → dynamic `insert`/`delete`: **amortized expected** `O(1)`
- → "Was bedeutet 'amortisiert erwartet'?" → amortized over the resizes, expected
  over the random hash functions
- → "Ist das dasselbe wie bei Fibonacci-Heaps?" → **No.** Those are amortized and
  fully deterministic; no probability anywhere.

---

## C. Board work

| # | Draw / write while talking | Target |
|---|---|---|
| C1 | Two-cell lookup — why worst-case `O(1)` | 20 s |
| C2 | The insert loop | 45 s |
| C3 | An eviction chain over a small table | 90 s |
| C4 | The cuckoo graph for 4 keys, 6 cells | 45 s |
| C5 | The path lemma and the geometric sum | 60 s |
| C6 | The rehash cost argument `O(1/r)·O(n)` | 30 s |

---

## D. Traps

**D1.** *"Suchen ist erwartet `O(1)`?"* — **Worst case.** This is the entire
selling point of the scheme; conceding "expected" throws the topic away.

**D2.** *"Amortisiert und erwartet — ist das nicht dasselbe?"* — No. Amortized:
deterministic, over a sequence. Expected: probabilistic, over the hash functions.
This course teaches both and cuckoo hashing's dynamic variant needs **both words
at once**.

**D3.** *"Die Tabelle kann also voll werden?"* — The analysis requires
`r ≥ 2cn`, i.e. the table is kept at constant slack. Without it, nothing holds.

**D4.** *"Einfügen ist im Worstcase auch `O(1)`?"* — No. Worst case it triggers a
rehash costing `O(n)`. Only the *expectation* is constant.

**D5.** *"Warum überhaupt zwei Hashfunktionen und nicht drei?"* — Fine to say the
deck stops at two, `d`-ary variants exist and are out of scope. Do not improvise
their analysis.

**D6.** *"Ihre Analyse setzt perfekte Zufälligkeit voraus?"* — Yes, and the deck's
own Ausblick names that as the open question: what should good hash functions look
like. Saying this unprompted is a strong finish.

---

## E. Two-minute version

> "Hashtabellen sind die effizienteste Umsetzung des ADT Dictionary, wenn man auf
> geordnete Operationen verzichtet — allerdings bekommt man wegen der
> Randomisierung nur Erwartungswerte. Chaining hat konstante erwartete
> Bucket-Größe, kann aber keine konstante Zugriffszeit garantieren, und lineares
> Sondieren verschlechtert sich beim Löschen. Cuckoo Hashing nutzt zwei
> Hashfunktionen: jeder Schlüssel darf nur an den zwei Positionen `h₁(x)` und
> `h₂(x)` liegen. Dadurch sind Suchen und Löschen im **Worstcase** `O(1)` — man
> prüft zwei Zellen. Beim Einfügen verdrängt man wie der Kuckuck den bisherigen
> Bewohner, der dann auf seine andere Position ausweicht. Die Verdrängungskette
> ist ein Weg im Cuckoo-Graphen; ein Lemma beschränkt die Wahrscheinlichkeit
> langer Wege, woraus erwartet `O(1)` folgt, solange `r ≥ 2cn`. Klappt es nicht,
> wird rehasht — das kostet `O(n)`, passiert aber nur mit Wahrscheinlichkeit
> `O(1/r)`, trägt also `O(1)` bei. Dynamisch bekommt man amortisiert erwartet
> `O(1)` für Einfügen und Löschen, Suchen bleibt Worstcase `O(1)`."

**~85 seconds.**
