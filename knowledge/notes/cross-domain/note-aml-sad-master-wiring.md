---
id: note-aml-sad-master-wiring
type: note
title: "AML × SaD — Master Wiring"
created: "2026-06-10"
role: crosswalk
state: evolving
authorship: mixed
concepts: [concept-maximum-likelihood, concept-cross-entropy, concept-mean-squared-error,
  concept-logistic-regression, concept-sigmoid, concept-decision-boundary,
  concept-naive-bayes, concept-laplace-smoothing, concept-gaussian-naive-bayes,
  concept-conditional-probability, concept-bayes-theorem, concept-gradient-descent,
  concept-adam-optimizer, concept-convexity, concept-feature-scaling,
  concept-perceptron, concept-kernel-trick, concept-xor-problem, concept-neural-network,
  concept-softmax, concept-backpropagation, concept-chain-rule, concept-weight-decay,
  concept-dropout, concept-early-stopping, concept-bias-variance-tradeoff,
  concept-k-nearest-neighbors, concept-classification-metrics, concept-hypothesis-testing,
  concept-entropy, concept-information-gain, concept-decision-trees, concept-random-forest,
  concept-bootstrap, concept-linear-regression, concept-normal-equation, concept-regularization]
sources: [source-aml-ss26-lectures, source-sad-ss26-lectures, source-islp,
  source-statquest, source-3b1b-neural-networks]
---

> **Migration note (2026-07-17, Stage-1 pilot):** body preserved verbatim from
> `Plans/ML/foundations/reference/AML-SaD_Master_Wiring.md` (legacy tree). The
> concept relations of §2–§3 now live canonically in `knowledge/concept-relations.yaml`;
> the slide-verified source judgments (§4 corrections, per-lecture scopes) live
> canonically as evaluations on `source-aml-ss26-lectures` / `source-sad-ss26-lectures`.
> Companion-doc mapping: Regression Bridge → `note-regression-sad-aml-islp-bridge`;
> AML L07 unit → `note-aml-l07-linear-classifiers` (+ exercise bank, mock exam);
> the L02 reference, the SaD 06–10 deep plan and the AML book crosswalk are still
> legacy files (Stage 2).

# AML × SaD — Master Wiring

*The single spine connecting both modules. Every AML lecture ↔ every SaD lecture ↔ ISLP, at concept level.*
*Created KW 24 (Jun 10, 2026) | Built by reading all AML L01–L11 and SaD 01–15 slide decks directly.*
*Companions (the "deep layers" — this doc wires, they drill):*
- `Plans/ML/foundations/AML/my notes/lect02 KNN-classifier/AML_L02_Ultimate_Reference.md` — k-NN, bias-variance, CV, metrics (Block D; part of the L02 unit)
- `Plans/ML/foundations/reference/Regression_SaD-AML-ISLP_Bridge.md` — regression, the SaD 03 ↔ AML L03/L04 bridge (Block E + H)
- `Plans/Math/sad/SaD/notes/SaD_06-10_Probability-Inference_DeepPlan.md` — probability & inference core (Blocks G + J)
- `Plans/ML/foundations/AML/my notes/AML_Book-Concept-Crosswalk_L02-L10.md` — every AML L02–L10 concept → exact book section/page in 7 sources, scope-flagged (Blocks D–M; extended to L07–L10 KW 27)

---

## 0. How to use this document

The two modules are **one course taught by two professors**. SaD (Leser/Akbik) teaches the statistics and the *why*; AML (Schäfer) teaches the loss-minimization machinery and the *how*. Studied separately they feel like two messes; wired together, every topic is studied **once, properly, for both exams**.

This doc has five jobs:

1. **§1 The full module map** — every lecture pair, wiring strength, where the deep doc lives.
2. **§2 The four pipelines** — the semester is really four concept chains, not 26 lectures. Two already have deep docs; the two new ones (Classification, Neural Networks) are wired here in full.
3. **§3 The cross-wire registry** — all "same idea, both modules" links with exact slide references. This is the highest-value section: spotting these is how studying one module studies the other.
4. **§4 Corrections** — places where the existing plans (Chat1, dependency graph) don't match what the 2026 slides actually teach. Found by reading the decks.
5. **§5 Wired study sequences** — session-by-session orders for the not-yet-studied blocks (F, I, K, L, M), interleaving SaD↔AML at the right points.

**Rule of thumb that falls out of the wiring:** *SaD first when the topic is statistical (probability, Bayes, trees), AML first when the topic is optimization (logistic regression, perceptron, MLP) — and SaD 15 always sandwiched between AML L07 and L09.*

---

## 1. The full module map

### 1.1 AML lecture → SaD twin → ISLP → Block

| AML | Topic (verified from slides) | SaD twin | ISLP | Block | Wiring strength | Deep doc |
|---|---|---|---|---|---|---|
| **L01** | What is ML, history, supervised/unsupervised | SaD 11 (sl. 1–22) | 2.1 pp 15–19 | B ✅ | ◐ same ground, two voices | — |
| **L02** | k-NN, bias-variance, CV, generalization | SaD 13 (algorithm) + SaD 11 (sl. 23–47) | 2.1–2.2, 5.1 | D | ● **strong** — SaD gives algorithm + metrics, AML gives theory | AML_L02_Ultimate_Reference |
| **L03** | Linear regression, MSE, derivative=0 | SaD 03 (sl. 1–16) | 3.1 | E | ● **strongest in the semester** — same minimization, scalar vs matrix | Regression Bridge (Tier 1) |
| **L04** | Design matrix, normal equation, polynomial features, Ridge/Lasso | SaD 03 (sl. 17–37: MLR + GD) | 3.2, 3.3.2, 6.2 | E + H | ● **strong** — SaD's k=(AᵀA)⁻¹Aᵀy *is* AML's w=(XᵀX)⁻¹Xᵀy | Regression Bridge (Tiers 2+5) |
| **L05** | Logistic regression: decision boundary, sigmoid, **MLE → cross-entropy loss** (full derivation, sl. 40–62) | SaD 04 (cond. prob., Bayes) + SaD 14 (the generative rival) | 4.1–4.3 | F + I | ● **strong** — both compute P(class\|x); plus L05's loss derivation is SaD 08's MLE engine re-run with Bernoulli instead of Gaussian | **this doc, §2-C** |
| **L06** | GD/SGD/mini-batch, learning rate, feature scaling, **Adam, Newton/Hessian, convexity proofs** | SaD 03 (sl. 29–37 GD intro) + SaD 08 (z-normalization) | (10.7) | J (E seed) | ◐ SaD plants the seed; AML grows the whole tree | Regression Bridge (Tier 1.6) + this doc §3.9–3.11 |
| **L07** | Perceptron (primal+dual), **kernel trick, RBF kernel, multi-class (OvR, multiclass perceptron)** — ⚠️ **no SVM** (see §4.1) | SaD 15 (sl. 1–12: perceptron as 1-neuron ANN) | 9.3.2 (kernels, optional) | K | ◐ perceptron shared; kernels AML-only | this doc, §2-D |
| **L08** | MLP, forward pass, XOR solved, activations, softmax output, **metrics: confusion matrix, precision/recall/F1, micro/macro/weighted** | SaD 15 (sl. on 1L-ANN = MLR, MLP, softmax) + SaD 01/11 (metrics!) | 10.1–10.2 | L (+D3b) | ● **strong** — and the metrics section is a literal repeat of SaD 11 (see §3.13) | this doc, §2-D |
| **L09** | Backprop: computation graphs, chain rule, worked example, regularization (L2/Frobenius, dropout, early stopping), double descent, vanishing/exploding gradients | SaD 15 (backprop overview) | 10.7 | L | ◐ AML derives, SaD overviews — read SaD's version as the warm-up | this doc, §2-D |
| **L10** | CNNs: convolution, filters, padding, stride, pooling, AlexNet | — (none) | 10.3 | M | ○ AML-only | this doc, §5.4 |
| **L11** | RNNs: embeddings, hidden state, unrolling, BPTT, vanishing grads, GRU, LSTM | — (none) | 10.5 | M | ○ AML-only | this doc, §5.4 |

● = study together as one unit · ◐ = one side leads, other reinforces · ○ = single-module topic

### 1.2 SaD lecture → AML twin (reverse map, for the SaD exam)

| SaD | AML twin | Coverage status |
|---|---|---|
| 01 Introduction | (AML L08 metrics section reuses precision/recall) | ✅ Block A |
| 02 Basics | foundation for every loss | ✅ Block A |
| 03 Correlation & Regression | **L03 + L04 + L06** | Bridge doc, Block E |
| 04 Probability & Naïve Bayes | **L05** (logistic = discriminative rival) | §2-C below |
| 05 Combinatorics | — SaD-only | Block G |
| 06 Random Variables | notation layer under all of ISLP/AML | Deep plan, Block C+G |
| 07 Discrete Distributions | (Bernoulli → logistic loss; multinomial → SaD 14) | Deep plan, Block G |
| 08 Normal & CLT & MLE | **L03/L05 loss functions** (MLE engine), L06 (z-norm) | Deep plan, Block G |
| 09 Estimation | ISLP 3.1.2 (SE/CI on β̂) | Deep plan, Block J |
| 10 Testing | model comparison; FP/FN ↔ Type I/II | Deep plan, Block J |
| 11 Data Science Intro | **L01 + L02 + L08-metrics** | ✅ Blocks B+D |
| 12 Tree-Based | — SaD-only (but bagging ↔ bias-variance) | §5.3 below |
| 13 Similarity-Based | **L02** | ✅ Block D |
| 14 Probability-Based (NB extensions) | **L05** rival; Gaussian NB uses SaD 08 | §2-C below |
| 15 Neural Networks | **L07 + L08 + L09** | §2-D below |

---

## 2. The four pipelines

The 26 lectures collapse into four concept chains. Each chain is one continuous argument across both modules.

### Pipeline A — Regression (SaD 02→03 → AML L03→L04 → ISLP 3, 6.2)
**Status: deep-wired.** Read `Plans/ML/foundations/reference/Regression_SaD-AML-ISLP_Bridge.md`. Nothing to add here; the bridge's Tier structure (0–5) is the canonical treatment.

### Pipeline B — Probability → Inference (SaD 04→05→06→07→08→09→10)
**Status: deep-wired.** Read `Plans/Math/sad/SaD/notes/SaD_06-10_Probability-Inference_DeepPlan.md`. One continuous argument: random variable → distributions → Normal/CLT/MLE → estimation → testing.

### Pipeline C — Classification (NEW deep wiring)

**The chain:** SaD 04 (Bayes, Naïve Bayes) → SaD 14 (NB extensions) → AML L05 (logistic regression) → AML L06 (how its loss is minimized) → ISLP 4.1–4.3.

**The single organizing idea: two ways to get P(class | x).**

| | Generative (SaD's way) | Discriminative (AML's way) |
|---|---|---|
| Model | Naïve Bayes: P(c\|x) ∝ P(c)·ΠP(xᵢ\|c) | Logistic regression: P(y=1\|x) = σ(w·x) |
| What it models | How each class *generates* features | The decision boundary *directly* |
| Trained by | Counting relative frequencies (+ smoothing) | Minimizing cross-entropy via gradient descent |
| Home | SaD 04 sl. ~40+, SaD 14 sl. 6 | AML L05 sl. 21–35 |
| Multi-class | argmax over classes (SaD 14 sl. 6) | softmax / One-vs-Rest (AML L07/L08) |

**Concept tiers (in dependency order):**

**Tier C0 — conditional probability & Bayes (SaD 04).** P(A|B), multiplication rule, Bayes' theorem, independence. *AML payoff:* AML L05 sl. 30–32 interprets σ(w·x) as the conditional probability p_w(y=1|x) — the object itself is defined in SaD 04. Without it, "the network outputs a probability" is just words.

**Tier C1 — Naïve Bayes + its three patches (SaD 14).**
1. **Laplace smoothing** (sl. 8–10): unseen feature/class combos give P=0 and kill the whole product → add pseudocount k: P(fᵢ=v|c) = (count+k)/(count(c)+k·dom(f)). *Cross-wire:* this is regularization-thinking — preventing extreme parameter estimates from small samples — before AML ever says the word "regularization."
2. **Continuous features → Gaussian NB** (sl. 14–18): assume each feature ~ N(μ_c, σ_c²) per class, estimate μ,σ from data, use the **SaD 08 Normal density** as P(x|c). *This is SaD 08 doing classification work.*
3. **Count features → Multinomial NB** (sl. 19–23): document = bag of words, P(d|c) multinomial; log-space trick log P(c|d) ~ log P(c) + Σ nᵢ log pᵢ. *Uses the multinomial distribution flagged in SaD 07's outlook.*
4. Outlook: Bayesian networks, Markov blanket (recognize, don't drill).

**Tier C2 — the logistic regression construction (AML L05 sl. 5–35).** The slide deck's own 3-step story is worth reproducing: (1) linear regression + threshold fails (outlier sensitivity, sl. 6–7); (2) a separator h_w(x)=w·x=0 works but distance is an unbounded "confidence" (sl. 8); (3) squash with σ(z)=1/(1+e⁻ᶻ) → bounded [0,1], interpret as probability (sl. 9, 22–32). Decision boundary geometry: w·x=0 is a hyperplane, scale-invariant (sl. 20); non-linear boundaries via basis expansion — fit a *circle* with x₁²+x₂² features (sl. 33–34, same trick as AML L04 polynomial regression).

**Tier C3 — ⭐ the loss: MLE → cross-entropy (AML L05 sl. 39–62).** The deepest cross-wire of the whole pipeline:
- Want: maximize p_w(y|x) per sample → cost = h_w(x) if y=1, 1−h_w(x) if y=0.
- Product over samples ℒ(w) = Π cost → **take log** (monotone, sl. 46) → sum of ln cost.
- Combined form: **L(w) = −(1/m) Σ [y ln h_w(x) + (1−y) ln(1−h_w(x))]** — the cross-entropy loss.
- Gradient: dL/dw = (1/m) Xᵀ(σ(Xw) − y) — *formally identical to linear regression's gradient with σ inserted* (L06 sl. 19 shows both in one frame).
- No closed form (sl. 67) → gradient descent is now *necessary*, not optional. MSE must NOT be used (non-convex for σ, sl. 53); cross-entropy is convex.

**The aha:** SaD 08 (sl. 29–36) showed: Gaussian noise + MLE ⟹ **MSE**. AML L05 shows: Bernoulli labels + MLE ⟹ **cross-entropy**. *Same engine, different distribution.* One derivation pattern explains both loss functions of the entire semester. (SaD 11 sl. ~15 lists exactly these two losses — now you know where both come from.)

**Tier C4 — interpretation layer (ISLP 4.1–4.3).** Log-odds: ln(p/(1−p)) = w·x — logistic regression is *linear regression on the log-odds*. Coefficient interpretation, multiple logistic regression, multinomial (softmax) — ties to ISLP 3's inference machinery (SE, z-stat on coefficients = the SaD 09/10 layer again).

**Connection self-test (both exams):**
- [ ] Compute a Naïve Bayes posterior with Laplace smoothing (k=1) on a 4-feature table (SaD exam staple, UE6)
- [ ] Gaussian NB: write P(x|c) using N(μ_c,σ_c²) and explain what's estimated from data
- [ ] Derive the cross-entropy loss from "maximize Π p_w(y|x)" in 4 steps (product → log → sum → ×(−1/m))
- [ ] Show dσ/dz = σ(1−σ), then show dL/dwⱼ = (1/m)Σ(h_w(x)−y)xⱼ
- [ ] Explain in 3 sentences why NB and logistic regression can disagree on the same data (generative vs discriminative)
- [ ] State why MSE is forbidden for logistic regression (non-convexity) and what convexity buys GD

🎥 [StatQuest — Logistic Regression](https://www.youtube.com/watch?v=yIYKR4sgzI8) · [StatQuest — Naive Bayes, Clearly Explained](https://www.youtube.com/watch?v=O2L2Uv9pdDA) · [StatQuest — Gaussian Naive Bayes](https://www.youtube.com/watch?v=H3EjCKtlVog) · MLE refresher: [Maximum Likelihood — StatQuest](https://www.youtube.com/watch?v=XepXtl9YKwc) (watch again with Bernoulli in mind)

### Pipeline D — Neural Networks (NEW deep wiring)

**The chain:** SaD 03 (GD) → AML L06 (GD formal) → SaD 15 sl. 1–12 (1L-ANN) → AML L07 (perceptron + XOR problem) → AML L08 (MLP + XOR solved) → SaD 15 sl. 12+ (MLP/backprop overview) → AML L09 (backprop full) → ISLP 10.

**The single organizing idea: a neural network is regression, stacked, with non-linear squashing — and you already own every ingredient.**

| Ingredient | Where you learned it | Where the NN uses it |
|---|---|---|
| Weighted sum w·x + b | SaD 03 / AML L03 (the hypothesis) | every single neuron |
| Sigmoid σ | AML L05 | classic hidden/output activation |
| Softmax | SaD 15 (as "differentiable argmax", see §3.6) | multi-class output layer |
| Gradient descent / SGD | SaD 03 sl. 29–37 → AML L06 | the training loop |
| Chain rule | calculus prereq (Bridge Tier 0) | backprop *is* the chain rule, cached |
| MSE / cross-entropy | SaD 08-MLE / AML L05-MLE | the loss at the output |
| L2 regularization | AML L04 (Ridge) | Frobenius-norm weight decay (L09) |
| Bias-variance | Block D | why dropout/early stopping exist |

**Concept tiers:**

**Tier D0 — the equivalence (SaD 15 "Remember MLR?" slide — the most important slide in SaD).** f_N(X) = φ(b + Wx); **drop φ and this is exactly multivariate linear regression**. Corollary stated on the slide: a 1L-ANN with identity activation is trained *like MLR, by gradient descent*. Everything from Pipeline A applies. Also here: one-hot encoding for classes, logits, and softmax as the differentiable replacement for Naïve Bayes' argmax.

**Tier D1 — the perceptron (AML L07 sl. 10–26 + SaD 15 perceptron slides).** σ → sign: ŷ = sign(w·x) ∈ {−1,+1}. Loss = "amount by which wrong": L = −y(w·x) if misclassified, else 0 (convex, sub-gradient). Update rule **w ← w + y⁽ⁱ⁾x⁽ⁱ⁾** for misclassified points = SGD with the sub-gradient −yx. Convergence guaranteed iff linearly separable; never converges otherwise. **Dual form:** w = Σ αᵢy⁽ⁱ⁾x⁽ⁱ⁾ where αᵢ = #updates on point i — predictions become sums of dot-products → *this is what makes it kernelizable* (Tier D2).

**Tier D2 — kernels (AML L07 sl. 41–72, AML-only).** Non-linear boundary = linear boundary in a feature space φ(x). Explicit φ for degree-2 polynomials is O(n²)-dimensional → **kernel trick**: K(x,z) = (1+x·z)^d ≡ φ(x)·φ(z) computed in O(n). RBF/Gaussian kernel K(x,z)=exp(−‖x−z‖²/2σ²) = similarity to landmarks (= all training points) → infinite-dimensional φ. *Cross-wires:* the Gaussian form is literally SaD 08's bell curve used as a similarity measure; "similarity to training points" is k-NN thinking (SaD 13) smuggled into a linear classifier. Multi-class: One-vs-Rest + multiclass perceptron (argmax over k weight vectors).

**Tier D3 — XOR, the hinge of history (AML L07 sl. 27–37 + L08 sl. 7–13 + SaD 15 XOR slide).** Perceptron does AND/OR/NAND but provably not XOR (Minsky/Papert 1969 → AI winter — both decks tell this story). Two fixes, *compare them deliberately*:
1. AML L07's fix: non-linear *feature* x₁x₂ (stay 1-layer, change the features) → kernel philosophy.
2. AML L08 + SaD 15's fix: **stack** — XOR = AND(OR(x₁,x₂), NAND(x₁,x₂)), a 2-layer perceptron program; SaD 15 does the same with ReLU. → deep-learning philosophy: *learn* the features (hidden layer = learned non-linear features a⁽¹⁾).

**Tier D4 — the MLP forward pass (AML L08 sl. 15–33 + SaD 15 MLP slides).** Layer recipe: **a⁽ˡ⁾ = g(W⁽ˡ⁾a⁽ˡ⁻¹⁾ + b⁽ˡ⁾)** (SaD 15 writes the same thing as Xⁱ = gᵢ(Wⁱ·Xⁱ⁻¹)). AML L08 and L09 run a *numerically identical worked example* (W⁽¹⁾=[[1,2],[1,2]], b⁽¹⁾=[−2,2], x=[1,0] → a⁽¹⁾=[0.269,0.953] → ŷ=0.94) — do it by hand once in L08, it carries straight into L09's backprop example with the same numbers. Key facts: g must be non-linear (else the whole stack collapses to one linear map — proven in both L08 sl. 41 and SaD 15); g_out is task-dependent (identity=regression, sigmoid=binary, softmax=multiclass — sigmoid-per-output for multi-*label* vs softmax for multi-*class*, L08 sl. 43–51); parameter counting n·l + (k−1)·l² + l·m (SaD 15 gives the formula — SaD exam target); universal approximation theorem (SaD 15, with the honest caveats: exponential width, no learning guarantee).

**Tier D5 — backprop (AML L09 + SaD 15 overview).** Read SaD 15's 3-sentence version *first* (forward → error at output → push back layer by layer), then AML L09's full machinery: computation graphs (nodes = atomic ops; forward computes loss, backward computes ∇L, intermediate results cached — *this is exactly what PyTorch's `loss.backward()` does*, L09 ends with the same example in PyTorch). The four per-layer rules to memorize: dz⁽ˡ⁾ = da⁽ˡ⁾ ∗ g′(z⁽ˡ⁾); da⁽ˡ⁻¹⁾ = W⁽ˡ⁾ᵀ·dz⁽ˡ⁾; dW⁽ˡ⁾ = dz⁽ˡ⁾·a⁽ˡ⁻¹⁾; db⁽ˡ⁾ = dz⁽ˡ⁾. Needs σ′=σ(1−σ) from Pipeline C. Then training pathology + fixes: vanishing/exploding gradients (λ⁷ argument, L09 sl. 71–74), L2/Frobenius weight decay (= Ridge on matrices), dropout, early stopping, double descent (modern twist on the Block-D U-curve — test risk descends *again* past the interpolation threshold).

**Connection self-test (both exams):**
- [ ] Write f(X)=φ(b+Wx), strike φ, and write the MLR formula next to it (SaD exam: prove the equivalence)
- [ ] Show that 2 linear layers = 1 linear layer (W′x+b′) — why non-linearity is non-negotiable
- [ ] Build XOR twice: once with the x₁x₂ feature (L07-style), once as AND∘(OR,NAND) (L08-style); say which philosophy each represents
- [ ] Run the shared worked example forward by hand (x=[1,0] → 0.94) and one backprop step (dW⁽²⁾=[0.0143, 0.0506])
- [ ] State the four backprop layer rules and identify the chain rule in them
- [ ] Count parameters of a 3-4-4-2 network (with biases)
- [ ] Why softmax instead of argmax? (differentiability — SaD 15's own argument) Why does Σ softmax outputs = 1 matter?
- [ ] Explain dropout and early stopping as bias-variance moves (link to Block D U-curve), and where double descent breaks the classical picture

🎥 [3B1B — Neural networks playlist](https://www.youtube.com/playlist?list=PLZHQObOWTQDNU6R1_67000Dx_ZCJB-3pi) (all 4: what is a NN → GD → backprop → backprop calculus; the single best preparation for AML L08–L09) · [StatQuest — Neural Networks Pt. 1](https://www.youtube.com/watch?v=CqOfi41LfDw) · [StatQuest — Backpropagation Main Ideas](https://www.youtube.com/watch?v=IN2XmBhILt4)

---

## 3. The cross-wire registry

The complete list of "same object, both modules" links — expanded from Chat1's 7 to 18, with slide-level grounding. **When you hit one of these while studying, stop and write the two versions side by side.** That act is the studying.

| # | Cross-wire | Where (A-side) | Where (B-side) | One-liner |
|---|---|---|---|---|
| 1 | x̄ ↔ E[X], s² ↔ Var(X) | SaD 02 | SaD 06 sl. 26/35 | sample ↔ population; unlocks all E[·] notation |
| 2 | Regression line, 3 notations | SaD 03: k=r·s_y/s_x | AML L03 w, ISLP β₁ | k = β₁ = w₁ |
| 3 | Normal equation appears in SaD *first* | SaD 03: k=(AᵀA)⁻¹Aᵀy | AML L04: w=(XᵀX)⁻¹Xᵀy | identical, renamed |
| 4 | **MLE → MSE (Gaussian)** | SaD 08 sl. 29–36 | AML L03 uses MSE unexplained | MSE is a consequence, not a choice |
| 5 | **MLE → cross-entropy (Bernoulli)** ⭐ new | AML L05 sl. 40–62 (full derivation) | SaD 08 MLE idea; SaD 11 lists both losses | the same engine as #4, second output; one pattern → both semester losses |
| 6 | **argmax → softmax** ⭐ new | SaD 14/04: ĉ = argmax P(c)·ΠP(xᵢ\|c) | SaD 15 (explicit: "argmax not differentiable → softmax"); AML L08 softmax layer | softmax is differentiable argmax; the NB decision rule lives on inside every classifier net |
| 7 | Generative vs discriminative | SaD 04/14 Naïve Bayes | AML L05 logistic | both compute P(c\|x); model data vs model boundary |
| 8 | **Gaussian NB runs on SaD 08** ⭐ new | SaD 14 sl. 14–18 | SaD 08 Normal density | per-class N(μ_c,σ_c²) as likelihood |
| 9 | GD: "alternative" → "everything" | SaD 03 sl. 29–37 | AML L06 (SGD, mini-batch, Adam) | L05's no-closed-form makes GD *necessary* |
| 10 | **Feature scaling, three appearances** ⭐ new | SaD 08 z-normalization; SaD 13 distance scaling (min-max, z-norm) | AML L06 sl. 35–45 (mean-norm/scaling for GD convergence) | same μ,σ transform: stats tool, k-NN fairness, GD speed |
| 11 | **Hessian/convexity** ⭐ new | AML L06 bonus: ∇²L = (1/m)XᵀX is PSD ⟹ MSE convex; logistic loss convex | Regression Bridge Tier 0.3 (derivative=0) | why GD on linear/logistic regression cannot get trapped |
| 12 | 1L-ANN = MLR | SaD 15 ("drop φ" slide) | AML L03/L04 + L08 | NNs are stacked regression |
| 13 | **XOR told twice** ⭐ new | AML L07 sl. 27–37 (perceptron limits, feature fix) | AML L08 sl. 7–13 + SaD 15 (stacking fix) | kernel philosophy vs deep-learning philosophy on one toy problem |
| 14 | **Metrics triple-taught** ⭐ new | SaD 01 (contingency) + SaD 11 sl. 23–38 | AML L08 sl. 60–80 (confusion matrix, P/R/F1, micro/macro/weighted) | both exams test it; AML adds multi-class averaging |
| 15 | **Type I/II ↔ FP/FN** ⭐ new | SaD 10 (α, β, power) | confusion matrix (SaD 01/11, AML L08) | the same 2×2 table, inferential vs predictive reading |
| 16 | **Entropy: trees ↔ loss** ⭐ new | SaD 12: H(S)=−Σp log p, information gain | AML L05 cross-entropy −Σ y log ŷ | one formula H; trees *minimize* it by splitting, classifiers by gradient |
| 17 | **Bootstrap → bagging → Random Forest** ⭐ new | SaD 09 (resampling) + SaD 11 (bootstrapping) | SaD 12 (bagging, RF) ↔ Block D bias-variance | RF = variance reduction by averaging; the U-curve in action |
| 18 | **Class imbalance, three rooms** ⭐ new | SaD 13 (k too large kills minority class) | AML L08 (accuracy useless, use F1) + AMLS project (FPR threshold calibration) | same disease, three treatments |

Soft wires worth a margin note: Laplace smoothing ↔ regularization (both tame small-sample extremes); RBF kernel ↔ SaD 08 bell curve ↔ k-NN similarity (SaD 13); Mahalanobis distance (SaD 13 outlook) runs on covariance (SaD 03); dual-form perceptron weights αᵢ ↔ "support points" (the ISLP 9 SVM idea, if you read it); SaD 12 regression trees minimize subset *variance* (SaD 02's s² as a split criterion).

---

## 4. Corrections — where the existing plans don't match the 2026 slides

Found by reading every deck. Fix these before they cost study time:

1. **AML L07 contains no SVM.** Chat1 Block K says "Perceptron + SVM + kernel trick" and maps ISLP 9.1–9.3. The actual deck: perceptron (primal/dual), separability, XOR, kernel trick, polynomial + RBF kernels, multi-class (OvR + multiclass perceptron). **No maximum margin, no support vector machine.** → Block K2 should read "perceptron + kernel trick + multi-class"; ISLP Ch 9 demote to *optional enrichment* (9.3.2 kernels closest to lecture content). The kernel trick is examinable; max-margin appears not to be.
2. **AML L05 is heavier than planned.** Not just "sigmoid + cross-entropy": it contains the full MLE→cross-entropy derivation, the combined/vectorized loss, the partial-derivative derivation, and the no-closed-form result. Block I time estimate should grow ~1h; the payoff is cross-wire #5.
3. **AML L06 goes far past "SGD".** Momentum, RMSProp, **Adam** (the optimizer in your AMLS project code — also S.C4 in AMLS), Newton's method with Hessian, convexity via PSD Hessian, feature scaling. Block J's F.J2 should explicitly include Adam — it double-pays for AMLS exam and project report.
4. **AML L08 has a metrics block** (accuracy/precision/recall/F1 + micro/macro/weighted averaging). F.D3b is *recalled* here; the multi-class averaging part is new and AML-exam-relevant.
5. **AML L09 includes regularization-for-NNs** (Frobenius/L2 weight decay, dropout, early stopping, double descent). Chat1 puts dropout/early stopping in Block H (AML L04) — actually they live in L09. Block H is Ridge/Lasso only; the NN regularization belongs to Block L.
6. **SaD 12 includes regression trees, stacking, and boosting** in addition to ID3/RF — UE7-relevant; the cluster-N5 review should include "variance as split criterion."
7. **SaD 13 includes indexing structures** (kd-trees, k-means trees, M-trees, LSH, metric axioms) — Leser-flavored, plausibly SaD-exam-relevant (metric definition: symmetry, non-negativity, identity, triangle inequality). Block D self-tests don't currently cover metric axioms — add one line.
8. **AML L08's forward-pass example and AML L09's backprop example use the same numbers.** Same W, b, x (→ ŷ=0.94). Do it by hand once in L08, reuse in L09. (SaD 15 uses its own XOR/ReLU example instead — also worth one hand-run for the SaD exam.)

---

## 5. Wired study sequences (the not-yet-studied blocks)

> ⚠️ **Supersession rule (KW 27):** once a lecture has a complete unit in `AML/my notes/lectNN …/`, its **Mini Plan replaces the sequence below for that lecture** (units exist: AML L02–L07 → §5.2's AML-half and §5.3's Session 2 are superseded by the L06/L07 Mini Plans). The SaD halves and the not-yet-built lectures (L08–L11, SaD 04/12/14/15) remain governed by this section.

Each session ≈ 2.5–3h. Rule: **video → SaD slides → AML slides → write the cross-wire → self-test items**. These slot into the F-hours of SEMESTER-STATUS §7 (theory is suppressed until ~KW 26; sequences below are ready when the hours open up — or for Block N exam prep directly).

### 5.1 Block F + I — Classification (Pipeline C), 2 sessions
**Session 1 — the generative side (SaD-led).** SaD 04 in full (probability axioms, conditional P, Bayes, Naïve Bayes spam example) → SaD 14 (smoothing, Gaussian NB, multinomial NB). Write cross-wires #8 (Gaussian NB ← SaD 08) and the smoothing↔regularization note. Do UE3 (probability part). ✅ Checkpoint: NB with Laplace smoothing by hand on a 4-feature table.
**Session 2 — the discriminative side (AML-led).** AML L05 in full — reproduce the three attempts (sl. 5–9), the boundary geometry, then the MLE→cross-entropy derivation *on paper* (cross-wire #5, write it next to SaD 08's MLE→MSE). ISLP 4.1–4.3 for the log-odds reading. ✅ Checkpoint: derive dL/dwⱼ = (1/m)Σ(h−y)xⱼ; explain generative-vs-discriminative in 3 sentences. *(F.I-test + UE6 classification half after Block J's testing part.)*

### 5.2 Block J — GD formal + estimation (1 session for the AML half)
AML L06: GD → SGD → mini-batch → feature scaling (cross-wire #10) → Adam → Newton/Hessian bonus (cross-wire #11). Watch [StatQuest — Stochastic Gradient Descent](https://www.youtube.com/watch?v=vMh0zPT0tLI) first. ✅ Checkpoint: write all three update-rule variants + Adam's two ideas (momentum = EMA of gradients; RMSProp = per-weight learning rates). *The SaD half (09–10) is Sessions 4–5 of the SaD 06–10 deep plan — already specified there.*

### 5.3 Block K — Trees (SaD-only) + linear classifiers, 2 sessions
**Session 1 — trees (pure SaD exam prep).** SaD 12: entropy → information gain → ID3 → pruning (pre/post, validation-set example) → bagging/boosting/stacking → Random Forests → regression trees. Write cross-wires #16 (entropy↔cross-entropy) and #17 (bootstrap→bagging→RF↔bias-variance). UE7 K-means alongside. ✅ Checkpoint: build a tree on a 6-instance set computing IG at each split; explain why RF beats one tree (variance).
**Session 2 — perceptron + kernels (AML-led, corrected scope per §4.1).** AML L07: perceptron loss/update → convergence → dual form → XOR problem → kernel trick (do the 2d worked example: (x·z)² vs φ(x)·φ(z)) → RBF → multi-class. SaD 15 sl. 1–12 right after (perceptron as neuron; cross-wire #12 preview). ✅ Checkpoint: perceptron update rule from the sub-gradient; show K(x,z)=(x·z)² equals φ(x)·φ(z) for φ(x)=(x₁², x₂², √2x₁x₂); XOR non-separability argument.

### 5.4 Block L + M — Neural networks (Pipeline D), 3 sessions
**Session 1 — equivalence + forward pass.** 3B1B video 1 → SaD 15 sl. 1–12 (Tier D0: drop-φ slide, softmax-as-argmax) → AML L08 (XOR solved, forward pass — run the worked example by hand, activations, output layers, multi-label vs multi-class). ✅ Checkpoint: 3-4-4-2 parameter count; XOR as AND(OR,NAND).
**Session 2 — backprop.** 3B1B videos 3–4 → SaD 15 backprop overview (the warm-up) → AML L09: computation graph, the four layer rules, full worked example (same numbers), PyTorch closing. ✅ Checkpoint: one backward pass by hand reproducing dW⁽²⁾=[0.0143,0.0506]; recite the four rules.
**Session 3 — training pathologies + deep architectures.** AML L09 second half: Frobenius regularization, dropout, early stopping, double descent, vanishing/exploding (λ⁷ argument). Then Block M: AML L10 (convolution arithmetic: output size = (n+2p−f)/s+1, pooling, AlexNet) and AML L11 (RNN unrolling, BPTT, GRU/LSTM gates) with ISLP 10.3/10.5. *Project synergy: you've already built a CNN (Task 1.2 ✅) — read L10 as theory-behind-what-you-did; augmentation (Task 1.3) and saliency (Task 1.4) hang off this lecture too (see `Plans/ML/systems/DL-AMLS-Learning-Plan.md` Phase 1).* ✅ Checkpoint: conv output dims for 28×28, 5×5 kernel, stride 1, no padding; LSTM forget gate in one sentence; dropout as variance reduction.

---

## 6. The one-page mental model (pin this)

```
            SaD 01–02 (descriptive: x̄, s², metrics vocabulary)
                       │
        ┌──────────────┴────────────────┐
        ▼                               ▼
  PIPELINE B: Probability        PIPELINE A: Regression
  SaD 04→05→06→07→08             SaD 03 ⇄ AML L03/L04 ⇄ ISLP 3+6.2
  (Bayes → RVs → Normal/CLT)     (k = β₁ = w; normal equation; Ridge/Lasso)
        │            │                  │
        │      MLE engine (SaD 08) ─────┤  Gaussian → MSE
        │            └──────────────────┼─ Bernoulli → cross-entropy (AML L05)
        ▼                               ▼
  SaD 09–10 (estimation,         PIPELINE C: Classification
  testing — the SaD-exam         SaD 04/14 (generative NB)
  inference layer; also            ⇄ AML L05 (discriminative logistic)
  ISLP 3.1.2 on β̂)                 → AML L06 (GD/SGD/Adam trains it)
                                        │
                                        ▼
                                 PIPELINE D: Neural networks
                                 SaD 15 (1L-ANN = MLR; softmax = diff. argmax)
                                   ⇄ AML L07 (perceptron, XOR, kernels)
                                   ⇄ AML L08 (MLP, forward pass)
                                   ⇄ AML L09 (backprop = chain rule + cache)
                                   → AML L10/L11 (CNN, RNN — AML-only)

  SaD-only side-quests (exam-required, no AML twin):
  SaD 05 combinatorics · SaD 12 trees/ID3/RF · UE7 k-means
```

*Everything in this doc verified against: AML L01–L11 decks (Schäfer, SoSe 2025/26), SaD 01–15 decks (Leser/Akbik), ISLP 2nd ed. Maps to Foundations Blocks B–N. Slide numbers from the PDF decks in `AML/` and `SaD/`; pdftotext extractions can shift ±1 slide — trust the content anchor over the number.*
