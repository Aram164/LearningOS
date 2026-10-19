---
id: workspace-thesis-mle-medical
type: workspace
title: Bachelor thesis — Exploring & optimizing MLE agents for medical use cases
created: '2026-07-20'
status: active
program_ids:
- program-thesis-projects
module_ids:
- module-project-bachelor-thesis
unit_ids:
- unit-thesis-landscape
- unit-thesis-experiments
project_id: project-bachelor-thesis
---

# Thesis — Exploring and optimizing MLE agents for medical use cases

## Objective

Scope, run and improve **machine-learning-engineering (MLE) agents** on
**medical tasks**. Working title (Aram, 2026-07-20): *"Exploring and optimizing
MLE agents for medical use cases."* The supervisor's brief has four threads:
(1) survey **MLE-bench and its variants**; (2) isolate the **medical subset** of
those benchmarks and the **openly available use-cases of MLE in medicine**;
(3) an **exploration phase** to adjust the agents to the specific medical
use-case; (4) start testing the given baseline setup, **"AID" = AIDE** (the
tree-search reference agent from MLE-bench). Study winning-solution write-ups to
understand what strong solutions look like.

The full landscape survey + exploration/optimization plan is the deliverable:
`outputs/thesis-landscape-and-plan.md`. The original brief is captured verbatim
in `inputs/original-thesis-brief.md`.

## Current Scope

> **Time budget is set by COORDINATION.md, not by this workspace.** Through the
> autumn exam cluster the thesis runs on *slack only* — it never displaces the
> next exam. The scope below is what to do **when thesis time is allocated**;
> it is not a claim on today. The thesis becomes the primary effort after the
> M2 Klausur (Phase D).

*Required when thesis time is allocated* — (a) confirm the scope boundary with
the supervisor (MLE-bench medical subset only, or extend to BioML-bench /
ReX-MLE); (b) stand up the AIDE ("AID") setup and reproduce its baseline on the
**4 low-complexity medical tasks** that sit inside MLE-bench Lite:
`aptos2019-blindness-detection`, `histopathologic-cancer-detection`,
`ranzcr-clip-catheter-line-classification`,
`siim-isic-melanoma-classification`.

*Helpful now* — read the exploration paper (arXiv 2507.02554) and the
BioML-bench paper (they already benchmark AIDE on biomedical tasks and name its
failure modes); skim the Kaggle winning-solutions index for the medical
competitions in scope.

*Defer* — the full 13-task clinical evaluation and any agent-vs-agent comparison
(MLE-STAR / R&D-Agent) until the AIDE baseline reproduces and a compute budget is
fixed.

*Reference only* — the broader MLE-agent scaffold zoo (ML-Master, DS-Agent,
AutoKaggle, MLE-Dojo, OpenHands) and the clinical LLM-agent benchmarks
(MedAgentBench, ABRA, AgentRx) — context for the thesis background, not the
build.

## Open Questions

- **Scope of benchmarks:** MLE-bench medical subset only, or also BioML-bench
  (biomedical, built on MLE-bench) and/or ReX-MLE (medical imaging)?
- **Compute:** GPU access and wall-clock budget? Imaging tasks need a GPU
  (BioML-bench used one NVIDIA L4, 16 h/task); tabular/omics ran CPU-only, 8 h.
- **Agents in scope:** AIDE only, or AIDE vs. MLE-STAR / R&D-Agent as a
  comparison arm?
- **What "optimizing" is graded on:** capability (medal rate / leaderboard
  percentile) vs. reliability (valid-submission rate) vs. cost/time.
- **Base LLM(s)** allowed and their budget (confounds agent-design effects —
  BioML-bench's caveat).
- **Bachelor vs. Master thesis** — recorded as **Bachelor**, stated by Aram
  2026-07-20. This is settled in the repository: the module is
  `module-project-bachelor-thesis` under `program-bachelors`. (Resolved
  2026-08-08: this line previously said "reconcile with the MSc profile in
  memory" — a durable record must never defer to an external agent's
  conversational memory for its own facts. If the degree level ever changes,
  Aram says so and the module record changes.)

## Next Action

*(Slack-time action — see the Current Scope banner.)* Confirm the scope boundary
+ compute budget with the supervisor (one email/meeting), then stand up the AIDE
("AID") environment and run it once on `histopathologic-cancer-detection`
(smallest medical Lite task) to establish the baseline medal /
valid-submission / cost numbers. Details in
`outputs/thesis-landscape-and-plan.md` §6 (Exploration phase — Phase 0).

## Deferred

- Registering any exam/registration/deadline facts — none exist yet; when the
  thesis is formally registered, the dates go in
  `curriculum/modules/module-project-bachelor-thesis/module.yaml`, not here.
- Extracting durable ML-agent concepts (tree search, best-first exploration,
  case-based reasoning) into `knowledge/notes/machine-learning/` — do this once
  the reading settles, not from the survey draft.
