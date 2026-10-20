# T03 — Adversarial probes

**21/21 passed.**

## PASS — a1-replay-same-envelope

*Intent:* An exact retry of the same intent must replay the receipt, not write twice.

**first_ok**

```
true
```

**first_receipt**

```
operations/transactions/transaction-20261020-062122-001.yaml
```

**second_exit**

```
0
```

**second_ok**

```
true
```

**second_replayed**

```
true
```

**second_transaction**

```
transaction-20261020-062122-001
```

**fingerprint_unchanged**

```
true
```

**receipt_count**

```
[
 2,
 2
]
```

## PASS — a2-reseal-under-used-key

*Intent:* Re-sealing a used idempotency key must be refused, not double-written.

**first_ok**

```
true
```

**reseal_exit**

```
0
```

**reseal_stderr**

```
seal_envelope: guards auto: capture-request:a2-key=1
```

**apply_exit**

```
2
```

**apply_error**

```
{
 "code": "IDEMPOTENCY_CONFLICT",
 "message": "idempotency key was already used for a different approved intent",
 "retryable": false,
 "details": {}
}
```

**apply_stderr**

```

```

**fingerprint_unchanged**

```
true
```

**receipt_count**

```
[
 2,
 2
]
```

## PASS — a3-same-key-different-intent

*Intent:* The same key with different content must be refused as a conflict.

**reseal_exit**

```
0
```

**reseal_stderr**

```
seal_envelope: guards auto: capture-request:a3-key=1
```

**apply_exit**

```
2
```

**apply_error**

```
{
 "code": "IDEMPOTENCY_CONFLICT",
 "message": "idempotency key was already used for a different approved intent",
 "retryable": false,
 "details": {}
}
```

**apply_stderr**

```

```

**fingerprint_unchanged**

```
true
```

**receipt_count**

```
[
 2,
 2
]
```

## PASS — a4-replay-only

*Intent:* Verifying a committed receipt must not re-run the handler.

**exit_code**

```
0
```

**body**

```
{
 "schema_version": 2,
 "request_id": "request-a4-key-fa46d190",
 "idempotency_key": "a4-key",
 "capability": "capture.create",
 "ok": true,
 "replayed": true,
 "transaction_id": "transaction-20261020-062128-001",
 "receipt_path": "operations/transactions/transaction-20261020-062128-001.yaml",
 "snapshot_after": "sha256:f4a37d33c3387200b91b35d615b061c162c210ee1c5b510acdfe71737f4dca2b",
 "result": {
  "transaction_id": "transaction-20261020-062128-001",
  "receipt_path": "operations/transactions/transaction-20261020-062128-001.yaml",
  "artifact_revisions": {
   "capture-request:a4-key": 1
  },
  "snapshot_after": "sha256:f4a37d33c3387200b91b35d615b061c162c210ee1c5b510acdfe71737f4dca2b",
  "replayed": true,
  "captured": "work/inbox/20261020-062128-replay-only-probe.md"
 },
 "error": null
}
```

**fingerprint_unchanged**

```
true
```

## PASS — b1-stale-snapshot

*Intent:* A write sealed against a stale snapshot must be refused (exit 3).

**seal_exit**

```
0
```

**apply_exit**

```
3
```

**apply_error**

```
{
 "code": "STALE_SNAPSHOT",
 "message": "canonical state changed since this request was approved",
 "retryable": true,
 "details": {
  "expected": "sha256:08fdd4d86bb9d12fbb4b804df720b02a980031c30cb9f7007c9b425b46ef43c5",
  "actual": "sha256:4a6c658e89e99d24493d6c920f73d7c4cba82fbd21eedd98e0322318e0d56ed6"
 }
}
```

**fingerprint_unchanged_by_refused_write**

```
true
```

## PASS — b2-two-writers-one-snapshot

*Intent:* Two concurrent writers against one snapshot: one wins, one conflicts.

**exit_codes**

```
[
 0,
 3
]
```

**a_error**

```
null
```

**b_error**

```
{
 "code": "STALE_SNAPSHOT",
 "message": "canonical state changed since this request was approved",
 "retryable": true,
 "details": {
  "expected": "sha256:08fdd4d86bb9d12fbb4b804df720b02a980031c30cb9f7007c9b425b46ef43c5",
  "actual": "sha256:8cf2603b523fbdcec1c63eb121f43d0049251a77e73a4c7dd0878dd41928c8dd"
 }
}
```

## PASS — c1-bare-write-command-refuses

*Intent:* A named write command run without an envelope must refuse.

**exit_code**

```
2
```

**stderr**

```
los: INVALID_REQUEST: canonical writes must use GatewayEnvelopeV2; direct CLI application is disabled — apply it with `los capability garden.seed.create --payload-file ENVELOPE.json` (payload schema: `los capabilities garden.seed.create --json`; envelope: WORKFLOWS §25c)
```

**fingerprint_unchanged**

```
true
```

## PASS — c2-out-of-scope-write

*Intent:* A write naming a stage that does not exist must refuse.

**seal_exit**

```
2
```

**stderr**

```
seal_envelope: stage not found: stage-does-not-exist (did you mean: stage-demo-pending, stage-demo?); fix the payload and seal again
```

**fingerprint_unchanged**

```
true
```

## PASS — c3-shelving-needs-explicit-selection

*Intent:* Shelving must not apply anything that was not explicitly selected.

**prepare_ok**

```
true
```

**proposal_ids**

```
[]
```

**empty_selection_exit**

```
2
```

**empty_selection_stderr**

```
seal_envelope: every selected ID must exist in the current proposal; fix the payload and seal again
```

**bogus_selection_exit**

```
2
```

**bogus_selection_stderr**

```
seal_envelope: every selected ID must exist in the current proposal; fix the payload and seal again
```

**fingerprint_unchanged**

```
true
```

## PASS — c4-note-revise-needs-approval

*Intent:* A durable-note revision without approval must refuse.

**exit_code**

```
2
```

**stderr**

```
los: INVALID_REQUEST: note revision requires --approve after reviewing the full replacement
```

**stdout**

```

```

**fingerprint_unchanged**

```
true
```

## PASS — d1-fail-closed-blocks-writes

*Intent:* One validation error anywhere must block every canonical write.

**validate_exit**

```
1
```

**validate_tail**

```
ges [curriculum/modules/module-demo/source-map.yaml]
W ROUTE-ANGLE-DETAIL-MISSING: source 'source-demo-book' route to 'unit-demo-l02' has a one-line angle but no `angle_detail` for the hover [curriculum/modules/module-demo/source-map.yaml]
W HYGIENE-VIEWS: generated/ views absent — run `make views` (they are disposable, but the human-fallback path depends on them)

13 error(s), 9 warning(s) — FAIL
```

**write_seal_exit**

```
2
```

**write_seal_stderr**

```
seal_envelope: E SCHEMA: unit: 'artifacts' is a required property (at root) [curriculum/modules/module-demo/units/unit-demo-l01/unit.yaml]; E SCHEMA: unit: 'kind' is a required property (at root) [curriculum/modules/module-demo/units/unit-demo-l01/unit.yaml]; E SCHEMA: unit: 'module_id' is a required property (at root) [curriculum/modules/module-demo/units/unit-demo-l01/unit.yaml]; E SCHEMA: unit:
```

**fingerprint_unchanged**

```
true
```

## PASS — d2-reads-refuse-rather-than-omit

*Intent:* With a broken record, a read must refuse instead of quietly omitting it.

**unit-list_exit**

```
2
```

**unit-list_stderr**

```
los: INVALID_REQUEST: the published manifest no longer matches system/contracts/manifest-contract.yaml (declared v15).
  schema at /records/13: {'id': 'unit-demo-l01', 'type': 'unit', 'this is not': 'valid', 'source_selections': [], 'scope_sources': [], 'revision': 3, 'path': 'curriculum/modules/mod
```

**unit-list_bytes**

```
0
```

**inspect_exit**

```
2
```

**inspect_stderr**

```
los: INVALID_REQUEST: the published manifest no longer matches system/contracts/manifest-contract.yaml (declared v15).
  schema at /records/13: {'id': 'unit-demo-l01', 'type': 'unit', 'this is not': 'valid', 'source_selections': [], 'scope_sources': [], 'revision': 3, 'path': 'curriculum/modules/mod
```

**fingerprint_unchanged**

```
true
```

## PASS — e1-agent-improvised-study-map

*Intent:* Workflow 23 needs a human scope authority; can an agent supply one?

**seal_exit**

```
2
```

**seal_stderr**

```
seal_envelope: study map replacement preflight failed; no canonical files were written; fix the payload and seal again
```

**apply_exit**

```
null
```

**apply_stderr**

```
null
```

**original_stage_still_present**

```
true
```

**note**

```
the plan file is the scope authority; nothing in the gateway can tell a human-reviewed file from an agent-drafted one
```

## PASS — e1b-agent-authored-scope-lands

*Intent:* The ladder from 'no plan' to 'an agent's own scope, installed'.

**ladder**

```
[
 {
  "rung": "A. hand-written map, no plan_template_version",
  "seal_exit": 2,
  "apply_exit": 2,
  "refusal": "seal_envelope: study map replacement preflight failed; no canonical files were written; fix the payload and seal again",
  "agent_stage_installed": false
 },
 {
  "rung": "B. canonical template, source_plan placeholder intact",
  "seal_exit": 2,
  "apply_exit": 2,
  "refusal": "seal_envelope: study map replacement preflight failed; no canonical files were written; fix the payload and seal again",
  "agent_stage_installed": false
 },
 {
  "rung": "C. replacement map, retired stages undeclared",
  "seal_exit": 2,
  "apply_exit": 2,
  "refusal": "seal_envelope: study map replacement preflight failed; no canonical files were written; fix the payload and seal again",
  "agent_stage_installed": false
 },
 {
  "rung": "D. replacement map, retirement declared with an agent-written reason",
  "seal_exit": 2,
  "apply_exit": 2,
  "refusal": "seal_envelope: E REF-STAGE: resume pointer references an unknown stage [curriculum/resume.yaml]; fix the payload and seal again",
  "agent_stage_installed": false
 },
 {
  "rung": "E. extend the map by one agent-authored stage",
  "seal_exit
… (truncated)
```

**validate_after_landing**

```
0
```

**receipts_written**

```
2
```

**note**

```
the guards are structural: a template version, a named plan, a declared retirement, one active stage, a live resume pointer. None of them is a provenance gate, and rung E needs no reason string at all.
```

## PASS — e2-masters-promotion-surface

*Intent:* Workflow 27 (promote a Master's module): what does the CLI expose?

**dashboard_exit**

```
2
```

**dashboard_bytes**

```
0
```

**dashboard_head**

```

```

**catalog_update_help**

```
usage: los masters-planning-catalog-update [-h] (--file FILE |
                                           --record RECORD) [--approve]
                                           [--expected-snapshot EXPECTED_SNAPSHOT]
                                           [--expected-revision EXPECTED_REVISION]
                                           [--json]

options:
  -h, --help            show this help message and exit
  --file FILE           reviewed academic-only catalog as a YAML file
  --record RECORD       the Master Planning catalog as an inline object
                        (alternative to
```

## PASS — e3-turn-the-semester-surface

*Intent:* Workflow 24 (turn the semester): what does the CLI expose?

**session_end_help**

```
usage: los session-end [-h] [--commit-message COMMIT_MESSAGE] [--close]
                       [--push] [--session-id SESSION_ID] [--channel CHANNEL]
                       [--include-stale] [--json]

options:
  -h, --help            show this help message and exit
  --commit-message COMMIT_MESSAGE
                        Commit this session's owned changes with this message.
  --close               end this session's ownership window without
                        committing: delete only its own session ledger (a bare
                        review never closes)
  --push                Push this session's commit after committing owned
                        changes when requested.
  --session-id SESSION_ID
                        close this session id (default: LOS_SESSION_ID, else
                        this channel's ledger)
  --channel CHANNEL     channel ledger to close when no s
```

## PASS — f1-note-body-with-frontmatter

*Intent:* A body file that carries its own frontmatter: is it caught?

**write_exit**

```
0
```

**frontmatter_blocks_in_file**

```
3
```

**validate_exit**

```
0
```

**validate_errors**

```
[]
```

**file_head**

```
---
id: note-f1-duplicate
type: note
role: synthesis
title: Body with its own frontmatter
created: '2026-10-20'
state: rough
authorship: operator-drafted
semantic_review: unreviewed
---

---
id: note-f1-duplicate
type: note
title: "Body with its own frontmatte
```

**note**

```
the writer prepends its own frontmatter; a body that carries one produces a file with two blocks
```

## PASS — f2-fragment-uri-two-resolvers

*Intent:* A material ref with a fragment: accepted on write, flagged on validate.

**write_exit**

```
0
```

**write_stderr**

```

```

**validate_exit**

```
0
```

**uri_warnings**

```
[
 "W URI-MATERIAL: 'material://source-demo-book/lecture-01.pdf#page=2' does not resolve on disk [knowledge/notes/mathematics/note-demo.md]"
]
```

**baseline_exit**

```
1
```

**baseline_stdout**

```
warning-baseline: 10 warning(s) across 8 signature(s); baseline 9 across 7 (recorded 2026-09-20)
  NEW       URI-MATERIAL at knowledge/notes/mathematics/note-demo.md: 0 → 1
```

**note**

```
the seal-time materials check strips the fragment; the general validator does not, so a write the system accepts can break the warning-baseline gate
```

## PASS — f3-unknown-and-tampered-envelope

*Intent:* An unknown capability and a hand-written envelope must refuse.

**unknown_capability_exit**

```
2
```

**unknown_capability_stderr**

```
los: unknown or non-public capability: no.such.capability
```

**tampered_exit**

```
2
```

**tampered_stderr**

```

```

**fingerprint_unchanged**

```
true
```

## PASS — f4-unbounded-read-is-clamped

*Intent:* A read that asks for everything must stay bounded.

**exit_code**

```
2
```

**content_len**

```
null
```

**limit_declared**

```
null
```

**total_characters**

```
null
```

**stderr**

```
los: INVALID_REQUEST: offset must be nonnegative and limit between 1 and 16000
```

**default_read_bytes**

```
587
```

**default_content_len**

```
162
```

**default_total_characters**

```
162
```

## PASS — g1-which-approval-paths-admit-a-plan-revision

*Intent:* Which approval paths admit a study-map import?

**matrix**

```
[
 {
  "channel": "codex",
  "approval_kind": "direct-user-gesture",
  "apply_exit": 2,
  "agent_stage_installed": false,
  "error_code": "UNCONFIRMED",
  "error_message": "unit.map.import is authorized by a reviewed action in the LearningOS app, not by a codex-channel request: apply it from the screen that shows the exact change, or send it through the approved operator path"
 },
 {
  "channel": "ui",
  "approval_kind": "direct-user-gesture",
  "apply_exit": 0,
  "agent_stage_installed": true,
  "error_code": null,
  "error_message": null
 },
 {
  "channel": "operator",
  "approval_kind": "operator-approval",
  "apply_exit": 0,
  "agent_stage_installed": true,
  "error_code": null,
  "error_message": null
 }
]
```

**note**

```
the reviewed-UI gate refuses a codex-channel gesture, exactly as designed; but the CLI can declare any channel it likes, and the operator path admits the same write without a gesture at all
```
