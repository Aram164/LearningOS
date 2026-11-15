<!-- GENERATED file - do not edit; promoted by tools/material_summarize.py --promote -->

# L06 pp. 9–13 — CDF, discrete computation, limits

CDF definition (p. 9): F(x) = P(X ≤ x) for discrete or continuous X,
illustrated by X = sum of two dice (note: the bar chart is a histogram,
not a cdf). Point queries P(Temp = 17.65…) are meaningless for continuous
variables; P(Temp < 20) is meaningful. Discrete computation (p. 10):
F(x) = Σ_{xi ≤ x} pi. Worked (p. 11): X = number of sixes in three throws;
P(X ≥ 1) = 1 − (5/6)³ ≈ 0.421 via the complement, P(X ≥ 2) ≈ 0.071 by
summing P(X = 2) + P(X = 3). Limits (pp. 12–13): F rises monotonically
0 → 1; one-sided limits exist with right limit F(y) = P(X ≤ y) and left
limit P(X < y); for discrete variables the jump at each xi equals
P(X = xi) (Treppenfunktion).
