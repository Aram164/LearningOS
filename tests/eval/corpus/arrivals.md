Arrivals: material that reaches the learner during the evaluation. The
builder copies each body to eval-drop/<id>.md with a public index. Header keys
are limited to kind, arrives, channel, context (and filename).

=== A01
kind: handwritten-transcription
arrives: 2026-09-19
channel: photo of a notebook page, transcribed
context: Page from the library, reading ahead of the retake.
---
Bayesian networks (Bishop 8.1–8.2)

- DAG over the variables. Joint = Π_i p(x_i | parents(x_i)).
- 5 binary vars with no structure: 2⁵ − 1 = 31 numbers. With the graph
  a → c ← b, c → d, c → e: 1 + 1 + 4 + 2 + 2 = 10 numbers.
- A node is independent of its non-descendants given its parents.
- d-separation: path blocked by an observed chain/fork node, or by an
  unobserved collider with no observed descendants.
- "Head-to-head" node observed → its parents become dependent (explaining
  away!!)

The simplest example in the chapter is a single class node with arrows to
every feature node. ??? recognize this from somewhere

=== A02
kind: stage-note-draft
arrives: 2026-09-19
channel: working note written during stage stage-l07-01-ridge-lasso-geometry
context: Continuation of the ridge/lasso stage.
---
Solved the 1-D lasso by hand. Minimize ½(y − w)² + λ|w|.

- If w > 0: derivative w − y + λ = 0 → w = y − λ, valid only if y > λ.
- If w < 0: w = y + λ, valid only if y < −λ.
- Otherwise the minimum is at the kink: w = 0.

So w = sign(y) · max(|y| − λ, 0) — "soft thresholding". Everything with
|y| ≤ λ is set to exactly zero. Ridge in 1-D: w = y / (1 + λ) — shrinks but
never hits zero.

That's why there is no neat matrix formula for the lasso: the solution is
piecewise, and which pieces are active depends on the data. Coordinate descent
applies this 1-D rule to one weight at a time.

=== A03
kind: project-log
arrives: 2026-09-20
channel: Tessera commit message and dev log
context: Evening session on Tessera.
---
Implemented the filter-below-join rule:

    Filter(p, Join(L, R, on)) → Join(Filter(p, L), R, on)   if cols(p) ⊆ cols(L)
                              → Join(L, Filter(p, R), on)   if cols(p) ⊆ cols(R)

A conjunction is split first and each part is placed separately. Predicates
that need both sides stay above the join.

Added the property test: for 500 random small queries over the test CSVs,
execute(optimize(q)) returns the same multiset of rows as execute(q). It found
a bug on the first run: a filter on a column that exists in both inputs with
the same name got pushed to the wrong side. Now qualified names are required.

Also merged adjacent Projects. Plan for the sample query went from 7 operators
to 5; runtime 1.9 s → 0.4 s on the 1M-row orders file.

=== A04
kind: inbox-capture
arrives: 2026-09-20
channel: saved paragraph from an article
context: Clipped while reading about LLM serving.
---
"vLLM's PagedAttention stores the KV cache of each sequence in fixed-size
blocks that do not need to be contiguous in GPU memory; a per-sequence block
table maps logical block numbers to physical blocks. Blocks are allocated on
demand as the sequence grows, and identical prefixes can share physical blocks
with copy-on-write. Reported memory waste drops from 60–80% to under 4%."

= memory management for the KV cache. where have I seen block tables before?

=== A05
kind: handwritten-transcription
arrives: 2026-09-21
channel: photo of a notebook page, transcribed
context: Practice dashboard, again.
---
Revenue per region doubled for "North" last week — impossible.

Walked back step by step with row counts:
- orders (week): 48,210 rows ✓
- ⋈ customers: 48,210 ✓
- ⋈ regions on region_code: 96,420 ✗ ← here

regions table had two rows for code "N" (old name + new name after the
rename). Every North order matched twice. Dedup the dimension table and add a
uniqueness check on the dim key before joining.

Second time a join fan-out has bitten me.

=== A06
kind: inbox-capture
arrives: 2026-09-21
channel: note typed on the phone
context: Idea while walking, despite Ledgerline being paused.
---
Ledgerline receipt format v0:

    receipt = { id, note_id, parent_receipt, before_sha256, after_sha256,
                author, timestamp, reason, diff }

- append-only file of receipts per note; never edit a receipt
- current text = apply diffs from the first receipt onward (or cache
  snapshots every 50 receipts)
- verify: recompute after_sha256 at every step; a mismatch = corrupted chain
- "why does this sentence say X?" → find the receipt that introduced it

=== A07
kind: source-excerpt
arrives: 2026-09-22
channel: excerpt from a paper PDF
context: Reading for the proportional-share stage.
---
From Waldspurger & Weihl, "Stride Scheduling" (1995), §2:

"Each client has a ticket allocation, a stride inversely proportional to its
tickets, and a pass value. The client with the minimum pass is selected, and
its pass is advanced by its stride. … Stride scheduling achieves
proportional-share allocation deterministically: the relative error in any
client's allocation is bounded by a constant, independent of the allocation
period, whereas lottery scheduling's expected error grows with the square root
of the number of allocations."

=== A08
kind: stage-note-draft
arrives: 2026-09-22
channel: experiment log
context: Evening experiment with a toy inference server.
---
Toy inference server (distilled BERT, one GPU), two clients:

| max_batch | max_wait | throughput | p50 | p99 |
|---|---|---|---|---|
| 1 | 0 ms | 180 req/s | 6 ms | 9 ms |
| 32 | 10 ms | 590 req/s | 14 ms | 45 ms |

With client A sending 500 req/s and client B 20 req/s, B's p99 went to 400 ms —
its requests sit behind A's full batches. Per-client queues served in turn
fixed B (p99 30 ms) at 5% throughput cost.

=== A09
kind: inbox-capture
arrives: 2026-09-22
channel: message from a friend doing an internship
context: Chat message forwarded to self.
---
"our migration script deadlocked in Postgres: transaction 1 updates accounts
then ledger, transaction 2 updates ledger then accounts. postgres killed one
of them with 'deadlock detected'. fix was to always touch tables in the same
order" — that's literally the exam question

=== A10
kind: handwritten-transcription
arrives: 2026-09-23
channel: photo of lecture notes from a friend
context: Guest lecture on database internals.
---
Cardinality estimation — guest lecture

Estimated rows for WHERE make = 'Honda' AND model = 'Civic':
    sel(make) = 0.08, sel(model) = 0.01 → est. 0.08 · 0.01 · 10⁶ = 800 rows
    actual: 10,000 rows (every Civic is a Honda)

"The optimizer factorizes the joint selectivity as if the columns were
unrelated. It is the most common source of bad plans." Remedy: extended
statistics on (make, model), or sampling.

=== A11
kind: inbox-capture
arrives: 2026-09-23
channel: flashcard back side typed into the inbox
context: Anki card.
---
p-value: P(observing a test statistic at least as extreme as ours | H0 true).
It is NOT P(H0 true | data). A large p-value does not prove H0.

=== A12
kind: handwritten-transcription
arrives: 2026-09-23
channel: photo of exercise sheet solution, transcribed
context: Statistical Learning bonus exercise.
---
Weather HMM: states {Rainy, Sunny}, observations walk / shop / clean.
Start (0.6, 0.4); A = [[0.7, 0.3], [0.4, 0.6]];
emissions R: (0.1, 0.4, 0.5), S: (0.6, 0.3, 0.1).
Observed: walk, shop, clean.

t=1: R = 0.6·0.1 = 0.06, S = 0.4·0.6 = 0.24
t=2: R = max(0.06·0.7, 0.24·0.4)·0.4 = 0.0384 (from S)
     S = max(0.06·0.3, 0.24·0.6)·0.3 = 0.0432 (from S)
t=3: R = max(0.0384·0.7, 0.0432·0.4)·0.5 = 0.01344 (from R)
     S = max(0.0384·0.3, 0.0432·0.6)·0.1 = 0.002592 (from S)
Best: R at t=3 → back: R ← R ← S. Sequence: Sunny, Rainy, Rainy.

=== A13
kind: source-excerpt
arrives: 2026-09-23
channel: excerpt from a textbook chapter
context: Reading on parallel performance.
---
"If a fraction s of the work is inherently sequential, no number of
processors can reduce the runtime below s times the original. Gustafson
observed that in practice the problem size is scaled with the machine, so
that the parallel work grows while the sequential part stays fixed; the
scaled speedup is then s + (1 − s)·N."

=== A14
kind: stage-note-draft
arrives: 2026-09-24
channel: working note written during stage stage-df-lazy-02-read-explain
context: Plans 2 and 3 of the explain() exercise.
---
Plan 2 (group-by after join, then filter on the aggregate):
- the filter on total > 100 cannot move below the group-by (it needs the sum);
- the filter on year = 2025 did move below the join into the orders scan;
- "PROJECT 4/31 COLUMNS" on orders — only columns used anywhere survive.

Plan 3 (same subquery used twice):
- "CACHE" node: the shared subplan is computed once and reused.

Rule I'm seeing: a filter can move below an operator only if it depends on
nothing that operator creates.

=== A15
kind: inbox-capture
arrives: 2026-09-24
channel: note typed after a seminar
context: Reading group on generative models.
---
Softmax at temperature T is a Boltzmann (Gibbs) distribution over classes with
energy −z_i: p_i ∝ exp(−E_i / T). T → 0: all mass on the lowest energy (argmax);
T → ∞: uniform. Same exp(−E/T) form as the Metropolis acceptance rule.

=== A16
kind: handwritten-transcription
arrives: 2026-09-24
channel: photo of notebook page, transcribed
context: Debugging a CNN that did worse at test time.
---
Model fine in training, much worse in eval. Cause: I forgot model.eval(), so
batch norm used the statistics of each small test batch (size 4) instead of
the running mean/variance from training. With batch size 4 the per-batch mean
jumps around a lot.

Also: with model.eval() on and batch size 1 everything is consistent, because
each activation is standardized with the stored μ and σ — like a z-score with
fixed population parameters.

=== A17
kind: question
arrives: 2026-09-25
channel: question typed into the inbox
context: Came up while revising DB and reading about distributed systems.
---
Is "consistency" in CAP the same thing as the C in ACID? If a database is
"strongly consistent", is it ACID-consistent?

=== A18
kind: inbox-capture
arrives: 2026-09-25
channel: note typed on the phone
context: Late-night thought.
---
Everything I touch is a DAG: git, make, Airflow, query plans, autograd graphs.
Maybe one note about topological order and cycle detection across all of them?

=== A19
kind: source-excerpt
arrives: 2026-09-25
channel: excerpt from a book chapter
context: Reading on storage engines.
---
"RocksDB keeps one Bloom filter per SSTable, typically at 10 bits per key.
A point lookup for a key that does not exist consults the filter of every
level; with ~1% false positives, almost all of those files are never read from
disk."

=== A20
kind: stage-note-draft
arrives: 2026-09-26
channel: working note written during stage stage-os-l05-01-translation
context: First session on the virtual-memory unit.
---
Two-level page table walk, 32-bit address, 4 KiB pages: 10 bits directory
index, 10 bits table index, 12 bits offset. TLB miss costs two extra memory
reads here, four on x86-64.

Huge pages (2 MiB): one TLB entry covers 512× more memory → far fewer TLB
misses for big arrays. Databases and JVMs like them.

After a context switch the TLB entries of the old process are useless unless
tagged with an address-space id (ASID/PCID).

=== A21
kind: source-excerpt
arrives: 2026-09-26
channel: slide text from the L09 lecture
context: Rewatching L09 for the retake.
---
L09 slide 24: "Let X be the centred n × d data matrix with SVD X = U S Vᵀ.
Then the sample covariance is C = XᵀX/(n−1) = V S² Vᵀ/(n−1). Hence the
principal directions are the columns of V and the variance along the i-th
direction is s_i²/(n−1). In practice PCA is computed via the SVD of X, which is
numerically more stable than forming C."

=== A22
kind: inbox-capture
arrives: 2026-09-27
channel: note typed after a talk
context: Talk on JAX.
---
Speaker: "backprop is just reverse-mode autodiff applied to a scalar loss".
Reverse mode: one backward sweep per *output*. Forward mode: one sweep per
*input*. Loss = 1 output, millions of inputs → reverse. jax.jvp vs jax.vjp.

=== A23
kind: project-log
arrives: 2026-09-27
channel: design note for Ledgerline
context: Written despite the pause.
---
Problem: the mobile client retries a save after a timeout and the server
appends the same receipt twice.

Fix: the client creates a save_id (UUID) per edit and sends it with every
retry; the server keeps a unique index on (note_id, save_id) and returns the
existing receipt when it sees the pair again.

=== A24
kind: inbox-capture
arrives: 2026-09-27
channel: note typed on the phone
context: Weekend.
---
sourdough starter feeding schedule: 1:1:1 every 12 h at room temperature, or
once a week from the fridge. discard half before feeding.

=== A25
kind: question
arrives: 2026-09-28
channel: question typed into the inbox
context: Mock exam review.
---
Why does logistic regression use cross-entropy and not the squared error like
linear regression? Is it just a convention?

=== A26
kind: inbox-capture
arrives: 2026-09-28
channel: note typed on the phone
context: Tutorial.
---
learning rate 1.0 on the MLP → loss went to NaN after 3 steps. 0.1 fine.
same as the housing thing in April?

=== A27
kind: stage-note-draft
arrives: 2026-09-29
channel: working note written during stage stage-df-joins-01-strategies
context: First measurement for the joins unit.
---
Joined events (50M rows) with users on user_id. One key, user_id = 0
("anonymous"), holds 40% of all events.

Hash join: the partition containing key 0 is ~20M rows, does not fit the
memory budget, spills to disk and is re-partitioned — but repartitioning by
hash cannot split a single key. Runtime 11 min vs 90 s after filtering key 0
out and joining it separately.

So a hash join is O(n + m) only if the build partitions fit in memory and keys
are spread out. With one giant key it degrades badly.

=== A28
kind: question
arrives: 2026-09-29
channel: question typed into the inbox
context: Reading about streaming systems.
---
What does a producer-consumer bounded buffer from OS have to do with Kafka
consumer lag? Is Kafka's lag the same as a full buffer?

=== A29
kind: inbox-capture
arrives: 2026-09-30
channel: second capture of the same link from another device
context: Duplicate capture from the laptop.
---
read later: Dominant Resource Fairness (Ghodsi et al., NSDI 2011) — the
speaker at the internship fair mentioned it for GPU sharing

=== A30
kind: inbox-capture
arrives: 2026-09-30
channel: note typed on the phone
context: After reading about attention.
---
Attention output = Σ_i softmax(qᵀk_i/√d)_i · v_i. During generation, all old
keys and values get reused for every new token — so what exactly does the
server keep in memory between steps, and why does it grow with the context?
