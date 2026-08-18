---
id: note-algo2-computational-geometry-exercise-bank
type: note
title: "Algo 2 T11 — Exercise Bank: Algorithmische Geometrie"
created: "2026-08-16"
role: exercise-bank
state: evolving
authorship: operator-drafted
concepts: [concept-computational-geometry, concept-determinant-orientation,
  concept-recurrences-master-theorem]
sources: [source-algo2-hu-materials, source-clrs, source-algo2-frankfurt-klausuren]
contexts: [workspace-algo2-exam-prep]
---

> **Build note (2026-08-16).** Operator-drafted from `ad2_computationalgeometry.pdf`.
> Solutions operator-computed, **unverified by Aram**. Deck wins on disagreement.

# Algo 2 · Topic 11 — Exercise Bank

**Scope:** orientation via determinants, segment intersection, the sweep-line
method, convex hull (Jarvis and Graham) with the `Ω(n log n)` bound, closest pair
by divide and conquer, general position.

> ✍️ **Everything here is drawable.** Do the drills with a pen and coordinates —
> sign conventions do not stick verbally.

## 1. Local material

| File | What | Where |
|---|---|---|
| `note-algo2-computational-geometry` | Reference (§ refs below) | this vault |
| `note-algo2-computational-geometry-viva-drill` | Oral drill | this vault |
| `note-algo2-phase0-prerequisites` | Phase 0.8 = determinants | this vault |
| CLRS Kap. 33 | **Assigned reading** | `material://source-clrs/clrs-de.pdf` |
| Ottmann/Widmayer, geometry chapter | Leseempfehlung (100+ pp, Voronoi) | `material://source-ottmann-widmayer/ow.pdf` |

## 2. Drills

### A. Orientation

**A1.** Why does the course use determinants rather than angles?

<details><summary>Solution</summary>

Angle-based tests require **division and trigonometric functions**, which are
computationally expensive and numerically awkward. The determinant is a few
multiplications and a subtraction, and only its **sign** is needed. *(Ref §1,
sl. 7.)*
</details>

**A2.** Give the orientation test about the origin and its sign convention.

<details><summary>Solution</summary>

`det[x₁ x₂; y₁ y₂] = x₁y₂ − x₂y₁`. **Positive** → `p₁` lies clockwise *after*
`p₂`; **negative** → clockwise *before*; **zero** → collinear with the origin.
*(Ref §1, sl. 9.)*
</details>

**A3.** Give the test relative to a base point `p₀`.

<details><summary>Solution</summary>

Translate: `(x₁−x₀)(y₂−y₀) − (x₂−x₀)(y₁−y₀)`. *(Ref §1, sl. 10.)*
</details>

**A4. [open]** For `p₀ = (0,0)`, `p₁ = (2,1)`, `p₂ = (1,3)`: compute the
orientation, state the turn direction, and draw it to confirm.

**A5. [open]** Show the 3×3 homogeneous form gives the same value as A3.
*(Ref §1, sl. 11–12.)*

**A6. [open]** Write pseudocode deciding whether segments `p₁p₂` and `p₃p₄`
intersect, **including the collinear case**. *(Ref §1, sl. 15–17.)*

### B. Sweep line

**B1.** Describe the method and its three ingredients.

<details><summary>Solution</summary>

A **vertical sweep line** moves left to right; **event points** are the
`x`-coordinates to process (here the segment endpoints); a **dynamic structure
`T`** holds the segments currently cut by the line, ordered by the `y`-coordinate
of intersection. *(Ref §2, sl. 19–23.)*
</details>

**B2.** Why is it enough to test only newly adjacent pairs? *(The correctness
argument.)*

<details><summary>Solution</summary>

Consider the **leftmost** intersection point `p`, with no intersection to its
left. Just before the sweep line reaches `p`, the two segments meeting at `p` must
be **adjacent in `T`** — nothing between them can cross either one, or there would
be an intersection further left. So testing pairs as they become adjacent (on
insertion and on deletion) suffices to detect it. *(Ref §2, sl. 25–27.)*
</details>

**B3. [open]** Why is the sweep line taken vertical, and what degenerate input
does that exclude? *(Ref §2, sl. 21.)*

**B4. [open]** What happens to the order of two segments in `T` as the line passes
their intersection? Why does that matter? *(Ref §2, sl. 24.)*

**B5. [open]** Trace the algorithm on four segments where exactly one pair
crosses. List the events and the state of `T` at each.

### C. Convex hull

**C1.** Define convexity and the hull.

<details><summary>Solution</summary>

`P` is convex if for all `p₁,p₂ ∈ P` every convex combination of them lies in `P`.
`CH(Q)` is the smallest convex set containing `Q`. *(Ref §3, sl. 30.)*
</details>

**C2.** Prove the `Ω(n log n)` lower bound.

<details><summary>Solution</summary>

Reduction from **sorting**: given numbers `x₁,…,x_n`, map each to a point on a
convex curve (e.g. `(xᵢ, xᵢ²)` on the parabola). All points are hull vertices, and
the hull is output in angular — hence sorted — order. A hull algorithm faster than
`n log n` would sort faster than the comparison lower bound allows. *(Ref §3,
sl. 32.)*
</details>

**C3.** Describe Jarvis' algorithm and its runtime.

<details><summary>Solution</summary>

Gift wrapping: start at the point with smallest `y`; repeatedly select the next
hull point as the one making the smallest angle with the current edge, decided by
**orientation tests, not angle computation**. Runtime `O(n·h)` with `h` the number
of hull vertices — **output-sensitive**. *(Ref §3, sl. 34–36.)*
</details>

**C4.** Describe Graham's algorithm and prove its runtime.

<details><summary>Solution</summary>

Take `p₀` = smallest `y` (ties: largest `x`); sort the rest by angle about `p₀`;
maintain a stack of the current hull in counter-clockwise order; for each new
point, **pop while the top two plus the new point do not make a left turn**, then
push. Sorting is `O(n log n)`; the stack phase is `O(n)` because **each point is
pushed once and popped at most once**. Total `O(n log n)` — optimal by C2.
*(Ref §3, sl. 38–42.)*
</details>

**C5. [open]** Run Graham's algorithm on 8 points you place by hand. Record every
pop.

**C6. [open]** For which `h` does Jarvis beat Graham? Solve `n·h < n log n`.

### D. Closest pair

**D1.** Give the divide-and-conquer structure and the combination step.

<details><summary>Solution</summary>

Split by `x` into halves, recurse for `δ_L`, `δ_R`, set `δ = min`. A closer pair
could straddle the line, so consider the strip `P′` of width `2δ` around it, sorted
by `y`; for each point only a **constant number** of following points in `y`-order
can be within `δ`. *(Ref §4, sl. 46–48.)*
</details>

**D2.** Justify the "constant number" claim.

<details><summary>Solution</summary>

Within the strip, any two points on the same side are at least `δ` apart (else the
recursion would have found them). A `δ × 2δ` rectangle can therefore contain only
a bounded number of such points, so scanning a constant number of `y`-successors
suffices. *(Ref §4, sl. 47, 49.)*
</details>

**D3.** Give both runtimes and the improvement.

<details><summary>Solution</summary>

Re-sorting inside each call: `T(n) = 2T(n/2) + O(n log n)` = `O(n log² n)`.
**Pre-sort once** by `x` and by `y` and pass the orders down: the combination step
becomes `O(n)`, so `T(n) = 2T(n/2) + O(n)` = **`O(n log n)`**. *(Ref §4,
sl. 50–51.)*
</details>

**D4. [open]** Solve both recurrences with the master theorem, naming the case
each falls into. *(Cross-wire to Phase 0.2 and T01.)*

### E. General position

**E1. [open]** What is "general position" and why is it assumed? Name two
degeneracies it rules out and say what each would break in the algorithms above.
*(Ref §5, sl. 53.)*

**E2. [open]** State the 3-points-on-a-line problem and its trivial bound.
*(Ref §5, sl. 54.)*

## 3. External practice — scope filter

| Source | Take | Avoid |
|---|---|---|
| CLRS Kap. 33 | **Assigned**; orientation, sweep line, hull, closest pair | — |
| Ottmann/Widmayer geometry chapter | Leseempfehlung only | its 100+ pages on Voronoi diagrams and geometric data structures |
| Frankfurt Klausuren | Geometry items as explain-aloud drill | written framing |

**Filter:** in scope are orientation tests, segment intersection, the sweep-line
method for *finding an* intersection, Jarvis, Graham, and closest pair.
**Out:** Voronoi diagrams, Delaunay triangulation, range-searching structures,
and the Bentley-Ottmann algorithm for reporting *all* intersections — the deck
finds one, not all.
