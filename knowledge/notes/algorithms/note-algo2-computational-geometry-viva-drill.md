---
id: note-algo2-computational-geometry-viva-drill
type: note
title: "Algo 2 T11 — Viva Drill: Algorithmische Geometrie"
created: "2026-08-16"
role: mock-exam
state: evolving
authorship: operator-drafted
concepts: [concept-computational-geometry, concept-determinant-orientation]
sources: [source-algo2-hu-materials]
contexts: [workspace-algo2-exam-prep]
---

> **Build note (2026-08-16).** Operator-drafted from `ad2_computationalgeometry.pdf`.
> `role: mock-exam` is the schema's nearest value; **this is an oral drill.**
> Unverified by Aram.

# Algo 2 · Topic 11 — Viva Drill

> ✍️ **The most drawing-dependent topic.** On Zoom that is a real constraint —
> have paper or a tablet ready and practise **narrating while sketching**.

---

## A. The five-minute summary

1. The design principle first: geometric algorithms **avoid division and
   trigonometry**; orientation is decided by the **sign of a determinant**.
2. From that one primitive: turn direction, and segment intersection by
   straddling.
3. **Sweep line** — traverse the plane with a vertical line, keep only what it
   touches; finding an intersection reduces to testing newly adjacent pairs.
4. **Convex hull** — `Ω(n log n)` by reduction from sorting; Jarvis `O(nh)`,
   output-sensitive; Graham `O(n log n)`, optimal.
5. **Closest pair** — divide and conquer, the `2δ` strip, and the pre-sorting
   trick that turns `O(n log² n)` into `O(n log n)`.

---

## B. Follow-up trees

**B1. "Wie bestimmen Sie, ob ein Punkt links oder rechts einer Strecke liegt?"**
- → write the determinant
- → "Warum nicht über den Winkel?" ⚠️ → division and trigonometry: expensive and
  numerically awkward
- → "Was genau lesen Sie ab?" → **only the sign**
- → "Und relativ zu einem Punkt `p₀`?" → translate first
- → "Wie testen Sie, ob sich zwei Strecken schneiden?" → straddling via four
  orientation tests
- → "Und wenn eine Orientierung null ist?" → collinear; additionally check whether
  the point lies *within* the segment

**B2. "Erklären Sie die Sweep-Line-Methode."**
- → "Was sind die Ereignispunkte?" → the segment endpoints
- → "Was verwalten Sie in `T`?" → the segments cut by the line, ordered by `y`
- → "Warum genügt es, neu benachbarte Paare zu testen?" ⚠️ *the correctness
  question* → consider the **leftmost** intersection; the two segments meeting
  there must be adjacent just before it
- → "Was passiert mit der Ordnung beim Überqueren eines Schnittpunkts?" → it swaps

**B3. "Konvexe Hülle — welche Algorithmen kennen Sie?"**
- → Jarvis and Graham
- → "Laufzeiten?" → `O(nh)` and `O(n log n)`
- → "Wann ist Jarvis besser?" → small `h`; it is output-sensitive
- → "Warum ist Graham `O(n log n)` und nicht mehr?" → sorting dominates; the stack
  phase is `O(n)` since each point is pushed once and popped at most once
- → "Geht es schneller als `n log n`?" ⚠️ → **no**, in the usual models
- → "Warum nicht?" → reduction from sorting: hull vertices come out in angular
  order

**B4. "Dichtestes Punktepaar?"**
- → divide by `x`, recurse, `δ = min(δ_L, δ_R)`
- → "Was ist am Kombinationsschritt kritisch?" → pairs straddling the line
- → "Wie viele Punkte müssen Sie im Streifen prüfen?" → a constant number per point
- → "Warum?" → points on one side are ≥ `δ` apart, so a `δ × 2δ` rectangle holds
  boundedly many
- → "Laufzeit?" → naively `O(n log² n)`
- → "Und besser?" ⚠️ → **pre-sort once** by `x` and `y`, pass the orders down →
  `O(n log n)`

---

## C. Board work

| # | Draw / write while talking | Target |
|---|---|---|
| C1 | The determinant and its three sign cases | 30 s |
| C2 | Two segments that straddle, and two that don't | 45 s |
| C3 | A sweep line mid-run with `T`'s contents labelled | 60 s |
| C4 | Graham's stack on 6 points, showing a pop | 90 s |
| C5 | The `2δ` strip with the packing rectangle | 60 s |

---

## D. Traps

**D1.** *"Man könnte den Winkel mit `atan2` berechnen?"* — You could, and the deck
explicitly says not to: division and trigonometry are what the determinant test
exists to avoid.

**D2.** *"Jarvis ist `O(n²)`?"* — It is `O(n·h)`. Worst case `h = n` gives `O(n²)`,
but stating the output-sensitive form is the informative answer.

**D3.** *"Der Graham-Scan ist `O(n²)`, weil man ja pops macht?"* — No. Each point
is pushed once and popped **at most once**, so the whole stack phase is `O(n)`.
Sorting dominates.

**D4.** *"Dichtestes Punktepaar ist `O(n log² n)`?"* — Only if you re-sort inside
the recursion. Pre-sorting once gives `O(n log n)`. Mention the improvement
unprompted.

**D5.** *"Die Sweep Line findet alle Schnittpunkte?"* — This deck's algorithm
finds **one** (or reports none). Reporting all is a different algorithm and out of
scope.

**D6.** *"Warum ist die Sweep Line vertikal?"* — So it meets each segment in at
most one point, which is what makes the `y`-ordering in `T` well defined. Vertical
input segments are excluded as degenerate.

---

## E. Two-minute version

> "Algorithmische Geometrie löst geometrische Probleme, hier alles in `ℝ²`.
> Grundbaustein ist der Orientierungstest: statt Winkel zu berechnen — das
> bräuchte Division und Trigonometrie — bestimmt man die Determinante
> `x₁y₂ − x₂y₁` beziehungsweise ihre auf `p₀` verschobene Variante und liest nur
> das **Vorzeichen** ab. Damit bekommt man Links-/Rechtskurven und den
> Schnitttest zweier Strecken. Die Sweep-Line-Methode traversiert die Ebene mit
> einer vertikalen Geraden und verwaltet nur die aktuell geschnittenen Strecken,
> nach `y` geordnet; um einen Schnittpunkt zu finden, genügt es, jeweils neu
> benachbarte Paare zu testen — denn beim **linkesten** Schnittpunkt sind die
> beteiligten Strecken kurz davor benachbart. Für die konvexe Hülle gibt es
> Jarvis mit `O(n·h)`, also ausgabesensitiv, und Graham mit `O(n log n)`:
> sortieren nach Winkel, dann ein Stack, von dem gepoppt wird, solange keine
> Linkskurve entsteht — jeder Punkt wird einmal gepusht und höchstens einmal
> gepoppt. Schneller als `n log n` geht es nicht, da man Sortieren darauf
> reduzieren kann. Das dichteste Punktepaar löst man mit Teile-und-Herrsche über
> die `x`-Koordinate; im Streifen der Breite `2δ` muss man pro Punkt nur konstant
> viele weitere prüfen, und wenn man einmal vorsortiert statt in jedem Aufruf,
> kommt man von `O(n log² n)` auf `O(n log n)`."

**~100 seconds.**
