---
id: note-algo2-computational-geometry
type: note
title: "Algo 2 T11 — Reference: Algorithmische Geometrie"
created: "2026-08-16"
role: reference
state: evolving
authorship: operator-drafted
concepts: [concept-computational-geometry, concept-determinant-orientation,
  concept-recurrences-master-theorem]
sources: [source-algo2-hu-materials, source-clrs]
contexts: [workspace-algo2-exam-prep]
---

> **Build note (2026-08-16).** Operator-drafted from `ad2_computationalgeometry.pdf`
> (57 sl.). Companions: `-exercise-bank`, `-viva-drill`. Not yet worked by Aram.

# Algo 2 · Topic 11 — Algorithmische Geometrie

*Lectures: 29. Juni `[1-17]`, 1. Juli `[18-36]`, 6. Juli `[37-end]`.*
***Literatur:** CLRS Kap. 33. **Leseempfehlung:** Ottmann/Widmayer's chapter on
geometric algorithms — over 100 pages, covering Voronoi diagrams and geometric
data structures.*

**Agenda (sl. 2):** foundations of geometric algorithms · the **sweep-line
method** · **convex hull** · **closest pair**.

**Applications (sl. 3):** chip design, robotics, image processing.

---

## 1. Foundations (sl. 6–13) — Phase 0.8

**Objects (sl. 6):** everything lives in `ℝ²`. A **point** is `p = (x,y)`; a
**segment** is given by two endpoints; polygons follow.

> **The design principle (sl. 7).** We often need to know whether a point lies
> left or right of a segment, or whether two segments intersect. School methods
> exist — but they use **division and trigonometric functions**, which geometric
> algorithms avoid wherever possible: they are computationally expensive and
> numerically awkward.

**Orientation via determinant (sl. 9).** Given `p₁ = (x₁,y₁)` and `p₂ = (x₂,y₂)`,
does `p₁` lie clockwise before or after `p₂` (about the origin)? Compute

$$\det\begin{pmatrix} x_1 & x_2 \\ y_1 & y_2 \end{pmatrix} = x_1y_2 - x_2y_1$$

The answer depends **only on the sign**:

| Sign | Meaning |
|---|---|
| **positive** | `p₁` lies clockwise **after** `p₂` |
| **negative** | `p₁` lies clockwise **before** `p₂` |
| **zero** | collinear with the origin |

**Relative to a point `p₀` (sl. 10).** For segments `p₀p₁` and `p₀p₂`, translate:
compute the same determinant on `(p₁ − p₀)` and `(p₂ − p₀)`, i.e.
`(x₁−x₀)(y₂−y₀) − (x₂−x₀)(y₁−y₀)`.

**As a 3×3 determinant (sl. 11–12).** The same value is the determinant of a 3×3
matrix in homogeneous coordinates — a compact way to remember it.

**Turn direction (sl. 13).** For consecutive segments `p₀p₁` and `p₁p₂`: the sign
of the orientation of `(p₀, p₁, p₂)` tells you whether the path turns **left** or
**right** at `p₁`. *(This one test drives the entire convex-hull section.)*

**Segment intersection (sl. 15–17).** Do `p₁p₂` and `p₃p₄` share a point? Use
orientation tests on the four triples; the segments **straddle** each other when
the orientations differ appropriately. **Degenerate case:** if an orientation is
zero, the three points are collinear and one must additionally check whether the
point lies **within** the other segment's bounding box.

---

## 2. The sweep-line method (sl. 19–28)

> **The method (sl. 19).** Rather than considering the plane as a whole, an
> imaginary line **sweeps across it**, and the algorithm maintains information
> about only what the line currently touches.

**Example problem (sl. 20):** given `n` segments by their endpoints, **find an
intersection point** (if one exists).

**From the sweep line's view (sl. 21):** the sweep line is **vertical**, so it
meets each segment in at most one point (vertical segments are excluded as a
degenerate case).

**Event points (sl. 22):** the sequence of `x`-coordinates to process, left to
right — here the **endpoints** of the segments.

**Dynamic data structure (sl. 23–24):** maintain `T` holding all segments
currently cut by the sweep line, **ordered by the `y`-coordinate of the
intersection**. Comparing two segments `s` and `t` as keys is a test we can do
directly; note that if `s` and `t` intersect, their order in `T` **swaps** as the
line passes the intersection.

**Algorithm idea (sl. 25–27):** the algorithm answers "yes" only when it has
actually found an intersection. Considering the **leftmost** intersection point
`p` — with no intersection to its left — the two segments meeting at `p` must be
**adjacent in `T`** just before the sweep line reaches `p`. So it suffices to test
**newly adjacent pairs** at each event: on insertion, test the new segment against
its neighbours; on deletion, test the two segments that become neighbours.

**Summary (sl. 28):** a very useful technique for two-dimensional problems; the
central idea is **traversing the plane** with a line and maintaining only local
state.

---

## 3. Convex hull (sl. 30–43)

> **Definition (sl. 30).** A point set `P` is **convex** if for all `p₁, p₂ ∈ P`
> every convex combination of `p₁` and `p₂` also lies in `P`. The **convex hull**
> `CH(Q)` is the smallest convex set containing `Q`.

**Approaches (sl. 31):** incremental (process points left to right by
`x`-coordinate), and others.

> **Lower bound (sl. 32).** In many computational models there is an
> **`Ω(n log n)`** lower bound for the convex hull — by reduction from **sorting**:
> hull vertices come out in angular order, so a sub-`n log n` hull algorithm would
> sort faster than allowed.

### Jarvis' algorithm — gift wrapping (sl. 34–36)

**Idea:** produce the hull points `(p₀, p₁, …, p_{h−1})` in order. Take `p₀` as the
point with smallest `y`-coordinate. Then repeatedly pick the next hull point as
the one making the **smallest angle** with the current edge — "wrapping" the set.

**Sl. 35 — the key implementation point:** instead of computing angles, use
**orientation tests on triples**. No trigonometry, no division.

**Runtime:** `O(n·h)` where `h` is the number of hull vertices — each of the `h`
steps scans all `n` points. **Output-sensitive**: excellent when `h` is small,
worse than Graham when `h` is large.

### Graham's algorithm (sl. 38–42)

**Idea (sl. 38):** start from `p₀`, the point with the smallest `y`-coordinate
(ties broken by largest `x`). **Sort the remaining points by angle** about `p₀`.
Then process them in order, maintaining the hull of the prefix.

**The incremental step (sl. 39–40):** maintain a **stack** `S` holding the vertices
of `CH(Qᵢ)` from bottom to top in counter-clockwise order. For a new point `pᵢ`:
while the top two stack entries together with `pᵢ` do **not** make a left turn,
**pop**; then push `pᵢ`.

**Correctness (sl. 41):** popping is safe — a point that fails the turn test lies
inside the hull of what remains — and no point is wrongly discarded during the
angular sort.

> **Runtime (sl. 42):** sorting by angle costs `O(n log n)` (comparisons done by
> orientation test via determinant); the stack phase is `O(n)` because **each
> point is pushed once and popped at most once**. **Total `O(n log n)` — optimal.**

**Summary (sl. 43):** a classical problem with many algorithms; the fastest are
output-sensitive.

---

## 4. Closest pair (sl. 45–51)

**Problem (sl. 45):** given `Q ⊆ ℝ²` with `n` points, find a pair at minimum
distance.

**Divide and conquer (sl. 46):** split by `x`-coordinate into left and right
halves, recurse to get the minimum distances `δ_L`, `δ_R`, and set
`δ = min(δ_L, δ_R)`.

**The combination step (sl. 47) — the crux.** A closer pair could straddle the
dividing line. Only points within the vertical **strip** `P′` of width `2δ` around
the line can participate. **Sort the strip by `y`-coordinate**; then for each point
only a **constant number** of subsequent points in `y`-order can lie within `δ` —
because a `δ × 2δ` rectangle can hold only boundedly many points that are pairwise
at least `δ` apart.

**Algorithm (sl. 48):** for `|P| ≤ 3` solve directly; else split, recurse, then
scan the strip.

**Correctness (sl. 49):** the only delicate point is that so few strip points need
examining — that is the packing argument above.

> **Runtime (sl. 50–51).** Naively, re-sorting in each recursive call gives
> `T(n) = 2T(n/2) + O(n log n)` = `O(n log² n)`. **Improvement:** sort all points
> by `x` and by `y` **once at the start** and pass the sorted orders down, so the
> combination step is `O(n)`. Then `T(n) = 2T(n/2) + O(n)` = **`O(n log n)`**.

> 🔗 **Cross-wire to T01:** this is a master-theorem recurrence, and the whole
> improvement is about getting `f(n)` from `n log n` down to `n`. Phase 0.2 pays
> off here.

---

## 5. General position and a hard problem (sl. 53–54)

**General position (sl. 53):** inputs are often assumed to be in "general
position" — no three points collinear, no two sharing a coordinate, and so on — to
avoid degenerate cases. Real implementations must handle them.

**The 3-points-on-a-line problem (sl. 54):** given `n` points in `ℝ²`, are three
collinear? Trivially `O(n³)` by testing all triples. *(Notable as a problem
resisting substantial improvement — the 3SUM-hardness connection.)*

---

## 6. Überblick and Ausblick (sl. 56–57)

**Überblick.** Basic questions about the arrangement of points and segments
(orientation via determinant); finding an intersection point with the sweep-line
method; convex hull; closest pair.

**Ausblick (sl. 57).** Computational geometry is an independent and extensive
research field with its own challenges.

---

## 7. Exam-critical minimum

| Must be automatic | Where |
|---|---|
| **Why determinants and not angles** — no division, no trigonometry | sl. 7 |
| `x₁y₂ − x₂y₁` and what its **sign** means | sl. 9 |
| Translating the test to a base point `p₀` | sl. 10 |
| Left/right turn from three points | sl. 13 |
| Segment intersection via straddling + the collinear case | sl. 15–17 |
| Sweep-line: line, event points, ordered structure `T` | sl. 19–23 |
| **Only newly adjacent pairs need testing** — via the leftmost intersection | sl. 26 |
| Convex hull definition and the `Ω(n log n)` bound by reduction from sorting | sl. 30, 32 |
| Jarvis `O(n·h)`, output-sensitive | sl. 34–36 |
| Graham: sort by angle, stack, pop on non-left turns, **`O(n log n)`** | sl. 38–42 |
| Why the stack phase is `O(n)` — each point pushed once, popped once | sl. 42 |
| Closest pair: the `2δ` strip and the constant-many-points argument | sl. 47 |
| **Pre-sorting turns `O(n log² n)` into `O(n log n)`** | sl. 50–51 |

**Traps:** computing angles instead of using orientation tests (the deck's whole
point); giving Jarvis as `O(n²)` without mentioning it is really `O(nh)`;
forgetting the pre-sorting trick in closest pair and quoting `O(n log² n)`; missing
that the sweep-line's correctness rests on the *leftmost* intersection argument.
