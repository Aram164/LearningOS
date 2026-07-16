---
id: note-amls-source-crosswalk
type: note
title: "AMLS — Source Crosswalk (narrative & S.X integration rules)"
created: "2026-07-02"
role: crosswalk
state: evolving
authorship: mixed
concepts: [concept-ml-systems, concept-program-rewrites, concept-operator-fusion,
  concept-data-parallelism, concept-parameter-servers, concept-llm-systems,
  concept-hardware-accelerators, concept-data-access-optimization,
  concept-ml-lifecycle, concept-ml-fairness-explainability, concept-model-serving]
sources: [source-amls-ss26-lectures, source-dmmls-boehm, source-mlsysbook-vol1,
  source-mlsysbook-vol2, source-ultrascale-playbook, source-htsym-scaling-book,
  source-mlc-book, source-huyen-dmls, source-cmu-10414, source-mit-6172,
  source-stanford-cs149]
contexts: [workspace-amls-exam-prep]
---

> **Migration note (2026-07-17, Stage 2):** decomposed from
> `Plans/ML/systems/AMLS-Source-Crosswalk.md` (legacy tree, created KW 27,
> book layer Jul 4). Per-lecture slide/mp4 links, the book shelf, and the
> per-lecture reading map live canonically as evaluations on the source
> records; exam facts (written 100%, sittings, chosen slot) live ONLY in
> `records/modules.yaml`. This note keeps the integration rules.

# AMLS source crosswalk (narrative)

Keyed to the **official SS26 course page** (verified Jul 2) — it links slides
AND mp4 recordings for every held lecture, which retired the old SS23-archive
workaround. The exam is **written**, so all prep is written drill, not
explain-aloud (this corrected an older oral-exam assumption).

## The S.X integration rules

1. **mp4 + slides stay primary.** Watch the lecture's mp4 → slides → self-test.
   The book layer is the *second pass* per lecture, then the testing column.
2. **DMMLS (the lecturer's own ~173 pp survey) is the spine of the book layer
   for the A-part core (lectures 02–06, 09)** — expect exam phrasing to echo
   it. One Springer-license pull. Read by section, never linearly.
3. **Volume discipline:** MLSysBook Vol 1 + Vol 2 ≈ 2200 pp — chapter-pick per
   the per-lecture map on the source records, never read linearly. SocratiQ
   quizzes double as written drill where no 6.172/10-414 material exists.
4. **Free-first:** everything except DMMLS (campus license) and the optional
   AIE/PMPP/Sze depth picks is free or local. Nothing needs buying.
5. **Géron is NOT a systems book** — project/AML support only; don't
   keyword-match it into exam prep.

## Unit-build order (for the chosen sitting)

Per-lecture 4-file units (AML-style) get built during S.X prep — priority:
**03–05 + 08–09** (the A-part technical core, where 6.172/10-414 testing
exists), then 10–13 lifecycle (MLSysBook quizzes). Lectures 12–13 slides/mp4
were still pending — check the course page (legacy Open Loop #6). Sourcing
honesty: Vol 2 chapter names are TOC-verified; Vol 1, DMMLS and Huyen-AIE are
cited by chapter *theme* — verify against the PDF TOC before citing page
numbers in S.X units.

## Project synergies worth keeping visible

Lecture 10 (data sourcing/cleaning) wires to Aram's own **mlprov** code; lecture
12's lab is his own **fairlearn (M.4.x) + Captum/saliency (Task 1.4)** project
code; the 10-414 autodiff lectures double-pay for AML L09 (computation graphs).
