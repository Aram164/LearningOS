# verify_plan_receipt has no deletion-row concept (2026-11-06)

Task: agent-perspective hunt on branch `codex/review-shortcomings-20261105`. Workflow
step: development gates — plan receipt verification.

Observation (verified, file:line): `tools/verify_plan_receipt.py:264` — the post-commit
loop treats every write row as a file that must exist. A schema-legal row with
`sha256_after: null` (`system/schema/transaction-receipt.schema.json` `write`
definition allows null; real ledger examples exist, e.g.
`transaction-20261002-213908-001.yaml`) always fails "receipt write is gone" if the
file was intentionally deleted.

Inference (ASSUMPTION, inferred from the write-scope check, not tested): plan
capabilities write only inside the target unit directory plus ledgers, with in-place
edits — so deletion rows are unreachable for this tool today, and the failure is loud,
not silent. The tool nonetheless misreports a schema-legal state if that assumption
ever breaks.

Safety retained: fails closed; a failed verification is never permission to apply
something new.

Smallest improvement: treat `sha256_after: null` + missing file as a verified deletion,
`sha256_after: null` + present file as a failure ("file exists but the receipt recorded
its deletion"), and add one deletion-row case to the existing tests
(`test_unit_plan_revision.py`, `test_plan_resume.py`, or
`test_compact_module_plan_revision.py` — none exercises a deletion row today).
Safeguards to retain: hash checks for non-null rows unchanged.

Filing: GitHub issue not filed — `gh` CLI unavailable (blocked by tooling availability,
2026-11-06). Proposed issue title: "verify_plan_receipt fails every schema-legal
deletion row".
