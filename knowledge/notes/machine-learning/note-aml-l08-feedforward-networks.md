---
id: note-aml-l08-feedforward-networks
type: note
title: "AML L08 — Ultimate Reference: Feedforward Neural Networks, Output Layers, Metrics"
created: "2026-08-15"
role: reference
state: evolving
authorship: operator-drafted
concepts: [concept-neural-network, concept-xor-problem, concept-perceptron,
  concept-softmax, concept-classification-metrics]
sources: [source-aml-ss26-lectures]
contexts: [workspace-aml-exam-prep]
---

> **Build note (2026-08-15).** Drafted by the operator directly from the current
> 2026 deck `lecture-slides/VL 08-feedforward-neural-network.pdf` (81 pages),
> page-anchored throughout. Companions: `note-aml-l08-exercise-bank`,
> `note-aml-l08-mock-exam`. `authorship: operator-drafted` (schema has no "operator-drafted" value — see the workspace note) — **this is not yet Aram's
> synthesis.** Nothing here has been reasoned through by him; the note becomes
> `authorship: mixed` when he works it and adds his own reasoning. Treat every
> claim as slide-traceable but unverified-by-learner.

# AML Lecture 08 — Ultimate Reference: Feedforward Neural Networks

*Built from `VL 08-feedforward-neural-network.pdf`, 81 pages, page numbers cited
per section. Prior-year variant for cross-checking:
`older-lecture-slides/08-feedforward-neural-network_953c2f291a61db5a2b6cae1711b40edd.pdf`.*

> ⚠️ **Scope note (slide-verified).** This lecture stops at the **forward pass**.
> Backpropagation is named on p53 and explicitly deferred — *"How to update the
> weights of the hidden layers? • Next lecture."* Do not pull L09 backprop
> material into L08 scope. The lecture's own arc is:
> **XOR revisited → forward propagation → activation functions → expressiveness
> → output layers (multi-label, softmax) → training (named only) → toolkit →
> metrics.**
>
> The **metrics block (p58–81) is roughly a quarter of the deck** and is the part
> most likely to be underweighted, because it reads like an appendix and is not.

## Table of Contents

0. [Notation](#0-notation)
1. [Why another algorithm](#1-why)
2. [XOR revisited: OR, AND, NAND as linear classifiers](#2-gates)
3. [Composing XOR — the first MLP](#3-xor)
4. [Building blocks: perceptron vs logistic unit](#4-blocks)
5. [The MLP: hidden units, weights, biases](#5-mlp)
6. [Vectorising a layer](#6-vectorise)
7. [Forward propagation — the algorithm](#7-forward)
8. [The worked forward-pass example](#8-worked)
9. [Activation functions: hidden vs output](#9-activations)
10. [Expressiveness — why g must be non-linear](#10-expressiveness)
11. [Output layer by task](#11-output)
12. [Multi-label: independent sigmoids](#12-multilabel)
13. [Multi-class: the softmax layer](#13-softmax)
14. [Training and the toolkit](#14-toolkit)
15. [Why accuracy is a bad metric](#15-accuracy-bad)
16. [The confusion matrix](#16-confusion)
17. [Precision, recall, F1](#17-prf)
18. [Multi-class metrics: micro, macro, weighted](#18-averaging)
19. [Exam-shaped summary](#19-summary)

---

## 0. Notation <a name="0-notation"></a>

| Symbol | Meaning | Slides |
|---|---|---|
| `a⁽ˡ⁾ᵢ` | activation of unit `i` in layer `l` | p24 |
| `a⁽⁰⁾ = x` | input layer is activation zero | p25 |
| `W⁽ˡ⁾`, `b⁽ˡ⁾` | weight matrix and bias vector into layer `l` | p20–21 |
| `g` | activation function of the **hidden** layers | p36 |
| `g_out` | activation function of the **output** layer | p37–38 |
| `L` | number of hidden layers | p25 |
| `ŷ` | network output | p22 |
| `σ(z) = 1/(1+e⁻ᶻ)` | logistic sigmoid, range [0,1] | p16 |
| `sign(z)` | +1 if z ≥ 0, else −1 | p15 |

Shapes are worth memorising as shapes, not formulas: with a 3-dimensional input
and 3 hidden units, `W ∈ ℝ³ˣ³`, `b ∈ ℝ³`, `a ∈ ℝ³`, and the check on p21 is
`(3×3)(3×1) + (3×1) = (3×1)`.

## 1. Why another algorithm <a name="1-why"></a>

p3. The deck opens by asking why we need yet another learning algorithm when we
already have linear and polynomial regression, logistic regression, the (kernel)
perceptron, decision trees and ensembles. The answer given is empirical rather
than theoretical: neural networks are an old idea that is now state of the art
for computer vision, NLP and more. p4 shows the traditional-ML-vs-deep-learning
performance-against-data-volume sketch.

**Exam-relevant framing:** the lecturer motivates NNs as the *resolution of a
specific representational limit* — the XOR wall from L07 — not as a general
upgrade. That framing is what an exam question about "why stack layers" wants.

## 2. XOR revisited: OR, AND, NAND as linear classifiers <a name="2-gates"></a>

p6–9. XOR is restated as the truth table (0,0)→0, (0,1)→1, (1,0)→1, (1,1)→0 and
shown to be the diagonal-class problem no single line separates.

Three gates are then each realised as a single linear classifier with
`Class 1 ⇔ wᵀx > 0` and a step activation. **Memorise these weight vectors —
they recur in the composition and in the exercises:**

| Gate | Weights (bias first) | Trace | Slide |
|---|---|---|---|
| OR | `w_OR = (−0.5, 1, 1)` | z = −0.5 + x₁ + x₂ | p7 |
| AND | `w_AND = (−1.5, 1, 1)` | z = −1.5 + x₁ + x₂ | p8 |
| NAND | `w_NAND = (1.5, −1, −1)` | z = 1.5 − x₁ − x₂ | p9 |

Each slide carries the full four-row trace of `z = w·x` and `step(z)`. The
pattern to internalise: **OR and AND differ only in the bias** — the bias sets
how many inputs must fire. NAND is AND with every sign flipped.

## 3. Composing XOR — the first MLP <a name="3-xor"></a>

p10–12. The key algebraic move:

```
XOR(x₁,x₂) = AND( OR(x₁,x₂), NAND(x₁,x₂) )
```

p10 verifies it row by row with `a₁ = OR`, `a₂ = NAND`:

| x₁ | x₂ | a₁ = OR | a₂ = NAND | AND(a₁,a₂) | XOR |
|---|---|---|---|---|---|
| 0 | 0 | 0 | 1 | 0 | 0 |
| 0 | 1 | 1 | 1 | 1 | 1 |
| 1 | 0 | 1 | 1 | 1 | 1 |
| 1 | 1 | 1 | 0 | 0 | 0 |

p11 rewrites this as *a program of perceptrons*:

```
a⁽¹⁾₁ = step(w_OR   · x)
a⁽¹⁾₂ = step(w_NAND · x)
ŷ     = step(w_AND  · a⁽¹⁾)
```

Two sentences on p11 carry most of the lecture's conceptual weight:

> *"Note that a⁽¹⁾ is a non-linear feature of x."*
> *"We call a⁽¹⁾ a hidden layer."*

This is the bridge from L07: the kernel trick bought non-linear features by
choosing a map φ; a hidden layer buys them by **learning** one. p12 stacks the
two hidden weight vectors into a single matrix and gives the complete two-layer
form, closing with *"This is our first Multi-Layer Perceptron"* and *"In
practice, we learn these weights using an algorithm called backpropagation."*

p13 links a Moodle gradient-descent demo for XOR.

## 4. Building blocks: perceptron vs logistic unit <a name="4-blocks"></a>

p15–16 contrast the two single units, and the contrast is examinable:

| Unit | Activation | Output | Interpretation | Slide |
|---|---|---|---|---|
| Perceptron | `sign(z)` | `{−1, +1}` | binary decision only | p15 |
| Logistic | `σ(z)` | `[0, 1]` | `p(y=1 | x)`, a probability | p16 |

Both are drawn with an explicit **bias unit `+1`** feeding weight `w₀`. On p16,
`1 − h(x) = p(y=0 | x)` is annotated directly on the sigmoid curve — the
complement is not a separate parameter.

## 5. The MLP: hidden units, weights, biases <a name="5-mlp"></a>

p17–19. The definition given is deliberately deflationary:

> *"We are simply stacking linear models with an activation function g."*
> *"'Hidden units' are the output of a linear model."*
> *"Connections are directed and information flows into one direction (left to right)."*

Per hidden unit `j`: `aⱼ = g(wⱼ · x + bⱼ)` with `wⱼ ∈ ℝᵈ`, `bⱼ ∈ ℝ` (p17, p19).

## 6. Vectorising a layer <a name="6-vectorise"></a>

p20–23. The individual `wⱼ` become the **rows** of `W`:

```
W = [ —w₁ᵀ— ; —w₂ᵀ— ; —w₃ᵀ— ] ∈ ℝ³ˣ³ ,  b = (b₁,b₂,b₃) ∈ ℝ³
a = g(Wx + b) ∈ ℝ³
```

p21 is the shape check written out — `Wx + b` expands to the column
`(w₁ᵀx + b₁, w₂ᵀx + b₂, w₃ᵀx + b₃)`, dimensions `3×3 · 3×1 + 3×1 = 3×1`. Being
able to reproduce that check is worth more in an exam than reciting the formula.

Output unit (p22–23): `ŷ = g_out(w_outᵀ a + b_out)` with `w_out ∈ ℝ³`,
`b_out ∈ ℝ`, and — stated on p23 — `g_out` depends on the task:
regression `g_out(z) = z`, classification `g_out(z) = σ(z)`.

p24 generalises to two hidden layers, showing every shape:
`W⁽¹⁾ ∈ ℝ³ˣ³`, `W⁽²⁾ ∈ ℝ²ˣ³`, `W⁽ᵒᵘᵗ⁾ ∈ ℝ¹ˣ²`.

## 7. Forward propagation — the algorithm <a name="7-forward"></a>

p25, given as pseudocode and worth memorising verbatim:

```
a⁽⁰⁾ = x                                  // initialization
for i = 1 to L
    a⁽ⁱ⁾ = g( W⁽ⁱ⁾ a⁽ⁱ⁻¹⁾ + b⁽ⁱ⁾ )        // activation of each hidden layer
ŷ = g_out( W⁽ᵒᵘᵗ⁾ a⁽ᴸ⁾ + b⁽ᵒᵘᵗ⁾ )         // output
```

> *"Forward Pass: This is how a neural network makes predictions."*

## 8. The worked forward-pass example <a name="8-worked"></a>

p26–32. **This is the single most exam-likely computation in the lecture** — the
deck spends seven slides building it up one step at a time, which is how the
lecturer signals what will be asked.

Network: 2 inputs → 2 sigmoid hidden units → 1 sigmoid output.

```
w₁ = (1, 2),  b₁ = −2
w₂ = (1, 2),  b₂ = +2
w_out = (−2, 4.5),  b_out = −1
input x = (1, 0)
```

Hidden layer (p30):

```
z₁ = (1,2)·(1,0) − 2 = 1 + 0 − 2 = −1   →  a₁ = σ(−1) = 0.267
z₂ = (1,2)·(1,0) + 2 = 1 + 0 + 2 = +3   →  a₂ = σ(+3) = 0.952
```

Output layer (p31):

```
z_out = (−2, 4.5)·(0.267, 0.952) − 1
      = −0.534 + 4.284 − 1 = 2.749
ŷ = σ(2.749) = 0.94
```

p32 repeats the identical computation in **vectorised** form with
`W⁽¹⁾ = [[1,2],[1,2]]`, `W⁽ᵒᵘᵗ⁾ = w_outᵀ = (−2, 4.5)`, `b⁽ᵒᵘᵗ⁾ = −1`, reaching
the same `a = (0.267, 0.952)` and `ŷ = 0.94`. **Practise it both ways** — the
exam may fix the form.

Sigmoid values worth having memorised: `σ(−1) ≈ 0.267`, `σ(0) = 0.5`,
`σ(3) ≈ 0.952`, `σ(2.749) ≈ 0.94`.

## 9. Activation functions: hidden vs output <a name="9-activations"></a>

p34–38. p34 shows the gallery of common activations. The two rules that matter:

- **Hidden layers (p36):** many choices, *"but g must be non-linear"* —
  *"Stacking linear functions is equivalent to a single linear function."*
- **Output layer (p37–38):** `g_out` is chosen by the task, and *"the activation
  function g_out in the output layer defines the type of machine learning
  problem."*

p38 makes explicit that hidden and output activations **need not be the same**,
and notes that designing activations for faster convergence is an active
research area.

## 10. Expressiveness — why g must be non-linear <a name="10-expressiveness"></a>

p40. The proof is short enough to reproduce under exam conditions, and doing so
is a likely 5–8 point question. Take a two-layer MLP:

```
ŷ = g⁽²⁾( W⁽²⁾ g⁽¹⁾( W⁽¹⁾x + b⁽¹⁾ ) + b⁽²⁾ )
```

Now set the activation to the identity, `g(x) = x`:

```
ŷ = W⁽²⁾( W⁽¹⁾x + b⁽¹⁾ ) + b⁽²⁾
  = W⁽²⁾W⁽¹⁾x + W⁽²⁾b⁽¹⁾ + b⁽²⁾
  = W′x + b′
```

Conclusion as the slide states it:

> *"Using only linear activations, we can express any MLP as a single neuron
> network."* → *"With only linear activations, a MLP can only express linear
> functions. We need non-linear activations to express non-linear (decision)
> functions."*

The collapse is exactly `W′ = W⁽²⁾W⁽¹⁾` and `b′ = W⁽²⁾b⁽¹⁾ + b⁽²⁾`. Depth without
non-linearity buys nothing.

## 11. Output layer by task <a name="11-output"></a>

Consolidating p23, p37, p42–50:

| Task | Output units | `g_out` | Outputs sum to 1? | Slide |
|---|---|---|---|---|
| Regression | 1 | identity, `z` | — | p23, p37 |
| Binary classification | 1 | `σ` (or sign/step) | — | p23, p37 |
| Multi-**label** | `k = |Y|` | `σ` on each, independently | **No** | p45, p48 |
| Multi-**class** | `k = |Y|` | softmax over all | **Yes** | p49–50 |

**The multi-label / multi-class distinction is the highest-yield discrimination
in this lecture.** Multi-label = "which of these are present" (a car *and* a
pedestrian); multi-class = "which one of these is it" (pedestrian *xor* car).

## 12. Multi-label: independent sigmoids <a name="12-multilabel"></a>

p42–45. Motivated by Andrew Ng's driving-scene example (p42): *is there a car? is
there a bus? is there a pedestrian?* — the target is a **vector** of independent
binary answers, e.g. `y = (1,0,1)`.

Two options are contrasted:

- **(a) One-vs-Rest (p43):** train `k = |Y|` separate networks; for each class,
  set that class to '1' and all others to '−1'. The slide's own verdict:
  *"Better: train one neural network with three outputs."*
- **(b) One network, k output neurons (p44–45):** each with sigmoid activation.
  Predict per label `yᵢ = a⁽ᵒᵘᵗ⁾ᵢ`.

p45's closing comment is the setup for softmax: *"Activations do not sum to 1."*
p48 restates it and names the fix: *"Solution: norm outputs to sum to 1."*

## 13. Multi-class: the softmax layer <a name="13-softmax"></a>

p47–50. p47 sets up the one-hot encoding: with
`Y = {pedestrian, car, motorcycle, truck}`, targets are `y ∈ ℝ⁴` and each label
is a one-hot column.

p49 gives the three-class expansion explicitly, then p50 the general form:

```
zᵢ = W⁽ᵒᵘᵗ⁾ᵢ · x + b⁽ᵒᵘᵗ⁾ᵢ

p(y = i | x) = a⁽ᵒᵘᵗ⁾ᵢ = e^{zᵢ} / Σⱼ₌₁ᵏ e^{zⱼ}

Σₖ p(y = k | x) = 1          (p49)

ŷ = argmax_{yᵢ ∈ Y} p(y = yᵢ | x)     (p50)
```

The normalising denominator is what makes the outputs a distribution rather than
`k` unrelated scores — that one sentence is the whole difference from p45.

## 14. Training and the toolkit <a name="14-toolkit"></a>

p52–57. p52 makes the qualitative point that weights further from the output
affect more downstream nodes, so changing any one weight changes the output.

p53 names **backpropagation (Rumelhart, Hinton & Williams, 1986)** and sketches
it as: forward-pass `x` to get `ŷ`; the last layer is closest to the error, so
(a) derive the error at the output and update those weights, then (b) recurse
backwards layer by layer. Then — *"How to update the weights of the hidden
layers? • Next lecture."* **Deferred to L09; not L08 exam scope.**

p55–57 cover toolkits. What you specify: the forward model as a computation
graph, the training samples and schedule, and the optimisation details (loss,
learning rate). *"The framework takes care of the derivative computations —
basic derivatives are hard-coded."*

p56 gives a Keras `Sequential` example (three `Dense` sigmoid layers 25→15→1,
`BinaryCrossentropy`, `adam`, `model.fit(X, Y, epochs=100)`). p57 is a
three-column Math / NumPy / TensorFlow correspondence table — worth reading as
"which abstraction level hides what", since it is the most likely source of a
conceptual toolkit question.

## 15. Why accuracy is a bad metric <a name="15-accuracy-bad"></a>

p59–60. The cancer-classification example, with the running class counts
`y=1 : 5`, `y=0 : 995` printed in the corner of every metrics slide:

- 1% test error → 99% of diagnoses right. *"We did pretty well?"*
- But only 0.5% of patients have cancer — **skewed classes**, 99.5% negative.
- The naïve baseline `def predictNaive(): return 0` scores **0.5% error, 99.5%
  accuracy** — better than the trained model.

That comparison is the argument. An exam question asking "why is accuracy
misleading here" wants the naïve baseline constructed, not just the words
"class imbalance".

## 16. The confusion matrix <a name="16-confusion"></a>

p61. Binary problem, positive class `y=1`, negative `y=0`:

|  | Actual `y=1` | Actual `y=0` |
|---|---|---|
| **Predicted `ŷ=1`** | True Positive (TP) | False Positive (FP) |
| **Predicted `ŷ=0`** | False Negative (FN) | True Negative (TN) |

Read the names as *(correctness, prediction)*: "false negative" = predicted
negative, and that was false. `y = 1` is the rare class we want to detect — a
footer repeated on p62–65.

## 17. Precision, recall, F1 <a name="17-prf"></a>

p62–69.

```
Accuracy  = (TP + TN) / total samples          (p66)
Precision = TP / (TP + FP)                     (p62)
Recall    = TP / (TP + FN)                     (p64)
F₁ = 2 · (P · R) / (P + R)  ∈ [0,1]            (p68)
```

In words, from the slides:

- **Precision (p62):** *of all patients we predicted `ŷ=1`, what fraction
  actually has cancer?*
- **Recall (p64):** *of all patients that have cancer, what fraction did we
  correctly detect?*

The degenerate-predictor table (p62–65) is the thing to be able to fill in cold:

| Strategy | TP | FP | FN | TN | Precision | Recall |
|---|---|---|---|---|---|---|
| always predict 1 | 5 | 995 | 0 | 0 | 5/1000 | 5/5 = 1.0 |
| always predict 0 | 0 | 0 | 5 | 995 | 0/0 ≡ 0 | 0/5 = 0 |

Note the convention on p63: **`0/0` is defined as `0`** for precision.

p67 and p69 give the comparison table that motivates F₁ — and it is the clearest
argument in the block:

| | Precision | Recall | F₁ |
|---|---|---|---|
| Algorithm 1 | 0.5 | 0.4 | 0.44 |
| Algorithm 2 | 0.7 | 0.1 | 0.175 |
| Algorithm 3 | 0.005 | 1.0 | 0.001 |

Algorithm 3 is "always predict `ŷ=1`". It has **perfect recall** and the
arithmetic mean would rank it respectably; the **harmonic** mean destroys it.
That is *why* F₁ is harmonic — it refuses to reward one metric bought entirely at
the other's expense. p68: F₁ reaches 1 only when both P and R are 1, and it is
useful under skew, as in anomaly detection.

## 18. Multi-class metrics: micro, macro, weighted <a name="18-averaging"></a>

p70–79. p70 flags the gap: P, R and F were defined for binary `Y = {0,1}`, but
most problems have more classes.

p71 gives the Iris-style confusion matrix, and p72–74 the one-vs-rest
decomposition — *for each class, set it 'True' and all others 'False', then
compute precision and recall*. The resulting per-class table (p72–78) is the
anchor for everything after, and its numbers are worth memorising because all
three averages are computed from them:

| Label | tp | fp | fn | precision | recall | support |
|---|---|---|---|---|---|---|
| versicolor | 2 | 1 | 1 | 0.67 | 0.67 | 3 |
| virginica | 1 | 3 | 0 | 0.25 | 1.00 | 1 |
| setosa | 3 | 0 | 3 | 1.00 | 0.50 | 6 |
| **total** | 6 | 4 | 4 | | | **10** |

The three averages (p75–78):

```
Accuracy (= micro average)  = 6/10 = 0.60
    "Ignores imbalances."                              (p75)

Macro_precision  = (1/3)(0.67 + 0.25 + 1.00) = 0.64
    "Compute mean of precision (or recall).
     Ignores frequency of class labels."               (p76)

Weighted_precision = (3/10)(0.67) + (1/10)(0.25) + (6/10)(1.00) = 0.82
    "Weight by frequency of class labels."             (p77)
```

Summary row from p77–78, and the pattern in it is the examinable insight:

| | Precision | Recall |
|---|---|---|
| Accuracy (micro) | 0.60 | 0.60 |
| Macro-averaged | 0.64 | 0.72 |
| Weighted-average | **0.82** | 0.60 |

**Weighted precision (0.82) is far above macro (0.64) because the one class that
scores perfectly — setosa, precision 1.00 — is also the most frequent (support
6/10).** Macro treats the badly-performing rare class (virginica, 0.25) as
equally important; weighted almost ignores it. Which average you report is
therefore a claim about whether rare classes matter — that is the point of the
slide, not the arithmetic.

p79 notes scikit-learn's `classification_report` produces all of these.

## 19. Exam-shaped summary <a name="19-summary"></a>

If you can do these eight things cold, L08 is covered:

1. Give `w_OR`, `w_AND`, `w_NAND` and trace all four rows of each (p7–9).
2. Compose XOR as `AND(OR, NAND)` and draw it as a 2-layer MLP with weights
   (p10–12).
3. Explain "a hidden layer is a learned non-linear feature of x", tying back to
   L07's kernel trick (p11).
4. Run the forward pass on the p26–32 network, both element-wise and vectorised,
   reaching `ŷ = 0.94`.
5. Prove that linear activations collapse an MLP to `W′x + b′` (p40).
6. Choose `g_out` and the number of output units for regression / binary /
   multi-label / multi-class, and say which sums to 1 (p23, p37, p45, p49).
7. Write softmax, show it normalises, and give the argmax prediction rule
   (p49–50).
8. Build the degenerate-predictor table, compute P/R/F₁, and compute all three
   multi-class averages from the per-class table (p62–78).

### Deliberately out of scope

- Backpropagation and gradient computation → **L09** (deferred on p53).
- Convolution, weight sharing → **L10**.
- Cross-entropy is *used* (p56, `BinaryCrossentropy`) but not derived here; its
  derivation sits with L05 logistic regression.

### Open questions for Aram

- p57's Math/NumPy/TensorFlow table: worth a hand-written reproduction, or is
  reading it enough? It is the kind of slide that is either free marks or absent.
- The prior-year L08 deck has not been diffed against the 2026 one. Worth 20
  minutes if you want certainty that no topic moved in or out.
