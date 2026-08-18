---
id: note-aml-l10-cnn
type: note
title: "AML L10 — Ultimate Reference: Convolutional Neural Networks"
created: "2026-08-15"
role: reference
state: evolving
authorship: operator-drafted
concepts: [concept-neural-network, concept-backpropagation]
sources: [source-aml-ss26-lectures]
contexts: [workspace-aml-exam-prep]
---

> **Build note (2026-08-15).** Drafted by the operator directly from the current
> 2026 deck `lecture-slides/VL 10-cnn.pdf` (70 pages), page-anchored throughout.
> Companions: `note-aml-l10-exercise-bank`, `note-aml-l10-mock-exam`.
> `authorship: operator-drafted` — **not yet Aram's synthesis**; becomes `mixed` when he
> works it. Slide-traceable but unverified-by-learner.

# AML Lecture 10 — Ultimate Reference: Convolutional Neural Networks

*Built from `VL 10-cnn.pdf`, 70 pages. Prior-year variant:
`older-lecture-slides/10-cnn_e88d2bb6a525f5e7dc6e15044f252d21.pdf`.*

> ⚠️ **Scope note (slide-verified).** The lecture's arc: convolutions → one layer
> → CNNs → famous architectures. It closes on residual connections — which L11
> then reuses inside the transformer block.
>
> *Correction 2026-08-15:* this note previously said L10 was "the last lecture
> with a current 2026 deck." That was true when written and is now false — the
> L11 Transformers deck (`VL 11-transformers.pdf`, 81 sl.) arrived the same day
> and is confirmed exam scope. See `note-aml-l11-transformers`.
>
> **This deck is unusually quiz-dense — five in-deck quiz slides** (p16, p34, p36,
> p51, p57). That is a strong signal about exam content; all five are drilled in
> the exercise bank.
>
> **Batch normalization is named once (p58) as a solution to the degradation
> problem and never developed.** Know it as a name, not a mechanism.

## Table of Contents

0. [Why not fully connected](#0-why)
1. [Convolution as cross-correlation](#1-conv)
2. [Filters and edge detection](#2-filters)
3. [Padding](#3-padding)
4. [Stride and the output-size formula](#4-stride)
5. [Multi-channel convolution](#5-channels)
6. [Multiple filters](#6-multifilter)
7. [Pooling](#7-pooling)
8. [Parameter counting — the exam's favourite](#8-params)
9. [Sparse connectivity and weight sharing](#9-sharing)
10. [One convolutional layer end to end](#10-layer)
11. [The full CNN](#11-cnn)
12. [Famous architectures](#12-architectures)
13. [The degradation problem and residual connections](#13-resnet)
14. [Exam-shaped summary](#14-summary)

---

## 0. Why not fully connected <a name="0-why"></a>

p3–4. A 64×64 grayscale image is 4096 features; a **1000×1000 RGB image is 3
million**. A fully-connected net *"conceives a picture as a flattened vector and
ignores spatial dependencies"* — `O(3 million)` input nodes, and **each hidden
unit has roughly 3 million weights to learn**.

p5: architectures are domain-specific — **computer vision → CNNs, text and speech
→ RNNs.**

p6–7: the ImageNet Challenge (1.2 million images, 1000 object categories). In
2012 **AlexNet drastically outperformed competitors and marked the start of the
"deep learning" era**, introducing three things now standard: **ReLU, dropout,
and GPU use.**

p9: CNNs are composed of **convolution layers, pooling layers, and
fully-connected layers.**

## 1. Convolution as cross-correlation <a name="1-conv"></a>

p11–15. A 6×6 image convolved with a 3×3 filter gives a **4×4** result. The
filter slides; each output is the elementwise product summed.

```
image (6×6)              filter (3×3)        result (4×4)
3  0  1  2  7  4          1  0 -1            -5  -4   0   8
1  5  8  9  3  1    *     1  0 -1     =     -10  -2   2   3
2  7  2  5  1  3          1  0 -1             0  -2  -4  -7
0  1  3  1  7  8                             -3  -2  -3 -16
4  2  1  6  2  8
2  4  5  2  3  9
```

First entry, worked (p11):
`3(1)+0(0)+1(−1) + 1(1)+5(0)+8(−1) + 2(1)+7(0)+2(−1) = 2 − 7 + 0 = −5`.

**The framing that matters (p15):** *"Convolution can be interpreted as
flattening the input patch and applying a dot-product `⟨w, x⟩`."* That single
sentence connects the whole lecture back to L08–L09 — a conv unit is an ordinary
linear unit applied to a patch.

## 2. Filters and edge detection <a name="2-filters"></a>

p16 is a **quiz slide**: what does `[[1,0,−1],[1,0,−1],[1,0,−1]]` do? Answer:
**detect vertical edges.**

p17 shows why. On an image whose left half is 10 and right half is 0:

```
10 10 10 | 0 0 0                     0  30  30  0
10 10 10 | 0 0 0    *  [1 0 -1]  =   0  30  30  0
   ...   |   ...       [1 0 -1]      0  30  30  0
                       [1 0 -1]      0  30  30  0
```

*"The result has a high response at the edge."* The zero column of the filter
never contributes; the response is (left − right).

p18: the **sign carries direction** — a black→white edge gives `+30`, white→black
gives `−30`. p19: the horizontal filter is the transpose,
`[[1,1,1],[0,0,0],[−1,−1,−1]]`, and on a checkerboard gives the characteristic
`−30, −10, 10, 30` pattern.

p20, the historical point worth quoting: *"In early days, scientists searched for
the optimal set of filters"* (Sobel-like kernels are shown). *"Nowadays, we
define the number and size of the filter and learn weights"* — the filter entries
become `w₁…w₉`, learned by backprop.

## 3. Padding <a name="3-padding"></a>

p21–23. Problem (p21): *each convolution reduces dimensionality* — 5×5 with a 3×3
filter gives 3×3, and stacking layers shrinks the image away.

| Mode | Definition | Output |
|---|---|---|
| **Valid** (no padding) | convolve only where the whole filter lies inside the input | `(n−f+1) × (n−f+1)` |
| **Zero padding** | add zeros around the boundary | can preserve size |
| **Same padding** | the special case where output = input size | `n × n` |

## 4. Stride and the output-size formula <a name="4-stride"></a>

p24–26: with **stride 2**, a 7×7 image and 3×3 filter give a **3×3** result — the
filter jumps two positions each step, horizontally and vertically.

p27, **the master formula — memorise this**:

```
Input n×n, filter f×f, padding p, stride s:

output = ⌊(n + 2p − f)/s + 1⌋  ×  ⌊(n + 2p − f)/s + 1⌋
```

Check it reproduces the special cases: `p=0, s=1` → `n−f+1` (valid); the 7×7/3×3
stride-2 case → `(7+0−3)/2 + 1 = 3`. ✓

## 5. Multi-channel convolution <a name="5-channels"></a>

p28–29. An RGB input is `1000×1000×3`. A filter must match the input's channel
depth: `3×3×3`. The output is `1000×1000×1` (with same padding) — **one channel,
not three.**

p29 shows the arithmetic: the filter's three channels each convolve their matching
input channel, and the results are **summed, plus a bias**:

```
120 + (−75) + 205 + 10 = 260
 ch1     ch2   ch3   bias   output
```

**The channel dimension collapses.** One filter always produces one output
channel, regardless of input depth — the most common misconception in this
lecture.

## 6. Multiple filters <a name="6-multifilter"></a>

p30. Use **two** `3×3×3` filters on the same `1000×1000×3` input → output
`1000×1000×2`. *"The output has 2 channels (one for each filter)."*

The rule: **#output channels = #filters.** Input depth determines each filter's
depth; filter count determines output depth.

## 7. Pooling <a name="7-pooling"></a>

p31. *"Pooling is an operation to reduce the dimensionality after convolution."*
Max-pooling takes the maximum in each patch:

```
1  3  2  1
2  9  1  1     max-pool, filter 2, stride 2      9  2
1  3  2  3   ───────────────────────────────►    6  3
5  6  1  2
```

Top-left patch `{1,3,2,9}` → 9; top-right `{2,1,1,1}` → 2; bottom-left
`{1,3,5,6}` → 6; bottom-right `{2,3,1,2}` → 3. Pooling has **no learnable
parameters**.

## 8. Parameter counting — the exam's favourite <a name="8-params"></a>

Two of the deck's five quiz slides are parameter counts. **Learn both patterns.**

**p34 (quiz) — fully connected.** 300×300×3 RGB image, FC layer with 100 neurons:

```
inputs = 300 × 300 × 3 = 270,000
weights = 270,000 × 100 = 27,000,000
+ biases = 100
total = 27,000,100                    ← answer 3
```

**p36 (quiz) — convolutional.** Same 300×300×3 input, 100 filters of 5×5×3:

```
per filter = 5 × 5 × 3 = 75 weights, + 1 bias = 76
× 100 filters = 7,600                 ← answer 4
```

**27 million versus 7,600** on identical input. That contrast is the lecture's
central quantitative claim.

p38 works a smaller case: 2 filters of 5×5×3 → `2 × (5×5×3 + 1) = 152`
parameters. And a footnote: *"only 52 weights for 2 filters if we use the same
weights for each channel"* — `2 × (5×5 + 1) = 52`.

p39 makes the comparison concrete on 32×32×3:

```
input  32×32×3 = 3072 units
output 32×32×2 = 2048 units
Fully connected first hidden layer: 3072 × 2048 + 2048 = 6.2 million weights
Convolutional (2 filters of 5×5×3):                            152 weights
```

**The general formula:** `#params = (f × f × channels_in + 1) × #filters`.

## 9. Sparse connectivity and weight sharing <a name="9-sharing"></a>

p33, p35, p37, p40. Two distinct mechanisms — the exam may ask you to separate
them:

- **Sparse connectivity (p35):** each hidden unit connects only to a **local
  neighbourhood**, not to every pixel. 200×200 input, 10×10 filter → ~100 weights
  per unit instead of 40,000 (p33).
- **Weight sharing (p40):** the *same* filter is reused at every position.
  Rationale, quotable: *"A vertical edge detector that's useful in one part of the
  image is probably useful in another part of the image."*

p37 (after Goodfellow 2016) contrasts the two connectivity patterns: convolutional
units share one `w` and `b` across positions; fully-connected units each have
their own `wᵢ`, `bᵢ`.

## 10. One convolutional layer end to end <a name="10-layer"></a>

p41–45. A 32×32×3 image with one 5×5×3 filter: each output pixel is a
**75-dimensional dot product plus bias** (`5·5·3 = 75`), then a non-linearity:

```
a = ReLU(w ∗ x + b)
```

giving a **28×28×1 activation map** (`32 − 5 + 1 = 28`, valid padding). p43 shows
the ReLU applied elementwise; p44 recalls that ReLU's gradient is **0 for z<0 and
1 for z>0**.

p45: **6 filters → six activation maps → 28×28×6.**

The layer is exactly an L08 unit with two additions: the input is a patch rather
than the whole image, and the weights are shared across patches.

## 11. The full CNN <a name="11-cnn"></a>

p47–51. Convolution layers stack, each consuming the previous output's depth:

```
32×32×3  ──CONV 6 filters 5×5×3, ReLU──►  28×28×6
         ──CONV 10 filters 5×5×6, ReLU──►  24×24×10  ──► …
```

Note the second layer's filters are `5×5×6` — **filter depth always equals input
depth.**

p49–50, the standard pipeline:

```
Input → Convolution → Pooling → Convolution → Pooling → Fully connected
        └────────── Feature Learning ──────────┘  └── Classification ──┘
```

with a **flatten** step before the fully-connected head (p49). p50: *"First layers
extract the low-level features, e.g. edges, colors. Next layers extract high-level
features, e.g. objects."*

p51 is a **quiz slide** — which do you typically see in CNNs? Answers: **1** (one
or many conv layers followed by a pooling layer) and **3** (fully connected layers
in the *last* few layers). Not 2, not 4.

## 12. Famous architectures <a name="12-architectures"></a>

p53–55. Four classics, with citations the deck gives in full:

| Network | Year | Citation | Key points |
|---|---|---|---|
| **LeNet-5** | 1998 | LeCun et al., *Proc. IEEE* 86(11) | 5×5 filters, **sigmoid**; 6 then 16 filters; **2×2 average pooling, stride 2**; 3 FC layers |
| **AlexNet** | 2012 | Krizhevsky, Sutskever & Hinton, *NeurIPS 25* | similar to LeNet but **8 layers** (5 conv + 2 FC hidden + 1 output); **ReLU not sigmoid**; GPUs |
| **GoogLeNet** | 2015 | Szegedy et al., *CVPR* | "Going deeper with convolutions" |
| **ResNet** | 2016 | He et al., *CVPR* | residual connections (§13) |

The LeNet→AlexNet delta is the examinable one: **sigmoid → ReLU, average pooling →
(deeper) conv stack, CPU → GPU, and dropout.**

## 13. The degradation problem and residual connections <a name="13-resnet"></a>

p57 is a **quiz slide**: *"Training a deeper network always results in a lower
training error."* → **False.**

p58, the **degradation problem**: networks need depth to improve, but *"with
networks getting too deep, the loss increases"*. Cause given: **vanishing
gradients** — *"it gets more and more difficult for the first layers to propagate
their information until the output layer"* (the direct continuation of L09 §15).
Two solutions named: **residual connections** and **batch normalization** (the
latter only named).

p59–61, the mechanism. Ordinary forward pass:

```
z[l+1] = W[l+1]a[l]   + b[l+1]        a[l+1] = g(z[l+1])
z[l+2] = W[l+2]a[l+1] + b[l+2]        a[l+2] = g(z[l+2])
```

Residual block — one term changes:

```
a[l+2] = g( z[l+2] + a[l] )
                     ↑ shortcut / skip connection
```

p61, **why it works**: if the network is too deep, the block can **learn the
identity** by setting `W[l+2], b[l+2] = 0`, giving `a[l+2] = g(a[l])`. Extra depth
therefore costs nothing — the network can always fall back to passing the signal
through, so adding layers cannot make it strictly worse.

## 14. Exam-shaped summary <a name="14-summary"></a>

Eight things to do cold:

1. Convolve a small image with a 3×3 filter by hand, and state the dot-product
   interpretation (p11–15).
2. Identify what a filter does from its entries — vertical vs horizontal edges,
   and the sign convention (p16–19).
3. Apply the output-size formula `⌊(n+2p−f)/s + 1⌋` and name valid / same padding
   (p23, p27).
4. Explain why one filter over a 3-channel input gives **one** output channel, and
   that #filters = #output channels (p28–30).
5. Max-pool a 4×4 to 2×2, and say pooling has no parameters (p31).
6. Count parameters both ways: FC `27,000,100` vs conv `7,600` on the same input
   (p34, p36), and the general formula.
7. Separate sparse connectivity from weight sharing, and quote the edge-detector
   rationale (p35, p37, p40).
8. State the degradation problem and write the residual update
   `a[l+2] = g(z[l+2] + a[l])`, explaining the identity argument (p57–61).

### Deliberately out of scope

- **Batch normalization** — named once (p58), never developed.
- **RNNs** — named as the text/speech paradigm (p5); the RNN unit is prior-year
  only and not current exam scope.
- Backprop *through* convolutions — not derived in this deck.

### Open questions for Aram

- **Five quiz slides** (p16, p34, p36, p51, p57) — the highest concentration in
  any AML deck. All five are in the exercise bank; treat them as near-certain
  exam items.
- p56 is a movie/animation slide with no extractable content. Worth a glance in
  the original PDF in case it carries a worked example.
