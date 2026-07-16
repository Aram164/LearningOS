# DL Learning Plan — AMLS Project Support (Two-Phase)

> **Created:** 2026-06-10 (KW 24) by Hub Chat (brain)
> **Purpose:** Turn Aram's YouTube playlist + Nielsen's *Neural Networks and Deep Learning* (NNDL) + curated additions into a learning plan that (Phase 1) directly serves AMLS Tasks 1.3/1.4 + report, and (Phase 2) builds the full DL foundation for the AMLS exam and DL 1 prep.
> **Supersedes:** the "DL Supplement" table in SEMESTER-STATUS §3 (which was deprioritized KW 23). This plan replaces it with a phased version that respects the deprioritization.

---

## Source Inventory

**Aram's playlist** (`PLcWYxtg2zMR7xx6QDWMR_h7AoiFVozzSX`), identified videos:

| # | Video | Use |
|---|---|---|
| 1 | MIT 6.S191 L1 — Intro to Deep Learning (Amini) | Phase 1 (optional) / Phase 2 core |
| 7 | Brandon Rohrer — How CNNs work, in depth (~25 min) | **Phase 1** — fastest honest explanation of conv/pool/feature maps |
| 11 | MIT OCW — Intro to NNs and DL; Training Deep NNs | Phase 2 — training dynamics depth |

**Given:** [NNDL Ch. 1](http://neuralnetworksanddeeplearning.com/chap1.html) (Nielsen) — free book, chapters 1–6.

**Curated additions (my picks):**

| Resource | Why added |
|---|---|
| [CS231n notes: ConvNets](https://cs231n.github.io/convolutional-networks/) + [Understanding/Visualizing](https://cs231n.github.io/understanding-cnn/) | The standard written reference for exactly your Task 1.4 methods (saliency, occlusion) — readable in under an hour |
| [3Blue1Brown NN series](https://www.youtube.com/playlist?list=PLZHQObOWTQDNU6R1_67000Dx_ZCJB-3pi) (already in HANDOFF) | Videos 1–2 for intuition; video 3 (backprop) is the mental model behind saliency maps |
| [Grad-CAM via PyTorch hooks tutorial](https://pytorch.org/tutorials/) + [Captum library](https://captum.ai/tutorials/) | Ready-made implementations of Task 1.4 methods; Captum has occlusion + saliency built in |
| [torchvision.transforms v2 docs](https://pytorch.org/vision/stable/transforms.html) | Task 1.3 implementation reference |
| Zeiler & Fergus 2014 (occlusion paper) — skim figs only | Where occlusion analysis comes from; one good figure for the report |
| Karpathy — *Neural Networks: Zero to Hero* (micrograd, ~2.5h) | Phase 2 only — backprop from scratch, best single prep for AML L09 |
| AMLS L11 slides 4–13, L12 slides 4–38 | Already on your disk — read EARLY, they are the project's actual playbook |

---

## Constraints This Plan Obeys (from SEMESTER-STATUS)

- **Jun 11 (tomorrow):** Task 1.4 internal deadline; Task 1.3 already overdue (Jun 4)
- **Jun 18:** Seminar presentation (CRITICAL, no buffer) + AMLS report (internal)
- **Jul 15:** AMLS + mlprov submission (mlprov CRITICAL)
- **Jul 23:** AMLS exam
- **Rule:** Phase 1 rides *inside* the P-task hours already budgeted in §7 (it IS project work, not extra theory). It never displaces seminar or mlprov hours. Phase 2 is gated: starts only after Jul 15.

---

# PHASE 1 — Task-Driven Core (Jun 10 → Jun 18, ~8–10h total)

Everything here exists to let you (a) finish Tasks 1.3/1.4 and (b) write report sections that sound like you understand what you built. Learn-by-doing order, not textbook order.

## Block P1-A: Augmentation crash course → Task 1.3 (Jun 10–12, ~3h study + coding)

| ID | Do | Time | Output |
|---|---|---|---|
| DL.P1.A1 | Read **AMLS L11 slides 4–13** (on disk). This is the literal playbook: geometric transforms, color jitter, cutout, AutoAugment. | 30m | List of 4–6 candidate augmentations matched to `validation_augmented/` degradations |
| DL.P1.A2 | **Rohrer — How CNNs work, in depth** (playlist #7). Watch once at 1.25×. Gives you the vocabulary (feature maps, pooling, invariance) to explain WHY augmentation helps a CNN. | 25m | Can answer: "why does a flipped image still classify correctly?" |
| DL.P1.A3 | Skim **torchvision.transforms v2 docs** while implementing P.1.3.2–1.3.3. Reference, not study. | 30m | Working augmentation pipeline |
| DL.P1.A4 | Bias-variance recap from your own `Plans/ML/foundations/AML/my notes/lect02 KNN-classifier/AML_L02_Ultimate_Reference.md`: augmentation = variance reduction. One paragraph of report ammunition. | 20m | Report sentence: *"Augmentation artificially increases training diversity, reducing variance without adding bias (cf. AML L02)"* |

## Block P1-B: Explainability crash course → Task 1.4 (Jun 11–15, ~4h study + coding)

| ID | Do | Time | Output |
|---|---|---|---|
| DL.P1.B1 | Read **AMLS L12 slides 4–19** (occlusion) + **20–38** (LIME/SHAP). On disk. The exam asks about occlusion (Q4c) — double ROI. | 45m | Method choice for P.1.4.1 |
| DL.P1.B2 | **3B1B video 3 (backprop)** — only the first half. The mental model: saliency map = "backprop all the way to the input pixels". | 20m | Intuition for DL.P1.B4 |
| DL.P1.B3 | **CS231n "Understanding and Visualizing ConvNets"** notes. Saliency + occlusion in written form, with figures you can paraphrase for the report. | 40m | Report-ready descriptions of both methods |
| DL.P1.B4 | **Captum tutorial** (Saliency + Occlusion classes) OR hand-roll: `input.requires_grad_()`, `score.backward()`, plot `input.grad`. Hand-rolling is ~30 lines and better for the report. | 1h | Working saliency + occlusion on your CNN |
| DL.P1.B5 | Skim **Zeiler & Fergus 2014 figures** (occlusion heatmaps) + AMLS L12 **Clever Hans** slide. Frame your critical discussion (P.1.4.5): is the model reading image content or generation artifacts? | 30m | The critical-discussion paragraph that separates 15/20 from 20/20 |

## Block P1-C: Report vocabulary backfill (Jun 14–17, ~2h, droppable under seminar pressure)

| ID | Do | Time | Output |
|---|---|---|---|
| DL.P1.C1 | **NNDL Ch. 1** — targeted read: perceptrons → sigmoid neurons → gradient descent sections. Skip the MNIST code walkthrough. This is your requested source, used surgically. | 1h | Can write: what a layer computes, what the loss measures, what GD does |
| DL.P1.C2 | **6.S191 L1** (playlist #1) at 1.5× — ONLY if seminar is under control. Covers loss → GD → backprop → regularization in DL framing; direct vocabulary for report §3. | 45m | Optional polish |

**Phase 1 exit test (self-check):** Can you explain, in 2–3 sentences each, without notes: (1) why your augmentations were chosen and why they reduce overfitting; (2) what a saliency map computes mathematically; (3) what occlusion analysis shows that saliency doesn't; (4) one way your explanations could be misleading (Clever Hans)? If yes → the report sections will write themselves.

---

# PHASE 2 — Full DL Foundation (after Jul 15, ~22–28h)

Dual purpose: AMLS exam (Jul 23) + AML exam Block F.L/F.M + DL 1 masters prep. Gate: **AMLS + mlprov submitted.** Between Jul 15–23, do only Blocks 2A–2C (exam-relevant); 2D after the exam.

## Block 2A: Neural net fundamentals (~6h) — maps to F.L, AML L08

1. **3B1B videos 1–4** (full series, ~1.5h) — intuition layer
2. **NNDL Ch. 1 complete + Ch. 2** (backprop derivation, ~3h) — rigor layer
3. **6.S191 L1** full, if not done in P1-C2 (~1h) — DL framing

## Block 2B: Backprop by hand (~4h) — maps to F.L, AML L09, exam favorite

1. **Karpathy micrograd** (Zero to Hero #1, ~2.5h) — build autograd from scratch; after this, `loss.backward()` is never magic again
2. Work one backprop example by hand against **AML L09 slides** (~1.5h)

## Block 2C: CNNs in depth (~6h) — maps to F.M, AML L10, your actual project model

1. **Rohrer in-depth** rewatch (25m) + **6.S191 L3 Deep Computer Vision** (~1h)
2. **NNDL Ch. 6** (deep convolutional nets, ~2h)
3. **CS231n ConvNet notes** (~1.5h) — parameter counting, receptive fields (exam-style material)
4. Re-derive your project CNN's parameter count + output shapes layer by layer (~1h) — turns your own code into exam prep

## Block 2D: Training dynamics + labs (~6–8h) — DL 1 prep, post-exam

1. **MIT OCW — Training Deep NNs** (playlist #11, ~1h) — initialization, vanishing gradients, batch norm
2. **NNDL Ch. 3** (cross-entropy, softmax, regularization, ~2h) — closes the loop on why CrossEntropyLoss + AdamW + weight decay
3. **6.S191 Lab 1 + Lab 2** (~3–4h) — hands-on; Lab 2 (facial detection) is closest to your project domain
4. Optional: **NNDL Ch. 5** (why deep nets are hard to train) — pairs with the OCW lecture

**Phase 2 exit test:** backprop a 2-layer net by hand; count parameters of your project CNN from memory; explain Adam vs SGD; explain vanishing gradients + two mitigations.

---

## What I Deliberately Left Out

- **LIME/SHAP implementation** — read the L12 slides (P1-B1) but don't implement unless the team requires it; occlusion + saliency satisfy the exercise spec at lower cost
- **NNDL Ch. 4** (universality proof) — beautiful, zero exam/project ROI
- **6.S191 L2/L4–L7** — stays deferred to DL 1, per KW 21 decision
- **Anything new before Jun 18 beyond Blocks P1-A/B** — the seminar owns those hours

## Tracking

Log completions in SEMESTER-STATUS §10 using the IDs above (DL.P1.A1 … DL.P2 blocks). Phase 1 items can be logged as part of P.1.3.x / P.1.4.x sessions since they're embedded in project work.
