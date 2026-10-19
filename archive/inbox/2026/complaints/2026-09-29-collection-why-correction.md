# Source attachment left a contradictory collection note

**Observed:** 2026-09-29, after attaching the Grinstead PDF to its source record.

## Where the friction appeared

`source.record.revise` intentionally leaves `sources/collections/math-bookshelf.yaml` alone. Its Grinstead entry still said the download had never landed after the source record and local material were correct. No collection-entry revision capability is declared, so I corrected that one `why` line as a separate authored file edit and rebuilt the views. The generated collection now names the local §4.1 reading and local URI.

## Why this is a complaint

The collection's one-line role and the source's evaluation have distinct owners; keeping them separate is sound. But a stale operational claim in the collection is easy to overlook, and the only available correction here bypassed the guarded receipt path used for the source record. This is a smaller but real completion gap.

## Smallest improvement to investigate

Make the source revision check report referring collection entries whose `why` contains an availability claim, without rewriting them automatically. If this recurs, add a narrow guarded `collection.entry.revise` action for one existing source entry and its `why` text. Keep source identity, order, group, unrelated entries, snapshot/revision guards, and receipts intact.
