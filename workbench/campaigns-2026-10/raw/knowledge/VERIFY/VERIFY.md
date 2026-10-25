# Verification of K1–K4 (Claude, 2026-10-25)

**Verifier:** Claude, at Aram's request. CAMPAIGNS.md names Codex as the
verifier; Aram assigned this to Claude instead.

**Verdict:** the campaign's claims hold.
- The workers proposed **0 findings**, and verification found **0 defects**.
- So there is **no fix block** to integrate.
- Every worker observation is classified below: absence, coverage gap,
  documentation drift, or recorded mechanics. One of them (K4 observation 1)
  is answered by UI code the worker did not read.

## Base

- Core `fb73b0f9` (PR #28 head, `codex/operator-developer-docs-20261025`),
  and UI `f7dbc1f`.
- All five campaign clones were re-checked. `git rev-parse HEAD` equals the
  pin in each.
- K2's data base: live Core `main` `7b713d84`, with no uncommitted changes
  under `knowledge/ sources/ curriculum/ records/ work/`.
- The probe copies in `K1/probes/` and `K4/probes/` are byte-identical
  (`cmp`) to the files that ran in the clones.

## 1. Reproductions re-run

Commands: one pytest process per file in the clone named in each report; one
`node` process per file in the K3 UI clone.

| Batch | Re-run | Result |
|---|---|---|
| K1 | 7 probe files, `tests/test_k1_*.py` | 25 passed, which matches the report |
| K4 | 7 probe files, `tests/test_k4_*.py` | 25 passed, which matches the report |
| K3 | `tests/test-atlas-graph.js` plus 6 `tests/k3-*.js` | all exit 0 |
| K2 | J1 hops, both J3 legs, all counts | matches the report; see below |

**K2 in detail.** K2 had no failing hops, so the rule "re-run 20% of the
failing hops" selected nothing. Instead:
- **J1:** `inspect stage-icop-l01-geometry` → `["concept-convexity"]`, and
  `inspect stage-icop-l01-forms` → `[]`. `atlas-context concept-convexity`
  → 1 relation and 0 questions.
- **J3:** the ICOP leg is `local-observed`, its binding is resolved with
  digest `76f3c809…`, and the PDF p.1 text appears. The `source-mml` leg is
  `remote-unobserved` with no spans, and it carries an explicit
  `next_action`.
- **Counts:** a direct YAML count, a different method from K2's read
  surface, agrees on all nine baseline lines: 138 / 99 / 67 / 94 / 152 / 120
  / 119 / 19 / 0. There are 0 `role: question` notes.

## 2. Refutation: do the green probes have teeth?

A probe that stays green under the bug it claims to guard proves nothing.
`VERIFY/mutate.py` plants one bug per invariant in the disposable clones, runs
the guarding probe, and then restores the file with `git checkout`. Afterward,
each clone's tracked files were back to the campaign state.

| Planted bug | Guarding probe | Probe result |
|---|---|---|
| strict-cycle check disabled (`registries.py`) | K1 `test_k1_4_prereq_cycles.py` | went red |
| Canvas draws dependent → prerequisite (`canvas.py`) | K1 `test_k1_5_canvas_direction.py` | went red |
| a node's unlicensed `concepts` field licenses an edge | K1 `test_k1_2_no_inferred_edges.py` | went red |
| old row matched by `from` alone, so a stale edit lands (`handlers/atlas.py`) | K4 `test_k4_1_stale_old_row.py` | went red |
| UI marks every question target present (`questions.ts`) | K3 `k3-questions.js` | went red |
| UI's old row leaks a projection `null` (`relation-editor.ts`) | K3 `k3-authoring.js` | went red |

Re-run with `python3 -I VERIFY/mutate.py`. Exit 0 means every mutation was
caught.

**Probe-quality note** (certain, not a product defect): K1
`test_three_concept_strict_cycle_names_the_whole_walk` slices its fixture down
to a 2-cycle, so its name overstates what it tests. A real 3-concept strict
cycle is covered by K4 `test_k4_2_replace_cycle.py`, through the gateway.

## 3. Observations, classified

| Source | Observation | Verdict |
|---|---|---|
| K1 | Content-mode `search` does not expand German aliases | **Absence by contract.** ARCHITECTURE §6 defines only the alias mapping, and `note.search` promises no expansion. Whether content search should bridge aliases is a product question for Aram. |
| K2 | `source-mml` route is `remote-unobserved` | **Missing linked evidence** (a count). The read is honest and names its own next step. |
| K2 | 0 saved questions; 0 `role: question` notes | **Recorded-question count = 0.** |
| K2 | 19 concepts with neither a note nor a relation | **Missing authored connection** (a count). Never a fix: ADR-017 decision 2. |
| K3 | Route contract carries a sixth lens, `domains` | **Certain documentation drift, not a behaviour defect.** ADR-016 decision 8 lists five lens values; `src/contracts/route-v1.ts:28-34` has six. It predates the UI's 2026-10-19 history snapshot (`5b1850c`), so its origin cannot be traced in-repo. The fix would amend the ADR, and ADRs record Aram's decisions, so this is his call. A judgment, not a certainty: `renderAtlasVariants` shows "Concepts" and "Domains" as two Atlas variants. That sits close to the "two atlases" outcome ADR-015 decision 4 warned against. |
| K3 | No UI affordance creates a question | **Absence.** ADR-017 decision 4 does not mandate a UI creation path; `atlas-question-save` creates questions from the CLI. Whether the Atlas should grow one is Aram's call. |
| K3 | Depth domain is {1, 2}; `depth: 3` falls back to 1 | **Consistent** with ADR-016 decisions 1 and 8: unknown values fall back. |
| K4 1 | `atlas.context` has no missing-target field | **Refuted as a gap.** ADR-017's missing-target consequence is met in the UI: `questions.ts:63-67` derives `targetPresent`, and `shell.ts:214-233` renders a non-clickable orphaned row reading "Recorded on … — no longer authored". This is code reading only: the DOM render is untested (K3 coverage gap 1). |
| K4 2–4 | No wording dedup; snapshot token is mandatory; revisions count commits | **Recorded mechanics,** confirmed by the passing probes. No contract line is violated. |

## 4. Still untested

None of these is a finding.
- **The UI's DOM rendering layer**, all of it (K3 gap 1). This includes the
  orphaned-question row above.
- **Fixture-vault end to end.**
- **J1–J3 for concepts other than `concept-convexity`.** K2 swept relations
  and counts over all 138 concepts, but walked only these chains.

## 5. Release state (context; nothing done here)

- PR #28 is open, and every check is green on `fb73b0f9`.
- The exact-pair `release-pair` run
  [40160353313](https://github.com/Aram164/LearningOS/actions/runs/40160353313)
  (core `fb73b0f9`, ui `f7dbc1f`) is green. STATUS.md still calls it pending.
- `origin/main` is still `7b713d84`, so the candidate the campaign tested has
  not landed.
- This verification does not certify a release. Landing is a separate,
  Aram-approved step.
- **Landed later on 2026-10-25,** on Aram's explicit OK:
  - the pair receipt was downloaded and verified locally (`"ok": true`);
  - Core `main` went `7b713d84` → `fb73b0f9`, a plain fast-forward pushed with
    `--no-verify` from the hook-less clone `~/los-land-pr28-2026-10-25`;
  - PR #28 is marked merged;
  - the live checkout was fast-forwarded and regenerated: validate 0 errors,
    no new warning signature.
