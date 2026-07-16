# Learning OS v3 — Migration Plan (Consolidated v3.1)

## 1. Objective

Migrate the current repository (`semestercontext/`, including `Masters-Planning/`) into Learning OS v3 without losing: user-authored synthesis, source evaluations, concept identities, meaningful relationships, module facts, handwritten originals, project context, Git history where practical, or recoverability of the original structure.

Migration is staged, reversible, and evidence-based.

## 2. Two-stage strategy

**Stage 1:** Phase 0 (safety) → Phase 1 (inventory) → Phase 2 (scaffold) → Phase 3 (pilot).

**Hard gate:** the user reviews and approves the pilot report.

**Stage 2:** Phases 4–8 (full migration, material separation, generation, validation, cutover). Stage 2 must not begin before the gate.

## 3. Core migration principle

Do not convert every existing artifact into a new canonical object. First classify each file as:

1. durable synthesis;
2. source identity or evaluation;
3. concept or relationship information;
4. module facts;
5. active operational workspace material;
6. cross-workspace coordination facts;
7. historical workspace material;
8. deterministic generated view;
9. agent-computed disposable artifact;
10. external material;
11. code project;
12. dependency or unrelated file;
13. unresolved.

## 4. Phases

### Phase 0 — Safety baseline

- clean Git commit + tag; full filesystem backup;
- record repository root, materials root, projects root;
- create `migration/inventory.json`, `migration/path-map.csv`, `migration/unresolved.md`;
- no deletion or overwriting of originals.

### Phase 1 — Inventory

For every authored file record: old path, type, size, hash, likely role, canonical candidate, target destination, confidence, notes. Exclude dependency trees, environments, cloned repositories, and vendored documentation from authored-knowledge analysis.

### Phase 2 — Scaffold

Create the target tree (including `records/`, `system/schema/`, `.gitignore` with `generated/*`), copy this spec package into `system/`, create root `README.md` and `CLAUDE.md`. **The authored repository is a fresh Git repository** — legacy history stays with the legacy tree. Do not move knowledge yet.

### Phase 3 — Pilot (mandatory contents)

- **the AML–SaD Master Wiring** (`Plans/ML/foundations/reference/AML-SaD_Master_Wiring.md`) — mandatory because it is the hardest decomposition in the repository: concept relations + source judgments + operational sequencing + synthesis in one file;
- one complete ML lecture unit (Ultimate Reference + Mini Plan + Exercise Bank + Mock Exam);
- one mathematics unit;
- one source crosswalk (e.g. `SaD_Source-Crosswalk_L01-L15.md`);
- one user-authored synthesis note;
- one active operational area (including its COORDINATION facts);
- module records for at least two modules, including one with a withdrawal + second sitting and the Kombimodul;
- one handwritten attachment if available.

Migrate the pilot, generate all outputs, run applicable acceptance tests, then evaluate against the frozen retrieval questions in `PILOT-CRITERIA.md` (5/5 to pass; ≤3/5 stops the migration). Produce the pilot report. **Stop for user review.**

### Phase 4 — Canonical extraction

**Ultimate References and durable notes** — migrate synthesis to `knowledge/notes/`; preserve original prose; assign stable IDs; attach concepts and sources; retain original path in the migration map.

**Exercise banks and mock exams** — durable notes with `role: exercise-bank` / `role: mock-exam`. Never auto-archive live exam material.

**Mini Plans** — workspace or disposable plan content; a note only if it has durable independent value.

**Crosswalks** — decompose: pedagogical judgments → source records (canonical); narrative and sequencing rationale → note with `role: crosswalk`; confirm the generated selector view reproduces the original table before the original is retired.

**Concept index (CONCEPT-INDEX.md)** — extract concept identities, aliases, and note associations. Do not copy depth glyphs as canonical truth. Regenerate the index.

**Degree and semester wiring (DEGREE-WIRING.md, WIRING.md)** — extract only durable concept-to-concept semantics into the relation registry; do not convert module edges blindly; planning context → archived workspaces.

**Module cards + Prüfungs facts** — extract institution, code, credits, exam type, attempts (including the 2026 Rücktritte and 2. Termine), and grades into `records/modules.yaml`. Unique interpretation prose → notes; card structure → archived context or discarded after extraction.

**Degree planning (MASTERS-MODULE-MENU.md, MASTERS-MODULE-PLAN.md, MTS-Ground-Truth.md, StuPO PDFs)** — deliberation → standing `workspace-degree-planning`; StuPO PDFs → materials, referenced as sources; committed facts → `modules.yaml`.

**Status, handoff, chat-division, and plan files** — active state → workspaces + `COORDINATION.md` facts (each fact routed to its single owner); completed state → archived workspaces; durable insights embedded in operational files → extracted into notes; historical instructions → migration archive.

**SESSION-LOG.md** — archived workspace context (historical); extract only durable insights into notes. It is not lost; it is retired from operational duty.

**Resource libraries (LEARNING-RESOURCES.md, MASTERS-*-RESOURCES.md)** — deduplicate source identities; preserve contextual evaluations; attach concept-specific usefulness; point `material://` URIs at the materials root.

**Legacy validators (check_links.py, check_system.py, lychee.toml)** — retired at cutover; replaced by `tools/validate.py` (see BUILD-SPEC). Keep lychee config only if the user wants the optional online URL audit.

### Phase 5 — Materials and projects separation

- books, PDFs, videos, slides, datasets → `LearningOS/materials/`; durable references become `material://` URIs;
- active code repositories (mlprov, amls-project, stratum, skrub clones) → `LearningOS/projects/` **only when the move is safe** (paths, remotes, teammates, running work); otherwise document locations and exclude them from the knowledge root;
- never break ongoing project work.

### Phase 6 — Full generation

Manifest, concept index, source index (with selector views), module view, coordination view, backlinks, validation report, migration summary.

### Phase 7 — Validation

Run all acceptance tests. Do not delete legacy originals until canonical counts are reviewed, unresolved references documented, generated outputs rebuild cleanly, and pilot + full migration are approved.

### Phase 8 — Cutover

Freeze the legacy tree under `LearningOS/legacy/` (or a tagged commit); make `LearningOS/repository/` the default root; update root `CLAUDE.md`; document regeneration and validation commands.

## 5. Created-date policy

For migrated notes, in order of preference:

1. existing metadata;
2. first Git commit of the file;
3. filesystem metadata;
4. migration date (recorded as such in the migration map).

## 6. Legacy mapping table

| Legacy artifact | v3 treatment |
|---|---|
| Ultimate Reference | Durable note |
| Handwritten transcription | Durable note + attachment |
| Mini Plan | Workspace or disposable plan |
| Exercise Bank | Durable note, `role: exercise-bank` |
| Mock Exam | Durable note, `role: mock-exam` |
| Crosswalk | Source evaluations (canonical) + narrative note `role: crosswalk` |
| CONCEPT-INDEX.md | Extract identities/aliases; regenerate |
| DEGREE-WIRING / WIRING.md | Extract durable concept semantics; archive planning context |
| Module cards | Facts → `records/modules.yaml`; prose → notes; views regenerated |
| MASTERS-MODULE-MENU / -PLAN / MTS-Ground-Truth | Standing `workspace-degree-planning` + facts → modules.yaml |
| SEMESTER-STATUS / MASTERS-STATUS | Facts → COORDINATION.md + modules.yaml; rest → workspaces/archive |
| HANDOFF / MASTERS-HANDOFF / CHAT-DIVISION | Workspace context or obsolete agent instruction (archive) |
| SESSION-LOG.md | Archived workspace context; extract durable insights |
| LEARNING-RESOURCES / MASTERS-*-RESOURCES | Source registry + collections |
| Dashboards | Generated views |
| check_links.py / check_system.py / lychee routine | Retired; replaced by tools/validate.py |
| Raw PDF / book / video / slides | `LearningOS/materials/` |
| Project repository | `LearningOS/projects/` or documented external location |
| Dependency tree / venv | Excluded entirely |

## 7. Preservation rules

- Preserve original bytes before transformation.
- Do not silently rewrite user-authored prose.
- Keep handwritten originals.
- Keep legacy identifiers in migration maps when useful.
- Preserve unresolved ambiguity explicitly.
- Do not infer mastery from file presence.
- Do not delete duplicate-looking content until semantic review.
- Prefer reversible copies or `git mv`.
- Generated legacy files may be recreated rather than preserved only after canonical inputs are confirmed.

## 8. Migration reporting

```text
migration/
├── inventory.json
├── path-map.csv
├── unresolved.md
├── duplicate-candidates.md
├── source-dedup-report.md
├── concept-alias-report.md
├── module-extraction-report.md
├── semantic-risk-report.md
├── pilot-report.md
└── final-report.md
```

`final-report.md` must include: migrated counts by type, archived counts, excluded material counts, unresolved items, manual decisions, files not migrated and why, validation results, remaining risks.
