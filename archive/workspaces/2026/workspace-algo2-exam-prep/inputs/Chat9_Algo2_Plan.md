# Algo 2 (AlgoDat II) — Deep Study Plan

> **Created:** 2026-06-12 (KW 24); skeleton replaced by this full plan same day.
> **Module:** „Algorithmen und Datenstrukturen II", Prof. Dr. Stefan Kratsch, HU. 2× 90-min VL/Woche; Übungen ungraded (group problem-solving, no Zulassung).
> **Step prefix:** **AL**
> **Prüfung: MÜNDLICH, 30 min, Zoom, DE or EN — 2. Prüfungszeitraum (Sept/Okt), together with the AMLS exam.** Booking: Agnes (Modul via Übungstermin + Prüfungsanmeldung) + Terminvereinbarung im Prüfungs-Moodle. Prüfungsplan online since May 26.
> **Why Aram took it:** deliberate re-learning of forgotten algorithmics fundamentals. **Depth over speed is the design goal of every block.** The oral format rewards exactly this: you must *explain*, not pattern-match.
> **Starting state (KW 24):** AlgoDat I long ago, content mostly forgotten. Lectures Kap. 1–8 already held, Kap. 9 in progress — Aram has NOT followed along. This plan IS the catch-up path; the course publishes "behandelte Kapitel + Seitenzahlen" at the end for exactly this use.
> **⚠️ Course policy:** Vorlesungsfolien + UB book PDFs may not be passed into AI systems. Sessions in Chat 9 therefore work from: the books as *Aram's own reading* (he summarizes/asks in his words), public papers (Pagh 2006, Sleator/Tarjan 1985 — both on Moodle but also freely published), public courses (MIT 6.046J, Erickson), and Aram's own notes. The plan references book sections by number only.

---

## Step ID Convention

`AL.<Block><Number>` — e.g. `AL.B2` = Block B, step 2. Block self-tests are `AL.B-test`. Completion entries in SEMESTER-STATUS §3: `AL.B1 ✓ (KW 31)`.

---

## Why This Plan Exists

1. **The module is a self-imposed rebuild.** Aram chose it to force re-learning of core algorithmics. A plan that optimizes for exam-passing shortcuts would defeat the purpose; every block therefore includes proof work and hand-running, not just "know the runtime."
2. **The oral format changes what "prepared" means.** A Klausur rewards drilled calculation; a 30-min oral rewards being able to *define precisely, state the theorem with hypotheses, sketch the proof, run the algorithm on a small example, and answer "why not simpler?"*. Every block self-test below is phrased as that exact 5-part oral pattern.
3. **The course's own exercise lists exist.** Prof. Kratsch published recommended exercises per chapter (captured below) — they are the drill bank and the most exam-predictive material available. No Altklausuren needed.

---

## Resource Stack (3 layers — use in this order per block)

| Layer | Resource | Role |
|---|---|---|
| **1. Intuition** | Targeted YouTube (per block below: Abdul Bari, William Fiset graph series, Reducible) + **MIT 6.046J Design and Analysis of Algorithms (OCW, Spring 2015)** mapped lectures | Watch FIRST when the topic feels foreign. Builds the "what problem does this solve and why is the naive way too slow" picture. Never watch 6.046 linearly. |
| **2. The course texts (exam-defining)** | **CLRS „Algorithmen: Eine Einführung", 4. Aufl. Deutsch** (= EN 3rd ed; `Plans/CS-Theory/algo2/Algo2/Buecher/Algo-Buch.pdf`, EN parallel: `Introduction_to_algorithms-3rd Edition.pdf`) · **DMS** = Dietzfelbinger/Mehlhorn/Sanders (`AlgoBuch 2.pdf`) for Kap. 1 + hashing Aufgaben · **OW** = Ottmann/Widmayer for Splay (5.4) + Matching (9.8) | THE sources of truth — the lecture follows them chapter by chapter (assignments per topic from Moodle, below). Read second, with Layer-1 intuition loaded. Definitions + theorem statements + proofs come from here. |
| **3. Rigor / alternative proofs** | **Jeff Erickson, *Algorithms*** (free, [jeffe.cs.illinois.edu/teaching/algorithms](https://jeffe.cs.illinois.edu/teaching/algorithms/)) — Ch. 8 (SSSP), Ch. 9 (APSP), Ch. 10 (Flows), Ch. 11 (Flow applications/matching) + extended notes (amortization, scapegoat/splay) · originals: **Pagh [2006] „Cuckoo Hashing for Undergraduates"**, **Sleator/Tarjan [1985]** (first 6 pp per Moodle) | Pull when a CLRS/OW proof feels unmotivated, or for a second telling before the oral. Erickson's proofs are often cleaner to *re-explain aloud* than CLRS's. |

**MIT 6.046J (2015) mapped lectures:** L3 Divide & Conquer: FFT → AL.K · L5 Amortization → AL.B · L11 All-Pairs Shortest Paths → AL.G · L13 Incremental Improvement: Max Flow, Min Cut → AL.H · L14 Incremental Improvement: Matching → AL.I. (Everything else: skip — different course emphasis.)

**Drill bank = the Moodle recommended exercises** (German CLRS page numbers as published by the professor; listed per block below). Rule of thumb from the course: *Übungen* = section-level vertiefung (do after reading the section), *Problemstellungen* = transfer tasks (do at block end, ideal oral simulation material).

**Solved-practice bank (added KW 24 — full table in LEARNING-RESOURCES §6 → "Algo 2 (AL)"):** ⭐ **Goethe Frankfurt B-ALGO-2: 8 complete Klausuren 2021–2024, each with a solutions PDF** ([directory](https://files.tcs.uni-frankfurt.de/algo2/exams/) — flows, matching, amortisiert + splay, APSP; skip their NP/LP problems; **download now**) · MIT 6.046J psets + quizzes + final, all with solutions · MIT 6.006 exams/psets (easier warm-up tier for AL.G) · Frankfurt Übungsblätter + weekly German topic videos (Blatt/Woche 2–4 = flows, matching, amortisiert+splay) · TU Wien Fib-heap chapter (German worked examples). Additional other-uni lectures: ⭐ **KIT Algorithmen 2 (Sanders — co-author of the course's own DMS book, German, full semester on YouTube)**, CMU 15-451 splay notes (Sleator's own course — best access-lemma writeup for AL.E2), Kevin Wayne KT slides (Stable-Matching stopgap for AL.I3). **Usage rule:** Frankfurt Klausur tasks feed AL.X3/X4 — solve in writing first, then *re-explain aloud* to convert written drill into oral rehearsal.

---

## Prerequisite Dependency Graph

```
AL.A (Schnellere Multiplikation)        [course opener; recurrences = the analysis tool]
  │
  ▼
AL.B (Amortisierte Analyse)  ◄─── the single most load-bearing block:
  │                               D and E are unintelligible without it,
  │                               and it's the #1 oral-exam technique question
  ├──────────► AL.C (B-Bäume)             [independent of B, placed here for course order]
  ├──────────► AL.D (Fibonacci-Heaps)     [potential method applied — needs B]
  ├──────────► AL.E (Splay-Bäume)         [potential method applied — needs B]
  └──────────► AL.F (Cuckoo-Hashing)      [independent of B; light]
  ▼
AL.G (Kürzeste Wege)                      [needs nothing new; refreshes AlgoDat-1 graphs]
  │
  ▼
AL.H (Maximaler Fluss)                    [residual networks, augmenting paths]
  │
  ▼
AL.I (Bipartites + Stable Matching)       [matching via flow — needs H]
  │
AL.J (Algorithmische Geometrie)           [independent]
AL.K (FFT)                                [closes the arc opened by AL.A]
  │
  ▼
AL.X (Oral exam prep: explain sheets, hand-run drill, proof rehearsal, mock oral)
```

Strict chain: **A → B → {C, D, E, F} → G → H → I**, then J and K in any order. Two natural halves: **DS half** (A–F: data structures + amortization) and **graph half** (G–I) — the oral will likely sample from both.

---

## Block-by-Block Plan

> Per-block pattern: Layer-1 intuition → course text → Moodle drill → oral self-test. Every `-test` follows the 5-part oral pattern: **(i) define, (ii) state theorem + hypotheses, (iii) sketch proof, (iv) hand-run an example, (v) answer one "warum nicht einfacher?"**

### BLOCK AL.A: Schnellere Multiplikation *(~3.5h — DMS Kap. 1, NOT CLRS)*

The course opener: how a small trick (Karatsuba) beats the Schulmethode, and the promise that FFT (AL.K) will beat it again. Moodle Leseaufgabe: read DMS Kap. 1 *completely*, including unlectured sections.

- **AL.A1** *(1.5h)* — Schulmethode O(n²) for n-digit numbers; the divide-and-conquer split x = x₁·B^(n/2) + x₀; the naive 4-multiplication recursion T(n) = 4T(n/2) + O(n) → still O(n²); **Karatsuba's trick**: (x₁+x₀)(y₁+y₀) recovers the middle term → 3 multiplications, T(n) = 3T(n/2) + O(n) → **O(n^log₂3) ≈ O(n^1.585)**. Read DMS Kap. 1 fully. Layer 1 if needed: any Karatsuba walkthrough (Abdul Bari / MIT 6.006 multiplication segment).
- **AL.A2** *(1.5h)* — The analysis machinery, because *every* later block leans on it: solving recurrences by recursion tree + Mastertheorem (CLRS Kap. 4.5 as supplement — this part IS CLRS territory). Re-derive log₂3 yourself. Contrast: Strassen's matrix multiplication (CLRS 4.2) uses the identical "save one multiplication" idea — know it as a one-sentence answer.
- **AL.A3** *(0.5h)* — Skim the Karatsuba [1995] retrospective from Moodle (historical color — orals love a "where does this come from" aside).
- **AL.A-test** — (i) Define the integer-multiplication problem and cost model (digit operations). (ii) State Karatsuba's runtime. (iii) Sketch: why 3 multiplications suffice; solve the recurrence on the board. (iv) Hand-run one level of Karatsuba on 2-digit numbers. (v) *Warum nicht einfacher?* — why doesn't splitting alone (4 mults) help at all? **Wire check:** the recursion-tree habit you build here is the same one AMLS uses for parallel-cost analysis (S.C).

### BLOCK AL.B: Amortisierte Analyse *(~4.5h — CLRS Kap. 17.1–17.3 + Leseaufgabe 17.4)*

THE technique block. The professor's exercise note says it himself: "in diesem Kapitel sind die Übungen fast alle sehr empfehlenswert."

- **AL.B1** *(1.5h)* — **Aggregat- und Accounting-Methode** (17.1–17.2) via the two canonical examples: Stack mit Multipop and Binärzähler (increment costs amortized O(1) although worst case O(k)). Key mental move: total cost of n operations vs. cost of one operation. Layer 1: MIT 6.046J L5 (Amortization) — excellent parallel telling.
- **AL.B2** *(1.5h)* — **Potenzialmethode** (17.3): Φ ≥ 0, Φ(D₀) = 0, amortized = actual + ΔΦ. Redo *both* canonical examples with potentials (Φ = stack size; Φ = number of 1-bits). This is the formalism Fibonacci-Heaps (AL.D) and Splay-Bäume (AL.E) need — invest here, harvest twice.
- **AL.B3** *(1.5h)* — Leseaufgabe **17.4 dynamische Tabellen**: doubling on overflow → amortized O(1) insert (do it with all three methods); contraction at α = 1/4 (not 1/2 — understand the oscillation argument). Drill: Ü 17.1-1/2/3 (S. 459f); 17.2-1/2/3 (S. 462); 17.3-1/2/6 (S. 466); Problemstellung 17-2.
- **AL.B-test** — (i) Define amortized cost (all three methods, one sentence each). (ii) State the potential-method theorem (conditions on Φ!). (iii) Prove binary-counter increment is amortized O(1) with Φ = #1-bits, cold. (iv) Hand-run: 8 increments, show actual vs. amortized cost per step. (v) *Warum nicht einfacher?* — why is "average over random inputs" NOT the same as amortized (worst-case sequence!)? **Wire check:** dynamic-table doubling IS the growth strategy of Python lists / C++ vectors / pandas buffers (PY/M plane) — say it with the 17.4 constants.

### BLOCK AL.C: B-Bäume *(~3.5h — CLRS Kap. 18)*

- **AL.C1** *(1.5h)* — Motivation: memory hierarchy, one node = one disk page, minimize I/Os (the chapter intro Moodle points to). Definition with Minimalgrad t: every node t−1…2t−1 keys (root exempt), all leaves same depth; **height ≤ log_t((n+1)/2)** — reproduce this proof, it's a classic oral request. Search = guided multiway descent (18.1).
- **AL.C2** *(1.5h)* — Insert via **Split-Child** preemptively on the way down (18.2); Delete with its case analysis — borrow from sibling / merge / recurse (18.3, the hairy part; aim for "I can state the three cases and run them", not memorized pseudocode).
- **AL.C3** *(0.5h)* — Drill: Ü 18.1-2/3/4 (S. 495f); 18.2-1/3/6 (S. 502); 18.3-1 (S. 507). Problemstellung 18-1 only AFTER AL.B (it's amortized — the professor flags this order too). If it clicks fast, skim B*-Bäume (2/3-full variant) per Moodle Leseaufgabe.
- **AL.C-test** — (i) Define a B-Baum (all conditions!). (ii) State the height bound. (iii) Sketch its proof (counting argument). (iv) Hand-run: insert a 10-key sequence into a t=2 tree (= 2-3-4 tree) with splits shown; delete two keys hitting different cases. (v) *Warum nicht einfacher?* — why not just a red-black tree on disk? (Answer lives in I/Os per level.) **Wire check:** B-trees are THE index structure of DB backends — relevant for Stratum/DuckDB contexts at the job (JK), and DBT background knowledge made concrete.

### BLOCK AL.D: Fibonacci-Heaps *(~5h — CLRS Kap. 19; the amortization showcase)*

Moodle caveat: the book never unmarks roots — for Ü 19.2-1 just ignore a marked root.

- **AL.D1** *(2h)* — The ADT goal first: mergeable priority queue with **amortized O(1)** Insert/Union/DecreaseKey and O(log n) ExtractMin/Delete — and WHY: Dijkstra/Prim go from O(E log V) to **O(E + V log V)**. Structure: circular root list of heap-ordered trees, min pointer, lazy Insert/Union (just splice). Layer 1: any good Fib-heap animation video before the text.
- **AL.D2** *(2h)* — The two real operations: **ExtractMin + Consolidate** (degree-indexed merging, like binary addition of binomial-ish trees) and **DecreaseKey + Cut/kaskadierende Schnitte** (marks!). The potential **Φ = t(H) + 2·m(H)** and the amortized analysis of both. The Fibonacci connection: cascading cuts ⇒ a degree-k subtree has ≥ F_{k+2} ≥ φᵏ nodes ⇒ max degree D(n) = O(log n). This proof is THE oral centerpiece of the chapter.
- **AL.D3** *(1h)* — Drill: Ü 19.2-1 (S. 524), 19.4-1 (S. 532); Problemstellung 19-3. Also write the comparison table binary heap / binomial heap / Fib-heap (Binomial = frühere Auflage, one paragraph of background is enough — the instructor's note exists precisely because it's only context).
- **AL.D-test** — (i) Define the structure + Φ. (ii) State all amortized bounds. (iii) Prove the degree bound via Fibonacci numbers (sketch). (iv) Hand-run: sequence of inserts, one ExtractMin with full consolidate, one DecreaseKey triggering a cascading cut — draw every state. (v) *Warum nicht einfacher?* — why do binary heaps fundamentally pay O(log n) for DecreaseKey-heavy workloads, and where exactly does laziness + potential pay the bill? **Wire check:** "do nothing now, pay later, bound it with a potential" is a general systems-design pattern (write-back caches, log-structured storage — AMLS S.E flavor).

### BLOCK AL.E: Splay-Bäume *(~3.5h — OW 5.4 + Sleator/Tarjan [1985] pp. 1–6)*

- **AL.E1** *(1.5h)* — Self-adjusting BSTs: no balance information at all; **Splay** = rotate accessed node to root via zig / zig-zig / zig-zag (the zig-zig double rotation is the whole secret — contrast with naive move-to-root). Search/Insert/Delete all end in a splay. OW 5.4 as the course text; Moodle Leseaufgabe OW 3.3 (selbstanordnende Listen, move-to-front) as the warm-up idea.
- **AL.E2** *(1.5h)* — The **access lemma / amortized O(log n)** via potential Φ = Σ_v log(size(v)) (ranks). Read Sleator/Tarjan pp. 1–6 (per Moodle). You don't need the full proof polished — but know what the rank potential is, why zig-zig telescopes, and the statement of static optimality flavor ("adapts to access patterns").
- **AL.E3** *(0.5h)* — Drill (all from Moodle): run insert(t,14), search(t,4), delete(t,8) on OW Abb. 5.42; predecessor/successor search strategy; what repeated failed search of the same key does; **why move-to-root alone fails** — construct the amortized-cost-n worst case (this is the best oral question in the whole list).
- **AL.E-test** — (i) Define splaying (three cases, pictures). (ii) State the amortized bound + potential. (iii) Sketch why zig-zig (not single rotations) makes the potential argument work. (iv) Hand-run a splay on a 7-node path. (v) *Warum nicht einfacher?* — the move-to-root counterexample, aloud. **Wire check:** self-adjusting = online adaptation to access distribution; conceptual cousin of caching/LRU arguments (AMLS S.E) and OW 3.3 move-to-front.

### BLOCK AL.F: Cuckoo-Hashing *(~3h — Pagh [2006] as primary text)*

- **AL.F1** *(1.5h)* — Read **Pagh, „Cuckoo Hashing for Undergraduates" [2006]** end to end (it's short and written to be read). Scheme: two tables/two hash functions, each key in h₁(x) or h₂(x) ⇒ **lookup worst-case O(1)** (2 probes — the headline feature vs. chaining/probing); insertion by eviction chains; cycles ⇒ rehash; expected O(1) insert at load < 1/2. Background: universal hashing (DMS Def. 4.2, via Aufgaben 4.11/4.12 — Moodle: "viel zu rechnen, aber Aussage ist wichtig" — read, don't grind).
- **AL.F2** *(1.5h)* — Drill (from Moodle): the insertion exercise — keys 10, 2, 5, 4 into T[1..6] with h₁(x) = x mod 6 + 1, h₂(x) = ((2x mod 13) + 1) mod 6 + 1, then the rehash functions; DMS Aufgaben 4.6, 4.7 (think, don't compute hard), 4.13.
- **AL.F-test** — (i) Define the scheme. (ii) State: worst-case O(1) lookup, expected amortized O(1) insert, load condition. (iii) Sketch why long eviction chains are improbable (the path/cycle counting idea, one paragraph). (iv) Hand-run the Moodle insertion exercise cold. (v) *Warum nicht einfacher?* — what exactly do chaining and linear probing NOT guarantee that cuckoo does? **Wire check:** Python dicts (PY.04) use open addressing with expected O(1) — cuckoo trades that for a *worst-case* lookup guarantee; know when that trade matters (latency-critical lookups, real-time).

### BLOCK AL.G: Kürzeste Wege *(~5h — CLRS Kap. 24 + 25; focus = general weights, AlgoDat 1 covered the non-negative case)*

- **AL.G1** *(2h)* — The relaxation framework (the unifying idea: INIT + RELAX, all SSSP algorithms are relaxation schedules); negative edges vs. **negative cycles** (when "shortest" stops being well-defined); **Bellman-Ford**: |V|−1 rounds of relax-all + one detection round, O(VE), correctness by induction on path length. Layer 1: William Fiset's Bellman-Ford video. The Moodle exercise "show Dijkstra fails with negative weights (no negative cycles!) — give a concrete graph" is mandatory — construct and keep that 3-node example; it's a guaranteed oral question.
- **AL.G2** *(2h)* — All-pairs (Kap. 25): shortest paths via **Matrizenmultiplikation** in the (min,+)-Semiring (25.1 — and why repeated squaring gives O(V³ log V)); **Johnson's algorithm** (25.3 — the Moodle exercise set lives here!): reweighting h(v) from a Bellman-Ford run makes all weights non-negative while preserving shortest paths ⇒ V× Dijkstra ⇒ O(VE + V² log V) on sparse graphs. (Floyd-Warshall 25.2: refresh as one paragraph — likely AlgoDat-1 material.) MIT 6.046J L11 covers exactly this arc.
- **AL.G3** *(1h)* — Drill: Ü 24.1-1/3/4 (S. 667); 25.3-1/4/6 (S. 717); Problemstellungen 24-3, 24-6 ("monoton" = streng monoton per Moodle).
- **AL.G-test** — (i) Define the SSSP problem + relaxation. (ii) State Bellman-Ford's guarantee incl. negative-cycle detection. (iii) Sketch the correctness induction. (iv) Hand-run Bellman-Ford on a 5-node graph with one negative edge; show the Dijkstra counterexample. (v) *Warum nicht einfacher?* — why does Johnson reweight with h from Bellman-Ford instead of just adding a constant to every edge? (Classic trap — paths have different edge counts.) **Wire check:** (min,+) matrix "multiplication" is the same algebraic-structure swap trick as semiring-based graph frameworks (GraphBLAS flavor — AMLS S.B compiler view of computation).

### BLOCK AL.H: Maximaler Fluss *(~5.5h — CLRS 26.1 + 26.2; notation differs slightly from VL per Moodle)*

- **AL.H1** *(2.5h)* — Flussnetzwerke (capacities, conservation, value |f|); **Residualnetz** G_f (incl. back edges — the part everyone gets wrong first), augmentierende Pfade, **Schnitte** und ihre Kapazität; the three-way equivalence **Max-Flow-Min-Cut-Theorem**: f maximal ⇔ no augmenting path ⇔ |f| = c(S,T) for some cut. This proof is the block's oral centerpiece — own all three implications. Layer 1: Fiset's max-flow videos.
- **AL.H2** *(2h)* — **Ford-Fulkerson** as a method (not algorithm): O(E·|f*|) with integer capacities, integrality theorem; the Moodle-linked Wikipedia example of **non-termination on irrational capacities** (read it — "give an instance where FF fails" is a beautiful oral question); **Edmonds-Karp** (BFS-shortest augmenting paths): O(VE²), proof idea = residual distances never decrease + each edge is critical O(V) times. MIT 6.046J L13.
- **AL.H3** *(1h)* — Drill: Ü 26.1-1/2/3 (S. 725ff); 26.2-2/3/4/10 (S. 743ff); Problemstellungen 26-4, 26-5 (26-2 marked "schwer" — attempt once, don't sink). Also per Moodle: re-read 26.1–26.2 *after* the topic and work the proofs.
- **AL.H-test** — (i) Define network, flow, residual network, cut. (ii) State Max-Flow-Min-Cut precisely. (iii) Prove the easy direction (|f| ≤ c(S,T)) cold + sketch the hard one. (iv) Hand-run Edmonds-Karp on a 6-node network, drawing G_f after every augmentation. (v) *Warum nicht einfacher?* — why are back edges in G_f necessary (give the example where greedy forward-only fails)? **Wire check:** min-cut duality is the combinatorial little sibling of LP duality; max-flow = the assignment engine behind AL.I.

### BLOCK AL.I: Bipartites + Stable Matching *(~4.5h — OW 9.8; Stable-Matching-Material TBD on Moodle)*

- **AL.I1** *(2h)* — Matchings: maximal vs. **maximum** (the |M*| ≤ 2|M| exercise nails the difference); **augmentierende Pfade** + Satz von Berge (M maximum ⇔ no M-augmenting path); bipartite case: **reduction to max flow** (unit capacities, source/sink) — do the Moodle proof exercise "show how maximum matching is found via max flow" formally, incl. why integrality (AL.H) makes the flow a matching. OW 9.8 as course text; Erickson Ch. 11 as the cleaner second telling.
- **AL.I2** *(1.5h)* — Drill (all Moodle): OW Aufgaben 9.31, 9.32a (S. 668); prove the augmenting-path lemma (|M′| = |M| + 1); prove |M*| ≤ 2|M| for maximal M. Skim the Vazirani [2020] MV-algorithm paper *only* for what it is (non-bipartite matching exists and is hard to prove correct) — Moodle lists it as Leseempfehlung, not core.
- **AL.I3** *(1h, gated on Moodle Kap. 10)* — **Stable Matching**: expected Gale-Shapley (proposals, rejections; termination, stability proof, proposer-optimality). Material not yet posted — pull the chapter section + exercises when it appears. Until then, the classic treatment (Kleinberg/Tardos Ch. 1 level) as Layer 1.
- **AL.I-test** — (i) Define matching / maximal / maximum / augmenting path / stable. (ii) State Berge + Gale-Shapley's guarantees. (iii) Sketch Berge's proof (symmetric difference of matchings!). (iv) Hand-run: augment a bipartite matching twice via paths; run Gale-Shapley on a 3×3 instance. (v) *Warum nicht einfacher?* — why doesn't greedy give maximum matchings, and what does ≤ 2|M| rescue? **Wire check:** assignment problems ↔ fairness/allocation formulations (AMLS L12, S.G); matching-via-flow is the standard pattern "solve X by reduction to a solved problem" — name one more reduction aloud.

### BLOCK AL.J: Algorithmische Geometrie *(~4h — CLRS Kap. 33 expected; material not yet posted)*

> Placeholder block — refine when the Moodle chapter appears. Standard Kap.-33 content assumed:

- **AL.J1** *(2h)* — Geometric primitives via **Kreuzprodukt** (orientation test, segment-intersection predicate — no division, no angles: understand why that matters numerically); **Sweep-Line**: any-segments-intersect in O(n log n) (event queue + status structure — the status structure is a balanced BST: nice callback to the DS half).
- **AL.J2** *(2h)* — **Convex Hull**: Graham Scan O(n log n) (sort by angle + stack discipline — the stack's amortized argument is an AL.B callback) and Jarvis March O(nh); closest-pair divide & conquer O(n log n) (the strip argument). 
- **AL.J-test** — (i) Define orientation predicate, convex hull. (ii) State runtimes of both hull algorithms + when Jarvis wins. (iii) Sketch the sweep-line invariant. (iv) Hand-run Graham Scan on 8 points (with the stack pops). (v) *Warum nicht einfacher?* — why do angle computations with atan2 invite disaster where cross products don't? **Wire check:** sweep-line = event-driven processing of a spatial dimension as "time" — the same reframing trick as scheduling problems.

### BLOCK AL.K: FFT *(~4h — CLRS Kap. 30 expected; material not yet posted — the arc-closer)*

> Placeholder block — refine when posted. The course framed Kap. 1 as "FFT will beat Karatsuba" — the oral may well ask you to tell that story end to end.

- **AL.K1** *(2h)* — Polynomials: Koeffizienten- vs. **Punkt-Wert-Darstellung**; multiplication is O(n) in point-value form ⇒ plan: evaluate, multiply pointwise, interpolate. **Einheitswurzeln** + their cancellation/halving properties. Layer 1: Reducible's FFT video (genuinely excellent), then MIT 6.046J L3.
- **AL.K2** *(2h)* — The **FFT recursion**: even/odd coefficient split, T(n) = 2T(n/2) + O(n) = O(n log n) (Mastertheorem from AL.A2 — say so in the oral); inverse FFT = same machine with ω⁻¹ and 1/n (DFT matrix inverse); **convolution theorem**; back to integers: multiplication in O(n log n)-ish, completing the Kap.-1 story.
- **AL.K-test** — (i) Define DFT, point-value representation. (ii) State the FFT runtime + convolution theorem. (iii) Sketch the even/odd recursion + why roots of unity make the subproblems half-size. (iv) Hand-run an 4-point FFT by hand. (v) *Warum nicht einfacher?* — why does evaluating at *arbitrary* n points cost O(n²) while roots of unity don't? **Wire check (the big one):** convolution = pointwise multiplication in frequency space — THE reason convolutions (CNNs, F.M/AML L09-CNN material) admit fast implementations; signal processing and polynomial multiplication are the same algebra.

### BLOCK AL.X: Oral Exam Prep *(~8.5h — replaces Klausur drill; format-matched to the 30-min mündliche Prüfung)*

- **AL.X1** *(2.5h)* — **Explain sheets**: one A4 page per topic (12 sheets), each in the 5-part oral pattern — definition / theorem + hypotheses / proof idea (3–5 bullets max) / worked micro-example / the "warum nicht einfacher" answer. Writing these IS studying; the sheets are also the last-day review artifact.
- **AL.X2** *(2h)* — **Hand-run drill** under explanation: B-tree insert+delete, Fib-heap ExtractMin + cascading cut, splay zig-zig chain, cuckoo insertion w/ rehash, Bellman-Ford table, Edmonds-Karp augmentation sequence, Graham scan, 4-point FFT — each *while talking* (record yourself or whiteboard to an empty room; the talking is the exam skill).
- **AL.X3** *(2h)* — **Proof rehearsal**, the five most likely "beweisen Sie": amortized O(1) counter (potential), B-tree height bound, Fib-heap degree bound (Fibonacci argument), Max-Flow-Min-Cut, Berge/|M*| ≤ 2|M|. Criterion: reproduce each on a blank page, aloud, < 10 min.
- **AL.X4** *(2h)* — **Mock oral**: 30 min, exam language (decide DE vs. EN now — and prep in that language), questions sampled across both halves. Best with a study partner from the Übung; fallback: self-test against the explain sheets, honestly graded. Then one gap-pass on whatever broke.
- **AL.X-test** — the mock oral itself, passed without notes.

**Total: ~54.5h** (A 3.5 + B 4.5 + C 3.5 + D 5 + E 3.5 + F 3 + G 5 + H 5.5 + I 4.5 + J 4 + K 4 + X 8.5). If the 2. PZ gets tight: J and K placeholders are the compression candidates *only if* the lecture ends up skipping/shortening them — check the final "Fortschritt" list first.

---

## Cross-Wire Registry (Algo 2 ↔ the rest of the semester)

| # | Algo 2 (this plan) | Connects to | The wire |
|---|---|---|---|
| W1 | AL.A/AL.K recurrences + FFT | **AML CNNs (F.M)** | Convolution theorem: convolution = pointwise mult in frequency space — the *why fast* behind conv layers; Karatsuba→FFT is the same "restructure to multiply less" story |
| W2 | AL.B dynamische Tabellen (17.4) | PY / M (mlprov) | Doubling-growth amortized O(1) append IS Python list / pandas buffer behavior — explain reallocation cost spikes with 17.4 vocabulary |
| W3 | AL.C B-Bäume | JK (Stratum/DuckDB), DBT background | THE index structure of disk-based DBs; node = page = I/O unit |
| W4 | AL.D laziness + potential | AMLS S.E systems patterns | "Defer work, bound it by a potential" = write-back caches, log-structured merge ideas |
| W5 | AL.E self-adjustment | AMLS S.E caching | Splay's adapt-to-access-pattern = LRU/move-to-front family of online heuristics |
| W6 | AL.F hashing guarantees | PY.04 dicts | Expected vs. worst-case O(1) lookup — when the cuckoo trade matters |
| W7 | AL.G (min,+) matrix APSP | AMLS S.B | Semiring swap on matrix multiplication = algebraic view of computation graphs |
| W8 | AL.H max-flow/min-cut | — (math culture) | Combinatorial duality, little sibling of LP duality |
| W9 | AL.I matching/assignment | AMLS L12 fairness (S.G) | Allocation problems formalized as matchings; reduction-to-flow as a design pattern |
| W10 | AL.B–E amortized proofs | AN (Analysis) | Potential functions are monotone-bounded sequences in disguise — AN.A convergence machinery, recognized in CS clothing |

**Direction of traffic:** AL is dormant until after Jul 23, but wires W1/W2/W9 fire from the *other* side first (F.M, mlprov, S.G land in June/July) — when they do, 30 seconds of "this is an Algo-2 concept" cross-referencing is free pre-learning.

---

## Calendar (Scenario: 2. Prüfungszeitraum — CONFIRMED)

**Until Jul 15:** zero AL hours (seminar → submissions own everything). **Jul 16 – end of Jul:** still zero — **late July = AML + SaD + Analysis written exams (1. Termin, confirmed Jun 12)**; AL waits behind all three. Watch Moodle passively for Kap. 10–12 + the final "Fortschritt" page list.

> **Jun 12 restructure:** AN moved from 2. PZ into the 1. Termin (with AML + SaD). The "Alongside AN" column below has been removed — AN is finished before the 2. PZ block begins. This frees ~5–8h/wk that were previously shared with AN, giving AL more breathing room. **Combined 2. PZ block is now AL (~54h) + S.X (~8–12h) ≈ 62–66h** at ~10–12h/wk over 5–6 weeks (down from 105–120h). The pace is much healthier.

**Post-last-1.-Termin-exam push** (AL + S.X only; AN already done):

| Week post-last 1.-Termin exam | AL blocks | AL hours | Alongside |
|---|---|---|---|
| 1 | AL.A + AL.B (the technique core) | ~10h | S.X Block A–B review start |
| 2 | AL.C + AL.D | ~10h | S.X Block B–C review |
| 3 | AL.E + AL.F | ~9h | S.X Block D–E review |
| 4 | AL.G + AL.H start | ~10h | S.X Block F–G review |
| 5 | AL.H finish + AL.I | ~8h | S.X Block H + exam format prep |
| 6 | AL.J + AL.K (if posted) | ~8h | S.X mock oral / written drill |
| 7 | AL.X (explain sheets → drills → proof rehearsal) | ~7h | Final S.X gap pass |
| 8 | AL.X4 mock oral + gap pass → **Prüfung** | ~2.5h | Buffer + AMLS Prüfung |

**Sequencing rule when booking the TWO 2. PZ dates (AL + AMLS — AN is in the 1. Termin):** confirm AMLS exam format first (oral vs written per action item #2 in AMLS plan); keep **≥ 1 week between AL and AMLS**; the AL oral benefits most from being last so explain sheets stay warm. Resolve when executing action item #1.

---

## Action Items (logged KW 24)

1. ⚠️ **Book the Prüfungstermine** — Moodle Prüfungsplan (online since May 26) → choose 2. PZ slot; Agnes Modul- + Prüfungsanmeldung; Termin im Prüfungs-Moodle. Sequence AMLS / Algo 2 / Analysis with ≥ 1 week spacing. (~20 min admin; do this week.)
2. **Decide exam language now** (DE or EN) — all AL.X rehearsal happens in that language.
3. **Watch Moodle** for Kap. 10–12 (Stable Matching, Geometrie, FFT) + literature notes → refine AL.I3/AL.J/AL.K when posted; pull the end-of-course "behandelte Kapitel + Seitenzahlen" list as the authoritative scope check before AL.X.
4. Optional, low-cost: attend/skim the remaining lectures (Kap. 9 finish, 10–12) live — they're the only topics where catch-up wouldn't be needed later. Keine VL/Übung 24.6. (dies academicus).

---

*Created by Hub Chat (Brain), KW 24. Wired into SEMESTER-STATUS §0/§1/§3/§4/§5/§6/§7/§8/§9, CHAT-DIVISION, HANDOFF. Course policy respected: plan references book sections by number; no slide/book content ingested.*
