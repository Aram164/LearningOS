# Unresolved migration items

> Updated 2026-07-17 (Stage-1 pilot). Rule: preserve, report, continue — nothing
> here blocks the pilot; every item needs a decision or a Stage-2 action.

## Facts needing Aram's confirmation (module records)

1. ✅ **AML Rücktritt execution** — confirmed by Aram 2026-07-17 ("2 exams were
   stepped back"); attempt 1 recorded `withdrawn` in records/modules.yaml.
2. ✅ **M2 Rücktritt execution** — confirmed by Aram 2026-07-17; attempt 1
   recorded `withdrawn`.
3. ✅ **AMLS sitting choice** — the LAST course-run slot, decided 2026-07-17;
   recorded as a `registered` attempt (termin 3) in records/modules.yaml.

## Deferred to Stage 2 (known destination, not yet migrated)

- SaD units L01, L03, L04, L05 (`Plans/Math/sad/SaD/notes/lect0*/`) → notes.
- SaD 06–10 Probability-Inference Deep Plan → note(s) (study-guide synthesis).
- `SaD_Book-Difficulty-Map_L01-L15.md` + the 5 KW-29 probability books
  (Pitman/Ross/Tijms/Schaum's; `The Principles of Probability.pdf` is flagged
  off-topic in the legacy shelf — candidate for exclusion) → source records.
- AML units L02–L06 → notes; AML book crosswalk rows L02–L04, L08–L10 → source
  evaluations (+ narrative note). L05/L06/L07 rows already decomposed in the pilot.
- AMLS source crosswalk, AN source crosswalk, LEARNING-RESOURCES.md → source
  registry + collections. **✅ LEARNING-RESOURCES.md FULLY MIGRATED
  2026-07-17** (two passes, same day):
  - §1+§2 → 40 records in `registry/external-supplements.yaml`, Rohrer
    chapter→module map onto `source-rohrer-e2eml`; collections mechanism built
    (schema + validator rules + generated views; intake formalized in
    WORKFLOWS §6a/6b).
  - §3–§8 → 48 records in `registry/external-shelf.yaml` (+ identifier/
    evaluation extensions on sklearn-user-guide, mit-6036, mit-6046j,
    ng-coursera, cmu-10414, stanford-cs149, bishop-prml). ⛔ Legacy §4 skrub +
    Stratum rows NOT registered — Job quarantine (CLAUDE.md §13).
  - 17 collections total under `sources/collections/` (lecture-series ×4,
    bookshelves ×5, explainers, python-internals, project-toolbox,
    papers-shelf, exam-practice-banks, broaden-later, degree-module-anchors).
- **✅ MASTERS-*-RESOURCES (6 axis files) MIGRATED 2026-07-17:** files copied
  verbatim into `work/active/workspace-degree-planning/inputs/` (prospective
  per-module menus = workspace planning material, joining MODULE-MENU/-PLAN
  there); the cross-module anchor tier (36 records) registered in
  `registry/degree-anchors.yaml` + `collections/degree-module-anchors.yaml`.
  Full menus promote into the registry when a module is chosen (rule recorded
  in WORKFLOWS §6a). Deliberately NOT registered wholesale: ~200 remaining
  prospective rows — they stay in the workspace inputs by design.
- ✅ Handwritten scans `Teil 01.pdf`, `Teil 02.pdf` — RESOLVED 2026-07-17:
  content inventoried (Teil 01 = Kapitel 02–04 Grundbegriffe/Wahrscheinlichkeit;
  Teil 02 = Kapitel 05–08 Verteilungen/Normal, "Blatt 04 … 2025" confirms SaD-2025
  provenance) → `note-sad-descriptive-probability-handwritten` +
  `note-sad-distributions-handwritten`, attachments as LOSSLESS qpdf page-splits
  (49–60 MB parts — the >100 MB originals would block a future GitHub remote;
  originals untouched in legacy). The GitHub-limit caveat is hereby CLOSED.
- All operational files (SEMESTER-STATUS, SESSION-LOG, HANDOFF, CHAT-DIVISION,
  chat plans) → workspaces / archive / COORDINATION routing per MIGRATION §Phase 4.

## Open decisions for the pilot review

- ✅ **Attachment policy for handwritten scans** — DECIDED by Aram 2026-07-17:
  **commit the whole original PDF when possible.** Applied: `Teil 03.pdf`
  (67 MB) committed as the canonical attachment; the interim 120-dpi page
  renders retired. Caveat recorded for Stage 2: `Teil 01.pdf` (109 MB) and
  `Teil 02.pdf` (101 MB) exceed GitHub's 100 MB per-file limit — if a remote is
  added, they need splitting or a size exception (LFS was already rejected);
  "when possible" covers exactly this case.
- ✅ **`concept-classification-metrics` granularity** — resolved by Aram's
  guidance (2026-07-17 review): note annotation stays flexible — a note may be
  about one concept or about many and how they connect (the Master Wiring note
  links 37; the L02 exercise bank links 2). Concepts are retrieval identities,
  not per-note containers, so the single metrics concept stays; split a concept
  only when a genuinely distinct retrieval identity emerges, never to make notes
  map one-to-one onto concepts.
- Legacy validators (`tools/check_links.py`, `check_system.py`, lychee routine)
  are replaced by `tools/validate.py` for the v3 tree — retirement happens at
  cutover (Phase 8), not in the pilot.
- ✅ `Plans/ML/mlprov/zitfCqCT` (stray 300 MB file) — RESOLVED 2026-07-17:
  identified as a TRUNCATED zip export of the "PPDS ML Data Provenance" folder
  (no end-of-central-directory record, unreadable; contents duplicate the intact
  sibling folder). Corrupt duplicate → deleted; 300 MB freed.
