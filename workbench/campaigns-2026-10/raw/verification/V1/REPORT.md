# V1 — the developer docs and system map against the code

## Base

- Core `fb73b0f9c65de0f7a74c6d6e6b65ba74115a2e46` — verified:
  `git rev-parse HEAD` in `~/los-glm-V1-2026-10/repository` →
  `fb73b0f9c65de0f7a74c6d6e6b65ba74115a2e46`.
- UI `f7dbc1f7607157d5c1c2edb84a14e6a26ab89f94` — verified:
  `git rev-parse HEAD` in `~/los-glm-V1-2026-10/obsidian-ui` →
  `f7dbc1f7607157d5c1c2edb84a14e6a26ab89f94`.
- Setup followed CAMPAIGN.md exactly: detached checkouts, siblings named
  `repository` and `obsidian-ui`, `python3.14 -m venv .venv && pip install -e
  '.[dev]'`, `npm install`, no `make setup`/`make hooks`.

## Reading route

1. `tests/test_system_map.py` and `tools/system_map.py` first, per the task, to
   attack only what the guard does not check. The guard verifies: the 7
   component-page headings and 80-line limit; entry-point/pinning-test/ADR
   symbol existence; invariant pinning; one-owner-per-module via Owned-path
   globs; owned-path globs matching ≥1 module; import-linter layer order and
   violations; staleness of the generated `edges`/`index`/`components` blocks;
   FLOWS symbol references and participant resolution; existence of
   `tools/`/`tests/`/`system/`/`pyproject.toml` paths named in
   CODEMAP/C4/FLOWS.
2. Everything under scope read in full: `system/DEVELOPER.md` (45 lines),
   `system/developer/{CODEMAP,C4,FLOWS,changing-contracts}.md` (392 lines),
   all **24** pages in `system/developer/components/` (922 lines).
   Note: the task says "all 23 pages"; 24 files exist on the pin. I checked all
   24 (the extra one is `package-root.md`, which the C4 text itself calls out as
   documented separately). The campaign's "23" is the only count that is off.
3. Claims verified against the clone by: file/anchor existence sweeps
   (`probes/probe_paths.py`), `ast`/`grep` symbol checks, behavioral schema
   probes (`probes/probe_schema_strictness.py`, `probes/probe_nested_open.py`,
   both using the production `schema_registry`), flow-order reading of
   `pipeline.py`/`generate.py`/`validate.py`/`los.py`/`cli_entry.py`/
   `commit.py`, and the UI clone at its pin for the sibling claims.
4. The two required counts (see below).

Totals: **claims checked 75** — verified **71** (of which ~30 held directly by
the system-map guard on this pin), **false 2** (both findings below, each with
a failing pytest), **unverifiable 2** (both process/roadmap statements, listed
under ASSUMPTIONS). No coverage gaps in the guard-checked surface; probe limits
are stated where they exist.

## Results per item

Legend: GUARD = already held by `tools/system_map.py --check` at this pin (I
re-ran the mechanism conceptually through `tests/test_system_map.py`, which
passes on the pin; the negative-control rows prove each check fires). HELD =
verified by me against the code. FINDING = false claim with failing test.

### system/DEVELOPER.md

| document:line | claim | check | result |
|---|---|---|---|
| DEVELOPER.md:9-12 | OPERATOR.md has a "Hard boundaries" section; OPERATOR-POLICY.md exists | `grep '^## Hard boundaries' system/OPERATOR.md` → line 116; file exists | HELD |
| DEVELOPER.md:13-14 | developer/CODEMAP.md, C4.md, FLOWS.md exist | files read in full | HELD |
| DEVELOPER.md:15 | "Static import arrows are not runtime calls" | matches guard docstring (`system_map.py:5-6`) | HELD |
| DEVELOPER.md:18-19 | "The corpus declares this entry as `developer_entrypoint`" | `grep developer_entrypoint system/contracts/normative-corpus.yaml` → line 56: `developer_entrypoint: system/DEVELOPER.md`; enum in normative-corpus.schema.json:12,32 | HELD |
| DEVELOPER.md:26 | `system/schema/requests/`, `system/contracts/capabilities.yaml` exist; cli-adapter and operation-pipeline pages exist | paths.log; component pages read | HELD |
| DEVELOPER.md:27 | developer/changing-contracts.md exists | read in full | HELD |
| DEVELOPER.md:28 | validation page; `system/VALIDATION.md` exists | paths.log | HELD |
| DEVELOPER.md:30 | "system-map check, code-check and import-linter" | `code-check` Makefile target; importlinter contracts in pyproject.toml | HELD |
| DEVELOPER.md:31 | `tools/code_reachability.py`, `tools/README.md`, `build_parser()` | files exist; `build_parser` at code_reachability.py:433 | HELD |
| DEVELOPER.md:32 | `tests/group_map.py` and `.github/shard-manifest.json` | files exist; I registered two test files in both per the task row | HELD |
| DEVELOPER.md:33 | `Makefile`, `tests/architecture/`, `commit-check` | target `commit-check:`; tests/architecture/ populated (a2-mode.txt, engine-baseline.json, …) | HELD |
| DEVELOPER.md:40-41 | `tools/system_map.py --write` / `--check` | both flags in system_map.py:213-214 | HELD |
| DEVELOPER.md:41-42 | "Its symbols prove names exist, not that a flow has executed" | matches `symbol_exists()` (ast definitions only, system_map.py:43-58) | HELD |
| DEVELOPER.md:44 | "The sibling UI's internal documentation is phase 2" | roadmap statement; nothing in either repo contradicts or confirms | UNVERIFIABLE (ASSUMPTION) |

### system/developer/CODEMAP.md

| document:line | claim | check | result |
|---|---|---|---|
| CODEMAP.md:10 | `tools/los.py` is the starting adapter | file exists; `main()` → `cli_entry.run` | HELD |
| CODEMAP.md:10-13 | adapters parse; app pipeline admits/coordinates; handlers own operation families; derive computes; store loads/contracts/persists; domain holds leaves | layer order in pyproject (adapters→app→derive→store→domain) + page purposes + handler family modules exist | HELD |
| CODEMAP.md:14 | `tools/README.md` classifies the executable tools | README head: "The table is the first place to answer whether a script is a supported entrypoint…" | HELD |
| CODEMAP.md:17-40 | component index block | generated block, guard-checked | GUARD |
| CODEMAP.md:45-46 | pyproject declares "A1 layers (PLAN D17)", "A1 transaction writer access (PLAN A2, D4)", "A1 transaction service protected (PLAN A1, D14)" | tomllib dump of importlinter contract names — exact strings, types layers/forbidden/protected | HELD |
| CODEMAP.md:47 | Import-linter enforces those contracts | contracts present in pyproject `[tool.importlinter]`; `code-check`/`lint` targets | HELD |
| CODEMAP.md:52 | `tests/architecture/` owns refusal-site, ownership and ratchet inventories | directory populated with inventories (cli-parity-*, effects.yaml, engine-baseline.json, …) | HELD |
| CODEMAP.md:53 | ADR-018 explains those gates; ADR-019 records the documentation split | ADR-018 "The operation boundary and enforced architecture" (2026-10-03); ADR-019 "operator-developer documentation" (2026-10-25) both exist | HELD |
| CODEMAP.md:55 | reciprocal component deps inside one layer ≠ module cycles | consistent with guard's component-level edge model; derive layer shows such pairs (learner-derivations ↔ projection/semantics) | HELD |
| CODEMAP.md:59-63 | one append-only receipt per successful write; diagnostics disposable; FLOWS gives order | transactions.py:7 ("append-only transaction receipt for every committed write"); diagnostics page; flow checks | HELD |
| CODEMAP.md:65-66 | "intentionally stable… Do not expand it into a function catalogue" | consistent with count below (0 of 223 modules named) | HELD |

### system/developer/C4.md

| document:line | claim | check | result |
|---|---|---|---|
| C4.md:20-26 | UI → Core over "CLI process / JSON"; core → authored store, ledger, views, materials | `los-runtime.ts` spawns `execFile` processes; receipts/operations, generated/ (gitignored), materials read-on-demand | HELD |
| C4.md:28-30 | `tools/los.py`, `tools/generate.py`, `tools/validate.py`, `tools/seal_envelope.py` are process entry points into `learning_os` | each imports `learning_os` (grep counts 2/4/5/35) | HELD |
| C4.md:31 | "The plugin starts Core using the vault's interpreter and script" | `los-runtime.ts:65-73` resolves `.venv/bin/python` (vault venv) then runs the script | HELD |
| C4.md:32 | "Generated views and caches are disposable; authored files and committed receipts are durable" | `.gitignore:1-2 generated/*`; receipts under `operations/transactions/` | HELD |
| C4.md:36-38 | printed layer order is the permitted downward direction; package-root outside the layers contract | layers = adapters→app→derive→store→domain in pyproject; package-root excluded from the layers contract in the guard | HELD |
| C4.md:41-115 | layer diagrams + "Component roster: 30 intra-layer imports omitted here" | generated block, guard-checked | GUARD |

### system/developer/FLOWS.md (order of each flow against the code)

| document:line | claim | check | result |
|---|---|---|---|
| FLOWS.md:2-3 | "traces were checked against the code at the change's base"; checker proves names, not execution | process claim; I re-verified every step at the pin myself | HELD (my checks) |
| FLOWS.md:34-38 (flow 1) | S seals → A submits → P validates/approves/locks/replay-checks → H via `_registered_compute` → bounded proposal back | pipeline.py:838-852 envelope validation; 909-946 approval/gesture; 958 operator lock; 960 replay_for_request; 1069-1090 snapshot guard; 1095 `_registered_compute` → `entry.handler` (780) returns `res.proposal` | HELD — order matches exactly |
| FLOWS.md:40 | "P->>C: `_commit_with_gesture` delegates commit" | pipeline.py:166-182: `_commit_with_gesture` → `commit_proposal` (symbol not in the guard's symbol list, but exists) | HELD |
| FLOWS.md:41-43 | C→T with writes/revisions/snapshot/validation-publication callbacks; typed failure/recovery back | commit.py:153-156 TransactionService construction; 165-179 validation/publish closures; 232 `service.commit(**kwargs)` | HELD |
| FLOWS.md:48-51 | exact replay returns before recomputing the handler; check mode validates a shadow proposal; post-commit bookkeeping failure does not undo a commit | pipeline.py:1046-1049 (replay returns before dispatch); 785-794 (`check_proposal`, no commit); 217-222 (`PostCommitFailure` raised after commit) | HELD |
| FLOWS.md:67-76 (flow 2) | G load → B generate_all → W write_outputs, in that order | generate.py:38 → 40 → 51 | HELD |
| FLOWS.md:78-79 | errors refuse publication instead of silently omitting unreadable state | generate.py:41-50 returns before `write_outputs` on TransactionFailure/RuntimeInputError | HELD |
| FLOWS.md:94-103 (flow 3) | V observe pins → L load → C Validator.run → print, optional report, refresh disposable cache | validate.py:60-63 discard+observe_pins BEFORE load_repo:64; 71-72 run; 91-95 print; 101-106 report; 108-115 write_static_cache | HELD — order matches exactly |
| FLOWS.md:103-106 | warning-baseline is a separate gate; cache is auxiliary and cannot turn a new observation into an earlier trusted result | store/warning_baseline.py separate; `make warnings` target; validate.py:57-63 pins observed before load | HELD |
| FLOWS.md:122-133 (flow 4) | U execFile with interpreter/script/args/session/trace env → L los.main → A cli_entry.run → P run_cli → H reads.bootstrap | los.py:34; cli_entry.py:11-21; pipeline.py:226-242 REGISTRY dispatch; reads.py::bootstrap (guard); los-runtime.ts:1,20-24 execFile + session/trace env | HELD |
| FLOWS.md:136-137 | boundary traced in sibling `src/infrastructure/los-runtime.ts` at UI `f7dbc1f` | file exists in the UI clone checked out at exactly that commit | HELD |
| FLOWS.md:138 | "The read shown is an example; it does not claim every UI read is bootstrap" | properly hedged in the document | HELD |

### system/developer/changing-contracts.md

| document:line | claim | check | result |
|---|---|---|---|
| changing-contracts.md:7 | "Every record schema is `additionalProperties: false`" | behavioral probe with the production registry over all 36 record schemas; 2 accept unknown root keys | **FINDING 1** |
| changing-contracts.md:8 | "canonical records carry no per-record version" | no record-schema root carries a record-format version; only content fields (schema_version/plan_template_version inside master-planning-promotion); versioning lives in data-contract.yaml | HELD |
| changing-contracts.md:13-16 | data-contract.yaml records version + fingerprint over stored-record schemas; `make check` compares them | data-contract.yaml:14-15 (`contract_version: 61`, `record_schemas: 36`); Makefile `check:` → validate.py → Validator.check_data_contract → data_contract.check | HELD |
| changing-contracts.md:14-15 | capability payload schemas excluded — they live in a subdirectory | record_schemas() globs only `system/schema/*.schema.json`; payload schemas in `system/schema/requests/` and `system/schema/capabilities/` | HELD |
| changing-contracts.md:17 | `SCHEMA-CONTRACT-DRIFT` fires | derive/validation/contract.py:70 | HELD |
| changing-contracts.md:19-21 | `tests/fixtures/formats/v<N>/` frozen snapshots loaded against the *current* schemas | test_format_fixtures.py (FORMATS); formats README states "loads them against the **current** schemas" | HELD |
| changing-contracts.md:22-25 | migrations idempotent, dry-run by default, bounded to the last generation they understand | tools/migrations/README.md:11-13 lists exactly these three properties | HELD |
| changing-contracts.md:27-28 | `tools/schema_contract.py --bump --note "…"`, `--migration PATH` | `--help` shows --bump, --note, --migration | HELD |
| changing-contracts.md:29-30 | new fixture added to FORMATS in tests/test_format_fixtures.py | file exists; FORMATS defined there (glob + history pointers) | HELD |
| changing-contracts.md:32-35 | fixtures README: never edit or regenerate an existing fixture | tests/fixtures/formats/README.md:11 "**Never edit an existing fixture.**" | HELD |
| changing-contracts.md:40-43 | generated/manifest.json is the one published shape; manifest-contract.yaml declares version and exact key sets | manifest-contract.yaml: `contract_version: 15`, `top_level_keys`, `generated_keys`, `index_keys`, `forbidden_top_level_keys`; generated/ is a gitignored build artifact (absent in a fresh clone, as expected) | HELD |
| changing-contracts.md:51-52 | version "read from this file; `make contract` reports it" | Makefile `contract:` runs both tools; each no-arg mode prints the declared version | HELD |
| changing-contracts.md:54 | "`build_manifest` checks itself against that declaration on every build" | derive/projection/manifest.py:349 (`enforce_contract: bool = True`) and 460-461 (`enforce(payload, repo.root)`) | HELD |
| changing-contracts.md:57-58 | 2026-08-08: only the consumer declared the version; it broke, with `topics` | manifest-contract.yaml:19-23 records exactly this incident (topics, ADR-009, UI CI red); data-contract history v4 (topics) adopted 2026-08-08 | HELD |
| changing-contracts.md:60 | "When `MANIFEST-CONTRACT-DRIFT` fires:" | no code emits the name; gate raises ManifestContractError with prose | **FINDING 2** |
| changing-contracts.md:62-64 | `tools/manifest_contract.py --bump --note`; `--show` prints without changing | `--help` shows all three | HELD |
| changing-contracts.md:65-66 | UI mirror: `contracts/manifest-v<N>.lock.json`, `MANIFEST_CONTRACT_VERSION`, `ManifestV<N>`, fixture vault manifest — same change | UI clone at f7dbc1f: contracts/manifest-v15.lock.json; manifest.ts:17 `MANIFEST_CONTRACT_VERSION = 15`; fixture-vault/generated/manifest.json | HELD (and 15 == Core's declared version) |
| changing-contracts.md:70 | "Consumers declare an exact version and fail closed" | manifest.ts:171-173 throws `Unsupported manifest contract …; expected 15` on mismatch | HELD |

### system/developer/components/ (24 pages)

| document:line | claim | check | result |
|---|---|---|---|
| all 24 pages | headings, entry points, pinning tests, ADRs, invariant pins, one owner per module, owned globs match, Depends-on/Used-by blocks, 80-line limit | system_map.py mechanisms; tests/test_system_map.py passes on the pin incl. 13 negative controls | GUARD |
| operation-handlers.md:27-50 | 21 family modules (`_shared.py` … `synthesis.py`) with the listed responsibilities | `ls tools/learning_os/app/handlers/` — exactly those 21 + `__init__.py` exist; responsibilities consistent with page purposes and capability families | HELD (existence; responsibility text read against module docstrings spot-wise) |
| operation-pipeline.md:47-49 | admission lives in capabilities.yaml; `app/admission.py` constants `GESTURE_ALLOWLIST` and `UI_REVIEWED_ALLOWLIST` enforce it; the UI mirrors its gesture set and checks parity in its own contract check | admission.py:31,90 define both; UI `scripts/check-contract.mjs` cross-checks `UI_GESTURE_CAPABILITIES` against `capabilities.yaml` + `GESTURE_ALLOWLIST` (error messages at lines 183, 213-215) | HELD |
| projection.md:29 | "Projection changes remain producer-owned and must be mirrored in the UI contract lock in the same release" | Core manifest-contract v15; UI manifest-v15.lock.json + MANIFEST_CONTRACT_VERSION = 15 at the UI pin | HELD |
| loading.md:32-37 | loader expands references within the same module and unit, refusing missing/ambiguous routes and overlapping inherited/local fields; editing context exposes the compact shape with route definitions once; manifest keeps the complete expanded shape | domain/material_refs.py:58-98 `expand_map`: `unit_routes(source_map, module_id, unit_id)` scope; refusal at :85 ("missing or ambiguous"); :91 ("cannot also override inherited"); :101 `compact_map` for editing; data-contract v18 note corroborates "loaded records and manifest v9 remain fully expanded" | HELD |
| semantics.md:27-34 | evaluator registry in predicates.py; policy.py normalized decisions; lineage.py claim freshness; goals.py+scan.py proposal lifecycle; claim_status.py exact occurrences; claim_audits.py seeded pool/sample; tasks.py task IR; dossiers.py bounded context; changes.py library preflight | all named files exist; predicates.py:940 `evaluate`; policy.py docstring "a normalized verdict …, OPA-style"; changes.py contains admit/build_envelope/build_trusted_context (preflight-shaped); rest of files present with matching subject matter | HELD (role nouns matched to module content; not every internal re-derived) |
| transactions.md:32-49 | every canonical mutation passes through TransactionService; one bounded write set, artifact-level expected revisions, post-write validation, republish, exactly one append-only receipt under `operations/transactions/`; revision zero implicit; rollback before receipt durability; reconciliation settles uncertainty | transactions.py:7 (append-only receipt), :855 (`operations/transactions/{transaction_id}.yaml`), recovery-journal machinery (:156-362); revisions.py:61-62 `artifact_revision(...).get(artifact_id, 0)` | HELD |
| package-root.md:13 | `tools/learning_os/__init__.py::_declared_version` | guard-verified symbol | GUARD |
| ai-action-store/ai-delivery/backup/contracts/derived-store/diagnostics/domain/evidence/legacy-archive/masters-planning/materials/plan-gate/search/session-ledger/validation pages | owned paths, purposes | owned paths guard-verified; purposes consistent with the modules I read in those areas | GUARD/HELD |

## Counts requested by the task

1. **`tools/learning_os/` modules that CODEMAP never mentions: 223 of 223.**
   Rule: a module counts as mentioned when its file path
   (`tools/learning_os/…`) or import name (`learning_os.x.y`) appears anywhere
   in `system/developer/CODEMAP.md`. Not one does — CODEMAP names
   `tools/los.py` (not inside the package), `tools/README.md`,
   `pyproject.toml`, `tests/architecture/` and two ADRs. This is the
   documented design ("intentionally stable… not a function catalogue",
   CODEMAP.md:65-66); the guard guarantees the missing coverage differently
   (every module has exactly one owning component page). Probe:
   `probes/probe_counts.py`, log `logs/counts.log`.
2. **Components whose page names no test: 8 of 24** — `ai-action-store`,
   `cli-adapter`, `derived-store`, `learner-derivations`, `operation-handlers`,
   `operation-pipeline`, `package-root`, `plan-gate`. Rule: the page
   identifier appears in no file under `tests/**/*.py`. Their *code* is tested
   (each page's Pinning-tests entry is guard-checked and exists — e.g.
   operation-pipeline's code is pinned by `tests/test_ops_pipeline.py`); what
   no test names is the page itself. Per ADR-017 decision 5 this is a count
   (absence), not a defect.

## Findings

### Finding 1 — `system/developer/changing-contracts.md:7`: "Every record schema is `additionalProperties: false`" is false for two record schemas

Two of the 36 schemas the data contract classifies as record schemas —
`system/schema/learning-plan.schema.json` and
`system/schema/material-comparison-defs.schema.json` — are definition-only
libraries with no root object constraint; an object with arbitrary unknown keys
validates against them. Failing test on the pin:
`tests/test_v1_record_schema_closure.py` (registered in `tests/group_map.py`
and `.github/shard-manifest.json`):

```
$ .venv/bin/python -m pytest tests/test_v1_record_schema_closure.py -q
1 failed in 0.06s
AssertionError: … accept unknown top-level keys: {'learning-plan.schema.json':
…, 'material-comparison-defs.schema.json': …}
```

Details, probe output, assessment (letter-vs-intent; both files are `$defs`
libraries no record is validated at the root of): `record-schema-closure-claim/finding.md`.

### Finding 2 — `system/developer/changing-contracts.md:60`: `MANIFEST-CONTRACT-DRIFT` is never emitted by any code

The document names the manifest drift failure as `MANIFEST-CONTRACT-DRIFT`
(parallel to the real `SCHEMA-CONTRACT-DRIFT`); the only non-document
occurrence is a comment in manifest-contract.yaml. The actual gate raises
`ManifestContractError` with prose that never contains the name. Failing test
on the pin: `tests/test_v1_manifest_drift_code.py` (registered likewise):

```
$ .venv/bin/python -m pytest tests/test_v1_manifest_drift_code.py -q
2 failed in 0.22s
```

Both failures print the actual refusal text. Details and assessment:
`manifest-drift-code/finding.md`.

## Coverage gaps

- The 13 `test_system_map.py` negative controls prove each guard check fires,
  but I did not re-derive every guard-verified value independently (e.g. I did
  not recompute all 24 × (entry points + pins + ADRs) by hand); I treated the
  guard's green run on the pin as verification for exactly the property classes
  it implements, which is what "read the guard first" was for.
- `semantics.md` role nouns (policy "normalized", lineage "freshness",
  goals/scan "proposal lifecycle") were matched to module docstrings and
  function shapes, not behaviorally exercised — that depth belongs to V3.
- `operation-handlers.md` responsibility column verified as existence +
  docstring consistency for all 21 modules; not one behavior per family.
- The UI-side claims (execFile, session/trace env, gesture parity, manifest
  lock) were checked by reading the UI clone at its pin, not by running node
  tests — running the UI suite is V2's method.

## Untested scope

- V2/V3/V4/V5 scopes (UI DOM, derived layer semantics, AI actions end-to-end,
  backup drill) — untouched here.
- `system/developer/components/` prose that makes no concrete claim (purpose
  one-liners' quality, invariant wording beyond the guard's pin requirement).
- `pyproject.toml` beyond the importlinter contracts; Makefile beyond the
  targets named in the docs; the full CI workflow definitions.
- I did not run the full suite, `make system-check`, or any test process in
  parallel (ground rules); only the two focused new test files were executed.

## ASSUMPTIONS

- "The sibling UI's internal documentation is phase 2" (DEVELOPER.md:44) is a
  roadmap statement — nothing in either repository can confirm or refute it.
- "These traces were checked against the code at the change's base"
  (FLOWS.md:2) is a process claim about the authors' diligence; I verified the
  traces myself at the pin, which is the strongest check available here.
- The campaign's "all 23 pages" is read as "all component pages"; 24 exist on
  the pin and all 24 were checked.
- For count 1, "CODEMAP never mentions" is measured as file path or import
  name appearing in CODEMAP.md; a looser reading (stem names inside prose,
  e.g. "adapters") would change the number but not the conclusion, since the
  generated index lists component identifiers, not modules.
- For count 2, "page names no test" is read as "no test names the page";
  the alternative parse ("a page whose Pinning-tests section names no test")
  yields 0 because the guard enforces a non-empty Pinning-tests section.
