---
id: note-aml-l08-mock-exam
type: note
title: "AML L08 — Mock Exam (Feedforward Networks, Output Layers, Metrics)"
created: "2026-08-15"
role: mock-exam
state: evolving
authorship: operator-drafted
concepts: [concept-neural-network, concept-xor-problem, concept-softmax,
  concept-classification-metrics]
sources: [source-aml-ss26-lectures]
contexts: [workspace-aml-exam-prep]
---

> **Build note (2026-08-15).** Drafted by the operator from the current 2026 deck
> `VL 08-feedforward-neural-network.pdf`. Companion:
> `note-aml-l08-feedforward-networks` (section refs in the answer key).
> `authorship: operator-drafted` (schema has no "operator-drafted" value — see the workspace note) — the key is operator-computed and **unverified by
> Aram**. Difficulty is set at or above the real exam by design.

# AML Lecture 08 — Mock Exam (Feedforward Networks, Output Layers, Metrics)

**Topic:** XOR and gate composition, the MLP and forward propagation, activation
choice and expressiveness, output layers (regression / binary / multi-label /
softmax), and classification metrics including micro/macro/weighted averaging.
**Companion:** `note-aml-l08-feedforward-networks` (§ refs in the key).
**Suggested time:** 75 minutes, closed-book. Solve everything before opening the
key, then self-grade.

> **Scoring:** Part A = 20 (2 each) · Part B = 40 · Part C = 15 (3 each) ·
> Part D = 25. **Total 100.**
>
> **Conventions:** `step(0) = 1`. `σ(z) = 1/(1+e⁻ᶻ)`.
> Provided values: σ(−1)=0.267, σ(0)=0.5, σ(3)=0.952, σ(4)=0.982, σ(2.749)=0.94,
> σ(2.419)=0.918. e²=7.389, e¹=2.718, e⁰=1, e⁻¹=0.368.
>
> ⚠️ **No backpropagation is examined** — it is L09 (deck p53). If a question
> seems to need a gradient, re-read it.

---

## Part A — Conceptual Short Answer (2 pts each)

**A1.** Give the weight vectors (bias first) for OR, AND and NAND as single
linear classifiers with a step activation.

**A2.** Write `XOR` as a composition of the three gates above.

**A3.** What is a "hidden layer", in the lecture's own phrasing? Why is `a⁽¹⁾`
described as a non-linear *feature* of `x`?

**A4.** State the two constraints on activation functions: one on the hidden
layers, one on the output layer.

**A5.** Write the forward-propagation pseudocode, including initialisation.

**A6.** For a hidden layer with `n` units and input dimension `d`, give the shapes
of `W` and `b`, and of the resulting activation vector.

**A7.** A network must predict a house price. Give the number of output units and
`g_out`.

**A8.** State the difference between multi-label and multi-class classification,
and which one produces outputs that sum to 1.

**A9.** Write the softmax formula and the prediction rule.

**A10.** Define precision and recall in words (not just formulas), for the cancer
setting where `y=1` is the rare positive class.

---

## Part B — Numerical Problems (show your work)

### B1. Forward pass, element-wise (12 pts)

Network: 2 inputs → 2 sigmoid hidden units → 1 sigmoid output.

```
w₁ = (1, 2),   b₁ = −2
w₂ = (1, 2),   b₂ = +2
w_out = (−2, 4.5),   b_out = −1
```

Compute `ŷ` for **x = (1, 0)**. Show `z₁, a₁, z₂, a₂, z_out, ŷ`.

### B2. The same network, vectorised (8 pts)

Write `W⁽¹⁾`, `b⁽¹⁾`, `W⁽ᵒᵘᵗ⁾`, `b⁽ᵒᵘᵗ⁾` explicitly and recompute B1 in matrix
form. Then compute `ŷ` for **x = (0, 1)**.

### B3. Expressiveness (8 pts)

Show that a two-layer MLP with the identity activation `g(x) = x` reduces to a
single linear model. Give `W′` and `b′` in terms of `W⁽¹⁾, W⁽²⁾, b⁽¹⁾, b⁽²⁾`, and
state the consequence in one sentence.

### B4. Softmax (6 pts)

Output scores `z = (2.0, 1.0, 0.0)`. Compute the softmax probabilities and the
predicted class. Verify they sum to 1.

### B5. Multi-class metrics (6 pts)

From this per-class table, compute **accuracy (micro)**, **macro-precision** and
**weighted-precision**.

| Label | tp | fp | fn | precision | recall | support |
|---|---|---|---|---|---|---|
| A | 4 | 2 | 1 | 0.67 | 0.80 | 5 |
| B | 1 | 3 | 4 | 0.25 | 0.20 | 5 |
| C | 9 | 1 | 1 | 0.90 | 0.90 | 10 |
| total | 14 | 6 | 6 | | | 20 |

---

## Part C — True / False + One-Line Justification (3 pts each)

**C1.** A deep network with linear activations can separate XOR if given enough
layers.

**C2.** The hidden-layer and output-layer activation functions must be identical.

**C3.** In a multi-label network with three sigmoid outputs, the three outputs sum
to 1.

**C4.** For skewed classes, a classifier with 99.5% accuracy is necessarily better
than one with 99% accuracy.

**C5.** Macro-averaged precision weights each class by how often it occurs.

---

## Part D — Synthesis (25 pts)

**D1. (10 pts)** A colleague proposes solving XOR by adding more perceptron units
*in the same single layer*, all reading `x` directly, then thresholding their sum.
Explain precisely why this fails, and what structural change is required. Refer to
both the XOR geometry and the expressiveness argument.

**D2. (8 pts)** You are building a cancer screen: 5 positives per 1000 patients.
Your model reports **99% accuracy**. Your supervisor is pleased. Write the
argument that this number is uninformative, construct the baseline that beats it,
and name the three metrics you would report instead and why.

**D3. (7 pts)** For the per-class table in B5, macro-precision and
weighted-precision differ substantially. Explain the mechanism, then argue which
one should be reported **if class B is the clinically dangerous class**.

---
---

# ANSWER KEY

*Section refs are to `note-aml-l08-feedforward-networks`.*

## Part A

**A1.** `w_OR = (−0.5, 1, 1)`, `w_AND = (−1.5, 1, 1)`, `w_NAND = (1.5, −1, −1)`.
Class 1 ⇔ `wᵀx > 0`. (§2, p7–9)

**A2.** `XOR(x₁,x₂) = AND( OR(x₁,x₂), NAND(x₁,x₂) )`. (§3, p10)

**A3.** The hidden layer is the vector `a⁽¹⁾` of hidden-unit outputs — *"'Hidden
units' are the output of a linear model"* (p17), *"We call a⁽¹⁾ a hidden layer"*
(p11). It is a **non-linear feature of x** because each unit applies a non-linear
activation to a linear function of `x`, producing a representation in which the
original non-separable problem becomes separable. (§3)

**A4.** Hidden: `g` **must be non-linear** — stacking linear functions collapses
to a single linear function (p36). Output: `g_out` is chosen **by the task**, and
it defines the type of ML problem (p37–38). (§9)

**A5.**
```
a⁽⁰⁾ = x
for i = 1 to L:  a⁽ⁱ⁾ = g(W⁽ⁱ⁾a⁽ⁱ⁻¹⁾ + b⁽ⁱ⁾)
ŷ = g_out(W⁽ᵒᵘᵗ⁾a⁽ᴸ⁾ + b⁽ᵒᵘᵗ⁾)
```
(§7, p25) — full marks require `a⁽⁰⁾ = x` and `g_out` on the last line.

**A6.** `W ∈ ℝⁿˣᵈ`, `b ∈ ℝⁿ`, `a = g(Wx+b) ∈ ℝⁿ`. (§6, p20–21)

**A7.** One output unit; `g_out(z) = z` (identity/linear). (§11, p23, p37)

**A8.** Multi-label = several independent yes/no questions about the same input
(car *and* pedestrian), `k` independent sigmoids, outputs **do not** sum to 1.
Multi-class = exactly one of `k` classes, softmax, outputs **do** sum to 1.
(§11–13, p42–50)

**A9.** `p(y=i|x) = e^{zᵢ} / Σⱼ e^{zⱼ}`; `ŷ = argmax_{yᵢ∈Y} p(y=yᵢ|x)`.
(§13, p49–50)

**A10.** Precision: of all patients we predicted positive, the fraction that
actually has cancer. Recall: of all patients that have cancer, the fraction we
correctly detected. (§17, p62, p64)

## Part B

**B1. (12 pts)**
```
z₁ = 1(1) + 2(0) − 2 = −1        a₁ = σ(−1) = 0.267
z₂ = 1(1) + 2(0) + 2 = +3        a₂ = σ(+3) = 0.952
z_out = −2(0.267) + 4.5(0.952) − 1 = −0.534 + 4.284 − 1 = 2.749
ŷ = σ(2.749) = 0.94
```
(§8, p30–31). *Marking: 3 pts each hidden pre-activation+activation, 4 pts output,
2 pts final.*

**B2. (8 pts)**
```
W⁽¹⁾ = [[1,2],[1,2]]   b⁽¹⁾ = (−2, 2)
W⁽ᵒᵘᵗ⁾ = (−2, 4.5)      b⁽ᵒᵘᵗ⁾ = −1

x=(1,0):  W⁽¹⁾x + b⁽¹⁾ = (1,1)+(−2,2) = (−1,3) → a = (0.267, 0.952) → ŷ = 0.94 ✓

x=(0,1):  W⁽¹⁾x + b⁽¹⁾ = (2,2)+(−2,2) = (0,4)
          a = (σ(0), σ(4)) = (0.5, 0.982)
          z_out = −2(0.5) + 4.5(0.982) − 1 = −1 + 4.419 − 1 = 2.419
          ŷ = σ(2.419) = 0.918
```
(§8, p32)

**B3. (8 pts)**
```
ŷ = W⁽²⁾(W⁽¹⁾x + b⁽¹⁾) + b⁽²⁾ = W⁽²⁾W⁽¹⁾x + W⁽²⁾b⁽¹⁾ + b⁽²⁾ = W′x + b′
W′ = W⁽²⁾W⁽¹⁾        b′ = W⁽²⁾b⁽¹⁾ + b⁽²⁾
```
Consequence: with only linear activations any MLP is expressible as a single
neuron, so it can represent only linear functions — non-linear `g` is required for
non-linear decision boundaries. (§10, p40)

**B4. (6 pts)**
```
e^{2.0}=7.389, e^{1.0}=2.718, e^{0.0}=1.000     Σ = 11.107
p₁ = 7.389/11.107 = 0.665
p₂ = 2.718/11.107 = 0.245
p₃ = 1.000/11.107 = 0.090
sum = 1.000 ✓        ŷ = class 1
```

**B5. (6 pts)**
```
Accuracy (micro) = Σtp / total = 14/20 = 0.70
Macro_P    = (1/3)(0.67 + 0.25 + 0.90) = 1.82/3 = 0.607 ≈ 0.61
Weighted_P = (5/20)(0.67) + (5/20)(0.25) + (10/20)(0.90)
           = 0.1675 + 0.0625 + 0.450 = 0.680 ≈ 0.68
```
(§18, p75–78)

## Part C

**C1. False.** By the collapse argument, any depth of linear activations equals
`W′x + b′` — one linear boundary, and XOR needs two. Depth adds nothing without
non-linearity. (§10)

**C2. False.** p38 states explicitly they need not be the same; only `g` must be
non-linear, while `g_out` is fixed by the task. (§9)

**C3. False.** Independent sigmoids do not normalise — p45: *"Activations do not
sum to 1."* That is precisely the deficiency softmax fixes. (§12)

**C4. False.** With 0.5% prevalence, the constant predictor `return 0` achieves
99.5% accuracy while detecting nothing. Higher accuracy can mean strictly less
useful. (§15, p60)

**C5. False.** That is the *weighted* average. Macro takes the **unweighted mean**
and explicitly *"ignores frequency of class labels"* (p76). (§18)

## Part D

**D1. (10 pts)** — 4 pts geometry, 4 pts expressiveness, 2 pts the fix.

*Geometry:* XOR's positive class is {(0,1),(1,0)} and its negative class is
{(0,0),(1,1)} — the two classes sit on opposite diagonals, so no single straight
line separates them (p6).

*Why more units in one layer does not help:* every unit in that layer reads `x`
directly, so each computes `step(wᵢᵀx)` — a linear function thresholded. Summing
them and thresholding again produces another function of linear forms of `x`; with
no intermediate non-linear **re-representation**, the composite still carves `x`-space
with linear boundaries. The expressiveness argument (p40) is the general statement:
composition without a non-linearity *between* the linear maps collapses to
`W′x + b′`.

*The structural change:* the units' outputs must be **fed as inputs to a further
unit** — i.e. become a hidden layer — so the second stage classifies in `a`-space,
not `x`-space. In `a = (OR, NAND)` coordinates the XOR classes *are* linearly
separable, and a single AND unit finishes the job (p10–12). Depth, not width, and
specifically depth *with* a non-linearity.

**D2. (8 pts)** — 3 pts baseline, 2 pts the argument, 3 pts metrics.

*Baseline:* `def predictNaive(): return 0` — always predict "no cancer". With
5/1000 prevalence it is right 995 times out of 1000: **99.5% accuracy, 0.5%
error** (p60). It beats the 99% model while detecting **zero** cancers.

*Argument:* accuracy is dominated by the majority class under skew, so it measures
how common the negative class is rather than whether the model works. A metric a
constant function can win is not measuring the task.

*Report instead:* **recall** (of the patients who have cancer, how many did we
catch — the clinically critical quantity, and the naïve baseline scores 0),
**precision** (of those we flagged, how many truly have it — governs false-alarm
cost), and **F₁**, the harmonic mean, which cannot be gamed by maximising one at
the other's expense: "always predict 1" gets recall 1.0 but F₁ ≈ 0.001 (p67–69).
Full credit should also mention reading the **confusion matrix** directly.

**D3. (7 pts)** — 4 pts mechanism, 3 pts the argument.

*Mechanism:* weighted-precision (0.68) exceeds macro (0.61) because class C, which
has the highest precision (0.90), also carries half the support (10/20), so
weighting by frequency lets C dominate. Class B, the worst performer at 0.25, has
support 5/20 and is correspondingly discounted — whereas macro gives B a full
third of the average regardless of how rare it is.

*Argument:* if **B is the clinically dangerous class**, report **macro** — or
better, report B's per-class precision and recall explicitly. Weighted averaging
would let strong performance on the common, benign classes conceal a 0.25
precision on the class where errors cause harm. This mirrors p59–60: the choice of
averaging is a claim about whose errors count, and under a safety objective rare
classes cannot be discounted by frequency. A strong answer notes that neither
average should replace looking at B's own row.

---

## Self-grading

| Band | Reading |
|---|---|
| **85–100** | L08 is exam-ready. Move to L09. |
| **70–84** | Solid. Re-drill the specific misses, then move on. |
| **55–69** | Forward pass or metrics not yet automatic — redo exercise-bank groups B and E, then re-sit. |
| **< 55** | Re-read the reference §7–8 and §15–18 against the deck before re-sitting. |

> **Log the result.** Record the score and the specific misses as evidence on
> `unit-aml-l08` — a mock sat and unrecorded leaves no trail (CLAUDE.md §7), and
> the misses are what should drive the next source choice from the L08 material
> menu (22 routed sources).
