# Full module package for a focused SaD revision

**Observed:** 2026-09-28, while improving SaD L06–L08's resource order and the Poisson-to-exponential waiting-time bridge.

## Where the friction appeared

The focused `plan-edit-context` reads made the existing stages and routes easy to inspect. The write crossed a different boundary: it added a source and routes, changed stage resources and wording across three existing units, and therefore required `module-plan-import`. The current [operator contract](../../../system/OPERATOR.md) and [plan creation SOP](../../../system/PLAN-CREATION-SOP.md) reserve the compact revision path for narrower changes; source-registry and source-map changes require the full plan path.

To express the small set of intended changes, the agent had to assemble a full module import package containing the current source map and complete L06–L08 unit/map records alongside the edits. That meant copying and reserializing unchanged state, then repairing package-level issues involving an inherited URL field, warning growth, and a learner-state fingerprint before the no-write check passed. Together, the source intake and plan import changed five plan files and one source-registry file, plus their transaction records. The [SaD audit](../../../work/active/workspace-m2-exam-prep/outputs/sad-l06-l08-distribution-bridges-audit-2026-09-28.md) records the intended learning change; [the import receipt](../../../operations/transactions/transaction-20260928-192027-001.yaml) records the applied plan transaction.

## Why this is a complaint

The broad package made the agent carry unchanged module data through a focused revision. Reconstructing that data added work and a chance of accidental drift without adding much safety beyond what snapshot guards, cross-file validation, reviewed intent, and atomic receipts already provide. This is an inference about the package shape, not a claim that the import's safeguards are unnecessary.

One refusal was valuable: preflight caught a wrong material reference (`MATERIAL-MISSING`) before any plan write. Preserve that check. The issue here is the amount of unchanged data the agent must supply to reach the check, not the check itself.

## Smallest improvement to investigate

Consider a reviewed, snapshot-bound change set for existing units that can atomically add source-registry entries and source-map routes while patching named stages. Let the importer load unchanged records from the guarded snapshot, as the existing compact `unit_revisions[]` path already does for its supported edits. Keep the same material-reference checks, warning regression gate, learner-state protection, cross-file validation, reviewed hash, receipt, and no-partial-write behavior.

Measure whether this reduces agent-supplied package size and preflight retries on a replay of this SaD change. If it merely moves equivalent complexity into an opaque request, it is not an improvement.
