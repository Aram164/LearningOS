# Intelligence Plane — Phase 1.5 record (policy query companion)

Parent proposal: `intelligence-plane-plan.md`. Prior phases:
`intelligence-plane-phase0-record.md`,
`intelligence-plane-phase1-record.md` (23 predicates, contract version 2,
20 VOQs at 15/5).

## Decision

Phase 1.5 (this slice) before Phase 2 (lineage). The policy layer is a
thin view over predicates Phase 1 just built — no new storage and no open
design questions. Phase 2 carries an explicit unresolved choice (lineage
as receipt-adjacent sidecar vs. generated projection) and benefits from
the query surface settling first, since lineage's `judged_by` will cite
exactly these policy decisions.

## What Phase 1.5 lands

- `tools/learning_os/semantics/policy.py`: seven governance rules as
  OPA-style queries returning `PolicyDecision(rule, verdict, reasons,
  predicate, authority)` over the shared `allow/deny/defer/needs-review`
  vocabulary. No new judgment — each rule maps one Phase 1 predicate and
  explains the mapping from the caller's own inputs.
- `tests/test_policy_query.py`: pinned rule set, verdict mapping,
  reasons/authority presence on every rule, unknown-rule KeyError,
  malformed-query deny.
- Policy section in `system/SEMANTIC-CONTRACT.md`; this record.

## Explicit non-changes

- No contract-version bump: the predicate truth tables are untouched, so
  version 2 still describes every judgment the queries cite.
- No VOQ additions: the Phase 1 set is a frozen benchmark — extending it
  post-hoc would contaminate the 15/5 measurement. Rule coverage lives in
  the policy suite instead.
- No rule composition: combining rules into a change envelope belongs to
  Phase 6 (proof-carrying change).
- No canonical migration, no gateway change, no new schema, no hand-edit
  of rebuilt views. No critique-point action taken.

## Validation observed (2026-09-07 session)

`make check` zero errors; warning baseline OK; `make lint` incl. code
reachability (156/156, the new module classified through the package
facade) green; policy suite 21 passed; full suite green; views
regenerated after the final authored change.
