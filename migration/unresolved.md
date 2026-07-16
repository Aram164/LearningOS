# Unresolved migration items

> Updated 2026-07-17 (Stage-1 pilot). Rule: preserve, report, continue — nothing
> here blocks the pilot; every item needs a decision or a Stage-2 action.

## Facts needing Aram's confirmation (module records)

1. **AML Rücktritt execution** — `records/modules.yaml` records attempt 1
   (2026-07-22) as `withdrawn` per the plan of record, but the AGNES execution by
   the 2026-07-15 deadline was never confirmed in any legacy document. **Verify in
   AGNES; correct the record before 2026-07-22 if the Rücktritt was missed.**
2. **M2 Rücktritt execution + original registration** — deferral decided
   2026-07-16 (COORDINATION), Rücktritt deadline 2026-07-20; AGNES execution
   unconfirmed. The 1.-Termin registration itself was also never verified
   (legacy Open Loop #1b).
3. **AMLS sitting choice** (Aug 06 vs Aug 27) — no attempt recorded until chosen.

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

- **Attachment policy for handwritten scans:** pilot used 120-dpi JPEG page
  renders (16 MB for 11 pages) with the original PDF preserved in the legacy
  tree. Alternative: commit original PDFs wholesale (67–109 MB each) into
  `knowledge/attachments/`. Decide before Stage 2 mass-migration.
- **`concept-classification-metrics` granularity** — one concept currently covers
  confusion matrix/precision/recall/F1; split if retrieval needs finer grain.
- Legacy validators (`tools/check_links.py`, `check_system.py`, lychee routine)
  are replaced by `tools/validate.py` for the v3 tree — retirement happens at
  cutover (Phase 8), not in the pilot.
