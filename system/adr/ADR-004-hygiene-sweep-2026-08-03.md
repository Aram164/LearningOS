# ADR-004 — The hygiene sweep: mess becomes self-announcing (2026-08-03)

**Status:** accepted · **Context:** after ADR-003, Aram asked how to make the
system robust against everyday human mess (duplicates, misfiled files) without
(a) requiring him to memorize the architecture, (b) adding rigidity, or
(c) recurring Claude "cleanup sessions" that cost credits.

## Decision

Move mess-policing from the operator's judgment into the validator, as four
deterministic **warning** checks (`tools/learning_os/rules.py::check_hygiene`,
codes `HYGIENE-*`, documented in VALIDATION.md). Warnings nag but never block;
they run free at every `make check`, every pre-commit, and in CI.

The four checks map one-to-one onto the failure classes that actually occurred
(ADR-003): **HYGIENE-LOCK** (stale `.git/index.lock` — the failure that
silently blocked both repos for two weeks), **HYGIENE-VIEWS** (views older
than the last commit — the stale-dashboard failure), **HYGIENE-UNFILED**
(loose Markdown outside the drop zones — the "where do I put this" failure),
**HYGIENE-SHADOW** (a legacy/Job twin edited after its canonical note — the
dual-copy drift failure, detected by filename + mtime, never content).

## Why this shape

- **Aram's contract stays one rule:** "never file — inbox." The sweep exists
  so that when the rule is accidentally broken, the *system* says so at
  commit time with the exact path and fix, instead of a paid audit finding it
  weeks later.
- **No rigidity added:** zero new schemas, metadata, or buckets; inbox,
  workspace subfolders and the Garden remain structure-free by design and are
  exempt. Errors still come only from the existing structural rules.
- **Quarantine respected:** the shadow sweep's Job root is a narrow,
  Aram-approved carve-out recorded in CLAUDE.md §13 — names and mtimes only.
- **Location-independence kept:** shadow roots are optional; on a repo moved
  away from the semestercontext container the checks silently no-op.

## Consequences

Cleanup cost model changes from O(weeks of accumulation, Claude session) to
O(one warning, one `mv`). Tests: `tests/test_hygiene.py` (13 cases incl.
false-positive guards); real-repo run at adoption: 0 errors, 0 warnings.
