---
id: workspace-thesis-mle-medical
type: workspace
title: Bachelor thesis — Exploring & optimizing MLE agents for medical use cases
created: '2026-07-20'
status: active
program_ids:
- program-bachelors
module_ids:
- module-project-bachelor-thesis
unit_ids:
- unit-thesis-landscape
- unit-thesis-experiments
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

When thesis time is allocated under [coordination](../../COORDINATION.md), start the [AIDE medical MLE preparation guide](../../../knowledge/notes/machine-learning/note-bachelor-thesis-medical-mle-exploration.md): read MLE-bench §2, AIDE §3/Algorithm 1 and ReX-MLE, then compare the APTOS and SIIM-ISIC solution writeups. Produce a one-page orientation and a two-task feasibility shortlist. Confirm the medical scope and compute/API budget with the supervisor before the first AIDE pilot; keep final test scores reserved until the adaptation is frozen. The earlier landscape survey remains in outputs/thesis-landscape-and-plan.md.

## Deferred

- Registering any exam/registration/deadline facts — none exist yet; when the
  thesis is formally registered, the dates go in
  `curriculum/modules/module-project-bachelor-thesis/module.yaml`, not here.
- Extracting durable ML-agent concepts (tree search, best-first exploration,
  case-based reasoning) into `knowledge/notes/machine-learning/` — do this once
  the reading settles, not from the survey draft.


## Research context

<a id="project-bachelor-thesis"></a>

```yaml
id: project-bachelor-thesis
type: project
title: Bachelor thesis
project_type: thesis
status: active
objective: 'Scope, run and improve machine-learning-engineering (MLE) agents on medical
  tasks. Working title (Aram, 2026-07-20): *"Exploring and optimizing MLE agents for
  medical use cases."* The supervisor''s brief has four threads: (1) survey MLE-bench
  and its variants; (2) isolate the medical subset of those benchmarks and the openly
  available use-cases of MLE in medicine; (3) an exploration phase to adjust the agents
  to the specific medical use-case; (4) start testing the given baseline setup, "AID"
  = AIDE (the tree-search reference agent from MLE-bench). Study winning-solution
  write-ups to understand what strong solutions look like.'
root_uri: github://Aram164/LearningOS
linked_module_ids:
- module-hu-aml
- module-hu-amls
unit_ids:
- unit-thesis-landscape
- unit-thesis-experiments
workspace_ids:
- workspace-thesis-mle-medical
thematic_group_ids:
- thematic-group-machine-learning
- thematic-group-data-systems
```


## Workstreams

<a id="workstream-thesis-landscape"></a>
<a id="step-thesis-scope"></a>
<a id="step-thesis-survey"></a>
<a id="workstream-thesis-experiments"></a>
<a id="step-map-thesis-baseline"></a>
<a id="step-thesis-aide-baseline"></a>
<a id="step-thesis-optimization"></a>

```yaml
structure:
  kind: parallel
  nodes:
  - children:
    - id: step-thesis-scope
      kind: step
      status: active
      title: Confirm scope and compute budget
    - id: step-thesis-survey
      kind: step
      status: active
      title: Map MLE-agent and medical benchmark landscape
    id: workstream-thesis-landscape
    kind: workstream
    status: active
    title: Landscape and scope
  - children:
    - children:
      - id: step-thesis-aide-baseline
        kind: step
        status: planned
        title: Reproduce the AIDE baseline
      - id: step-thesis-optimization
        kind: step
        status: planned
        title: Run bounded optimization comparisons
      id: step-map-thesis-baseline
      kind: step-map
      status: planned
      title: Baseline reproduction map
    id: workstream-thesis-experiments
    kind: workstream
    status: planned
    title: Baseline and optimization experiments
```


## Research decisions

<a id="decision-thesis-scope-boundary"></a>
<a id="decision-thesis-compute-budget"></a>

```yaml
decisions:
- id: decision-thesis-scope-boundary
  status: open
  summary: Decide whether the thesis stays within the MLE-bench medical subset or
    includes BioML-bench/ReX-MLE.
  title: Benchmark scope
- id: decision-thesis-compute-budget
  status: open
  summary: Confirm GPU access, wall-clock limits, and allowed model/API budget before
    experiments.
  title: Compute budget
```


## Materials and deliverables

<a id="relationship-thesis-amls"></a>
<a id="relationship-thesis-project-toolbox"></a>
<a id="relationship-thesis-landscape-plan"></a>

```yaml
files:
- kind: input
  label: Original thesis brief
  path: work/active/workspace-thesis-mle-medical/inputs/original-thesis-brief.md
- kind: output
  label: Landscape and experiment plan
  path: work/active/workspace-thesis-mle-medical/outputs/thesis-landscape-and-plan.md
- kind: output
  label: AIDE medical MLE — setup, reading path and exploration plan (2026-10-23)
  path: knowledge/notes/machine-learning/note-bachelor-thesis-medical-mle-exploration.md
relationships:
- id: relationship-thesis-amls
  from_project_id: project-bachelor-thesis
  to_id: module-hu-amls
  to_type: module
  relation_type: informs
  reason: Advanced ML Systems is the closest active module to the thesis systems questions.
  contribution: Provides systems vocabulary, evaluation discipline, and reference
    methods for the experiments.
- id: relationship-thesis-project-toolbox
  from_project_id: project-bachelor-thesis
  to_id: project-toolbox
  to_type: topic-pack
  relation_type: uses
  reason: The Project Toolbox is the narrow working shelf chosen for this project.
  contribution: Keeps implementation and experiment-support materials in a deliberate
    working order.
- id: relationship-thesis-landscape-plan
  from_project_id: project-bachelor-thesis
  to_id: file-thesis-landscape-plan
  to_type: file
  relation_type: produces
  reason: This is the project-owned planning output for the current thesis scope.
  contribution: Stores the evidence landscape, bounded experiment design, and unresolved
    decisions.
  path: work/active/workspace-thesis-mle-medical/outputs/thesis-landscape-and-plan.md
```


## Milestone identities


```yaml
milestone_ids:
- milestone-thesis-scope
- milestone-thesis-baseline
```

```yaml
owners:
  milestone-thesis-scope: unit-thesis-landscape
  milestone-thesis-baseline: unit-thesis-experiments
```


## Boundaries


```yaml
boundaries:
  confidentiality: private
  external_code_access: approved
  notes: Employer code and Job/ remain outside this project record.
```


## Migration provenance


```yaml
schema_version: 1
revision: 0
migrated_at: '2026-08-06T04:04:58+00:00'
migrated_from: module-project-bachelor-thesis
migration: projects-v1
source_sha256: 36e7794a93591ae62a9c70e6a5b1b310ebabec6caebef9041e540e76c67f6ff7
```
