# Learning OS v3 — Claude Build Specification (Consolidated v3.1)

## Mission

Rebuild the existing repository (semestercontext/ including Masters-Planning/) into the architecture defined by this package. The objective is not to preserve the old organization; it is to preserve valuable knowledge and facts while replacing the old structure with the frozen v3 model.

Do not redesign the architecture during implementation. This package already incorporates all agreed revisions — it is the single spec.

## Required reading

`PHILOSOPHY.md` → `WHY-REDESIGN.md` → `ARCHITECTURE.md` → `schema/*.schema.json` + `VALIDATION.md` → `CLAUDE.md` → `WORKFLOWS.md` → `MIGRATION.md` → `ACCEPTANCE-TESTS.md`. Then inspect the current repository.

## Deliverables

Target tree · root docs · canonical registries (concepts, relations, sources, **modules**) · `COORDINATION.md` · JSON Schema validation · generator tools · unified validator · migration inventory and reports · migrated notes and workspaces · separated materials and projects · generated indexes and views · automated tests · final migration report.

## Implementation order

### Step 1 — Protect the original
Clean commit + tag; full inventory with hashes; backup; migration report scaffolding; no destructive changes.

### Step 2 — Scaffold v3
Complete target tree including `records/`, `knowledge/attachments/`, `work/inbox/`, and `system/schema/`; copy this package (headed by `PHILOSOPHY.md`) into `system/`; root `README.md` and `CLAUDE.md`; `.gitignore` containing `generated/*`. Enforce the file-saving conventions of ARCHITECTURE §3.3 from the first migrated file (note filename = ID, attachments per note, materials by source ID).

### Step 3 — Implement loaders
One internal loader API supporting: consolidated and partitioned concept/source YAML; relation YAML; module records; Markdown frontmatter; workspace context files; `COORDINATION.md`. The logical model must not depend on registry partitioning.

### Step 4 — Implement validation
`tools/validate.py` enforces the JSON Schemas plus every rule in `VALIDATION.md`:

- schema conformance for all seven record types;
- ID patterns, family prefixes, uniqueness, gratuitous-suffix warnings;
- reference resolution (concepts, sources, relation endpoints, coordination dependencies);
- alias collisions; duplicate relations; duplicate sources;
- internal Markdown link integrity;
- generated-file boundaries (no canonical file cites `generated/` as input);
- material URI resolution or reporting;
- coordination ownership boundaries (no exam dates or statuses in COORDINATION.md);
- crosswalk judgment-table heuristic (warning);
- module attempt consistency;
- archived-workspace exclusion; active-workspace count warning at 8+.

**Consolidation:** validate.py replaces `check_links.py`, `check_system.py`, and routine offline lychee runs. External URLs are checked only via `validate.py --online` (or an occasional manual lychee run) — link rot is audited deliberately, not on every validation.

### Step 5 — Implement generation
`tools/generate.py` produces, deterministically except timestamps: manifest; concept index; source index **including per-lecture and per-concept selector views** (first-learning / review / implementation recommendations); module view; coordination view (modules.yaml exam spine + workspace frontmatter + COORDINATION facts + Git-derived neglect signals); backlinks; health report.

### Step 6 — Pilot migration (Stage 1 gate)
Migrate the pilot set from MIGRATION.md §Phase 3 — the AML–SaD Master Wiring is mandatory. Run all applicable acceptance tests. Produce `migration/pilot-report.md`. **Stop for user approval before Stage 2.**

### Step 7 — Full migration
Classify and migrate all authored files per the mapping table. Do not create canonical entities merely to mirror the old artifact taxonomy. Route every operational fact to its single owner. Preserve unresolved cases.

### Step 8 — Separate materials and projects
Materials → `LearningOS/materials/` with `material://` references. Code repositories → `LearningOS/projects/` only when safe; otherwise document and exclude. Never break active project work.

### Step 9 — Regenerate and test
Delete and rebuild `generated/`; run the full test suite.

### Step 10 — Final report
Migration summary; unresolved items; validation results; counts by canonical type; excluded materials; semantic-risk list; exact commands for validation and generation.

## Required tool commands

```bash
python tools/validate.py            # full offline validation
python tools/validate.py --online   # + external URL audit
python tools/generate.py            # rebuild all generated outputs
python -m pytest                    # test suite
```

One command may combine validation and generation, but individual commands must remain available.

## Generator behavior

**Manifest** — per canonical record: ID, type, title/label, path, concepts, sources, role/state, reviewed date when present.

**Concept index** — per concept: preferred label, aliases, directly linked notes (with roles), related concepts by relation type, contextual sources. No manual maturity glyphs.

**Source index** — per source: identity, type, location, concepts, contextual roles, strengths/weaknesses; plus selector views per lecture and per concept answering: best for first learning, best for review, best for implementation.

**Module view** — per module: identity, credits, semester, components, attempt history, status, grade; upcoming exam spine sorted by date.

**Coordination view** — the operational dashboard: exam spine (modules.yaml), active workspaces with status/deadline/next action (frontmatter), commitments/priorities/dependencies/deferrals (COORDINATION.md), neglect warnings (Git timestamps). Clearly marked generated and disposable.

**Backlinks** — concept→notes, source→notes, note→incoming references, workspace→durable notes, concept→incoming/outgoing relations, module→workspaces referencing it.

## Migration rules

Preserve original semantics; do not polish prose automatically; do not infer mastery; do not convert every old plan into a note; do not convert every module wire into a concept relation; do not treat folder names as identity; do not retain manually maintained indexes as canonical; do not record any exam date outside `records/modules.yaml`; do not delete unresolved files; do not introduce new canonical entity types.

## Stop conditions

Pause and report only when: the specification is internally impossible; proceeding risks semantic loss; required repository data is unavailable; a destructive action cannot be made reversible; the repository contains a canonical category not representable by the frozen model. Do not pause for ordinary classification ambiguity — preserve, report, and continue safely.

## Completion

The rebuild is complete only when the acceptance tests pass, `generated/` can be deleted and rebuilt without loss, and the pilot and final reports have been approved by the user.
