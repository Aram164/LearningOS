# Semantic state report — 2026-08-14

**Author:** operator (semantic recheck of the current learning plans and the system as a whole)
**Status:** findings recorded; **remediation applied 2026-08-14** — see
*Resolution* at the end. One item deliberately left open.
**Scope:** live plans, workspaces, module records, curriculum units, study maps,
the note corpus and the evidence layer — read as committed at `817f277`, not as
discussed in any prior session.
**Triggering fact:** *"AMLS will not be written."* (Aram, 2026-08-14.)

> **Why this file exists.** A semantic recheck was requested; midway through it,
> the AMLS decision landed and changed the picture structurally rather than in
> degree. This report is written against the post-decision state. Nothing below
> has been applied to canonical data — the administrative shape of the drop is
> Aram's to state, and several downstream edits are planning decisions, not
> mechanical ones.

## Overall judgment

> The machinery is sound and the data is internally consistent. What has drifted
> is **the relationship between the planning layer and reality**: the plans
> describe an intent that the evidence layer never recorded, and the plan of
> record is anchored on an event that will now not occur.
>
> This is the same class of problem ADR-008 fixed — a cold reader deriving the
> wrong current state — but one level up. ADR-008 normalized prose against rules.
> This is prose that has come loose from **facts**.

Mechanically verified clean at the time of writing:

| Check | Result |
|---|---|
| `python tools/validate.py` | **0 errors, 0 warnings** |
| `python tools/generate.py` | rebuilds without error |
| Working tree | clean, level with remote |
| Schema/ID integrity | every cross-reference resolves |

No structural defect was found. Every finding below is semantic.

---

## Part 1 — What the AMLS decision invalidates

### 1.1 The plan of record is now structurally invalid, not merely stale

`work/COORDINATION.md` organizes the entire run to the autumn cluster into five
phases, and **every one of them is anchored on the AMLS sitting as the pivot**:

- Phase A — *now → the AMLS sitting*: AMLS-primary, AML-synergy, M2 steady
- Admin gate — the 2.-PZ Anmeldung window
- Phase B — *after the AMLS sitting* → the AML 2. Termin
- Phase C — AML written → the M2 Klausur
- Phase D — after the M2 Klausur → thesis primary

With AMLS removed, Phase A has **no terminating event and no primary subject**,
and Phases B and C inherit the break through their "after the AMLS sitting"
predicate. The document is not out of date at the margins; its organizing spine
is gone. It cannot be repaired by editing the Deferrals list alone.

The same applies to the guiding move recorded 2026-07-25 — *"AMLS and AML are
studied as one synergy track"* — which was the stated justification for how AML
was being handled. That justification no longer has a referent.

### 1.2 Three layers now assert work that has been cancelled

| Layer | Current state |
|---|---|
| `workspace-amls-exam-prep` | `status: active` |
| 14 AMLS units | `status: ready` (all) |
| 14 AMLS study maps | `status: ready`, **42/42 stages `pending`** |

This is precisely the contradiction the 2026-08-08 normalization pass removed for
Algo 2 — where one layer claimed work was ready while another said it was
dropped — and which a validator invariant now guards against. **Algo 2 is the
template**: workspace → `blocked`, unit and study map → `paused`, moved
*together*, with the plan preserved below a status banner as an explicit
reinstatement plan rather than deleted.

One material difference from Algo 2, which is why this should not be applied
mechanically: the AMLS module record states that sitting 3 (2026-08-27) was the
**last course-run slot**. Algo 2's oral can be reinstated inside the same cycle.
AMLS cannot. Whether the preserved plan is a *reinstatement* plan for a future
course run or an *archived* one is a question of fact only Aram can answer
(see Part 4).

### 1.3 The AML deferral loses its justification — and AML inverts to primary

`workspace-aml-exam-prep` currently reads:

- *Required now* — the AML foundations AMLS builds on, "pulled in on demand from
  the AMLS track", specifically `unit-aml-l09` behind AMLS L03/L04 and
  `unit-aml-l08` behind the AMLS hardware decks.
- *Defer* — AML **exam-specific** preparation "until after the AMLS sitting":
  the L07 material choice, the closed-book mock, the systematic L05→L11 review.
- *Next Action* — "**Now (synergy):** when the AMLS track reaches computation
  graphs and rewriting…"

Read literally against the new fact: the required-now block instructs study
alongside a track that will not run, and the defer block defers AML exam prep
**until an event that will not occur** — i.e. indefinitely. The Next Action's
"Now" clause is unreachable.

The correct reading is the inverse of what the file says. **AML is now the
nearest exam and should be the primary track**, at T+47.

### 1.4 The corpus inversion resolves itself — by subtraction

The recheck's most uncomfortable finding before the decision was that the note
corpus was inverted against the stated priority order:

| Module | Exam | Posture (pre-decision) | Reference | Exercise banks | Mock exams |
|---|---|---|---|---|---|
| AML | T+47 | deferred | 6 | 6 | 6 |
| SaD (M2) | T+56 | steady | 7 | 5 | 0 |
| **AMLS** | **T+13** | **super-priority** | **0** | **0** | **0** |

AMLS held exactly one note — `note-amls-source-crosswalk`, a `crosswalk` carrying
integration rules, not study content. Health reporting did not surface this,
because all 11 AMLS concepts are listed in that single crosswalk's frontmatter
and therefore read as "covered": **a green metric over a hollow subject.**

The drop resolves this at zero cost. The corpus that exists — AML L02–L07 and
SaD L01–L05, L11 — now maps precisely onto the two exams that remain. This is
worth stating plainly rather than burying: *the material you actually built
serves the modules you are actually sitting.*

### 1.5 What becomes inert

65.9 h of planned AMLS work: 14 units, 42 stages, 60 curated must-read papers and
283 lecture-grouped bibliography entries recovered from slide citations, plus the
per-stage `scope_triage` ranking built on 2026-08-08. None of it was consumed —
all 42 stages are `pending` and all 42 stage notes are empty.

Per hard rule #4 and the Algo 2 precedent, **none of this should be deleted.**
The recovered paper inventory in particular is genuine durable value independent
of the exam: it is a curated map of the ML-systems literature, and
`thematic-group-ml-systems` is also the thesis's primary group.

---

## Part 2 — Findings that survive the decision

These were true before 2026-08-14 and remain true after. The drop changes their
urgency, not their existence.

### 2.1 The evidence layer is empty, repository-wide

**All 99 stage notes across every module are 0 bytes.** The system's own metrics
agree independently:

```
los status:   reviewed 0/50 · evidence 0/50
health.md:    notes with a `reviewed` date: 0/50
              notes with `evidence` entries: 0/50
```

Hard rule #7 says *never declare mastery — show evidence trails or their
documented absence.* The documented absence is currently total. The repository
cannot see study done off-system; what it can say is that no evidence has been
recorded inside it.

This is now the **primary risk**, because the AMLS drop buys ~66 h of calendar
relief but creates no evidence. Two exams remain:

- **AML — T+47** (2026-09-30). 11 units, all `not-started`. Knowledge maps and
  complete material menus exist for L01–L11; **zero study maps** — by design
  since the 2026-08-14 cutover, which made study maps optional. Reference notes
  and mocks exist for L02–L07; L08–L11 have neither.
- **M2 — T+56** (2026-10-09). Analysis: 11 stages, all `pending`, 47.5 h planned,
  `current_stage: stage-m2-analysis-calibrate` — i.e. the first stage. SaD: 15 of
  17 units `not-started`; `unit-m2-sad-l04` is `active` with **no current study
  map**, matching the workspace's stated "L04 remains the open lecture, but it
  has no forced current stage."

### 2.2 Build-vs-use asymmetry

Commits since 2026-07-15 (87 total), by path:

```
tools           62        knowledge/notes   12   (mostly migration/mechanical)
system          45        curriculum        11
tests           40        records           10
work            19        sources           17
```

The last commit adding genuinely new study content was 2026-08-03. Since then:
ADR-008, ADR-009, ADR-010, manifest contract v3→v4, domain loaders and manifest
projectors, the Garden projection, the Core review queue, the Job surface.

The system has been improving its ability to describe study considerably faster
than it has been used to study. Stated as a measurement, not a verdict — but it
is the pattern most likely to repeat, and re-planning after the AMLS drop is
exactly the moment it would repeat.

### 2.3 The hard administrative gate is mis-filed as an open question

With AMLS gone, the **2.-PZ Anmeldung window is the only hard deadline left
before the exams**: opens 2026-08-31 (**T+17**), closes 2026-09-10 (**T+27**).
It governs both remaining modules — AML and M2 — and COORDINATION.md itself
calls it "non-negotiable".

Both workspaces file it under *Open Questions* as a reminder-setting query:

- `workspace-aml-exam-prep` — "2.-PZ Anmeldung for the 2. Termin — set the reminder."
- `workspace-m2-exam-prep` — "2.-PZ Anmeldung: calendar reminder set?"

A non-negotiable dated gate is not an open question; it is a required action with
a deadline. The same mis-filing previously hid the AMLS registration formality.
Missing this window costs both remaining exams.

### 2.4 Unresolved administrative residue

- **Seminar IuG** — the written peer review "was due 2026-07-16 (2–4 pages —
  **submission to confirm**)". A month old and still unconfirmed in the record,
  on a module whose grade is pending.
- **PPDS** — project submitted 2026-07-15, grade pending. No action, tracked only.
- **Algo 2** — dropped 2026-07-25, module still `enrolled` with no formal
  Abmeldung recorded. Consistent and deliberate; noted for completeness. Its
  registration window is the same 2026-08-31 → 09-10 gate, which the drop
  decision says to let lapse.

### 2.5 Minor — an unreal capacity figure

`module-skill-python` reports 7.5 h across 43 stages because **38 of the 43 carry
no `estimate_minutes`** (`unit-python-depth-drills` 10/10 missing,
`unit-python-intermediate-roadmap` 28/28 missing). Any capacity or planning view
consuming that total is consuming a fiction. Either populate the estimates or
have views report "unestimated" rather than summing to a number.

---

## Part 3 — Corrected state of the system

What a cold reader should now derive, once the edits in Part 4 are applied:

| Track | Exam | Status | Real position |
|---|---|---|---|
| **AML** | 2026-09-30 (T+47) | **primary** | Material menus complete L01–L11; notes + mocks L02–L07; L08–L11 unbuilt; no stage evidence |
| **M2** | 2026-10-09 (T+56) | **strong parallel → primary after AML** | Analysis map ready, unstarted (47.5 h); SaD L04 open; notes L01–L05, L11 |
| AMLS | — | **dropped** | 65.9 h plan + paper inventory preserved, inert |
| Algo 2 | — | dropped | Reinstatement plan preserved, inert |
| Thesis | — | slack → primary after M2 | Landscape + plan complete; AIDE baseline not stood up |
| PPDS / Seminar | — | grades pending | Seminar peer-review submission unconfirmed |

**Freed capacity:** roughly 66 h that Phase A had committed to AMLS, plus the
removal of the 13-day crunch. Where it goes is a planning decision (Part 4).

---

## Part 4 — Required canonical updates (not applied)

Ordered by dependency. Each names its owner per hard rule #2.

1. **`work/COORDINATION.md`** — record the AMLS drop under *Deferrals* (a fact
   Aram stated; recordable as stated), then **re-phase** *Priorities* around an
   AML → M2 → thesis spine. The re-phasing is a planning decision and is
   deliberately left to Aram; a phase structure invented by the operator would be
   the same failure mode this report documents.
2. **`curriculum/modules/module-hu-amls/module.yaml`** — the attempt record
   currently reads `termin: 3 · result: registered`. What replaces it depends on
   the mechanism of the drop, which cannot be inferred (see Part 5).
3. **`workspace-amls-exam-prep` + 14 units + 14 study maps** — move to
   `blocked` / `paused` **together**, per the Algo 2 template and the lifecycle
   invariant. Preserve the plan below a dated status banner; delete nothing.
4. **`workspace-aml-exam-prep`** — rewrite *Current Scope*, *Next Action* and
   *Deferred* to remove the synergy predicate; AML becomes primary and its
   exam-specific prep starts now rather than "after the AMLS sitting".
5. **`workspace-m2-exam-prep`** — *Current Scope* and *Open Questions* sequence
   around "during Phase A" and "after the AMLS sitting"; both need re-anchoring.
6. **Both remaining workspaces** — promote the 2.-PZ Anmeldung from *Open
   Questions* to a dated required action (finding 2.3).
7. Re-run `python tools/validate.py` and `python tools/generate.py`; expect the
   lifecycle rule to be the one that would have caught 1.2.

---

## Part 5 — Questions only Aram can answer

1. **Mechanism of the AMLS drop** — formal Rücktritt, simply not registering, or
   registered-and-not-appearing? This determines the `attempts` record in
   `module-hu-amls/module.yaml`, and the three are not equivalent.
2. **Deferred or abandoned?** Sitting 3 was the last course-run slot. Is AMLS
   intended for a future course run (→ preserve as a reinstatement plan, Algo 2
   style) or dropped for good (→ archive the workspace)?
3. **LP consequence.** AMLS was taken as Bachelor-UEWP, LP-gesperrt im Master.
   Not writing it means those LP are not earned — does that leave a gap in
   `program-bachelors` that needs filling from elsewhere?
4. **Where does the freed ~66 h go** — AML, M2, or is some of it deliberately
   *not* reallocated?
5. **Seminar IuG** — was the written peer review submitted on 2026-07-16?

---

## Appendix — measurements

Taken 2026-08-14 at `817f277`, after `python tools/generate.py`.

```
notes 50 · concepts 89 · relations 69 · sources 239
programs 5 · modules 9 (6 enrolled) · projects 1 · units 52 · study maps 20
workspaces 5 active (0 standing), 3 archived
inbox 0 · garden 1 · reviewed 0/50 · evidence 0/50
validation: OK
```

Planned-vs-consumed, by module:

| Module | Units | Study maps | Stages | Pending | Planned | Stage notes with content |
|---|---|---|---|---|---|---|
| AMLS | 14 (`ready`) | 14 | 42 | 42 | 65.9 h | 0 / 42 |
| M2 | 17 (15 `not-started`) | 1 | 11 | 11 | 47.5 h | 0 / 11 |
| AML | 11 (`not-started`) | 0 | 0 | — | — | — |
| Python | 3 (`ready`) | 3 | 43 | 43 | 7.5 h † | 0 / 43 |
| Algo 2 | 1 (`paused`) | 1 | 1 | 1 | — | 0 / 1 |
| Thesis | 2 | 1 | 1 | 1 `active` | — | 0 / 1 |

† unreal — 38 of 43 stages carry no estimate (finding 2.5).

**Repository-wide: 99 stage notes, 99 empty.**

Note corpus by role: reference 20 · exercise-bank 15 · mock-exam 6 ·
crosswalk 5 · synthesis 4. By state: evolving 47 · rough 3. No note carries a
`reviewed` date or an `evidence` entry.

Source visibility debt (unchanged, repaid on use per WORKFLOWS §6a): 52 of 239
sources have no concept link, no shelf and no note.

---

## Resolution — 2026-08-14

**Aram's decisions:** *"Math 2 and AML for sure. Shelve the AMLS content, do not
delete it, I will do it next year. Clean everything you found."*

That resolves Part 5 Q2: AMLS is **deferred to a future course run**, not
abandoned — so the plan is preserved as a reinstatement plan, Algo 2 style.

### Applied

| # | Change | Files |
|---|---|---|
| 1.2 | AMLS shelved: workspace → `blocked`, 14 units + 14 study maps → `paused`, moved together. Dated banner added; plan, 42 stages, 60 curated papers and 283 bibliography entries preserved intact. Next Action neutralised to "None", with the reinstatement first step kept verbatim below it. Both Open Questions marked dormant. | `workspace-amls-exam-prep/CONTEXT.md` + 28 YAML |
| 1.1 | Plan of record re-phased. The five AMLS-anchored phases replaced by an AML → M2 → thesis spine; the rationale for the wholesale replacement recorded rather than silently patched. | `work/COORDINATION.md` |
| 1.3 | AML rewritten as the primary track. Synergy predicate removed from *Current Scope*, *Next Action* and *Deferred*; exam prep starts now; **L08–L11 named as the real build** (L02–L07 already have reference + drills + mocks, L08–L11 have none). | `workspace-aml-exam-prep/CONTEXT.md` |
| — | M2 re-anchored off the AMLS pivot and moved from "steady" to **substantially parallel**, on the ground that the two sittings are nine days apart. Legacy Open Loop #2 closed. | `workspace-m2-exam-prep/CONTEXT.md` |
| 2.3 | 2.-PZ Anmeldung promoted from *Open Questions* ("reminder set?") to a required action in *Current Scope* of both live workspaces, pointing at each owning `module.yaml` for dates rather than restating them. | both live workspaces |

`validate.py`: **0 errors**. Views rebuilt.

> **The validator caught one of my own edits.** The first draft of the
> COORDINATION Deferrals entry restated the AMLS sitting date in prose —
> `COORD-EXAM-DATE`, a hard-rule-#2 violation. Corrected to name the slot and
> point at the owning module record. Worth recording: the rule fired on the
> operator, which is the case it was written for.

### Deliberately not applied

- **`module-hu-amls/module.yaml` `attempts` — untouched.** It still reads
  `termin: 3 · result: registered`. The enum offers only
  `registered | withdrawn | passed | failed`, and Rücktritt, never-registered and
  no-show are not the same event. Aram said he will not write it; he did not say
  by which mechanism, and §4 forbids inferring a module fact not explicitly
  stated. **Consequence, and it is visible:** `los status` still leads with
  *"exam: 2026-08-27 — AMLS (Termin 3)"* as the next exam, because the owner of
  exam facts still says he is registered. One word from Aram closes this.
- **`module-hu-amls` `status`** stays `enrolled` for the same reason —
  `paused`/`dropped` would assert an administrative event.
- **Python `estimate_minutes` (2.5)** — populating 38 missing estimates would be
  inventing Aram's data, not cleaning it. Left as the honest gap; the fix is
  either his numbers or a view that reports "unestimated" instead of summing.
- **Visibility debt (52 sources)** — WORKFLOWS §6a is explicit that this is
  repaid on use and never bulk-backfilled.
- **Seminar IuG peer review (2.4)** — a question of fact, Part 5 Q5.
- **Stale `.git/index.lock`** — could not be removed from the sandbox
  (`Operation not permitted`). Still blocking commits; Aram runs
  `rm repository/.git/index.lock`.

### Still open

Part 5 Q1 (drop mechanism), Q3 (Bachelor-UEWP LP gap), Q5 (Seminar submission).
Q2 and Q4 are resolved — next year, and the freed ~66 h goes to the AML L08–L11
build plus a genuinely parallel M2.

**Finding 2.1 is untouched by any of this.** The evidence layer is still empty:
99 stage notes, 99 empty, `evidence 0/50`. Shelving AMLS bought calendar room; it
did not create evidence. Two exams remain, and the AML L08–L11 artifacts do not
exist yet.
