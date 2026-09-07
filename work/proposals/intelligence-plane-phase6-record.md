# Intelligence Plane — Phase 6 record (proof-carrying change)

Parent proposal: `intelligence-plane-plan.md`. Prior phases: Phase 0
(record), Phase 1 (23 predicates, contract v2, 20 VOQs), Phase 1.5
(policy-query envelope), Phase 2 (lineage sidecar), Phase 3 (goal
engine), Phase 4 (Task IR, telemetry, static router), Phase 5 (dossiers).

## What Phase 6 lands

- `tools/learning_os/semantics/changes.py`: the change envelope
  (intent, scope, read revisions, claims plus evidence locators, write
  set with capability and scopes, expected snapshot, Aram approval plus
  approved capabilities, postconditions, validation plan), the
  deterministic `admit` check with fixed refusal order (authority,
  freshness, evidence, lineage, scope, shape), and post-apply
  `verify_postconditions` replaying the VOQ assertion operators.
- Highest-risk validation, exercised explicitly:
  stale-write-never-commits, snapshot-race conflict, one-approval-one-
  scope, out-of-scope deny, missing-evidence replan, unsupported-lineage
  conflict, non-Aram approval deny.
- `tests/test_proof_carrying_change.py` (12 tests); change section in
  `system/SEMANTIC-CONTRACT.md`; this record.

## Explicit non-changes

- The gateway still applies: the envelope is preflight, not an
  alternative write path, and no gateway code was touched. Translation
  validation between producer candidates and independent validators
  remains harness work for the first live envelope.
- No contract-version bump (still v2), no VOQ additions, no new schema,
  no queue or ledger writes by the admission check itself.
- No canonical migration, no new write path, no hand-edit of rebuilt
  views. No critique-point action taken.

## Validation observed (2026-09-07 session)

`make check` zero errors; warning baseline OK; `make lint` incl. code
reachability (161/161) green; change suite green; full suite green;
views regenerated after the final authored change. The complete
Intelligence Plane (Phases 0–6 plus 1.5) is committed per phase and
pushed.
