# Changing Core contracts

Audience: developer. Existing schema and manifest change obligations live here.

## Changing a schema (the data contract)

Every record schema is `additionalProperties: false`, and canonical records carry
no per-record version. That is strict by design, but it means editing a schema
silently redefines what "valid" means for data already on disk — and years later
there is no way to ask "what format was this note written under, and what brings
it forward?"

`system/contracts/data-contract.yaml` records the current format version and a
fingerprint over `system/schema/*.schema.json` (the schemas governing stored
records; capability payload schemas are excluded — they validate requests, not
data at rest). `make check` compares them, so a schema edit cannot land without a
deliberate decision. When `SCHEMA-CONTRACT-DRIFT` fires:

1. **Does existing data still validate?** `tests/fixtures/formats/v<N>/` holds a
   frozen snapshot of each historical format and is loaded against the *current*
   schemas. If those tests still pass, the change is backward-compatible.
2. **If not, write the migration** under `tools/migrations/` — idempotent,
   dry-run by default, and bounded to the last data-contract generation it
   understands. A completed migration cannot be replayed on a later live
   format; write a new migration instead. See `tools/migrations/README.md`.
3. **Bump the contract:**
   `.venv/bin/python tools/schema_contract.py --bump --note "…"`
   If a migration is needed, add its path with `--migration PATH`.
4. **Freeze the new shape** as a *new* `tests/fixtures/formats/v<N+1>/` and add
   it to `FORMATS` in `tests/test_format_fixtures.py`.

Never edit or regenerate an existing fixture — see
`tests/fixtures/formats/README.md`. A fixture that tracks current code can never
fail, and one that gets edited to pass destroys the record of the format it was
supposed to preserve.

## Changing the manifest (the interface contract)

The data contract above governs what this repository *stores*. What it
*publishes* is a separate contract with separate consumers:
`generated/manifest.json` is the one shape every interface reads, and
`system/contracts/manifest-contract.yaml` declares its version and its exact key
sets.

They are versioned independently and deliberately: a record can gain an optional
field without changing the projection, and the projection can be reshaped
without touching a single stored record.

| what | contract | version owner |
|---|---|---|
| canonical record format | `system/contracts/data-contract.yaml` | read from this file; `make contract` reports it |
| published manifest shape | `system/contracts/manifest-contract.yaml` | read from this file; `make contract` reports it |

`build_manifest` checks itself against that declaration on every build, so a
change to the published shape fails here rather than downstream. That is the
point: until 2026-08-08 only the consumer declared the version (in the Obsidian
UI's lock file), so Core could add a top-level key, pass its own tests, push —
and break the other repository. It happened, with `topics`.

When `MANIFEST-CONTRACT-DRIFT` fires:

1. **Bump:** `.venv/bin/python tools/manifest_contract.py --bump --note "…"` — it rebuilds
   with enforcement off, adopts the shape actually produced, and records the
   history entry. `--show` prints the current shape without changing anything.
2. **Mirror into the UI in the same change** — `contracts/manifest-v<N>.lock.json`,
   `MANIFEST_CONTRACT_VERSION`, `ManifestV<N>`, and the fixture vault manifest.
   Core and the UI release together; a bump that lands alone is the exact bug
   this contract exists to prevent.

Additive still bumps. Consumers declare an exact version and fail closed, so
"only added a key" is not "invisible".

