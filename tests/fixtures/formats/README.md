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

`v2` (adopted 2026-08-08) is `v1` plus resource-level `scope_triage` on study-map
stage resources. Its demo stage deliberately carries one resource of each rank —
`required-now`, `helpful-now`, `deferred`, `reference-only` — **and one with no
rank at all**, because unranked is what every v1 record carries and the loader
must keep accepting it. A v2 fixture that ranked everything would stop proving
the field is optional.

`v3` (adopted 2026-08-08) is `v2` plus resource identity: an optional stable `id`
on stage resources, and an optional `resource_id` on `source_feedback`. The demo
stage carries **two resources with ids and two without**, and three feedback
entries: one narrowed to `§1`, one narrowed to `Appendix A` with a *contradictory*
verdict, and one plain source-level entry with no `resource_id`. The
contradictory pair is the point — under v1/v2 both judgments collapsed onto
`source-demo-book` and could not be told apart, which is the gap v3 exists to
close. The id-less resources and the source-level entry keep proving the old
shape still loads.

`v4` (adopted 2026-08-08) is `v3` plus the optional source `topics` facet over
the closed vocabulary in `sources/topics.yaml`. The field remains optional so
older source records continue to load unchanged.

`v5` (adopted 2026-08-12) is `v4` plus an optional unit `knowledge_map` and a
rich module source route. Its demo lecture declares two linked knowledge nodes,
and its book route states format, lecture-specific angle, covered nodes, depth,
scope, and exact locator. The v1–v4 string routes remain frozen and valid,
proving the redesign is additive rather than a forced migration.

`v6` (adopted 2026-08-15) adds operator-drafted note authorship, a structured
module drop record, and richer source-route formats/depth/scope. All three are
optional additions; the fixture deliberately exercises them while older
fixtures remain valid.

`v7` (adopted 2026-08-19) adds producer-owned schemas for the quarantined Job
dashboard and structured Job plans. Those records live outside the canonical
data tree, so the frozen canonical fixture is byte-identical to `v6`; that is
the compatibility claim being recorded, not a regenerated fixture.

The project family is the only one whose records already carry their own
`schema_version`; everything else is versioned collectively by
`system/contracts/data-contract.yaml`.
