# Test area groups

A change in one area should rerun only that area's tests. The current file
inventory and group membership are defined in
[`group_map.py`](group_map.py), applied as pytest markers at collection time by
[`conftest.py`](conftest.py) (no per-file marker edits), and registered in the
pytest config in [`pyproject.toml`](../pyproject.toml).
Use `pytest --collect-only -q` for the current test count; gate timings are
recorded with each run instead of maintained as a second inventory here.

## The groups

| Group | Covers |
|---|---|
| `studyplan` | curriculum, study maps, routes, units, plan revisions, promotion |
| `materials` | materials farm, attachments, slices, summaries, ingestion |
| `synthesis` | semantics, synthesis, dossiers, goals, runtime, operator questions |
| `generation` | generation, projections, views, derived state, search index, Garden |
| `contracts` | contracts, manifest, normative corpus, tree contract, UI contract mirror |
| `gateway` | gateways, CLI, capabilities, transactions, recovery, operations, diagnostics |
| `validation` | validation, hygiene, perimeter, audits, architecture guards |
| `migrations` | migrations and multi-year format compatibility |

A test file belongs to the subsystem it pins, not the harness it uses:
CLI-driven write-path tests are `gateway`, while CLI-driven plan, material or
dossier tests stay with their area. The `contracts` group includes the UI
contract mirror (`test_contract_differential`, `test_release_pair_receipt`);
the paired recovery driver (`test_ui_gateway_recovery`) is `gateway`.

## Running

```sh
make test-group G=gateway        # one area
pytest -m "gateway or contracts"  # several areas
pytest -m "not full_repo"         # make test-fast (unchanged)
make test                        # the full suite — still the gate
```

`make system-check` and CI always run the full suite. Groups minimise reruns
during development; they never replace the gate.

## Affected mapping

```sh
make test-affected [BASE=main]   # groups touched by this branch
python tools/affected_tests.py --files tools/los.py  # explicit paths
python tools/affected_tests.py --files tools/los.py --groups  # names only
```

`tools/affected_tests.py` maps changed repo-relative paths to groups via the
`PATH_RULES` table in `group_map.py`: a changed test file selects its own
group; changed production code selects its area (plus `gateway` when the area
has CLI surface); **a change to shared machinery — `conftest.py`, test
helpers, the loader, rules, generator framework, transactions, contracts,
schemas, canonical data — selects every group**, as does any unknown path.
The mapping fails closed by design: when in doubt it reruns more, never less.

Sibling UI changes (outside this repository) are not visible to the script:
after a UI change rerun `make test-paired` (the `paired` marker: every Core
test that reads the live sibling checkout), and the release still goes
through the full paired `make system-check`. The pre-push gate runs
`test-paired` itself when Core is unchanged against the last stamped pair.

## Adding a test file

Add the filename to exactly one group in `group_map.py`. Collection fails with
an explicit error if a `test_*.py` file is ungrouped, grouped twice, or
grouped but missing — the map cannot drift silently.

## Shared `full_repo` snapshots

Several `full_repo` tests used to each pay a full load, validation, or
generation of the checked-in tree. `conftest.py` now builds each once per
session (`real_repo`, `real_issues`, `real_generated`, `real_manifest`) and
the live-tree tests share them. This is sound because the suite never mutates
the real tree and the loader/validator/generators do not mutate the loaded
object; every assertion is unchanged, only the recomputation is gone.
