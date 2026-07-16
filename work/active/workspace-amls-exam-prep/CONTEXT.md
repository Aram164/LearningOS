---
id: workspace-amls-exam-prep
type: workspace
title: "AMLS written exam prep — S.X track (last August sitting)"
created: "2026-07-17"
status: active
standing: false
concepts: [concept-ml-systems, concept-program-rewrites, concept-operator-fusion,
  concept-data-parallelism, concept-parameter-servers, concept-llm-systems,
  concept-hardware-accelerators, concept-data-access-optimization,
  concept-ml-lifecycle, concept-ml-fairness-explainability, concept-model-serving]
notes: [note-amls-source-crosswalk]
sources: [source-amls-ss26-lectures, source-dmmls-boehm, source-mlsysbook-vol1,
  source-mlsysbook-vol2, source-ultrascale-playbook, source-mit-6172, source-cmu-10414]
---

# AMLS exam prep — S.X

## Objective

Pass the AMLS written exam at the chosen sitting (the LAST course-run slot —
attempt and date in records/modules.yaml). The project prerequisite is done
(submitted 2026-07-15, up to +5 bonus points). This is now the FIRST exam on
the calendar — the S-block processing backlog (lectures attended, not
processed) gets cleared here.

## Current Scope

*Required now* — process lectures in unit-build priority order: **03–05 +
08–09** (the A-part technical core, where 6.172/10-414 testing exists), then
06–07, then 10–13 lifecycle. Per lecture: mp4 → slides → ⭐ book item → 🧪
drill (the per-lecture selector is in the generated source index).

*Helpful now* — pull DMMLS via the Springer campus license (one pull, ~173 pp —
the lecturer's own survey, exam-nearest prose); MLSysBook SocratiQ quizzes for
rows without 6.172/10-414 material.

*Defer* — building full AML-style 4-file units for lectures without testing
material; Huyen AIE / PMPP / Sze depth picks.

*Reference only* — the legacy Chat2 plan (S blocks; copy in `inputs/`) — its
block structure holds, its calendar is stale.

## Open Questions

- Lectures 12–13: slides/mp4 posted yet? (legacy Open Loop #6 — check the
  course page.)
- tubcloud mp4 links: click-test one on first use (cited from the course page,
  not yet opened — legacy Open Loop #7).
- Course-run exam registration formality for the chosen sitting — anything to
  do besides showing up? Verify once on the course page/Moodle.

## Next Action

Session 1 of the S.X track: lecture 03 (Size Inference, Rewrites, Operator
Selection) — mp4 + slides, then MLC tensor-program chapter, then 10-414 HW1
autodiff parts as drill. (Synergy: the computation-graph half also services AML
L09 backprop prep.)

## Durable Notes

`note-amls-source-crosswalk` carries the integration rules; per-lecture
judgments live on the source records. Durable understanding from S.X sessions
should land as notes in `knowledge/notes/systems/`.

## Deferred

- Per-lecture unit builds for 01–02, 06–07, 10–13 — only if the core-five
  processing leaves time before the sitting (decision 2026-07-17: core first).
