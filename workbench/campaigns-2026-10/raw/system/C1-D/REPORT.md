# C1-D report — sources and intake bug hunt (Flash, 2026-10-24)

**Item:** L2-5. **Batch:** C1-D — capabilities starting `source`, `collection`,
`material`, `ai-action`, `capture`, `inbox` (12 total:
`material.span`, `material.context`, `inbox.content`, `inbox.list`,
`capture.create`, `inbox.resolve`, `ai-action.delivery.apply`,
`collection.create`, `source.feedback.record`, `source.intake.record`,
`collection.entry.revise`, `source.record.revise`).

**Base:** `origin/main` = `d6c4779029e366718b71bda158d2aa8f9da1db39` (clone
`~/los-glm-C1-D-2026-10/repository`, from GitHub, branch `glm/C1-D-2026-10-24`,
own python3.14 venv). **Nothing committed, nothing pushed.** The two finding
tests sit uncommitted in the clone's `tests/` (registered in `tests/group_map.py`,
group `gateway`); the workbench copies are the durable ones.

## Findings (2, both with failing pytest on base `d6c47790`)

### 1. capture.create — a same-second file capture can overwrite an earlier capture's bytes

`C1-D/capture.create/same-second-file-capture-overwrite/` (finding.md + test).

`capture.create` promises "original input is preserved" and never overwrites —
the text branch loops for a free name. The file branch takes exactly one
fallback name, `{stamp}-{src.name}`, and never re-checks it
(`tools/learning_os/app/handlers/capture.py:109-111`); the engine overwrites by
design (`store/transactions.py:1752-1754, 1997-2005`) and inbox files are not
revision-tracked, so a third file capture sharing the basename lands in the
same clock second silently replaces the second capture's bytes while its
receipt still points at that path. Test: three V2 captures of different files
named `notes.md` under the production `LOS_OBSERVATIONS` frozen clock; the
third exits 0 and the second capture's file now holds the third's bytes.

### 2. material.context — an explicit `--limit 0` is silently widened to a full page of 20

`C1-D/material.context/zero-limit-widened/` (finding.md + test). Minor.

The request contract bounds the page ("page size from 1 to 20 items") and the
shared window helper refuses out-of-range limits, but
`tools/learning_os/app/handlers/materials.py:1204-1206` reads the page as
`req.get("limit") or 20` first — an explicit zero never reaches the check and
becomes the maximum page. `inbox.content` takes its limit verbatim and refuses
0; `material.context` is the odd one out. Test: `material-context "density
worked example" --limit 0` on a one-note repo returns exit 0 with the item
instead of refusing.

Both tests are fix-agnostic (refuse, or the fact still holds) per the C1-C
convention, so a fix by either refusal or preservation passes them.

## Attacked and held (dead leads — do not re-hunt)

- **Inbox path traversal/symlinks (inbox.content/resolve).** `..` and absolute
  names refuse (`capture.py:276`, `_admit` `capture.py:602-617`); the shared
  `bytes_inside_owner` walks the *entire* parent chain and refuses every
  symlink component (`store/fs.py:31-45`), so reading through a symlinked
  in-inbox directory is refused; the folder envelope path (`_admit` + `_collect`)
  refuses symlink components and non-regular files too. Dot-files: excluded
  from `inbox.list` (`_shared.py:87-107`), readable by exact name in
  `inbox.content` — as declared. Non-UTF-8 refuses before any text is produced.
- **capture.create stdin under V2.** The invariant "never comes from stdin" is
  enforced upstream: the generated payload schema
  (`system/schema/capabilities/capture.create.schema.json`) requires exactly
  one of `file`/`text` (oneOf), and `validate_payload` refuses a payload with
  no declared schema (`app/gateway.py:157-171`). The `sys.stdin.read()` branch
  (`capture.py:113`) is unreachable through the gateway. Direct CLI capture is
  refused entirely ("must use the gateway").
- **source.feedback.record vocabulary/type.** The gateway payload schema and
  `system/schema/study-map.schema.json` both pin `feedback` to the six-value
  enum; the ranking consumer deliberately degrades unknown values to
  reported-but-unranked (`derive/semantics/source_use.py:12-19`). Resource
  binding is checked against the stage (handler `learner.py:606-637`) and
  again by the validator (`FEEDBACK-RESOURCE`, `FEEDBACK-RESOURCE-SOURCE`).
- **Intake type confusion via gateway.** Suspicious unguarded fields
  (`partition` used in set membership before any type check,
  `sources.py:604`) are unreachable through the gateway: the generated
  `source.intake.record.schema.json` pins `partition: string`,
  `identifiers: [object,null]`, `remove_identifiers: array`, and
  `validate_payload` runs before the handler. Batch rules (1–20 rows, duplicate
  ids, create-only fields on a correct, link dedup within batch and registry,
  cited-URL removal guard) all check out in `_plan_one`/`_plan_source_intake`.
- **collection.create identity.** A collection record carries no internal id —
  identity *is* the filename stem (ARCHITECTURE §3.3), so no stem/record
  divergence exists; the existing destination refuses
  (`sources.py:382-389`) and the reviewed bytes are hash-bound before use.
- **Check→apply binding on the three approved writers** (`collection.entry.revise`,
  `source.intake.record`, `source.record.revise`): all re-plan at apply, refuse
  on diff-hash change, and take snapshot + revision guards
  (`sources.py:268-301, 865-899, 1492-1526`). The record-revise lineage-ledger
  write is capability-declared (`operations/transactions/lineage.yaml` is in
  the capability's `writes`); the dossier-rebase shortcut's narrow conditions
  (only material_checksums moves, screened/evidence-free/analysis-free, outside
  comparisons) are enforced in `_rebase_routes_or_refuse` (`sources.py:1021-1086`);
  replacement dossiers are validated against the staged state and reuse of live
  provenance is refused.
- **material.context continuation.** Equivalent filters page on (normalized
  into the observations digest), changed filters/material bytes/dossier bytes
  refuse mixed pages; double snapshot guard around the read
  (`materials.py:1441-1454, 1493`). Unreadable notes/dossiers refuse the query
  up front (`materials.py:1231-1242`).
- **material.span.** Snapshot-guarded both sides; remote sources are never
  fetched (status machine `materials.py:767-784`); `--extract` re-hashes the
  file after reading and refuses changed bytes (`materials.py:820-821`).
- **Engine-level crash windows/concurrency.** Same conclusion as C1-B/C: the
  journal-backed compare-and-undo engine with inflight reconciliation
  (`store/transactions.py:1894+`) covers mid-commit kill windows; hunt
  handler-level holes the validator blesses — which is exactly finding 1.

## Residual surface (not fully audited this session — for the verification pass)

- `AIActionService.apply_delivery_proposal` internals (delivery/artifact SHA
  binding, delivery idempotency) behind `ai_action_apply_delivery`
  (`app/handlers/ai.py:97-145`): the handler wrapper enforces the V2 +
  approved-delivery authority and delegates; the service module was recently
  reworked (commits `d6c4779`, `d962456` reference #12 delivery cases).
  ASSUMPTION: I did not line-audit the service this session.
- `material.span` helpers `_placement_route`/`_brief_analysis_refs` and the
  bounded `_read_part` extractor: entry points checked as above; internals
  skimmed, not exhausted.

## Environment notes for the verification pass

- Re-register the workbench test copies in a clone's `tests/group_map.py`
  (group `gateway`) or conftest collection errors out; imports are flat
  (`gateway_helpers`, `repo_builders`, `conftest` from `tests/`).
- Finding 1's test needs `LOS_OBSERVATIONS` (production override, PLAN D19) —
  the test sets it itself via monkeypatch; it models "three calls inside one
  wall-clock second", which in-process gateway hosts reach trivially. Without
  the freeze the same collision needs the stamped fallback to repeat within
  one second.
- One pytest file per run; both files fail standalone (1 failed in 1.60s /
  0.23s).

Stop here per the campaign: fixes, issues and landing belong to Aram/Claude.
