Durable notes — mathematics (probability, statistics, linear algebra, calculus).
Bundle format: see tools/bundle.py.

=== note-conditional-probability-basics
domain: mathematics
title: Conditional probability and Bayes' rule
created: 2026-04-14
role: synthesis
state: evolving
authorship: user
concepts: [concept-conditional-probability, concept-bayes-theorem]
sources: [source-tuh-statlearn-slides]
---
P(A | B) = P(A ∩ B) / P(B), only defined when P(B) > 0. The way I remember it:
conditioning shrinks the universe to B and renormalizes.

Bayes' rule is just writing the joint two ways:

    P(A | B) P(B) = P(A ∩ B) = P(B | A) P(A)
    ⇒ P(A | B) = P(B | A) P(A) / P(B)

Names from the lecture: P(A) prior, P(B | A) likelihood, P(A | B) posterior,
P(B) evidence. The evidence is usually computed with the law of total
probability: P(B) = Σ_i P(B | A_i) P(A_i).

Classic trap (the disease test): test with 99% sensitivity, 95% specificity,
prevalence 1%. P(sick | positive) = 0.99·0.01 / (0.99·0.01 + 0.05·0.99) ≈ 0.17.
I got 0.99 the first time because I swapped the conditional. Writing the
2×2 table with 10,000 people fixes it every time.

=== note-independence-vs-conditional-independence
domain: mathematics
title: Independence is not the same as conditional independence
created: 2026-05-02
role: synthesis
state: evolving
authorship: user
concepts: [concept-conditional-independence, concept-conditional-probability]
sources: [source-murphy-pml1]
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

=== note-mle-coin-flips
domain: mathematics
title: Maximum likelihood for a coin
created: 2026-04-20
role: derivation
state: evolving
authorship: user
concepts: [concept-maximum-likelihood]
sources: [source-tuh-statlearn-slides]
evidence:
  - {type: derivation, ref: "github://noor-haddad/ml-exercises/sheet01/mle_coin.pdf"}
---
Data: n flips, k heads. Model: each flip ~ Bernoulli(θ), flips independent.

    L(θ) = θ^k (1 − θ)^(n−k)
    ℓ(θ) = k log θ + (n − k) log(1 − θ)
    dℓ/dθ = k/θ − (n − k)/(1 − θ) = 0  ⇒  θ̂ = k/n

Second derivative is negative everywhere on (0, 1), so it is a maximum.

Things I had to convince myself of:

1. Taking the log is allowed because log is strictly increasing — same argmax.
2. The log turns the product over flips into a sum, which is what makes
   differentiating painless.
3. With k = 0 the MLE is θ̂ = 0, which is silly after three tails in a row.
   That is the overconfidence problem the lecture fixes later with priors.

Written in the general form, the thing being maximized is
Σ_i [y_i log θ + (1 − y_i) log(1 − θ)] with y_i ∈ {0, 1}.

=== note-gaussian-noise-least-squares
domain: mathematics
title: Why least squares falls out of Gaussian noise
created: 2026-04-27
role: derivation
state: evolving
authorship: user
concepts: [concept-maximum-likelihood, concept-linear-regression]
sources: [source-tuh-statlearn-slides, source-murphy-pml1]
evidence:
  - {type: derivation, ref: "github://noor-haddad/ml-exercises/sheet03/ex2_gaussian_mle.pdf"}
---
Model: y_i = wᵀx_i + ε_i with ε_i ~ N(0, σ²), i.i.d.

Each observation has density

    p(y_i | x_i, w) = (2πσ²)^(−1/2) · exp(−(y_i − wᵀx_i)² / (2σ²))

The likelihood of the whole dataset is the product over i. Take logs:

    log L(w) = −(n/2) log(2πσ²) − (1/(2σ²)) Σ_i (y_i − wᵀx_i)²

The first term does not depend on w, and 1/(2σ²) is a positive constant, so

    argmax_w log L(w) = argmin_w Σ_i (y_i − wᵀx_i)²

So "minimize the sum of squared residuals" is not an arbitrary choice — it is
exactly what you get if you believe the noise is Gaussian with constant
variance. If the noise were Laplace instead, the same steps would give the sum
of absolute residuals.

What I still find strange: σ² drops out of the argmax entirely, but it comes
back if you also want to estimate it (σ̂² = mean squared residual).

=== note-p-values-first-take
domain: mathematics
title: p-values (first take)
created: 2026-04-22
role: synthesis
state: deprecated
authorship: user
concepts: [concept-hypothesis-testing]
sources: [source-tuh-statlearn-slides]
---
A p-value is the probability that the null hypothesis is true. So p = 0.03
means there is a 3% chance H0 is right, which is why we reject it below 5%.

Small p → H0 probably false → effect is real. Large p → H0 true.

Significance level α = 0.05 is the threshold. Not sure why 5% and not 1%.

=== note-p-values-corrected
domain: mathematics
title: What a p-value actually is
created: 2026-06-18
role: synthesis
state: evolving
authorship: user
concepts: [concept-hypothesis-testing]
sources: [source-wasserstein-asa-2016, source-tuh-statlearn-slides]
---
I had this wrong in April. Correct statement:

> p = P(test statistic at least as extreme as the one observed | H0 is true)

It is computed *assuming* H0. It is not P(H0 | data) — getting that would need
Bayes' rule and a prior on H0, which a frequentist test never uses.

Consequences I got wrong before:

- A large p-value does not show H0 is true. It only says the data are not
  surprising under H0; they might not be surprising under H1 either (small
  sample, low power).
- p = 0.03 is not "3% chance the null is right".
- A tiny p-value with a huge sample can go with a practically irrelevant
  effect. Report the effect size and a confidence interval next to it.

The ASA statement lists six principles; the one that finally fixed it for me:
"P-values do not measure the probability that the studied hypothesis is true."

Rule of thumb I use now: read "p = 0.03" as "if nothing were going on, data
this extreme would show up about 3% of the time".

=== note-consistent-estimators
domain: mathematics
title: Unbiased versus consistent estimators
created: 2026-05-12
role: synthesis
state: evolving
authorship: user
concepts: [concept-statistical-estimation]
sources: [source-tuh-statlearn-slides]
---
An estimator θ̂_n is a function of the sample. Two properties that the
lecture kept mixing up for me:

- **Unbiased:** E[θ̂_n] = θ for every n.
- **Consistent:** θ̂_n → θ in probability as n → ∞, i.e. for every ε > 0,
  P(|θ̂_n − θ| > ε) → 0.

Consistency is about large samples, unbiasedness about the average over
repeated samples at a fixed size. You can have either without the other:

- X_1 alone as an estimator of the mean is unbiased but not consistent (it
  never uses more data).
- The variance estimator with 1/n instead of 1/(n−1) is biased but
  consistent — the bias (−σ²/n) vanishes as n grows.

Sufficient condition I will use in the exam: if the bias → 0 and the variance
→ 0, the estimator is consistent (Chebyshev).

=== note-bias-variance-decomposition-lecture
domain: mathematics
title: Bias–variance decomposition (lecture version)
created: 2026-05-26
role: derivation
state: evolving
authorship: user
concepts: [concept-bias-variance-tradeoff]
sources: [source-tuh-statlearn-slides]
evidence:
  - {type: derivation, ref: "github://noor-haddad/ml-exercises/l07/bias_variance_derivation.pdf"}
---
Setting: y = f(x) + ε, E[ε] = 0, Var(ε) = σ². We train f̂ on a random training
set D and look at the expected squared error at a fixed point x, averaging
over D and ε:

    E[(y − f̂(x))²] = (f(x) − E_D[f̂(x)])² + E_D[(f̂(x) − E_D[f̂(x)])²] + σ²
                   =        bias²        +          variance            + noise

The cross terms vanish because ε is independent of D and has mean zero, and
because f̂(x) − E_D[f̂(x)] has mean zero over D.

Reading it: simple models are wrong in the same way on every dataset (high
bias, low variance); flexible models chase each dataset's noise (low bias,
high variance). The noise term σ² is a floor no model can go below.

The picture from the slides: training error falls monotonically with model
complexity, test error is U-shaped.

=== note-bias-variance-from-book
domain: mathematics
title: Bias and variance, rewritten from Murphy
created: 2026-07-30
role: synthesis
state: rough
authorship: user
concepts: [concept-bias-variance-tradeoff, concept-statistical-estimation]
sources: [source-murphy-pml1]
---
Murphy phrases it for a parameter estimate instead of a prediction:

    MSE(θ̂) = E[(θ̂ − θ*)²] = (E[θ̂] − θ*)² + Var(θ̂)

so for an estimator: mean squared error = bias² + variance. Same shape as the
prediction version from the lecture, minus the irreducible noise term, because
here there is no fresh noisy y to predict.

Murphy's example that clicked: shrinking an estimate towards zero (e.g.
multiplying the sample mean by 0.9) adds bias but can reduce variance enough
that the MSE goes down. So a biased estimator can be *better*.

I think this is the same thing as the U-shaped test-error curve, just seen
from the estimator side. Written in July while re-reading for the retake.

=== note-map-estimation-priors
domain: mathematics
title: MAP estimation — a prior turns into an extra term
created: 2026-06-02
role: derivation
state: evolving
authorship: user
concepts: [concept-map-estimation, concept-bayes-theorem]
sources: [source-murphy-pml1]
evidence:
  - {type: derivation, ref: "github://noor-haddad/ml-exercises/murphy/map_4_5.pdf"}
---
MAP picks the mode of the posterior:

    θ_MAP = argmax_θ p(θ | D) = argmax_θ p(D | θ) p(θ)
          = argmax_θ [ log p(D | θ) + log p(θ) ]

(the evidence p(D) does not depend on θ, so it drops out).

So MAP = maximum likelihood + one extra term, the log-prior.

Worked case: parameters with an isotropic Gaussian prior θ ~ N(0, τ² I).

    log p(θ) = −‖θ‖² / (2τ²) + const

Plugging in and flipping the sign to get a minimization:

    θ_MAP = argmin_θ [ −log p(D | θ) + (1/(2τ²)) ‖θ‖² ]

If the likelihood is the Gaussian-noise linear model, the first term is the
sum of squared residuals over 2σ², so the whole thing is squared error plus a
constant times ‖θ‖², with the constant being σ²/τ² after rescaling.

Other direction: a narrow prior (small τ) → big penalty → parameters pulled
hard to zero; τ → ∞ → flat prior → back to plain MLE.

Laplace prior p(θ_j) ∝ exp(−|θ_j| / b) gives Σ|θ_j| instead of ‖θ‖².

=== note-eigenvectors-intuition
domain: mathematics
title: Eigenvectors — the directions a matrix only stretches
created: 2026-05-05
role: synthesis
state: evolving
authorship: user
concepts: [concept-eigendecomposition]
sources: [source-3b1b-linalg, source-strang-linalg]
contexts: [workspace-linalg-refresh]
---
Av = λv, v ≠ 0. Most vectors get knocked off their line by A; eigenvectors
stay on their span and only get scaled by λ (flipped if λ < 0).

How to find them: (A − λI)v = 0 has a non-zero solution only if
det(A − λI) = 0 — the characteristic polynomial. Its roots are the λs, then
solve for v in each null space.

Diagonalization: if A has n independent eigenvectors, stack them into V and
A = V Λ V⁻¹. Then A^k = V Λ^k V⁻¹ — powers become cheap.

Symmetric matrices are the nice case: real eigenvalues and an *orthonormal*
set of eigenvectors, A = Q Λ Qᵀ. This is the spectral theorem and it is why
covariance matrices behave so well.

3Blue1Brown's picture of a shear: only the horizontal axis stays on its line,
so the shear has just one eigen-direction.

=== note-covariance-matrix
domain: mathematics
title: The covariance matrix and its ellipse
created: 2026-05-09
role: synthesis
state: evolving
authorship: user
concepts: [concept-covariance-matrix, concept-eigendecomposition]
sources: [source-strang-linalg]
contexts: [workspace-linalg-refresh]
---
For centered data X (n × d): Σ = (1/n) XᵀX. Entry Σ_jk is the covariance of
feature j and feature k; the diagonal holds the variances.

Properties: symmetric, positive semi-definite (vᵀΣv = variance of the data
projected onto v, which is ≥ 0).

Geometric picture: the contour lines of a 2-D Gaussian with covariance Σ are
ellipses. Because Σ is symmetric, Σ = QΛQᵀ; the eigenvectors in Q are the
axes of the ellipse and √λ are the half-lengths along them. The longest axis
is the direction where the cloud of points is most spread out.

Correlation is covariance after dividing each feature by its standard
deviation, so it is scale-free and lies in [−1, 1].

=== note-svd-geometric
domain: mathematics
title: SVD as rotate–stretch–rotate
created: 2026-06-08
role: synthesis
state: evolving
authorship: user
concepts: [concept-svd, concept-eigendecomposition]
sources: [source-strang-linalg]
contexts: [workspace-linalg-refresh]
---
Every real matrix A (m × n) factors as A = U Σ Vᵀ with U, V orthogonal and Σ
diagonal with σ_1 ≥ σ_2 ≥ … ≥ 0.

Reading it right to left for a vector x: Vᵀ rotates, Σ stretches along the
axes, U rotates again. A circle becomes an ellipse whose half-axes are the
singular values.

Connection to eigen-things:

    AᵀA = V Σᵀ Σ Vᵀ   and   AAᵀ = U Σ Σᵀ Uᵀ

so the right singular vectors are eigenvectors of AᵀA and σ_i² are its
eigenvalues. Unlike the eigendecomposition, the SVD exists for every matrix,
including rectangular ones.

Rank = number of non-zero singular values.

=== note-low-rank-approximation
domain: mathematics
title: Low-rank approximation (unfinished)
created: 2026-06-10
role: synthesis
state: rough
authorship: user
concepts: [concept-low-rank-approximation, concept-svd]
sources: [source-strang-linalg]
contexts: [workspace-linalg-refresh]
---
Keep only the k largest singular values:

    A_k = Σ_{i=1..k} σ_i u_i v_iᵀ

Eckart–Young: A_k is the best rank-k approximation of A in both the
Frobenius and the spectral norm; the error is ‖A − A_k‖_F² = Σ_{i>k} σ_i².

Image compression experiment: a 512×512 grayscale photo needs 262,144
numbers; rank 20 needs 20·(512 + 512 + 1) ≈ 20,500. Started the rank 5/20/50
comparison but stopped here when exams took over.

Open question: could this be how recommender systems fill in missing ratings?
The user × movie matrix is mostly empty — if taste only has a few "directions",
a low-rank matrix could describe it, but the SVD needs every entry, so I don't
see how you would compute it with the holes.

=== note-queueing-littles-law
domain: mathematics
title: Little's law
created: 2026-07-06
role: synthesis
state: evolving
authorship: user
concepts: [concept-queueing-theory]
sources: []
---
In any stable system where things arrive, wait/get served, and leave:

    L = λ · W

L = average number of items in the system, λ = average arrival rate,
W = average time an item spends in the system.

Coffee shop version: 30 customers arrive per hour and each stays 10 minutes
on average → on average 30 · (1/6 h) = 5 people are inside.

What surprised me: it does not care about the arrival distribution, the
service order, or the number of servers. It only needs the long-run averages
to exist (a stable system — arrivals do not outpace service forever).

Rearranged: W = L / λ. If you can count how many are waiting and you know the
throughput, you know the average delay without timing anybody.

=== note-normal-distribution-standardizing
domain: mathematics
title: Standardizing and z-scores
created: 2026-04-16
role: synthesis
state: evolving
authorship: user
concepts: [concept-normal-distribution]
sources: [source-tuh-statlearn-slides]
---
If X ~ N(μ, σ²) then Z = (X − μ)/σ ~ N(0, 1). Standardizing lets one table
(or one scipy call) answer every normal question.

Example: exam points ~ N(60, 12²). P(X > 84) = P(Z > 2) ≈ 0.023.

The same move shows up in ML preprocessing: normalize each feature by
subtracting its mean and dividing by its standard deviation so features on
different scales (square metres vs number of rooms) become comparable. The
lecture called it "standardization"; the sklearn class is StandardScaler.

68–95–99.7 rule for ±1, 2, 3 σ.

=== note-central-limit-theorem-simulation
domain: mathematics
title: CLT by simulation
created: 2026-04-30
role: implementation
state: evolving
authorship: user
concepts: [concept-central-limit-theorem]
sources: [source-tuh-statlearn-slides]
evidence:
  - {type: implementation, ref: "github://noor-haddad/ml-exercises/clt_simulation.ipynb"}
---
Simulated means of n draws from a very skewed distribution (exponential,
λ = 1) for n = 1, 5, 30, 200, 10,000 repetitions each. The histogram of means
looks normal by n = 30 and the spread shrinks like 1/√n.

The statement: for i.i.d. X_i with mean μ and finite variance σ²,
√n (X̄_n − μ)/σ → N(0, 1) in distribution.

It needs finite variance — tried a Cauchy distribution and the sample means
never settle down, which was a nice surprise.

=== note-convexity-basics
domain: mathematics
title: Convex functions and why they matter for optimization
created: 2026-05-19
role: synthesis
state: evolving
authorship: user
concepts: [concept-convexity]
sources: [source-murphy-pml1]
---
f is convex if f(tx + (1−t)y) ≤ t f(x) + (1−t) f(y) for t ∈ [0, 1] — the chord
lies above the graph. For twice-differentiable f: Hessian positive semi-definite
everywhere.

Why it matters: every local minimum of a convex function is a global minimum,
so anything that walks downhill and stops at a flat point has found the best
answer. Squared error of a linear model is convex in the weights; the loss of
a neural network is not.

Strictly convex → the minimizer is unique. The sum of a convex loss and
λ‖w‖² is strictly convex for λ > 0, even if the loss alone was not strictly
convex (e.g. more features than data points).

=== note-kernel-density-estimation
domain: mathematics
title: Kernel density estimation
created: 2026-06-24
role: synthesis
state: rough
authorship: user
concepts: [concept-kernel-density-estimation]
sources: []
---
A histogram depends on where the bins start. KDE smooths instead: put a small
bump (the kernel) on every data point and add them up.

    f̂(x) = (1/(n h)) Σ_i K((x − x_i)/h)

K is usually the standard normal density; h is the bandwidth. Small h →
spiky, one bump per point; large h → oversmoothed, everything becomes one
blob. Silverman's rule of thumb for h ≈ 1.06 σ̂ n^(−1/5).

It is the continuous cousin of a histogram — and choosing h is the same kind
of problem as choosing the bin width.

=== note-markov-chains-stationary
domain: mathematics
title: Markov chains and stationary distributions
created: 2026-07-01
role: synthesis
state: evolving
authorship: user
concepts: [concept-markov-chains, concept-eigendecomposition]
sources: [source-bishop-prml]
---
State distribution as a row vector π_t; transition matrix P with rows
summing to 1; π_{t+1} = π_t P.

A stationary distribution satisfies π = πP, i.e. πᵀ is an eigenvector of Pᵀ
with eigenvalue 1. For an irreducible, aperiodic finite chain it is unique and
π_t converges to it from any start.

Weather toy: sunny→sunny 0.9, rainy→rainy 0.5. Solving π = πP gives
π = (5/6, 1/6).

PageRank is this: a random surfer's stationary distribution over web pages
(with random restarts so the chain is irreducible).

=== note-chain-rule-multivariable
domain: mathematics
title: Multivariable chain rule as Jacobian products
created: 2026-04-29
role: synthesis
state: evolving
authorship: user
concepts: [concept-chain-rule]
sources: [source-goodfellow-dl]
---
For y = f(g(x)) with x ∈ ℝⁿ, u = g(x) ∈ ℝᵐ, y ∈ ℝᵏ:

    ∂y/∂x = (∂y/∂u)(∂u/∂x)      (k×m)(m×n) = (k×n)

A long composition f_L(…f_2(f_1(x))) gives a product of L Jacobians. The
product is associative, so you can multiply it left-to-right or right-to-left,
and the cost differs hugely depending on the shapes:

- output is a single number (k = 1, like a loss): multiplying from the output
  side keeps every intermediate a row vector — cheap.
- a single input (n = 1): multiplying from the input side is the cheap order.

Noted this because the lecturer said "remember this when we get to neural
networks" and did not say why.

=== note-bloom-filter-false-positive-math
domain: mathematics
title: How often a Bloom filter lies
created: 2026-08-03
role: derivation
state: evolving
authorship: user
concepts: [concept-bloom-filters, concept-probability]
sources: []
evidence:
  - {type: derivation, ref: "github://noor-haddad/scratch/bloom_sim.py"}
---
Bit array of m bits, k independent hash functions, n inserted elements.

After inserting n elements, a given bit is still 0 with probability
(1 − 1/m)^(kn) ≈ e^(−kn/m).

A query for an element that was never inserted returns "present" only if all
k of its bits are 1:

    P(false positive) ≈ (1 − e^(−kn/m))^k

Minimized at k = (m/n) ln 2, where it equals about 0.6185^(m/n). With 10 bits
per element and k = 7: ≈ 0.8%.

It never gives a false negative — an inserted element's bits are all set and
stay set (no deletions in the basic version).

Simulation with m = 10,000, n = 1,000, k = 7: measured 0.83%, formula 0.82%.
