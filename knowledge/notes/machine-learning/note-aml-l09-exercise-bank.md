---
id: note-aml-l09-exercise-bank
type: note
title: "AML L09 — Exercise Bank (Backpropagation, Training, Vanishing Gradients)"
created: "2026-08-15"
role: exercise-bank
state: evolving
authorship: operator-drafted
concepts: [concept-backpropagation, concept-neural-network, concept-gradient-descent]
sources: [source-aml-ss26-lectures, source-cs4780-homeworks, source-mit-6036,
  source-cs231n-notes, source-karpathy-micrograd, source-pytorch-tutorials]
contexts: [workspace-aml-exam-prep]
---

> **Build note (2026-08-15).** Drafted by the operator from
> `VL 09-neural-networks.pdf`. Companions: `note-aml-l09-backpropagation`
> (reference), `note-aml-l09-mock-exam`. `authorship: operator-drafted` — solutions are
> operator-computed and **unverified by Aram**. Where a solution disagrees with
> the deck, the deck wins.

# AML Lecture 09 — Exercise Bank (Backpropagation, Training, Vanishing Gradients)

All L09 practice in one place, with solutions to self-check against.

**Reading-scope rule:** computation graphs, the chain rule and local derivatives,
the full backward pass, the four backprop rules, SGD, autograd, hyper-parameters,
regularization (Frobenius/L2/L1), dropout, early stopping, double descent,
vanishing/exploding gradients, and expressiveness by depth.

> ⚠️ **No batch normalization** — it is not in this deck. External NN problem sets
> lean on it heavily; skip those items. Softmax and metrics are **L08**, not here.
>
> 🔎 Use **L09's** rounding (`a⁽¹⁾ = 0.269, 0.953`) for all gradient arithmetic;
> L08 prints 0.267/0.952 and the downstream numbers shift if you mix them.

---

## 1. Local material

| File | What it is | Where |
|---|---|---|
| `note-aml-l09-backpropagation` | Full page-anchored reference | this vault |
| `note-aml-l09-mock-exam` | 100-pt mock, verified key | this vault |
| `note-aml-l08-feedforward-networks` | The forward pass this lecture extends | this vault |
| `note-aml-sad-master-wiring` | Cross-module wiring; L09 section | this vault |

## 2. Source sheets to solve (in the repo)

- **Übung 09** — `exercise-slides/` — tutorial deck for this lecture. Do the
  backward-pass example before the Besprechung.
- **The deck's own three quiz slides** — p12 (forward-prop indices), p48
  (hyper-parameters), p53 (logistic loss). Treat these as exam questions, not
  filler; a lecturer who quizzes in-deck tends to reuse the items.
- **PyTorch tutorials** (`source-pytorch-tutorials`) — the autograd basics page
  is p43–45 in expanded form. Run the deck's own snippet and check `.grad`
  against the hand-computed numbers; that is the single best verification you
  can do for this lecture.

## 3. Drills — Group A: computation graphs and the forward pass

**A1.** Name the three kinds of nodes in a computation graph, and draw the graph
for a one-hidden-layer MLP with squared loss.

<details><summary>Solution</summary>

**Input nodes, parameter nodes, compute nodes** (p7).

```
x, W⁽¹⁾, b⁽¹⁾ → z⁽¹⁾ → a⁽¹⁾ → z⁽²⁾ → a⁽²⁾=ŷ → L
                          ↑ W⁽²⁾, b⁽²⁾           ↑ y
```
`x` and `y` are inputs; `W`s and `b`s are parameters; `z`, `a`, `L` are compute.
</details>

**A2.** Why are the forward and backward passes efficient?

<details><summary>Solution</summary>

*"Forward pass and the backward pass are efficient due to storing and reusing
intermediate results"* (p6). Decomposing into atomic assignments lets every
intermediate `z⁽ˡ⁾`, `a⁽ˡ⁾` be computed once and reused by the backward pass —
that decomposition *"is key of the backpropagation algorithm"*.
</details>

**A3.** *(Quiz slide p12.)* Which is correct for layer `l`?
1. `z[l] = W[l]a[l] + b[l]`  2. `z[l] = W[l−1]a[l] + b[l−1]`  3. `z[l] = W[l]a[l−1] + b[l]`

<details><summary>Solution</summary>

**Option 3.** Layer `l` consumes the *previous* layer's activation `a[l−1]` and
uses *its own* parameters `W[l], b[l]`. Option 1 feeds `a[l]` into its own
definition (circular); option 2 mismatches the parameter index.
</details>

**A4.** Run the forward pass on the running example to the loss.

<details><summary>Solution</summary>

```
z⁽¹⁾ = (1,1) + (−2,2)              = (−1, 3)
a⁽¹⁾ = σ(−1, 3)                    = (0.269, 0.953)
z⁽²⁾ = (−2,4.5)·(0.269,0.953) − 1  = 2.749
ŷ    = σ(2.749)                    = 0.940
L2   = ½(0.940 − 0)²               = 0.442
```
(p11, p14). Why the ½ in the loss: it cancels in the derivative (p13).
</details>

## 4. Drills — Group B: local derivatives

**B1.** State the local derivative at each node type.

<details><summary>Solution</summary>

```
∂L2/∂ŷ  = ŷ − y                    (p22)
∂a/∂z   = σ′(z) = σ(z)(1 − σ(z))   (p23)
∂z/∂a   = W                        (p24)
∂z/∂b   = 1                        (p24)
∂z/∂W   = a                        (p25–26)
```
</details>

**B2.** Derive `σ′(z) = σ(z)(1−σ(z))` from `σ(z) = 1/(1+e⁻ᶻ)`.

<details><summary>Solution</summary>

```
σ(z) = (1+e⁻ᶻ)⁻¹
σ′(z) = −(1+e⁻ᶻ)⁻² · (−e⁻ᶻ) = e⁻ᶻ/(1+e⁻ᶻ)²
      = [1/(1+e⁻ᶻ)] · [e⁻ᶻ/(1+e⁻ᶻ)]
      = σ(z) · [(1+e⁻ᶻ−1)/(1+e⁻ᶻ)]
      = σ(z)(1 − σ(z))   ∎
```
Worth doing once by hand — it is the only non-trivial derivative in the lecture.
</details>

**B3.** What caveat does the deck attach to `∂z/∂W = a`?

<details><summary>Solution</summary>

p27 footnote: it *"is only correct in the context of the chain rule (else ∂z/∂W
is a second-order Tensor)."* Differentiating a vector by a matrix genuinely gives
a higher-order object; the simplification holds because it is immediately
contracted against the incoming gradient.
</details>

## 5. Drills — Group C: the backward pass (the core drill)

**C1.** *(Do this until automatic.)* Running example, `y = 0`. Compute, in order:
`∂L2/∂a⁽²⁾`, `∂L2/∂z⁽²⁾`, `∂L2/∂b⁽²⁾`, `∂L2/∂a⁽¹⁾`, `∂L2/∂W⁽²⁾`.

<details><summary>Solution</summary>

```
∂L2/∂a⁽²⁾ = ŷ − y = 0.94 − 0                      = 0.940
∂L2/∂z⁽²⁾ = 0.94 · σ(2.749)(1−σ(2.749))
          = 0.94 · (0.940)(0.060) = 0.94 · 0.0565 = 0.0531
∂L2/∂b⁽²⁾ = 0.0531 · 1                            = 0.0531
∂L2/∂a⁽¹⁾ = (−2, 4.5)ᵀ · 0.0531                   = (−0.106, 0.239)
∂L2/∂W⁽²⁾ = 0.0531 · (0.269, 0.953)               = (0.0143, 0.0506)
```
(p30–34)
</details>

**C2.** Continue to layer 1: give `dz⁽¹⁾`, `db⁽¹⁾`, `dW⁽¹⁾`, `dx`. Why does
`dW⁽¹⁾` have a zero column?

<details><summary>Solution</summary>

```
dz⁽¹⁾ = (−0.0209, 0.0108)
db⁽¹⁾ = (−0.0209, 0.0108)
dW⁽¹⁾ = [[−0.0209, 0], [0.0108, 0]]
dx    = (−0.0101, −0.0202)
```
(p35). `dW⁽¹⁾ = dz⁽¹⁾ · a⁽⁰⁾ᵀ = dz⁽¹⁾ · xᵀ` and `x = (1,0)`, so the column
multiplying `x₂ = 0` is zero — **a dead input gets no gradient**, which is the
comprehension check here.
</details>

**C3.** Write the four backprop rules and the layer routine's signature.

<details><summary>Solution</summary>

```
dz⁽ˡ⁾   = da⁽ˡ⁾ ∗ g′⁽ˡ⁾(z⁽ˡ⁾)
da⁽ˡ⁻¹⁾ = W⁽ˡ⁾ᵀ · dz⁽ˡ⁾
dW⁽ˡ⁾   = dz⁽ˡ⁾ · a⁽ˡ⁻¹⁾
db⁽ˡ⁾   = dz⁽ˡ⁾
```
Signature (p39): **input `da[l]`; output `da[l−1]`, `dW[l]`, `db[l]`.** That
uniform signature is what lets frameworks compose arbitrary architectures.
</details>

**C4.** What is `δ⁽ˡ⁾` and what three jobs does it do?

<details><summary>Solution</summary>

`δ⁽ˡ⁾ = dz⁽ˡ⁾`, the **error signal** for layer `l` (p40). It (1) accumulates the
gradient of the loss, (2) is passed backward to compute weight and bias
gradients, (3) helps compute the next layer's delta.
</details>

**C5.** Write the SGD-with-backprop algorithm and label its three phases.

<details><summary>Solution</summary>

See reference §8 (p41). Phases: **forward pass** (feed-forward to `ŷ`, `a[l]`,
`z[l]`) → **backpropagation** (`da[L] = dL/dŷ`, then `dz[l]`, `da[l−1]` per layer)
→ **gradient descent** (`W ← W − α dz·a[l−1]`, `b ← b − α dz`). Initialisation is
"small random numbers", which is specified deliberately (cf. p47, p67).
</details>

**C6.** *(Verification, worth doing once.)* Run the p43–45 PyTorch snippet and
compare `W2.grad` and `b2.grad` against C1.

<details><summary>Solution</summary>

`b2.grad ≈ 0.0531`, `W2.grad ≈ (0.0143, 0.0506)`. If they match, your hand
computation is right *and* you understand what `requires_grad` / `.backward()` /
`.grad` do. This is the highest-value single exercise in the bank.
</details>

## 6. Drills — Group D: training

**D1.** *(Quiz slide p48.)* Which are hyper-parameters: #iterations, `b[l]`,
`W[l]`, #layers `L`, `a[l]`, learning rate `α`?

<details><summary>Solution</summary>

Hyper-parameters: **#iterations, #layers L, learning rate α**. Model parameters
(learned by training): **`W[l]`, `b[l]`**. `a[l]` is **neither** — it is a
computed activation. That is the trap. (p49)
</details>

**D2.** *(Quiz slide p53.)* Which is the logistic loss?

<details><summary>Solution</summary>

`L(ŷ,y) = −[y log ŷ + (1−y) log(1−ŷ)]`. The others are L1/absolute, hinge-like
`max(0, ŷ−y)`, and squared error.
</details>

**D3.** Give the regularized network cost with the Frobenius penalty, and the one
change it makes to the gradient.

<details><summary>Solution</summary>

```
L = −(1/m)Σᵢ cost(xⁱ,yⁱ) + (λ/2m) Σₗ ‖W[l]‖²_F ,  ‖W[l]‖²_F = ΣᵢΣⱼ (W[l]ᵢⱼ)²
dW[l] = (old gradient from backprop) + (λ/m)·W[l]
```
(p56–57). Note the bias is excluded from the penalty (p54).
</details>

**D4.** Compute `‖W‖²_F` for `W = [[1,2,1], [−1,2,−3], [0,1,−2]]`.

<details><summary>Solution</summary>

`1+4+1 + 1+4+9 + 0+1+4 = 25` (p56).
</details>

**D5.** Explain how high `λ` reduces variance, in the deck's own terms.

<details><summary>Solution</summary>

High `λ` forces `Σ‖W[l]‖²_F` small, so many `Wᵢⱼ → 0`, which *"effectively
removes nodes from the network"* — shrinking capacity and moving the model along
**high variance → just right → high bias** (p58).
</details>

**D6.** L1 vs L2: which zeroes weights, and why geometrically?

<details><summary>Solution</summary>

**L1 (Lasso)** zeroes them: its constraint region has corners on the axes, so the
optimum frequently lands *at* an axis → many weights exactly 0. **L2 (Ridge)** has
a round region, so the intersection can be anywhere → weights become small but
nonzero. (p55)
</details>

**D7.** Describe dropout at train and test time, and give **both** rationales.

<details><summary>Solution</summary>

Train: with some probability and for some iterations, randomly set node weights to
0 and do not update them (10–20%+); training later resumes with a different set.
**Test: all nodes kept.** (p60)

Both rationales (p61): dropped nodes may be **good** — others must learn to
compensate for their absence, so no unit is relied on exclusively; or **bad** —
dropping them stops others over-compensating for a misleading node. The second
half is the one usually forgotten.
</details>

**D8.** When do you stop under early stopping, and what two benefits are claimed?

<details><summary>Solution</summary>

Stop **once the validation loss plateaus** — training loss still falling while
validation turns up. Benefits: avoids overfitting, saves computation time. (p63)
</details>

**D9.** State double descent, its citation, and the honest caveat.

<details><summary>Solution</summary>

Performance first improves, then worsens (overfitting), then **improves again**
with larger model size, data size or training time. Belkin et al., PNAS 116(32),
2019. Caveat, in the deck's words: *"The mechanism is not fully understood, yet"*
(p65–66). Say the caveat — asserting a settled explanation is wrong.
</details>

## 7. Drills — Group E: vanishing / exploding gradients

**E1.** 7-layer network, linear activations, no bias, `W[l] = λI`. Give `ŷ` for
`λ = 1.5` and `λ = 0.5`, and state the general rule.

<details><summary>Solution</summary>

`ŷ = λ⁷·x`. With `λ=1.5` → `1.5⁷·x ≈ 17.1·x`, **explodes**. With `λ=0.5` →
`0.5⁷·x ≈ 0.0078·x`, **vanishes**. General: `λ>1` explodes, `λ<1` vanishes.
(p70–72)
</details>

**E2.** Why does the same problem affect the *backward* pass?

<details><summary>Solution</summary>

`dz⁽ˡ⁾ = da⁽ˡ⁾ ∗ σ′(z⁽ˡ⁾)` and `da⁽ˡ⁻¹⁾ = W⁽ˡ⁾ᵀ·dz⁽ˡ⁾`, so the same factor `λ`
multiplies at every layer going backwards — the gradient picks up `λᴸ` exactly as
the signal did (p72). One phenomenon, seen twice, not two problems.
</details>

**E3.** Give the expressiveness ladder by depth.

<details><summary>Solution</summary>

- **No hidden layer:** perceptron power — AND, OR, NOT, **not XOR**.
- **One hidden layer:** any Boolean function, but possibly needing an
  **exponential** number of hidden units.
- **Two hidden layers:** any function to arbitrary accuracy. (p73)
</details>

## 8. External practice — solution-checked, matched to L09

- **Karpathy, micrograd** (`source-karpathy-micrograd`) — builds a scalar autograd
  engine from nothing. The closest possible match to p6–7 and p38–40; if backprop
  feels like symbol-pushing, this is the fix.
- **CS231n notes** (`source-cs231n-notes`) — the "Backpropagation, Intuitions"
  page is the same local-gradient/chain-rule story with more worked graphs.
- **MIT 6.036** (`source-mit-6036`) — clean, solution-bearing backprop problems.
- **CS4780 homeworks** (`source-cs4780-homeworks`) — local complete bank; take the
  gradient-derivation and regularization items.
- **PyTorch tutorials** (`source-pytorch-tutorials`) — autograd, for C6.

## 9. Suggested sequence

1. **A1–A4** — graph vocabulary and the forward pass (fast; reuses L08).
2. **B1–B3** — the local derivatives; derive `σ′` by hand once.
3. **C1 then C2** — the full backward pass. Repeat until automatic.
4. **C6** — verify against PyTorch. Do not skip; it converts belief into evidence.
5. **C3–C5** — the four rules, `δ`, and the SGD algorithm from memory.
6. **D1, D2, D3, D4** — the two quiz slides plus the Frobenius arithmetic.
7. **D5–D9, E1–E3** — training techniques and the `λᴸ` argument.
8. Then `note-aml-l09-mock-exam`, 75 minutes closed book.

> **Evidence note.** Record what you actually solved on `unit-aml-l09` — an
> exercise bank with no recorded attempts is a plan, not evidence (CLAUDE.md §7).
