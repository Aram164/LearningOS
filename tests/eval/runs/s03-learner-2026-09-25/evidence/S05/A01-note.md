---
id: note-independence-vs-conditional-independence
type: note
title: Independence is not the same as conditional independence
created: 2026-05-02
role: synthesis
state: evolving
authorship: user
concepts:
- concept-conditional-independence
- concept-conditional-probability
sources:
- source-murphy-pml1
---

Two statements that look alike and are not:

- A ⊥ B: P(A, B) = P(A) P(B)
- A ⊥ B | C: P(A, B | C) = P(A | C) P(B | C) for every value of C

Neither implies the other.

**Dependent, but independent given C.** Ice-cream sales and drowning
incidents are correlated across the year. Given the temperature, they are
(roughly) not — the temperature explains both. Same with two students' exam
scores in the same class: correlated overall, but once you fix the teacher
(and so the difficulty of what was taught) the remaining noise is separate.

**Independent, but dependent given C.** Two fair coins X, Y are independent.
Let C = X XOR Y. Given C = 1, knowing X determines Y completely. "Explaining
away" in Murphy is the same effect: two independent causes of one observed
effect become dependent once you observe the effect.

Useful equivalent form: A ⊥ B | C ⇔ P(A | B, C) = P(A | C) — once C is known,
B carries no extra information about A.

Why I care: the lecture said a lot of models become tractable only because
some big joint distribution splits into a product of small factors, and every
such split is an independence claim that could be false.

## Reading page: Bayesian networks (Bishop 8.1–8.2) — added 2026-09-19

*Transcribed from a photographed notebook page (library, reading ahead of the
retake); filed here by the operator, wording unchanged.*

- DAG over the variables. Joint = Π_i p(x_i | parents(x_i)).
- 5 binary vars with no structure: 2⁵ − 1 = 31 numbers. With the graph
  a → c ← b, c → d, c → e: 1 + 1 + 4 + 2 + 2 = 10 numbers.
- A node is independent of its non-descendants given its parents.
- d-separation: path blocked by an observed chain/fork node, or by an
  unobserved collider with no observed descendants.
- "Head-to-head" node observed → its parents become dependent (explaining
  away!!)

The simplest example in the chapter is a single class node with arrows to
every feature node. ??? recognize this from somewhere
