# `learning_os` Core package

This package owns LearningOS semantics.  The sibling Obsidian UI presents the
state; it does not reimplement these rules.  The supported cross-process surface
is `tools/los.py` (or the installed `los` command), not an internal Python module.

Developer routing and the checked architecture map live in
`system/DEVELOPER.md` and `system/developer/CODEMAP.md`.

## Dependency direction

`adapters → app → derive → store → domain` (from `pyproject.toml`).
See `system/developer/C4.md` for generated component views.

The package has five subpackages.  Dependencies point inward from entrypoints to
semantic owners:

1. `tools/*.py` owns process arguments, printing, and exit status.  It may
   import `learning_os`; package modules do not reach outward to executable
   scripts as a source of business rules.
2. `adapters/` parses the CLI and shapes its input and output types.  It owns no
   semantic rule.
3. `app/` owns the operation surface: `registry.py` maps an operation name to
   its handler, `pipeline.py` runs one operation (admission, snapshot,
   transaction, receipt), and `handlers/` holds one module per operation
   family.  It coordinates the owners below; semantic rules stay with them.
4. `domain/` owns the semantic leaves — failures and refusals, identifiers,
   snapshot and vocabulary, markdown, plan import, route identity, unit notes.
   `store/` owns persistence and shapes: `store/contracts/` (versioned shapes,
   capability declarations, write scopes, migration lifecycle guards),
   `store/loading/` (canonical read models, one module per domain, with
   `store/loader.py` as the import site every tool already uses),
   `store/transactions.py` (the canonical write boundary), and the
   dependency-light leaves `store/evidence.py`, `store/revisions.py` and
   `store/fingerprint.py`.
5. `derive/` derives from one already-loaded snapshot: `derive/validation/`
   validates loaded state; `derive/projection/` and `derive/semantics/` project
   it.  Neither is a canonical writer, and read-only projection modules do not
   initialize the AI delivery service.
6. `app/ai_actions/` and `store/ai_actions/` are a bounded delivery workflow
   over the same contracts and transaction boundary, not a second Core.

Two visible compatibility surfaces remain.  The preserved Job-collapse and
route-identity planners live in `domain/plan_import.py` and
`domain/route_identity.py` and are imported by `app/_plan_gate.py`; new
features must not add further dependencies on completed migrations — extract a
current semantic service instead.  The path operations (`path.progress.update`,
`path.attachment.add`, `path.note.write`) remain reachable compatibility
surfaces registered in `app/handlers/learner.py`, and must not be removed
merely because newer unit-level flows exist.

## Entrypoints and boundaries

- Public machine/human API: `tools/los.py`; preserve command names, payloads,
  JSON, exit codes, optimistic-concurrency behavior, and receipts.
- Canonical validation and generation: `tools/validate.py` and
  `tools/generate.py`; `los validate`/`los generate` delegate to them.
- Package facade: `learning_os.store.loader`, `learning_os.derive.validation`, and
  `learning_os.derive.projection` retain established import surfaces for repository tools
  and tests.  Other modules are implementation details unless a contract says
  otherwise.
- Separate presentation helper: `tools/materials_index/` is not part of the
  semantic package and is reached only through `tools/build_materials_index.py`.
- Compatibility: existing path operations, legacy archive/Job capabilities, and
  the two preserved planners named above remain operationally visible.
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
retired migration modules. It also checks that the generated CLI bindings match
the declared request schemas. It deliberately does not import the package,
inspect canonical content, read materials, or claim that a reachable module
was exercised at runtime. A lazy edge must be declared under `TYPE_CHECKING`;
an intentionally retired module needs an explicit allowlist entry with its
reason. Broad directory exclusions are not acceptable.
