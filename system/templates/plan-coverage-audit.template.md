# MODULE plan coverage audit — YYYY-MM-DD

Plan package: `work/active/WORKSPACE/outputs/PLAN.yaml`

Scope authority: CURRENT DECKS / RECORDINGS / BRIEF

Review boundary: name the exact local material roots, workspace inputs,
bibliographies, preserved plans, source collections, and official web pages
that were inventoried. State any inaccessible boundary explicitly.

## Local material inventory

One row per file. Duplicate files remain separate rows and point at the same
hash/group; folders and counts alone are not enough.

| Locator | Version/year | Format | Opened/inspected evidence | Actual contents | Duplicate/version relation | Disposition | Unit route | Lecture-specific angle |
|---|---|---|---|---|---|---|---|---|
| `material://source-id/path/file.pdf` | current | course-material | pages 1–40 + rendered formula pages | topic list | unique | current | `unit-id` | scope authority and lecturer notation |

Allowed inventory dispositions include `current`, `prerequisite`,
`complementary`, `optional`, `prior-year`, `duplicate`, `superseded`,
`out-of-scope`, and `unresolved`. Learner selection is recorded separately; it
must not be used as a synonym for availability or quality.

## Linked web material inventory

One row per URL named by any authoritative artifact, even if unreachable or
not selected.

| URL | Named by | Format | Official/primary evidence | Verified on | Actual topic/locator | Disposition | Unit route | Lecture-specific angle |
|---|---|---|---|---|---|---|---|---|
| `https://example.edu/course/topic` | deck L01 p. 4 | website | official course page | YYYY-MM-DD | exact lecture/section | complementary | `unit-id` | independent derivation |

## Current/prior and duplicate reconciliation

| Current asset | Prior/alternate asset | Content match/difference | Authority decision | Route |
|---|---|---|---|---|
| current L01 | older L01 | list the verified difference | current defines scope; older is reference-only | `unit-id` |

Record hashes for suspected duplicates and record numbering mismatches here.

## Explicit exclusions and unresolved gaps

| Material/topic | Disposition | Evidence | Reason | Revisit condition |
|---|---|---|---|---|
| named source with dead link | unresolved | checked YYYY-MM-DD | no reachable primary locator | revisit when course page returns |

Omitting a reviewed material without a row and reason is not permitted.

## Unit knowledge and material matrix

| Unit | Knowledge nodes and edges | Authoritative scope | Course material | Books | Videos/websites/courses | Practice/exercises | Optional/prior-year | Coverage gap |
|---|---|---|---|---|---|---|---|---|
| `unit-id` | stable IDs + meaningful `builds_on` edges | exact deck/recording | exact locator + angle | exact section + angle | exact locator + angle | exact sheet/problem + angle | exact locator + status reason | none or explicit gap |

Every ordinary lecture receives its own row. Auxiliary synthesis/topic units do
not replace those rows. The row describes the complete choice menu, not an
ordered study sequence.

## Completeness sign-off

- [ ] Every file under each declared local root has an inventory row.
- [ ] Every link named by decks, bibliographies, plans, and workspace inputs has a row.
- [ ] Materials were opened; no scope decision came from filenames/counts alone.
- [ ] Current and prior-year scope were compared by content, not numbering.
- [ ] Suspected duplicates were hashed or otherwise proven.
- [ ] Every item has a disposition, format, lecture route, and angle.
- [ ] Every rich route names only knowledge nodes declared by its lecture.
- [ ] Learner choices are separate from the complete material menu.
- [ ] Exercise gaps and unreachable sources are explicit.
- [ ] Every ordinary lecture has an individual knowledge/material row.
