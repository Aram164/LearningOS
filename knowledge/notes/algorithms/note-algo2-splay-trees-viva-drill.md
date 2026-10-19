---
id: note-algo2-splay-trees-viva-drill
type: note
title: "Algo 2 T05 — Viva Drill: Splay-Bäume"
created: "2026-08-16"
role: mock-exam
state: evolving
authorship: operator-drafted
concepts: [concept-splay-trees, concept-amortized-analysis]
sources: [source-algo2-hu-materials]
contexts: [workspace-algo2-exam-prep]
---

> **Build note (2026-08-16).** Operator-drafted from `ad2_splaytrees.pdf`.
> `role: mock-exam` is the schema's nearest value; **this is an oral drill.**
> Unverified by Aram.

# Algo 2 · Topic 5 — Viva Drill

---

## A. The five-minute summary

1. The alternative to strict balancing: **let the tree adapt to the access
   pattern** — self-adjusting lists generalized to trees.
2. Splay trees carry **no balance information at all**.
3. The `splay` operation moves `k` to the root by rotations, roughly halving the
   depth of everything on the path; the three cases.
4. **zig-zig rotates the grandparent first** — that is what distinguishes it from
   move-to-root, and it is the only reason the bound works.
5. search/insert/delete all reduce to splay.
6. A single operation can cost `Ω(n)`; the bound is **amortized** `O(log n)`, via
   the rank potential.
7. Trade-offs, and the open dynamic-optimality conjecture.

---

## B. Follow-up trees

**B1. "Was ist ein Splay-Baum?"**
- → "Welche Balance-Informationen speichert er?" → **none**
- → "Wie bleibt er dann effizient?" → the splay operation restructures on access
- → "Was garantiert er im Worstcase pro Operation?" ⚠️ → nothing; `Ω(n)` possible
- → "Also was garantiert er?" → amortized `O(log n)`, `O(m log n)` per sequence

**B2. "Erklären Sie die splay-Operation."**
- → "Nennen Sie die drei Fälle." → zig, zig-zig, zig-zag
- → "Wann zig?" → parent is the root; terminating case
- → "Zeichnen Sie zig-zig." ⚠️ *grandparent rotation first*
- → "Und warum nicht einfach zweimal an `p` rotieren?" → that is move-to-root; `p`
  still reaches the root, but the other path nodes don't improve, and there is no
  good amortized bound
- → "Was passiert, wenn `k` gar nicht im Baum ist?" → splay the last inner node of
  the failed search

**B3. "Wie realisieren Sie delete?"**
- → splay `k` to the root, remove it, splay the largest key of `t_ℓ`, attach `t_r`
- → "Warum hat dieser Knoten danach kein rechtes Kind?" → it is the maximum of `t_ℓ`
- → "Und insert?"

**B4. "Wie sieht die amortisierte Analyse aus?"**
- → "Was ist der Rang?" → `r(x) = log(size(x))`
- → "Was ist das Potential?" → the **sum of all node ranks**
- → "Nennen Sie das Lemma." → `3(r(t) − r(p)) + 1`
- → "Wie folgt daraus `O(log n)`?" → `r(t) = log n`, `r(p) ≥ 0`
- → "Welcher der drei Fälle war scharf?" ⚠️ → **zig-zig** — hence the constant 3
- → "Woher kommt die +1?" → the single terminating zig; the rest telescopes
- → "Sie brauchten einen Hilfssatz über Logarithmen — welchen?"
  → `a + b ≤ c` ⟹ `log a + log b ≤ 2 log c − 2`, from `(a−b)² ≥ 0`

**B5. "Vor- und Nachteile?"**
- → "Was ist der Preis dafür, dass auch beim Suchen umgebaut wird?"
  → problematic for concurrency and caching — reads mutate the structure
- → "Wann würden Sie trotzdem Splay-Bäume nehmen?" → skewed access patterns,
  no need for per-operation guarantees, simplicity of implementation

**B6. "Sind Splay-Bäume optimal?"**
- → static optimality follows from the analysis with other weights (sl. 48)
- → dynamic optimality is **conjectured by Sleator and Tarjan and still open**

---

## C. Board work

| # | Draw / write while talking | Target |
|---|---|---|
| C1 | zig, before and after | 30 s |
| C2 | **zig-zig**, before and after, grandparent first | 60 s |
| C3 | zig-zag, before and after | 45 s |
| C4 | A path of 8 nodes, splay the deepest, show the halving | 90 s |
| C5 | `r(x) = log(size(x))`, potential = Σ ranks | 20 s |
| C6 | The lemma and the `O(log n)` derivation | 45 s |
| C7 | The auxiliary lemma with its `(a−b)² ≥ 0` proof | 45 s |

> ⚠️ **C2 is the single highest-value drawing in the course.** Get the rotation
> order wrong under questioning and the examiner learns you memorized a name.

---

## D. Traps

**D1.** *"Splay-Bäume sind balanciert?"* — No, not in general. They can be
path-shaped. They are *self-adjusting*, which is a different property.

**D2.** *"`O(log n)` pro Operation?"* — **Amortized.** One operation can be `Ω(n)`.

**D3.** *"zig-zig ist zweimal rotieren an `p`?"* — No. **Grandparent first.**
Rotating twice at `p` is move-to-root, which lacks the bound.

**D4.** *"Beim Suchen bleibt der Baum unverändert?"* — No, and that is a *listed
disadvantage*: reads restructure, which complicates concurrency.

**D5.** *"Die dynamische Optimalität ist bewiesen?"* — It is a **conjecture**, and
still open. Do not be talked into agreeing.

**D6.** *"Warum die Konstante 3?"* — Because the zig-zig estimate is tight; the
other two cases have slack. This is a real "why", not a convention.

---

## E. Two-minute version

> "Statt einen Suchbaum strikt zu balancieren, kann man ihn sich an das
> Zugriffsmuster anpassen lassen — die Idee der selbstanordnenden Listen,
> übertragen auf Bäume. Splay-Bäume speichern gar keine Balance-Informationen.
> Zentral ist die splay-Operation: der gesuchte Schlüssel wird durch Rotationen
> zur Wurzel bewegt, wobei sich die Tiefe der Knoten auf dem Suchpfad etwa
> halbiert. Drei Fälle: zig, wenn der Vater die Wurzel ist; zig-zig, wenn `p` und
> sein Vater beide linke oder beide rechte Kinder sind — dann rotiert man
> **zuerst am Großvater**; und zig-zag sonst. Genau diese Reihenfolge
> unterscheidet splay von Move-to-Root und ist der Grund für die Schranke.
> Search, insert und delete lassen sich alle auf splay zurückführen. Einzelne
> Operationen können `Ω(n)` kosten; amortisiert sind es aber `O(log n)`. Der
> Beweis nutzt Ränge `r(x) = log(size(x))` und als Potential die Summe aller
> Ränge; man zeigt, dass splay amortisiert höchstens `3(r(t) − r(p)) + 1` kostet,
> und teleskopiert. Nur der zig-zig-Fall ist dabei scharf."

**~85 seconds.**
