---
id: note-aml-l10-exercise-bank
type: note
title: "AML L10 — Exercise Bank (Convolutional Neural Networks)"
created: "2026-08-15"
role: exercise-bank
state: evolving
authorship: operator-drafted
concepts: [concept-neural-network, concept-backpropagation]
sources: [source-aml-ss26-lectures, source-cs231n-notes, source-cs4780-homeworks,
  source-eecs498, source-geron-handson]
contexts: [workspace-aml-exam-prep]
---

> **Build note (2026-08-15).** Drafted by the operator from `VL 10-cnn.pdf`.
> Companions: `note-aml-l10-cnn` (reference), `note-aml-l10-mock-exam`.
> `authorship: operator-drafted` — solutions operator-computed, **unverified by Aram**.
> Where a solution disagrees with the deck, the deck wins.

# AML Lecture 10 — Exercise Bank (Convolutional Neural Networks)

**Reading-scope rule:** convolution arithmetic, filters and edge detection,
padding, stride and output shapes, multi-channel and multi-filter convolution,
pooling, parameter counting, sparse connectivity and weight sharing, the CNN
pipeline, the four classic architectures, and residual connections.

> ⚠️ **Batch normalization is named once (p58) and never developed** — know the
> name, skip external BN derivations. **Backprop through convolutions is not in
> this deck.** RNNs are prior-year only.
>
> 🔎 **Section 3 drills the deck's five quiz slides** (p16, p34, p36, p51, p57).
> This deck has the highest quiz density in the AML course — do those first.

---

## 1. Local material

| File | What it is | Where |
|---|---|---|
| `note-aml-l10-cnn` | Full page-anchored reference | this vault |
| `note-aml-l10-mock-exam` | 100-pt mock, verified key | this vault |
| `note-aml-l09-backpropagation` | Vanishing gradients — the setup for §13 degradation | this vault |
| `note-aml-l08-feedforward-networks` | The unit a conv filter generalises | this vault |

## 2. Source sheets to solve (in the repo)

- **Übung 10** — `exercise-slides/` — tutorial deck for this lecture.
- **d2l.ai** — the deck links it twice for LeNet (p54) and ResNet (p61). Its CNN
  chapters carry runnable code for exactly these architectures.

## 3. Drills — Group A: the five quiz slides (do these first)

**A1.** *(p16)* What does `[[1,0,−1],[1,0,−1],[1,0,−1]]` do to a grayscale image?
Smoothen / horizontal edges / vertical edges / 45° edges?

<details><summary>Solution</summary>

**Vertical edge detection.** The middle column is zero, so the response is
(left neighbourhood − right neighbourhood) — large exactly where intensity changes
horizontally, i.e. at a vertical edge. The horizontal detector is its transpose.
</details>

**A2.** *(p34)* 300×300×3 RGB image, fully connected layer with 100 neurons. How
many weights (including bias)?

<details><summary>Solution</summary>

```
300 × 300 × 3 = 270,000 inputs
270,000 × 100 = 27,000,000 weights
+ 100 biases
= 27,000,100                        ← option 3
```
The trap is forgetting the ×3 channels or the biases.
</details>

**A3.** *(p36)* Same 300×300×3 input, CNN with 100 filters of kernel 5×5×3. How
many weights in the first conv layer (including bias)?

<details><summary>Solution</summary>

```
per filter: 5 × 5 × 3 = 75 weights + 1 bias = 76
× 100 filters = 7,600               ← option 4
```
**Note what does not appear: the input's spatial size.** 300×300 is irrelevant to
the parameter count — that is the whole point of weight sharing. Option 3 (7,500)
is the same answer with the biases dropped.
</details>

**A4.** *(p51)* Which do you typically see in CNNs?
1. conv layer(s) followed by a pooling layer 2. multiple pooling then a conv
3. FC layers in the last few layers 4. FC layers in the first few layers

<details><summary>Solution</summary>

**1 and 3.** The pipeline is Conv→Pool (repeated) then FC at the end (p49–50):
feature learning first, classification last. Putting FC first would flatten away
the spatial structure the convolutions exist to exploit.
</details>

**A5.** *(p57)* True or false: *training a deeper network always results in lower
training error.*

<details><summary>Solution</summary>

**False** — the **degradation problem** (p58). Beyond some depth the loss
*increases*, because vanishing gradients make it *"more and more difficult for the
first layers to propagate their information until the output layer."* Note this is
about **training** error, so it is not overfitting — that is what makes it
surprising and why ResNet was needed.
</details>

## 4. Drills — Group B: convolution arithmetic

**B1.** Compute the first two entries of the 4×4 result for the p11 example
(6×6 image, filter `[[1,0,−1],[1,0,−1],[1,0,−1]]`).

<details><summary>Solution</summary>

```
(1,1): 3(1)+0(0)+1(−1) + 1(1)+5(0)+8(−1) + 2(1)+7(0)+2(−1)
     = (3−1) + (1−8) + (2−2) = 2 − 7 + 0 = −5
(1,2): 0(1)+1(0)+2(−1) + 5(1)+8(0)+9(−1) + 7(1)+2(0)+5(−1)
     = (0−2) + (5−9) + (7−5) = −2 − 4 + 2 = −4
```
Full result: `[[−5,−4,0,8], [−10,−2,2,3], [0,−2,−4,−7], [−3,−2,−3,−16]]` (p15).
</details>

**B2.** State the dot-product interpretation of convolution.

<details><summary>Solution</summary>

p15: *"Convolution can be interpreted as flattening the input patch and applying a
dot-product `⟨w, x⟩`."* A conv unit is an ordinary linear unit (L08) applied to a
patch, with the weights reused across patches.
</details>

**B3.** On the p17 image (left half 10, right half 0), apply the vertical filter.
What is the response, and what changes for a white→black edge?

<details><summary>Solution</summary>

Response `0, 30, 30, 0` per row — high at the edge, zero in the flat regions.
p18: a black→white edge gives `+30`, white→black gives `−30`. **The sign encodes
the direction of the transition.**
</details>

**B4.** Give the output size for each:
(a) n=5, f=3, p=0, s=1 (b) n=7, f=3, p=0, s=2 (c) n=32, f=5, p=0, s=1
(d) n=6, f=3, p=1, s=1

<details><summary>Solution</summary>

Formula (p27): `⌊(n + 2p − f)/s + 1⌋`.
```
(a) (5+0−3)/1 + 1 = 3      → 3×3
(b) (7+0−3)/2 + 1 = 3      → 3×3
(c) (32+0−5)/1 + 1 = 28    → 28×28
(d) (6+2−3)/1 + 1 = 6      → 6×6   (same padding)
```
</details>

**B5.** Define valid, zero and same padding, and say why padding exists at all.

<details><summary>Solution</summary>

**Valid:** convolve only where the whole filter lies inside the input → output
`(n−f+1)×(n−f+1)`. **Zero:** add zeros around the boundary. **Same:** the zero
padding that makes output = input size, `n×n`. (p22–23)

Why: *"Each convolution with a filter reduces the dimensionality of the output"*
(p21) — without padding, stacking layers shrinks the representation away.
</details>

**B6.** Max-pool `[[1,3,2,1],[2,9,1,1],[1,3,2,3],[5,6,1,2]]` with filter 2,
stride 2. How many parameters does this layer have?

<details><summary>Solution</summary>

```
[9 2]
[6 3]
```
patches `{1,3,2,9}→9`, `{2,1,1,1}→2`, `{1,3,5,6}→6`, `{2,3,1,2}→3`. (p31)

**Zero parameters** — pooling is a fixed operation with nothing to learn.
</details>

## 5. Drills — Group C: channels and filters

**C1.** A 1000×1000×3 RGB image convolved with **one** 3×3×3 filter. What is the
output shape (same padding), and why is the depth what it is?

<details><summary>Solution</summary>

`1000×1000×1`. The filter's three channels each convolve the matching input
channel and the results are **summed, plus one bias** (p29: 120 + (−75) + 205 + 10
= 260). **The channel dimension collapses** — one filter always yields one output
channel, whatever the input depth. This is the most common misconception here.
</details>

**C2.** Now use two such filters. Output shape? State the general rule.

<details><summary>Solution</summary>

`1000×1000×2` — *"the output has 2 channels (one for each filter)"* (p30).

Rules: **filter depth = input depth**; **#output channels = #filters**.
</details>

**C3.** A CNN layer takes 28×28×6 and applies 10 filters of 5×5. Give the full
filter shape and the output shape (valid padding).

<details><summary>Solution</summary>

Filters must match input depth: **5×5×6**. Output: `(28−5+1) = 24` →
**24×24×10** (p48).
</details>

**C4.** Count the parameters for C3.

<details><summary>Solution</summary>

`(5 × 5 × 6 + 1) × 10 = (150 + 1) × 10 = 1,510`.
General: `#params = (f·f·channels_in + 1) × #filters`.
</details>

**C5.** *(p38)* Two filters of 5×5×3. How many parameters? And how many if the
same weights were shared across channels?

<details><summary>Solution</summary>

`2 × (5×5×3 + 1) = 2 × 76 = 152`. Sharing across channels: `2 × (5×5 + 1) = 52`.
</details>

**C6.** *(p39)* Input 32×32×3, output 32×32×2. Compare a fully-connected first
hidden layer against 2 conv filters of 5×5×3.

<details><summary>Solution</summary>

```
FC:   3072 × 2048 + 2048 = 6.2 million weights
CONV: 2 × (5×5×3 + 1)    = 152 weights
```
Four orders of magnitude, same input and output dimensions. This is the lecture's
central quantitative claim.
</details>

## 6. Drills — Group D: architecture and design

**D1.** Distinguish sparse connectivity from weight sharing.

<details><summary>Solution</summary>

**Sparse connectivity (p35):** each hidden unit connects only to a *local
neighbourhood* — 200×200 input with a 10×10 filter → ~100 weights per unit
instead of 40,000 (p33). **Weight sharing (p40):** the *same* filter is reused at
every spatial position, so the parameter count is independent of image size.

Two separate savings; an exam may ask for both by name. Rationale for sharing
(p40): *"A vertical edge detector that's useful in one part of the image is
probably useful in another part."*
</details>

**D2.** Write the computation of one conv layer's output pixel for a 32×32×3 image
with a 5×5×3 filter. How many dimensions is the dot product?

<details><summary>Solution</summary>

`a = ReLU(w ∗ x + b)`, where the patch dot product is `5·5·3 = 75`-dimensional
plus bias (p41–43). Output map: `32−5+1 = 28` → 28×28×1; with 6 filters, 28×28×6
(p45).
</details>

**D3.** Draw the standard CNN pipeline and label the two functional halves.

<details><summary>Solution</summary>

```
Input → Convolution → Pooling → Convolution → Pooling → [flatten] → Fully connected
        └─────────── Feature Learning ───────────┘        └── Classification ──┘
```
(p49–50). *"First layers extract low-level features, e.g. edges, colors. Next
layers extract high-level features, e.g. objects."*
</details>

**D4.** LeNet-5 vs AlexNet: give the year, citation and the concrete differences.

<details><summary>Solution</summary>

**LeNet-5** (LeCun et al., *Proc. IEEE* 86(11), 1998): 5×5 filters with **sigmoid**;
6 filters then 16; **2×2 average pooling, stride 2**; 3 FC layers.

**AlexNet** (Krizhevsky, Sutskever & Hinton, *NeurIPS* 25, 2012): similar shape but
**8 layers** (5 conv + 2 FC hidden + 1 output), **ReLU instead of sigmoid**, GPU
training. It *"drastically outperformed the competitors"* on ImageNet (1.2M images,
1000 categories) and **marked the start of the deep-learning era**, introducing
ReLU, dropout and GPU use (p6–7, p53–55).
</details>

**D5.** State the degradation problem and its named cause and solutions.

<details><summary>Solution</summary>

Networks need depth, but too deep and **the loss increases** (p58) — note:
*training* loss, so not overfitting. Cause: **vanishing gradients**, since the
first layers cannot propagate information to the output. Solutions named:
**residual connections** and **batch normalization** (the latter only named).
</details>

**D6.** Write the residual forward pass and explain why it helps.

<details><summary>Solution</summary>

Ordinary (p59): `z[l+2] = W[l+2]a[l+1] + b[l+2]`, `a[l+2] = g(z[l+2])`.

Residual (p60): **`a[l+2] = g( z[l+2] + a[l] )`** — a shortcut / skip connection.

Why (p61): if the network is too deep, the block can **learn the identity** by
setting `W[l+2], b[l+2] = 0`, giving `a[l+2] = g(a[l])`. Extra depth therefore
cannot make the network strictly worse — it can always pass the signal through.
</details>

## 7. External practice — solution-checked, matched to L10

- **CS231n notes** (`source-cs231n-notes`) — the convolutional-networks module is
  the canonical treatment of exactly p21–45, with an interactive conv demo. The
  single best external match for this lecture.
- **EECS 498** (`source-eecs498`) — CNN architecture lectures cover the LeNet →
  AlexNet → GoogLeNet → ResNet lineage of p53–61.
- **CS4780 homeworks** (`source-cs4780-homeworks`) — local bank; take the shape and
  parameter-counting items.
- **Géron, *Hands-On ML*** (`source-geron-handson`) — the CNN chapter builds these
  architectures in Keras; good for making the shape arithmetic concrete.
- **d2l.ai** — linked by the deck itself for LeNet (p54) and ResNet (p61).

## 8. Suggested sequence

1. **A1–A5** — the five quiz slides. Highest expected value in the whole bank.
2. **B1–B2** — convolve by hand once; learn the dot-product framing.
3. **B4** — the output-size formula on four cases until it is reflexive.
4. **C1–C2** — the channel-collapse rule, which is the most-missed idea here.
5. **C3–C6** — shapes and parameter counting, including the 6.2M vs 152 contrast.
6. **D1, D3** — sparse vs shared, and the pipeline.
7. **D4–D6** — architectures, degradation, residual connections.
8. Then `note-aml-l10-mock-exam`, 75 minutes closed book.

> **Evidence note.** Record what you actually solved on `unit-aml-l10` — an
> exercise bank with no recorded attempts is a plan, not evidence (CLAUDE.md §7).
