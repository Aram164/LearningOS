# Agent runner allowed porcelain writes past an uncertain write

Task: implement review findings 1–2 from PR #59, authorized by Aram on
2026-10-27. Tested base: Core `d3d3b35`, Python 3.14, macOS, isolated linked
checkout and synthetic `mini_repo` fixtures. No live learner data was changed.

## Observed

`tools/agent_run.py::build_index` classified only registry commands as writes
for argv/log plans, but used catalogue `writes`/`kind` for plans containing
`use`. Neither rule included `session-end`, `generate` or AI porcelain writers.
Missing registry entries also produced different classifications between paths.

Before the repair, 13 new regression cases failed and one passed. In particular,
the real runner adapter (without an injected executor) dispatched a mocked
`session-end --commit-message fixture --push` after a simulated lost gateway
response under `on_error: continue`. The observed call sequence was
`seal, session-end, inspect`, rather than `seal, inspect`. Sessionless argv,
prefixed argv and operation-id plans were admitted as well.

Reproduce with `tests/test_agent_run.py`, selecting
`classification_is_conservative or session_end_commit_push or
uncertain_write_blocks_porcelain or describing_porcelain` against the base
runner. Dispatch and the lost subprocess response are mocked to avoid any Git
commit or push. These experiments prove runner admission/scheduling behavior;
they do not claim an actual remote push occurred.

## Repair and acceptance

Use the executing parser/registry once for every plan shape. The existing
`query` and `tool` kinds declare repository reads; commands, porcelain,
unregistered operations and unknown kinds remain write barriers. The
catalogue resolves task names without overriding runtime operation bindings.
This preserves lightweight explicit reads while avoiding a second effect rule.

Require a plan session before any dispatch, honor the uncertainty barrier even
with `write: false`, retain independent reads under `on_error: continue`, and
permit sessionless descriptions of effectful operations. Tests exercise the
production admission/scheduling route; removing legacy injected-test paths is
outside this repair.

Acceptance: both discovery paths return identical writer sets; every tested
sessionless commit/push attempt is refused before any step runs; uncertain
writes block porcelain while an independent read still succeeds. Retain all
existing gateway, session, projection and report safeguards.

Verification: 127 runner/read-session/readiness/consolidation/task tests,
82 architecture tests and 111 efficiency/catalogue/document-command tests
pass. Ruff, mypy, code reachability and the system map pass. Validation has
zero errors; the baseline remains 964 warnings across 32 managed signatures
(nine additional operational advisories are baseline-exempt in this checkout).

GitHub issue: https://github.com/Aram164/LearningOS/issues/60
