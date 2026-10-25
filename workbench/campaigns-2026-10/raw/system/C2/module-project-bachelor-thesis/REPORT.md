# C2 — module-project-bachelor-thesis (item L2-10)

GLM-5.3-Flash session, 2026-10-24, evidence only. Clone
`~/los-glm-C2-2026-10/repository` on `takeover/complete-and-install-2026-10-23`
(commit `a2e2d49d`), materials mounted at `~/los-glm-C2-2026-10/materials` →
live tree. Nothing was pushed; nothing outside this workbench folder was
written. No fix packages were prepared (Aram's kickoff: evidence only).

## Verdict

**0 defects.** All four per-module checks pass — mostly vacuously, because the
module carries no routes, no `material://` URIs, no locators and no PDF
references. The validator emits **0 warnings for this module**. Everything the
module references resolves on disk. No post-snapshot write ever touched the
module: its only git history is the initial snapshot itself.

## What this module is

`curriculum/modules/module-project-bachelor-thesis/` is a **fossil kept for
link compatibility**, not a live study surface:

- `module.yaml`: `compatibility_only: true`, `migrated_to:
  project-bachelor-thesis`, `migrated_at: 2026-08-06T04:04:58+00:00`,
  `migration: projects-v1`. It is excluded from active module listings
  (`tools/learning_os/app/handlers/reads.py:477`).
- `source-map.yaml`: `sources: []` — the module adopts no sources.
- Two units. `unit-thesis-landscape` has one study map with **one stage and one
  resource**; `unit-thesis-experiments` has `status: needs-map` and no study
  map, with `scope: A later thesis milestone; scope is intentionally not
  invented.`
- The single resource (`units/unit-thesis-landscape/study-map.yaml`, stage
  `stage-01-research-landscape-and-question-framing`):

  ```yaml
  - kind: reference
    label: Existing thesis landscape and plan
    vault_path: work/active/workspace-thesis-mle-medical/outputs/thesis-landscape-and-plan.md
  ```

  `kind: reference` rows are exempt from route binding by design — the
  validator returns early on them (`tools/learning_os/derive/validation/
  plan_rigor.py:569`, docstring at :559–566: "A `reference` row is a pointer,
  and pointing outside the module's map is what it is for").

The live content migrated to `projects/registry/project-bachelor-thesis.yaml`
(the only project record in the repo), which likewise holds no routes and no
material references — three `files` entries, two open `decisions`, and
workstream/step structure only.

## Check results

**1. `vault_path` / `material://` against the file named in `locator`.**
No `material://` URI and no `locator` field exists anywhere in the module
tree. The one `vault_path` resolves: `work/active/workspace-thesis-mle-medical/
outputs/thesis-landscape-and-plan.md`, 17,527 bytes. **Pass.**

**2. Page ranges inside the PDF's real page count.** No PDF is referenced by
the module or the project record. **Vacuous.**

**3. TOC/section named in `angle_detail` against the text.** No
`angle_detail` field exists in the module. The one prose pointer is the
`reference` row above; its target opens as the claimed document ("Thesis
landscape & plan — Exploring and optimizing MLE agents for medical use cases",
operator-compiled 2026-07-20). **Vacuous / pass.**

**4. Duplicate `locator` / `angle_detail` among sibling routes of one
`(source_id, unit_id)` group.** No routes exist, so no sibling groups.
**Vacuous.**

## Validator warnings — triage

`.venv/bin/python tools/validate.py --compact` in the clone: **0 error(s),
1468 warning(s)**, full list in the clone's `generated/reports/validation-
report.md`. Grep over the full list for `module-project-bachelor-thesis`,
`study-map-thesis-landscape` and `workspace-thesis-mle-medical`: **0 hits**.
The module contributes nothing to the 1468. (Near-name hits checked and
assigned elsewhere: `note-sad-*` ATTACH-LOCAL-ABSENT rows belong to the m2-
statistik attachments; `study-map-amls-*` RESOURCE-SCOPE-UNBOUND rows belong
to the skipped `module-hu-amls`.) Nothing to triage.

## Provenance — original design vs damage

Git history in the clone starts at `1d32c918 Initial clean LearningOS Core
snapshot` (the 2026-10-19 snapshot).

- **The module tree is untouched since the snapshot.** `git log --follow --
  curriculum/modules/module-project-bachelor-thesis/` shows exactly one
  commit: `1d32c918`. There has been no post-snapshot write that *could* have
  caused damage.
- The workspace `work/active/workspace-thesis-mle-medical/` holds four files
  (CONTEXT.md, inputs/original-thesis-brief.md, outputs/thesis-landscape-
  and-plan.md, scratch/.gitkeep). Aram's preservation commit `98f7e3ad`
  (2026-10-23) touched only CONTEXT.md (+1/−6); the plan and brief are
  unchanged since the snapshot.
- The project record's current rich shape (boundaries, decisions, files,
  linked_module_ids, milestone_ids, structure) also comes from Aram's own
  `98f7e3ad` — his preservation commit, original by definition.
- Cross-check: module and project record carry the same `source_sha256`
  (`36e7794a…`), matching `migrated_from`/`migrated_to`/`migration:
  projects-v1` on both sides.
- The study map's `source_plan` points at `work/active/workspace-thesis-mle-
  medical/outputs/thesis-landscape-and-plan.md` with `provenance: operator`;
  the file exists and its content (§6 phase plan, §7 supervisor decisions)
  matches the stage's objective and done_when ("Record the concrete next
  research decision…"). The two-unit split (landscape / experiments) mirrors
  the plan's Phase 0–3 and the project record's two workstreams.

## Observations (not defects)

- **`milestone_ids` dangle.** The project record declares `milestone-thesis-
  scope` and `milestone-thesis-baseline`, and no milestone record exists
  anywhere in the repo (`projects/` holds only the registry, aliases and
  relations). Traced: both ids are **hardcoded output of the projects_v1
  migration itself** (`tools/migrations/projects_v1.py:92`). Original
  migration output, not damage. Platform handlers read `milestone_ids`
  defensively (`tools/learning_os/app/handlers/platform.py:200,239`).
- **No back-link from project to the compatibility module — by design.**
  `linked_module_ids: [module-hu-aml, module-hu-amls]` omits the module it
  migrated from because the validator makes that an error
  (`tools/learning_os/derive/validation/projects.py:34-36`: a linked module
  that is unknown **or** `compatibility_only` raises REF-MODULE "unknown
  active module"). Both linked ids are active modules; validator 0 errors
  confirms.
- **`unit-thesis-experiments` stays `needs-map`.** Declared intentionally in
  the unit's `scope`; the project record's experiments workstream is
  `planned`. Consistent with the source plan (experiments follow the
  landscape milestone).
- **`module-hu-amls` in `linked_module_ids`** is the archived/dropped module
  C2 skips — noted only because future sessions must not read that link as a
  reason to audit it.

## Method note

All module files were read in full (they total well under one screen of
YAML); the validator was run once in the clone; every path quoted above was
stat'ed or opened in the clone. Claims about validator internals cite the
clone's code at file:line, read in this session. No PDFs needed opening —
none are referenced.
