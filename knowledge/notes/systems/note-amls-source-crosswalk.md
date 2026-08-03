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

> **Migration note (2026-07-17, Stage 2; corrected 2026-08-03):** decomposed
> from `Plans/ML/systems/AMLS-Source-Crosswalk.md` (legacy tree, created KW 27,
> book layer Jul 4). Per-lecture scope, locators and source roles now live in
> the 13 module-owned lecture units and their study maps. The recovered SS26
> paper inventory was wired on 2026-08-03 after a source-completeness review.
> Source-wide judgments remain on source records; exam facts live only in the
> owning partitioned AMLS module. This note keeps the integration rules.

# AMLS source crosswalk (narrative)

The **SS26 Architecture of ML Systems** course bundle is primary. All 13 decks
and `AMLS-Source-Papers-Reading-List.md` are local and reachable through the
registered `material://` source, verified 2026-08-03. The reading list preserves
**60 curated must-reads** and **283 lecture-grouped bibliography entries**
recovered from inline slide citations. Lecture 12 remains visibly qualified:
its title page says "Last update: Jul 09, 2025" although it occupies the SS26
Lecture 12 slot. The unit preserves that stamp anomaly rather than inventing
certainty.

The exam is **written**, so evidence is written: diagrams, hand calculations,
short explanations and timed questions. The official 90-minute, 100-point
sample in Lecture 13 pages 36–48 is the module-level mock.

## The S.X integration rules

1. **Source completeness precedes selection.** Every source named by a course
   artifact, authoritative template, bibliography or preserved plan remains
   reachable and is explicitly selected, reference-only, or deferred with a
   reason. Registered source IDs are not an inventory count. Silent omission
   is forbidden.
2. **One lecture spine, one standard shape.** Every lecture uses exactly three
   passes: scope from mp4 + deck, primary-paper and targeted-source integration,
   then closed-book evidence. The older Block A–H Chat2 plan remains
   reference-only.
3. **Slides as taught set scope.** Supplementary sources may clarify, derive,
   implement or test a deck concept; they do not add syllabus topics. Every
   curated paper is triaged against a deck anchor rather than read as new scope.
4. **DMMLS is the lecturer-authored prose spine** for lectures 02–06 and
   09–11. It is campus-licensed and still needs acquisition; section names are
   verified against its TOC on first open before page numbers are cited.
5. **Volume discipline.** MLSysBook Vol 1 and Vol 2 are local but are always
   chapter-picked. Their checkpoints/SocratiQ material becomes written drill
   where the official sample, MIT 6.172 or CMU 10-414 has no matching item.
6. **Implementation and calculation stay targeted.** MLC serves lectures
   03–04; Ultra-Scale serves 05–07; How to Scale Your Model serves 07–08;
   Huyen serves 10–13; CMU 10-414, MIT 6.172 and Stanford CS149 supply the
   checkable implementation/performance questions routed by the unit maps.
7. **Free-first.** Nothing in the 11 registered supporting-source plan or the
   linked paper spine requires a purchase. Optional Huyen *AI Engineering*,
   PMPP and Sze depth remains collected and reference-only unless a marked mock
   exposes a specific gap.

## Unit-build order and depth

The current module order is **03, 04, 05, 08, 09 → 06, 07 → 10, 11, 12, 13 →
01, 02 → module mock**.

- Lectures 03, 04, 05, 08 and 09 use the full evidence pass: reference,
  source-tagged drills and a lecture mock.
- Lectures 06, 07 and 11 use reference plus drills.
- Lectures 01, 02, 10, 12 and 13 use reference plus closed-book recall.
- Every lecture integration stage exposes all of its curated primary papers
  directly and retains the complete slide-citation section as reference-only.
  Each curated item must be marked read, skimmed, or deferred with a reason and
  a deck anchor.
- `unit-amls-theory` is retained as the final module-wide mock/remediation unit;
  its former placeholder history remains in Git rather than being deleted.

This uneven depth is deliberate. Extra artifact work is opened only when the
technical core or marked module mock demonstrates a concrete need.

## Project synergies worth keeping visible

Lecture 10 (data acquisition/preparation) connects to Aram's own **mlprov**
work; Lecture 12 connects to his **fairlearn + Captum/saliency** project work;
and the CMU 10-414 computation-graph material in Lectures 03–04 also supports
AML backpropagation preparation. These are reuse opportunities, not extra AMLS
scope.
