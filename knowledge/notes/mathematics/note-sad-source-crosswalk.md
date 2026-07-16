---
id: note-sad-source-crosswalk
type: note
title: "SaD L01–L15 — Source Crosswalk (narrative & sequencing rationale)"
created: "2026-07-02"
role: crosswalk
state: evolving
authorship: mixed
concepts: [concept-descriptive-statistics, concept-probability, concept-combinatorics,
  concept-random-variable, concept-discrete-distributions, concept-normal-distribution,
  concept-statistical-estimation, concept-hypothesis-testing, concept-decision-trees,
  concept-k-nearest-neighbors, concept-naive-bayes, concept-neural-network]
sources: [source-sad-ss26-lectures, source-teschl-mathe-informatiker,
  source-fahrmeir-statistik, source-blitzstein-hwang, source-openintro-statistics,
  source-dekking-mips, source-kelleher-fmlpda, source-fau-klausur-ws1415,
  source-fahrmeir-arbeitsbuch, source-sad-uebungen, source-mit-1805,
  source-sad-2025-recordings]
contexts: [workspace-m2-exam-prep]
---

> **Migration note (2026-07-17, Stage-1 pilot):** decomposed from
> `Plans/Math/sad/SaD_Source-Crosswalk_L01-L15.md` (legacy tree, created KW 27,
> Jul 2 2026). Per the v3 architecture, this note now carries **narrative and
> sequencing rationale only**. The per-lecture 📒/🎥/🧪 judgment tables live
> canonically as evaluations on the source records; the per-lecture selector is
> rendered by the source index (rebuild with `python tools/generate.py`).
> **Stage-2 update (2026-07-17):** the KW-29 difficulty ladder
> (`SaD_Book-Difficulty-Map_L01-L15.md`) is now decomposed too — the four
> probability-ladder books (Pitman 🟡, Ross 🔴, Tijms 🟢, Schaum's 🧮) are source
> records with their difficulty roles; `The Principles of Probability.pdf` is
> off-topic (math logic) and stays excluded. Ladder rule: the 5 probability
> books only help L04–L08; descriptive/inference/ML stay on
> Dekking/OpenIntro/Fahrmeir/Kelleher. The gentle escape hatch from Blitzstein
> is usually Tijms or OpenIntro, Pitman as the middle rung, Schaum's for drill.

# SaD L01–L15 — Source Crosswalk (narrative)

*The SaD twin of the AML book crosswalk. Originally one row per lecture with three
scope-flagged layers (books · videos · testing); those judgments are now source
records — this note keeps the rules that made the crosswalk work.*

## Ground rules (same as AML)

**Scope-to-lecture:** pull named sections, never whole chapters. Multiple sources
per topic *by design* — each shines on a different aspect — but every lecture has
ONE primary. Only locally-verified sources get page numbers; chapter-level cites
(Blitzstein, OpenIntro) must be verified against the PDFs on first use.

**Scope discipline:** ESL tree/forest chapters are grad-level; Blitzstein goes past
SaD in places (moment generating functions, story proofs galore) — pull the named
chapters only.

## Division of labor

This crosswalk *selects sources*; the detailed study guides stay authoritative
where they exist:

- **SaD 06–10** → the probability/inference deep plan (legacy:
  `Plans/Math/sad/SaD/notes/SaD_06-10_Probability-Inference_DeepPlan.md` — Stage 2);
- **SaD 03** → `note-regression-sad-aml-islp-bridge` (Tiers 0–5 are the canonical
  treatment; already maps Fahrmeir Ch 3, ISLP Ch 3, AML L03/L04);
- **SaD 13/15** → the AML-side selector rows (L02 / L08–L09) — point there instead
  of duplicating;
- **Block N** (Chat1) remains the exam-prep program: the testing tier feeds
  clusters N1–N5; per-lecture units are the study scripts where they exist
  (`note-sad-l02-descriptive-basics` + `note-sad-l02-exercise-bank` for L02; the
  L01/L03/L04/L05 units are still legacy files — Stage 2).

## Reading ladder per stats topic

OpenIntro (gentle, EN) → **Fahrmeir (course notation, DE — the exam layer)** →
Blitzstein (depth/why) → 18.05 notes (practice-nearest). **Pick two, not all four.**

Correction (KW 28, from L01 slide 40): the *officially-named* primary stats text is
**Teschl & Teschl** (+ Kelleher for the ML half) — NOT Fahrmeir. Fahrmeir stays the
notation-matched exam layer.

The **SaD-2025 recordings** are the highest-value video source — same course, one
year older; always the first video pick. The 2026↔2025 numbering map is in the
legacy brain (SEMESTER-STATUS §3 — Stage 2).

## Why these testing sources

The course publishes no Altklausuren, so the Klausur tier is external: the **FAU
WS14/15 Klausur pair** is the top pick (two complete German exams with full
solutions, content-matched to clusters N1–N4); **Dekking** doubles as book and
drill (~300 solved-answer exercises); the **UE sheets** are the course's own
format — solutions are only walked through in the Übung, so collect them there.
Kelleher's worked toy examples are the exam format for the ML half (SaD 12–15) —
its four learning families map 1:1 onto those lectures (TOC-verified Jul 2).
