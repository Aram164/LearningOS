---
id: note-algo2-maximum-flow-viva-drill
type: note
title: "Algo 2 T08 — Viva Drill: Maximaler Fluss"
created: "2026-08-16"
role: mock-exam
state: evolving
authorship: operator-drafted
concepts: [concept-max-flow, concept-graph-basics]
sources: [source-algo2-hu-materials]
contexts: [workspace-algo2-exam-prep]
---

> **Build note (2026-08-16).** Operator-drafted from `ad2_maximumflow.pdf`.
> `role: mock-exam` is the schema's nearest value; **this is an oral drill.**
> Unverified by Aram.

# Algo 2 · Topic 8 — Viva Drill

> 🔑 **Four lecture sessions — the largest topic.** Also the one with a genuine
> *theorem* at its centre (max-flow min-cut), which makes it attractive to
> examiners who want to see whether you can prove something.

---

## A. The five-minute summary

1. Flow network, flow (two constraints), value.
2. The naive greedy and **why it fails** — you cannot take back a bad decision.
3. The residual network, **especially the backward edges**, which restore that
   ability.
4. Ford-Fulkerson; terminates with integer capacities; `O(F·m)` is **not**
   polynomial.
5. Edmonds-Karp: shortest augmenting path by BFS → `O(|V|·|A|²)`, independent of
   capacities.
6. Cuts give upper bounds; the three equivalences; **max-flow min-cut**.
7. One line on variants: matchings, disjoint paths, vertex capacities, Menger.

---

## B. Follow-up trees

**B1. "Was ist ein Fluss?"**
- → "Welche zwei Bedingungen?" → capacity, conservation
- → "Wie ist der Wert definiert?" → net outflow from `s`
- → "Warum ist das wohldefiniert — könnte man ihn nicht auch bei `t` messen?"

**B2. "Warum reicht ein Greedy-Algorithmus nicht?"** ⚠️ *the pivotal question*
- → "Zeichnen Sie ein Beispiel." *have one ready*
- → "Was fehlt dem Algorithmus?" → the ability to undo
- → "Wie repariert das Residualnetzwerk das?" → backward edges of capacity `f(a)`
- → "Wie sieht die Aktualisierung entlang eines Pfades aus?"

**B3. "Ford-Fulkerson — Laufzeit?"**
- → `O(F·m)` with integer capacities
- → "Ist das polynomiell?" ⚠️ → **No** — `F` can be exponential in the bit length
- → "Und mit irrationalen Kapazitäten?" → may not terminate at all
- → "Wie behebt Edmonds-Karp das?" → always take a shortest residual path
- → "Warum hilft das?" → residual distances increase monotonically
- → "Wie viele Iterationen?" → `O(|V|·|A|)`; each edge critical ≤ `|V|/2` times
- → "Gesamtlaufzeit?" → `O(|V|·|A|²)`, capacity-independent

**B4. "Was ist ein Schnitt?"**
- → "Zeigen Sie `|f| ≤ c(S,T)`."
- → "Nennen Sie die drei äquivalenten Aussagen."
- → "Beweisen Sie (2) ⇒ (3)." ⚠️ *the construction: `S` = reachable from `s` in `G_f`*
- → "Warum gilt `f(a) = c(a)` für alle `a ∈ δ⁺(S)`?"
- → "Und daraus folgt Max-flow Min-cut?"

**B5. "Wie finden Sie einen minimalen Schnitt?"**
- → compute a max flow, then `S` = reachable from `s` in the residual network
- → "Warum ist das minimal?" → weak duality plus the equality just established

**B6. "Nennen Sie Anwendungen."**
- → edge-disjoint `s,t`-paths (unit capacities)
- → bipartite matching (T09)
- → undirected graphs; vertex capacities — and the four combinations
- → "Und Menger?" → both variants; separators via min cut

---

## C. Board work

| # | Draw / write while talking | Target |
|---|---|---|
| C1 | A network where naive greedy gets stuck | 60 s |
| C2 | The residual network of a given flow | 60 s |
| C3 | The `f′` update rule | 30 s |
| C4 | The `|f| ≤ c(S,T)` cancellation argument | 90 s |
| C5 | The `S` = reachable construction, showing saturation across the cut | 90 s |
| C6 | The vertex-splitting reduction `v⁻ → v⁺` | 30 s |

---

## D. Traps

**D1.** *"`O(F·m)` ist doch polynomiell?"* — **No.** `F` is a *value*, not an input
size; it can be exponential in the number of bits. This distinction between
*pseudo-polynomial* and polynomial is exactly why Edmonds-Karp exists.

**D2.** *"Das Residualnetzwerk enthält nur die Restkapazitäten?"* — It also has
**backward** edges with capacity `f(a)`. Omit them and you have described the
broken greedy.

**D3.** *"Max-flow Min-cut sagt, dass es einen Schnitt gibt?"* — It says the
**values are equal**, and the proof *constructs* the cut. Be ready to produce it.

**D4.** *"Ford-Fulkerson terminiert immer?"* — Only with integer (or rational)
capacities. With irrational ones it can run forever.

**D5.** *"Menger — das sind knotendisjunkte Pfade?"* — There are **two** versions,
vertex- and edge-disjoint, with different adjacency conditions on `s,t`. Name
which one you mean.

**D6.** *"Warum gerade kürzeste Wege bei Edmonds-Karp?"* — Because that is what
makes residual distances monotone, which is what bounds how often an edge can be
critical. Not an arbitrary tie-break.

---

## E. Two-minute version

> "Ein Flussnetzwerk ist ein gerichteter Graph mit Kapazitäten und zwei
> ausgezeichneten Knoten `s` und `t`. Ein Fluss erfüllt die Kapazitätsbedingung
> und die Flusserhaltung; sein Wert ist der Nettoausfluss aus `s`. Ein naiver
> Greedy-Algorithmus, der entlang beliebiger Pfade verstärkt, bleibt unter dem
> Optimum stecken, weil er getroffene Entscheidungen nicht zurücknehmen kann.
> Genau dafür gibt es das Residualnetzwerk: neben den Restkapazitäten enthält es
> **Rückwärtskanten** mit Kapazität `f(a)`. Ford-Fulkerson verstärkt entlang
> `s,t`-Pfaden im Residualnetzwerk; bei ganzzahligen Kapazitäten terminiert er in
> `O(F·m)` — das ist aber nicht polynomiell, weil `F` ein Wert und keine
> Eingabegröße ist. Edmonds-Karp wählt stets einen kürzesten Residualpfad per
> Breitensuche; dann wachsen die Abstände monoton, jede Kante wird höchstens
> `|V|/2`-mal kritisch, und man landet bei `O(|V|·|A|²)` unabhängig von den
> Kapazitäten. Schnitte liefern obere Schranken, und man zeigt: `f` maximal ⟺
> kein `s,t`-Pfad im Residualnetzwerk ⟺ es gibt einen Schnitt mit
> `|f| = c(S,T)`. Daraus folgt das Max-flow-Min-cut-Theorem, und man erhält den
> minimalen Schnitt als die von `s` im Residualnetzwerk erreichbare Knotenmenge."

**~100 seconds** — the longest of the set, and appropriate for a four-session
topic.
