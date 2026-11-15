<!-- GENERATED file - do not edit; promoted by tools/material_summarize.py --promote -->

# L06 pp. 5–8 — Random variables and discrete variables

Motivation (p. 5): samples estimate population means, but judging the
estimate needs formalism; the central concept is the random variable.
Roadmap (p. 6): RVs model populations, leading to distributions, expected
values (generalized means), variance, and first coarse sample-vs-population
bounds; tighter bounds come later from named distributions.

Definition (p. 7): a random variable is a function X: Ω → ℝ assigning each
outcome of a random experiment a real number; examples are height of a
person, daily temperature, illness probability. Discrete case: three fair
dice throws, X = sum, X ∈ {3,…,18}; interest lies in P(X = x).

Discrete RVs (p. 8): X is discrete when its image is finite or countably
infinite, with pi = P(X = xi). Point probabilities are meaningless for
continuous variables (individual values are infinitesimally rare).
Worked: X = sum of three dice; P(X = 8) by counting ordered triples over
6³; P(X < 5) = 4/216 ≈ 0.0185.
