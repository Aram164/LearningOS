# Task IR P3 feasibility findings — 2026-10-28

Offline only: zero paid model trials, zero production changes. PR #71 and
P1 remain frozen at `e895758`. The proof of concept lives in the workbench
(`LearningOS/workbench/task-ir-p3-feasibility/`), not in the repository.

## Assessment: what each alternative actually removes

| Responsibility | B — runner | B+projection | P3 — declarative resolution |
|---|---|---|---|
| Discover candidate routes | agent reads full output | agent reads projected output | system-internal; agent never sees candidates |
| Select the target route | agent judgment | agent judgment (projection only reformats) | system enforces exactly-one match |
| Carry the route ID into the write | agent copies it | agent copies it | system binds it; ID never crosses to the agent |
| Construct the write payload | agent | agent | agent supplies selector + changes only |
| Detect ambiguity | agent notices count > 1 | agent notices count > 1 | system refuses `ambiguous` |
| Returned bytes | full reports | compact projections | compact projections |

The decisive row is selection. The existing `summarize()` mechanism
(fields / max_items / max_bytes) can shrink what the agent reads, but it
cannot enforce uniqueness or choose among placements. A B+ wrapper that
returns only `{route_id}` for a unique match is no longer mere formatting —
it contains the same resolution logic as P3, just client-side. So the real
comparison is: resolution logic in a runner-side helper the agent still
drives step by step, versus resolution inside one server-side intent the
agent submits once.

What P3 uniquely removes: candidate interpretation, selection, ID carrying,
and one agent invocation (discovery merges into preview). What it does not
remove: system-side work. Internally it runs discovery plus the full Task
IR preview/apply machinery — more total subprocess work than B, hidden
from the agent rather than eliminated.

## Proof of concept

`poc/p3_selector.py` (131 lines) resolves `{unit_id, stage_id?, source_id?,
locator?}` via the existing `plan-edit-context` read, requires exactly one
distinct route, then drives the frozen Task IR preview/apply unchanged.
Compact responses return only the requested projection; full discovery and
task reports are retained as evidence files. No gateway, guard, approval,
receipt, or recovery code was touched or duplicated.

## Deterministic comparison (scripted, identical semantics, same oracles)

All 12 runs pass. Oracle: intended field only, all other fields preserved,
receipt counts, stale external change preserved.

| Scenario | B calls / visible | B+ calls / visible | P3 calls / visible |
|---|---|---|---|
| S1 unique patch | 3 / 5,601 B | 3 / 375 B | 2 / 474 B |
| S2 ambiguous (2 routes) | 1 / 4,633 B | 1 / 240 B | 1 / 235 B |
| S3 missing source | 1 / 3,208 B | 1 / 215 B | 1 / 283 B |
| S5 stale after preview | 3 / 4,301 B | 3 / 373 B | 2 / 472 B |

Agent-authored bytes on S1: B ≈ 436 (plan 195 + check payload 127 + submit
payload 114, the route ID copied into both payloads); P3 = 252 (one intent,
reused at apply). P3 statuses behaved as designed: `needs_review` →
`committed` with a review reference, `ambiguous`, `missing`, and stale
`refused` with the external change preserved.

## Interpretation

1. **Bytes are a projection problem, and B+ already wins it.** B+projection
   is the cheapest arm in visible bytes in three of four scenarios. The
   5,264-byte Task IR apply verbosity is fixable formatting, not evidence
   for a declarative engine — confirming the brief's caution.
2. **P3's distinct saving is one invocation plus removed selection work.**
   Two boundary crossings instead of three on write scenarios, and the
   agent never handles the route ID. Worth roughly 200 authored bytes and
   one round trip per write on this workflow — real, but small.
3. **Error prevention is P3's only untested upside.** Server-enforced
   uniqueness removes a class of agent mistakes (wrong-route selection,
   mis-copied IDs) that scripted operators and the P2b screening agents did
   not actually make. Valuing it would need the paid trials this phase was
   forbidden to run, on harder tasks than P2-07.
4. **Production cost is not small.** The POC is 131 lines because it stands
   on P1. A production selector needs a contract, capability registration
   and task-scope entries, effect classification, transcript and
   architecture tests, and documentation — the P1 increment (766 lines of
   implementation, 805 of tests) is the honest scale reference. That buys
   the one-invocation and selection-removal benefits above, on one
   operation (`route.patch`) with a four-attribute selector.

## Recommendation: reject P3 as a production direction; simplify instead

Under the stated stop conditions, P3 provides no meaningful advantage over
B+projection on anything measurable offline, and its remaining advantage
(error prevention on harder tasks) is speculative. Building it would repeat
the P1 pattern: substantial safety-adjacent infrastructure for a benefit
the existing runner nearly matches.

Recommended instead, as ordinary runner improvement outside this experiment:

1. Add compact result projection to the runner's write path (the B+ shape:
   `{status, route_id}` plus a retained-report reference), which captures
   most of the byte saving measured here for a fraction of the cost.
2. If route selection friction is ever observed in real agent work, add a
   deterministic unique-route helper at the runner layer — the same
   resolution logic as this POC, without a new declarative surface.

Do not request paid B/P3 trials on this evidence. Revisit declarative
resolution only if real operating work shows selection or ID-carrying
errors that the runner demonstrably causes. The declarative research
question stays open in principle; on current evidence the existing runner
is sufficient, and discovering that cheaply was the point of the exercise.

Artifacts (workbench `task-ir-p3-feasibility/`): POC sha256
`7ef50bc4f59fea06250159d566d186abd07a9cddf48f956ca25624ec93ebeb13`,
comparison harness `f431c7cd30d9d5e5fd628a2d3ad5118855bcebaffb50e9cb0255f85498a8c0e7`,
raw results `0b11f17b6a95aec560806e0a94979935c3faa953c50f6996e990f6c3ef7c7143`.
