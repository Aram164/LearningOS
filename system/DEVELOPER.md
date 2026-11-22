# LearningOS developer entry

Use this route to change Core code, contracts, tests or documentation. To operate
learner records, enter through [OPERATOR.md](OPERATOR.md). This page assigns no
agent role and grants no additional write authority.

## Read in this order

1. Read OPERATOR's [hard boundaries](OPERATOR.md#hard-boundaries): learner
   ownership, review, canonical writes and external-repository boundaries still
   bind implementation work. Relevant permissions remain in
   [OPERATOR-POLICY.md](OPERATOR-POLICY.md); the short adapter does not relax them.
2. Read [CODEMAP](developer/CODEMAP.md), then the component page under
   `system/developer/components/` owning the change.
3. Read [C4](developer/C4.md) for runtime structure and [FLOWS](developer/FLOWS.md)
   for execution order. Static import arrows are not runtime calls.
4. Follow the task row below; read only the relevant contracts and ADRs next.

The corpus declares this entry as `developer_entrypoint`. Audience selects the
reading route; authority and status determine what binds. An informative or
historical page gains no authority by being useful to a developer.

## How do I change it?

| Task | Owning starting point | Verification |
|---|---|---|
| Add/change a CLI verb or capability | `system/schema/requests/`, `system/contracts/capabilities.yaml`, `tools/learning_os/app/registry.py`, then [cli-adapter](developer/components/cli-adapter.md), [operation-pipeline](developer/components/operation-pipeline.md) and [operation-handlers](developer/components/operation-handlers.md) | `.venv/bin/python tools/generate_capability_schemas.py --check`, `.venv/bin/python tools/doc_blocks.py --check`, `make code-check`, and `tests/test_cli.py`, `tests/test_capability_dispatch.py`, `tests/test_ops_pipeline.py` |
| Change stored records or the published manifest | [Changing contracts](developer/changing-contracts.md), `system/contracts/data-contract.yaml`, `system/contracts/manifest-contract.yaml`, [loading](developer/components/loading.md) and [projection](developer/components/projection.md) | `make contract`, `tests/test_format_fixtures.py`, `tests/test_projection_fidelity.py`, `make test-paired` and sibling `npm --prefix ../obsidian-ui run contract:check` |
| Change material resolution, search or reading memory | [materials](developer/components/materials.md) (`tools/learning_os/store/materials/`), [search](developer/components/search.md), `system/schema/material-*.schema.json`, `tools/study_launch.py` and `tools/learning_os/adapters/study_broker.py` | `tests/test_material_span.py`, `tests/test_material_search.py`, `tests/test_material_reading_cards.py`, `tests/test_study_broker.py`, `tests/test_study_launch.py` |
| Add/change a validation rule | [validation](developer/components/validation.md) (`tools/learning_os/derive/validation/`), `system/VALIDATION.md`, `operations/validation-warning-baseline.yaml`, contract register if declaring a contract | `make check`, `make warnings`, and focused rule/refusal tests (`tests/test_validation.py`, `tests/test_warning_baseline.py`) |
| Add/change a system document or procedure transcript | `system/contracts/normative-corpus.yaml`, `system/contracts/task-scope.yaml`, `system/procedures/INDEX.yaml` and [contracts](developer/components/contracts.md) | `.venv/bin/python tools/doc_blocks.py --check`, `tests/test_normative_corpus.py`, `tests/test_procedures.py` (`.venv/bin/scrut test system/procedures/<name>.md`) |
| Add/split a package module | owning component page under `system/developer/components/`, `tools/learning_os/README.md`, `pyproject.toml` layer contracts | `.venv/bin/python tools/system_map.py --check`, `make code-check`, `.venv/bin/lint-imports --no-cache`, `tests/test_arch_layers.py` |
| Add an executable tool | `tools/code_reachability.py` entry points, `tools/README.md`, `build_parser()` | `make code-check`, `tests/test_code_reachability.py`, `tests/test_tool_entrypoint_contract.py` |
| Add a test file | `tests/group_map.py`, `tests/GROUPS.md` and `.github/shard-manifest.json` | `tests/test_test_groups.py`, `tests/test_workflows.py` |
| Run development and release gates | `Makefile`, `tests/architecture/`, [changing contracts](developer/changing-contracts.md) | focused pytest file or `make test-group G=<area>`, `make commit-check` locally; upstream GitHub Actions `validate` (`.github/workflows/validate.yml`), `UI CI` (`../obsidian-ui/.github/workflows/ui-ci.yml`) and exact-SHA `release-pair` (`.github/workflows/release-pair.yml`) close the change |
| Plan an architecture or contract change | `system/ARCHITECTURE.md`, the owning ADR in `system/adr/`, and `system/contracts/`. An open point in `system/CRITIQUE-POINTS.md` is acted on only on Aram's word. | a plan reviewed against the workspace `AGENTS.md` at the `semestercontext/` root, plus an ADR when a binding contract changes |

## Before calling a change complete

Validate with zero errors and no new warning signature (`make check && make warnings`).
Preserve the public `tools/los.py` CLI command names, request/response schemas,
exit codes (`0` ok, `1` validation error, `2` usage/refusal, `3` concurrency
conflict), snapshot and artifact-revision guards, append-only receipts under
`operations/transactions/`, established package facades (`learning_os.store.loader`,
`learning_os.derive.validation`, `learning_os.derive.projection`), and registered
compatibility operations (`path.*`, legacy archive, route-identity planner; see
`tools/learning_os/README.md`). Exercise write paths against synthetic fixtures
(`mini_repo`, `rich_world`) or an isolated disposable worktree — never against live
learner records. If `system/contracts/*` or `system/schema/*` content changed,
re-record scenario expectations (`LOS_RECORD_SCENARIOS=1`) and `tests/architecture/engine-baseline.json` (`tests/test_arch_engine_neutrality.py`) last (see
[changing contracts](developer/changing-contracts.md#scenario-recordings-pin-contract-content--re-record-last)).

Compare the generated system map and tree; run the owning tests and existing
architecture gates. Keep stored-record and manifest changes under their own
contracts. Generated dependency blocks come from `tools/system_map.py --write`;
compare them with `tools/system_map.py --check`. The map check is a development
gate, not a learner write gate. Its symbols prove names exist, not that a flow has
executed.

For sibling Obsidian UI implementation work, start at `../obsidian-ui/AGENTS.md`
and `../obsidian-ui/ARCHITECTURE.md`. Core describes its public consumer boundary
here without becoming the owner of UI implementation rules.
