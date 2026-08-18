---
id: note-algo2-b-trees-viva-drill
type: note
title: "Algo 2 T03 — Viva Drill: B-Bäume"
created: "2026-08-16"
role: mock-exam
state: evolving
authorship: operator-drafted
concepts: [concept-b-trees, concept-adt-dictionary]
sources: [source-algo2-hu-materials]
contexts: [workspace-algo2-exam-prep]
---

> **Build note (2026-08-16).** Operator-drafted from `ad2_btrees.pdf`.
> `role: mock-exam` is the schema's nearest value; **this is an oral drill.**
> Unverified by Aram.

# Algo 2 · Topic 3 — Viva Drill

---

## A. The five-minute summary

*"Erzählen Sie mir von B-Bäumen."*

1. **The motivation first, always.** Large data lives on secondary storage; disk
   accesses dominate everything. A BST costs one access per level.
2. The fix: many keys per node, so one access fetches a whole page.
3. The definition: minimal degree `t`, `t−1` to `2t−1` keys, **all leaves at
   equal depth**.
4. The height theorem `h ≤ log_t((n+1)/2)` — **base `t`, and that is the point**.
5. Operations: search descends comparing within nodes; insert splits full nodes
   on the way down in one pass; the tree grows at the root.
6. Deletion is the hard one — the `≥ t` keys invariant and its cases.
7. One line: B⁺, B*, External Memory Algorithms.

**Self-check:** did you lead with the disk? Candidates who start from the
definition sound like they memorized a data structure; candidates who start from
the cost model sound like they understand why it exists.

---

## B. Follow-up trees

**B1. "Warum B-Bäume und nicht einfach balancierte Suchbäume?"**
- → "Was genau kostet ein Zugriff auf sekundären Speicher?"
- → "Wie viele Zugriffe braucht die Suche im binären Suchbaum?" → `≈ c log n`, one per level
- → "Und im B-Baum?" → `≤ h ≤ log_t((n+1)/2)`
  - → "Rechnen Sie es für `t = 100`, `n = 10⁹` vor." ⚠️ *have a number ready*
- → "Wie wählt man `t`?" → to match the page size of the storage device

**B2. "Definieren Sie einen B-Baum."**
- → "Warum müssen alle Blätter dieselbe Tiefe haben?"
- → "Warum mindestens `t−1` Schlüssel?"
- → "Was ist mit der Wurzel?" → ≥ 1 key if non-empty; the exception matters (sl. 15)
- → "Wie viele Kinder hat ein innerer Knoten mit `x.n` Schlüsseln?" → `x.n + 1`

**B3. "Beweisen Sie die Höhenschranke."**
- → "Wie viele Knoten hat Ebene `i` mindestens?" → `2t^{i−1}`
- → "Warum die 2?" → the root only forces two children, not `t`
- → "Und wie viele Schlüssel folgen daraus?" → `n ≥ 2t^h − 1`

**B4. "Wie fügt man ein?"**
- → "Was passiert, wenn ein Knoten voll ist?" → split
- → "Beschreiben Sie B-Tree-Split-Child." → median up, right half into `z`, `z.n = t−1`
- → "Warum spalten Sie auf dem Weg nach unten?" ⚠️ *the key design question* —
  so the parent is always non-full and no upward pass is needed
- → "Wie wächst der Baum in der Höhe?" → only at the root

**B5. "Und Löschen?"**
- → "Welche Invariante halten Sie ein?" → current node has ≥ `t` keys
- → "Warum reicht `t−1` nicht?" → then removing one would immediately underflow
- → "Nennen Sie die Fälle." → 1, 2a/2b/2c, 3
- → "Fall 2c — was passiert da genau?" → merge `y`, `k`, `z`; the only route to a shorter tree
- → "Welcher Fall tritt in der Praxis am häufigsten auf?" → the leaf case, since most keys are in leaves

**B6. "B⁺- und B*-Bäume?"**
- → "Wofür ist die Verkettung der Blätter im B⁺-Baum gut?" → range scans

---

## C. Board work

| # | Draw / write while talking | Target |
|---|---|---|
| C1 | A `t = 2` B-tree with ~10 keys | 45 s |
| C2 | A split, before and after | 45 s |
| C3 | The height theorem + proof skeleton | 60 s |
| C4 | The insert pass on a tree with a full root | 60 s |
| C5 | Case 2c merge, before and after | 45 s |

> ✍️ **Zoom-specific:** you cannot gesture at a shared board. Have paper ready and
> hold it up, or use a tablet — and **practise narrating a drawing you are making**,
> because silence while drawing reads as being stuck.

---

## D. Traps

**D1.** *"Die Höhe ist also `O(log n)`?"* — True but evasive. The content is
`log_t`, base `t`. Give the base or you have said nothing about B-trees.

**D2.** *"Ein B-Baum ist ein balancierter Binärbaum mit mehr Schlüsseln?"* — Not
binary; the branching factor is `t` to `2t`. Balanced, yes — by construction,
since all leaves are at equal depth.

**D3.** *"Beim Einfügen läuft man doch wieder hoch, um zu spalten?"* — That is the
naive version. This deck's design splits **downward** precisely so no upward pass
is needed. Say why.

**D4.** *"Die Invariante beim Löschen ist `t−1` Schlüssel?"* — No, `t`. One above
the minimum, so a key can be removed safely.

**D5.** *"Warum nicht einfach `t` riesig wählen?"* — Then the linear search
*inside* a node dominates: CPU is `O(t log_t n)`. `t` is tuned to the page size,
which is a hardware fact, not a free parameter.

---

## E. Two-minute version

> "Bei sehr großen Datenmengen liegt die Struktur auf sekundärem Speicher, und
> dort dominieren die Zugriffe alles andere. Ein binärer Suchbaum braucht pro
> Ebene einen Zugriff. B-Bäume speichern deshalb viele Schlüssel pro Knoten —
> ein Zugriff holt eine ganze Seite. Ein B-Baum mit Minimalgrad `t` hat pro
> Knoten zwischen `t−1` und `2t−1` Schlüssel, alle Blätter auf gleicher Tiefe,
> und Höhe `h ≤ log_t((n+1)/2)`. Die Suche kostet also höchstens `h`
> Plattenzugriffe. Eingefügt wird in einem einzigen Abwärtslauf: volle Knoten
> werden unterwegs gespalten, wobei der mittlere Schlüssel nach oben wandert —
> dadurch ist der Vater nie voll und man braucht keinen Rücklauf. Der Baum wächst
> nur an der Wurzel. Löschen ist komplizierter: man hält die Invariante, dass der
> aktuelle Knoten mindestens `t` Schlüssel hat, und unterscheidet Blatt, innerer
> Knoten mit `k`, und innerer Knoten ohne `k`."

**~70 seconds.**
