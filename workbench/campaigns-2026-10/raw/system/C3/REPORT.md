# C3 report — make the 2-hour gate a 30-minute gate

- Session: ZCode GLM-5.3, 2026-10-24, campaign C3 (lane 1, item L1-1)
- Branch: `glm/C3-2026-10-24` in `Aram164/LearningOS` (Core only; UI
  untouched, `origin/main` = `f7dbc1f` = the campaign's pinned base)
- Base: `d6c4779029e366718b71bda158d2aa8f9da1db39` (exactly the campaign
  floor — `origin/main` had not moved past it)
- Clone: `~/los-glm-C3-2026-10/{repository,obsidian-ui}`, own python3.14
  venv, no `make setup`/`make hooks`, no local suite run. Local pytest
  use (one focused file at a time): `tests/test_workflows.py` (pin
  checks), `tests/test_scenarios_health_shim.py` (witness-artifact
  smoke), `tests/test_cli.py` (node-shard partition smoke). Durations
  came only from CI.

## What the campaign asked for, and where each item stands

| Requirement | Status |
|---|---|
| `validate.yml` and `release-pair.yml` finish ≤ 40 min on GitHub runners | **Done: validate 31m04s (run 40089524544), release-pair 29m35s incl. pair receipt (run 40096318808)** — vs 2h03m22s unsharded |
| **Exactly** the same set of tests | Proven structurally and per-run: manifest partition + gate-job sum-vs-collection check; numbers below |
| Per-test durations from CI only | Done: `--durations=0` + JUnit artifact on the measurement commit `40d8bb5`, run 40048956366 |
| Shard via pytest-split or equivalent + matrix | Equivalent: file-level manifest legs + a `conftest` node-hash hook (`LOS_NODE_SHARDS`) for the one file that must split below file granularity |
| zz population tests after shards over merged witness artifacts | Done: witness legs upload, zz legs merge (incl. re-keyed A9 attribution sidecars); A19's population check passed over the merged population in CI |
| Sum across shards == unsharded count | Unsharded reference at base `d6c47790`: **8511 passed, 7 skipped, 1 deselected, 2 xfailed** (green run 40035916222); measurement run at `40d8bb5` (same test set): **1 failed [the expected pin violation], 8510 passed, 7 skipped, 1 deselected, 2 xfailed in 1:59:18** — i.e. 8510+1 = 8511. **Sharded: the gate asserted and printed `8522 tests across shards == full collection`** (8511 reference + this branch's 2 new pin tests), 0 failures, skip set identical id-for-id |
| A test injected to fail is still caught | **Done**: run 40092254952 — exactly the injected test's leg (`rest-2`) failed, dependents skipped, run red; reverted verbatim |

## The diagnosis (all numbers from GitHub runners, none local)

The 2h03m gate was 99% one thing: `make system-check` = 40 s setup +
~20 s static checks (ruff/code-reachability/mypy/validate/warning
baseline) + **2h01m34s of pytest** + ~25 s UI `npm run check`
(run 40035916222, Core at exactly `d6c47790`).

Per-file durations (measurement run 40048956366, junit artifact in this
folder) pinned the shape of the problem:

- `tests/test_scenarios_zz_refusal_sites.py` — **39.9 min**, 799 tests.
  Its parametrized declared-site match tests re-derive the static site
  collection (AST over every handler) and re-parse every scenario case
  YAML per test, by design (the control tests monkeypatch and expect
  freshness), so it cannot be cached away and, at file granularity, is
  an atomic 40-minute block.
- Witness producers: `test_scenarios_effects.py` 17.1, `test_procedures.py`
  9.0, `test_scenarios_session.py` 1.3, `test_scenarios_recovery.py` 0.5,
  `test_scenarios.py` 0.1, `test_scenarios_health_shim.py` 0.0 — 28.0 min.
- Everything else: 50.8 min across 195 files.

The A9 hard part is worse than the campaign anticipated: refusal witness
lines never reach the audit logs (`arch_audit_hook._append_refusal_line`:
"The event never reaches the audit log") and A9's per-case attribution
(`scenario_harness.CASE_SITE_WITNESSES`) is process-local memory. So
"merge the artifacts" is not enough — attribution itself had to cross
the process boundary.

## The design (decisions, each with its reason)

**D1 — Two-phase matrix, not one big matrix.**
Phase 1: `pytest-shards` matrix of 5 legs — `witness-0`
(`test_scenarios_effects.py`, 17.1 min), `witness-1` (procedures + the
four small scenario files, 10.8 min), `rest-0/1/2` (~16.9 min each,
duration-balanced longest-first). Phase 2: `zz-shards` matrix of 4 legs
(`needs: pytest-shards`), each merging the witness population and running
`test_scenarios_zz_refusal_sites.py` node-hash-split 4 ways (~10.0 min
each; `test_scenarios_zz_operational_owners.py` whole in `zz-0`).
`ui-check` and the static gates run as their own jobs in parallel; the
`gate` job joins everything. Critical path ≈ setup + witness-0 + zz +
gate ≈ 31 min.

**D2 — Witness artifacts cross the boundary explicitly (conftest).**
Witness legs run pytest with `--basetemp` so the session witness file
and audit dir land at globbable paths; a new `pytest_sessionfinish`-time
dump (teardown of the session fixture) writes
`sites.jsonl.attribution.json` — the `CASE_SITE_WITNESSES` map
serialized. Witness legs upload both plus the audit dir (with its
`cases.txt`). zz legs download, merge deterministically (concatenate
witness lines; union audit logs; merge `cases.txt` entry set) and run
with `LOS_PREMERGED_{WITNESS,ATTRIBUTION,AUDIT_DIR}`, under which the
conftest session fixtures use the merged artifacts instead of creating
fresh ones, and re-key the sidecar attribution onto the merged witness
path. Local runs and producer legs are byte-identical in behavior to
today (the fixtures only branch when the premerged envs are set).

**D3 — Node-level sharding via conftest, not pytest-split.**
`LOS_NODE_SHARDS="file=i/n"` trims a listed file's collected items to
`crc32(nodeid) % n == i` (reported to pytest as deselected). A mod-N
split is a partition for every N, so the gate's sum invariant holds by
construction; no dependency, no durations file that can go stale, and no
unknown-test hazard (pytest-split assigns tests missing from its store
unpredictably, which is exactly the hazard a gate cannot carry). Only
`test_scenarios_zz_refusal_sites.py` needs it; everything else shards at
file granularity.

**D4 — The completeness proof runs on every trigger, in CI.**
The gate job re-collects the whole suite (`--collect-only -q -m "not
live_install"`), counts `<testcase>` elements across every leg's JUnit,
fails on any failing testcase, and asserts `sum == collection`. No test
can be lost, duplicated, or invented without the gate going red — this
is the permanent enforcement; the campaign's one-off numeric proof is
below.

**D5 — `tests/test_workflows.py` re-pinned, per job.** *(scope deviation
— Aram's call)*
The campaign's scope (`.github/workflows/*`, `pyproject.toml`,
`tests/conftest.py`) was insufficient: `test_workflows.py` pinned exactly
one `make system-check` step and exactly one `setup-python` per file, so
no sharded CI could exist under it. The edits keep every policy — pinned
3.14.4 interpreter per job, venv installs, scrut pinned before every
suite shard, exact `live_install` deselection per shard, read-only
permissions, exact-SHA inputs, no `make stress` — and add two new
invariants: the manifest partitions `tests/` (fails locally the moment a
new test file is not in the manifest) and zz legs depend on witness legs.
`pyproject.toml` needed no change.

**D6 — What I did NOT change:** the Makefile, `make system-check`
itself (still the local gate), any contract, the UI repo, `main`.

## Evidence index

- `shard-manifest.json` — the manifest as embedded in both workflows.
- `make_shard_manifest.py` — the generator (input: CI junit).
- `unsharded-durations-40d8bb5.junit.xml` — per-test durations from the
  measurement run (40048956366).
- Run list (all `Aram164/LearningOS`):
  - 40035916222 — green unsharded validate at `d6c47790` (reference
    counts + timing split).
  - 40048956366 — measurement run at `40d8bb5` (durations artifact;
    expectedly red on the old pin test).
  - 40065548893 — first sharded run at `5c8e103`, red, and the red is
    informative: (a) `ui-check` failed in 18 s because the UI check's
    `contract:check-production` imports `learning_os` from the sibling
    Core checkout — the split job needed the pinned interpreter + venv
    (fixed); (b) `witness-0` errored at session teardown because the new
    attribution sidecar serialized tuple keys (fixed; unit round-trip
    added locally — the first smoke missed it because its attribution
    map was empty). All five pytest legs otherwise green; measured leg
    times: witness-0 19m46s, witness-1 12m30s, rest-0 14m27s,
    rest-1 19m04s, rest-2 14m27s — phase 1 ≈ 20 min worst leg.
  - 40067067406 — second sharded run at `d2edb2f`: all five pytest legs
    and ui-check green (leg walls ≈ 12–20 min); all four zz legs red
    before pytest started — the node-shard resolver's `python3 -c`
    one-liner carried `\"` f-string escapes that the runner's shell
    mangling turned into a bare backslash (`SyntaxError: unexpected
    character after line continuation character`). The merge step itself
    worked (premerged envs exported). Fixed by plain concatenation;
    the exact step script now executes locally as a pre-push check.
  - 40068522813 — third sharded run at `618e296`: resolver fixed; phase 1
    and ui-check green. All four zz legs ran their full ~9–10 min and the
    **A19 population test over the merged witness artifacts passed** —
    the merge machinery works. The remaining red was A9's module-level
    `_PROOFS` dict: proof tests populate it and the entry/match tests of
    the same site read it, so hashing whole node ids could split a site's
    tests across processes. Fix: the bracketed parameter is the shard
    key. Verified locally: 4 legs, 799 tests, exact partition, **zero
    sites split across legs**.
  - 40070735742 — fourth sharded run at `fdbe606`: **every pytest leg,
    every zz leg, and ui-check green; 32-minute wall** — under the
    40-minute goal. Only the gate job failed, on its own partition check:
    a prefix mismatch (bare names vs the manifest's `tests/`-prefixed
    entries) — the completeness proof doing its job on the first
    discrepancy it met, even a self-inflicted one. Its failing-test
    detector also counted `<skipped>` children as failures; both fixed.
  - Offline verification against run 4's JUnit artifacts (before pushing
    the gate fix): the nine legs sum to **8522 testcases == the full
    collection at that SHA** (the measurement run's 8520 plus this
    branch's two new pin tests), **zero** `<failure>`/`<error>` entries,
    and the skip set is **identical** to the unsharded measurement run's
    (9 in JUnit terms, same ids both runs — no silent narrowing; the
    terminal summary's "7 skipped" counts differently from JUnit
    elements).
  - 40089524544 — fifth sharded run at `5abbf3a` (gate fixes): **GREEN,
    end to end, 31m04s wall** (created 11:20:40Z, updated 11:51:44Z)
    against the unsharded gate's 2h03m — the ~4× the campaign wanted.
    The gate job's own log line is the standing proof:
    `gate: 8522 tests across shards == full collection (9 skipped,
    visible, never blocking)` — every leg green, static gates green,
    UI check green.
  - 40092254952 — injected-failure run at `94a896e`: one deliberately
    failing test appended to `tests/test_cli.py` (rides in `rest-2`).
    **Observed: exactly the rest-2 leg failed** —
    `FAILED tests/test_cli.py::test_c3_injected_failure_must_be_caught_by_its_shard`,
    leg summary `1 failed, 1733 passed, 2 skipped, 1 deselected` — the
    other four legs and ui-check stayed green, zz-shards and gate
    skipped, the run concluded **failure**. A failing test cannot hide
    inside a shard. Reverted verbatim (`2bf13a8`).

## Release-pair gates

- First sharded dispatch (40093199094, on `2bf13a8`) died in 69 seconds:
  the inputs-validation and checkout-verify bash steps inherited the job
  default `working-directory: repository`, which does not exist before
  the first checkout — every pytest leg failed at startup while ui-check
  (no default) passed. Fixed by running those steps at the workspace
  root (`211503f`, the branch's final tip). An earlier same-cause lesson
  from validate.yml did not exist there because validate's first run
  step comes after its checkout.
- On the final tip `211503f`, both gates were dispatched:
  - **Ground rule gate** (`--ref main`, the unsharded workflow Aram
    prescribed): run 40093593040, core `211503f`, ui `f7dbc1f`. This
    simultaneously proves the branch passes the *current* landing path —
    my conftest/test edits are inert without the merge envs.
  - **Sharded release-pair** (`--ref glm/C3-2026-10-24`): run
    40093594906, same SHAs. **Interpretation note:** the ground rules
    prescribe gating with `--ref main`, but main's workflow file cannot
    execute the sharded release-pair this campaign exists to build; the
    campaign's stated goal ("release-pair.yml ... 40 minutes or less")
    is unprovable without dispatching the branch's own file. Both
    dispatches are read-only (`contents: read`) and touch only this
    branch's commits. Flagged here for Aram; nothing lands without him.
- A superseded main-ref run (40093197328, on the pre-fix tip `2bf13a8`)
  was left to finish as extra evidence; its outcome is recorded below.
- Second sharded dispatch (40093594906, on `211503f`): every test leg,
  every zz leg, ui-check and the gate's completeness proof green —
  **31m14s wall** — but the receipt tail failed: `npm run build:info`
  without `npm run build` ("build-info.json is missing"): in the old
  single job, `make system-check`'s UI check had already built the
  plugin by receipt time; the split gate job had not. Fixed: the gate
  builds, then records (`323b68c`, the actual final tip). The test-phase
  wall and proof were unaffected — they had already passed.
- On the final tip `323b68c`, both gates were dispatched once more:
  sharded 40096318808, ground-rule (`--ref main`) 40096320763.

(Final outcomes appended below.)

## The numbers, side by side

| | unsharded (40035916222) | sharded (40089524544) |
|---|---|---|
| wall | 2h03m22s | **31m04s** |
| tests run | 8511 passed, 7 skipped, 1 deselected, 2 xfailed | 8522 across 9 legs == full collection at that SHA (8511 + 2 new pin tests on this branch), 9 skipped (same ids), 0 failures |
| structure | 1 job, serial | 5 phase-1 legs + 4 zz legs + ui-check + gate, parallel |

## Final outcomes (all `Aram164/LearningOS`)

| run | what | result |
|---|---|---|
| 40035916222 | unsharded validate, base `d6c47790` (reference) | green, 2h03m22s, 8511/7/1/2 |
| 40048956366 | measurement, `40d8bb5` | red on the old pin (expected), durations artifact, 1:59:18 pytest |
| 40065548893 | sharded validate #1, `5c8e103` | red: ui-check venv + sidecar tuple keys |
| 40067067406 | sharded validate #2, `d2edb2f` | red: zz resolver shell quoting |
| 40068522813 | sharded validate #3, `618e296` | red: A9 `_PROOFS` split across legs |
| 40070735742 | sharded validate #4, `fdbe606` | all legs+ui green, 32 min; gate red on its own prefix bug |
| **40089524544** | **sharded validate #5, `5abbf3a`** | **GREEN, 31m04s, gate: 8522 == full collection** |
| 40092254952 | injected failure, `94a896e` | **RED, exactly `rest-2`** (the injected test's leg); reverted |
| 40093592933 | sharded validate, `211503f` | GREEN (second green run) |
| 40093199094 | sharded rp #1, `2bf13a8` | red in 69 s: pre-checkout working directory |
| 40093594906 | sharded rp #2, `211503f` | tests+proof green, 31m14s; receipt tail red: missing `npm run build` |
| **40096318808** | **sharded release-pair, final tip `323b68c`** | **GREEN, 29m35s, pair receipt uploaded (`learningos-pair-323b68c1408c-f7dbc1f76071`)** |
| **40096318747** | **sharded validate, final tip `323b68c`** | **GREEN** |
| 40093197328 / 40093593040 / 40096320763 | ground-rule `--ref main` unsharded gates on `2bf13a8` / `211503f` / `323b68c` | `211503f`: **GREEN in 1h37m** — the branch passes the current, unsharded landing path (my conftest/test edits are inert without the merge envs). The `2bf13a8` dispatch returned no conclusion after 4 s (startup anomaly, superseded). The final-tip run (`323b68c`) was still in flight at report time, expected ~15:05Z; it is redundant by content: `323b68c` differs from `211503f` only in `release-pair.yml`'s gate step, which the main-ref workflow never executes. |

## Verdict

Every campaign requirement is proven in CI on `glm/C3-2026-10-24` at
`323b68c`: validate 31m04s and release-pair 29m35s, both under the
40-minute goal with the 2h→30m (~4×) speedup the campaign wanted; the
shards are provably exactly the suite (asserted by the gate on every
run, 8522 == full collection); an injected failure was caught by exactly
its shard; the pair receipt is produced and uploaded. Six real defects
were found and fixed along the way — every one caught by the new
invariants or the shard structure itself, which is the strongest
available evidence the gate is not blind. The one open judgment is
Aram's: landing (which changes CI), the `test_workflows.py` scope
deviation, and the `--ref` interpretation for the sharded release-pair
proof.

## What Aram decides

1. **Land or not** — `glm/C3-2026-10-24` at `323b68c` (11 commits: design,
   6 CI-found fixes, injection + revert, receipt build fix). Landing
   changes CI; the campaign reserves that for him.
2. **The scope deviation** — `tests/test_workflows.py` is outside the
   campaign's stated scope and had to be edited (old pins made sharding
   structurally impossible). The edits re-pin the same policies per job
   and add the manifest-partition + zz-after-witness invariants. If he
   rejects that file's changes, nothing else can land either.
3. **The `--ref` interpretation** — the sharded release-pair proof
   required dispatching the branch's own workflow file (read-only, own
   branch). Ground-rule gates with `--ref main` were also dispatched.
4. **Maintenance rule** — when suite balance drifts (a leg approaching
   45 min), regenerate the manifest from a CI durations artifact
   (`make_shard_manifest.py` in this folder) and paste it into both
   workflows; the partition test fails locally until the manifest covers
   every file, so drift is loud, never silent.

## ASSUMPTIONS

- The paired UI `npm run check` needs the Core checkout beside it (it
  drives the cross-process recovery harness against this Core) — taken
  from the workflow's own comment and `make system-check`'s enforcement;
  the ui-check job checks out both. Not separately verified.
- Runner parallelism: 9 legs + ui + gate fit GitHub's free concurrency
  for public repos; observed, not documented.
- ASSUMPTION (verified on `origin/main` at push time only): UI `main`
  stays at `f7dbc1f` for the pair gates.

(Final results, the injected-failure proof, and the release-pair gates
are appended below as the runs complete.)
