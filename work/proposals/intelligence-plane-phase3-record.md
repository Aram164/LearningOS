# Intelligence Plane — Phase 3 record (candidate-goal engine)

Parent proposal: `intelligence-plane-plan.md`. Prior phases: Phase 0
(record), Phase 1 (23 predicates, contract v2, 20 VOQs), Phase 1.5
(policy-query envelope), Phase 2 (lineage sidecar).

## What Phase 3 lands

- `tools/learning_os/semantics/goals.py`: five read-only detectors
  (covering-routes-stale, source-changed-under-claim,
  repeated-question-gap, inspection-without-dossier,
  reviewer-correction-pattern), each pure over caller-supplied signals,
  thresholded (default 3), and deduplicated via `known_ids`.
- Full lifecycle with refused skips: the 9-step chain plus
  deferred/rejected/stale/superseded exits. AUTHORIZED requires Aram's
  explicit action (anyone else refused); SUPERSEDED names its successor;
  FORMULATED and beyond require rationale plus evidence; terminal states
  never move. Queue shape (`goal_to_dict`/`goal_from_dict`) for one file
  per goal under `work/proposals/goals/` — detectors write nothing, the
  operator files what the engine proposes.
- `tests/test_goal_proposals.py`: each detector fires exactly on fixture
  (readers only, gaps only, thresholds honored), purity (no disk writes),
  the full walk to CLOSED through Aram, refusal of foreign approval and
  skipped steps, deferral/supersession/stale re-entry, queue round-trip.
- Goals section in `system/SEMANTIC-CONTRACT.md`; this record.

## Explicit non-changes

- No queue files committed: detectors propose, nothing auto-files.
  (`work/proposals/` is declared with an unchecked interior, so goal
  files need no tree change when they arrive.)
- No goal-record schema file: queue shapes are validated by
  `goal_from_dict`; the standing ledger precedent (lineage) does not
  apply to Aram-facing proposals.
- No contract-version bump (still v2), no VOQ additions, no detector
  learning (static thresholds until Phase 4 telemetry can justify more).
- No canonical migration, no gateway change, no new write path, no
  hand-edit of rebuilt views. No critique-point action taken.

## Validation observed (2026-09-07 session)

`make check` zero errors; warning baseline OK; `make lint` incl. code
reachability (158/158) green; goal suite green; full suite green; views
regenerated after the final authored change.
