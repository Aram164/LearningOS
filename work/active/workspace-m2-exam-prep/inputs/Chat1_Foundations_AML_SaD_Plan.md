# Chat 1: Foundations — AML × SaD × ISLP Step-by-Step Study Plan

*Generated: 21 April 2026 (KW 17) | Revised after deep-reading all lecture PDFs*
*Updated: 20 May 2026 (KW 21) — SaD speed-run + AML L01 + ISLP 2.1 completed*
*Updated: 10 Jun 2026 (KW 24) — **wired to `Plans/ML/foundations/reference/AML-SaD_Master_Wiring.md`** (the cross-module spine, built from reading all AML L01–L11 + SaD 01–15 decks). Per-block pointers added below; Block K corrected (AML L07 has NO SVM — see Wiring §4).*
*Updated: 1 Jul 2026 (KW 27) — **book layer perfected for every AML lecture.** The crosswalk now covers **L02–L10** (`AML/my notes/AML_Book-Concept-Crosswalk_L02-L10.md`, slide-verified + PDF-TOC-verified): Blocks I/J/K/L/M got exact scope-flagged book readings (K3 rewritten — kernels-without-SVM route via ESL §4.5.1 + CS229 Ch 5; L4 corrected — **no batch norm in AML L09**; M2/M4 upgraded with Murphy Ch 14/§15.2). L11 map preliminary until the 2026 RNN deck posts.*
*Status (KW 24): SaD 01-03, 06 (slides 1-35) done. AML L01, L02 done. ISLP 2.1 through 2.1.3 done. ISLP 5.1 done. SaD 2025 L11 (instance-based) done. SaD 04 NOT yet done. Block B COMPLETE (B1 ✅ B2 ✅ B3 ✅). Block D: D2, D3, D3b, D4 ✅ — D1 (ISLP 2.1 pp 20-25) + D5 (ISLP 2.2) + D-test still ⬜. Next: F.D1 → F.D5 → F.E3-4 → F.H → F.I1. Exam-driven from KW 27: Block N. SaD 2025 video supplements added inline to Blocks C, F, G, J, K, L (KW 24).*

> **🔗 The wiring layer.** This plan defines *what and in which order*. Four companion docs define *how AML and SaD connect*:
> | Doc | Covers | Blocks |
> |---|---|---|
> | **`Plans/ML/foundations/reference/AML-SaD_Master_Wiring.md`** | the full spine: lecture map, 4 pipelines, 18 cross-wires, corrections, wired session sequences | all |
> | **`Plans/ML/foundations/AML/my notes/AML_Book-Concept-Crosswalk_L02-L10.md`** | every AML L02–L10 concept → exact section/page in 7 book sources, scope-flagged (extended to L07–L10 KW 27; prelim. L11 map) | D, E, H, I, J, K, L, M |
> | `Plans/ML/foundations/AML/my notes/lect02 KNN-classifier/AML_L02_Ultimate_Reference.md` | k-NN, bias-variance, CV, metrics (part of the L02 unit) | D |
> | `Plans/ML/foundations/reference/Regression_SaD-AML-ISLP_Bridge.md` | regression deep bridge (Tiers 0–5) | E, H |
> | `Plans/Math/sad/SaD/notes/SaD_06-10_Probability-Inference_DeepPlan.md` | probability & inference core | G, J |
>
> **📌 The single-study-script rule (KW 27):** once a lecture has a **complete unit** in `AML/my notes/lectNN …/`, its **Mini Plan is the ONLY study script** for that lecture — the block tables below are just the **step-ID ledger**, and the Wiring §5 sequences are superseded for that lecture. Units exist for **AML L02–L07** (L08+ pending). For lectures *without* a unit yet, use Master Wiring §2-C/§2-D + §5 as the study guide.

---

## Step ID Convention

All steps in this plan use the prefix **F** (Foundations). Reference format: **F.{Block}.{Step#}**

| ID | Meaning | Example |
|---|---|---|
| F.A1 | Block A, Step 1 (SaD 01) | "Completed F.A1 and F.A2" |
| F.E3 | Block E, Step 3 (ISLP Ch 3.1-3.2) | "Starting F.E3 tomorrow" |
| F.A-test | Block A self-test | "Passed F.A-test" |
| F.N2 | Block N, Step 2 (SaD cheat sheets) | "F.N2 in progress" |

**When updating SEMESTER-STATUS.md:** write step IDs exactly as above. This chat (the brain) uses them to track dependencies.

---

## Why This Plan Exists

The original Theorieplan schedules ISLP 2.1 in KW 16 as first reading. But ISLP 2.1 uses E[X] and Var(ε) notation on page 20 — concepts that SaD doesn't formally introduce until lecture 06 (Random Variables). That's the gap that tripped you up. This plan fixes it by building a strict prerequisite chain: **you never read something that uses a concept you haven't seen yet.**

---

## Prerequisite Dependency Graph

Each arrow means "you must understand A before B makes sense."

```
SaD 01 (intro: mean, median, precision/recall)
  │
  ▼
SaD 02 (basics: sample mean x̄, variance s², std dev s)
  │
  ├──────────────────────────────────────┐
  ▼                                      ▼
AML L01 (supervised/unsupervised)    SaD 04 (probability, Bayes' theorem)
  │                                      │
  ▼                                      │
ISLP 2.1 pp 15-19 (Y = f(X) + ε)       │
  │                                      │
  ▼                                      ▼
SaD 06 slides 1-35 ◄────────────────────┘
(E[X], Var(X), correspondence
 sample mean ↔ expected value)
  │
  ├─────────────────────┐
  ▼                     ▼
ISLP 2.1 pp 20-25    SaD 11 slides 39-47
(reducible/irreduc.)  (bias-variance intuitive)
  │                     │
  ▼                     ▼
SaD 13 (K-NN algorithm, distances)
  │
  ▼
AML L02 (K-NN + bias-variance + generalization)
  │
  ▼
ISLP 2.2.1-2.2.2 (MSE, bias-variance decomposition)
```

For regression:
```
SaD 02 (variance, std dev)
  │
  ▼
SaD 03 (correlation, simple regression, MLR, gradient descent)
  │                      ← uses partial derivatives ∂S/∂k
  ▼
ISLP Ch 3.1-3.2 (simple linear regression in ML language)
  │
  ▼
AML L03 (linear regression: β̂ = (XᵀX)⁻¹Xᵀy, MSE)
  │
  ▼
SaD 08 slides 29-36 (WHY MSE: normal errors → MLE → MSE)
```

For classification:
```
SaD 04 (probability, conditional P, Bayes' theorem, Naïve Bayes)
  │
  ▼
SaD 14 (Naïve Bayes extended: smoothing, numerical features)
  │
  ▼
AML L05 (logistic regression: P(class|X) via sigmoid)
  │                      ← both compute P(class|features), different approach
  ▼
ISLP Ch 4.1-4.3 (classification, logistic regression)
```

For neural networks:
```
SaD 03 (gradient descent algorithm introduced)
  │
  ▼
SaD 15 slides 1-12 (perceptron, 1-layer ANN = MLR without activation)
  │
  ▼
AML L07 (perceptron + SVM + kernel trick)
  │
  ▼
SaD 15 slides 12-38 (MLP, backpropagation overview)
  │
  ▼
AML L08 (FFN/MLP deep dive) → AML L09 (backprop derivation)
```

---

## SaD Coverage Map

Every SaD lecture and exercise is covered in this plan. This map shows exactly where.

### SaD Lectures → Blocks

| SaD Lecture | Title | Block(s) | Step IDs | Depth |
|-------------|-------|----------|----------|-------|
| **SaD 01** ✅ | Introduction | A | F.A1 | Full (42 slides) |
| **SaD 02** ✅ | Basic Concepts | A | F.A2 | Full (39 slides) |
| **SaD 03** ✅ | Correlations & Regression | E | F.E1, F.E2 | Full (37 slides, split into simple + multivariate/GD) |
| **SaD 04** | Probability Theory | F | F.F1 | Full (59 slides) |
| **SaD 05** | Combinatorics | G | F.G4 | Full (34 slides) — low AML relevance, SaD exam topic |
| **SaD 06** ✅ | Random Variables | C + G | F.C1–C3 (slides 1-35), F.G1 (slides 35-60) | Full, split across two blocks — slides 1-35 done, slides 35-60 remaining |
| **SaD 07** | Discrete Distributions | G | F.G2 | Full (33 slides) |
| **SaD 08** | Normal Distribution | G | F.G3 | Full (38 slides, incl. MLE→MSE derivation) |
| **SaD 09** | Estimation | J | F.J1 | Full (45 slides) |
| **SaD 10** | Statistical Tests | J | F.J4 | Full (65 slides) — important SaD exam topic |
| **SaD 11** | Intro to Data Science | B + D | F.B2 (slides 1-22), F.D3b (slides 23-38: evaluation metrics, data pipelines), F.D4 (slides 39-47) | Full, split across three readings |
| **SaD 12** | Tree-Based Learning | K | F.K1 | Full (36 slides) — SaD-only, not in AML |
| **SaD 13** | Similarity-Based Learning | D | F.D2 | Full (32 slides) |
| **SaD 14** | Probability-Based Learning | I | F.I1 | Full (29 slides) |
| **SaD 15** | Neural Networks | L | F.L1 (slides 1-12), F.L3 (slides 12-38) | Full, split: perceptron early, MLP+backprop later |

### SaD Exercises → Blocks

| Exercise | Topic | Block | Step ID | When to do |
|----------|-------|-------|---------|------------|
| **UE2** | Features, Korrelation & lineare Regression | E | F.E5 | After seeing regression from SaD 03, ISLP Ch 3, and AML L03 |
| **UE3** | Wahrscheinlichkeitsrechnung & Gradient Descent | F | F.F2 | After SaD 04 (probability) + SaD 03 (GD section) |
| **UE4** | Zufallsvariablen & Diskrete Verteilungen | G | F.G5 | After SaD 06 + SaD 07 |
| **UE5** | Normalverteilung & Parameterschätzung | J | F.J5 | After SaD 08 + SaD 09 |
| **UE6** | Hypothesentests & Klassifikation | I | F.I4 | After SaD 10 + SaD 14 |
| **UE7** | Clustering & Klausurvorbereitung | K + N | F.K4 (clustering), F.N1 (exam prep) | Split: K-means with Block K, exam prep in Block N |

### SaD-Only Topics (not in AML — must study independently)

These SaD lectures have **no AML counterpart**. They rely entirely on the SaD self-tests and exercises below for reinforcement:

| Topic | SaD Lecture | Block | Why it matters for the SaD exam |
|-------|------------|-------|---------------------------------|
| Combinatorics | SaD 05 | G | Counting problems appear in probability questions |
| Discrete Distributions | SaD 07 | G | Binomial/Poisson calculation questions are common |
| Normal Distribution & CLT | SaD 08 | G | z-score lookups, CLT applications, MLE derivation |
| Estimation & Confidence Intervals | SaD 09 | J | Confidence interval calculations are exam staples |
| Statistical Tests | SaD 10 | J | Hypothesis testing is a major SaD exam section |
| Decision Trees & Random Forests | SaD 12 | K | Tree construction by hand (information gain) is a classic exam task |
| K-Means Clustering | SaD UE7 | K | Unsupervised learning, not in AML at all |

---

## Block-by-Block Reading Plan

The plan is organized into **prerequisite blocks**, not calendar weeks. Each block unlocks the next. Within a block, the numbered order is strict — don't skip ahead.

---

### BLOCK A: Statistics Vocabulary ✅ COMPLETED
**Time: ~3 hours | Prerequisites: none**

This block gives you the language of statistics. Every concept here will be used constantly.

| Step | Source | Pages/Slides | What you learn | Why it matters |
|------|--------|-------------|----------------|----------------|
| A1 | **SaD 01** | 42 slides | Mean, median, mode, histogram, precision/recall, conditional probability via contingency tables, false positives/negatives | Builds your statistics vocabulary from scratch. The medical test example (slides 12-22) introduces TP/FP/FN/TN and precision/recall — you'll see these again in AML and SaD 11. |
| A2 | **SaD 02** | 39 slides | Population vs sample, frequencies, **sample mean x̄ = (1/n)Σxᵢ**, median, mode, quantiles, boxplots, **sample variance s² = (1/(n-1))Σ(xᵢ-x̄)²**, standard deviation s, range | These are the building blocks. The variance formula appears in every single ML lecture. Note: this is SAMPLE variance (from data), not population variance (from a random variable) — that distinction comes in Block C. |

**Self-test after Block A:**
- [ ] Compute the mean and variance of {3, 7, 7, 9, 14} by hand
- [ ] Explain precision vs recall in one sentence each
- [ ] Given a contingency table, compute precision and recall

---

### BLOCK B: What Is Machine Learning? (partially done)
**Time: ~3.5 hours | Prerequisites: Block A ✅**

Three sources that all answer "what is ML?" from different angles. No heavy math.

| Step | Source | Pages/Slides | What you learn | Why it matters |
|------|--------|-------------|----------------|----------------|
| B1 ✅ | **AML L01** slides | 73 slides (speed-run: focus slides 1-20, skim 21-73) | History of ML (three waves), supervised vs unsupervised learning, Tom Mitchell's definition, train/test concept | The history (slides 6-20) gives you context but isn't exam-critical. The key definitions are on slides 4-5 and the "recall" slides at the start of L02. |
| B2 ✅ | **SaD 11** slides 1-22 | 22 slides | Data Science vs ML vs AI, supervised vs unsupervised, classification vs regression, loss functions (MSE for regression, cross-entropy for classification), train/test split | SaD 11 covers the same ground as AML L01 but adds loss functions and train/test formalism. Seeing the same concepts twice from different professors cements them. |
| B3 ✅ | **ISLP 2.1 pages 15-19 ONLY** | ~5 pages | Y = f(X) + ε (the fundamental statistical learning equation), prediction vs inference, parametric vs non-parametric methods | **STOP at page 19.** Pages 20+ use E[...] notation you haven't seen yet. Pages 15-19 are safe — they introduce the idea that data = true pattern + noise, which is the foundation for everything. |

**Self-test after Block B:**
- [ ] State the supervised learning setup: given (X, Y) pairs, learn f̂ such that…
- [ ] Write Y = f(X) + ε and explain each symbol
- [ ] Name one advantage of a simple model over a complex one (hint: interpretability)
- [ ] What's the difference between classification and regression? Give one example of each.

---

### BLOCK C: The Expected Value Bridge ✅ COMPLETED (via SaD 06 speed-run)
**Time: ~2.5 hours | Prerequisites: Block A (sample mean/variance) ✅, basic probability concepts from SaD 01 ✅**

> 🎬 **SaD 2025 supplement:** `Plans/Math/sad/SaD/SaD-2025/` — **2025 L05 (random_variables) + L06 (expected_values)**. The 2026 slides compress E[X] into one lecture; 2025 splits it into two. If the bridge slides don't click, watch these — they go step by step through E[X], Var(X), and the sample↔population connection with more examples.

**This is the block that was missing from my original plan.** SaD 06 slides 1-35 formally introduce E[X] and Var(X) and explicitly connect them to the sample mean and variance you learned in Block A. After this block, ISLP's notation will make sense.

| Step | Source | Pages/Slides | What you learn | Why it matters |
|------|--------|-------------|----------------|----------------|
| C1 | **SaD 06** slides 1-13 | 13 slides | Random variable X: Ω→ℝ, discrete vs continuous, CDF F(x) = P(X ≤ x), probability function for discrete variables | A random variable is just "the number you get from a repeatable experiment." A die throw is a random variable. |
| C2 | **SaD 06** slides 14-24 | 11 slides | Continuous random variables, PDF f(x) = F'(x), properties (total area = 1, P(X=x) = 0 for continuous), equal and exponential distributions, independence of random variables | The PDF is just the derivative of the CDF. For continuous variables, you ask "probability of being in a range", not "probability of being exactly this value." |
| C3 | **SaD 06** slides 25-35 | 11 slides | **E[X] = Σxᵢpᵢ** (discrete) or **∫xf(x)dx** (continuous), rules: E[X+Y] = E[X]+E[Y], E[aX+b] = aE[X]+b. **Var(X) = E[(X-μ)²] = E[X²]-μ²**, rules: Var(aX+b) = a²Var(X). **The correspondence table (slide 35): sample mean x̄ ↔ E[X], sample variance s² ↔ Var(X).** | This is THE key bridge. Slide 26 literally says: "When we replace 'sample' with 'random variable', the mean becomes the expected value." After this, when ISLP writes E[(Y-Ŷ)²], you'll read it as "the average squared prediction error." |

**Self-test after Block C:**
- [ ] What is E[X] for a fair die? (Answer: 3.5)
- [ ] What is Var(X) for a fair die? (Answer: 35/12 ≈ 2.92)
- [ ] If E[X] = 5 and Var(X) = 2, what are E[3X+1] and Var(3X+1)?
- [ ] Explain in one sentence: "E[X] is the population version of x̄"

---

### BLOCK D: Bias-Variance + K-NN
**Time: ~5.5 hours | Prerequisites: Blocks A, B, C**

Now you have all the tools. This block is the core of KW 17.

| Step | Source | Pages/Slides | What you learn | Why it matters |
|------|--------|-------------|----------------|----------------|
| D1 | **ISLP 2.1 pages 20-25** | ~6 pages | Reducible vs irreducible error: E[(Y-Ŷ)²] = [f(X)-f̂(X)]² + Var(ε). Flexibility-interpretability tradeoff. | **Now this formula makes sense.** E[...] is the average you learned in Block C. Var(ε) is the variance of the noise. The reducible part is what your model gets wrong; the irreducible part is pure noise. |
| D2 | **SaD 13** | 32 slides | K-NN algorithm (1-NN and k-NN pseudocode), Voronoi cells, effect of different k values (slides showing k=1,3,5,15), aggregation functions (majority vote, weighted), class imbalance, **distance measures**: Minkowski (p=1 Manhattan, p=2 Euclidean), Jaccard, Cosine, edit distance, indexing for fast search | SaD 13 gives you the ALGORITHM cleanly. Slide 8 has the actual pseudocode. Slides 11-12 show how k=1 overfits and k=15 smooths — this is bias-variance in action. |
| D3 | **AML L02** | 79 slides | Formal treatment of k-NN, **bias-variance tradeoff** (slides 40-57): underfitting = high bias, overfitting = high variance, generalization gap, train/validation/test split, cross-validation (k-fold, leave-one-out), distance functions (Lq norms) | AML L02 goes deeper than SaD 13 on the theory side: the bias-variance U-curve (slide 55), cross-validation details (slides 52-57), and formal distance functions. Having seen k-NN from SaD 13 first, these slides will feel like a natural deepening. |
| D3b | **SaD 11 slides 23-38** | 16 slides | Evaluation metrics (accuracy, precision, recall, F1 in ML context), confusion matrix, ROC/AUC, data preprocessing and pipelines, feature engineering | These slides bridge between the ML overview (Block B) and the bias-variance theory. The evaluation metrics are important for both SaD and AML exams — you'll need to compute precision/recall from confusion matrices. |
| D4 | **SaD 11 slides 39-47** | 9 slides | Inductive bias, overfitting/underfitting (SaD's version), variance-bias tradeoff diagram, cross-validation, bootstrapping | SaD 11 covers the same tradeoff as AML L02 but with different examples and adds bootstrapping. Third exposure to the same core idea — it should be solid now. |
| D5 | **ISLP 2.2.1-2.2.2** (pp 28-34) | ~7 pages | MSE = (1/n)Σ(yᵢ-f̂(xᵢ))², training MSE vs test MSE, the U-shaped test MSE curve, **full bias-variance decomposition**: E[(y₀-f̂(x₀))²] = Var(f̂(x₀)) + [Bias(f̂(x₀))]² + Var(ε). Figure 2.12 showing bias², variance, and test MSE curves. | ISLP presents the formal decomposition and the famous three-panel figure. The book says "the mathematical proof is beyond the scope" — but you now understand every symbol in the formula. |

**Self-test after Block D:**
- [ ] Write k-NN pseudocode from memory (input: dataset D, query point z, parameter k; output: predicted class)
- [ ] Draw the bias-variance U-curve. Label the axes and the regions (underfitting, sweet spot, overfitting)
- [ ] Explain: k=1 in k-NN → high variance, k=N → high bias. Why?
- [ ] State the bias-variance decomposition and explain each of the three terms
- [ ] What is the difference between validation set and test set?

**SaD exam focus (SaD 13):**
- [ ] Given a 2D dataset of 8 labeled points and a query point, classify it using k-NN with k=3 (compute distances, find neighbors, majority vote)
- [ ] Name 4 distance/similarity measures from SaD 13 and state when each is appropriate (e.g., Jaccard for sets, cosine for text, edit distance for strings)
- [ ] What is a Voronoi cell and how does it relate to 1-NN?

---

### BLOCK E: Correlation & Linear Regression
**Time: ~6 hours | Prerequisites: Block A (mean, variance), Block D (MSE concept), partial derivatives**

> **Optional supplement:** [TU Python-for-ML Sheet 4](https://github.com/mahmutoezmen/Python-for-ML-Course/tree/main/4.%20Sheet) — hands-on linear algebra exercises in Python. Do alongside or after F.E to practice the matrix operations behind β̂ = (XᵀX)⁻¹Xᵀy.

This is the mathematical heart of early AML. SaD 03 covers the same topic as AML L03 — but SaD derives it from correlation (statistical view) while AML derives it from loss minimization (ML view).

| Step | Source | Pages/Slides | What you learn | Why it matters |
|------|--------|-------------|----------------|----------------|
| E1 ✅ | **SaD 03** slides 1-16 | 16 slides | Correlation (covariance sxy, Pearson coefficient rxy ∈ [-1,1], proof via Cauchy-Schwarz), **simple linear regression**: f(x) = kx + d where k = rxy·sy/sx, d = ȳ - k·x̄. Proof by partial derivatives ∂S/∂k = 0, ∂S/∂d = 0. Why RMSE (differentiable, unlike MAD). | SaD derives regression from correlation. The key proof (slides 13-14) uses partial derivatives to minimize Σ(yᵢ - kxᵢ - d)². This is the SAME minimization AML does in matrix form. |
| E2 ✅ | **SaD 03** slides 17-37 | 21 slides | **Multivariate linear regression** in matrix form: Ak-y, solution k = (AᵀA)⁻¹Aᵀy. Discussion of matrix inverse issues (O(m³), numerical stability). **Gradient descent algorithm** (slides 29-37): error surfaces, learning rate α, convergence, local minima, partial derivatives for GD, stochastic GD mention, complexity analysis. | SaD 03 already introduces BOTH the closed-form solution AND gradient descent! This means when you see AML L03 (closed form) and later AML L06 (gradient descent), you've already seen both ideas. The GD section (slides 29-37) is surprisingly detailed — pseudocode, learning rate effects, convergence diagrams. |
| E3 | **ISLP Ch 3.1-3.2** | ~20 pages | Simple linear regression: β₀, β₁ estimated by least squares, residual plots, R², RSE, confidence intervals for coefficients. Multiple linear regression: β̂ = (XᵀX)⁻¹Xᵀy (same as SaD's k = (AᵀA)⁻¹Aᵀy with different notation), F-statistic, variable selection. | ISLP is the deepest treatment. It assumes you've seen the formulas (you have, from SaD 03) and adds interpretation: what do coefficients mean? How do you check if the model is good? R² and residual analysis. |
| E4 | **AML L03** | lecture slides | Closed-form OLS, MSE loss, model evaluation | Having seen regression three times (SaD 03 → ISLP Ch 3 → AML L03), you can focus on what AML adds: the ML-specific framing (loss minimization, model selection). |
| E5 | **SaD UE2** | exercise | Features, Korrelation & lineare Regression — practice problems | Do these after seeing all three sources. The exercises reinforce computation skills. |

**Cross-wire moment:** SaD writes f(x) = kx + d with k = rxy·sy/sx. ISLP writes ŷ = β₀ + β₁x with β₁ = Σ(xᵢ-x̄)(yᵢ-ȳ) / Σ(xᵢ-x̄)². AML writes ŷ = wᵀx with w = (XᵀX)⁻¹Xᵀy. Same thing, three notations. k = β₁ = w.

**Self-test after Block E:**
- [ ] Given 5 data points, compute the Pearson correlation and regression line by hand
- [ ] Derive the closed-form solution β̂ = (XᵀX)⁻¹Xᵀy from ∂L/∂β = 0
- [ ] Explain gradient descent in 3 sentences: start point, update rule, stopping criterion
- [ ] What happens if the learning rate α is too large? Too small?

**SaD exam focus (SaD 03):**
- [ ] Compute covariance sxy and Pearson rxy from a small dataset by hand (use the SaD formulas, not matrix notation)
- [ ] From rxy, compute the regression coefficients k = rxy·sy/sx and d = ȳ − k·x̄
- [ ] Explain why we minimize Σ(yᵢ − kxᵢ − d)² and not Σ|yᵢ − kxᵢ − d| (hint: differentiability)
- [ ] Write the gradient descent update rule as it appears in SaD 03 (slides 29-37) and sketch an error surface with a trajectory

---

### BLOCK F: Probability & Bayes
**Time: ~4 hours | Prerequisites: Block A (frequencies)**

> 🎬 **SaD 2025 supplement:** `Plans/Math/sad/SaD/SaD-2025/` — **2025 L04 (probability_with_notes)**. Same content as SaD 04 but an annotated version with the instructor's handwritten notes on the slides. Especially useful for the conditional probability section and the Naïve Bayes derivation.

This block builds the probability foundation for classification and Naïve Bayes.

| Step | Source | Pages/Slides | What you learn | Why it matters |
|------|--------|-------------|----------------|----------------|
| F1 | **SaD 04** | 59 slides | Event spaces, probability axioms, accuracy for nominal variables, Laplace experiments, **conditional probability P(A|B)**, multiplication rule, **Bayes' theorem P(A|B) = P(B|A)·P(A)/P(B)**, independence, **Naïve Bayes classifier** (assuming conditional independence of features given class) | The Naïve Bayes classifier is the first real ML algorithm from the probabilistic side. SaD 04's spam detection example (slides 7-) builds it step by step. Understanding Bayes' theorem here directly prepares you for logistic regression (Block I). |
| F2 | **SaD UE3** | exercise | Wahrscheinlichkeitsrechnung & Gradient Descent practice | Combines probability practice with GD practice from SaD 03. |

**Self-test after Block F:**
- [ ] State Bayes' theorem and use it to compute P(ill|positive test) given P(positive|ill)=0.99, P(positive|healthy)=0.10, P(ill)=0.02
- [ ] Explain the "naïve" assumption in Naïve Bayes
- [ ] Why does Naïve Bayes work well despite the clearly wrong independence assumption?

**SaD exam focus (SaD 04):**
- [ ] Given a training table with 3 features and 2 classes, classify a new instance using Naïve Bayes (show the P(C)·ΠP(xᵢ|C) computation for each class)
- [ ] Define: event space, σ-algebra, probability measure — in plain language
- [ ] Two events A and B are independent iff P(A∩B) = P(A)·P(B). Give an example of two events that are NOT independent
- [ ] Compute P(A∪B) when A and B are not mutually exclusive

---

### BLOCK G: Distributions & Why MSE
**Time: ~5 hours | Prerequisites: Block C (E[X], Var), Block E (regression)**

> 🎬 **SaD 2025 supplement:** `Plans/Math/sad/SaD/SaD-2025/` — **2025 L07 (discrete_distributions) + L08 (normal_distribution)**. Direct match to SaD 07 and SaD 08. Particularly valuable for G3: L08 walks through the MLE→MSE derivation at lecture pace, which is easy to rush when reading slides alone. Also: **[jbstatistics](https://www.youtube.com/@jbstatistics)** on YouTube — short exam-style videos on Binomial, Poisson, Normal, z-scores, CLT (tagged `SaD` in LEARNING-RESOURCES §2).

This block completes your understanding of random variables and connects the normal distribution to MSE via Maximum Likelihood.

| Step | Source | Pages/Slides | What you learn | Why it matters |
|------|--------|-------------|----------------|----------------|
| G1 | **SaD 06** slides 35-60 | 25 slides | Var(aX+b) = a²Var(X), E and Var for special distributions, **Tschebyscheff inequality** (P(|X-μ| ≥ c) ≤ σ²/c²), **IID assumption**, **Law of Large Numbers** (sample mean → true mean as n→∞), variance of sample mean = σ²/n | Tschebyscheff quantifies "how likely is an observation far from the mean?" — used in outlier detection and confidence arguments. LLN justifies why we can learn from data at all: more data → better estimates. |
| G2 | **SaD 07** | 33 slides | Binomial distribution (Bernoulli trials), Hypergeometric distribution, Poisson distribution | Concrete distributions. Binomial is the most important — it models "how many successes in n trials?" which appears in classification error analysis. |
| G3 | **SaD 08** | 38 slides | **Normal distribution** N(μ,σ²): PDF formula, properties (symmetric, 68-95-99.7 rule), standard normal (z-scores), **Central Limit Theorem** (sum of many independent variables → normal), approximating other distributions, **slides 29-36: WHY MSE — MLE derivation** showing that if errors are normally distributed, then maximizing likelihood = minimizing MSE. | The MLE derivation (slides 29-36) is a highlight. It shows: assume errors εᵢ ~ N(0,σ²) → write likelihood L = ΠP(yᵢ|θ) → take log → drop constants → you're left with minimizing Σεᵢ² = MSE. This connects SaD 03's regression, AML L03's MSE, and probability theory in one clean argument. |
| G4 | **SaD 05** | 34 slides | Combinatorics: permutations, variations, combinations (with and without replacement) | Independent of everything else. Needed for SaD exam but low AML relevance. Can be done any time in this block. |
| G5 | **SaD UE4** | exercise | Zufallsvariablen & Diskrete Verteilungen practice | Practice Block C + G concepts. |

**Self-test after Block G:**
- [ ] State the Tschebyscheff inequality and compute a bound for P(|X-μ| ≥ 2σ)
- [ ] State the Central Limit Theorem in one sentence
- [ ] Walk through the MLE derivation: from "errors are normal" to "minimize MSE" in 5 steps
- [ ] Compute P(X ≤ 3) for X ~ Binomial(n=5, p=0.4)

**SaD exam focus (SaD 05-08):**
- [ ] Combinatorics: "A committee of 4 is chosen from 10 people. How many committees are possible?" — state the formula and compute
- [ ] Combinatorics: distinguish between permutation, variation, and combination with one example each
- [ ] Binomial: X ~ B(n=8, p=0.5). Compute P(X=3) using the PMF formula
- [ ] Hypergeometric: "An urn has 5 red and 7 blue balls. Draw 3 without replacement. What is P(exactly 2 red)?"
- [ ] Poisson: if λ=3 events per hour, compute P(X=0) and P(X≥1)
- [ ] Normal: given X ~ N(100, 15²), compute P(X > 130) using z-score standardization
- [ ] State the 68-95-99.7 rule and sketch the normal curve with labeled regions
- [ ] Walk through the MLE→MSE derivation in SaD 08 (slides 29-36): write each step from likelihood to Σεᵢ²

---

### BLOCK H: Regularization
**Time: ~3 hours | Prerequisites: Block E (regression)**

| Step | Source | Pages/Slides | What you learn | Why it matters |
|------|--------|-------------|----------------|----------------|
| H1 | **AML L04** | lecture slides | Polynomial regression (non-linear features, still linear in parameters), **Ridge regression** (L2: add λ‖w‖² to loss), **Lasso** (L1: add λ‖w‖₁), why Lasso produces sparse solutions | Regularization is the practical answer to overfitting from Block D. Ridge shrinks all weights; Lasso shrinks some to exactly zero (feature selection). |
| H2 | **ISLP Ch 6.2** (Shrinkage Methods) | ~15 pages | Ridge regression: β̂ = (XᵀX + λI)⁻¹Xᵀy, geometric interpretation (constraint region is circle vs diamond), cross-validation for choosing λ | ISLP has the clearest geometric picture of L1 vs L2 regularization (the diamond vs circle constraint). |

**Self-test after Block H:**
- [ ] Write the Ridge regression loss function and its closed-form solution
- [ ] Draw the L1 (diamond) and L2 (circle) constraint regions. Why does L1 hit corners (→ sparse)?
- [ ] When would you prefer Lasso over Ridge?

---

### BLOCK I: Classification
**Time: ~4.5 hours | Prerequisites: Block F (Bayes), Block E (regression concepts)**

The bridge from regression to classification. SaD gives the generative view (Naïve Bayes), AML gives the discriminative view (logistic regression).

> **🔗 Wiring:** `Plans/ML/foundations/reference/AML-SaD_Master_Wiring.md` §2-C (full Classification pipeline, Tiers C0–C4) + §5.1 (2-session sequence). Key cross-wires: #5 (MLE→cross-entropy — the Bernoulli twin of SaD 08's MLE→MSE), #6 (argmax→softmax), #7 (generative vs discriminative), #8 (Gaussian NB runs on SaD 08).

| Step | Source | Pages/Slides | What you learn | Why it matters |
|------|--------|-------------|----------------|----------------|
| I1 | **SaD 14** | 29 slides | Naïve Bayes extensions: **Laplace smoothing** (pseudocounts for zero-count combos), numerical attributes (**Gaussian NB** — per-class N(μc,σc²) from SaD 08), **multinomial Bayes** (bag-of-words, log-space trick), outlook on Bayesian Networks + Markov blanket | Extends the basic Naïve Bayes from Block F to handle real-world data issues (zero probabilities, continuous features). Smoothing is regularization-thinking before AML says the word. |
| I2 | **AML L05** | lecture slides | **Logistic regression**: the 3-attempt construction (regression+threshold fails → separator → sigmoid), decision-boundary geometry (w·x=0, scale-invariant), σ(z) = 1/(1+e⁻ᶻ) as P(y=1\|x), **full MLE → cross-entropy derivation** (product → log → combined form → vectorized gradient (1/m)Xᵀ(σ(Xw)−y)), non-linear boundaries via basis expansion, no closed form → GD necessary | Heavier than it looks (Wiring §4.2): the loss derivation is the discriminative twin of SaD 08's MLE→MSE — write the two side by side. Models P(class\|X) directly instead of going through Bayes' theorem. 📒 Book layer: Crosswalk L05 (Murphy Ch 10 ⭐, ISLP §4.3, CS229 §2.1). |
| I3 | **ISLP Ch 4.1-4.3** | ~15 pages | Logistic regression: log-odds, maximum likelihood estimation, multiclass (softmax) | ISLP adds the statistical interpretation: logistic regression models the log-odds as a linear function of predictors. |
| I4 | **SaD UE6** | exercise | Hypothesentests & Klassifikation practice | Combines classification practice with hypothesis testing (from Block G/SaD 10). |

**Cross-wire moment:** Naïve Bayes computes P(C|X) = P(X|C)·P(C)/P(X) (generative: models how data is generated per class). Logistic regression computes P(C|X) = σ(wᵀx) (discriminative: directly models the decision boundary). For the SAME data, they can give different predictions. AML will revisit this distinction.

**Self-test after Block I:**
- [ ] Write the sigmoid function and sketch it
- [ ] Derive dσ/dz = σ(z)(1-σ(z))
- [ ] Explain generative vs discriminative in 2 sentences
- [ ] What problem does smoothing solve in Naïve Bayes?

**SaD exam focus (SaD 14):**
- [ ] Apply Laplace smoothing to a Naïve Bayes problem where one feature value has zero occurrences for a class
- [ ] How does Gaussian Naïve Bayes handle continuous (numerical) features? (Answer: assumes each feature follows N(μc, σc²) per class, estimates μ and σ from training data)
- [ ] Given a training set, compute the Naïve Bayes prediction for a new instance with both discrete and continuous features

---

### BLOCK J: Gradient Descent Formal + Estimation
**Time: ~4 hours | Prerequisites: Block E (GD introduced in SaD 03), Block G (distributions)**

> 🎬 **SaD 2025 supplement:** `Plans/Math/sad/SaD/SaD-2025/` — **2025 L09 (point_interval_estimation) + L10 (statistical_significance)**. Confidence intervals and hypothesis tests are significantly easier to follow as a video walkthrough than as slides. Use if J1/J4 feel abstract. Also: **[jbstatistics](https://www.youtube.com/@jbstatistics)** for confidence intervals, t-distribution, and p-value explanations. For J2 (GD/Adam), **Cornell CS4780** (Weinberger) lecture on "Gradient Descent" is the closest match to AML L06's content — see LEARNING-RESOURCES §2.

| Step | Source | Pages/Slides | What you learn | Why it matters |
|------|--------|-------------|----------------|----------------|
| J1 | **SaD 09** | 45 slides | Inferential statistics, point estimators (unbiased, consistent, efficient), **confidence intervals**, mean estimation for normal distribution with known/unknown variance, t-distribution | SaD 09 formalizes "how good is our estimate?" OLS from Block E is a point estimator for β. Confidence intervals tell you how much to trust it. |
| J2 | **AML L06** | lecture slides | Gradient descent: full-batch, **stochastic GD** (one sample per update), **mini-batch GD**, learning rate schedules, **feature scaling** (mean-norm/min-max — why elliptic contours kill convergence), **Adam** (momentum + RMSProp), **Newton's method** (Hessian, H⁻¹∇L), convexity via PSD Hessian (∇²L = (1/m)XᵀX) | You saw GD basics in SaD 03 (Block E). AML L06 goes much deeper than "SGD" (Wiring §4.3): Adam is the optimizer in your AMLS project code AND in AMLS theory (S.C4) — triple ROI. Feature scaling = SaD 08's z-normalization in a third costume (Wiring cross-wire #10). See Wiring §5.2 for the 1-session sequence. 📒 Book layer: Crosswalk L06 — only CS229 §1.1 ⭐, Murphy Ch 8 ⭐, MML Ch 7 do GD properly; skip ISLP/ESL here. |
| J3 | **ISLP 10.7** (relevant sections) | ~5 pages | GD in context of neural networks | Brief treatment that connects GD to the neural network training loop. |
| J4 | **SaD 10** | 65 slides | Statistical tests: p-values, null/alternative hypothesis, Type I/II errors, parametric tests (t-test, z-test), non-parametric tests, good scientific practice | Important for SaD exam. Indirect AML connection: when you compare two models' performance, you're implicitly doing a hypothesis test ("is model A significantly better than model B?"). |
| J5 | **SaD UE5** | exercise | Normalverteilung & Parameterschätzung practice | |

**Cross-wire moment:** SaD 03 introduced GD as "an alternative to the matrix inverse." AML L06 reveals it as THE optimization algorithm for ML: when your loss function doesn't have a closed-form solution (which is most of the time — logistic regression, neural networks), GD is how you train. The shift from "nice alternative" to "this is how everything actually works" is important.

**Self-test after Block J:**
- [ ] Write the SGD update rule: w ← w - η·∇L(wᵢ) for a single sample
- [ ] Explain the tradeoff: full-batch GD (stable but slow) vs SGD (noisy but fast) vs mini-batch (compromise)
- [ ] What is a confidence interval? Give the formula for the 95% CI of a mean with known variance
- [ ] What is a p-value? What does p < 0.05 mean?

**SaD exam focus (SaD 09-10):**
- [ ] Define: unbiased estimator, consistent estimator, efficient estimator — one sentence each
- [ ] Given x̄=48, σ=12, n=36: construct the 95% confidence interval (use z=1.96)
- [ ] Given x̄=48, σ unknown, s=12, n=16: which distribution do you use instead of z? (Answer: t-distribution)
- [ ] Set up a hypothesis test: H₀: μ=50 vs H₁: μ≠50. Given x̄=47, σ=6, n=36, α=0.05 — compute the test statistic, compare to z_crit, state your conclusion
- [ ] Explain Type I error (reject H₀ when H₀ is true) and Type II error (fail to reject H₀ when H₁ is true) with the medical test analogy
- [ ] Name one parametric and one non-parametric test from SaD 10. When would you use the non-parametric one?

---

### BLOCK K: Trees + Linear Classifiers
**Time: ~4 hours | Prerequisites: Block D (bias-variance), Block I (classification concepts)**

Two families of classifiers. Trees are SaD-only content (not in AML). Perceptron/kernels are AML-only.

> 🎬 **SaD 2025 supplement:** `Plans/Math/sad/SaD/SaD-2025/` — **2025 L12 (clustering)**. K-means is covered here (unsupervised, SaD-only). Also: **Cornell CS4780** has excellent lectures on decision trees (information gain, ID3) and perceptrons — see LEARNING-RESOURCES §2. For the ID3 self-test problems, **MIT 6.034** past quizzes (with solutions) are the closest exam format match — see LEARNING-RESOURCES §6.

> **🔗 Wiring:** `Plans/ML/foundations/reference/AML-SaD_Master_Wiring.md` §2-D Tiers D1–D3 (perceptron, kernels, XOR) + §5.3 (2-session sequence) + cross-wires #13, #16, #17.
> **📚 Complete unit (KW 27):** `Plans/ML/foundations/AML/my notes/lect07 linear classifiers/` — Ultimate Reference + Mini Plan + Exercise Bank + Mock Exam + Blatt-4 solution. Use the Mini Plan as the K2 study script.
> **⚠️ Corrected KW 24 (Wiring §4.1):** the actual AML L07 deck contains **no SVM / maximum margin**. It covers perceptron (primal + dual form), separability, XOR, the **kernel trick** (polynomial + RBF kernels), and **multi-class classification** (One-vs-Rest, multiclass perceptron). K2/K3 updated accordingly.

| Step | Source | Pages/Slides | What you learn | Why it matters |
|------|--------|-------------|----------------|----------------|
| K1 | **SaD 12** | 36 slides | **Decision trees**: building by entropy/information gain, **ID3 algorithm**, tree pruning (pre/post), **regression trees** (variance as split criterion), ensembles (**stacking, bagging, boosting**), **Random Forests** | SaD exam topic. Not in AML, but connects to bias-variance: individual trees = high variance, Random Forest = variance reduction via averaging many trees (bagging). Boosting = reduce bias by sequential learning. Entropy here = the H in cross-entropy loss (Wiring cross-wire #16). |
| K2 | **AML L07** | lecture slides | **Perceptron** learning rule (sub-gradient SGD, convergence iff linearly separable), **dual form** (w = Σαᵢyⁱxⁱ), XOR non-separability, **kernel trick** (polynomial, RBF), **multi-class** (One-vs-Rest, multiclass perceptron) | The perceptron is the simplest neural network (1 neuron, binary threshold) — direct bridge into Block L. The kernel trick enables non-linear boundaries without explicitly computing the high-dimensional mapping; RBF = SaD 08's Gaussian used as a similarity function. |
| K3 | **Book layer for L07** (Crosswalk L07): **ESL §4.5.1** (Rosenblatt perceptron, p.130) → **CS229 §2.2 + Ch 5** (kernels *without* SVM — the only such book source) → **ISLP §9.4.2** (One-vs-All, 1 page) → Murphy §17.1.2 (kernel reference) | ~15 pages total | The perceptron algorithm with convergence (ESL); feature maps → kernel trick → kernel properties on LMS/perceptron-style updates (CS229 Ch 5 — exactly the lecture's route); OvR multi-class (ISLP) | ⚠️ Every other book reaches kernels only through the SVM, which L07 does **not** teach — ISLP §9.1–9.2/margin remains enrichment-only. Worked example to reproduce: K(x,z)=(x·z)² = φ(x)·φ(z) for φ(x)=(x₁²,x₂²,√2x₁x₂). |
| K4 | **SaD UE7 (first part)** | exercise | Clustering (K-means) — SaD exam topic | K-means is unsupervised, not in AML. Separate SaD exam topic. |

**Self-test after Block K:**
- [ ] Build a decision tree for a 3-feature, 6-instance toy dataset using information gain
- [ ] Explain why Random Forests reduce variance compared to a single tree
- [ ] State the perceptron update rule
- [ ] What does the kernel trick do in one sentence?

**SaD exam focus (SaD 12 + K-Means):**
- [ ] Compute entropy H(S) = −Σpᵢlog₂(pᵢ) for a dataset with 5 positive and 3 negative instances
- [ ] Given a candidate split, compute information gain = H(parent) − Σ(|Sᵢ|/|S|)·H(Sᵢ). Choose the best split among 3 candidates
- [ ] Explain ID3 algorithm in 4 steps (choose attribute → split → recurse → stop condition)
- [ ] What is pruning and why is it needed? (Answer: prevent overfitting, reduce tree complexity)
- [ ] Explain bagging (bootstrap aggregating) and how Random Forests use it
- [ ] K-Means: given 6 points and k=2 with initial centroids, run 2 iterations by hand (assign → recompute centroids → reassign)

---

### BLOCK L: Neural Networks
**Time: ~6 hours | Prerequisites: Block E (regression, GD), Block J (SGD), Block K (perceptron)**

> 🎬 **Start here before the slides:** **[3Blue1Brown — Neural Networks](https://www.youtube.com/playlist?list=PLZHQObOWTQDNU6R1_67000Dx_ZCJB-3pi)** (4 videos, ~1.5h): "What is a NN?", "Gradient Descent", "Backpropagation", "Backprop Calculus". Watch all 4 BEFORE L1–L4 — they build exactly the right intuition. Also on KI-Campus: https://ki-campus.org/en/learning-opportunities/videos/neural-networks.
>
> 🎬 **SaD 2025 supplement:** `Plans/Math/sad/SaD/SaD-2025/` — **2025 L14 (neural_nets_part1) + L15 (neural_nets_part2)**. Two full lectures on neural networks vs. one in 2026. Significantly more depth on backpropagation — watch after L2 (AML L08) to deepen before L4 (AML L09). **UMich EECS 498** (Justin Johnson) for CNN/backprop — see LEARNING-RESOURCES §2.

> **Optional supplement:** [TU Python-for-ML Sheet 5](https://github.com/mahmutoezmen/Python-for-ML-Course/tree/main/5.%20Sheet) — automatic differentiation (autograd), Numba, Cython. Autograd is exactly what PyTorch's `loss.backward()` does. Do during or after Block L to see backpropagation from the implementation side.

Peak synergy between SaD and AML. SaD 15 gives the 38-slide overview. AML spends two full lectures going deep.

> **🔗 Wiring:** `Plans/ML/foundations/reference/AML-SaD_Master_Wiring.md` §2-D (full Neural-network pipeline, Tiers D0–D5) + §5.4 (3-session sequence). Key facts found in the decks (Wiring §4.5, §4.8): NN regularization (Frobenius/L2 weight decay, **dropout, early stopping, double descent**) lives in **AML L09**, not L04; and AML L08 + AML L09 share one **numerically identical worked example** (W⁽¹⁾=[[1,2],[1,2]], x=[1,0] → ŷ=0.94) — do it by hand once in L08, reuse for backprop in L09.

| Step | Source | Pages/Slides | What you learn | Why it matters |
|------|--------|-------------|----------------|----------------|
| L1 | **SaD 15** slides 1-12 | 12 slides | Perceptron recap, 1-layer ANN formula f(X) = φ(b + Wx), algebraic form, **"If we drop φ, this is exactly MLR"** (slide 9!), activation functions for classification (softmax), limitations of 1-layer ANN (can only separate linearly separable data) | The most important single slide in the SaD course: slide 9 proves that a 1-layer neural network without activation = multivariate linear regression from Block E. Everything connects. |
| L2 | **AML L08** | lecture slides | **Feedforward Neural Networks / MLP**: multiple layers, activation functions (ReLU, sigmoid, tanh), forward pass a⁽ˡ⁾=g(W⁽ˡ⁾a⁽ˡ⁻¹⁾+b⁽ˡ⁾) + worked example, expressiveness (linear activations collapse — proof), output layers (multi-label sigmoids vs multi-class softmax), toolkits, **metrics block** (confusion matrix, P/R/F1, micro/macro/weighted) | AML goes deep on architectures. After SaD 15's overview, you'll understand WHY we need multiple layers (1 layer can't solve XOR) and what each component does. Do the worked forward pass by hand ONCE here — L09 reuses the same numbers (Wiring §4.8). 📒 Book layer: Crosswalk L08 (ISLP §10.1–10.2, Murphy §13.2.1+13.2.3, Kroese §7.2 for metrics, CS229 §7.1–7.2). ⚠️ Micro/macro/weighted averaging is in no book — slides + sklearn docs only. |
| L3 | **SaD 15** slides 12-38 | 26 slides | **MLP architecture**, **backpropagation** (overview), vanishing gradients, further topics | SaD 15 gives the backprop overview. Read this between AML L08 and L09 as a bridge. |
| L4 | **AML L09** | lecture slides | **Backpropagation**: computational graphs (atomic ops, caching), chain rule applied layer by layer (the four per-layer rules), full worked example (same numbers as L08 → dW⁽²⁾=[0.0143, 0.0506]), weight initialization (small random), **NN regularization** (L2/Frobenius weight decay, dropout, early stopping, **double descent**), vanishing/exploding gradients (λ⁷ argument), PyTorch autograd closing | The full backprop derivation. AML derives it on a 2-layer MLP by hand. This is the deepest math in the course but you're ready: chain rule (T5 check), matrix multiplication (Block E), gradient descent (Blocks E+J). ⚠️ **Corrected KW 27 (slide-verified): NO batch normalization in this deck** — the older claim was wrong. 📒 Book layer: Crosswalk L09 — Murphy §13.3–13.5 ⭐ (only book with computation graphs), ISLP §10.7–**10.8** + CS229 §8.2 (the only two double-descent sources), CS229 §7.3, MML §5.6 for the chain-rule math. |
| L5 | **ISLP Ch 10.1-10.2** | ~15 pages | Single-layer and multi-layer networks, fitting neural networks | ISLP gives a clean textbook treatment with good diagrams. |

**Self-test after Block L:**
- [ ] Draw a 2-layer MLP with input dimension 3, hidden layer size 4, output size 2. Count the parameters.
- [ ] Explain ReLU, sigmoid, tanh — one advantage and one problem of each
- [ ] Apply the chain rule to compute ∂L/∂w₁ for a 2-layer network (conceptually, not full derivation)
- [ ] What is the vanishing gradient problem and how do ReLU and batch normalization help?

**SaD exam focus (SaD 15):**
- [ ] Write the 1-layer ANN formula: f(X) = φ(b + Wx). Identify each component (weights W, bias b, activation φ, input X)
- [ ] Prove: "if we drop φ, this is exactly MLR" — write out both formulas side by side
- [ ] Name 3 activation functions and state one property of each (e.g., sigmoid outputs in (0,1), ReLU is not differentiable at 0)
- [ ] Explain why a single-layer perceptron cannot solve XOR (linear separability)
- [ ] Describe backpropagation in 3 sentences as it appears in SaD 15 (forward pass → compute error → backward pass updating weights layer by layer)

---

### BLOCK M: Deep Architectures (AML only)
**Time: ~4 hours | Prerequisites: Block L**

CNNs and RNNs are not in SaD. These are AML-only.

> 🎬 **Supplement:** **UMich EECS 498** (Justin Johnson) — backprop/CNN/RNN lectures, the deepest free treatment of exactly these architectures. **CS231n 2017** Stanford — CNNs for visual recognition, slides + lecture videos (convolution intuition, pooling, ResNet). Both tagged in LEARNING-RESOURCES §2. For M1 CNN self-test, the **[Patrick Loeber PyTorch CNN tutorial](https://www.youtube.com/watch?v=pDdP0TFzsoQ)** (CIFAR-10, ~30min) makes the architecture concrete — same dataset as the AMLS project.

| Step | Source | Pages/Slides | What you learn | Why it matters |
|------|--------|-------------|----------------|----------------|
| M1 | **AML L10** | lecture slides | **CNNs** (slide-verified KW 27): convolution/cross-correlation, filters (edge detectors → learned), **padding** (valid/zero/same), **stride**, output-size formula ⌊(n+2p−f)/s+1⌋, RGB/multi-channel convs, multiple filters → feature maps, pooling (max/avg), conv+pool stacks → flatten → FC → softmax, famous architectures (**LeNet-5, AlexNet, GoogLeNet, ResNet**) | CNNs are the dominant architecture for images. The key insight: weight sharing (same filter applied everywhere) dramatically reduces parameters compared to an MLP. Project synergy: you already built this CNN (Task 1.2 ✅) — read as theory-behind-your-code. |
| M2 | **ISLP Ch 10.3** (pp 406–412) + **Murphy §14.1–14.3** (pp 467–484) | ~5 + ~15 pages | ISLP: convolution, pooling, architecture, **§10.3.4 data augmentation** (= AMLS Task 1.3 theory!). Murphy: full conv arithmetic (the (n+2p−f)/s+1 formula), pooling, and §14.3.1–14.3.4 = the lecture's exact architecture list | 📒 Crosswalk L10: these are the ONLY two real CNN book sources (ESL/Toronto/Kroese/MML/CS229 have none; ESL §11.7 ZIP-code is a fun historical read). ⚠️ Murphy §14.2.4 batch norm + §14.4 dilated/transposed convs = beyond lecture scope. |
| M3 | **AML L11** *(2026 deck not yet posted — scope from the older 11-rnn deck; verify on release)* | lecture slides | **RNNs**: hidden state, unrolling through time, BPTT, vanishing gradient in sequences, **LSTM** (gates: forget, input, output), **GRU** | RNNs handle sequences (text, time series). The vanishing gradient problem from Block L returns — LSTM solves it with gating mechanisms. |
| M4 | **ISLP Ch 10.5** (p.416) + **Murphy §15.2** (p.503; §15.2.7 GRU/LSTM gates, p.512) | ~5 + ~10 pages | ISLP: gentle RNN treatment. Murphy §15.2.7: the only local source with the actual gate equations | 📒 Crosswalk L11 (preliminary): no other book covers RNNs. Finalize when the 2026 deck drops. |

**Self-test after Block M:**
- [ ] Compute the output dimensions of a convolution: input 28×28, kernel 5×5, stride 1, no padding → ?
- [ ] Why is parameter sharing in CNNs better than a fully connected layer for images?
- [ ] Draw an unrolled RNN for a sequence of length 3. Show where the same weights are reused.
- [ ] Explain the LSTM forget gate in one sentence

---

### BLOCK N: SaD Exam Prep
**Time: ~12-15 hours | Prerequisites: All previous blocks**

This is where SaD gets its own dedicated space. By now you've seen every SaD lecture at least once through the AML-synergy blocks. This block is purely SaD-focused: revisit, consolidate, and practice for the exam format.

#### N Phase 1: Topic Cluster Review (~6h)

Group the 15 lectures into 5 clusters and review each as a unit. For each cluster, re-read the SaD slides (not AML/ISLP — only the SaD version matters for the SaD exam) and do the linked exercises.

| Step | Cluster | SaD Lectures | Exercise | Review focus |
|------|---------|-------------|----------|--------------|
| N1 | **Descriptive Statistics** | SaD 01 + 02 | — | Frequency tables, mean/median/mode, variance s², boxplots, precision/recall from contingency tables. Exam format: compute by hand from a small dataset. |
| N2 | **Probability & Counting** | SaD 04 + 05 | UE3 | Bayes' theorem applications, conditional probability, combinatorics (permutations/combinations). Exam format: "compute P(A|B)" with Bayes, counting problems. |
| N3 | **Random Variables & Distributions** | SaD 06 + 07 + 08 | UE4 | E[X], Var(X), Tschebyscheff, LLN, Binomial/Poisson/Normal distributions, z-scores, CLT. Exam format: compute E[X] and Var(X) for a given distribution, z-score lookups, CLT application. |
| N4 | **Inference** | SaD 09 + 10 | UE5 | Point estimators (unbiased, consistent), confidence intervals, hypothesis tests (z-test, t-test), p-values, Type I/II errors. Exam format: "construct a 95% CI", "test whether μ > 5 at α = 0.05". |
| N5 | **ML Methods** | SaD 03 + 11 + 12 + 13 + 14 + 15 | UE2, UE6, UE7 | Linear regression (compute k and d), decision trees (build by information gain), k-NN (apply algorithm), Naïve Bayes (compute posterior), MLP basics. Exam format: apply algorithms step-by-step on toy datasets. |

#### N Phase 2: SaD Cheat Sheets (~3h)

| Step | What to do |
|------|------------|
| N6 | Write a **one-page cheat sheet per cluster** (5 sheets, not 15). Each sheet: key formulas, one worked example, common exam traps. This forces you to compress and identify what matters. |
| N7 | Create a **formula reference card**: all SaD formulas on one double-sided page (x̄, s², rxy, regression k/d, E[X], Var(X), Bayes' theorem, Binomial PMF, Normal PDF, CI formula, test statistics). |

#### N Phase 3: Exam Practice (~4-6h)

| Step | What to do |
|------|------------|
| N8 | **SaD UE7** Klausurvorbereitung section — work through completely, timed |
| N9 | **Past SaD exams** — if available, do under exam conditions (time limit, no notes first, then check with cheat sheets). *No public Altklausuren exist (checked KW 24) — use the solved exam-practice bank in `LEARNING-RESOURCES.md` §6 (Fahrmeir Arbeitsbuch ⭐, MIT 18.05 exams+solutions, Stat 110 strategic practice, MIT 6.034 algorithm-tracing quizzes) and chase real Altklausuren via Moodle + Fachschaft (action items there).* |
| N10 | **Weak-spot drill**: after UE7/past exams, identify your 3 weakest topics and re-do those cluster exercises |

#### SaD Exam Self-Test (comprehensive)

Run through these before the exam. If you can do all of them, you're ready.

**Descriptive (SaD 01-02):**
- [ ] Given a dataset of 8 values: compute x̄, s², median, Q1, Q3, and draw the boxplot
- [ ] Given a contingency table: compute precision, recall, and accuracy

**Probability & Counting (SaD 04-05):**
- [ ] Apply Bayes' theorem to a medical test problem (given sensitivity, specificity, prevalence → compute PPV)
- [ ] "How many ways to choose 3 from 10 without replacement?" — state which formula and compute
- [ ] Classify a new instance using Naïve Bayes with a given training table

**Random Variables & Distributions (SaD 06-08):**
- [ ] Compute E[X] and Var(X) for a custom discrete distribution (given as a table)
- [ ] Apply Tschebyscheff: "at least what fraction of data lies within 2σ of the mean?"
- [ ] X ~ Binomial(n=10, p=0.3): compute P(X = 3) and P(X ≤ 2)
- [ ] Standardize a value to a z-score and look up the probability
- [ ] State the CLT and explain why it justifies using the normal distribution for sample means

**Inference (SaD 09-10):**
- [ ] Construct a 95% confidence interval for a mean (known σ, n=25, x̄=50, σ=10)
- [ ] Perform a one-sample z-test: state H₀, H₁, compute test statistic, compare to critical value, conclude
- [ ] Explain Type I vs Type II error with an example
- [ ] What does "p = 0.03" mean in words?

**ML Methods (SaD 03, 11-15):**
- [ ] Given 5 data points: compute rxy, then k and d for the regression line
- [ ] Build a decision tree for a 6-instance dataset using information gain (compute entropy at each split)
- [ ] Run k-NN (k=3) on a 2D toy dataset: find the 3 nearest neighbors, predict the class
- [ ] Apply Naïve Bayes with Laplace smoothing to classify a new instance
- [ ] Draw a 1-layer perceptron, write its formula, and explain what happens when you remove the activation function

---

## Mapping Blocks to Calendar Weeks

> ⚠️ **SUPERSEDED (KW 23, 2026-06-03).** This sequential calendar was written in April and assumed Blocks A→M in order. The **KW 21 fast-path pivot** (project-driven subset: F.D → E3-4 → H → I1 → K) replaced it, and as of KW 23 you are still mid-Block D — not at Block L/M as the table implies. **Do not follow the week numbers below.** The live schedule is `SEMESTER-STATUS.md` §7 (weekly load planner) + §9 (priority stack). F is now exam-driven (Block N from KW 27), not lecture-paced. The table is kept only as the block-ordering reference.

Given ~8-10 hours/week available for AML+SaD theory (see Theorieplan Wochenstruktur), here's a realistic pacing:

| KW | Dates | Blocks | AML Lecture | SaD focus | Hours |
|----|-------|--------|------------|-----------|-------|
| **17** | Apr 21-27 | **A** ✅ + speed-run (SaD 03, 06 partial) | L01 ✅ | SaD 01 ✅, 02 ✅, 03 ✅, 06 slides 1-35 ✅ | done |
| **18** | Apr 28 – May 4 | **B** (finish: SaD 11 slides 1-22, ~~ISLP 2.1 pp 15-19~~ ✅) + **D** (~~ISLP 2.1 pp 20-25~~ ✅, SaD 13, AML L02, SaD 11 slides 23-47, ISLP 2.2.1-2.2.2) + **E** (continue: ISLP Ch 3, AML L03, UE2) | L02 + L03 | SaD 11, 13 + UE2 | ~12h (heavy — absorbing KW 17 overflow) |
| **19** | May 5-11 | **F + G (start)** | L04 | SaD 04, 05, 06 (finish), 07 | ~10h |
| **20** | May 12-18 | **G (finish) + I (start)** | L05 | SaD 08, 14 + UE3, UE4 | ~10h (no AMLS = extra time) |
| **21** | May 19-25 | **H + J (start)** | L06 | SaD 09, 10 + UE5 | ~9h |
| **22** | May 26 – Jun 1 | **J (finish) + K** | L07 | SaD 12 + UE6 | ~8h |
| **23** | Jun 2-8 | **L (start)** | L08 | SaD 15 (partial) | ~8h |
| **24** | Jun 9-15 | **L (finish)** | L09 | SaD 15 (finish) | ~8h |
| **25** | Jun 16-22 | **M (start)** | L10 | — | ~6h |
| **26** | Jun 23-29 | **M (finish)** | L11 | UE7 | ~6h |
| **27** | Jun 30 – Jul 5 | **N Phase 1** (cluster review) | revision | SaD 01-15 revisit by cluster | ~6h |
| **28** | Jul 6-12 | **N Phase 2+3** (cheat sheets + practice) | revision | Cheat sheets, UE7 Klausurvorbereitung, past exams | ~8h |
| **29+** | Jul 13+ | **Exam drill** | both exams | Weak-spot drill, timed practice, final review | flexible |

**KW 17 is the heaviest week** because you're catching up Block A+B (which should have been KW 16) plus doing the current week's content (Block C+D). After KW 17, the pace normalizes.

---

## Quick Reference: The 7 Cross-Wire Moments

> **Superseded by the full registry (KW 24):** `Plans/ML/foundations/reference/AML-SaD_Master_Wiring.md` §3 expands these 7 to **18 slide-grounded cross-wires** (new: MLE→cross-entropy, argmax→softmax, Gaussian-NB↔SaD 08, feature scaling ×3, Hessian/convexity, XOR×2, metrics ×3, Type I/II↔FP/FN, entropy↔cross-entropy, bootstrap→bagging→RF, class imbalance ×3). The 7 below remain valid as the core set.

These are the specific "aha" connections to watch for as you study:

1. **Sample mean ↔ Expected value (Block C, SaD 06 slide 26+35):** x̄ from a sample is an estimate of E[X] from the population. ISLP's E[...] notation is just the population version of the averaging you already know.

2. **Regression line — three notations, one idea (Block E):** SaD writes k = rxy·sy/sx. ISLP writes β₁ = cov(x,y)/var(x). AML writes w = (XᵀX)⁻¹Xᵀy. They're all minimizing the sum of squared errors.

3. **Normal errors → MSE (Block G, SaD 08 slides 29-36):** IF prediction errors are normally distributed, THEN the Maximum Likelihood Estimation naturally produces the MSE loss function. This is why MSE is the default for regression — not arbitrary, but a consequence of the CLT.

4. **Naïve Bayes vs Logistic Regression (Block I):** Both compute P(class|features). Naïve Bayes goes through Bayes' theorem (generative). Logistic regression models P directly via sigmoid (discriminative). Understanding both = understanding the generative/discriminative divide in ML.

5. **SaD GD → AML GD (Block E → Block J):** SaD 03 introduces gradient descent as "an alternative when the matrix inverse is expensive." AML L06 reveals it as THE training algorithm for all of modern ML. Same algorithm, radically different significance.

6. **1-layer ANN = linear regression (Block L, SaD 15 slide 9):** If you remove the activation function from a neural network, you get multivariate linear regression. Every concept from Block E applies. Neural networks are "regression, but with non-linear activation functions stacked in layers."

7. **Single tree variance → Random Forest (Block K):** One decision tree overfits (high variance). A Random Forest averages many trees → reduces variance without increasing bias much. This is the bias-variance tradeoff from Block D in action.
