---
id: note-aml-l07-mock-exam
type: note
title: "AML L07 — Mock Exam (Perceptron, Kernel Trick, Multi-Class)"
created: "2026-07-01"
role: mock-exam
state: evolving
authorship: mixed
concepts: [concept-perceptron, concept-kernel-trick, concept-xor-problem]
sources: [source-aml-ss26-lectures]
contexts: [workspace-aml-exam-prep]
---

> **Migration note (2026-07-17, Stage-1 pilot):** body preserved verbatim from
> `Plans/ML/foundations/AML/my notes/lect07 linear classifiers/AML_L07_Mock_Exam.md` (legacy tree). Companions in v3: `note-aml-l07-linear-classifiers` (answer-key section refs). The step hook (F.K2) and the Mini Plan are operational and live in
> `work/active/workspace-aml-exam-prep/`.

# AML Lecture 07 — Mock Exam (Perceptron, Kernel Trick, Multi-Class)

**Topic:** linear classifiers & separability, the perceptron (loss, update, convergence, dual form), computed features & XOR, the kernel trick (polynomial, RBF, landmarks), One-vs-Rest & the multiclass perceptron.
**Companion:** `AML_L07_Ultimate_Reference.md` (section refs in the answer key).
**Suggested time:** 75 minutes, closed-book. Solve everything before opening the key, then self-grade.

> Scoring: Part A = 20 (2 each), Part B = 40, Part C = 15 (3 each), Part D = 25. Total 100.
> Conventions: labels y ∈ {−1,+1}; `sign(0) = +1`; e⁻⁰·²⁵ ≈ 0.78, e⁻¹ ≈ 0.37, e⁻²·²⁵ ≈ 0.11.

---

## Part A — Conceptual Short Answer (2 pts each)

**A1.** Write the perceptron's **prediction rule**. Which label space does it use (and which does logistic regression use)?

**A2.** Write the perceptron **loss** for a single sample (both cases). Why is it called "the amount by which we are wrong"?

**A3.** Write the perceptron **update rule**. Why does it need **no learning rate**?

**A4.** State the perceptron **convergence guarantee** — and what happens when the data is *not* linearly separable.

**A5.** In the **dual form**, what exactly is `αᵢ`? What is it *not* (common confusion)?

**A6.** State the **kernelization criterion**: when can a method be kernelized?

**A7.** Define the **kernel trick** in one sentence (what does `K(x,z)` compute, and what does it avoid?).

**A8.** Give the **polynomial kernel** formula. How many implicit features for degree d in n dimensions, and what does computing K actually cost?

**A9.** Give the **RBF kernel** formula. What does `σ²` control?

**A10.** **One-vs-Rest** with k classes: how is it trained, how does it predict, and name one drawback.

---

## Part B — Numerical Problems (show your work)

### B1. Perceptron trace (12 pts)

Dataset (x ∈ ℝ², labels ±1): `P1 = ([2,1], +1)`, `P2 = ([−1,1], −1)`, `P3 = ([0,−2], −1)`.
Augment `x → (1, x₁, x₂)`, init `w = (0,0,0)`, process points in order P1, P2, P3, repeat; `sign(0)=+1`.
(a) Trace the algorithm in a table (columns: point, y, w·x, ŷ, update?, new w) until a full clean pass.
(b) Give the final w and the number of updates.
(c) Write the final w in dual form: give `α = (α₁, α₂, α₃)` and verify `w = Σαᵢy⁽ⁱ⁾x⁽ⁱ⁾`.

### B2. XOR impossibility (8 pts)

Using step activation (`1 if z ≥ 0`) and `z = w₀ + w₁x₁ + w₂x₂`, write down the four inequalities XOR demands on (w₀, w₁, w₂) and derive a contradiction. What is the **best achievable error** of a linear classifier on the 4 XOR points?

### B3. Kernel trick check (10 pts)

Let `φ(x) = (x₁², x₂², √2·x₁x₂)` and `K(x,z) = (x·z)²`. For `x = (1,2)`, `z = (3,1)`:
(a) Compute `K(x,z)` the kernel way. (b) Compute `φ(x)`, `φ(z)`, and `φ(x)·φ(z)` the naïve way. (c) Compare the operation counts (rough). (d) For MNIST (n = 784, d = 2): how many implicit features does the naïve mapping have (formula suffices), and what does the kernel way cost?

### B4. RBF landmarks (10 pts)

Landmarks `l⁽¹⁾ = (0,0)`, `l⁽²⁾ = (4,0)`; RBF with `σ² = 2`; weights `w = (w₀, w₁, w₂) = (−0.5, 1, 0)`; query `x = (1, 0)`.
(a) Compute `f₁ = K(x, l⁽¹⁾)` and `f₂ = K(x, l⁽²⁾)`.
(b) Compute `z = w₀ + w₁f₁ + w₂f₂` and the prediction (`y=1` iff `z ≥ 0`).
(c) In the lecture's construction, what serves as the landmarks, and how many features does each training sample get?

---

## Part C — True / False + One-Line Justification (3 pts each)

**C1.** The perceptron algorithm converges on any dataset — non-separable data just takes longer.

**C2.** In the dual form, both training and prediction access the data **only through dot products** between sample pairs.

**C3.** The RBF kernel corresponds to a finite-dimensional feature mapping φ.

**C4.** Increasing σ² makes the RBF similarity drop off more slowly (each landmark influences a wider region).

**C5.** In the multiclass perceptron, only the weight vector of the **correct** class is updated on a mistake.

---

## Part D — Synthesis (25 pts)

**D1. (9 pts) The dual form.** Starting from the update rule `w ← w + y⁽ⁱ⁾x⁽ⁱ⁾` (init w = 0), derive `w = Σᵢ αᵢy⁽ⁱ⁾x⁽ⁱ⁾`. Rewrite the prediction so x appears only in dot products, and explain why this — and not the primal form — can be kernelized. Write the kernelized prediction.

**D2. (8 pts) XOR, two cures.** The XOR problem has two historical fixes. Describe both (this lecture's and the next lecture's), give a concrete construction for each (feature ψ / gate combination), and name the ML philosophy each one grew into.

**D3. (8 pts) Multiclass perceptron by hand.** Classes {1,2,3}, current weights `w⁽¹⁾=(0,1,1)`, `w⁽²⁾=(1,−1,0)`, `w⁽³⁾=(0,0,2)`; sample `x = (1,1,2)` (augmented), true label `y = 2`.
(a) Compute the three scores and the prediction. (b) Perform the update (state the rule). (c) Recompute the scores — is x now classified correctly? (d) What is the decision boundary between two classes c and c′, and is it linear?

---
---

# ANSWER KEY

> Section references (§) point to `AML_L07_Ultimate_Reference.md`.

## Part A

**A1.** (§3) `ŷ = sign(w·x)` ∈ **{−1, +1}** (logistic regression uses {0,1} with σ and threshold 0.5).

**A2.** (§4) `L(w) = 0` if `y(w·x) ≥ 0`, else `L(w) = −y(w·x)`. When misclassified, `−y(w·x) = |w·x|·(wrong-side factor)` — literally the size of the violating score, e.g. y=+1, w·x=−0.1 → loss 0.1.

**A3.** (§6) On a mistake: `w ← w + y·x`. The boundary `w·x=0` is **scale-invariant** — multiplying w by any α>0 changes no prediction, so a step size would only rescale w; α=1 suffices.

**A4.** (§8) Separable ⇒ finds a zero-training-error boundary in **finitely many updates** (which one depends on init/order). Non-separable ⇒ **never converges** (always a mistake → always another update).

**A5.** (§7) `αᵢ` = the **number of times point i triggered an update**. It is **not a learning rate** (slide 24's explicit warning).

**A6.** (§13) When every feature vector appears **only inside inner products** `x⁽ⁱ⁾·x⁽ʲ⁾` — true for the dual-form perceptron's training and prediction.

**A7.** (§14) `K(x,z) ≡ φ(x)·φ(z)`, evaluated by algebraic shortcut **in the original space** — avoiding ever computing or storing φ(x).

**A8.** (§15) `K(x,z) = (1 + x·z)^d`. Implicit features: `(n+d choose d) = O(n^d)`; computing K costs only **O(n)**.

**A9.** (§17) `K(x,z) = exp(−‖x−z‖²/2σ²)`. σ² sets the **drop-off rate** of similarity around a point — small σ² = spiky/local (variance risk), large σ² = wide/smooth (bias risk).

**A10.** (§20) Train k binary classifiers (class j vs **all** rest), `k×(n+1)` parameters; predict `argmax_j h⁽ʲ⁾(x)`. Drawbacks: greedy/heuristic; **imbalanced splits** (1 vs k−1).

## Part B

**B1.** (§6–7)

| Point | y | w·x | ŷ | update? | new w |
|---|---|---|---|---|---|
| P1 (1,2,1) | +1 | 0 | +1 (sign(0)=+1) | no | (0,0,0) |
| P2 (1,−1,1) | −1 | 0 | +1 | **yes**: w −= (1,−1,1) | (−1,1,−1) |
| P3 (1,0,−2) | −1 | −1+0+2 = 1 | +1 | **yes**: w −= (1,0,−2) | (−2,1,1) |
| P1 | +1 | −2+2+1 = 1 | +1 | no | (−2,1,1) |
| P2 | −1 | −2−1+1 = −2 | −1 | no | (−2,1,1) |
| P3 | −1 | −2+0−2 = −4 | −1 | no | (−2,1,1) |

(b) **w = (−2, 1, 1)**, **2 updates**. (c) `α = (0, 1, 1)`: `Σαᵢy⁽ⁱ⁾x⁽ⁱ⁾ = (−1)(1,−1,1) + (−1)(1,0,−2) = (−2,1,1)` ✓.

**B2.** (§10) Requirements: (0,0)→0: `w₀ < 0`*; (0,1)→1: `w₀+w₂ ≥ 0`; (1,0)→1: `w₀+w₁ ≥ 0`; (1,1)→0: `w₀+w₁+w₂ < 0`. Adding the middle two: `2w₀+w₁+w₂ ≥ 0`, i.e. `w₀+w₁+w₂ ≥ −w₀ > 0` — contradicting the fourth. ∎ (*with `step(z)=1 iff z≥0`; strict/non-strict placement may swap but the contradiction is identical.) Best achievable: **3/4 correct → 25% error** (computer-verified).

**B3.** (§14–15) (a) `x·z = 1·3 + 2·1 = 5`; `K = 5² = **25**`. (b) `φ(x) = (1, 4, 2√2)`, `φ(z) = (9, 1, 3√2)`; dot = `9 + 4 + 12 = **25**` ✓. (c) Kernel ≈ 4 ops vs naïve ≈ 11 ops (2 mults + 1 add + 1 square vs building two 3-vectors + 3 mults + 2 adds). (d) `784 + 784 + 784·783/2 = **308,504** implicit features (O(n²))`; the kernel way costs **O(784)** — time proportional to the original dimension.

**B4.** (§17–18) (a) `f₁ = exp(−1²/(2·2)) = e^(−0.25) ≈ **0.78**`; `f₂ = exp(−3²/4) = e^(−2.25) ≈ **0.11**`. (b) `z = −0.5 + 1·0.78 + 0·0.11 ≈ **0.28** ≥ 0 → predict **1**`. (c) **All m training points** serve as landmarks; each sample becomes an **m-vector** of similarities `f⁽ⁱ⁾ ∈ ℝᵐ` (with `fᵢ⁽ⁱ⁾ = 1`).

## Part C

**C1.** **False.** Non-separable data ⇒ it **never** converges — there's always a misclassified point. (§8)

**C2.** **True.** Prediction is `sign(Σⱼαⱼy⁽ʲ⁾(x⁽ʲ⁾·x))` and updates only touch α — that's the kernelization criterion. (§7, §13)

**C3.** **False.** The RBF's implicit feature space is **infinite-dimensional** (Taylor expansion of the exponential). (§17)

**C4.** **True.** σ² divides the squared distance — larger σ² ⇒ slower decay ⇒ wider, smoother influence. (§17–18)

**C5.** **False.** **Two** rows change: the correct class gets `+x`, the wrongly-predicted class gets `−x`. (§21)

## Part D

**D1.** (§7, §13–14, §19) Every update adds `y⁽ⁱ⁾x⁽ⁱ⁾` to w; starting from 0, after training w is the sum of all applied updates: `w = Σᵢ αᵢy⁽ⁱ⁾x⁽ⁱ⁾` with αᵢ = update count of point i. Prediction: `ŷ = sign(w·x) = sign(Σᵢ αᵢy⁽ⁱ⁾(x⁽ⁱ⁾·x))` — x appears **only** in dot products, and training in dual form also only compares `x⁽ʲ⁾·x⁽ⁱ⁾` (the kernelization criterion). The primal form stores w in *feature space* — with an implicit φ that vector may be huge or infinite, so it can't be materialized. Kernelized prediction: `ŷ = sign(Σⱼ αⱼy⁽ʲ⁾K(x⁽ʲ⁾, x))`.

**D2.** (§10–11) **Fix 1 (this lecture):** keep one linear layer, add **computed features** — `ψ(x) = (1, x₁, x₂, x₁x₂)`, `w = (−0.5, 1, 1, −2)` solves XOR; generalized, this becomes implicit feature maps = the **kernel philosophy**. **Fix 2 (L08):** **stack** perceptrons — `XOR = AND(OR(x₁,x₂), NAND(x₁,x₂))`, a 2-layer network whose hidden layer *learns* the features; this is the **deep-learning philosophy**. Same wall, two doors — 1969's Minsky/Papert critique led to both.

**D3.** (§21) (a) Scores: `w⁽¹⁾·x = 0+1+2 = 3`, `w⁽²⁾·x = 1−1+0 = 0`, `w⁽³⁾·x = 0+0+4 = 4` → `ŷ = argmax = 3` ≠ y=2. (b) Rule: `w^(y) += x`, `w^(ŷ) −= x` → `w⁽²⁾ = (2,0,2)`, `w⁽³⁾ = (−1,−1,0)` (w⁽¹⁾ unchanged). (c) New scores: 3, **6**, −2 → argmax = 2 = y ✓ (one update fixed it — not guaranteed in general). (d) Between c and c′: predict c iff `w⁽ᶜ⁾·x > w⁽ᶜ′⁾·x` ⟺ `(w⁽ᶜ⁾−w⁽ᶜ′⁾)·x > 0` — a hyperplane, so yes, **linear**.

---

*Self-grade, then reread the cited § in `AML_L07_Ultimate_Reference.md` for any miss. All numerical answers are computer-verified (NumPy).*
