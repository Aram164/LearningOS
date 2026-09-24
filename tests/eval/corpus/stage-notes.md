Stage working notes. Key = the working-note path the builder assigns
(curriculum/modules/<module>/units/<unit>/stages/<stage>/notes.md).

=== curriculum/modules/module-tuh-statlearn/units/unit-statlearn-l05/stages/stage-l05-01-derive-naive-bayes/notes.md
date: 2026-09-07
---
# Derive Naive Bayes (without slides)

Class y ∈ {spam, ham}, features x = (x_1..x_d) word indicators.

p(y | x) = p(x | y) p(y) / p(x)        (Bayes)
p(x | y) = Π_j p(x_j | y)              ← the naive step: features treated as
                                         unrelated once the class is fixed
⇒ ŷ = argmax_y [ log p(y) + Σ_j log p(x_j | y) ]

p(x) is the same for both classes → drop it for the argmax.

Estimates: p(x_j = 1 | y) = (count_j,y + 1) / (N_y + 2) (Laplace).

Checked against slides after writing: matches, except the slides use
multinomial counts rather than indicators. Done.

=== curriculum/modules/module-tuh-statlearn/units/unit-statlearn-l05/stages/stage-l05-02-generative-vs-discriminative/notes.md
date: 2026-09-12
---
# Generative vs discriminative — working

Same bag-of-words features, both models, training sizes 50, 200, 1000, 5000.

| n | NB acc | LogReg acc |
|---|---|---|
| 50 | 0.88 | 0.79 |
| 200 | 0.92 | 0.90 |

Stopped here — 1000 and 5000 still to run (notebook cell 14).

So far matches the lecture claim: NB ahead with little data.

Why? Guess: NB only estimates per-word counts, each from all the data of one
class, while logistic regression has to fit all weights jointly and overfits
with 50 examples.

NEXT: finish the two larger runs, then write the two-paragraph comparison and
answer mock exam Q2.

=== curriculum/modules/module-tuh-statlearn/units/unit-statlearn-l07/stages/stage-l07-01-ridge-lasso-geometry/notes.md
date: 2026-09-15
---
# Ridge / lasso — working

Ridge closed form derived again, fine (see the ridge note).

Lasso: tried to set the gradient to zero like for ridge and got stuck — |w| has
no derivative at 0. The slides jump straight to "use coordinate descent".

Question for later: is there a one-dimensional version I can solve by hand to
see where the zeros come from?

=== curriculum/modules/module-tuh-statlearn/units/unit-statlearn-l09/stages/stage-l09-01-pca-from-covariance/notes.md
date: 2026-06-09
---
# PCA by hand

6 points, centred. Σ = [[2.0, 1.2], [1.2, 1.0]].
λ² − 3λ + 0.56 = 0 → λ₁ ≈ 2.79, λ₂ ≈ 0.21. v₁ ≈ (0.84, 0.55).
93% variance on PC1. numpy.linalg.eigh agrees (sign flipped).

Done — wrote it up as a durable note.

=== curriculum/modules/module-tuh-statlearn/units/unit-statlearn-l09/stages/stage-l09-02-svd-connection/notes.md
date: 2026-06-10
---
# PCA ↔ SVD

Centred data X = U Σ Vᵀ. Then XᵀX = V Σ² Vᵀ, and XᵀX / n is the covariance
matrix. So the columns of V are eigenvectors of the covariance …

Stopped here — exams. Still need: why the singular values relate to the
explained variance (σ_i² / n?).

=== curriculum/modules/module-tuh-os/units/unit-os-l02/stages/stage-os-l02-01-classic-policies/notes.md
date: 2026-08-26
---
# Classic policies — exercise log

- Problem 1 (FCFS/SJF/RR, quantum 2): done, avg turnaround FCFS 9.0, SJF 7.3,
  RR 10.7.
- Problem 2 (MLFQ starvation): done — two interactive jobs that always yield
  before the quantum ends starve a long batch job without the boost.
- Problem 6 (overhead): 1 ms quantum, 50 µs switch → 4.8% overhead; 100 µs
  quantum → 33%.

Stage complete.

=== curriculum/modules/module-tuh-os/units/unit-os-l02/stages/stage-os-l02-02-proportional-share/notes.md
date: 2026-09-16
---
# Proportional share — working

Lottery: fair only in expectation. P(B with 25 of 100 tickets gets no slice in
4 draws) = 0.75⁴ ≈ 0.32 — surprisingly unfair in the short run.

Stride: stride = L / tickets, pass starts at 0, always run the lowest pass,
then add its stride. A=100, B=50, C=250 tickets, L = 10,000 → strides 100,
200, 40.

  step 1: all pass 0 → run A (tie-break by name), A.pass = 100
  step 2: B=0, C=0 → run B, B.pass = 200
  step 3: C=0 → run C, C.pass = 40
  step 4: …

Stopped at step 4 (2026-09-16).

NEXT: finish the first eight decisions, check that C runs 5/8 of the time in
the long run, then explain vruntime aloud in under two minutes.

=== curriculum/modules/module-skill-dataframes/units/unit-dataframes-lazy-plans/stages/stage-df-lazy-01-lazy-vs-eager/notes.md
date: 2026-08-08
---
# Lazy vs eager — results

2 GB CSV, filter + group-by + join. Eager 41 s / 9 GB peak; lazy 6 s / 1.3 GB.
Most of the gain: only 4 of 31 columns are read at all.

=== curriculum/modules/module-skill-dataframes/units/unit-dataframes-lazy-plans/stages/stage-df-lazy-02-read-explain/notes.md
date: 2026-09-10
---
# Reading explain() — annotations

Plan 1 (orders ⋈ customers, filter country = 'DE', select 3 columns):
- unoptimized: FILTER sits above the JOIN, both scans read all columns;
- optimized: the country filter moved into the customers scan ("SELECTION:"
  line inside the scan), and the scans list only the needed columns
  ("PROJECT 3/31 COLUMNS").

Plans 2 and 3 still to do.

=== curriculum/modules/module-skill-linalg-refresh/units/unit-linalg-svd/stages/stage-linalg-svd-01-geometry/notes.md
date: 2026-06-08
---
Rotate–stretch–rotate sketched for [[3, 0], [4, 5]]: σ ≈ 6.71, 2.24. Done.

=== curriculum/modules/module-skill-linalg-refresh/units/unit-linalg-svd/stages/stage-linalg-svd-02-low-rank/notes.md
date: 2026-06-10
---
Rank 5 reconstruction of the test photo: recognizable blur, relative error
0.31. Ranks 20 and 50 not done yet.
