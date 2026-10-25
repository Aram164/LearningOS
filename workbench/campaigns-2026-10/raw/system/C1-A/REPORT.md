# C1-A report — curriculum and plans batch (hunting pass)

Session: GLM-5.3-Flash, 2026-10-24. Base: GitHub `origin/main` at
`d6c4779029e366718b71bda158d2aa8f9da1db39` (exactly the commit the ground
rules name). Clone: `~/los-glm-C1-A-2026-10/repository`, branch
`glm/C1-A-2026-10-24` (local only — nothing pushed, nothing committed).
The live trees, the vault, C3's clone and all other campaigns were not
touched. One focused pytest process at a time; no full suite, no gates.

Batch scope: the 11 capabilities in `system/contracts/capabilities.yaml`
whose names start with `module`, `program`, `masters-planning`, `plan`:
queries `masters-planning.dashboard`, `plan.edit-context`, `plan.template`;
commands `masters-planning.catalog.update`, `masters-planning.comparison.publish`,
`module.attempt.record`, `module.create`, `module.materials.compact`,
`module.plan.import`, `module.sitting.update`, `program.semester.update`.

## Findings (2)

Both come with a failing pytest in this folder. Each test fails on base main
and passes once the expected behaviour holds. Details, verbatim output,
contract lines, root causes and suggested fixes are in each `finding.md`.

1. **`module.create/legacy-identity-clash`** — creation accepts a module id
   that already exists as a canonical identity in the legacy registry
   `records/modules.yaml`; the declared refusal ("an existing canonical
   identity or file is refused") only checks the filesystem. The new
   partitioned record then shadows the legacy record's facts, and every
   validator stays green. Root cause:
   `tools/learning_os/app/handlers/plan.py:940-957`.

2. **`module.attempt.record/graded-attempt-dead-end`** — once a termin's
   attempt row carries a grade, correcting that termin's `result` to any
   non-passed value is refused forever (`MOD-GRADE` on the sticky old grade),
   and no payload of the capability can clear the grade. The contract's
   "updates the row for the same termin" is unreachable for exactly the rows
   that need correcting; boundary 16 forbids the hand edit that would fix it.
   Root cause: `tools/learning_os/app/handlers/admin.py:114-125` combined
   with `tools/learning_os/derive/validation/curriculum.py:21-27`.

## Attacked and held (no finding)

Labelled **probed** when I drove the real CLI/V2 gateway against a synthetic
mini repository and observed the refusal; **read** when I verified by reading
the handler, contract and procedure without a probe.

- `module.plan.import` (**probed**): unit ids with `../` traversal (1–3
  levels, including into a sibling module's real units directory) are refused
  by the staged validation before any write (`E SCHEMA` on `unit_order`,
  `E REF-UNIT`, `E UNIT-ORDER`); stage-note paths that climb out of the unit
  are refused (`E MAP-NOTE-OWNER`), and a note path escaping the repository
  entirely is refused by the transaction layer (`planned write escapes
  repository`). Traversal to outside the repo via the note path is caught by
  `write_target` (`tools/learning_os/store/contracts/write_scopes.py:64-100`),
  which refuses `..`, non-normalized paths and symlinks at every component,
  including the terminal one.
- Symlink and `..` write-target attacks generally (**read**): every
  `TransactionProposal` write passes through `write_target`; terminal
  symlinks are refused even when they resolve back inside the root. Content
  binding (`read_content_bound_file`, `tools/learning_os/app/gateway.py:29-70`)
  reads the approved bytes once and hashes those exact bytes, so there is no
  hash-then-reread TOCTOU window on `--file` inputs of the three
  content-bound capabilities in this batch.
- `module.create` (**read** + the probe above): schema-validated record and
  source map, pinned id regex, pinned `source_map` name, destination check
  (half-defective — finding 1), one transaction/receipt.
- `program.semester.update` (**read**): `semester_plan`
  (`tools/learning_os/derive/semesters.py:153-187`) keeps every existing
  semester row (the old current becomes `previous`; nothing dropped), the
  no-change case refuses, non-semester-bound programs refuse, package bytes
  are content-bound, apply requires snapshot + revisions. Matches WORKFLOWS
  §24 step 5 verbatim.
- `module.sitting.update` (**read**): refuses a missing sitting with the
  known termins listed; writes only `withdrawal_deadline`; snapshot and
  revision guarded.
- `module.materials.compact` / `route.patch` (**read**): compaction refuses
  unless `expand_map(compact)` reproduces the current effective map
  byte-identically ("compaction changed <id>"), apply requires the reviewed
  `plan_sha256`, direct CLI apply is disabled, and the plan hash is computed
  from the exact write set. `route.patch` is outside this batch but shares
  the flow.
- `masters-planning.catalog.update` / `comparison.publish` / `dashboard`
  (**read**): dashboard refuses without the explicit `confirm` gesture;
  comparison and catalog records are schema-pinned (the comparison id
  pattern `^candidate-comparison-…$` also pins the destination filename, so
  no traversal); catalog revision must be exactly current+1; comparisons are
  re-validated against the current catalog on every dashboard open and fail
  closed on a stale catalog (declared fail-closed read behaviour, OPERATOR
  "What 'clean' means").
- `plan.edit-context` (**read**): one-selector exclusivity, `--audit`/`--brief`
  flag pairing, and the batch contract (1–20 distinct routes, resolve-all-
  before-build, atomic refusal) are all enforced as declared
  (`tools/learning_os/app/handlers/materials.py:177-202`).
- `plan.template` (**read**): unknown profiles refuse inside
  `build_plan_template`; the generated record and the whole response are each
  schema-validated before being answered; no repository file is touched.
- Exact replay and stale snapshots (**read**): the transaction layer replays
  by idempotency key and refuses stale `expected_snapshot` /
  `expected_revisions` (revision conflicts fail closed); the declared
  refusal sites of this batch are additionally enforced by the A9
  witness inventory (`tests/test_scenarios_zz_refusal_sites.py`), so
  "declared but never witnessed" found no gap here.

## Reproducing the tests

The two test files are copied into this folder; in the clone they live at
`tests/test_c1a_module_create_legacy_identity.py` and
`tests/test_c1a_attempt_correction.py`, and both are registered in
`tests/group_map.py` under the `studyplan` group (the suite's conftest
refuses to collect unregistered files — that registration is part of the
repro). Run each on its own:

```
.venv/bin/python -m pytest tests/test_c1a_module_create_legacy_identity.py -q
.venv/bin/python -m pytest tests/test_c1a_attempt_correction.py -q
```

Both fail on base `d6c47790`. Nothing was committed; the clone's working
tree carries them uncommitted, exactly as the ground rules require.

## ASSUMPTIONs

- ASSUMPTION: GitHub `origin/main` is the intended base sense of the ground
  rules. The live checkout's local `main` (`1d80aa03`) is a divergent line
  that does not contain `d6c47790`; I cloned the live checkout, then fetched
  the public repo and rebased my branch onto GitHub `main`, which is exactly
  `d6c4779029e366718b71bda158d2aa8f9da1db39`.
- ASSUMPTION: the six-capability read-only verdicts above are as strong as
  stated only for the attack classes listed; I did not probe them
  empirically, and the verification pass should treat them as
  code-reading evidence, not proof.
- The venv was built with `python3.14 -m venv .venv && .venv/bin/pip install
  -e '.[dev]'` exactly as prescribed; `make setup` / `make hooks` were never
  run (verified by omission — nothing else was invoked).

## Not done, on purpose

No pushes, no commits, no CI runs, no issue filing, no fixes, no contract
edits. Verification belongs to the C1 verification pass on GLM-5.3; landing
belongs to Aram or Claude.
