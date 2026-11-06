# data-contract.yaml header rule does not reproduce its declared record_schemas count (2026-11-06)

Task: agent-perspective hunt on branch `codex/review-shortcomings-20261105`. Workflow
step: development gates — data contract.

Observation (verified count, tool rule not adjudicated): `system/contracts/data-contract.yaml`
declares `record_schemas: 36`. By the header's own stated rule (top-level
`system/schema/*.json` minus schemas declaring `x-governs: artifact`) a hand count
gives 49 top-level schemas with 8 artifact-governed → 41, not 36.

Inference: `tools/schema_contract.py` (and `make check`) enforce this mechanically and
pass, so the tool presumably implements the real rule and the header's stated rule is
stale — or the tool's rule has drifted from the documented one. Not adjudicated here;
flagged, not concluded.

Safety retained: the count is machine-enforced; nothing can drift silently between the
file and the tool.

Smallest improvement: make the header state exactly the tool's rule (or align the tool
with the header) and pin the stated rule with a test, so the next hand-count agrees.
Safeguards to retain: the mechanical gate stays the authority.

Filing: GitHub issue not filed — `gh` CLI unavailable (blocked by tooling availability,
2026-11-06). Proposed issue title: "data-contract record_schemas header rule counts 41,
declares 36".
