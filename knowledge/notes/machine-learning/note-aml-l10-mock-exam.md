---
id: note-aml-l10-mock-exam
type: note
title: "AML L10 — Mock Exam (Convolutional Neural Networks)"
created: "2026-08-15"
role: mock-exam
state: evolving
authorship: operator-drafted
concepts: [concept-neural-network, concept-backpropagation]
sources: [source-aml-ss26-lectures]
contexts: [workspace-aml-exam-prep]
---

> **Build note (2026-08-15).** Drafted by the operator from `VL 10-cnn.pdf`.
> Companion: `note-aml-l10-cnn` (section refs in the key). `authorship: operator-drafted`
> — key operator-computed, **unverified by Aram**. Difficulty at or above the real
> exam by design.

# AML Lecture 10 — Mock Exam (Convolutional Neural Networks)

**Topic:** convolution arithmetic, filters and edge detection, padding, stride and
shapes, multi-channel and multi-filter convolution, pooling, parameter counting,
sparse connectivity and weight sharing, the CNN pipeline, classic architectures,
degradation and residual connections.
**Companion:** `note-aml-l10-cnn` (§ refs in the key).
**Suggested time:** 75 minutes, closed-book.

> **Scoring:** Part A = 20 (2 each) · Part B = 40 · Part C = 15 (3 each) ·
> Part D = 25. **Total 100.**
>
> ⚠️ **Batch normalization is not examined beyond its name.** Backprop through
> convolutions is not in this deck. RNNs are out of current scope.

---

## Part A — Conceptual Short Answer (2 pts each)

**A1.** Why are fully-connected networks a poor fit for images? Give the concrete
number the deck uses for a 1000×1000 RGB image.

**A2.** Name the three layer types a CNN is composed of.

**A3.** What does the filter `[[1,0,−1],[1,0,−1],[1,0,−1]]` detect? What detects
the perpendicular feature?

**A4.** Write the output-size formula for input `n×n`, filter `f×f`, padding `p`,
stride `s`.

**A5.** Define valid padding and same padding.

**A6.** A `1000×1000×3` input is convolved with one `3×3×3` filter. Give the
output depth and explain it in one sentence.

**A7.** State the rule connecting number of filters to output shape.

**A8.** How many learnable parameters does a max-pooling layer have?

**A9.** Give the rationale for weight sharing, in the lecture's own terms.

**A10.** Write the residual-block activation.

---

## Part B — Numerical Problems (show your work)

### B1. Convolution by hand (8 pts)

Compute the top-left entry of the convolution of

```
3  0  1  2         with filter    1  0 -1
1  5  8  9                        1  0 -1
2  7  2  5                        1  0 -1
0  1  3  1
```

and give the output dimensions of the full convolution (valid padding).

### B2. Shapes (10 pts)

Give the output shape for each:

(a) `n=32, f=5, p=0, s=1`, 6 filters, input depth 3
(b) `n=28, f=5, p=0, s=1`, 10 filters, input depth 6
(c) `n=7, f=3, p=0, s=2`, 1 filter, input depth 1
(d) `n=224, f=7, p=3, s=2`, 64 filters, input depth 3

### B3. Parameter counting (12 pts)

Input is a `300×300×3` RGB image.

(a) A fully-connected layer with 100 neurons — how many weights including bias?
(b) A conv layer with 100 filters of `5×5×3` — how many weights including bias?
(c) State the ratio, and say which quantity in (a) is absent from (b).

### B4. Pooling (4 pts)

Max-pool with filter 2, stride 2:

```
1  3  2  1
2  9  1  1
1  3  2  3
5  6  1  2
```

### B5. FC vs conv on identical shapes (6 pts)

Input `32×32×3`, desired output `32×32×2`. Compare the parameter count of a
fully-connected first hidden layer against 2 conv filters of `5×5×3`.

---

## Part C — True / False + One-Line Justification (3 pts each)

**C1.** Training a deeper network always results in a lower training error.

**C2.** Convolving a 3-channel image with one 3-channel filter produces a
3-channel output.

**C3.** In a typical CNN, fully-connected layers appear in the first few layers.

**C4.** The parameter count of a convolutional layer depends on the spatial size
of the input image.

**C5.** LeNet-5 used ReLU activations.

---

## Part D — Synthesis (25 pts)

**D1. (10 pts)** Explain why convolutional layers need drastically fewer
parameters than fully-connected layers for the same input and output dimensions.
Name and distinguish the **two** mechanisms, give the general parameter formula,
and support the argument with the deck's `32×32×3` numbers.

**D2. (8 pts)** Describe the standard CNN pipeline end to end for classifying a
`32×32×3` image. Name each stage, say what it does to the shape, and explain what
the deck means by "feature learning" versus "classification".

**D3. (7 pts)** A colleague reports that their 50-layer plain CNN has *higher
training error* than their 20-layer one, and concludes they are overfitting.
Diagnose it correctly, name the phenomenon and its cause, and explain how residual
connections fix it — including why the fix cannot make things worse.

---
---

# ANSWER KEY

*Section refs are to `note-aml-l10-cnn`.*

## Part A

**A1.** They flatten the image and **ignore spatial dependencies**; a 1000×1000
RGB image is **3 million** features, so *"each hidden unit has roughly 3 million
weights to learn"*. (§0, p3–4)

**A2.** Convolution layers, pooling layers, fully-connected layers. (§0, p9)

**A3.** **Vertical edges.** The perpendicular (horizontal) detector is its
transpose, `[[1,1,1],[0,0,0],[−1,−1,−1]]`. (§2, p16, p19)

**A4.** `⌊(n + 2p − f)/s + 1⌋ × ⌊(n + 2p − f)/s + 1⌋`. (§4, p27)

**A5.** **Valid:** convolve only where the whole filter lies inside the input →
`(n−f+1)×(n−f+1)`. **Same:** zero-pad so the output equals the input size, `n×n`.
(§3, p22–23)

**A6.** Depth **1**. The filter's three channels convolve the matching input
channels and the results are **summed plus a bias**, so the channel dimension
collapses. (§5, p28–29)

**A7.** **#output channels = #filters** (each filter contributes one map); filter
depth must equal input depth. (§6, p30)

**A8.** **Zero** — pooling is a fixed operation. (§7, p31)

**A9.** *"A vertical edge detector that's useful in one part of the image is
probably useful in another part of the image."* (§9, p40)

**A10.** `a[l+2] = g( z[l+2] + a[l] )`. (§13, p60)

## Part B

**B1. (8 pts)**
```
3(1)+0(0)+1(−1) + 1(1)+5(0)+8(−1) + 2(1)+7(0)+2(−1)
= (3−1) + (1−8) + (2−2) = 2 − 7 + 0 = −5
```
Output: `(4−3+1) = 2` → **2×2**. (§1, p11)

**B2. (10 pts)** — using `⌊(n+2p−f)/s + 1⌋`, depth = #filters:
```
(a) (32−5)/1 + 1 = 28      → 28×28×6
(b) (28−5)/1 + 1 = 24      → 24×24×10
(c) (7−3)/2 + 1  = 3       → 3×3×1
(d) (224+6−7)/2 + 1 = 112  → 112×112×64
```
(§4, §6). (d) is AlexNet/ResNet-style stem arithmetic.

**B3. (12 pts)**
```
(a) 300 × 300 × 3 = 270,000;  × 100 = 27,000,000;  + 100 = 27,000,100
(b) (5 × 5 × 3 + 1) × 100 = 76 × 100 = 7,600
(c) ratio ≈ 3,553 : 1
```
Absent from (b): **the spatial size of the input (300×300)**. The conv count
depends only on filter size, input depth and filter count — that independence *is*
weight sharing. (§8, p34, p36)

**B4. (4 pts)**
```
[9 2]
[6 3]
```
patches `{1,3,2,9}→9`, `{2,1,1,1}→2`, `{1,3,5,6}→6`, `{2,3,1,2}→3`. (§7, p31)

**B5. (6 pts)**
```
FC:   3072 × 2048 + 2048 = 6.2 million
CONV: 2 × (5×5×3 + 1)    = 152
```
(§8, p39)

## Part C

**C1. False.** The **degradation problem** — beyond some depth *training* loss
increases, due to vanishing gradients preventing early layers from propagating
information. (§13, p57–58)

**C2. False.** One filter gives **one** output channel; the filter's channels are
summed with a bias. Three channels would require three filters. (§5, p28–29)

**C3. False.** FC layers come **last** — feature learning first, classification
last. Putting them first would discard the spatial structure. (§11, p49–51)

**C4. False.** `#params = (f·f·channels_in + 1) × #filters` — spatial size does
not appear. That is precisely the benefit of weight sharing. (§8)

**C5. False.** LeNet-5 used **sigmoid**; ReLU arrived with **AlexNet** (2012).
(§12, p54–55)

## Part D

**D1. (10 pts)** — 4 pts the two mechanisms, 2 pts the formula, 4 pts the numbers.

*Two distinct mechanisms:*

1. **Sparse connectivity (p35):** each hidden unit connects only to a **local
   neighbourhood** rather than every pixel. On a 200×200 input a 10×10 filter
   means ~100 weights per unit instead of 40,000 (p33).
2. **Weight sharing (p40):** the **same** filter is applied at every spatial
   position, so the parameter count becomes independent of image size. Rationale:
   *"A vertical edge detector that's useful in one part of the image is probably
   useful in another part."*

*Formula:* `#params = (f × f × channels_in + 1) × #filters` — note the absence of
any term in `n`.

*The numbers (p39):* input `32×32×3 = 3072` units, output `32×32×2 = 2048` units.
Fully connected: `3072 × 2048 + 2048 = 6.2 million` weights. Two conv filters of
`5×5×3`: `2 × (5×5×3 + 1) = 152`. Identical input and output dimensions, four
orders of magnitude apart. Full credit should note this is **not** merely
compression — the sparse, shared structure encodes the prior that useful local
features are translation-invariant, which is *why* it works rather than merely
being smaller.

**D2. (8 pts)** — 4 pts stages and shapes, 4 pts the two halves.

```
Input 32×32×3
  → CONV (6 filters 5×5×3, ReLU)   → 28×28×6
  → POOL (2×2, stride 2)           → 14×14×6
  → CONV (10 filters 5×5×6, ReLU)  → 10×10×10
  → POOL                           → 5×5×10
  → FLATTEN                        → 250
  → FULLY CONNECTED                → class scores
```

Convolution applies learned filters and shrinks by `n−f+1` (or preserves size with
same padding), adding depth equal to the filter count. Pooling reduces spatial
dimensionality with no parameters. Flattening turns the volume into a vector for
the dense head.

*The two halves (p49–50):* everything up to the flatten is **feature learning** —
*"first layers extract low-level features, e.g. edges, colors; next layers extract
high-level features, e.g. objects"*. The fully-connected tail is
**classification**, mapping the learned representation to class scores. The split
matters because the conv stack is transferable across tasks while the head is
task-specific.

**D3. (7 pts)** — 3 pts diagnosis, 4 pts the fix.

*The diagnosis is wrong.* Overfitting means low training error with high
validation error. Here **training** error is higher for the deeper net, so the
model is failing to *fit*, not failing to generalise. This is the **degradation
problem** (p58): *"with networks getting too deep, the loss increases."*

*Cause:* **vanishing gradients** — *"it gets more and more difficult for the first
layers to propagate their information until the output layer"* (continuing L09's
`λᴸ` argument, where repeated multiplication by factors < 1 shrinks the signal
exponentially in depth).

*The fix:* a **residual connection** adds a shortcut so that
**`a[l+2] = g(z[l+2] + a[l])`** (p60). Why it cannot make things worse (p61): the
block can **learn the identity** by driving `W[l+2], b[l+2] → 0`, leaving
`a[l+2] = g(a[l])`. A deeper residual network can therefore always reproduce a
shallower one, so extra depth costs nothing in principle — which is exactly what
the plain 50-layer net could not do. The deck also names **batch normalization**
as a second solution, without developing it.

---

## Self-grading

| Band | Reading |
|---|---|
| **85–100** | L10 is exam-ready. The L08–L10 build is complete. |
| **70–84** | Solid. Re-drill the misses. |
| **55–69** | Shapes or parameter counting not automatic — redo exercise-bank groups B and C, then re-sit. |
| **< 55** | Re-read reference §4–§8 against the deck before re-sitting. |

> **Log the result.** Record the score and misses as evidence on `unit-aml-l10`,
> and let them drive which of L10's 19 routed sources you pick next.
