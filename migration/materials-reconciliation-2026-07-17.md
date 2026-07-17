# Materials reconciliation — audit vs the master index (Jul 17 2026)

**Trigger:** Aram's concern that the reorganization lost materials.
**Method:** every pre-migration material file from `migration/inventory.json`
(45,636-entry snapshot, Phase 1) matched against today's disk by
name+size, then by byte-size (catches renames). Cross-checked against
`legacy/LEARNING-RESOURCES.md` (the master index) entry by entry.

## Result

**319 material files existed before migration → 302 are on disk right now.**
245 under identical names, 57 renamed but byte-identical (the intake
normalizations). **Nothing was lost by the topic-tree reorganization or the
_unsorted intake — all of today's moves reconcile 100%.**

Also verified individually: all five SaD Klausuren-extern, all nine Analysis
Klausuren-extern + TUM/MIT sets, all eight Frankfurt Algo2 exams, Murphy +
solutions, Lebl I+II, both CLRS editions, all 12 stats/probability books, the
19 SaD-2025 files (slides+UE — **no lecture videos ever existed in this
workspace**; the 2025 "recordings" were streaming links), CS4780 homework
set, ISLP/ESL/Géron (+ the AMLS Géron copy = `geron-copy2.pdf`, intentional
per the index), Strang OCW mirror, MIT 18.100A notes, cheatsheets, StuPO.

## The 17 genuinely missing files — and none are from today's reorg

All 17 were deleted by commit `a74184f` ("Purge + Job quarantine",
Jul 17, **before** this session), which removed the legacy seminar and
mlprov trees.

### Recovered already ✓

The 7 git-tracked seminar markdown files are restored to
`legacy/Plans/crosscutting/seminar/` — including **Vortrag-Skript.md and
Mini-Skript-Spickzettel.md, the sources of the two "lost" deliverable PDFs**
(those PDFs were just exports; regenerable any time).

### Re-downloadable (published papers — search title)

| File | Where |
|---|---|
| Shao et al. 2018 — Spread of low-credibility content by social bots | Nature Communications, open access |
| Hajli et al. 2022 — Social Bots and the Spread of Disinformation | Brit. J. of Management |
| Zhang et al. 2022 — Social Bots' Involvement in COVID-19 Vaccine Discussions | open access |
| Kolomeets & Chechulin 2023 — social bots metrics | open access |
| Yu et al. 2025 — Social bots in cryptocurrency manipulation | open access |
| Buneman et al. 2001 — Why and Where: Data Provenance (×2 copies) | classic, freely available |
| Grafberger et al. — Data distribution debugging in ML pipelines (mlinspect) | VLDB, open access |

### Course-internal (re-download from Moodle)

`SystematicLiteratureReview.pdf`, `REFERENZBEISPIEL_Review.pdf`,
`Organisation und Themenaufteilung VL.pdf` — seminar IuG Moodle.

### Your own work — check backups TODAY

- `Plattformregulierung-Vortrag.pptx` (the delivered talk)
- `mlprov_presentation-F copy.key` (not in the submission zip — checked)

Deleted this morning → if Desktop syncs to iCloud: **iCloud Drive → Recently
Deleted (30-day window)**. Otherwise Time Machine / macOS Trash. Also likely
attached in the Moodle submission or sent mail.

### Non-issues

`AMLS-project/.../AMLS_2026_Exercise.pdf` (near-identical version lives in
`LearningOS/projects/amls-project/`) and `report/acm-report/main.pdf`
(compiled LaTeX artifact, regenerable).

## Fix applied during audit

`dms-grundwerkzeuge` (Dietzfelbinger/Mehlhorn/Sanders) was shelved under
Books/stats — identified via title page, moved to **Books/algorithms**,
SOURCES.md lists rebuilt, validator 0/0.
