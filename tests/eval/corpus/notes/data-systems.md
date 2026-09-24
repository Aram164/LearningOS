Durable notes — databases and data engineering.

=== note-relational-algebra-operators
domain: data-systems
title: Relational algebra operators
created: 2026-04-20
role: reference
state: evolving
authorship: user
concepts: [concept-relational-algebra]
sources: [source-tuh-dbsys-slides]
---
- σ_p(R) selection: keep rows satisfying p.
- π_A(R) projection: keep columns A (set semantics removes duplicates; SQL
  does not unless DISTINCT).
- R × S, R ⋈_θ S (theta join), natural join.
- ∪, −, ∩ for union-compatible relations; ρ renaming.
- Division R ÷ S for "for all" queries — the one everyone forgets.

SQL → algebra: FROM gives the product/join, WHERE the selection, SELECT the
projection. A query becomes an operator tree with base tables at the leaves.

=== note-algebraic-equivalences-pushdown
domain: data-systems
title: Algebraic equivalences and pushing selections down
created: 2026-05-06
role: synthesis
state: evolving
authorship: user
concepts: [concept-relational-algebra, concept-query-optimization]
sources: [source-tuh-dbsys-slides, source-garcia-molina-db]
---
Rewrite rules that keep the result identical but change the cost:

1. σ_{p∧q}(R) = σ_p(σ_q(R)) — split conjunctions.
2. σ_p(R ⋈ S) = σ_p(R) ⋈ S if p only mentions attributes of R.
3. π_A(R ⋈ S) = π_A(π_{A∪J}(R) ⋈ π_{A∪J}(S)) where J are the join attributes
   — drop unused columns early.
4. Joins are commutative and associative (with care about attribute names).

Heuristic from the lecture: push selections as far down the tree as possible,
then projections, then worry about join order. Filtering before a join shrinks
both inputs, and a join's cost grows with its input sizes.

Worked exam example: σ_{city='Havelberg'}(Customer ⋈ Orders) — moving the
selection onto Customer turned a 10⁶-row join into a 2·10³-row join.

=== note-selinger-join-ordering
domain: data-systems
title: System R join ordering
created: 2026-05-21
role: synthesis
state: evolving
authorship: user
concepts: [concept-query-optimization, concept-join-algorithms]
sources: [source-selinger-1979, source-tuh-dbsys-slides]
---
For n tables there are (2(n−1))!/(n−1)! join orders — hopeless to try them all
beyond a handful of tables.

What System R does (Selinger 1979):

1. For every single table, find the cheapest access path (scan or index).
2. For every pair of tables, the cheapest way to join them, built from the
   single-table results.
3. For every set of three, extend the best plans for its two-table subsets by
   one more table; keep only the cheapest plan per set.
4. … up to the set of all n tables.

It only considers left-deep trees (the right input is always a base table),
which keeps the search manageable and suits pipelining.

"Interesting orders": also keep a more expensive plan for a subset if it
produces rows sorted in a way a later merge join or ORDER BY can use.

Why keeping only the best plan per subset is safe: how the rest of the query
continues does not depend on how the subset was joined, only on its result
(and its sort order, hence interesting orders).

=== note-query-optimizer-cost-model
domain: data-systems
title: Cost models and selectivity
created: 2026-05-23
role: synthesis
state: evolving
authorship: user
concepts: [concept-cardinality-estimation, concept-query-optimization]
sources: [source-tuh-dbsys-slides, source-selinger-1979]
---
The optimizer needs the number of rows each operator produces to cost a plan.

Selectivity of a predicate = fraction of rows that pass it. With a histogram
on column a, sel(a = v) ≈ (rows in v's bucket / bucket width) / total rows.

For a conjunction the textbook rule is

    sel(p₁ ∧ p₂) = sel(p₁) · sel(p₂)

i.e. the optimizer behaves as if the two columns had nothing to do with each
other. For city = 'Havelberg' AND zip = '14712' this is badly wrong: the zip
code already determines the city, so the true selectivity is sel(zip), and the
product underestimates it by a factor of 1/sel(city).

Underestimates compound through joins; a plan that looks cheap for "10 rows"
is catastrophic for 100,000. Lecture: "estimation errors grow exponentially
with the number of joins".

Fixes mentioned: multi-column statistics, sampling, adaptive re-optimization.

=== note-hash-join-vs-sort-merge
domain: data-systems
title: Hash join versus sort-merge join
created: 2026-05-28
role: synthesis
state: evolving
authorship: user
concepts: [concept-join-algorithms]
sources: [source-garcia-molina-db]
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

=== note-external-merge-sort
domain: data-systems
title: External merge sort
created: 2026-05-30
role: derivation
state: evolving
authorship: user
concepts: [concept-external-sorting]
sources: [source-garcia-molina-db]
---
Sorting N pages with B buffer pages when N ≫ B:

1. Pass 0: read B pages at a time, sort in memory, write out ⌈N/B⌉ sorted runs.
2. Merge passes: merge B−1 runs at a time into longer runs.

Number of passes = 1 + ⌈log_{B−1} ⌈N/B⌉⌉; every pass reads and writes all N
pages. With B = 100 and N = 10⁶ pages: 1 + ⌈log₉₉ 10⁴⌉ = 3 passes.

Replacement selection in pass 0 produces runs of about 2B on average.

=== note-db-normalization-3nf
domain: data-systems
title: Normal forms (up to BCNF)
created: 2026-04-27
role: reference
state: evolving
authorship: user
concepts: [concept-db-normalization]
sources: [source-tuh-dbsys-slides]
---
Functional dependency X → Y: rows equal on X are equal on Y.

- 1NF: atomic attribute values.
- 2NF: no non-key attribute depends on part of a composite key.
- 3NF: for every FD X → A, X is a superkey or A is part of some key.
- BCNF: for every non-trivial FD X → Y, X is a superkey.

Normalizing = decomposing a table into smaller ones to remove redundancy and
update anomalies. Decompositions should be lossless-join (always achievable
for BCNF) and dependency-preserving (guaranteed only for 3NF synthesis).

Example: Enrolment(student, course, lecturer) with course → lecturer and
{student, lecturer} → course: 3NF but not BCNF.

=== note-acid-consistency
domain: data-systems
title: ACID — and what the C means
created: 2026-06-04
role: synthesis
state: evolving
authorship: user
concepts: [concept-transactions-acid]
sources: [source-tuh-dbsys-slides, source-garcia-molina-db]
---
- Atomicity: all of a transaction's effects or none.
- Consistency: a transaction takes the database from one state that satisfies
  the integrity constraints to another one that does.
- Isolation: concurrent transactions behave as if run one after another
  (serializability, at the strictest level).
- Durability: once committed, survives crashes.

The C is the odd one out: it is mostly the *application's* job (the
constraints are what the application says they are); the database only
enforces the declared ones (keys, foreign keys, CHECK). A and I and D are the
database's machinery that makes keeping C possible.

=== note-cap-consistency-linearizability
domain: data-systems
title: The C in CAP is not the C in ACID
created: 2026-07-22
role: synthesis
state: evolving
authorship: user
concepts: [concept-cap-theorem, concept-transactions-acid]
sources: [source-kleppmann-ddia]
---
Kleppmann is blunt about it: the word "consistency" is used for completely
different things.

CAP consistency = linearizability: every read sees the most recent completed
write, as if there were a single copy of the data. It is a property of
replicated systems.

ACID consistency = invariants hold (see the June note). Nothing to do with
replicas.

CAP itself, stated carefully: when a network partition happens, a replicated
system must choose between linearizability and availability. When there is no
partition, nothing forces the choice. Kleppmann thinks the theorem is less
useful than its fame suggests.

Also "eventual consistency", "consistent hashing", "read-your-writes
consistency" — each a different idea again.

=== note-two-phase-locking-deadlocks
domain: data-systems
title: Two-phase locking and deadlocks
created: 2026-06-07
role: synthesis
state: evolving
authorship: user
concepts: [concept-two-phase-locking, concept-transactions-acid]
sources: [source-tuh-dbsys-slides, source-garcia-molina-db]
---
2PL: a transaction acquires locks in a growing phase and releases them in a
shrinking phase; after its first release it may not acquire any lock.
Guarantees conflict-serializable schedules. Strict 2PL holds write locks until
commit, which avoids cascading aborts.

2PL does *not* prevent deadlocks: T1 locks row A then wants B; T2 locks B then
wants A. The database keeps a waits-for graph (edge Ti → Tj if Ti waits for a
lock Tj holds) and checks it for cycles, periodically or on every wait. A cycle
= deadlock; abort one transaction in the cycle (the victim — youngest, or the
one with the least work done) and let the other proceed.

Alternatives: wait-die / wound-wait with timestamps, or plain timeouts.

=== note-write-ahead-logging-aries
domain: data-systems
title: Write-ahead logging and ARIES recovery
created: 2026-06-11
role: synthesis
state: evolving
authorship: user
concepts: [concept-write-ahead-logging, concept-transactions-acid]
sources: [source-tuh-dbsys-slides, source-garcia-molina-db, source-mohan-aries-1992]
---
Rule: the log record describing a change must reach stable storage *before*
the changed data page is written (write-ahead), and all of a transaction's log
records must be on disk before its commit is acknowledged.

Log records carry an LSN; every page remembers the LSN of the last change
applied to it (pageLSN), so recovery can tell whether a logged change is
already on the page.

ARIES recovery after a crash, three passes:
1. Analysis — from the last checkpoint, rebuild which transactions were active
   and which pages were dirty.
2. Redo — repeat history: reapply every logged change whose page does not
   have it yet, including changes of transactions that will be undone.
3. Undo — roll back the losers in reverse order, writing compensation log
   records so a crash during undo is also recoverable.

Steal/no-force: pages may be written before commit (needs undo), and need not
be written at commit (needs redo). The log makes both safe.

=== note-buffer-pool-replacement
domain: data-systems
title: Buffer pool management
created: 2026-06-14
role: synthesis
state: evolving
authorship: user
concepts: [concept-buffer-management]
sources: [source-garcia-molina-db]
---
The buffer pool keeps disk pages in memory frames; a page table maps page ids
to frames; each frame has a pin count and a dirty bit.

When a frame is needed and none is free, pick an unpinned victim; write it
back first if dirty.

Plain LRU fails on sequential scans: one scan of a large table pushes every
useful page out ("sequential flooding"). Remedies: LRU-K (evict by the time of
the K-th most recent access), putting scan pages at the cold end, or a
separate small ring buffer for scans (what PostgreSQL does).

The database knows its access pattern (a scan, an index lookup) better than
the OS does, which is why databases manage this themselves and often bypass
the OS page cache.

=== note-lsm-trees
domain: data-systems
title: LSM trees
created: 2026-07-18
role: synthesis
state: evolving
authorship: user
concepts: [concept-lsm-trees]
sources: [source-kleppmann-ddia]
---
Writes go to an in-memory sorted structure (memtable) and a log for
durability. When the memtable is full it is written out as an immutable
sorted file (SSTable). Background compaction merges SSTables and drops
overwritten or deleted keys.

Reads check the memtable, then SSTables from newest to oldest. To avoid
reading every file for a key that is not there, each SSTable has a small
in-memory filter that answers "definitely not here" or "maybe here".

Trade-off vs B-trees: much higher write throughput (sequential writes only),
but reads may touch several files and compaction competes for disk bandwidth.
Used in LevelDB, RocksDB, Cassandra.

=== note-b-plus-tree-indexes
domain: data-systems
title: B+ tree indexes
created: 2026-05-25
role: synthesis
state: evolving
authorship: user
concepts: [concept-b-plus-trees]
sources: [source-garcia-molina-db]
---
All keys in the leaves; inner nodes only route. Leaves are linked, so a range
scan finds the first key and walks right.

Fanout ~ page size / (key + pointer) ≈ 4096 / 16 = 256; three levels already
index 256³ ≈ 16 million keys, and the top two levels are almost always cached,
so a lookup costs about one disk read.

Insert: split a full leaf and push the middle key up; splits can cascade to
the root, which is the only way the tree grows taller.

Clustered index: the table itself is stored in index order; only one per
table.

=== note-lazy-evaluation-query-plans
domain: data-systems
title: Lazy frames build a plan first
created: 2026-08-05
role: synthesis
state: evolving
authorship: user
concepts: [concept-lazy-evaluation, concept-query-optimization]
sources: [source-polars-guide]
contexts: [workspace-dataframe-skill]
---
Eager dataframes execute every method call immediately. A lazy frame only
records what was asked for; nothing runs until collect(). In between, the
whole pipeline exists as a logical plan the library can rewrite.

Optimizations the guide lists (explain() shows the result):

- predicate pushdown — filters move as close to the data source as possible,
  ideally into the file reader so rows are skipped while reading;
- projection pushdown — only the columns used anywhere in the query are read;
- slice pushdown, common subplan elimination, simplifying expressions.

My benchmark: 2 GB of CSV, filter + group-by + join. Eager: 41 s, 9 GB peak
memory. Lazy: 6 s, 1.3 GB peak.

explain(optimized=False) vs explain() side by side is the best way to see what
changed.

=== note-data-lineage-debugging
domain: data-systems
title: Debugging a wrong dashboard number
created: 2026-08-09
role: synthesis
state: rough
authorship: user
concepts: []
sources: []
contexts: [workspace-dataframe-skill]
---
The weekly-active-users number in my practice dashboard jumped 38% in one
week. Nothing real had happened.

How I found it: started from the final number and walked backwards through
the pipeline one step at a time — for each intermediate table, count rows and
distinct user ids, and compare with the week before. Everything matched until
the join with the device table: after it, the row count was 1.38× larger. Some
users had two devices registered, so the join duplicated their rows, and the
later COUNT(*) counted them twice.

Fix: COUNT(DISTINCT user_id), and dedupe the device table first.

What would have made it faster: if every output row could say which input rows
it came from, I could have gone straight from a suspicious user to the two
device rows. Keep lineage.

=== note-why-provenance-paper
domain: data-systems
title: Why- and where-provenance
created: 2026-08-11
role: reference
state: rough
authorship: user
concepts: [concept-data-provenance]
sources: [source-buneman-provenance-2001]
---
Buneman, Khanna & Tan distinguish two questions about a query result:

- **Why-provenance**: which input tuples justify that this output tuple
  exists? Answered by a set of *witnesses* — minimal sets of input tuples that
  are enough to produce it.
- **Where-provenance**: where was this particular value copied from?

For a join, the witness of an output tuple contains one tuple from each side;
for a union, either side alone is a witness.

Later work (provenance semirings, Green et al. 2007) generalizes this: every
tuple carries an annotation, and joins multiply and unions add the
annotations, so the same machinery gives counting, trust scores or lineage.

=== note-idempotent-pipelines-backfills
domain: data-systems
title: Idempotent pipeline steps
created: 2026-08-13
role: synthesis
state: evolving
authorship: user
concepts: [concept-idempotency, concept-workflow-orchestration]
sources: [source-kleppmann-ddia]
---
A step is idempotent if running it twice leaves the same result as running it
once. Pipelines get rerun all the time — retries after failures, backfills of
old dates — so every step should be.

Patterns:
- write to a partition keyed by the logical date and *overwrite* it, never
  append;
- use MERGE/upsert on a natural key instead of INSERT;
- derive output file names from the inputs, not from the current time.

Anti-pattern I had: `INSERT INTO daily_totals SELECT … WHERE day = today()`.
A retry after a timeout doubled that day's totals.

=== note-kafka-consumer-lag-backpressure
domain: data-systems
title: Consumer lag and backpressure
created: 2026-08-16
role: synthesis
state: rough
authorship: user
concepts: [concept-stream-processing]
sources: [source-kleppmann-ddia]
---
Consumer lag = latest offset written by producers − offset the consumer group
has committed. If producers write 5,000 msgs/s and the consumers handle 4,000,
the lag grows by 1,000 every second, forever.

Lag in messages divided by the consume rate is roughly how far behind real
time the consumers are: 120,000 messages of lag at 4,000/s ≈ 30 s behind.

Options when consumers fall behind: add partitions and consumers (parallelism
is capped by the partition count), make each message cheaper, or push back on
the producers. Kafka itself does not push back — the log just grows (bounded by
retention). Push-based systems with bounded buffers do push back: the producer
blocks when the buffer is full.

=== note-data-pipeline-orchestration-dag
domain: data-systems
title: Pipelines as DAGs of tasks
created: 2026-08-07
role: synthesis
state: rough
authorship: user
concepts: [concept-workflow-orchestration]
sources: []
---
An orchestrator (Airflow, Dagster, Prefect) runs a pipeline defined as a
directed acyclic graph of tasks; an edge means "run after". The scheduler runs
every task whose upstream tasks have succeeded — a topological order, with
independent branches in parallel.

Why acyclic: a cycle would mean a task waits for itself. The orchestrator
refuses such a DAG at load time.

Per-task retries, timeouts and backfills (run the DAG for past dates) come for
free, which is why the tasks themselves must be safe to rerun.

=== note-parallel-workers-no-speedup
domain: data-systems
title: 16 workers, 1.6× faster
created: 2026-08-21
role: synthesis
state: rough
authorship: user
concepts: []
sources: []
contexts: [workspace-dataframe-skill]
---
Nightly job on the practice dataset: read one big CSV, clean, aggregate per
customer, write Parquet. Took 20 minutes with 4 worker processes. I went to 16
workers expecting 5 minutes. Got 12.5 minutes.

Timed each step: reading and parsing the single CSV file is done by one
process before anything can be split — about 10 of the 20 minutes. The
aggregation part did get 4× faster, but it was only half the job to begin
with.

So the job can never get below ~10 minutes however many workers I add, unless
the parse itself is split (several input files, or a parallel CSV reader).
Switched the upstream export to 32 Parquet files: now 3 minutes with 16
workers.

=== note-columnar-storage-compression
domain: data-systems
title: Columnar storage and compression
created: 2026-07-25
role: synthesis
state: evolving
authorship: user
concepts: [concept-columnar-storage]
sources: [source-kleppmann-ddia]
---
Store each column contiguously instead of each row. An analytical query that
reads 3 of 200 columns reads 1.5% of the data.

Columns compress well because neighbouring values are similar: dictionary
encoding for low-cardinality strings, run-length encoding for sorted or
repetitive columns, bit-packing for small integers. Parquet stores per-chunk
min/max statistics, so a reader can skip whole row groups whose range cannot
match a filter.

Downside: writing one row touches every column file — fine for bulk loads,
terrible for OLTP.

=== note-db-exam-cheatsheet
domain: data-systems
title: Database Systems — exam cheat sheet
created: 2026-07-10
role: reference
state: rough
authorship: mixed
concepts: [concept-relational-algebra, concept-query-optimization, concept-two-phase-locking, concept-write-ahead-logging, concept-db-normalization]
sources: [source-tuh-dbsys-slides]
contexts: [workspace-dbsys-exam]
---
Compiled the week before the exam; half from the slides, half my own.

- Pushdown rules: see the algebraic equivalences note.
- External sort passes: 1 + ⌈log_{B−1}⌈N/B⌉⌉.
- 2PL: growing/shrinking; strict 2PL holds X locks to commit.
- ARIES: analysis → redo (repeat history) → undo (CLRs).
- BCNF test: every non-trivial FD has a superkey on the left.

After the exam (2026-07-16): went OK, I think. Probably a 2.3 or so — the
recovery question was harder than expected.
