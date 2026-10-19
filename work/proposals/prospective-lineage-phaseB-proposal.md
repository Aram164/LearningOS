# Phase B proposal: prospective proof-carrying lineage

Status: proposed. Authorizes nothing beyond this document until Aram
approves section 7.

Division of responsibility (approved design):

```text
builder   declares claim + evidence + reads
judge     proves resolvability, support, freshness, admissibility
gateway   persists canonical mutation + lineage atomically, never invents it
```

## 1. Reuse inventory (no parallel concepts)

- Claim IDs: `covers:<route_id>`, `scope:<kind>:<owner>`,
  `dossier:<key>` (`semantics/lineage.py` emitters).
- Evidence: bare locator strings, harness-resolved to digests
  (`semantics/changes.py` `build_envelope`, `TrustedContext`).
- Reads: revisions ledger + predicate `CONTRACT_VERSION`.
- Statuses, contest/review, withdraw cascade: as implemented.
- Ledger file, schema validation, assumption-integrity checks: as
  implemented (`operations/transactions/lineage.yaml`).

## 2. Honest delta (the only new machinery)

1. **Record bindings.** `ClaimLineage` has no `admitted_by`
   (transaction/request) and no successor link. Repair-supersession
   needs both, plus defined same-`claim_id` re-judgment behavior
   (withdraw-old + record-new, old fields preserved). This is a small,
   explicit sidecar schema delta, versioned like the ledger itself —
   not zero change, and not a new authority.
2. **Judge hook.** `module.plan.import` / `unit.map.import` do not pass
   through Phase-6 `admit()`. Add an evidence-validation preflight in
   those handlers: diff the package against live state to find changed
   Phase-B claims; require one evidence entry per changed claim;
   resolve via the harness (never trust builder digests); check
   freshness; refuse (`WriteRefused` class) on missing/unresolvable.
   Reuse `TrustedContext` resolution; do not fork a second judge.
3. **Package contract.** Builders supply per-claim evidence
   (`claim_evidence` map, claim id -> bare locators + reads); template
   + SOP note + contract validation. My L07/L08 builders are the
   pattern to extend.
4. **Atomicity.** Append the sidecar write to the same `writes` dict
   handed to `_write_transaction`. Same boundary or rollback; a
   committed canonical write with a failed lineage write must be
   impossible, not merely unlikely.
5. **Trigger rule (no-backfill guard).** Lineage is created iff the
   transaction changes a Phase-B claim: new edge, repaired edge,
   changed scope-authority or dossier-freshness judgment. Untouched
   claims, unchanged values, and unrelated metadata: no record.

## 3. Claim-class activation honesty

Route-covers has live writers today (plan/map imports) and is fully
covered. Scope-authority and dossier-freshness judgments have no
canonical write path that changes them yet (predicates answer;
dossier serving is unwired) — their record shape and fail-closed rule
land with Phase B, enforcement attaches where their writers land
(`unit.material-synthesis.publish` is the dossier-freshness candidate).
No enforcement theater over paths that do not exist.

## 4. Fail-closed rule

After Phase B lands, a semantic mutation that changes a Phase-B claim
without resolvable admitted evidence is refused before apply. This is
not the gateway judging truth — the judge already did that. It is the
gateway refusing to let admitted proof be accidentally discarded.

## 5. Accepted cost of no-backfill

L07/L08's evidence bases live in session transcripts, audits, and
package files — not in the ledger. Under prospective-only, they stay
unrecorded. Deliberate, and the price of the policy Aram set.

## 6. Test plan

Extend `tests/test_semantic_lineage.py` (bindings, supersession,
withdraw-preserves-provenance) plus admission tests: missing evidence
refused; unresolvable locator refused; stale read refused; atomicity
(canonical-only commit impossible); trigger rule (untouched claims
produce no records). L07/L08 applied diffs serve as fixtures for the
diff-to-claims step, not as backfill data.

## 7. Acceptance (approved wording)

For a newly created or repaired covered claim, a fresh audit can
retrieve the exact admitted evidence basis and transaction provenance
from lineage alone, without reopening the underlying source locator;
if the canonical semantic mutation can commit without that lineage
being resolvable, Phase B fails.

## 8. Out of scope

Detectors, page-text cache, dossier serving, bulk migration, any new
lineage authority, any change to lazy historical policy.
