---
id: note-amdahls-law
type: note
title: Amdahl's law
created: 2026-07-02
role: synthesis
state: evolving
authorship: user
concepts:
- concept-amdahls-law
sources:
- source-tuh-os-slides
---

If a fraction p of a program can be parallelized and the rest cannot, then
with n processors

    S(n) = 1 / ((1 − p) + p / n)

and as n → ∞, S → 1 / (1 − p). With p = 0.9 the speedup can never exceed 10,
no matter how many cores.

Gustafson's counterpoint: people use more cores to solve bigger problems, and
then the parallel part grows while the serial part stays the same.

## Textbook excerpt (reading on parallel performance, 2026-09-23)

*Excerpt from a textbook chapter (book not identified in the capture); filed
here by the operator, wording unchanged.*

"If a fraction s of the work is inherently sequential, no number of
processors can reduce the runtime below s times the original. Gustafson
observed that in practice the problem size is scaled with the machine, so
that the parallel work grows while the sequential part stays fixed; the
scaled speedup is then s + (1 − s)·N."
