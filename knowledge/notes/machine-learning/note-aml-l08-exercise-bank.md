---
id: note-aml-l08-exercise-bank
type: note
title: "AML L08 — Exercise Bank (Feedforward Networks, Output Layers, Metrics)"
created: "2026-08-15"
role: exercise-bank
state: evolving
authorship: operator-drafted
concepts: [concept-neural-network, concept-xor-problem, concept-softmax,
  concept-classification-metrics]
sources: [source-aml-ss26-lectures, source-cs4780-homeworks, source-mit-6036,
  source-cs231n-notes, source-geron-handson]
contexts: [workspace-aml-exam-prep]
---

> **Build note (2026-08-15).** Drafted by the operator from the current 2026 deck
> `VL 08-feedforward-neural-network.pdf`. Companions:
> `note-aml-l08-feedforward-networks` (reference), `note-aml-l08-mock-exam`.
> `authorship: operator-drafted` (schema has no "operator-drafted" value — see the workspace note) — solutions below are operator-computed and
> **unverified by Aram**. Where a solution disagrees with the deck, the deck wins.

# AML Lecture 08 — Exercise Bank (Feedforward Networks, Output Layers, Metrics)

All L08 practice in one place, with solutions to self-check against.

**Reading-scope rule:** practice matched to what AML L08 actually covers —
**gate composition and XOR, forward propagation, activation choice and
expressiveness, output layers (multi-label vs softmax), and classification
metrics including micro/macro/weighted averaging.**

> ⚠️ **No backpropagation in this lecture.** p53 defers it to L09. Most external
> "neural network" problem sets are dominated by gradient derivations — take only
> the forward-pass and metrics parts, and leave the backward pass for the L09
> bank. This is the exact analogue of the "no SVM in L07" trap.

---

## 1. Local material

| File | What it is | Where |
|---|---|---|
| `note-aml-l08-feedforward-networks` | Full page-anchored reference | this vault |
| `note-aml-l08-mock-exam` | 100-pt mock, verified key | this vault |
| `note-aml-bonusblatt04-solutions` | Worked key to **Bonusblatt 4** — **Aufg. 3–4 are L08 scope** | this vault |
| `note-aml-sad-master-wiring` | Cross-module wiring; L08 section | this vault |

## 2. Source sheets to solve (in the repo)

- **Bonusblatt 4** — `bonus-exercises/zusatz-blatt04.pdf`.
  **Aufgabe 3 (single-neuron gates)** and **Aufgabe 4 (MLP design)** are squarely
  L08. Aufg. 1–2 are L07. Already solved in `note-aml-bonusblatt04-solutions` —
  attempt 3–4 cold first, the key is the check.
- **Übung 08** — `exercise-slides/` — the tutorial deck for this lecture. Work
  the forward-pass example before the Besprechung resolution.
- **Primer_Linear_Algebra.pdf** — if the `Wx + b` shape check on p21 does not
  feel automatic, this is the 36-page diagnostic. Do not read it linearly; find
  the matrix–vector product section.

## 3. Drills — Group A: gates and XOR (p6–12)

**A1.** Give the weight vector (bias first) for OR, AND and NAND, and trace all
four input rows for each, showing `z = w·x` and `step(z)`.

<details><summary>Solution</summary>

`w_OR = (−0.5, 1, 1)`, `w_AND = (−1.5, 1, 1)`, `w_NAND = (1.5, −1, −1)`.

| x₁ | x₂ | z_OR | OR | z_AND | AND | z_NAND | NAND |
|---|---|---|---|---|---|---|---|
| 0 | 0 | −0.5 | 0 | −1.5 | 0 | +1.5 | 1 |
| 0 | 1 | +0.5 | 1 | −0.5 | 0 | +0.5 | 1 |
| 1 | 0 | +0.5 | 1 | −0.5 | 0 | +0.5 | 1 |
| 1 | 1 | +1.5 | 1 | +0.5 | 1 | −0.5 | 0 |

OR and AND differ **only in the bias** — it sets how many inputs must fire.
NAND is AND with all signs flipped.
</details>

**A2.** Verify `XOR = AND(OR, NAND)` on all four rows.

<details><summary>Solution</summary>

| x₁ | x₂ | a₁=OR | a₂=NAND | AND(a₁,a₂) | XOR |
|---|---|---|---|---|---|
| 0 | 0 | 0 | 1 | 0 | 0 |
| 0 | 1 | 1 | 1 | 1 | 1 |
| 1 | 0 | 1 | 1 | 1 | 1 |
| 1 | 1 | 1 | 0 | 0 | 0 |

The only rows where AND fires are those where OR fires *and* NAND has not vetoed
— i.e. "at least one, but not both". (p10)
</details>

**A3.** Why is `a⁽¹⁾` called "a non-linear feature of x"? Connect it to L07.

<details><summary>Solution</summary>

Each hidden unit applies a *non-linear* step/sigmoid to a linear function of `x`,
so `a⁽¹⁾` is a new representation in which XOR **is** linearly separable — the
output unit is then just a linear classifier on `a⁽¹⁾`.

L07 bought exactly this with the kernel trick, by *choosing* a feature map φ. L08
buys it by *learning* one. Same problem, same shape of solution, different source
of the features. (p11)
</details>

**A4.** *(Design)* Build a 2-layer MLP computing `x₁ AND (NOT x₂)`. Give weights
for a single hidden unit or argue none is needed.

<details><summary>Solution</summary>

No hidden layer is needed — the function is linearly separable. One unit with
`w = (−0.5, 1, −1)`: z = −0.5 + x₁ − x₂, which is > 0 only for (1,0). ✓

The trap: reaching for depth reflexively. Depth is for *non*-separable targets
(p40). Being able to say "this needs no hidden layer" is the point.
</details>

## 4. Drills — Group B: forward propagation (p25–32)

**B1.** *(The core drill — do this until it is automatic.)* Network: 2 inputs →
2 sigmoid hidden units → 1 sigmoid output, with
`w₁=(1,2), b₁=−2`, `w₂=(1,2), b₂=+2`, `w_out=(−2,4.5), b_out=−1`.
Compute `ŷ` for `x = (1,0)`, element-wise.

<details><summary>Solution</summary>

```
z₁ = 1·1 + 2·0 − 2 = −1      a₁ = σ(−1)    = 0.267
z₂ = 1·1 + 2·0 + 2 = +3      a₂ = σ(+3)    = 0.952
z_out = −2(0.267) + 4.5(0.952) − 1
      = −0.534 + 4.284 − 1   = 2.749
ŷ = σ(2.749) = 0.94
```
(p30–31)
</details>

**B2.** Redo B1 in **vectorised** form: write `W⁽¹⁾`, `b⁽¹⁾`, `W⁽ᵒᵘᵗ⁾`, `b⁽ᵒᵘᵗ⁾`
and compute `a = σ(W⁽¹⁾x + b⁽¹⁾)` then `ŷ`.

<details><summary>Solution</summary>

```
W⁽¹⁾ = [[1,2],[1,2]]   b⁽¹⁾ = (−2, +2)
W⁽ᵒᵘᵗ⁾ = (−2, 4.5)      b⁽ᵒᵘᵗ⁾ = −1

W⁽¹⁾x + b⁽¹⁾ = (1,1) + (−2,2) = (−1, 3)
a = σ(−1, 3) = (0.267, 0.952)
ŷ = σ((−2,4.5)·(0.267,0.952) − 1) = σ(2.749) = 0.94
```
Same answer, fewer lines. (p32)
</details>

**B3.** Same network, `x = (0,1)`. Compute `ŷ`.

<details><summary>Solution</summary>

```
z₁ = 0 + 2 − 2 = 0      a₁ = σ(0) = 0.5
z₂ = 0 + 2 + 2 = 4      a₂ = σ(4) ≈ 0.982
z_out = −2(0.5) + 4.5(0.982) − 1 = −1 + 4.419 − 1 = 2.419
ŷ = σ(2.419) ≈ 0.918
```
Worth doing precisely because the deck does not — if you can only reproduce the
memorised numbers, you have memorised rather than understood.
</details>

**B4.** Write the forward-propagation pseudocode from memory, with the
initialisation and the output line.

<details><summary>Solution</summary>

```
a⁽⁰⁾ = x
for i = 1 to L
    a⁽ⁱ⁾ = g( W⁽ⁱ⁾ a⁽ⁱ⁻¹⁾ + b⁽ⁱ⁾ )
ŷ = g_out( W⁽ᵒᵘᵗ⁾ a⁽ᴸ⁾ + b⁽ᵒᵘᵗ⁾ )
```
(p25). The two things people drop: `a⁽⁰⁾ = x`, and that the output line uses
`g_out`, not `g`.
</details>

**B5.** *(Shapes)* Input `x ∈ ℝ⁵`, hidden layer 1 has 4 units, hidden layer 2 has
3, single output. Give every weight-matrix and bias shape, and the total
parameter count.

<details><summary>Solution</summary>

```
W⁽¹⁾ ∈ ℝ⁴ˣ⁵   b⁽¹⁾ ∈ ℝ⁴    → 20 + 4 = 24
W⁽²⁾ ∈ ℝ³ˣ⁴   b⁽²⁾ ∈ ℝ³    → 12 + 3 = 15
W⁽ᵒᵘᵗ⁾ ∈ ℝ¹ˣ³ b⁽ᵒᵘᵗ⁾ ∈ ℝ¹  →  3 + 1 =  4
total = 43 parameters
```
Rule: `W⁽ˡ⁾` is `(units in l) × (units in l−1)`. Biases are one per unit in `l`.
</details>

## 5. Drills — Group C: expressiveness (p40)

**C1.** Prove that a 2-layer MLP with identity activations collapses to a single
linear model. State `W′` and `b′` explicitly.

<details><summary>Solution</summary>

```
ŷ = W⁽²⁾(W⁽¹⁾x + b⁽¹⁾) + b⁽²⁾
  = W⁽²⁾W⁽¹⁾x + W⁽²⁾b⁽¹⁾ + b⁽²⁾
  = W′x + b′       with  W′ = W⁽²⁾W⁽¹⁾ ,  b′ = W⁽²⁾b⁽¹⁾ + b⁽²⁾
```
Therefore linear activations make depth worthless: any such MLP equals one
neuron. Non-linear `g` is what buys non-linear decision functions. (p40)
</details>

**C2.** True/false: *"A deep network with linear activations can separate XOR if
it has enough layers."* Justify.

<details><summary>Solution</summary>

**False.** By C1 the whole stack collapses to `W′x + b′`, one linear boundary,
and XOR needs two. Depth without non-linearity adds nothing — no number of
layers helps.
</details>

**C3.** Must hidden and output activations be the same? What does `g_out`
determine?

<details><summary>Solution</summary>

No (p38). `g` in the hidden layers only has to be non-linear; `g_out` **defines
the type of ML problem** — identity → regression, sigmoid → binary
classification, softmax → multi-class. (p37–38)
</details>

## 6. Drills — Group D: output layers (p42–50)

**D1.** State the difference between multi-label and multi-class, give an example
of each, and say which output activation and which "sums to 1" answer applies.

<details><summary>Solution</summary>

| | Multi-label | Multi-class |
|---|---|---|
| Question | which of these are present? | which one is it? |
| Example | car *and* pedestrian in a scene (p42) | pedestrian / car / motorcycle / truck (p47) |
| Output | `k` independent sigmoids | softmax over `k` |
| Sum to 1 | **no** (p45) | **yes** (p49) |
| Target | vector of 0/1, e.g. (1,0,1) | one-hot |
</details>

**D2.** Write the softmax formula, show the outputs sum to 1, and give the
prediction rule.

<details><summary>Solution</summary>

```
p(y = i | x) = e^{zᵢ} / Σⱼ₌₁ᵏ e^{zⱼ}
Σᵢ p(y=i|x) = (Σᵢ e^{zᵢ}) / (Σⱼ e^{zⱼ}) = 1     ✓
ŷ = argmax_{yᵢ ∈ Y} p(y = yᵢ | x)
```
(p49–50)
</details>

**D3.** *(Numerical)* Output scores `z = (2.0, 1.0, 0.1)`. Compute the softmax.
Use `e² ≈ 7.389`, `e¹ ≈ 2.718`, `e⁰·¹ ≈ 1.105`.

<details><summary>Solution</summary>

```
Σ = 7.389 + 2.718 + 1.105 = 11.212
p₁ = 7.389/11.212 ≈ 0.659
p₂ = 2.718/11.212 ≈ 0.242
p₃ = 1.105/11.212 ≈ 0.099
sum ≈ 1.000 ✓     ŷ = class 1
```
</details>

**D4.** Why is One-vs-Rest with `k` separate networks worse than one network with
`k` outputs?

<details><summary>Solution</summary>

The deck states the verdict without a full argument: *"Better: train one neural
network with three outputs"* (p43). The supporting reasons — shared hidden
representation, one training run instead of `k`, no calibration mismatch between
independently-trained nets — are standard but **not on the slide**, so give the
slide's claim first and the reasoning as support.
</details>

## 7. Drills — Group E: metrics (p59–79)

**E1.** With 5 positives and 995 negatives, construct the naïve baseline and give
its error and accuracy. Why does this make accuracy a bad metric?

<details><summary>Solution</summary>

`def predictNaive(): return 0` → 0.5% error, **99.5% accuracy** (p60), beating a
trained model at 99%. Accuracy rewards ignoring the rare class, which is the only
class we care about. (p59–60)
</details>

**E2.** Fill the degenerate-predictor table cold.

<details><summary>Solution</summary>

| Strategy | TP | FP | FN | TN | Precision | Recall |
|---|---|---|---|---|---|---|
| always 1 | 5 | 995 | 0 | 0 | 5/1000 = 0.005 | 5/5 = 1.0 |
| always 0 | 0 | 0 | 5 | 995 | 0/0 ≡ **0** | 0/5 = 0 |

The `0/0 ≡ 0` convention is stated on p63.
</details>

**E3.** Compute F₁ for the three algorithms on p67 and explain what the harmonic
mean is protecting against.

<details><summary>Solution</summary>

```
Alg 1: 2(0.5·0.4)/(0.9)    = 0.444
Alg 2: 2(0.7·0.1)/(0.8)    = 0.175
Alg 3: 2(0.005·1.0)/(1.005) = 0.00995 ≈ 0.001 as printed
```
Algorithm 3 is "always predict 1": perfect recall, useless precision. The
**arithmetic** mean would give it 0.5 and rank it top. The harmonic mean is
dominated by the smaller term, so it refuses to reward one metric bought entirely
at the other's expense. (p67–69)
</details>

**E4.** *(The high-yield one.)* From this per-class table, compute accuracy
(micro), macro-precision and weighted-precision.

| Label | tp | fp | fn | precision | recall | support |
|---|---|---|---|---|---|---|
| versicolor | 2 | 1 | 1 | 0.67 | 0.67 | 3 |
| virginica | 1 | 3 | 0 | 0.25 | 1.00 | 1 |
| setosa | 3 | 0 | 3 | 1.00 | 0.50 | 6 |

<details><summary>Solution</summary>

```
Accuracy (micro) = Σtp / Σsamples = 6/10 = 0.60
Macro_P    = (1/3)(0.67 + 0.25 + 1.00) = 0.64
Weighted_P = (3/10)(0.67) + (1/10)(0.25) + (6/10)(1.00)
           = 0.201 + 0.025 + 0.600 = 0.826 ≈ 0.82
```
(p75–78). Also on the summary row: macro-recall 0.72, weighted-recall 0.60.
</details>

**E5.** Weighted precision (0.82) is much higher than macro (0.64). Explain, and
say what choosing between them commits you to.

<details><summary>Solution</summary>

Setosa has perfect precision (1.00) *and* the largest support (6/10), so weighting
by frequency lets it dominate. Virginica scores worst (0.25) but has support 1, so
weighting almost erases it — while macro gives it a full third of the average.

Choosing macro says **rare classes matter as much as common ones**; choosing
weighted says **performance should reflect the population you will actually see**.
It is a claim about the problem, not a neutral summary statistic. In the cancer
setting of p59, macro is the honest choice.
</details>

**E6.** Derive the per-class table above from the p71 confusion matrix, for
versicolor.

<details><summary>Solution</summary>

p71 matrix (rows = predicted, columns = actual):

| | Act. versicolor | Act. virginica | Act. setosa |
|---|---|---|---|
| Pred. versicolor | 2 | 0 | 1 |
| Pred. virginica | 1 | 1 | 2 |
| Pred. setosa | 0 | 0 | 3 |

Versicolor as 'True': TP = 2 (diagonal). FP = rest of its **row** = 0 + 1 = 1.
FN = rest of its **column** = 1 + 0 = 1. → P = 2/3 = 0.67, R = 2/3 = 0.67. ✓

The row/column rule is the thing to remember: **FP along your row, FN down your
column.** (p72–74)
</details>

## 8. External practice — solution-checked, matched to L08

Take only forward-pass, architecture and metrics items; skip gradient
derivations until L09.

- **CS4780 homeworks** (`source-cs4780-homeworks`, complete local bank) — MLP
  architecture and expressiveness questions.
- **MIT 6.036** (`source-mit-6036`) — clean feedforward/shape problems with
  solutions; its neural-network chapter separates forward and backward cleanly,
  so the forward half is directly usable.
- **CS231n notes** (`source-cs231n-notes`) — the "Neural Networks Part 1: setting
  up the architecture" page is almost exactly p15–24, with better diagrams.
- **Géron, *Hands-On ML*** (`source-geron-handson`) — the Keras `Sequential`
  chapter matches p56 closely; useful if the toolkit slide feels thin.

## 9. Suggested sequence

1. **A1–A3** — gates and the XOR composition. Fast, and it is the lecture's spine.
2. **B1 then B2** — the worked forward pass, element-wise then vectorised. Repeat
   until automatic; then **B3** with fresh inputs to prove it is not memorised.
3. **B5** — shapes and parameter counting. Cheap marks, commonly dropped.
4. **C1** — write the collapse proof out longhand once.
5. **D1–D3** — the multi-label/multi-class split and softmax arithmetic.
6. **E2, E4, E6** — the three metric computations most likely to be asked.
7. **Bonusblatt 4 Aufg. 3–4** cold, then check against
   `note-aml-bonusblatt04-solutions`.
8. Only then: `note-aml-l08-mock-exam`, 75 minutes closed book.

> **Evidence note.** When you work these, record what you actually solved on the
> unit — an exercise bank with no recorded attempts is a plan, not evidence
> (CLAUDE.md §7).
