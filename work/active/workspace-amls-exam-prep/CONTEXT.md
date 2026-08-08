---
id: workspace-amls-exam-prep
type: workspace
title: AMLS written exam prep — S.X track (last August sitting)
created: '2026-07-17'
status: active
standing: false
concepts:
- concept-ml-systems
- concept-program-rewrites
- concept-operator-fusion
- concept-data-parallelism
- concept-parameter-servers
- concept-llm-systems
- concept-hardware-accelerators
- concept-data-access-optimization
- concept-ml-lifecycle
- concept-ml-fairness-explainability
- concept-model-serving
notes:
- note-amls-source-crosswalk
sources:
- source-amls-ss26-lectures
- source-dmmls-boehm
- source-mlsysbook-vol1
- source-mlsysbook-vol2
- source-ultrascale-playbook
- source-htsym-scaling-book
- source-mlc-book
- source-huyen-dmls
- source-cmu-10414
- source-mit-6172
- source-stanford-cs149
program_ids:
- program-bachelors
module_ids:
- module-hu-amls
unit_ids:
- unit-amls-l03
- unit-amls-l04
- unit-amls-l05
- unit-amls-l08
- unit-amls-l09
- unit-amls-l06
- unit-amls-l07
- unit-amls-l10
- unit-amls-l11
- unit-amls-l12
- unit-amls-l13
- unit-amls-l01
- unit-amls-l02
- unit-amls-theory
---

# AMLS exam prep — S.X

## Objective

Convert the 13-lecture AMLS backlog into page-located references,
written drills and one module-wide timed mock. Administrative attempt,
sitting and registration facts remain in the owning AMLS module; this
workspace owns only the preparation effort and its next action.

## Current Scope

*Required now* — use the lecture spine in exam-value order: **03, 04, 05,
08, 09 → 06, 07 → 10, 11, 12, 13 → 01, 02**, followed by the
module-wide 90-minute mock. Every lecture unit uses the same three passes:
**scope (mp4 + deck) → primary-paper and targeted-source integration →
closed-book evidence**.

The SS26 course bundle includes the recovered paper inventory: **60 curated
must-reads** across all 13 lectures and **283 lecture-grouped bibliography
entries** extracted from the slide citations. Every curated paper is a direct
stage resource. Every full lecture bibliography is retained as reference-only;
an item may be deferred, but it may never disappear silently.

**Preserving all of it is the operator's job; reading all of it is not yours
(2026-08-08, normalization items 4–5).** Source-completeness is discharged once
at plan-creation time (WORKFLOWS.md) — it must never appear as a stage
`done_when` telling you to disposition every paper. Each stage resource now
carries its own `scope_triage`, so a lecture reads as a fast route with the
depth still attached:

| rank | what it is | what you do |
|---|---|---|
| `required-now` | the deck/recording, the lecture's own system paper, the closed-book evidence | the exam core — this is the lecture |
| `helpful-now` | book chapter, executable notebook | reach for it when the deck alone doesn't land |
| `deferred` | the further curated papers | depth; read if the lecture is one of the deep ones, skip without guilt otherwise |
| `reference-only` | the full slide-citation bibliography | preserved so it is never lost; not reading material for this stage |

The ranking is **mechanical, not a verdict on any paper**: first curated paper
per lecture = required (it is the lecture's own system paper in all 13 cases —
SystemML for Compilation, fusion for Advanced Compilation, RDD for Execution
Strategies, DistBelief for Parameter Servers, Attention for LLMs, Roofline for
Hardware, CLA for Data Access, Deequ for Data Sourcing, AlexNet for Model
Selection); the rest are depth. Re-rank any individual paper freely — that is a
presentation choice about a stage, not a change to the source's own evaluation.

At ~66 h of planned work, the required-now spine is what fits the remaining
window; the deferred tier is what you drop first if time gets short.

Depth is deliberately uneven: full reference + drills + lecture mock for
03/04/05/08/09; reference + drills for 06/07/11; reference + recall for
01/02/10/12/13. The module source map also routes the 11 registered supporting
source identities from the AMLS crosswalk; source-ID coverage is not treated as
a substitute for paper-inventory coverage.

*Helpful now* — acquire DMMLS through the campus license before its first
routed second pass. MLSysBook volumes are chapter-picked, never read linearly.

*Reference only* — the legacy Chat2 Block A–H plan in `inputs/`; its topic
grouping remains useful context, but it is not the current study script.

## Open Questions

- Lecture 12's deck is present, but its title page says "Last update: Jul
  09, 2025". Treat this as a source-stamp anomaly until the chair/course
  page confirms whether the SS26 upload intentionally reused the deck.
- Course-run exam registration formality for the chosen sitting: verify
  the TU/MOSES or chair-side action recorded in the owning module.

## Next Action

Start `unit-amls-l03`, stage `stage-amls-l03-scope`: watch the SS26
recording and build the page-located outline for **03 Compilation – Size
Inference and Rewrites** (43 pages). Then enter the integration stage and read
the one `required-now` paper — **SystemML: Declarative Machine Learning on
Spark** — closely enough to state its mechanism and the result the deck leans
on. The other three curated L03 papers are ranked `deferred`: available as
depth, not a checklist. Finish at the evidence stage, closed book.

## Durable Notes

`note-amls-source-crosswalk` carries the source-completeness and integration
rules. The complete paper inventory remains in the SS26 course material; each
unit records its selected paper use and per-stage feedback. Durable
understanding from S.X sessions should land as notes in
`knowledge/notes/systems/`.

## Deferred

- Extra artifact depth for the light and mid-tier lectures is deferred until
  the technical-core units and the module mock expose a concrete gap.
- Huyen *AI Engineering*, PMPP, Sze and other optional GPU/serving sources stay
  collected and explicitly reference-only unless a marked mock selects them.
- A paper may be deferred only with a recorded reason and deck anchor; no
  authoritative template, bibliography or course-artifact source may be
  silently omitted.
