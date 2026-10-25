# BS initial setup — material coverage audit — 2026-10-23

Plan package: `LearningOS/workbench/bs-initial-setup-2026-10-23/module-plan.yaml` (outside the authored repository).

## Scope authority and decision

Aram requested initial BS setup using the older slides and a learning plan only for the first big set. The exact selected artifact is `02_structure.pdf`, **Operating System Basics**, 46 physical PDF pages, with May 2006 slide footers. This is the confirmed scope of this practice unit; current WS 2026/27 taught/exam scope is unverified. It is not inferred from a book or lecture number. The integrated deck, not a claimed current lecture session, defines this one unit.

Create exactly one unit and one seven-stage study map. Keep the later decks available and deferred without active units or placeholder plans. Keep all pre-existing learner records, module administrative facts and unrelated work. Do not claim mastery or current exam equivalence.

## Review boundary

Complete file inventory of the exact managed slide folder and the exact original Desktop Betriebssysteme archive. Every selected slide page was text-read; all 46 pages rendered; diagrams on pp18/25 and the architecture diagrams were visually inspected. Other decks have complete text extraction plus title/scope inspection; book front/contents pages and personal files were inspected for identity only. Whole-book bibliographies, practical references and their historical administrative details remain deferred with those unselected documents. No external material was fetched or adopted. Local paths, full SHA-256 and inspection evidence for every original file are retained in `bs-original-archive-inventory.json` beside this audit.

## Local material inventory

| Managed material | PDF pages | Content and inspection | Disposition | Route/decision |
|---|---:|---|---|---|
| `material://source-bs-hu-prior-slides/02_structure.pdf` | 46 | Full text pp1-46, diagrams inspected. OS role; hardware; interrupt/trap/IRQL; memory protection/MMU; privileges; system calls; historical Linux; OS structures. | selected, prior-year | Seven exact section routes in unit-bs-os-structure |
| `material://source-bs-hu-prior-slides/03_processes.pdf` | 88 | Processes, PCB, states, scheduling basics, Unix creation/termination, IPC and Windows; complete extracted text and title/scope reviewed. | deferred, prior-year | No unit or study map now, per user scope |
| `material://source-bs-hu-prior-slides/04_cpu_scheduling copy.pdf` | 56 | Scheduling metrics/algorithms, fairness, priorities and historical implementations; complete extracted text and title/scope reviewed. | deferred, prior-year | No unit or study map now, per user scope |

## Original archive inventory

All original files stay in `/Users/aramaljanadi/Desktop/Huberlin /Betriebssysteme`; none was edited or moved. Three managed slides match the original bytes. Duplicate detection is by SHA-256, not filename. Two CSAPP filenames are byte-identical; only one conceptual candidate is counted. No additional book was selected or copied.

| Original file | PDF pages | Observed identity/period | Disposition and reason |
|---|---:|---|---|
| `(1) Silberschatz.pdf` | 944 | Operating System Concepts; 9th edition; copyright 2013 | reference-only — Locally available background candidate; no supplemental book selected for the first-deck study map. Bibliographies and precise chapter routing remain deferred until selected. |
| `(B3) operating_systems_three_easy_pieces.pdf` | 643 | Operating Systems: Three Easy Pieces; Version 0.80; May 2014 | reference-only — Locally available background candidate; no supplemental book selected for the first-deck study map. Bibliographies and precise chapter routing remain deferred until selected. |
| `.DS_Store` | — | macOS directory metadata; not applicable | excluded-nonlearning — macOS directory metadata. |
| `02_structure.pdf` | 46 | Operating System Basics; May 2006 | selected — Only selected deck for initial study map, explicitly using old slides. |
| `03_processes.pdf` | 88 | Processes; May 2006 | deferred — User requested a plan only for the first substantial slide deck; keep available for later. |
| `04_cpu_scheduling copy.pdf` | 56 | CPU Scheduling; May 2006 | deferred — User requested a plan only for the first substantial slide deck; keep available for later. |
| `Advanced.Programming.in.the.UNIX.Environment.3rd.Edition.0321637739.pdf` | 1034 | Advanced Programming in the UNIX Environment; 3rd edition; copyright 2013 | reference-only — Locally available background candidate; no supplemental book selected for the first-deck study map. Bibliographies and precise chapter routing remain deferred until selected. |
| `Andrew S. Tanenbaum - Modern Operating Systems.pdf` | 1137 | Modern Operating Systems; 4th edition; copyright 2015 | reference-only — Locally available background candidate; no supplemental book selected for the first-deck study map. Bibliographies and precise chapter routing remain deferred until selected. |
| `Computer Systems A Programmer’s Perspective.pdf` | 1105 | Computer Systems: A Programmer’s Perspective; 3rd global edition | reference-only — Locally available background candidate; no supplemental book selected for the first-deck study map. Bibliographies and precise chapter routing remain deferred until selected. |
| `CSAPP_2016.pdf` | 1105 | Computer Systems: A Programmer’s Perspective; 3rd global edition; exact duplicate of other CSAPP-named file | reference-only — Locally available background candidate; no supplemental book selected for the first-deck study map. Bibliographies and precise chapter routing remain deferred until selected. |
| `Klausurvorbereitung.pdf` | 56 | Betriebssysteme I — Prüfungsvorbereitung; Praktikum WiSe 24/25 | deferred — Older practical/exam material retained in archive; outside the first-deck setup and no study map requested. |
| `Mein-praktikum1.pdf` | 23 | Betriebssysteme I — Organisatorisches; C und Assembly; Praktikum WiSe 25/26 | deferred — Older practical/exam material retained in archive; outside the first-deck setup and no study map requested. |
| `mein-praktikum2.pdf` | 23 | Betriebssysteme I — Bootprozess; Praktikum WiSe 25/26 | deferred — Older practical/exam material retained in archive; outside the first-deck setup and no study map requested. |
| `praktikum3.pdf` | 19 | Betriebssysteme I — Systemrufe; Praktikum WiSe 24/25 | deferred — Older practical/exam material retained in archive; outside the first-deck setup and no study map requested. |
| `praktikum4.pdf` | 43 | Betriebssysteme I — Interprozesskommunikation; Praktikum WiSe 24/25 | deferred — Older practical/exam material retained in archive; outside the first-deck setup and no study map requested. |
| `praktikum5.pdf` | 24 | Betriebssysteme I — Netzwerkkommunikation; Praktikum WiSe 24/25 | deferred — Older practical/exam material retained in archive; outside the first-deck setup and no study map requested. |
| `praktikum6.pdf` | 60 | Betriebssysteme I — Nebenläufigkeit; Praktikum WiSe 24/25 | deferred — Older practical/exam material retained in archive; outside the first-deck setup and no study map requested. |
| `praktikum7.pdf` | 35 | Betriebssysteme I — Speicherverwaltung; Praktikum WiSe 24/25 | deferred — Older practical/exam material retained in archive; outside the first-deck setup and no study map requested. |
| `process_components_map.html` | — | Process Components Map + PCB Mapping Table; undated | reference-only — Existing personal study work preserved; no correctness assessment, rewriting or canonical note conversion authorized by this setup. |
| `ProgrammingGroundUp-1-0-booksize.pdf` | 326 | Programming from the Ground Up; copyright 2003; filename 1-0 | reference-only — Locally available background candidate; no supplemental book selected for the first-deck study map. Bibliographies and precise chapter routing remain deferred until selected. |
| `Systemcall vs Device interrupt.txt` | — | Systemcall vs Device interrupt; undated | reference-only — Existing personal study work preserved; no correctness assessment, rewriting or canonical note conversion authorized by this setup. |
| `TCP:IP Illustrated, Volume 1.pdf` | 1059 | TCP/IP Illustrated, Volume 1: The Protocols; 2nd edition; copyright 2012 | reference-only — Locally available background candidate; no supplemental book selected for the first-deck study map. Bibliographies and precise chapter routing remain deferred until selected. |
| `The Standard C Library.pdf` | 514 | The Standard C Library; copyright 1992 | reference-only — Locally available background candidate; no supplemental book selected for the first-deck study map. Bibliographies and precise chapter routing remain deferred until selected. |

## Linked and named material inventory

These are preserved leads, not selected teaching resources. Their current reachability and editions are unresolved; no working stage relies on them. Scope checks use the observed local PDF bytes. Do not present a historical footer as an inspected current course page.

| Named material / URL | Evidence | Disposition | Revisit condition |
|---|---|---|---|
| `http://sar.informatik.hu-berlin.de` | Attribution footer in the three decks | reference-only historical provenance; current page not checked | Current official course alignment needed |
| `Intel document volume 3` | 02_structure.pdf p25, visually verified | unresolved reference-only lead; exact title/edition absent | Need detailed interrupt/exception architecture |
| `http://www.linux-kernel.de/lxr/source/include/linux/sched.h#L334` | 03_processes.pdf p15 | deferred with Processes | That deck is selected |
| `http://www.linux-kernel.de/lxr/source/kernel/sched.c#L1357` | 03_processes.pdf p28 | deferred with Processes | That deck is selected |
| `http://www.linux-kernel.de/lxr/source/kernel/exit.c#L326` | 03_processes.pdf p54 | deferred with Processes | That deck is selected |

Code references `include/asm-i386/unistd.h`, `arch/i386/kernel/entry.S`, `<linux/unistd.h>`, `copy_from_user` and `copy_to_user` on 02 pp28-34 remain exact historical anchors within the selected deck. No current-kernel checkout or programming procedure is implied.

## Current/prior and duplicate reconciliation

Only prior material is available for this unit. User expressly chose it. Current-term equivalence remains an open question; routes are `scope: prior-year`, exam_critical is false, and the scope source is marked reference. Visible May 2006 content takes precedence over later PDF metadata. Original practice sheets mix WiSe24/25 and WiSe25/26; the exam-prep file is WiSe24/25. None establishes current dates, requirements or exam difficulty.

## Unit knowledge and material matrix

| Node suffix | PDF pages | Knowledge and action | Prerequisite node suffixes |
|---|---|---|---|
| os-hardware | 1-7 | OS roles, CPU/memory/controller cooperation; diagram and I/O narration | — |
| interrupts | 8-12 | Interrupt/trap, saved state, dispatch/handler/return, historical IRQL | os-hardware |
| memory | 13-18 | Bounds vs translation; MMU and page/frame/offset diagram | os-hardware |
| privileges | 19-22 | User/kernel boundary, privileged instructions, rings vs IRQL | memory, interrupts |
| syscall-boundary | 23-27 | Wrapper/control transfer, trusted entry, validation and stacks | privileges, interrupts |
| linux-example | 28-34 | Historical alarm pipeline, error handling, argument passing and user buffers | syscall-boundary |
| os-structures | 35-44 | Monolithic/layered/microkernel tradeoffs and NT qualification | syscall-boundary, privileges |

All nodes use prefix `knowledge-bs-`, routes `route-bs-`, stages `stage-bs-`. p45 is a cartoon; p46 is a final vocabulary pointer, not independent coverage of every listed topic. It is accessible as a reference resource on the final stage.

## Completeness: explicit exclusions and unresolved gaps

- Processes and CPU scheduling remain deferred, without units/maps.
- DMA and synchronous/asynchronous I/O are listed on p46 but not substantively taught here. Retain that gap explicitly; do not add an invented stage or imply the learner has learned it.
- No matching official first-deck exercise sheet or current exam baseline has been verified. The new exercise bank and self-test are operator-drafted original practice based on inspected content; no real-exam equivalence or mastery is asserted.
- Linux int 0x80, _syscall macros, IA-32 paths, NT terminology and the IRQL table are historical examples. Neither current Linux implementation nor a universal CPU priority scheme is claimed.
- No global concept relations are inferred. Unit-local prerequisites organize the selected material only.

## Decisions and verification

1. One integrated older deck is one unit: its cover and pp2-44 establish a coherent scope; authoring units for the deferred decks would contradict the user's requested start.
2. Seven section routes/stages: exact inspected page ranges keep the workload navigable and source claims checkable.
3. Reference, eight drills and a separate self-test support the initial plan; they preserve the distinction between source explanation, practice and observed learner evidence.
4. Gateway-only application: no canonical curriculum or note file is hand-written. Review the no-write report, apply exact bytes, inspect receipt, run `make plan-check` and verify the committed projection.
5. No commits, push, install, administrative edits, changes to other modules, or full-semester plan.

## Mechanically bound managed inventory

Original Desktop archive rows above are retained evidence and outside managed material boundaries. The structured block binds exactly the managed source folder used by this package; deferred managed files are present but out of this package's teaching scope.

```inventory-v1
roots:
- data-systems/architecture/bs-hu-prior-slides
rows:
- kind: local
  path: data-systems/architecture/bs-hu-prior-slides/02_structure.pdf
  sha256: b82d9c9e6652bffcef034e405f740615a5134011457fd1fef7fc1a93dfdbd9bf
  disposition: routed
- kind: local
  path: data-systems/architecture/bs-hu-prior-slides/03_processes.pdf
  sha256: 0205e0c0546eb81d92dec1c149ae19f76a6dcce78570c9465961be771ec28b09
  disposition: out-of-scope
- kind: local
  path: data-systems/architecture/bs-hu-prior-slides/04_cpu_scheduling copy.pdf
  sha256: 2b5059afd43bb8964bf2330b6881206bb78e6230b71d42fda5cdd2d5caf35cf9
  disposition: out-of-scope
```
