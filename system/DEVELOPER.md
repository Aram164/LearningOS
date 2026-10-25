# LearningOS developer entry

Use this route to change Core code, contracts, tests or documentation. To operate
learner records, enter through [OPERATOR.md](OPERATOR.md). This page assigns no
agent role and grants no additional write authority.

## Read in this order

1. Read OPERATOR's [hard boundaries](OPERATOR.md#hard-boundaries): learner
   ownership, review, canonical writes and external-repository boundaries still
   bind implementation work. Relevant permissions remain in
   [OPERATOR-POLICY.md](OPERATOR-POLICY.md); the short adapter does not relax them.
2. Read [CODEMAP](developer/CODEMAP.md), then the component page owning the change.
3. Read [C4](developer/C4.md) for runtime structure and [FLOWS](developer/FLOWS.md)
   for execution order. Static import arrows are not runtime calls.
4. Follow the task row below; read only the relevant contracts and ADRs next.

The corpus declares this entry as `developer_entrypoint`. Audience selects the
reading route; authority and status determine what binds. An informative or
historical page gains no authority by being useful to a developer.

## How do I change it?

| Task | Owning starting point | Verification |
|---|---|---|
| Add/change a CLI verb or capability | `system/schema/requests/`, `system/contracts/capabilities.yaml`, then cli-adapter and operation-pipeline pages | request-schema generation check and CLI/gateway tests |
| Change stored records or the published manifest | [Changing contracts](developer/changing-contracts.md) | schema/manifest contract checks and paired consumer tests |
| Add a validation rule | validation page, `system/VALIDATION.md`, contract register if declaring a contract | focused rule and refusal tests |
| Add a system document | corpus index and schema; choose audience, authority and owner | corpus and doc-block/command checks |
| Add/split a package module | owning component page's paths and boundaries | system-map check, code-check and import-linter |
| Add an executable tool | `tools/code_reachability.py` entry points, `tools/README.md`, `build_parser()` | tool entry-point and reachability tests |
| Add a test file | `tests/group_map.py` and `.github/shard-manifest.json` | group/CI population checks |
| Run development gates | `Makefile`, `tests/architecture/`, [changing contracts](developer/changing-contracts.md) | focused tests, commit-check; full system-check upstream on the exact Core/UI pair |

## Before calling a change complete

Validate with zero errors and no new warning signature. Compare the generated
system map and tree; run the owning tests and existing architecture gates.
Keep stored-record and manifest changes under their own contracts. Generated
dependency blocks come from `tools/system_map.py --write`; compare them with
`tools/system_map.py --check`. The map check is a development gate, not a learner
write gate. Its symbols prove names exist, not that a flow has executed.

The sibling UI's internal documentation is phase 2. Core describes its public
consumer boundary here without becoming the owner of UI implementation rules.
