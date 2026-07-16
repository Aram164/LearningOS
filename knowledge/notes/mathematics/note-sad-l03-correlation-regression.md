---
id: note-sad-l03-correlation-regression
type: note
title: "SaD Lecture 03 — Ultimate Reference: Correlation & Regression"
created: "2026-07-11"
role: reference
state: evolving
authorship: mixed
concepts: [concept-correlation, concept-linear-regression, concept-normal-equation]
sources: [source-sad-ss26-lectures, source-fahrmeir-statistik, source-kelleher-fmlpda]
contexts: [workspace-m2-exam-prep]
---

> **Migration note (2026-07-17, Stage 2):** body preserved verbatim from
> `Plans/Math/sad/SaD/notes/lect03 correlation-regression/SaD_L03_Ultimate_Reference.md` (legacy tree).

# SaD Lecture 03 — Ultimate Reference: Correlation & Regression

*Synthesized from: SaD L03 (Leser, HU SoSe 2026) `Lecture-slides/03_correlation_regression.pdf` (48 slides) + Kelleher Ch 7 (error-based learning, the rent example) + the depth layer below.*
*Created: KW 28 (Jul 2026) — third per-lecture SaD unit (3-file variant, no Mock Exam).*

> **📎 This unit is keyed to the L03 *slides*. The deeper regression theory, the cross-exam study order, and the video library live in the authoritative doc — `Plans/ML/foundations/reference/Regression_SaD-AML-ISLP_Bridge.md`** (Tiers 0–5, 5 cross-wires, ordered study sequence, dual-purpose self-test). This reference does NOT duplicate the Bridge; it explains what L03 itself teaches and points into the Bridge for the AML/ISLP payoff and the probabilistic "why." Read this for the lecture; read the Bridge for the *program*.

---

## Table of Contents

1. [Correlation: comparing two samples](#1-correlation-comparing-two-samples)
2. [Covariance and the Pearson coefficient](#2-covariance-and-the-pearson-coefficient)
3. [Simple Linear Regression](#3-simple-linear-regression)
4. [Why RMSE / L2 loss](#4-why-rmse--l2-loss)
5. [The Four Issues (Anscombe warning)](#5-the-four-issues)
6. [Regression vs Classification; Supervised Setup](#6-regression-vs-classification)
7. [Multivariate Linear Regression — the Normal Equation](#7-multivariate-linear-regression)
8. [Gradient Descent](#8-gradient-descent)
9. [The Rent Example, Feature Scaling, Interpreting Weights](#9-the-rent-example)
10. [Beyond MLR & Correlation ≠ Causation](#10-beyond-mlr--correlation--causation)
11. [Summary and Cross-Wire Moments](#11-summary-and-cross-wire-moments)

---

## 1. Correlation: comparing two samples

**[Source: SaD L03, slides 5–7]**

Statistics constantly compares samples. Leser's taxonomy of comparisons (slide 5):

- **same feature, different samples, same universe** — two random draws of 50 CS 1st-semesters.
- **same feature, different samples, different universes** — 1st- vs 2nd-semester students.
- **different features, same sample, same universe** — age vs income, height vs weight. ← *this is the correlation setting.*
- **different features, different samples, different universes** — storks vs babies. ⚠️ nonsense correlations live here.

**Correlation** = a metaphor for "behaving similarly": when one value grows, the other tends to grow (**positive**) or shrink (**negative**), "on average." L03 studies only **linear** correlation. Three warnings Leser hammers (slide 5):

1. **You can correlate anything and always get *a* number** — a value near 0 vs near ±1 is what matters.
2. **Correlation ≠ causation** (see §10).
3. **Computation ≠ interpretation** — the coefficient is mechanical; meaning is your job.

**Visualization: the scatterplot** (*Streudiagramm*, slide 6) — plot (xᵢ, yᵢ) pairs; the shape reveals whether a linear summary is even appropriate (§5).

---

## 2. Covariance and the Pearson coefficient

**[Source: SaD L03, slides 8–11]**

For a sample with two continuous features x, y where each xᵢ corresponds to yᵢ ("same person/day/region"):

**Covariance:**
$$s_{xy} = \frac{1}{n-1}\sum_{i=1}^{n}(x_i-\bar{x})(y_i-\bar{y})$$

Sign tells direction: positive → move together; negative → move oppositely. But its **magnitude is unit-dependent** (depends on the scales of x and y) — not comparable across feature pairs.

**Pearson correlation coefficient** — covariance normalized by both standard deviations:
$$r_{xy} = \frac{s_{xy}}{s_x\, s_y} \in [-1, 1]$$

- **r ≈ +1**: strong positive linear relation; **r ≈ −1**: strong negative; **r ≈ 0**: no *linear* correlation.
- |r| → 1 ⇔ the points fall exactly on a line (the tighter, the closer the "pace" matches).
- Scale-free → **comparable across different feature pairs** (this is why we normalize).

> **Worked examples (slide 10, Pearson verified exactly).** For the 19-person height/weight/income/shoes table:
> - height vs **weight**: r = **0.67** (moderate positive)
> - height vs **income**: r = **−0.16** (essentially none)
> - height vs **shoes**: r = **0.94** (strong positive)
>
> Covariances are ~71 / −33 / 15 (scale-dependent, and the deck mixes the ÷n vs ÷(n−1) convention — see L02 §9); the **Pearson values are the comparable ones** and match the slide exactly. Football aside (slide 9): goals vs points had Σ = 22.5 → covariance 22.5/(6−1) = **4.5** (positive, as expected).

**Why r ∈ [−1, 1] — the Cauchy–Schwarz proof (slide 11).** Define centered, scaled vectors
$$a = \tfrac{1}{\sqrt{n-1}}(x_1-\bar{x},\dots,x_n-\bar{x}),\qquad b = \tfrac{1}{\sqrt{n-1}}(y_1-\bar{y},\dots,y_n-\bar{y}).$$
Then $\|a\| = s_x$, $\|b\| = s_y$, and $\langle a,b\rangle = s_{xy}$. Cauchy–Schwarz says $\langle a,b\rangle^2 \le \|a\|^2\|b\|^2$, i.e. $s_{xy}^2 \le s_x^2 s_y^2$, so $|s_{xy}|/(s_x s_y) = |r_{xy}| \le 1$. **Pearson r is literally the cosine of the angle between the two centered feature vectors** — the same dot-product/cosine idea as cosine similarity in k-NN (AML L02 §4.3).

---

## 3. Simple Linear Regression

**[Source: SaD L03, slides 13–16]**

r says *how much* the pairs deviate from a line; regression finds *which* line. A line is f(xᵢ) = k·xᵢ + d; we need slope k and intercept d. If |r| = 1 any two points suffice; if |r| < 1 we must *define* "best" line = the one minimizing total error. The standard choice: **least squares** — minimize the mean squared error
$$\text{MSE} = \frac{1}{n}\sum_{i=1}^{n}\big(y_i - f(x_i)\big)^2.$$

**Theorem (the closed-form solution):**
$$\boxed{\,k = r_{xy}\cdot\frac{s_y}{s_x}, \qquad d = \bar{y} - k\bar{x}\,}$$

**Derivation (slides 15–16).** Minimize $S = \sum (y_i - kx_i - d)^2$. Set partials to zero:
$$\frac{\partial S}{\partial k} = \sum 2(y-kx-d)(-x) = 0,\qquad \frac{\partial S}{\partial d} = \sum 2(y-kx-d)(-1) = 0.$$
With A = (1/n)Σx² and B = (1/n)Σxy, these become the *normal equations* $Ak + \bar{x}d = B$ and $\bar{x}k + d = \bar{y}$. Solving:
$$k = \frac{B-\bar{x}\bar{y}}{A-\bar{x}^2} = \frac{s_{xy}}{s_x^2} = r_{xy}\frac{s_y}{s_x},\qquad d = \bar{y}-k\bar{x}.$$
The intercept formula guarantees the line **passes through (x̄, ȳ)** — a useful sanity check.

---

## 4. Why RMSE / L2 loss

**[Source: SaD L03, slide 17]**

Three reasons the squared-error loss is the default:

1. **Differentiable everywhere** → you can set derivatives to zero (§3) or run gradient descent (§8). MAD ($\frac1n\sum|y_i-f(x_i)|$) "would also make sense" but is **not differentiable** at 0, so the clean calculus breaks.
2. **It's the L2 (Euclidean) member of the Minkowski distance family** $D(x,y)=(\sum|y_i-x_i|^p)^{1/p}$ — same p-norm family as the k-NN distances (AML L02 §4.2).
3. **Probabilistic optimality:** assuming **normally distributed errors**, minimizing squared error is the **maximum-likelihood** solution. (The MLE→MSE derivation is a SaD L08 / cross-wire staple — see the Bridge Tier 3 and `SaD_06-10…DeepPlan.md`. Don't derive it here; just know squared error ⇔ Gaussian-noise MLE.)

RMSE = √MSE just restores the original units; minimizing MSE, RMSE, or SSE (drop the 1/n) all give the **same** k, d.

---

## 5. The Four Issues

**[Source: SaD L03, slide 18 — the Anscombe-quartet warning]**

A fitted line (and r) can be dangerously misleading. Four canonical failure patterns:

- **Y1 — fine:** genuine linear relation, line is meaningful.
- **Y2 — non-linear relation** modelled by a line → systematically wrong (r underates a real curved dependence).
- **Y3 — outliers** drag the line and inflate/deflate r away from the bulk pattern.
- **Y4 — meaningless correlation:** e.g. an r driven entirely by one leverage point, or spurious.

**Lesson: always look at the scatterplot before trusting r or a regression line.** (This is Anscombe's quartet: four datasets with near-identical mean, variance, r, and regression line but completely different shapes.)

---

## 6. Regression vs Classification; Supervised Setup

**[Source: SaD L03, slides 21–22]**

- **Regression:** predict a **continuous** value (temperature, energy demand).
- **Classification:** predict a **discrete/nominal** value — binary (pass/fail) or multi-class (topic).
- **Ordinal prediction** sits in between (predict a grade) — special methods.
- **Structured output** (LLM answers, molecules) is beyond this course.

Both are **supervised learning**: given examples (x₁,…,xₘ, y), learn a function predicting y from the inputs; the labeled examples are the **training data / supervision signal**. L03 lists the course's other supervised models (MLR, Naïve Bayes, trees/RF, k-NN, ANNs) — MLR is the first and the template for "minimize a loss."

---

## 7. Multivariate Linear Regression

**[Source: SaD L03, slides 20, 23, 26–29]**

Keep one dependent y, allow **m input features**. Model with intercept k₀ and weights k₁…kₘ:
$$f(x_1,\dots,x_m) = k_0 + k_1 x_1 + \dots + k_m x_m,\qquad \text{minimize } \sum_{i=1}^{n}\big(f(x_i)-y_i\big)^2.$$

### The algebraic ("math-style") solution — the normal equation

Stack the data into the **design matrix A** (n × (m+1), a leading column of 1s for the intercept), weight vector **k**, target **y**. Then the loss is $\|Ak - y\|^2$. Introduce the error vector e = Ak − y; minimize $e^Te = (Ak-y)^T(Ak-y)$. Differentiating by k and setting to zero:
$$\boxed{\,k = (A^T A)^{-1} A^T y\,}$$

**Conditions (slide 28) — state these:** A must have **full (column) rank** (features linearly independent), $A^TA$ must be **non-singular** (else no inverse), and you need **n > m** (more instances than features). Ensure by preprocessing (remove duplicate/collinear columns).

**Cost (slide 29):** inverting the (m × m) matrix $A^TA$ is **O(m³)** (Gauss–Jordan) → time+memory blow up for large m, and **numerical stability** degrades (many small error terms). This is exactly why the iterative alternative exists. *(Depth — the geometry of the normal equation as an orthogonal projection, and ridge as $(A^TA+\lambda I)^{-1}$ — is Bridge Tier 2 & 5.)*

---

## 8. Gradient Descent

**[Source: SaD L03, slides 31–39]** — *the general optimizer that recurs for logistic regression and neural nets.*

**Setup:** the loss defines an **error surface** over parameter space; we want its minimum. GD starts at a random k and repeatedly steps **downhill along the negative gradient**.

**The gradient step per dimension j (slides 37–38).** For one instance, by the chain rule:
$$\frac{\partial}{\partial k_j}\big(f(x)-y\big)^2 = 2\big(f(x)-y\big)\cdot x_j.$$
Summed over all instances, the gradient in dimension j is
$$\text{step}(A,j) = 2\sum_{i=1}^{n}\big(f(x_i)-y_i\big)\,x_{j,i}$$
(the factor 2 gets absorbed into the learning rate). Update: $k_j \leftarrow k_j - \alpha\cdot\text{step}(A,j)$ for every j, repeat until movement < threshold t.

**The three knobs (slides 32, 34–35):**

- **Learning rate α** — too small → crawls; too large → oscillates/overshoots. Often adapted over iterations.
- **Start point** — random.
- **Stopping** — convergence: total movement (Σ|step|) below threshold t. Large t → stops early/suboptimal; tiny t → runs forever for little gain.

**Local minima (slide 33):** general error surfaces have many minima and GD (being local) can get stuck; classical escapes are multiple restarts, allowing temporary worsening (simulated annealing), or other step types. **Good news:** for **MLR with L2 loss the error surface is convex** → a single global optimum, so GD converges to *the* solution (proof omitted).

**Complexity (slide 39):** memory O(m·n); one `step()` is O(n); one full sweep O(m·n); number of iterations unknown. **Stochastic GD** — compute the step on only a subset of instances per iteration — is the standard speed-up (recurs in the NN lectures).

**Algebra vs GD:** exact/O(m³)/unstable-for-large-m vs iterative/scalable/needs-tuning. Same solution for convex MLR; GD is what generalizes to models with no closed form.

---

## 9. The Rent Example, Feature Scaling, Interpreting Weights

**[Source: SaD L03, slides 41–47 — Kelleher et al. rental-price example]**

Predict flat **rent** from size, floor, broadband rate. Running GD from a random k with a tiny α = 0.00000002:

- After **100 iterations**, weights moved random → fitted: bias −0.15, size 0.19 → **0.63**, floor −0.04 → **−0.18**, broadband 0.12 → **0.07**; error fell ~1,000,000 → ~3,000.

**Why the absurdly small α? (slide 45)** The **size** feature has much larger raw values than floor/rate, so its gradient is huge and steep → any normal α makes size overshoot and diverge, while a tiny α barely moves the other dimensions → agonizingly slow. **Remedy: feature scaling** — standardize all features to comparable ranges: min-max into [0,1], or **z-scores** (assuming rough normality). This is the same standardization as L02 §8 / L08, and the same fix k-NN needs (AML L02 §6). After scaling you can use a sane α and all dimensions converge together.

**Interpreting weights (slide 47):**

- **Sign** = direction of effect: larger flats → higher rent (+); higher floor → lower rent (−) here.
- **Relative magnitude ≠ importance unless features are scaled.** You **cannot** say "size is 9× as important as broadband" from raw-scale weights — the weight also absorbs the feature's units/scale. Only after scaling do magnitudes become comparable.

---

## 10. Beyond MLR & Correlation ≠ Causation

**[Source: SaD L03, slides 48–50]**

**Variants of MLR (slide 48):**

- **Logistic regression** — same machinery applied to **classification** (SaD L15 / AML L05).
- **Non-linear regression** — replace xᵢ by non-linear features (xᵢ², …) → still linear *in the weights* (AML L04, Bridge Tier 5).
- **Ridge regression** — better with correlated features; adds an L2 penalty (the $(A^TA+\lambda I)^{-1}$ fix).
- **Lasso** — L1 penalty forces most weights to **zero** → sparse, interpretable models. Both ridge and lasso = **regularization** (AML L04 / ISLP 6.2 / Bridge Tier 5).

**What MLR is bad at:** highly correlated features → arbitrary/unstable weights (use another method); can't produce structured output.

**Correlation ≠ Causation (slides 49–50) — the closing law.** A correlation can arise from:

- **pure chance** (July Berlin temperatures vs a die showing 25–30);
- **a common cause / confounder** (drug dose ↔ mortality, both driven by disease severity);
- **an inappropriate mixed population** (income ↔ shoe size, because sex confounds both).

**Getting to causation is an intellectual process, not a statistical one:** exclude confounders, design **interventional experiments** (change the generating process of one variable, observe the other — e.g. a controlled cell-line model), and if no other explanation survives, provisionally assume causation until disproven. Ties back to L02's Simpson/sampling-bias theme.

---

## 11. Summary and Cross-Wire Moments

### 11.1 Key takeaways

- **Covariance** gives direction (unit-dependent); **Pearson r = s_{xy}/(s_x s_y) ∈ [−1,1]** is the scale-free strength of *linear* association (= cosine of the centered vectors).
- **Simple LS line:** **k = r·s_y/s_x, d = ȳ − k·x̄** — passes through (x̄, ȳ).
- **L2 loss** because it's differentiable and = Gaussian-noise MLE.
- **MLR two ways:** normal equation **k = (AᵀA)⁻¹Aᵀy** (exact, O(m³), needs full rank & n>m) vs **gradient descent** (iterative, scalable, convex for L2 so global optimum). Gradient step = 2Σ(f(xᵢ)−yᵢ)·x_{j,i}.
- **Feature scaling** is what makes GD converge and weights comparable.
- **Correlation ≠ causation** — always.

### 11.2 Cross-wires

1. **→ the Regression Bridge** (`…/reference/Regression_SaD-AML-ISLP_Bridge.md`) is the authoritative study doc: Tier 1 = this lecture *cold*, Tier 2 = the linear-algebra upgrade, Tier 3 = the MLE "why," Tier 5 = regularization, plus the ordered sequence + verified video library. **Use it for the plan; use this for the lecture.**
2. **L03 ↔ AML L03/L04:** SaD's MLR + GD is AML's linear/polynomial regression; the normal equation and GD are shared. AML adds bias-variance and regularization depth.
3. **L03 feature scaling ↔ L02 §8 / L08 (z-scores) / AML L02 §6:** one standardization idea, four homes.
4. **L03 Pearson (cosine of centered vectors) ↔ AML L02 §4.3 cosine similarity:** same dot-product geometry.
5. **L03 GD ↔ SaD L15 / AML L08–L09 (neural nets):** the identical optimizer; a 1-layer ANN *is* MLR ("drop φ"). L03 is where GD is born.
6. **L03 MLE-with-normal-errors ↔ SaD L08 (MLE→MSE):** the probabilistic justification of L2 loss.

### 11.3 What's next

- **L04 (Probability & Bayes + Naïve Bayes):** axioms → conditional probability → Bayes (the formal home of L01 §5/§8) → the Naïve Bayes classifier.

---

*Document version 1.0 — KW 28 (Jul 2026). Pearson values (0.67, −0.16, 0.94) verified against the slide; covariance convention (÷n vs ÷(n−1)) noted per L02 §9. Deep theory intentionally delegated to the Regression Bridge.*
*Supports Block N1/N5 (regression). SaD steps remain F.* in Chat1.*
