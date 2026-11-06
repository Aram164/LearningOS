# Stratum anchor notes pin optimizer/ir/ paths that no longer exist in Stratum (2026-11-06)

Task: agent-perspective hunt on branch `codex/review-shortcomings-20261105`. Workflow
step: source anchoring (knowledge notes referencing Stratum code).

Observation (verified by exact-path finds): all 14 notes under
`knowledge/notes/data-systems/stratum/` (13 `note-stratum-op-*.md` +
`note-stratum-extract-dataframe-op.md`) carry "Legacy Job provenance" stamps:
`verified_against: f63b93c (2026-07-27)` with component paths
`stratum/optimizer/ir/_aggregation_ops.py` and five siblings. The commit pin is valid
(tip of Stratum `origin/agent/fold-missing-masks`). None of the six `ir/` paths exists
at Stratum HEAD; the code now lives under `optimizer/logical/` + `optimizer/physical/`,
which the *current* study-map locators already use.

Unverified: whether the paths existed at `f63b93c` (needs `git ls-tree` in Stratum).

Inference: real drift against Stratum HEAD, but the stamps are historical by design
("Legacy Job provenance"), so re-pointing is a content decision, not a mechanical fix.

Safety retained: current study maps point at live paths; only the historical provenance
stamps are stale.

Smallest improvement: decide per note — re-point the stamps to current paths, or add an
annotation convention ("paths as of <commit>; current layout: …") so a future reader
does not treat the stale paths as live. Safeguards to retain: historical stamps are
never silently rewritten; any change is a reviewed content edit.

Filing: GitHub issue not filed — `gh` CLI unavailable (blocked by tooling availability,
2026-11-06). Proposed issue title: "14 Stratum provenance stamps pin optimizer/ir/
paths that no longer exist".
