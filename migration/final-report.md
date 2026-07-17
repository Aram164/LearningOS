# Final Migration Report — Learning OS v3

> **Date:** 2026-07-17 · **Scope:** Stage 2 (BUILD-SPEC Steps 7–10 / MIGRATION
> Phases 4–8), executed the same day the pilot gate was approved by Aram
> ("everything else you decide, continue with the next phase").
> Pilot record: `pilot-report.md` (5/5 frozen criteria).

## 1. Migrated counts by canonical type

| Type | Count | Notes |
|---|---|---|
| **Notes** | 46 | 6 AML units (L02–L07: references, exercise banks, mock exams, 4 Bonusblatt solution sets), 6 SaD units (L01–L05 + L11) + the probability-inference deep plan, 4 crosswalk narratives (Master Wiring, SaD, AML-books, AMLS, AN), Regression Bridge, handwritten hypothesis-testing note, 5 library/programming references |
| **Concepts** | 89 | statistics, regression/GD, classification, trees, NN, deep architectures, analysis, ML systems, algorithms, programming — English labels, German aliases throughout |
| **Concept relations** | 69 | the four AML×SaD pipelines, analysis block order, ML-systems prerequisites (incl. the two legacy hard prerequisites F.E→S.B, F.J→S.C) |
| **Sources** | 69 (164 contextual evaluations) | all sources cited by canonical notes and selector views; per-lecture scoping via `useful_sections` |
| **Modules** | 6 | M2 (Kombimodul, withdrawn T1), AML (withdrawn T1), AMLS (registered, last Aug slot; ÜWP LP-gesperrt), PPDS (submitted; ÜWP), Seminar IuG, Algo 2 — every exam date canonically here and nowhere else |
| **Workspaces — active** | 6 | m2-exam-prep, aml-exam-prep, amls-exam-prep, algo2-exam-prep + standing: job-deem, degree-planning (validator target ≤7 non-standing: 4 ✓) |
| **Workspaces — archived** | 5 | seminar-iug, mlprov, amls-project, semester-brain-sose26 (the legacy brain, whole), masters-planning-v2 |
| **Attachments** | 1 note, 1 original PDF (67 MB) | per the approved commit-whole-PDF policy |

Mappings: **108 rows** in `path-map.csv` + **89 material moves** in
`material-moves.csv`.

## 2. Materials and projects (Phase 5)

**1.3 GB separated** into `LearningOS/materials/`: 43 registered source folders
(every `material://` URI resolves — validator: **0 warnings**) + 521 MB in
`_unsorted/` (grouped by origin: unregistered books, Rust/Python/Git extras,
Seminar reference, Job papers, StuPO PDFs, drill collections — register-then-move
as needed). Identity checks done during the move: CLRS-DE ("Algorithmen — Eine
Einführung"), Ottmann/Widmayer and **DMS (Dietzfelbinger/Mehlhorn confirmed via
pdftotext)** routed to their source folders; ambiguity went to `_unsorted`,
never guessed.

**Code projects NOT moved** (documented in `../projects/README.md`): mlprov and
amls-project (submitted 2026-07-15, grading in progress), stratum + skrub clone
(live job setup). Revisit after grades land.

## 3. Operational routing (Phase 4)

Facts routed to single owners: exam/attempt facts → `records/modules.yaml`;
deferrals + cross-workspace dependencies → `COORDINATION.md`; per-effort state →
workspace CONTEXT files; legacy Open Loops #5–#7 → the Open Questions of the
owning workspaces; #8 (validator retirement) → resolved by cutover (see §6).
Mini Plans and chat plans → workspace `inputs/` (operational study scripts, not
notes). SEMESTER-STATUS / SESSION-LOG / HANDOFF / CHAT-DIVISION /
LEARNING-RESOURCES / Masters-Planning v2 → archived whole (provenance preserved)
with copies in the two archive workspaces.

## 4. Validation results (Phase 7)

`python tools/validate.py`: **0 errors, 0 warnings.**
`python -m pytest`: **32/32 pass** (incl. Scenario 5 delete-and-rebuild,
Scenario 7 attempt lifecycle + no-date-duplication grep, Scenario 8 spot-checks).
`generated/` deleted and rebuilt from scratch as part of Phase 6 — deterministic
except timestamps (test-verified).

## 5. Unresolved items and semantic risks

Tracked in `unresolved.md`; highlights: Teil 01/02 handwritten scans (109/101 MB
— exceed GitHub's 100 MB limit; split-or-exception decision needed if a remote
is added; no LFS per earlier decision) · long-tail video channels (Foltz, zed,
6.041, 18.650, 6.S191, Loeber, Domingos essay …) not individually registered —
they remain findable in the archived LEARNING-RESOURCES copy; register on first
canonical citation · MASTERS-*-RESOURCES files not decomposed (copies in the
masters-planning-v2 archive) · `_unsorted/` contents await source registration ·
the 300 MB stray zip `zitfCqCT` (Aram to identify/delete) · DMMLS book still to
pull via Springer license.

**Semantic-risk list:** legacy prose citations inside migrated notes still name
pre-move material paths (bodies are verbatim by design; the migration-note
blockquote in each note explains; source records carry the resolvable
locations) · legacy plans copied into workspace `inputs/` contain stale
calendars — each workspace CONTEXT says "reuse the block order, not the dates" ·
module-to-module edges from DEGREE-WIRING were deliberately NOT converted into
concept relations (copies archived).

## 6. Cutover (Phase 8)

`LearningOS/repository/` is the operational root: root `README.md` updated;
retirement banners placed on legacy `HANDOFF.md` and `SEMESTER-STATUS.md`
pointing here. The legacy tree stays in place, frozen (tag `pre-v3-baseline`
preserves the pre-migration state; the post-separation state is committed on the
legacy repo). **Legacy validators retired:** `tools/check_links.py`,
`Masters-Planning/tools/check_system.py` and routine offline lychee runs are
replaced by `python tools/validate.py` (offline) / `--online` (URL audit) for
the v3 tree. `LearningOS/` can be dragged out of `semestercontext/` whenever
convenient — the repository is location-independent (fresh Git history).

## 7. Exact commands

```bash
cd LearningOS/repository
python tools/validate.py            # full offline validation (0 errors, 0 warnings)
python tools/validate.py --online   # + external URL audit (deliberate, not routine)
python tools/generate.py            # rebuild all generated outputs
python -m pytest                    # 32 tests
```

Requires Python 3.10+, `pyyaml`, `jsonschema>=4`, `pytest`.

## 8. Completion statement

All acceptance-test sections pass for the migrated scope; `generated/` rebuilds
from scratch without loss; pilot report approved 2026-07-17; this final report
closes the migration pending Aram's review. The system now runs on four
canonical knowledge families + module records + a facts-only coordination
layer — the drift disease the redesign set out to eliminate has no home left.
