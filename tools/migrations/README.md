# Migration lifecycle

The per-file current/retired status is indexed in `tools/README.md`; this file
defines the lifecycle rule shared by every migration.

A migration is a bridge from one declared stored-record generation to the next.
It is not a permanent alternative writer for the live repository.

Every migration must therefore be:

- dry-run by default;
- explicit about the last `data-contract.yaml` generation it understands;
- refused when the repository has advanced beyond that generation;
- replayable against its frozen historical fixture or checkout;
- replaced by a new migration when a later record generation needs work.

This boundary exists because a once-idempotent migration can stop being
idempotent as schemas and ownership rules evolve. Re-running the old program on
new records can restore retired fields or defaults while still producing valid
YAML. `learning_os.contracts.migration_lifecycle` makes that state transition
mechanical: historical code stays available as evidence, but cannot mutate a
future live canon.
