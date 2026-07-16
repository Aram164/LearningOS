# Chat 3: AMLS Project — AI Image Detection Step-by-Step Plan

*Generated: 23 April 2026 (KW 17) | Built from exercise spec + Chat 1/2 theory plans + Bootcamp*
*Updated: 30 April 2026 — theory prerequisites verified against actual AML L01–L11 and AMLS L10–L12 lecture PDFs*
*Status (KW 24, Jun 10): Tasks 1.1 + 1.2 (CNN) ✅. Task 1.3 OVERDUE (Jun 4), Task 1.4 due Jun 11 — renegotiate internal dates with Abdalla. DL theory support for 1.3/1.4: `Plans/ML/systems/DL-AMLS-Learning-Plan.md` Phase 1. Hard deadline: 15 Jul 2026. Internal report: 18 Jun 2026.*

---

## Step ID Convention

All steps in this plan use the prefix **P** (Project). Reference format: **P.{Task}.{Step#}**

| ID | Meaning | Example |
|---|---|---|
| P.1.1.3 | Task 1.1, Step 3 (class distribution analysis) | "Completed P.1.1.3" |
| P.1.2.8 | Task 1.2, Step 8 (implement reference CNN) | "Starting P.1.2.8" |
| P.Report | Report writing phase | "P.Report section 3 done" |
| P.Docker | Docker build + testing | "P.Docker checklist complete" |

**When updating SEMESTER-STATUS.md:** write step IDs exactly as above. This chat (the brain) uses them to track dependencies.

---

## Why This Plan Exists

The AMLS exercise (AI Image Detection, 100 points) is not a "follow a recipe" project — it's an open-ended ML engineering challenge that requires you to make and justify design decisions. The danger is starting to code before you have the conceptual vocabulary, or waiting so long for "perfect theory" that you run out of time. This plan threads the needle: it tells you exactly which theory from Chat 1 (AML/SaD) and Chat 2 (AMLS) you need *before* each task, what you can learn *while* doing the task, and what the Bootcamp already covered so you don't revisit it.

---

## The Exercise at a Glance

**What:** Binary classification — real images (label 0) vs AI-generated images (label 1, merging SD 2.1/SDXL/SD 3/DALL-E 3/Midjourney). Data is in parquet files with binary image columns.

**Constraint that shapes everything:** Maximize recall_ai while keeping the false-positive rate on real images ≤ 20%. CPU-only. Strict time budgets (train.py: 1800s, others: 600s). No pretrained models at runtime. Docker container < 4 GB.

**Deliverables:**

| File | Purpose | Timeout |
|------|---------|---------|
| `clean.py` | Data exploration + cleaning | 600s |
| `prepare.py` | Feature extraction / data prep (NOT for predict split) | 600s |
| `train.py` | Train best Task 2 model | 1800s |
| `predict.py` | Inference → `artifacts/task02/predictions.csv` | 600s |
| `train_augmented.py` | Train robust Task 3 model | 1800s |
| `predict_augmented.py` | Inference → `artifacts/task03/predictions.csv` | 600s |
| `report.pdf` | 8 pages, 10pt, documenting everything | — |

**Grading:** 100% project (exercise is alternative to programming projects). Up to 5 bonus points on the AMLS exam.

**Exam dates:** Jul 23 (4pm), Aug 06 (4pm), Aug 27 (4pm). Project is a prerequisite for exam eligibility.

---

## Team Structure and Workflow

**Team size:** 3 people (task split TBD — discuss in next team meeting)

### GitHub (managed by Abdalla)

- **One stable `main` branch** — always working, always passes Docker build
- **Per-exercise branches:** `task-1.1`, `task-1.2`, `task-1.3`, `task-1.4`
- **Per-participant branches within each task:** e.g., `task-1.2/aram`, `task-1.2/abdalla`, `task-1.2/[third]`
- Merge flow: participant branch → exercise branch → `main` (via PR review)
- `main` should always contain a runnable Docker build

### Overleaf (for report)

- Split report sections by task ownership (whoever implements a task writes its report section)
- One person assembles introduction + conclusion
- Use consistent formatting from day 1 (10pt, 8-page limit)

### Internal Deadlines (finish-by dates, agreed in team meeting)

| Milestone | Finish by | KW |
|-----------|-----------|-----|
| **Setup** (repo, Docker, venv, data download) | ~May 4 | KW 18 |
| **Task 1.1** — Data exploration + cleaning | **May 7** | KW 19 |
| **Task 1.2** — Modeling + tuning (split by architecture) | **May 21** | KW 21 |
| **Task 1.3** — Data augmentation | **Jun 4** | KW 23 |
| **Task 1.4** — Explainability | **Jun 11** | KW 24 |
| **Report** — 8-page PDF finalized | **Jun 18** | KW 25 |

**Buffer:** Jun 18 → Jul 15 = 4 weeks. This is for polishing, fixing Docker edge cases, improving model performance, or absorbing delays. Do not plan new work into the buffer — it's insurance.

### Task Split Options (discuss with team)

The task split hasn't been decided yet. Here are three sensible approaches given 3 people:

**Option A — By task:** Person 1 owns Task 1.1 + 1.4, Person 2 owns Task 1.2 (classical), Person 3 owns Task 1.2 (CNN) + 1.3. Pros: clear ownership. Risk: Task 1.2 is 35 points and needs both architectures — splitting it across two people requires tight coordination.

**Option B — Everyone does 1.2 independently, split the rest:** All three try different architectures for Task 1.2 (the heaviest task), pick the best, then divide 1.1/1.3/1.4 among the remaining capacity. Pros: maximizes model quality for the biggest task. Risk: duplicate effort.

**Option C — Pipeline split:** Person 1 does data pipeline (1.1 + `prepare.py`), Person 2 does modeling (1.2 classical + CNN), Person 3 does robustness + analysis (1.3 + 1.4). Pros: clean pipeline dependencies. Risk: Person 2 is overloaded.

**Aram's theory advantage:** Your Chat 1/2 theory study means you'll understand *why* models work, which is most valuable for Task 1.2 (architecture decisions) and Task 1.4 (explainability). Consider volunteering for one of these.

---

## How This Project Connects to Your Theory Courses

This project sits at the intersection of everything you're learning. The table below shows where each task draws from — these are not abstract connections, they're "you will literally use this concept while coding."

| Project Task | AML/SaD Theory (Chat 1) | AMLS Systems Theory (Chat 2) | What the connection looks like in practice |
|---|---|---|---|
| **1.1 Cleaning** | Block A: descriptive stats (mean, variance, histograms) | Block F, L10: data validation, feature transforms, encoding | You compute class distributions, image-size stats — that's SaD 01/02 descriptive statistics. Your cleaning pipeline choices (resize, normalize) are the feature transforms from AMLS L10. |
| **1.2 Modeling** | Block D: bias-variance, cross-validation. Block E: regression loss. Block I: classification, logistic regression, precision/recall. Block L: neural networks, backprop. Block M: CNNs. | Block F, L11: model selection, grid search, Bayesian optimization. Block C, L06: Adam optimizer. | You train two model families (classical + CNN). Choosing hyperparameters = AMLS L11 model selection. The CNN uses Adam = AMLS L06 SGD optimizer. The FPR constraint uses precision/recall from SaD 01. |
| **1.3 Augmentation** | Block D: overfitting = high variance, augmentation reduces it | Block F, L11 slides 4-13: data augmentation strategies, AutoAugment | You're directly implementing what AMLS L11 teaches: image augmentations to improve robustness. The theory of *why* augmentation works comes from AML's bias-variance (Block D). |
| **1.4 Explainability** | Block D: understanding where models fail | Block G, L12: LIME, SHAP, occlusion explanations, saliency maps, SliceLine, Clever Hans | This task IS AMLS Block G made concrete. You implement saliency maps or occlusion analysis — the exact methods from L12. The "discuss whether explanations are plausible" part mirrors the Clever Hans discussion. |

---

## Prerequisite Dependency Graph

```
BOOTCAMP (KW 17–18) + SETUP (by May 4)
  Python fluency, venv, pytest, Docker basics, git
  Repo setup (Abdalla), Docker skeleton, data download
  │
  ▼
TASK 1.1: Data Exploration + Cleaning ──── due May 7 (KW 19)
  Needs: SaD Block A (descriptive stats) ✓
         pandas + parquet reading
         matplotlib/seaborn for visualization
  │
  ├────────────────────────────────────────┐
  ▼                                        ▼
TASK 1.2 — Classical          TASK 1.2 — CNN
  (KW 19–20)                   (KW 20–21)
  Needs: Chat 1 Blocks         Needs: PyTorch basics
  D, E, I, H                   Reference CNN (Appendix B)
  sklearn API                   Chat 1 Block L arrives KW 23
  │                             (theory deepens retroactively)
  └────────────┬────────────────┘
               ▼
         TASK 1.2 done ──── due May 21 (KW 21)
               │
  ┌────────────┴────────────┐
  ▼                         ▼
TASK 1.3: Augmentation    TASK 1.4: Explainability
  due Jun 4 (KW 23)         due Jun 11 (KW 24)
  Needs: Task 1.2 model     Needs: Task 1.2/1.3 model
  torchvision.transforms     Chat 2 Block G (L12)
  Chat 2 Block F L11          arrives KW 28 — implement
  arrives KW 27 — implement    from exercise spec + tutorials
  from intuition first         first, theory later
  │                         │
  └────────────┬────────────┘
               ▼
         REPORT (Overleaf) ──── due Jun 18 (KW 25)
               │
               ▼
         BUFFER (KW 25–29) ──── 4 weeks until Jul 15
           Polish, Docker edge cases, model improvements
```

**The critical path** runs through Task 1.2 — it's 35 points and everything else depends on it. With the compressed timeline (done by May 21), both the classical baseline and CNN must be developed in parallel or in quick succession across KW 19–21. The CNN part has a theory dependency on Chat 1 Block L (neural networks, KW 23–24), but you'll start coding the CNN *before* the theory arrives — using the reference CNN from Appendix B and PyTorch docs. The theory deepens your understanding retroactively.

**⚠️ Key tension:** The new deadlines are aggressive. Task 1.2 (35 points) must be done by May 21 — that's only ~2.5 weeks after Task 1.1 finishes. This is where the team split matters: if different people work on different architectures in parallel, the deadline is realistic. If one person does all of Task 1.2, it's very tight.

---

## Timeline (Team Internal Deadlines)

These are the finish-by dates agreed in the team meeting. The hard submission deadline is Jul 15, giving a 4-week buffer after the internal Jun 18 finish.

| KW | Dates | Project Focus | Internal Deadline | Theory Arriving (Aram) | Hours (Aram) |
|----|-------|--------------|-------------------|----------------------|-------------|
| **18** | Apr 28 – May 4 | **Setup**: Repo (Abdalla), Docker skeleton, venv, data download, timing reference | **Setup done** | Chat 1: Block E (regression). Bootcamp finishing. | ~3h |
| **19** | May 5–7 | **Task 1.1**: Data exploration, class/size distributions, cleaning pipeline, `clean.py` | **May 7: Task 1.1 done** | Chat 1: Block F (probability). Job starts. | ~6h |
| **19–20** | May 7–14 | **Task 1.2 — Classical baseline**: Feature engineering + logistic regression / random forest / SVM | — | Chat 1: Block G (distributions), Block I start (classification) | ~7h |
| **20–21** | May 14–21 | **Task 1.2 — CNN**: Reference CNN → tune architecture → calibration → compare models → finalize pipeline scripts | **May 21: Task 1.2 done** | Chat 1: Block H (regularization), Block J (SGD). Chat 2: Block C (Adam) | ~10h |
| **21–23** | May 21 – Jun 4 | **Task 1.3**: Analyze augmented data, design augmentation strategy, train robust model, compare to Task 1.2 | **Jun 4: Task 1.3 done** | Chat 1: Block K (trees), Block L start (NNs — retroactively deepens your CNN work) | ~10h |
| **23–24** | Jun 4–11 | **Task 1.4**: Saliency maps, occlusion analysis, failure mode analysis, critical discussion | **Jun 11: Task 1.4 done** | Chat 1: Block L finish (backprop). Chat 2: Block D (LLMs — background) | ~8h |
| **24–25** | Jun 11–18 | **Report**: Assemble 8-page PDF on Overleaf, final Docker testing, code cleanup | **Jun 18: Report done** | Chat 1: Block M (CNNs — retroactive). Chat 2: Block E (HW — background) | ~6h |
| **25–29** | Jun 18 – Jul 15 | **Buffer**: Polish, fix edge cases, improve model performance if needed. Submit before Jul 15. | **Jul 15: Hard deadline** | Chat 2: Blocks F, G (data lifecycle, explainability — deepens what you already built) | minimal |

**Total project hours (Aram): ~50h** — reduced from ~69h because the team splits the work. Actual hours depend on which tasks you own.

**Exam dates:** Jul 23 (4pm), Aug 06 (4pm), Aug 27 (4pm). The project finishes by Jun 18 internally — that gives you 5 full weeks of exam prep before Jul 23. If you use the buffer (through Jul 15), you still have 1 week of pure exam prep.

### Why This Compressed Timeline Works

The team's aggressive internal deadlines (everything done by Jun 18) create a massive buffer. The tradeoff: some theory arrives *after* you've already implemented it (especially CNNs and explainability). This is intentional — you learn by doing first, then deepen understanding when the lecture arrives. The exam prep benefit is significant: finishing the project 5 weeks early means you can focus entirely on the AMLS exam (Jul 23) during the critical final weeks.

### ⚠️ Theory Timing Tensions

| What you need to code | When you need it | When the theory arrives | How to bridge the gap |
|---|---|---|---|
| CNN architecture (Task 1.2) | KW 20–21 (by May 21) | Chat 1 Block L: KW 23–24 | Use reference CNN from Appendix B + PyTorch tutorials. Theory arrives retroactively. |
| Augmentation strategies (Task 1.3) | KW 21–23 (by Jun 4) | Chat 2 Block F L11: KW 27 | Intuitive — apply transforms that match validation_augmented degradations. Theory confirms later. |
| Explainability methods (Task 1.4) | KW 23–24 (by Jun 11) | Chat 2 Block G L12: KW 28 | Exercise spec describes methods. Implement from tutorials. L12 provides formal framework later. |
| Adam optimizer understanding | KW 20 (CNN training) | Chat 2 Block C L06: KW 22 | Use `AdamW` from PyTorch — it works. Understand why when L06 arrives. |

---

## Task-by-Task Detailed Plan

### TASK 1.1: Data Exploration and Cleaning (15 points)

> **Optional supplement:** [TU Python-for-ML Sheet 3](https://github.com/mahmutoezmen/Python-for-ML-Course/tree/main/3.%20Sheet) — dataset analysis exercises in Python (pandas, plotting, data loading). A useful dry run before working with the parquet image data. Do in KW 18–19 before Task 1.1.

**What the exercise asks:** Analyze training data. Report class distribution, image-size distribution, descriptive statistics. Identify characteristics that distinguish classes. Build a deterministic cleaning pipeline. Justify your choices.

**Timeline:** KW 19, done by May 7 (~6 hours — compressed from 9h because team splits work)

#### Theory Prerequisites (check these off before starting)

| Prerequisite | Source | What you need from it | When it's ready |
|---|---|---|---|
| Descriptive statistics (mean, variance, histograms, boxplots) | Chat 1, Block A (SaD 01 + 02) | Computing and interpreting summary stats for image sizes, pixel distributions | ✓ Done by KW 17 |
| Precision, recall, FP/FN vocabulary | Chat 1, Block A (SaD 01 slides 12-22) | Understanding the FPR ≤ 20% constraint that shapes everything downstream | ✓ Done by KW 17 |
| Train/test split concept | Chat 1, Block B (AML L01, SaD 11) | Understanding why you don't touch predict/ split | ✓ Done by KW 17 |

#### Bootcamp Prerequisites (already covered — just verify)

- [ ] Can read parquet files with pandas (`pd.read_parquet`) — *Bootcamp Part B Day 3 file I/O + pandas install*
- [ ] Can create plots with matplotlib — *not in Bootcamp, learn on the fly (30 min)*
- [ ] Docker basics understood — *Bootcamp Day 6-7*
- [ ] Project folder structure set up with venv — *Bootcamp Day 3-4*

#### Step-by-Step

| Step | What to do | Time | Output |
|------|-----------|------|--------|
| 1.1.1 | **Set up project.** Clone/create project folder. Create venv. Install pandas, pyarrow, matplotlib, seaborn, Pillow, scikit-learn, torch (CPU). Create `requirements.txt`. Test Docker build. | 1h | Working environment |
| 1.1.2 | **Load and inspect data.** Read one parquet file from `data/train/`. Understand the schema: `image` (binary) and `source_class` (int8). Decode a few images with PIL. Check image dimensions, color channels, byte sizes. | 1h | Jupyter notebook / scratch script with findings |
| 1.1.3 | **Class distribution analysis.** Load all training parquet files. Count samples per `source_class` (0–5). Compute the binary distribution (0: real vs 1: ai_generated after merging 1-5). Visualize with bar charts. Note any class imbalance. | 1h | Distribution plots + stats for report |
| 1.1.4 | **Image-size analysis.** Compute width, height, aspect ratio for all images. Plot distributions (histograms, boxplots). Check if image size varies by class — this could be a shortcut feature (the exercise warns about this: "characteristics that could be used to deduce which class an image belongs to"). | 1.5h | Size distribution plots, potential leakage flags |
| 1.1.5 | **Pixel-level analysis.** Compute per-channel mean/std across a sample of images. Check for anomalies (e.g., do AI-generated images have different color distributions? JPEG artifacts? Uniform noise patterns?). | 1.5h | Pixel statistics, visual examples |
| 1.1.6 | **Build cleaning pipeline.** Based on findings, decide: (a) target image size (resize all to uniform dimensions — balance quality vs. training speed given CPU constraint), (b) normalization strategy (per-channel mean/std), (c) format conversion (ensure consistent dtype), (d) any filtering (corrupt images, extreme outliers). Write `clean.py` that reads from `data/train/`, applies pipeline, writes cleaned data to `artifacts/`. | 2h | Working `clean.py` |
| 1.1.7 | **Justify choices in report notes.** For each cleaning step, write 2–3 sentences explaining why. This is what distinguishes 10/15 from 15/15 — the exercise says "justify your preprocessing choices rather than simply applying a fixed recipe." | 1h | Report draft section for Task 1.1 |

#### Theory That Arrives *After* You've Done This (Retroactive Deepening)

When you reach AMLS L10 (Chat 2, Block F, KW 26), you'll study data validation (TFDV), feature transformations (encoding, standardization, deferred standardization), and data cleaning from a *systems* perspective. By then you'll already have built a cleaning pipeline — the lecture will deepen your understanding of *why* your choices were right (or reveal improvements). Update your report if needed.

**⟷ Cross-wire to AMLS L10:** Your `clean.py` performs exactly what AMLS L10 calls "data preparation" in the ML lifecycle. The exercise asks you to justify deterministic preprocessing — L10's feature transformation discussion (recoding, binning, standardization) gives you the vocabulary. Your image resizing is a form of the "CPU-friendly" constraint that maps to AMLS's memory-vs-compute tradeoff discussion (L02 slide 13).

---

### TASK 1.2: Modeling and Tuning (35 points)

**What the exercise asks:** Build an ML pipeline for binary classification (real vs AI-generated). Maximize recall_ai with FPR ≤ 20% on real images. Train at least two model families (classical + neural). CPU-only, strict time budget (training ≤ 1800s). Calibrate automatically. Report all meaningful metrics.

**This is the heaviest task.** 35 points, and Tasks 1.3 + 1.4 depend on it. The team agreed to split this by architecture (e.g., one person does classical, another does CNN). Plan for iteration.

**Timeline:** KW 19–21, done by May 21 (~17 hours for Aram's share — split with team)

#### Theory Prerequisites

*Verified against actual AML L01–L11 and AMLS L10–L12 lecture PDFs on 30 Apr 2026.*

| Prerequisite | Source | What you need from it | When it's ready |
|---|---|---|---|
| **Bias-variance tradeoff** | Chat 1, Block D (AML L02, SaD 11) | Understanding underfitting vs overfitting — why you compare models | ✓ KW 17 |
| **Cross-validation** | Chat 1, Block D (AML L02 slides 52-57) | k-fold CV for model evaluation | ✓ KW 17 |
| **Precision, recall, FPR** | Chat 1, Block A (SaD 01) | The FPR ≤ 20% constraint; recall_ai is your optimization target | ✓ KW 17 |
| **Linear regression + loss functions** | Chat 1, Block E (SaD 03, AML L03) | Understanding MSE and why we minimize loss functions | ✓ KW 18 |
| **Logistic regression + sigmoid** | Chat 1, Block I (AML L05) | Your classical baseline will likely use logistic regression. The sigmoid outputs probabilities, which you threshold to control FPR. | KW 20–21 |
| **Regularization (L1/L2, dropout, early stopping)** ⬆️ | Chat 1, Block H (AML L04) | **Upgraded:** AML L04 covers L1/L2 regularization, dropout layers, and early stopping in detail. All three are directly used in CNN training — dropout prevents overfitting on small datasets, early stopping is built into your checkpoint loop. Essential for both classical and CNN models. | KW 21 |
| **Decision boundaries + threshold calibration** ⬆️ | Chat 1, Block I (AML L07) | **Upgraded:** AML L07 covers linear classifiers and decision boundary geometry. Threshold calibration (moving the classification boundary to trade off precision vs recall) is exactly how you satisfy the FPR ≤ 20% constraint. | KW 20–21 |
| **Gradient descent, SGD, Adam** | Chat 1 Block J (AML L06) + Chat 2 Block C (AMLS L06 slide 18) | The optimizer for your CNN. The exercise's reference CNN uses `AdamW`. AMLS L06 explains Adam's mechanics (momentum + adaptive learning rate). | KW 21 (AML) / KW 22 (AMLS) |
| **Neural networks (MLP)** | Chat 1, Block L (AML L08-L09, SaD 15) | Forward pass, backprop, activation functions (ReLU), counting parameters | KW 23–24 ⚠️ |
| **CNNs** | Chat 1, Block M (AML L10) | Conv2d, pooling, feature maps, parameter sharing — the architecture of your CNN model | KW 25 ⚠️ (but you'll start CNN work in KW 22–23 using the reference code + PyTorch docs) |
| **Model selection, hyperparameter tuning** | Chat 2, Block F (AMLS L11) | Grid search, Bayesian optimization — how to systematically tune hyperparameters | KW 27 (late!) — use sklearn `GridSearchCV` pragmatically before the theory arrives |

**⚠️ The CNN timing gap:** Chat 1 covers neural networks in Block L (KW 23–24) and CNNs in Block M (KW 25). But you need a working CNN by KW 24. Solution: start with the reference CNN from Appendix B (the exercise gives you one!), learn enough PyTorch to modify it, and deepen your understanding as Block L/M arrive. You're learning by doing first, then understanding why.

#### Phase 1: Classical Baseline (KW 19–20, ~10h)

This phase uses theory you already have (Blocks D, E, I, H from Chat 1).

| Step | What to do | Time | Theory link |
|------|-----------|------|-------------|
| 1.2.1 | **Design feature engineering.** From your Task 1.1 analysis, extract features from images: pixel statistics (mean, std per channel), edge detection (Sobel/Canny), texture features (GLCM), frequency-domain features (DCT/FFT — AI images may have different frequency signatures). This is the "engineered features" approach the exercise mentions. | 3h | AMLS L10 (feature transforms). You're doing this before the lecture — pragmatic first, theory later. |
| 1.2.2 | **Train classical models.** Using sklearn: try Logistic Regression, Random Forest, and/or SVM on your engineered features. Use `train_test_split` or k-fold CV. Evaluate with recall, precision, FPR, accuracy. | 3h | Chat 1 Block I (logistic reg.), Block K (trees, SVM), Block D (CV). sklearn API from Praxisplan Phase 2. |
| 1.2.3 | **Implement threshold calibration.** The key to the FPR ≤ 20% constraint: don't use the default 0.5 threshold. Use `calibration/` data to find the threshold where FPR on real images = 20%, then check if recall_ai is acceptable at that threshold. Use `sklearn.calibration.CalibratedClassifierCV` or manually compute the ROC curve and pick the operating point. | 2h | Chat 1 Block A (precision/recall). This is the bridge between "classification" (theory) and "operating point selection" (engineering). |
| 1.2.4 | **Validate on validation set.** Compute FPR and recall_ai on `data/validation/`. Record all metrics. Also run on `data/validation_augmented/` as a robustness baseline. | 1h | Chat 1 Block D (train vs validation vs test). |
| 1.2.5 | **Document classical baseline.** Write report notes: which features, which models, which hyperparameters, what metrics. This becomes your comparison point for the CNN. | 1h | — |

**⟷ Cross-wire to Chat 1 Block I:** When AML L05 teaches logistic regression, you'll have already *used* it. The sigmoid σ(wᵀx) that AML derives is exactly what sklearn's `LogisticRegression` computes under the hood. The `predict_proba()` output is σ(wᵀx), and your threshold calibration is choosing the cutoff on that probability.

**⟷ Cross-wire to AMLS L11 (Chat 2, Block F):** Your manual hyperparameter search in step 1.2.2 is what AMLS L11 calls "grid search." When you study L11 later (KW 27), you'll learn why Bayesian optimization would have been more efficient — and you can retroactively improve your approach if time allows.

#### Phase 2: CNN Model (KW 20–21, ~12h)

This phase overlaps with Chat 1 Block L (neural networks). You'll learn the theory and apply it simultaneously.

| Step | What to do | Time | Theory link |
|------|-----------|------|-------------|
| 1.2.6 | **Learn PyTorch basics.** You need: `torch.Tensor`, `nn.Module`, `nn.Sequential`, `DataLoader`, `optim.AdamW`, `nn.CrossEntropyLoss`, training loop (forward → loss → backward → step). The exercise's Appendix B+C are your starting point. | 3h | Chat 1 Block L (forward pass, loss, backprop) gives you the WHY. PyTorch docs give you the HOW. Study them in parallel. |
| 1.2.7 | **Build data pipeline.** Write a PyTorch `Dataset` that reads your cleaned images, converts to tensors, normalizes. Use `DataLoader` with batching. This must run within memory and time constraints. | 2h | The `DataLoader` is a practical implementation of AMLS L05's "data-parallel mini-batch" concept. Each batch is a mini-batch SGD step. |
| 1.2.8 | **Implement reference CNN.** Start with Appendix B's architecture. Get it training on your cleaned data. Verify it converges (loss decreases). Run the timing reference (Appendix C) to calibrate your time budget: your training must stay within 5× that time. | 3h | Chat 1 Block L: the forward pass through Conv2d → ReLU → MaxPool → Flatten → Linear is exactly what AML L08 teaches. Block M deepens Conv2d. |
| 1.2.9 | **Tune CNN architecture and hyperparameters.** Experiment with: number of channels (k), number of conv layers, learning rate, batch size, number of epochs, weight decay. Use the calibration set for threshold tuning (same as step 1.2.3). Monitor training time — stay within budget! | 4h | Chat 2 Block C (AMLS L06 slide 18): Adam optimizer mechanics — momentum β₁, adaptive learning rate β₂. Chat 2 Block F (L11): model selection strategies. |
| 1.2.10 | **Compare models and select best.** Compare classical baseline vs CNN on validation set. Report: FPR, recall_ai, accuracy, training time. Select the single best pipeline for submission. | 2h | Chat 1 Block D: this comparison IS the bias-variance tradeoff. Classical model = lower variance but potentially higher bias. CNN = lower bias but risk of overfitting. |
| 1.2.11 | **Write final pipeline scripts.** Package your best model into `prepare.py` (feature extraction / preprocessing), `train.py` (training with checkpoint saving), `predict.py` (load model, run inference on `data/predict/`, output `artifacts/task02/predictions.csv`). Handle the `--timeout_seconds` argument — save checkpoints regularly so you have a usable model even if training is cut short. | 2h | — |

**⟷ Cross-wire to AMLS Block C (L06):** The exercise uses `AdamW` optimizer. AMLS L06 teaches SGD → momentum → Adam progression. When you study L06 (KW 22), you'll understand why Adam converges faster than vanilla SGD (adaptive per-parameter learning rates) and why weight decay (the "W" in AdamW) is a regularization technique separate from L2 regularization.

**⟷ Cross-wire to Chat 1 Block L/M:** AML L08 teaches MLP architecture (layers, activations, parameter counting). AML L09 derives backpropagation by hand. AML L10 teaches CNNs (convolution, pooling). Your Task 1.2 CNN is a direct application: 3 conv layers with ReLU + MaxPool, followed by a linear classifier. When you study L08–L10 in Chat 1, you're studying the theory of the exact model you built.

#### Checkpoint Saving Strategy (Critical for Time Constraints)

The exercise warns: "each script is terminated after a timeout." Your `train.py` MUST save model checkpoints during training, not just at the end. Pattern:

```python
best_recall = 0
for epoch in range(max_epochs):
    train_one_epoch(model, train_loader, optimizer, criterion)
    metrics = evaluate(model, val_loader)
    if metrics['recall_ai'] > best_recall and metrics['fpr'] <= 0.20:
        best_recall = metrics['recall_ai']
        torch.save(model.state_dict(), 'artifacts/task02/best_model.pt')
    if time.time() - start > timeout_seconds - 60:  # 1-min safety margin
        break
```

This ensures you always have a usable model, even if training is interrupted.

---

### TASK 1.3: Data Augmentation (30 points)

**What the exercise asks:** Improve model robustness using augmentation. Images may be scaled, compressed, blurred, etc. Train on augmented data. Same FPR ≤ 20% constraint. Same CPU time budget. Compare to Task 1.2 model on both `validation/` and `validation_augmented/`. Target: ≥ 0.6 recall_ai on `validation_augmented/`.

**Timeline:** KW 21–23, done by Jun 4 (~10 hours)

#### Theory Prerequisites

*Verified against actual AMLS L11 lecture PDF on 30 Apr 2026.*

| Prerequisite | Source | What you need from it | When it's ready |
|---|---|---|---|
| **Data augmentation strategies** 🔴 CRITICAL | Chat 2, Block F (AMLS L11 slides 4-13) | **Verified critical:** AMLS L11 covers geometric transforms (rotation, flipping, cropping), color jittering, cutout/random erasing, AutoAugment (learned augmentation policies), and transfer learning in detail. This is essentially the playbook for your augmentation strategy. | KW 27 (late!) — but the concepts are intuitive enough to apply before the lecture. Consider reading AMLS L11 slides early as a reference. |
| **Overfitting = high variance** | Chat 1, Block D (AML L02) | WHY augmentation works: it artificially increases training data diversity, reducing variance without increasing bias much | ✓ KW 17 |
| **Regularization as variance reduction** ⬆️ | Chat 1, Block H (AML L04) | **Added:** AML L04's dropout and early stopping are regularization techniques that complement augmentation. Augmentation + dropout together is the standard approach to prevent CNN overfitting on small datasets. | KW 21 |
| **CNN architecture understanding** | From Task 1.2 | You've already built and tuned the CNN — now you're making it robust | ✓ Task 1.2 done |

#### Step-by-Step

| Step | What to do | Time | Theory link |
|------|-----------|------|-------------|
| 1.3.1 | **Analyze `validation_augmented/`.** Load the augmented validation data. Compare to `validation/`: what augmentations were applied? (blur, compression, resizing, noise?). Identify which augmentations hurt your Task 1.2 model most. | 2h | This analysis mirrors AMLS L11's "evaluate robustness" concept. |
| 1.3.2 | **Design augmentation strategy.** Based on 1.3.1, choose augmentations that match the types of degradation in the augmented data. Common choices: random horizontal flip, random rotation (small), color jitter, Gaussian blur, JPEG compression simulation, random resize-and-crop. Use `torchvision.transforms` or `albumentations`. | 2h | AMLS L11 slides 4-13: the principle is to augment training data with transformations the model will encounter at inference time. |
| 1.3.3 | **Implement augmented training pipeline.** Modify your Task 1.2 training loop to apply augmentations on-the-fly during training. You can either: (a) train from scratch with augmented data, or (b) fine-tune the Task 1.2 checkpoint on augmented data. Option (b) is faster and often works better — try both if time allows. | 3h | Chat 1 Block D: augmentation is a regularization technique, like dropout or weight decay. It reduces the gap between training and test performance. |
| 1.3.4 | **Calibrate and validate.** Use `calibration_augmented/` for threshold calibration. Evaluate on both `validation/` and `validation_augmented/`. The target: ≥ 0.6 recall_ai on augmented data while FPR ≤ 20%. Strong solutions maintain good performance on non-augmented data too. | 2h | — |
| 1.3.5 | **Write `train_augmented.py` and `predict_augmented.py`.** Same structure as Task 1.2 scripts but with augmented training. Same checkpoint-saving strategy. Output to `artifacts/task03/predictions.csv`. | 2h | — |
| 1.3.6 | **Document comparison.** Create a comparison table: Task 1.2 model vs Task 1.3 model on both validation sets. Show that augmentation improved robustness. Explain *why* each augmentation choice was made. | 2h | AMLS L11: this is the "evaluate augmentation strategy" step. The report should show the impact of individual augmentations (ablation study if time permits). |

**⟷ Cross-wire to AMLS L11 (Chat 2, Block F):** When you study AMLS L11 in KW 27, the augmentation section (slides 4-13) will cover AutoAugment (learned augmentation policies), data programming, and Snorkel. You'll have already implemented manual augmentation — the lecture shows you the automated version. If time permits, you could retroactively try a learned augmentation policy.

**⟷ Cross-wire to Chat 1 Block D:** AML's bias-variance framework explains why augmentation works: a single tree overfits (high variance), a Random Forest averages many trees to reduce variance. Augmentation does something analogous — it shows the model many versions of each image, making it "average over" the augmentations and reducing sensitivity to any single transformation.

---

### TASK 1.4: Explainability (20 points)

**What the exercise asks:** Analyze and explain your model's behavior. Use saliency maps, occlusion analysis, gradient-based explanations, or perturbation analysis. Discuss false positives/negatives. Compare what the model attends to for real vs AI images. Be critical — discuss whether explanations are plausible and whether they reveal shortcuts or dataset bias.

**Timeline:** KW 23–24, done by Jun 11 (~8 hours)

#### Theory Prerequisites

*Verified against actual AMLS L12 lecture PDF on 30 Apr 2026.*

| Prerequisite | Source | What you need from it | When it's ready |
|---|---|---|---|
| **Occlusion-based explanations** | Chat 2, Block G (AMLS L12 slides 4-19) | Slide a gray patch over the image, measure how prediction changes. Exam Q4c asks exactly this. | KW 28 (very late!) — but the concept is simple enough to implement before the lecture |
| **Saliency maps / gradient-based** | Chat 2, Block G (AMLS L12) | Compute gradient of the output class score with respect to input pixels. High-gradient pixels = important for the prediction. | KW 28 |
| **LIME** | Chat 2, Block G (AMLS L12 slides 20-38) | Perturb input, get predictions, fit a simple local model to explain the prediction | KW 28 |
| **SHAP** | Chat 2, Block G (AMLS L12 slides 20-38) | Shapley-value-based feature importance — fair attribution | KW 28 |
| **Clever Hans phenomenon** | Chat 2, Block G (AMLS L12 slide 15) | Models may learn shortcuts (wolf = snow background, horse = watermark). Your model might learn "AI images have certain artifacts" but the explanation reveals it's using something unintended. | KW 28 |
| **Confusion matrix analysis** ⬆️ | Chat 2, Block G (AMLS L12) | **Added:** AMLS L12 also covers confusion matrix interpretation and model evaluation from an explainability perspective — directly relevant to your failure mode analysis in step 1.4.4. | KW 28 |

**⚠️ The timing gap:** AMLS L12 (explainability theory) arrives in KW 28, but you need to implement this in KW 26–27. However: the exercise spec itself describes the methods you should use (saliency maps, occlusion analysis). You can implement them from PyTorch tutorials and the exercise description, then deepen your theoretical understanding when L12 arrives. This is the same learn-by-doing pattern as the CNN in Task 1.2.

#### Step-by-Step

| Step | What to do | Time | Theory link |
|------|-----------|------|-------------|
| 1.4.1 | **Choose explainability method(s).** Pick at least two: (a) gradient-based saliency maps (simplest — compute `input.grad` after a backward pass on the class score), (b) occlusion analysis (slide a patch, measure prediction change). Optional: (c) LIME via the `lime` library, (d) Grad-CAM for CNN-specific attention visualization. | 1h | AMLS L12: these are the exact methods from the lecture. You're implementing them before studying the formal theory. |
| 1.4.2 | **Implement saliency maps.** For your CNN: enable gradient computation on input images, compute the loss for the predicted class, call `loss.backward()`, visualize `input.grad` as a heatmap overlay. | 2h | Chat 1 Block L (backprop): saliency maps are literally "backprop all the way to the input" instead of stopping at the first layer's weights. |
| 1.4.3 | **Implement occlusion analysis.** Slide a gray square (e.g., 16×16) across the image. For each position, run inference and record the prediction confidence. Plot a heatmap of how confidence changes — regions where occlusion drops confidence are "important." | 2h | AMLS L12 slides 14-16: this is the exact method from the lecture. The Clever Hans example (slide 15) shows why you need to check if the model is attending to the right thing. |
| 1.4.4 | **Analyze failure modes.** Collect false positives (real images classified as AI) and false negatives (AI images classified as real). Run your explainability methods on these. Look for patterns: do FPs share visual characteristics? Do FNs have features that make them look "real"? | 2h | Chat 2 Block G (SliceLine): you're manually doing what SliceLine automates — finding problematic subgroups in your data. |
| 1.4.5 | **Critical discussion for report.** This is where the points are. Don't just show pretty heatmaps — discuss: Are the explanations plausible? (Does the model look at image content or at artifacts?) Do explanations differ for real vs AI images? Does the model exhibit shortcut behavior? What are the limitations of your explainability method? | 3h | AMLS L12 (Clever Hans, bias sources, fairness). The exercise explicitly says "Explanations should not be treated as automatically correct." |

**⟷ Cross-wire to AMLS L12 (Chat 2, Block G):** This task is the most direct theory→practice connection in the entire project. AMLS L12 teaches occlusion explanations, saliency maps, LIME, SHAP, and the Clever Hans phenomenon. You'll implement at least two of these methods. When you study L12, every slide will connect to code you've already written. The exam asks about occlusion explanations (Q4c) — you'll have implemented them.

**⟷ Cross-wire to PPDS GroupFairness (Chat 4):** AMLS L12's fairness metrics (statistical parity, equalized odds) connect to PPDS's GroupFairness analysis. While Task 1.4 focuses on explainability rather than fairness, the mindset is the same: "does this model work well for all subgroups, and can we explain why?"

---

### REPORT + DOCKER (KW 24–25, done by Jun 18, ~6 hours)

**Workflow:** Report lives on Overleaf, split by task ownership. Each person writes their section. One person assembles intro + conclusion. Docker is tested continuously — don't leave it for this phase.

#### Report Structure (8 pages, 10pt)

| Section | Pages | Content | Theory vocabulary to use |
|---------|-------|---------|------------------------|
| **1. Introduction** | 0.5 | Problem description, approach overview | ML pipeline lifecycle (AMLS L01) |
| **2. Data Exploration & Cleaning (Task 1.1)** | 1.5 | Class distribution, image stats, cleaning pipeline with justifications, visualizations | Descriptive statistics (SaD 01-02), feature transforms (AMLS L10) |
| **3. Modeling (Task 1.2)** | 2.5 | Two model families (classical + CNN), architecture choices, hyperparameter tuning, calibration method, all metrics (FPR, recall, accuracy), comparison table | Bias-variance (AML L02), logistic regression (AML L05), CNN architecture (AML L10), model selection (AMLS L11), Adam optimizer (AMLS L06) |
| **4. Data Augmentation (Task 1.3)** | 1.5 | Augmentation strategy, justification, robustness comparison (Task 2 vs Task 3 on both validation sets) | Data augmentation (AMLS L11), regularization as variance reduction (AML L04) |
| **5. Explainability (Task 1.4)** | 1.5 | Method description, visual examples, failure analysis, critical discussion of what explanations reveal | Occlusion/saliency (AMLS L12), Clever Hans (AMLS L12), SliceLine concept (AMLS L12) |
| **6. Conclusion** | 0.5 | Summary, limitations, what you'd do with more time | — |

#### Docker Checklist

- [ ] `Dockerfile` based on Appendix A (`python:3.11-slim`)
- [ ] `requirements.txt` with pinned versions (including `torch` CPU-only)
- [ ] Build: `docker build -t amls-project .` — must succeed without internet
- [ ] Test full pipeline: mount `data/` as read-only, run all 6 scripts in order with timeouts
- [ ] Image size < 4 GB: check with `docker images`
- [ ] No internet access at runtime: test with `--network none`
- [ ] All outputs land in `artifacts/` — nothing writes to `data/`
- [ ] `predictions.csv` format: `row_id,predicted_label` (integers, no extra columns)

---

## The 6 Theory → Practice Moments (When Theory Clicks)

These are the specific moments where studying theory in Chat 1/2 will suddenly make sense because you've already done the practice:

1. **Descriptive stats → Data exploration (Task 1.1, KW 19):** SaD 01-02's mean/variance/histograms are exactly what you compute for image sizes and pixel distributions. The theory is alive.

2. **Logistic regression → Classical baseline (Task 1.2a, KW 19-20):** AML L05's sigmoid σ(wᵀx) is what sklearn's `LogisticRegression.predict_proba()` computes. Your threshold calibration is choosing where on the sigmoid to cut.

3. **Neural networks → CNN training (Task 1.2b, KW 20-21):** You'll code the CNN *before* AML L08-L09 (KW 23-24). When you later study forward pass and backpropagation, you'll realize: `loss.backward()` IS backprop, `optimizer.step()` IS the SGD update rule w ← w - η∇L. The theory will click because you've already seen it work.

4. **Adam optimizer → Why your CNN converges (Task 1.2b, KW 20-21):** You'll use `AdamW` pragmatically. When AMLS L06 arrives (KW 22), it explains why Adam works better than vanilla SGD: adaptive per-parameter learning rates (β₂) + momentum (β₁). Retroactive understanding.

5. **Data augmentation theory → Why your robust model works (Task 1.3, KW 21-23):** You'll implement augmentation before AMLS L11 (KW 27). When the lecture arrives, slides 4-13 explain *why* your approach worked — the theory confirms your intuition.

6. **Explainability methods → Your saliency maps (Task 1.4, KW 23-24):** You'll implement saliency maps and occlusion analysis before AMLS L12 (KW 28). When the lecture arrives, every slide connects to code you wrote weeks ago. The Clever Hans critique will make you reconsider your own model's explanations — update the report if needed during the buffer period.

---

## Risk Assessment and Buffers

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| **Task 1.2 CNN doesn't converge** | Medium | High (blocks 1.3 + 1.4) | Start with reference CNN from Appendix B — it's designed to work. Tune incrementally. Keep a working checkpoint at all times. |
| **Time budget too tight on CPU** | Medium | Medium | Run timing reference (Appendix C) in KW 19 during setup. Know your time budget early. Use smaller images (128×128 instead of 256×256) if needed. |
| **CNN theory not studied when coding starts** | Expected | Low | The exercise provides a reference CNN. PyTorch tutorials are sufficient to get started. Theory deepens understanding retroactively. |
| **Docker issues at submission** | Low | Very High | Build Docker in KW 19 (step 1.1.1) and test regularly. Don't leave Docker for the last week. |
| **Report takes longer than planned** | Medium | Medium | Write report sections as you go (each task's last step includes report notes). Final KW 27-28 is assembly + polish, not writing from scratch. |

**Buffer period:** KW 25–29 (Jun 18 – Jul 15) is a 4-week buffer. If everything goes smoothly, use it for model improvement or early exam prep. If tasks slip, it absorbs the delay. After Jul 15 submission, full focus shifts to AMLS exam (Jul 23, 4pm) with retakes available Aug 6 and Aug 27.

---

## What This Chat Does NOT Cover (Handled Elsewhere)

| Topic | Where it lives | Why not here |
|-------|---------------|-------------|
| Python basics, venv, git, Docker fundamentals | **Bootcamp Chat** (Plans/Programming/python/Programming-Toolbox-Bootcamp.md) | Already covered. This plan assumes those skills. |
| AML/SaD theory (bias-variance, regression, classification, NNs) | **Chat 1** (Plans/ML/foundations/Chat1_Foundations_AML_SaD_Plan.md) | This plan references Chat 1 blocks as prerequisites, doesn't re-teach them. |
| AMLS systems theory (compilation, parallelism, lifecycle) | **Chat 2** (Plans/ML/systems/Chat2_AMLS_Theory_Plan.md) | This plan references Chat 2 blocks for cross-wires, doesn't re-teach them. |
| PPDS mlprov implementation | **Chat 4** | Separate project, same deadline. Coordinate time allocation. |
| sklearn API deep dive | **Praxisplan Phase 2** (KW 19) | This plan assumes you learn sklearn in KW 19 as the Praxisplan schedules. |

---

## Weekly Checklist Template

Use this at the end of each week to track progress:

```
### KW __ Check-in
- [ ] Task step(s) completed this week: ___
- [ ] Docker still builds and runs: yes/no
- [ ] Best model metrics: FPR=___, recall_ai=___
- [ ] Report sections drafted: ___
- [ ] Hours spent this week: ___
- [ ] Blockers for next week: ___
- [ ] Theory I used this week: ___
```
