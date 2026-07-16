# AML Lecture 07 — Mini Learning Plan (Linear Classifiers: Perceptron, Kernel Trick, Multi-Class)

> **📌 Closes step: F.K2** (AML L07) · supports **F.K-test** (perceptron/kernel half; K1 trees + K4 k-means are SaD-side). Log completion in `SESSION-LOG.md` + tick SEMESTER-STATUS §3.

Sequenced study path for L07, in the **lecture's own order** (VL07: linear classifiers → perceptron → separability/XOR → computed features → kernel trick → RBF → multi-class). Each step pairs **concept → lecture video → reading → practice**.

**Primary course material:** `…/SoSe 2026/lecture slides/VL 07-linear-classifiers.pdf` (94 slides).
**Reference:** `AML_L07_Ultimate_Reference.md` (this folder — TOC + self-test).
**Book map:** crosswalk L07 section — `../AML_Book-Concept-Crosswalk_L02-L10.md`.

> L07 is the hinge between the "classic ML" half (L02–L06) and the neural-network arc (L08–L10): the perceptron **is** the single neuron of L08, and the XOR wall motivates both kernels (this lecture) and deep nets (next lecture).
>
> **Reading scope:** ⚠️ **this deck has NO SVM / max margin** — skip ISLP §9.1–9.2 and all "support vector" machinery. Kernels-without-SVM exists in exactly one book source: **CS229 Ch 5** — that's your primary book layer. ESL §4.5.1 is the only classic-book perceptron *algorithm*. ISLP §9.4.2 (One-vs-All, 1 page) covers the multi-class part.
>
> **Prerequisites you already own:** decision-boundary geometry + scale invariance (L05), SGD (L06), basis expansion (L04), Gaussian density (SaD 08), similarity/distance thinking (SaD 13 / L02).

---

## Step 1 — Perceptron: model, loss, update, convergence  (~1.25 h)
[Slides 3–27 · Reference §1–§8]

`ŷ = sign(w·x)`; loss = "amount by which wrong" (convex); sub-gradient `∇L = −yx`; update `w += y·x` on mistakes only; converges iff linearly separable; dual form `w = Σαᵢy⁽ⁱ⁾x⁽ⁱ⁾`.

- 🎥 **Cornell CS4780 — "Perceptron"** (Weinberger) — the closest lecture-format match, incl. the convergence proof · 📝 [written note](https://www.cs.cornell.edu/courses/cs4780/2018fa/lectures/lecturenote03.html).
- 🎥 **MIT 6.036 perceptron unit** (Open Learning Library) — auto-graded practice.
- 📖 **ESL §4.5.1** Rosenblatt's Perceptron Learning Algorithm (p.130) — the rigorous 3 pages: update as SGD on the perceptron criterion, separable-case convergence, the two caveats (many solutions; cycling when non-separable).
- 📖 **CS229 notes §2.2** (p.23) — the perceptron in 2 pages, threshold-vs-sigmoid framing · **Murphy §10.2.5** (p.346) — perceptron = logistic regression with a hard threshold (the cleanest wire back to L05).
- 📝 Do one full **trace by hand**: Bonusblatt 4 Aufgabe 1(d) → check against `AML_BonusSheet04_Solution.md` (this folder).

## Step 2 — Boolean gates & the XOR wall  (~45 min)
[Slides 28–42 · Reference §9–§11]

AND/OR/NAND weight vectors; XOR impossibility proof; Minsky/Papert history; fix #1 = computed feature x₁x₂.

- 🎥 **3B1B NN #1** ("What is a neural network?") — optional warm-up for the neuron picture.
- 📝 Verify all three gate tables by hand (30 s each); write the XOR 4-inequality contradiction once (mock exam D-material).
- 📝 Bonusblatt 4 **Aufgaben 2–3** (separability + step-activation gates) → solution key in this folder.
- 🔗 Cross-wire #13: note fix #1 (features, this lecture) vs fix #2 (stacking, L08) — one sentence each in your notes.

## Step 3 — Kernel trick  (~1.25 h)
[Slides 44–62 · Reference §12–§16, §19]

φ-mapping cost O(n²) → kernelization criterion (x only in dot products — the dual form!) → `K(x,z) ≡ φ(x)·φ(z)` → polynomial kernel `(1+x·z)^d` in O(n) → kernelized perceptron.

- 📖 **CS229 notes Ch 5** ⭐ (p.49–58): §5.1 feature maps → §5.2 LMS with features → §5.3 LMS with the kernel trick → §5.4 properties of kernels ("what makes a valid kernel"). **The** book match — kernels developed without SVM, ending at the kernelized perceptron.
- 🎥 **StatQuest — "The Kernel Trick"** (visual intuition for the implicit mapping).
- 📝 Reproduce the 2d worked example by hand: `(x·z)²` vs `φ(x)·φ(z)` for x=(1,2), z=(3,1) (→ 25 both ways); count the operations.
- 📖 *Optional depth:* **Murphy §17.1–17.1.2** (Mercer kernels, popular kernels, p.567/569) — the reference card for slide 61.

## Step 4 — RBF kernel & landmarks  (~45 min)
[Slides 63–79 · Reference §17–§18]

RBF = Gaussian without normalization; similarity ∈ (0,1]; landmarks = all m training points; σ² = drop-off dial; infinite implicit dimension.

- 🎥 **Andrew Ng — "Kernels I" + "Kernels II"** (Coursera ML, Week 7) — the landmark/similarity construction on slides 68–73 *is* Ng's presentation; closest level-match.
- 📝 Compute K(x,z) for 2–3 pairs and σ² values by hand (e.g. ‖x−z‖²=4, σ²=2 → e^(−1)≈0.368); sketch small-σ vs large-σ boundaries and label which overfits.
- 🔗 Cross-wires: RBF formula = SaD 08's bell curve; landmark similarity = k-NN thinking (SaD 13); σ² = the bias-variance dial (L02's k).

## Step 5 — Multi-class  (~30 min)
[Slides 80–94 · Reference §20–§22]

OvR (k binary models, argmax response) vs multiclass perceptron (joint w ∈ ℝ^{k×(n+1)}, two-row update).

- 📖 **ISLP §9.4.2** One-Versus-All (p.383–384) — 1 page, exact match for OvR.
- 📝 Run one multiclass-perceptron update by hand (3 classes, 1 misclassified point): which two rows change, and in which direction?
- 🔗 Cross-wire #6: argmax over class scores → L08's softmax (differentiable argmax).

## Step 6 — Practice & self-test

See **`AML_L07_Exercise_Bank.md`** (this folder) for the full scoped list. Highlights:

- **Bonusblatt 4 (zusatz-blatt04) Aufgaben 1–2** → ✓ `AML_BonusSheet04_Solution.md` (Aufg. 3–4 lean into L08 — do them as a preview or defer).
- **`AML_L07_Mock_Exam.md`** (75 min, timed) → self-grade with its key.
- ✓ **CS4780 HW2** (perceptron, solutions local) — see the exercise bank for the exact problems.
- Reference §24 self-test as the final gate.

---

### Suggested schedule (~4.5 h)

| Session | Steps |
|---|---|
| 1 | Step 1 (perceptron end-to-end) + Bonusblatt 4 A1 trace |
| 2 | Step 2 (gates + XOR) + Step 5 (multi-class) + Bonusblatt 4 A2–A3 |
| 3 | Steps 3–4 (kernel trick + RBF) + the two by-hand kernel drills |
| 4 | Mock exam (timed) → review; CS4780 HW2 |
