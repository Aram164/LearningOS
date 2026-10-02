# Valid evaluation shape rendered as the wrong reading sections

**Observed:** 2026-09-29, evaluating Grinstead §4.1 during the source revision.

## Where the friction appeared

`system/schema/sources.schema.json` allows each `evaluations[].useful_sections[]` object to have arbitrary string keys. I submitted one object with `locator` and `use`. The gateway validated and committed it, but `inspect source-grinstead-snell` displayed two separate entries: `section: locator` and `section: use`. The actual projection treats every key/value pair as an independent section. A second `source.record.revise` transaction corrected it to a one-key map; see [transaction-20260929-062902-001.yaml](../../../operations/transactions/transaction-20260929-062902-001.yaml). The source index now shows one correct §4.1 section.

## Why this is a complaint

The first request satisfied the declared schema and passed validation, yet learner-facing output was wrong. The second snapshot, check, approval envelope, transaction, and receipt added no semantic review; they repaired a mismatch between schema and projection.

## Smallest improvement to investigate

Require exactly one key/value pair per `useful_sections` object in the source schema and reject `locator`/`use` as pseudo-fields with a message showing the accepted mapping form. All currently loaded `useful_sections` entries have exactly one key, so this should not require data migration. Add a contract test that a valid evaluation projects one intended section and that a two-key entry fails before publication.
