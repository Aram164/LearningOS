# Frozen format fixtures

Each `v<N>/` directory is a snapshot of what this repository actually wrote when
the data contract was at version `<N>`. `tests/test_format_fixtures.py` loads
them against the **current** schemas, which is the one question no other test in
the suite can ask: every other test builds its input with today's code, so it can
only prove the system is self-consistent today.

## Three rules

**Never edit an existing fixture.** If a schema change breaks `v1`, that is the
fixture doing its job. Editing it to pass would erase the only record of what the
old format looked like, and with it the ability to write a migration.

**Never regenerate them from current code.** A fixture that can be rebuilt by a
script silently tracks every schema change and can therefore never fail. These
were materialised once, by hand, and are static from then on.

**Data only — no `system/`.** The schemas and the data contract come from the
live tree at test time. A fixture carrying its own schemas would validate old
data against old rules and pass forever.

## When a schema change breaks a fixture

1. Decide whether existing data is still valid. The failing test names the field.
2. If it is not, write the migration under `tools/migrations/`.
3. `python tools/schema_contract.py --bump --note "…" --migration tools/migrations/…`
4. Freeze the new shape as a **new** directory, `v<N+1>/`, and add it to
   `FORMATS` in `tests/test_format_fixtures.py`.

## Coverage

`v1` (adopted 2026-08-07, the v3 cutover format) covers: programs, modules,
module source maps, units, study maps, stage notes, the resume pointer, notes,
concepts, concept relations, sources, the modules registry, coordination,
workspaces, and projects (registry, aliases, relations).

The project family is the only one whose records already carry their own
`schema_version`; everything else is versioned collectively by
`system/contracts/data-contract.yaml`.
