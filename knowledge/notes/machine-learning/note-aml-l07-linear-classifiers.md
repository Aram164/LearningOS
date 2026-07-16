---
id: note-aml-l07-linear-classifiers
type: note
title: "AML L07 — Ultimate Reference: Linear Classifiers, Perceptron, Kernel Trick, Multi-Class"
created: "2026-07-01"
role: reference
state: evolving
authorship: mixed
concepts: [concept-perceptron, concept-kernel-trick, concept-xor-problem,
  concept-decision-boundary, concept-gradient-descent]
sources: [source-aml-ss26-lectures, source-cs229-notes, source-esl, source-mit-6036]
contexts: [workspace-aml-exam-prep]
---

> **Migration note (2026-07-17, Stage-1 pilot):** body preserved verbatim from
> `Plans/ML/foundations/AML/my notes/lect07 linear classifiers/AML_L07_Ultimate_Reference.md` (legacy tree). Companions in v3: `note-aml-l07-exercise-bank`, `note-aml-l07-mock-exam`. The step hook (F.K2) and the Mini Plan are operational and live in
> `work/active/workspace-aml-exam-prep/`.

# AML Lecture 07 — Ultimate Reference: Linear Classifiers, Perceptron, Kernel Trick, Multi-Class

*Built KW 27 from `…/SoSe 2026/lecture slides/VL 07-linear-classifiers.pdf` (94 slides, slide numbers cited per section). Companion docs: `AML_L07_Mini_Plan.md`, `AML_L07_Exercise_Bank.md`, `AML_L07_Mock_Exam.md` (this folder). Book layer: crosswalk L07 section (`../AML_Book-Concept-Crosswalk_L02-L10.md`).*

> ⚠️ **Scope note (slide-verified):** this lecture has **NO SVM and no maximum margin** — do not study ISLP §9.1–9.2 for it. The chain is: perceptron → separability limits (XOR) → computed features → **kernel trick** → RBF → multi-class. See Master Wiring §4.1.

## Table of Contents

0. [Notation](#0-notation)
1. [Linear classifiers — the general form](#1-general)
2. [Separability & class overlap](#2-separability)
3. [The perceptron: model](#3-perceptron)
4. [The perceptron loss](#4-loss)
5. [Sub-gradient & update rule](#5-gradient)
6. [The perceptron algorithm](#6-algorithm)
7. [Primal vs dual form](#7-dual)
8. [Convergence](#8-convergence)
9. [Boolean gates: AND, OR, NAND](#9-gates)
10. [XOR — the wall](#10-xor)
11. [Fix: computed features](#11-features)
12. [The mapping φ and its cost](#12-phi)
13. [Kernelization criterion](#13-kernelize)
14. [The kernel trick](#14-trick)
15. [The polynomial kernel](#15-poly)
16. [Common kernel functions](#16-common)
17. [The RBF / Gaussian kernel](#17-rbf)
18. [RBF as similarity: landmarks](#18-landmarks)
19. [The kernelized perceptron](#19-kernel-perceptron)
20. [Multi-class: One-vs-Rest](#20-ovr)
21. [Multi-class: the multiclass perceptron](#21-mc-perceptron)
22. [OvR vs multi-class extension](#22-comparison)
23. [Summary](#23-summary)
24. [Self-test](#24-self-test)

---

## 0. Notation <a name="0-notation"></a>

| Symbol | Meaning |
|---|---|
| `x ∈ ℝⁿ`, augmented `x = (1, x₁, …, xₙ) ∈ ℝⁿ⁺¹` | features (bias absorbed as x₀=1) |
| `y ∈ {−1, +1}` | perceptron labels (⚠️ **not** {0,1} — logistic regression's convention) |
| `w ∈ ℝⁿ⁺¹` | weights; decision boundary `w·x = 0` |
| `ŷ = sign(w·x)` | perceptron prediction |
| `φ(x)` | feature mapping into a higher-dimensional space |
| `K(x, z)` | kernel: `K(x,z) ≡ φ(x)·φ(z)`, computed *without* building φ |
| `αᵢ` | dual variable = **number of updates made using point i** (not a learning rate!) |
| `l⁽ⁱ⁾` | landmark (RBF view); the lecture sets `l⁽ⁱ⁾ = x⁽ⁱ⁾` for all m training points |
| `σ²` | RBF hyper-parameter (drop-off rate) |
| `k` | number of classes (multi-class section) |

---

## 1. Linear classifiers — the general form <a name="1-general"></a>
[Source: VL07 slides 3–6]

A linear classifier = a **decision boundary** `w·x = 0` (a hyperplane) + an **activation function** g applied to `z = w·x`:

- Predict `y = 1` if `h_w(x) ≥ T`, else 0 — for some threshold T.
- **Logistic regression** is the case `g = σ`, `T = 0.5` (recall L05: `σ(w·x) ≥ 0.5 ⟺ w·x ≥ 0` — same boundary!).
- The perceptron is the case `g = sign` (§3).

The family differs only in g; the *geometry* (a hyperplane splitting ℝⁿ) is identical. That is the "linear" in linear classifier.

## 2. Separability & class overlap <a name="2-separability"></a>
[Source: VL07 slides 7–9]

- A dataset is **separable by a learner** if some instance of that learner predicts *all* points correctly.
- **Linearly separable** = a linear boundary (line in 2d) achieves zero training error.
- Real classes typically **overlap** (benign/malignant cells look similar). Options [slide 8]: add **computed features**, use a **more complex classifier**, or **accept some errors**.
- Slide 9's "Gemischtes Doppel" scatter: non-separable by any line, separable by a non-linear boundary — the lecture's motivating picture for §11+.

## 3. The perceptron: model <a name="3-perceptron"></a>
[Source: VL07 slides 10–12]

Rosenblatt's model of a neuron (weights = synapses, threshold = firing):

```
 x₀=1 ──w₀─┐
 x₁  ──w₁──┤
 x₂  ──w₂──┼──▶  z = w·x ──▶ sign(z) ──▶ ŷ ∈ {−1, +1}
  ⋮        │
 xₙ  ──wₙ─┘
```

```
ŷ = sign(w·x),   sign(z) = +1 if z ≥ 0, else −1
```

Two computations only: weighted sum, then threshold. **This single neuron is the building block of every neural network in L08–L10.**

## 4. The perceptron loss <a name="4-loss"></a>
[Source: VL07 slides 13–15]

Correct classification ⟺ `y` and `w·x` have the same sign ⟺ **`y (w·x) ≥ 0`**. The loss per sample = "the amount by which we are wrong":

```
L(w) = 0            if y(w·x) ≥ 0      (correct → no loss)
L(w) = −y(w·x)      otherwise           (misclassified → positive loss)
```

Examples [slide 13]: `y=+1, w·x=−0.1 → loss 0.1`; `y=−1, w·x=6 → loss 6`.

Properties [slides 14–15]: **convex** (global optimum reachable), but with **multiple zero-loss solutions** if the data is separable (any separating hyperplane is optimal). Contrast with L05: logistic loss also convex, but strictly — unique optimum.

## 5. Sub-gradient & update rule <a name="5-gradient"></a>
[Source: VL07 slides 16–17]

For a **misclassified** sample, `L = −y(w₁x₁ + … + wₙxₙ)`, so

```
∂L/∂wⱼ = −y·xⱼ     →    ∇L = −y·x      (a vector — NO dot product here!)
```

For a correctly classified sample: `∇L = 0` (flat region). Precisely it's a **sub-gradient** — L has a kink at `y(w·x) = 0` where it isn't differentiable [slide 17].

## 6. The perceptron algorithm <a name="6-algorithm"></a>
[Source: VL07 slides 18–22]

**SGD with the sub-gradient**, one point at a time, stepping opposite `∇L = −yx`:

```
randomly init w
while there is error on the train data do
    for each point (x⁽ⁱ⁾, y⁽ⁱ⁾) do
        ŷ = sign(w·x⁽ⁱ⁾)
        if y⁽ⁱ⁾ ≠ ŷ:                    # misclassified
            w = w + y⁽ⁱ⁾·x⁽ⁱ⁾           # step opposite −yx
```

Notes:
- **No learning rate** (α=1 works: rescaling w doesn't change sign(w·x) — the boundary is scale-invariant, cf. L05).
- Misclassified positive point → **add** x to w (rotate boundary toward it); misclassified negative → **subtract**.
- Correct points change nothing (their gradient is 0).

## 7. Primal vs dual form <a name="7-dual"></a>
[Source: VL07 slides 23–24]

Since w starts at (or near) 0 and only ever gets `±x⁽ⁱ⁾` added, the final answer has a special form:

```
w = Σᵢ αᵢ y⁽ⁱ⁾ x⁽ⁱ⁾        αᵢ = number of times point i triggered an update
```

**Dual algorithm** — store α instead of w; the prediction becomes a sum of dot-products:

```
ŷ = sign( Σⱼ αⱼ y⁽ʲ⁾ (x⁽ʲ⁾·x) )
```

```
randomly init α = 0
while there is error do
    for each point (x⁽ⁱ⁾, y⁽ⁱ⁾):
        ŷ = sign( Σⱼ αⱼ y⁽ʲ⁾ (x⁽ʲ⁾·x⁽ⁱ⁾) )
        if y⁽ⁱ⁾ ≠ ŷ:   αᵢ = αᵢ + 1
```

Why bother? (1) the dot-products `x⁽ʲ⁾·x⁽ⁱ⁾` can be **precomputed** [slide 24]; (2) **x now appears ONLY inside dot products** → the door to kernels (§13). ⚠️ α is a *counter*, not a learning rate [slide 24 footnote].

## 8. Convergence <a name="8-convergence"></a>
[Source: VL07 slides 26–27]

| Data | Behaviour |
|---|---|
| **Linearly separable** | Guaranteed to find *some* zero-training-error boundary in **finitely many** iterations. Which one depends on initialization/order — slide 26 shows 3 valid boundaries for the same 85 points. |
| **Not separable** | **Never converges** — there is always a misclassified point triggering another update; the boundary jiggles forever. (In practice: stop after a max number of epochs.) |

## 9. Boolean gates: AND, OR, NAND <a name="9-gates"></a>
[Source: VL07 slides 28–34; step activation `step(z) = 1 if z > 0 else 0` from slide 29]

Any Boolean function = a classification problem on inputs {0,1}². The lecture's verified weight vectors (`w·x` with augmented `x = (1, x₁, x₂)`):

| Gate | w = (w₀, w₁, w₂) | Check |
|---|---|---|
| **OR** | (−0.5, 1, 1) | z = −0.5, +0.5, +0.5, +1.5 → 0,1,1,1 ✓ |
| **AND** | (−1.5, 1, 1) | z = −1.5, −0.5, −0.5, +0.5 → 0,0,0,1 ✓ |
| **NAND** | (+1.5, −1, −1) | z = +1.5, +0.5, +0.5, −0.5 → 1,1,1,0 ✓ |

**NAND vs AND** [slide 34]: *same* decision boundary `x₂ = −x₁ + 1.5`, *different* weights (negated) — the boundary is a set, the weights orient which side is which.

## 10. XOR — the wall <a name="10-xor"></a>
[Source: VL07 slides 35–37, 42]

XOR: (0,0)→0, (0,1)→1, (1,0)→1, (1,1)→0. **No linear boundary exists.**

Proof sketch (the "formally prove this" of slide 36): a linear classifier needs `w₀ ≤ 0` (from (0,0)), `w₀+w₂ > 0`, `w₀+w₁ > 0` (from (0,1),(1,0)), and `w₀+w₁+w₂ ≤ 0` (from (1,1)). Adding the two middle inequalities: `2w₀+w₁+w₂ > 0`, but the first and last give `2w₀+w₁+w₂ ≤ w₀ ≤ 0`. Contradiction. ∎

Best a linear classifier can do on XOR: **3 of 4 correct** (25% error — computer-verified).

**History** [slides 37, 42]: 1957 Rosenblatt invents the perceptron (MARK 1 hardware, slide 25) → 1969 Minsky & Papert's *Perceptrons* proves the XOR limit → neural-net research declines in the 70s ("AI winter") → 1974 backpropagation proposed as the fix for training multi-layer networks (→ L08/L09).

**Two fixes for XOR** — compare deliberately (Wiring cross-wire #13):
1. **This lecture:** keep 1 layer, add the computed feature `x₁x₂` (§11) → kernel philosophy.
2. **L08:** stack perceptrons — `XOR = AND(OR(x₁,x₂), NAND(x₁,x₂))` → deep-learning philosophy.

## 11. Fix: computed features <a name="11-features"></a>
[Source: VL07 slides 38–40, 44–46]

Augment `ψ(x) = (1, x₁, x₂, x₁x₂)` with `w = (−0.5, 1, 1, −2)` — verified table [slide 39]:

| x₁ x₂ | z = w·ψ(x) | step(z) | XOR |
|---|---|---|---|
| 0 0 | −0.5 | 0 | 0 ✓ |
| 0 1 | +0.5 | 1 | 1 ✓ |
| 1 0 | +0.5 | 1 | 1 ✓ |
| 1 1 | −0.5 | 0 | 0 ✓ |

- General recipe [slides 44–46]: non-separable in x-space can be **separable in a transformed space**. 1-D example: classes split by `|x₁|` → add `x₂ = x₁²` → separable [slide 45]. Full quadratic augmentation: `φ(x) = (1, x₁, x₂, x₁x₂, x₁², x₂²)` [slide 46].
- "Analogous to polynomial curve fitting" [slide 39] — this is L04's basis expansion doing classification work.
- ⚠️ **Price** [slide 40]: higher dimension = easier separation = **overfitting risk** — the L02 U-curve (train error ↓, test error ∪) reappears verbatim on slide 40.

## 12. The mapping φ and its cost <a name="12-phi"></a>
[Source: VL07 slides 47–49]

The 3-step recipe [slide 47]: (1) map data via `φ(x⁽ⁱ⁾)` to a higher-dim space, (2) train a linear model there, (3) map unseen data through the *same* φ to predict.

**Cost blow-up** — dimension of a full quadratic (degree-2) mapping:
- n=3: `φ(x) = (x₁,x₂,x₃, x₁²,x₂²,x₃², x₁x₂,x₁x₃,x₂x₃)` → 9 dims [slide 48]
- general n: `n + n + n(n−1)/2 ∈ O(n²)` [slide 49]
- MNIST n=784 → **308,504 dimensions** [slide 58] (= 784 + 784 + 784·783/2, computer-verified)

Computing and storing φ explicitly is the bottleneck → kernels.

## 13. Kernelization criterion <a name="13-kernelize"></a>
[Source: VL07 slide 50]

> A method can be **kernelized** if every feature vector `x⁽ⁱ⁾` appears **only inside inner products** with other feature vectors: `x⁽ⁱ⁾·x⁽ʲ⁾`.

The **dual-form perceptron** qualifies (prediction `= sign Σⱼ αⱼy⁽ʲ⁾(x⁽ʲ⁾·x)` — §7). Slide 50 notes logistic regression can also be kernelized. This criterion is *why* the dual form was introduced.

## 14. The kernel trick <a name="14-trick"></a>
[Source: VL07 slides 51–54]

A dot product of mappings is just a real number → define a **kernel** that produces the same number *without ever computing φ*:

```
K(x, z) ≡ φ(x)·φ(z) ∈ ℝ        computed by algebraic shortcut in the ORIGINAL space
```

**Worked example** [slides 52–53] — `φ(x) = (x₁², x₂², √2·x₁x₂)`:

| Way | Computation | Ops |
|---|---|---|
| Naïve | build φ(x), φ(z), then dot: `x₁²z₁² + x₂²z₂² + 2x₁x₂z₁z₂` | ≈ 11 |
| Kernel | `(x·z)² = (x₁z₁ + x₂z₂)²` — same expansion, never left ℝ² | ≈ 4 |

Verify once by hand (mock exam B3): `x=(1,2), z=(3,1)`: `(x·z)² = 5² = 25`; `φ(x)·φ(z) = 1·9 + 4·1 + (2√2)(3√2) = 9+4+12 = 25` ✓.

The difference [slide 54]: naïve works *in* φ-space; kernel **stays in x-space** but yields the identical scalar.

## 15. The polynomial kernel <a name="15-poly"></a>
[Source: VL07 slides 55–58]

```
K(x, z) = (1 + x·z)^d      ⟷      degree-d polynomial mapping
```

For d=2: `φ(x) = (1, √2x₁, √2x₂, x₁², x₂², √2x₁x₂)` [slide 55] — the constant 1 and √2-weighted linear terms make the expansion of `(1+x·z)²` come out exactly.

**Cost:** O(n^d) implicit features, computed in **O(n)** time [slides 55, 57]. MNIST: naïve = dot products in 308,504-dim space; kernel = time proportional to 784 [slide 58]. Slides 59–60: a *linear* kernel fails to converge on non-separable rings; the quadratic kernel separates them.

## 16. Common kernel functions <a name="16-common"></a>
[Source: VL07 slide 61]

| Kernel | Formula |
|---|---|
| Linear | `K(x,z) = x·z` |
| Polynomial | `K(x,z) = (1 + x·z)^d` |
| **RBF / Gaussian** | `K(x,z) = exp(−‖x−z‖² / 2σ²)` |
| Specialized | graph kernels, string-similarity kernels (see slide 61's link) |

## 17. The RBF / Gaussian kernel <a name="17-rbf"></a>
[Source: VL07 slides 64–67, 76]

Same formula as the 2d Normal density **without the normalization term** [slides 64–65]:

```
K(x, z) = exp( −‖x−z‖² / 2σ² )      σ² = hyper-parameter (drop-off rate)
```

- `K` measures how close z is to the center of a Gaussian bell centered at x [slide 66]. E.g. x=(0,0), z=(−2,−1): ‖x−z‖²=5; with σ²=1, K = e^(−2.5) ≈ **0.082** (far → small).
- `K(x,x) = e⁰ = 1` (identical → maximal similarity).
- Formally [slide 76]: replace **all** dot products `x⁽ⁱ⁾·x⁽ʲ⁾` by `K_rbf(x⁽ⁱ⁾, x⁽ʲ⁾, σ)`. This implicitly maps into an **infinite-dimensional** space (Taylor-series expansion of the exponential — stated, not shown).
- 🔗 Cross-wires: the formula is **SaD 08's bell curve used as a similarity measure**; "similarity to training points" is **k-NN thinking (SaD 13 / L02)** smuggled into a linear classifier.

## 18. RBF as similarity: landmarks <a name="18-landmarks"></a>
[Source: VL07 slides 68–75]

Feature-construction view of RBF:

1. Choose **landmarks** `l⁽¹⁾, …` — the lecture uses **all m training points** as landmarks [slide 72].
2. For any x, compute new features `fᵢ = K(x, l⁽ⁱ⁾)`: `fᵢ ≈ 1` near the landmark, `≈ 0` far away [slide 68].
3. Train/predict linearly on f: `predict y=1 iff w·f ≥ 0` [slide 69].

Worked example [slide 70]: `w = (−0.5, 1, 1, 0)`, query lands near l⁽²⁾ → `f ≈ (0, 1, 0)` → `z = −0.5 + 0 + 1 + 0 = 0.5 ≥ 0` → predict 1.

Each training sample becomes an m-vector of similarities `f⁽ⁱ⁾ = (K(x⁽ⁱ⁾,x⁽¹⁾), …, K(x⁽ⁱ⁾,x⁽ᵐ⁾)) ∈ ℝᵐ`, with `fᵢ⁽ⁱ⁾ = 1` [slide 73].

**σ² controls the drop-off** [slides 71, 74–75]: small σ² = sharp spike (only immediate neighbourhood counts → wiggly boundary, variance risk); large σ² = wide bell (smooth boundary, bias risk). *That's the bias-variance dial of the RBF kernel — same role as k in k-NN.*

## 19. The kernelized perceptron <a name="19-kernel-perceptron"></a>
[Source: VL07 slide 62]

Take the dual algorithm (§7), replace the dot product with any kernel:

```
ŷ = sign( Σⱼ αⱼ y⁽ʲ⁾ K(x⁽ʲ⁾, x) )
if misclassified:  αᵢ = αᵢ + 1
```

One-line summary of the whole middle of this lecture: **dual form + kernel = non-linear perceptron without ever computing φ**. ("More in the tutorials" [slide 62] → Übung deck.)

## 20. Multi-class: One-vs-Rest <a name="20-ovr"></a>
[Source: VL07 slides 81, 84–87]

`Y = {1, …, k}` (wine k=3, email tagging k=4, weather k=4 [slide 81]). Of the methods so far [slide 83]: **k-NN is inherently multi-class; logistic regression and the perceptron are not** (both are binary).

**One-vs-Rest (OvR)** — adapt the *data*:
- Train k binary classifiers; for classifier j, class j's samples are positive, **all** others negative [slide 86].
- Parameters: `k × (n+1)` total.
- Predict: compute all k responses, pick `ŷ = argmax_j h_w⁽ʲ⁾(x)` [slide 87].

## 21. Multi-class: the multiclass perceptron <a name="21-mc-perceptron"></a>
[Source: VL07 slides 88–92]

Adapt the *model*: jointly learn `w ∈ ℝ^(k×(n+1))` — one weight row per class [slide 88].

- **Predict:** `ŷ = argmax_{j∈Y} (w⁽ʲ⁾·x)` — highest response wins [slide 89].
- **Learn** [slide 90]:

```
init w⁽¹⁾ = … = w⁽ᵏ⁾ = 0
while error on train data:
    for each (x⁽ⁱ⁾, y⁽ⁱ⁾):
        ŷ = argmax_j (w⁽ʲ⁾·x⁽ⁱ⁾)
        if ŷ ≠ y⁽ⁱ⁾:
            w^(y⁽ⁱ⁾) += x⁽ⁱ⁾      # give the CORRECT class more weight
            w^(ŷ)    −= x⁽ⁱ⁾      # give the WRONGLY-predicted class less
```

**Two rows change per mistake** — the true class is pulled toward x, the impostor pushed away.
- Boundary between classes c and c′ [slide 92]: predict c iff `w⁽ᶜ⁾·x > w⁽ᶜ′⁾·x` ⟺ `(w⁽ᶜ⁾−w⁽ᶜ′⁾)·x > 0` — pairwise boundaries are still linear.
- 🔗 `argmax` over class scores = the pre-softmax decision rule; L08 replaces argmax with **softmax** to make it differentiable (Wiring cross-wire #6).

## 22. OvR vs multi-class extension <a name="22-comparison"></a>
[Source: VL07 slides 84, 94]

| | One-vs-Rest | Multi-class extension |
|---|---|---|
| Adapts… | the **input data** (k binary problems) | the **model** (joint parameters) |
| Applicability | **always** applicable | each model must be re-derived |
| Training | easy to **parallelize** by class | joint |
| Quality | **greedy/heuristic**; suffers **imbalanced splits** (1 class vs k−1) | **optimal solution** |

## 23. Summary <a name="23-summary"></a>

1. Linear classifiers = hyperplane `w·x=0` + activation; logistic regression and the perceptron are siblings [slides 5, 41].
2. Perceptron: `ŷ = sign(w·x)`; convex "amount-wrong" loss; SGD update `w += y·x` on mistakes; converges **iff** linearly separable.
3. Dual form `w = Σαᵢy⁽ⁱ⁾x⁽ⁱ⁾` → predictions need only **dot products** → kernelizable.
4. Kernel trick: `K(x,z) ≡ φ(x)·φ(z)` computed in the original space — O(n) instead of O(n^d); polynomial and RBF are the workhorses.
5. RBF = Gaussian similarity to landmarks (= all training points); σ² is its bias-variance dial; implicit dimension ∞.
6. Multi-class: OvR (simple, heuristic, imbalanced) vs multiclass perceptron (joint argmax, two-row update, optimal).
7. XOR kills the single linear layer → this lecture's fix is features/kernels; L08's fix is stacking. Know both.

## 24. Self-test <a name="24-self-test"></a>

- [ ] Write the perceptron prediction, loss, sub-gradient, and update rule from memory. Why is no learning rate needed?
- [ ] State the convergence theorem *and* what happens on non-separable data.
- [ ] Derive `w = Σαᵢy⁽ⁱ⁾x⁽ⁱ⁾` from the update rule. What exactly is αᵢ?
- [ ] State the kernelization criterion and explain why the dual (not primal) form satisfies it.
- [ ] Show `K(x,z) = (x·z)²` equals `φ(x)·φ(z)` for `φ(x) = (x₁², x₂², √2x₁x₂)` — numerically with x=(1,2), z=(3,1) (→ 25).
- [ ] Give the operation-count argument: degree-2 features for MNIST naïvely vs via kernel.
- [ ] Write the RBF kernel. What happens for x=z? For ‖x−z‖ → ∞? What does σ² control (in bias-variance words)?
- [ ] Give AND, OR, NAND weight vectors and verify their truth tables with step activation.
- [ ] Prove XOR is not linearly separable (4-inequality contradiction).
- [ ] Build XOR with the feature x₁x₂ (give w and the table). Name the *other* fix (L08) and the philosophy each represents.
- [ ] Write the multiclass-perceptron update. Why do exactly two weight rows change?
- [ ] Name two advantages of OvR and its two drawbacks.

*All numerical values in this reference are computer-verified (NumPy). Slide numbers from the SoSe 2026 deck; pdftotext extraction can shift ±1 slide — trust the content anchor.*
