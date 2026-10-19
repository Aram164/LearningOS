---
id: note-algo2-shortest-paths-viva-drill
type: note
title: "Algo 2 T07 — Viva Drill: Kürzeste Wege"
created: "2026-08-16"
role: mock-exam
state: evolving
authorship: operator-drafted
concepts: [concept-shortest-paths, concept-graph-basics]
sources: [source-algo2-hu-materials]
contexts: [workspace-algo2-exam-prep]
---

> **Build note (2026-08-16).** Operator-drafted from `ad2_shortestpaths.pdf`.
> `role: mock-exam` is the schema's nearest value; **this is an oral drill.**
> Unverified by Aram.

# Algo 2 · Topic 7 — Viva Drill

---

## A. The five-minute summary

1. **Frame it as "what breaks with negative weights."** Dijkstra handles the
   non-negative case (AlgoDat I); everything new here exists because of negative
   edges.
2. Distances: `δ` can be `∞` or `−∞`; shortest walks can be taken to be paths.
3. The shared machinery: optimal substructure, `π`-pointers, **relaxation**.
4. Bellman-Ford: `n−1` passes over all edges, `Θ(nm)`, plus a detection pass.
5. Why `n−1`: a shortest path has ≤ `n−1` edges, and each pass extends every
   traced walk by one edge.
6. Negative-cycle detection, by telescoping around the cycle.
7. All-pairs: **reweighting** makes weights non-negative without changing which
   paths are shortest — then `n ×` Dijkstra. That is Johnson.

---

## B. Follow-up trees

**B1. "Warum reicht Dijkstra nicht?"**
- → "Konstruieren Sie ein Gegenbeispiel." ⚠️ *have a 4-vertex one ready*
- → "Was genau geht kaputt?" → a finished vertex can later be improved
- → "Und wenn ich zu allen Gewichten eine Konstante addiere?" ⚠️ → **doesn't work**
  — it penalizes long paths more than short ones and changes which path is
  shortest. This is exactly why Johnson's reweighting is *per-vertex*, not global

**B2. "Erklären Sie Bellman-Ford."**
- → "Wie viele Iterationen?" → `n−1`, plus one detection pass
- → "Warum genau `n−1`?" → a shortest path has ≤ `n−1` edges
- → "Laufzeit?" → `Θ(nm)`
- → "Wie erkennen Sie negative Kreise?" → one more pass; if anything still relaxes,
  report `false`
- → "Beweisen Sie das." → telescoping sum around the cycle gives `0 ≤ (negative)`

**B3. "Was ist Relaxation?"**
- → write it
- → "Welche Invariante gilt dabei?" → `d[v] ≥ δ(s,v)` always
- → "Was ist optimale Teilstruktur?"
- → "Wozu die `π`-Zeiger?" → implicit shortest-path tree

**B4. "Wie lösen Sie All-Pairs mit negativen Gewichten?"**
- → "Warum nicht einfach `n`-mal Bellman-Ford?" → `Θ(n²m)`, worse
- → "Was macht Johnson?" → reweight to non-negative, then `n ×` Dijkstra
- → "Schreiben Sie die Umgewichtung auf." → `ŵ(u,v) = w(u,v) + h(u) − h(v)`
- → "Warum ändert das die kürzesten Wege nicht?" → the `h`-terms telescope; the
  offset depends only on the endpoints
- → "Was passiert mit Kreisen?" ⚠️ → **unchanged** — which is why a negative cycle
  cannot be reweighted away
- → "Wie wählen Sie `h`?" → new vertex `s`, 0-weight edges, Bellman-Ford,
  `h(v) = δ(s,v)`
- → "Warum ist `ŵ` dann nicht-negativ?" → `δ(s,v) ≤ δ(s,u) + w(u,v)`
- → "Gesamtlaufzeit?" → `Θ(nm)` + `n ×` Dijkstra

---

## C. Board work

| # | Draw / write while talking | Target |
|---|---|---|
| C1 | A 4-vertex counterexample for Dijkstra with a negative edge | 45 s |
| C2 | The relaxation step | 15 s |
| C3 | Bellman-Ford, full pseudocode | 45 s |
| C4 | The telescoping detection proof | 60 s |
| C5 | `ŵ(u,v) = w(u,v) + h(u) − h(v)` and the walk telescoping | 45 s |
| C6 | The `G′` construction with the new source | 30 s |

---

## D. Traps

**D1.** *"Man kann negative Gewichte doch einfach durch Addition einer Konstanten
loswerden?"* — **No**, and this is the best trap in the topic. A global shift adds
`c` per *edge*, so it penalizes paths with more edges and can change which path is
shortest. Johnson's reweighting is per-**vertex** and telescopes, which is exactly
why it works. If you can articulate that contrast, you've shown you understand
Johnson rather than memorized it.

**D2.** *"Bellman-Ford macht `n` Iterationen?"* — `n−1`, then a separate detection
pass.

**D3.** *"Ein kürzester Weg kann Knoten wiederholen?"* — Only if the repetition
lies on a zero-length cycle; a shortest **path** always exists when a shortest
walk does.

**D4.** *"`δ(u,v)` ist immer eine Zahl?"* — `∞` (unreachable) and `−∞` (negative
cycle en route) are both legitimate values.

**D5.** *"Umgewichten könnte auch negative Kreise beseitigen?"* — No. Cycle lengths
are invariant under reweighting. That invariance is a *feature*: it means Johnson
cannot accidentally hide an ill-posed instance.

**D6.** *"Dijkstra ist doch Stoff dieser Vorlesung?"* — It is assumed from
AlgoDat I (the deck says so explicitly). Know it cold anyway — it is called as a
subroutine by Johnson.

---

## E. Two-minute version

> "Neu ist hier eigentlich nur der Umgang mit negativen Kantengewichten —
> Dijkstra löst den nicht-negativen Fall bereits. Alle Verfahren beruhen auf
> Relaxation: man hält obere Schranken `d[v]` für `δ(s,v)` und verbessert sie
> entlang von Kanten. Bellman-Ford relaxiert `n−1` mal alle Kanten — das genügt,
> weil ein kürzester Pfad höchstens `n−1` Kanten hat — und läuft in `Θ(nm)`. Ein
> zusätzlicher Durchlauf erkennt erreichbare negative Kreise: relaxiert dann noch
> etwas, gibt es einen; der Beweis summiert die Ungleichungen um den Kreis, die
> `d`-Terme heben sich weg und man erhält `0 ≤` etwas Negatives. Für alle
> Knotenpaare nutzt Johnson eine Umgewichtung `ŵ(u,v) = w(u,v) + h(u) − h(v)`:
> entlang eines Weges teleskopieren die `h`-Terme, sodass sich nur ein von den
> Endknoten abhängiger Offset ergibt — kürzeste Wege bleiben also kürzeste Wege,
> und Kreislängen ändern sich gar nicht. Mit `h(v) = δ(s,v)`, berechnet per
> Bellman-Ford von einem neuen Knoten mit 0-Kanten, wird `ŵ` nicht-negativ, und
> man kann `n`-mal Dijkstra laufen lassen."

**~85 seconds.**
