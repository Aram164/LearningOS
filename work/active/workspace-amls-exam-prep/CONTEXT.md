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
Inference and Rewrites** (43 pages). Then enter the integration stage and
triage all four curated L03 primary papers before the supplementary books and
courses; record read/skim/defer-with-reason for each.

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
