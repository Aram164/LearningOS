# Claude's verdict on C3, CI sharding (L1-1, 2026-10-24, overnight orchestrator)

**Verdict: the goal is met, and the CI claims hold on GitHub.** There is
one latent design gap in how witness producers are classified (below).
Landing is Aram's call.

The branch is `glm/C3-2026-10-24` at `323b68c`. It changes four files:
`.github/workflows/validate.yml`, `.github/workflows/release-pair.yml`,
`tests/conftest.py` and `tests/test_workflows.py`. No contract, Makefile or
`pyproject.toml` change.

C3 never sent its finish signal. It errored three times on GLM-5.3 capacity,
then finished its report at 16:19. Per the brief, that counts as done.

## Checked on GitHub, not taken from the report

**Wall times** (createdAt to updatedAt):

| run | result | wall |
|---|---|---|
| unsharded `validate` 40035916222 on `d6c47790` | success | 2h03m |
| sharded `validate` 40089524544 on `5abbf3a` | success | 31m04s |
| sharded `validate` 40096318747 on the final tip | success | 33m09s |
| sharded `release-pair` 40096318808 on the final tip | success | 29m35s |

All are under the 40-minute goal.

**Exactly the same tests.** Per-leg pytest summaries from 40096318747's log,
summed across the 9 legs:
- **passed:** 1151 + 73 + 1733 + 3044 + 1692 + 201 + 199 + 189 + 231 = **8513**;
- **skipped:** 2 + 4 + 1 = **7**;
- **xfailed:** **2**;
- **deselected:** **1** (`live_install`, in rest-2).

The unsharded reference is 8511/7/1/2, and the branch adds exactly two
tests: `test_shard_manifest_partitions_the_suite` and
`test_zz_legs_run_after_the_witness_legs` (the other two diffs in
`test_workflows.py` are renames). So 8513 = 8511 + 2.

The zz legs' other deselections are the hash split, which is an exact
partition of the 799-test file: 179 + 199 + 232 + 189 = 799.

The gate job's log line reads: `gate: 8522 tests across shards == full
collection (9 skipped, visible, never blocking)`. 8522 counts JUnit test
cases: 8513 + 7 + 2, with xfailed counted as skipped, which makes the "9
skipped".

**An injected failure is caught.** In run 40092254952 (conclusion failure),
only `pytest-shards (rest-2)` failed, and `zz-shards` and `gate` were
skipped. The injection was reverted in `2bf13a8`.

**The current landing path also passes.** The `--ref main` unsharded
release-pair 40093593040 on `211503f` succeeded (1h37m). The final tip
`323b68c` differs from `211503f` only in 4 lines of `release-pair.yml`,
which the main-ref workflow never runs. Its own main-ref run, 40096320763,
was still in progress at 16:37 and is redundant by content.

## A9/A19: do the population tests still see the whole population?

**Yes, today.** The zz legs merge the witness file and audit dir only from
the `witness-*` legs:
- `witness-0` is `test_scenarios_effects.py`;
- `witness-1` is `test_procedures.py`, `test_scenarios.py`,
  `test_scenarios_health_shim.py`, `test_scenarios_recovery.py` and
  `test_scenarios_session.py`.

Every leg gets an `autouse` session witness file and audit dir
(`tests/conftest.py:68-100` at base). So I checked whether any rest-leg file
also writes to them:

- **Measured.** I ran each file alone at base `d6c47790`, with
  `--basetemp`, then counted lines in the session `sites.jsonl` and files in
  the audit dir. `test_arch_callbacks.py`, `test_ops_pipeline.py`,
  `test_material_observation_port.py`, `test_arch_writes.py` and
  `test_lineage_writer_interpositions.py` all wrote **0 witness lines and
  0 audit files**. These are the rest-leg files that install the hook or
  use the scenario harness or `arch_site`.
- **Read, not measured** (the run was stopped at hand-off).
  `test_arch_output.py:149-171` and `test_arch_suggestions.py:52-55`
  redirect `LOS_SITE_WITNESS_FILE` to their own file, so they cannot write to
  the session file.
- ASSUMPTION: no other rest-leg file installs the hook. I enumerated the
  importers of `arch_audit_hook` and the users of `arch_site` by grep. One
  remaining hit, `tools/learning_os/app/render.py`, was not inspected.

The A19 population file (`test_scenarios_zz_operational_owners.py`, in zz-0)
and all four A9 legs were green over the merged population.

**The gap, certainly real but latent:** which legs count as witness
producers is set by hand in the manifest. C3's partition test proves that
every *file* is in some leg. It does not prove that every file *writing
witness lines* is in a witness leg. A future rest-leg test that writes to the
session witness file would drop out of the population silently. The zz
tests would then pass over a narrowed population, which is the masking
failure this campaign had to avoid.

**Cheap fix, recommended before or with landing:**
- Upload the witness and audit artifacts from *every* phase-1 leg, and let
  the zz merge take all of them (`pattern: witness-*` already globs).
- Or assert in each rest leg's session teardown that its session witness
  file and audit dir are empty.

## Judgments

- **Certainly fine.** The shard design: a two-phase matrix, a crc32
  partition over parametrized ids, and a gate that re-collects and compares
  on every run. That gate is the right permanent guard.
- **Aram's call: the `tests/test_workflows.py` scope deviation.** It was
  necessary: the old pins required exactly one `make system-check` job.
  The new pins keep the same policies per job.
- **Aram's call: dispatching the branch's own `release-pair.yml`
  (`--ref glm/C3-2026-10-24`).** It was the only way to prove the sharded
  release-pair's time. It is read-only and touched only this branch.
- **A dislike, not a defect.** `SHARD_MANIFEST` is pasted into both
  workflows, so two copies can drift. A single file read by both would
  avoid that.

## For Aram

**Land or not.** It changes CI for every future landing, from about 2 h to
about 30 min.

**If yes:**
1. Close the witness-producer gap above first, or in the same change.
2. Accept the `test_workflows.py` edits.
3. Landing belongs to the landing session or to you; the orchestrator does
   not land.

## Addendum (conductor 2, 19:12): the final unsharded gate is green

- **The run:** release-pair 40096320763 (`--ref main`) on Core `323b68c`
  with UI `f7dbc1f`.
- **Result:** success, 13:00Z to 15:04Z. `8513 passed, 7 skipped,
  1 deselected, 2 xfailed in 7305.87s (2:01:45)`, then
  `{"ok": true, "action": "verify", ...}`.
- **What it confirms:** the unsharded suite on the branch tip matches the
  sum of the sharded legs exactly (8513/7/1/2). The sharded gate ran in
  about 30 min, against 2 h 2 min for this run.

## C3-F verdict (conductor 2, Sun 2026-10-25 02:30): the witness gap is closed

Report: `C3/FOLLOWUP.md` (L1-8). I checked its claims on GitHub.

**Holds.**
- **The final tip `f56a7b3` is green.** Sharded validate 40130556604 and
  the branch's sharded release-pair 40130583202 are both success (33 min
  and 30 min). Every zz leg logs `merged 5 suite legs: 859 witness lines,
  1163 audit logs`.
- **The injection proof is real.** Run 40128082544 (`101f407`) failed in
  the zz legs, quoting the marker `c3f.injected.rest-leg-marker` verbatim. A
  rest-leg witness line now reaches the merged population.
- **C3-F also found and fixed a real pre-C3-F defect.** The old merge
  counted every witness line twice, because pytest's `<name>current`
  aliases were uploaded as copies. Every consumer deduplicated, so it was
  invisible. The merge now collapses byte-identical copies and fails on
  anything that differs.
- **The gap was already live.** One rest-1 line (`unit.note.append`) never
  reached the old population.

**My landing decision:** the two deliberate inject/revert pairs (`94a896e`
/`2bf13a8` from C3, `101f407`/`c712db2` from C3-F) stay off `main`.
- Each pair nets to nothing.
- A deliberately failing commit on `main` is bisect noise.
- The proofs live in these reports and on `glm/C3-2026-10-24`.
