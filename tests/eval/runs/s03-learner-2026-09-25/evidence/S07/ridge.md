---
id: note-ridge-regression-penalty
type: note
title: Ridge regression
created: 2026-06-01
role: derivation
state: evolving
authorship: user
concepts:
- concept-regularization
- concept-linear-regression
sources:
- source-tuh-statlearn-slides
---

Add a penalty on the weight size:

    L(w) = ‖y − Xw‖² + λ‖w‖²

Gradient to zero: −2Xᵀ(y − Xw) + 2λw = 0 ⇒

    w = (XᵀX + λI)⁻¹ Xᵀ y

XᵀX + λI is always invertible for λ > 0 (its eigenvalues are shifted up by
λ), which also fixes the collinearity problem from the normal-equation note.

Effect: all weights shrink towards zero, none becomes exactly zero. Large λ →
more bias, less variance.

Open questions:

- Why is there a neat closed form here while the lasso needs special solvers?
- Where does λ come from — is it just a knob you tune by cross-validation, or
  does it mean something?

Answered 2026-09-19 (first open question), recorded by the operator: the 1-D
lasso worked by hand in the stage-l07-01-ridge-lasso-geometry working note —
"That's why there is no neat matrix formula for the lasso: the solution is
piecewise, and which pieces are active depends on the data."
