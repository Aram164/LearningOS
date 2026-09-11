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
| `code_reachability.py` | supported code gate | Static, code-only import/reachability report. |
| `schema_contract.py` | supported contract tool | Stored-record contract check and deliberate bump entrypoint. |
| `tree_contract.py` | supported contract tool | Renders ARCHITECTURE §3.2 from the tree contract; `--check` is what `make check` compares. |
| `manifest_contract.py` | supported contract tool | Published-manifest contract check and deliberate bump entrypoint. |
| `generate_capability_schemas.py` | supported maintenance | Rebuilds capability payload schemas after an approved CLI contract change. |
| `release_pair_receipt.py` | supported release tool | Produces or verifies exact Core/UI release evidence. |
| `stress_check.py` | supported deep gate | Explicit, expensive local stress checks; not a routine edit gate. |
| `codex_obsidian.py` | compatibility/security adapter | Fail-closed wrapper retained for the existing Agentic Copilot boundary. |
| `assemble_lecture_study_maps.py` | bounded authoring tool | Builds review drafts from already-authored maps; never a general canonical writer. |
| `build_materials_index.py` | bounded materials maintenance | Builds plain-text material catalogues; its HTML surface is retired unless explicitly requested. |
| `build_materials_tree.py` | bounded materials maintenance | Maintains the physical topic tree and `.flat` compatibility links. |
| `material_toc.py` | bounded authoring tool | Reads local material structure while authoring or checking exact locators. |
| `materials_manifest.py` | bounded integrity tool | Builds/verifies the external-material checksum inventory. |
| `ingest_transcript.py` | bounded materials maintenance | Fetches third-party video captions into the managed materials tree as timestamp-addressable transcripts; writes only under `LearningOS/materials/`, never canonical state. |
| `refresh_amls_fixture.py` | bounded fixture maintenance | Refreshes the checked-in AMLS paper inventory when its external source changes. |
| `legacy_exit_review.py` | read-only diagnostic | Reviews the frozen legacy tree without moving or deleting it. |
| `plan_write_audit.py` | read-only diagnostic | Reports plan changes without same-commit gateway receipts. |
| `lift_angle_out_of_locator.py` | compatibility repair | Bounded repair for the former fused locator/angle representation. |
| `normalise_material_uris.py` | compatibility repair | Bounded conversion from former physical-path material URIs to ID-based URIs. |

The `materials_index/` package is private implementation for
`build_materials_index.py`.  The `learning_os/` package structure and allowed
dependency direction are documented in `learning_os/README.md`.

## Migration status

`tools/migrations/` is preserved executable evidence.  A completed migration is
not an alternative writer for current records.  Unless noted as a compatibility
planner below, its apply path is retired by
`learning_os.contracts.migration_lifecycle` because the current stored-record
contract is newer than the last generation it understands.

| Migration | Status at data-contract v14 | Current relationship |
|---|---|---|
| `curriculum_v2.py` | retired after v0 | Historical module-first migration and fixture evidence. |
| `library_taxonomy_v1.py` | retired after v1 | Historical taxonomy migration. |
| `projects_v1.py` | retired after v0 | Historical project migration/rollback evidence. |
| `registry_partition_v1.py` | retired after v1 | Historical source-registry partition migration. |
| `standardize_job_plans_v1.py` | retired after v10 | Historical Job plan standardization. |
| `standardize_plan_template_v10.py` | retired after v10 | Historical plan-template standardization. |
| `route_identity_v13.py` | apply retired after v13; compatibility planner retained | The public compatibility command still imports its deterministic planner and fails closed on current apply. |
| `job_quarantine_collapse.py` | compatibility planner; direct apply always refused | The gateway-bound legacy Job capability reuses its plan and before-image verification. |

When the current contract needs a data rewrite, add a new migration with a new
identifier and supported-through declaration.  Do not revive or broaden a
retired one.
