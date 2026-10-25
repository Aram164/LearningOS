# Plan provenance audit mislabels commit evidence and receipt counts

Observed while fact-checking architecture assessments and applying the verified fixes on 2026-10-22. Baseline Core: `1d80aa03e674131a67bda37db04fce2d8076c62a`.

## Workflow and impact
`tools/plan_write_audit.py` labelled commits as mediated/off-gateway by intersecting plan-path history with any change under the transaction directory. A revision-ledger update or edit to an existing receipt therefore qualified as receipt evidence. The output could not support operation-level provenance judgments.

The same tool counted every transaction-directory YAML as a receipt. In the inspected tree, 349 YAML files contained 346 transaction receipts and three ledgers. This wording and counting affected the architecture assessments.

## Reproduction and proof
Create a disposable Git history with a plan change plus a ledger edit, then one with an existing receipt edit. The original implementation treats both as receipt-carrying commits. Neither added a receipt document. A new receipt concerning unrelated work also cannot establish that the plan change was mediated.

The original source is at the baseline commit; the relevant implementation is `tools/plan_write_audit.py:56-84`. New regression cases in `tests/test_plan_write_audit.py` cover ledger additions/updates, existing receipts, renames, real receipt additions, merges, migrations, local-ref scope and malformed input.

## Smallest improvement and acceptance
Report commit co-occurrence explicitly, detect actual receipt-document additions, count current receipt documents separately and state the scope of history inspected. Do not claim that a shared commit proves a receipt covers each edit.

- Ledger and existing-receipt changes never count as added receipt documents.
- Renames and receipts brought in through merge parents are not new receipts.
- New receipts created by a merge are handled against every parent.
- The supported `--list` CLI and anchored-copy executable procedure remain usable.
- Current receipt counts exclude revision, idempotency and lineage ledgers.
- Receipt schema/write-set/hash validation remains outside this diagnostic; the output says so.

## Local repair
The bounded patch implements those criteria and updates the current executable procedure and tool/workflow wording. Historical critique measurements are preserved. Focused and integration verification is retained in `LearningOS/workbench/review-fixes-2026-10-22`.

## Filing status
Duplicate search found no matching issue. Aram directly approved publication. Filed: https://github.com/Aram164/LearningOS/issues/10

Focused audit/anchored-copy checks: 21 passed; native executable procedure: 41/41 cases passed with audit/render witnesses. The root integration selection independently passed 19 checks (10 deselected). Complete UI development check, Core static checks and preservation checks are recorded with the local repair evidence.

