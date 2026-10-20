# T02 — The operator's filing journey

**13/16 passed.**

## PASS — j1-capture-inbox

*Intent:* A learner (or the agent) drops an unsorted fragment.

**step**

```
capture
```

**capability**

```
capture.create
```

**seal_exit**

```
0
```

**apply_exit**

```
0
```

**seal_stderr**

```
seal_envelope: guards auto: capture-request:t02-capture=0
```

**apply_stderr**

```

```

**seal_tokens**

```
1
```

**apply_tokens**

```
216
```

**replayed**

```
false
```

**transaction_id**

```
transaction-20261020-143528-001
```

**receipt_path**

```
operations/transactions/transaction-20261020-143528-001.yaml
```

**error**

```
null
```

**receipt_on_disk**

```
true
```

**inbox_after**

```
[
 "20261020-143528-synthetic-fragment.md",
 "note-drop.md",
 "pack/one.md",
 "pack/two.md"
]
```

## PASS — j2-read-inbox

*Intent:* The operator lists the inbox and reads one drop, bounded.

**listing**

```
{
 "step": "inbox-list",
 "argv": [
  "inbox-list"
 ],
 "exit_code": 0,
 "tokens": 171,
 "bytes": 685
}
```

**captured_name**

```
20261020-143528-synthetic-fragment.md
```

**read**

```
{
 "step": "inbox-read",
 "argv": [
  "inbox-read",
  "20261020-143528-synthetic-fragment.md"
 ],
 "exit_code": 0,
 "tokens": 153,
 "bytes": 614,
 "keys": [
  "content",
  "content_sha256",
  "contract",
  "item",
  "next_offset",
  "offset",
  "offset_unit",
  "path",
  "schema_version",
  "snapshot_id",
  "start_line",
  "total_characters"
 ]
}
```

**content_sha256**

```
sha256:ca506f3c0cd794c223c5185058f8811013e32c3cbefce87363defcb75ceda45a
```

## FAIL — j3-create-durable-note

*Intent:* The operator files the fragment as a durable, source-bound note.

**step**

```
note.create
```

**capability**

```
note.create
```

**seal_exit**

```
2
```

**apply_exit**

```
2
```

**seal_stderr**

```
seal_envelope: note body carries its own frontmatter; the writer owns the frontmatter — strip it and send the body only; fix the payload and seal again
```

**apply_stderr**

```
seal_envelope: note body carries its own frontmatter; the writer owns the frontmatter — strip it and send the body only; fix the payload and seal again
```

**seal_tokens**

```
1
```

**apply_tokens**

```
1
```

## FAIL — j4-read-back-the-note

*Intent:* The operator reads the note back — the filing is observable.

**read**

```
{
 "step": "note-read",
 "argv": [
  "note-read",
  "note-canvas-variance"
 ],
 "exit_code": 2,
 "tokens": 1,
 "bytes": 0
}
```

**path**

```
null
```

**has_content**

```
false
```

## FAIL — j5-bind-evidence

*Intent:* The operator binds one piece of evidence to the note.

**step**

```
note.evidence.add
```

**capability**

```
note.evidence.add
```

**seal_exit**

```
2
```

**apply_exit**

```
2
```

**seal_stderr**

```
seal_envelope: note not found: note-canvas-variance; fix the payload and seal again
```

**apply_stderr**

```
seal_envelope: note not found: note-canvas-variance; fix the payload and seal again
```

**seal_tokens**

```
1
```

**apply_tokens**

```
1
```

## PASS — j6-relation

*Intent:* The operator records one explicit concept relation.

**step**

```
concept.relations.change
```

**capability**

```
concept.relations.change
```

**seal_exit**

```
0
```

**apply_exit**

```
0
```

**seal_stderr**

```
seal_envelope: guards auto: registry-concept-relations=0
```

**apply_stderr**

```

```

**seal_tokens**

```
1
```

**apply_tokens**

```
208
```

**replayed**

```
false
```

**transaction_id**

```
transaction-20261020-143530-001
```

**receipt_path**

```
operations/transactions/transaction-20261020-143530-001.yaml
```

**error**

```
null
```

**receipt_on_disk**

```
true
```

## PASS — j7-garden-seed

*Intent:* A deliberately half-formed idea is planted, not filed.

**step**

```
garden.seed.create
```

**capability**

```
garden.seed.create
```

**seal_exit**

```
0
```

**apply_exit**

```
0
```

**seal_stderr**

```
seal_envelope: guards auto: garden-request:t02-garden=0
```

**apply_stderr**

```

```

**seal_tokens**

```
1
```

**apply_tokens**

```
225
```

**replayed**

```
false
```

**transaction_id**

```
transaction-20261020-143531-001
```

**receipt_path**

```
operations/transactions/transaction-20261020-143531-001.yaml
```

**error**

```
null
```

**receipt_on_disk**

```
true
```

## PASS — j8-save-question

*Intent:* The operator saves a question as a first-class record.

**step**

```
atlas.question.save
```

**capability**

```
atlas.question.save
```

**seal_exit**

```
0
```

**apply_exit**

```
0
```

**seal_stderr**

```
seal_envelope: guards auto: note-canvas-question-variance=0
```

**apply_stderr**

```

```

**seal_tokens**

```
1
```

**apply_tokens**

```
233
```

**replayed**

```
false
```

**transaction_id**

```
transaction-20261020-143532-001
```

**receipt_path**

```
operations/transactions/transaction-20261020-143532-001.yaml
```

**error**

```
null
```

**receipt_on_disk**

```
true
```

## PASS — j9-register-source

*Intent:* The operator registers one global source identity.

**step**

```
source.intake.record
```

**capability**

```
source.intake.record
```

**seal_exit**

```
0
```

**apply_exit**

```
0
```

**seal_stderr**

```
seal_envelope: guards auto: source-canvas-synthetic=0
```

**apply_stderr**

```

```

**seal_tokens**

```
1
```

**apply_tokens**

```
199
```

**replayed**

```
false
```

**transaction_id**

```
transaction-20261020-143534-001
```

**receipt_path**

```
operations/transactions/transaction-20261020-143534-001.yaml
```

**error**

```
null
```

**receipt_on_disk**

```
true
```

**check_exit**

```
0
```

**diff_sha256**

```
sha256:02b74017246d73bf2a500e42236abff3afad47b4b5f33111c12b11cb83faff77
```

## PASS — j10-source-feedback

*Intent:* The operator records lightweight personal evidence.

**step**

```
source.feedback.record
```

**capability**

```
source.feedback.record
```

**seal_exit**

```
0
```

**apply_exit**

```
0
```

**seal_stderr**

```
seal_envelope: guards auto: study-map-demo-l01=0, unit-demo-l01=3
```

**apply_stderr**

```

```

**seal_tokens**

```
1
```

**apply_tokens**

```
271
```

**replayed**

```
false
```

**transaction_id**

```
transaction-20261020-143535-001
```

**receipt_path**

```
operations/transactions/transaction-20261020-143535-001.yaml
```

**error**

```
null
```

**receipt_on_disk**

```
true
```

## PASS — j11-record-observation

*Intent:* The operator records one attempt — evidence, never mastery.

**step**

```
learner.observation.append
```

**capability**

```
learner.observation.append
```

**seal_exit**

```
0
```

**apply_exit**

```
0
```

**seal_stderr**

```
seal_envelope: guards auto: workspace-demo=0
```

**apply_stderr**

```

```

**seal_tokens**

```
1
```

**apply_tokens**

```
435
```

**replayed**

```
false
```

**transaction_id**

```
transaction-20261020-143536-001
```

**receipt_path**

```
operations/transactions/transaction-20261020-143536-001.yaml
```

**error**

```
null
```

**receipt_on_disk**

```
true
```

## PASS — j12-stage-note

*Intent:* Stage-specific learning belongs in the stage's working note.

**step**

```
stage.note.write
```

**capability**

```
stage.note.write
```

**seal_exit**

```
0
```

**apply_exit**

```
0
```

**seal_stderr**

```
seal_envelope: guards auto: unit-demo-l01=4
```

**apply_stderr**

```

```

**seal_tokens**

```
1
```

**apply_tokens**

```
238
```

**replayed**

```
false
```

**transaction_id**

```
transaction-20261020-143537-001
```

**receipt_path**

```
operations/transactions/transaction-20261020-143537-001.yaml
```

**error**

```
null
```

**receipt_on_disk**

```
true
```

## PASS — j13-shelving-prepare

*Intent:* The operator prepares the review packet — nothing is applied yet.

**prepare**

```
{
 "step": "review.prepare",
 "capability": "review.prepare",
 "seal_exit": 0,
 "apply_exit": 0,
 "seal_stderr": "seal_envelope: guards auto: study-map-demo-l01=1, unit-demo-l01=5",
 "apply_stderr": "",
 "seal_tokens": 1,
 "apply_tokens": 244,
 "ok": true,
 "replayed": false,
 "transaction_id": "transaction-20261020-143538-001",
 "receipt_path": "operations/transactions/transaction-20261020-143538-001.yaml",
 "error": null,
 "receipt_on_disk": true
}
```

**proposal_items**

```
null
```

**proposal_count**

```
null
```

## PASS — j14-session-end

*Intent:* The session ends deliberately; the ledger names its own rows.

**exit_code**

```
0
```

**stderr**

```

```

**stdout_head**

```
{"ok":true,"touched":["curriculum/modules/module-demo/units/unit-demo-l01/shelving-proposal.md","curriculum/modules/module-demo/units/unit-demo-l01/stages/stage-demo/notes.md","curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml","knowledge/concept-relations.yaml","knowledge/garden/synthetic-half-formed-idea-maybe-the-variance-identity-is-a-spec.md","knowledge/notes/questions/note-canvas-question-variance.md","operations/transactions/idempotency.yaml","operations/transactions/revisions.yaml","operations/transactions/transaction-20261020-143528-001.yaml","operations/transactions/t
```

**keys**

```
[
 "client",
 "committed",
 "ok",
 "other_sessions",
 "owned_changes",
 "ownership_conflicts",
 "pushed",
 "session_closed",
 "session_id",
 "stale_hours",
 "stale_paths",
 "touched",
 "unrelated_changes",
 "validation"
]
```

## PASS — j15-read-back-the-world

*Intent:* After the journey: the world still validates and the baseline holds.

**validate_exit**

```
0
```

**validate_stdout**

```
stage 'stage-demo-pending' teaches source-demo-book at '§2' — the module's source map declares no route for it; adopt the material in the module's map, or bind the resource to a route the map declares [curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml]

0 error(s), 13 warning(s) — OK
```

**warnings_exit**

```
0
```

**warnings_stdout**

```
warning-baseline: 13 warning(s) across 8 signature(s); baseline 13 across 8 (recorded 2026-09-20)
warning-baseline: OK — zero errors, no new warning signature.
```

**status_stdout**

```
Learning OS v3 · learning_os v3.2.0 · /Users/aramaljanadi/los-canvas-fixed/worlds/t02/LearningOS/repository
  notes 3 · concepts 2 · relations 2 · sources 2
  programs 1 · modules 1 (1 enrolled) · projects 1 · units 2 · study maps 1 · workspaces 2 active (0 standing), 0 archived
  inbox 3 top-level · 4 files · garden 2 · reviewed 0/3 · evidence 0/3
  exam: 2026-10-09 — Demo Module (Termin 2)
  validation: OK · 13 warning(s), visible and nonblocking (`make warnings` for the delta)
  human home page: generated/reading-room.md (make views)
```

## PASS — j16-cost-ledger

*Intent:* What did one filing session cost in steps and tokens?

**steps**

```
14
```

**writes**

```
11
```

**reads**

```
3
```

**write_tokens**

```
2282
```

**read_tokens**

```
325
```

**total_tokens**

```
2607
```

**per_step**

```
[
 {
  "step": "capture",
  "capability": "capture.create",
  "seal_exit": 0,
  "apply_exit": 0,
  "seal_tokens": 1,
  "apply_tokens": 216
 },
 {
  "step": "inbox-list",
  "tokens": 171
 },
 {
  "step": "inbox-read",
  "tokens": 153
 },
 {
  "step": "note.create",
  "capability": "note.create",
  "seal_exit": 2,
  "apply_exit": 2,
  "seal_tokens": 1,
  "apply_tokens": 1
 },
 {
  "step": "note-read",
  "tokens": 1
 },
 {
  "step": "note.evidence.add",
  "capability": "note.evidence.add",
  "seal_exit": 2,
  "apply_exit": 2,
  "seal_tokens": 1,
  "apply_tokens": 1
 },
 {
  "step": "concept.relations.change",
  "capability": "concept.relations.change",
  "seal_exit": 0,
  "apply_exit": 0,
  "seal_tokens": 1,
  "apply_tokens": 208
 },
 {
  "step": "garden.seed.create",
  "capability": "garden.seed.create",
  "seal_exit": 0,
  "apply_exit": 0,
  "seal_tokens": 1,
  "apply_tokens": 225
 },
 {
  "step": "atlas.question.save",
  "capability": "atlas.question.save",
  "seal_exit": 0,
  "apply_exit": 0,
  "seal_tokens": 1,
  "apply_tokens": 233
 },
 {
  "step": "source.intake.record",
  "capability": "source.intake.record",
  "seal_exit": 0,
  "apply_exit": 0,
  "seal_tokens": 1,
  "apply_to
… (truncated)
```
