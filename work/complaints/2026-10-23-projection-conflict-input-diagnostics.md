# Projection conflict reports hashes without the changed input paths

## Observed during authorized work

On 2026-10-23, while adding the AIDE medical-MLE preparation guide to the Bachelor thesis project, a `source.record.revise` transaction for `source-pytorch-tutorials` refused during projection publication. Core HEAD was `1d80aa03e674131a67bda37db04fce2d8076c62a` with pre-existing dirty/untracked work. The proposal appended one contextual evaluation while preserving the source identity and previous evaluation.

The sealed request was `request-thesis-mle-20261023-source-pytorch-tutorials` in session `thesis-mle-medical-20261023`. Its response was:

```json
{
  "ok": false,
  "transaction_id": null,
  "receipt_path": null,
  "error": {
    "code": "PROJECTION_FAILED",
    "message": "canonical state changed during projection publication (projected sha256:87722081705970a83448da685cac246dab692975a2b152955ab9a9644d72d5d6, actual sha256:aa29e13cb7d80d83dbbfe14f8c08f7b5a323beb7f1b3db61ddd4758aabf0417c)",
    "retryable": true,
    "details": {"stage": "core.projection", "rollback_complete": true}
  }
}
```

The refusal correctly preserves the snapshot/publication safeguard. The diagnostic identifies only two aggregate hashes, so it does not tell the operator which input changed or whether the changed input overlapped this transaction. ASSUMPTION: another writer changed an input during publication; the response alone does not identify the writer or changed file. No controlled concurrent-writer reproduction was attempted.

## Reproduction and limits

1. Prepare and seal a valid `source.record.revise` request using the current snapshot and derived revision guards.
2. Submit it with `los capability source.record.revise --payload-file ENVELOPE.json`.
3. In this observed run, the publication detected a changed canonical fingerprint and returned the response above. The concurrent trigger is not established, so these steps describe the incident, not a deterministic reproduction.

Evidence is retained in the task's temporary bundle at `/private/tmp/thesis-mle-20261023/source-pytorch-tutorials-result.json`, with the record, preflight and envelope alongside it. This complaint retains the bounded diagnostic independently of that temporary bundle. Relevant workflow: source revision and GatewayEnvelopeV2 projection reconciliation.

## Smallest improvement to investigate

Include a bounded list of changed input paths (or an equivalent diagnostic reference) in a canonical-fingerprint publication conflict. Preserve rollback and fail-closed behavior. A dedicated conflict code may also help distinguish this condition from unrelated generator failures, but do not automatically retry when effects are uncertain.

Acceptance criteria:

- A controlled canonical-input change during publication still refuses safely and reports rollback completeness.
- The diagnostic identifies the changed paths without exposing file contents or secrets.
- An ordinary generator error remains distinguishable from a changed-input publication conflict.
- A fresh, explicitly re-read and re-sealed request can be reconciled without overwriting unrelated work.

## Recovery and filing status

Re-reading the source diff and sealing a fresh request succeeded in `transaction-20261023-015612-001`. The thesis guide, project attachment and workspace next action were subsequently saved and verified; validation had zero errors and the warning baseline had no new signature.

Duplicate searches for projection conflicts, `PROJECTION_FAILED`, and fingerprints found no matching issue. The configured Git remote and connected repository metadata both verified `Aram164/LearningOS` as the destination, with administrative access. Automatic approval review rejected the initial issue payload because it disclosed internal diagnostic details. A reduced, sanitized payload was also rejected because issue creation was considered outside the user-authorized thesis-plan task and requires explicit approval. No issue was created; do not work around this rejection through another client.

### Ready-to-file sanitized report

Title: Identify changed inputs in projection-conflict diagnostics

A source revision encountered a changed-input conflict during projection publication. The operation refused with `PROJECTION_FAILED` and reported `rollback_complete: true`. A fresh request after re-reading the state succeeded.

The safeguard behaved correctly. The diagnostic supplied aggregate fingerprints without identifying changed input paths, so the operator could not determine which input needed reconciliation. This is a diagnostics improvement request, not an assertion that rollback was incorrect.

Please investigate a bounded list of changed input paths, or an equivalent diagnostic reference, while preserving fail-closed publication and rollback. Report paths only, without file contents.

Acceptance:
- A controlled input change during publication still refuses safely.
- The response reports rollback completeness and identifies changed paths.
- Ordinary generator errors remain distinguishable from changed-input conflicts.

Observed once; a deterministic concurrent-writer reproduction has not been established.

### Filed

Filed: https://github.com/Aram164/LearningOS/issues/12

Aram approved publishing the sanitized report above ("I APPROVE") after the review rejection recorded earlier in this section, so "No issue was created" held only until that approval. The Codex session then reached its usage limit while the final `gh issue create` was running and never recorded the outcome. Recorded afterwards on 2026-10-23 from a separate session: a new duplicate search finds exactly this one issue (open, no comments), and its title and body match the report above word for word. ASSUMPTION: that final command created it; the log timestamps are one second apart and the command's own output was never captured.
