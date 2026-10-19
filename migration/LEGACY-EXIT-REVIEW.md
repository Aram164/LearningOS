# Legacy exit review

> Prepared 2026-08-19. No file was moved out of or deleted from `legacy/`.
> This page is the human checkpoint before Aram removes that folder himself.

## Outcome

The useful legacy model is already represented by LearningOS v3:

- lecture scope is owned by module units and knowledge maps;
- references, exercise banks, mock exams, and cross-domain bridges are
  canonical notes;
- source crosswalks are decomposed into source records, module source maps,
  rich unit routes, and collections;
- degree-wide prospective resources are sealed inside the Master's Planning
  quarantine and excluded from current recommendations;
- semester and Master's operational history is preserved in archived
  workspaces;
- the useful old rituals survive as the v3 `lecture-unit-builder`,
  `promotion-ritual`, and `semester-kickoff` skills.

The review also found two useful material packets that did not have a safe
copy outside legacy. They are now copied—without changing the originals—to:

- `LearningOS/materials/_unsorted/Legacy-DBT-review/` — nine Database Theory
  PDFs (script, readings, mock exam, and exercise sheets), 13 MB;
- `LearningOS/materials/_unsorted/Legacy-SaD-review/` — the compiled SaD
  L01–L05 unit PDF, 330 KB.

They intentionally remain under `_unsorted/`: preserving bytes is mechanical;
registering or promoting them later is a separate semantic choice.

## Automated evidence

Run from `LearningOS/repository/`:

```bash
.venv/bin/python tools/legacy_exit_review.py
```

Current result:

| Disposition | Files |
|---|---:|
| integrated through a recorded migration | 113 |
| integrated through the materials migration | 2 |
| preserved byte-for-byte elsewhere in LearningOS | 17 |
| replaced by an explicit v3 system mechanism | 24 |
| needs a separate Job-boundary decision | 3 |
| **total** | **159** |

The tool is read-only. It compares migration records and hashes, scans the
LearningOS repository and materials tree, skips generated/cache data, never
enters `Job/`, and never writes, moves, or deletes anything. `--details` prints
the complete evidence trail; `--json` makes the result machine-readable.

## The three remaining decisions

These files are Job-related, so the normal LearningOS audit deliberately did
not compare them with the quarantined `Job/` tree:

1. `Plans/Libraries/skrub/Stratum-Optimizer-Walkthrough_Read-Filter-Join.md`
2. `Plans/archive/BIFOLD-DEEM-Job-Plan.md`
3. `Plans/archive/BIFOLD-DEEM-Job-Vorbereitung-v2.md`

Before deleting legacy, either compare these three in a separate, explicitly
authorized Job review or decide that their older plans/walkthrough are no
longer needed. Nothing else in the 159-file tree is awaiting a decision.

## Manual review route

1. Browse the two new `_unsorted/*-review/` material folders and confirm the
   preserved PDFs are the ones worth keeping.
2. Open the Master's Planning boundary and spot-check its module menu, degree
   wiring, and one resource-axis file against the old versions.
3. Spot-check one migrated note and one source map named in
   `migration/path-map.csv`.
4. Resolve the three Job-boundary files above.
5. Rerun `tools/legacy_exit_review.py`. A delete-ready result has no
   `manual-review` or `job-boundary-review` rows.
6. Delete `legacy/` yourself only after those checks. The audit intentionally
   provides no delete command.

## Scope note

This review records preservation and migration coverage. It does not claim
that old plans are current, that every archived recommendation is still good,
or that historical notes prove mastery. Current state remains owned by the v3
module, unit, source, note, and workspace records.
