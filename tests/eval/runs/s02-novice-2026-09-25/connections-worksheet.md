# Connection worksheet (judge)

Grade each returned relevant target: explanation 0 (wrong/absent) · 1 (partly) · 2 (correct), provenance 0/1. Oracle mentions are guidance, not wording.

## C01 — note-naive-bayes-spam-filter

_not answered_

## C02 — note-map-estimation-priors

_not answered_

## C03 — note-parallel-workers-no-speedup

_not answered_

## C04 — note-cfs-fair-share

_not answered_

## C05 — note-write-ahead-logging-aries

_not answered_

## C06 — note-selinger-join-ordering

_not answered_

## C07 — note-query-optimizer-cost-model

_not answered_

## C08 — note-low-rank-approximation

_not answered_

## C09 — note-data-lineage-debugging

_not answered_

## C10 — note-kv-cache-transformer-serving

_not answered_

## C11 — note-os-kernel-user-mode

_not answered_

## C12 — note-db-normalization-3nf

_not answered_

## C13 — note-acid-consistency

_not answered_

## C14 — note-spaced-repetition-scheduler

_not answered_

## C15 — note-buffer-pool-replacement

_not answered_

## C16 — note-p-values-corrected

_not answered_

## C17 — note-gradient-descent-from-scratch

_not answered_

## C18 — note-dynamic-batching-inference

_not answered_

## C19 — note-softmax-temperature

_not answered_

## C20 — note-constant-folding-cse

_not answered_

## A01 — arrival:A01

_not answered_

## A02 — arrival:A02

_not answered_

## A03 — arrival:A03

_not answered_

## A04 — arrival:A04

_not answered_

## A05 — arrival:A05

_not answered_

## A06 — arrival:A06

_not answered_

## A07 — arrival:A07

_not answered_

## A08 — arrival:A08

_not answered_

## A09 — arrival:A09

| rank | target | oracle | reason given | should mention | expl | prov |
|---|---|---|---|---|---|---|
| 1 | inbox:20260915-os-oral-questions.md | USEFUL_CONNECT | This is 'the exam question' the capture refers to: last year's OS oral asked 'How can deadlock be prevented? Which condition would you break in practice?' — the friend's fix (always touch tables in the same order) is a real-world answer: break circular wait. |  | 2 | 1 |
| 2 | note-deadlock-four-conditions | MUST_CONNECT | States the four Coffman conditions and that the practical prevention is a global lock order so no cycle (circular wait) can form — exactly the fix in the message. | a fixed lock order breaks circular wait | 2 | 1 |
| 3 | note-two-phase-locking-deadlocks | MUST_CONNECT | The database side of the same story: T1 locks A then B, T2 locks B then A; the DBMS keeps a waits-for graph, detects the cycle and aborts a victim — which is what Postgres' 'deadlock detected' did. | waits-for cycle; the DB aborts a victim | 2 | 1 |
| 4 | stage:stage-os-l07-01-deadlock | UNJUDGED | Where the capture was filed: the pending, exam-critical OS L07 stage whose objective is to state the four conditions and detect a cycle; the example is a worked instance. |  | 2 | 1 |
| 5 | workspace-os-oral-prep | UNJUDGED | The active effort the capture serves (oral on 2026-10-12 covering scheduling, virtual memory and deadlock). |  | 2 | 1 |
| 6 | note-db-exam-cheatsheet | UNJUDGED | Database Systems cheat sheet lists two-phase locking; weaker link (DB exam already passed). |  | 2 | 1 |
| 7 | note-semaphores-producer-consumer | USEFUL_CONNECT | Another deadlock from acquiring two synchronization objects in the wrong order (bounded buffer); same pattern in the OS course. |  | 2 | 1 |

## A10 — arrival:A10

_not answered_

## A11 — arrival:A11

_not answered_

## A12 — arrival:A12

_not answered_

## A13 — arrival:A13

_not answered_

## A14 — arrival:A14

_not answered_

## A15 — arrival:A15

_not answered_

## A16 — arrival:A16

_not answered_

## A17 — arrival:A17

_not answered_

## A18 — arrival:A18

_not answered_

## A19 — arrival:A19

_not answered_

## A20 — arrival:A20

_not answered_

## A21 — arrival:A21

_not answered_

## A22 — arrival:A22

_not answered_

## A23 — arrival:A23

_not answered_

## A24 — arrival:A24

_not answered_

## A25 — arrival:A25

_not answered_

## A26 — arrival:A26

_not answered_

## A27 — arrival:A27

_not answered_

## A28 — arrival:A28

_not answered_

## A29 — arrival:A29

_not answered_

## A30 — arrival:A30

_not answered_


## Judge grading notes (S10)

- expl: 0 wrong/absent, 1 partly right, 2 correct. All keyword-heuristic misses
  were human-graded; heuristic-covered rows were accepted after a 12-row
  spot-check per run found no false covers. MUST_NOT rows graded on whether
  the stated reason is factually correct (several are knowing contrasts).
- prov: 1 cited material refs resolve and support the claim; 0 no usable
  citation (no evidence, or only a discovery-method note such as a `los ...`
  command or `surfaced by:` line). Sampled rows only; see FAILURE_ANALYSIS.md.
