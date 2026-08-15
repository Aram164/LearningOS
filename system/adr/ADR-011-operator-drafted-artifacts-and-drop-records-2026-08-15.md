# ADR-011 — Operator-drafted artifacts, drop records, and unevaluated routes

**Date:** 2026-08-15
**Status:** accepted
**Scope:** three additive schema extensions and the data contract v5 → v6. No new
entity types, no new hierarchy, no migration.
**Approved by:** Aram ("fix the schema issues", 2026-08-15) — schema changes
require explicit approval under CLAUDE.md §5.

## Context

Aram restated the operating philosophy on 2026-08-15:

> "your job is to give me per lecture all possible sources detailing the angle
> the individual source highlights i than select the ones i need. create the
> missing AML artifacts"

Acting on that produced three places where the schema could not express what the
work actually was. In each case the operator had to record something **less true
than what it knew**, which is the failure mode this repository exists to prevent:
a cold reader would derive the wrong current state.

The three were not discovered by review. Each surfaced as a validator rejection
while doing ordinary work, which is the validator behaving correctly — it refused
values that did not exist rather than letting them through.

### 1. Operator-drafted notes had no honest authorship value

Nine artifacts were built for AML L08–L10 (reference + exercise bank + mock exam
per lecture), page-anchored to the current 2026 decks. `note.authorship` offered
`user | mixed | external`. None fits:

- `user` would claim Aram's synthesis — false, and it would let a study input
  masquerade as evidence of understanding, which hard rule #7 forbids.
- `mixed` would claim his reasoning is present — it is not, yet.
- `external` was used as the least-wrong option, on the argument that the
  substance is the lecturer's deck. But `external` means *another author's text
  carried in*, and these are neither the lecturer's prose nor Aram's.

Under the old philosophy this barely arose: the operator built menus, Aram wrote
the notes. Under the new one, **operator-drafted artifacts are routine**, so the
gap is now structural rather than incidental.

### 2. A drop could only be recorded as prose

AMLS was dropped from SoSe 2026 with **no attempt ever made** — no sitting taken,
no registration completed. The module record could express `status: dropped` and
`attempts: []`, but not *why*, or the load-bearing fact that nothing was ever
registered.

`attempts: []` is genuinely ambiguous: it cannot distinguish "nothing was ever
registered" from "the record is incomplete". Since `module.schema.json` is
`additionalProperties: false`, the full account had to go into
`examination.notes` — a prose field owned by a different concern. Hard rule #2
says exam facts live in the owning module; it does not say every module fact is
an exam fact.

### 3. "Never evaluated" collapsed into "judged optional"

Converting `unit-m2-analysis-exam-prep` to the menu model surfaced **22 sources
routed to the unit, 12 of them bare unit-id strings** with no title, angle,
coverage or locator. Five of those twelve had rich evaluations sitting unused in
their own source records. **Seven had no evaluation at all.**

Writing an angle for the seven would have been inventing a pedagogical judgment,
which CLAUDE.md §4 forbids. Recording them honestly required saying *"no
evaluation exists"* — but `depth` and `scope` had no value for that, so they were
forced to `orientation` and `optional`. That is a real distortion: **`optional`
means assessed and judged skippable; these were never assessed at all.** The
distinction is exactly the visibility debt the health report tracks, and flattening
it hides the debt at the point where it would actually be acted on.

## Decision

Three additive extensions. Every one is backward-compatible: absent values mean
precisely what they meant at v5, so no migration is required and none was written.

**1. `note.authorship` gains `operator-drafted`.**

> Built by the operator from a scope source and **not yet reasoned through by the
> learner** — a study input, never evidence of understanding. Becomes `mixed` the
> moment Aram works it and adds his own reasoning.

**2. `module` gains an optional structured `drop` record.**

Fields: `date` and `attempt_made` (required), plus `semester`, `stated_by`,
`reversible`, `intent` (`retake-later | abandoned | undecided`) and `notes`.

`attempt_made` is the load-bearing field. `reversible` and `intent` exist because
they change what happens to the preparation plan: a `retake-later` drop preserves
it as a reinstatement plan (the Algo 2 pattern), an `abandoned` one archives it.
The record is purely descriptive — it never overrides `status`, and exam facts
stay in `examination`.

**3. `module-source-map` unit_routes gain four enum values.**

- `format`: `exam` and `solutions`, separated from `exercise` because they are
  *used* differently — a past paper is spent once under timed conditions, and
  model solutions are read as writing samples rather than solved.
- `depth`: `unassessed` — no evaluation written, so depth is genuinely unknown.
  Not a judgment of shallowness, and never to be inferred by an operator.
- `scope`: `unevaluated` — routed to this unit but never assessed. Distinct from
  `optional`, which means assessed and judged skippable.

## Consequences

**Good.**

- An operator-drafted artifact now declares itself. `los status` counts
  `evidence 0/59` honestly, and no dashboard can mistake a generated mock exam
  for worked understanding.
- A drop is queryable. "Which modules were dropped without an attempt, and which
  intend a retake?" is now a field lookup rather than prose archaeology.
- Visibility debt is visible **at the point of choice**. The seven unevaluated
  Analysis sources appear on the menu marked as unevaluated, so Aram can pick one
  deliberately and the operator repays the debt on use (WORKFLOWS §6a) instead of
  the source silently vanishing from consideration.

**Costs and risks.**

- Four new enum values are four more things a writer can get wrong.
  `operator-drafted` in particular is only useful if it is **promoted to `mixed`
  when Aram actually works the note** — an unmaintained value would be worse than
  none, because it would understate his contribution over time.
- `drop` partially overlaps `status: dropped`. It is deliberately descriptive
  rather than authoritative, but a future reader could treat the two as
  independent. They are not: `status` decides, `drop` explains.
- `unevaluated` could become a dumping ground — a way to route sources without
  ever assessing them. The mitigation is that it is *visible*: it renders on the
  menu and shows in health reporting, so accumulation is legible rather than
  silent.

**Deliberately not done.**

- No migration. All three changes are additive; v1–v5 fixtures load unchanged
  under v6 (`tests/test_format_fixtures.py`, 13 passed).
- **The seven unevaluated Analysis sources were not evaluated.** That is
  wire-on-use work, not a bulk backfill (WORKFLOWS §6a), and inventing seven
  pedagogical judgments to clear a field would be precisely the error the new
  enum exists to prevent.
- `module-source-map` `format` was not otherwise expanded. `handout` folded into
  `documentation` without loss; `exercise-sheet` and `exercise-book` folded into
  `exercise` without loss. Only the two genuinely different *uses* were split out.

## Verification

```
python tools/schema_contract.py --bump --note "…"   → contract v6, 21 record schemas
python tools/validate.py                            → 0 errors
python -m pytest tests/                             → 319 passed, 1 skipped
tests/fixtures/formats/v6/                          → frozen, hand-materialised
```

The v6 fixture exercises all three changes: an `operator-drafted` note, a module
carrying a `drop` record, and routes using `exam`, `solutions`, `unassessed` and
`unevaluated`. Per the fixture README it was written by hand, not generated from
current code — a fixture that can be regenerated can never fail.

## Data touched

- Nine AML L08–L10 notes re-tagged `external` → `operator-drafted`.
- `module-hu-amls`: prose drop account in `examination.notes` replaced by the
  structured `drop` record; `examination.notes` keeps only what it owns.
- Seven `unit-m2-analysis-exam-prep` routes restored to
  `depth: unassessed` / `scope: unevaluated`; the Klausuren route moved to
  `format: exam` and Ableitinger to `format: solutions`.
