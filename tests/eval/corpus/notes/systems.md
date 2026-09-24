Durable notes — operating systems and ML systems.

=== note-os-kernel-user-mode
domain: systems
title: Kernel mode, user mode and system calls
created: 2026-04-15
role: synthesis
state: evolving
authorship: user
concepts: [concept-os-kernel]
sources: [source-tuh-os-slides]
---
The CPU has (at least) two privilege levels. The kernel runs in kernel mode
and may execute privileged instructions (change page tables, talk to devices,
disable interrupts); applications run in user mode and may not.

A system call is the controlled door between them: the program puts a number
and arguments in registers and executes a trap instruction; the CPU switches
to kernel mode and jumps to a handler the kernel registered at boot. The
kernel checks the arguments, does the work, and returns to user mode.

That is why read() is much more expensive than a function call — mode switch,
argument checking, cache and TLB pollution.

Monolithic kernel (Linux) vs microkernel (drivers and file systems as user
processes): the microkernel is more robust, but every service call becomes
message passing.

=== note-cpu-scheduling-round-robin
domain: systems
title: CPU scheduling — FCFS, SJF, round robin
created: 2026-04-17
role: reference
state: evolving
authorship: user
concepts: [concept-cpu-scheduling]
sources: [source-tuh-os-slides, source-ostep]
contexts: [workspace-os-oral-prep]
---
Metrics: turnaround time (completion − arrival), response time (first run −
arrival), waiting time.

- **FCFS**: simple; one long job in front makes everyone wait (convoy effect).
- **SJF / STCF**: optimal average turnaround if job lengths are known; they
  never are; long jobs can starve.
- **Round robin**: run each job for one time quantum, then the next. Great
  response time, bad turnaround. The quantum trades responsiveness against
  switching overhead — too small and the CPU spends its time switching.
- **MLFQ**: several queues with priorities; a job that uses its whole quantum
  moves down; periodic priority boost to avoid starvation. Learns the
  interactive/batch split without being told.

Exercise from tutorial 2: jobs A(0, 8), B(1, 4), C(2, 9), D(3, 5), quantum 4 →
average waiting time 12.25 under RR, 7.75 under SJF.

=== note-cfs-fair-share
domain: systems
title: Proportional share and Linux CFS
created: 2026-04-21
updated: 2026-09-16
role: synthesis
state: evolving
authorship: user
concepts: [concept-proportional-share, concept-cpu-scheduling]
sources: [source-tuh-os-slides, source-ostep]
contexts: [workspace-os-oral-prep]
---
Different goal from MLFQ: not "optimize turnaround" but "each process gets a
guaranteed fraction of the CPU".

**Lottery scheduling**: every process holds tickets; every time slice draw a
random ticket; the holder runs. Over time each process gets CPU in proportion
to its tickets — but only on average, short-term it can be unfair.

**CFS (Linux)**: each task has a virtual runtime that grows while it runs;
the scheduler always picks the task with the smallest vruntime (kept in a
red-black tree). Weights come from the nice value — a heavier task's vruntime
grows more slowly, so it gets picked more often. sched_latency (e.g. 48 ms) is
divided among the runnable tasks to get each slice, with a minimum
granularity so slices never get absurdly short.

"Fair" here means: over any interval, CPU time divided in proportion to the
weights of the tasks that wanted to run.

Update 2026-09-16 (oral prep): stride scheduling is the deterministic version
of lottery — still need to work an example by hand.

=== note-cfs-fair-share @2026-04-21
---
Different goal from MLFQ: not "optimize turnaround" but "each process gets a
guaranteed fraction of the CPU".

**Lottery scheduling**: every process holds tickets; every time slice draw a
random ticket; the holder runs. Over time each process gets CPU in proportion
to its tickets.

**CFS (Linux)**: each task has a virtual runtime that grows while it runs;
the scheduler always picks the task with the smallest vruntime (kept in a
red-black tree). Weights come from the nice value.

=== note-context-switch-cost
domain: systems
title: What a context switch costs
created: 2026-04-19
role: synthesis
state: rough
authorship: user
concepts: [concept-context-switch]
sources: [source-ostep]
---
Direct cost: save registers of the old process, restore the new one, switch
the address space. A few microseconds.

Indirect cost, usually bigger: the new process finds the caches and the TLB
full of the old process's data, so it runs slowly until they warm up again.

Measured with the pipe ping-pong trick from OSTEP chapter 6 homework: about
2.1 µs per switch on my laptop with both processes pinned to one core.

This is why a very small round-robin quantum is a bad idea.

=== note-priority-inversion
domain: systems
title: Priority inversion
created: 2026-04-28
role: synthesis
state: evolving
authorship: user
concepts: [concept-priority-inversion, concept-synchronization]
sources: [source-tuh-os-slides]
---
Low-priority L holds a lock; high-priority H blocks on it; medium-priority M
(does not need the lock) preempts L. Now H effectively waits for M.

Mars Pathfinder, 1997: exactly this caused watchdog resets on the rover.

Fix: priority inheritance — while L holds a lock that H wants, L runs at H's
priority, so M cannot preempt it. VxWorks had it available; it was switched off
for that mutex and was turned on by a remote patch.

=== note-virtual-memory-is-swap
domain: systems
title: Virtual memory
created: 2026-04-30
role: synthesis
state: deprecated
authorship: user
concepts: [concept-virtual-memory]
sources: []
---
Virtual memory is when the OS uses the disk as extra RAM. When physical memory
is full, pages are written to the swap partition and read back later. So a
machine without a swap partition has no virtual memory.

=== note-virtual-memory-address-translation
domain: systems
title: Virtual memory is address translation
created: 2026-05-11
role: synthesis
state: evolving
authorship: user
concepts: [concept-virtual-memory]
sources: [source-tuh-os-slides, source-ostep]
contexts: [workspace-os-oral-prep]
---
Corrects my April note, which confused virtual memory with swapping.

Virtual memory = every process gets its own address space, and the hardware
translates each virtual address to a physical one on every access. Swapping
is one optional thing this makes possible, not the definition. A phone without
swap still has virtual memory.

Mechanics: the address splits into a virtual page number and an offset. The
page table maps page numbers to physical frame numbers; multi-level page
tables avoid allocating entries for unused regions. The TLB caches recent
translations — without it every access would need extra memory accesses for
the page walk.

What it buys: isolation (a process cannot even name another's memory),
convenience (every program can assume the same layout), sharing (map the same
frame into two address spaces), lazy allocation, copy-on-write fork, and yes,
paging to disk.

Page fault: the entry is not present → trap → the kernel decides (allocate,
load from disk, or kill with SIGSEGV).

=== note-page-replacement-lru-clock
domain: systems
title: Page replacement — FIFO, LRU, clock
created: 2026-05-13
role: synthesis
state: evolving
authorship: user
concepts: [concept-page-replacement]
sources: [source-ostep]
---
When a page must be brought in and no frame is free, which page to evict?

- **OPT (Belady)**: evict the page used furthest in the future. Unrealizable,
  but the benchmark.
- **FIFO**: evict the oldest page. Can get *worse* with more frames (Belady's
  anomaly — reference string 1,2,3,4,1,2,5,1,2,3,4,5 with 3 vs 4 frames).
- **LRU**: evict the least recently used page. Good because of locality;
  exact LRU is too expensive to maintain on every memory access.
- **Clock**: frames in a circle, each with a reference bit set by hardware on
  access. The hand sweeps: bit 1 → clear it and move on; bit 0 → evict. A
  cheap approximation of LRU.

Looping over a working set one page larger than memory is the worst case for
LRU: every access misses.

=== note-cpu-cache-locality
domain: systems
title: Caches and locality
created: 2026-05-04
role: synthesis
state: evolving
authorship: user
concepts: [concept-cpu-caches]
sources: []
---
Memory is fetched in cache lines (64 bytes). Temporal locality: recently used
data will be used again. Spatial locality: data next to recently used data
will be used soon.

Experiment: summing a 4096×4096 matrix of doubles in C, row by row: 18 ms;
column by column: 140 ms. Same arithmetic; the column order touches a new
cache line on every access because C stores rows contiguously.

Rough latencies: L1 ~1 ns, L2 ~4 ns, L3 ~15 ns, DRAM ~80 ns.

=== note-deadlock-four-conditions
domain: systems
title: Deadlock — the four conditions
created: 2026-05-18
role: synthesis
state: evolving
authorship: user
concepts: [concept-deadlock, concept-synchronization]
sources: [source-tuh-os-slides, source-ostep]
contexts: [workspace-os-oral-prep]
---
Deadlock needs all four (Coffman):

1. mutual exclusion — resources cannot be shared;
2. hold and wait — a thread holds one resource while waiting for another;
3. no preemption — resources cannot be taken away;
4. circular wait — a cycle of threads each waiting for the next.

Break any one to prevent deadlock. The practical one: impose a global lock
order so a cycle cannot form (circular wait).

Detection: build the resource-allocation graph (threads → resources they wait
for, resources → threads that hold them); with single-instance resources a
cycle means deadlock. Then recover by killing or rolling back one thread.

Avoidance (banker's algorithm): only grant a request if the system stays in a
safe state. Needs maximum demands in advance — rarely practical.

Oral question from a senior student: "Is a livelock a deadlock?" — no, threads
keep running but make no progress.

=== note-semaphores-producer-consumer
domain: systems
title: Semaphores and the bounded buffer
created: 2026-05-16
role: derivation
state: evolving
authorship: user
concepts: [concept-synchronization]
sources: [source-ostep]
---
Bounded buffer with N slots, one or more producers, one or more consumers.

    empty = N, full = 0, mutex = 1

    producer:  wait(empty); wait(mutex); put(item); post(mutex); post(full)
    consumer:  wait(full);  wait(mutex); item = get(); post(mutex); post(empty)

When the buffer is full, producers block on `empty` — the slow consumer pushes
back on the fast producer automatically. When it is empty, consumers block on
`full`.

Classic bug I made: taking `mutex` before `empty` → a producer holds the mutex
while sleeping on a full buffer, and no consumer can get in. Deadlock.

=== note-cpu-instruction-pipeline
domain: systems
title: Instruction pipelining
created: 2026-04-25
role: synthesis
state: rough
authorship: user
concepts: [concept-instruction-pipelining]
sources: []
---
Refresher from computer architecture. Classic five stages: fetch, decode,
execute, memory, write-back. With pipelining a new instruction enters every
cycle, so throughput approaches one instruction per cycle even though each one
still takes five cycles.

Hazards:
- structural — two stages need the same unit;
- data — an instruction needs a result not yet written (forwarding helps,
  load-use still stalls one cycle);
- control — a branch: which instruction to fetch next? Branch prediction; a
  misprediction flushes the pipeline (10–20 cycles on modern CPUs).

This is why sorted data made the branchy loop in the famous StackOverflow
question six times faster.

=== note-journaling-filesystems
domain: systems
title: Journaling file systems
created: 2026-06-26
role: synthesis
state: evolving
authorship: user
concepts: [concept-journaling-file-systems]
sources: [source-ostep]
---
Problem: appending a block to a file touches several on-disk structures (the
data block, the inode, the free-block bitmap). A crash between the writes
leaves them inconsistent. fsck repairs this by scanning the whole disk —
minutes to hours.

Journaling (ext3/ext4): before touching the real structures, write a
description of all the intended updates to a separate journal area, then a
commit block. Only then write the structures in place (the checkpoint). After
a crash, replay every committed transaction from the journal; ignore the ones
without a commit block. Recovery takes seconds.

Metadata-only journaling (ordered mode) writes the data block first, then
journals only the metadata — cheaper, and still never points an inode at
garbage.

The ordering is the whole trick: the journal record must be durable before
the in-place write.

=== note-amdahls-law
domain: systems
title: Amdahl's law
created: 2026-07-02
role: synthesis
state: evolving
authorship: user
concepts: [concept-amdahls-law]
sources: [source-tuh-os-slides]
---
If a fraction p of a program can be parallelized and the rest cannot, then
with n processors

    S(n) = 1 / ((1 − p) + p / n)

and as n → ∞, S → 1 / (1 − p). With p = 0.9 the speedup can never exceed 10,
no matter how many cores.

Gustafson's counterpoint: people use more cores to solve bigger problems, and
then the parallel part grows while the serial part stays the same.

=== note-dynamic-batching-inference
domain: systems
title: Dynamic batching in model serving
created: 2026-08-14
role: synthesis
state: rough
authorship: user
concepts: [concept-model-serving]
sources: [source-huyen-dmls]
---
A GPU processes a batch of 32 inputs almost as fast as a batch of 1, so a
server that runs requests one at a time wastes most of the hardware.

Dynamic batching: incoming requests wait in a queue; the server launches a
batch when either max_batch_size requests are waiting or the oldest one has
waited max_wait (e.g. 5 ms).

Trade-off: bigger batches and longer waits → more throughput, but every
request pays up to max_wait extra latency, and the p99 latency gets worse
under light load (you wait for a batch that never fills).

Rule of thumb from the book: choose max_wait as a small fraction of the
latency budget, then raise max_batch_size until throughput stops improving.

=== note-multi-tenant-gpu-sharing
domain: systems
title: Sharing one inference cluster between teams
created: 2026-08-18
role: synthesis
state: rough
authorship: user
concepts: [concept-model-serving, concept-dominant-resource-fairness]
sources: [source-huyen-dmls]
---
From the internship-fair talk: one team's nightly batch-scoring jobs took all
the GPUs, and the chat product's interactive requests timed out every night.

What they did: every team gets a weighted share of GPU time. A team that is
not using its share lends it out, but gets it back within seconds when its own
requests arrive. Interactive traffic gets a higher weight than batch traffic.

The speaker said "strict priorities starved the batch jobs completely; weights
fixed it". Also: memory matters as much as compute — one team with huge models
can exhaust GPU memory while using little compute.

=== note-dominant-resource-fairness-paper
domain: systems
title: Dominant Resource Fairness
created: 2026-08-17
role: reference
state: evolving
authorship: user
concepts: [concept-dominant-resource-fairness]
sources: [source-ghodsi-drf-2011]
---
Setting: several users share a cluster with more than one resource (CPU and
memory). Max-min fairness is clear for one resource; with two it is not — one
user needs lots of CPU, another lots of memory.

DRF: for each user compute the *dominant share*, the largest fraction of any
single resource that user holds. Allocate so as to equalize dominant shares
(progressive filling).

Example from the paper: 9 CPUs, 18 GB. User A tasks need (1 CPU, 4 GB), user B
tasks need (3 CPU, 1 GB). DRF gives A three tasks and B two: A's dominant share
(memory) = 12/18 = 2/3, B's (CPU) = 6/9 = 2/3.

Properties they prove: sharing incentive, strategy-proofness, envy-freeness,
Pareto efficiency. Used in Mesos.

=== note-kv-cache-transformer-serving
domain: systems
title: The KV cache in transformer inference
created: 2026-08-22
role: synthesis
state: rough
authorship: user
concepts: [concept-kv-cache, concept-model-serving]
sources: []
---
Generating token t needs attention over all previous tokens. Recomputing their
keys and values every step would be quadratic, so the server stores them: the
KV cache.

Size per sequence = 2 (K and V) × layers × heads × head_dim × sequence length ×
bytes per value. For a 7B model in fp16 that is about 0.5 MB per token — a
2,000-token conversation needs ~1 GB.

Problem: the final length is unknown in advance. Reserving memory for the
maximum length wastes most of it; allocating as you go leaves gaps between
sequences. The talk claimed that more than half of KV memory was wasted this
way in naive servers, which directly limits how many requests fit in a batch.

=== note-data-parallel-training-scaling
domain: systems
title: Data-parallel training did not scale as expected
created: 2026-08-26
role: synthesis
state: rough
authorship: user
concepts: [concept-data-parallel-training]
sources: []
---
Cloud credits experiment: ResNet-18 on 1, 2, 4, 8 GPUs, same global batch.

| GPUs | epoch time | speedup |
|---|---|---|
| 1 | 412 s | 1.0 |
| 2 | 221 s | 1.9 |
| 4 | 131 s | 3.1 |
| 8 | 98 s | 4.2 |

Profiling: each step = forward/backward (shrinks with more GPUs because each
gets fewer examples) + all-reduce of the gradients (does not shrink; the whole
model's gradient must be exchanged every step) + data loading from one shared
disk (does not shrink either). At 8 GPUs the part that does not shrink is
already most of the step.

Bigger per-GPU batches helped, until accuracy started to drop.

=== note-mixed-precision-training
domain: systems
title: Mixed-precision training
created: 2026-08-29
role: synthesis
state: rough
authorship: user
concepts: [concept-mixed-precision]
sources: []
---
Store activations and do matrix multiplications in fp16/bf16, keep a master
copy of the weights in fp32 for the update.

fp16 has a small exponent range: small gradients underflow to zero. Loss
scaling multiplies the loss by e.g. 1024 before backward and divides the
gradients afterwards; dynamic scaling lowers the factor when it sees inf/NaN.

bf16 has fp32's exponent range with fewer mantissa bits, so it usually needs
no loss scaling.

Speedup on my rented GPU: 1.8× for the ResNet run, half the activation memory.

=== note-os-scheduling-exercise-bank
domain: systems
title: OS scheduling — exercise bank
created: 2026-08-19
role: exercise-bank
state: rough
authorship: operator-drafted
concepts: [concept-cpu-scheduling, concept-proportional-share, concept-context-switch]
sources: [source-tuh-os-slides]
contexts: [workspace-os-oral-prep]
---
Drafted from tutorial 2 and the lecture; solutions are not included.

1. Jobs A(0, 6), B(2, 3), C(4, 7). Draw the Gantt chart and compute average
   turnaround for FCFS, SJF, STCF and RR with quantum 2.
2. Why does MLFQ need a periodic priority boost? Give a job mix that starves
   without it.
3. Lottery: A holds 75 tickets, B 25. After 4 slices, what is the probability
   that B has not run at all?
4. Stride scheduling: A, B, C hold 100, 50, 250 tickets, L = 10,000. List the
   first eight scheduling decisions.
5. CFS: two tasks with nice 0 and nice 5. Which gets more CPU, and roughly how
   much more?
6. The quantum is 1 ms and a context switch costs 50 µs. What fraction of time
   is overhead? What if the quantum is 100 µs?
