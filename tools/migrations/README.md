# Migration lifecycle

The per-file current/retired status is indexed in `tools/README.md`; this file
defines the lifecycle rule shared by every migration.

Name a new migration `<purpose>_v<generation>.py`, where `<generation>` matches
the `supported_through=` the migration declares to the lifecycle guard — the
last `data-contract.yaml` generation it understands. The filename suffix is the
readable form of that declaration, so keep the two equal
(`route_identity_v13.py` is the readable form done right). Keep the two
equal when you name a new migration.

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
YAML. `learning_os.store.contracts.migration_lifecycle` makes that state transition
mechanical: historical code stays available as evidence, but cannot mutate a
future live canon.
