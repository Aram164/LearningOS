# Standard plan creation and lecture-material mapping procedure

This procedure is mandatory for every new or revised plan in LearningOS or the
bounded Job learning area, and for every module learning surface.
It turns a material review into one reviewable `module-plan-import` package
without silently losing sources, inventing scope, forcing one study order, or
discovering structural mistakes only after canonical files have been touched.

## One plan template, two bounded profiles

All newly authored plans use `plan_template_version: 1`. There is one shared
stage and resource contract in `system/schema/learning-plan.schema.json`:

- every stage has `id`, sequential `number`, `title`, `status`, `objective`,
  `done_when`, `exam_critical`, `concepts`, `scope_triage`, `resources`,
  `attachments`, and `source_feedback`;
- curriculum stages add `working_note` (plus curriculum-only detour/completion
  state); and
- Job stages add `job_context`. Its Stratum anchor is descriptive and strictly
  read-only; no plan operation may write the Stratum worktree or `.git`.

Generate a valid starting record instead of copying an old plan:

```bash
.venv/bin/python tools/los.py plan-template curriculum \
  --module-id module-example --unit-id unit-example-l01 --title "Lecture 01"
.venv/bin/python tools/los.py plan-template job --title "Rust systems track"
```

The curriculum and Job schemas both reference that shared contract. The Core
Job gateway expands editor drafts using it. Legacy records remain readable as
history, but creation gateways reject them as templates.

The interface reads the same generator rather than carrying its own defaults.
`plan.template` is a declared read-only query (`system/contracts/capabilities.yaml`)
answering the `plan-template-v1` envelope in `system/schema/plan-template.schema.json`:

```bash
.venv/bin/python tools/los.py plan-template job --title "Rust systems track" --json
```

Obsidian's *Create study plan* prefills from that answer, and the Job dashboard
projects each plan's `plan_template_version` so a record that predates the
standard is labelled rather than silently shown as conforming. Anything that
authors a plan — SOP, gateway, or interface — must go through this generator;
a second copy of the defaults is the drift this standard exists to remove.

Use the project environment. If `.venv/bin/python` does not exist, run
`make setup` once. Do not assume a global `los` executable exists.

## Definition of done

A plan is complete only when all of the following are true:

1. every local and linked learning material in scope appears in the coverage
   audit, including duplicates, older variants, exercise assets, bibliographies,
   and unreachable links;
2. every item has an explicit disposition: selected, reference-only, deferred,
   duplicate, superseded, off-scope, or unresolved;
3. current taught material is the scope authority; filenames, numbering, books,
   search snippets, and prior-year material are never treated as scope evidence;
4. each normal lecture has its own unit with a knowledge map of what the lecture
   covers; a cluster is used only when the authoritative material actually
   defines one, while synthesis/review units are auxiliary and never replace
   lecture units;
5. every usable material appears as a lecture-specific option with title,
   format, explanation angle, covered knowledge nodes, depth, scope status, and
   exact locator; the overview is complete even when nothing is selected;
6. `source_selections` records actual learner choices, and every unit of an
   active or enrolled module carries a `study-map.yaml` on plan template v1
   (OPERATOR.md rule 6). A complete material menu is not a substitute: it says
   what may be used, not in what order or against what proof. Until 2026-08-22
   the map was optional here, and the result was 27 enrolled lecture units with
   a full menu, a knowledge map, and nothing to work through;
7. the package passes the no-write preflight;
8. the snapshot-guarded import succeeds once; and
9. validation, generation, focused tests, and the final diff are clean.

## Gate 0 — establish the contract and repository state

Run:

```bash
.venv/bin/python tools/los.py capabilities --json
.venv/bin/python tools/los.py bootstrap
git status --short
```

Preserve unrelated changes. Read the current module, source map, units, optional
study maps, workspace, the relevant JSON Schemas, and any earlier plan package
before drafting. Older plans are evidence about possible coverage, never the
semantic authority or a required output shape. Copy `snapshot.snapshot_id` from
`bootstrap`; the actual import requires it. A preflight may run without it, but
an import may not.

## Gate 1 — build the material inventory before writing stages

Create a coverage audit from
`system/templates/plan-coverage-audit.template.md` in the owning workspace's
`outputs/` directory.

Inventory all of these, even when they will not be selected:

- current lecture decks, recordings, transcripts, handouts, notebooks, code,
  exercise sheets, exercise decks, solutions, mock exams, and course notices;
- every file under the authoritative material roots, including files ignored
  by Git and files with misleading or duplicate names;
- prior-year and alternate versions;
- every book, paper, course, playlist, documentation page, and URL named by a
  deck, bibliography, preserved plan, source collection, or workspace input;
- locally stored external course banks and their solutions; and
- materials already registered in the module/workspace plus materials named in
  the authoritative artifacts but not yet registered.

`rg --files` is the first file inventory tool. If the materials tree is
gitignored and therefore invisible to it, use a narrowly scoped `find` on the
exact material root. Never scan the quarantined `Job/` tree.

Open the materials. For PDFs and slide decks, extract text for search and inspect
the relevant rendered pages for formulas, diagrams, tables, exercise prompts,
and page ordering. Never infer contents from a filename, lecture number, file
count, or an old plan. Hash same-looking files to distinguish duplicates from
different editions.

For linked material, open the primary/official page, verify that the locator
still resolves and matches the claimed topic, record the verification date, and
retain an explicit unresolved/deferred row when it does not. Search results and
third-party summaries are discovery aids, not final evidence.

The count of registered source IDs is not a completeness test. The audit's
item-by-item inventory is the completeness evidence.

## Gate 2 — reconcile scope and granularity

Use this authority order:

1. current taught deck/recording/brief;
2. current exercises and solutions;
3. current official bibliography or course page;
4. prior-year variants, only after a topic-level comparison;
5. books and external courses for explanation, derivation, or practice.

Record mismatches instead of smoothing them over. An older L11 is not a current
L11 merely because its number matches. An exercise asset that contains a topic
missing from the lecture sequence becomes an explicitly justified topic/bridge
unit or remains a recorded gap; it is not silently forced into the nearest
lecture.

Create one lecture unit per ordinary lecture. Split combined plans such as
`L06–L10` into L06, L07, L08, L09, and L10. A combined exam-synthesis unit may
remain only as an auxiliary review unit with explicit parent/child or purpose
context.

For every unit, finish its semantic map before considering stages:

- authoritative scope material and the exact concepts actually taught;
- stable knowledge nodes with short explanations and explicit `builds_on`
  edges where the dependency is meaningful;
- every first exposure, intuition, derivation, implementation, practice,
  reference, and advanced-depth option available for those nodes;
- one lecture-specific angle statement explaining what each option contributes,
  rather than a generic description of the source as a whole;
- format grouping (`course-material`, `exercise`, `book`, `video`, `website`,
  `course`, `documentation`, `code`, or `paper`);
- current/prerequisite/complementary/optional/prior-year/out-of-scope status,
  with no older source presented as current; and
- a stated exercise/practice gap when no matching asset exists.

Do not choose a winner merely to make a plan look complete. The permanent
output is a navigable knowledge-to-material graph. The learner chooses from it.

## Gate 3 — build the package from the canonical template

Copy `system/templates/module-plan-import.template.yaml`. Do not use YAML
anchors, aliases, or merge keys. Quote text containing colons or YAML-sensitive
punctuation. The gateway also serializes without aliases so shared defaults
cannot leak anchors into authored files.

When an ordinary lecture already has its knowledge nodes and complete rich
source routing, use the tracked draft assembler instead of rebuilding the join
in an ignored workbench script:

```bash
.venv/bin/python tools/assemble_lecture_study_maps.py \
  --out work/active/<workspace>/outputs/lecture-map-drafts \
  --unit <unit-id>
```

It writes no canonical file. Before it writes a draft, it refuses stale curated
concept edges, missing concept coverage, uncovered knowledge nodes, a drifting
plan template, or a schema-invalid map. Review the resulting YAML, then apply it
through `unit.map.import` (or include it in the module package). This preserves
the reproducible creation operation without treating a deterministic draft as
learner-approved pedagogy.

The package must contain `plan_contract.version: 2`,
`plan_contract.plan_template_version: 1`, the repository-relative coverage-audit
path, all six completeness checks set to `true`, and an `intentional_reorders`
list (normally empty). Every supplied `study_map` must also declare
`plan_template_version: 1` and sequential stage numbers. These are truth claims:
do not set one until its audit work is complete.

Plan expansion must preserve the relative order of every existing module unit
and study-map stage. The preflight enforces this mechanically: adding a new
record is allowed, but silently moving existing records is rejected. A genuine
pedagogical reorder must be listed in `intentional_reorders` with target
`module-unit-order` or `study-map-stage-order`, the affected module/map ID, and
a concrete reason. A declaration that does not correspond to an actual reorder
is also rejected, so stale approvals cannot linger in reusable packages.

Use only schema enums. Module source-map roles are:

`course-material`, `spine`, `first-exposure`, `intuition`, `derivation`,
`implementation`, `practice`, `exam-preparation`, `optional-depth`,
`reference`, and `candidate`.

Each rich `unit_routes` entry is one source-to-lecture edge and must contain:

- `unit_id`, a human-readable option `title`, and `format`;
- `angle`, written for this lecture rather than copied from global source
  metadata;
- `covers`, containing only knowledge-node IDs declared by that unit;
- `depth`: `orientation`, `intuition`, `course-aligned`, `derivation`,
  `implementation`, `practice`, or `advanced-reference`;
- `scope`: `current`, `prerequisite`, `complementary`, `optional`, `prior-year`,
  or `out-of-scope`; and
- the most exact safe `locator`, `url`, or `vault_path` available.

Legacy string routes remain readable for backward compatibility, but a newly
mapped lecture must use rich routes so the interface can explain the choice.

Additional package invariants:

- `module_patch.unit_order` lists every final owned unit exactly once, including
  pre-existing units not changed by this package, and agrees with the numeric
  `order` on those units;
- the `stages` list is the study-map ordering authority; plan expansion keeps
  the relative sequence of existing stage IDs unless an intentional reorder is
  explicitly declared and reviewed;
- every unit, knowledge-node, and optional map/stage ID is unique and
  module-scoped;
- every material `covers` reference resolves inside its target unit;
- when a study map is supplied, `current_stage` resolves and every working note
  stays below its owning unit;
- every source used by a unit scope, selection, stage resource, feedback entry,
  or workspace update exists in the module source map;
- every source used by a unit explicitly routes to that unit in
  `unit_routes`;
- source selections are empty until the learner has chosen; if a selection
  names `stage_ids`, those IDs resolve to stages in the same optional map;
- the workspace's `sources` and `unit_ids` contain the final intended joins;
- older-only material is labelled as prior-year/reference/candidate and never
  described as current; and
- absence of a matching exercise is recorded, not filled by mislabelling a
  nearby sheet.

## Gate 4 — run the no-write preflight

Run:

```bash
.venv/bin/python tools/los.py module-plan-import MODULE_ID \
  --file work/active/WORKSPACE/outputs/PLAN.yaml --check
```

The command checks the plan contract, source routing, schemas, references,
module ownership, unit order, study-map state, and workspace joins in a shadow
repository. Success reports `canonical_files_written: 0`. A failure is a
rejected plan, not a rollback: correct the package or audit and rerun the check;
do not patch canonical YAML to make a defective package pass.

Read the first diagnostic completely before changing anything. Then scan for
all occurrences of the same failure class (for example, every non-schema role
or every missing source route) and fix the class once.

## Gate 5 — apply once with optimistic concurrency

After a successful check, run `bootstrap` again and use its current snapshot:

```bash
.venv/bin/python tools/los.py module-plan-import MODULE_ID \
  --file work/active/WORKSPACE/outputs/PLAN.yaml \
  --expected-snapshot sha256:CURRENT_SNAPSHOT
```

If the snapshot conflicts, reload, review the intervening changes, regenerate
the package if necessary, and preflight again. Never bypass the guard.

## Gate 6 — post-import acceptance

Run, in order:

```bash
make check
make views
make check
.venv/bin/python -m pytest -q tests/test_curriculum_v2.py
git diff --check
git status --short
```

Also run `.venv/bin/python tools/validate.py --online` when registered or newly
selected web sources changed. If the module is still covered by a compatibility
migration, run that migration in dry-run/report mode and require `0 action(s)`;
a migration must preserve evolved units and source maps instead of recreating
an older snapshot.

Review the final diff against the coverage audit, not only against the package:
every reviewed material must land in the intended unit menu with the correct
angle and disposition, chosen material must remain distinguishable from merely
available material, optional study maps must use only chosen resources, lecture
units must not have collapsed back into a cluster, and unrelated dirty-tree
changes must remain untouched.

## Why these gates exist

| Observed failure | Permanent control |
|---|---|
| Drafting before the complete local/web inventory | Coverage audit is required before an executable package. |
| Trusting filenames or old lecture numbers | Materials must be opened; current/prior reconciliation is explicit. |
| Inventing source roles or malformed YAML scalars | Canonical template, schema enums, and shadow validation. |
| A source appeared in a stage/workspace but not its source map | Package routing preflight checks both presence and `unit_routes`. |
| A long source list gave no reason to choose one item | Every rich route carries a lecture-specific angle, depth, scope, and knowledge coverage. |
| A generated plan silently became the only way to view a lecture | Knowledge maps and complete material menus are permanent; study maps are optional personal projections. |
| YAML anchors changed serialized canonical files | Template forbids anchors and the gateway emits alias-free YAML. |
| Discovering schema errors only after canonical writes | `--check` validates a shadow repository and writes zero files. |
| Expanding a plan silently reshuffled existing units or stages | Preflight preserves relative order by default; deliberate reorders require a reasoned declaration. |
| Applying against stale state | The real import requires `--expected-snapshot`. |
| A compatibility migration recreated old units after planning | Post-import migration dry-run must be idempotent. |
| A combined lecture range hid missing individual coverage | One ordinary lecture equals one unit knowledge/material map; synthesis is auxiliary. |
