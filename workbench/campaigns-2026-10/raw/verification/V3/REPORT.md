# V3 — the derived layer (learning runtime, semantics) — REPORT

Batch V3 of campaign `glm-v-2026-10-25`. Final status: **complete — 0 findings, 5/5 properties HELD, 28/28 probes green.**

## Base

- Core pin `fb73b0f9c65de0f7a74c6d6e6b65ba74115a2e46` — verified with `git rev-parse HEAD` in `~/los-glm-V3-2026-10/repository` after detached checkout: `fb73b0f9c65de0f7a74c6d6e6b65ba74115a2e46`. MATCHES.
- UI pin `f7dbc1f7607157d5c1c2edb84a14e6a26ab89f94` — verified with `git rev-parse HEAD` in `~/los-glm-V3-2026-10/obsidian-ui` after detached checkout: `f7dbc1f7607157d5c1c2edb84a14e6a26ab89f94`. MATCHES.
- Core venv: `python3.14 -m venv .venv && .venv/bin/pip install -e '.[dev]'` — succeeded. `make setup`/`make hooks` not run, per ground rules.
- UI `npm install` not run: V3 has no UI probe and nothing in this batch touches `obsidian-ui/` beyond the pinned checkout.
- Clone git status after every probe process: only the batch's own intentional files (`tests/test_v3_probe_p1..p5*.py`, registration lines in `tests/group_map.py` and `.github/shard-manifest.json`). Never anything else.

## Reading route

All read at the pin, in this order:

1. `LearningOS/workbench/glm-v-2026-10-25/CAMPAIGN.md` — Ground rules + V3 only.
2. `system/SEMANTIC-CONTRACT.md` — predicates as pure functions over existing records, no fifth canonical family, fail-closed fallbacks, lineage sidecar never a projection, contract version 3.
3. `system/developer/components/learner-derivations.md` — invariant: "Derived proposals must never declare mastery or move recorded progress."
4. `system/developer/components/semantics.md` — invariant: "Interpretation must never become stored learner truth or write authority."
5. `system/developer/components/derived-store.md` — "Stale or corrupt cache content is a miss, never authority for current state."
6. `tools/learning_os/derive/learning_runtime.py` (346 lines, whole file) — `compile_requirement`, `collect_requirements`, `read_observations`, `read_stage_results`, `stage_results_for`, requirement/review/activity fingerprints.
7. `semantic.query` capability: `.venv/bin/python tools/los.py capabilities semantic.query --json` — verb `semantic`, `writes: false`, kind `tool`, task "governance-question"; handler read at `tools/learning_os/app/handlers/reads.py:538`.
8. `tests/scenarios/cases/semantic.query.yaml` — 7 cases; probes deliberately did not duplicate it.
9. `tools/learning_os/derive/projection/session_compiler.py` (843 lines, whole file) — `compile_session`, `replan_session`, eligibility/pool ordering, bounded repair, structural replacement.
10. `tests/repo_builders.py`, `tests/conftest.py::build_mini_repo` — fixture mechanics.
11. `system/adr/ADR-016-focused-atlas-navigation-2026-09-04.md` decision 2 — only the strict layer (`requires`, `builds-on`) orders; semantic relations never reorder a prerequisite.
12. Call sites and schemas: `reads.py` `runtime.session` handler, `system/schema/study-map.schema.json` (detour/shelving states), `system/schema/learner-observation.schema.json`, `system/schema/learner-stage-result.schema.json`.

## Results per item

One pytest file per process, no `-n`, no xdist; `git status --porcelain` run after every process (output recorded above under Base and in the shell transcript).

| # | Property | Probe file (`probes/`) | Result |
|---|---|---|---|
| 1 | Pure | `test_v3_probe_p1_pure.py` | **HELD** — 4/4. Two runs over the same records serialize byte-identical (`requirements`, `observations`, `stage_results`, live results, `compile_session` for `unseen`); two identically built fixture roots byte-identical; permuting `unit_order` leaves `collect_requirements` identical; `los semantic --list` and `semantic RepoClean --input error_count=0 --input new_or_grown_warnings=[]` stdout byte-identical across runs. |
| 2 | Read-only | `test_v3_probe_p2_readonly.py` | **HELD** — 3/3. Fixture committed as a git repo; after `collect_requirements`/`read_observations`/`read_stage_results`/`stage_results_for`, `compile_session` for all five statuses, `replan_session` (target-changed), and the `semantic` CLI (`--list`, `RepoClean` evaluate, unknown-predicate refusal, bad-input refusal), `git status --porcelain` was empty each time: no derived value lands anywhere, canonical or generated. |
| 3 | Faithful | `test_v3_probe_p3_faithful.py` | **HELD** — 5/5. Every compiled requirement resolves its citations via `requirement_stage` (unit, module, current study map, stage); editing an unrelated note body and a stage title leaves `collect_requirements` and the requirement fingerprint unchanged; removing the cited `runtime_target` empties the compilation and `read_observations` refuses naming the exact requirement id and ledger path (`observations.jsonl:1`); a stage-result citing a vanished stage is refused naming stage and unit; a requirement citing an unknown concept is refused naming the concept. |
| 4 | No mastery | `test_v3_probe_p4_no_mastery.py` | **HELD** — 8/8. Every string of `compile_session` output for all five statuses matches no mastery/understanding/proficiency vocabulary; with an empty observation ledger `interpret_observations` returns status `unseen`, the session reports `current_status: unseen`, empty `evidence_ids`, and never `plan_status: satisfied`; `demonstrated` appears only when the recorded interpretation carries it, and even then no mastery sentence is added; the requirement IR itself carries none. (ARCHITECTURE §12 absent-evidence honesty holds on this path.) |
| 5 | Session order | `test_v3_probe_p5_session_order.py` | **HELD** — 8/8. Sessions select only resources of the requirement's own stage; the stage resolves only through the unit's current study map (repointed map → `RuntimeInputError`); replan refuses a packet whose `source_stage` belongs to another stage, refuses a stale snapshot and an unknown event, and requires an explicit `target-changed` event for a different requirement; adding `derives`/`equivalent-to`/`motivates` semantic relations (both directions, cyclic) between the two stage concepts leaves the compiled session byte-identical (ADR-016 decision 2); the role structure is fixed and authored order decides within the evidence pool; adding an open detour row and a `proposed` shelving proposal with items leaves session output byte-identical. |

Probe-run totals: P1 4, P2 3, P3 5, P4 8, P5 8 = **28 probes, all passing on the pin**.

## Findings

None. Every probe passed on the pin; there is no failing test to report.

Honest note on probe history: three probes initially failed for reasons that were defects in my probe, not in the code, and were corrected and re-run — (1) a wrong base path passed to `build_mini_repo` in P1; (2) P3 ledger rows missing the schema-required `activity` field, which the schema validator correctly refused before resolution errors could fire; (3) P5 expected authored-order reversal to flip the whole step list, but with unreviewed evidence the session takes the documented blocked-practice branch where the intervention resource leads by role structure (`session_compiler.py` docstring and `_repair_with_prerequisites`/practice branch); with evidence reviewed, the ready path shows authored order deciding inside the evidence pool, as asserted. Also relaxed: P3 initially demanded the orphaned-observation error name the stage — it names the requirement id and ledger location instead, which is the most it can know (no stage declares the requirement any more) and satisfies "names the loss".

Observations (no contract line violated, recorded for the record):
- `compile_session` resolves the stage through the unit's current study **map** but never consults the map's `current_stage` pointer; `runtime.session` will compile a session for any stage of the current map whose requirement is named. Detour/return-to-stage semantics make revisiting earlier stages legitimate, so this reads as intended; pinning it either way is a design decision, not a defect found.
- The orphaned-observation refusal message (`learning_runtime.py:240-246`) says in its comment it names "which stage stopped declaring it", but the message cannot and does not name a stage — it names the requirement and the ledger line. Comment/message mismatch only.

## Coverage gaps

- The `semantic.query` scenario cases (`tests/scenarios/cases/semantic.query.yaml`) were not re-executed as a suite; refusal **site codes** (`semantic.query.bad-recipe` etc.) rest on the scenario file plus a handler read. I exercised unknown-predicate and bad-input refusals directly (nonzero exit, no writes) but not the exact site strings.
- Lineage (Phase 2), goal lifecycle (Phase 3), dossiers (Phase 5), proof-carrying change (Phase 6), VOQs, and the intelligence scan were read at contract level but not probed: the five V3 properties as stated target the learning runtime and the session compiler, and the campaign forbids full-suite runs that would have re-driven their pinning tests.
- `los resume` / `build_resume_dossier` compilation: not probed (read at contract level only).
- `derive/` siblings outside the five properties' path — `material_synthesis.py`, `masters_catalog.py`, `garden.py`, `semesters.py`, `health.py`, `ai_actions.py` — untouched.
- The gateway porcelain transport of `runtime.session` (CLI `los session`) was not driven end-to-end; probes call `compile_session`/`replan_session` directly, the same functions the handler at `reads.py:1166` calls, with the same schema validations.

## Untested scope

- Multi-process or concurrent derived reads (campaign rule: one test process at a time).
- Performance/efficiency properties (`tests/test_runtime_efficiency.py` exists; not in the five properties).
- Everything UI-side (V2's scope) and every V4/V5 concern.
- Behavior at Core revisions other than the pin.

## ASSUMPTIONS

- The `semantic.query` scenario passes on the pin (site codes and refusal bodies taken from `tests/scenarios/cases/semantic.query.yaml`, not re-run). ASSUMPTION.
- `_review`-shaped `independent_evidence` blocks (copied shape from `tests/test_session_compiler.py` usage of the public fingerprint helpers) are schema-valid for stage resources on the pin. ASSUMPTION — the ready-path probes passed with them, which exercises the validator, but I did not separately pin the schema file.
- `run_los` subprocess timeouts (120 s) never bound: every probe finished in under 3.5 s total per file. Verified by the logs.
