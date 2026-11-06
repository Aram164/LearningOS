# warning_baseline --update prints a green adoption line over a broken tree (2026-11-06)

Task: agent-perspective hunt on branch `codex/review-shortcomings-20261105`. Workflow
step: development gates — warning baseline.

Observation (verified): `tools/warning_baseline.py --update` (non-ratchet mode) adopts
the collected warnings and exits 0 even when `collect` reported validation *errors*,
printing none of them. The `--check` gate still fails afterwards, so the overall
system stays fail-closed.

Inference: an agent reading only the adoption line can believe the tree is healthy
after adopting; the green line over a red tree is the friction.

Safety retained: the `--check` gate refuses a broken tree regardless of adoption;
ratchet semantics unchanged.

Smallest improvement: refuse `--update` when the collected report has errors (or print
the error count prominently on the adoption line). Safeguards to retain: ratchet
behavior; baseline-managed signatures never hide errors.

Filing: GitHub issue not filed — `gh` CLI unavailable (blocked by tooling availability,
2026-11-06). Proposed issue title: "warning_baseline --update exits 0 while validation
errors are present".
