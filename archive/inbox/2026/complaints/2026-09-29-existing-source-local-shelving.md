# Shelving a downloaded copy of an existing source

**Observed:** 2026-09-29, while shelving the local Grinstead and Snell probability PDF for SaD L06–L08.

## Where the friction appeared

The book already had `source-grinstead-snell` in the source registry and five SaD routes. The useful new fact was narrow: verified local PDF bytes now exist at `materials/mathematics/probability-statistics/grinstead-snell/grinstead.pdf`. The source intake operation does not update an existing source's `material` or evaluation. Adding that link therefore required a reviewed `module.plan.import` package, a module unit-order copy, six plan-coverage declarations, a separate audit under `work/active/`, a shadow preflight, and a transaction against the SaD module. The [receipt](../../../operations/transactions/transaction-20260929-043750-001.yaml) shows that only `sources/registry/mathematics.yaml` changed bytes; the module revision still advanced from 60 to 61.

The first local-route draft also tried to add `vault_path` to existing Grinstead routes. Its preflight required a replacement approved synthesis for L04. That refusal protected a real source-bound analysis, so the route change was removed from this shelving transaction. `make inventory` was also required to register the new PDF in the materials manifest; that is a useful integrity check.

After `make materials`, the physical subject shelf lists Grinstead in `materials/mathematics/probability-statistics/SOURCES.md`, but `materials/README.md` has no Grinstead entry despite reporting 96 local sources. The catalogue builder classifies current lowercase material folders (such as `mathematics/`) against older uppercase domain names (`Math`, `ML`), then renders only the latter. This is a separate discoverability defect in the plain text catalogue, not a failure of the source record or material resolver.

## Why this is a complaint

The full module plan contract was applied to a source-library fact with no teaching-plan or route change. Repeating the current unit order and declaring curriculum coverage did not add much safety for that specific edit. The snapshot guard, material resolution, review hash, validation, and receipt did add safety and should remain.

## Smallest improvement to investigate

Add a reviewed operation for attaching verified local material to an **existing** source record. It should accept the source ID, exact material URI and byte hash, load all unchanged source fields from the guarded snapshot, validate the material manifest and every existing reference, and write a normal atomic receipt. It must refuse to mutate route descriptions or source-bound syntheses; those continue through their existing guarded paths. Measure whether shelving this same book would then need fewer supplied fields and fewer preflight retries while preserving the same integrity checks.

For the catalogue, align its physical-folder classification with the current material taxonomy, then verify that a shelved local source appears once under its intended subject. Keep the count and unregistered-file logic consistent with that change.

## Follow-up — 2026-09-29

Commit `66d5bdc` added `source.record.revise` and repaired the catalogue grouping. The Grinstead attachment was completed through that capability in [transaction-20260929-062735-001.yaml](../../../operations/transactions/transaction-20260929-062735-001.yaml): the source and L04 dossier changed together, and all five SaD L04–L08 routes now resolve locally. The original complaint above describes the pre-fix workflow. The narrower friction observed during the completed run is recorded in the separate dossier-payload, useful-sections-shape, and collection-why notes linked from this folder's README.
