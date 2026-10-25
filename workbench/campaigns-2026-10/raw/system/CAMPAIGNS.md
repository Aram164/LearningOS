# GLM campaigns, 2026-10-24 to 2026-10-26 (written by Claude for Aram)

Aram has free GLM-5.3 and GLM-5.3-Flash credits until 2026-10-26 02:00. Each
campaign below runs as its own ZCode session. Read **Ground rules** first, then
only your own campaign.

Each campaign is built so that its output proves itself: as a failing test, a
CI run, or a command anyone can re-run. Output that has to be taken on trust
costs more to review than it saves.

## Ground rules (every campaign)

**Your own copies.**
- Use full clones only, at `~/los-glm-<campaign>-2026-10/{repository,obsidian-ui}`.
  Never use a worktree of the live checkout.
- **Clone from GitHub:** `git clone https://github.com/Aram164/LearningOS.git`
  and `…/learningos-obsidian-ui.git`. Do not clone from the live checkout. A
  clone of the live checkout carries Aram's personal-data branches, and its
  local `main` is stale (behind, not divergent). C2 is the one exception: it
  needs the live data and never pushes.
- Give the clone its own venv:
  `python3.14 -m venv .venv && .venv/bin/pip install -e '.[dev]'`.
- Do not run `make setup` or `make hooks`.

**Base.**
- Core: `origin/main` once it reads `d6c47790` or later. Until then, use
  `d6c4779029e366718b71bda158d2aa8f9da1db39`.
- UI: `f7dbc1f7607157d5c1c2edb84a14e6a26ab89f94`.

**Never touch:**
- the live trees `LearningOS/repository/` and `LearningOS/obsidian-ui/`;
- the vault or Obsidian;
- `main` on any repo;
- other campaigns' clones and branches;
- issues and PRs;
- other agents' processes.

**The laptop.**
- One pytest process at a time, on focused test files only.
- Never run the full suite, `make system-check`, a broad `make test-affected`,
  or a pre-push gate.
- No more than **two campaigns at once** on this machine.

**CI upstream.** Both repos are public, so Actions minutes are free.
- Push only your own branch, `glm/<campaign>-2026-10-24`, with
  `git push --no-verify` (Aram authorizes this for that branch only).
- Gate it with
  `gh workflow run release-pair.yml --repo Aram164/LearningOS --ref main -f core_sha=<sha> -f ui_sha=<sha>`.
- Wait with one background `gh run watch`. Never poll.

**Public repos.** Never commit or push anything from Aram's study data,
materials or notes. Personal-data output stays in this workbench folder only.
`LearningOS/` is ignored by the wrapper, and the workbench is outside Core.

**Contracts.** Do not edit `system/contracts/` unless your campaign says so.
Every contract edit moves the fixture snapshot, and with it recordings on
every other branch.

**Models.**
- GLM-5.3-Flash (300M a day) for bulk reading and hunting.
- GLM-5.3 (200M a day) for diagnosis, design and adversarial verification.
- One long session costs about 25M input tokens, about 99% of it cache reads,
  so budget in sessions, not tokens.

**Finish signal (mandatory).** Your prompt names your item id, for example
`L2-3`. A Claude orchestrator wakes on this signal and starts the next
session, so a missing signal stalls the whole lane. As your very last
action, after the report is written, run exactly this:

```bash
mkdir -p /Users/aramaljanadi/Desktop/semestercontext/LearningOS/workbench/glm-campaigns-2026-10-24/signals && echo "<report path relative to the campaign folder>" > /Users/aramaljanadi/Desktop/semestercontext/LearningOS/workbench/glm-campaigns-2026-10-24/signals/<item id>.done
```

If you have to stop without finishing (blocked, out of credits, or a ground
rule would be broken), still signal. Write `BLOCKED: <one-line reason>` as
the content instead of the report path.

**Reporting.**
- Write into `LearningOS/workbench/glm-campaigns-2026-10-24/<campaign>/`.
- Mark everything you did not run or read yourself as ASSUMPTION.
- Stop at the report. Fixing what you found, filing issues and landing all
  belong to Aram or Claude.

## Run order: two lanes, never more than two sessions at once

The exact prompts, in order, are in [PROMPTS.md](PROMPTS.md).

| When | Lane 1 (GLM-5.3) | Lane 2 (Flash) |
|---|---|---|
| Now (Sat night) | C3, which mostly waits on CI | C2 for M2, which Aram is studying |
| Sat | C3 iterations, then C1 verification of A–C | C1-A to C1-E |
| Sat evening | C1 verification of D–E | C2 modules 2–4 |
| Sun | C2's 20% re-check; C4, once its prerequisites hold | C2 modules 5–8 |
| Sun 22:00 | Every session reports and stops | |

The credits end Mon 26 Oct at 02:00.

Every report goes to Claude for verification before anything lands or reaches
an issue.

## C1: Bug hunt with proof

**Why.** The audit wave on 2026-10-23 found the real bugs #10–#25. This
campaign repeats that hunt systematically, across all 75 capabilities in
`system/contracts/capabilities.yaml`: 50 commands, 20 queries, 4 domain
capabilities and 1 internal command.

**Batches.** Run **one session per batch, on Flash**, in this order. Each
batch takes every capability whose name starts with the listed families.

| Batch | Families |
|---|---|
| **C1-A** curriculum and plans | `module`, `program`, `masters-planning`, `plan` |
| **C1-B** units and paths | `unit`, `stage`, `path`, `route`, `detour`, `review`, `learner` |
| **C1-C** knowledge | `note`, `concept`, `ability`, `atlas`, `garden`, `relationship`, `semantic` |
| **C1-D** sources and intake | `source`, `collection`, `material`, `ai-action`, `capture`, `inbox` |
| **C1-E** operations | `lineage`, `legacy`, `backup`, `coordination`, `workspace`, `project`, `goal`, `runtime`, `health`, `operator` |

Name the branch and the output folder after the batch, for example
`glm/C1-A-2026-10-24` and `C1-A/`.

**What to attack, per capability:**
- crash windows: kill the process between commit and promotion;
- exact-replay and idempotency conflicts;
- stale snapshots;
- paths with unicode, spaces, `..` and symlinks;
- two sessions writing at once;
- rollback after partial writes;
- refusal sites that are declared but never witnessed;
- mismatches between the docs and the code (`system/procedures/*.md` against
  the handler).

**A finding counts only when it comes with a failing pytest.** That test must
fail on base `main`, and it must pass once the expected behaviour holds.

**For each finding, save:**
- `C1/<capability>/<slug>/test_<slug>.py`, the reproduction;
- `C1/<capability>/<slug>/finding.md`, with:
  - the command;
  - what you observed, verbatim;
  - what you expected, and which contract or doc line says so;
  - the root cause at `file:line`;
  - a suggested fix in one paragraph.

Write the test inside your clone's `tests/` and run only that file. Copy the
result into the workbench. Do not commit it.

**Verification pass, on GLM-5.3, in a fresh session.** For every finding:
1. Re-run the test on `main`.
2. Try to refute the diagnosis: is it really a contract violation, or did the
   test misuse the API?
3. Mark the finding CONFIRMED or REFUTED, with the reason. Only CONFIRMED
   findings reach Aram.

Write no fixes and file no issues.

## C2: Your study plans against your real materials

**Why.** The validator checks that a locator exists and can be addressed. It
never checks that the locator belongs to the route's own material. Past case:
in September, a repair in `module-hu-m2-statistik-analysis` keyed on
`(source_id, unit_id)` broadcast one route's locator onto five siblings, and
`make check` stayed clean. **That damage was repaired by 2026-10-24.** Do not
go looking for it; report what you actually find.

**Before calling anything damage, establish where it came from.** Git
history in the live branch starts at the 2026-10-19 snapshot. The original
generated plans live in the module's workspace `outputs/`, for example
`work/active/workspace-m2-exam-prep/outputs/Analysis-chapter-maps-2026-08-29/`.
- If the current shape matches the original, it is **original design or
  unmigrated debt**, not damage. Say which.
- Call it damage only when an original said something different and a later
  pass overwrote it.

**Input.** A local clone of Aram's live branch, which contains his data:
`git clone --no-hardlinks <semestercontext>/LearningOS/repository` and check
out `takeover/complete-and-install-2026-10-23`. Read materials in place,
read-only, from `LearningOS/materials/`. **Never push this clone: it holds
personal data and the repo is public.**

**Per module, check that each route and stage resource matches its own
material:**
- `vault_path` and `material://` against the file named in `locator`;
- page ranges inside the PDF's real page count;
- the TOC or section named in `angle_detail`, against the text
  (`tools/material_toc.py`, `tools/material_text.py`);
- duplicate `locator` or `angle_detail` strings among sibling routes of one
  `(source_id, unit_id)` group.

**Also** triage each validation warning in your clone
(`.venv/bin/python tools/validate.py --compact`, about 1470 of them) as a real
defect or noise, and say why.

**Pitfalls (from past mistakes):**
- A route's identity is its `id`, never `(source_id, unit_id)`.
- Map PDF ligatures and quotes before you search: `ﬀ ﬁ ﬂ ﬃ ′ ’` become
  `ff fi fl ffi ' '`. Then collapse whitespace.
- Confirm a miss against the whole document, never against one page.
- A title match is not evidence of coverage. Open the material.
- Page numbers are PDF page numbers, never printed ones.

**Output:** `C2/<module-id>/REPORT.md`, listing each defect with its evidence
(page and extracted text).

**One gate needs Aram first.** These warnings are the deferred debt of
critique point 1 (`system/CRITIQUE-POINTS.md`, OPERATOR boundary 17).
- Recording evidence is always allowed.
- Preparing fix packages (`module-plan-import` with `--check` only, in your
  clone, never applied) counts as acting on the point, which needs Aram's
  explicit go-ahead. His kickoff message says which of the two he allows.

**Models.** Flash, one session per module. Then one GLM-5.3 session that
re-checks a sample of 20% of the defects against the PDFs.

**Module order.** Skip the archived and dropped modules: `hu-algo2`,
`hu-ppds`, `hu-seminar-iug` and `hu-amls`. The rest, most urgent first:

1. `module-hu-m2-statistik-analysis`, which has the known route damage
2. `module-hu-aml`
3. `module-hu-betriebssysteme`
4. `module-hu-icop`
5. `module-project-bachelor-thesis`
6. `module-foundation-ml-math-bridges`
7. The five `module-job-*` modules, together in one session
8. `module-skill-python`

## C3: Make the 2-hour gate a 30-minute gate

**Why.** Every landing on 2026-10-23 waited about 2 hours: validate took
2h05, and each release-pair run about 2h. A 30-minute gate makes every future
agent iteration about four times faster, and removes the temptation to run
tests locally.

**Goal.** `validate.yml` and `release-pair.yml` both finish in 40 minutes or
less on GitHub runners, with **exactly** the same set of tests.

**Inputs.**
- Per-test durations come from CI only: add `--durations=0` or JUnit XML as
  an artifact on your own branch. Never measure locally.
- Shard with `pytest-split` or an equivalent, plus a matrix.

**The hard part.** `tests/test_scenarios_zz_*` assert over the whole
session's population of witnesses: A19 and A9. They must run after the shards,
over merged witness artifacts, or the witnesses must stay in a single shard.
Prove that the sum across shards equals the unsharded count: 8507 passed, 7
skipped, 1 deselected and 2 xfailed at `eb087e3a`. Also prove that a test
injected to fail is still caught.

**Scope.** `.github/workflows/*`, `pyproject.toml`, and `tests/conftest.py` if
it is needed. Landing changes CI, so it needs Aram's approval.

**Model.** One GLM-5.3 session.

## C4: Process this semester's lectures

This is the learner-facing payoff of the new transcript. It has three
prerequisites, and Aram owns two of them:

1. **The `learning-gaps-2026-10-24` branch has landed, and the live branch
   contains it.** Claude merges `main` into
   `takeover/complete-and-install-2026-10-23`, so that the live
   `OPERATOR.md` carries the new boundary 18.
2. **The as-taught decks are in the materials tree.** On 2026-10-24,
   `module-hu-betriebssysteme` had no materials folder, and
   `materials/algorithms/structures/icop-hu-ws2627/` held 2 PDFs. Aram
   downloads this semester's slides into the module's materials folder.
3. **C4 is the only session running in the live Core tree.** C1, C2 and C3
   use clones and do not count.

Then, model GLM-5.3, one module per session, working in the live tree:
1. Follow `system/procedures/process-a-lecture.md` for each deck.
2. Stop at `module-plan-import … --check`, as boundary 18 requires.
3. Write `C4/<module-id>/<unit>.md` with the package and the check result.

Aram reviews the packages in one batch. Apply only those he answers yes to.


## Next blocks, added Saturday 2026-10-24 19:10

Added by the orchestrator once C1, C2 and C3 were verified. C4 still waits
for its prerequisites. Each block names the files its session reads first.

### C3-F: close the witness-producer gap (Lane 1, GLM-5.3)

**Why.** `C3/CLAUDE-VERDICT.md`, "The gap, certainly real but latent": which
legs count as witness producers is set by hand in the manifest. A future
rest-leg test that writes witness lines would drop out of the A9/A19
population silently. That should be closed before C3 lands.

**Read first:** `C3/REPORT.md` and `C3/CLAUDE-VERDICT.md`.

**Where:** your existing clone `~/los-glm-C3-2026-10/repository`, branch
`glm/C3-2026-10-24` (tip `323b68c`).

**Decisions, already made:**
- **Every phase-1 leg uploads its witness and audit artifacts, and the zz
  merge takes all of them.** The hand-kept list of witness producers goes.
  - Reason: the population is then complete by construction. A check
    against a hand list could only detect drift; this removes the list.
- **One manifest file, read by both workflows,** instead of
  `SHARD_MANIFEST` pasted into each.
  - Reason: it touches the same lines, and two copies can drift.

**Proof required:**
1. The sharded `validate` and the branch's own sharded `release-pair` are
   green on the new SHA.
2. The legs still sum to the unsharded count in `C3/REPORT.md`.
3. **The gap is closed.** A temporary commit makes one rest-leg test write a
   witness line, and that line appears in the merged zz population. Then
   revert it. Name the run that proves it.

**Output:** `C3/FOLLOWUP.md`. Do not land; landing C3 is Aram's call.

### C5: a fix branch for the confirmed C1 findings (GLM-5.3)

**Why.** C1 left 9 CONFIRMED findings, each with a failing test. Turn the
fixable ones into one gated branch, which the landing session can land
after Aram's OK.

**Read first:** `L1-234-CLAUDE-VERDICT.md`, then each batch's
`CLAUDE-VERDICT.md` and `ISSUES-DRAFT.md`.

**Where:** a fresh GitHub clone at `~/los-glm-C5-2026-10/repository`, branch
`glm/C5-2026-10-24` from `origin/main` (`d6c47790` or later).

**Rules:**
- **One commit per finding.** It holds the fix plus the finding's test,
  copied from the workbench and registered in `tests/group_map.py`, as a
  regression test.
- **The test must fail before the fix and pass after it.** Then run the
  capability's existing focused test files, one pytest process at a time.
- **No edits under `system/contracts/`.** If a finding's right fix needs one
  (a new declared refusal site, an invariant's wording, a fixture move),
  leave the finding out of the branch and write its fix as a proposal in
  the report.
  - Reason: the unlanded `learning-gaps-2026-10-24` branch already edits
    two contract files. A second contract edit would move the fixture
    snapshot and collide at landing.
- **Never write a closing keyword** ("Fixes #27") in a commit message. A
  plain `(#27)` is fine.

**Which finding, and the design decision for each:**

| Finding | Fix |
|---|---|
| #27, `module.attempt.record` (C1-A) | As the issue proposes. |
| C1-A `module.create` legacy clash | **Out.** Decided not to fix: the contract's invariant wording is what should change. |
| C1-B-1, `review.apply` partial apply | **Unselected items stay pending.** The packet keeps `state: proposed` while unapplied items remain; applied items leave the packet (their receipt records them); no new schema field. |
| C1-C-1, `note.revise` | Uphold `ARCHITECTURE.md` §5.7: the general path must not change a question's target, nor a reference note's bytes under its `material_analysis` binding. Fix witness 2's `sha256:` precondition bug in the test first. |
| C1-C-2, garden reserved slug | The writer never produces a stem the reader skips. Suffix it, as the collision loop does. |
| C1-D-1, same-second capture | The file branch loops with a serial, as the text branch does. |
| C1-D-2, `--limit 0` | Zero reaches the existing bad-window refusal. |
| C1-E-1, backup symlinked subtree | **Refuse**, as the module already does for unreadable directories and a symlinked declared tree. |
| C1-E-2, coordination reflow | `replace_h2_section` leaves every other section byte-identical. |

Reasons for the C1-B-1 decision:
- The code already accepts a later apply of the remainder.
- The UI offers a checkbox per item.
- "Declined" would discard proposals the learner never declined.

**CI:**
- Push `glm/C5-2026-10-24` with `git push --no-verify`.
- Dispatch one `release-pair.yml` (`--ref main`) on the final SHA.
- Wait with one background `gh run watch`.

**Output:** `C5/REPORT.md`, with:
- per finding: the commit, the test's before and after output, the files
  touched, and the focused tests run;
- the proposals for the findings left out;
- the release-pair run ID and its counts.

### C2-R: M2's 80 unchecked routes (Lane 2, Flash)

**Why.** M2's section check (`C2/module-hu-m2-statistik-analysis/scripts/c2_sections_audit.py`)
silently skipped 80 routes. Each names a PDF in its `locator` or
`angle_detail` but has no `vault_path`. Its fallback search used `rglob`,
which finds nothing through the `materials/.flat` symlinks. The 80 are
measured in `L1-234-CLAUDE-VERDICT.md`.

**Where:** the C2 clone `~/los-glm-C2-2026-10/repository`, read-only. Never
push it.

**Method:**
- Find the PDF each route names with a lookup that follows symlinks: Python
  3.14 `rglob(..., recurse_symlinks=True)`, or `os.walk(followlinks=True)`.
- Verify every section and page claim as C2 requires, with the C2 pitfalls.
- Record a route whose PDF cannot be found at all as its own defect class.

**Output:** `C2/module-hu-m2-statistik-analysis/RECHECK-80.md`. Evidence only.
