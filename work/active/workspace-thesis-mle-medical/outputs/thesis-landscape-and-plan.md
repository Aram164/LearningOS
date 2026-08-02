# Thesis landscape & plan — Exploring and optimizing MLE agents for medical use cases

*Operator-compiled orientation brief, 2026-07-20. Balanced landscape + action
plan. Sources are listed with links in §8; every non-obvious claim traces to one
of them. This is a synthesis draft, not a canonical note — extend it freely.*

---

## 0. The thesis in one paragraph

A **machine-learning-engineering (MLE) agent** is an LLM-driven system that, given
a dataset and a task description, writes and iteratively debugs the whole ML
pipeline (load → preprocess → model → validate → submit) with no human in the
loop. **MLE-bench** (OpenAI, 2024) is the standard yardstick: 75 real Kaggle
competitions, scored against the human leaderboards. Your baseline agent,
**"AID" = AIDE**, is the tree-search reference scaffold from that benchmark. The
thesis takes this general-purpose machinery into **medicine** — where a ready-made
medical subset already exists inside MLE-bench, plus purpose-built biomedical
benchmarks (BioML-bench, ReX-MLE) — and asks: *how well do MLE agents do on
medical tasks, and how do we adjust them to do better?* The core intellectual
move is the **exploration phase**: characterize where the agent fails on medical
data, then apply targeted optimizations.

---

## 1. MLE-bench and its variants

### 1.1 Base MLE-bench (OpenAI, arXiv 2410.07095, Oct 2024)

- **75 Kaggle competitions** curated for real ML-engineering skill (train models,
  build datasets, run experiments). Deterministic scoring reuses each Kaggle
  competition's own metric; agent submissions are ranked against the **human
  leaderboard** and awarded **bronze/silver/gold medals** on the same thresholds
  Kaggle uses.
- **Complexity split:** 22 low (an experienced engineer < 2 h), 38 medium
  (2–10 h), 15 high (> 10 h). 15 problem categories.
- **Headline result at launch:** the best scaffold was **o1-preview + AIDE**,
  reaching **≥ bronze in 16.9 %** of competitions. Open-sourced at
  `github.com/openai/mle-bench`.
- **Leaderboard status (Apr 2026):** OpenAI paused new submissions while they
  redesign the fairness/comparability process — so cite specific agent numbers
  by their papers, not "the live leaderboard."

### 1.2 MLE-bench Lite

The **22 low-complexity** competitions, used as a cheap, fast evaluation set
(most agent papers report "MLE-bench-Lite" numbers). **Four of the 22 are
medical** — this is your natural starting point (see §2).

### 1.3 Sibling / derivative benchmarks (the "variants")

| Benchmark | What it is | Why it matters here |
|---|---|---|
| **MLE-bench Lite** | 22-task low-complexity subset of MLE-bench | Cheap reproduction set; contains 4 medical tasks |
| **BioML-bench** (biorxiv 2025) | MLE-bench's engine **rebuilt for biomedicine**: 4 domains, expert leaderboards | **Most relevant variant** — already benchmarks AIDE on medical data (§4) |
| **ReX-MLE** (arXiv 2512.17838) | Autonomous-agent benchmark of **medical-imaging** challenges (20 challenges / 10 competitions from Grand Challenge) | Pure medical-imaging variant; alternative/additional eval set |
| **MLGym** (Meta, arXiv 2502.14499) | Gym-style framework, 13 open-ended AI-research tasks | Broader "AI research agent" framing; RL-style env |
| **MLAgentBench** (arXiv 2310.03302) | 13 tasks; measures ≥10 % improvement over a baseline | Older; a second baseline agent in BioML-bench |
| **RE-Bench** (METR) | 7 hard ML-research environments (optimize loss / runtime) | Frontier-research difficulty, not Kaggle-style |
| **DSBench** | Data-science tasks from Kaggle + ModelOff | Adds analysis/notebook tasks |
| **MLE-Dojo** (arXiv 2505.07782) | Interactive, RL-friendly MLE environment | For training/`gym`-style agent work |
| **TimeSeriesGym** | Time-series-focused MLE agent benchmark | Only if a temporal-clinical angle appears |

**Takeaway for the thesis:** MLE-bench is the trunk; **BioML-bench and ReX-MLE
are the two branches already pointed at medicine.** Decide early (supervisor
question) whether the thesis lives inside MLE-bench's medical subset only, or
extends onto BioML-bench / ReX-MLE.

---

## 2. The medical subset of MLE-bench (key deliverable)

Pulled from the official split files (`experiments/splits/{low,medium,high}.txt`)
and classified by hand. **~13 clinical + 3 biomolecular** of the 75.

### 2.1 Clinical / human-medical (the core 13)

| Competition (slug) | Modality | Task | MLE-bench tier |
|---|---|---|---|
| `aptos2019-blindness-detection` | Retinal fundus photos | Diabetic-retinopathy grading (ordinal) | **Low (Lite)** |
| `histopathologic-cancer-detection` | Histopathology patches | Tumor present? (binary) | **Low (Lite)** |
| `ranzcr-clip-catheter-line-classification` | Chest X-ray | Catheter/line placement (multi-label) | **Low (Lite)** |
| `siim-isic-melanoma-classification` | Dermoscopy | Melanoma detection (binary, imbalanced) | **Low (Lite)** |
| `hubmap-kidney-segmentation` | Kidney histology (WSI) | Glomeruli segmentation | Medium |
| `osic-pulmonary-fibrosis-progression` | CT + spirometry (tabular) | Predict FVC decline (regression + uncertainty) | Medium |
| `uw-madison-gi-tract-image-segmentation` | MRI | GI-organ segmentation for radiotherapy | Medium |
| `hms-harmful-brain-activity-classification` | EEG / spectrograms | Seizure & harmful-brain-activity class | High |
| `rsna-2022-cervical-spine-fracture-detection` | CT | Cervical-spine fracture detection | High |
| `rsna-breast-cancer-detection` | Mammography | Screening breast-cancer detection | High |
| `rsna-miccai-brain-tumor-radiogenomic-classification` | MRI | MGMT methylation status (radiogenomics) | High |
| `siim-covid19-detection` | Chest X-ray | COVID detection + opacity localization | High |
| `vinbigdata-chest-xray-abnormalities-detection` | Chest X-ray | Thoracic abnormality **object detection** | High |

### 2.2 Biomolecular / drug-adjacent (extended "medicine", +3)

| Competition | Modality | Task | Tier |
|---|---|---|---|
| `stanford-covid-vaccine` (OpenVaccine) | mRNA sequence | mRNA degradation prediction | High |
| `champs-scalar-coupling` | Molecular graphs | NMR scalar-coupling constants | Medium |
| `bms-molecular-translation` | Molecule images | Image → InChI (chem-OCR) | High |

**Why this matters:** the medical subset is not homogeneous — it spans
**7+ imaging modalities** (fundus, dermoscopy, histology WSI, X-ray, CT, MRI,
mammography), plus EEG signal, tabular, and object-detection/segmentation task
types. That heterogeneity is itself a thesis finding: an agent tuned for
"medical" must actually handle very different data. **Start with the 4 Lite
tasks** (small, fast, cheap) before touching the high-complexity RSNA/CT set
(large images, GPU-hungry).

---

## 3. Agent scaffolds — what "AID"/AIDE is, and the competition

### 3.1 AIDE — your baseline ("AID")

**AIDE = AI-Driven Exploration in the Space of Code** (Weco AI, arXiv 2502.13138;
repo `github.com/WecoAI/aideml`). It frames MLE as a **code-optimization problem**
and runs **best-first tree search** over a *solution tree*: each node is a full
candidate solution (a specific architecture / preprocessing / hyperparameters).
The loop is **draft → execute → analyze results → branch** (propose an
improvement or a bug-fix on the most promising node). It was OpenAI's best
scaffold on MLE-bench and **wins ~4× more medals than the best linear/step
agent**.

**Known weaknesses (important — these are your optimization targets):**
- Leans on the **LLM's internal knowledge** → tends to pick **outdated or overly
  simple models**, and (per BioML-bench) **rarely uses deep learning even on
  image tasks**, where humans win with DL.
- Refinement can **shift between pipeline stages prematurely**.
- In BioML-bench, AIDE's most common failure was **resource exhaustion** (e.g.,
  copying large image files) — a *scaffolding* problem, not a reasoning one.

### 3.2 The scaffold landscape (background chapter material)

| Agent | Core idea | MLE-bench standing | Note |
|---|---|---|---|
| **AIDE** | Best-first **tree search** over code | ~17 % medal (o1-preview) at launch | Your baseline |
| **R&D-Agent** (Microsoft, arXiv 2505.14738) | **Dual agent** Researcher+Developer, parallel exploration traces | **Top of MLE-bench, ~35 % any-medal** | Strongest reported |
| **MLE-STAR** (Google, arXiv 2506.15692) | **Web-search** for SOTA models + **targeted refinement** (ablate high-impact code blocks) | **63 % medals on MLE-bench-Lite** | Directly critiques AIDE's stale-knowledge flaw |
| **ML-Master** (arXiv 2506.16499) | Integrates exploration + reasoning | ~24 % any-medal, high valid-submission | |
| **DS-Agent** | **Case-based reasoning** from curated Kaggle cases | — | Motivates a "winning-solution case bank" |
| **AutoKaggle** | Multi-agent + unit testing for code correctness | tabular focus | |
| **OpenHands** | General SWE-agent scaffold | used as MLE-bench baseline | |

**One paper to read first for the "exploration" theme:** *"AI Research Agents for
Machine Learning: Search, Exploration, and Generalization in MLE-bench"* (arXiv
2507.02554) — it dissects **search operators, exploration strategy, and
generalization** on MLE-bench. This is the closest existing work to your thesis's
core question and the best template for the exploration-phase methodology.

---

## 4. Open MLE-in-medicine use-cases and benchmarks

### 4.1 BioML-bench — the anchor paper (biorxiv 2025.09.01.673319)

Built **on MLE-bench's engine**, extended for biomedicine (h5ad formats, cloud
deploy, expert leaderboards). **Four domains:** protein engineering (ProteinGym),
single-cell omics (OpenProblems), biomedical imaging (Kaggle), drug discovery
(PolarisHub). It **benchmarks exactly the agents you care about** — AIDE and
MLAgentBench (generalists) vs. Biomni and STELLA (biomedical specialists).
**Findings you can build on directly:**

1. **All agents underperform human experts** — best (Biomni, AIDE) average only
   the **~34–37th leaderboard percentile**.
2. **No consistent advantage for biomedical-specialist agents** over generalists
   → **agent architecture / scaffolding is the primary driver of capability**,
   not domain-specialization. (This is a strong justification for *optimizing the
   scaffold*, i.e., your thesis.)
3. **Agents avoid deep learning, even on images**, while human leaderboards are
   DL-dominated → a concrete optimization lever.
4. **Most failures are scaffolding bugs** (resource exhaustion, silent
   try/except that never saves predictions, package-install stalls) — "likely
   avoidable," i.e., low-hanging fruit.
5. Winning runs used **more diverse classical strategies** (feature engineering,
   stacking) more often. Released pip-installable: `github.com/science-machine/biomlbench`.

### 4.2 Other medical/biomedical agent benchmarks (context)

- **ReX-MLE** (arXiv 2512.17838) — 20 medical-imaging challenges from Grand
  Challenge; a clean imaging-only eval set.
- **MedAgentBench** — virtual-EHR environment for medical LLM agents (clinical,
  not pipeline-MLE).
- **ABRA** (radiology), **AgentRx** (multimodal clinical prediction),
  **MedMemoryBench** (agent memory in personalized healthcare) — adjacent
  clinical-agent benchmarks; useful for the background survey, not the build.

### 4.3 Open data sources to draw *new* medical MLE tasks

Grand Challenge (imaging), **MedMNIST** (lightweight imaging — ideal for cheap
iteration), PhysioNet / **MIMIC** (EHR & signals), TCIA (cancer imaging),
ProteinGym (protein fitness), OpenProblems (single-cell), PolarisHub &
**Therapeutics Data Commons (TDC)** (drug discovery). These are how you'd extend
beyond MLE-bench if the supervisor wants novel tasks with real human baselines.

---

## 5. Kaggle winning solutions as a knowledge source

The link in the brief (SRK / *"Winning solutions of Kaggle competitions"*) is a
**curated index** pointing to winning-solution write-ups and forum discussions
across many competitions. Two uses for the thesis:

1. **Human-strategy reference** — read the write-ups for the medical competitions
   in scope to see what actually wins: **ensembling, test-time augmentation,
   pseudo-labeling, external data, and domain preprocessing** (stain
   normalization for histopathology, lung-window CT scaling, class-imbalance
   handling for melanoma). This is the "understand the solutions" ask.
2. **A retrieval / case bank for the agent** — inject these write-ups into the
   agent's draft step. This is precisely how **DS-Agent** (case-based reasoning)
   and **MLE-STAR** (web search for SOTA methods) beat AIDE's stale internal
   knowledge — and it's an obvious, defensible optimization to test on the
   medical subset (§6, Phase 2b).

*(The page is JavaScript-rendered, so the raw index didn't extract cleanly here;
open it in a browser, or I can pull the per-competition solution links for the 13
medical tasks on request.)*

---

## 6. Exploration phase — plan to adjust the agents for the medical use-case

Structured as the supervisor framed it: **explore first, then optimize.**

**Phase 0 — Reproduce the AIDE baseline (do this first).**
Stand up the "AID"/AIDE environment; run it on the **smallest medical Lite task**
(`histopathologic-cancer-detection`), then the other 3 Lite medical tasks. Log
**medal rate, valid-submission rate, and cost/wall-clock** per run, with
≥3 replicates (agents are stochastic — BioML-bench saw the *same* agent swing
54th→100th percentile across replicates). This number is your control.

**Phase 1 — Characterize failure & strategy on the medical subset (the "exploration").**
Expand to the 13 clinical tasks as budget allows. Replicate BioML-bench's
analysis on *your* runs: does AIDE (a) **avoid deep learning** on imaging?
(b) **exhaust resources** on large image data? (c) miss **modality-specific
preprocessing**? (d) fail silently without saving a submission? Produce a failure
taxonomy + a strategy-usage heatmap. **This characterization is the thesis's
empirical spine.**

**Phase 2 — Targeted optimizations (hypotheses to test one at a time).**
- **(a) Medical-domain priming** — modality-aware system prompt / preprocessing
  hints (windowing, stain norm, class-imbalance, TTA).
- **(b) Winning-solution retrieval** — inject Kaggle write-ups / web search into
  the draft node (DS-Agent / MLE-STAR style) to fix stale-knowledge model choices.
- **(c) DL scaffolding & pretrained-model tools** — give the agent `timm` /
  **MONAI** (medical-imaging models) so it *can* and *will* reach for DL.
- **(d) Resource & robustness guards** — fix the #1 AIDE failure (resource
  exhaustion / unsaved submissions): stream large files, wrap the submission
  write, cap memory. Cheapest win per BioML-bench.
- **(e) Search-policy tuning** — tree width/depth, node-selection, and budget
  allocation, informed by the exploration paper (arXiv 2507.02554).

**Phase 3 — Evaluation protocol.**
Fixed compute budget, **N replicates**, report **medal rate + leaderboard
percentile in both "penalized" (failed run = 0) and "non-penalized" settings**
(BioML-bench's protocol — the penalized/non-penalized gap is exactly what
isolates *scaffolding* fixes from *capability* gains). **Ablate each optimization
(a)–(e)** against the Phase-0 baseline so every gain is attributable.

---

## 7. Decisions to settle with the supervisor

1. **Benchmark boundary:** MLE-bench medical subset only, or add BioML-bench /
   ReX-MLE?
2. **Compute:** GPU + wall-clock budget (imaging needs GPU; BioML used L4 @ 16 h).
3. **Agents:** AIDE only, or an AIDE-vs-{MLE-STAR, R&D-Agent} comparison arm?
4. **Grading target of "optimizing":** capability (medals) vs. reliability
   (valid submissions) vs. cost.
5. **Base LLM(s)** and their budget (a confound to control, per BioML-bench).
6. Confirm **"AID" == AIDE** (not an in-house fork) before Phase 0.

---

## 8. Sources (annotated)

**MLE-bench & core**
- MLE-bench paper — https://arxiv.org/abs/2410.07095 · repo https://github.com/openai/mle-bench
- OpenAI announcement — https://openai.com/index/mle-bench/
- Split files (medical subset derivation) — https://raw.githubusercontent.com/openai/mle-bench/main/experiments/splits/low.txt (also medium.txt, high.txt)

**Agent scaffolds**
- AIDE ("AID") — https://arxiv.org/abs/2502.13138 · repo https://github.com/WecoAI/aideml
- R&D-Agent (Microsoft) — https://arxiv.org/abs/2505.14738 · repo https://github.com/microsoft/RD-Agent
- MLE-STAR (Google) — https://arxiv.org/abs/2506.15692 · https://research.google/blog/mle-star-a-state-of-the-art-machine-learning-engineering-agents/
- ML-Master — https://arxiv.org/pdf/2506.16499
- **Exploration paper (read first)** — https://arxiv.org/abs/2507.02554
- MLE-Dojo — https://arxiv.org/abs/2505.07782 · MLGym — https://arxiv.org/abs/2502.14499

**Medical / biomedical benchmarks**
- **BioML-bench** — https://www.biorxiv.org/content/10.1101/2025.09.01.673319v2 · repo https://github.com/science-machine/biomlbench
- ReX-MLE — https://arxiv.org/abs/2512.17838
- Awesome-AI-Agents-for-Healthcare — https://github.com/AgenticHealthAI/Awesome-AI-Agents-for-Healthcare
- How to benchmark medical AI agents (PLOS Medicine) — https://journals.plos.org/plosmedicine/article?id=10.1371/journal.pmed.1005170

**Solution knowledge**
- Kaggle winning solutions index (SRK) — https://www.kaggle.com/code/sudalairajkumar/winning-solutions-of-kaggle-competitions
