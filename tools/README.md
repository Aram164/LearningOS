# Core tool lifecycle index

This directory contains executable code, not LearningOS content.  The table is
the first place to answer whether a script is a supported entrypoint, a bounded
maintenance tool, a compatibility surface, or retained history.  Do not infer
status from file age, and do not delete a file merely because normal execution
does not import it.

`make code-check` parses the Python import graph without importing LearningOS or
reading canonical records. It fails on an unclassified `tools/*.py` file, an
unreachable package module, a dependency cycle, or a package import back into
an executable entrypoint. Its result is static architecture evidence, not
runtime coverage; the exact roots and historical allowlist live in
`code_reachability.py`.

## Supported and bounded tools

| Tool | Lifecycle | Purpose |
|---|---|---|
| `los.py` | supported public interface | Stable human, agent, and UI CLI; the `los` package script points here. |
| `validate.py` | supported gate | Offline/online canonical validator. |
| `generate.py` | supported gate | Deterministic generated-view publisher. |
| `warning_baseline.py` | supported gate | No-new-warning policy. |
| `verify_plan_receipt.py` | supported gate | Receipt/projection check for one plan transaction (`make plan-check`). |
| `code_reachability.py` | supported code gate | Static, code-only import/reachability report. |
| `schema_contract.py` | supported contract tool | Stored-record contract check and deliberate bump entrypoint. |
| `system_map.py` | supported development gate | Checks module ownership, named references, layers and generated developer-map blocks; `--write` regenerates those blocks. Never a canonical validation rule. |
| `tree_contract.py` | supported contract tool | Renders ARCHITECTURE §3.2 from the tree contract; `--check` is what `make check` compares. |
| `doc_blocks.py` | supported contract tool | Checks or regenerates documentation counts, command names and procedure links from their metadata owners; validation blocks stale or malformed projections. |
| `manifest_contract.py` | supported contract tool | Published-manifest contract check and deliberate bump entrypoint. |
| `contract_bundle.py` | prototype contract tool | Side-by-side manifest contract bundler (Point-3 prototype); build/check only, never a canonical writer. |
| `generate_capability_schemas.py` | supported maintenance | Rebuilds capability payload schemas after an approved CLI contract change (`--check` compares instead of writing). |
| `release_pair_receipt.py` | supported release tool | Produces or verifies exact Core/UI release evidence. |
| `verified_pairs.py` | supported release tool | Advisory memo of pairs `make system-check` verified; the pre-push hook skips the full gate for an exact stamped pair. |
| `stress_check.py` | supported deep gate | Explicit, expensive local stress checks; not a routine edit gate. |
| `codex_obsidian.py` | compatibility/security adapter | Fail-closed wrapper retained for the existing Agentic Copilot boundary. |
| `assemble_lecture_study_maps.py` | bounded authoring tool | Builds review drafts from already-authored maps; never a general canonical writer. |
| `build_materials_index.py` | bounded materials maintenance | Builds plain-text material catalogues; its HTML surface is retired unless explicitly requested. |
| `build_materials_tree.py` | bounded materials maintenance | Maintains the physical topic tree and `.flat` compatibility links. Dry-run plan by default; acts only with `--apply`. |
| `material_text.py` | bounded authoring tool | Digest-keyed page-text cache for local materials; read cached pages instead of re-extracting. |
| `material_toc.py` | bounded authoring tool | Reads local material structure while authoring or checking exact locators. |
| `material_summarize.py` | bounded authoring tool | Admits reviewed chapter summaries; `--read --material PATH --pages START-END` returns one reusable summary with live source checks, explicit hit/missing/stale/refused status, and content integrity — serving a durable analysis note first when one binds the exact source and range. |
| `materials_manifest.py` | bounded integrity tool | Builds/verifies the external-material checksum inventory. |
| `move_map.py` | supported maintenance | Applies a module move map to files, imports and path-keyed text (OD9); `--check` plans, `--apply` moves. |
| `ingest_transcript.py` | bounded materials maintenance | Legacy caption import for already managed material; not the two-pass YouTube examination path, which uses Gemini Notebook on demand (WORKFLOWS §6a). Writes only under `LearningOS/materials/`, never canonical state. |
| `refresh_amls_fixture.py` | bounded fixture maintenance | Refreshes the checked-in AMLS paper inventory when its external source changes. |
| `legacy_exit_review.py` | read-only diagnostic | Reviews the frozen legacy tree without moving or deleting it. |
| `library_reconciliation.py` | read-only diagnostic | Occurrence-level reconciliation of the old resource lists against the source registry (two-pass source intake); reads only declared inputs and writes only inside its workspace, never canonical records. |
| `plan_write_audit.py` | read-only diagnostic | Reports commit co-occurrence of plan changes and newly added receipt documents across available Git refs; it does not prove per-write gateway provenance. |
| `normalise_material_uris.py` | compatibility repair | Bounded conversion from former physical-path material URIs to ID-based URIs. |
| `diagnostics_prune.py` | bounded maintenance | Prunes the disposable diagnostics trace store to its retention bound. |
| `affected_tests.py` | supported test tool | Maps changed files to test groups for `make test-affected`; a rerun minimizer, never a gate. |
| `seal_envelope.py` | bounded authoring tool | Seals one GatewayEnvelopeV2 from caller intent (WORKFLOWS §25c); reads the repo, writes nothing canonical. |
| `agent_run.py` | experimental operator runner | One call batches CLI steps over an explicitly selected data root. Log/gateway plans require a stable `session_id`; logs also require unique explicit retry keys. Presealed gateway files must bind the same session, and approved bytes are preserved. `on_error` defaults to `stop`, reporting skipped steps; `continue` keeps independent steps running. Dependent reads require a projection from a successful write at or after the latest required write. Missing/pending readiness and unknown snapshots refuse. Nonfinite output fails its step; summaries name `_missing_fields` under their UTF-8 byte budget. Optional typed preflight reuses the pinned validation cache and refuses every validation error. Cluster previews retain counts and a supported expansion. Bounded read sessions memoize eligible reads under manifest pins; `read_workers` (1-4, default 1) runs contiguous eligible read waves in isolated processes; `deadline_s` (default 120) stops admission; `report_max_bytes` bounds the whole report with a private full-report artifact on every run (`--report-dir` chooses its parent). `--expand-report PATH [--step ID]` verifies report and raw-output digests before expansion. No bulk learner decisions. |
| `capture_world.py` | supported contract tool | Captures one world (data, pins, observations, material inventory) for captured-world identity (SPEC §6). |
| `compare_world.py` | supported gate | Compares two revisions against one captured world; exits 0 on identity, 1 on difference (SPEC §6). |

The `materials_index/` package is private implementation for
`build_materials_index.py`.  The `learning_os/` package structure and allowed
dependency direction are documented in `learning_os/README.md`.

## Entrypoint contract

Every `tools/*.py` entrypoint parses arguments with `argparse` as its first
act: `--help` prints usage and exits 0, an unknown flag exits 2, both before
any write. The materials tree builder additionally defaults to a dry-run
plan and acts only with an explicit `--apply`, because the materials tree
has no git history to review a write against.
`tests/test_tool_entrypoint_contract.py` runs every entrypoint with `--help`
in a scratch copy and asserts exit 0 and no file changed.

## Migration status

`tools/migrations/` is preserved executable evidence.  A completed migration is
not an alternative writer for current records.  Unless noted as a compatibility
planner below, its apply path is retired by
`learning_os.store.contracts.migration_lifecycle` because the current stored-record
contract is newer than the last generation it understands.

| Migration | Status at data-contract v14 | Current relationship |
|---|---|---|
| `curriculum_v2.py` | retired after v0 | Historical module-first migration and fixture evidence. |
| `library_taxonomy_v1.py` | retired after v1 | Historical taxonomy migration. |
| `projects_v1.py` | retired after v0 | Historical project migration/rollback evidence. |
| `registry_partition_v1.py` | retired after v1 | Historical source-registry partition migration. |
| `lift_angle_out_of_locator.py` | retired after v12 | Historical un-fusing of locator and angle (3,885 study-map rows); `LOCATOR-ANGLE-FUSED` now refuses the defect. |
| `standardize_job_plans_v1.py` | retired after v10 | Historical Job plan standardization. |
| `standardize_plan_template_v10.py` | retired after v10 | Historical plan-template standardization. |
| `route_identity_v13.py` | apply retired after v13; compatibility planner retained | The public compatibility command still imports its deterministic planner and fails closed on current apply. |
| `job_quarantine_collapse.py` | compatibility planner; direct apply always refused | The gateway-bound legacy Job capability reuses its plan and before-image verification. |
| `summaries_to_notes_v1.py` | one-shot; direct operator execution through v35 | Freeze, map, and migrate legacy summary-cache entries to durable analysis notes via note.analysis.save; refuses changed inputs and retires by lifecycle after v35. |

When the current contract needs a data rewrite, add a new migration with a new
identifier and supported-through declaration.  Do not revive or broaden a
retired one.
