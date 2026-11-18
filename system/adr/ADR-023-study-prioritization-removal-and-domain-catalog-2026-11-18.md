# ADR-023: Study selection without built-in prioritization, and one published domain catalog

Date: 2026-11-18. Status: accepted. Extends: ADR-005, ADR-006. Amends
`system/ARCHITECTURE.md` invariant 22b and `system/VALIDATION.md`
governed-recovery wording (one sentence each).

## Context

The passive resume screen ranked the learner's next step for him: an exam gate
confined `--unit`, the menu preferred one map status over another, recovery
auto-steered toward the last historical destination, a "Top goal" decoration
ranked goal clusters by exam proximity, and module rows picked one active unit
to represent a module. Three review rounds verified each behavior in code and
found the two halves of the system disagreeing about who may study what: Core's
menu admitted skipped stages that the UI's `isOpenStage` treats as closed, and
a literal enrollment filter would have silently dropped every skill, foundation
and project module — the lifecycle projection gives them no registrar. Domain
grouping, meanwhile, was derived independently in four places (the markdown
atlas, the bootstrap glance, and each UI design), each with its own label,
order and membership rules. This ADR records the campaign's decisions (the
2026-11-18 streamlining plan §2, D1–D11) as the contracts the implementation
pins, so a later session can check the code against the decision rather than
against a memory of it.

## Decision

**1. The system offers choices; it does not filter them by preference, rank
or decorate them (D1).** Eligibility rules still decide what counts as a
choice; the point is that no preference or ranking does. Every built-in study
prioritization is removed: the exam-module
`--unit` confinement, the Study Desk semester chain, the menu status-rank
preference, recovery auto-steering, the passive "Top goal" decoration, and the
subordinate active-unit selection inside module rows. What stays is named, so
removal is never over-applied:

| Kept | Why it stays |
|---|---|
| `ranked_scan` in `intelligence scan` (`reads.py:776`) | Explicitly requested output; the learner asked for the ranking. |
| The `--json` dossier's `top-cluster` section | Explicit machine request, labeled exam-proximity facts; a hashed dossier section, so its digest moves when the top cluster moves — that is the existing documented behavior. |
| `modules.ts` semester grouping | Factual grouping of records, not a recommendation. |
| The pointer-first in-progress list (`study-work.ts`) | The learner's own recorded pointer, not a preference. |

**2. One candidate builder defines eligible study choices once (D2, D10).** A
single domain predicate (`domain/curriculum/stages.py::study_candidate_stage`)
owns eligibility; the Core builder (`resume.py::_study_rows`) consumes it for
scope, ordering and row construction, and the manifest projection publishes its
verdict as `study_maps[].is_study_candidate`. The supporting lifecycle verdicts
are likewise owned by schema-pinned classification tables in
`domain/curriculum/{lifecycle,stages}.py` and published once in the manifest
(`modules[].is_settled`, `modules[].is_retired`, `stages[].is_open`,
`resources[].is_entry`, `workspaces[].is_open`). Untargeted `--study`, the
recovery menu, explicit `--unit`, `bootstrap` (`--brief`, `--compact`, full,
exposing `study_candidates`), and every interface all consume those published
verdicts; no path bypasses them and no consumer re-derives the rules.
Eligibility filters before anything counts: one valid row beside one ineligible
map is one choice. The lifecycle table it implements:

| Dimension | Values | Rule |
|---|---|---|
| Module kind | academic, skill, foundation, project | Every kind is in the pool; kind never filters. |
| Module status | planned, enrolled, active, paused, awaiting-grade, completed, dropped, archived | Settled administrative statuses (awaiting-grade, completed, dropped, archived) close the pool; planned, enrolled, active and paused never filter. The lifecycle projection displays academic `active` as administratively enrolled; skill, foundation and project modules have no administrative status. |
| Study-map status | active, paused, ready | Eligible as open study choices. `not-started`, `ready-to-shelve` and `complete` are not. |
| Stage status | pending, active, paused | Fresh-suggestion eligible (`stage_is_open` / `stages[].is_open` is true). |
| Stage status | complete, skipped | Closed to fresh suggestions (`stage_is_open` / `stages[].is_open` is false; unknown values fail closed). Skipped joins complete so the builder agrees with the UI's `isOpenStage` — a skipped stage is a decision already made, never a next step. |
| Units without maps | — | Produce no rows; the pool is defined by study-map ownership. |

Enrollment rides each row as display-only lifecycle metadata
(`administrative_status`) and never filters the pool. The settled filter reads
the administrative axis only, so the enrollment trap above does not return:
skill, foundation and project modules have no administrative status and stay
eligible. "Exactly one" is decided only over valid rows, after eligibility
filtering.

**3. One pinned ordering (D2).** Module ID ascending, then each unit's position
in the authored `module.unit_order`, then the unit's numeric `order` for
unlisted units, then unit ID, then map ID. Status is row metadata, never a
rank. The total is computed before the five-row truncation, so the one-screen
bound never lies about how many choices exist; the UI's neutral lists use the
same rule.

**4. Recovery asks instead of guessing (D9).** The pointer wins when it
resolves — it is the learner's own last explicit study action. The full state
matrix:

| Pointer | Available choices | Historical context | Required behavior |
|---|---|---|---|
| Valid | any | any | Exact pointer destination, including terminal (complete/skipped) stages — the resolver intentionally keeps recorded stages resumable whatever their status. |
| Missing/stale | one or more | present | Choices first; the historical trail rides along as clearly secondary labeled context. |
| Missing/stale | one or more | absent | Choices; no historical guess required. |
| Missing/stale | none | present | The historical destination, labeled as history — never claimed as an available study choice. |
| Missing/stale | none | absent | The existing refusal with actionable discovery guidance. |

The menu is built independently of any history. All rows stay read-only:
`learner_choice` is false on every row, and nothing here writes the pointer —
only an explicit stage action does.

**5. Options are payload contract, not presentation (D9, D3).** The pipeline
renders `human_view` only for human output; JSON clients serialize the payload.
The selection menu is therefore defined in the payload
(`contract: resume-study-options` with `options`, `total`, `select_with` and a
`continuation` naming commands that exist), and lives outside the
content-addressed dossier: the dossier's per-section digests and key are
unchanged, and no payload key claims to identify unhashed content. No
`resume --session` is added — the pointer already implements explicit
selection.

**6. The UI hero shows the pointer, or a neutral list (D4).** Under the D2
pool and ordering: the hero is the resume pointer when it resolves; without a
pointer it is a neutral browsable list; the plan's `next_action` renders
verbatim under its own label; exam dates remain only in "Coming up". (Executed
in the UI package of this campaign.)

**7. Domain grouping is published exactly once, from named producers (D5).**
Manifest v19→v20, additive: a top-level `domains` catalog — the known domains
in fixed order with empty ones included, then every observed future bucket
sorted; unique ids; a one-based `order`; a label resolved once in Core — plus
one `domain_bucket` per note record. Producers: `atlas.py` hosts the single
bucket function (`note_domain_bucket`) and `build_domain_catalog`;
`records_knowledge.py::project_notes` publishes each note's bucket;
`manifest.py::assemble_manifest_semantic_payload` assembles the catalog;
`reads.py::_domain_glance` consumes only the published fields and never
re-derives. The catalog covers every domain id the published notes and shelves
name; the real `cross-domain` bucket is distinct from the presentation-only
"Not yet grouped" destination, which is deliberately not in the catalog. No
second published concept-membership table: browsing membership derives from
`note.concepts` plus `domain_bucket`. `test_projection_fidelity`'s derived set
gained `domain_bucket`. This retires ADR-005 decision 1's view-level shelf→domain
placement (banner on ADR-005); ADR-006's boundary — the projection is Core's,
the rendering is the UI's — is what puts the catalog in the manifest at all.

**8. One manifest bump, one re-record campaign (D6).** Contract bytes move
once: one v20 bump on this branch pair, one re-record at the end, one
release-pair CI. Recording diffs are audited in three explicit classes —
intended behavior changes, intended projection/contract metadata changes, and
incidental hash/size/identity movement; a fourth, unexplained class blocks
landing. The re-record itself belongs to the campaign's final package, not to
the implementation waves.

**9. Exams remain canonical facts (D7).** `module.yaml` ownership,
`academic_deadlines`, the dashboard exam spine and the "Coming up" panel are
untouched. Exam proximity may rank the explicitly requested intelligence scan;
it never selects anything on a passive screen.

**10. Drawing and browsing are two named memberships (D11).** Drawing
membership is the canonical majority: canvas cards, chips, counts, mini-map
sizing, cross-region link counts and marker placement all use canonical
placement where a single placement is intended. Browsing membership is the
union of the domains a concept actually touches. No inferred concept edges.

**11. Browse context is preserved; one validated resolver (D11).**
Breadcrumbs and return navigation preserve the selected browse domain while it
remains a membership of the focused concept; deep links and search without a
browse context may fall back to canonical placement. Core validates pointer
ownership and stage coherence at manifest publication (`resolve_resume_target`),
publishing `resume_pointer` only when coherent; Atlas's study marker and every
raw-pointer "current destination" claimant reuse Home's resolver, which looks
up the published records by ID (checking `unitMap.id === pointer.study_map_id`
and stage membership, and returning unresolved if any lookup misses — including
pointers to retired modules filtered from the UI store). (Decisions 6, 10 and
11 are executed in the UI package; Core publishes the catalog, buckets,
verdicts, and validated pointer they consume.)

## Consequences

- Core's resume screen no longer contains an exam gate, a status rank, or a
  passive ranking; `ranking.py` and `goals.py` survive untouched because the
  explicitly requested scan still uses them.
- Schema-pinned tables in `domain/curriculum/{lifecycle,stages}.py` own every
  curriculum status vocabulary, and skipped stages cannot re-enter the menu
  quietly: `stage_is_open` and the UI's `isOpenStage` read one published
  `stages[].is_open` verdict.
- The manifest gains `domains`, `domain_bucket`, `modules[].is_settled`,
  `modules[].is_retired`, `stages[].is_open`, `resources[].is_entry`, and
  `workspaces[].is_open` under contract v20 (`bootstrap` also aligns on
  `is_study_candidate` under `study_candidates`); the UI lock moves with it in
  the same release, and the UI stops re-deriving labels, order, membership,
  and lifecycle verdicts.
- The re-record of scenario goldens is owned by the campaign's final package;
  until then, recordings that embed v19 paths or old resume screens are known
  stale, not silently wrong.

## Rejected

- **A literal `module.status == "enrolled"` filter.** It would drop every
  skill, foundation and project module — the enrollment trap the reviews
  verified.
- **Options inside the content-addressed dossier.** It would move the dossier
  digest semantics; options are a separate payload section instead.
- **`resume --session`.** No such capability; the pointer is the recorded
  selection.
- **A second published concept-membership table.** Note links already state
  the membership; a second table is a second place to drift.
- **UI-side bucket re-derivation.** A published bucket that differs from the
  path wins; the consumer that re-derives it is the defect.
