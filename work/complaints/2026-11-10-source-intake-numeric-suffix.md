# Source intake admits a numeric suffix that blocks the next write

The source-intake preflight accepted a new source ID ending in `-3` without an existing unsuffixed counterpart. The operator reviewed and applied that intake through the gateway. Receipt `transaction-20261110-165202-001` records the successful write.

The next module plan import refused with `NEW-OR-GROWN-WARNING: ID-SUFFIX` in `sources/registry/software.yaml`. Live validation found zero errors and the new warning. Source intake correction and source record revision preserve the existing ID, so neither can remove this warning.

To reproduce on a fixture, prepare one metadata intake row whose unused ID ends in a one-digit numeric suffix and whose unsuffixed counterpart is absent. Run `source-intake --check`, submit the reviewed envelope, then run the warning-baseline check. The expected result is refusal before the first write. The observed result at Core `d7ccce7` was a committed intake followed by a failing warning gate.

Investigate checking the same collision-only suffix rule against the staged registry before an intake is accepted. An invalid row should leave registry bytes and transaction history unchanged. A genuine collision and a nonnumeric ID should still be accepted.
