# Analysis route restore and 3b1b transcript routing — coverage audit, 2026-09-12

Plan package: `LearningOS/workbench/audits/analysis-route-restore-2026-09-12/repair.yaml`

Two independent repairs in one package, because both touch the same source map.

## Repair 1 — four routes carrying a sibling's locator and angle_detail

`work/active/workspace-m2-exam-prep/outputs/fix_m2_route_rigor_2026_08_29.py`
keys its edit table by `(source_id, unit_id)` and applies it at
`key = (sid, route.get("unit_id"))`. That pair is not a route identity: 49
`(source, unit)` groups in this module hold more than one route, because one
source legitimately reaches one unit through several different materials. Two of
the pass's sixteen keys addressed groups of 2 and 4. Its own comment reads "two
locators of mine"; it wrote six.

Both broadcasts are in the Analysis lane. The other fourteen keys address
single routes and are unaffected.

| Route | What it is | Was overwritten with | Restored from |
|---|---|---|---|
| `route-an-ch02-analysisskript` | Kapitel 2 spine, `vault_path` *unser skript.pdf* | locator and detail of HU Hausaufgabe 5.4 | `Analysis-chapter-plan-2026-08-29.yaml` |
| `route-an-exam-prep-analysisskripthu` | the WV exam-format sheet | locator and detail of the course contract | same |
| `route-an-exam-prep-analysisskriptbeweise` | `kleine_beweise.pdf` | same | same |
| `route-an-exam-prep-analysisskript-2` | the deferral ledger | same | same |

Left untouched, because they are what the pass actually meant to edit and their
current text is the intended result: `route-an-ch02-analysisskripthu` and
`route-an-exam-prep-analysisskript`.

The most visible loss was ch02's. It was the only one of the seven chapters with
no page range at all — the other six name every `§` with printed and PDF pages —
while its `vault_path` still said `unser skript.pdf` and its locator said
`ana_inf_serie05.pdf`. Restoring it returns printed pp. 7-40 (PDF pp. 17-50) and
the nine `§` addresses under it. The chapter range also exists in
`unit-m2-analysis-ch02/unit.yaml` (`scope`, `scope_sources`) and agrees.

12 stage rows across `unit-m2-analysis-ch02` (8) and `unit-m2-analysis-exam-prep`
(4) reference these four routes through `material_ref`/`inherit` rather than
copying them, so they resolve the restored text with no edit of their own.

Verified after the restore: no two Analysis routes of one source in one unit
share a locator or an `angle_detail`.

## Repair 2 — the twelve Essence-of-Calculus transcripts

`tools/ingest_transcript.py` fetched all twelve episodes into the managed tree on
2026-09-11 and, by design, stopped one step short of routing them: pointing a plan
row at a span is a governed import, not a materials write. They are checksummed in
`records/materials-manifest.yaml`. The three existing Analysis routes still carried
`vault_path: None` and named their episodes by title only, and the 2026-08-29
audit still records this source as "No local copy" — accurate when written,
stale now.

| Route | Gains | Span now addressable |
|---|---|---|
| `route-an-ch05-3b1bessenceofcalculus` | `transcript/kfF40MiS7zA.md` | epsilon-delta at [06:00]-[10:30] |
| `route-an-ch06-3b1bessenceofcalculus` | `transcript/3d6DsjIBzJ4.md` + three more named in the locator | Taylor coefficients at [08:30]-[12:30]; l'Hospital at [11:00]-[17:00] |
| `route-an-ch07-3b1bessenceofcalculus` | `transcript/rfG8ce4nNh0.md` | area-slope inverse at [07:30]-[11:30] |

Every timestamp above was read out of the transcript on 2026-09-12; none is
inferred from an episode title. The captions are German, which suits a German
exam; the header of each file records `captions: manual`, and translation
quality degrades in the later windows of `kfF40MiS7zA.md`, so quote only after
checking the moment named — as the file's own preamble instructs.

12 inlined stage rows in ch05-ch07 were re-synchronised, because those five units
inline route fields instead of referencing them.

### Not routed here — needs review before it becomes a scope judgment

Three further episodes are now on disk and look in scope. Routing any of them
adds a contextual source evaluation, which CLAUDE.md §4 puts behind visible
review, so they are named here and left unrouted:

| Episode | File | Would serve |
|---|---|---|
| Ch 5 — What's so special about Euler's number e? | `m2MIpDrF7Es.md` | §5.6 Exponentialfunktion und Logarithmen |
| Ch 9 — What does area have to do with slope? | `FnJqaIESC2s.md` | §7.2 Hauptsatz |
| Ch 10 — Higher order derivatives | `BLkz5LGWihw.md` | §6.7 Höhere Ableitungen |

The remaining six (Ch 1, 3, 6, 12 and the two already named) are either covered
by an existing route or outside a one-variable Analysis script.

## Local

No new local material was consulted beyond the five transcripts named above,
each opened on 2026-09-12 before its span was recorded. Every other locator,
angle, node, stage and unit order in the module is unchanged. Every `vault_path`
this package writes resolves to exactly one manifest entry that exists on disk.

The full local inventory for this module stands as recorded in
`Analysis-chapter-coverage-audit-2026-08-29.md`, with one correction: its
"Linked and unresolved material" row for `source-3b1b-essence-of-calculus`
reads "No local copy", which ceased to be true on 2026-09-11. Nothing else in
that inventory has changed. `source-professor-leonard` still has no local copy
and that row stands.

## Linked

None. This pass consults no external material.

## Observed, not repaired

- The SaD lane shares two boilerplate `angle_detail` paragraphs across eleven and
  five routes, spanning eight and five different units. That is a template rather
  than a collision — each of those routes has its own locator and its own `angle`
  — so it is a visibility-debt item under WORKFLOWS §6a, not a defect, and it is
  out of scope for this package.
- `unit-m2-analysis-ch03` through `ch07` inline the full route fields into their
  stage rows while `ch01`, `ch02` and `exam-prep` reference routes through
  `material_ref`. Both forms were verified byte-identical to their routes before
  this package, and this package re-synchronises the twelve rows it affects, but
  the two forms mean a future source-map edit reaches only three of the eight
  units on its own.
- `unit-m2-analysis-ch06` and `ch07` still have no current HU practice at all.
  Unresolved and unowned since 2026-08-03; unchanged by this pass.
- `route-an-ch07-stewartcalculus` has a title naming `§7.1, §7.4 and §7.8` while
  its locator correctly also carries `§5.2`, `§5.3`, `§5.5` and `§7.5`. Cosmetic;
  left alone rather than bundled into a repair about something else.

## Completeness

- [x] Every route this package edits is named above with what it was and what it becomes.
- [x] The restored text is taken verbatim from a package that predates the defect, not rewritten.
- [x] The two routes the defective pass actually meant to edit are left untouched.
- [x] Every new `vault_path` resolves to one manifest entry that exists on disk.
- [x] Every timestamp was read out of the transcript, never inferred from a title.
- [x] Inlined stage copies re-synchronised; inheriting rows verified as needing no edit.
- [x] Exclusions and unresolved gaps recorded, including the three episodes held for review.

No claim of mastery or readiness is made anywhere in this document.
