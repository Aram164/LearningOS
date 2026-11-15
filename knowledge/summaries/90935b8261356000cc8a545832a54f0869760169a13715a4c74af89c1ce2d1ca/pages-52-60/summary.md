<!-- GENERATED file - do not edit; promoted by tools/material_summarize.py --promote -->

# L06 pp. 52–60 — Sample mean, IID, law of large numbers

Question (p. 52): what a size-n sample tells about X — mean, variance,
shape — e.g. voters, customers, therapy effects. IID as modeling
assumption (pp. 53–54): same experiment, independent copies; in
practice only approximated by removing known confounders (drug trials,
vaccines, ML train/serve skew, transfer learning). Sample mean lemma
(p. 55): X̄ = (1/n)ΣXi is random with E[X̄] = μ (linearity) and
Var(X̄) = σ²/n — the variance half needs zero cross-covariances and
the squared 1/n² factor, which the slide's one-line proof does not
show. Ten-dice table (p. 56): two realized experiments (means 2.9,
3.3) separating each Xi, realized xi, and random X̄; Var(Xi) = 2.92
versus Var(X̄) = 0.292. LLN (p. 57): lim P(|X̄−μ| < ε) = 1 for every
ε > 0. Stochastic — not plain — convergence (p. 58): a late long
strange run stays possible; probability 0 in the limit, never the
path. Proof (p. 59): Chebyshev on X̄ with σ²/n. Empirics (p. 60):
Hauptsatz pointwise empirical-CDF convergence per x — not the
uniform Glivenko–Cantelli statement.
