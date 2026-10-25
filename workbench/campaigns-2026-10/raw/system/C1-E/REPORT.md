# C1-E report — operations bug hunt (Flash, 2026-10-24)

**Item:** L2-6. **Batch:** C1-E — capabilities starting `lineage`, `legacy`,
`backup`, `coordination`, `workspace`, `project`, `goal`, `runtime`,
`health`, `operator` (15 of the 75 in `system/contracts/capabilities.yaml`:
queries `runtime.session`, `operator.bootstrap`, `project.list`,
`project.inspect`, `health.report`, `backup.manifest`,
`legacy.archive.inspect`, `legacy.archive.status`; commands `lineage.restamp`,
`legacy.archive.lock.publish`, `coordination.section.revise`,
`workspace.next-action.update`, `project.create`, `project.update`;
internal `goal.decision.record`).

**Base:** `origin/main` = `d6c4779029e366718b71bda158d2aa8f9da1db39` (clone
`~/los-glm-C1-E-2026-10/repository`, from GitHub, branch
`glm/C1-E-2026-10-24`, own python3.14 venv). **Nothing committed, nothing
pushed.** The two finding tests sit uncommitted in the clone's `tests/`
(registered in `tests/group_map.py`, group `gateway`); the workbench copies
are the durable ones.

## Findings (2, both with failing pytest on base `d6c47790`)

### 1. backup.manifest — a symlinked subtree inside a declared tree leaves the inventory without a trace

`C1-E/backup.manifest/symlinked-subtree-silent-omit/` (finding.md + test).

`backup.manifest` answers for exactly the producer-declared roots, and the
module's own #25 principle is that declared content must never silently
disappear from the inventory. The declared-*tree*-symlink case refuses
(`_inside`) and the one known symlink farm is recorded as data
(`materials_aliases`, #31), but a symlinked *subdirectory* inside a
declared tree is neither followed, refused, nor recorded:
`_admitted_paths`' `os.walk` does not descend it and `_admit_file` refuses
symlinked files, so `backup-manifest` exits 0 with a schema-valid, green
manifest in which the whole subtree is missing — and the restore verifier
shares the same walk, so nothing downstream catches it either. Test: the
manifest completes with 222 entries and no mention of
`records/archive/**`. Reachability is latent today: the live materials
tree has zero symlinks outside `.flat` (read-only listing, this session),
and the live core trees were not audited for symlinks — ASSUMPTION. It
becomes live the day a subtree moves behind a link (the classic
external-disk move), which is precisely the disaster-recovery scenario
this query exists for. Fix-agnostic: refuse, cover, or record the skipped
subtree.

### 2. coordination.section.revise — one section's edit re-flows every other section's lines

`C1-E/coordination.section.revise/whole-document-reflow/` (finding.md +
test). Minor.

The contract says "frontmatter and other section content are preserved",
but `replace_h2_section` routes the WHOLE document through
`render.serialise`, which forces one blank line after every heading and
trims every section's edges — an unrelated Commitments edit rewrites the
hand-authored Priorities section (`['(none)', '']` → `['', '(none)', '']`)
silently. The existing coordination test compares other sections with
`.strip()` and cannot see it; the same re-serialisation runs for
`workspace.next-action.update` ("only the Next Action section content
changes"). Test asserts the other sections' parsed lines are untouched;
fix-agnostic for either a splice-based editor or a preserving serialiser.

Both tests are fix-agnostic per the C1-C convention, run standalone
(1 failed in 0.77s / 0.27s), and pass on refusal-shaped or
preservation-shaped fixes.

## Attacked and held (dead leads — do not re-hunt)

- **V2 admission and the snapshot guard.** `run_gateway` unconditionally
  compares `envelope["expected_snapshot"]` against the live fingerprint
  before dispatch (`app/pipeline.py:1069-1090`), under the operator lock
  held from replay lookup through dispatch+commit
  (`pipeline.py:958-1106`) — plan and commit cannot drift apart within
  one apply.
- **project.create/update revision semantics.** The engine forces
  gateway applies to carry `expected_revisions` covering exactly every
  transaction artifact (`store/transactions.py:1622-1632`), and the
  artifact revision moves whenever the project file does, so a stale
  payload cannot land without a stale revision number refusing first.
  The record's own `revision` field (project.schema.json, default 0) is
  caller-managed data — no code bumps it (grepped the handlers) — so
  there is no field-level guard to violate. The plan-time
  `target.is_file()` check is race-free because plan+commit share the
  lock.
- **coordination/workspace section ambiguity and fenced headings.** The
  fence-blind shared reader `md_section`
  (`domain/markdown.py:8-21`) versus the fence-aware writer is already
  PINNED as accepted read behavior
  (`tests/test_workspace_next_action.py:49-60` calls it "pre-existing
  read behavior") — not fileable. Duplicate real `## Next Action`
  sections: writer and reader both take the first match, so the pair
  stays consistent; the workspace invariant does not declare the
  ambiguity refusal coordination declares. Injected headings into
  coordination refuse (`parse_sections(req["text"])` check,
  `admin.py:300-310`).
- **goal.decision.record.** Batch apply binds `reviewed_sha256` over the
  exact pre-write ledger bytes + goal ids + decision
  (`handlers/goals.py:289-298, 380-387`); malformed ledgers refuse
  before anything is written; audit authorization freezes the complete
  eligible pool and refuses redraw; audit closure re-verifies the
  report digest and lineage history. The audit file is read from an
  arbitrary caller-supplied path, but that is a direct-user-gesture
  internal command reading the reviewer's own file — no boundary
  crossed.
- **legacy.archive.inspect / status / lock.publish.** `_exact_file`
  refuses every symlink component along both allowlisted sources and
  canonical targets (`store/legacy_archive.py:43-61`); the lock schema
  enforces `excluded: {count, status}` with `additionalProperties:
  false`, so boundary paths/hashes cannot ride into the published lock;
  publish is content-bound under V2 (`_CONTENT_BOUND_V2`,
  `app/gateway.py:141-150`), requires explicit approval, and reuses the
  public reader's schema validation.
- **runtime.session.** Sticky repair demands both `--previous-json` and
  `--event`, validates the previous packet against the schema AND its
  `snapshot_id` against the *current* snapshot
  (`handlers/reads.py:1186-1196`), and re-checks the snapshot after the
  read (double-snapshot guard, reads.py:1203-1207).
- **operator.bootstrap compact/brief.** Continuation is snapshot-bound:
  `window_values` refuses any nonzero offset without
  `--expected-snapshot` (`handlers/_shared.py:126-133`), and both
  bootstrap modes re-verify the snapshot after building the page.
- **lineage.restamp.** Apply re-runs `analyze()` fresh and re-verifies
  every listed claim stampable (`_verify_named`, ELIGIBLE-only);
  `claims_list_sha256` sorts and refuses duplicates; the envelope
  snapshot guard makes check→apply plan drift impossible; withdrawn/
  contested/already-narrowed claims fall outside `rows` and refuse.
- **backup.manifest `--out` guard.** Compares the *resolved* target
  against *resolved* authorities (`backup_authorities` resolves all
  three), so symlinked writes into a backed-up root are caught; declared
  files that are symlinks refuse in `_inside`; `excluded_names` pruning
  is contract-declared, not silent.
- **health.report.** Every check carries an owner and a remedy
  (`derive/health.py:487+`), failures degrade to per-check
  error/warning rows rather than dropping the report — the invariant
  holds as declared.

## Residual surface (not fully audited this session — for the verification pass)

- `derive/semantics/restamp.py` internals: `_analyze_claim` and
  `_attribute_bundled_window` (the git-archaeology eligibility engine,
  ~450 lines) were audited at their entry points and guard structure
  only; `restamp_claim`'s field-preservation ("evidence, judge,
  admission, status and review state pass through untouched") was not
  line-audited. ASSUMPTION: the #94 machinery is correct as shipped.
- `runtime.session` proposal logic `compile_session`/`replan_session`
  (the derive-side session planner) — the handler shell is tight; the
  planner internals were not audited.
- `build_health_report`'s later checks (master-catalog leak scan,
  projection check, UI plugin check) were read only down to the
  legacy-archive check.
- `project.inspect` batch mode (`_inspect_batch`, up to 20 ids) was not
  exercised.

## Environment notes for the verification pass

- Re-register the workbench test copies in a clone's `tests/group_map.py`
  (group `gateway`) or conftest collection errors out; imports are flat
  (`gateway_helpers`, `repo_builders`, `conftest` from `tests/`).
- Finding 1's test builds the default UI authority at
  `<repo-parent>/obsidian-ui` (4 plugin files + `plugin-assets.json`) so
  the plain command runs without `--ui-root`; the symlink points outside
  the repository (into `<repo-parent>/outside-stash/`), modeling the
  external-disk move.
- Finding 2's test reshapes the fixture `work/COORDINATION.md`
  (`## Priorities` with no following blank line) before applying through
  `approved_v2_envelope`; staged validation accepts both the reshaped
  input and the re-flowed output, which is why the drift lands silently.

Stop here per the campaign: fixes, issues and landing belong to Aram/Claude.
