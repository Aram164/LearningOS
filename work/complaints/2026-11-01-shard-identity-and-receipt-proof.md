# Preserve the stricter CI identity proof from unmerged PR 64

Task: assess open Core PR 64 by content against the commissioned repair tip a480e7b39c9d9190bde2983df4e3172a14926ce9. Its preserved head is 57c9d3bffc8b669f57b29bdcaa94cba6577fb594. The draft is not wholly superseded; this note records inspected proof differences, not a failed current test run.

Observed: current .github/workflows/validate.yml and release-pair.yml check file coverage and equality of total JUnit case count with total collected count. Equal totals do not establish equality of test identities. The draft tools/check_shard_completeness.py instead maps JUnit cases back to collected node IDs and compares their multisets. That helper is absent on current main. Current witness merge copies audit logs to the merged directory by filename; the draft adds collision refusal. Current tools/release_pair_receipt.py unconditionally writes system_check_passed=true; the draft describes it as caller-asserted evidence.

Impact: the existing gates provide useful coverage/static evidence, and UI CI runs the paired system-check directly. This observation does not demonstrate any skipped/duplicated test, lost witness or falsely accepted current release. The specific count-only proof is weaker than its set-equality comment suggests, and a receipt boolean does not independently authenticate test execution.

Smallest investigation: preserve and port only the shared identity checker/collision refusal and truthful receipt wording through separate reviewed commits. First use small negative fixtures: equal-count missing-plus-duplicated cases, unmapped case, failing/error case and audit-name collision must refuse; exact multisets pass with declared skips visible. Retain existing file partition/pin/static gates, all hosted execution and receipt hash/provenance verification. No full local suite is required for these small checker tests. Do not merge the old runner/Task IR stack as an incidental dependency.

Proof retained externally: LearningOS/workbench/gemini-arena-2026-11-01/evidence/pr-64-original.patch, PR-ASSESSMENT.md and REPAIR-PLAN.md; preserved draft commits dc7a6b9, 6a6c271 and 57c9d3b. No CI implementation was changed by this review.

Issue: https://github.com/Aram164/LearningOS/issues/90
