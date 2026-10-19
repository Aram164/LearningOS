# L08/L09 UE5 scope audit — 2026-09-09

Plan package: `/tmp/module-plan-l08-l09.yaml`

Scope authority: current Blatt 4 sheets plus the UE5/UE6 PDFs listed below.

Review boundary: local roots are UE5.pdf and UE6.pdf; linked boundary is empty for
this scoped package. Prior L08/L09 descriptive and stage repairs are already
committed under separate receipts.

## Local material inventory

| Locator | Version/year | Format | Opened/inspected evidence | Actual contents | Duplicate/version relation | Disposition | Unit route | Lecture-specific angle |
|---|---|---|---|---|---|---|---|---|
| `material://source-sad-ss26-lectures/exercise-slides/UE5.pdf` | prior-year tutorial | exercise | slides 20-38 and 40-77 extracted 2026-09-09 via pdftotext | generic Normal lecture (20-38) and estimation lecture (40-77), not Blatt 4 solutions | differs from UE6 Blatt 4 solutions | complementary | `unit-m2-sad-l08`, `unit-m2-sad-l09` | prior-year walkthrough |
| `material://source-sad-ss26-lectures/exercise-slides/UE6.pdf` | current tutorial | exercise | slides 5-20 and 10-13 extracted 2026-09-09 via pdftotext | Blatt 4 Aufgabe 1 (166/6, 179/8, lognormal, keyboards) and Aufgabe 2 bootstrap (same 10 samples, 80% CI) | matches current sheet | current | `unit-m2-sad-l08`, `unit-m2-sad-l09` | official solutions |

## Linked web material inventory

| URL | Named by | Format | Official/primary evidence | Verified on | Actual topic/locator | Disposition | Unit route | Lecture-specific angle |
|---|---|---|---|---|---|---|---|---|
| none in scope | — | — | — | — | — | — | — | — |

## Current/prior and duplicate reconciliation

| Current asset | Prior/alternate asset | Content match/difference | Authority decision | Route |
|---|---|---|---|---|
| Blatt 4 (Statistics_And_Data_Science.pdf) | UE5 slides 20-38, 40-77 | UE5 is generic lecture, not the sheet | current sheet defines scope; UE5 is complementary | `unit-m2-sad-l08`, `unit-m2-sad-l09` |
| Blatt 4 solutions (UE6) | UE5 | UE6 matches params exactly | UE6 stays current | `unit-m2-sad-l08`, `unit-m2-sad-l09` |

## Explicit exclusions and unresolved gaps

| Material/topic | Disposition | Evidence | Reason | Revisit condition |
|---|---|---|---|---|
| all other L08/L09 shelf sources | out-of-scope for this package | prior committed repairs | unchanged by this scope delta | full-reshelf audit |

## Unit knowledge and material matrix

| Unit | Knowledge nodes and edges | Authoritative scope | Course material | Books | Videos/websites/courses | Practice/exercises | Optional/prior-year | Coverage gap |
|---|---|---|---|---|---|---|---|---|
| `unit-m2-sad-l08` | unchanged nodes | unchanged | unchanged | unchanged | unchanged | UE5 scope current to complementary | UE5 walkthrough | none |
| `unit-m2-sad-l09` | unchanged nodes | unchanged | unchanged | unchanged | unchanged | UE5 scope current to complementary | UE5 walkthrough | none |

## Completeness sign-off

- [x] Every file under each declared local root has an inventory row.
- [x] Every link named by decks, bibliographies, plans, and workspace inputs has a row.
- [x] Materials were opened; no scope decision came from filenames/counts alone.
- [x] Current and prior-year scope were compared by content, not numbering.
- [x] Suspected duplicates were hashed or otherwise proven.
- [x] Every item has a disposition, format, lecture route, and angle.
- [x] Every rich route names only knowledge nodes declared by its lecture.
- [x] Learner choices are separate from the complete material menu.
- [x] Exercise gaps and unreachable sources are explicit.
- [x] Every ordinary lecture has an individual knowledge/material row.
