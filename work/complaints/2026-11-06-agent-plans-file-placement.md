# agent-plans.md writes the plan file inside the data root it declares off-limits (2026-11-06)

Task: agent-perspective hunt on branch `codex/review-shortcomings-20261105`. Workflow
step: agent plans (tools/agent_run.py procedure).

Observation (verified, texts): `system/procedures/agent-plans.md` heads with "Author
the plan **outside canonical data**", then its transcript writes the plan with
`printf '%s' '…' > "$LOS_FX/agent-plan.json"` where the same `$LOS_FX` is passed as
`--root`. A placement rule exists only for reports (`--report-dir` must be outside the
root or under gitignored `.venv/` scratch); none exists for the plan file.

Inference: an agent mirroring the transcript in a real checkout drops `agent-plan.json`
into the repository root, and no document says whether that is legal or where it should
go.

Safety retained: the runner is experimental and its output is never settled fact
(OPERATOR.md says so); no canonical write is involved.

Smallest improvement: state the plan-file rule explicitly (outside the root, like
reports, or in gitignored scratch) and align the transcript with it. Safeguards to
retain: the "verify a run report against the repository" instruction.

Filing: GitHub issue not filed — `gh` CLI unavailable (blocked by tooling availability,
2026-11-06). Proposed issue title: "agent-plans transcript places the plan inside
--root while the heading says outside canonical data".
