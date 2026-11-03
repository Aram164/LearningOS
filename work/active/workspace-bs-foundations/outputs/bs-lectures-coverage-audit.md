# BS lectures plan coverage audit — 2026-11-04

Plan package: `LearningOS/workbench/bs-lectures-2026-11-04/module-plan.yaml` (draft outside the repository; applied through `module-plan-import`)

Scope authority: The three saved prior-year HU BS decks held under `material://source-bs-hu-prior-slides/`. Aram confirmed on 2026-11-04 that this year's Betriebssysteme lectures use the same slides, so the deferred decks `03_processes.pdf` and `04_cpu_scheduling copy.pdf` now receive lecture units and study maps. No claim is made beyond the decks themselves: exam format, dates, and any current-year deviation remain unrecorded.

Review boundary: the BS material root `materials/data-systems/architecture/bs-hu-prior-slides/` (three PDFs), the existing BS unit `unit-bs-os-structure`, its source map, and workspace `workspace-bs-foundations`. Books, Praktikumsblätter, and further personal Unterlagen from the old BS folder were not inventoried in this pass and remain deferred (see gaps).

## Local material inventory

| Locator | Version/year | Format | Opened/inspected evidence | Actual contents | Duplicate/version relation | Disposition | Unit route | Lecture-specific angle |
|---|---|---|---|---|---|---|---|---|---|
| `material://source-bs-hu-prior-slides/02_structure.pdf` | 2006 (May 2006) | course-material | PDF pp. 1–46 text-extracted 2026-10-23; sha256 `b82d9c9e…` | OS tasks/hardware, interrupts, memory protection, privileges, syscall boundary, Linux example, OS structures | unique; already planned | prior-year | `unit-bs-os-structure` (existing, unchanged) | scope authority of the existing BS 02 unit |
| `material://source-bs-hu-prior-slides/03_processes.pdf` | 2006 (May 2006) | course-material | PDF pp. 1–88 text-extracted 2026-11-04; sha256 `0205e0c0…` | process concept/PCB/context switch (pp. 1–14), state + scheduling basics (pp. 15–29), Unix creation/termination/kernel threads (pp. 30–54), signals/pipes IPC (pp. 55–65), Windows processes/threads (pp. 66–87), vocabulary (p. 88) | unique | prior-year | `unit-bs-processes` | lecturer's Unix-first process model with Windows contrast at the end |
| `material://source-bs-hu-prior-slides/04_cpu_scheduling copy.pdf` | 2006 (May 2006) | course-material | PDF pp. 1–56 text-extracted 2026-11-04; sha256 `2b5059af…` | scheduling goals/metrics/fairness (pp. 1–16), FCFS/RR (pp. 17–28), SJF/STCF + burst prediction (pp. 29–38), priority/multilevel/CFS/lottery (pp. 39–49), context-switch costs/parallel systems (pp. 50–56) | unique; filename carries a ` copy` suffix, bytes are the only held copy | prior-year | `unit-bs-cpu-scheduling` | deepens the scheduling-basics pages of `03_processes.pdf` pp. 15–29 |

## Linked web material inventory

| URL | Named by | Format | Official/primary evidence | Verified on | Actual topic/locator | Disposition | Unit route | Lecture-specific angle |
|---|---|---|---|---|---|---|---|---|
| `http://sar.informatik.hu-berlin.de` | deck headers of all three PDFs | website | not opened in this pass | — | HU Systems Architecture group page named on every slide | unresolved | — | provenance only; no teaching content routed from it |

## Current/prior and duplicate reconciliation

| Current asset | Prior/alternate asset | Content match/difference | Authority decision | Route |
|---|---|---|---|---|
| none held | `02_structure.pdf` (2006) | — | Aram confirmed 2026-11-04 the same slides are used this year; deck remains labelled prior-year, not current | `unit-bs-os-structure` |
| none held | `03_processes.pdf` (2006) | pp. 15–29 introduce scheduling basics that `04_cpu_scheduling copy.pdf` then treats in depth | one unit per deck; the overlap is recorded as a `builds_on` edge, not merged | `unit-bs-processes`, `unit-bs-cpu-scheduling` |
| none held | `04_cpu_scheduling copy.pdf` (2006) | full scheduling treatment | same as above | `unit-bs-cpu-scheduling` |

No duplicate bytes: the three SHA-256 hashes above are pairwise distinct.

## Explicit exclusions and unresolved gaps

| Material/topic | Disposition | Evidence | Reason | Revisit condition |
|---|---|---|---|---|
| Books, Praktikumsblätter, further Unterlagen in the old BS-Ordner | deferred | workspace `workspace-bs-foundations` Deferred section | not inventoried in this pass; no exercise/practice asset is routed, so each new unit records a practice gap instead of mislabelling the decks as exercises | revisit when Aram names the folder or a concrete Bedarf arises |
| Durable notes (reference / exercise bank / self-test) for the two new units | deferred | workflow 23 step 5 pattern of `unit-bs-os-structure` | this pass creates units, routes, selections and study maps; notes are a separate reviewed step | create after the first study pass shows what needs a reference |
| Current-year exam scope, sittings, deviations from the 2006 decks | unresolved | no current course artifact held | decks are the confirmed slide basis only | revisit when a current Moodle/AGNES artifact exists |
| `http://sar.informatik.hu-berlin.de` | unresolved | named on every slide header | provenance, not teaching material | none |

## Unit knowledge and material matrix

| Unit | Knowledge nodes and edges | Authoritative scope | Course material | Books | Videos/websites/courses | Practice/exercises | Optional/prior-year | Coverage gap |
|---|---|---|---|---|---|---|---|---|
| `unit-bs-os-structure` (existing) | 7 nodes as recorded | `02_structure.pdf` pp. 1–46 | 7 existing routes, unchanged | none routed | none | deck-internal Übungen via existing notes | the deck itself (prior-year) | none in this pass |
| `unit-bs-processes` | `knowledge-bs-process-concept` → `knowledge-bs-pcb-context-switch` → `knowledge-bs-process-state` → `knowledge-bs-unix-lifecycle` → `knowledge-bs-ipc` → `knowledge-bs-windows-processes` | `03_processes.pdf` pp. 1–88 (May 2006), confirmed reused this year | 6 new routes, one per node, exact page ranges | none routed | none | none held — practice gap recorded | the deck itself (prior-year) | no exercise asset; fork/COW quizzes on pp. 37–38, 41–43 are the only deck-internal checks |
| `unit-bs-cpu-scheduling` | `knowledge-bs-scheduling-goals` → `knowledge-bs-fifo-rr` → `knowledge-bs-sjf-prediction` → `knowledge-bs-priority-multilevel` → `knowledge-bs-scheduling-costs` | `04_cpu_scheduling copy.pdf` pp. 1–56 (May 2006), confirmed reused this year | 5 new routes, one per node, exact page ranges | none routed | none | none held — practice gap recorded | the deck itself (prior-year) | no exercise asset; worked waiting-time examples on pp. 20, 25, 31–32 are the only deck-internal checks |

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
