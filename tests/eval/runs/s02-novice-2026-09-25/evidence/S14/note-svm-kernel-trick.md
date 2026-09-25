---
id: note-svm-kernel-trick
type: note
title: SVMs and the kernel trick
created: 2026-06-23
role: synthesis
state: rough
authorship: user
concepts:
- concept-svm
sources:
- source-tuh-statlearn-slides
contexts:
- workspace-statlearn-retake
---

Maximum-margin separating hyperplane; only the support vectors (points on the
margin) determine it. Soft margin with slack variables and a penalty C.

The dual problem only uses the data through inner products x_iᵀx_j. Replace
every inner product by a kernel k(x_i, x_j) = φ(x_i)ᵀφ(x_j) and you get a
linear separator in the feature space of φ without ever computing φ.

RBF kernel: k(x, x') = exp(−γ‖x − x'‖²) — an infinite-dimensional φ.

A function is a valid kernel iff every kernel matrix it produces is positive
semi-definite (Mercer).

Out of exam scope beyond the definition (workspace deferral).
