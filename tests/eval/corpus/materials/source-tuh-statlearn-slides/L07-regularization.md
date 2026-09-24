# Statistical Learning — L07 Regularization (slide text export)

Slide 3. Expected test error = bias² + variance + irreducible noise.
Slide 12. Ridge: minimize ‖y − Xw‖² + λ‖w‖². Closed form (XᵀX + λI)⁻¹Xᵀy.
Slide 18. Lasso: minimize ‖y − Xw‖² + λ‖w‖₁. No closed form in general.
Slide 21. Constraint-region picture (disc vs diamond).
Slide 26. Choose λ by k-fold cross-validation; refit on all training data.
Slide 30. Standardize features before penalizing — the penalty is not scale invariant.
