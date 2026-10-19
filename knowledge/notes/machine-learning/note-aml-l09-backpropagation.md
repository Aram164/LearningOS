---
id: note-aml-l09-backpropagation
type: note
title: "AML L09 — Ultimate Reference: Backpropagation, Training, Vanishing Gradients"
created: "2026-08-15"
role: reference
state: evolving
authorship: operator-drafted
concepts: [concept-backpropagation, concept-neural-network, concept-gradient-descent,
  concept-cross-entropy]
sources: [source-aml-ss26-lectures]
contexts: [workspace-aml-exam-prep]
---

> **Build note (2026-08-15).** Drafted by the operator directly from the current
> 2026 deck `lecture-slides/VL 09-neural-networks.pdf` (74 pages), page-anchored
> throughout. Companions: `note-aml-l09-exercise-bank`, `note-aml-l09-mock-exam`.
> `authorship: operator-drafted` — **not yet Aram's synthesis**; becomes `mixed` when he
> works it. Slide-traceable but unverified-by-learner.

# AML Lecture 09 — Ultimate Reference: Backpropagation

*Built from `VL 09-neural-networks.pdf`, 74 pages (titled "Training Feedforward
Neural Networks"). Prior-year variant:
`older-lecture-slides/09-neural-networks_ee470e688da6f9ccb513b94db8c60280.pdf`.*

> ⚠️ **Scope note (slide-verified).** L09 is the backward pass that L08 deferred
> (L08 p53 → "Next lecture"). It **reuses L08's exact running example** and adds
> a loss node, so the forward numbers are identical — study the two together.
>
> **Batch normalization is NOT in this lecture** — do not import it from external
> NN material. The training block is exactly: regularization (Frobenius/L2/L1),
> dropout, early stopping, double descent, then vanishing/exploding gradients.
>
> 🔎 **Slide anomaly (p11):** the deck prints *"σ(1.749) = 0.940"*. The value
> 0.940 is `σ(2.749)`, and 2.749 is the `z⁽²⁾` computed on that same slide — so
> "1.749" is a typo. Preserved here rather than silently corrected; use 2.749.

## Table of Contents

0. [The running example](#0-example)
1. [What backpropagation is](#1-what)
2. [Computation graphs](#2-graphs)
3. [The forward pass with a loss node](#3-forward)
4. [Chain rule refresher](#4-chain)
5. [The four local derivatives](#5-locals)
6. [The backward pass, numerically](#6-backward)
7. [The four backprop rules](#7-rules)
8. [SGD with backpropagation](#8-sgd)
9. [PyTorch autograd](#9-pytorch)
10. [Hyper-parameters vs model parameters](#10-hyper)
11. [Regularization](#11-reg)
12. [Dropout](#12-dropout)
13. [Early stopping](#13-early)
14. [Double descent](#14-dd)
15. [Vanishing and exploding gradients](#15-vanishing)
16. [Expressiveness by depth](#16-expressiveness)
17. [Exam-shaped summary](#17-summary)

---

## 0. The running example <a name="0-example"></a>

p9. **Identical to L08's** network, now with `y = 0` and an L2 loss node:

```
W⁽¹⁾ = [[1,2],[1,2]]   b⁽¹⁾ = (−2, 2)
W⁽²⁾ = (−2, 4.5)        b⁽²⁾ = −1
x = (1, 0)              y = 0
```

Every number in this reference comes from that one example. Learn it once.

## 1. What backpropagation is <a name="1-what"></a>

p2–4. *"Backpropagation is the workhorse of neural networks."* The algorithm is
**a mixture of the chain rule and stochastic gradient descent**. Introduced in
the 1970s, rediscovered in 1986 by **Rumelhart, Hinton and Williams**.

p3 gives the shape: forward-pass `x` to get `ŷ`; the last layer is closest to the
error, so (a) derive the error at the output and update those weights, then
(b) recurse backwards to the second-last layer and so on to the first.

p4 quotes Papadimitriou: *"An ancient algorithm known to perform poorly when the
dimension is small suddenly becomes miraculous when the dimension is huge — the
blessing of dimensionality."* Quotable in a synthesis answer.

## 2. Computation graphs <a name="2-graphs"></a>

p6–7. Rationale: *decompose complex computations into a sequence of atomic
assignments*. The forward pass takes one training point `(x,y)` and computes loss
`L`; the gradients `∇L` come from a backward pass. Both are efficient **because
intermediate results are stored and reused** — that reuse is the whole efficiency
argument, and it is the most likely "why is backprop fast" answer.

> *"This decomposition is key of the backpropagation algorithm."*

p7: a computation graph has **three kinds of nodes — input, parameter, compute.**
The MLP-with-squared-loss graph is:

```
x, W⁽¹⁾, b⁽¹⁾ → z⁽¹⁾ → a⁽¹⁾ → z⁽²⁾ → a⁽²⁾ = ŷ → L
                          ↑ W⁽²⁾, b⁽²⁾              ↑ y
```

p8 states the assumptions: fully-connected, **one hidden layer**, weight updates
after a **single** training example (i.e. SGD), squared loss `L = ½(ŷ−y)²`,
sigmoid activations.

## 3. The forward pass with a loss node <a name="3-forward"></a>

p11, p14:

```
z⁽¹⁾ = W⁽¹⁾x + b⁽¹⁾ = (1,1) + (−2,2) = (−1, 3)
a⁽¹⁾ = σ(−1, 3)                      = (0.269, 0.953)
z⁽²⁾ = (−2,4.5)·(0.269,0.953) − 1    = 2.749
a⁽²⁾ = ŷ = σ(2.749)                  = 0.940
L2(ŷ, y) = ½(0.940 − 0)²             = 0.442
```

(L08 rounds the hidden activations to 0.267/0.952; L09 prints 0.269/0.953. Use
L09's for L09 arithmetic — the downstream gradient numbers depend on them.)

p13: `cost = ½(ŷ − y)²`, chosen *"for simplicity of calculation"* — the ½ exists
so the derivative is clean.

p12 poses a forward-prop quiz; the correct implementation for layer `l` is
**option 3**: `z[l] = W[l]a[l−1] + b[l]`, `a[l] = g⁽ˡ⁾(z[l])`. Options 1 and 2 get
the indices wrong (`a[l]` on the right, or mismatched `W[l−1]`).

p15 motivates autodiff: all operations must be differentiable, but *"manually
deriving the gradient would be very painful/tedious — and we must derive it every
time we modify the architecture."*

## 4. Chain rule refresher <a name="4-chain"></a>

p18–20. `(f(g(x)))′ = f′(g(x)) · g′(x)`, Leibniz form `dz/dx = (∂z/∂y)(dy/dx)`.

p19 notes the notation convention: **∂ marks a partial derivative** —
differentiate with respect to one variable holding the others constant.

p20 is the picture worth carrying: the whole network is one long composition

```
x → z⁽¹⁾ = W⁽¹⁾x+b⁽¹⁾ → a⁽¹⁾ = g(z⁽¹⁾) → z⁽²⁾ = W⁽²⁾a⁽¹⁾+b⁽²⁾ → ŷ = g(z⁽²⁾) → L(y,ŷ)
```

and backprop is the chain rule walked right-to-left along it.

## 5. The four local derivatives <a name="5-locals"></a>

p22–28. Each node contributes one local derivative; memorise these four:

| Node | Derivative | Value | Slide |
|---|---|---|---|
| L2 loss | `∂L2/∂ŷ` | `ŷ − y` | p22 |
| Sigmoid | `∂a/∂z = σ′(z)` | `σ(z)(1 − σ(z))` | p23 |
| Weight node, wrt input | `∂z/∂a` | `W` | p24 |
| Weight node, wrt bias | `∂z/∂b` | `1` | p24 |
| Weight node, wrt weights | `∂z/∂W` | `a` | p25–26 |

p25 gives the scalar case, p26 the vector case (differentiate `w·a + b`
componentwise → each entry is the matching `aᵢ`, so the gradient is `a`).

> ⚠️ **p27 footnote, and it is exam-bait:** `∂z/∂W = a` *"is only correct in the
> context of the chain rule (else ∂z/∂W is a second-order tensor)."* Quote the
> caveat if asked to justify the shape.

`σ′(z) = σ(z)(1−σ(z))` is worth deriving once so it is not just memorised.

## 6. The backward pass, numerically <a name="6-backward"></a>

p30–35. **This is the single most exam-likely computation in the lecture** — six
slides, one step each. `y = 0`, so `ŷ − y = 0.940`.

```
∂L2/∂a⁽²⁾ = ŷ − y                        = 0.94 − 0 = 0.940      (p30)

∂L2/∂z⁽²⁾ = (∂L2/∂a⁽²⁾)·σ′(z⁽²⁾)
          = 0.94 · σ(2.749)(1−σ(2.749))
          = 0.94 · 0.0565                = 0.0531                (p31)

∂L2/∂b⁽²⁾ = ∂L2/∂z⁽²⁾ · 1                = 0.0531                (p32)

∂L2/∂a⁽¹⁾ = W⁽²⁾ᵀ · ∂L2/∂z⁽²⁾
          = (−2, 4.5)ᵀ · 0.0531          = (−0.106, 0.239)       (p33)

∂L2/∂W⁽²⁾ = ∂L2/∂z⁽²⁾ · a⁽¹⁾
          = 0.0531 · (0.269, 0.953)      = (0.0143, 0.0506)      (p34)
```

p35 shows the complete forward-and-backward picture, adding the first-layer
gradients:

```
dz⁽¹⁾ = (−0.0209, 0.0108)
db⁽¹⁾ = (−0.0209, 0.0108)
dW⁽¹⁾ = [[−0.0209, 0], [0.0108, 0]]      (second column 0 because x₂ = 0)
dx    = (−0.0101, −0.0202)
```

`dW⁽¹⁾`'s zero column is a good comprehension check: `dW = dz · a⁽⁰⁾ᵀ = dz · xᵀ`,
and `x = (1,0)`, so nothing flows to weights on the dead input.

p36: the weight update, `W ← W − α·dW`, `b ← b − α·db`, with `α` the learning
rate.

## 7. The four backprop rules <a name="7-rules"></a>

p38–39. Everything above compresses to four lines. **Memorise these:**

```
dz⁽ˡ⁾   = da⁽ˡ⁾ ∗ g′⁽ˡ⁾(z⁽ˡ⁾)        // elementwise
da⁽ˡ⁻¹⁾ = W⁽ˡ⁾ᵀ · dz⁽ˡ⁾
dW⁽ˡ⁾   = dz⁽ˡ⁾ · a⁽ˡ⁻¹⁾
db⁽ˡ⁾   = dz⁽ˡ⁾
```

p39 frames it as a reusable layer routine: **input `da[l]`; output `da[l−1]`,
`dW[l]`, `db[l]`.** That signature is why frameworks can compose arbitrary
architectures.

p40 connects to classical notation: `dz⁽ˡ⁾ = δ⁽ˡ⁾`, the **error signal** for layer
`l`, which (1) accumulates the gradient of the loss, (2) is passed backward to
compute weight and bias gradients, and (3) helps compute the next layer's delta.

## 8. SGD with backpropagation <a name="8-sgd"></a>

p41, worth reproducing verbatim:

```
Initialize all weights to small random numbers
Repeat until convergence:
    Pick a single training example x
    Feed-forward to compute ŷ, activations a[l], pre-activations z[l]   // forward
    For the final L-th layer:  da[L] = dL/dŷ                            // backprop
    For layer l ∈ [1…L]:
        dz[l]   = da[l] ∗ g′⁽ˡ⁾(z[l])
        da[l−1] = W[l]ᵀ · dz[l]
    Update:  W[l] ← W[l] − α·dz[l]·a[l−1]                               // GD
             b[l] ← b[l] − α·dz[l]
```

Three phases, and the exam may ask you to label them: **forward pass →
backpropagation → gradient descent**. Note "small random" initialisation is
specified, not incidental (see p47).

## 9. PyTorch autograd <a name="9-pytorch"></a>

p43–45. The same example in code:

```python
W1 = torch.tensor([[1,2],[1,2]], requires_grad=True, dtype=torch.float)
b1 = torch.tensor([-2,2],        requires_grad=True, dtype=torch.float)
W2 = torch.tensor([-2,4.5],      requires_grad=True, dtype=torch.float)
b2 = torch.tensor([-1.0],        requires_grad=True, dtype=torch.float)
x  = torch.tensor([1,0], dtype=torch.float)

z1 = W.mv(x) + b1                       # matrix-vector product
a1 = torch.nn.Sigmoid()(z1)
z2 = torch.dot(W2, a1) + b2
a2 = y_pred = torch.nn.Sigmoid()(z2)
error = 1/2 * (y - y_pred) ** 2

error.backward()                        # gradients derived automatically
W1.grad, b1.grad, W2.grad, b2.grad
```

`requires_grad=True` is what puts a tensor in the graph; `.backward()` runs the
pass; `.grad` holds the result. The values match §6.

## 10. Hyper-parameters vs model parameters <a name="10-hyper"></a>

p48–49. p48 is a quiz slide — of `#iterations`, `b[l]`, `W[l]`, `#layers L`,
`a[l]`, `α`, which are hyper-parameters? Answer from p49:

- **Model parameters** (learned via **training**): `W[l]`, `b[l]`.
- **Hyper-parameters** (chosen via **validation**): learning rate, epochs,
  #hidden layers, #hidden units, activation function, Adam settings
  (momentum, RMSProp), mini-batch size, regularization.

`a[l]` is neither — it is a computed activation. That is the trap in the quiz.

p47 lists the training problems: (1) wrong learning rate → drastic updates,
(2) bad initialization → slow progress, (3) local optima → premature convergence.

## 11. Regularization <a name="11-reg"></a>

p50–58. p50: with millions of parameters networks overfit easily when trained for
many epochs (GPT-4 named as hundreds of billions of parameters). p51 lists the
four remedies: **regularization, dropout, early stopping, double descent.**

p53 quizzes which is the "logistic loss" — the answer is
`L(ŷ,y) = −[y log ŷ + (1−y) log(1−ŷ)]`.

p54 recalls the logistic-regression case:

```
L2 (Ridge):  L(w) = −(1/m)Σ cost + (λ/2m)‖w‖²₂ ,  ‖w‖²₂ = Σ w²ⱼ = wᵀw
L1 (Lasso):  L(w) = −(1/m)Σ cost + (λ/2m)‖w‖₁  ,  ‖w‖₁  = Σ |wⱼ|
```

with `λ` a hyper-parameter, and **the bias `b = w₀` excluded** from the penalty.

p55: Lasso's constraint region has corners on the axes, so the optimum often lands
*at* an axis → **many weights exactly 0**; Ridge's is round, so weights become
small but nonzero.

p56, the network version — the penalty uses the **Frobenius norm**:

```
L(W⁽¹⁾,b⁽¹⁾,…) = −(1/m) Σᵢ cost(xⁱ,yⁱ) + (λ/2m) Σₗ ‖W[l]‖²_F
‖W[l]‖²_F = Σᵢ Σⱼ (W[l]ᵢⱼ)²
```

Worked example on p56: for `W = [[1,2,1], [−1,2,−3], [0,1,−2]]`,
`‖W‖²_F = 1+4+1+1+4+9+0+1+4 = 25`.

p57, the gradient change — one term, and it is the examinable line:

```
dW[l] = (old gradient from backprop) + (λ/m)·W[l]
```

p58, the intuition: high `λ` forces `‖W‖²_F` small → many `Wᵢⱼ → 0` → *"we
effectively remove nodes from the network"*, moving along the
**high-variance → just right → high bias** axis.

## 12. Dropout <a name="12-dropout"></a>

p60–61.

- **At train time**, with some probability and for some iterations, randomly
  remove nodes by **setting their weight to 0**; those parameters are not updated.
  Typically **10%, 20% or more** of nodes. Training then resumes with a different
  dropped set.
- **At test time, all nodes are kept.**

p61's rationale is two-sided and the second half is the part usually forgotten:
dropped nodes may be **good** — so other nodes must learn to compensate for their
absence, preventing over-reliance on any one unit; or **bad** — so dropping them
avoids other nodes over-compensating for a misleading node.

## 13. Early stopping <a name="13-early"></a>

p63. Stop training **once the validation loss plateaus** — the point where
training loss keeps falling while validation loss turns up. Two benefits given:
avoids overfitting, and saves computation time.

## 14. Double descent <a name="14-dd"></a>

p65–66. Belkin et al., *"Reconciling modern machine-learning practice and the
classical bias–variance trade-off"*, PNAS 116(32), 2019.

Performance **first improves** (generalization), **then gets worse**
(overfitting), and **finally improves again** as model size, data size or training
time increases. The deck is explicit that *"the mechanism is not fully understood,
yet"* — say that too; claiming a settled explanation is wrong.

The practical reading (p51): "train an even larger model" is a legitimate response
to overfitting, which contradicts the classical bias–variance story.

p67 lists practice: use a regularizer, try other losses, initialize more cleverly
(*"random initializations are likely to be far from optimal"*), dropout, early
stopping, Adam (momentum + RMSProp).

## 15. Vanishing and exploding gradients <a name="15-vanishing"></a>

p69–72. Take a deep network with **linear activations and no bias**, 7 layers:

```
ŷ = W⁽⁷⁾W⁽⁶⁾W⁽⁵⁾W⁽⁴⁾W⁽³⁾W⁽²⁾(W⁽¹⁾x)
```

With every `W[l] = λI`:

| λ | Result | Slide |
|---|---|---|
| `1.5` | `ŷ = 1.5⁷·x` → **explodes** | p70 |
| `0.5` | `ŷ = 0.5⁷·x` → **vanishes** | p71 |

p72 generalises: `W[l] = λI` with `L = 7` gives `ŷ = λᴸ·x`, so `λ>1` explodes and
`λ<1` vanishes — **and the same holds for the derivative**, since
`dz⁽ˡ⁾ = da⁽ˡ⁾ ∗ σ′(z⁽ˡ⁾)` chains the same multiplicative factor backwards.

That last sentence is the point: it is one phenomenon seen twice, forward and
backward, not two separate problems.

## 16. Expressiveness by depth <a name="16-expressiveness"></a>

p73, a compact and very examinable ladder:

| Depth | Representational power |
|---|---|
| **No hidden layer** | same as a perceptron — Boolean AND, OR, NOT, **but not XOR** |
| **One hidden layer** | can represent **any Boolean function** — but may require an **exponential** number of hidden units |
| **Two hidden layers** | **any function** approximated to arbitrary accuracy |

The middle row is the one to state carefully: one hidden layer is *sufficient* in
principle, and that is exactly why the exponential-width caveat matters.

## 17. Exam-shaped summary <a name="17-summary"></a>

Eight things to do cold:

1. Draw the computation graph for a one-hidden-layer MLP with squared loss, and
   name the three node kinds (p7).
2. Run the forward pass on the running example to `L2 = 0.442` (p11, p14).
3. State the four local derivatives, including the `∂z/∂W = a` chain-rule caveat
   (p22–27).
4. Run the full backward pass to `dW⁽²⁾ = (0.0143, 0.0506)` (p30–35).
5. Write the four backprop rules and the layer routine's input/output signature
   (p38–39).
6. Write the SGD-with-backprop algorithm and label its three phases (p41).
7. Separate model parameters from hyper-parameters (p49); give the Frobenius
   penalty and the `+(λ/m)W` gradient term (p56–57).
8. Explain dropout (both rationales), early stopping, double descent, and the
   `λᴸ` vanishing/exploding argument (p60–72).

### Deliberately out of scope

- **Batch normalization** — not in this deck.
- Convolution → **L10**.
- Softmax and metrics → **L08**.
- Adam's internals — named on p49 and p67, never derived.

### Open questions for Aram

- p12 (forward-prop indices), p48 (hyper-parameters) and p53 (logistic loss) are
  three **quiz slides**. Lecturers who quiz in-deck often reuse those exact items
  — treat all three as high-probability exam questions.
- The p11 typo (`σ(1.749)`) is recorded, not corrected. If the exam reproduces the
  slide verbatim, the intended value is still 0.940.
