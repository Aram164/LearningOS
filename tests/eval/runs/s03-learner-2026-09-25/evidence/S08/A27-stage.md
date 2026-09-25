
## 2026-09-29 — first measurement: skewed join (stage note draft)

Joined events (50M rows) with users on user_id. One key, user_id = 0
("anonymous"), holds 40% of all events.

Hash join: the partition containing key 0 is ~20M rows, does not fit the
memory budget, spills to disk and is re-partitioned — but repartitioning by
hash cannot split a single key. Runtime 11 min vs 90 s after filtering key 0
out and joining it separately.

So a hash join is O(n + m) only if the build partitions fit in memory and keys
are spread out. With one giant key it degrades badly.
