# Stage 8 repair and complete acceptance

## Understanding

Aram now authorizes repairing all six failures from hosted run 40945395574 and delivering the completed, clean experiment. Preserve the existing product behavior, exact review and transaction safeguards while fixing the demonstrated verification gaps. Publish a repaired Core paired with the unchanged UI, run the complete hosted release-pair gate, and independently inspect its artifacts and learner-state evidence before declaring readiness.

## Files affected

- `system/procedures/back-up-and-restore.md`: reconcile its five inventory count expectations with the verified declared backup inventory, preserving restore and tamper assertions.
- `tests/test_system_audit_2026_09_05.py`: observe actual material hashing/file reads rather than the whole-byte hashing helper; preserve one hash per build and fresh-build invalidation.
- `tests/scenarios/recorded/ai-action.delivery.apply/{apply-garden-shelve,exact-replay}.json`: refresh only after proving why the request bytes/digests changed and checking exact replay and receipt correspondence.
- `tests/scenarios/recorded/lineage.restamp/{check-all,check-all-cli}.json`: refresh only after proving the fixture commit change from its real tree inputs.
- This plan, the existing Stage 8 outcome and complaint records: retain the original failure and append repaired verification/publication evidence.
- Sibling `stage8-repair/`: retain root-cause probes, source pins, CI logs, downloaded artifacts and independent acceptance results outside the source checkout.

## Decisions and reasons

1. Keep streamed hashing and existing per-build cache lifetime. Repair the historical audit's observation boundary; restoring whole-file allocation would undo the measured product improvement merely to satisfy a spy.
2. Keep exact backup entry counts/checksums. First verify the extra two Core schemas and one UI file explain 488 to 491; do not replace the check with a wildcard or silently omit files.
3. **ASSUMPTION:** changed fixture contracts explain the AI request hashes and real judgment commit. Reproduce both old and current contract inputs in disposable fixtures and compare actual source bytes before refreshing any recording. Retain all receipt, replay and ownership checks; add no broad normalization rule.
4. Run focused local checks and the full hosted exact-pair workflow; no local full-suite substitute. A successful job status alone is insufficient: verify JUnit completeness/population results, artifact digests, pair receipt, source/contract pins and preservation independently.
5. Reuse the current UI `8e82f8a` unless new measured evidence requires a bounded UI repair. Readiness means zero validation errors, no new/grown managed warning signature, all hosted acceptance jobs passing and verified artifacts; the existing warning baseline is disclosed rather than erased.

## Steps

1. Preserve the pending report files and protected primary pins; reproduce/trace all four failure families without production edits.
2. Apply the justified bounded test/transcript/recording repairs and check exact deltas.
3. Run the six formerly failing cases, owning parser/transaction/refusal checks and the complete procedure transcripts, then validation/static gates.
4. Commit/push the clean repaired source, pin both SHAs, and dispatch one existing `release-pair.yml` run.
5. Monitor every suite, witness-population, UI and final gate; diagnose any new failure before a further repair.
6. Verify downloaded acceptance artifacts, all integrity/preservation checks, and report the exact accepted pair, run and remaining limits.

## Risks and verification

Blind recording updates could hide changed learner behavior; the old/current fixture-input differential and semantic receipt/replay assertions expose that. A hash spy could miss repeated hashing; instrument actual reads and verify a later build sees changed material. Backup count repair could hide lost files; compare the declared inventory and retain checksum/tamper checks. Use focused pytest, Scrut 0.5.0, Ruff/mypy/system-map checks, zero-error validation/warning baseline, hosted full JUnit/population gate, artifact SHA-256 and the existing pair-receipt verifier.

## Out of scope

Further optimizations/features, unrelated warning debt, changing real learner Units/plans, paid trials, subagents, merges, installation and production migration. The original learner checkout stays untouched. The prior acceptance-only restriction is superseded for the six demonstrated failures by Aram's explicit repair request.

## Verified root causes and selected repair

The disposable `stage8-repair/trace-fixture-inputs.py` differential changes only `system/contracts/capabilities.yaml` plus the two new study-sequence schemas between accepted Stage 4C and current inputs. All four old recordings are reproduced byte-for-byte with historical inputs. Under current inputs the AI requests differ only at `preconditions.snapshot_id`; their serialized request/receipt hashes therefore change. Both lineage checks' judgment commit equals the corresponding real fixture HEAD. No broad hash/commit normalization or production semantics change is needed. Refresh exactly the four named recordings, retaining their old copies and the differential proof outside the source tree.

The backup contract includes both Core schemas and the UI `src` tree. Those two schemas plus `src/features/unit/sequence.ts` explain exactly three added entries; update the five explicit transcript counts from 488 to 491 and retain all checksum and tamper assertions. The F13 audit now counts reads of the actual shared material through `Path.open`, proving one read despite two routes; a new loaded repository after changed material performs one fresh read and invalidates the dossier. Its original zero-extra-repository-load assertion remains. All 28 focused audit/efficiency cases pass.

The complete local procedure run passed the repaired backup drill, then exposed a previously masked expectation in `system/procedures/bootstrap-order.md:82`: the compact catalogue now has 21 queries and the unchanged 48 commands, while the transcript expects 20/48. Add this concrete owning path to the repair and update only that count; the new query is the approved Stage 6 read. Run every transcript independently with the existing Scrut/audit helpers so an earlier stale expectation cannot hide later failures; retain all results, then rerun the owning pytest procedure suite.

All 38 independent Scrut transcripts and their owning audit/render checks pass after the catalogue-count correction; the 21 affected scenario cases and 28 audit/efficiency cases pass. The earlier pytest procedure run had already passed its other 15 tests (two expected failures); the final whole procedure test and population persistence run in hosted CI. Avoid repeating the already-passing 38-transcript local matrix; full upstream CI remains authoritative.

Publication includes the prior failed-attempt report and complaint notes, this repair plan, narrow verified test/transcript/recording changes and retained focused proof. Final acceptance evidence is written beside the checkout after CI, preserving an exact, clean certified source pair. No later documentation change will silently replace that tested SHA.
