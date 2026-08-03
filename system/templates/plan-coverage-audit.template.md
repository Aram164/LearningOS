# MODULE plan coverage audit — YYYY-MM-DD

Plan package: `work/active/WORKSPACE/outputs/PLAN.yaml`

Scope authority: CURRENT DECKS / RECORDINGS / BRIEF

Review boundary: name the exact local material roots, workspace inputs,
bibliographies, preserved plans, source collections, and official web pages
that were inventoried. State any inaccessible boundary explicitly.

## Local material inventory

One row per file. Duplicate files remain separate rows and point at the same
hash/group; folders and counts alone are not enough.

| Locator | Version/year | Opened/inspected evidence | Actual contents | Duplicate/version relation | Disposition | Unit/stage route | Reason |
|---|---|---|---|---|---|---|---|
| `material://source-id/path/file.pdf` | current | pages 1–40 + rendered formula pages | topic list | unique | selected | `unit-id` / `stage-id` | scope authority |

Allowed dispositions: `selected`, `reference-only`, `deferred`, `duplicate`,
`superseded`, `off-scope`, `unresolved`.

## Linked web material inventory

One row per URL named by any authoritative artifact, even if unreachable or
not selected.

| URL | Named by | Official/primary evidence | Verified on | Actual topic/locator | Disposition | Unit/stage route | Reason |
|---|---|---|---|---|---|---|---|
| `https://example.edu/course/topic` | deck L01 p. 4 | official course page | YYYY-MM-DD | exact lecture/section | selected | `unit-id` / `stage-id` | derivation |

## Current/prior and duplicate reconciliation

| Current asset | Prior/alternate asset | Content match/difference | Authority decision | Route |
|---|---|---|---|---|
| current L01 | older L01 | list the verified difference | current defines scope; older is reference-only | `unit-id` |

Record hashes for suspected duplicates and record numbering mismatches here.

## Explicit exclusions and unresolved gaps

| Material/topic | Disposition | Evidence | Reason | Revisit condition |
|---|---|---|---|---|
| named source with dead link | unresolved | checked YYYY-MM-DD | no reachable primary locator | revisit when course page returns |

“Not selected” without a row and reason is not permitted.

## Unit and stage coverage matrix

| Unit | Authoritative scope | First exposure | Spine/derivation | Practice/exercises | Reference/deferred | Coverage gap |
|---|---|---|---|---|---|---|
| `unit-id` | exact deck/recording | exact locator | exact locator | exact sheet/problem | exact locator + reason | none or explicit gap |

Every ordinary lecture receives its own row. Auxiliary synthesis/topic units do
not replace those rows.

## Completeness sign-off

- [ ] Every file under each declared local root has an inventory row.
- [ ] Every link named by decks, bibliographies, plans, and workspace inputs has a row.
- [ ] Materials were opened; no scope decision came from filenames/counts alone.
- [ ] Current and prior-year scope were compared by content, not numbering.
- [ ] Suspected duplicates were hashed or otherwise proven.
- [ ] Every item has a disposition and every selected item has a unit/stage route.
- [ ] Exercise gaps and unreachable sources are explicit.
- [ ] Every ordinary lecture has an individual unit/map row.

