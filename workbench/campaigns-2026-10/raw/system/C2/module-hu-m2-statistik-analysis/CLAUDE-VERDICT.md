# Claude's verdict on C2 for M2 (2026-10-24)

Re-checked against the live data, read-only, and against the module's
original generated maps.

## The headline is WRONG

The report says "The known route damage is real, and it's five units".

**The September damage is repaired.** It lived in `source-map.yaml` routes.
`route-an-ch02-analysisskript` has its full page map again, and the four
exam-prep routes each name their own PDF. Both were checked on 2026-10-24.

**The ch03–ch07 shape is the original design.** These are chapter-wide
resources repeated on every stage plus stage-specific extras, and they were
there from the start. In the generated maps of 29 Aug
(`work/active/workspace-m2-exam-prep/outputs/Analysis-chapter-maps-2026-08-29/`),
the number of resources shared by every stage is:

| Unit | Original (2026-08-29) | Now |
|---|---|---|
| ch03 | 3 | 3 |
| ch04 | 5 | 5 |
| ch05 | 12 | 12 |
| ch06 | 14 | 14 |
| ch07 | 19 | 19 |

Per-stage resource counts are also unchanged; ch03, for example, reads
19/3/23/21/16/4 in both. The original resources have no `source_id` and no
`material_ref`; their keys are `angle`, `angle_detail`, `kind`, `label`,
`locator`, `scope_triage` and `vault_path`. The ch01 and ch02 maps were later
re-done with route-bound resources (bound 25/25 and 71/71), while ch03–ch07
never were (bound 0/472).

**So it is unmigrated critique-point-1 debt, not a broadcast.**

## The measurements are RIGHT

- All 481 of the module's warnings are real: 472 unbound rows in ch03–ch07,
  and 9 prose placeholders in combined-exam-rehearsal.
- All 318 `vault_path` values resolve, and none mismatches its locator file.
- There are 0 page-range violations across 2020 items.
- The section and page claims GLM tested held up.
- The two printed→PDF offsets of the Fahrmeir book are explained.

Claude did not re-run these checks one by one. L1-4 (the 20% re-check) is
the gate for them.

## What it means for Aram's studying

- The page references in the M2 plan are correct.
- In Analysis ch03–ch07, each stage shows the whole chapter's menu (for
  example, the Kapitel 3 skript range on all six ch03 stages) next to its
  stage-specific items. That makes the plan coarser than ch01/ch02, but not
  wrong. The stage title (§3.5, and so on) names the section.

## Fix, when wanted

Migrate ch03–ch07 to route-bound, per-stage resources, as ch01/ch02 were.
That is acting on critique point 1 (boundary 17), so it needs Aram's say-so,
and it is better done after his current study session. The migration would
be prepared as `module-plan-import --check` packages.

## RECHECK-80 and the fix packages (conductor 2, Sun 2026-10-25 02:30)

**RECHECK-80.md (L2-14) holds.** 83 routes were re-checked: my 80, plus 3
whose `Regensburg_...pdf`-style names my regex missed. I spot-checked both
of its findings against the PDFs:
- **F1:** `VL 09-training-neural-networks.pdf` exists nowhere. The real deck
  is `VL 09-neural-networks.pdf`. It is an original defect, already wrong
  in the 2026-08-29 generated plan.
- **F2:** `IngMath2_Aufgaben.pdf` PDF p. 161 begins with the printed "158",
  and p. 222 with Kapitel 16. So the three IngMath2 anchors are printed
  pages, off by +3. Low.

Everything else in the 83 verifies, so the section-check gap is closed.

**PACKAGES.md (L2-16, finished on Flash after GLM-5.3 ran out).** Four
`--check`-green packages, none applied:

| Package | What it fixes |
|---|---|
| P1 | binds the 472 ch03–ch07 rows, derived from the ch01/ch02 rule (`covers`), with 0 content mismatches on expansion |
| P2 | the AML-l09 deck name |
| P3 | the IngMath2 pages |
| P4 | the 9 rehearsal rows |

Applying them is live-tree work: it waits for the live-branch merge and
Aram's "done studying" (decision 7). The packages carry their expected
snapshot, so a stale apply refuses rather than overwrites.
