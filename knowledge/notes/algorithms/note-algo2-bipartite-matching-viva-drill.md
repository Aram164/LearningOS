---
id: note-algo2-bipartite-matching-viva-drill
type: note
title: "Algo 2 T09 — Viva Drill: Bipartites Matching"
created: "2026-08-16"
role: mock-exam
state: evolving
authorship: operator-drafted
concepts: [concept-bipartite-matching, concept-max-flow]
sources: [source-algo2-hu-materials]
contexts: [workspace-algo2-exam-prep]
---

> **Build note (2026-08-16).** Operator-drafted from `ad2_bipartitematching.pdf`.
> `role: mock-exam` is the schema's nearest value; **this is an oral drill.**
> Unverified by Aram.

# Algo 2 · Topic 9 — Viva Drill

---

## A. The five-minute summary

1. Motivating problems — dorm pairing (general graph), study places (bipartite,
   with capacities handled by duplication).
2. Matching; **maximal ≠ maximum**, and greedy only gives maximal.
3. Alternating and augmenting paths; `M △ E(P)` grows the matching by one.
4. **Berge's theorem**, and the characterization: maximum ⟺ no augmenting path.
5. Hopcroft-Karp: shortest augmenting-path lengths grow monotonically, so work in
   **phases** over maximal SAP-packings.
6. `O(√n)` phases; `O(m)` per phase via level-graph BFS + backward DFS;
   **`O(m√n)`**.
7. One line: it also reduces to max flow; general graphs need blossoms.

---

## B. Follow-up trees

**B1. "Was ist der Unterschied zwischen maximal und maximum?"** ⚠️ *classic opener*
- → "Geben Sie ein Beispiel." *(a path on 4 vertices: match the middle edge →
  maximal, size 1; the two outer edges → maximum, size 2)*
- → "Was liefert der naive Greedy?" → maximal only

**B2. "Was ist ein augmentierender Pfad?"**
- → "Und ein alternierender?"
- → "Was passiert beim Augmentieren?" → `M △ E(P)`, one edge more
- → "Warum ist das wieder ein Matching?"

**B3. "Nennen Sie den Satz von Berge."**
- → "Beweisen Sie ihn." → degrees ≤ 2 in `M △ M′` → components are paths and even
  cycles → surplus sits in `M′`-starting-and-ending paths
- → "Welche Charakterisierung folgt?" → maximum ⟺ no augmenting path
- → "Warum sind die Pfade knotendisjunkt?" → they are distinct components

**B4. "Wie funktioniert Hopcroft-Karp?"**
- → "Was ist ein SAP-Packing?" → vertex-disjoint shortest augmenting paths
- → "Warum in Phasen?" → shortest lengths grow strictly after a maximal packing
- → "Wie viele Phasen?" → `O(√n)`
- → "Beweisen Sie das." → after `√n` phases paths are longer than `√n`, so at most
  `√n` disjoint ones remain
- → "Ist das schon die Laufzeit?" ⚠️ **No** — sl. 38 explicitly warns; a phase must
  also be implemented in `O(m)`
- → "Wie sieht eine Phase aus?" → BFS level graph from the `M`-free vertices in
  `A`; backward DFS greedily picking disjoint paths
- → "Gesamtlaufzeit?" → `O(m√n)`

**B5. "Kann man Matching auch über Flüsse lösen?"**
- → build `s → A → B → t`, all capacities 1
- → "Warum entspricht ein ganzzahliger Fluss einem Matching?"
- → "Welche Laufzeit bekommen Sie so?" → via Edmonds-Karp; compare to `O(m√n)`
- → "Chen et al. 2022?" → `O(m^{1+o(1)})`, again via max flow

**B6. "Und in allgemeinen Graphen?"**
- → "Was bleibt gültig?" → Berge, and the monotone growth
- → "Was geht kaputt?" → odd cycles: **blossoms**
- → "Was macht Edmonds?" → contract blossoms, search, expand

---

## C. Board work

| # | Draw / write while talking | Target |
|---|---|---|
| C1 | Maximal-but-not-maximum, on a 4-path | 20 s |
| C2 | An augmenting path and the result of augmenting | 45 s |
| C3 | `M △ M′` with its path/cycle components | 90 s |
| C4 | A level graph with `F`, layers, and `R` | 60 s |
| C5 | The flow network for a bipartite instance | 45 s |
| C6 | A blossom | 30 s |

---

## D. Traps

**D1.** *"Ein maximales Matching ist doch das größte?"* — **No.** *Maximal* means
inextendable; *maximum* means largest. German usage invites the slip; be explicit.

**D2.** *"Hopcroft-Karp läuft in `O(√n)`?"* — That is the **phase count**. The
runtime is `O(m√n)`, and the deck itself flags the confusion on sl. 38.

**D3.** *"Der Satz von Berge sagt, dass es einen augmentierenden Pfad gibt?"* —
It says more: at least `|M′| − |M|` **vertex-disjoint** ones. The disjointness and
the count are what the `O(√n)` bound uses.

**D4.** *"Die Pfade im Packing müssen kantendisjunkt sein?"* — **Vertex**-disjoint,
so that all augmentations can be applied simultaneously without interfering.

**D5.** *"Hopcroft-Karp funktioniert auch für allgemeine Graphen?"* — No.
Blossoms — odd cycles — break the level-graph argument. That is exactly why
Edmonds' algorithm exists.

**D6.** *"Bipartites und stabiles Matching sind dasselbe?"* — Different problems,
taught back to back. This one **maximizes cardinality**; stable matching (T10)
optimizes for **stability against preferences** and is always perfect on a complete
instance.

---

## E. Two-minute version

> "Ein Matching ist eine Kantenmenge ohne gemeinsame Endknoten. Wichtig ist der
> Unterschied zwischen *maximal* — nicht erweiterbar — und *maximum* — größtmöglich;
> der naive Greedy liefert nur maximal. Der Schlüsselbegriff ist der
> augmentierende Pfad: ein alternierender Pfad, dessen beide Endknoten `M`-frei
> sind. Augmentiert man mit der symmetrischen Differenz, wächst das Matching um
> eins. Der Satz von Berge sagt: sind `|M| < |M′|`, so enthält `M △ M′`
> mindestens `|M′| − |M|` knotendisjunkte `M`-augmentierende Pfade — denn dort hat
> jeder Knoten Grad höchstens zwei, die Komponenten sind also Pfade und gerade
> Kreise. Daraus folgt: `M` ist maximum genau dann, wenn es keinen
> augmentierenden Pfad gibt. Hopcroft-Karp nutzt, dass die Länge kürzester
> augmentierender Pfade monoton wächst, und augmentiert phasenweise entlang eines
> maximalen Packings knotendisjunkter kürzester Pfade. Es genügen `O(√n)` Phasen,
> und eine Phase lässt sich in `O(m)` realisieren — Breitensuche für den
> Ebenengraph, dann Tiefensuche rückwärts. Insgesamt `O(m√n)`. Alternativ lässt
> sich das Problem auf maximalen Fluss reduzieren."

**~95 seconds.**
