# L06 pp. 44–50 — Chebyshev: motivation, inequality, examples

Motivation (p. 44): assessing observations against known μ and σ² —
outliers, errors, conformance; framed loosely as "how likely was x
created by X", for arbitrary distributions but not sharp. Inequality
(p. 45): P(|X−μ| ≥ c) ≤ σ²/c², proved for the discrete case by
restricting the sum to |xi−μ| ≥ c and extending it to the full
variance. Intuition (p. 46): mass concentrates near μ; the bound only
bites for small variance, saturating at 1 otherwise. Dice example
(p. 47): throwing 1 (2.5 from μ = 3.5) bounds at ≈ 0.46 against the
true 1/6 — then the key correction: the bound covers distance to the
mean (here {1, 6}), not a concrete value; symmetry halves it to 0.23.
Biomarker example (pp. 48–49): healthy μ = 14.5, σ² = 2.3 gives ≤ 19%
at b = 18 and ≤ 4% at b = 22, versus < 3.8% and < 0.1% under a normal
model — distribution knowledge sharpens enormously. Outlook (p. 50):
comparing healthy/ill distributions is hypothesis testing, later.
