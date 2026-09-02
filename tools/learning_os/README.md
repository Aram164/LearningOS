# `learning_os` Core package

This package owns LearningOS semantics.  The sibling Obsidian UI presents the
state; it does not reimplement these rules.  The supported cross-process surface
is `tools/los.py` (or the installed `los` command), not an internal Python module.

## Dependency direction

```text
human / agent / Obsidian UI
            |
            v
tools/los.py and focused tools/*.py entrypoints
            |
            v
learning_os.commands          command parsing adapters and orchestration
       |          |
       v          v
domain services   contracts + transactions
       |          |
       +-----> loading/model, rules, and generated projections
```

Dependencies point inward from entrypoints to semantic owners:

1. `tools/*.py` owns process arguments, printing, and exit status.  It may
   import `learning_os`; package modules do not reach outward to executable
   scripts as a source of business rules.
2. `commands/` adapts the public CLI to domain services.  It may coordinate
   contracts, loading, transactions, and generated projections, but semantic
   rules stay in those owners rather than in parser callbacks.
3. `contracts/` owns versioned shapes, capability declarations, write scopes,
   and migration lifecycle guards.  Lower layers must not import `commands/`.
4. `loading/` and `loading/model.py` own canonical read models.  `loader.py` is
   the compatibility facade for existing callers.
5. `errors.py`, `revisions.py`, and `material_inventory.py` are dependency-light
   shared leaves. Projection, validation, and preserved planners use them
   without importing a write orchestrator or executable script.
6. `rules/` validates loaded state; `genout/` projects one already-loaded
   snapshot. Neither is a canonical writer, and read-only projection modules do
   not initialize the AI delivery service.
7. `transactions.py` is the canonical write boundary. Domain writers provide
   intended changes; they do not implement alternate ledgers or receipts.
8. `ai_actions/` is a bounded delivery workflow over the same contracts and
   transaction boundary, not a second Core. Its package facade is lazy so leaf
   readers do not pay for or cycle through the write service.

There are two visible compatibility exceptions.  `commands/vnext.py` imports
the preserved Job-collapse and route-identity planners from `tools/migrations/`
for existing public capabilities.  New features must not add further
dependencies on completed migrations; extract a current semantic service
instead.  `commands/path.py` and the stage-note/attachment commands remain
reachable compatibility surfaces and must not be removed merely because newer
unit-level flows exist.

## Entrypoints and boundaries

- Public machine/human API: `tools/los.py`; preserve command names, payloads,
  JSON, exit codes, optimistic-concurrency behavior, and receipts.
- Canonical validation and generation: `tools/validate.py` and
  `tools/generate.py`; `los validate`/`los generate` delegate to them.
- Package facade: `learning_os.loader`, `learning_os.rules`, and
  `learning_os.genout` retain established import surfaces for repository tools
  and tests.  Other modules are implementation details unless a contract says
  otherwise.
- Separate presentation helper: `tools/materials_index/` is not part of the
  semantic package and is reached only through `tools/build_materials_index.py`.
- Compatibility: existing path commands, legacy archive/Job capabilities, and
  the two migration planners named above remain operationally visible.
- Historical: completed migrations stay under `tools/migrations/`, guarded
  against replay on newer data contracts.  Their lifecycle index is
  `tools/README.md`.

## Version and dependencies

`pyproject.toml` is the single authority for package version, runtime
dependencies, and the `dev` extra.  `learning_os.__version__` reads that
declaration in a source checkout and falls back to package metadata in an
installed wheel.  `requirements-dev.txt` is only a compatibility redirect to
`.[dev]`; it must not duplicate dependency names or constraints.

## Static reachability gate

Run `make code-check` after adding, splitting, or retiring a module. The gate
has explicit executable roots, checks static reachability, rejects dependency
cycles and package-to-entrypoint imports, and keeps a reasoned allowlist for
retired migration modules. It deliberately does not import the package,
inspect canonical content, read materials, or claim that a reachable module
was exercised at runtime. A lazy edge must be declared under `TYPE_CHECKING`;
an intentionally retired module needs an explicit allowlist entry with its
reason. Broad directory exclusions are not acceptable.
