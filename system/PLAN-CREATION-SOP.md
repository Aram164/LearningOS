# Standard plan-creation procedure

This procedure is mandatory for every new or revised module plan. It turns a
material review into one reviewable `module-plan-import` package without
silently losing sources, inventing scope, or discovering structural mistakes
only after canonical files have been touched.

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
4. each normal lecture has its own unit and study map; a cluster is used only
   when the authoritative material actually defines one, while synthesis/review
   units are auxiliary and never replace lecture units;
5. the package passes the no-write preflight;
6. the snapshot-guarded import succeeds once; and
7. validation, generation, focused tests, and the final diff are clean.

## Gate 0 — establish the contract and repository state

Run:

```bash
.venv/bin/python tools/los.py capabilities --json
.venv/bin/python tools/los.py bootstrap
git status --short
```

Preserve unrelated changes. Read the current module, source map, units, study
maps, workspace, the relevant JSON Schemas, and any earlier plan package before
drafting. Copy `snapshot.snapshot_id` from `bootstrap`; the actual import
requires it. A preflight may run without it, but an import may not.

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

For every unit, finish a coverage row before drafting stages:

- authoritative scope material;
- selected first exposure, spine, derivation, implementation, and practice;
- reference-only/deferred items with reasons;
- exact stage destination for each selected locator; and
- a stated exercise/practice gap when no matching asset exists.

## Gate 3 — build the package from the canonical template

Copy `system/templates/module-plan-import.template.yaml`. Do not use YAML
anchors, aliases, or merge keys. Quote text containing colons or YAML-sensitive
punctuation. The gateway also serializes without aliases so shared defaults
cannot leak anchors into authored files.

The package must contain `plan_contract.version: 1`, the repository-relative
coverage-audit path, and all six completeness checks set to `true`. These are
truth claims: do not set one until its audit work is complete.

Use only schema enums. Module source-map roles are:

`course-material`, `spine`, `first-exposure`, `intuition`, `derivation`,
`implementation`, `practice`, `exam-preparation`, `optional-depth`,
`reference`, and `candidate`.

Additional package invariants:

- `module_patch.unit_order` lists every final owned unit exactly once, including
  pre-existing units not changed by this package;
- every unit/map/stage ID is unique and module-scoped;
- `current_stage` resolves, and every working note stays below its owning unit;
- every source used by a unit scope, selection, stage resource, feedback entry,
  or workspace update exists in the module source map;
- every source used by a unit explicitly routes to that unit in
  `unit_routes`;
- source selections that name `stage_ids` resolve to stages in the same map;
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
every selected material must land in the intended unit/stage, every non-selected
material must retain its disposition, lecture units must not have collapsed
back into a cluster, and unrelated dirty-tree changes must remain untouched.

## Why these gates exist

| Observed failure | Permanent control |
|---|---|
| Drafting before the complete local/web inventory | Coverage audit is required before an executable package. |
| Trusting filenames or old lecture numbers | Materials must be opened; current/prior reconciliation is explicit. |
| Inventing source roles or malformed YAML scalars | Canonical template, schema enums, and shadow validation. |
| A source appeared in a stage/workspace but not its source map | Package routing preflight checks both presence and `unit_routes`. |
| YAML anchors changed serialized canonical files | Template forbids anchors and the gateway emits alias-free YAML. |
| Discovering schema errors only after canonical writes | `--check` validates a shadow repository and writes zero files. |
| Applying against stale state | The real import requires `--expected-snapshot`. |
| A compatibility migration recreated old units after planning | Post-import migration dry-run must be idempotent. |
| A combined lecture range hid missing individual plans | One ordinary lecture equals one unit/map; synthesis is auxiliary. |

