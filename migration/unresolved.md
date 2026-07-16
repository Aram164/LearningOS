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
  registry + collections.
- Handwritten scans `Teil 01.pdf`, `Teil 02.pdf` (Oct 2025, earlier chapters) →
  attachment + owning note(s) once their content is inventoried.
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
