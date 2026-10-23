---
id: note-bachelor-thesis-medical-mle-exploration
type: note
role: synthesis
title: Bachelor thesis — AIDE medical MLE setup, reading path and exploration plan
created: '2026-10-23'
state: rough
authorship: operator-drafted
semantic_review: unreviewed
concepts:
- concept-classification-metrics
- concept-bias-variance-tradeoff
sources:
- source-mle-bench-paper
- source-mle-bench-repository
- source-aide-paper
- source-aide-reference
- source-rex-mle-paper
- source-aira-paper
- source-rd-agent-paper
- source-piml-paper
- source-tripod-ai
- source-aptos-winning-solution
- source-siim-isic-winning-solution
- source-medmnist
- source-ptb-xl
- source-mimic-iv
- source-kaggle-winning-solutions
- source-sklearn-user-guide
- source-pytorch-tutorials
contexts:
- workspace-thesis-mle-medical
---

# Exploring and Optimizing MLE Agents for Medical Use Cases

Preparation guide for the Bachelor thesis exposé, saved from the research discussion on **23 October 2026**. AIDE is the confirmed starting agent. This is an operator-drafted research proposal and reading guide; the research question, task selection, and optimization remain candidates for refinement. Experiment execution has not started.

The existing [landscape survey](../../../work/active/workspace-thesis-mle-medical/outputs/thesis-landscape-and-plan.md) and [original supervisor brief](../../../work/active/workspace-thesis-mle-medical/inputs/original-thesis-brief.md) remain background evidence. This dated guide adds a narrower preparation path and current source links. Work allocation follows [coordination](../../../work/COORDINATION.md).

## 1. Understanding and confirmed brief

The thesis should explore how machine learning engineering agents build and improve pipelines for medical tasks. Begin with AIDE, reproduce a small baseline, examine failures, and then compare one targeted adaptation under controlled conditions. The immediate objective is an evidence-backed exposé and a feasible first experiment.

Confirmed by Aram in this discussion: **“AIDE was meant.”** The supervisor also suggested looking for health/healthcare tags in Kaggle competitions and said: **“Also look into the discussions to get an understand of the solutions.”**

Keep three objects separate:

| Object | Meaning | Example |
|---|---|---|
| Agent | Code, tools, memory and search workflow that conducts experiments | AIDE |
| Underlying LLM | Model used by the agent to generate and analyse code | Record the exact model/version for each run |
| Benchmark | Tasks, prepared data, rules and grading | MLE-bench or ReX-MLE |

An MLE agent loads and preprocesses data, writes and debugs training code, evaluates models, and produces predictions. A medical question-answering agent is a different task family.

## 2. Read and learn first

Read the first three papers before choosing an optimization. Keep one short record per paper: research problem; method; evaluation; findings; limitations; possible relevance to the thesis. Planned reading is not evidence that the material has been studied.

| Order | Reading | Focus and intended output | Disposition |
|---|---|---|---|
| 1 | [MLE-bench: Evaluating Machine Learning Agents on Machine Learning Engineering](https://arxiv.org/abs/2410.07095) | Start with §2, then experiments and limitations. Explain agent inputs, withheld evaluation, submission formats, resource budgets and medal thresholds in your own words. | Required first |
| 2 | [AIDE: AI-Driven Exploration in the Space of Code](https://arxiv.org/abs/2502.13138) | §3 and Algorithm 1: Draft, Debug and Improve; candidate scripts as search-tree nodes; selection by measured feedback. Draw the loop and explain where failures or misleading validation can enter. | Required first |
| 3 | [ReX-MLE: The Autonomous Agent Benchmark for Medical Imaging Challenges](https://proceedings.mlr.press/v315/kenia26a.html) | Closest medical related work, published at MIDL 2026. Identify overlap with the proposed thesis, tested interventions, failure modes and open questions. | Required first |
| 4 | [AI Research Agents for Machine Learning: Search, Exploration, and Generalization in MLE-bench](https://arxiv.org/abs/2507.02554) | Separate search policies from code operators; read the generalization analysis and Appendix I on repeated runs. Explain why improved validation scores can fail to improve held-out results. | Helpful for experiment design |
| 5 | [TRIPOD+AI](https://pmc.ncbi.nlm.nih.gov/articles/PMC11019967/) | Reporting of medical prediction studies: data provenance, evaluation, calibration, uncertainty and limitations. Use it as reporting guidance, not as proof of clinical validity. | Helpful for medical framing |

If model training is unfamiliar, do these practical foundations alongside papers 1–2:

- [scikit-learn: common pitfalls and data leakage](https://scikit-learn.org/stable/common_pitfalls.html): split data before fitting preprocessing; understand training, validation and final testing; prevent leakage with pipelines.
- [PyTorch: transfer learning for computer vision](https://docs.pytorch.org/tutorials/beginner/transfer_learning_tutorial.html): load a dataset, adapt a pretrained network, train, validate and save the model.

Learn enough to explain overfitting, class imbalance, ROC-AUC, precision/recall, ordinal severity labels, transfer learning and sources of randomness. For medical records with repeated observations, learn patient/slide grouping and temporal separation; apply these only when the data provides the necessary identifiers. A random image split must not be described as independent-patient or external-hospital validation without evidence.

## 3. Benchmark and agent variants

| Benchmark / subset | Definition | Role in this proposal |
|---|---|---|
| [MLE-bench](https://github.com/openai/mle-bench) | 75 Kaggle competitions with preparation and grading code | Main framework and methodology reference |
| [MLE-bench Lite](https://github.com/openai/mle-bench#lite-evaluation) | Official 22-task low-complexity split | Starting task pool; it is not an official medical-only benchmark |
| [MLE-Pi / PiML](https://proceedings.mlr.press/v293/chopde25a.html) | A 26-task evaluation subset introduced with PiML | Reference-only comparison for smaller benchmark selection |
| [ReX-MLE](https://rexrank.ai/ReX-MLE/index.html) | 20 tasks drawn from medical imaging competitions | Essential specialist related work; possible later evaluation extension |

“Low complexity” estimates engineering difficulty, not necessarily training cost or download size. The official Lite collection is about 158 GB; prepare one chosen competition first.

For agent variants, start with **AIDE**. Read **AIRA** next because its experiments separate code operators from greedy, MCTS and evolutionary search. Its results show that changing search alone did not overcome limitations of AIDE's operators in the studied settings. **[R&D-Agent](https://arxiv.org/abs/2505.14738)** is a reference-only architectural comparison through its iterative research/development workflow. Broader agent comparisons stay deferred until the baseline and budget are known.

## 4. Candidate medical tasks

These four competitions are verified members of [MLE-bench Lite](https://github.com/openai/mle-bench#lite-evaluation). The medical selection is a research choice within that split. Task definitions and metrics are available in the [official competition folders](https://github.com/openai/mle-bench/tree/main/mlebench/competitions).

| Task | Prediction | Main metric | Listed dataset size | Proposed disposition |
|---|---|---|---:|---|
| Histopathologic Cancer Detection | Tumour presence in pathology patches | ROC-AUC | 7.76 GB | First full benchmark candidate |
| APTOS 2019 Blindness Detection | Ordered diabetic retinopathy severity | Quadratic weighted kappa | 10.22 GB | Second candidate; different target structure |
| RANZCR CLiP | Tubes/lines on chest X-rays; multiple labels | Mean ROC-AUC | 13.13 GB | Deferred: inspect documented preparation defect first |
| SIIM-ISIC Melanoma Classification | Melanoma probability | ROC-AUC | 116.16 GB | Deferred until storage/compute and imbalance handling are feasible |

The [current MLE-bench known-issues list](https://github.com/openai/mle-bench#known-issues) documents missing RANZCR sample-submission columns and a HuBMAP information leak. Check the chosen task's preparation and evaluator before the pilot; pin the benchmark revision and document any fixes. Keep an unchanged benchmark evaluation separate from any custom split or repaired-task experiment.

Kaggle downloads require credentials and applicable access/rules. Dataset licenses are separate from the benchmark software license; verify the selected dataset's terms before use. Dataset access and local runtime readiness have not been tested in this preparation phase.

## 5. Learn from winning-solution discussions

Use the supervisor's [Kaggle winning-solutions index](https://www.kaggle.com/code/sudalairajkumar/winning-solutions-of-kaggle-competitions) to find original writeups. It is a discovery aid; cite the original authors for methodological claims.

1. [APTOS first-place solution — Guanshuo Xu](https://www.kaggle.com/competitions/aptos2019-blindness-detection/writeups/guanshuo-xu-1st-place-solution-summary): study validation, external training data, model formulation and ensembles. The author reports abandoning local validation in favour of public-leaderboard feedback. Examine that decision critically when designing an evaluation with an untouched final test set.
2. [SIIM-ISIC first-place solution](https://www.kaggle.com/competitions/siim-isic-melanoma-classification/discussion/175412): study rare positive cases, validation folds, external data, metadata and ensembles. The discussion redirects to the competition's solution writeup.

For each solution, record **data used → validation → preprocessing → model → improvements → compute → limitations**. Separate transferable lessons from techniques tied to that competition. Record external data and pretrained-model provenance.

Reading writeups as the researcher and supplying them to the evaluated agent are different conditions. Keep a record of every source the agent can access. ReX-MLE already includes comparisons with and without winning-solution reports, so retrieval alone cannot be assumed to be a novel thesis contribution.

## 6. Other public medical use cases

- [MedMNIST](https://medmnist.com/): standardized medical image classification datasets, suitable for a small learning/setup exercise. It is a dataset/model benchmark; an AIDE task and evaluator would still need to be specified. Reference-only until an exercise is selected. The resource explicitly states that it is not intended for clinical use.
- [PTB-XL v1.0.3](https://physionet.org/content/ptb-xl/1.0.3/): openly accessible ECG data under CC BY 4.0. Reference-only alternative if the supervisor prefers physiological signals rather than imaging.
- [MIMIC-IV v3.1](https://physionet.org/content/mimiciv/3.1/): clinical records requiring credentialing, training and a data-use agreement. Deferred because access and permitted processing need preparation.

For an example of an agent handling a medical workflow, inspect the public AIDE run examples linked from [ReX-MLE](https://rexrank.ai/ReX-MLE/index.html). Public medical datasets and successful offline predictions do not establish clinical usefulness or safe deployment.

## 7. Proposed setup and exploration plan

### Candidate research question

**Can structured feedback about medical-task evaluation improve AIDE's reliability and held-out predictive performance under a fixed compute budget?**

This is a proposal, not a settled novelty claim. A candidate intervention is a structured report of per-class validation performance supplied to AIDE's Improve operation. Select the actual intervention only after baseline failure analysis and checking related work.

### Technical decisions and reasons

- **Start with one AIDE implementation and one underlying LLM.** This keeps a change to the agent distinguishable from a change to its model.
- **Start with one medical task, then a small justified task set.** This makes setup and cost measurable before a larger commitment.
- **Use the existing project as the home for preparation.** This guide records a proposal; it does not claim completion of an experiment or automatically adopt a curriculum study map.
- **Choose one optimization.** A controlled ablation is easier to interpret than changing prompts, search, tools and LLM simultaneously.
- **Keep final test labels outside the agent's accessible environment.** Use development data/tasks to choose the adaptation and reserve final evaluation for the frozen comparison.
- **Preserve the initial failure rate in reporting.** Report valid submissions and all attempted runs, including failures, so reliability gains are visible.

### Independently checkable steps

1. **Orientation.** Read MLE-bench §2, AIDE §3/Algorithm 1 and ReX-MLE. Produce a one-page explanation of the agent/benchmark/LLM distinction and a short related-work comparison.
2. **Human solutions.** Read the APTOS and SIIM-ISIC writeups. Produce the comparison template from §5, including validation and external-data choices.
3. **Feasibility record.** Confirm medical scope, available hardware/storage, runtime allowance, LLM/API budget and the university's exposé requirements. Record these when known; no deadline or funding amount is assumed here.
4. **Isolated setup.** Follow the [AIDE reference README](https://github.com/WecoAI/aideml) and [MLE-bench agent instructions](https://github.com/openai/mle-bench/blob/main/agents/README.md). Pin code revisions and dependencies. Record the exact LLM models used by coding, feedback and reporting stages. The AIDE reference package declares Python ≥3.10; verify its current installation requirements before creating the environment.
5. **Single-task data preparation.** Configure Kaggle access, then prepare only the chosen task. After installing MLE-bench, its documented command is `mlebench prepare -c histopathologic-cancer-detection`. Verify the resulting file layout, submission schema and evaluator. This command is a future setup step, not a recorded execution.
6. **Baseline smoke run.** Run AIDE once with a small explicit budget. Retain generated code, logs, predictions, validation scores, failure status, elapsed time and API usage. Check submission structure without exposing final test scores; smoke runs and exploration use development/validation feedback only. Reproduce a simple non-agent reference model if needed to diagnose the task/evaluator.
7. **Exploration.** Inspect traces and classify failures: execution/dependencies, data loading, preprocessing, metric errors, resource exhaustion, invalid submissions, model choice, and validation overfitting. Treat these as categories to investigate, not assumed findings.
8. **Freeze a bounded intervention.** Develop it on designated development data/tasks. State the exact difference from baseline and its expected mechanism; keep the final evaluation tasks and labels untouched during this choice.
9. **Controlled evaluation.** Compare baseline and adapted AIDE with matching task data, LLM versions, hardware, time and API limits. Begin with three repetitions for feasibility, then choose a larger repetition budget using observed variability. AIRA's analysis recommends 10–20 seeds per task for more stable rankings; a small pilot does not support broad superiority claims.
10. **Exposé and results.** Write motivation, related work, research question, intervention, evaluation design, feasibility, risks and expected contribution. Keep raw task metrics separate: ROC-AUC and quadratic weighted kappa cannot be averaged as if they were the same scale. Report per-task outcomes, dispersion, failures and cost.

### Risks and evidence of failure

| Risk | How it would show | Response |
|---|---|---|
| Overlap with existing medical-agent work | ReX-MLE or another paper has already tested the same intervention | Refine the question and state the narrower contribution |
| Validation overfitting / leakage | Validation improves but held-out results stagnate; repeated patients/slides cross splits | Audit the data and selection process; preserve test isolation |
| Benchmark preparation defect | Invalid sample schema, leaked answers or failed grading | Use a documented clean task or label a repaired-task experiment explicitly |
| Insufficient compute or repetitions | Few completed runs, wide variability, unstable rankings | Narrow task count, estimate cost from the pilot and limit conclusions |
| Multiple simultaneous changes | Gains cannot be attributed to one mechanism | Freeze one difference and retain matched controls |

### First-week preparation outputs

- One page explaining MLE-bench and AIDE.
- A comparison of the APTOS and SIIM-ISIC solution writeups.
- A shortlist of two medical tasks with access, dataset size, evaluation and compute requirements.
- A one-page exposé skeleton with a candidate question and a clearly bounded experiment.

These are a suggested sequence, not dated commitments or completed work.

## 8. Scope boundaries and open decisions

Current baseline choice: **AIDE**, confirmed by Aram. Open product/research decisions: exact medical use case, final benchmark boundary, primary outcome, compute/API budget, and the exposé format/deadline. Broader biomedical datasets and additional agents are reference-only or deferred as listed above.

Out of scope for this preparation save: conducting experiments, purchasing compute, accepting dataset agreements, contacting the supervisor, claiming clinical validity, declaring learning progress, or publishing the thesis materials. No result, completed reading, mastery or experiment outcome is implied by saving this guide.
