<!-- GENERATED file - do not edit; promoted by tools/material_summarize.py --promote -->

# L06 pp. 24–32 — Independence, expectation, LOTUS, linearity proofs

Independence (p. 24): factorization definitions for the continuous
(P(X ≤ a ∩ Y ≤ b)) and discrete (P(X = a ∩ Y = b)) cases, with a
two-dice example. Expectation (p. 26): integral and sum definitions;
not the most probable value. Dice motivation (p. 27): sample mean 3.44
at n = 9, conjectured limit 3.5 = E(X), which need not be a realizable
value ("you cannot throw 3.5"); convergence is promised for later.
Lemma collection (p. 28): linearity E(X+Y), scaling E(aX) and E(aX+b),
and the E[g(X)] sum/integral formulas — the LOTUS rule, unnamed on the
slide. Repair-cost example (pp. 29–30): X = errors/day on {0,…,4} with
masses 0.3/0.4/0.2/0.08/0.02, per-error cost g(x) = 6 − 5/(1+x); the
slide computes E[g(X)] = 3.05 while asking for cost per day, whereas a
daily total under that wording is X·g(X) with expectation 4.6733 —
decide which quantity the model represents first. Linearity proof
(p. 31, discrete): double sum over joint probabilities pzij without
assuming independence (flagged: factorization only under independence),
collapsing inner sums to marginals. Independence lemma (p. 32):
E[XY] = E[X]E[Y] for independent variables, proved by factorizing the
double sum.
