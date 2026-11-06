# Planning work has no entry row; the two entry chains give conflicting reading rules (2026-11-06)

Task: agent-perspective hunt on branch `codex/review-shortcomings-20261105`. Workflow
step: OPERATOR.md "Start here" task table / planning.

Observation (verified, all texts): the OPERATOR task table has no row for planning or
documentation work, so both escape clauses ("unless that entry fails or the task crosses
the scope it declares") are undefined for a planning task. Root `AGENTS.md` requires
"Files affected — concrete paths" and forbids asking what the repository can answer,
while repository `AGENTS.md` forbids preceding the named entry read with directory
listings — but "that entry" does not exist for planning. The two chains also disagree on
which whole-document reads are allowed (root says read OPERATOR.md in full before
planning anything touching the repo; repository AGENTS.md routes code/docs work to
DEVELOPER.md whose step 1 reads only the hard-boundary section). The root file sits
outside `normative-corpus.yaml`, so nothing reconciles them mechanically.

Inference: a planner must either scan (discouraged), ask (forbidden by root), or guess.

Safety retained: none of this weakens learner-ownership boundaries; it is navigation
friction only.

Smallest improvement: add a planning row to the OPERATOR task table (entry read: the
DEVELOPER route for code/docs planning), or an explicit "planners may list after the
entry read" clause in repository `AGENTS.md`. Safeguards to retain: learner-state entry
reads stay mandatory before operating records.

Filing: GitHub issue not filed — `gh` CLI unavailable (blocked by tooling availability,
2026-11-06). Proposed issue title: "no OPERATOR task-table row for planning; entry-read
escape clauses undefined for planners".
