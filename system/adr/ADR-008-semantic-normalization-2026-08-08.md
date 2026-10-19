# ADR-008 — Semantic normalization pass

**Date:** 2026-08-08
**Status:** accepted
**Scope:** live data and prose only. No entity types, no new hierarchy, no
feature work. One schema addition (data contract v1 → v2).

## Context

An external review read the repository cold — contracts, coordination, every
active workspace, module records, and the AMLS / AML / M2 / thesis / Algo 2
study maps — and reached a conclusion worth acting on:

> The architecture and the newer curriculum are strong. The repository is
> carrying **two generations of semantics at once**: the module-first system,
> and residue from the pre-cutover planning state.

The finding was not "redesign". It was that several live files had not caught up
with rules the architecture already states, and a cold reader could therefore
derive the wrong current state. Since the whole point of this repository is that
an agent can read it cold and reach the same interpretation Aram would, that is a
correctness bug, not untidiness.

Verified before acting — each of these was real:

- `records/modules.yaml` opened with "the single canonical owner of
  administrative module facts", while `CLAUDE.md` hard rule #2 calls it a frozen
  compatibility snapshot and the partitioned `curriculum/modules/<id>/module.yaml`
  records already held every fact.
- `workspace-algo2-exam-prep` said "DROPPED … no study time allocated" and
  "Next Action: None", and simultaneously "*Required now* — book the
  Prüfungstermin".
- `workspace-aml-exam-prep` said "parked … nothing before mid-August", the rule
  `COORDINATION.md` explicitly superseded on 2026-07-25 with the AMLS↔AML
  synergy decision.
- 55 migrated stages carried `exam_critical: false` while their own prose said
  "Exam-relevant", "the heart of the lecture", "High exam value". Operator-built
  plans used the field deliberately (101 true / 6 false); migrated ones had a
  mechanical default.
- Three resources pointed neural-network videos at `source-3b1b-linear-algebra`.
- All 13 AMLS integrate stages required the learner to disposition every curated
  paper — the operator's plan-creation gate, copied into learner gates.

## Decision

Six changes. Nothing was deleted; educational content was preserved verbatim.

1. **Authority.** `records/modules.yaml` is banner-marked as owning nothing, and
   every live pointer to it now names the owning `module.yaml`
   (`COORDINATION.md`, four workspaces, `SPEC-README.md`, `BUILD-SPEC.md`).
   Historical migration records keep their original wording; a stale
   *instruction* was corrected, a stale *record* was annotated.

2. **Current state.** AML reconciled to the synergy policy (what is deferred is
   AML *exam-specific* prep, not AML learning); Algo 2's reinstatement plan
   separated from live scope so a blocked workspace has no imperatives; M2 given
   an explicit Resume-vs-Planned-Next split; thesis scope subordinated to the
   coordination slack policy.

3. **Migrated maps normalized.** 31 `exam_critical` corrections in AML L02–L07
   and 28 in M2 SaD L01–L05 — content and practice stages to `true`, with
   `unit-m2-sad-l01/stage-04` left `false` and commented, because its own
   objective says "Non-examinable". Two wrong source IDs corrected, eight
   missing ones added, 15 pre-ADR-007 filesystem paths stripped from labels
   (page and section references kept).

4. **Learner scope ≠ inventory completeness.** The 13 AMLS learner gates now ask
   for the lecture's primary paper; the completeness obligation is stated in
   `WORKFLOWS.md` as binding the operator and never the learner. All 60 curated
   papers and 283 bibliography entries remain wired exactly as before.

5. **Resource-level triage (data contract v2).** Stage resources gained an
   optional `scope_triage` using the stage's own four-value vocabulary. Without
   it, a required stage's deck, fallback video, depth paper and preserved
   bibliography all render identically. Applied to 150 AMLS resources by a
   mechanical rule (first curated paper = required, rest = deferred, full
   bibliography = reference-only), which is a presentation decision about a
   stage and never edits a source's own evaluation.

6. **Compatibility presentation.** `unit-m2-sad-l06-l10` marked as the
   `lecture-cluster` it is; ARCHITECTURE invariant 22a now requires interfaces to
   render `kind` rather than list units flat. AMLS and the thesis gained
   `thematic-group-ml-systems`; the platform-regulation seminar moved off
   `thematic-group-algorithms`.

   **Superseded 2026-08-12:** the SaD semantic redesign retired that compatibility
   aggregate in favor of independent L06–L10 knowledge maps and complete
   material-choice menus. This paragraph remains the historical decision record.

## Consequences

- `make check`: 0 errors. Suite: 228 passed, 1 skipped. Contract v2 matches 21
  record schemas.
- Two tests were changed, both to assert the corrected semantics rather than to
  pass: the AMLS inventory test now asserts the operator gate has *not* leaked
  into a learner `done_when`, and the rollback-evidence test now asserts data
  equality plus the frozen-snapshot banner instead of whole-file byte equality.
  A third failure was mine — I had written a literal exam date into workspace
  prose, and `test_scenario_7` correctly caught it. That test was left alone and
  the prose fixed.
- Fixture `v2` is frozen and added to `FORMATS`. It deliberately includes one
  unranked resource, because unranked is what every v1 record carries and the
  loader must keep accepting it.

## Follow-up (same day, after review of commit `e2e26be`)

A review of the landed commit found the authority rule enforced in the *pointers*
but not in the *dates themselves*: live workspace prose still restated
administrative facts the module records own — `after AML on 30.09`, `the 09.10
sitting`, `2.-PZ Anmeldung (31.08–10.09)`, `unnecessary depth before 09.10`.
Five lines across `workspace-aml-exam-prep/CONTEXT.md`,
`workspace-m2-exam-prep/CONTEXT.md`, and two M2 workspace outputs. All now name
the owning record instead.

This slipped past `test_scenario_7` for two compounding reasons, both fixed:

1. it collected dates from `attempts` only, so **sitting dates and Anmeldung
   windows were never covered** — precisely the facts a plan restates;
2. it matched ISO strings only, and Aram writes German dates, so `30.09` and
   `31.08–10.09` were invisible to it.

`test_admin_dates_are_not_restated_in_live_operational_prose` now collects every
owned sitting, `end_date`, registration window and attempt, expands each into its
ISO and German forms, and scans coordination, workspace `CONTEXT.md` files and
workspace `outputs/`. It was negative-tested both ways — reintroducing `31.08.`
and `2026-09-30` each fail it — because a hygiene test that cannot fail is worse
than none.

**Scope of the rule, stated so it is not re-flagged.** Eight further occurrences
exist and are correct:

- `work/active/*/inputs/` — preserved pre-migration plans. CLAUDE.md §5 forbids
  rewriting migration content; a preserved plan reading "Klausur Mo 27.07" is
  evidence of what was planned, not a competing owner.
- `knowledge/notes/` — durable notes. Hard rule #3 forbids rewriting a note body,
  and a note recording *"slide 39 said probably 27.7.26, later confirmed"* is
  provenance.

Hard rule #2 governs prose that **directs current work** — that is what goes
stale when a date moves. It does not reach into the historical record, and a
rule that did would be in direct conflict with §5 and hard rule #3.

`make check`: 0 errors, 0 warnings. Suite: 229 passed, 1 skipped.

## Deliberately not done

- **The faceted-library proposal** (source-ID-only physical storage, five facets,
  generated views superseding ADR-007's subject folders) is not adopted here. It
  is a real project with a real argument behind it, not a cleanup, and the AMLS
  sitting is close. → **now designed and costed in ADR-009 (proposed).**
- **Stage-resource identity for feedback.** `source_feedback` still targets a
  `source_id`, so two judgments about two different papers inside
  `source-amls-ss26-lectures` cannot be told apart. Registering all 60 papers as
  Library sources would fix it and is the wrong fix; stable resource IDs are the
  right one. → **now designed and costed in ADR-009 (proposed).**
- **A Computing & Society thematic group.** The seminar's move to
  `method-admin` is the least-bad existing home, not a good one. Adding a group
  amends ADR-007 and needs Aram.
- **Dropping `thematic-group-machine-learning` from AMLS** now that
  `ml-systems` is present — plausible, but removing a classification unreviewed
  is exactly what CLAUDE.md §4 reserves for visible review.
