# Completion of the interrupted planning verification

18 October 2026. Read-only against Core
`074f4717e14527798752de84b3c9c4e88348b658` and UI
`a88b1188ad54439b4df32813904de182c06a105c`; both source trees were clean.
The check/apply/receipt experiment used a temporary synthetic world only.
This is planning evidence, not candidate implementation acceptance.

Reproducible measurements: [verify_remaining.py](verify_remaining.py) and
[VERIFICATION-2026-10-18.json](VERIFICATION-2026-10-18.json).
Run the script with `LearningOS/repository/.venv/bin/python`. It reads live
state, writes its report here, and performs its mutation probe under a temporary
directory. It does not change Core source or live learner data.

## The seven outstanding checks

| Check from scan plan §8 | Finding and consequence |
|---|---|
| 1. Reviewed-apply binding | **Confirmed.** `app/handlers/_shared.py::apply_reviewed_envelope`, `app/gateway.py::prepare_review_envelope`, and `adapters/capability.py::reviewed_envelope_apply` bind reviewed input bytes, capability/payload, snapshot/revisions and saved envelope identity. They do not hash the whole report. A synthetic report augmented with both `claims` and `claim_anchors` applied successfully. Keep these fields outside the envelope/route rows. |
| 2. Evidence-only ledger guard | **The keep-as-written answer is false.** `_execute_plan_import` prepares the check report without rendering the lineage write; `domain/plan_import.py::minimal_artifact_ids` ignores that path. A ledger-only check therefore has no owners, while `store/transactions.py::transaction_artifacts` falls back to `file:operations/transactions/lineage.yaml` at apply. `_plan_revisions` requires exact equality. Explicitly prepare the prospective ledger path and identical guards in check/apply. See migration decision M2. |
| 3. Goal request schema | **Confirmed, with a wording correction.** `goal_id` is an array of strings, not a scalar plain string; its items have no regex. JSON Schema validation accepted the proposed `@basis` and `claims-audit:` tokens. `x-los-id-kind` is metadata; the handler independently checks exact, whitespace-free tokens. |
| 4. A6 round-trip | **Confirmed.** `tests/test_arch_idroundtrip.py`: **28 passed**. Its detector-alternation test reads only `scan.py`; six detector names emitted by `goals.py` escape that check. The live scan has 128 IDs outside the present grammar. Both emitter helpers are named `_emit`, but their detector-name argument positions differ (scan: 1; goals: 0). Cover both and test actual emitted IDs, including caller-fed detectors. |
| 5. Receipt verifier/report extras | **Confirmed for added report fields.** The augmented report passed the full existing synthetic reviewed-apply, generate, and `verify_plan_receipt.py` sequence: both exits 0, `committed-and-verified`. **Additional required repair:** the verifier currently refuses an empty `expected_write_sha256` dictionary, so the future ledger-only revision still needs a narrow verifier update. It already excludes lineage from the expected-hash key set. Allow an empty map only for the correctly bound ledger-only case, retaining ordinary-write equality checks. |
| 6. Baseline writers | **Resolved.** `tests/arch_surface.py::main` writes `surface.json`. `tools/generate_capability_schemas.py` owns capability schemas. `tests/arch_cli_describe.py::describe` provides the parity description; no standalone parity writer was found in the Python tools/tests searched. Update only affected command rows in `cli-parity-baseline.json` and affected historical cases in `cli-parity-corpus.json`; verify with `test_arch_cli_parity.py`. Preserve unrelated historical normalizations. Add new flag cases in that test module rather than silently changing the 1,786-case corpus pin in `tests/test_cli.py`. |
| 7. Second grammar enforcement | **Confirmed in the searched runtime and tests.** Searches for goal-kind `ids.parse`/`ids.is_valid` and `KINDS["goal"]` found the A6 test, not a runtime input gate. `app/handlers/goals.py::goal` validates tokens and then scan/ledger membership. New audit IDs still require the explicitly designed historical-membership rule; grammar acceptance does not grant membership. |

The pending planning reads are complete. End-to-end tests of *new* evidence-only
re-judgment, anchor admission and audit commands remain implementation acceptance
work because those behaviors do not exist yet.

## Refreshed measurements

- Scan: **152 goals / 52 groups**; 107 review, 21 lineage-stale,
  21 source-changed, 3 study-map obligations.
- Re-stamp analysis: **0 eligible / 12 needs-rejudgment / 9 needs-review**.
- Rich routes: **914**; supported lineage: **128**; unrecorded: **786**.
- Core's actual file resolver on the **894 active rich routes** returns PDFs
  for **524**, Markdown for **6**, notebooks for **8**, no resolved file with
  a URL for **184**, and neither resolved file nor URL for **172**. Two routes
  resolve multiple files; their IDs are in the JSON. These are resolution
  buckets, not the future admission classifier. This closes the anchor plan's
  mirror-resolver measurement assumption without pretending its reader exists.
- Exact hypergeometric calculation for a uniform sample without replacement
  from 128: zero defects in 20 gives upper bound **16**; in 30 gives **10**
  at the stated 95% level. The statistical guarantee requires a sampling
  assumption; deterministic selection alone is not a proof of uniform sampling.

## Integration corrections found while closing the checks

1. **One admission set.** Combine material/coverage changes with explicit
   unchanged stale/disputed re-judgments, then run the same anchor admission on
   every positive claim in that set. Implementing either plan's trigger rule
   in isolation would either reject the other's repair or bypass its check.
2. **One ledger guard shared by writers.** `transaction_artifacts` uses declared
   logical owners *instead of* file fallback, not their union. Ordinary plan
   imports and `unit.material-synthesis.publish` currently declare logical
   owners; re-stamp declares the file artifact. Therefore adding that guard
   only to evidence-only revisions would not catch an intervening publication
   by another existing writer. Migration M2 specifies the shared correction.
3. **Route-patch is a fifth writer if V7 lands.** Its catalog `writes` and A19
   `operational-owners.yaml` currently exclude lineage. Update both under an
   explicit scope amendment. The expected A11 keys are
   `cli.route-patch`, `request_schemas.route.patch.schema.json`, and
   `catalog.commands.route.patch`; capability schemas are generated but are
   not independently hashed by A11. Exact keys come from the final surface diff.
4. **UI generation is narrower than the anchor plan assumes.** The checked
   generators derive manifest and UI-response types; no inspected generator
   turns each request schema into a UI request type. Route-patch is refused by
   the UI gesture table. Keep contract checks; regenerate only artifacts whose
   real schema closure changes. Do not manufacture a UI request-type task.
5. **Audit selection and attestation need separate treatment.** To claim a
   population bound, freeze the complete eligible pool before drawing a random
   seed, store pool/seed/sample in its authorized ledger entry, and require the
   closing audit to match it. Reproduction uses the recorded seed. Otherwise
   report a deterministic spot check with no probability guarantee. A seed or
   second session does not prove semantic reviewer independence.

Final baseline checks: validation **0 errors / 3 visible operational warnings**;
warning baseline **OK, no new signature**. Both proposed goal-token forms also
passed the current CLI parser. Core and UI remained clean.

No literature claims were independently re-audited in this pass; the supplied
review was used to locate implementation questions. No commit, installation,
publication, live re-judgment or audit decision was performed.
