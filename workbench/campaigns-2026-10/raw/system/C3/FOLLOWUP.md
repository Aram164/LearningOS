# C3-F follow-up report — closing the witness-producer gap

- Session: ZCode GLM-5.3, 2026-10-24, campaign C3-F (lane 1, item L1-8)
- Branch: `glm/C3-2026-10-24` in `Aram164/LearningOS`, from the C3 tip
  `323b68c` to the final tip `f56a7b3` (five commits: the change, a
  CI-found fix, the injection, its revert, a comment correction)
- Clone: the existing `~/los-glm-C3-2026-10` (own venv); no local suite
  run — local pytest use was `tests/test_workflows.py`,
  `tests/test_release_pair_receipt.py`, one smoke file, and the injected
  test alone, one process at a time
- Read first (done): `C3/REPORT.md`, `C3/CLAUDE-VERDICT.md`

## What the block asked, and where each item stands

| Requirement | Status |
|---|---|
| Every phase-1 leg uploads its witness and audit artifacts; zz merge takes all; the hand-kept producer list goes | **Done**: upload runs on every suite leg (`if: always()`, no shard-name condition); the zz merge takes every `population-*` artifact and asserts the artifact set equals the manifest's suite legs; `WITNESS_BLOCK` (the hand list) is deleted from `tests/test_workflows.py` |
| One manifest file, read by both workflows | **Done**: `.github/shard-manifest.json` (extracted byte-for-byte from the pasted copies, which were verified identical before extraction); both workflows' pick/resolver/gate steps read it; a new pin forbids `SHARD_MANIFEST` from reappearing |
| Proof 1: sharded `validate` and the branch's own sharded `release-pair` green on the new SHA | **Done** on the final tip `f56a7b3` (runs appended at the bottom); also green one tip earlier on `f7836f0` (run 40121362655) |
| Proof 2: the legs still sum to the unsharded count in `C3/REPORT.md` | **Done**: 8514 passed = 8511 (unsharded base) + 2 (C3's pin tests) + 1 (C3-F's net: −1 removed, +2 added); gate asserted `8523 tests across shards == full collection`; skip and xfail sets identical (7 / 2), `live_install` deselected exactly once |
| Proof 3: a temporary commit makes one rest-leg test write a witness line, the line appears in the merged zz population, then revert; name the run | **Done**: run **40128082544** (run #36, commit `101f407`, reverted as `c712db2`) — details below |

## What changed (five files, no contracts, no Makefile, no `pyproject.toml`)

- **`.github/shard-manifest.json`** (new) — the single manifest: the
  exact JSON that was pasted into both workflows, plus nothing else.
- **`.github/workflows/validate.yml`** and **`release-pair.yml`** — the
  ~245-line pasted `SHARD_MANIFEST` env block deleted from each; the
  pick, node-shard-resolver and gate-proof steps load the file; every
  suite leg uploads `population-<leg>` (witness file, attribution
  sidecar, audit dir); the zz legs download `population-*`, merge all of
  them, and assert completeness; headers re-commented.
- **`tests/conftest.py`** — the session audit-dir fixture touches
  `cases.txt` at creation, so every leg's artifact is the full triple
  (an empty directory would not survive an artifact upload, and a leg
  that produced nothing must still be *present* in the merge).
- **`tests/test_workflows.py`** — `WITNESS_BLOCK` and its
  witness-legs-only constraint deleted; the partition test reads the
  manifest file once; new pins: both workflows read the one file (and
  never mention `SHARD_MANIFEST`), each workflow's two matrices equal
  the manifest's legs, the population upload is unconditional + globs
  the session fixtures' own locations + declares
  `follow-symbolic-links: false`, the zz job downloads `population-*`
  and depends on the suite job.

## The design decisions, each with its reason

The block pre-decided the two headline choices (upload from every leg;
one manifest file). The decisions below are mine.

1. **Upload globs name the session fixtures' own basetemp locations**
   (`pytesttmp/site-witness*/…`, `pytesttmp/operational-audit*`), not a
   broad `pytesttmp/**` sweep. Reason: `tests/test_ops_pipeline.py`
   (eight sites) and `tests/test_material_slices.py` create *private*
   witness files named exactly `sites.jsonl` under their per-test tmp
   dirs — in rest legs. A broad glob would have swept those into the
   population once rest legs upload. The pin test holds this narrow
   shape.
2. **The merge collapses byte-identical copies per artifact and fails
   on anything that differs** (see the defect below). Reason: pytest
   leaves `<name>current` symlinks beside every session dir and the
   upload materializes them as real duplicate files; identical copies
   must merge as one, while a genuinely different second file (a
   private witness file) must stay a loud failure.
3. **The merge asserts the downloaded artifact set equals the
   manifest's suite legs** (every leg except this job's `zz-*`). Reason:
   without it, a download-pattern drift would merge 4 of 5 legs and the
   missing leg's witnesses would be lost silently — the exact failure
   mode this campaign exists to make impossible.
4. **`cases.txt` is touched by the fixture.** Reason: it makes every
   leg's artifact structurally the full triple, which is what makes
   decision 3's per-leg assertion meaningful, and the A19 merge already
   unions `cases.txt` entry sets, so empty entries are free.
5. **Artifacts are named `population-<leg>`** (parallel to
   `junit-<leg>`). Reason: the artifact is "this leg's contribution to
   the witness population"; keeping the old `witness-` prefix for rest
   legs would have read as the old producer classification.
6. **The `WITNESS_BLOCK` constraint is removed entirely, not
   weakened.** Reason: with every leg uploaded and merged, a
   witness-writing file is asserted over wherever it runs — the
   classification cannot be violated, only maintained pointlessly. A zz
   population file moved into a suite leg would fail loudly on its own
   (it would read that leg's session witness file, not the merged one,
   and find almost every site unwitnessed), so no pin is needed there.

## The seventh CI-found defect: the population was merged twice

Run 40120145283 (run #34, on the first C3-F commit `763cead`) went red
in every zz leg exactly as the new invariant intended:

```
AssertionError: population artifact of leg 'rest-0' must hold exactly
one witness file, one attribution sidecar and one audit dir; found 2/2/2
```

Diagnosis from the *previous* C3 runs' own artifacts (this defect
predates C3-F): pytest leaves a `<name>current` symlink beside each
session dir; upload-artifact follows it; the artifact therefore contains
everything twice (`site-witness0/` and `site-witnesscurrent/`,
byte-identical — verified by downloading `witness-witness-0` from green
run 40096318747: two 105716-byte `sites.jsonl`, two identical audit
dirs). C3's merge then printed, unnoticed:

```
merged 4 witness legs: 1716 witness lines, 1163 audit logs
```

— "4 witness legs" for two legs, 1716 lines for 858. Every downstream
consumer (A9's `(operation, site)` sets, A19's case-set checks, the
attribution sets) deduplicates, so the doubled population was invisible
to every assertion. The fix (`f7836f0`) has two halves:
`follow-symbolic-links: false` on the upload, and byte-identical
collapse in the merge. **The flag is empirically inert** — run
40121362655's artifacts still contain the `*current` copies — so the
merge dedupe is the load-bearing half; the final tip's commit
(`f56a7b3`) states this in the comment and the pin so nobody later
removes the dedupe as "redundant given the flag".

Local verification before pushing (one process at a time): the exact
merge script extracted from the YAML and executed in six scenarios —
happy path, duplicate-alias path, the real downloaded CI artifact as one
leg's contribution (815 lines merged exactly once), a missing leg
(loud), a differing stray `sites.jsonl` (loud), a bogus shard id (loud)
— plus the pick and resolver scripts for all nine legs, the 20 workflow
pins, the 31 receipt pins, and ruff.

## The gap was already live, not merely latent

Run 40121362655's per-leg artifacts answer the 858-vs-859 question:
`rest-1` contributed **one real witness line** —

```json
{"operation": "unit.note.append", "kind": "direct-refused", "site": null, "code": 3}
```

— writer: the transaction tests (`tests/test_transactions.py` rides
rest-1; see ASSUMPTIONS). Under C3's design this line never reached the
zz merge. It is null-site, so A9's site population happened to be
unaffected — the mechanism, however, was live: a rest-leg test already
writes witness lines, and the old merge dropped them. The new merge line
count exposed it: `merged 5 suite legs: 859 witness lines` where C3's
runs had 858 unique.

## Proof 3 in detail — the injection run

Commit `101f407` appended one test to `tests/test_cli.py` (rides
rest-2) that appends a marker line to the session witness file through
`LOS_SITE_WITNESS_FILE` — the exact shape of the gap: a rest-leg test
writing a witness line.

Run **40128082544** (run #36, 20:03–20:26Z):

- all five phase-1 legs green (the injected test itself passed; the
  marker rode rest-2's population artifact),
- the merge in every zz leg reported `merged 5 suite legs: 860 witness
  lines` — 859 + the marker: **the rest-leg line is in the merged
  population**,
- all four zz legs went red over it — 497 failures — each quoting the
  marker verbatim:

```
AssertionError: A9 witness line 2 is not an item 8.1 refusal line
('{"operation": "c3f.injected", "site": "c3f.injected.rest-leg-marker"}')
```

  ("line 2": line 1 is rest-1's pre-existing `unit.note.append` line —
  sorted leg order puts rest-1's lines before rest-2's),
- `gate` skipped, run conclusion failure. Under the old design this
  line would have vanished and every zz leg would have stayed green —
  the masking failure. Reverted verbatim as `c712db2`.

Under the old design the same commit would have produced a fully green
run; that contrast is the proof that the gap is closed.

## The numbers (run 40121362655, `f7836f0`)

| leg | result |
|---|---|
| rest-0 | 3045 passed |
| rest-1 | 1692 passed, 4 skipped |
| rest-2 | 1733 passed, 2 skipped, 1 deselected |
| witness-0 | 1151 passed |
| witness-1 | 73 passed, 2 xfailed |
| zz-0 / zz-1 / zz-2 / zz-3 | 201 / 199 / 231 / 189 passed |
| **sum** | **8514 passed, 7 skipped, 2 xfailed, 1 deselected** |

8514 = 8511 (unsharded reference at `d6c47790`, `C3/REPORT.md`) + 2
(C3's added pin tests) + 1 (C3-F net: `test_zz_legs_run_after_the_
witness_legs` removed; `test_both_workflows_read_the_one_shard_manifest`
and `test_workflow_matrices_and_population_flow_match_the_manifest`
added). The gate's own line: `gate: 8523 tests across shards == full
collection (9 skipped, visible, never blocking)` — 8514+7+2 in JUnit
terms. The skip set is id-for-id the unsharded run's; `live_install` is
deselected exactly once (rest-2). Wall 32m43s, under the 40-minute goal.

## Run list (all `Aram164/LearningOS`)

| run | commit | what | result |
|---|---|---|---|
| 40120145283 (#34) | `763cead` | first C3-F validate | **red by design**: merge rejected `2/2/2` per artifact in all zz legs — the invariant catching the alias duplication; all 5 phase-1 legs + ui-check green (every-leg upload worked from the start) |
| 40121362655 (#35) | `f7836f0` | dedupe-fix validate | **GREEN, 32m43s**, gate 8523, merged 5 legs / 859 lines / 1163 logs |
| **40128082544 (#36)** | `101f407` | **injection proof** | **red by design: all 4 zz legs fail quoting the marker; merge shows 860 lines; phase 1 all green**; reverted as `c712db2` |
| 40130010634 | `c712db2` | validate, post-revert tip | **GREEN, 30m51s** (20:29:32–21:00:23Z) |
| 40130147619 | `c712db2` | sharded release-pair, post-revert tip | **GREEN, 31m19s** (20:31:16–21:02:35Z) |
| **40130556604** | `f56a7b3` | **validate, final tip** | **GREEN, 33m04s** (20:36:44–21:09:48Z): gate `8523 tests across shards == full collection`, merge `5 suite legs: 859 witness lines, 1163 audit logs` |
| **40130583202** | `f56a7b3` | **sharded release-pair, final tip** | **GREEN, 30m22s** (20:37:05–21:07:27Z): same gate and merge lines; pair receipt uploaded as `learningos-pair-f56a7b33974f-f7dbc1f76071`; all five `population-*` artifacts present beside the nine `junit-*` |

The `c712db2` and `f56a7b3` trees differ only in the two workflow
comments and the pin message (verified: `git diff c712db2 f56a7b3` is
those three hunks), so the `c712db2` pair are corroborating runs for the
`f56a7b3` pair.

## What Aram decides

1. **Land or not** — `glm/C3-2026-10-24` at `f56a7b3`: C3's 11 commits
   plus C3-F's five. Landing is still his call; nothing has landed.
2. **The alias-duplication fix rides along** — it is a real defect fix
   found by the new invariant (the pre-C3-F merge doubled the
   population), but it is also a change in merged-population *content*
   that only this branch's runs have exercised.
3. **Maintenance** — manifest regeneration now means writing
   `.github/shard-manifest.json` (the workbench
   `make_shard_manifest.py` output format is unchanged); the partition
   pin fails locally the moment a new test file is not covered, and the
   gate fails in CI the moment the manifest and the matrices disagree.

## ASSUMPTIONS

- The `unit.note.append` direct-refused line's writer is
  `tests/test_transactions.py`: it is the only rest-1 file referencing
  `note.append`, and the line's operation matches; the exact test was
  not pinpointed.
- `follow-symbolic-links: false` being inert is concluded from run
  40121362655's artifacts (the `*current` copies are present in them);
  the merge dedupe provably handles both behaviors, so correctness does
  not rest on this reading.
- upload-artifact is assumed to drop empty directories (why `cases.txt`
  is touched); with the touch, the question is moot.
- UI `main` stays at `f7dbc1f` for the pair gates — verified by
  `ls-remote` immediately before each dispatch.
- Run 40128082544's phase-1 legs being green implies the injected test
  passed in rest-2 (its junit shows no failure); not separately quoted.

## Verdict

Every C3-F requirement is proven in CI on `glm/C3-2026-10-24` at the
final tip `f56a7b3`: the sharded validate (33m04s) and the branch's own
sharded release-pair (30m22s, pair receipt uploaded) are both green,
both under the 40-minute goal; the legs sum exactly to the unsharded
reference plus the branch's added tests (8514 = 8511 + 2 + 1; gate
8523); and the injection run (40128082544) proves that a witness line
written by a rest-leg test now reaches the merged zz population and is
asserted over — the gap is closed. The branch also fixed a real,
pre-existing defect (the doubled merged population) that the new
invariant caught on its first run, and found that the gap was already
live (rest-1's `unit.note.append` line). Nothing landed; landing the
branch — C3 and C3-F together — is Aram's call.
