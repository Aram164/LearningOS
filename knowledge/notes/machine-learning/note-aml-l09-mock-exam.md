---
id: note-aml-l09-mock-exam
type: note
title: "AML L09 — Mock Exam (Backpropagation, Training, Vanishing Gradients)"
created: "2026-08-15"
role: mock-exam
state: evolving
authorship: operator-drafted
concepts: [concept-backpropagation, concept-neural-network, concept-gradient-descent]
sources: [source-aml-ss26-lectures]
contexts: [workspace-aml-exam-prep]
---

> **Build note (2026-08-15).** Drafted by the operator from
> `VL 09-neural-networks.pdf`. Companion: `note-aml-l09-backpropagation`
> (section refs in the key). `authorship: operator-drafted` — key is operator-computed and
> **unverified by Aram**. Difficulty at or above the real exam by design.

# AML Lecture 09 — Mock Exam (Backpropagation, Training, Vanishing Gradients)

**Topic:** computation graphs, chain rule and local derivatives, the backward
pass, the four backprop rules, SGD, autograd, hyper-parameters, regularization,
dropout, early stopping, double descent, vanishing/exploding gradients,
expressiveness by depth.
**Companion:** `note-aml-l09-backpropagation` (§ refs in the key).
**Suggested time:** 75 minutes, closed-book.

> **Scoring:** Part A = 20 (2 each) · Part B = 40 · Part C = 15 (3 each) ·
> Part D = 25. **Total 100.**
>
> **Conventions:** `σ(z) = 1/(1+e⁻ᶻ)`, `L2 = ½(ŷ−y)²`.
> Provided: σ(−1)=0.269, σ(3)=0.953, σ(2.749)=0.940, σ′(2.749)=0.0565.
> `1.5⁷ ≈ 17.09`, `0.5⁷ ≈ 0.0078`.
>
> ⚠️ **No batch normalization is examined** — not in this deck. Softmax and
> metrics are L08.

---

## Part A — Conceptual Short Answer (2 pts each)

**A1.** Name the three kinds of nodes in a computation graph.

**A2.** Why are the forward and backward passes efficient? Give the deck's reason.

**A3.** Write the local derivative of the L2 loss node and of the sigmoid node.

**A4.** State the caveat the deck attaches to `∂z/∂W = a`.

**A5.** Write the four backprop rules for layer `l`.

**A6.** What is `δ⁽ˡ⁾`, and name one of its three roles.

**A7.** Classify as model parameter, hyper-parameter, or neither:
`W[l]`, `α`, `a[l]`, number of hidden units.

**A8.** Write the regularized cost with the Frobenius penalty, and the single term
it adds to `dW[l]`.

**A9.** What happens to dropout at **test** time?

**A10.** State the expressiveness of a network with **one** hidden layer, including
the caveat.

---

## Part B — Numerical Problems (show your work)

### B1. Forward pass with loss (8 pts)

`W⁽¹⁾ = [[1,2],[1,2]]`, `b⁽¹⁾ = (−2,2)`, `W⁽²⁾ = (−2,4.5)`, `b⁽²⁾ = −1`,
`x = (1,0)`, `y = 0`. Compute `z⁽¹⁾, a⁽¹⁾, z⁽²⁾, ŷ, L2`.

### B2. Backward pass (16 pts)

Same network. Compute in order: `∂L2/∂a⁽²⁾`, `∂L2/∂z⁽²⁾`, `∂L2/∂b⁽²⁾`,
`∂L2/∂a⁽¹⁾`, `∂L2/∂W⁽²⁾`.

### B3. First-layer gradient (6 pts)

Given `dz⁽¹⁾ = (−0.0209, 0.0108)`, give `db⁽¹⁾` and `dW⁽¹⁾`. Explain why one
column of `dW⁽¹⁾` is entirely zero.

### B4. Frobenius norm (4 pts)

`W = [[1,2,1], [−1,2,−3], [0,1,−2]]`. Compute `‖W‖²_F`. If `λ = 10` and `m = 5`,
what is added to `dW`?

### B5. Vanishing / exploding (6 pts)

7-layer network, linear activations, no bias, `W[l] = λI`. Give `ŷ` in terms of
`λ` and `x`, evaluate for `λ = 1.5` and `λ = 0.5`, and state which case affects
the *gradient*.

---

## Part C — True / False + One-Line Justification (3 pts each)

**C1.** `a[l]` is a hyper-parameter because you choose the activation function.

**C2.** Dropout removes nodes at both training and test time.

**C3.** L1 regularization drives many weights to exactly zero, L2 drives them
toward small nonzero values.

**C4.** Double descent is a well-understood phenomenon with an accepted
theoretical explanation.

**C5.** A network with one hidden layer cannot represent XOR.

---

## Part D — Synthesis (25 pts)

**D1. (10 pts)** Explain, end to end, why backpropagation is efficient — and why
the naive alternative is not. Refer to the computation-graph decomposition, the
reuse of intermediate results, and the layer routine's input/output signature.

**D2. (8 pts)** You train a deep network; the training loss falls steadily while
validation loss bottoms out at epoch 30 and then climbs. Name **four** distinct
interventions the lecture offers, say what each does mechanically, and note which
one is in tension with the classical bias–variance story.

**D3. (7 pts)** A colleague initialises all weights of a 7-layer network to
`2·I` and reports that training produces `NaN` within a few steps. Diagnose it
using the lecture's own argument, explain why the problem appears in **both**
passes, and name two fixes the deck offers.

---
---

# ANSWER KEY

*Section refs are to `note-aml-l09-backpropagation`.*

## Part A

**A1.** Input nodes, parameter nodes, compute nodes. (§2, p7)

**A2.** *"Forward pass and the backward pass are efficient due to storing and
reusing intermediate results"* — the decomposition into atomic assignments is what
makes that reuse possible. (§2, p6)

**A3.** `∂L2/∂ŷ = ŷ − y` (p22); `∂a/∂z = σ′(z) = σ(z)(1−σ(z))` (p23). (§5)

**A4.** It *"is only correct in the context of the chain rule (else ∂z/∂W is a
second-order Tensor)"* — p27 footnote. (§5)

**A5.**
```
dz⁽ˡ⁾ = da⁽ˡ⁾ ∗ g′⁽ˡ⁾(z⁽ˡ⁾);  da⁽ˡ⁻¹⁾ = W⁽ˡ⁾ᵀ·dz⁽ˡ⁾;  dW⁽ˡ⁾ = dz⁽ˡ⁾·a⁽ˡ⁻¹⁾;  db⁽ˡ⁾ = dz⁽ˡ⁾
```
(§7, p38–39)

**A6.** `δ⁽ˡ⁾ = dz⁽ˡ⁾`, the error signal for layer `l`. Roles: accumulates the loss
gradient; is passed backward for weight/bias gradients; helps compute the next
layer's delta. (§7, p40)

**A7.** `W[l]` = model parameter; `α` = hyper-parameter; `a[l]` = **neither**
(a computed activation); number of hidden units = hyper-parameter. (§10, p49)

**A8.** `L = −(1/m)Σ cost + (λ/2m) Σₗ ‖W[l]‖²_F`; adds `+(λ/m)·W[l]` to `dW[l]`.
(§11, p56–57)

**A9.** **All nodes are kept** at test time. (§12, p60)

**A10.** It can represent **any Boolean function**, but may require an
**exponential** number of hidden units. (§16, p73)

## Part B

**B1. (8 pts)**
```
z⁽¹⁾ = (1,1) + (−2,2) = (−1, 3)
a⁽¹⁾ = (σ(−1), σ(3))  = (0.269, 0.953)
z⁽²⁾ = −2(0.269) + 4.5(0.953) − 1 = −0.538 + 4.2885 − 1 = 2.749
ŷ    = σ(2.749) = 0.940
L2   = ½(0.940 − 0)² = 0.442
```
(§3, p11, p14)

**B2. (16 pts)** — 3 pts each of the first four, 4 pts the last.
```
∂L2/∂a⁽²⁾ = ŷ − y = 0.940
∂L2/∂z⁽²⁾ = 0.940 · σ′(2.749) = 0.940 · 0.0565 = 0.0531
∂L2/∂b⁽²⁾ = 0.0531 · 1 = 0.0531
∂L2/∂a⁽¹⁾ = W⁽²⁾ᵀ · 0.0531 = (−2, 4.5)ᵀ·0.0531 = (−0.106, 0.239)
∂L2/∂W⁽²⁾ = 0.0531 · (0.269, 0.953) = (0.0143, 0.0506)
```
(§6, p30–34)

**B3. (6 pts)**
```
db⁽¹⁾ = dz⁽¹⁾ = (−0.0209, 0.0108)
dW⁽¹⁾ = dz⁽¹⁾ · xᵀ = [[−0.0209, 0], [0.0108, 0]]
```
The second column is zero because `dW⁽¹⁾ = dz⁽¹⁾·a⁽⁰⁾ᵀ = dz⁽¹⁾·xᵀ` and `x₂ = 0` —
**an input that is zero contributes no gradient to the weights that read it**.
(§6, p35)

**B4. (4 pts)**
```
‖W‖²_F = (1+4+1) + (1+4+9) + (0+1+4) = 25
added to dW: (λ/m)·W = (10/5)·W = 2W
```
(§11, p56–57)

**B5. (6 pts)**
```
ŷ = W[7]…W[1]x = λ⁷·x
λ = 1.5 → 1.5⁷·x ≈ 17.09·x   → explodes
λ = 0.5 → 0.5⁷·x ≈ 0.0078·x  → vanishes
```
**Both** affect the gradient: `dz⁽ˡ⁾ = da⁽ˡ⁾∗σ′(z⁽ˡ⁾)` and
`da⁽ˡ⁻¹⁾ = W⁽ˡ⁾ᵀ·dz⁽ˡ⁾` chain the same `λ` factor backwards, so the gradient picks
up `λᴸ` exactly as the forward signal did. (§15, p70–72)

## Part C

**C1. False.** The *activation function* is a hyper-parameter; `a[l]` is the
computed **activation value**, which is neither a parameter nor a
hyper-parameter. This is exactly the p48 trap. (§10)

**C2. False.** Dropout is train-time only — *"At test time, we keep all nodes."*
(§12, p60)

**C3. True.** Lasso's constraint region has corners on the axes so optima land at
zero; Ridge's is round, giving small but nonzero weights. (§11, p55)

**C4. False.** The deck states *"The mechanism is not fully understood, yet."*
(§14, p66)

**C5. False.** One hidden layer can represent **any Boolean function** — including
XOR, as L08 constructed explicitly. The caveat is width (possibly exponential),
not capability. (§16, p73)

## Part D

**D1. (10 pts)** — 4 pts decomposition/reuse, 3 pts the naive alternative, 3 pts
the signature.

*Decomposition and reuse:* the network is decomposed into a sequence of atomic
assignments — a computation graph (p6). The forward pass computes and **stores**
every intermediate `z⁽ˡ⁾` and `a⁽ˡ⁾`; the backward pass then **reuses** them, since
every local derivative (`σ′(z⁽ˡ⁾)`, `a⁽ˡ⁻¹⁾`, `W⁽ˡ⁾`) is expressible in quantities
already computed. Nothing is recomputed. This reuse *"is key of the
backpropagation algorithm"*.

*The naive alternative:* differentiating the loss with respect to each parameter
independently re-traverses the whole composition once per parameter, and
recomputes every shared intermediate each time — cost scaling with the number of
parameters rather than one backward sweep. p15 adds the human cost: manual
derivation is *"very painful/tedious — and we must derive it every time we modify
the architecture."*

*The signature:* p39 gives every layer the same interface — **in: `da[l]`;
out: `da[l−1]`, `dW[l]`, `db[l]`.** Because `da[l−1]` is exactly what the previous
layer needs, layers compose without knowing anything about each other, which is
what makes autodiff frameworks (p43–45) possible at all.

**D2. (8 pts)** — 1.5 pts per intervention, 2 pts the tension.

The pattern described is textbook overfitting (p50). Four interventions (p51):

1. **Regularization** — add `(λ/2m)Σ‖W[l]‖²_F` to the cost, which adds `(λ/m)W[l]`
   to the gradient; high `λ` shrinks weights toward 0, *"effectively removing
   nodes"* and reducing capacity (p56–58).
2. **Dropout** — randomly zero 10–20%+ of nodes during training so no unit is
   relied on exclusively and others cannot over-compensate for bad units; all
   nodes restored at test (p60–61).
3. **Early stopping** — halt once validation loss plateaus, i.e. at ~epoch 30
   here; avoids overfitting and saves computation (p63).
4. **Double descent** — train an even *larger* model, because performance improves
   again beyond the overfitting regime (p65–66).

*Tension:* **double descent**. The classical bias–variance trade-off says a larger
model past the interpolation point should generalise worse; double descent says it
improves again. Full credit should note the deck's caveat that the mechanism is
not fully understood.

**D3. (7 pts)** — 3 pts diagnosis, 2 pts both passes, 2 pts fixes.

*Diagnosis:* with `W[l] = λI` and `λ = 2` over `L = 7` layers, the forward signal
is `ŷ = λᴸ·x = 2⁷·x = 128·x` (p70, p72). With more layers or more steps this
compounds multiplicatively — **exploding activations**, and overflow to `NaN`.

*Both passes:* the backward recursion `da⁽ˡ⁻¹⁾ = W⁽ˡ⁾ᵀ·dz⁽ˡ⁾` multiplies by the
same `λ` at every layer, so the gradient also scales as `λᴸ`. Exploding gradients
then produce enormous weight updates `W ← W − α·dW`, which diverge immediately —
p47's *"wrong learning rate leads to drastic parameter updates"* compounded by bad
initialisation. It is one multiplicative phenomenon appearing twice, not two.

*Fixes from the deck (any two):* **initialise more cleverly** — *"random
initializations are likely to be far from optimal"*, and `2I` is a deliberate
worst case (p67); **lower the learning rate** (p47); **regularization** to keep
`‖W‖_F` small (p56–58); **Adam (momentum + RMSProp)**, which adapts step size
(p49, p67). A strong answer notes that `λ` near 1 is the target — the failure is
symmetric, since `λ = 0.5` vanishes just as badly.

---

## Self-grading

| Band | Reading |
|---|---|
| **85–100** | L09 is exam-ready. Move to L10. |
| **70–84** | Solid. Re-drill the misses. |
| **55–69** | Backward pass not automatic — redo exercise-bank group C, including the PyTorch check, then re-sit. |
| **< 55** | Re-read reference §5–§7 against the deck before re-sitting. |

> **Log the result.** Record the score and the specific misses as evidence on
> `unit-aml-l09`, and let the misses drive which of L09's 24 routed sources you
> pick next.
