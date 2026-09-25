---
id: note-hash-join-vs-sort-merge
type: note
title: Hash join versus sort-merge join
created: 2026-05-28
role: synthesis
state: evolving
authorship: user
concepts:
- concept-join-algorithms
sources:
- source-garcia-molina-db
---

**Hash join**: build a hash table on the smaller input (build side), then
stream the larger input (probe side) and look up each key. Cost O(n + m);
needs the build side in memory, otherwise partition both inputs by hash into
buckets that fit (Grace hash join).

**Sort-merge join**: sort both inputs on the key, then merge. O(n log n + m log
m), but nothing extra if the inputs are already sorted, and the output comes
out sorted.

**Nested loops** only for tiny inputs or with an index on the inner side.

My summary for the exam: hash join is always O(n + m), so it wins whenever
there is no sort order to exploit.

## Correction (2026-09-29) — the exam summary above is wrong as stated

Recorded by the operator from my own measurement (working note of
stage-df-joins-01-strategies); the summary line above is kept as I wrote it.

Joining 50M events with users on user_id, where one key (user_id = 0) held 40%
of all events: the partition for that key (~20M rows) did not fit the memory
budget, spilled and was re-partitioned — "but repartitioning by hash cannot
split a single key." 11 min vs 90 s after joining key 0 separately.

"So a hash join is O(n + m) only if the build partitions fit in memory and keys
are spread out. With one giant key it degrades badly."
